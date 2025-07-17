from app.models.models import Movie, Country, MoviesCountries
from app import db
from flask import Blueprint, request, jsonify
from sqlalchemy import func

country_bp = Blueprint('country', __name__)

# Get all country names
@country_bp.route('/api/get_country_names', methods=['GET'])
def get_all_country():
    try:
        countries = (
            db.session.query(Country.country_name)
            .order_by(Country.country_name)
            .distinct()
            .all()
        )
        country_list = [name for (name,) in countries]  # Unpack tuples
        return jsonify({'countries': country_list}), 200
    except Exception as e:
        print(f"Error fetching countries: {e}")
        return jsonify({'message': 'Failed to get country names'}), 500

# Given a country, fetch all the movies in the country
@country_bp.route('/api/country', methods=['GET'])
def get_movies_by_country():
    country_name = request.args.get('country', type=str)
    limit = request.args.get('limit', default=10, type=int)

    try:
        # Get country object first
        country = db.session.query(Country).filter_by(country_name=country_name).first()
        if not country:
            return jsonify({"error": "Country not found"}), 404

        # Join tables to get movies linked to the country
        movies = (
            db.session.query(Movie.poster_path, Movie.movie_id)
            .join(MoviesCountries, Movie.movie_id == MoviesCountries.movie_id)
            .filter(MoviesCountries.country_id == country.country_id)
            .limit(limit)
            .all()
        )

        formatted_movies = [
            {"poster_path": poster_path, "movie_id": movie_id}
            for poster_path, movie_id in movies
        ]
        return jsonify({"movies": formatted_movies}), 200
    except Exception as e:
        print(f"Error fetching movies for country {country_name}: {e}")
        return jsonify({"error": "Failed to fetch movies"}), 500

