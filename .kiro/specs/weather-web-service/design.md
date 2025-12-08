# Design Document

## Overview

The weather web service will be built using a modern web stack with Python Flask for the backend API and vanilla JavaScript with HTML/CSS for the frontend. The application will be containerized using Docker for easy deployment. The architecture follows a client-server model where the frontend makes API calls to the backend, which in turn scrapes weather data from weather.gov.

**Technology Stack:**
- **Backend**: Python 3.10+ with Flask web framework
- **Frontend**: HTML5, CSS3, vanilla JavaScript (ES6+)
- **Web Server**: Gunicorn (production WSGI server)
- **Containerization**: Docker and Docker Compose
- **HTTPS**: Nginx reverse proxy with SSL/TLS support
- **Data Source**: weather.gov (National Weather Service)
- **Location Data**: OpenStreetMap Nominatim API for geocoding

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Browser                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  HTML/CSS/JavaScript Frontend                          │ │
│  │  - Search Interface                                    │ │
│  │  - Autocomplete                                        │ │
│  │  - Geolocation                                         │ │
│  │  - Weather Display                                     │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Nginx Reverse Proxy                       │
│                    (SSL/TLS Termination)                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flask Web Application                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  API Endpoints                                         │ │
│  │  - GET /api/weather?location=<query>                  │ │
│  │  - GET /api/autocomplete?q=<query>                    │ │
│  │  - GET /api/weather/coordinates?lat=<>&lon=<>         │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Business Logic                                        │ │
│  │  - Location Resolution                                 │ │
│  │  - Weather Scraping                                    │ │
│  │  - Caching                                             │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
│  - weather.gov (Weather Data)                               │
│  - Nominatim API (Geocoding)                                │
└─────────────────────────────────────────────────────────────┘
```

### Container Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Compose                          │
│                                                              │
│  ┌──────────────────────┐    ┌──────────────────────┐      │
│  │  Nginx Container     │    │  Flask App Container │      │
│  │  - Port 443 (HTTPS)  │───▶│  - Port 5000         │      │
│  │  - Port 80 (HTTP)    │    │  - Gunicorn          │      │
│  │  - SSL Certificates  │    │  - Flask App         │      │
│  └──────────────────────┘    └──────────────────────┘      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Frontend Components

#### Search Interface Component
**Responsibilities:**
- Render search input field
- Handle user input and trigger autocomplete
- Display autocomplete suggestions
- Handle location selection
- Trigger weather data fetch

**Interface:**
```javascript
class SearchInterface {
    constructor(containerId)
    render()
    onInput(callback)
    showSuggestions(suggestions)
    hideSuggestions()
    selectSuggestion(suggestion)
}
```

#### Geolocation Component
**Responsibilities:**
- Request browser geolocation permission
- Get user coordinates
- Handle geolocation errors
- Trigger weather fetch by coordinates

**Interface:**
```javascript
class GeolocationHandler {
    requestLocation()
    onSuccess(callback)
    onError(callback)
    getCurrentPosition()
}
```

#### Weather Display Component
**Responsibilities:**
- Render weather data in card layout
- Display temperature, conditions, metrics
- Show weather advisories
- Handle loading and error states

**Interface:**
```javascript
class WeatherDisplay {
    constructor(containerId)
    showLoading()
    showWeather(weatherData)
    showError(errorMessage)
    showAdvisory(advisory)
}
```

### 2. Backend API Endpoints

#### Weather Endpoint
```
GET /api/weather?location=<query>
GET /api/weather?zip=<zipcode>
GET /api/weather/coordinates?lat=<lat>&lon=<lon>

Response:
{
    "location": {
        "name": "San Francisco, CA",
        "zip_code": "94102",
        "coordinates": {"lat": 37.7749, "lon": -122.4194}
    },
    "weather": {
        "temp_f": 65.0,
        "temp_c": 18.3,
        "conditions": "Partly Cloudy",
        "rain_chance": 20,
        "humidity": 65,
        "wind_speed": "10 mph"
    },
    "advisory": {
        "type": "Heat Advisory",
        "description": "...",
        "severity": "Advisory"
    } | null
}
```

#### Autocomplete Endpoint
```
GET /api/autocomplete?q=<query>

Response:
{
    "suggestions": [
        {
            "display_name": "San Francisco, California, United States",
            "type": "city",
            "zip_code": "94102",
            "coordinates": {"lat": 37.7749, "lon": -122.4194}
        },
        ...
    ]
}
```

### 3. Backend Service Modules

#### Location Service
**Responsibilities:**
- Resolve location queries to coordinates
- Validate zip codes
- Query Nominatim API for geocoding
- Cache location lookups

**Interface:**
```python
class LocationService:
    def resolve_location(query: str) -> Location
    def resolve_zip_code(zip_code: str) -> Location
    def resolve_coordinates(lat: float, lon: float) -> Location
    def get_autocomplete_suggestions(query: str) -> List[LocationSuggestion]
```

#### Weather Service
**Responsibilities:**
- Fetch weather data from weather.gov
- Parse HTML responses
- Extract weather metrics
- Parse advisories
- Cache weather data

**Interface:**
```python
class WeatherService:
    def get_weather_by_location(location: Location) -> WeatherData
    def get_weather_by_coordinates(lat: float, lon: float) -> WeatherData
    def parse_weather_page(html: str) -> WeatherData
    def parse_advisory(html: str) -> Optional[Advisory]
```

#### Cache Service
**Responsibilities:**
- Cache weather data with TTL
- Cache location lookups
- Implement LRU eviction
- Thread-safe operations

**Interface:**
```python
class CacheService:
    def get(key: str) -> Optional[Any]
    def set(key: str, value: Any, ttl: int)
    def clear()
```

## Data Models

### Location Model
```python
@dataclass
class Location:
    name: str
    display_name: str
    zip_code: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: str
    coordinates: Coordinates

@dataclass
class Coordinates:
    lat: float
    lon: float
```

### WeatherData Model
```python
@dataclass
class WeatherData:
    location: Location
    temp_f: float
    temp_c: float
    conditions: str
    rain_chance: int
    humidity: int
    wind_speed: str
    advisory: Optional[Advisory]
    timestamp: datetime
```

### Advisory Model
```python
@dataclass
class Advisory:
    type: str
    description: str
    severity: str  # "Warning", "Advisory", "Watch"
    
    def get_severity_rank(self) -> int:
        """Return numeric rank for severity comparison."""
```

### LocationSuggestion Model
```python
@dataclass
class LocationSuggestion:
    display_name: str
    type: str  # "city", "zip", "country"
    zip_code: Optional[str]
    coordinates: Coordinates
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: HTTPS enforcement for all requests

*For any* HTTP request to the web service, the request should be redirected to HTTPS or rejected.

**Validates: Requirements 1.4**

### Property 2: Autocomplete suggestions for search input

*For any* non-empty search query, the autocomplete endpoint should return a list of location suggestions.

**Validates: Requirements 2.2**

### Property 3: Weather data retrieval for valid locations

*For any* valid location (zip code, city, or coordinates), the weather endpoint should return complete weather data including all required fields.

**Validates: Requirements 2.4**

### Property 4: Zip code validation accepts only 5-digit strings

*For any* input string, the zip code validation should return true if and only if the string contains exactly 5 digits.

**Validates: Requirements 2.5**

### Property 5: Geolocation coordinates fetch weather data

*For any* valid latitude and longitude coordinates, the weather service should successfully retrieve and return weather data.

**Validates: Requirements 3.3, 3.5**

### Property 6: Weather display includes all required metrics

*For any* weather data object, the display should include temperature (F and C), conditions, rain chance, humidity, wind speed, and location name.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6**

### Property 7: Temperature displayed in both units

*For any* weather data, both Fahrenheit and Celsius temperature values should be present in the response and display.

**Validates: Requirements 5.2**

### Property 8: Weather metrics include visual indicators

*For any* weather metric displayed, there should be an associated icon or visual indicator element.

**Validates: Requirements 5.3**

### Property 9: Advisory presence is always communicated

*For any* weather data retrieval, the response should either include an advisory object or explicitly indicate no advisories are active.

**Validates: Requirements 6.1, 6.2, 6.5**

### Property 10: Advisory display includes all required information

*For any* advisory object, the display should contain the advisory type, full description, and severity information.

**Validates: Requirements 6.3**

### Property 11: Most severe advisory is selected from multiple advisories

*For any* collection of multiple advisory objects with different severity levels, only the advisory with the highest severity rank (Warning > Advisory > Watch) should be included in the response.

**Validates: Requirements 6.4**

### Property 12: Error messages are non-empty and descriptive

*For any* error condition (network failure, parsing failure, invalid location), the error message should be a non-empty string that describes the error type.

**Validates: Requirements 7.4**

### Property 13: Configurable port exposure

*For any* valid port number configuration, the Docker container should expose the web service on that port.

**Validates: Requirements 8.4**

### Property 14: API returns JSON for valid requests

*For any* valid API request to the weather endpoint, the response should be valid JSON containing weather data.

**Validates: Requirements 9.2**

### Property 15: API returns appropriate status codes for invalid requests

*For any* invalid API request (malformed parameters, missing required fields), the response should have an appropriate HTTP error status code (4xx) and error message.

**Validates: Requirements 9.3**

### Property 16: CORS headers present in API responses

*For any* API response, the response headers should include appropriate CORS headers to allow cross-origin requests.

**Validates: Requirements 9.4**

### Property 17: Cache improves response times

*For any* location that has been cached, subsequent requests for that location should return faster than the initial request.

**Validates: Requirements 10.3**

### Property 18: All requests are logged

*For any* incoming HTTP request, a log entry should be created with timestamp, request details, and request ID.

**Validates: Requirements 12.1**

### Property 19: All errors are logged with context

*For any* error that occurs during request processing, a log entry should be created with error details, stack trace, and request context.

**Validates: Requirements 12.2**

### Property 20: Logs written to standard output

*For any* log entry created, it should be written to standard output (stdout) for container-based log collection.

**Validates: Requirements 12.4**

### Property 21: Request IDs in all log entries

*For any* log entry, it should include a unique request ID that can be used to trace the request through the system.

**Validates: Requirements 12.5**

## Error Handling

### Error Categories

1. **Input Validation Errors**
   - Invalid zip code format
   - Invalid coordinates
   - Malformed API requests
   - HTTP Status: 400 Bad Request
   - Response: `{"error": "Invalid input", "message": "..."}`

2. **Network Errors**
   - Cannot connect to weather.gov
   - Cannot connect to Nominatim API
   - Timeout errors
   - HTTP Status: 502 Bad Gateway
   - Response: `{"error": "Network error", "message": "Unable to fetch weather data"}`

3. **Parsing Errors**
   - HTML structure changed
   - Missing expected data fields
   - HTTP Status: 500 Internal Server Error
   - Response: `{"error": "Parsing error", "message": "Unable to parse weather data"}`

4. **Location Errors**
   - Location not found
   - No weather data available for location
   - HTTP Status: 404 Not Found
   - Response: `{"error": "Location not found", "message": "..."}`

5. **Rate Limiting**
   - Too many requests from same IP
   - HTTP Status: 429 Too Many Requests
   - Response: `{"error": "Rate limit exceeded", "message": "Please try again later"}`

### Error Handling Strategy

- All errors should return JSON responses with consistent structure
- Frontend should display user-friendly error messages
- Errors should be logged with full context
- Network operations should have reasonable timeouts (10 seconds)
- Failed requests should be retryable
- Cache should be used to reduce external API calls

## Testing Strategy

### Unit Testing

The application will use Python's `pytest` framework for backend unit tests and Jest for frontend JavaScript tests.

**Backend Unit Tests:**
- API endpoint handlers
- Location service (geocoding, validation)
- Weather service (scraping, parsing)
- Cache service operations
- Error handling for all services

**Frontend Unit Tests:**
- Search interface component
- Autocomplete functionality
- Weather display component
- Geolocation handler
- Error display

### Property-Based Testing

The application will use the `hypothesis` library for property-based testing. Each property-based test will run a minimum of 100 iterations.

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
- Tag format: `# Feature: weather-web-service, Property {number}: {property_text}`
- Each correctness property must be implemented by exactly one property-based test
- Tests should use appropriate Hypothesis strategies for generating test data

**Property Tests to Implement:**

1. **Zip code validation** (Property 4)
   - Strategy: Generate random strings
   - Verify only 5-digit strings pass validation

2. **Weather data completeness** (Property 6)
   - Strategy: Generate random weather data
   - Verify all required fields are present

3. **Temperature unit display** (Property 7)
   - Strategy: Generate random temperature values
   - Verify both F and C are in response

4. **Advisory severity ranking** (Property 11)
   - Strategy: Generate lists of advisories with random severities
   - Verify highest severity is selected

5. **Error message non-empty** (Property 12)
   - Strategy: Trigger various error conditions
   - Verify all error messages are non-empty

6. **API JSON response** (Property 14)
   - Strategy: Generate random valid location queries
   - Verify responses are valid JSON

7. **CORS headers present** (Property 16)
   - Strategy: Make random API requests
   - Verify CORS headers in all responses

8. **Request logging** (Property 18)
   - Strategy: Generate random requests
   - Verify all requests are logged

### Integration Testing

Integration tests will verify the complete flow:
- End-to-end API requests
- Frontend-backend integration
- Docker container startup and health
- HTTPS redirect functionality
- Caching behavior
- Error handling across layers

### End-to-End Testing

E2E tests using Selenium or Playwright:
- Search by zip code
- Search by city name
- Use current location
- Display weather data
- Show advisories
- Handle errors gracefully

## Implementation Notes

### Frontend Implementation

**HTML Structure:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weather Service</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Weather Service</h1>
        </header>
        <div class="search-section">
            <input type="text" id="search-input" placeholder="Enter zip code, city, or country">
            <div id="autocomplete-suggestions"></div>
            <button id="current-location-btn">Use Current Location</button>
        </div>
        <div id="weather-display"></div>
        <div id="error-display"></div>
    </div>
    <script src="/static/js/app.js"></script>
</body>
</html>
```

**CSS Framework:**
- Use CSS Grid and Flexbox for layout
- Mobile-first responsive design
- CSS variables for theming
- Smooth transitions and animations

**JavaScript Architecture:**
- ES6 modules for code organization
- Async/await for API calls
- Event delegation for dynamic content
- Debouncing for autocomplete

### Backend Implementation

**Flask Application Structure:**
```
app/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── weather.py
│   └── autocomplete.py
├── services/
│   ├── __init__.py
│   ├── location_service.py
│   ├── weather_service.py
│   └── cache_service.py
├── models/
│   ├── __init__.py
│   ├── location.py
│   ├── weather.py
│   └── advisory.py
├── utils/
│   ├── __init__.py
│   ├── validators.py
│   └── logger.py
└── static/
    ├── css/
    ├── js/
    └── images/
```

**Flask Configuration:**
```python
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    CACHE_TTL = 300  # 5 minutes
    REQUEST_TIMEOUT = 10  # seconds
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
```

### Docker Implementation

**Dockerfile:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:create_app()"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - flask-app

  flask-app:
    build: .
    environment:
      - FLASK_ENV=production
      - LOG_LEVEL=INFO
    expose:
      - "5000"
```

### HTTPS Configuration

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name _;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location / {
        proxy_pass http://flask-app:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Caching Strategy

**Cache Implementation:**
- In-memory cache using Python dictionary with threading.Lock
- TTL-based expiration (5 minutes for weather data)
- LRU eviction when cache size exceeds limit
- Cache keys: location hash for weather, query string for autocomplete

**Cache Keys:**
```python
weather_key = f"weather:{lat}:{lon}"
autocomplete_key = f"autocomplete:{query}"
```

### Logging Strategy

**Log Format:**
```json
{
    "timestamp": "2024-12-07T20:00:00Z",
    "level": "INFO",
    "request_id": "abc123",
    "message": "Weather request",
    "location": "San Francisco, CA",
    "duration_ms": 250
}
```

**Log Levels:**
- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages for recoverable issues
- ERROR: Error messages for failures
- CRITICAL: Critical errors requiring immediate attention

## Dependencies

### Backend Dependencies

```
Flask>=2.3.0
gunicorn>=21.2.0
requests>=2.31.0
beautifulsoup4>=4.12.0
hypothesis>=6.90.0
pytest>=7.4.0
flask-cors>=4.0.0
```

### Frontend Dependencies

- No external JavaScript libraries (vanilla JS)
- Modern browser with ES6+ support
- Geolocation API support (optional)

## Security Considerations

1. **HTTPS Only**: All traffic must use HTTPS
2. **Input Validation**: Sanitize all user inputs
3. **Rate Limiting**: Prevent abuse with rate limits
4. **CORS Configuration**: Restrict origins in production
5. **Error Messages**: Don't expose internal details
6. **Dependency Updates**: Keep all dependencies updated
7. **Secret Management**: Use environment variables for secrets

## Performance Optimization

1. **Caching**: Cache weather data and location lookups
2. **Compression**: Enable gzip compression in Nginx
3. **Minification**: Minify CSS and JavaScript
4. **CDN**: Consider CDN for static assets
5. **Database**: Consider Redis for distributed caching
6. **Connection Pooling**: Reuse HTTP connections
7. **Async Operations**: Use async/await for I/O operations

## Future Enhancements

- Extended forecast (3-7 days)
- Weather maps and radar
- Historical weather data
- User accounts and saved locations
- Weather alerts via email/SMS
- Mobile app (React Native)
- GraphQL API
- Real-time weather updates via WebSocket
- Multi-language support
- Dark mode theme
