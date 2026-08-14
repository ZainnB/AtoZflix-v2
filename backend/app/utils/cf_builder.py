"""
Sparse item-item collaborative filtering build (numpy + scipy).

IMPORT BOUNDARY - read before adding an import of this module
-------------------------------------------------------------
This module is imported by OFFLINE SCRIPTS ONLY: build_similarity.py and
eval_recommender.py. It is deliberately NOT imported by app/utils/recommender.py
or by any route, because that would make numpy and scipy hard runtime
dependencies of the web process. The API reads precomputed neighbours out of the
Item_Similarity table instead and needs neither library.

Keeping that boundary is what lets the deployment image stay on the original
requirements.txt while the model itself is built with proper numerical tooling.

THE MATH
--------
Let X be the (users x items) preference matrix with columns L2-normalised:

    S = X.T @ X                     cosine similarity between every item pair
    C = B.T @ B                     co-occurrence counts (B = X binarised)
    S = S * C / (C + shrinkage)     significance shrinkage

Two films sharing one enthusiastic user otherwise score a perfect 1.0 and
outrank pairs backed by thousands of users; the shrinkage term pulls
low-evidence pairs toward zero.

Only positive preferences enter the matrix. Cosine over signed ratings would
multiply two negatives into a positive, making two mutually-disliked films look
similar and recommending each to anyone who liked the other.
"""

import time

import numpy as np
from scipy import sparse
from sqlalchemy import text

# Preference midpoint on the project's 0-10 rating scale.
RATING_MIDPOINT = 5.0

# Rows pulled from the database per fetch. Reading 15.6M rows in one fetchall
# materialises 15.6M Python tuples (several GB); chunking into preallocated
# numpy arrays keeps peak memory in the hundreds of MB.
FETCH_CHUNK = 1_000_000


def load_interaction_arrays(session, include_movielens=True, verbose=True):
    """
    Stream every interaction out of the database into numpy arrays.

    Returns (rows, cols, vals, user_keys, item_ids) where rows/cols are integer
    codes into user_keys / item_ids.

    Arrays rather than {user: {movie: pref}} dicts on purpose. At MovieLens
    scale the dict-of-dicts form costs roughly 100 bytes per interaction - about
    3-4 GB for 15.6M ratings - while three numpy arrays cost 12 bytes each, so
    the same data fits in ~190 MB. The per-user dicts are still built later, but
    only for the handful of users actually being scored.
    """
    started = time.time()
    user_index, item_index = {}, {}
    row_chunks, col_chunks, val_chunks = [], [], []

    def consume(sql, to_key, to_pref):
        total = 0
        result = session.execute(text(sql))
        while True:
            batch = result.fetchmany(FETCH_CHUNK)
            if not batch:
                break
            rows, cols, vals = [], [], []
            for record in batch:
                preference = to_pref(record)
                if preference <= 0:
                    continue
                key = to_key(record)
                ui = user_index.get(key)
                if ui is None:
                    ui = user_index[key] = len(user_index)
                ii = item_index.get(record[1])
                if ii is None:
                    ii = item_index[record[1]] = len(item_index)
                rows.append(ui)
                cols.append(ii)
                vals.append(preference)
            if rows:
                row_chunks.append(np.asarray(rows, dtype=np.int32))
                col_chunks.append(np.asarray(cols, dtype=np.int32))
                val_chunks.append(np.asarray(vals, dtype=np.float32))
            total += len(batch)
        return total

    n_app = consume(
        "SELECT user_id, movie_id, rating FROM Ratings",
        lambda r: ("app", r[0]),
        lambda r: (r[2] - RATING_MIDPOINT) / RATING_MIDPOINT if r[2] is not None else 0.0,
    )
    n_fav = consume(
        "SELECT user_id, movie_id, 1 FROM Favorites",
        lambda r: ("app", r[0]),
        lambda r: 1.0,
    )
    n_ml = 0
    if include_movielens:
        n_ml = consume(
            "SELECT ml_user_id, movie_id, rating FROM MovieLens_Ratings",
            lambda r: ("ml", r[0]),
            lambda r: (r[2] - RATING_MIDPOINT) / RATING_MIDPOINT if r[2] is not None else 0.0,
        )

    if not row_chunks:
        return None, None, None, [], []

    rows = np.concatenate(row_chunks)
    cols = np.concatenate(col_chunks)
    vals = np.concatenate(val_chunks)

    user_keys = [None] * len(user_index)
    for key, idx in user_index.items():
        user_keys[idx] = key
    item_ids = np.empty(len(item_index), dtype=np.int64)
    for movie_id, idx in item_index.items():
        item_ids[idx] = movie_id

    if verbose:
        print(f"  app ratings {n_app:,} | favourites {n_fav:,} | "
              f"MovieLens {n_ml:,}")
        print(f"  {len(user_keys):,} users x {len(item_ids):,} items, "
              f"{len(vals):,} positive interactions ({time.time() - started:.1f}s)")

    return rows, cols, vals, user_keys, item_ids


def matrix_from_arrays(rows, cols, vals, n_users, n_items, min_item_ratings=0,
                       item_ids=None, verbose=True):
    """Assemble a CSC (users x items) matrix from coordinate arrays."""
    matrix = sparse.csr_matrix((vals, (rows, cols)), shape=(n_users, n_items))
    matrix.sum_duplicates()

    if min_item_ratings > 0:
        support = np.asarray((matrix > 0).sum(axis=0)).ravel()
        keep = support >= min_item_ratings
        if not keep.all():
            if verbose:
                print(f"  dropping {int((~keep).sum()):,} items with "
                      f"< {min_item_ratings} ratings")
            matrix = matrix[:, keep]
            if item_ids is not None:
                item_ids = item_ids[keep]

    return matrix.tocsc(), item_ids


def build_matrix(interactions, min_item_ratings=0, verbose=True):
    """
    Turn {user_key: {movie_id: preference}} into a CSC (users x items) matrix.

    user_key may be any hashable - plain ints for app users, ("ml", id) tuples
    for MovieLens reference users - because it is only ever used as a dict key
    for row assignment. Column j corresponds to item_ids[j].

    Returns (matrix, item_ids) or (None, []) when there is nothing to build.
    """
    started = time.time()
    user_index, item_index = {}, {}
    rows, cols, values = [], [], []

    for user_key, prefs in interactions.items():
        for movie_id, preference in prefs.items():
            if preference <= 0:
                continue
            ui = user_index.setdefault(user_key, len(user_index))
            ii = item_index.setdefault(movie_id, len(item_index))
            rows.append(ui)
            cols.append(ii)
            values.append(preference)

    if not values:
        return None, []

    matrix = sparse.csr_matrix(
        (np.asarray(values, dtype=np.float32),
         (np.asarray(rows, dtype=np.int32), np.asarray(cols, dtype=np.int32))),
        shape=(len(user_index), len(item_index)),
    )
    # A user who both rated and favourited a film produces two entries; the
    # constructor sums them, this collapses them into one stored value.
    matrix.sum_duplicates()

    item_ids = np.empty(len(item_index), dtype=np.int64)
    for movie_id, idx in item_index.items():
        item_ids[idx] = movie_id

    if verbose:
        print(f"  matrix: {matrix.shape[0]:,} users x {matrix.shape[1]:,} items, "
              f"{matrix.nnz:,} nonzero ({time.time() - started:.1f}s)")

    if min_item_ratings > 0:
        support = np.asarray((matrix > 0).sum(axis=0)).ravel()
        keep = support >= min_item_ratings
        if not keep.all():
            if verbose:
                print(f"  dropping {int((~keep).sum()):,} items with "
                      f"< {min_item_ratings} ratings")
            matrix = matrix[:, keep]
            item_ids = item_ids[keep]

    return matrix.tocsc(), item_ids


def compute_neighbours(matrix, item_ids, n_neighbours=60, shrinkage=10.0, verbose=True):
    """
    Cosine similarity with significance shrinkage; keeps the top N per item.

    Returns a list of (movie_id, neighbour_id, similarity, rank) tuples.
    """
    n_items = matrix.shape[1]
    if verbose:
        print(f"\nComputing {n_items:,} x {n_items:,} item similarities ...")
    started = time.time()

    # L2-normalise each item column so a dot product IS cosine similarity.
    norms = np.sqrt(np.asarray(matrix.multiply(matrix).sum(axis=0)).ravel())
    norms[norms == 0] = 1.0
    normalised = matrix.multiply(sparse.csr_matrix(1.0 / norms)).tocsc()

    similarity = (normalised.T @ normalised).tocsr()
    if verbose:
        print(f"  cosine: {similarity.nnz:,} nonzero pairs "
              f"({time.time() - started:.1f}s)")

    binary = matrix.copy()
    binary.data = np.ones_like(binary.data)
    co_counts = (binary.T @ binary).tocsr()
    if verbose:
        print(f"  co-occurrence done ({time.time() - started:.1f}s)")

    similarity = similarity.tocoo()
    counts = np.asarray(co_counts[similarity.row, similarity.col]).ravel()
    shrunk = similarity.data * (counts / (counts + shrinkage))
    similarity = sparse.csr_matrix(
        (shrunk, (similarity.row, similarity.col)), shape=(n_items, n_items)
    )
    similarity.setdiag(0)  # an item is not its own neighbour
    similarity.eliminate_zeros()
    if verbose:
        print(f"  shrinkage applied ({time.time() - started:.1f}s)")

    records = []
    for i in range(n_items):
        start, end = similarity.indptr[i], similarity.indptr[i + 1]
        if start == end:
            continue
        cols = similarity.indices[start:end]
        vals = similarity.data[start:end]

        if len(vals) > n_neighbours:
            # argpartition is O(n) where a full sort is O(n log n); only the
            # retained slice needs ordering and it is tiny.
            top = np.argpartition(-vals, n_neighbours)[:n_neighbours]
            cols, vals = cols[top], vals[top]

        for rank, pos in enumerate(np.argsort(-vals)):
            if vals[pos] <= 0:
                continue
            records.append(
                (int(item_ids[i]), int(item_ids[cols[pos]]), float(vals[pos]), rank)
            )

    if verbose:
        print(f"  {len(records):,} neighbour rows ({time.time() - started:.1f}s total)")
    return records


def records_to_neighbour_map(records):
    """(movie, neighbour, sim, rank) tuples -> {movie: [(neighbour, sim), ...]}."""
    neighbours = {}
    for movie_id, neighbour_id, similarity, _rank in records:
        neighbours.setdefault(movie_id, []).append((neighbour_id, similarity))
    return neighbours
