from app import db
from datetime import datetime

class Movie(db.Model):
    __tablename__ = 'Movies'
    movie_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    original_title = db.Column(db.String(255), nullable=False)
    budget = db.Column(db.BigInteger, nullable=False)
    original_language = db.Column(db.String(10), nullable=False)
    release_date = db.Column(db.Date, nullable=False)
    revenue = db.Column(db.BigInteger, nullable=False)
    runtime = db.Column(db.Integer, nullable=False, default=0)
    overview = db.Column(db.Text, nullable=False, default='No Overview')
    production_companies = db.Column(db.Text, nullable=False)
    rating_avg = db.Column(db.Float, nullable=False)
    rating_count = db.Column(db.Integer, nullable=False)
    country = db.Column(db.String(255), nullable=False, default='Unknown')
    backdrop_path = db.Column(db.String(255), nullable=False, default='Backdrop is not available')
    poster_path = db.Column(db.String(255), nullable=False, default='Poster is not available')
    adult = db.Column(db.Boolean, nullable=False, default=False)

class Genre(db.Model):
    __tablename__ = 'Genres'
    genre_id = db.Column(db.Integer, primary_key=True)
    genre_name = db.Column(db.String(255), nullable=False, unique=True)

class MoviesGenres(db.Model):
    __tablename__ = 'Movies_Genres'
    movie_id = db.Column(db.Integer, db.ForeignKey('Movies.movie_id'), primary_key=True)
    genre_id = db.Column(db.Integer, db.ForeignKey('Genres.genre_id'), primary_key=True)

class Country(db.Model):
    __tablename__ = 'Countries'
    country_id = db.Column(db.Integer, primary_key=True)
    country_name = db.Column(db.String(255), nullable=False, unique=True)

class MoviesCountries(db.Model):
    __tablename__ = 'Movies_Countries'
    movie_id = db.Column(db.Integer, db.ForeignKey('Movies.movie_id'), primary_key=True)
    country_id = db.Column(db.Integer, db.ForeignKey('Countries.country_id'), primary_key=True)

class Actor(db.Model):
    __tablename__ = 'Actors'
    actor_id = db.Column(db.Integer, primary_key=True)
    actor_name = db.Column(db.String(255), nullable=False)
    character_name = db.Column(db.String(255), nullable=False)

class MoviesActors(db.Model):
    __tablename__ = 'Movies_Actors'
    movie_id = db.Column(db.Integer, db.ForeignKey('Movies.movie_id'), primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('Actors.actor_id'), primary_key=True)

class Crew(db.Model):
    __tablename__ = 'Crew'
    crew_id = db.Column(db.Integer, primary_key=True)
    crew_name = db.Column(db.String(255), nullable=False)
    job_title = db.Column(db.String(255), nullable=False)

class MoviesCrew(db.Model):
    __tablename__ = 'Movies_Crew'
    movie_id = db.Column(db.Integer, db.ForeignKey('Movies.movie_id'), primary_key=True)
    crew_id = db.Column(db.Integer, db.ForeignKey('Crew.crew_id'), primary_key=True)

class Keyword(db.Model):
    __tablename__ = 'Keywords'
    keyword_id = db.Column(db.Integer, primary_key=True)
    keyword_name = db.Column(db.String(255), nullable=False, unique=True)

class MoviesKeywords(db.Model):
    __tablename__ = 'Movies_Keywords'
    movie_id = db.Column(db.Integer, db.ForeignKey('Movies.movie_id'), primary_key=True)
    keyword_id = db.Column(db.Integer, db.ForeignKey('Keywords.keyword_id'), primary_key=True)

class User(db.Model):
    __tablename__ = 'Users'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(255), nullable=False, default='user')
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

class Rating(db.Model):
    __tablename__ = 'Ratings'
    rating_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('Movies.movie_id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text)
    rated_at = db.Column(db.Date)

class Favorite(db.Model):
    __tablename__ = 'Favorites'
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('Movies.movie_id'), primary_key=True)
    added_at = db.Column(db.Date)

class WatchLater(db.Model):
    __tablename__ = 'WatchLater'
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('Movies.movie_id'), primary_key=True)
    added_at = db.Column(db.Date)

class MovieLog(db.Model):
    __tablename__ = 'MovieLogs'
    movie_log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), nullable=False)
    action = db.Column(db.String(10), nullable=False)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime)

class UserLog(db.Model):
    __tablename__ = 'UserLogs'
    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'))
    action = db.Column(db.String(10), nullable=False)
    old_data = db.Column(db.Text)
    new_data = db.Column(db.Text)
    timestamp = db.Column(db.DateTime)
