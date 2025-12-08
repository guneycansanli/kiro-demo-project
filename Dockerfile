# Dockerfile for Weather Web Service
# Multi-stage build for production-ready Flask application
# Validates: Requirements 8.1, 8.3, 8.5

# Base Image
# Use Python 3.10 slim variant for smaller image size
# Slim variant includes only essential packages
FROM python:3.10-slim

# Set Working Directory
# All subsequent commands will run in /app directory
WORKDIR /app

# Install Python Dependencies
# Copy requirements file first to leverage Docker layer caching
# If requirements don't change, this layer will be cached
COPY requirements-web.txt .

# Install dependencies without caching pip files to reduce image size
# --no-cache-dir: Don't cache downloaded packages
# This reduces the final image size significantly
RUN pip install --no-cache-dir -r requirements-web.txt

# Copy Application Code
# Copy all application files to the container
# This includes:
# - app/ directory (Flask application)
# - wsgi.py (WSGI entry point)
# - Configuration files
COPY . .

# Expose Application Port
# Document that the container listens on port 5000
# This is informational only; actual port binding happens at runtime
# Validates: Requirements 8.4
EXPOSE 5000

# Run Application with Gunicorn
# Gunicorn is a production-grade WSGI HTTP server
# Configuration:
# --bind 0.0.0.0:5000: Listen on all interfaces, port 5000
# --workers 4: Run 4 worker processes for handling requests
#              Recommended: (2 x CPU cores) + 1
# wsgi:app: Import 'app' from wsgi.py module
# Validates: Requirements 8.3, 8.5
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "wsgi:app"]
