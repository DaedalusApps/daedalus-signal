"""
DaedalusSignal Backend Application
"""
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.config import SECRET_KEY, CORS_ORIGINS, RATE_LIMIT_DEFAULT
from app.database import init_db

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[RATE_LIMIT_DEFAULT]
)


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    
    # Secure session configuration
    app.config['SESSION_COOKIE_SECURE'] = False  # Set True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Initialize extensions
    CORS(app, origins=CORS_ORIGINS, supports_credentials=True)
    limiter.init_app(app)
    
    # Initialize database
    init_db()
    
    # Register blueprints
    from app.api.auth import auth_bp
    from app.api.sources import sources_bp
    from app.api.tags import tags_bp
    from app.api.content import content_bp
    from app.api.admin import admin_bp
    from app.api.feedback import feedback_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(sources_bp, url_prefix='/api/sources')
    app.register_blueprint(tags_bp, url_prefix='/api/tags')
    app.register_blueprint(content_bp, url_prefix='/api/content')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(feedback_bp, url_prefix='/api/feedback')
    
    # Create admin user on first run
    from app.security.auth import create_admin_if_not_exists
    with app.app_context():
        create_admin_if_not_exists()
    
    return app
