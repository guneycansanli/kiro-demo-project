# Design Document

## Overview

The weather CLI script will be implemented in Python, which provides excellent cross-platform compatibility and robust libraries for web scraping and HTML parsing. Python is pre-installed on macOS and most Linux distributions, and easily installable on Windows. The script will use the `requests` library for HTTP operations and `BeautifulSoup` for HTML parsing. Weather data will be scraped from weather.gov (National Weather Service), which provides comprehensive weather information including advisories without requiring API keys.

The script will follow a modular design with clear separation between:
- Command-line argument parsing and validation
- Web scraping and data extraction
- Data formatting and display
- Cache management

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│  CLI Interface  │
│  (argparse)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Zip Code       │
│  Manager        │
│  - Validation   │
│  - Caching      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Weather        │
│  Scraper        │
│  - HTTP Request │
│  - HTML Parsing │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Data           │
│  Formatter      │
│  - Display      │
└─────────────────┘
```

### Component Flow

1. **CLI Interface**: Parses command-line arguments and determines which zip code to use
2. **Zip Code Manager**: Validates zip codes, manages cache file operations
3. **Weather Scraper**: Makes HTTP requests to weather.gov and extracts weather data
4. **Data Formatter**: Formats and displays weather information with proper highlighting

## Components and Interfaces

### 1. CLI Interface Module

**Responsibilities:**
- Parse command-line arguments
- Coordinate between other modules
- Handle top-level error handling and exit codes

**Interface:**
```python
def main() -> int:
    """Main entry point. Returns exit code."""
    
def parse_arguments() -> argparse.Namespace:
    """Parse and return command-line arguments."""
```

### 2. Zip Code Manager Module

**Responsibilities:**
- Validate zip code format (5 digits)
- Read and write cached zip code
- Determine which zip code to use (argument > cached > default)

**Interface:**
```python
def validate_zip_code(zip_code: str) -> bool:
    """Validate that zip code is exactly 5 digits."""
    
def get_cached_zip_code() -> Optional[str]:
    """Read cached zip code from file."""
    
def save_cached_zip_code(zip_code: str) -> None:
    """Save zip code to cache file."""
    
def get_cache_file_path() -> Path:
    """Get platform-appropriate cache file path."""
    
def determine_zip_code(arg_zip: Optional[str]) -> str:
    """Determine which zip code to use based on priority."""
```

### 3. Weather Scraper Module

**Responsibilities:**
- Make HTTP requests to weather.gov
- Parse HTML to extract weather data
- Extract advisory information
- Handle network and parsing errors

**Interface:**
```python
class WeatherData:
    """Data class for weather information."""
    zip_code: str
    temp_f: float
    temp_c: float
    rain_chance: int
    humidity: int
    wind_speed: str
    conditions: str
    advisory: Optional[Advisory]

class Advisory:
    """Data class for weather advisory."""
    type: str
    description: str
    severity: str

def fetch_weather_data(zip_code: str) -> WeatherData:
    """Fetch and parse weather data for given zip code."""
    
def parse_weather_page(html: str) -> WeatherData:
    """Parse weather information from HTML."""
    
def parse_advisory(html: str) -> Optional[Advisory]:
    """Extract advisory information if present."""
```

### 4. Data Formatter Module

**Responsibilities:**
- Format weather data for display
- Highlight advisories prominently
- Ensure readable output across platforms

**Interface:**
```python
def format_weather_output(weather: WeatherData) -> str:
    """Format weather data into readable display."""
    
def format_advisory(advisory: Advisory) -> str:
    """Format advisory with highlighting."""
```

## Data Models

### WeatherData

```python
@dataclass
class WeatherData:
    """Complete weather information for a location."""
    zip_code: str
    temp_f: float
    temp_c: float
    rain_chance: int  # Percentage 0-100
    humidity: int  # Percentage 0-100
    wind_speed: str  # e.g., "10 mph"
    conditions: str  # e.g., "Partly Cloudy"
    advisory: Optional[Advisory] = None
```

### Advisory

```python
@dataclass
class Advisory:
    """Weather advisory information."""
    type: str  # e.g., "Heat Advisory", "Wind Warning"
    description: str  # Full advisory text
    severity: str  # e.g., "Warning", "Advisory", "Watch"
    
    def get_severity_rank(self) -> int:
        """Return numeric rank for severity comparison."""
        # Warning > Advisory > Watch
```

### Cache File Format

The cache file will be stored as plain text containing only the 5-digit zip code:
- Location: `~/.weather_cli_cache`
- Format: Single line with 5-digit zip code
- Example: `07610`

## 
Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Zip code validation accepts only 5-digit strings

*For any* input string, the validation function should return true if and only if the string contains exactly 5 digits (0-9) and nothing else.

**Validates: Requirements 2.2**

### Property 2: Invalid zip codes produce non-zero exit codes

*For any* invalid zip code input (not exactly 5 digits), the script should exit with a non-zero status code and display an error message.

**Validates: Requirements 2.3**

### Property 3: Valid zip codes are cached after successful retrieval

*For any* valid 5-digit zip code, after successfully retrieving weather data, the zip code should be written to the cache file and be readable on subsequent reads.

**Validates: Requirements 2.4, 3.1, 3.3**

### Property 4: Cached zip codes are validated before use

*For any* content in the cache file, if the content is not exactly 5 digits, it should be rejected and not used as the zip code.

**Validates: Requirements 3.4**

### Property 5: Command-line argument overrides cached and default values

*For any* valid zip code provided as a command-line argument, that zip code should be used regardless of whether a cached zip code exists or what the default is.

**Validates: Requirements 2.1**

### Property 6: Weather data extraction is comprehensive

*For any* valid weather.gov HTML response, the parser should extract all required fields: temperature (F and C), rain chance, humidity, wind speed, and conditions description.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

### Property 7: Formatted output contains all weather metrics with labels

*For any* WeatherData object, the formatted output should contain labeled fields for temperature (both F and C), rain chance, humidity, wind speed, conditions, and the zip code.

**Validates: Requirements 5.1, 5.2, 5.3**

### Property 8: Advisory display includes all required information

*For any* Advisory object, the formatted output should contain the advisory type, full description, and severity information.

**Validates: Requirements 8.3**

### Property 9: Most severe advisory is selected from multiple advisories

*For any* collection of multiple Advisory objects with different severity levels, only the advisory with the highest severity rank (Warning > Advisory > Watch) should be included in the WeatherData.

**Validates: Requirements 8.4**

### Property 10: Advisory presence is always communicated

*For any* weather data retrieval, the output should either display an active advisory prominently or indicate that no advisories are active.

**Validates: Requirements 8.2, 8.5**

### Property 11: Error messages are non-empty

*For any* error condition (network failure, parsing failure, invalid location), the error message displayed to the user should be a non-empty string that describes the error type.

**Validates: Requirements 6.4**

### Property 12: Cache file path is valid across platforms

*For any* platform (macOS, Windows, Linux), the cache file path resolution should return a valid, writable path in the user's home directory.

**Validates: Requirements 7.4**

### Property 13: HTTP requests include user-agent header

*For any* HTTP request made by the weather scraper, the request headers should include a user-agent field that identifies the script.

**Validates: Requirements 9.4**

### Property 14: HTML parsing extracts data correctly

*For any* valid weather.gov HTML page, parsing should successfully extract weather data without raising exceptions, and all extracted numeric values should be within reasonable ranges (e.g., temperature between -100°F and 150°F, percentages between 0-100).

**Validates: Requirements 9.2**

## Error Handling

### Error Categories

1. **Input Validation Errors**
   - Invalid zip code format (not 5 digits)
   - Corrupted cache file
   - Exit code: 1
   - Message format: "Error: Invalid zip code '{zip_code}'. Zip code must be exactly 5 digits."

2. **Network Errors**
   - Cannot connect to weather.gov
   - Timeout errors
   - Exit code: 2
   - Message format: "Error: Unable to connect to weather service. Please check your internet connection."

3. **Parsing Errors**
   - HTML structure changed
   - Missing expected data fields
   - Exit code: 3
   - Message format: "Error: Unable to parse weather data. The weather service may have changed."

4. **Location Errors**
   - Zip code not found
   - No weather data available for location
   - Exit code: 4
   - Message format: "Error: No weather data found for zip code '{zip_code}'. Please verify the zip code is valid."

### Error Handling Strategy

- All errors should be caught at the appropriate level
- Error messages should be written to stderr
- Exit codes should be consistent and documented
- Network operations should have reasonable timeouts (10 seconds)
- Parsing errors should not crash the script
- Cache file errors should fall back to default zip code

## Testing Strategy

### Unit Testing

The script will use Python's built-in `unittest` framework for unit testing. Unit tests will cover:

**Zip Code Manager:**
- Validation function with valid and invalid inputs
- Cache file read/write operations
- Zip code priority logic (argument > cached > default)
- Platform-specific path resolution

**Weather Scraper:**
- HTML parsing with sample weather.gov pages
- Advisory extraction and severity ranking
- Error handling for malformed HTML
- Data extraction completeness

**Data Formatter:**
- Output formatting with various weather data
- Advisory highlighting
- Field label presence
- Temperature unit display

**Error Handling:**
- Network error simulation
- Invalid location handling
- Parsing error handling

### Property-Based Testing

The script will use the `hypothesis` library for property-based testing. Each property-based test will run a minimum of 100 iterations to ensure thorough coverage.

**Property Test Configuration:**
```python
from hypothesis import given, settings
import hypothesis.strategies as st

@settings(max_examples=100)
@given(st.text())
def test_property(input_data):
    # Test implementation
    pass
```

**Property Test Requirements:**
- Each property-based test must be tagged with a comment referencing the design document property
- Tag format: `# Feature: weather-cli-script, Property {number}: {property_text}`
- Each correctness property must be implemented by exactly one property-based test
- Tests should use appropriate Hypothesis strategies for generating test data

**Property Tests to Implement:**

1. **Zip code validation** (Property 1)
   - Strategy: Generate random strings of various lengths and character types
   - Verify only 5-digit strings pass validation

2. **Caching round-trip** (Property 3)
   - Strategy: Generate random valid zip codes
   - Verify write then read returns same value

3. **Cached data validation** (Property 4)
   - Strategy: Generate random strings for cache file content
   - Verify invalid content is rejected

4. **Argument priority** (Property 5)
   - Strategy: Generate random valid zip codes for argument and cache
   - Verify argument always wins

5. **Output completeness** (Property 7)
   - Strategy: Generate random WeatherData objects
   - Verify all required fields and labels present in output

6. **Advisory severity ranking** (Property 9)
   - Strategy: Generate lists of advisories with random severities
   - Verify highest severity is selected

7. **Error message non-empty** (Property 11)
   - Strategy: Trigger various error conditions
   - Verify all error messages are non-empty strings

8. **Path validity** (Property 12)
   - Strategy: Test on available platforms
   - Verify paths are valid and writable

9. **Data range validation** (Property 14)
   - Strategy: Parse various HTML samples
   - Verify extracted values are within reasonable ranges

### Integration Testing

Integration tests will verify the complete flow:
- End-to-end execution with default zip code
- End-to-end execution with command-line argument
- End-to-end execution with cached zip code
- Advisory display when present
- Error handling for network failures

### Test Data

Sample HTML files from weather.gov will be saved for testing:
- Normal weather conditions
- Weather with active advisory
- Weather with multiple advisories
- Edge cases (extreme temperatures, 0% rain, 100% humidity)

## Implementation Notes

### Web Scraping Considerations

**Target Website:** weather.gov (National Weather Service)
- URL pattern: `https://forecast.weather.gov/zipcity.php?inputstring={zip_code}`
- Advantages: No API key required, comprehensive data, includes advisories
- Considerations: HTML structure may change, requiring parser updates

**Parsing Strategy:**
- Use BeautifulSoup with html.parser
- Identify data by CSS classes and element structure
- Implement defensive parsing with try-except blocks
- Validate extracted data types and ranges

**Advisory Detection:**
- Look for hazard/warning banners in HTML
- Extract advisory type from heading elements
- Parse full description from advisory text
- Determine severity from advisory type keywords

### Cross-Platform Compatibility

**File Paths:**
- Use `pathlib.Path` for all file operations
- Cache location: `Path.home() / '.weather_cli_cache'`
- Works identically on Windows, macOS, and Linux

**Dependencies:**
- `requests`: HTTP library (cross-platform)
- `beautifulsoup4`: HTML parsing (cross-platform)
- `hypothesis`: Property-based testing (cross-platform)
- All dependencies available via pip on all platforms

**Execution:**
- Script should be executable with: `python weather.py [zip_code]`
- Shebang line: `#!/usr/bin/env python3` for Unix-like systems
- Windows users can run with: `python weather.py [zip_code]`

### Temperature Conversion

Fahrenheit to Celsius conversion formula:
```
C = (F - 32) × 5/9
```

If weather.gov provides only Fahrenheit, the script will calculate Celsius. If both are provided, use the provided values.

### Output Format Example

```
================================================================================
WEATHER ADVISORY ACTIVE
================================================================================
⚠️  HEAT ADVISORY
Excessive heat warning in effect until 8:00 PM EDT this evening.
Heat index values up to 105 expected. Drink plenty of fluids, stay in an
air-conditioned room, and check on relatives and neighbors.
================================================================================

Weather for 07610:

Temperature:     92°F (33°C)
Conditions:      Partly Cloudy
Rain Chance:     20%
Humidity:        65%
Wind Speed:      8 mph SW

No active advisories.
```

## Dependencies

### Required Python Packages

```
requests>=2.31.0
beautifulsoup4>=4.12.0
hypothesis>=6.90.0  # For property-based testing
```

### Python Version

- Minimum: Python 3.8
- Recommended: Python 3.10+
- Rationale: Dataclasses (3.7+), pathlib improvements, type hints

## Future Enhancements

Potential features for future versions:
- Extended forecast (3-5 days)
- Multiple location support
- Configuration file for preferences
- Colored terminal output
- JSON output mode for scripting
- Historical weather data
- Severe weather alerts with notifications
