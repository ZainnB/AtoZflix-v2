from app import db
from app.models.models import WatchLater,Movie
from flask import Blueprint,request,jsonify, g
from datetime import date
from app.utils.decorators import token_required, verify_user_ownership

watchlater_bp=Blueprint('watch_later',__name__)

@watchlater_bp.route('/api/get_watchlist', methods=['GET'])
@token_required
@verify_user_ownership
def get_watchlist():
    user_id = g.current_user.get('user_id')  # Get from JWT token
    
    # If user_id in query params, verify it matches token
    request_user_id = request.args.get('user_id')
    if request_user_id and int(request_user_id) != int(user_id):
        return jsonify({"status": "error", "message": "You can only access your own watchlist"}), 403

    try:
        watchlist = (
            db.session.query(WatchLater.movie_id, Movie.poster_path, WatchLater.added_at)
            .join(Movie, WatchLater.movie_id == Movie.movie_id)
            .filter(WatchLater.user_id == int(user_id))
            .order_by(WatchLater.added_at.desc())
            .all()
        )

        result = [
            {
                "movie_id": w.movie_id,
                "poster_path": w.poster_path,
                "added_at": w.added_at
            } for w in watchlist
        ]

        return jsonify({"status": "success", "watchlist": result}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    
@watchlater_bp.route('/api/add_to_watchlist', methods=['POST'])
@token_required
@verify_user_ownership
def add_to_watchlist():
    data = request.get_json()
    user_id = g.current_user.get('user_id')  # Get from JWT token
    movie_id = data.get('movie_id')

    if not movie_id:
        return jsonify({"error": "movie_id is required"}), 400

    try:
        exists = db.session.query(WatchLater).filter_by(user_id=user_id, movie_id=movie_id).first()
        if exists:
            return jsonify({"message": "Movie already in watchlist"}), 409

        entry = WatchLater(user_id=user_id, movie_id=movie_id, added_at=date.today())
        db.session.add(entry)
        db.session.commit()

        return jsonify({"message": "Movie added to watchlist"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to add to watchlist", "details": str(e)}), 500
    finally:
        db.session.close()

@watchlater_bp.route('/api/remove_from_watchlist', methods=['POST'])
@token_required
@verify_user_ownership
def remove_from_watchlist():
    data = request.get_json()
    user_id = g.current_user.get('user_id')  # Get from JWT token
    movie_id = data.get('movie_id')

    if not movie_id:
        return jsonify({"error": "movie_id is required"}), 400

    try:
        entry = db.session.query(WatchLater).filter_by(user_id=user_id, movie_id=movie_id).first()
        if not entry:
            return jsonify({"error": "Movie not found in watchlist"}), 404

        db.session.delete(entry)
        db.session.commit()
        return jsonify({"message": "Movie removed from watchlist"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to remove from watchlist", "details": str(e)}), 500
   

@watchlater_bp.route('/api/check_watchlist', methods=['GET'])
@token_required
@verify_user_ownership
def check_watchlist():
    user_id = g.current_user.get('user_id')  # Get from JWT token
    movie_id = request.args.get('movie_id')
    
    # Verify user_id from query matches token
    request_user_id = request.args.get('user_id')
    if request_user_id and int(request_user_id) != int(user_id):
        return jsonify({"error": "You can only check your own watchlist"}), 403

    if not movie_id:
        return jsonify({"error": "movie_id is required"}), 400

    try:
        exists = db.session.query(WatchLater).filter_by(user_id=user_id, movie_id=movie_id).first() is not None
        return jsonify({"is_in_watchlist": exists}), 200

    except Exception as e:
        return jsonify({"error": "Failed to check watchlist", "details": str(e)}), 500
