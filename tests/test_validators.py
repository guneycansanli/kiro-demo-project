"""
Property-based and unit tests for validation utilities.

Tests validation functions for zip codes and coordinates using
property-based testing with Hypothesis.
"""

import unittest
from hypothesis import given, settings, strategies as st
from app.utils.validators import validate_zip_code, validate_coordinates


class TestZipCodeValidation(unittest.TestCase):
    """Property-based tests for zip code validation."""
    
    @settings(max_examples=100)
    @given(st.text())
    def test_zip_code_validation_property(self, input_string: str):
        """
        Feature: weather-web-service, Property 4: Zip code validation accepts only 5-digit strings
        
        For any input string, the zip code validation should return true if and only if
        the string contains exactly 5 digits.
        
        Validates: Requirements 2.5
        """
        result = validate_zip_code(input_string)
        
        # Check if the string is exactly 5 digits
        is_five_digits = (
            len(input_string) == 5 and 
            all(c.isdigit() for c in input_string)
        )
        
        # The validation result should match our expectation
        self.assertEqual(result, is_five_digits)
    
    def test_valid_zip_codes(self):
        """Test that valid 5-digit zip codes pass validation."""
        valid_zips = ["12345", "00000", "99999", "90210", "10001"]
        for zip_code in valid_zips:
            with self.subTest(zip_code=zip_code):
                self.assertTrue(validate_zip_code(zip_code))
    
    def test_invalid_zip_codes(self):
        """Test that invalid zip codes fail validation."""
        invalid_zips = [
            "1234",      # Too short
            "123456",    # Too long
            "abcde",     # Letters
            "12 45",     # Space
            "12-45",     # Hyphen
            "",          # Empty
            "12.45",     # Decimal
        ]
        for zip_code in invalid_zips:
            with self.subTest(zip_code=zip_code):
                self.assertFalse(validate_zip_code(zip_code))
    
    def test_non_string_input(self):
        """Test that non-string inputs return False."""
        self.assertFalse(validate_zip_code(12345))
        self.assertFalse(validate_zip_code(None))
        self.assertFalse(validate_zip_code([1, 2, 3, 4, 5]))


class TestCoordinateValidation(unittest.TestCase):
    """Property-based tests for coordinate validation."""
    
    @settings(max_examples=100)
    @given(
        lat=st.one_of(
            st.floats(min_value=-90, max_value=90),
            st.floats(min_value=-1000, max_value=-90.1),
            st.floats(min_value=90.1, max_value=1000)
        ),
        lon=st.one_of(
            st.floats(min_value=-180, max_value=180),
            st.floats(min_value=-1000, max_value=-180.1),
            st.floats(min_value=180.1, max_value=1000)
        )
    )
    def test_coordinate_validation_property(self, lat: float, lon: float):
        """
        Feature: weather-web-service, Property 5: Geolocation coordinates fetch weather data
        
        For any latitude and longitude values, the coordinate validation should return
        true if and only if latitude is in [-90, 90] and longitude is in [-180, 180].
        
        Validates: Requirements 3.3
        """
        is_valid, error_msg = validate_coordinates(lat, lon)
        
        # Determine expected validity
        lat_valid = -90 <= lat <= 90
        lon_valid = -180 <= lon <= 180
        expected_valid = lat_valid and lon_valid
        
        # Check that validation result matches expectation
        self.assertEqual(is_valid, expected_valid)
        
        # If invalid, there should be an error message
        if not is_valid:
            self.assertNotEqual(error_msg, "")
        else:
            self.assertEqual(error_msg, "")
    
    def test_valid_coordinates(self):
        """Test that valid coordinates pass validation."""
        valid_coords = [
            (0, 0),           # Equator, Prime Meridian
            (37.7749, -122.4194),  # San Francisco
            (-33.8688, 151.2093),  # Sydney
            (90, 180),        # Boundary values
            (-90, -180),      # Boundary values
            (45.5, 90.5),     # Mid-range values
        ]
        for lat, lon in valid_coords:
            with self.subTest(lat=lat, lon=lon):
                is_valid, error_msg = validate_coordinates(lat, lon)
                self.assertTrue(is_valid)
                self.assertEqual(error_msg, "")
    
    def test_invalid_latitude(self):
        """Test that invalid latitude values fail validation."""
        invalid_lats = [
            (91, 0),
            (-91, 0),
            (100, 0),
            (-100, 0),
        ]
        for lat, lon in invalid_lats:
            with self.subTest(lat=lat, lon=lon):
                is_valid, error_msg = validate_coordinates(lat, lon)
                self.assertFalse(is_valid)
                self.assertIn("Latitude", error_msg)
    
    def test_invalid_longitude(self):
        """Test that invalid longitude values fail validation."""
        invalid_lons = [
            (0, 181),
            (0, -181),
            (0, 200),
            (0, -200),
        ]
        for lat, lon in invalid_lons:
            with self.subTest(lat=lat, lon=lon):
                is_valid, error_msg = validate_coordinates(lat, lon)
                self.assertFalse(is_valid)
                self.assertIn("Longitude", error_msg)
    
    def test_non_numeric_coordinates(self):
        """Test that non-numeric inputs fail validation."""
        is_valid, error_msg = validate_coordinates("37.7749", -122.4194)
        self.assertFalse(is_valid)
        self.assertIn("number", error_msg)
        
        is_valid, error_msg = validate_coordinates(37.7749, "-122.4194")
        self.assertFalse(is_valid)
        self.assertIn("number", error_msg)


if __name__ == '__main__':
    unittest.main()
