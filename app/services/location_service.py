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
        
        Queries the Nominatim search API with enhanced parameters for better
        worldwide coverage, parses and ranks results by relevance, and returns
        up to 10 suggestions prioritizing cities and countries.
        
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
            # Query Nominatim search API with enhanced parameters for worldwide coverage
            url = f"{self.nominatim_base_url}/search"
            params = {
                'q': query,
                'format': 'json',
                'limit': 20,  # Get more results to filter and rank
                'addressdetails': 1,
                # Accept multiple languages for international coverage
                'accept-language': 'en'
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            results = response.json()
            
            suggestions = []
            seen_locations = set()  # Track unique locations to avoid duplicates
            
            # Process and rank results
            for result in results:
                address = result.get('address', {})
                osm_type = result.get('osm_type', '')
                place_class = result.get('class', '')
                place_type = result.get('type', '')
                
                # Skip non-relevant results (like roads, buildings, etc.)
                if place_class in ['highway', 'building', 'amenity', 'shop', 'tourism']:
                    continue
                
                # Determine suggestion type and priority
                suggestion_type, priority = self._classify_location_type(address, place_class, place_type)
                
                # If we couldn't classify it with our enhanced logic, fall back to simple classification
                if not suggestion_type:
                    suggestion_type, priority = self._simple_classify_location(address, place_class, place_type)
                
                # Skip if we still couldn't classify it
                if not suggestion_type:
                    continue
                
                # Create a clean display name
                display_name = self._create_clean_display_name(address, result.get('display_name', ''))
                
                # Create a unique key to avoid duplicates
                location_key = f"{display_name.lower()}_{suggestion_type}"
                if location_key in seen_locations:
                    continue
                seen_locations.add(location_key)
                
                # Extract zip code if available
                zip_code = address.get('postcode')
                
                # Create coordinates
                coordinates = Coordinates(
                    lat=float(result['lat']),
                    lon=float(result['lon'])
                )
                
                # Create suggestion with priority for sorting
                suggestion = LocationSuggestion(
                    display_name=display_name,
                    type=suggestion_type,
                    zip_code=zip_code,
                    coordinates=coordinates
                )
                
                # Add priority for sorting (lower number = higher priority)
                suggestion._priority = priority
                
                suggestions.append(suggestion)
            
            # Sort by priority (cities first, then countries, then others)
            suggestions.sort(key=lambda x: getattr(x, '_priority', 999))
            
            # Return top 10 suggestions
            return suggestions[:10]
            
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to get autocomplete suggestions: {str(e)}")
        except (KeyError, ValueError, TypeError) as e:
            # Return empty list on parsing errors rather than failing
            return []
    
    def _classify_location_type(self, address: dict, place_class: str, place_type: str) -> tuple:
        """
        Classify a location and assign priority for ranking.
        
        Args:
            address: Address components from Nominatim
            place_class: OSM class
            place_type: OSM type
            
        Returns:
            Tuple of (suggestion_type, priority) or (None, None) if not relevant
        """
        # Check for postal codes first
        if address.get('postcode') and place_class == 'place' and place_type == 'postcode':
            return 'postal_code', 4
        
        # Major cities (highest priority)
        if place_class == 'place' and place_type in ['city', 'metropolis']:
            return 'city', 1
        
        # Towns and smaller cities
        if place_class == 'place' and place_type in ['town', 'municipality']:
            return 'city', 2
        
        # Villages and smaller settlements
        if place_class == 'place' and place_type in ['village', 'hamlet', 'suburb', 'neighbourhood']:
            return 'city', 3
        
        # Countries (high priority for international searches)
        if place_class == 'place' and place_type == 'country':
            return 'country', 2
        
        # States/provinces
        if place_class == 'place' and place_type in ['state', 'province']:
            return 'state', 3
        
        # Administrative boundaries that represent cities/regions
        if place_class == 'boundary' and place_type == 'administrative':
            admin_level = address.get('admin_level')
            if admin_level in ['4', '6', '8']:  # State/province, county, city level
                if address.get('city') or address.get('town'):
                    return 'city', 2
                elif address.get('state'):
                    return 'state', 3
        
        # Islands (for places like Hawaii, Malta, etc.)
        if place_class == 'place' and place_type == 'island':
            return 'region', 3
        
        # Skip irrelevant types
        return None, None
    
    def _create_clean_display_name(self, address: dict, full_display_name: str) -> str:
        """
        Create a clean, user-friendly display name for autocomplete.
        
        Args:
            address: Address components from Nominatim
            full_display_name: Full display name from Nominatim
            
        Returns:
            Clean display name
        """
        # Extract key components
        city = (address.get('city') or 
               address.get('town') or 
               address.get('village') or 
               address.get('hamlet') or
               address.get('municipality'))
        
        state = (address.get('state') or 
                address.get('state_district') or
                address.get('province'))
        
        country = address.get('country')
        
        # Build clean name
        name_parts = []
        
        if city:
            name_parts.append(city)
        
        # Add state for US locations, or for disambiguation
        if state and country:
            if country.lower() in ['united states', 'usa', 'us']:
                # For US, always show state
                name_parts.append(state)
            elif len(name_parts) == 0:
                # If no city, show state
                name_parts.append(state)
        
        # Add country for international locations or if it's the main result
        if country:
            if len(name_parts) == 0:
                # Country-only result
                name_parts.append(country)
            elif country.lower() not in ['united states', 'usa', 'us']:
                # International location - show country
                name_parts.append(country)
        
        # If we couldn't build a clean name, use the first part of the full name
        if not name_parts:
            first_part = full_display_name.split(',')[0].strip()
            name_parts.append(first_part)
        
        return ', '.join(name_parts)
    
    def _simple_classify_location(self, address: dict, place_class: str, place_type: str) -> tuple:
        """
        Simple fallback classification for locations.
        
        Args:
            address: Address components from Nominatim
            place_class: OSM class
            place_type: OSM type
            
        Returns:
            Tuple of (suggestion_type, priority) or (None, None) if not relevant
        """
        # Check for postal codes
        if address.get('postcode'):
            return 'postal_code', 4
        
        # Check for cities/towns in address
        if address.get('city') or address.get('town') or address.get('village'):
            return 'city', 2
        
        # Check for countries
        if address.get('country') and not (address.get('city') or address.get('town')):
            return 'country', 2
        
        # Check for states/provinces
        if address.get('state') and not (address.get('city') or address.get('town')):
            return 'state', 3
        
        # Default to location if we have coordinates
        return 'city', 5
