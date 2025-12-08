"""
Weather Data Models

This module defines data models for weather information.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from app.models.location import Location
from app.models.advisory import Advisory


@dataclass
class WeatherData:
    """Complete weather information for a location."""
    location: Location
    temp_f: float
    temp_c: float
    conditions: str
    rain_chance: int
    humidity: int
    wind_speed: str
    advisory: Optional[Advisory]
    timestamp: datetime
