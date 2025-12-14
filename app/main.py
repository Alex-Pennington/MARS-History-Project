"""
Flask application factory and entry point for SME Interview System.
"""

import os
from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.models.database import init_db, close_db
from app.routes.auth import bp as auth_bp
from app.routes.interview import interview_bp
from app.routes.sessions import sessions_bp
from app.routes.static import static_bp


def create_app(config_class=Config):
    """
    Application factory for creating Flask app instances.
    
    Args:
        config_class: Configuration class to use
    
    Returns:
        Configured Flask application
    """
    # Create Flask app
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Load configuration
    app.config.from_object(config_class)
    app.secret_key = config_class.SECRET_KEY
    
    # Ensure required directories exist
    config_class.ensure_directories()
    
    # Enable CORS for development
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    
    # Initialize database
    with app.app_context():
        init_db()
    
    # Register blueprints
    # Auth blueprint handles /, /auth, /interview, /api/auth, /api/logout
    app.register_blueprint(auth_bp)
    app.register_blueprint(interview_bp)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(static_bp)
    
    # Register teardown
    @app.teardown_appcontext
    def teardown_db(exception):
        """Close database connection on app context teardown."""
        pass  # Connection is managed globally for simplicity
    
    # Log startup info
    if app.debug:
        print("=" * 60)
        print("SME Interview System Starting")
        print("=" * 60)
        print(f"Environment: {config_class.FLASK_ENV}")
        print(f"Debug Mode: {config_class.DEBUG}")
        print(f"Auth Required: {config_class.REQUIRE_AUTH}")
        print(f"Database: {config_class.DATABASE_PATH}")
        print(f"Audio Cache: {config_class.AUDIO_CACHE_DIR}")
        print("=" * 60)
        
        # Validate configuration
        errors = config_class.validate()
        if errors:
            print("WARNING: Configuration issues detected:")
            for error in errors:
                print(f"  - {error}")
            print("=" * 60)
    
    return app


# For running directly with `python -m app.main`
if __name__ == '__main__':
    app = create_app()
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
