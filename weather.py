#!/usr/bin/env python3
"""
Weather CLI Script

A cross-platform command-line tool that retrieves and displays current weather
information for a given zip code by scraping data from weather.gov.
"""

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup


# Data Models
@dataclass
class Advisory:
    """Weather advisory information."""
    type: str
    description: str
    severity: str
    
    def get_severity_rank(self) -> int:
        """Return numeric rank for severity comparison.
        
        Returns:
            int: Higher number = more severe (Warning=3, Advisory=2, Watch=1)
        """
        severity_map = {
            'warning': 3,
            'advisory': 2,
            'watch': 1
        }
        return severity_map.get(self.severity.lower(), 0)


@dataclass
class WeatherData:
    """Complete weather information for a location."""
    zip_code: str
    temp_f: float
    temp_c: float
    rain_chance: int
    humidity: int
    wind_speed: str
    conditions: str
    advisory: Optional[Advisory] = None


# Zip Code Validation and Management
def validate_zip_code(zip_code: str) -> bool:
    """Validate that zip code is exactly 5 digits.
    
    Args:
        zip_code: String to validate as a zip code
        
    Returns:
        bool: True if zip_code is exactly 5 digits, False otherwise
    """
    return len(zip_code) == 5 and zip_code.isdigit()


def get_cache_file_path() -> Path:
    """Get platform-appropriate cache file path.
    
    Returns:
        Path: Path to cache file in user's home directory
    """
    return Path.home() / '.weather_cli_cache'


def get_cached_zip_code() -> Optional[str]:
    """Read cached zip code from file.
    
    Returns:
        Optional[str]: Cached zip code if valid, None otherwise
    """
    cache_path = get_cache_file_path()
    try:
        if cache_path.exists():
            cached_value = cache_path.read_text().strip()
            # Validate cached value before returning
            if validate_zip_code(cached_value):
                return cached_value
    except (IOError, OSError):
        # Handle file read errors gracefully
        pass
    return None


def save_cached_zip_code(zip_code: str) -> None:
    """Save zip code to cache file.
    
    Args:
        zip_code: Valid 5-digit zip code to cache
    """
    cache_path = get_cache_file_path()
    try:
        cache_path.write_text(zip_code)
    except (IOError, OSError):
        # Handle file write errors gracefully
        pass


def determine_zip_code(arg_zip: Optional[str]) -> str:
    """Determine which zip code to use based on priority.
    
    Priority: argument > cached > default (07610)
    
    Args:
        arg_zip: Zip code from command-line argument (if provided)
        
    Returns:
        str: The zip code to use
    """
    # Priority 1: Command-line argument
    if arg_zip is not None:
        return arg_zip
    
    # Priority 2: Cached zip code
    cached = get_cached_zip_code()
    if cached is not None:
        return cached
    
    # Priority 3: Default zip code
    return "07610"


def make_weather_request(zip_code: str) -> str:
    """Make HTTP GET request to weather.gov for given zip code.
    
    Args:
        zip_code: 5-digit zip code to fetch weather for
        
    Returns:
        str: HTML content from weather.gov
        
    Raises:
        requests.exceptions.RequestException: For network errors
        requests.exceptions.Timeout: For timeout errors
    """
    url = f"https://forecast.weather.gov/zipcity.php?inputstring={zip_code}"
    headers = {
        'User-Agent': 'WeatherCLI/1.0 (Educational Project)'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.Timeout:
        raise
    except requests.exceptions.RequestException:
        raise


def fetch_weather_data(zip_code: str) -> WeatherData:
    """Fetch and parse weather data for given zip code.
    
    Combines HTTP request and HTML parsing to retrieve complete weather information.
    
    Args:
        zip_code: 5-digit zip code to fetch weather for
        
    Returns:
        WeatherData: Complete weather information including advisory if present
        
    Raises:
        requests.exceptions.RequestException: For network errors
        requests.exceptions.Timeout: For timeout errors
        ValueError: For parsing errors
    """
    try:
        # Make HTTP request
        html = make_weather_request(zip_code)
        
        # Parse the HTML
        weather_data = parse_weather_page(html, zip_code)
        
        return weather_data
        
    except requests.exceptions.Timeout:
        raise
    except requests.exceptions.RequestException:
        raise
    except ValueError:
        raise


def parse_weather_page(html: str, zip_code: str) -> WeatherData:
    """Parse weather information from HTML.
    
    Args:
        html: HTML content from weather.gov
        zip_code: Zip code being queried
        
    Returns:
        WeatherData: Parsed weather information
        
    Raises:
        ValueError: If required weather data cannot be extracted
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    try:
        # === PARSING LOGIC: Temperature Extraction ===
        # Weather.gov displays current temperature in a <p> tag with class 'myforecast-current-lrg'
        # The text format is typically "72°F" which we need to parse into a numeric value
        temp_f = None
        temp_elem = soup.find('p', class_='myforecast-current-lrg')
        if temp_elem:
            temp_text = temp_elem.get_text().strip()
            # Extract numeric value (e.g., "72°F" -> 72)
            # Remove both degree symbols and 'F' to handle various formats
            temp_f = float(temp_text.replace('°F', '').replace('°', '').strip())
        
        # Temperature is required - fail if we couldn't extract it
        if temp_f is None:
            raise ValueError("Could not extract temperature")
        
        # Calculate Celsius from Fahrenheit using standard conversion formula: C = (F - 32) × 5/9
        # Round to 1 decimal place for readability
        temp_c = round((temp_f - 32) * 5 / 9, 1)
        
        # === PARSING LOGIC: Weather Conditions ===
        # Current conditions are in a <p> tag with class 'myforecast-current'
        conditions = "Unknown"
        conditions_elem = soup.find('p', class_='myforecast-current')
        if conditions_elem:
            conditions = conditions_elem.get_text().strip()
        
        # === PARSING LOGIC: Detailed Weather Metrics ===
        # Initialize with default values in case parsing fails
        rain_chance = 0
        humidity = 0
        wind_speed = "Unknown"
        
        # Weather.gov provides detailed info in the 'detailed-forecast-body' div
        # We use regex patterns to extract specific metrics from the text content
        detail_table = soup.find('div', id='detailed-forecast-body')
        if detail_table:
            text_content = detail_table.get_text()
            import re
            
            # Rain/precipitation chance: Look for patterns like "20% chance" or "chance of rain 20%"
            # Use flexible regex to handle various phrasings
            rain_match = re.search(r'(?:chance|precipitation).*?(\d+)%|(\d+)%.*?(?:chance|precipitation)', text_content, re.IGNORECASE)
            if rain_match:
                # Extract whichever group matched (group 1 or group 2)
                rain_chance = int(rain_match.group(1) or rain_match.group(2))
            
            # Humidity: Look for "Humidity: 65%" or "Humidity 65%"
            humidity_match = re.search(r'humidity[:\s]*(\d+)%', text_content, re.IGNORECASE)
            if humidity_match:
                humidity = int(humidity_match.group(1))
            
            # Wind speed: Look for patterns like "Wind 10 mph" or "Wind 10 to 15 mph"
            # Capture both single values and ranges
            wind_match = re.search(r'wind[:\s]*[a-z]*\s*(\d+(?:\s*to\s*\d+)?)\s*mph', text_content, re.IGNORECASE)
            if wind_match:
                wind_speed = wind_match.group(1) + " mph"
        
        # === PARSING LOGIC: Fallback to Current Conditions Section ===
        # If we didn't find metrics in detailed forecast, try the current conditions summary
        # This provides redundancy in case the page structure varies
        current_conditions = soup.find('div', id='current_conditions-summary')
        if current_conditions:
            # Only look for humidity if we haven't found it yet
            if humidity == 0:
                humidity_elem = current_conditions.find(string=re.compile(r'Humidity', re.IGNORECASE))
                if humidity_elem:
                    parent = humidity_elem.find_parent()
                    if parent:
                        humidity_text = parent.get_text()
                        humidity_match = re.search(r'(\d+)%', humidity_text)
                        if humidity_match:
                            humidity = int(humidity_match.group(1))
            
            # Only look for wind if we haven't found it yet
            if wind_speed == "Unknown":
                wind_elem = current_conditions.find(string=re.compile(r'Wind', re.IGNORECASE))
                if wind_elem:
                    parent = wind_elem.find_parent()
                    if parent:
                        wind_text = parent.get_text()
                        wind_match = re.search(r'(\d+(?:\s*to\s*\d+)?)\s*mph', wind_text)
                        if wind_match:
                            wind_speed = wind_match.group(1) + " mph"
        
        # Parse advisory if present
        advisory = parse_advisory(html)
        
        return WeatherData(
            zip_code=zip_code,
            temp_f=temp_f,
            temp_c=temp_c,
            rain_chance=rain_chance,
            humidity=humidity,
            wind_speed=wind_speed,
            conditions=conditions,
            advisory=advisory
        )
        
    except (AttributeError, ValueError, TypeError) as e:
        raise ValueError(f"Failed to parse weather data: {e}")


def parse_advisory(html: str) -> Optional[Advisory]:
    """Extract advisory information if present.
    
    If multiple advisories are present, returns the most severe one.
    Severity ranking: Warning > Advisory > Watch
    
    Args:
        html: HTML content from weather.gov
        
    Returns:
        Optional[Advisory]: Most severe advisory if present, None otherwise
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    try:
        # === PARSING LOGIC: Advisory Detection ===
        # Weather.gov displays advisories in divs with classes containing keywords like
        # 'alert', 'warning', or 'hazard'. We use a lambda function to flexibly match these.
        alert_divs = soup.find_all('div', class_=lambda x: x and ('alert' in x.lower() or 'warning' in x.lower() or 'hazard' in x.lower()))
        
        # Fallback: Try alternative selectors if the class-based search didn't work
        # Some pages use id attributes instead of classes for alerts
        if not alert_divs:
            alert_divs = soup.find_all(['div', 'section'], attrs={'id': lambda x: x and ('alert' in x.lower() or 'hazard' in x.lower())})
        
        # No advisories found
        if not alert_divs:
            return None
        
        # === PARSING LOGIC: Extract Advisory Details ===
        # Collect all advisories found on the page (there may be multiple)
        advisories = []
        
        for alert_div in alert_divs:
            # Advisory type is typically in a heading element (h1-h4) or strong tag
            heading = alert_div.find(['h1', 'h2', 'h3', 'h4', 'strong'])
            if not heading:
                continue  # Skip if no heading found
            
            advisory_type = heading.get_text().strip()
            
            # Get the full description (all text content from the alert div)
            description = alert_div.get_text().strip()
            
            # === SEVERITY RANKING LOGIC ===
            # Determine severity level from the advisory type text
            # National Weather Service uses standard terminology:
            #   - "Warning" = most severe (imminent threat)
            #   - "Advisory" = moderate severity (conditions may cause inconvenience)
            #   - "Watch" = least severe (conditions possible but not certain)
            severity = "Advisory"  # Default to middle severity
            type_lower = advisory_type.lower()
            if 'warning' in type_lower:
                severity = "Warning"
            elif 'watch' in type_lower:
                severity = "Watch"
            elif 'advisory' in type_lower:
                severity = "Advisory"
            
            advisories.append(Advisory(
                type=advisory_type,
                description=description,
                severity=severity
            ))
        
        if not advisories:
            return None
        
        # === SEVERITY RANKING LOGIC: Select Most Severe ===
        # When multiple advisories exist, we only display the most severe one
        # Use the get_severity_rank() method which returns: Warning=3, Advisory=2, Watch=1
        # The max() function with key parameter finds the advisory with highest rank
        most_severe = max(advisories, key=lambda a: a.get_severity_rank())
        return most_severe
        
    except (AttributeError, TypeError):
        # Gracefully handle parsing errors - return None if advisory parsing fails
        return None


def format_weather_output(weather: WeatherData) -> str:
    """Format weather data into readable display.
    
    Args:
        weather: WeatherData object containing all weather information
        
    Returns:
        str: Formatted weather output with labeled fields
    """
    output_lines = []
    
    # Add advisory if present (will be formatted separately)
    if weather.advisory:
        output_lines.append(format_advisory(weather.advisory))
        output_lines.append("")  # Blank line separator
    
    # Weather information header
    output_lines.append(f"Weather for {weather.zip_code}:")
    output_lines.append("")
    
    # Temperature (both F and C)
    output_lines.append(f"Temperature:     {weather.temp_f}°F ({weather.temp_c}°C)")
    
    # Conditions
    output_lines.append(f"Conditions:      {weather.conditions}")
    
    # Rain chance
    output_lines.append(f"Rain Chance:     {weather.rain_chance}%")
    
    # Humidity
    output_lines.append(f"Humidity:        {weather.humidity}%")
    
    # Wind speed
    output_lines.append(f"Wind Speed:      {weather.wind_speed}")
    
    # Advisory status message if no advisory
    if not weather.advisory:
        output_lines.append("")
        output_lines.append("No active advisories.")
    
    return "\n".join(output_lines)


def format_advisory(advisory: Advisory) -> str:
    """Format advisory with highlighting.
    
    Args:
        advisory: Advisory object containing alert information
        
    Returns:
        str: Formatted advisory with prominent visual highlighting
    """
    separator = "=" * 80
    
    output_lines = []
    output_lines.append(separator)
    output_lines.append("WEATHER ADVISORY ACTIVE")
    output_lines.append(separator)
    
    # Add emoji for visual prominence
    emoji = "⚠️ "
    
    # Advisory type with severity
    output_lines.append(f"{emoji} {advisory.type}")
    
    # Description
    output_lines.append(advisory.description)
    
    output_lines.append(separator)
    
    return "\n".join(output_lines)


def parse_arguments() -> argparse.Namespace:
    """Parse and return command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description='Retrieve and display current weather information for a given zip code.'
    )
    parser.add_argument(
        'zip_code',
        nargs='?',
        default=None,
        help='5-digit US zip code (optional)'
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point. Returns exit code.
    
    Returns:
        int: Exit code (0 for success, non-zero for errors)
            1 - Invalid zip code format
            2 - Network error
            3 - Parsing error
            4 - Invalid location
    """
    # Parse command-line arguments
    args = parse_arguments()
    
    # Determine which zip code to use (argument > cached > default)
    zip_code = determine_zip_code(args.zip_code)
    
    # Validate the zip code before making any network requests
    if not validate_zip_code(zip_code):
        print(f"Error: Invalid zip code '{zip_code}'. Zip code must be exactly 5 digits.", 
              file=sys.stderr)
        return 1
    
    # === ERROR HANDLING STRATEGY ===
    # We use specific exception types to determine the appropriate exit code:
    # - Timeout/RequestException -> Exit code 2 (network errors)
    # - ValueError with location keywords -> Exit code 4 (invalid location)
    # - Other ValueError -> Exit code 3 (parsing errors)
    # - Unexpected exceptions -> Exit code 3 (general errors)
    try:
        # Fetch weather data from weather.gov
        weather_data = fetch_weather_data(zip_code)
        
        # Cache the zip code after successful retrieval for future use
        save_cached_zip_code(zip_code)
        
        # Format and display the output
        output = format_weather_output(weather_data)
        print(output)
        
        return 0
        
    except requests.exceptions.Timeout:
        # Network timeout - user's connection may be slow or weather.gov is down
        print("Error: Unable to connect to weather service. Please check your internet connection.", 
              file=sys.stderr)
        return 2
    except requests.exceptions.RequestException:
        # Other network errors (connection refused, DNS failure, etc.)
        print("Error: Unable to connect to weather service. Please check your internet connection.", 
              file=sys.stderr)
        return 2
    except ValueError as e:
        # ValueError can indicate either a location error or parsing error
        # Check the error message to distinguish between them
        if "no weather data" in str(e).lower() or "invalid location" in str(e).lower():
            # Location error - zip code exists but has no weather data
            print(f"Error: No weather data found for zip code '{zip_code}'. Please verify the zip code is valid.", 
                  file=sys.stderr)
            return 4
        else:
            # Parsing error - couldn't extract required data from HTML
            print("Error: Unable to parse weather data. The weather service may have changed.", 
                  file=sys.stderr)
            return 3
    except Exception as e:
        # Catch-all for unexpected errors - treat as parsing/general errors
        print(f"Error: An unexpected error occurred: {e}", 
              file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
