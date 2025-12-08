"""
Data Models Package

This package contains all data model definitions.
"""

from app.models.location import Location, Coordinates, LocationSuggestion
from app.models.weather import WeatherData
from app.models.advisory import Advisory

__all__ = [
    'Location',
    'Coordinates',
    'LocationSuggestion',
    'WeatherData',
    'Advisory'
]
