from app.models.models import User, Movie, Genre, Actor, Crew, MoviesGenres, MoviesActors, MoviesCrew, MoviesKeywords, Favorite, WatchLater, Rating, MovieLog, UserLog
from app import db
from flask import Blueprint, request, jsonify, g
from app.utils.loggers import MovieLog_action, UserLog_action
from app.utils.tmdb_importer import fetch_movies, fetch_movie_details, fetch_with_retry, fetch_credits, populate_movies, populate_genres, populate_actors_and_crew, get_movie_id_by_name, fetch_keywords,populate_keywords
from app.utils.decorators import admin_required, token_required
import os

admin_bp = Blueprint('admin', __name__)

# Get API key from environment variable
API_KEY = os.getenv('TMDB_API_KEY', '')
BASE_URL = "https://api.themoviedb.org/3"

@admin_bp.route('/api/add_single_movie', methods=['POST'])
@token_required
@admin_required
def add_single_movie():
    admin_id = g.current_user.get('user_id')
    movie_name = request.json.get('movie_name')
    if not movie_name:
        return jsonify({'error': 'Movie name is required'}), 400

    try:
        movie_id = get_movie_id_by_name(movie_name)
        if not movie_id:
            return jsonify({'error': 'Movie not found'}), 404
        # Check if the movie already exists in the database
        details = fetch_movie_details(movie_id)

        if db.session.query(Movie).filter_by(movie_id=details['id']).first():
            return jsonify({'error': 'Movie already exists in the database'}), 400

        credits = fetch_credits(details['id'])

        populate_movies(db.session, details)
        populate_genres(db.session, details)
        populate_actors_and_crew(db.session, credits, details['id'])
        populate_keywords(db.session, details['id'])

        MovieLog_action(db.session, admin_id, 'Add', f"Added movie {details['title']} (ID: {details['id']})")
        db.session.commit()

        return jsonify({'message': f"Movie '{details['title']}' added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/update_single_movie', methods=['PUT'])
@token_required
@admin_required
def update_single_movie():
    admin_id = g.current_user.get('user_id')
    movie_name = request.json.get('movie_name')
    if not movie_name:
        return jsonify({'error': 'Movie name is required'}), 400

    try:
        movie_id = get_movie_id_by_name(movie_name)
        if not movie_id:
            return jsonify({'error': 'Movie not found'}), 404
        
        movie = db.session.get(Movie, movie_id)
        if not movie:
            return jsonify({'error': 'Movie does not exist in the database'}), 404

        details = fetch_movie_details(movie_id)
        credits = fetch_credits(movie_id)

        # Update the movie entry
        populate_movies(db.session, details)  # Make sure this uses ORM to update or add
        populate_genres(db.session, details)
        populate_actors_and_crew(db.session, credits, movie_id)
        populate_keywords(db.session, movie_id)

        MovieLog_action(db.session, admin_id, 'Update', f"Updated movie {details['title']} (ID: {movie_id})")

        db.session.commit()
        return jsonify({'message': f"Movie '{details['title']}' updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/delete_single_movie', methods=['DELETE'])
@token_required
@admin_required
def delete_single_movie():
    admin_id = g.current_user.get('user_id')
    movie_name = request.json.get('movie_name')
    if not movie_name:
        return jsonify({'error': 'Movie name is required'}), 400

    try:
        movie_id = get_movie_id_by_name(movie_name)
        if not movie_id:
            return jsonify({'error': 'Movie not found'}), 404
        
        movie = db.session.get(Movie, movie_id)
        if not movie:
            return jsonify({'error': 'Movie does not exist in the database'}), 404

        # Delete all related records via ORM relationships (if cascades not set)
        db.session.query(MoviesActors).filter_by(movie_id=movie_id).delete()
        db.session.query(MoviesCrew).filter_by(movie_id=movie_id).delete()
        db.session.query(MoviesGenres).filter_by(movie_id=movie_id).delete()
        db.session.query(Favorite).filter_by(movie_id=movie_id).delete()
        db.session.query(WatchLater).filter_by(movie_id=movie_id).delete()
        db.session.query(Rating).filter_by(movie_id=movie_id).delete()
        db.session.query(MoviesKeywords).filter_by(movie_id=movie_id).delete()


        db.session.delete(movie)

        MovieLog_action(db.session, admin_id, 'Delete', f"Deleted movie ID: {movie_id}")

        db.session.commit()
        return jsonify({'message': f"Movie with ID '{movie_id}' deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/add_batch_movies', methods=['POST'])
@token_required
@admin_required
def add_batch_movies():
    admin_id = g.current_user.get('user_id')
    year_start = request.json.get('year_start', 2024)
    year_end = request.json.get('year_end', 2024)
    page_start = request.json.get('page_start', 1)
    page_end = request.json.get('page_end', 1)

    try:
        for page in range(page_start, page_end + 1):
            movies = fetch_movies(year_start, year_end, page).get('results', [])
            for movie in movies:
                if not db.session.get(Movie, movie['id']):  # ORM check
                    details = fetch_movie_details(movie['id'])
                    credits = fetch_credits(movie['id'])

                    populate_movies(db.session, details)
                    populate_genres(db.session, details)
                    populate_actors_and_crew(db.session, credits, movie['id'])
                    populate_keywords(db.session, movie['id'])

        MovieLog_action(db.session, admin_id, 'Add', f"Added movies for {year_start}-{year_end}, pages {page_start}-{page_end}")
        db.session.commit()
        return jsonify({'message': f"Movies added successfully for {year_start}-{year_end}, pages {page_start}-{page_end}"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        db.session.close()


@admin_bp.route('/api/update_batch_movies', methods=['PUT'])
@token_required
@admin_required
def update_batch_movies():
    admin_id = g.current_user.get('user_id')
    year_start = request.json.get('year_start', 2024)
    year_end = request.json.get('year_end', 2024)
    page_start = request.json.get('page_start', 1)
    page_end = request.json.get('page_end', 1)

    try:
        for page in range(page_start, page_end + 1):
            movies = fetch_movies(year_start, year_end, page).get('results', [])
            for movie in movies:
                details = fetch_movie_details(movie['id'])
                credits = fetch_credits(movie['id'])

                try:
                    if db.session.get(Movie, movie['id']):  # If exists, update
                        populate_movies(db.session, details)
                        populate_genres(db.session, details)
                        populate_actors_and_crew(db.session, credits, movie['id'])
                        populate_keywords(db.session, movie['id'])
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    raise e

        try:
            MovieLog_action(db.session, admin_id, 'Update', f"Updated movies for {year_start}-{year_end}, pages {page_start}-{page_end}")
            db.session.commit()
            return jsonify({'message': f"Movies updated successfully for {year_start}-{year_end}, pages {page_start}-{page_end}"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Get all users
@admin_bp.route('/api/get_all_users',methods=['GET'])
@token_required
@admin_required
def get_all_users():
    try:
        users=User.query.all()
        if not users:
            return jsonify({'message':'No users exist'}),404
    
        user_list=[{
            'user_id':user.user_id,
            'email':user.email,
            'username':user.username,
            'role':user.role} 
            for  user in users]
        return jsonify(user_list),200
    except Exception as e:
        return jsonify({'message':f'An error occured: {str(e)}'}),500

@admin_bp.route('/api/delete_user', methods=['DELETE'])
@token_required
@admin_required
def delete_user():
    user_id = request.args.get('user_id')
    admin_id = g.current_user.get('user_id')
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    try:
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Prepare old data before deletion
        old_data = {
            "user_id": user.user_id,
            "email": user.email,
            "username": user.username,
            "role": user.role
        }

        # Delete the user
        db.session.delete(user)
        db.session.flush()  # Ensures user is removed before inserting log

        # Log the deletion
        UserLog_action(db.session, admin_id, user_id,'Delete', f"Deleted user {user.username} (ID: {user.user_id})", old_data=old_data)
        db.session.commit()

        return jsonify({"message": "User deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete user: {str(e)}"}), 500


@admin_bp.route('/api/update_user', methods=['PUT'])
@token_required
@admin_required
def update_user():
    data = request.get_json()
    user_id = data.get('user_id')
    username = data.get('username')
    email = data.get('email')
    role = data.get('role')
    admin_id = g.current_user.get('user_id')

    if not user_id or not username or not email or not role:
        return jsonify({"error": "user_id, username, email, and role are required"}), 400

    try:
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        old_data = {
            "user_id": user.user_id,
            "email": user.email,
            "username": user.username,
            "role": user.role
        }

        # Update user
        user.username = username
        user.email = email
        user.role = role

        new_data = {
            "user_id": user_id,
            "email": email,
            "username": username,
            "role": role
        }

        # Log the update
        UserLog_action(db.session, admin_id, user_id,'Update', f"Updated user {user.username} (ID: {user.user_id})", old_data=old_data, new_data=new_data)
        db.session.commit()

        return jsonify({"message": "User updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update user: {str(e)}"}), 500

@admin_bp.route('/api/get_movieLogs', methods=['GET'])
@token_required
@admin_required
def get_movie_logs():
    try:
        logs = db.session.query(MovieLog).all()
        if logs:
            logs_list = [{
                "log_id": log.movie_log_id,
                "admin_id": log.admin_id,
                "action": log.action,
                "details": log.details,
                "created_at": log.timestamp
            } for log in logs]
            return jsonify({"status": "success", "logs": logs_list}), 200
        return jsonify({"status": "success", "message": "No logs found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@admin_bp.route('/api/get_userLogs', methods=['GET'])
@token_required
@admin_required
def get_user_logs():

    try:
        logs = db.session.query(UserLog).all()
        if logs:
            logs_list = [{
                "log_id": log.log_id,
                "admin_id": log.admin_id,
                "user_id": log.user_id,
                "action": log.action,
                "old_data": log.old_data,
                "new_data": log.new_data,
                "created_at": log.timestamp
            } for log in logs]
            return jsonify({"status": "success", "logs": logs_list}), 200
        return jsonify({"status": "success", "message": "No logs found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# NOTE: Admin registration should be done manually via database or removed in production
# This endpoint is disabled for security - admins should be created directly in the database
# @admin_bp.route('/api/register_admin', methods=['POST'])
# def register_admin():
#     # This endpoint is disabled - admins must be created via database
#     return jsonify({"error": "This endpoint is disabled for security reasons"}), 403
