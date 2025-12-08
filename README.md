# Weather Web Service

A modern web-based weather service that provides current weather information through an HTTPS web interface. Search for weather by zip code, city name, or country with real-time autocomplete suggestions and geolocation support. Built with Flask and containerized with Docker for easy deployment.

## 🌟 Features

- **🌐 Web Interface**: Clean, responsive web UI accessible from any browser
- **🔍 Smart Search**: Search by US zip code, city name, or country
- **💡 Autocomplete**: Real-time location suggestions as you type
- **📍 Geolocation**: One-click weather for your current location
- **🌡️ Comprehensive Data**: Temperature (F & C), rain chance, humidity, wind speed, conditions
- **⚠️ Weather Advisories**: Prominent display of active weather warnings and advisories
- **🔒 HTTPS Secure**: All traffic encrypted with SSL/TLS
- **🐳 Docker Ready**: Fully containerized for easy deployment
- **📱 Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **⚡ Fast & Cached**: Intelligent caching for improved response times
- **🔌 REST API**: JSON API for integration with other applications

## 📸 Screenshots

### Main Interface
The clean search interface with autocomplete suggestions:

```
┌─────────────────────────────────────────────────────┐
│              Weather Service                         │
├─────────────────────────────────────────────────────┤
│  Search: [San Francisco, CA____________]            │
│          ┌──────────────────────────────┐           │
│          │ San Francisco, California    │           │
│          │ San Francisco Bay, CA        │           │
│          │ South San Francisco, CA      │           │
│          └──────────────────────────────┘           │
│  [📍 Use Current Location]                          │
└─────────────────────────────────────────────────────┘
```

### Weather Display
Comprehensive weather information with visual indicators:

```
┌─────────────────────────────────────────────────────┐
│  San Francisco, California                          │
│                                                      │
│  🌡️  65°F (18°C)                                    │
│  ☁️  Partly Cloudy                                  │
│                                                      │
│  🌧️ Rain Chance: 20%                               │
│  💧 Humidity: 65%                                   │
│  💨 Wind Speed: 10 mph                              │
│                                                      │
│  ✅ No active advisories                            │
└─────────────────────────────────────────────────────┘
```

### Weather Advisory
Prominent display when advisories are active:

```
┌─────────────────────────────────────────────────────┐
│  ⚠️  HEAT ADVISORY                                  │
│  Excessive heat warning in effect until 8:00 PM.   │
│  Heat index values up to 105 expected.              │
└─────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Clone the repository**:
```bash
git clone <repository-url>
cd weather-web-service
```

2. **Generate SSL certificates** (for development):
```bash
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -nodes \
  -out ssl/cert.pem \
  -keyout ssl/key.pem \
  -days 365 \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

3. **Start the services**:
```bash
docker-compose up -d
```

4. **Access the application**:
- Open your browser to `https://localhost`
- Accept the self-signed certificate warning (development only)

That's it! The weather service is now running.

### Local Development (Without Docker)

1. **Install Python 3.10+** and create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements-web.txt
```

3. **Run the development server**:
```bash
python wsgi.py
```

4. **Access the application**:
- Open your browser to `http://localhost:5000`

## 📋 Requirements

### For Docker Deployment
- Docker Engine 20.10+
- Docker Compose 2.0+

### For Local Development
- Python 3.10 or higher
- pip (Python package manager)
- Internet connection (for weather data APIs)

## 🏗️ Architecture

### Technology Stack

- **Backend**: Python 3.10+ with Flask web framework
- **Frontend**: HTML5, CSS3, vanilla JavaScript (ES6+)
- **Web Server**: Gunicorn (production WSGI server)
- **Reverse Proxy**: Nginx with SSL/TLS termination
- **Containerization**: Docker and Docker Compose
- **Data Sources**: 
  - weather.gov (National Weather Service)
  - OpenStreetMap Nominatim API (geocoding)

### Project Structure

```
weather-web-service/
├── app/
│   ├── __init__.py              # Flask application factory
│   ├── api/                     # API endpoints
│   │   ├── __init__.py
│   │   ├── weather.py           # Weather API endpoints
│   │   └── autocomplete.py      # Autocomplete API endpoints
│   ├── models/                  # Data models
│   │   ├── __init__.py
│   │   ├── location.py          # Location and coordinates models
│   │   ├── weather.py           # Weather data model
│   │   └── advisory.py          # Weather advisory model
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── location_service.py  # Location resolution & geocoding
│   │   ├── weather_service.py   # Weather data scraping
│   │   └── cache_service.py     # Caching service
│   ├── utils/                   # Utility modules
│   │   ├── __init__.py
│   │   ├── validators.py        # Input validation
│   │   └── logger.py            # Logging configuration
│   ├── static/                  # Frontend assets
│   │   ├── css/
│   │   │   └── style.css        # Application styles
│   │   └── js/
│   │       └── app.js           # Frontend JavaScript
│   └── templates/               # HTML templates
│       └── index.html           # Main application page
├── tests/                       # Test suite
│   ├── test_api.py              # API endpoint tests
│   ├── test_models.py           # Data model tests
│   ├── test_validators.py       # Validation tests
│   ├── test_cache.py            # Cache service tests
│   ├── test_location_service.py # Location service tests
│   ├── test_weather_service.py  # Weather service tests
│   ├── test_logging.py          # Logging tests
│   └── test_docker.py           # Docker integration tests
├── ssl/                         # SSL certificates
│   ├── cert.pem                 # SSL certificate
│   └── key.pem                  # SSL private key
├── wsgi.py                      # WSGI entry point
├── Dockerfile                   # Docker image definition
├── docker-compose.yml           # Docker Compose configuration
├── nginx.conf                   # Nginx configuration
├── requirements-web.txt         # Python dependencies
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## 🔌 API Documentation

### Weather Endpoints

#### Get Weather by Location
```http
GET /api/weather?location=<query>
```

**Parameters**:
- `location` (string): City name, zip code, or location query

**Example**:
```bash
curl "https://localhost/api/weather?location=San%20Francisco"
```

**Response**:
```json
{
  "location": {
    "name": "San Francisco, CA",
    "display_name": "San Francisco, California, United States",
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

#### Get Weather by Zip Code
```http
GET /api/weather?zip=<zipcode>
```

**Parameters**:
- `zip` (string): 5-digit US zip code

**Example**:
```bash
curl "https://localhost/api/weather?zip=94102"
```

#### Get Weather by Coordinates
```http
GET /api/weather/coordinates?lat=<latitude>&lon=<longitude>
```

**Parameters**:
- `lat` (float): Latitude (-90 to 90)
- `lon` (float): Longitude (-180 to 180)

**Example**:
```bash
curl "https://localhost/api/weather/coordinates?lat=37.7749&lon=-122.4194"
```

### Autocomplete Endpoint

#### Get Location Suggestions
```http
GET /api/autocomplete?q=<query>
```

**Parameters**:
- `q` (string): Search query (minimum 2 characters)

**Example**:
```bash
curl "https://localhost/api/autocomplete?q=San%20Fran"
```

**Response**:
```json
{
  "suggestions": [
    {
      "display_name": "San Francisco, California, United States",
      "type": "city",
      "coordinates": {
        "lat": 37.7749,
        "lon": -122.4194
      }
    },
    {
      "display_name": "San Francisco Bay, California, United States",
      "type": "bay",
      "coordinates": {
        "lat": 37.8,
        "lon": -122.4
      }
    }
  ]
}
```

### Error Responses

All API endpoints return consistent error responses:

```json
{
  "error": "Error type",
  "message": "Detailed error message"
}
```

**HTTP Status Codes**:
- `200 OK` - Successful request
- `400 Bad Request` - Invalid input parameters
- `404 Not Found` - Location not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `502 Bad Gateway` - External API unavailable

## ⚙️ Configuration

### Environment Variables

Create a `.env` file or set environment variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Flask secret key for sessions | `dev-secret-key` | Yes (production) |
| `CACHE_TTL` | Cache time-to-live in seconds | `300` | No |
| `REQUEST_TIMEOUT` | HTTP request timeout in seconds | `10` | No |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | `INFO` | No |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated or *) | `*` | No |

### Example .env File

```bash
# Flask Configuration
SECRET_KEY=your-secure-random-secret-key-here
FLASK_ENV=production

# Cache Configuration
CACHE_TTL=300

# Request Configuration
REQUEST_TIMEOUT=10

# Logging Configuration
LOG_LEVEL=INFO

# CORS Configuration
CORS_ORIGINS=*
```

**Generate a secure secret key**:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## 🧪 Testing

### Run All Tests

```bash
# Install test dependencies
pip install -r requirements-web.txt

# Run all tests with coverage
python -m pytest tests/ -v --cov=app

# Run specific test file
python -m pytest tests/test_api.py -v

# Run with property-based testing
python -m pytest tests/ -v --hypothesis-show-statistics
```

### Test Categories

- **Unit Tests**: Test individual components and functions
- **Property-Based Tests**: Test properties across many random inputs using Hypothesis
- **Integration Tests**: Test API endpoints and service integration
- **Docker Tests**: Test Docker container build and deployment

### Example Test Output

```
tests/test_api.py::test_weather_endpoint PASSED
tests/test_api.py::test_autocomplete_endpoint PASSED
tests/test_validators.py::test_zip_code_validation PASSED
tests/test_cache.py::test_cache_round_trip PASSED

==================== 45 passed in 2.34s ====================
```

## 🐳 Docker Deployment

### Quick Start

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Docker Services

The application runs two containers:

1. **nginx**: Reverse proxy with SSL/TLS termination
   - Ports: 80 (HTTP), 443 (HTTPS)
   - Handles HTTPS and forwards to Flask app

2. **flask-app**: Flask application with Gunicorn
   - Port: 5000 (internal)
   - Runs the weather service

### Health Check

```bash
# Check service health
curl -k https://localhost/api/health

# Expected response
{"status": "healthy", "service": "weather-web-service"}
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f flask-app
docker-compose logs -f nginx
```

For detailed Docker documentation, see [DOCKER.md](DOCKER.md).

## 🔒 HTTPS & Security

### Development (Self-Signed Certificates)

For local development, use self-signed certificates:

```bash
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -nodes \
  -out ssl/cert.pem \
  -keyout ssl/key.pem \
  -days 365 \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

Browsers will show a security warning - this is expected for self-signed certificates.

### Production (Trusted Certificates)

For production, use certificates from a trusted Certificate Authority:

**Option 1: Let's Encrypt (Free)**
```bash
# Install certbot
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates to ssl directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem
```

**Option 2: Commercial CA**
- Purchase SSL certificate from a trusted CA
- Place certificate in `ssl/cert.pem`
- Place private key in `ssl/key.pem`

### Security Best Practices

- ✅ Always use HTTPS in production
- ✅ Set a strong `SECRET_KEY` (use `secrets.token_hex(32)`)
- ✅ Restrict `CORS_ORIGINS` to specific domains in production
- ✅ Keep dependencies updated
- ✅ Use environment variables for sensitive configuration
- ✅ Enable rate limiting for production deployments
- ✅ Monitor logs for suspicious activity

## 📊 Performance

### Caching

The application implements intelligent caching:

- **Weather Data**: Cached for 5 minutes (configurable via `CACHE_TTL`)
- **Location Lookups**: Cached to reduce geocoding API calls
- **LRU Eviction**: Automatically removes least recently used entries
- **Thread-Safe**: Safe for concurrent requests

### Response Times

Typical response times:

- **Cached Weather Data**: < 50ms
- **Fresh Weather Data**: 500ms - 2s (depends on external APIs)
- **Autocomplete**: < 500ms
- **Page Load**: < 2s

### Optimization Tips

1. **Increase Cache TTL**: For less frequently changing data
2. **Use CDN**: For static assets in production
3. **Enable Compression**: Gzip compression in Nginx (already configured)
4. **Scale Horizontally**: Run multiple Flask instances with Docker Compose
5. **Add Redis**: For distributed caching across multiple instances

## 🔧 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Check what's using port 80/443
sudo lsof -i :80
sudo lsof -i :443

# Change ports in docker-compose.yml
ports:
  - "8080:80"
  - "8443:443"
```

#### SSL Certificate Errors
```bash
# Verify certificates exist
ls -la ssl/

# Regenerate if missing
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -nodes \
  -out ssl/cert.pem -keyout ssl/key.pem -days 365 \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

#### Cannot Connect to External APIs
```bash
# Test connectivity
curl https://weather.gov
curl https://nominatim.openstreetmap.org

# Check Docker network
docker-compose exec flask-app ping -c 3 weather.gov
```

#### Application Won't Start
```bash
# Check logs
docker-compose logs flask-app

# Common issues:
# - Missing environment variables
# - Invalid configuration
# - Port conflicts
```

### Debug Mode

Enable debug logging:

```bash
# Set in .env
LOG_LEVEL=DEBUG

# Restart services
docker-compose restart
```

## 🚀 Production Deployment

### Pre-Deployment Checklist

- [ ] Generate trusted SSL certificates (Let's Encrypt or commercial CA)
- [ ] Set secure `SECRET_KEY` environment variable
- [ ] Configure `CORS_ORIGINS` to restrict allowed domains
- [ ] Set `LOG_LEVEL=INFO` or `LOG_LEVEL=WARNING`
- [ ] Review and adjust `CACHE_TTL` for your use case
- [ ] Set up monitoring and alerting
- [ ] Configure automated backups (if using persistent storage)
- [ ] Test all endpoints thoroughly
- [ ] Load test the application
- [ ] Set up log aggregation (e.g., ELK stack, CloudWatch)

### Deployment Options

1. **Docker Compose** (Single Server)
   - Simple deployment for small to medium traffic
   - Use the provided `docker-compose.yml`

2. **Kubernetes** (Scalable)
   - For high availability and auto-scaling
   - Create Kubernetes manifests from Docker images

3. **Cloud Platforms**
   - AWS ECS/Fargate
   - Google Cloud Run
   - Azure Container Instances

### Scaling

Run multiple Flask instances:

```bash
docker-compose up -d --scale flask-app=3
```

Nginx will automatically load balance between instances.

## 📝 Development

### Adding New Features

1. **Create a feature branch**:
```bash
git checkout -b feature/your-feature-name
```

2. **Make changes** following the project structure

3. **Write tests** for new functionality

4. **Run tests**:
```bash
python -m pytest tests/ -v
```

5. **Submit a pull request**

### Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions small and focused
- Add comments for complex logic

### Running Development Server

```bash
# With auto-reload
FLASK_ENV=development python wsgi.py

# Or use Flask CLI
export FLASK_APP=wsgi.py
flask run --reload
```

## 📄 License

This is an educational project. Use at your own discretion.

## 🙏 Acknowledgments

- **Weather Data**: National Weather Service (weather.gov)
- **Location Data**: OpenStreetMap Nominatim API
- **Icons**: Weather icons from various open-source projects

## 📞 Support

For issues, questions, or contributions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review existing issues in the repository
3. Create a new issue with detailed information
4. Include logs and error messages

## 🗺️ Roadmap

Future enhancements planned:

- [ ] Extended forecast (3-7 days)
- [ ] Weather maps and radar
- [ ] Historical weather data
- [ ] User accounts and saved locations
- [ ] Weather alerts via email/SMS
- [ ] Mobile app (React Native)
- [ ] GraphQL API
- [ ] Real-time updates via WebSocket
- [ ] Multi-language support
- [ ] Dark mode theme
- [ ] Weather widgets for embedding

---

**Built with ❤️ using Flask, Docker, and modern web technologies**
