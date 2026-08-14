"""
Backfill headshot paths for actors and crew already in the catalog.

WHY A SEPARATE PASS
-------------------
`profile_path` was added to Actors/Crew after the catalog had already been
imported, so 45,009 actors exist with no headshot. Fetching TMDb's /person
endpoint per actor would be 45,009 requests.

Movie credits carry `profile_path` for every cast and crew member, so
re-fetching the 6,486 movies we already have updates every person in one pass -
roughly seven people per request instead of one. At ~25 movies/sec that is about
four minutes for the whole catalog.

Biography, birthday and place of birth are NOT fetched here. Those only exist on
the per-person endpoint, so they are fetched lazily the first time somebody opens
an actor's page and cached on the row from then on (see actor_routes.py).

Usage:
    python backfill_people.py
    python backfill_people.py --workers 12
"""

import argparse
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from sqlalchemy import text

from app import create_app, db
from app.models.models import Actor, Crew, Movie
from app.utils.tmdb_importer import build_session, fetch_with_retry, BASE_URL

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        print("=" * 70)
        print("Backfilling headshots from movie credits")
        print("=" * 70)
        db.create_all()

        movie_ids = [m for (m,) in db.session.query(Movie.movie_id).all()]
        print(f"Movies to scan: {len(movie_ids):,}")

        missing_actors = db.session.query(Actor).filter(
            Actor.profile_path.is_(None)
        ).count()
        print(f"Actors without a headshot: {missing_actors:,}")

        session = build_session()
        lock = threading.Lock()
        # Collected in memory then written once: 45k individual UPDATEs through
        # the ORM would be far slower than one executemany per batch.
        actor_updates = {}
        crew_updates = {}
        done = {"n": 0, "failed": 0}
        started = time.time()

        def fetch(movie_id):
            try:
                data = fetch_with_retry(
                    f"{BASE_URL}/movie/{movie_id}/credits", session=session
                ).json()
                return data, None
            except Exception as exc:
                return None, exc

        print(f"\nFetching credits with {args.workers} workers ...")
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(fetch, mid) for mid in movie_ids]
            for future in as_completed(futures):
                data, error = future.result()
                with lock:
                    done["n"] += 1
                    n = done["n"]
                    if error is not None:
                        done["failed"] += 1
                    else:
                        for person in (data.get("cast") or []):
                            if person.get("profile_path"):
                                actor_updates[person["id"]] = (
                                    person["profile_path"], person.get("popularity")
                                )
                        for person in (data.get("crew") or []):
                            if person.get("profile_path"):
                                crew_updates[person["id"]] = person["profile_path"]

                if n % 500 == 0 or n == len(movie_ids):
                    rate = n / max(1e-9, time.time() - started)
                    print(f"  {n:>6,}/{len(movie_ids):,}  {rate:>5.1f}/s  "
                          f"actors={len(actor_updates):,} crew={len(crew_updates):,} "
                          f"failed={done['failed']}")

        print(f"\nWriting {len(actor_updates):,} actor rows ...")
        rows = [{"i": k, "p": v[0], "pop": v[1]} for k, v in actor_updates.items()]
        for offset in range(0, len(rows), 5000):
            db.session.execute(
                text("UPDATE Actors SET profile_path = :p, popularity = :pop "
                     "WHERE actor_id = :i"),
                rows[offset:offset + 5000],
            )
            db.session.commit()

        print(f"Writing {len(crew_updates):,} crew rows ...")
        rows = [{"i": k, "p": v} for k, v in crew_updates.items()]
        for offset in range(0, len(rows), 5000):
            db.session.execute(
                text("UPDATE Crew SET profile_path = :p WHERE crew_id = :i"),
                rows[offset:offset + 5000],
            )
            db.session.commit()

        with_photo = db.session.query(Actor).filter(
            Actor.profile_path.isnot(None)
        ).count()
        total = db.session.query(Actor).count()
        print(f"\nDone in {(time.time() - started) / 60:.1f} min")
        print(f"  actors with a headshot: {with_photo:,}/{total:,} "
              f"({with_photo / max(1, total):.0%})")


if __name__ == "__main__":
    main()
