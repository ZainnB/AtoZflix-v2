from app.models.models import Genre, Movie, MoviesGenres
from app import db
from flask import Blueprint,request,jsonify

genre_bp=Blueprint('genre',__name__)

# This is used to get every genre
@genre_bp.route("/api/get_genre_names", methods=["GET"])
def get_all_genre():
    try:
        genres = db.session.query(Genre.genre_name).distinct().all()
        genre_names = [genre_name for (genre_name,) in genres]
        return jsonify({"genres": genre_names}), 200

    except Exception as e:
        print(f"Error fetching genre details: {e}")
        return jsonify({"error": "Failed to fetch genre details"}), 500
    

# Getting movies by genre
@genre_bp.route('/api/genre',methods=['GET'])
def get_movie_by_genre():
    genre_name=request.args.get('genre',type=str)
    limit=request.args.get('limit',default=10,type=int)
    
    try:
        genre = db.session.query(Genre).filter_by(genre_name=genre_name).first()
        if not genre:
            return jsonify({'error':'Genre not found'}),404
        movies =(
            db.session.query(Movie.poster_path,Movie.movie_id)
            .join(MoviesGenres, Movie.movie_id==MoviesGenres.movie_id)
            .filter(MoviesGenres.genre_id==genre.genre_id)
            .limit(limit)
            .all()
        )
        formatted_movies=[
            {'poster_path':poster_path,'movie_id':movie_id}
        for poster_path,movie_id in movies
        ]
        return jsonify({'movies':formatted_movies}),200
    except Exception as e:
        print(f'Error fetching genre movies:{e}')
        return jsonify({'error': 'Failed to fetch genre movies'}),500
    