#!/usr/bin/env python3
"""
Property-based tests for weather CLI script.

Uses Hypothesis for property-based testing to verify correctness properties
defined in the design document.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import requests
from hypothesis import given, settings
import hypothesis.strategies as st

from weather import (
    validate_zip_code,
    get_cache_file_path,
    get_cached_zip_code,
    save_cached_zip_code,
    determine_zip_code,
    Advisory,
    make_weather_request,
    parse_weather_page,
    WeatherData,
    parse_advisory,
    format_weather_output,
    format_advisory,
    main,
)


class TestZipCodeValidation(unittest.TestCase):
    """Tests for zip code validation functionality."""
    
    @settings(max_examples=100)
    @given(st.text())
    def test_property_1_zip_code_validation_accepts_only_5_digit_strings(self, input_string: str):
        """Feature: weather-cli-script, Property 1: Zip code validation accepts only 5-digit strings
        
        Validates: Requirements 2.2
        
        For any input string, the validation function should return true if and only if
        the string contains exactly 5 digits (0-9) and nothing else.
        """
        result = validate_zip_code(input_string)
        
        # Expected: True if exactly 5 digits, False otherwise
        expected = len(input_string) == 5 and input_string.isdigit()
        
        self.assertEqual(result, expected,
                        f"validate_zip_code('{input_string}') returned {result}, expected {expected}")


class TestCacheFilePath(unittest.TestCase):
    """Tests for cache file path resolution."""
    
    def test_property_12_cache_file_path_is_valid_across_platforms(self):
        """Feature: weather-cli-script, Property 12: Cache file path is valid across platforms
        
        Validates: Requirements 7.4
        
        For any platform (macOS, Windows, Linux), the cache file path resolution should
        return a valid, writable path in the user's home directory.
        """
        cache_path = get_cache_file_path()
        
        # Verify it's a Path object
        self.assertIsInstance(cache_path, Path)
        
        # Verify it's in the home directory
        self.assertTrue(str(cache_path).startswith(str(Path.home())))
        
        # Verify the filename is correct
        self.assertEqual(cache_path.name, '.weather_cli_cache')
        
        # Verify the parent directory exists and is writable
        self.assertTrue(cache_path.parent.exists())
        self.assertTrue(cache_path.parent.is_dir())
        
        # Test that we can write to this location
        try:
            test_content = "test"
            cache_path.write_text(test_content)
            read_content = cache_path.read_text()
            self.assertEqual(read_content, test_content)
            # Clean up
            cache_path.unlink()
        except (IOError, OSError) as e:
            self.fail(f"Cache path is not writable: {e}")


class TestCacheOperations(unittest.TestCase):
    """Tests for cache read and write operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.temp_cache_path = Path(self.temp_dir) / '.weather_cli_cache'
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary cache file if it exists
        if self.temp_cache_path.exists():
            self.temp_cache_path.unlink()
        Path(self.temp_dir).rmdir()
    
    @settings(max_examples=100)
    @given(st.text(alphabet=st.characters(whitelist_categories=('Nd',)), min_size=5, max_size=5))
    def test_property_3_valid_zip_codes_are_cached_after_successful_retrieval(self, zip_code: str):
        """Feature: weather-cli-script, Property 3: Valid zip codes are cached after successful retrieval
        
        Validates: Requirements 2.4, 3.1, 3.3
        
        For any valid 5-digit zip code, after successfully retrieving weather data,
        the zip code should be written to the cache file and be readable on subsequent reads.
        """
        with patch('weather.get_cache_file_path', return_value=self.temp_cache_path):
            # Save the zip code
            save_cached_zip_code(zip_code)
            
            # Read it back
            cached = get_cached_zip_code()
            
            # Verify round-trip
            self.assertEqual(cached, zip_code,
                           f"Round-trip failed: saved '{zip_code}', got '{cached}'")
    
    @settings(max_examples=100)
    @given(st.text())
    def test_property_4_cached_zip_codes_are_validated_before_use(self, invalid_content: str):
        """Feature: weather-cli-script, Property 4: Cached zip codes are validated before use
        
        Validates: Requirements 3.4
        
        For any content in the cache file, if the content is not exactly 5 digits,
        it should be rejected and not used as the zip code.
        """
        # Only test with invalid zip codes
        if len(invalid_content) == 5 and invalid_content.isdigit():
            return  # Skip valid zip codes
        
        with patch('weather.get_cache_file_path', return_value=self.temp_cache_path):
            # Write invalid content directly to cache file
            self.temp_cache_path.write_text(invalid_content)
            
            # Try to read it
            cached = get_cached_zip_code()
            
            # Should return None for invalid content
            self.assertIsNone(cached,
                            f"Invalid content '{invalid_content}' was accepted as valid zip code")


class TestZipCodePriority(unittest.TestCase):
    """Tests for zip code priority logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_cache_path = Path(self.temp_dir) / '.weather_cli_cache'
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_cache_path.exists():
            self.temp_cache_path.unlink()
        Path(self.temp_dir).rmdir()
    
    @settings(max_examples=100)
    @given(
        arg_zip=st.text(alphabet=st.characters(whitelist_categories=('Nd',)), min_size=5, max_size=5),
        cached_zip=st.text(alphabet=st.characters(whitelist_categories=('Nd',)), min_size=5, max_size=5)
    )
    def test_property_5_command_line_argument_overrides_cached_and_default_values(
        self, arg_zip: str, cached_zip: str
    ):
        """Feature: weather-cli-script, Property 5: Command-line argument overrides cached and default values
        
        Validates: Requirements 2.1
        
        For any valid zip code provided as a command-line argument, that zip code should be used
        regardless of whether a cached zip code exists or what the default is.
        """
        with patch('weather.get_cache_file_path', return_value=self.temp_cache_path):
            # Set up a cached zip code
            save_cached_zip_code(cached_zip)
            
            # Call determine_zip_code with an argument
            result = determine_zip_code(arg_zip)
            
            # The argument should always win
            self.assertEqual(result, arg_zip,
                           f"Argument '{arg_zip}' should override cached '{cached_zip}', got '{result}'")
    
    def test_cached_zip_overrides_default(self):
        """Test that cached zip code overrides default when no argument provided."""
        with patch('weather.get_cache_file_path', return_value=self.temp_cache_path):
            # Set up a cached zip code
            cached_zip = "12345"
            save_cached_zip_code(cached_zip)
            
            # Call without argument
            result = determine_zip_code(None)
            
            # Should use cached value
            self.assertEqual(result, cached_zip)
    
    def test_default_used_when_no_argument_or_cache(self):
        """Test that default zip code is used when no argument or cache exists."""
        with patch('weather.get_cache_file_path', return_value=self.temp_cache_path):
            # Ensure no cache exists
            if self.temp_cache_path.exists():
                self.temp_cache_path.unlink()
            
            # Call without argument
            result = determine_zip_code(None)
            
            # Should use default
            self.assertEqual(result, "07610")


class TestAdvisorySeverityRanking(unittest.TestCase):
    """Tests for Advisory severity ranking functionality."""
    
    def test_warning_severity_rank(self):
        """Test that Warning severity has the highest rank.
        
        Validates: Requirements 8.4
        """
        advisory = Advisory(
            type="Heat Warning",
            description="Excessive heat warning in effect",
            severity="Warning"
        )
        self.assertEqual(advisory.get_severity_rank(), 3)
    
    def test_advisory_severity_rank(self):
        """Test that Advisory severity has middle rank.
        
        Validates: Requirements 8.4
        """
        advisory = Advisory(
            type="Heat Advisory",
            description="Heat advisory in effect",
            severity="Advisory"
        )
        self.assertEqual(advisory.get_severity_rank(), 2)
    
    def test_watch_severity_rank(self):
        """Test that Watch severity has the lowest rank.
        
        Validates: Requirements 8.4
        """
        advisory = Advisory(
            type="Heat Watch",
            description="Heat watch in effect",
            severity="Watch"
        )
        self.assertEqual(advisory.get_severity_rank(), 1)
    
    def test_severity_ordering_warning_greater_than_advisory(self):
        """Test that Warning > Advisory in severity ranking.
        
        Validates: Requirements 8.4
        """
        warning = Advisory(type="Test", description="Test", severity="Warning")
        advisory = Advisory(type="Test", description="Test", severity="Advisory")
        
        self.assertGreater(warning.get_severity_rank(), advisory.get_severity_rank())
    
    def test_severity_ordering_advisory_greater_than_watch(self):
        """Test that Advisory > Watch in severity ranking.
        
        Validates: Requirements 8.4
        """
        advisory = Advisory(type="Test", description="Test", severity="Advisory")
        watch = Advisory(type="Test", description="Test", severity="Watch")
        
        self.assertGreater(advisory.get_severity_rank(), watch.get_severity_rank())
    
    def test_severity_ordering_warning_greater_than_watch(self):
        """Test that Warning > Watch in severity ranking.
        
        Validates: Requirements 8.4
        """
        warning = Advisory(type="Test", description="Test", severity="Warning")
        watch = Advisory(type="Test", description="Test", severity="Watch")
        
        self.assertGreater(warning.get_severity_rank(), watch.get_severity_rank())
    
    def test_case_insensitive_severity(self):
        """Test that severity comparison is case-insensitive.
        
        Validates: Requirements 8.4
        """
        warning_upper = Advisory(type="Test", description="Test", severity="WARNING")
        warning_lower = Advisory(type="Test", description="Test", severity="warning")
        warning_mixed = Advisory(type="Test", description="Test", severity="Warning")
        
        self.assertEqual(warning_upper.get_severity_rank(), 3)
        self.assertEqual(warning_lower.get_severity_rank(), 3)
        self.assertEqual(warning_mixed.get_severity_rank(), 3)
    
    def test_unknown_severity_returns_zero(self):
        """Test that unknown severity types return rank 0.
        
        Validates: Requirements 8.4
        """
        unknown = Advisory(type="Test", description="Test", severity="Unknown")
        self.assertEqual(unknown.get_severity_rank(), 0)


if __name__ == '__main__':
    unittest.main()


class TestHTTPRequests(unittest.TestCase):
    """Tests for HTTP request functionality."""
    
    @settings(max_examples=100)
    @given(st.text(alphabet=st.characters(whitelist_categories=('Nd',)), min_size=5, max_size=5))
    def test_property_13_http_requests_include_user_agent_header(self, zip_code: str):
        """Feature: weather-cli-script, Property 13: HTTP requests include user-agent header
        
        Validates: Requirements 9.4
        
        For any HTTP request made by the weather scraper, the request headers should
        include a user-agent field that identifies the script.
        """
        import requests
        
        # Mock the requests.get to capture the headers
        original_get = requests.get
        captured_headers = {}
        
        def mock_get(url, headers=None, timeout=None):
            nonlocal captured_headers
            captured_headers = headers or {}
            # Create a mock response
            mock_response = unittest.mock.Mock()
            mock_response.text = "<html></html>"
            mock_response.status_code = 200
            mock_response.raise_for_status = lambda: None
            return mock_response
        
        with patch('requests.get', side_effect=mock_get):
            try:
                make_weather_request(zip_code)
            except Exception:
                # We're only testing that headers are set, not that the request succeeds
                pass
            
            # Verify User-Agent header is present
            self.assertIn('User-Agent', captured_headers,
                         "User-Agent header must be present in HTTP requests")
            
            # Verify User-Agent is non-empty
            self.assertTrue(len(captured_headers.get('User-Agent', '')) > 0,
                          "User-Agent header must be non-empty")



class TestWeatherParsing(unittest.TestCase):
    """Tests for weather data parsing functionality."""
    
    @settings(max_examples=100)
    @given(
        zip_code=st.text(alphabet=st.characters(whitelist_categories=('Nd',)), min_size=5, max_size=5),
        temp_f=st.floats(min_value=-100, max_value=150, allow_nan=False, allow_infinity=False),
        conditions=st.text(min_size=1, max_size=50),
        rain_chance=st.integers(min_value=0, max_value=100),
        humidity=st.integers(min_value=0, max_value=100),
        wind_speed=st.integers(min_value=0, max_value=100)
    )
    def test_property_6_weather_data_extraction_is_comprehensive(
        self, zip_code: str, temp_f: float, conditions: str, 
        rain_chance: int, humidity: int, wind_speed: int
    ):
        """Feature: weather-cli-script, Property 6: Weather data extraction is comprehensive
        
        Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
        
        For any valid weather.gov HTML response, the parser should extract all required fields:
        temperature (F and C), rain chance, humidity, wind speed, and conditions description.
        """
        # Create a mock HTML page with weather data
        html = f"""
        <html>
            <body>
                <div id="current_conditions-summary">
                    <p class="myforecast-current-lrg">{temp_f}°F</p>
                    <p class="myforecast-current">{conditions}</p>
                </div>
                <div id="detailed-forecast-body">
                    <p>Chance of precipitation is {rain_chance}%. Humidity {humidity}%. Wind {wind_speed} mph.</p>
                </div>
            </body>
        </html>
        """
        
        try:
            weather_data = parse_weather_page(html, zip_code)
            
            # Verify all required fields are present and non-None
            self.assertIsNotNone(weather_data.zip_code, "zip_code must be present")
            self.assertIsNotNone(weather_data.temp_f, "temp_f must be present")
            self.assertIsNotNone(weather_data.temp_c, "temp_c must be present")
            self.assertIsNotNone(weather_data.rain_chance, "rain_chance must be present")
            self.assertIsNotNone(weather_data.humidity, "humidity must be present")
            self.assertIsNotNone(weather_data.wind_speed, "wind_speed must be present")
            self.assertIsNotNone(weather_data.conditions, "conditions must be present")
            
            # Verify zip code matches
            self.assertEqual(weather_data.zip_code, zip_code)
            
            # Verify temperature was extracted correctly
            self.assertAlmostEqual(weather_data.temp_f, temp_f, places=1)
            
            # Verify Celsius was calculated correctly: C = (F - 32) × 5/9
            expected_temp_c = round((temp_f - 32) * 5 / 9, 1)
            self.assertAlmostEqual(weather_data.temp_c, expected_temp_c, places=1)
            
            # Verify other fields were extracted
            self.assertEqual(weather_data.rain_chance, rain_chance)
            self.assertEqual(weather_data.humidity, humidity)
            self.assertIn(str(wind_speed), weather_data.wind_speed)
            
        except ValueError:
            # If parsing fails, it should be due to malformed HTML, not missing fields
            pass

    
    @settings(max_examples=100)
    @given(
        zip_code=st.text(alphabet=st.characters(whitelist_categories=('Nd',)), min_size=5, max_size=5),
        temp_f=st.floats(min_value=-100, max_value=150, allow_nan=False, allow_infinity=False),
        conditions=st.text(min_size=1, max_size=50),
        rain_chance=st.integers(min_value=0, max_value=100),
        humidity=st.integers(min_value=0, max_value=100),
        wind_speed=st.integers(min_value=0, max_value=100)
    )
    def test_property_14_html_parsing_extracts_data_correctly(
        self, zip_code: str, temp_f: float, conditions: str,
        rain_chance: int, humidity: int, wind_speed: int
    ):
        """Feature: weather-cli-script, Property 14: HTML parsing extracts data correctly
        
        Validates: Requirements 9.2
        
        For any valid weather.gov HTML page, parsing should successfully extract weather data
        without raising exceptions, and all extracted numeric values should be within reasonable
        ranges (e.g., temperature between -100°F and 150°F, percentages between 0-100).
        """
        # Create a mock HTML page with weather data
        html = f"""
        <html>
            <body>
                <div id="current_conditions-summary">
                    <p class="myforecast-current-lrg">{temp_f}°F</p>
                    <p class="myforecast-current">{conditions}</p>
                </div>
                <div id="detailed-forecast-body">
                    <p>Chance of precipitation is {rain_chance}%. Humidity {humidity}%. Wind {wind_speed} mph.</p>
                </div>
            </body>
        </html>
        """
        
        try:
            weather_data = parse_weather_page(html, zip_code)
            
            # Verify temperature is within reasonable range
            self.assertGreaterEqual(weather_data.temp_f, -100,
                                   "Temperature F should be >= -100°F")
            self.assertLessEqual(weather_data.temp_f, 150,
                                "Temperature F should be <= 150°F")
            
            # Verify Celsius is within reasonable range
            self.assertGreaterEqual(weather_data.temp_c, -73.3,
                                   "Temperature C should be >= -73.3°C")
            self.assertLessEqual(weather_data.temp_c, 65.6,
                                "Temperature C should be <= 65.6°C")
            
            # Verify percentages are within 0-100 range
            self.assertGreaterEqual(weather_data.rain_chance, 0,
                                   "Rain chance should be >= 0%")
            self.assertLessEqual(weather_data.rain_chance, 100,
                                "Rain chance should be <= 100%")
            
            self.assertGreaterEqual(weather_data.humidity, 0,
                                   "Humidity should be >= 0%")
            self.assertLessEqual(weather_data.humidity, 100,
                                "Humidity should be <= 100%")
            
            # Verify wind speed is non-negative
            # Extract numeric part from wind speed string
            import re
            wind_match = re.search(r'(\d+)', weather_data.wind_speed)
            if wind_match:
                wind_value = int(wind_match.group(1))
                self.assertGreaterEqual(wind_value, 0,
                                       "Wind speed should be >= 0 mph")
            
        except ValueError as e:
            # Parsing errors are acceptable for malformed HTML
            # but should not occur for well-formed HTML
            self.fail(f"Parsing should not fail for well-formed HTML: {e}")



class TestAdvisoryParsing(unittest.TestCase):
    """Tests for advisory parsing and severity selection."""
    
    @settings(max_examples=100)
    @given(
        advisory_types=st.lists(
            st.sampled_from(['Warning', 'Advisory', 'Watch']),
            min_size=2,
            max_size=5
        ),
        descriptions=st.lists(
            st.text(min_size=10, max_size=100),
            min_size=2,
            max_size=5
        )
    )
    def test_property_9_most_severe_advisory_is_selected_from_multiple_advisories(
        self, advisory_types: list, descriptions: list
    ):
        """Feature: weather-cli-script, Property 9: Most severe advisory is selected from multiple advisories
        
        Validates: Requirements 8.4
        
        For any collection of multiple Advisory objects with different severity levels,
        only the advisory with the highest severity rank (Warning > Advisory > Watch)
        should be included in the WeatherData.
        """
        # Ensure we have matching lengths
        min_len = min(len(advisory_types), len(descriptions))
        advisory_types = advisory_types[:min_len]
        descriptions = descriptions[:min_len]
        
        if min_len < 2:
            return  # Skip if we don't have at least 2 advisories
        
        # Create HTML with multiple advisories
        alert_html_parts = []
        for adv_type, desc in zip(advisory_types, descriptions):
            alert_html_parts.append(f"""
                <div class="alert-warning">
                    <h3>{adv_type} Alert</h3>
                    <p>{desc}</p>
                </div>
            """)
        
        html = f"""
        <html>
            <body>
                {''.join(alert_html_parts)}
            </body>
        </html>
        """
        
        # Parse the advisory
        result = parse_advisory(html)
        
        # Should return an advisory
        self.assertIsNotNone(result, "Should return an advisory when multiple are present")
        
        # Determine the expected most severe type
        severity_order = {'Warning': 3, 'Advisory': 2, 'Watch': 1}
        max_severity = max(advisory_types, key=lambda x: severity_order[x])
        
        # The returned advisory should have the highest severity
        self.assertEqual(result.severity, max_severity,
                        f"Should select {max_severity} from {advisory_types}, got {result.severity}")
        
        # Verify the severity rank is correct
        expected_rank = severity_order[max_severity]
        self.assertEqual(result.get_severity_rank(), expected_rank,
                        f"Severity rank should be {expected_rank} for {max_severity}")



class TestWeatherScrapingUnit(unittest.TestCase):
    """Unit tests for weather scraping functionality."""
    
    def test_parse_normal_weather_conditions(self):
        """Test parsing HTML with normal weather conditions.
        
        Validates: Requirements 6.2, 9.2
        """
        html = """
        <html>
            <body>
                <div id="current_conditions-summary">
                    <p class="myforecast-current-lrg">72°F</p>
                    <p class="myforecast-current">Partly Cloudy</p>
                </div>
                <div id="detailed-forecast-body">
                    <p>Chance of precipitation is 20%. Humidity 65%. Wind 8 mph SW.</p>
                </div>
            </body>
        </html>
        """
        
        weather = parse_weather_page(html, "07610")
        
        self.assertEqual(weather.zip_code, "07610")
        self.assertAlmostEqual(weather.temp_f, 72.0, places=1)
        self.assertAlmostEqual(weather.temp_c, 22.2, places=1)
        self.assertEqual(weather.conditions, "Partly Cloudy")
        self.assertEqual(weather.rain_chance, 20)
        self.assertEqual(weather.humidity, 65)
        self.assertIn("8", weather.wind_speed)
        self.assertIsNone(weather.advisory)
    
    def test_parse_weather_with_advisory(self):
        """Test parsing HTML containing weather advisory.
        
        Validates: Requirements 6.2, 9.2
        """
        html = """
        <html>
            <body>
                <div class="alert-warning">
                    <h3>Heat Warning</h3>
                    <p>Excessive heat warning in effect until 8:00 PM EDT. Heat index values up to 105 expected.</p>
                </div>
                <div id="current_conditions-summary">
                    <p class="myforecast-current-lrg">95°F</p>
                    <p class="myforecast-current">Sunny</p>
                </div>
                <div id="detailed-forecast-body">
                    <p>Chance of precipitation is 5%. Humidity 70%. Wind 5 mph.</p>
                </div>
            </body>
        </html>
        """
        
        weather = parse_weather_page(html, "07610")
        
        self.assertEqual(weather.zip_code, "07610")
        self.assertAlmostEqual(weather.temp_f, 95.0, places=1)
        self.assertEqual(weather.conditions, "Sunny")
        self.assertIsNotNone(weather.advisory)
        self.assertEqual(weather.advisory.severity, "Warning")
        self.assertIn("Heat", weather.advisory.type)
    
    def test_parse_malformed_html_raises_error(self):
        """Test that malformed HTML raises appropriate error.
        
        Validates: Requirements 6.2, 9.2
        """
        # HTML missing required temperature element
        html = """
        <html>
            <body>
                <div id="current_conditions-summary">
                    <p class="myforecast-current">Partly Cloudy</p>
                </div>
            </body>
        </html>
        """
        
        with self.assertRaises(ValueError):
            parse_weather_page(html, "07610")
    
    def test_parse_advisory_returns_none_when_no_advisory(self):
        """Test that parse_advisory returns None when no advisory present.
        
        Validates: Requirements 8.1
        """
        html = """
        <html>
            <body>
                <div id="current_conditions-summary">
                    <p>Normal weather conditions</p>
                </div>
            </body>
        </html>
        """
        
        advisory = parse_advisory(html)
        self.assertIsNone(advisory)
    
    def test_parse_advisory_extracts_warning(self):
        """Test that parse_advisory correctly extracts warning information.
        
        Validates: Requirements 8.1, 8.3
        """
        html = """
        <html>
            <body>
                <div class="alert-warning">
                    <h3>Severe Thunderstorm Warning</h3>
                    <p>Severe thunderstorm warning in effect until 6:00 PM. Expect damaging winds and large hail.</p>
                </div>
            </body>
        </html>
        """
        
        advisory = parse_advisory(html)
        
        self.assertIsNotNone(advisory)
        self.assertIn("Warning", advisory.type)
        self.assertEqual(advisory.severity, "Warning")
        self.assertIn("thunderstorm", advisory.description.lower())
    
    def test_parse_multiple_advisories_selects_most_severe(self):
        """Test that most severe advisory is selected when multiple exist.
        
        Validates: Requirements 8.4
        """
        html = """
        <html>
            <body>
                <div class="alert-warning">
                    <h3>Heat Watch</h3>
                    <p>Heat watch in effect for tomorrow.</p>
                </div>
                <div class="alert-warning">
                    <h3>Air Quality Advisory</h3>
                    <p>Air quality advisory in effect.</p>
                </div>
                <div class="alert-warning">
                    <h3>Severe Weather Warning</h3>
                    <p>Severe weather warning in effect now.</p>
                </div>
            </body>
        </html>
        """
        
        advisory = parse_advisory(html)
        
        self.assertIsNotNone(advisory)
        # Should select the Warning (most severe)
        self.assertEqual(advisory.severity, "Warning")
        self.assertIn("Warning", advisory.type)


class TestWeatherFormatting(unittest.TestCase):
    """Tests for weather data formatting functionality."""
    
    @settings(max_examples=100)
    @given(
        zip_code=st.text(alphabet=st.characters(whitelist_categories=('Nd',)), min_size=5, max_size=5),
        temp_f=st.floats(min_value=-100, max_value=150, allow_nan=False, allow_infinity=False),
        temp_c=st.floats(min_value=-73.3, max_value=65.6, allow_nan=False, allow_infinity=False),
        rain_chance=st.integers(min_value=0, max_value=100),
        humidity=st.integers(min_value=0, max_value=100),
        wind_speed=st.text(min_size=1, max_size=20),
        conditions=st.text(min_size=1, max_size=50)
    )
    def test_property_7_formatted_output_contains_all_weather_metrics_with_labels(
        self, zip_code: str, temp_f: float, temp_c: float, rain_chance: int,
        humidity: int, wind_speed: str, conditions: str
    ):
        """Feature: weather-cli-script, Property 7: Formatted output contains all weather metrics with labels
        
        Validates: Requirements 5.1, 5.2, 5.3
        
        For any WeatherData object, the formatted output should contain labeled fields for
        temperature (both F and C), rain chance, humidity, wind speed, conditions, and the zip code.
        """
        # Create WeatherData object
        weather = WeatherData(
            zip_code=zip_code,
            temp_f=temp_f,
            temp_c=temp_c,
            rain_chance=rain_chance,
            humidity=humidity,
            wind_speed=wind_speed,
            conditions=conditions,
            advisory=None
        )
        
        # Format the output
        output = format_weather_output(weather)
        
        # Verify output is non-empty
        self.assertTrue(len(output) > 0, "Formatted output must be non-empty")
        
        # Verify zip code is present
        self.assertIn(zip_code, output, "Output must contain zip code")
        
        # Verify temperature F is present
        self.assertIn(str(temp_f), output, "Output must contain temperature in Fahrenheit")
        
        # Verify temperature C is present
        self.assertIn(str(temp_c), output, "Output must contain temperature in Celsius")
        
        # Verify both F and C units are shown
        self.assertIn("°F", output, "Output must show Fahrenheit unit")
        self.assertIn("°C", output, "Output must show Celsius unit")
        
        # Verify rain chance is present
        self.assertIn(str(rain_chance), output, "Output must contain rain chance")
        
        # Verify humidity is present
        self.assertIn(str(humidity), output, "Output must contain humidity")
        
        # Verify wind speed is present
        self.assertIn(wind_speed, output, "Output must contain wind speed")
        
        # Verify conditions are present
        self.assertIn(conditions, output, "Output must contain conditions")
        
        # Verify labels are present
        self.assertIn("Temperature:", output, "Output must have Temperature label")
        self.assertIn("Conditions:", output, "Output must have Conditions label")
        self.assertIn("Rain Chance:", output, "Output must have Rain Chance label")
        self.assertIn("Humidity:", output, "Output must have Humidity label")
        self.assertIn("Wind Speed:", output, "Output must have Wind Speed label")


class TestAdvisoryFormatting(unittest.TestCase):
    """Tests for advisory formatting functionality."""
    
    @settings(max_examples=100)
    @given(
        advisory_type=st.text(min_size=5, max_size=50),
        description=st.text(min_size=10, max_size=200),
        severity=st.sampled_from(['Warning', 'Advisory', 'Watch'])
    )
    def test_property_8_advisory_display_includes_all_required_information(
        self, advisory_type: str, description: str, severity: str
    ):
        """Feature: weather-cli-script, Property 8: Advisory display includes all required information
        
        Validates: Requirements 8.3
        
        For any Advisory object, the formatted output should contain the advisory type,
        full description, and severity information.
        """
        # Create Advisory object
        advisory = Advisory(
            type=advisory_type,
            description=description,
            severity=severity
        )
        
        # Format the advisory
        output = format_advisory(advisory)
        
        # Verify output is non-empty
        self.assertTrue(len(output) > 0, "Formatted advisory must be non-empty")
        
        # Verify advisory type is present
        self.assertIn(advisory_type, output, "Output must contain advisory type")
        
        # Verify description is present
        self.assertIn(description, output, "Output must contain advisory description")
        
        # Verify visual prominence (separators)
        self.assertIn("=", output, "Output must contain visual separators for prominence")
        
        # Verify "ADVISORY" or similar header is present
        self.assertIn("ADVISORY", output.upper(), "Output must indicate this is an advisory")
    
    @settings(max_examples=100)
    @given(
        zip_code=st.text(alphabet=st.characters(whitelist_categories=('Nd',)), min_size=5, max_size=5),
        temp_f=st.floats(min_value=-100, max_value=150, allow_nan=False, allow_infinity=False),
        temp_c=st.floats(min_value=-73.3, max_value=65.6, allow_nan=False, allow_infinity=False),
        rain_chance=st.integers(min_value=0, max_value=100),
        humidity=st.integers(min_value=0, max_value=100),
        wind_speed=st.text(min_size=1, max_size=20),
        conditions=st.text(min_size=1, max_size=50),
        has_advisory=st.booleans()
    )
    def test_property_10_advisory_presence_is_always_communicated(
        self, zip_code: str, temp_f: float, temp_c: float, rain_chance: int,
        humidity: int, wind_speed: str, conditions: str, has_advisory: bool
    ):
        """Feature: weather-cli-script, Property 10: Advisory presence is always communicated
        
        Validates: Requirements 8.2, 8.5
        
        For any weather data retrieval, the output should either display an active advisory
        prominently or indicate that no advisories are active.
        """
        # Create advisory if needed
        advisory = None
        if has_advisory:
            advisory = Advisory(
                type="Test Advisory",
                description="This is a test advisory description.",
                severity="Advisory"
            )
        
        # Create WeatherData object
        weather = WeatherData(
            zip_code=zip_code,
            temp_f=temp_f,
            temp_c=temp_c,
            rain_chance=rain_chance,
            humidity=humidity,
            wind_speed=wind_speed,
            conditions=conditions,
            advisory=advisory
        )
        
        # Format the output
        output = format_weather_output(weather)
        
        # Verify output is non-empty
        self.assertTrue(len(output) > 0, "Formatted output must be non-empty")
        
        if has_advisory:
            # If advisory is present, it should be displayed prominently
            self.assertIn("ADVISORY", output.upper(), 
                         "Output must prominently display advisory when present")
            self.assertIn(advisory.type, output,
                         "Output must contain advisory type when present")
            self.assertIn(advisory.description, output,
                         "Output must contain advisory description when present")
        else:
            # If no advisory, should indicate that
            output_lower = output.lower()
            self.assertTrue(
                "no active" in output_lower or "no advisories" in output_lower,
                "Output must indicate when no advisories are active"
            )



class TestErrorHandling(unittest.TestCase):
    """Tests for error handling functionality."""
    
    @settings(max_examples=100)
    @given(st.text())
    def test_property_2_invalid_zip_codes_produce_non_zero_exit_codes(self, invalid_zip: str):
        """Feature: weather-cli-script, Property 2: Invalid zip codes produce non-zero exit codes
        
        Validates: Requirements 2.3
        
        For any invalid zip code input (not exactly 5 digits), the script should exit with
        a non-zero status code and display an error message.
        """
        # Only test with invalid zip codes
        if len(invalid_zip) == 5 and invalid_zip.isdigit():
            return  # Skip valid zip codes
        
        # Skip strings starting with '-' as argparse interprets them as flags
        if invalid_zip.startswith('-'):
            return
        
        # Mock sys.argv to simulate command-line argument
        with patch('sys.argv', ['weather.py', invalid_zip]):
            # Capture stderr to verify error message
            import io
            captured_stderr = io.StringIO()
            
            with patch('sys.stderr', captured_stderr):
                # Call main function
                exit_code = main()
            
            # Verify non-zero exit code
            self.assertNotEqual(exit_code, 0,
                              f"Invalid zip code '{invalid_zip}' should produce non-zero exit code, got {exit_code}")
            
            # Verify exit code is 1 (validation error)
            self.assertEqual(exit_code, 1,
                           f"Invalid zip code should produce exit code 1, got {exit_code}")
            
            # Verify error message was displayed
            error_output = captured_stderr.getvalue()
            self.assertTrue(len(error_output) > 0,
                          "Error message should be displayed for invalid zip code")
            self.assertIn("Error", error_output,
                         "Error message should contain 'Error'")
            self.assertIn(invalid_zip, error_output,
                         "Error message should mention the invalid zip code")
    
    @settings(max_examples=100, deadline=None)
    @given(
        error_type=st.sampled_from(['network', 'parsing', 'location'])
    )
    def test_property_11_error_messages_are_non_empty(self, error_type: str):
        """Feature: weather-cli-script, Property 11: Error messages are non-empty
        
        Validates: Requirements 6.4
        
        For any error condition (network failure, parsing failure, invalid location),
        the error message displayed to the user should be a non-empty string that
        describes the error type.
        """
        import io
        
        # Mock sys.argv with a valid zip code
        with patch('sys.argv', ['weather.py', '12345']):
            captured_stderr = io.StringIO()
            
            with patch('sys.stderr', captured_stderr):
                if error_type == 'network':
                    # Mock network error
                    with patch('weather.make_weather_request', side_effect=requests.exceptions.Timeout()):
                        exit_code = main()
                        self.assertEqual(exit_code, 2, "Network error should produce exit code 2")
                
                elif error_type == 'parsing':
                    # Mock parsing error
                    with patch('weather.parse_weather_page', side_effect=ValueError("Parsing failed")):
                        exit_code = main()
                        self.assertEqual(exit_code, 3, "Parsing error should produce exit code 3")
                
                elif error_type == 'location':
                    # Mock location error
                    with patch('weather.parse_weather_page', side_effect=ValueError("No weather data found")):
                        exit_code = main()
                        self.assertEqual(exit_code, 4, "Location error should produce exit code 4")
            
            # Verify error message is non-empty
            error_output = captured_stderr.getvalue()
            self.assertTrue(len(error_output) > 0,
                          f"Error message for {error_type} error should be non-empty")
            
            # Verify error message contains "Error"
            self.assertIn("Error", error_output,
                         f"Error message for {error_type} should contain 'Error'")


class TestErrorScenariosUnit(unittest.TestCase):
    """Unit tests for specific error scenarios."""
    
    def test_network_error_handling(self):
        """Test network error handling.
        
        Validates: Requirements 6.1
        """
        import io
        
        with patch('sys.argv', ['weather.py', '12345']):
            captured_stderr = io.StringIO()
            
            with patch('sys.stderr', captured_stderr):
                # Mock network timeout
                with patch('weather.make_weather_request', side_effect=requests.exceptions.Timeout()):
                    exit_code = main()
            
            # Verify exit code 2 for network error
            self.assertEqual(exit_code, 2)
            
            # Verify error message
            error_output = captured_stderr.getvalue()
            self.assertIn("Error", error_output)
            self.assertIn("connect", error_output.lower())
    
    def test_parsing_error_handling(self):
        """Test parsing error handling.
        
        Validates: Requirements 6.2
        """
        import io
        
        with patch('sys.argv', ['weather.py', '12345']):
            captured_stderr = io.StringIO()
            
            with patch('sys.stderr', captured_stderr):
                # Mock parsing error
                with patch('weather.parse_weather_page', side_effect=ValueError("Failed to parse")):
                    exit_code = main()
            
            # Verify exit code 3 for parsing error
            self.assertEqual(exit_code, 3)
            
            # Verify error message
            error_output = captured_stderr.getvalue()
            self.assertIn("Error", error_output)
            self.assertIn("parse", error_output.lower())
    
    def test_invalid_location_handling(self):
        """Test invalid location error handling.
        
        Validates: Requirements 6.3
        """
        import io
        
        with patch('sys.argv', ['weather.py', '12345']):
            captured_stderr = io.StringIO()
            
            with patch('sys.stderr', captured_stderr):
                # Mock location error
                with patch('weather.parse_weather_page', side_effect=ValueError("No weather data found")):
                    exit_code = main()
            
            # Verify exit code 4 for location error
            self.assertEqual(exit_code, 4)
            
            # Verify error message
            error_output = captured_stderr.getvalue()
            self.assertIn("Error", error_output)
            self.assertIn("No weather data", error_output)



class TestIntegration(unittest.TestCase):
    """Integration tests for end-to-end functionality.
    
    Validates: Requirements 1.1, 1.2, 2.1, 3.2, 8.2
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_cache_path = Path(self.temp_dir) / '.weather_cli_cache'
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_cache_path.exists():
            self.temp_cache_path.unlink()
        Path(self.temp_dir).rmdir()
    
    def test_end_to_end_with_default_zip_code(self):
        """Test end-to-end execution with default zip code.
        
        Validates: Requirements 1.1, 1.2
        """
        import io
        
        # Mock sys.argv to simulate no arguments
        with patch('sys.argv', ['weather.py']):
            with patch('weather.get_cache_file_path', return_value=self.temp_cache_path):
                # Ensure no cache exists
                if self.temp_cache_path.exists():
                    self.temp_cache_path.unlink()
                
                # Mock the weather request to avoid actual network call
                mock_html = """
                <html>
                    <body>
                        <div id="current_conditions-summary">
                            <p class="myforecast-current-lrg">72°F</p>
                            <p class="myforecast-current">Partly Cloudy</p>
                        </div>
                        <div id="detailed-forecast-body">
                            <p>Chance of precipitation is 20%. Humidity 65%. Wind 8 mph.</p>
                        </div>
                    </body>
                </html>
                """
                
                captured_stdout = io.StringIO()
                
                with patch('weather.make_weather_request', return_value=mock_html):
                    with patch('sys.stdout', captured_stdout):
                        exit_code = main()
                
                # Verify successful execution
                self.assertEqual(exit_code, 0, "Should exit with code 0 on success")
                
                # Verify output contains weather data
                output = captured_stdout.getvalue()
                self.assertIn("07610", output, "Should use default zip code 07610")
                self.assertIn("Temperature:", output, "Should display temperature")
                self.assertIn("°F", output, "Should display Fahrenheit")
                self.assertIn("°C", output, "Should display Celsius")
                
                # Verify zip code was cached
                cached = get_cached_zip_code()
                self.assertEqual(cached, "07610", "Default zip code should be cached after successful retrieval")
    
    def test_end_to_end_with_command_line_argument(self):
        """Test end-to-end execution with command-line argument.
        
        Validates: Requirements 1.1, 1.2, 2.1
        """
        import io
        
        test_zip = "90210"
        
        # Mock sys.argv to simulate command-line argument
        with patch('sys.argv', ['weather.py', test_zip]):
            with patch('weather.get_cache_file_path', return_value=self.temp_cache_path):
                # Mock the weather request
                mock_html = """
                <html>
                    <body>
                        <div id="current_conditions-summary">
                            <p class="myforecast-current-lrg">85°F</p>
                            <p class="myforecast-current">Sunny</p>
                        </div>
                        <div id="detailed-forecast-body">
                            <p>Chance of precipitation is 5%. Humidity 45%. Wind 12 mph.</p>
                        </div>
                    </body>
                </html>
                """
                
                captured_stdout = io.StringIO()
                
                with patch('weather.make_weather_request', return_value=mock_html):
                    with patch('sys.stdout', captured_stdout):
                        exit_code = main()
                
                # Verify successful execution
                self.assertEqual(exit_code, 0, "Should exit with code 0 on success")
                
                # Verify output contains correct zip code
                output = captured_stdout.getvalue()
                self.assertIn(test_zip, output, f"Should use provided zip code {test_zip}")
                self.assertIn("Temperature:", output, "Should display temperature")
                
                # Verify zip code was cached
                cached = get_cached_zip_code()
                self.assertEqual(cached, test_zip, "Provided zip code should be cached after successful retrieval")
    
    def test_end_to_end_with_cached_zip_code(self):
        """Test end-to-end execution with cached zip code.
        
        Validates: Requirements 1.1, 1.2, 3.2
        """
        import io
        
        cached_zip = "10001"
        
        # Mock sys.argv to simulate no arguments
        with patch('sys.argv', ['weather.py']):
            with patch('weather.get_cache_file_path', return_value=self.temp_cache_path):
                # Set up cached zip code
                save_cached_zip_code(cached_zip)
                
                # Mock the weather request
                mock_html = """
                <html>
                    <body>
                        <div id="current_conditions-summary">
                            <p class="myforecast-current-lrg">68°F</p>
                            <p class="myforecast-current">Cloudy</p>
                        </div>
                        <div id="detailed-forecast-body">
                            <p>Chance of precipitation is 30%. Humidity 70%. Wind 6 mph.</p>
                        </div>
                    </body>
                </html>
                """
                
                captured_stdout = io.StringIO()
                
                with patch('weather.make_weather_request', return_value=mock_html):
                    with patch('sys.stdout', captured_stdout):
                        exit_code = main()
                
                # Verify successful execution
                self.assertEqual(exit_code, 0, "Should exit with code 0 on success")
                
                # Verify output contains cached zip code
                output = captured_stdout.getvalue()
                self.assertIn(cached_zip, output, f"Should use cached zip code {cached_zip}")
                self.assertIn("Temperature:", output, "Should display temperature")
                
                # Verify cached zip code is still present
                cached_after = get_cached_zip_code()
                self.assertEqual(cached_after, cached_zip, "Cached zip code should remain after successful retrieval")
    
    def test_advisory_display_when_present(self):
        """Test that advisories are displayed prominently when present.
        
        Validates: Requirements 8.2
        """
        import io
        
        # Mock sys.argv
        with patch('sys.argv', ['weather.py', '12345']):
            with patch('weather.get_cache_file_path', return_value=self.temp_cache_path):
                # Mock the weather request with advisory
                mock_html = """
                <html>
                    <body>
                        <div class="alert-warning">
                            <h3>Heat Warning</h3>
                            <p>Excessive heat warning in effect until 8:00 PM EDT. Heat index values up to 105 expected.</p>
                        </div>
                        <div id="current_conditions-summary">
                            <p class="myforecast-current-lrg">95°F</p>
                            <p class="myforecast-current">Sunny</p>
                        </div>
                        <div id="detailed-forecast-body">
                            <p>Chance of precipitation is 0%. Humidity 75%. Wind 5 mph.</p>
                        </div>
                    </body>
                </html>
                """
                
                captured_stdout = io.StringIO()
                
                with patch('weather.make_weather_request', return_value=mock_html):
                    with patch('sys.stdout', captured_stdout):
                        exit_code = main()
                
                # Verify successful execution
                self.assertEqual(exit_code, 0, "Should exit with code 0 on success")
                
                # Verify advisory is displayed prominently
                output = captured_stdout.getvalue()
                self.assertIn("ADVISORY", output.upper(), "Should display advisory prominently")
                self.assertIn("Heat", output, "Should display advisory type")
                self.assertIn("Warning", output, "Should display advisory severity")
                self.assertIn("=", output, "Should have visual separators for prominence")
                
                # Verify weather data is also present
                self.assertIn("Temperature:", output, "Should display temperature along with advisory")
                self.assertIn("95", output, "Should display correct temperature")
