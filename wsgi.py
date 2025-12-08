"""
WSGI Entry Point

This module provides the WSGI application entry point for production deployment.

In production, this file is used by Gunicorn to create the Flask application.
For development, it can be run directly with Python to start the Flask dev server.

Usage:
    Production (with Gunicorn):
        gunicorn --bind 0.0.0.0:5000 --workers 4 wsgi:app
    
    Development (direct execution):
        python wsgi.py

Validates: Requirements 8.3, 8.5
"""

from app import create_app

# Create the Flask Application Instance
# This calls the application factory function which:
# 1. Initializes Flask with configuration
# 2. Registers blueprints (API endpoints)
# 3. Sets up CORS
# 4. Configures logging
# 5. Registers error handlers
app = create_app()

if __name__ == '__main__':
    # Development Server
    # This block only runs when executing the file directly (not with Gunicorn)
    # 
    # Configuration:
    # - host='0.0.0.0': Listen on all network interfaces
    # - port=5000: Listen on port 5000
    # - debug=True: Enable debug mode with auto-reload and detailed error pages
    #
    # WARNING: Never use debug=True in production!
    # For production, use Gunicorn or another production WSGI server
    app.run(host='0.0.0.0', port=5000, debug=True)
