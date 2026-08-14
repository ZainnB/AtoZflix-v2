"""
Offline item-item collaborative filtering build.

WHY THIS IS A SEPARATE OFFLINE JOB
----------------------------------
The first version of this built the item-item matrix inside the Flask process on
a cache miss. At 1,500 movies and ~28k interactions that took 0.88 seconds and
was completely reasonable. At 25M ratings it is not: accumulating co-occurrence
in Python is O(sum of k^2 over users), which at these volumes runs for hours and
would have to run in every gunicorn worker independently.

So the computation moved here and changed shape. Instead of nested Python loops
it is one sparse matrix multiplication - `X.T @ X` over a CSR matrix computes
every co-occurring pair at once in compiled code. What took hours takes seconds.

The output is written to the Item_Similarity table. The web process then never
builds anything: it reads precomputed neighbour lists. That means numpy/scipy
are a BUILD dependency, not a runtime one - the API still runs on the original
requirements.txt, every worker shares one consistent model, and a cold start is
an indexed query instead of a multi-hour computation.

THE MATH
--------
Let X be the (users x items) preference matrix, columns L2-normalised.

    S = X.T @ X                     cosine similarity between every item pair
    C = B.T @ B                     co-occurrence counts (B = X binarised)
    S = S * C / (C + shrinkage)     significance shrinkage

Shrinkage is what stops two obscure films sharing a single enthusiastic user
from scoring a perfect 1.0 and outranking pairs backed by thousands.

Only positive preferences build the matrix - see the recommender module for why
cosine over signed ratings makes mutually-disliked films look similar.

Usage:
    python build_similarity.py
    python build_similarity.py --neighbours 80 --shrinkage 10 --min-ratings 20
"""

import argparse
import time

from sqlalchemy import text

from app import create_app, db
from app.models.models import ItemSimilarity
from app.utils.cf_builder import (
    compute_neighbours, load_interaction_arrays, matrix_from_arrays,
)

DEFAULT_NEIGHBOURS = 60
DEFAULT_SHRINKAGE = 10.0
DEFAULT_MIN_RATINGS = 10
BATCH = 20000




def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--neighbours", type=int, default=DEFAULT_NEIGHBOURS)
    parser.add_argument("--shrinkage", type=float, default=DEFAULT_SHRINKAGE)
    parser.add_argument("--min-ratings", type=int, default=DEFAULT_MIN_RATINGS)
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        print("=" * 70)
        print("Item-item collaborative filtering build (offline)")
        print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"neighbours={args.neighbours} shrinkage={args.shrinkage} "
              f"min_ratings={args.min_ratings}")
        print("=" * 70)
        db.create_all()

        print("Loading interactions ...")
        rows, cols, vals, user_keys, item_ids = load_interaction_arrays(db.session)
        if rows is None:
            print("No interactions found. Run import_movielens.py first.")
            return

        matrix, item_ids = matrix_from_arrays(
            rows, cols, vals, len(user_keys), len(item_ids),
            min_item_ratings=args.min_ratings, item_ids=item_ids,
        )
        if matrix.shape[1] == 0:
            print("No items survived the min-ratings filter.")
            return

        records = compute_neighbours(
            matrix, item_ids, n_neighbours=args.neighbours, shrinkage=args.shrinkage
        )

        print("\nWriting Item_Similarity ...")
        started = time.time()
        db.session.execute(text("DELETE FROM Item_Similarity"))
        db.session.commit()

        insert_sql = text(
            "INSERT INTO Item_Similarity (movie_id, neighbour_id, similarity, rank) "
            "VALUES (:m, :n, :s, :r)"
        )
        for offset in range(0, len(records), BATCH):
            chunk = records[offset:offset + BATCH]
            db.session.execute(insert_sql, [
                {"m": m, "n": n, "s": s, "r": r} for m, n, s, r in chunk
            ])
            db.session.commit()

        total = db.session.query(ItemSimilarity).count()
        covered = db.session.execute(text(
            "SELECT COUNT(DISTINCT movie_id) FROM Item_Similarity"
        )).scalar()
        print(f"  wrote {total:,} rows in {time.time() - started:.1f}s")
        print(f"  {covered:,} movies have neighbours")
        print("\nDone. The API will pick this up on its next model refresh.")


if __name__ == "__main__":
    main()
