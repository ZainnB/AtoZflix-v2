"""
Load MovieLens 25M ratings for movies already present in the catalog.

Run AFTER import_catalog.py - this only keeps ratings for films that exist
locally, because a rating pointing at a movie we never imported is dead weight.

WHAT GETS FILTERED, AND WHY
---------------------------
25M ratings will not fit comfortably in SQLite, and are far more than the
collaborative model needs. Two filters cut it down without losing signal:

  * movie must be in our catalog (mapped MovieLens id -> TMDb id via links.csv)
  * user must have at least MIN_USER_RATINGS ratings inside that catalog

The second filter is the important one. A user with three ratings contributes
almost nothing to item-item similarity but still costs a row in every
co-occurrence pass. Dropping them sharpens the matrix and shrinks it at once.
Users are then sampled to --max-users, taking the most active first.

Ratings are rescaled from MovieLens' 0.5-5.0 half-star scale to this project's
0-10 integer scale by doubling - exact, no rounding loss.

Rows land in MovieLens_Ratings, never in Ratings: these are reference data, not
users of this application. See the model docstring for the full reasoning.

Usage:
    python import_movielens.py
    python import_movielens.py --max-users 40000 --min-user-ratings 20
"""

import argparse
import csv
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import text

from app import create_app, db
from app.models.models import Movie, MovieLensRating

load_dotenv()

DEFAULT_MAX_USERS = 40000
DEFAULT_MIN_USER_RATINGS = 15
BATCH = 50000


def movielens_dir():
    configured = os.getenv("MOVIELENS_DIR", "../ml-25m")
    path = configured if os.path.isabs(configured) else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), configured
    )
    return os.path.normpath(path)


def load_link_map(ml_dir, catalog_ids):
    """MovieLens movieId -> TMDb id, restricted to films we actually imported."""
    mapping = {}
    with open(os.path.join(ml_dir, "links.csv"), newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            tmdb = row["tmdbId"].strip()
            if not tmdb:
                continue
            tmdb_id = int(tmdb)
            if tmdb_id in catalog_ids:
                mapping[int(row["movieId"])] = tmdb_id
    return mapping


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-users", type=int, default=DEFAULT_MAX_USERS)
    parser.add_argument("--min-user-ratings", type=int, default=DEFAULT_MIN_USER_RATINGS)
    args = parser.parse_args()

    ml_dir = movielens_dir()
    ratings_path = os.path.join(ml_dir, "ratings.csv")
    if not os.path.exists(ratings_path):
        sys.exit(f"Missing {ratings_path}\nSet MOVIELENS_DIR in backend/.env")

    app = create_app()
    with app.app_context():
        print("=" * 70)
        print("MovieLens ratings import")
        print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print("=" * 70)
        db.create_all()

        catalog_ids = {mid for (mid,) in db.session.query(Movie.movie_id).all()}
        if not catalog_ids:
            sys.exit("Catalog is empty. Run import_catalog.py first.")
        print(f"Catalog: {len(catalog_ids):,} movies")

        link_map = load_link_map(ml_dir, catalog_ids)
        print(f"Mapped : {len(link_map):,} MovieLens ids into the catalog")

        # --- pass 1: how many in-catalog ratings does each user have? --------
        print("\nPass 1/2: counting per-user in-catalog ratings ...")
        started = time.time()
        user_counts = Counter()
        scanned = 0
        with open(ratings_path, newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            next(reader)
            for row in reader:
                scanned += 1
                if int(row[1]) in link_map:
                    user_counts[int(row[0])] += 1
        print(f"  scanned {scanned:,} rows in {time.time() - started:.1f}s")
        print(f"  {len(user_counts):,} users have >=1 in-catalog rating")

        eligible = [(u, n) for u, n in user_counts.items() if n >= args.min_user_ratings]
        eligible.sort(key=lambda kv: kv[1], reverse=True)
        keep_users = {u for u, _ in eligible[:args.max_users]}

        kept_ratings = sum(n for u, n in eligible[:args.max_users])
        print(f"  {len(eligible):,} users clear the >={args.min_user_ratings} threshold")
        print(f"  keeping top {len(keep_users):,} users -> ~{kept_ratings:,} ratings")

        # --- pass 2: stream the rows we decided to keep ----------------------
        print("\nPass 2/2: inserting ...")
        db.session.execute(text("DELETE FROM MovieLens_Ratings"))
        db.session.commit()

        # Raw executemany rather than ORM objects: constructing millions of
        # model instances is dominated by Python object overhead, and there is
        # no business logic to run on the way in.
        insert_sql = text(
            "INSERT OR IGNORE INTO MovieLens_Ratings "
            "(ml_user_id, movie_id, rating, rated_at) VALUES (:u, :m, :r, :d)"
        )
        if not db.engine.dialect.name == "sqlite":
            insert_sql = text(
                "INSERT INTO MovieLens_Ratings "
                "(ml_user_id, movie_id, rating, rated_at) VALUES (:u, :m, :r, :d)"
            )

        started = time.time()
        inserted = 0
        batch = []
        with open(ratings_path, newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            next(reader)
            for row in reader:
                user_id = int(row[0])
                if user_id not in keep_users:
                    continue
                movie_id = link_map.get(int(row[1]))
                if movie_id is None:
                    continue

                batch.append({
                    "u": user_id,
                    "m": movie_id,
                    # 0.5-5.0 half stars -> 1-10 integer. Exact.
                    "r": int(float(row[2]) * 2),
                    "d": datetime.utcfromtimestamp(int(row[3])).date(),
                })

                if len(batch) >= BATCH:
                    db.session.execute(insert_sql, batch)
                    db.session.commit()
                    inserted += len(batch)
                    batch.clear()
                    rate = inserted / max(1e-9, time.time() - started)
                    print(f"  {inserted:>10,} rows  {rate:>8,.0f}/s")

        if batch:
            db.session.execute(insert_sql, batch)
            db.session.commit()
            inserted += len(batch)

        elapsed = time.time() - started
        total = db.session.query(MovieLensRating).count()
        distinct_users = db.session.execute(
            text("SELECT COUNT(DISTINCT ml_user_id) FROM MovieLens_Ratings")
        ).scalar()
        distinct_movies = db.session.execute(
            text("SELECT COUNT(DISTINCT movie_id) FROM MovieLens_Ratings")
        ).scalar()

        print(f"\nInserted {inserted:,} rows in {elapsed / 60:.1f} min")
        print(f"  rows in table  : {total:,}")
        print(f"  distinct users : {distinct_users:,}")
        print(f"  distinct movies: {distinct_movies:,}")
        density = total / max(1, distinct_users * distinct_movies)
        print(f"  matrix density : {density:.3%}")


if __name__ == "__main__":
    main()
