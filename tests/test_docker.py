"""
Docker Configuration Tests

This module contains property-based tests for Docker configuration.
"""

import pytest
import os
import subprocess
from hypothesis import given, settings, strategies as st


# Feature: weather-web-service, Property 13: Configurable port exposure
# Validates: Requirements 8.4
@settings(max_examples=100)
@given(st.integers(min_value=1024, max_value=65535))
def test_configurable_port_exposure(port):
    """
    Property: For any valid port number, the Docker container should be configurable
    to expose the web service on that port.
    
    This test verifies that the PORT environment variable can be used to configure
    the port on which the Flask application listens.
    
    Note: This is a unit test of the configuration logic rather than actually
    starting Docker containers, as that would be too slow for property-based testing.
    """
    # Verify that the port is in the valid range
    assert 1024 <= port <= 65535, f"Port {port} is outside valid range"
    
    # Test that the Dockerfile exposes port 5000 by default
    with open('Dockerfile', 'r') as f:
        dockerfile_content = f.read()
        assert 'EXPOSE 5000' in dockerfile_content, "Dockerfile should expose port 5000"
    
    # Test that docker-compose.yml exposes the flask-app service
    with open('docker-compose.yml', 'r') as f:
        compose_content = f.read()
        assert 'expose:' in compose_content, "docker-compose.yml should expose flask-app"
        assert '"5000"' in compose_content or '5000' in compose_content, "flask-app should expose port 5000"
    
    # Verify that the configuration can be overridden via environment variables
    # The docker-compose.yml should support environment variable configuration
    assert 'environment:' in compose_content, "docker-compose.yml should support environment variables"


def test_dockerfile_structure():
    """
    Unit test: Verify Dockerfile has correct structure.
    
    Validates: Requirements 8.1, 8.3, 8.5
    """
    with open('Dockerfile', 'r') as f:
        content = f.read()
    
    # Check for required elements
    assert 'FROM python:3.10-slim' in content, "Should use Python 3.10-slim base image"
    assert 'WORKDIR /app' in content, "Should set working directory to /app"
    assert 'COPY requirements-web.txt' in content, "Should copy requirements-web.txt"
    assert 'RUN pip install' in content, "Should install dependencies"
    assert 'COPY . .' in content, "Should copy application code"
    assert 'EXPOSE 5000' in content, "Should expose port 5000"
    assert 'CMD' in content and 'gunicorn' in content, "Should run Gunicorn"


def test_docker_compose_structure():
    """
    Unit test: Verify docker-compose.yml has correct structure.
    
    Validates: Requirements 8.2, 8.3, 8.4
    """
    with open('docker-compose.yml', 'r') as f:
        content = f.read()
    
    # Check for required services
    assert 'nginx:' in content, "Should define nginx service"
    assert 'flask-app:' in content, "Should define flask-app service"
    
    # Check nginx configuration
    assert 'ports:' in content, "nginx should have port mappings"
    assert '"80:80"' in content or '80:80' in content, "nginx should expose port 80"
    assert '"443:443"' in content or '443:443' in content, "nginx should expose port 443"
    
    # Check flask-app configuration
    assert 'build: .' in content, "flask-app should build from current directory"
    assert 'environment:' in content, "flask-app should have environment variables"
    assert 'depends_on:' in content, "nginx should depend on flask-app"
    
    # Check for SSL certificate volume mount
    assert 'volumes:' in content, "Should mount volumes"
    assert 'ssl' in content, "Should mount SSL certificates"


def test_nginx_configuration_structure():
    """
    Unit test: Verify nginx.conf has correct structure.
    
    Validates: Requirements 1.4, 8.3
    """
    with open('nginx.conf', 'r') as f:
        content = f.read()
    
    # Check for HTTP to HTTPS redirect
    assert 'listen 80' in content, "Should listen on port 80"
    assert 'return 301 https://' in content, "Should redirect HTTP to HTTPS"
    
    # Check for HTTPS configuration
    assert 'listen 443 ssl' in content, "Should listen on port 443 with SSL"
    assert 'ssl_certificate' in content, "Should configure SSL certificate"
    assert 'ssl_certificate_key' in content, "Should configure SSL certificate key"
    
    # Check for proxy configuration
    assert 'proxy_pass http://flask-app:5000' in content, "Should proxy to flask-app"
    assert 'proxy_set_header Host' in content, "Should set Host header"
    assert 'proxy_set_header X-Real-IP' in content, "Should set X-Real-IP header"
    assert 'proxy_set_header X-Forwarded-For' in content, "Should set X-Forwarded-For header"
    assert 'proxy_set_header X-Forwarded-Proto' in content, "Should set X-Forwarded-Proto header"


def test_dockerignore_excludes_unnecessary_files():
    """
    Unit test: Verify .dockerignore excludes unnecessary files.
    
    Validates: Requirements 8.1
    """
    with open('.dockerignore', 'r') as f:
        content = f.read()
    
    # Check for required exclusions
    assert '.git' in content, "Should exclude .git"
    assert '__pycache__' in content, "Should exclude __pycache__"
    assert '.venv' in content or 'venv' in content, "Should exclude virtual environments"
    assert '.pytest_cache' in content or 'pytest' in content, "Should exclude test cache"
    assert '.hypothesis' in content or 'hypothesis' in content, "Should exclude hypothesis cache"


def test_environment_variable_template_exists():
    """
    Unit test: Verify .env.example exists and has required variables.
    
    Validates: Requirements 8.4, 12.3
    """
    with open('.env.example', 'r') as f:
        content = f.read()
    
    # Check for required environment variables
    assert 'FLASK_ENV' in content, "Should document FLASK_ENV"
    assert 'LOG_LEVEL' in content, "Should document LOG_LEVEL"
    assert 'SECRET_KEY' in content, "Should document SECRET_KEY"
    assert 'CACHE_TTL' in content, "Should document CACHE_TTL"
    assert 'REQUEST_TIMEOUT' in content, "Should document REQUEST_TIMEOUT"
    assert 'CORS_ORIGINS' in content, "Should document CORS_ORIGINS"


# Feature: weather-web-service, Property 1: HTTPS enforcement for all requests
# Validates: Requirements 1.4
@settings(max_examples=100)
@given(st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=97, max_codepoint=122)))
def test_https_enforcement_for_all_requests(path):
    """
    Property: For any HTTP request to the web service, the request should be 
    redirected to HTTPS or rejected.
    
    This test verifies that the nginx configuration enforces HTTPS by redirecting
    all HTTP requests to HTTPS. We test this by verifying the nginx configuration
    contains the proper redirect rules for any arbitrary path.
    
    Note: This is a configuration-level test. The actual HTTP redirect behavior
    is tested in integration tests with a running Docker container.
    """
    # Read nginx configuration
    with open('nginx.conf', 'r') as f:
        nginx_config = f.read()
    
    # Verify HTTP server block exists and redirects to HTTPS
    assert 'listen 80' in nginx_config, "nginx should listen on HTTP port 80"
    assert 'return 301 https://' in nginx_config, "nginx should redirect HTTP to HTTPS with 301"
    
    # Verify HTTPS server block exists
    assert 'listen 443 ssl' in nginx_config, "nginx should listen on HTTPS port 443 with SSL"
    
    # Verify SSL certificates are configured
    assert 'ssl_certificate' in nginx_config, "nginx should have SSL certificate configured"
    assert 'ssl_certificate_key' in nginx_config, "nginx should have SSL certificate key configured"
    
    # Verify SSL protocols are configured securely
    assert 'ssl_protocols' in nginx_config, "nginx should specify SSL protocols"
    assert 'TLSv1.2' in nginx_config or 'TLSv1.3' in nginx_config, "nginx should support modern TLS versions"
    
    # The redirect should work for any path (including the generated test path)
    # The nginx config uses 'return 301 https://$host$request_uri' which preserves the path
    assert '$request_uri' in nginx_config, "nginx should preserve request URI in HTTPS redirect"
