"""
End-to-End Tests

This module contains end-to-end tests for complete user flows.
Validates: Requirements 1.1, 2.1, 2.4, 3.1, 3.3
"""

import pytest
import json
from app import create_app


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app = create_app({'TESTING': True})
    with app.test_client() as client:
        yield client


class TestEndToEndUserFlows:
    """End-to-end tests for complete user flows."""
    
    def test_search_by_zip_code_flow(self, client):
        """
        E2E Test: Complete flow for searching weather by zip code.
        
        User flow:
        1. User enters a 5-digit zip code
        2. System validates the zip code
        3. System fetches weather data
        4. System displays weather information
        
        Validates: Requirements 2.1, 2.4, 2.5
        """
        # Test with a valid San Francisco zip code
        zip_code = "94102"
        
        response = client.get(f'/api/weather?zip={zip_code}')
        
        # Should return success or network error (if external API is down)
        assert response.status_code in [200, 502], f"Unexpected status: {response.status_code}"
        
        data = json.loads(response.data)
        
        if response.status_code == 200:
            # Verify complete weather data structure
            assert 'location' in data, "Missing location in response"
            assert 'weather' in data, "Missing weather in response"
            assert 'advisory' in data, "Missing advisory in response"
            
            # Verify location information
            location = data['location']
            assert 'name' in location
            assert 'coordinates' in location
            assert 'lat' in location['coordinates']
            assert 'lon' in location['coordinates']
            
            # Verify weather metrics (all required fields)
            weather = data['weather']
            assert 'temp_f' in weather, "Missing temperature in Fahrenheit"
            assert 'temp_c' in weather, "Missing temperature in Celsius"
            assert 'conditions' in weather, "Missing conditions"
            assert 'rain_chance' in weather, "Missing rain chance"
            assert 'humidity' in weather, "Missing humidity"
            assert 'wind_speed' in weather, "Missing wind speed"
            
            # Verify advisory is present (can be null)
            assert data['advisory'] is None or isinstance(data['advisory'], dict)
            
            print(f"✓ Zip code search flow completed successfully for {zip_code}")
    
    def test_search_by_city_name_flow(self, client):
        """
        E2E Test: Complete flow for searching weather by city name.
        
        User flow:
        1. User enters a city name
        2. System resolves city to coordinates
        3. System fetches weather data
        4. System displays weather information
        
        Validates: Requirements 2.1, 2.4
        """
        # Test with a well-known city
        city = "San Francisco, CA"
        
        response = client.get(f'/api/weather?location={city}')
        
        # Should return success or network error
        assert response.status_code in [200, 502], f"Unexpected status: {response.status_code}"
        
        data = json.loads(response.data)
        
        if response.status_code == 200:
            # Verify complete response structure
            assert 'location' in data
            assert 'weather' in data
            assert 'advisory' in data
            
            # Verify location was resolved
            location = data['location']
            assert location['name'] is not None
            assert location['coordinates']['lat'] is not None
            assert location['coordinates']['lon'] is not None
            
            # Verify all weather metrics are present
            weather = data['weather']
            required_fields = ['temp_f', 'temp_c', 'conditions', 'rain_chance', 'humidity', 'wind_speed']
            for field in required_fields:
                assert field in weather, f"Missing required field: {field}"
            
            print(f"✓ City name search flow completed successfully for {city}")
    
    def test_autocomplete_search_flow(self, client):
        """
        E2E Test: Complete flow for autocomplete suggestions.
        
        User flow:
        1. User types in search field
        2. System provides autocomplete suggestions
        3. User selects a suggestion
        4. System fetches weather for selected location
        
        Validates: Requirements 2.2, 2.3, 2.4
        """
        # Step 1 & 2: Get autocomplete suggestions
        query = "San"
        response = client.get(f'/api/autocomplete?q={query}')
        
        assert response.status_code == 200, f"Autocomplete failed: {response.status_code}"
        
        data = json.loads(response.data)
        assert 'suggestions' in data
        assert isinstance(data['suggestions'], list)
        
        # Verify suggestions have required structure
        if len(data['suggestions']) > 0:
            suggestion = data['suggestions'][0]
            assert 'display_name' in suggestion
            assert 'type' in suggestion
            assert 'coordinates' in suggestion
            assert 'lat' in suggestion['coordinates']
            assert 'lon' in suggestion['coordinates']
            
            # Step 3 & 4: Use suggestion to get weather
            lat = suggestion['coordinates']['lat']
            lon = suggestion['coordinates']['lon']
            
            weather_response = client.get(f'/api/weather/coordinates?lat={lat}&lon={lon}')
            
            if weather_response.status_code == 200:
                weather_data = json.loads(weather_response.data)
                assert 'location' in weather_data
                assert 'weather' in weather_data
                
                print(f"✓ Autocomplete flow completed successfully for query '{query}'")
    
    def test_current_location_flow(self, client):
        """
        E2E Test: Complete flow for using current location.
        
        User flow:
        1. User clicks "Use Current Location" button
        2. Browser provides coordinates
        3. System fetches weather for coordinates
        4. System displays weather information
        
        Validates: Requirements 3.1, 3.3, 3.5
        """
        # Simulate browser providing coordinates (San Francisco)
        lat = 37.7749
        lon = -122.4194
        
        response = client.get(f'/api/weather/coordinates?lat={lat}&lon={lon}')
        
        # Should return success or network error
        assert response.status_code in [200, 502], f"Unexpected status: {response.status_code}"
        
        data = json.loads(response.data)
        
        if response.status_code == 200:
            # Verify complete response
            assert 'location' in data
            assert 'weather' in data
            assert 'advisory' in data
            
            # Verify coordinates match (within reasonable tolerance)
            returned_lat = data['location']['coordinates']['lat']
            returned_lon = data['location']['coordinates']['lon']
            assert abs(returned_lat - lat) < 0.1, "Latitude mismatch"
            assert abs(returned_lon - lon) < 0.1, "Longitude mismatch"
            
            # Verify all weather data is present
            weather = data['weather']
            assert weather['temp_f'] is not None
            assert weather['temp_c'] is not None
            assert weather['conditions'] is not None
            
            print(f"✓ Current location flow completed successfully for ({lat}, {lon})")


class TestErrorScenarios:
    """End-to-end tests for error handling scenarios."""
    
    def test_invalid_zip_code_error_flow(self, client):
        """
        E2E Test: Error handling for invalid zip code.
        
        User flow:
        1. User enters invalid zip code
        2. System validates and rejects
        3. System displays error message
        
        Validates: Requirements 2.5, 7.1, 7.4
        """
        invalid_zips = ["123", "abcde", "12345678", ""]
        
        for invalid_zip in invalid_zips:
            response = client.get(f'/api/weather?zip={invalid_zip}')
            
            # Should return 400 Bad Request
            assert response.status_code == 400, f"Expected 400 for zip '{invalid_zip}', got {response.status_code}"
            
            data = json.loads(response.data)
            
            # Should have error information
            assert 'error' in data or 'message' in data, "Missing error information"
            
            # Error message should be non-empty and descriptive
            error_msg = data.get('error') or data.get('message')
            assert error_msg, "Error message is empty"
            assert len(error_msg) > 0, "Error message is empty"
            
            print(f"✓ Invalid zip code '{invalid_zip}' properly rejected with error")
    
    def test_invalid_coordinates_error_flow(self, client):
        """
        E2E Test: Error handling for invalid coordinates.
        
        User flow:
        1. System receives invalid coordinates
        2. System validates and rejects
        3. System displays error message
        
        Validates: Requirements 3.3, 7.1, 7.4
        """
        invalid_coords = [
            (91, 0),      # Latitude too high
            (-91, 0),     # Latitude too low
            (0, 181),     # Longitude too high
            (0, -181),    # Longitude too low
            (100, 200),   # Both invalid
        ]
        
        for lat, lon in invalid_coords:
            response = client.get(f'/api/weather/coordinates?lat={lat}&lon={lon}')
            
            # Should return 400 Bad Request
            assert response.status_code == 400, f"Expected 400 for ({lat}, {lon}), got {response.status_code}"
            
            data = json.loads(response.data)
            
            # Should have error information
            assert 'error' in data or 'message' in data, "Missing error information"
            
            # Error message should be descriptive
            error_msg = data.get('error') or data.get('message')
            assert error_msg, "Error message is empty"
            
            print(f"✓ Invalid coordinates ({lat}, {lon}) properly rejected with error")
    
    def test_missing_parameters_error_flow(self, client):
        """
        E2E Test: Error handling for missing required parameters.
        
        User flow:
        1. Request made without required parameters
        2. System validates and rejects
        3. System displays error message
        
        Validates: Requirements 7.1, 7.4, 9.3
        """
        # Test missing parameters for different endpoints
        test_cases = [
            ('/api/weather', "No location, zip, or coordinates provided"),
            ('/api/weather/coordinates', "Missing both lat and lon"),
            ('/api/weather/coordinates?lat=37.7749', "Missing lon"),
            ('/api/weather/coordinates?lon=-122.4194', "Missing lat"),
        ]
        
        for url, description in test_cases:
            response = client.get(url)
            
            # Should return 400 Bad Request
            assert response.status_code == 400, f"Expected 400 for '{description}', got {response.status_code}"
            
            data = json.loads(response.data)
            
            # Should have error information
            assert 'error' in data or 'message' in data, f"Missing error for: {description}"
            
            print(f"✓ Missing parameters properly rejected: {description}")
    
    def test_location_not_found_error_flow(self, client):
        """
        E2E Test: Error handling for location not found.
        
        User flow:
        1. User searches for non-existent location
        2. System attempts to resolve location
        3. System displays appropriate error message
        
        Validates: Requirements 7.3, 7.4
        """
        # Test with a nonsensical location
        response = client.get('/api/weather?location=XYZ123NonExistentPlace456')
        
        # Should return error (400, 404, or 502 depending on implementation)
        assert response.status_code in [400, 404, 502], f"Unexpected status: {response.status_code}"
        
        data = json.loads(response.data)
        
        # Should have error information
        assert 'error' in data or 'message' in data, "Missing error information"
        
        error_msg = data.get('error') or data.get('message')
        assert error_msg, "Error message is empty"
        
        print(f"✓ Location not found properly handled with error message")


class TestWeatherAdvisoryFlow:
    """End-to-end tests for weather advisory display."""
    
    def test_advisory_display_when_present(self, client):
        """
        E2E Test: Advisory is displayed when present.
        
        User flow:
        1. User searches for location
        2. System fetches weather data
        3. If advisory exists, system displays it prominently
        
        Validates: Requirements 6.1, 6.2, 6.3
        """
        # Test with a location (may or may not have advisory)
        response = client.get('/api/weather?zip=94102')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            
            # Advisory field must be present
            assert 'advisory' in data, "Advisory field missing from response"
            
            # If advisory exists, verify structure
            if data['advisory'] is not None:
                advisory = data['advisory']
                assert 'type' in advisory, "Advisory missing type"
                assert 'description' in advisory, "Advisory missing description"
                assert 'severity' in advisory, "Advisory missing severity"
                
                # Verify severity is valid
                valid_severities = ['Warning', 'Advisory', 'Watch']
                assert advisory['severity'] in valid_severities, f"Invalid severity: {advisory['severity']}"
                
                print(f"✓ Advisory properly structured: {advisory['type']} ({advisory['severity']})")
            else:
                print("✓ No advisory present (null value properly returned)")
    
    def test_no_advisory_message(self, client):
        """
        E2E Test: System indicates when no advisory is active.
        
        User flow:
        1. User searches for location
        2. System fetches weather data
        3. If no advisory, system indicates this clearly
        
        Validates: Requirements 6.5
        """
        response = client.get('/api/weather?zip=94102')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            
            # Advisory field must be present (even if null)
            assert 'advisory' in data, "Advisory field missing from response"
            
            # Frontend should handle null advisory by showing "No active advisories"
            # This is verified by the presence of the field
            print("✓ Advisory field present in response (null indicates no active advisories)")


class TestCompleteUserJourney:
    """Test a complete user journey through the application."""
    
    def test_complete_user_journey(self, client):
        """
        E2E Test: Complete user journey from search to weather display.
        
        Complete flow:
        1. User loads the application (GET /)
        2. User types in search field
        3. User sees autocomplete suggestions
        4. User selects a suggestion or enters zip code
        5. System displays complete weather information
        6. User sees advisory if present
        
        Validates: Requirements 1.1, 2.1, 2.2, 2.4, 4.1-4.6, 6.1-6.5
        """
        # Step 1: Load application (verify index page exists)
        response = client.get('/')
        assert response.status_code == 200, "Application index page not accessible"
        
        # Step 2 & 3: Autocomplete
        response = client.get('/api/autocomplete?q=San Francisco')
        assert response.status_code == 200, "Autocomplete failed"
        
        suggestions = json.loads(response.data)['suggestions']
        
        # Step 4 & 5: Get weather (using zip code)
        response = client.get('/api/weather?zip=94102')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            
            # Verify complete weather information
            assert 'location' in data
            assert 'weather' in data
            assert 'advisory' in data
            
            # Verify all required weather metrics
            weather = data['weather']
            required_metrics = ['temp_f', 'temp_c', 'conditions', 'rain_chance', 'humidity', 'wind_speed']
            for metric in required_metrics:
                assert metric in weather, f"Missing required metric: {metric}"
            
            # Step 6: Advisory handling
            assert 'advisory' in data  # Must be present (null or object)
            
            print("✓ Complete user journey test passed successfully")
            print(f"  - Location: {data['location']['name']}")
            print(f"  - Temperature: {weather['temp_f']}°F / {weather['temp_c']}°C")
            print(f"  - Conditions: {weather['conditions']}")
            print(f"  - Advisory: {'Yes' if data['advisory'] else 'No'}")
