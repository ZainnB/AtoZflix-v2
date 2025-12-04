from flask_cors import CORS
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Load configuration from environment variables
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Normalize DATABASE_URL (Railway might provide mysql://)
    database_url = os.getenv('DATABASE_URL', 'sqlite:///movies.db')
    if database_url and database_url.startswith("mysql://"):
        # SQLAlchemy needs driver prefix
        database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url

    # Recommended engine options for pooled connections / cloud DBs
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_size": int(os.getenv('DB_POOL_SIZE', 10)),
        "pool_recycle": int(os.getenv('DB_POOL_RECYCLE', 3600)),
        "pool_pre_ping": True
    }

    # CORS configuration
    cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:3000').split(',')
    CORS(app, origins=cors_origins, supports_credentials=True)
    
    # Initialize extensions
    db.init_app(app)
    
    # Rate limiting (must be initialized after app is created)
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    
    # Make limiter available to routes via app context
    app.limiter = limiter

    # Register blueprints
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

    return app
