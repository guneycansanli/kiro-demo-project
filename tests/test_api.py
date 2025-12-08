"""
API Endpoint Tests

This module contains property-based and integration tests for API endpoints.
"""

import pytest
import json
from hypothesis import given, settings, strategies as st, HealthCheck
from app import create_app


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app = create_app({'TESTING': True})
    with app.test_client() as client:
        yield client


# Feature: weather-web-service, Property 14: API returns JSON for valid requests
# Validates: Requirements 9.2
def test_api_returns_json_for_valid_requests(client):
    """
    Property: For any valid request, the API should return valid JSON.
    
    This test verifies that API endpoints always return valid JSON responses.
    """
    # Test various valid coordinate combinations
    test_coords = [
        (37.7749, -122.4194),  # San Francisco
        (40.7128, -74.0060),   # New York
        (0, 0),                # Equator/Prime Meridian
        (-33.8688, 151.2093),  # Sydney
        (51.5074, -0.1278),    # London
    ]
    
    for lat, lon in test_coords:
        response = client.get(f'/api/weather/coordinates?lat={lat}&lon={lon}')
        
        # Response should be valid JSON
        try:
            data = json.loads(response.data)
            assert isinstance(data, dict)
        except json.JSONDecodeError:
            pytest.fail(f"API did not return valid JSON for lat={lat}, lon={lon}")



# Feature: weather-web-service, Property 15: API returns appropriate status codes for invalid requests
# Validates: Requirements 9.3
def test_api_returns_error_status_for_invalid_coordinates(client):
    """
    Property: For any invalid coordinates, the API should return a 4xx error status code.
    
    This test verifies that the API properly rejects invalid coordinate values
    with appropriate HTTP error codes.
    """
    # Test invalid latitude values
    invalid_lats = [-91, -100, 91, 100, 200]
    for invalid_lat in invalid_lats:
        response = client.get(f'/api/weather/coordinates?lat={invalid_lat}&lon=0')
        assert 400 <= response.status_code < 500, f"Expected 4xx for lat={invalid_lat}, got {response.status_code}"
        data = json.loads(response.data)
        assert 'error' in data or 'message' in data
    
    # Test invalid longitude values
    invalid_lons = [-181, -200, 181, 200, 360]
    for invalid_lon in invalid_lons:
        response = client.get(f'/api/weather/coordinates?lat=0&lon={invalid_lon}')
        assert 400 <= response.status_code < 500, f"Expected 4xx for lon={invalid_lon}, got {response.status_code}"
        data = json.loads(response.data)
        assert 'error' in data or 'message' in data



def test_api_returns_error_for_missing_parameters(client):
    """
    Test that API returns 400 error when required parameters are missing.
    """
    # Missing both lat and lon
    response = client.get('/api/weather/coordinates')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data or 'message' in data
    
    # Missing lon
    response = client.get('/api/weather/coordinates?lat=37.7749')
    assert response.status_code == 400
    
    # Missing lat
    response = client.get('/api/weather/coordinates?lon=-122.4194')
    assert response.status_code == 400
    
    # Missing both location and zip for /api/weather
    response = client.get('/api/weather')
    assert response.status_code == 400


# Feature: weather-web-service, Property 16: CORS headers present in API responses
# Validates: Requirements 9.4
def test_cors_headers_present_in_responses(client):
    """
    Property: For any API request, CORS headers should be present in the response.
    
    This test verifies that all API responses include appropriate CORS headers
    to allow cross-origin requests.
    """
    # Test various endpoints
    test_requests = [
        '/api/weather/coordinates?lat=37.7749&lon=-122.4194',
        '/api/weather/coordinates?lat=0&lon=0',
        '/api/autocomplete?q=San',
        '/api/weather',  # Should return error but still have CORS headers
    ]
    
    for url in test_requests:
        response = client.get(url)
        
        # Check for CORS headers
        # Flask-CORS adds Access-Control-Allow-Origin header
        assert 'Access-Control-Allow-Origin' in response.headers, f"Missing CORS header for {url}"



# Integration Tests
# Validates: Requirements 9.1, 9.2, 9.3

def test_weather_endpoint_with_zip_code(client):
    """
    Integration test: Get weather by zip code.
    
    Tests the complete flow of requesting weather data using a zip code.
    """
    # Use a known zip code (San Francisco)
    response = client.get('/api/weather?zip=94102')
    
    # Should return 200 or 502 (if external API is down)
    assert response.status_code in [200, 502]
    
    data = json.loads(response.data)
    
    if response.status_code == 200:
        # Verify response structure
        assert 'location' in data
        assert 'weather' in data
        assert 'advisory' in data
        
        # Verify location data
        assert 'name' in data['location']
        assert 'coordinates' in data['location']
        
        # Verify weather data
        assert 'temp_f' in data['weather']
        assert 'temp_c' in data['weather']
        assert 'conditions' in data['weather']


def test_weather_endpoint_with_location_query(client):
    """
    Integration test: Get weather by location query.
    
    Tests the complete flow of requesting weather data using a location string.
    """
    # Use a known location
    response = client.get('/api/weather?location=San Francisco, CA')
    
    # Should return 200 or 502 (if external API is down)
    assert response.status_code in [200, 502]
    
    data = json.loads(response.data)
    
    if response.status_code == 200:
        # Verify response structure
        assert 'location' in data
        assert 'weather' in data
        assert 'advisory' in data


def test_weather_coordinates_endpoint(client):
    """
    Integration test: Get weather by coordinates.
    
    Tests the complete flow of requesting weather data using lat/lon.
    """
    # San Francisco coordinates
    response = client.get('/api/weather/coordinates?lat=37.7749&lon=-122.4194')
    
    # Should return 200 or 502 (if external API is down)
    assert response.status_code in [200, 502]
    
    data = json.loads(response.data)
    
    if response.status_code == 200:
        # Verify response structure
        assert 'location' in data
        assert 'weather' in data
        assert 'advisory' in data
        
        # Verify coordinates match
        assert abs(data['location']['coordinates']['lat'] - 37.7749) < 0.1
        assert abs(data['location']['coordinates']['lon'] - (-122.4194)) < 0.1


def test_autocomplete_endpoint(client):
    """
    Integration test: Get autocomplete suggestions.
    
    Tests the complete flow of requesting location suggestions.
    """
    # Query for San Francisco
    response = client.get('/api/autocomplete?q=San Francisco')
    
    assert response.status_code == 200
    
    data = json.loads(response.data)
    
    # Should have suggestions key
    assert 'suggestions' in data
    assert isinstance(data['suggestions'], list)
    
    # If suggestions are returned, verify structure
    if len(data['suggestions']) > 0:
        suggestion = data['suggestions'][0]
        assert 'display_name' in suggestion
        assert 'type' in suggestion
        assert 'coordinates' in suggestion


def test_autocomplete_with_empty_query(client):
    """
    Integration test: Autocomplete with empty query returns empty list.
    """
    response = client.get('/api/autocomplete?q=')
    
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'suggestions' in data
    assert data['suggestions'] == []


def test_weather_endpoint_with_invalid_zip(client):
    """
    Integration test: Invalid zip code returns error.
    """
    response = client.get('/api/weather?zip=123')  # Invalid: not 5 digits
    
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert 'error' in data or 'message' in data


def test_error_response_format(client):
    """
    Integration test: Error responses have consistent format.
    
    Validates: Requirements 7.1, 7.2, 7.3, 9.3
    """
    # Test various error conditions
    error_requests = [
        '/api/weather',  # Missing parameters
        '/api/weather/coordinates?lat=100&lon=0',  # Invalid lat
        '/api/weather/coordinates?lat=0&lon=200',  # Invalid lon
        '/api/weather?zip=abc',  # Invalid zip format
    ]
    
    for url in error_requests:
        response = client.get(url)
        
        # Should return 4xx error
        assert 400 <= response.status_code < 500, f"Expected 4xx for {url}, got {response.status_code}"
        
        # Should have consistent error format
        data = json.loads(response.data)
        assert 'error' in data or 'message' in data, f"Missing error info for {url}"
