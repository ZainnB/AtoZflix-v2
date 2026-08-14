from flask import Blueprint, request, jsonify, g

from app.utils.decorators import token_required, admin_required
from app.utils.recommender import (
    MODEL_CACHE,
    hydrate,
    recommend_for_user,
    similar_movies,
)

recommendation_bp = Blueprint('recommendation', __name__)

MAX_LIMIT = 50


def _clamped_limit(default):
    limit = request.args.get('limit', default=default, type=int)
    return max(1, min(MAX_LIMIT, limit))


@recommendation_bp.route('/api/recommendations', methods=['GET'])
@token_required
def get_recommendations():
    """
    Personalised hybrid recommendations for the caller.

    The user is taken from the JWT, never from a query parameter, so one user
    cannot ask for another user's feed.
    """
    user_id = g.current_user.get('user_id')
    limit = _clamped_limit(20)
    explain = request.args.get('explain', default='false').lower() == 'true'

    try:
        payload = recommend_for_user(user_id, limit=limit, explain=explain)
        payload['results'] = hydrate(payload['results'])
        return jsonify({
            "status": "success",
            "strategy": payload["strategy"],
            "content_weight": payload["content_weight"],
            "interaction_count": payload["interaction_count"],
            "movies": payload["results"],
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@recommendation_bp.route('/api/similar_movies', methods=['GET'])
def get_similar_movies():
    """
    "More like this" for one film. Public - it needs no user history, which is
    exactly why it still works for a logged-out visitor or a brand new account.
    """
    movie_id = request.args.get('movie_id', type=int)
    if not movie_id:
        return jsonify({"status": "error", "message": "movie_id is required"}), 400

    limit = _clamped_limit(12)
    strategy = request.args.get('strategy', default='hybrid').lower()
    if strategy not in ('content', 'collaborative', 'hybrid'):
        return jsonify({
            "status": "error",
            "message": "strategy must be one of: content, collaborative, hybrid"
        }), 400

    try:
        results = hydrate(similar_movies(movie_id, limit=limit, strategy=strategy))
        return jsonify({
            "status": "success",
            "strategy": strategy,
            "movies": results,
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@recommendation_bp.route('/api/recommender_stats', methods=['GET'])
@token_required
@admin_required
def get_recommender_stats():
    """Model introspection: how big the index is and how long the build took."""
    try:
        return jsonify({"status": "success", "stats": MODEL_CACHE.stats()}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@recommendation_bp.route('/api/rebuild_recommender', methods=['POST'])
@token_required
@admin_required
def rebuild_recommender():
    """
    Force a model rebuild.

    The cache already self-invalidates on a TTL and on a row-count fingerprint,
    but a bulk TMDb import is exactly the moment an admin wants the new titles
    recommendable immediately rather than up to TTL seconds later.
    """
    try:
        MODEL_CACHE.invalidate()
        return jsonify({
            "status": "success",
            "message": "Recommender models rebuilt",
            "stats": MODEL_CACHE.stats(),
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
