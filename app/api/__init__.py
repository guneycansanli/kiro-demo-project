"""
API Blueprint Package

This package contains all API endpoints and error handlers.
"""

from flask import Blueprint, jsonify
from app.utils.logger import log_error

# Create blueprints
weather_bp = Blueprint('weather', __name__)
autocomplete_bp = Blueprint('autocomplete', __name__)


def register_error_handlers(app):
    """Register error handlers for the Flask application.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        log_error(error, {'status_code': 400})
        return jsonify({
            'error': 'Bad Request',
            'message': str(error.description) if hasattr(error, 'description') else 'Invalid request'
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        log_error(error, {'status_code': 404})
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server Error."""
        log_error(error, {'status_code': 500})
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all unhandled exceptions."""
        log_error(error, {'status_code': 500})
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500


# Import routes to register them with blueprints
from app.api import weather, autocomplete
