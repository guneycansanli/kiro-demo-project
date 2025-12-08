"""
Weather API Endpoints

This module provides REST API endpoints for retrieving weather data.
"""

from flask import request, jsonify, current_app
from app.api import weather_bp
from app.services.weather_service import WeatherService
from app.services.location_service import LocationService
from app.utils.validators import validate_zip_code
import requests


@weather_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring.
    
    Returns:
        JSON response indicating service health
        
    Validates: Requirements 8.1, 8.3, 8.5
    """
    return jsonify({
        'status': 'healthy',
        'service': 'weather-web-service'
    }), 200


@weather_bp.route('/weather', methods=['GET'])
def get_weather():
    """Get weather data by location query or zip code.
    
    Query Parameters:
        location: Location query string (city, country, etc.)
        zip: 5-digit US zip code
        
    Returns:
        JSON response with weather data or error
        
    Validates: Requirements 2.4, 9.2, 9.3
    """
    # Parse query parameters
    location_query = request.args.get('location')
    zip_code = request.args.get('zip')
    
    # Validate that at least one parameter is provided
    if not location_query and not zip_code:
        return jsonify({
            'error': 'Bad Request',
            'message': 'Either "location" or "zip" parameter is required'
        }), 400
    
    try:
        # Initialize services
        timeout = current_app.config.get('REQUEST_TIMEOUT', 10)
        weather_service = WeatherService(timeout=timeout)
        location_service = LocationService(timeout=timeout)
        
        # Resolve location based on input type
        if zip_code:
            # Validate zip code format
            if not validate_zip_code(zip_code):
                return jsonify({
                    'error': 'Bad Request',
                    'message': 'Invalid zip code format. Must be exactly 5 digits.'
                }), 400
            
            # Resolve zip code to location
            location = location_service.resolve_zip_code(zip_code)
        else:
            # Resolve location query
            location = location_service.resolve_location(location_query)
        
        # Get weather data
        weather_data = weather_service.get_weather_by_coordinates(
            location.coordinates.lat,
            location.coordinates.lon
        )
        
        # Build response
        response = {
            'location': {
                'name': weather_data.location.name,
                'display_name': weather_data.location.display_name,
                'zip_code': weather_data.location.zip_code,
                'coordinates': {
                    'lat': weather_data.location.coordinates.lat,
                    'lon': weather_data.location.coordinates.lon
                }
            },
            'weather': {
                'temp_f': weather_data.temp_f,
                'temp_c': weather_data.temp_c,
                'conditions': weather_data.conditions,
                'rain_chance': weather_data.rain_chance,
                'humidity': weather_data.humidity,
                'wind_speed': weather_data.wind_speed
            },
            'advisory': None
        }
        
        # Add advisory if present
        if weather_data.advisory:
            response['advisory'] = {
                'type': weather_data.advisory.type,
                'description': weather_data.advisory.description,
                'severity': weather_data.advisory.severity
            }
        
        return jsonify(response), 200
        
    except ValueError as e:
        # Handle validation and parsing errors
        return jsonify({
            'error': 'Bad Request',
            'message': str(e)
        }), 400
        
    except requests.RequestException as e:
        # Handle network errors
        return jsonify({
            'error': 'Network Error',
            'message': 'Unable to fetch weather data. Please try again later.'
        }), 502
        
    except Exception as e:
        # Handle unexpected errors
        current_app.logger.error(f"Unexpected error in get_weather: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500


@weather_bp.route('/weather/coordinates', methods=['GET'])
def get_weather_by_coordinates():
    """Get weather data by latitude and longitude.
    
    Query Parameters:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)
        
    Returns:
        JSON response with weather data or error
        
    Validates: Requirements 3.3, 9.2
    """
    # Parse query parameters
    lat_str = request.args.get('lat')
    lon_str = request.args.get('lon')
    
    # Validate that both parameters are provided
    if not lat_str or not lon_str:
        return jsonify({
            'error': 'Bad Request',
            'message': 'Both "lat" and "lon" parameters are required'
        }), 400
    
    try:
        # Convert to float
        lat = float(lat_str)
        lon = float(lon_str)
        
        # Validate coordinate ranges
        from app.utils.validators import validate_coordinates
        is_valid, error_msg = validate_coordinates(lat, lon)
        if not is_valid:
            return jsonify({
                'error': 'Bad Request',
                'message': error_msg
            }), 400
        
        # Initialize weather service
        timeout = current_app.config.get('REQUEST_TIMEOUT', 10)
        weather_service = WeatherService(timeout=timeout)
        
        # Get weather data
        weather_data = weather_service.get_weather_by_coordinates(lat, lon)
        
        # Build response
        response = {
            'location': {
                'name': weather_data.location.name,
                'display_name': weather_data.location.display_name,
                'zip_code': weather_data.location.zip_code,
                'coordinates': {
                    'lat': weather_data.location.coordinates.lat,
                    'lon': weather_data.location.coordinates.lon
                }
            },
            'weather': {
                'temp_f': weather_data.temp_f,
                'temp_c': weather_data.temp_c,
                'conditions': weather_data.conditions,
                'rain_chance': weather_data.rain_chance,
                'humidity': weather_data.humidity,
                'wind_speed': weather_data.wind_speed
            },
            'advisory': None
        }
        
        # Add advisory if present
        if weather_data.advisory:
            response['advisory'] = {
                'type': weather_data.advisory.type,
                'description': weather_data.advisory.description,
                'severity': weather_data.advisory.severity
            }
        
        return jsonify(response), 200
        
    except ValueError as e:
        # Handle conversion and validation errors
        return jsonify({
            'error': 'Bad Request',
            'message': str(e)
        }), 400
        
    except requests.RequestException as e:
        # Handle network errors
        return jsonify({
            'error': 'Network Error',
            'message': 'Unable to fetch weather data. Please try again later.'
        }), 502
        
    except Exception as e:
        # Handle unexpected errors
        current_app.logger.error(f"Unexpected error in get_weather_by_coordinates: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
