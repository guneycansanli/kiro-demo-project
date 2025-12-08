"""
Validation utilities for input data.

This module provides validation functions for user inputs including
zip codes and geographic coordinates.
"""

import re
from typing import Tuple


def validate_zip_code(zip_code: str) -> bool:
    """
    Validate that a zip code is exactly 5 digits.
    
    Args:
        zip_code: String to validate as a US zip code
        
    Returns:
        True if the zip code is exactly 5 digits, False otherwise
        
    Validates: Requirements 2.5
    """
    if not isinstance(zip_code, str):
        return False
    
    # Check if the string is exactly 5 digits
    return bool(re.match(r'^\d{5}$', zip_code))


def validate_coordinates(lat: float, lon: float) -> Tuple[bool, str]:
    """
    Validate that latitude and longitude are within valid ranges.
    
    Latitude must be between -90 and 90 (inclusive).
    Longitude must be between -180 and 180 (inclusive).
    
    Args:
        lat: Latitude value to validate
        lon: Longitude value to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if coordinates are valid, False otherwise
        - error_message: Empty string if valid, error description if invalid
        
    Validates: Requirements 3.3
    """
    # Validate latitude range
    if not isinstance(lat, (int, float)):
        return False, "Latitude must be a number"
    
    if lat < -90 or lat > 90:
        return False, f"Latitude must be between -90 and 90, got {lat}"
    
    # Validate longitude range
    if not isinstance(lon, (int, float)):
        return False, "Longitude must be a number"
    
    if lon < -180 or lon > 180:
        return False, f"Longitude must be between -180 and 180, got {lon}"
    
    return True, ""
