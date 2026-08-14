"""
Offline evaluation of the AtoZFlix recommender.

PROTOCOL
--------
Leave-one-out with a temporal split, the standard top-N recommendation protocol
and a stricter one than a random split: for every evaluated user, their single
most recent positively-rated film is removed and hidden. Models are trained on
what remains, then each produces a ranked top-K of films that user has never
touched. The question measured is whether the held-out film lands in the top K.

The temporal part matters. A random split lets the model train on a user's
future behaviour to predict their past, which inflates every metric and
describes no situation that exists in production.

NO LEAKAGE
----------
The collaborative model is rebuilt here from the training split alone. It does
NOT read the Item_Similarity table, because that matrix is built over all data
including the held-out interactions - using it would leak the answers and report
a hit rate that production could never reproduce. This is why the scipy build
lives in `app/utils/cf_builder.py` and is shared between this harness and
`build_similarity.py`: the two must compute the same thing from different data.

METRICS
-------
HitRate@K   fraction of users whose held-out film appears in their top-K.
            With exactly one held-out item this equals Recall@K.
Precision@K HitRate@K / K - mechanically small when only one item can be
            correct; useful only for comparing models to each other.
MRR         mean of 1/rank of the held-out film (0 when missed). Rewards putting
            the right answer near the top, not merely inside the list.
NDCG@K      the same idea with a logarithmic position discount.
Coverage    fraction of the catalog appearing in anyone's recommendations. A
            model that always returns the same 20 blockbusters can post a decent
            hit rate while being useless as a product; coverage exposes that.

BASELINE AND CEILING
--------------------
Every model is compared against a popularity ranker. Popularity is a deceptively
strong baseline on sparse data, and a personalisation model that cannot beat it
is not earning its complexity.

On the synthetic dataset an ORACLE row also appears - a ranker that cheats by
reading the generator's hidden latent factors. It is not a model, it is the
ceiling. Top-N hit rates look alarmingly low in absolute terms (one right answer
among thousands of candidates), so without a ceiling there is no way to tell a
weak model from a hard task. On real data no such ceiling exists, so the row is
absent and the popularity baseline and random-guess reference carry the
interpretation.

Usage:
    DATABASE_URL=sqlite:///movies.db python eval_recommender.py
    python eval_recommender.py --k 20 --sample-users 5000
"""

import argparse
import json
import math
import os
import random
import sys

import numpy as np

from app import create_app, db
from app.models.models import Favorite, MovieLensRating, Rating
from app.utils.cf_builder import (
    compute_neighbours, load_interaction_arrays, matrix_from_arrays,
    records_to_neighbour_map,
)
from app.utils.recommender import (
    CollaborativeModel,
    _min_max_normalise,
    apply_popularity_prior,
    build_content_model,
    build_user_profile,
    content_weight_for,
)

DEFAULT_K = 10
DEFAULT_SAMPLE = 3000
MIN_HISTORY = 5
RATING_MIDPOINT = 5.0
LATENT_SIDECAR = "demo_latent.json"
SEED = 42


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def group_by_user(rows, cols, vals, n_users):
    """
    Index the coordinate arrays by user so one user's interactions can be sliced
    without materialising every user's dict.

    Returns (order, start, end) where order sorts the arrays by user and
    positions start[u]:end[u] belong to user code u.
    """
    order = np.argsort(rows, kind="stable")
    sorted_rows = rows[order]
    start = np.searchsorted(sorted_rows, np.arange(n_users), side="left")
    end = np.searchsorted(sorted_rows, np.arange(n_users), side="right")
    return order, start, end


def fetch_holdout_dates(user_keys_by_code, codes):
    """
    Interaction dates for just the sampled users, so the temporal holdout can be
    chosen without loading 15.6M timestamps.
    """
    ml_ids = [user_keys_by_code[c][1] for c in codes if user_keys_by_code[c][0] == "ml"]
    app_ids = [user_keys_by_code[c][1] for c in codes if user_keys_by_code[c][0] == "app"]

    dates = {}

    def chunked(ids, size=900):
        for i in range(0, len(ids), size):
            yield ids[i:i + size]

    for chunk in chunked(ml_ids):
        for uid, mid, when in db.session.query(
            MovieLensRating.ml_user_id, MovieLensRating.movie_id, MovieLensRating.rated_at
        ).filter(MovieLensRating.ml_user_id.in_(chunk)).all():
            if when:
                dates[(("ml", uid), mid)] = when

    for chunk in chunked(app_ids):
        for uid, mid, when in db.session.query(
            Rating.user_id, Rating.movie_id, Rating.rated_at
        ).filter(Rating.user_id.in_(chunk)).all():
            if when:
                dates[(("app", uid), mid)] = when
        for uid, mid, when in db.session.query(
            Favorite.user_id, Favorite.movie_id, Favorite.added_at
        ).filter(Favorite.user_id.in_(chunk)).all():
            if when and dates.get((("app", uid), mid), when) <= when:
                dates[(("app", uid), mid)] = when

    return dates


def held_out_item(user_key, prefs, dates):
    """
    The user's most recent positive interaction, or None if they have none.

    Undated rows fall back to the strongest preference, keeping the choice
    deterministic.
    """
    positives = [(m, p) for m, p in prefs.items() if p > 0]
    if not positives:
        return None
    dated = [(m, dates.get((user_key, m)), p) for m, p in positives]
    with_dates = [d for d in dated if d[1] is not None]
    if with_dates:
        return max(with_dates, key=lambda t: (t[1], t[2]))[0]
    return max(positives, key=lambda kv: kv[1])[0]


# ---------------------------------------------------------------------------
# Oracle (synthetic data only)
# ---------------------------------------------------------------------------

def load_latent():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), LATENT_SIDECAR)
    if not os.path.exists(path):
        return None
    with open(path) as handle:
        raw = json.load(handle)
    return {
        "movie_cluster": {int(k): v for k, v in raw["movie_cluster"].items()},
        "cluster_theme": {int(k): v for k, v in raw["cluster_theme"].items()},
        "user_taste": {
            int(u): {
                "themes": {int(t): v for t, v in data["themes"].items()},
                "clusters": set(data["clusters"]),
            }
            for u, data in raw["user_taste"].items()
        },
    }


def oracle_ranking(latent, user_key, seen, limit):
    """Rank by the generator's true affinity - the achievable ceiling."""
    if not isinstance(user_key, tuple) or user_key[0] != "app":
        return []
    taste = latent["user_taste"].get(user_key[1])
    if not taste:
        return []
    scored = []
    for movie_id, cluster_id in latent["movie_cluster"].items():
        if movie_id in seen:
            continue
        affinity = taste["themes"].get(latent["cluster_theme"][cluster_id], 0.0)
        if cluster_id in taste["clusters"]:
            affinity += 0.9
        scored.append((movie_id, affinity))
    scored.sort(key=lambda kv: kv[1], reverse=True)
    return [m for m, _ in scored[:limit]]


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate(k, sample_size, neighbours, shrinkage):
    app = create_app()
    with app.app_context():
        print("=" * 78)
        print(f"AtoZFlix recommender - offline evaluation (leave-one-out, K={k})")
        print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print("=" * 78)

        print("Loading interactions ...")
        rows, cols, vals, user_keys, item_ids = load_interaction_arrays(db.session)
        if rows is None:
            sys.exit("No interactions found. Import data first.")

        n_users, n_items = len(user_keys), len(item_ids)
        item_id_by_code = {i: int(item_ids[i]) for i in range(n_items)}
        code_by_item_id = {int(m): i for i, m in enumerate(item_ids)}

        print("\nBuilding content model ...")
        content_model = build_content_model()
        print(f"  {content_model.size:,} movies, "
              f"{len(content_model.postings):,} distinct features")

        # --- index interactions by user --------------------------------------
        order, start, end = group_by_user(rows, cols, vals, n_users)
        sorted_cols, sorted_vals = cols[order], vals[order]
        history_len = end - start

        eligible = np.flatnonzero(history_len >= MIN_HISTORY + 1)
        rng = random.Random(SEED)
        if sample_size and len(eligible) > sample_size:
            sampled = rng.sample(list(eligible), sample_size)
            print(f"\nEvaluating a random sample of {len(sampled):,} users "
                  f"(of {len(eligible):,} eligible)")
        else:
            sampled = list(eligible)
            print(f"\nEvaluating all {len(sampled):,} eligible users")

        # --- choose the temporal holdout for each sampled user ---------------
        print("Fetching interaction dates for sampled users ...")
        dates = fetch_holdout_dates(user_keys, sampled)

        holdouts = {}
        user_prefs = {}
        for code in sampled:
            lo, hi = start[code], end[code]
            prefs = {
                item_id_by_code[int(sorted_cols[i])]: float(sorted_vals[i])
                for i in range(lo, hi)
            }
            target = held_out_item(user_keys[code], prefs, dates)
            if target is None or len(prefs) <= 1:
                continue
            holdouts[code] = target
            prefs.pop(target, None)
            user_prefs[code] = prefs

        print(f"  held out {len(holdouts):,} interactions")
        if not holdouts:
            sys.exit("No users have enough history to evaluate.")

        # --- CF trained on the train split only ------------------------------
        # The held-out entries are masked out of the coordinate arrays BEFORE
        # the matrix is built, so no held-out interaction can influence any
        # similarity. Reading the precomputed Item_Similarity table instead
        # would leak the answers, which is why this rebuild exists.
        print("\nBuilding collaborative model from the TRAIN split ...")
        holdout_keys = np.array(
            [code * n_items + code_by_item_id[holdouts[code]] for code in holdouts],
            dtype=np.int64,
        )
        all_keys = rows.astype(np.int64) * n_items + cols.astype(np.int64)
        mask = ~np.isin(all_keys, holdout_keys)
        print(f"  masked {int((~mask).sum()):,} held-out interactions "
              f"from {len(vals):,}")

        matrix, _ = matrix_from_arrays(
            rows[mask], cols[mask], vals[mask], n_users, n_items, verbose=False
        )
        records = compute_neighbours(
            matrix, item_ids, n_neighbours=neighbours, shrinkage=shrinkage
        )
        cf_model = CollaborativeModel(records_to_neighbour_map(records), 0, n_items)
        print(f"  {cf_model.size:,} items have neighbours")

        popularity_ranking = sorted(
            content_model.popularity.items(), key=lambda kv: kv[1], reverse=True
        )

        # The oracle only means anything on the synthetic dataset. A stale
        # demo_latent.json left over from a previous synthetic run must not
        # produce a meaningless 0% ceiling row against real data, so the file
        # existing is not enough - its users have to actually be these users.
        latent = load_latent()
        if latent and not any(
            isinstance(user_keys[c], tuple) and user_keys[c][0] == "app"
            and user_keys[c][1] in latent["user_taste"]
            for c in holdouts
        ):
            print("Oracle ceiling: skipped (latent file does not match this dataset)")
            latent = None

        strategies = ["popularity", "content", "collaborative", "hybrid"]
        if latent:
            print("Oracle ceiling: enabled (synthetic latent factors found)")
            strategies.append("ORACLE (ceiling)")

        hits = {s: 0 for s in strategies}
        mrr = {s: 0.0 for s in strategies}
        ndcg = {s: 0.0 for s in strategies}
        recommended = {s: set() for s in strategies}
        evaluated = 0

        print(f"\nScoring {len(holdouts):,} users ...")
        for code, target in holdouts.items():
            user_key = user_keys[code]
            prefs = user_prefs[code]
            seen = set(prefs)

            profile = build_user_profile(content_model, prefs)
            content_scores = content_model.score(profile, exclude=seen) if profile else {}
            content_scores = apply_popularity_prior(
                content_scores, content_model.popularity
            )
            cf_scores = cf_model.score(prefs, exclude=seen)

            alpha = content_weight_for(len(prefs))
            norm_content = _min_max_normalise(content_scores)
            norm_cf = _min_max_normalise(cf_scores)
            hybrid = {
                m: alpha * norm_content.get(m, 0.0) + (1.0 - alpha) * norm_cf.get(m, 0.0)
                for m in set(norm_content) | set(norm_cf)
            }

            ranked = {
                "popularity": [m for m, _ in popularity_ranking if m not in seen][:k],
                "content": [m for m, _ in sorted(
                    content_scores.items(), key=lambda kv: kv[1], reverse=True)][:k],
                "collaborative": [m for m, _ in sorted(
                    cf_scores.items(), key=lambda kv: kv[1], reverse=True)][:k],
                "hybrid": [m for m, _ in sorted(
                    hybrid.items(), key=lambda kv: kv[1], reverse=True)][:k],
            }
            if latent:
                ranked["ORACLE (ceiling)"] = oracle_ranking(latent, user_key, seen, k)

            evaluated += 1
            for strategy, ids in ranked.items():
                recommended[strategy].update(ids)
                if target in ids:
                    position = ids.index(target) + 1
                    hits[strategy] += 1
                    mrr[strategy] += 1.0 / position
                    ndcg[strategy] += 1.0 / math.log2(position + 1)

            if evaluated % 500 == 0:
                print(f"  {evaluated:,}/{len(holdouts):,}")

        catalog_size = max(1, content_model.size)

        print("\n" + "-" * 78)
        print(f"{'Strategy':<18}{'HitRate@K':>11}{'Prec@K':>10}{'MRR':>9}"
              f"{'NDCG@K':>10}{'Coverage':>11}")
        print("-" * 78)
        for strategy in strategies:
            hit_rate = hits[strategy] / evaluated
            print(f"{strategy:<18}{hit_rate:>10.1%}{hit_rate / k:>10.3f}"
                  f"{mrr[strategy] / evaluated:>9.3f}"
                  f"{ndcg[strategy] / evaluated:>10.3f}"
                  f"{len(recommended[strategy]) / catalog_size:>10.1%}")
        print("-" * 78)

        base = hits["popularity"] / evaluated
        ceiling = hits["ORACLE (ceiling)"] / evaluated if latent else None
        random_baseline = k / float(catalog_size)

        print(f"\nUsers evaluated          : {evaluated:,}")
        print(f"Random-guess reference   : {random_baseline:.2%} hit rate "
              f"({k} picks from {catalog_size:,} movies)")

        for strategy in ["content", "collaborative", "hybrid"]:
            rate = hits[strategy] / evaluated
            parts = []
            parts.append(f"{(rate - base) / base:+.0%} vs popularity" if base > 0
                         else "popularity scored 0")
            if random_baseline > 0:
                parts.append(f"{rate / random_baseline:.1f}x random")
            if ceiling:
                parts.append(f"{rate / ceiling:.0%} of oracle ceiling")
            print(f"{strategy:>14}: " + ", ".join(parts))
        print("=" * 78)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--sample-users", type=int, default=DEFAULT_SAMPLE,
                        help="0 evaluates every eligible user (slow at scale)")
    parser.add_argument("--neighbours", type=int, default=60)
    parser.add_argument("--shrinkage", type=float, default=10.0)
    args = parser.parse_args()
    evaluate(args.k, args.sample_users, args.neighbours, args.shrinkage)


if __name__ == "__main__":
    main()
