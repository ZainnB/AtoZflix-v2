from app.models.models import Actor,Movie,MoviesActors
from app import db
from flask import Blueprint,request,jsonify
from sqlalchemy import func
actor_bp=Blueprint('actor',__name__)

@actor_bp.route('/api/top-actors', methods=['GET'])
def get_top_actors():
    try:
        actors=Actor.query.all()
        print(actors)
        limit = request.args.get('limit', default=5, type=int)
        subquery = (
            db.session.query(
                Actor.actor_id,
                Actor.actor_name,
                db.func.sum(Movie.rating_avg).label("total_rating")
            )
            .join(MoviesActors, Actor.actor_id == MoviesActors.actor_id)
            .join(Movie, MoviesActors.movie_id == Movie.movie_id)
            .group_by(Actor.actor_id)
            .subquery()
        )
        results = (
            db.session.query(subquery.c.actor_id, subquery.c.actor_name)
            .order_by(subquery.c.total_rating.desc())
            .limit(limit)
            .all()
        )
        actors = [{"actor_id": actor_id, "actor_name": actor_name} for actor_id, actor_name in results]
        return jsonify({"status": "success", "data": actors}), 200
    except Exception as e:
        print(f"Error in get_top_actors: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# Search a movie given an actor
@actor_bp.route("/api/search_actor", methods=["GET"])
def search_movie_by_actor():
    actor_id = request.args.get("actor_id", type=int)
    search_query = request.args.get("query", type=str)
    limit = request.args.get("limit", default=10, type=int)

    try:
        if actor_id:
            actor = db.session.query(Actor).filter_by(actor_id=actor_id).first()
            if not actor:
                return jsonify({"movies": [], "message": "Actor not found"}), 404
            search_query = actor.actor_name

        if not search_query:
            return jsonify({"error": "No search query or actor_id provided"}), 400
        matching_actors = (
            db.session.query(Actor.actor_id)
            .filter(Actor.actor_name.ilike(f"%{search_query}%"))
            .limit(limit)
            .all()
        )
        if not matching_actors:
            return jsonify({"movies": [], "message": "No actors found"}), 404

        actor_ids = [actor_id for (actor_id,) in matching_actors]
        movies = (
            db.session.query(Movie.poster_path, Movie.movie_id)
            .join(MoviesActors, MoviesActors.movie_id == Movie.movie_id)
            .filter(MoviesActors.actor_id.in_(actor_ids))
            .distinct()
            .all()
        )

        formatted_movies = [
            {"poster_path": poster_path, "movie_id": movie_id}
            for poster_path, movie_id in movies
        ]

        return jsonify({"movies": formatted_movies}), 200

    except Exception as e:
        print(f"Error fetching actor movies: {e}")
        return jsonify({"error": "Failed to fetch actor movies"}), 500

# Getting movies by actor
@actor_bp.route('/api/actor-movies', methods=['GET'])
def get_actor_movies():
    try:
        # Get actor_id and limit from request args
        actor_id = request.args.get('actor_id', type=int)
        limit = request.args.get('limit', default=5, type=int)

        if not actor_id:
            return jsonify({"status": "error", "message": "actor_id parameter is required"}), 400

        # Fetch movies associated with the actor, ordered by rating
        movies = (
            db.session.query(Movie.movie_id, Movie.poster_path)
            .join(MoviesActors, MoviesActors.movie_id == Movie.movie_id)
            .filter(MoviesActors.actor_id == actor_id)
            .order_by(Movie.rating_avg.desc())
            .limit(limit)
            .all()
        )

        result = [
            {"poster_path": poster_path, "movie_id": movie_id}
            for movie_id, poster_path in movies
        ]

        return jsonify({"status": "success", "data": result}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
