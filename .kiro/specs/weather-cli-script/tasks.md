# Implementation Plan

- [x] 1. Set up project structure and dependencies
  - Create main script file `weather.py` with proper shebang
  - Create `requirements.txt` with required packages (requests, beautifulsoup4, hypothesis)
  - Set up basic project structure with module imports
  - _Requirements: 7.5, 9.1_

- [x] 2. Implement zip code validation and management
  - _Requirements: 2.2, 2.3, 3.3, 3.4, 7.4_

- [x] 2.1 Create zip code validation function
  - Write `validate_zip_code()` function that checks for exactly 5 digits
  - _Requirements: 2.2_

- [x] 2.2 Write property test for zip code validation
  - **Property 1: Zip code validation accepts only 5-digit strings**
  - **Validates: Requirements 2.2**

- [x] 2.3 Implement cache file path resolution
  - Write `get_cache_file_path()` function using pathlib for cross-platform compatibility
  - Use `Path.home() / '.weather_cli_cache'` pattern
  - _Requirements: 3.3, 7.4_

- [x] 2.4 Write property test for cache file path validity
  - **Property 12: Cache file path is valid across platforms**
  - **Validates: Requirements 7.4**

- [x] 2.5 Implement cache read and write functions
  - Write `get_cached_zip_code()` to read from cache file
  - Write `save_cached_zip_code()` to write to cache file
  - Handle file not found and invalid content gracefully
  - _Requirements: 3.1, 3.3, 3.4_

- [x] 2.6 Write property test for caching round-trip
  - **Property 3: Valid zip codes are cached after successful retrieval**
  - **Validates: Requirements 2.4, 3.1, 3.3**

- [x] 2.7 Write property test for cached data validation
  - **Property 4: Cached zip codes are validated before use**
  - **Validates: Requirements 3.4**

- [x] 2.8 Implement zip code priority logic
  - Write `determine_zip_code()` function that implements priority: argument > cached > default (07610)
  - _Requirements: 1.1, 2.1, 3.2_

- [x] 2.9 Write property test for argument priority
  - **Property 5: Command-line argument overrides cached and default values**
  - **Validates: Requirements 2.1**

- [x] 3. Implement data models
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 8.3_

- [x] 3.1 Create WeatherData dataclass
  - Define `WeatherData` dataclass with all required fields (zip_code, temp_f, temp_c, rain_chance, humidity, wind_speed, conditions, advisory)
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 3.2 Create Advisory dataclass
  - Define `Advisory` dataclass with type, description, and severity fields
  - Implement `get_severity_rank()` method for severity comparison
  - _Requirements: 8.3, 8.4_

- [x] 3.3 Write unit tests for Advisory severity ranking
  - Test that `get_severity_rank()` correctly orders Warning > Advisory > Watch
  - _Requirements: 8.4_

- [x] 4. Implement weather scraping and parsing
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 8.1, 8.2, 8.3, 8.4, 9.1, 9.2, 9.4_

- [x] 4.1 Create HTTP request function
  - Write function to make GET request to weather.gov with proper user-agent header
  - Implement timeout handling (10 seconds)
  - Handle network errors and return appropriate error codes
  - _Requirements: 9.1, 9.4, 6.1_

- [x] 4.2 Write property test for user-agent header
  - **Property 13: HTTP requests include user-agent header**
  - **Validates: Requirements 9.4**

- [x] 4.3 Implement HTML parsing for weather data
  - Write `parse_weather_page()` function using BeautifulSoup
  - Extract temperature (F and C), rain chance, humidity, wind speed, conditions
  - Implement defensive parsing with try-except blocks
  - Calculate Celsius from Fahrenheit if needed using formula: C = (F - 32) × 5/9
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 9.2_

- [x] 4.4 Write property test for weather data extraction completeness
  - **Property 6: Weather data extraction is comprehensive**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

- [x] 4.5 Write property test for data range validation
  - **Property 14: HTML parsing extracts data correctly**
  - **Validates: Requirements 9.2**

- [x] 4.6 Implement advisory parsing
  - Write `parse_advisory()` function to extract advisory information from HTML
  - Parse advisory type, description, and severity
  - Return None if no advisory present
  - _Requirements: 8.1, 8.3_

- [x] 4.7 Implement advisory severity filtering
  - Write logic to select most severe advisory when multiple exist
  - Use `get_severity_rank()` for comparison
  - _Requirements: 8.4_

- [x] 4.8 Write property test for advisory severity selection
  - **Property 9: Most severe advisory is selected from multiple advisories**
  - **Validates: Requirements 8.4**

- [x] 4.9 Create main weather fetching function
  - Write `fetch_weather_data()` that combines HTTP request and parsing
  - Return WeatherData object with all fields populated
  - Handle parsing errors with appropriate error codes
  - _Requirements: 1.2, 6.2_

- [x] 4.10 Write unit tests for weather scraping
  - Test with sample HTML files for normal conditions
  - Test with sample HTML containing advisories
  - Test with malformed HTML for error handling
  - _Requirements: 6.2, 9.2_

- [x] 5. Implement data formatting and display
  - _Requirements: 5.1, 5.2, 5.3, 8.2, 8.5_

- [x] 5.1 Create weather output formatter
  - Write `format_weather_output()` function that creates readable display
  - Include labeled fields for all weather metrics
  - Display temperature in both F and C
  - Include zip code in output
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 5.2 Write property test for output completeness
  - **Property 7: Formatted output contains all weather metrics with labels**
  - **Validates: Requirements 5.1, 5.2, 5.3**

- [x] 5.3 Create advisory formatter
  - Write `format_advisory()` function with prominent highlighting
  - Include advisory type, description, and severity
  - Use visual separators (lines, emoji) for prominence
  - _Requirements: 8.2, 8.3_

- [x] 5.4 Write property test for advisory display completeness
  - **Property 8: Advisory display includes all required information**
  - **Validates: Requirements 8.3**

- [x] 5.5 Implement advisory presence communication
  - Ensure output always indicates advisory status (present or absent)
  - Display "No active advisories" message when none present
  - _Requirements: 8.5_

- [x] 5.6 Write property test for advisory presence communication
  - **Property 10: Advisory presence is always communicated**
  - **Validates: Requirements 8.2, 8.5**

- [x] 6. Implement error handling
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 6.1 Create error handling for invalid zip codes
  - Implement error message display for invalid zip code format
  - Exit with code 1 for validation errors
  - _Requirements: 2.3, 6.4_

- [x] 6.2 Write property test for invalid zip code exit codes
  - **Property 2: Invalid zip codes produce non-zero exit codes**
  - **Validates: Requirements 2.3**

- [x] 6.3 Implement network error handling
  - Catch connection errors and timeouts
  - Display clear network error message
  - Exit with code 2 for network errors
  - _Requirements: 6.1, 6.4_

- [x] 6.4 Implement parsing error handling
  - Catch parsing exceptions
  - Display clear parsing error message
  - Exit with code 3 for parsing errors
  - _Requirements: 6.2, 6.4_

- [x] 6.5 Implement location error handling
  - Detect when zip code returns no data
  - Display clear invalid location message
  - Exit with code 4 for location errors
  - _Requirements: 6.3, 6.4_

- [x] 6.6 Write property test for error message non-empty
  - **Property 11: Error messages are non-empty**
  - **Validates: Requirements 6.4**

- [x] 6.7 Write unit tests for error scenarios
  - Test network error handling
  - Test parsing error handling
  - Test invalid location handling
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 7. Implement CLI interface
  - _Requirements: 1.1, 1.2, 2.1, 2.4_

- [x] 7.1 Create argument parser
  - Use argparse to define optional zip code argument
  - Add help text and usage information
  - _Requirements: 2.1_

- [x] 7.2 Implement main function
  - Coordinate all modules: parse args, determine zip code, fetch weather, format output
  - Handle all error cases with appropriate exit codes
  - Cache zip code after successful retrieval
  - _Requirements: 1.1, 1.2, 2.4_

- [x] 7.3 Add script entry point
  - Add `if __name__ == "__main__":` block
  - Call main() and exit with returned code
  - _Requirements: 1.1_

- [x] 7.4 Write integration tests
  - Test end-to-end with default zip code
  - Test end-to-end with command-line argument
  - Test end-to-end with cached zip code
  - Test advisory display when present
  - _Requirements: 1.1, 1.2, 2.1, 3.2, 8.2_

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Create documentation
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 9.1 Add docstrings to all functions
  - Write clear docstrings explaining purpose, parameters, and return values
  - Include type hints in function signatures
  - _Requirements: 7.5_

- [x] 9.2 Create README file
  - Document installation instructions (pip install -r requirements.txt)
  - Explain usage with examples
  - List requirements and compatibility
  - Include example output
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 9.3 Add inline comments for complex logic
  - Comment parsing logic
  - Comment severity ranking logic
  - Comment error handling strategy
  - _Requirements: 9.2_

- [ ] 10. Final verification and polish
  - _Requirements: 7.1, 7.2, 7.3_

- [ ] 10.1 Test on multiple platforms
  - Verify execution on macOS
  - Verify execution on Linux (if available)
  - Verify execution on Windows (if available)
  - _Requirements: 7.1, 7.2, 7.3_

- [ ] 10.2 Verify all requirements are met
  - Review requirements document
  - Confirm each acceptance criterion is satisfied
  - Test edge cases manually
  - _Requirements: All_

- [ ] 10.3 Make script executable on Unix systems
  - Add shebang line: `#!/usr/bin/env python3`
  - Set executable permissions: `chmod +x weather.py`
  - _Requirements: 7.1, 7.3_

- [ ] 11. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
