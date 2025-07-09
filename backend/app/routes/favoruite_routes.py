from app.models.models import Favorite,Movie
from app import db
from sqlalchemy.exc import IntegrityError
from flask import Blueprint,request,jsonify, current_app as app
import logging
logging.basicConfig(level=logging.DEBUG)

favourite_bp=Blueprint('favourite',__name__)

@favourite_bp.route('/api/get_favourites', methods=['GET'])
def get_favourites():
    user_id = request.args.get('user_id')
    if not user_id or not user_id.isdigit():
        return jsonify({"status": "error", "message": "Valid User ID is required"}), 400

    user_id = int(user_id)
   
    try:
        favourites = (
            db.session.query(Favorite.movie_id, Movie.poster_path, Favorite.added_at)
            .join(Movie, Favorite.movie_id == Movie.movie_id)
            .filter(Favorite.user_id == user_id)
            .order_by(Favorite.added_at.desc())
            .all()
        )

        result = [
            {
                "movie_id": movie_id,
                "poster_path": poster_path,
                "added_at": added_at
            }
            for movie_id, poster_path, added_at in favourites
        ]

        return jsonify({"status": "success", "favourites": result}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
   

@favourite_bp.route('/api/add_favourite', methods=['POST'])
def add_to_favorites():
    try:
        data = request.get_json()
        app.logger.info(f"Received data: {data}")

        user_id = data.get('user_id')
        movie_id = data.get('movie_id')

        if not user_id or not movie_id:
            return jsonify({"message": "user_id and movie_id are required"}), 400

        # Check if the favorite already exists
        existing_fav = db.session.query(Favorite).filter_by(user_id=user_id, movie_id=movie_id).first()
        if existing_fav:
            return jsonify({"success": False, "message": "Movie is already in favorites"}), 409

        # Add new favorite
        new_fav = Favorite(user_id=user_id, movie_id=movie_id)
        db.session.add(new_fav)
        db.session.commit()

        app.logger.info(f"Movie {movie_id} added to user {user_id}'s favorites.")
        return jsonify({"success": True, "message": "Movie added to favorites"}), 200

    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Integrity error: {str(e)}"}), 409

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
   

@favourite_bp.route('/api/remove_favourite', methods=['POST'])
def remove_from_favorites():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        movie_id = data.get('movie_id')

        if not user_id or not movie_id:
            return jsonify({"message": "user_id and movie_id are required"}), 400

        favorite = db.session.query(Favorite).filter_by(user_id=user_id, movie_id=movie_id).first()
        if favorite:
            db.session.delete(favorite)
            db.session.commit()
            return jsonify({"success": True, "message": "Movie removed from favorites"}), 200
        else:
            return jsonify({"success": False, "message": "Favorite not found"}), 404

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
 
@favourite_bp.route('/api/check_favourite', methods=['GET'])
def check_favorite():
    try:
        user_id = request.args.get('user_id')
        movie_id = request.args.get('movie_id')

        if not user_id or not movie_id:
            return jsonify({"message": "user_id and movie_id are required"}), 400

        exists = db.session.query(Favorite).filter_by(user_id=user_id, movie_id=movie_id).first() is not None

        return jsonify({"is_favourite": exists}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
  
