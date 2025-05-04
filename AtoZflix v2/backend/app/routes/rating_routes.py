from app.models.models import Rating, Movie, User
from app import db
from flask import Blueprint, request, jsonify
from sqlalchemy import func, desc
from datetime import datetime, timedelta

rating_bp = Blueprint('rating', __name__)

# get raings for a movie from user
@rating_bp.route('/api/rate_movie', methods=['POST'])
def rate_movie():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        movie_id = data.get('movie_id')
        rating = data.get('rating')
        review = data.get('review', '')

        # Validate input
        if not user_id or not movie_id or rating is None:
            return jsonify({"status": "error", "message": "Missing required fields"}), 400
        if not (0 <= rating <= 10):
            return jsonify({"status": "error", "message": "Rating must be between 0 and 10"}), 400

        # Check if rating already exists
        existing_rating = Rating.query.filter_by(user_id=user_id, movie_id=movie_id).first()

        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating
            existing_rating.review = review
            message = "Rating updated successfully"
        else:
            # Create new rating
            new_rating = Rating(user_id=user_id, movie_id=movie_id, rating=rating, review=review)
            db.session.add(new_rating)
            message = "Rating added successfully"

        # Commit rating change
        db.session.commit()

        # Recalculate and update the movie's average rating
        avg_rating = db.session.query(func.avg(Rating.rating))\
            .filter(Rating.movie_id == movie_id).scalar()

        movie = Movie.query.get(movie_id)
        if movie:
            movie.rating_avg = round(avg_rating, 2)
            db.session.commit()

        return jsonify({"status": "success", "message": message}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    

@rating_bp.route('/api/get_all_ratings', methods=['GET'])
def get_all_ratings():
    try:
        ratings = db.session.query(Rating).join(User).join(Movie).all()
        if ratings:
            ratings_list = []
            for r in ratings:
                ratings_list.append({
                    "rating_id": r.rating_id,
                    "rating": r.rating,
                    "review": r.review,
                    "user_id": r.user_id,
                    "username": r.user.username,
                    "movie_id": r.movie_id,
                    "movie_title": r.movie.title
                })
            return jsonify({"status": "success", "ratings": ratings_list}), 200
        return jsonify({"status": "success", "message": "No ratings found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    