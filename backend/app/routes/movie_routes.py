from app.models.models import Movie,MoviesGenres,Genre,Actor,MoviesActors
from sqlalchemy import func,desc
from datetime import datetime,timedelta
from app import db
from flask import Blueprint,request,jsonify

movie_bp=Blueprint('movie',__name__)

# Get latest movies
@movie_bp.route('/api/latest',methods=['GET'])
def get_latest_movie():
    limit=request.args.get('limit',default=80,type=int)
    offset=request.args.get('offset',default=0,type=int)
    try:
        movies=(
            db.session.query(Movie.poster_path,Movie.movie_id)
            .order_by(Movie.release_date.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        print(movies)
        formatted_movies=[{"poster_path":poster_path,"movie_id":movie_id} for poster_path,movie_id in movies]
        return jsonify({'movies':formatted_movies}),200
    except Exception as e:
        return jsonify({'message':'Failed to fetch latest movies'}),500
    
# Get trending movies (6 months) made by zain
@movie_bp.route('/api/trending', methods=['GET'])
def get_trending_movies():
    limit = request.args.get('limit', default=5, type=int)
    
    try:
        # Calculate date 6 months ago
        six_months_ago = datetime.now() - timedelta(days=180)
        
        # Subquery to group genres per movie
        genre_subquery = (
            db.session.query(
                MoviesGenres.movie_id,
                func.group_concat(Genre.genre_name, ', ').label("genres")
            )
            .join(Genre, MoviesGenres.genre_id == Genre.genre_id)
            .group_by(MoviesGenres.movie_id)
            .subquery()
        )
        
        # Main query for trending logic
        trending_movies = (
            db.session.query(
                Movie.title,
                Movie.backdrop_path,
                Movie.overview,
                Movie.rating_avg,
                Movie.runtime,
                Movie.release_date,
                Movie.movie_id,
                genre_subquery.c.genres
            )
            .outerjoin(genre_subquery, Movie.movie_id == genre_subquery.c.movie_id)
            .filter(Movie.release_date >= six_months_ago)
            .order_by((Movie.rating_avg * 0.7 + Movie.rating_count * 0.3).desc())
            .limit(limit)
            .all()
        )

        result = [
            {
                "title": m.title,
                "backdrop_path": m.backdrop_path,
                "overview": m.overview,
                "rating": m.rating_avg,
                "duration": m.runtime,
                "release_date": m.release_date,
                "movie_id": m.movie_id,
                "genres": m.genres
            }
            for m in trending_movies
        ]

        return jsonify({"status": "success", "movies": result}), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
  

@movie_bp.route('/api/top_rated',methods=['GET'])
def get_top_rated_movie():
    limit=request.args.get('limit',default=10,type=int)
    offset=request.args.get('offset',default=0,type=int)
    try:
        movies=(
            db.session.query(Movie.poster_path,Movie.movie_id)
            .order_by(Movie.rating_avg.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        print(movies)
        formatted_movies=[{"poster_path":poster_path,"movie_id":movie_id} for poster_path,movie_id in movies]
        return jsonify({'movies':formatted_movies}),200
    except Exception as e:
        return jsonify({'message':'Failed to fetch latest movies'}),500
    

@movie_bp.route("/api/movie_details", methods=["GET"])
def movie_details():
    movie_id = request.args.get("movie_id", type=int)

    if not movie_id:
        return jsonify({"error": "movie_id parameter is required"}), 400

    try:
        movie = (
            db.session.query(Movie)
            .filter(Movie.movie_id == movie_id)
            .first()
        )

        if movie:
            formatted_movie = {
                "title": movie.title,
                "original_title": movie.original_title,
                "release_date": movie.release_date,
                "budget": movie.budget,
                "revenue": movie.revenue,
                "runtime": movie.runtime,
                "overview": movie.overview,
                "production_companies": movie.production_companies,
                "production_countries": movie.production_countries,
                "rating_avg": movie.rating_avg,
                "rating_count": movie.rating_count,
                "country": movie.country,
                "poster_path": movie.poster_path,
                "backdrop_path": movie.backdrop_path,
                "adult": movie.adult
            }
            return jsonify({"movie": formatted_movie}), 200
        else:
            return jsonify({"error": "Movie not found"}), 404

    except Exception as e:
        print(f"Error fetching movie details: {e}")
        return jsonify({"error": "Failed to fetch movie details"}), 500

@movie_bp.route("/api/search_movie", methods=["GET"])
def search_movies():
    search_query = request.args.get("query", type=str)
    limit = request.args.get("limit", default=10, type=int)

    if not search_query:
        return jsonify({"error": "Missing search query"}), 400
    try:
        # Case-insensitive, partial match using ilike
        results = (
            db.session.query(Movie.poster_path, Movie.movie_id)
            .filter(Movie.title.ilike(f"%{search_query}%"))
            .limit(limit)
            .all()
        )

        formatted_movies = [
            {"poster_path": poster_path, "movie_id": movie_id}
            for poster_path, movie_id in results
        ]

        return jsonify({"movies": formatted_movies}), 200

    except Exception as e:
        print(f"Error in search: {e}")
        return jsonify({"error": "Failed to fetch search movies"}), 500
   

@movie_bp.route('/api/get_movie_count', methods=['GET'])
def get_movie_count():
    try:
        count = db.session.query(Movie).count()
        return jsonify({"status": "success", "count": count}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
