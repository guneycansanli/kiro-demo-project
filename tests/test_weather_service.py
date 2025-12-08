"""
Property-based and unit tests for weather service.

Tests weather scraping and parsing functionality using property-based
testing with Hypothesis.
"""

import unittest
from datetime import datetime
from hypothesis import given, settings, strategies as st
from app.models.weather import WeatherData
from app.models.location import Location, Coordinates
from app.models.advisory import Advisory
from app.services.weather_service import WeatherService


class TestWeatherDataCompleteness(unittest.TestCase):
    """Property-based tests for weather data completeness."""
    
    @settings(max_examples=100)
    @given(
        temp_f=st.floats(min_value=-50, max_value=150),
        conditions=st.text(min_size=1),
        rain_chance=st.integers(min_value=0, max_value=100),
        humidity=st.integers(min_value=0, max_value=100),
        wind_speed=st.text(min_size=1)
    )
    def test_weather_data_completeness_property(
        self, 
        temp_f: float, 
        conditions: str, 
        rain_chance: int, 
        humidity: int, 
        wind_speed: str
    ):
        """
        Feature: weather-web-service, Property 6: Weather display includes all required metrics
        
        For any weather data object, the display should include temperature (F and C),
        conditions, rain chance, humidity, wind speed, and location name.
        
        Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
        """
        # Create a test location
        location = Location(
            name="Test City",
            display_name="Test City, Test State, Test Country",
            zip_code="12345",
            city="Test City",
            state="Test State",
            country="Test Country",
            coordinates=Coordinates(lat=37.7749, lon=-122.4194)
        )
        
        # Calculate Celsius
        temp_c = round((temp_f - 32) * 5 / 9, 1)
        
        # Create weather data object
        weather_data = WeatherData(
            location=location,
            temp_f=temp_f,
            temp_c=temp_c,
            conditions=conditions,
            rain_chance=rain_chance,
            humidity=humidity,
            wind_speed=wind_speed,
            advisory=None,
            timestamp=datetime.now()
        )
        
        # Verify all required fields are present and not None
        self.assertIsNotNone(weather_data.location)
        self.assertIsNotNone(weather_data.location.name)
        self.assertIsNotNone(weather_data.temp_f)
        self.assertIsNotNone(weather_data.temp_c)
        self.assertIsNotNone(weather_data.conditions)
        self.assertIsNotNone(weather_data.rain_chance)
        self.assertIsNotNone(weather_data.humidity)
        self.assertIsNotNone(weather_data.wind_speed)
        
        # Verify temperature values are present
        self.assertIsInstance(weather_data.temp_f, (int, float))
        self.assertIsInstance(weather_data.temp_c, (int, float))
        
        # Verify location name is present
        self.assertTrue(len(weather_data.location.name) > 0)


class TestTemperatureUnits(unittest.TestCase):
    """Property-based tests for temperature unit display."""
    
    @settings(max_examples=100)
    @given(temp_f=st.floats(min_value=-50, max_value=150, allow_nan=False, allow_infinity=False))
    def test_temperature_units_property(self, temp_f: float):
        """
        Feature: weather-web-service, Property 7: Temperature displayed in both units
        
        For any weather data, both Fahrenheit and Celsius temperature values
        should be present in the response and display.
        
        Validates: Requirements 5.2
        """
        # Create a test location
        location = Location(
            name="Test City",
            display_name="Test City, Test State, Test Country",
            zip_code="12345",
            city="Test City",
            state="Test State",
            country="Test Country",
            coordinates=Coordinates(lat=37.7749, lon=-122.4194)
        )
        
        # Calculate Celsius
        temp_c = round((temp_f - 32) * 5 / 9, 1)
        
        # Create weather data object
        weather_data = WeatherData(
            location=location,
            temp_f=temp_f,
            temp_c=temp_c,
            conditions="Sunny",
            rain_chance=0,
            humidity=50,
            wind_speed="10 mph",
            advisory=None,
            timestamp=datetime.now()
        )
        
        # Verify both temperature units are present
        self.assertIsNotNone(weather_data.temp_f)
        self.assertIsNotNone(weather_data.temp_c)
        
        # Verify they are numeric values
        self.assertIsInstance(weather_data.temp_f, (int, float))
        self.assertIsInstance(weather_data.temp_c, (int, float))
        
        # Verify the conversion is approximately correct
        expected_temp_c = round((temp_f - 32) * 5 / 9, 1)
        self.assertAlmostEqual(weather_data.temp_c, expected_temp_c, places=1)


class TestAdvisorySeveritySelection(unittest.TestCase):
    """Property-based tests for advisory severity selection."""
    
    @settings(max_examples=100)
    @given(
        st.lists(
            st.sampled_from(['Warning', 'Advisory', 'Watch']),
            min_size=1,
            max_size=5
        )
    )
    def test_advisory_severity_selection_property(self, severities: list):
        """
        Feature: weather-web-service, Property 11: Most severe advisory is selected from multiple advisories
        
        For any collection of multiple advisory objects with different severity levels,
        only the advisory with the highest severity rank (Warning > Advisory > Watch)
        should be included in the response.
        
        Validates: Requirements 6.4
        """
        # Create multiple advisories with different severities
        advisories = []
        for i, severity in enumerate(severities):
            advisory = Advisory(
                type=f"{severity} Type {i}",
                description=f"Test {severity} description {i}",
                severity=severity
            )
            advisories.append(advisory)
        
        # Find the most severe advisory using get_severity_rank()
        most_severe = max(advisories, key=lambda a: a.get_severity_rank())
        
        # Verify that the most severe advisory has the highest rank
        for advisory in advisories:
            self.assertGreaterEqual(
                most_severe.get_severity_rank(),
                advisory.get_severity_rank()
            )
        
        # Verify severity ranking order
        severity_ranks = {
            'Warning': 3,
            'Advisory': 2,
            'Watch': 1
        }
        
        # The most severe should have the highest numeric rank
        expected_max_rank = max(severity_ranks[s] for s in severities)
        self.assertEqual(most_severe.get_severity_rank(), expected_max_rank)


if __name__ == '__main__':
    unittest.main()



class TestWeatherScraping(unittest.TestCase):
    """Unit tests for weather scraping and parsing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.weather_service = WeatherService(timeout=10)
        self.test_location = Location(
            name="Test City",
            display_name="Test City, Test State, Test Country",
            zip_code="12345",
            city="Test City",
            state="Test State",
            country="Test Country",
            coordinates=Coordinates(lat=37.7749, lon=-122.4194)
        )
    
    def test_parse_weather_page_normal_conditions(self):
        """
        Test parsing weather page with normal conditions.
        
        Validates: Requirements 4.1, 6.1
        """
        # Sample HTML with normal weather conditions
        sample_html = """
        <html>
            <body>
                <p class="myforecast-current-lrg">65°F</p>
                <p class="myforecast-current-sm">Partly Cloudy</p>
                <div class="forecast-text">
                    Partly cloudy with a 20 percent chance of rain.
                    Winds 10 to 15 mph.
                </div>
                <table>
                    <tr>
                        <td>Humidity: 65%</td>
                    </tr>
                </table>
            </body>
        </html>
        """
        
        # Parse the weather page
        weather_data = self.weather_service.parse_weather_page(sample_html, self.test_location)
        
        # Verify temperature
        self.assertEqual(weather_data.temp_f, 65.0)
        self.assertAlmostEqual(weather_data.temp_c, 18.3, places=1)
        
        # Verify conditions
        self.assertEqual(weather_data.conditions, "Partly Cloudy")
        
        # Verify location
        self.assertEqual(weather_data.location.name, "Test City")
        
        # Verify no advisory
        self.assertIsNone(weather_data.advisory)
    
    def test_parse_weather_page_with_advisory(self):
        """
        Test parsing weather page with weather advisory.
        
        Validates: Requirements 6.1, 6.2
        """
        # Sample HTML with weather advisory
        sample_html = """
        <html>
            <body>
                <p class="myforecast-current-lrg">95°F</p>
                <p class="myforecast-current-sm">Sunny</p>
                <div class="alert">
                    Heat Advisory in effect. Temperatures will reach dangerous levels.
                    Stay hydrated and avoid prolonged outdoor exposure.
                </div>
                <div class="forecast-text">
                    Sunny and hot. Winds 5 mph.
                </div>
            </body>
        </html>
        """
        
        # Parse the weather page
        weather_data = self.weather_service.parse_weather_page(sample_html, self.test_location)
        
        # Verify temperature
        self.assertEqual(weather_data.temp_f, 95.0)
        
        # Verify advisory is present
        self.assertIsNotNone(weather_data.advisory)
        self.assertEqual(weather_data.advisory.severity, "Advisory")
        self.assertIn("Heat Advisory", weather_data.advisory.type)
    
    def test_parse_weather_page_with_warning(self):
        """
        Test parsing weather page with weather warning (highest severity).
        
        Validates: Requirements 6.1, 6.2
        """
        # Sample HTML with weather warning
        sample_html = """
        <html>
            <body>
                <p class="myforecast-current-lrg">32°F</p>
                <p class="myforecast-current-sm">Snow</p>
                <div class="warning">
                    Winter Storm Warning in effect. Heavy snow expected.
                    Travel will be dangerous or impossible.
                </div>
            </body>
        </html>
        """
        
        # Parse the weather page
        weather_data = self.weather_service.parse_weather_page(sample_html, self.test_location)
        
        # Verify advisory is present with correct severity
        self.assertIsNotNone(weather_data.advisory)
        self.assertEqual(weather_data.advisory.severity, "Warning")
        self.assertIn("Warning", weather_data.advisory.type)
    
    def test_parse_weather_page_multiple_advisories(self):
        """
        Test that most severe advisory is selected when multiple exist.
        
        Validates: Requirements 6.4
        """
        # Sample HTML with multiple advisories
        sample_html = """
        <html>
            <body>
                <p class="myforecast-current-lrg">85°F</p>
                <p class="myforecast-current-sm">Partly Cloudy</p>
                <div class="watch">
                    Flood Watch in effect for low-lying areas.
                </div>
                <div class="advisory">
                    Wind Advisory in effect. Gusty winds expected.
                </div>
                <div class="warning">
                    Heat Warning in effect. Dangerous heat conditions.
                </div>
            </body>
        </html>
        """
        
        # Parse the weather page
        weather_data = self.weather_service.parse_weather_page(sample_html, self.test_location)
        
        # Verify that the Warning (most severe) is selected
        self.assertIsNotNone(weather_data.advisory)
        self.assertEqual(weather_data.advisory.severity, "Warning")
        self.assertEqual(weather_data.advisory.get_severity_rank(), 3)
    
    def test_parse_weather_page_malformed_html(self):
        """
        Test error handling with malformed HTML.
        
        Validates: Requirements 4.1
        """
        # Malformed HTML missing temperature
        malformed_html = """
        <html>
            <body>
                <p class="myforecast-current-sm">Sunny</p>
            </body>
        </html>
        """
        
        # Should raise ValueError when temperature cannot be extracted
        with self.assertRaises(ValueError) as context:
            self.weather_service.parse_weather_page(malformed_html, self.test_location)
        
        self.assertIn("temperature", str(context.exception).lower())
    
    def test_parse_advisory_no_advisory(self):
        """Test that parse_advisory returns None when no advisory present."""
        html_no_advisory = """
        <html>
            <body>
                <p class="myforecast-current-lrg">70°F</p>
                <p class="myforecast-current-sm">Clear</p>
            </body>
        </html>
        """
        
        advisory = self.weather_service.parse_advisory(html_no_advisory)
        self.assertIsNone(advisory)
    
    def test_parse_advisory_with_watch(self):
        """Test parsing advisory with Watch severity."""
        html_with_watch = """
        <html>
            <body>
                <div class="watch">
                    Flood Watch in effect until midnight.
                </div>
            </body>
        </html>
        """
        
        advisory = self.weather_service.parse_advisory(html_with_watch)
        self.assertIsNotNone(advisory)
        self.assertEqual(advisory.severity, "Watch")
        self.assertEqual(advisory.get_severity_rank(), 1)
    
    def test_advisory_severity_ranking(self):
        """Test that advisory severity ranking is correct."""
        warning = Advisory(type="Test Warning", description="Test", severity="Warning")
        advisory = Advisory(type="Test Advisory", description="Test", severity="Advisory")
        watch = Advisory(type="Test Watch", description="Test", severity="Watch")
        
        # Verify ranking order: Warning > Advisory > Watch
        self.assertGreater(warning.get_severity_rank(), advisory.get_severity_rank())
        self.assertGreater(advisory.get_severity_rank(), watch.get_severity_rank())
        self.assertEqual(warning.get_severity_rank(), 3)
        self.assertEqual(advisory.get_severity_rank(), 2)
        self.assertEqual(watch.get_severity_rank(), 1)
