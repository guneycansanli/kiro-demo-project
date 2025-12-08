"""
Weather Service

This module provides weather data scraping from weather.gov.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional, List
from app.models.weather import WeatherData
from app.models.location import Location
from app.models.advisory import Advisory
from app.services.location_service import LocationService


class WeatherService:
    """
    Service for fetching and parsing weather data from weather.gov.
    
    Scrapes weather information including temperature, conditions, and advisories
    from the National Weather Service website.
    """
    
    def __init__(self, timeout: int = 10):
        """
        Initialize the WeatherService.
        
        Sets up HTTP client with proper user-agent header and timeout.
        
        Args:
            timeout: Request timeout in seconds (default: 10)
            
        Validates: Requirements 4.1
        """
        self.timeout = timeout
        self.user_agent = "WeatherWebService/1.0 (Educational Project)"
        
        # Set up session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        
        # Initialize location service for resolving locations
        self.location_service = LocationService(timeout=timeout)

    def get_weather_by_location(self, query: str) -> WeatherData:
        """
        Get weather data for a location query.
        
        Resolves the location query to coordinates, then fetches and parses
        weather data from weather.gov.
        
        Args:
            query: Location string (e.g., "San Francisco", "New York, NY")
            
        Returns:
            WeatherData object with complete weather information
            
        Raises:
            ValueError: If location cannot be resolved
            requests.RequestException: If weather data cannot be fetched
            
        Validates: Requirements 2.4, 4.1
        """
        # Resolve location to get coordinates
        location = self.location_service.resolve_location(query)
        
        # Fetch weather data using coordinates
        return self.get_weather_by_coordinates(
            location.coordinates.lat,
            location.coordinates.lon
        )

    def get_weather_by_coordinates(self, lat: float, lon: float) -> WeatherData:
        """
        Get weather data for specific coordinates.
        
        Builds weather.gov URL from coordinates, makes HTTP request with proper
        headers, and parses the response HTML.
        
        Args:
            lat: Latitude (-90 to 90)
            lon: Longitude (-180 to 180)
            
        Returns:
            WeatherData object with complete weather information
            
        Raises:
            ValueError: If coordinates are invalid or weather data cannot be parsed
            requests.RequestException: If HTTP request fails
            
        Validates: Requirements 3.3, 4.1
        """
        # Resolve coordinates to location for display name
        location = self.location_service.resolve_coordinates(lat, lon)
        
        # Build weather.gov URL
        # Format: https://forecast.weather.gov/MapClick.php?lat=LAT&lon=LON
        url = f"https://forecast.weather.gov/MapClick.php"
        params = {
            'lat': lat,
            'lon': lon
        }
        
        try:
            # Make HTTP request
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse the HTML response
            weather_data = self.parse_weather_page(response.text, location)
            
            return weather_data
            
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to fetch weather data: {str(e)}")

    def parse_weather_page(self, html: str, location: Location) -> WeatherData:
        """
        Parse weather data from weather.gov HTML page.
        
        Extracts temperature (F and C), conditions, rain chance, humidity,
        wind speed, and advisories using BeautifulSoup. Handles missing data
        gracefully by using default values.
        
        Args:
            html: HTML content from weather.gov
            location: Location object for the weather data
            
        Returns:
            WeatherData object with parsed information
            
        Raises:
            ValueError: If critical data cannot be extracted
            
        Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract temperature in Fahrenheit
        temp_f = None
        temp_elem = soup.find('p', class_='myforecast-current-lrg')
        if temp_elem:
            temp_text = temp_elem.get_text(strip=True)
            # Extract numeric value (e.g., "65°F" -> 65)
            try:
                temp_f = float(temp_text.replace('°F', '').replace('°', '').strip())
            except (ValueError, AttributeError):
                pass
        
        # If not found, try alternative selector
        if temp_f is None:
            temp_elem = soup.find('p', class_='myforecast-current')
            if temp_elem:
                temp_text = temp_elem.get_text(strip=True)
                try:
                    temp_f = float(temp_text.replace('°F', '').replace('°', '').strip())
                except (ValueError, AttributeError):
                    pass
        
        if temp_f is None:
            raise ValueError("Could not extract temperature from weather page")
        
        # Convert to Celsius
        temp_c = round((temp_f - 32) * 5 / 9, 1)
        
        # Extract conditions
        conditions = "Unknown"
        conditions_elem = soup.find('p', class_='myforecast-current-sm')
        if conditions_elem:
            conditions = conditions_elem.get_text(strip=True)
        
        # Extract detailed weather metrics
        # These are typically in a table or list format
        rain_chance = 0
        humidity = 0
        wind_speed = "Unknown"
        
        # Look for detailed forecast information
        detail_elems = soup.find_all('td')
        for elem in detail_elems:
            text = elem.get_text(strip=True).lower()
            
            # Extract rain chance
            if 'chance' in text and '%' in text:
                try:
                    # Extract percentage (e.g., "Chance of Rain: 30%" -> 30)
                    import re
                    match = re.search(r'(\d+)%', text)
                    if match:
                        rain_chance = int(match.group(1))
                except (ValueError, AttributeError):
                    pass
            
            # Extract humidity
            if 'humidity' in text and '%' in text:
                try:
                    import re
                    match = re.search(r'(\d+)%', text)
                    if match:
                        humidity = int(match.group(1))
                except (ValueError, AttributeError):
                    pass
            
            # Extract wind speed
            if 'wind' in text and 'mph' in text:
                try:
                    import re
                    match = re.search(r'(\d+)\s*mph', text)
                    if match:
                        wind_speed = f"{match.group(1)} mph"
                except (ValueError, AttributeError):
                    pass
        
        # Also check in the detailed forecast text
        forecast_text_elem = soup.find('div', class_='forecast-text')
        if forecast_text_elem:
            forecast_text = forecast_text_elem.get_text(strip=True).lower()
            
            # Extract rain chance from forecast text
            if rain_chance == 0:
                import re
                match = re.search(r'(\d+)\s*percent', forecast_text)
                if match:
                    rain_chance = int(match.group(1))
            
            # Extract wind speed from forecast text
            if wind_speed == "Unknown":
                import re
                match = re.search(r'(\d+)\s*(?:to\s*\d+\s*)?mph', forecast_text)
                if match:
                    wind_speed = f"{match.group(0)}"
        
        # Parse advisory if present
        advisory = self.parse_advisory(html)
        
        # Create WeatherData object
        weather_data = WeatherData(
            location=location,
            temp_f=temp_f,
            temp_c=temp_c,
            conditions=conditions,
            rain_chance=rain_chance,
            humidity=humidity,
            wind_speed=wind_speed,
            advisory=advisory,
            timestamp=datetime.now()
        )
        
        return weather_data

    def parse_advisory(self, html: str) -> Optional[Advisory]:
        """
        Parse weather advisory from HTML page.
        
        Searches for advisory elements in the HTML, extracts advisory type,
        description, and severity. When multiple advisories exist, selects
        the most severe using get_severity_rank().
        
        Args:
            html: HTML content from weather.gov
            
        Returns:
            Most severe Advisory object if found, None otherwise
            
        Validates: Requirements 6.1, 6.3, 6.4
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Collect all potential advisory elements
        advisory_elems = []
        
        # Look for various advisory/warning elements
        advisory_elems.extend(soup.find_all('div', class_='alert'))
        advisory_elems.extend(soup.find_all('div', class_='warning'))
        advisory_elems.extend(soup.find_all('div', class_='watch'))
        advisory_elems.extend(soup.find_all('div', class_='advisory'))
        
        # Also check for hazards section
        hazards_elem = soup.find('div', id='hazards')
        if hazards_elem:
            advisory_elems.append(hazards_elem)
        
        if not advisory_elems:
            return None
        
        # Parse all advisories
        advisories: List[Advisory] = []
        
        for advisory_elem in advisory_elems:
            advisory_text = advisory_elem.get_text(strip=True)
            
            if not advisory_text:
                continue
            
            # Determine advisory type and severity
            advisory_type = "Weather Advisory"
            severity = "Advisory"
            
            text_lower = advisory_text.lower()
            
            # Check for warning (highest severity)
            if 'warning' in text_lower:
                severity = "Warning"
                # Try to extract specific warning type
                if 'heat warning' in text_lower:
                    advisory_type = "Heat Warning"
                elif 'winter warning' in text_lower:
                    advisory_type = "Winter Weather Warning"
                elif 'storm warning' in text_lower:
                    advisory_type = "Storm Warning"
                elif 'flood warning' in text_lower:
                    advisory_type = "Flood Warning"
                else:
                    advisory_type = "Weather Warning"
            
            # Check for watch (lower severity)
            elif 'watch' in text_lower:
                severity = "Watch"
                if 'heat watch' in text_lower:
                    advisory_type = "Heat Watch"
                elif 'winter watch' in text_lower:
                    advisory_type = "Winter Weather Watch"
                elif 'storm watch' in text_lower:
                    advisory_type = "Storm Watch"
                elif 'flood watch' in text_lower:
                    advisory_type = "Flood Watch"
                else:
                    advisory_type = "Weather Watch"
            
            # Check for advisory (medium severity)
            elif 'advisory' in text_lower:
                severity = "Advisory"
                if 'heat advisory' in text_lower:
                    advisory_type = "Heat Advisory"
                elif 'winter advisory' in text_lower:
                    advisory_type = "Winter Weather Advisory"
                elif 'wind advisory' in text_lower:
                    advisory_type = "Wind Advisory"
                else:
                    advisory_type = "Weather Advisory"
            
            # Create Advisory object
            advisory = Advisory(
                type=advisory_type,
                description=advisory_text,
                severity=severity
            )
            
            advisories.append(advisory)
        
        if not advisories:
            return None
        
        # Select the most severe advisory using get_severity_rank()
        # Higher rank = more severe
        most_severe = max(advisories, key=lambda a: a.get_severity_rank())
        
        return most_severe
