import requests
from datetime import datetime
from app import db
from app.models.models import Movie, Genre, MoviesGenres, Actor, MoviesActors, Crew, MoviesCrew
import time
from flask import Blueprint, request, jsonify

API_KEY = 'ddfbd71a6d0caa560e3a1f793b91aa5f'
BASE_URL = "https://api.themoviedb.org/3"

def fetch_with_retry(url, params, retries=3, backoff_factor=1):
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=10)  # Set a timeout
            response.raise_for_status()  # Raise an error for HTTP codes >= 400
            return response
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                wait = backoff_factor * (2 ** attempt)  # Exponential backoff
                print(f"Error: {e}. Retrying in {wait} seconds...")
                time.sleep(wait)
            else:
                raise

def fetch_movies(year_start, year_end, page=1):
    url = f"{BASE_URL}/discover/movie"
    params = {
        "api_key": API_KEY,
        "language": "en-US",
        "sort_by": "vote_average.desc",
        "primary_release_date.gte": f"{year_start}-01-01",
        "primary_release_date.lte": f"{year_end}-12-31",
        "vote_count.gte": 2000 if year_end <= 2022 else 500,
        "vote_average.gte": 6,
        "page": page
    }
    response = fetch_with_retry(url, params=params)
    return response.json()

def get_movie_id_by_name(name):
    url = f"{BASE_URL}/search/movie"
    params = {"api_key": API_KEY, "query": name, "language": "en-US"}
    response = fetch_with_retry(url, params=params)
    data = response.json()
    results = data.get('results')
    if results:
        return results[0]['id']  # return the top result
    return None

def fetch_movie_details(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {"api_key": API_KEY, "language": "en-US"}
    response = fetch_with_retry(url, params=params)
    return response.json()

def fetch_credits(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}/credits"
    params = {"api_key": API_KEY}
    response = fetch_with_retry(url, params=params)
    return response.json()

def populate_movies(session, movie):
    new_movie = Movie(
        movie_id=movie['id'],
        title=movie['title'],
        original_title=movie['original_title'],
        budget=movie.get('budget', 0),
        original_language=movie['original_language'],
        release_date=datetime.strptime(movie['release_date'], '%Y-%m-%d').date(),
        revenue=movie.get('revenue', 0),
        runtime=movie.get('runtime', 0),
        overview=movie.get('overview', 'No Overview'),
        production_companies=', '.join([c['name'] for c in movie.get('production_companies', [])]),
        production_countries=', '.join([c['name'] for c in movie.get('production_countries', [])]),
        rating_avg=movie['vote_average'],
        rating_count=movie['vote_count'],
        country=', '.join([c['name'] for c in movie.get('production_countries', [])]),
        backdrop_path=movie.get('backdrop_path', 'Backdrop is not available'),
        poster_path=movie.get('poster_path', 'Poster is not available'),
        adult=movie['adult']
    )
    session.merge(new_movie)  # INSERT OR UPDATE



def populate_genres(session, movie):
    for genre in movie.get('genres', []):
        genre_obj = Genre(genre_id=genre['id'], genre_name=genre['name'])
        session.merge(genre_obj)

        movie_genre = MoviesGenres(movie_id=movie['id'], genre_id=genre['id'])
        session.merge(movie_genre)


def populate_actors_and_crew(session, credits, movie_id):
    for cast in credits.get('cast', []):
        actor = Actor(
            actor_id=cast['id'],
            actor_name=cast['name'],
            character_name=cast.get('character', 'Unknown')
        )
        session.merge(actor)

        movie_actor = MoviesActors(movie_id=movie_id, actor_id=cast['id'])
        session.merge(movie_actor)

    for crew in credits.get('crew', []):
        if crew['job'] in ['Director', 'Producer', 'Writer']:
            crew_member = Crew(
                crew_id=crew['id'],
                crew_name=crew['name'],
                job_title=crew['job']
            )
            session.merge(crew_member)

            movie_crew = MoviesCrew(movie_id=movie_id, crew_id=crew['id'])
            session.merge(movie_crew)
