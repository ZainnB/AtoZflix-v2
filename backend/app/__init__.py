from flask_cors import CORS
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db=SQLAlchemy()
def create_app():
    app=Flask(__name__)
    CORS(app)
    app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///movies.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
    db.init_app(app)

    from app.routes.main_routes import main
    app.register_blueprint(main)
    from app.routes.user_routes import user_bp
    app.register_blueprint(user_bp)
    from app.routes.admin_routes import admin_bp
    app.register_blueprint(admin_bp)
    from app.routes.movie_routes import movie_bp
    app.register_blueprint(movie_bp)
    from app.routes.genre_routes import genre_bp
    app.register_blueprint(genre_bp)
    from app.routes.country_routes import country_bp
    app.register_blueprint(country_bp)
    from app.routes.actor_routes import actor_bp
    app.register_blueprint(actor_bp)
    from app.routes.crew_routes import crew_bp
    app.register_blueprint(crew_bp)
    from app.routes.rating_routes import rating_bp
    app.register_blueprint(rating_bp)

    from app.routes.favoruite_routes import favourite_bp
    app.register_blueprint(favourite_bp)
    from app.routes.watchlist_routes import watchlater_bp
    app.register_blueprint(watchlater_bp)
    #from app.routes.recommendation_routes import recommendation
    #app.register_blueprint(recommendation,url_prefix='/api')
    return app