"""
Location Data Models

This module defines data models for location information.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Coordinates:
    """Geographic coordinates."""
    lat: float
    lon: float


@dataclass
class Location:
    """Location information with coordinates."""
    name: str
    display_name: str
    zip_code: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: str
    coordinates: Coordinates


@dataclass
class LocationSuggestion:
    """Autocomplete suggestion for location search."""
    display_name: str
    type: str  # "city", "zip", "country"
    zip_code: Optional[str]
    coordinates: Coordinates
