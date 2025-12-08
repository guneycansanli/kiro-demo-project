# Weather Web Service API Documentation

Complete API reference for the Weather Web Service REST API.

## Base URL

```
https://localhost/api
```

For local development without HTTPS:
```
http://localhost:5000/api
```

## Authentication

No authentication is required for this API. All endpoints are publicly accessible.

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Limit**: 100 requests per minute per IP address
- **Headers**: Rate limit information is included in response headers
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Time when the rate limit resets (Unix timestamp)

When rate limit is exceeded:
```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again later."
}
```

## Response Format

All API responses are in JSON format with appropriate HTTP status codes.

### Success Response

```json
{
  "location": { ... },
  "weather": { ... },
  "advisory": { ... } | null,
  "timestamp": "2024-12-07T20:00:00Z"
}
```

### Error Response

```json
{
  "error": "Error type",
  "message": "Detailed error message"
}
```

## HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success - Request completed successfully |
| `400` | Bad Request - Invalid parameters or malformed request |
| `404` | Not Found - Location not found or resource doesn't exist |
| `429` | Too Many Requests - Rate limit exceeded |
| `500` | Internal Server Error - Server-side error occurred |
| `502` | Bad Gateway - External API unavailable |
| `503` | Service Unavailable - Service temporarily unavailable |

## CORS

The API supports Cross-Origin Resource Sharing (CORS) with the following headers:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

In production, configure `CORS_ORIGINS` environment variable to restrict allowed origins.

---

## Endpoints

### 1. Get Weather by Location

Retrieve weather data for a location specified by name (city, state, country).

**Endpoint**: `GET /api/weather`

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `location` | string | Yes* | Location name (e.g., "San Francisco", "New York, NY") |
| `zip` | string | Yes* | 5-digit US zip code (alternative to location) |

*Either `location` or `zip` must be provided, but not both.

**Example Requests**:

```bash
# By city name
curl "https://localhost/api/weather?location=San%20Francisco"

# By city and state
curl "https://localhost/api/weather?location=New%20York,%20NY"

# By zip code
curl "https://localhost/api/weather?zip=94102"
```

**Success Response** (200 OK):

```json
{
  "location": {
    "name": "San Francisco, CA",
    "display_name": "San Francisco, California, United States",
    "zip_code": null,
    "city": "San Francisco",
    "state": "California",
    "country": "United States",
    "coordinates": {
      "lat": 37.7749,
      "lon": -122.4194
    }
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
    "description": "Excessive heat warning in effect until 8:00 PM EDT this evening. Heat index values up to 105 expected.",
    "severity": "Advisory"
  },
  "timestamp": "2024-12-07T20:00:00Z"
}
```

**Error Responses**:

```json
// 400 Bad Request - Missing parameters
{
  "error": "Invalid input",
  "message": "Either 'location' or 'zip' parameter is required"
}

// 400 Bad Request - Invalid zip code
{
  "error": "Invalid input",
  "message": "Zip code must be exactly 5 digits"
}

// 404 Not Found - Location not found
{
  "error": "Location not found",
  "message": "Could not find weather data for the specified location"
}

// 502 Bad Gateway - External API error
{
  "error": "Network error",
  "message": "Unable to fetch weather data from external service"
}
```

---

### 2. Get Weather by Coordinates

Retrieve weather data for a specific geographic location using latitude and longitude.

**Endpoint**: `GET /api/weather/coordinates`

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lat` | float | Yes | Latitude (-90 to 90) |
| `lon` | float | Yes | Longitude (-180 to 180) |

**Example Requests**:

```bash
# San Francisco coordinates
curl "https://localhost/api/weather/coordinates?lat=37.7749&lon=-122.4194"

# New York coordinates
curl "https://localhost/api/weather/coordinates?lat=40.7128&lon=-74.0060"
```

**Success Response** (200 OK):

```json
{
  "location": {
    "name": "San Francisco, CA",
    "display_name": "San Francisco, California, United States",
    "zip_code": null,
    "city": "San Francisco",
    "state": "California",
    "country": "United States",
    "coordinates": {
      "lat": 37.7749,
      "lon": -122.4194
    }
  },
  "weather": {
    "temp_f": 65.0,
    "temp_c": 18.3,
    "conditions": "Partly Cloudy",
    "rain_chance": 20,
    "humidity": 65,
    "wind_speed": "10 mph"
  },
  "advisory": null,
  "timestamp": "2024-12-07T20:00:00Z"
}
```

**Error Responses**:

```json
// 400 Bad Request - Missing parameters
{
  "error": "Invalid input",
  "message": "Both 'lat' and 'lon' parameters are required"
}

// 400 Bad Request - Invalid coordinates
{
  "error": "Invalid input",
  "message": "Latitude must be between -90 and 90"
}

// 400 Bad Request - Invalid coordinates
{
  "error": "Invalid input",
  "message": "Longitude must be between -180 and 180"
}

// 404 Not Found - No weather data
{
  "error": "Location not found",
  "message": "No weather data available for these coordinates"
}
```

---

### 3. Get Location Autocomplete Suggestions

Get location suggestions for autocomplete as the user types.

**Endpoint**: `GET /api/autocomplete`

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query (minimum 2 characters) |

**Example Requests**:

```bash
# Search for "San"
curl "https://localhost/api/autocomplete?q=San"

# Search for "New York"
curl "https://localhost/api/autocomplete?q=New%20York"
```

**Success Response** (200 OK):

```json
{
  "suggestions": [
    {
      "display_name": "San Francisco, California, United States",
      "type": "city",
      "zip_code": null,
      "coordinates": {
        "lat": 37.7749,
        "lon": -122.4194
      }
    },
    {
      "display_name": "San Diego, California, United States",
      "type": "city",
      "zip_code": null,
      "coordinates": {
        "lat": 32.7157,
        "lon": -117.1611
      }
    },
    {
      "display_name": "San Jose, California, United States",
      "type": "city",
      "zip_code": null,
      "coordinates": {
        "lat": 37.3382,
        "lon": -121.8863
      }
    }
  ]
}
```

**Error Responses**:

```json
// 400 Bad Request - Missing query
{
  "error": "Invalid input",
  "message": "Query parameter 'q' is required"
}

// 400 Bad Request - Query too short
{
  "error": "Invalid input",
  "message": "Query must be at least 2 characters long"
}

// 502 Bad Gateway - Geocoding service error
{
  "error": "Network error",
  "message": "Unable to fetch location suggestions"
}
```

---

### 4. Health Check

Check if the API service is running and healthy.

**Endpoint**: `GET /api/health`

**Parameters**: None

**Example Request**:

```bash
curl "https://localhost/api/health"
```

**Success Response** (200 OK):

```json
{
  "status": "healthy",
  "service": "weather-web-service",
  "timestamp": "2024-12-07T20:00:00Z"
}
```

**Error Response** (503 Service Unavailable):

```json
{
  "status": "unhealthy",
  "service": "weather-web-service",
  "message": "Service is experiencing issues"
}
```

---

## Data Models

### Location Object

```json
{
  "name": "San Francisco, CA",
  "display_name": "San Francisco, California, United States",
  "zip_code": "94102",
  "city": "San Francisco",
  "state": "California",
  "country": "United States",
  "coordinates": {
    "lat": 37.7749,
    "lon": -122.4194
  }
}
```

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Short location name |
| `display_name` | string | Full location name with hierarchy |
| `zip_code` | string \| null | US zip code if available |
| `city` | string \| null | City name |
| `state` | string \| null | State/province name |
| `country` | string | Country name |
| `coordinates` | object | Latitude and longitude |

### Coordinates Object

```json
{
  "lat": 37.7749,
  "lon": -122.4194
}
```

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `lat` | float | Latitude (-90 to 90) |
| `lon` | float | Longitude (-180 to 180) |

### Weather Object

```json
{
  "temp_f": 65.0,
  "temp_c": 18.3,
  "conditions": "Partly Cloudy",
  "rain_chance": 20,
  "humidity": 65,
  "wind_speed": "10 mph"
}
```

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `temp_f` | float | Temperature in Fahrenheit |
| `temp_c` | float | Temperature in Celsius |
| `conditions` | string | Weather conditions description |
| `rain_chance` | integer | Chance of rain (0-100%) |
| `humidity` | integer | Humidity percentage (0-100%) |
| `wind_speed` | string | Wind speed with units |

### Advisory Object

```json
{
  "type": "Heat Advisory",
  "description": "Excessive heat warning in effect until 8:00 PM EDT this evening.",
  "severity": "Advisory"
}
```

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Advisory type (e.g., "Heat Advisory", "Winter Storm Warning") |
| `description` | string | Detailed advisory description |
| `severity` | string | Severity level: "Warning", "Advisory", or "Watch" |

**Severity Levels** (highest to lowest):
1. **Warning** - Most severe, immediate action required
2. **Advisory** - Moderate severity, caution advised
3. **Watch** - Lowest severity, be aware

When multiple advisories are active, only the most severe is returned.

### LocationSuggestion Object

```json
{
  "display_name": "San Francisco, California, United States",
  "type": "city",
  "zip_code": null,
  "coordinates": {
    "lat": 37.7749,
    "lon": -122.4194
  }
}
```

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `display_name` | string | Full location name |
| `type` | string | Location type (e.g., "city", "state", "country") |
| `zip_code` | string \| null | US zip code if available |
| `coordinates` | object | Latitude and longitude |

---

## Code Examples

### JavaScript (Fetch API)

```javascript
// Get weather by location
async function getWeather(location) {
  try {
    const response = await fetch(
      `https://localhost/api/weather?location=${encodeURIComponent(location)}`
    );
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message);
    }
    
    const data = await response.json();
    console.log('Weather:', data);
    return data;
  } catch (error) {
    console.error('Error fetching weather:', error);
    throw error;
  }
}

// Get weather by coordinates
async function getWeatherByCoordinates(lat, lon) {
  try {
    const response = await fetch(
      `https://localhost/api/weather/coordinates?lat=${lat}&lon=${lon}`
    );
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching weather:', error);
    throw error;
  }
}

// Get autocomplete suggestions
async function getAutocompleteSuggestions(query) {
  try {
    const response = await fetch(
      `https://localhost/api/autocomplete?q=${encodeURIComponent(query)}`
    );
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message);
    }
    
    const data = await response.json();
    return data.suggestions;
  } catch (error) {
    console.error('Error fetching suggestions:', error);
    throw error;
  }
}

// Usage
getWeather('San Francisco').then(data => {
  console.log(`Temperature: ${data.weather.temp_f}°F`);
  console.log(`Conditions: ${data.weather.conditions}`);
});
```

### Python (requests)

```python
import requests

BASE_URL = "https://localhost/api"

def get_weather(location):
    """Get weather by location name."""
    response = requests.get(
        f"{BASE_URL}/weather",
        params={"location": location},
        verify=False  # Only for self-signed certificates
    )
    response.raise_for_status()
    return response.json()

def get_weather_by_coordinates(lat, lon):
    """Get weather by coordinates."""
    response = requests.get(
        f"{BASE_URL}/weather/coordinates",
        params={"lat": lat, "lon": lon},
        verify=False
    )
    response.raise_for_status()
    return response.json()

def get_autocomplete_suggestions(query):
    """Get location autocomplete suggestions."""
    response = requests.get(
        f"{BASE_URL}/autocomplete",
        params={"q": query},
        verify=False
    )
    response.raise_for_status()
    return response.json()["suggestions"]

# Usage
try:
    data = get_weather("San Francisco")
    print(f"Temperature: {data['weather']['temp_f']}°F")
    print(f"Conditions: {data['weather']['conditions']}")
    
    if data['advisory']:
        print(f"Advisory: {data['advisory']['type']}")
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
```

### cURL

```bash
# Get weather by location
curl -X GET "https://localhost/api/weather?location=San%20Francisco" \
  -H "Accept: application/json" \
  -k

# Get weather by zip code
curl -X GET "https://localhost/api/weather?zip=94102" \
  -H "Accept: application/json" \
  -k

# Get weather by coordinates
curl -X GET "https://localhost/api/weather/coordinates?lat=37.7749&lon=-122.4194" \
  -H "Accept: application/json" \
  -k

# Get autocomplete suggestions
curl -X GET "https://localhost/api/autocomplete?q=San" \
  -H "Accept: application/json" \
  -k

# Health check
curl -X GET "https://localhost/api/health" \
  -H "Accept: application/json" \
  -k

# With pretty printing (using jq)
curl -X GET "https://localhost/api/weather?location=San%20Francisco" \
  -H "Accept: application/json" \
  -k | jq '.'
```

Note: The `-k` flag is used to accept self-signed certificates in development. Remove it when using trusted certificates in production.

---

## Caching

The API implements intelligent caching to improve performance:

- **Weather Data**: Cached for 5 minutes (configurable via `CACHE_TTL` environment variable)
- **Location Lookups**: Cached to reduce geocoding API calls
- **Cache Key Format**: `weather:{lat}:{lon}` for weather, `autocomplete:{query}` for suggestions

**Cache Headers**:

Responses include cache-related headers:

```
X-Cache-Status: HIT | MISS
X-Cache-TTL: 300
```

- `HIT`: Data served from cache
- `MISS`: Fresh data fetched from external APIs

---

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "error": "Error category",
  "message": "Human-readable error description"
}
```

### Error Categories

| Error | HTTP Status | Description |
|-------|-------------|-------------|
| `Invalid input` | 400 | Invalid parameters or malformed request |
| `Location not found` | 404 | Location doesn't exist or no weather data available |
| `Rate limit exceeded` | 429 | Too many requests from the same IP |
| `Network error` | 502 | Cannot connect to external APIs |
| `Parsing error` | 500 | Cannot parse weather data |
| `Internal server error` | 500 | Unexpected server error |

### Retry Strategy

For transient errors (502, 503), implement exponential backoff:

```javascript
async function fetchWithRetry(url, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url);
      if (response.ok) return response;
      
      // Don't retry client errors (4xx)
      if (response.status >= 400 && response.status < 500) {
        throw new Error('Client error');
      }
      
      // Retry server errors (5xx)
      if (i < maxRetries - 1) {
        await new Promise(resolve => 
          setTimeout(resolve, Math.pow(2, i) * 1000)
        );
      }
    } catch (error) {
      if (i === maxRetries - 1) throw error;
    }
  }
}
```

---

## Best Practices

### 1. Always Handle Errors

```javascript
try {
  const data = await getWeather(location);
  displayWeather(data);
} catch (error) {
  displayError(error.message);
}
```

### 2. Use Appropriate Timeouts

```javascript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 10000);

fetch(url, { signal: controller.signal })
  .then(response => response.json())
  .finally(() => clearTimeout(timeoutId));
```

### 3. Implement Debouncing for Autocomplete

```javascript
let debounceTimer;
function debounce(func, delay) {
  return function(...args) {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => func.apply(this, args), delay);
  };
}

const debouncedAutocomplete = debounce(getAutocompleteSuggestions, 300);
```

### 4. Cache Responses Client-Side

```javascript
const cache = new Map();

async function getCachedWeather(location) {
  const cacheKey = `weather:${location}`;
  const cached = cache.get(cacheKey);
  
  if (cached && Date.now() - cached.timestamp < 300000) {
    return cached.data;
  }
  
  const data = await getWeather(location);
  cache.set(cacheKey, { data, timestamp: Date.now() });
  return data;
}
```

### 5. Validate Input Before Sending

```javascript
function isValidZipCode(zip) {
  return /^\d{5}$/.test(zip);
}

function isValidCoordinates(lat, lon) {
  return lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180;
}
```

---

## Changelog

### Version 1.0.0 (2024-12-07)

- Initial API release
- Weather data retrieval by location, zip code, and coordinates
- Location autocomplete suggestions
- Weather advisory support
- HTTPS support
- Caching implementation
- CORS support

---

## Support

For API issues or questions:

1. Check this documentation
2. Review the [main README](README.md)
3. Check application logs
4. Create an issue in the repository

---

**API Version**: 1.0.0  
**Last Updated**: December 7, 2024
