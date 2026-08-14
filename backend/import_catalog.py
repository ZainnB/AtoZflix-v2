"""
Build the movie catalog: MovieLens chooses the films, TMDb supplies the metadata.

WHY THIS ORDER
--------------
The naive approach is to import "popular movies" from TMDb and then hope
MovieLens has ratings for them. That gets the dependency backwards and leaves a
catalog full of films with no collaborative signal.

Instead MovieLens drives the selection. It is ranked by how many ratings each
film actually has, the top N are taken, `links.csv` maps each MovieLens id to a
TMDb id, and only those films are fetched. Every movie in the catalog is
therefore guaranteed to arrive with real interaction data attached.

The long tail is deliberately cut. MovieLens has 62,423 films but the median has
6 ratings, which is nowhere near enough to compute a similarity from. Taking the
top 5,000 by rating volume covers ~93% of all 25M ratings - almost the entire
signal for a third of the storage and a tenth of the API calls.

THE POST-2019 GAP
-----------------
MovieLens 25M ends in November 2019, so the selection above cannot produce a
single film newer than that - the catalog stops at Joker. That leaves the
"Trending" shelf permanently empty and the product looking abandoned.

`--recent` covers the gap from the other direction: it asks TMDb directly for
well-rated films in a year range and imports them with no MovieLens involvement.
Those films have zero collaborative signal by construction, which is precisely
the case the content-based half of the recommender exists to serve - a film is
recommendable from its metadata the moment it is imported, long before anyone
has interacted with it.

So the catalog ends up in two halves, on purpose:
  * pre-2020: deep collaborative signal, served by the full hybrid
  * post-2020: no interaction history, served by content + popularity prior

Usage:
    python import_catalog.py                       # 5000 MovieLens-ranked films
    python import_catalog.py --limit 2000
    python import_catalog.py --recent --year-start 2020 --year-end 2026
"""

import argparse
import csv
import os
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

from app import create_app, db
from app.models.models import Movie
from app.utils.tmdb_importer import (
    build_session, fetch_movie_bundle, fetch_with_retry, persist_bundle,
)

load_dotenv()

DEFAULT_LIMIT = 5000
DEFAULT_MIN_RATINGS = 50
DEFAULT_WORKERS = 12


def movielens_dir():
    configured = os.getenv("MOVIELENS_DIR", "../ml-25m")
    path = configured if os.path.isabs(configured) else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), configured
    )
    return os.path.normpath(path)


def rank_candidates(ml_dir, limit, min_ratings):
    """
    Count ratings per MovieLens movie, join to TMDb ids, return the top `limit`.

    ratings.csv is 678MB, so it is streamed with the csv module and only a
    counter is kept in memory - never the 25M rows themselves.
    """
    links_path = os.path.join(ml_dir, "links.csv")
    ratings_path = os.path.join(ml_dir, "ratings.csv")
    movies_path = os.path.join(ml_dir, "movies.csv")

    for path in (links_path, ratings_path, movies_path):
        if not os.path.exists(path):
            sys.exit(f"Missing {path}\nSet MOVIELENS_DIR in backend/.env")

    print("Reading links.csv ...")
    ml_to_tmdb = {}
    with open(links_path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            tmdb = row["tmdbId"].strip()
            if tmdb:
                ml_to_tmdb[int(row["movieId"])] = int(tmdb)
    print(f"  {len(ml_to_tmdb):,} MovieLens ids carry a TMDb id")

    print("Reading movies.csv ...")
    titles = {}
    with open(movies_path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            titles[int(row["movieId"])] = row["title"]

    print("Counting ratings per movie (streaming 25M rows, ~30s) ...")
    counts = Counter()
    started = time.time()
    with open(ratings_path, newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        next(reader)  # header
        for row in reader:
            counts[int(row[1])] += 1
    print(f"  counted {sum(counts.values()):,} ratings over {len(counts):,} movies "
          f"in {time.time() - started:.1f}s")

    eligible = [
        (ml_id, ml_to_tmdb[ml_id], n)
        for ml_id, n in counts.items()
        if n >= min_ratings and ml_id in ml_to_tmdb
    ]
    eligible.sort(key=lambda row: row[2], reverse=True)

    # 35 MovieLens rows point at a TMDb id another row already claims (re-releases
    # and duplicate entries). TMDb id is our primary key, so the first - most
    # rated - wins and the rest are dropped.
    seen_tmdb = set()
    selected = []
    for ml_id, tmdb_id, n in eligible:
        if tmdb_id in seen_tmdb:
            continue
        seen_tmdb.add(tmdb_id)
        selected.append((ml_id, tmdb_id, n, titles.get(ml_id, "")))
        if len(selected) >= limit:
            break

    covered = sum(row[2] for row in selected)
    total = sum(counts.values())
    print(f"\nSelected {len(selected):,} movies (>= {min_ratings} ratings each)")
    print(f"  covering {covered:,} of {total:,} ratings ({covered / total:.1%})")
    return selected


def discover_recent(year_start, year_end, limit, session):
    """
    Films TMDb considers well-rated in a year range, newest-first by popularity.

    Used for the post-MovieLens era where no collaborative signal can exist.
    `vote_count.gte` filters out the enormous tail of barely-released titles that
    would otherwise dominate a year query.
    """
    print(f"\nDiscovering TMDb films {year_start}-{year_end} ...")
    found = []
    seen = set()
    page = 1

    while len(found) < limit and page <= 500:
        payload = fetch_with_retry(
            "https://api.themoviedb.org/3/discover/movie",
            params={
                "language": "en-US",
                "sort_by": "popularity.desc",
                "primary_release_date.gte": f"{year_start}-01-01",
                "primary_release_date.lte": f"{year_end}-12-31",
                "vote_count.gte": 200,
                "page": page,
            },
            session=session,
        ).json()

        results = payload.get("results", [])
        if not results:
            break

        for movie in results:
            if movie["id"] not in seen:
                seen.add(movie["id"])
                found.append((None, movie["id"], movie.get("title", "")))

        if page >= payload.get("total_pages", 1):
            break
        page += 1

    print(f"  {len(found):,} candidates across {page} pages")
    return found[:limit]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--min-ratings", type=int, default=DEFAULT_MIN_RATINGS)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--resume", action="store_true",
                        help="skip movies already present in the database")
    parser.add_argument("--recent", action="store_true",
                        help="import recent films from TMDb instead of MovieLens "
                             "selection (covers the post-2019 gap)")
    parser.add_argument("--year-start", type=int, default=2020)
    parser.add_argument("--year-end", type=int, default=2026)
    args = parser.parse_args()

    if not os.getenv("TMDB_ACCESS_TOKEN") and not os.getenv("TMDB_API_KEY"):
        sys.exit("Set TMDB_ACCESS_TOKEN (v4 token) or TMDB_API_KEY in backend/.env")

    session = build_session()

    print("=" * 70)
    if args.recent:
        print(f"Catalog import: recent TMDb films {args.year_start}-{args.year_end}")
        print("(no MovieLens signal by construction - content-based serves these)")
        print("=" * 70)
        selected = None
    else:
        ml_dir = movielens_dir()
        print("Catalog import: MovieLens selection -> TMDb metadata")
        print(f"MovieLens dir: {ml_dir}")
        print("=" * 70)
        selected = rank_candidates(ml_dir, args.limit, args.min_ratings)

    app = create_app()
    with app.app_context():
        print(f"\nDatabase: {app.config['SQLALCHEMY_DATABASE_URI']}")
        db.create_all()

        if args.recent:
            targets = discover_recent(
                args.year_start, args.year_end, args.limit, session
            )
        else:
            targets = [(ml_id, tmdb_id, title) for ml_id, tmdb_id, _n, title in selected]

        if args.resume:
            existing = {mid for (mid,) in db.session.query(Movie.movie_id).all()}
            before = len(targets)
            targets = [t for t in targets if t[1] not in existing]
            print(f"Resume: {before - len(targets):,} already present, "
                  f"{len(targets):,} to fetch")

        if not targets:
            print("Nothing to do.")
            return

        # Fetching is IO-bound, so threads help a lot; writing is not thread-safe
        # on one SQLAlchemy session, so workers only fetch and the main thread
        # does every write.
        lock = threading.Lock()
        progress = {"done": 0, "failed": 0, "skipped": 0}
        started = time.time()

        def fetch(target):
            _ml_id, tmdb_id, title = target
            try:
                return tmdb_id, title, fetch_movie_bundle(tmdb_id, session=session), None
            except Exception as exc:
                return tmdb_id, title, None, exc

        print(f"\nFetching {len(targets):,} movies with {args.workers} workers "
              f"(1 request each via append_to_response) ...")

        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(fetch, t) for t in targets]

            for future in as_completed(futures):
                tmdb_id, title, bundle, error = future.result()

                with lock:
                    progress["done"] += 1
                    n = progress["done"]

                if error is not None:
                    progress["failed"] += 1
                    if progress["failed"] <= 10:
                        print(f"  ! {tmdb_id} {title}: {type(error).__name__}: {error}")
                else:
                    try:
                        if persist_bundle(db.session, bundle):
                            if n % 250 == 0:
                                db.session.commit()
                        else:
                            progress["skipped"] += 1
                    except Exception as exc:
                        db.session.rollback()
                        progress["failed"] += 1
                        if progress["failed"] <= 10:
                            print(f"  ! persist {tmdb_id} {title}: {exc}")

                if n % 250 == 0 or n == len(targets):
                    rate = n / max(1e-9, time.time() - started)
                    remaining = (len(targets) - n) / rate if rate else 0
                    print(f"  {n:>6,}/{len(targets):,}  "
                          f"{rate:>5.1f}/s  eta {remaining / 60:>4.1f}m  "
                          f"failed={progress['failed']} skipped={progress['skipped']}")

        db.session.commit()

        elapsed = time.time() - started
        total = db.session.query(Movie).count()
        print(f"\nDone in {elapsed / 60:.1f} min")
        print(f"  fetched : {progress['done'] - progress['failed']:,}")
        print(f"  failed  : {progress['failed']:,}")
        print(f"  skipped : {progress['skipped']:,} (no release date)")
        print(f"  movies in database: {total:,}")


if __name__ == "__main__":
    main()
