"""
Generate a synthetic catalog + interaction history for evaluating the recommender.

WHY THIS EXISTS
---------------
Offline evaluation needs a user-interaction history. A portfolio deployment does
not have thousands of real users, and the real catalog needs a TMDb key. This
script builds a statistically realistic stand-in so `eval_recommender.py` can be
run by anyone, on any machine, with one command.

The data is SYNTHETIC. It is generated from a latent-factor model, which is the
standard way to produce a dataset where both signals genuinely exist:

  * Movies belong to a broad THEME (gritty-crime, feel-good-comedy, ...) and to a
    tight CLUSTER within it. A cluster stands in for the thing that actually
    drives real taste: a franchise, or a director's body of work. Cluster members
    share a director, several keywords and part of their cast. This is the
    structure content-based filtering is supposed to recover from metadata.

  * Users have a latent taste vector over themes AND an affinity for a handful of
    specific clusters. So a user who watched three films by one director is
    disproportionately likely to watch the fourth - the kind of co-occurrence
    that collaborative filtering is supposed to recover from behaviour alone.

  * Consumption also carries a popularity bias and a noise floor, so neither
    model gets a clean signal.

Crucially the generator never writes the latent vectors into the database tables
the recommender reads. The recommender only sees genres, keywords, cast, crew and
interactions, and has to recover the structure itself. That is what makes the
evaluation meaningful rather than circular.

The latent assignments ARE written to a JSON sidecar next to the database, but
only so that `eval_recommender.py` can compute an oracle upper bound - a ranker
that cheats by reading the ground truth. Without that ceiling there is no way to
tell whether a given hit rate means the model is weak or the task is hard.

THIS SCRIPT DROPS EVERY TABLE
-----------------------------
It calls db.drop_all() before generating, so it must only ever be pointed
at a throwaway database. Run bare, it picks up DATABASE_URL from .env,
which on a development machine is the real catalog - so it refuses unless
the target looks disposable (a SQLite file, or a database named
demo/test/scratch/tmp) or --force is passed explicitly.

Usage:
    python seed_demo_data.py sqlite:///demo.db
    DATABASE_URL=sqlite:///demo.db python seed_demo_data.py
    python seed_demo_data.py --force            # only if you mean it
"""

import argparse
import json
import os
import random
import sys
from datetime import date, timedelta

from app import create_app, db
from app.utils.helpers import safe_database_uri
from app.models.models import (
    Actor,
    Country,
    Crew,
    Favorite,
    Genre,
    Keyword,
    Movie,
    MoviesActors,
    MoviesCountries,
    MoviesCrew,
    MoviesGenres,
    MoviesKeywords,
    Rating,
    User,
    WatchLater,
)

SEED = 42
N_MOVIES = 1500
N_USERS = 800
N_THEMES = 20
N_CLUSTERS = 190       # ~8 movies each: a franchise or a director's filmography
N_KEYWORDS = 600
N_ACTORS = 1400
N_CREW = 260

GENRE_NAMES = [
    "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary",
    "Drama", "Family", "Fantasy", "History", "Horror", "Music", "Mystery",
    "Romance", "Science Fiction", "Thriller", "War", "Western",
]
COUNTRY_NAMES = [
    "United States of America", "United Kingdom", "France", "Japan",
    "South Korea", "India", "Germany", "Canada", "Spain", "Italy",
]
LANGUAGES = ["en", "en", "en", "fr", "ja", "ko", "hi", "de", "es", "it"]

LATENT_SIDECAR = "demo_latent.json"


def weighted_sample(rng, population, weights, k):
    """Sample k distinct items with probability proportional to weights."""
    chosen = []
    pool = list(zip(population, weights))
    total = sum(w for _, w in pool)
    k = min(k, len(pool))
    while len(chosen) < k and pool and total > 0:
        r = rng.random() * total
        upto = 0.0
        for idx, (item, weight) in enumerate(pool):
            upto += weight
            if upto >= r:
                chosen.append(item)
                pool.pop(idx)
                total -= weight
                break
        else:
            break
    return chosen


def build_themes(rng):
    """Broad taste categories: characteristic genres, keyword pool, cast pool."""
    return [
        {
            "genres": rng.sample(range(len(GENRE_NAMES)), rng.randint(2, 4)),
            "keywords": rng.sample(range(N_KEYWORDS), 40),
            "actors": rng.sample(range(N_ACTORS), 90),
            "country": rng.randrange(len(COUNTRY_NAMES)),
            "language": rng.randrange(len(LANGUAGES)),
        }
        for _ in range(N_THEMES)
    ]


def build_clusters(rng, themes):
    """
    Tight groups within a theme - the synthetic equivalent of a franchise or a
    director's filmography. This is where the sharpest predictive signal lives.
    """
    clusters = []
    for cluster_id in range(N_CLUSTERS):
        theme_id = rng.randrange(N_THEMES)
        theme = themes[theme_id]
        clusters.append({
            "theme": theme_id,
            "director": rng.randrange(N_CREW),
            "keywords": rng.sample(theme["keywords"], 6),
            "actors": rng.sample(theme["actors"], 5),
        })
    return clusters


def looks_disposable(uri):
    """
    True when the target is plainly a scratch database.

    SQLite is a file, so a bad guess there costs nothing. A server-hosted
    database is only treated as disposable when its name says so. Anything
    else - including the atozflix_db in a developer .env - is assumed to hold
    real data that took half an hour of TMDb calls and a 678MB CSV to build.
    """
    if not uri:
        return False
    if uri.startswith("sqlite"):
        return True
    name = uri.rsplit("/", 1)[-1].split("?")[0].lower()
    return any(hint in name for hint in ("demo", "test", "scratch", "tmp"))


def seed(database_url=None, force=False):
    rng = random.Random(SEED)

    if database_url:
        os.environ["DATABASE_URL"] = database_url

    app = create_app()
    with app.app_context():
        uri = app.config['SQLALCHEMY_DATABASE_URI']
        safe_uri = safe_database_uri(uri)

        # db.drop_all() below is unconditional and irreversible, so the target
        # has to earn it. This guard exists because the default target is
        # whatever .env says, which is exactly the database you do not want.
        if not force and not looks_disposable(uri):
            sys.exit(
                "\nRefusing to run against: " + safe_uri + "\n"
                "\nThis script calls db.drop_all(), which would destroy every row"
                " in that database - an imported catalog and millions of"
                " MovieLens ratings included.\n"
                "\nPoint it at a throwaway instead:\n"
                "    python seed_demo_data.py sqlite:///demo.db\n"
                "\nor pass --force if you genuinely mean to wipe the one above.\n"
            )

        print(f"Database: {safe_uri}")
        print("Dropping and recreating all tables...")
        db.drop_all()
        db.create_all()

        themes = build_themes(rng)
        clusters = build_clusters(rng, themes)

        # --- reference tables ------------------------------------------------
        for idx, name in enumerate(GENRE_NAMES):
            db.session.add(Genre(genre_id=idx + 1, genre_name=name))
        for idx, name in enumerate(COUNTRY_NAMES):
            db.session.add(Country(country_id=idx + 1, country_name=name))
        for idx in range(N_KEYWORDS):
            db.session.add(Keyword(keyword_id=idx + 1, keyword_name=f"keyword-{idx + 1}"))
        for idx in range(N_ACTORS):
            db.session.add(Actor(actor_id=idx + 1, actor_name=f"Actor {idx + 1}"))
        for idx in range(N_CREW):
            db.session.add(Crew(crew_id=idx + 1, crew_name=f"Crew {idx + 1}",
                                job_title=rng.choice(["Director", "Producer", "Writer"])))
        db.session.commit()
        print(f"  reference rows: {len(GENRE_NAMES)} genres, {N_KEYWORDS} keywords, "
              f"{N_ACTORS} actors, {N_CREW} crew, {len(COUNTRY_NAMES)} countries")

        # --- movies ----------------------------------------------------------
        movie_cluster = {}
        for movie_id in range(1, N_MOVIES + 1):
            cluster_id = rng.randrange(N_CLUSTERS)
            cluster = clusters[cluster_id]
            theme = themes[cluster["theme"]]
            movie_cluster[movie_id] = cluster_id

            release = date(1980, 1, 1) + timedelta(days=rng.randrange(0, 16000))
            # Long-tailed vote counts: a few blockbusters, many small films.
            vote_count = int(rng.paretovariate(1.3) * 400)
            vote_avg = round(min(10.0, max(1.0, rng.gauss(6.6, 1.1))), 1)

            db.session.add(Movie(
                movie_id=movie_id,
                title=f"Movie {movie_id}",
                original_title=f"Movie {movie_id}",
                budget=rng.randrange(1_000_000, 250_000_000),
                original_language=LANGUAGES[theme["language"]],
                release_date=release,
                revenue=rng.randrange(0, 900_000_000),
                runtime=rng.randrange(80, 175),
                overview=f"Synthetic overview for movie {movie_id}.",
                production_companies="Synthetic Studios",
                rating_avg=vote_avg,
                rating_count=vote_count,
                country=COUNTRY_NAMES[theme["country"]],
                backdrop_path=f"/backdrop_{movie_id}.jpg",
                poster_path=f"/poster_{movie_id}.jpg",
                adult=False,
            ))

            # Composite primary keys reject duplicates, so dedupe before insert.
            genre_ids = set(rng.sample(theme["genres"], min(2, len(theme["genres"]))))
            for genre_idx in genre_ids:
                db.session.add(MoviesGenres(movie_id=movie_id, genre_id=genre_idx + 1))

            # Signature keywords from the cluster (strong signal) plus a few from
            # the wider theme (weak signal) plus noise (no signal).
            keyword_ids = set(rng.sample(cluster["keywords"], 4))
            keyword_ids.update(rng.sample(theme["keywords"], 3))
            keyword_ids.update(rng.sample(range(N_KEYWORDS), 2))
            for kw in keyword_ids:
                db.session.add(MoviesKeywords(movie_id=movie_id, keyword_id=kw + 1))

            actor_ids = set(rng.sample(cluster["actors"], 3))
            actor_ids.update(rng.sample(theme["actors"], 4))
            for actor in actor_ids:
                db.session.add(MoviesActors(movie_id=movie_id, actor_id=actor + 1))

            # The cluster's recurring director, plus a rotating second credit.
            crew_ids = {cluster["director"], rng.randrange(N_CREW)}
            for crew in crew_ids:
                db.session.add(MoviesCrew(movie_id=movie_id, crew_id=crew + 1))

            db.session.add(MoviesCountries(movie_id=movie_id, country_id=theme["country"] + 1))

            if movie_id % 300 == 0:
                db.session.commit()
        db.session.commit()
        print(f"  movies: {N_MOVIES} across {N_CLUSTERS} clusters "
              f"(~{N_MOVIES / N_CLUSTERS:.1f} per cluster)")

        # --- users and their histories ---------------------------------------
        popularity = dict(
            db.session.query(Movie.movie_id, Movie.rating_count).all()
        )
        max_pop = max(popularity.values()) or 1

        movies_in_cluster = {}
        for movie_id, cluster_id in movie_cluster.items():
            movies_in_cluster.setdefault(cluster_id, []).append(movie_id)

        latent = {"movie_cluster": {}, "cluster_theme": {}, "user_taste": {}}
        for movie_id, cluster_id in movie_cluster.items():
            latent["movie_cluster"][str(movie_id)] = cluster_id
        for cluster_id, cluster in enumerate(clusters):
            latent["cluster_theme"][str(cluster_id)] = cluster["theme"]

        n_ratings = n_favs = n_watch = 0
        for user_id in range(1, N_USERS + 1):
            db.session.add(User(
                user_id=user_id,
                email=f"user{user_id}@example.com",
                username=f"user{user_id}",
                password="synthetic-not-a-real-hash",
                role="user",
            ))

            # Latent taste: a couple of loved themes, plus a few beloved clusters
            # inside them (the "I watch everything this director makes" effect).
            loved_themes = rng.sample(range(N_THEMES), rng.randint(2, 3))
            theme_taste = {t: (0.80 if t in loved_themes else rng.uniform(0.0, 0.15))
                           for t in range(N_THEMES)}
            candidate_clusters = [c for c in range(N_CLUSTERS)
                                  if clusters[c]["theme"] in loved_themes]
            loved_clusters = set(rng.sample(
                candidate_clusters, min(len(candidate_clusters), rng.randint(3, 6))
            )) if candidate_clusters else set()

            latent["user_taste"][str(user_id)] = {
                "themes": {str(t): round(v, 4) for t, v in theme_taste.items()},
                "clusters": sorted(loved_clusters),
            }

            history_size = min(140, max(6, int(rng.paretovariate(1.5) * 22)))

            candidates = []
            weights = []
            for movie_id, cluster_id in movie_cluster.items():
                theme_id = clusters[cluster_id]["theme"]
                affinity = theme_taste[theme_id]
                if cluster_id in loved_clusters:
                    affinity += 0.9
                pop_bias = 0.20 * (popularity[movie_id] / max_pop)
                candidates.append(movie_id)
                weights.append(max(0.001, affinity + pop_bias + 0.03))

            watched = weighted_sample(rng, candidates, weights, history_size)

            for movie_id in watched:
                cluster_id = movie_cluster[movie_id]
                theme_id = clusters[cluster_id]["theme"]
                affinity = theme_taste[theme_id] + (0.4 if cluster_id in loved_clusters else 0.0)
                affinity = min(1.0, affinity)
                # Rating reflects affinity plus noise, clipped to the 0-10 scale.
                score = int(round(min(10, max(0, rng.gauss(2.5 + 7.5 * affinity, 1.5)))))
                when = date.today() - timedelta(days=rng.randrange(0, 900))

                roll = rng.random()
                if roll < 0.65:
                    db.session.add(Rating(user_id=user_id, movie_id=movie_id,
                                          rating=score, review="", rated_at=when))
                    n_ratings += 1
                if affinity > 0.6 and roll < 0.45:
                    db.session.add(Favorite(user_id=user_id, movie_id=movie_id, added_at=when))
                    n_favs += 1
                elif roll > 0.88:
                    db.session.add(WatchLater(user_id=user_id, movie_id=movie_id, added_at=when))
                    n_watch += 1

            if user_id % 100 == 0:
                db.session.commit()
        db.session.commit()

        total = n_ratings + n_favs + n_watch
        print(f"  users: {N_USERS}")
        print(f"  interactions: {n_ratings} ratings, {n_favs} favourites, "
              f"{n_watch} watch-later ({total} total)")
        density = total / float(N_USERS * N_MOVIES)
        print(f"  matrix density: {density:.4%}  (MovieLens-100k sits around 6%)")

        sidecar = os.path.join(os.path.dirname(os.path.abspath(__file__)), LATENT_SIDECAR)
        with open(sidecar, "w") as handle:
            json.dump(latent, handle)
        print(f"  latent ground truth -> {LATENT_SIDECAR} (oracle bound only)")
        print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "database_url", nargs="?", default=None,
        help="SQLAlchemy URL to seed, e.g. sqlite:///demo.db. Defaults to "
             "DATABASE_URL from the environment.",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="drop and reseed even when the target does not look disposable",
    )
    args = parser.parse_args()
    seed(args.database_url, force=args.force)
