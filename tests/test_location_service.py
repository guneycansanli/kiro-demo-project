"""
Property-based and unit tests for LocationService.

This module tests location resolution, geocoding, and autocomplete functionality.
"""

import pytest
from hypothesis import given, settings, strategies as st, assume
from app.services.location_service import LocationService
from app.models.location import LocationSuggestion
import requests


class TestLocationServiceProperties:
    """Property-based tests for LocationService."""
    
    @settings(max_examples=100, deadline=None)
    @given(st.text(min_size=1, max_size=50).filter(lambda x: x.strip() and x.isascii()))
    def test_autocomplete_returns_suggestions_for_nonempty_query(self, query):
        """
        Feature: weather-web-service, Property 2: Autocomplete suggestions for search input
        
        For any non-empty search query, the autocomplete endpoint should return
        a list of location suggestions.
        
        Validates: Requirements 2.2
        """
        # Filter out queries that are likely to cause issues
        assume(len(query.strip()) >= 2)
        assume(not all(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/~`' for c in query))
        
        service = LocationService(timeout=5)
        
        try:
            suggestions = service.get_autocomplete_suggestions(query)
            
            # Should return a list
            assert isinstance(suggestions, list), f"Expected list, got {type(suggestions)}"
            
            # All items should be LocationSuggestion objects
            for suggestion in suggestions:
                assert isinstance(suggestion, LocationSuggestion), \
                    f"Expected LocationSuggestion, got {type(suggestion)}"
                assert isinstance(suggestion.display_name, str), \
                    "display_name must be a string"
                assert len(suggestion.display_name) > 0, \
                    "display_name must not be empty"
                assert suggestion.type in ['city', 'zip', 'country'], \
                    f"Invalid suggestion type: {suggestion.type}"
                assert hasattr(suggestion, 'coordinates'), \
                    "Suggestion must have coordinates"
                assert hasattr(suggestion.coordinates, 'lat'), \
                    "Coordinates must have lat"
                assert hasattr(suggestion.coordinates, 'lon'), \
                    "Coordinates must have lon"
                assert -90 <= suggestion.coordinates.lat <= 90, \
                    f"Invalid latitude: {suggestion.coordinates.lat}"
                assert -180 <= suggestion.coordinates.lon <= 180, \
                    f"Invalid longitude: {suggestion.coordinates.lon}"
            
            # Should not exceed 10 suggestions
            assert len(suggestions) <= 10, \
                f"Too many suggestions: {len(suggestions)}"
            
        except requests.RequestException as e:
            # Network errors are acceptable in property tests
            # We're testing the contract, not the external API reliability
            pytest.skip(f"Network error during test: {e}")
        except Exception as e:
            # Re-raise other exceptions
            raise



class TestLocationServiceUnit:
    """Unit tests for LocationService."""
    
    def test_empty_query_returns_empty_suggestions(self):
        """Test that empty queries return empty suggestion lists."""
        service = LocationService()
        
        assert service.get_autocomplete_suggestions("") == []
        assert service.get_autocomplete_suggestions("   ") == []
    
    def test_resolve_location_rejects_empty_query(self):
        """Test that resolve_location raises ValueError for empty queries."""
        service = LocationService()
        
        with pytest.raises(ValueError, match="Location query cannot be empty"):
            service.resolve_location("")
        
        with pytest.raises(ValueError, match="Location query cannot be empty"):
            service.resolve_location("   ")
    
    def test_resolve_zip_code_validates_format(self):
        """Test that resolve_zip_code validates zip code format."""
        service = LocationService()
        
        # Invalid formats should raise ValueError
        with pytest.raises(ValueError, match="Invalid zip code format"):
            service.resolve_zip_code("1234")  # Too short
        
        with pytest.raises(ValueError, match="Invalid zip code format"):
            service.resolve_zip_code("123456")  # Too long
        
        with pytest.raises(ValueError, match="Invalid zip code format"):
            service.resolve_zip_code("abcde")  # Not digits
        
        with pytest.raises(ValueError, match="Invalid zip code format"):
            service.resolve_zip_code("12-345")  # Contains non-digits
    
    def test_resolve_coordinates_validates_ranges(self):
        """Test that resolve_coordinates validates coordinate ranges."""
        service = LocationService()
        
        # Invalid latitude
        with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
            service.resolve_coordinates(91.0, 0.0)
        
        with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
            service.resolve_coordinates(-91.0, 0.0)
        
        # Invalid longitude
        with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
            service.resolve_coordinates(0.0, 181.0)
        
        with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
            service.resolve_coordinates(0.0, -181.0)
    
    def test_location_service_has_correct_timeout(self):
        """Test that LocationService initializes with correct timeout."""
        service = LocationService(timeout=15)
        assert service.timeout == 15
        
        service_default = LocationService()
        assert service_default.timeout == 10
    
    def test_location_service_has_user_agent(self):
        """Test that LocationService sets proper User-Agent header."""
        service = LocationService()
        assert 'User-Agent' in service.session.headers
        assert service.session.headers['User-Agent'] == "WeatherWebService/1.0"
