"""
Location Service

This module provides location resolution and geocoding services using
the Nominatim API and weather.gov.
"""

import requests
from typing import List, Optional
from app.models.location import Location, Coordinates, LocationSuggestion
from app.utils.validators import validate_zip_code, validate_coordinates


class LocationService:
    """
    Service for resolving locations and providing autocomplete suggestions.
    
    Uses OpenStreetMap Nominatim API for geocoding and weather.gov for
    zip code resolution.
    """
    
    def __init__(self, timeout: int = 10):
        """
        Initialize the LocationService.
        
        Args:
            timeout: Request timeout in seconds (default: 10)
        """
        self.timeout = timeout
        self.nominatim_base_url = "https://nominatim.openstreetmap.org"
        self.user_agent = "WeatherWebService/1.0"
        
        # Set up session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent
        })
    
    def resolve_location(self, query: str) -> Location:
        """
        Resolve a location query to a Location object.
        
        Queries the Nominatim API with a location string and parses
        the response into a Location object.
        
        Args:
            query: Location string (e.g., "San Francisco", "New York, NY")
            
        Returns:
            Location object with coordinates and details
            
        Raises:
            ValueError: If location cannot be resolved
            requests.RequestException: If API request fails
            
        Validates: Requirements 2.4
        """
        if not query or not query.strip():
            raise ValueError("Location query cannot be empty")
        
        try:
            # Query Nominatim search API
            url = f"{self.nominatim_base_url}/search"
            params = {
                'q': query,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            results = response.json()
            
            if not results:
                raise ValueError(f"Location not found: {query}")
            
            # Parse the first result
            result = results[0]
            address = result.get('address', {})
            
            # Extract location details
            city = (address.get('city') or 
                   address.get('town') or 
                   address.get('village') or 
                   address.get('hamlet'))
            
            state = (address.get('state') or 
                    address.get('state_district'))
            
            country = address.get('country', 'Unknown')
            
            zip_code = address.get('postcode')
            
            # Create coordinates
            coordinates = Coordinates(
                lat=float(result['lat']),
                lon=float(result['lon'])
            )
            
            # Create location object
            location = Location(
                name=result.get('name', query),
                display_name=result['display_name'],
                zip_code=zip_code,
                city=city,
                state=state,
                country=country,
                coordinates=coordinates
            )
            
            return location
            
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to resolve location: {str(e)}")
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"Failed to parse location data: {str(e)}")
    
    def resolve_zip_code(self, zip_code: str) -> Location:
        """
        Resolve a US zip code to a Location object.
        
        Validates the zip code format and queries weather.gov to get
        location information and coordinates.
        
        Args:
            zip_code: 5-digit US zip code
            
        Returns:
            Location object with coordinates and details
            
        Raises:
            ValueError: If zip code is invalid or cannot be resolved
            requests.RequestException: If API request fails
            
        Validates: Requirements 2.5
        """
        # Validate zip code format
        if not validate_zip_code(zip_code):
            raise ValueError(f"Invalid zip code format: {zip_code}. Must be exactly 5 digits.")
        
        try:
            # Use Nominatim to resolve zip code (more reliable than weather.gov)
            url = f"{self.nominatim_base_url}/search"
            params = {
                'postalcode': zip_code,
                'country': 'us',
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            results = response.json()
            
            if not results:
                raise ValueError(f"Zip code not found: {zip_code}")
            
            # Parse the result
            result = results[0]
            address = result.get('address', {})
            
            # Extract location details
            city = (address.get('city') or 
                   address.get('town') or 
                   address.get('village') or 
                   address.get('hamlet'))
            
            state = address.get('state')
            country = address.get('country', 'United States')
            
            # Create coordinates
            coordinates = Coordinates(
                lat=float(result['lat']),
                lon=float(result['lon'])
            )
            
            # Create location name
            name_parts = []
            if city:
                name_parts.append(city)
            if state:
                name_parts.append(state)
            name = ', '.join(name_parts) if name_parts else zip_code
            
            # Create location object
            location = Location(
                name=name,
                display_name=result['display_name'],
                zip_code=zip_code,
                city=city,
                state=state,
                country=country,
                coordinates=coordinates
            )
            
            return location
            
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to resolve zip code: {str(e)}")
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"Failed to parse zip code data: {str(e)}")
    
    def resolve_coordinates(self, lat: float, lon: float) -> Location:
        """
        Resolve coordinates to a Location object via reverse geocoding.
        
        Validates coordinate ranges and performs reverse geocoding to
        get the location name.
        
        Args:
            lat: Latitude (-90 to 90)
            lon: Longitude (-180 to 180)
            
        Returns:
            Location object with name and coordinates
            
        Raises:
            ValueError: If coordinates are invalid
            requests.RequestException: If API request fails
            
        Validates: Requirements 3.3
        """
        # Validate coordinates
        is_valid, error_msg = validate_coordinates(lat, lon)
        if not is_valid:
            raise ValueError(error_msg)
        
        try:
            # Perform reverse geocoding
            url = f"{self.nominatim_base_url}/reverse"
            params = {
                'lat': lat,
                'lon': lon,
                'format': 'json',
                'addressdetails': 1
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            
            if 'error' in result:
                raise ValueError(f"Could not resolve coordinates: {result['error']}")
            
            # Parse address details
            address = result.get('address', {})
            
            # Extract location details
            city = (address.get('city') or 
                   address.get('town') or 
                   address.get('village') or 
                   address.get('hamlet'))
            
            state = (address.get('state') or 
                    address.get('state_district'))
            
            country = address.get('country', 'Unknown')
            
            zip_code = address.get('postcode')
            
            # Create coordinates object
            coordinates = Coordinates(lat=lat, lon=lon)
            
            # Create location name
            name_parts = []
            if city:
                name_parts.append(city)
            if state:
                name_parts.append(state)
            name = ', '.join(name_parts) if name_parts else f"{lat}, {lon}"
            
            # Create location object
            location = Location(
                name=name,
                display_name=result.get('display_name', f"{lat}, {lon}"),
                zip_code=zip_code,
                city=city,
                state=state,
                country=country,
                coordinates=coordinates
            )
            
            return location
            
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to resolve coordinates: {str(e)}")
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"Failed to parse coordinate data: {str(e)}")
    
    def get_autocomplete_suggestions(self, query: str) -> List[LocationSuggestion]:
        """
        Get autocomplete suggestions for a location query.
        
        Queries the Nominatim search API, parses and ranks results by
        relevance, and returns up to 10 suggestions.
        
        Args:
            query: Partial location string
            
        Returns:
            List of LocationSuggestion objects (max 10)
            
        Raises:
            requests.RequestException: If API request fails
            
        Validates: Requirements 2.2, 2.3
        """
        if not query or not query.strip():
            return []
        
        try:
            # Query Nominatim search API
            url = f"{self.nominatim_base_url}/search"
            params = {
                'q': query,
                'format': 'json',
                'limit': 10,
                'addressdetails': 1
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            results = response.json()
            
            suggestions = []
            for result in results[:10]:  # Limit to top 10
                address = result.get('address', {})
                
                # Determine suggestion type
                suggestion_type = 'city'
                if address.get('postcode'):
                    suggestion_type = 'zip'
                elif address.get('country') and not address.get('city'):
                    suggestion_type = 'country'
                
                # Extract zip code if available
                zip_code = address.get('postcode')
                
                # Create coordinates
                coordinates = Coordinates(
                    lat=float(result['lat']),
                    lon=float(result['lon'])
                )
                
                # Create suggestion
                suggestion = LocationSuggestion(
                    display_name=result['display_name'],
                    type=suggestion_type,
                    zip_code=zip_code,
                    coordinates=coordinates
                )
                
                suggestions.append(suggestion)
            
            return suggestions
            
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to get autocomplete suggestions: {str(e)}")
        except (KeyError, ValueError, TypeError) as e:
            # Return empty list on parsing errors rather than failing
            return []
