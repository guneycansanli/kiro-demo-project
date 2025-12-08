# Weather Web Service

A web-based weather service that provides current weather information through an HTTPS web interface. Users can search for weather by zip code, city name, or country, with autocomplete suggestions and geolocation support.

## Features

- 🌐 Web-based interface accessible from any browser
- 🔍 Search by zip code, city name, or country
- 📍 Geolocation support for current location weather
- 💡 Real-time autocomplete suggestions
- 🌡️ Temperature in both Fahrenheit and Celsius
- 🌧️ Comprehensive weather metrics (rain chance, humidity, wind speed)
- ⚠️ Active weather advisories display
- 🔒 HTTPS support for secure communication
- 🐳 Docker containerized for easy deployment
- 📱 Responsive design for mobile and desktop

## Technology Stack

- **Backend**: Python 3.10+ with Flask
- **Frontend**: HTML5, CSS3, vanilla JavaScript
- **Web Server**: Gunicorn (production)
- **Containerization**: Docker and Docker Compose
- **HTTPS**: Nginx reverse proxy with SSL/TLS
- **Data Source**: weather.gov (National Weather Service)
- **Location Data**: OpenStreetMap Nominatim API

## Project Structure

```
.
├── app/
│   ├── __init__.py           # Flask application factory
│   ├── api/                  # API endpoints
│   │   ├── __init__.py
│   │   ├── weather.py        # Weather endpoints
│   │   └── autocomplete.py   # Autocomplete endpoints
│   ├── models/               # Data models
│   │   ├── __init__.py
│   │   ├── location.py
│   │   ├── weather.py
│   │   └── advisory.py
│   ├── services/             # Business logic
│   │   └── __init__.py
│   ├── utils/                # Utilities
│   │   ├── __init__.py
│   │   └── logger.py
│   ├── static/               # Frontend assets
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── app.js
│   └── templates/            # HTML templates
│       └── index.html
├── wsgi.py                   # WSGI entry point
├── requirements-web.txt      # Python dependencies
└── README-web.md            # This file
```

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Docker and Docker Compose (for containerized deployment)

### Local Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements-web.txt
```

4. Run the development server:
```bash
python wsgi.py
```

5. Open your browser and navigate to:
```
http://localhost:5000
```

## Docker Deployment

Docker configuration will be added in later implementation tasks.

## API Endpoints

### Weather Endpoints

- `GET /api/weather?location=<query>` - Get weather by location
- `GET /api/weather?zip=<zipcode>` - Get weather by zip code
- `GET /api/weather/coordinates?lat=<lat>&lon=<lon>` - Get weather by coordinates

### Autocomplete Endpoint

- `GET /api/autocomplete?q=<query>` - Get location suggestions

## Configuration

Environment variables:

- `SECRET_KEY` - Flask secret key (default: 'dev-secret-key')
- `CACHE_TTL` - Cache time-to-live in seconds (default: 300)
- `REQUEST_TIMEOUT` - HTTP request timeout in seconds (default: 10)
- `LOG_LEVEL` - Logging level (default: 'INFO')
- `CORS_ORIGINS` - CORS allowed origins (default: '*')

## Development Status

This project is currently under development. The following tasks are in progress:

- ✅ Project structure and dependencies setup
- ⏳ Core data models implementation
- ⏳ Validation utilities
- ⏳ Cache service
- ⏳ Location service
- ⏳ Weather scraping service
- ⏳ API endpoints
- ⏳ Frontend implementation
- ⏳ Docker configuration
- ⏳ HTTPS support

## Testing

Testing framework will be set up in later implementation tasks.

## License

This is an educational project. Use at your own discretion.

## Acknowledgments

Weather data provided by the National Weather Service (weather.gov).
Location data provided by OpenStreetMap Nominatim API.
