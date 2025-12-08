"""
Autocomplete API Endpoints

This module provides REST API endpoints for location autocomplete suggestions.
"""

from flask import request, jsonify, current_app
from app.api import autocomplete_bp
from app.services.location_service import LocationService
import requests


@autocomplete_bp.route('/autocomplete', methods=['GET'])
def get_autocomplete():
    """Get autocomplete suggestions for location search.
    
    Query Parameters:
        q: Search query string
        
    Returns:
        JSON response with location suggestions or error
        
    Validates: Requirements 2.2, 9.2
    """
    # Parse query parameter
    query = request.args.get('q', '').strip()
    
    # Return empty suggestions for empty query
    if not query:
        return jsonify({'suggestions': []}), 200
    
    try:
        # Initialize location service
        timeout = current_app.config.get('REQUEST_TIMEOUT', 10)
        location_service = LocationService(timeout=timeout)
        
        # Get autocomplete suggestions
        suggestions = location_service.get_autocomplete_suggestions(query)
        
        # Build response
        response = {
            'suggestions': [
                {
                    'display_name': suggestion.display_name,
                    'type': suggestion.type,
                    'zip_code': suggestion.zip_code,
                    'coordinates': {
                        'lat': suggestion.coordinates.lat,
                        'lon': suggestion.coordinates.lon
                    }
                }
                for suggestion in suggestions
            ]
        }
        
        return jsonify(response), 200
        
    except requests.RequestException as e:
        # Handle network errors gracefully - return empty suggestions
        current_app.logger.warning(f"Network error in autocomplete: {str(e)}")
        return jsonify({'suggestions': []}), 200
        
    except Exception as e:
        # Handle unexpected errors gracefully - return empty suggestions
        current_app.logger.error(f"Unexpected error in get_autocomplete: {str(e)}")
        return jsonify({'suggestions': []}), 200
