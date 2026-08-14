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
    # A composite PK indexes (movie_id, genre_id), which serves lookups by
    # movie_id but NOT "all movies in this genre" - the leading column is wrong
    # for that. Hence the explicit index on the second column here and on every
    # other junction table below.
    genre_id = db.Column(db.Integer, db.ForeignKey('Genres.genre_id'), primary_key=True, index=True)

class Country(db.Model):
    __tablename__ = 'Countries'
    country_id = db.Column(db.Integer, primary_key=True)
    country_name = db.Column(db.String(255), nullable=False, unique=True)

class MoviesCountries(db.Model):
    __tablename__ = 'Movies_Countries'
    movie_id = db.Column(db.Integer, db.ForeignKey('Movies.movie_id'), primary_key=True)
    country_id = db.Column(db.Integer, db.ForeignKey('Countries.country_id'), primary_key=True, index=True)

class Actor(db.Model):
    __tablename__ = 'Actors'
    actor_id = db.Column(db.Integer, primary_key=True)
    actor_name = db.Column(db.String(255), nullable=False)
    # Headshot path, filled in bulk from movie credits (backfill_people.py).
    profile_path = db.Column(db.String(255))
    popularity = db.Column(db.Float)

    # Biography fields come from TMDb's /person endpoint, which is one request
    # PER PERSON - 45,009 actors makes a bulk fetch impractical. They are
    # instead fetched lazily the first time someone opens an actor's page and
    # then cached here forever. `details_fetched` records that the lookup
    # happened, so an actor with a genuinely empty biography is not re-fetched
    # on every single view.
    biography = db.Column(db.Text)
    birthday = db.Column(db.String(20))
    deathday = db.Column(db.String(20))
    place_of_birth = db.Column(db.String(255))
    details_fetched = db.Column(db.Boolean, nullable=False, default=False)

class MoviesActors(db.Model):
    __tablename__ = 'Movies_Actors'
    movie_id = db.Column(db.Integer, db.ForeignKey('Movies.movie_id'), primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('Actors.actor_id'), primary_key=True, index=True)
    # The character belongs to the ROLE, not to the actor: Tom Hanks is Forrest
    # Gump in one film and Woody in another. Holding it on Actors meant each
    # import overwrote the last one's character. It lives on the junction now.
    character_name = db.Column(db.String(255))
    # TMDb billing order. Lets the recommender weight top-billed cast above the
    # 140th credited extra, and lets the UI show a cast list in the right order.
    billing_order = db.Column(db.Integer)

class Crew(db.Model):
    __tablename__ = 'Crew'
    crew_id = db.Column(db.Integer, primary_key=True)
    crew_name = db.Column(db.String(255), nullable=False)
    job_title = db.Column(db.String(255), nullable=False)
    profile_path = db.Column(db.String(255))

class MoviesCrew(db.Model):
    __tablename__ = 'Movies_Crew'
    movie_id = db.Column(db.Integer, db.ForeignKey('Movies.movie_id'), primary_key=True)
    crew_id = db.Column(db.Integer, db.ForeignKey('Crew.crew_id'), primary_key=True, index=True)

class Keyword(db.Model):
    __tablename__ = 'Keywords'
    keyword_id = db.Column(db.Integer, primary_key=True)
    keyword_name = db.Column(db.String(255), nullable=False, unique=True)

class MoviesKeywords(db.Model):
    __tablename__ = 'Movies_Keywords'
    movie_id = db.Column(db.Integer, db.ForeignKey('Movies.movie_id'), primary_key=True)
    keyword_id = db.Column(db.Integer, db.ForeignKey('Keywords.keyword_id'), primary_key=True, index=True)

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
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), nullable=False, index=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('Movies.movie_id'), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text)
    rated_at = db.Column(db.Date)

class Favorite(db.Model):
    __tablename__ = 'Favorites'
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('Movies.movie_id'), primary_key=True, index=True)
    added_at = db.Column(db.Date)

class WatchLater(db.Model):
    __tablename__ = 'WatchLater'
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('Movies.movie_id'), primary_key=True, index=True)
    added_at = db.Column(db.Date)


class MovieLensRating(db.Model):
    """
    Reference ratings imported from the MovieLens 25M dataset.

    Deliberately NOT stored in `Ratings`. MovieLens user ids are its own dense
    1..162541 sequence and would collide head-on with our autoincrementing
    Users.user_id, and these are not our users: nobody can log in as them, they
    have no email or password, and they must never appear in an admin user list
    or a "users" count. Keeping them in their own table means the FK to Users
    stays honest and no route has to remember to filter them out.

    The recommender unions both sources at read time under namespaced keys
    (("app", id) vs ("ml", id)), so collaborative filtering trains on 25M real
    ratings while the product's own tables stay clean.

    Ratings are rescaled from MovieLens' 0.5-5.0 half-star scale to this
    project's 0-10 integer scale by doubling, which is exact and lossless.
    """
    __tablename__ = 'MovieLens_Ratings'
    ml_user_id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('Movies.movie_id'), primary_key=True, index=True)
    rating = db.Column(db.Integer, nullable=False)
    rated_at = db.Column(db.Date)


class ItemSimilarity(db.Model):
    """
    Precomputed item-item collaborative filtering neighbours.

    Building this in-process was fine at 1.5k movies and ~28k interactions. At
    25M ratings the co-occurrence accumulation is O(sum of k^2 over users) in
    pure Python and takes hours, so the build moved offline into
    `build_similarity.py`, which does it as sparse matrix multiplication and
    writes the top-N neighbours per movie here.

    The web process then never builds the model at all - it reads these rows.
    That keeps numpy and scipy out of the request path (and out of the
    deployment image's runtime requirements), makes every gunicorn worker share
    one consistent model instead of each rebuilding its own, and turns a
    multi-hour cold start into a single indexed query.
    """
    __tablename__ = 'Item_Similarity'
    movie_id = db.Column(db.Integer, db.ForeignKey('Movies.movie_id'), primary_key=True)
    neighbour_id = db.Column(db.Integer, db.ForeignKey('Movies.movie_id'), primary_key=True)
    similarity = db.Column(db.Float, nullable=False)
    rank = db.Column(db.Integer, nullable=False)

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
