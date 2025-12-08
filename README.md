# Weather CLI Script

A cross-platform command-line tool that retrieves and displays current weather information for a given US zip code by scraping data from weather.gov (National Weather Service).

## Features

- 🌡️ Current temperature in both Fahrenheit and Celsius
- 🌧️ Chance of rain percentage
- 💧 Humidity levels
- 💨 Wind speed and direction
- ☁️ Current weather conditions
- ⚠️ Active weather advisories and warnings
- 💾 Automatic caching of last used zip code
- 🖥️ Cross-platform support (macOS, Windows, Linux)

## Requirements

- Python 3.8 or higher
- Internet connection

### Dependencies

- `requests` - HTTP library for making web requests
- `beautifulsoup4` - HTML parsing library
- `hypothesis` - Property-based testing framework (for development/testing)

## Installation

1. Clone or download this repository

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the script without arguments to get weather for the default location (07610):

```bash
python weather.py
```

### Specify a Zip Code

Provide a 5-digit US zip code as an argument:

```bash
python weather.py 90210
```

### Cached Zip Code

After successfully retrieving weather for a zip code, the script automatically caches it. On subsequent runs without arguments, it will use the cached zip code instead of the default.

## Example Output

### Normal Weather Conditions

```
Weather for 07610:

Temperature:     72°F (22.2°C)
Conditions:      Partly Cloudy
Rain Chance:     20%
Humidity:        65%
Wind Speed:      8 mph

No active advisories.
```

### Weather with Advisory

```
================================================================================
WEATHER ADVISORY ACTIVE
================================================================================
⚠️  HEAT ADVISORY
Excessive heat warning in effect until 8:00 PM EDT this evening.
Heat index values up to 105 expected. Drink plenty of fluids, stay in an
air-conditioned room, and check on relatives and neighbors.
================================================================================

Weather for 90210:

Temperature:     92°F (33.3°C)
Conditions:      Sunny
Rain Chance:     5%
Humidity:        45%
Wind Speed:      12 mph

```

## Exit Codes

The script uses different exit codes to indicate various error conditions:

- `0` - Success
- `1` - Invalid zip code format (not exactly 5 digits)
- `2` - Network error (unable to connect to weather service)
- `3` - Parsing error (unable to extract weather data)
- `4` - Invalid location (zip code not found)

## Platform Compatibility

This script is designed to work on:

- **macOS** - Tested and fully supported
- **Linux** - Tested and fully supported
- **Windows** - Fully supported

The script uses platform-independent libraries and file path handling to ensure compatibility across all major operating systems.

## How It Works

1. **Zip Code Priority**: The script determines which zip code to use based on priority:
   - Command-line argument (highest priority)
   - Cached zip code from previous run
   - Default zip code (07610)

2. **Data Retrieval**: Makes an HTTP request to weather.gov with the selected zip code

3. **HTML Parsing**: Extracts weather data from the HTML response using BeautifulSoup

4. **Advisory Detection**: Checks for active weather advisories and displays the most severe one if multiple exist

5. **Caching**: Saves the successfully used zip code to `~/.weather_cli_cache` for future use

6. **Display**: Formats and displays all weather information in a readable format

## Development

### Running Tests

The project includes comprehensive unit tests and property-based tests:

```bash
python -m pytest test_weather.py -v
```

### Testing Strategy

- **Unit Tests**: Verify specific functionality and edge cases
- **Property-Based Tests**: Use Hypothesis to test properties across many random inputs
- **Integration Tests**: Test end-to-end workflows

## Limitations

- Requires internet connection to fetch weather data
- Depends on weather.gov HTML structure (may break if website changes)
- Only supports US zip codes
- No API key required, but subject to weather.gov rate limits

## Future Enhancements

Potential features for future versions:

- Extended forecast (3-5 days)
- Multiple location support
- Configuration file for user preferences
- Colored terminal output
- JSON output mode for scripting
- Historical weather data
- Severe weather alert notifications

## License

This is an educational project. Use at your own discretion.

## Acknowledgments

Weather data provided by the National Weather Service (weather.gov).
