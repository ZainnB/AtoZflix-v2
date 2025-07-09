from app.models.models import Crew,Movie,MoviesCrew
from app import db
from flask import Blueprint,request,jsonify
crew_bp=Blueprint('crew',__name__)

@crew_bp.route('/api/top-crew', methods=['GET'])
def get_top_crew():
    try:
        limit = request.args.get('limit', default=5, type=int)

        # Perform the equivalent SQLAlchemy query
        from sqlalchemy import func

        results = (
            db.session.query(
                Crew.crew_id,
                Crew.crew_name,
                Crew.job_title,
                func.sum(Movie.rating_avg).label('total_rating')
            )
            .join(MoviesCrew, Crew.crew_id == MoviesCrew.crew_id)
            .join(Movie, MoviesCrew.movie_id == Movie.movie_id)
            .group_by(Crew.crew_id)
            .order_by(func.sum(Movie.rating_avg).desc())
            .limit(limit)
            .all()
        )

        crew = [
            {
                "crew_id": crew_id,
                "crew_name": crew_name,
                "job_title": job_title
            } for crew_id, crew_name, job_title, _ in results
        ]

        return jsonify({"status": "success", "data": crew}), 200

    except Exception as e:
        print(f"Error in get_top_crew: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# Search a movie given a crew member
@crew_bp.route("/api/search_crew", methods=["GET"])
def search_crew():
    search_query = request.args.get("query", type=str)
    crew_id = request.args.get("crew_id", type=int)
    limit = request.args.get("limit", default=10, type=int)

    try:
        # If crew_id is provided, fetch crew's name
        if crew_id:
            crew = db.session.query(Crew).filter_by(crew_id=crew_id).first()
            if not crew:
                return jsonify({"movies": [], "message": "Crew member not found"}), 404
            search_query = crew.crew_name

        if not search_query:
            return jsonify({"movies": [], "message": "No search query provided"}), 400

        # Find all crew members matching the search query (case-insensitive)
        matched_crew = (
            db.session.query(Crew)
            .filter(Crew.crew_name.ilike(f"%{search_query}%"))
            .limit(limit)
            .all()
        )

        if not matched_crew:
            return jsonify({"movies": [], "message": "No crew members found"}), 404

        crew_ids = [crew.crew_id for crew in matched_crew]

        # Fetch movies associated with these crew_ids
        movies = (
            db.session.query(Movie.movie_id, Movie.poster_path)
            .join(MoviesCrew, MoviesCrew.movie_id == Movie.movie_id)
            .filter(MoviesCrew.crew_id.in_(crew_ids))
            .distinct()
            .all()
        )

        formatted_movies = [
            {"poster_path": poster_path, "movie_id": movie_id}
            for movie_id, poster_path in movies
        ]

        return jsonify({"movies": formatted_movies}), 200

    except Exception as e:
        print(f"Error in crew movie search: {e}")
        return jsonify({"error": "Failed to fetch crew movies"}), 500


# Getting movies by crew member
@crew_bp.route('/api/crew-movies', methods=['GET'])
def get_crew_movies():
    try:
        crew_id = request.args.get('crew_id', type=int)
        limit = request.args.get('limit', default=5, type=int)

        if not crew_id:
            return jsonify({"status": "error", "message": "crew_id parameter is required"}), 400

        # ORM Query
        movies = (
            db.session.query(Movie.movie_id, Movie.poster_path)
            .join(MoviesCrew, MoviesCrew.movie_id == Movie.movie_id)
            .filter(MoviesCrew.crew_id == crew_id)
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
