"""
TMDb ingestion.

Authentication supports both of TMDb's schemes:
  * v4 read access token  -> Authorization: Bearer <token>   (TMDB_ACCESS_TOKEN)
  * v3 API key            -> ?api_key=<key>                  (TMDB_API_KEY)
Bearer is preferred when both are set.

The single most important call here is `fetch_movie_bundle`, which uses TMDb's
`append_to_response` to return details, credits and keywords in ONE request
instead of three. Over a 5,000 film import that is 5,000 requests instead of
15,000 - a third of the wall time and a third of the rate-limit budget.
"""

import os
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

from app import db
from app.models.models import (
    Actor, Country, Crew, Genre, Keyword, Movie, MoviesActors, MoviesCountries,
    MoviesCrew, MoviesGenres, MoviesKeywords,
)

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")
ACCESS_TOKEN = os.getenv("TMDB_ACCESS_TOKEN")
BASE_URL = "https://api.themoviedb.org/3"

# TMDb returns every credited performer - 145 for Forrest Gump. Past the top of
# the bill these are noise: they dilute the content-based similarity vectors and
# add ~130 junction rows per film for no signal. Keep the billed leads.
CAST_LIMIT = 15
CREW_JOBS = ("Director", "Writer", "Screenplay", "Producer")
CREW_LIMIT = 8


def _auth_headers():
    if ACCESS_TOKEN:
        return {"accept": "application/json", "Authorization": f"Bearer {ACCESS_TOKEN}"}
    return {"accept": "application/json"}


def _auth_params(params=None):
    params = dict(params or {})
    if not ACCESS_TOKEN and API_KEY:
        params["api_key"] = API_KEY
    return params


def build_session():
    """
    A requests.Session reuses the TCP connection and TLS handshake across calls.
    Over thousands of requests that is a large fraction of total time.
    """
    session = requests.Session()
    session.headers.update(_auth_headers())
    adapter = requests.adapters.HTTPAdapter(pool_connections=32, pool_maxsize=32)
    session.mount("https://", adapter)
    return session


def fetch_with_retry(url, params=None, retries=4, backoff_factor=1, session=None):
    """
    GET with exponential backoff.

    HTTP 429 is handled separately from a generic failure: TMDb sends a
    Retry-After header saying exactly how long to wait, and honouring it is both
    faster and politer than doubling blindly.
    """
    getter = session or requests
    params = _auth_params(params)
    headers = None if session else _auth_headers()

    for attempt in range(retries):
        try:
            response = getter.get(url, params=params, headers=headers, timeout=15)

            if response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 2)) + 1
                time.sleep(wait)
                continue

            response.raise_for_status()
            return response

        except requests.exceptions.RequestException:
            if attempt < retries - 1:
                time.sleep(backoff_factor * (2 ** attempt))
            else:
                raise
    raise requests.exceptions.RetryError(f"exhausted retries for {url}")


def fetch_movie_bundle(movie_id, session=None):
    """Details + credits + keywords in a single round trip."""
    response = fetch_with_retry(
        f"{BASE_URL}/movie/{movie_id}",
        params={"language": "en-US", "append_to_response": "credits,keywords"},
        session=session,
    )
    return response.json()


def fetch_movies(year_start, year_end, page=1, session=None):
    url = f"{BASE_URL}/discover/movie"
    params = {
        "language": "en-US",
        "sort_by": "vote_average.desc",
        "primary_release_date.gte": f"{year_start}-01-01",
        "primary_release_date.lte": f"{year_end}-12-31",
        "vote_count.gte": 2000 if year_end <= 2022 else 500,
        "vote_average.gte": 6,
        "page": page,
    }
    return fetch_with_retry(url, params=params, session=session).json()


def get_movie_id_by_name(name, session=None):
    response = fetch_with_retry(
        f"{BASE_URL}/search/movie",
        params={"query": name, "language": "en-US"},
        session=session,
    )
    results = response.json().get("results")
    return results[0]["id"] if results else None


def fetch_movie_details(movie_id, session=None):
    return fetch_with_retry(
        f"{BASE_URL}/movie/{movie_id}", params={"language": "en-US"}, session=session
    ).json()


def fetch_credits(movie_id, session=None):
    return fetch_with_retry(f"{BASE_URL}/movie/{movie_id}/credits", session=session).json()


def fetch_keywords(movie_id, session=None):
    return fetch_with_retry(f"{BASE_URL}/movie/{movie_id}/keywords", session=session).json()


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def populate_movies(session, movie):
    """
    Upsert one movie. `merge` issues an UPDATE when the PK exists and an INSERT
    otherwise, which is what makes re-running an import idempotent.
    """
    release_date = _parse_date(movie.get("release_date"))
    if release_date is None:
        # release_date is NOT NULL and a film with no date cannot be sorted into
        # "latest" or given a decade feature. Skip rather than write a sentinel.
        return False

    countries = movie.get("production_countries", []) or []

    session.merge(Movie(
        movie_id=movie["id"],
        title=movie.get("title") or movie.get("original_title") or "Untitled",
        original_title=movie.get("original_title") or movie.get("title") or "Untitled",
        budget=movie.get("budget") or 0,
        original_language=movie.get("original_language") or "en",
        release_date=release_date,
        revenue=movie.get("revenue") or 0,
        runtime=movie.get("runtime") or 0,
        overview=movie.get("overview") or "No Overview",
        production_companies=", ".join(
            c["name"] for c in (movie.get("production_companies") or [])
        ),
        rating_avg=movie.get("vote_average") or 0.0,
        rating_count=movie.get("vote_count") or 0,
        country=countries[0]["name"] if countries else "Unknown",
        backdrop_path=movie.get("backdrop_path") or "",
        poster_path=movie.get("poster_path") or "",
        adult=bool(movie.get("adult", False)),
    ))

    for country_data in countries:
        country = session.query(Country).filter_by(country_name=country_data["name"]).first()
        if not country:
            country = Country(country_name=country_data["name"])
            session.add(country)
            session.flush()
        session.merge(MoviesCountries(movie_id=movie["id"], country_id=country.country_id))

    return True


def populate_genres(session, movie):
    for genre in movie.get("genres", []) or []:
        session.merge(Genre(genre_id=genre["id"], genre_name=genre["name"]))
        session.merge(MoviesGenres(movie_id=movie["id"], genre_id=genre["id"]))


def populate_actors_and_crew(session, credits, movie_id):
    """
    Cast is truncated to the top CAST_LIMIT by TMDb's `order` (billing position),
    and the character/billing now live on the junction row where they belong -
    an actor plays a different character in every film.
    """
    cast = sorted(
        (credits.get("cast") or []),
        key=lambda c: c.get("order", 9999),
    )[:CAST_LIMIT]

    for member in cast:
        session.merge(Actor(
            actor_id=member["id"],
            actor_name=member["name"],
            profile_path=member.get("profile_path"),
            popularity=member.get("popularity"),
        ))
        session.merge(MoviesActors(
            movie_id=movie_id,
            actor_id=member["id"],
            character_name=member.get("character") or None,
            billing_order=member.get("order"),
        ))

    seen_crew = set()
    for member in (credits.get("crew") or []):
        if member.get("job") not in CREW_JOBS or member["id"] in seen_crew:
            continue
        if len(seen_crew) >= CREW_LIMIT:
            break
        seen_crew.add(member["id"])
        session.merge(Crew(
            crew_id=member["id"],
            crew_name=member["name"],
            job_title=member["job"],
            profile_path=member.get("profile_path"),
        ))
        session.merge(MoviesCrew(movie_id=movie_id, crew_id=member["id"]))


def fetch_person(person_id, session=None):
    """
    Biography-level detail for one person.

    One request per person, so this is only ever called lazily for an actor
    somebody actually opened - never in bulk across 45,000 actors.
    """
    return fetch_with_retry(
        f"{BASE_URL}/person/{person_id}", params={"language": "en-US"}, session=session
    ).json()


def populate_keywords(session, movie_id, keywords=None):
    """
    `keywords` may be passed in from a bundled response to avoid a second call;
    it is fetched only when absent (the path admin_routes still uses).
    """
    if keywords is None:
        keywords = fetch_keywords(movie_id).get("keywords", [])

    for keyword in keywords or []:
        session.merge(Keyword(keyword_id=keyword["id"], keyword_name=keyword["name"]))
        session.merge(MoviesKeywords(movie_id=movie_id, keyword_id=keyword["id"]))


def persist_bundle(session, bundle):
    """Write one `fetch_movie_bundle` payload across all catalog tables."""
    if not populate_movies(session, bundle):
        return False
    populate_genres(session, bundle)
    populate_actors_and_crew(session, bundle.get("credits", {}) or {}, bundle["id"])
    populate_keywords(session, bundle["id"], (bundle.get("keywords") or {}).get("keywords", []))
    return True
