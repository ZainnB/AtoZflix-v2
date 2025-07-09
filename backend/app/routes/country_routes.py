from app.models.models import Movie
from app import db
from flask import Blueprint, request, jsonify
from sqlalchemy import func

country_bp = Blueprint('country', __name__)

# Get all country names
@country_bp.route('/api/get_country_names',methods=['GET'])
def get_all_country():

    try:
        countries=(
            db.session.query(Movie.country).distinct().all()
        )
        country_list=[country[0] for country in countries] # Flattening tuples into list
        return jsonify({'countries':country_list}),200
    except Exception as e:
        return jsonify({'message':'Failed to get country names'}),500
    

# Given a country, fetch all the movies in the country
@country_bp.route('/api/country',methods=['GET'])
def get_movies_by_country():
    country=request.args.get('country',type=str)
    limit=request.args.get('limit',default=10,type=int)

    try:
        movies =(
            db.session.query(Movie.poster_path,Movie.movie_id)
            .filter(Movie.country==country)
            .limit(limit)
            .all()
        )
        formatted_movies = [
            {"poster_path": poster_path, "movie_id": movie_id}
            for poster_path, movie_id in movies
        ]
        return jsonify({"movies": formatted_movies}), 200
    except Exception as e:
        print(f"Error fetching country movies: {e}")
        return jsonify({"error": "Failed to fetch country movies"}), 500
   
