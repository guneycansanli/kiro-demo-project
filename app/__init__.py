"""
Weather Web Service - Flask Application Factory

This module provides the Flask application factory for the weather web service.
"""

from flask import Flask
from flask_cors import CORS
import os


def create_app(config=None):
    """Create and configure the Flask application.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')
    
    # Load configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['CACHE_TTL'] = int(os.environ.get('CACHE_TTL', '300'))  # 5 minutes
    app.config['REQUEST_TIMEOUT'] = int(os.environ.get('REQUEST_TIMEOUT', '10'))  # seconds
    app.config['LOG_LEVEL'] = os.environ.get('LOG_LEVEL', 'INFO')
    app.config['CORS_ORIGINS'] = os.environ.get('CORS_ORIGINS', '*')
    
    # Apply custom config if provided
    if config:
        app.config.update(config)
    
    # Enable CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Register blueprints
    from app.api import weather_bp, autocomplete_bp
    app.register_blueprint(weather_bp, url_prefix='/api')
    app.register_blueprint(autocomplete_bp, url_prefix='/api')
    
    # Register error handlers
    from app.api import register_error_handlers
    register_error_handlers(app)
    
    # Setup logging
    from app.utils.logger import setup_logging
    setup_logging(app)
    
    # Register middleware
    from app.utils.logger import request_id_middleware, request_logging_middleware
    app.before_request(request_id_middleware)
    app.before_request(request_logging_middleware)
    
    # Root route to serve the frontend
    @app.route('/')
    def index():
        from flask import render_template
        return render_template('index.html')
    
    return app
