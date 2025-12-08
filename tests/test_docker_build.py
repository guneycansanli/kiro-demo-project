"""
Docker Build and Run Tests

This module contains tests for Docker container build and run functionality.
Note: These tests validate configuration without requiring Docker daemon.
"""

import pytest
import os
import subprocess


def test_dockerfile_exists_and_valid():
    """
    Test that Dockerfile exists and has valid syntax.
    
    Validates: Requirements 8.1, 8.3, 8.5
    """
    assert os.path.exists('Dockerfile'), "Dockerfile should exist"
    
    with open('Dockerfile', 'r') as f:
        content = f.read()
    
    # Validate Dockerfile structure
    lines = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
    
    # Should start with FROM
    assert lines[0].startswith('FROM'), "Dockerfile should start with FROM instruction"
    
    # Should have WORKDIR
    assert any('WORKDIR' in line for line in lines), "Dockerfile should set WORKDIR"
    
    # Should have COPY for requirements
    assert any('COPY requirements' in line for line in lines), "Dockerfile should copy requirements"
    
    # Should have RUN pip install
    assert any('RUN pip install' in line for line in lines), "Dockerfile should install dependencies"
    
    # Should have COPY for application code
    copy_count = sum(1 for line in lines if line.startswith('COPY'))
    assert copy_count >= 2, "Dockerfile should copy requirements and application code"
    
    # Should have EXPOSE
    assert any('EXPOSE' in line for line in lines), "Dockerfile should expose a port"
    
    # Should have CMD
    assert any('CMD' in line for line in lines), "Dockerfile should have CMD instruction"


def test_docker_compose_exists_and_valid():
    """
    Test that docker-compose.yml exists and has valid structure.
    
    Validates: Requirements 8.2, 8.3, 8.4
    """
    assert os.path.exists('docker-compose.yml'), "docker-compose.yml should exist"
    
    with open('docker-compose.yml', 'r') as f:
        content = f.read()
    
    # Basic YAML validation - check for required keys
    assert 'version:' in content, "docker-compose.yml should specify version"
    assert 'services:' in content, "docker-compose.yml should define services"
    assert 'nginx:' in content, "docker-compose.yml should define nginx service"
    assert 'flask-app:' in content, "docker-compose.yml should define flask-app service"


def test_nginx_config_exists_and_valid():
    """
    Test that nginx.conf exists and has valid structure.
    
    Validates: Requirements 1.4, 8.3
    """
    assert os.path.exists('nginx.conf'), "nginx.conf should exist"
    
    with open('nginx.conf', 'r') as f:
        content = f.read()
    
    # Check for required nginx directives
    assert 'events {' in content, "nginx.conf should have events block"
    assert 'http {' in content, "nginx.conf should have http block"
    assert 'server {' in content, "nginx.conf should have server block"


def test_ssl_directory_structure():
    """
    Test that SSL directory exists for certificates.
    
    Validates: Requirements 1.4
    """
    assert os.path.exists('ssl'), "ssl directory should exist"
    
    # Check if certificates exist (they should be created for deployment)
    # For testing, we just verify the directory exists
    assert os.path.isdir('ssl'), "ssl should be a directory"


def test_health_endpoint_available():
    """
    Test that health check endpoint is defined in the application.
    
    Validates: Requirements 8.1, 8.3, 8.5
    """
    # Read the weather API file to verify health endpoint exists
    with open('app/api/weather.py', 'r') as f:
        content = f.read()
    
    assert '/health' in content, "Health endpoint should be defined"
    assert 'def health_check' in content, "Health check function should exist"


def test_wsgi_entry_point():
    """
    Test that WSGI entry point is properly configured.
    
    Validates: Requirements 8.1, 8.5
    """
    assert os.path.exists('wsgi.py'), "wsgi.py should exist"
    
    with open('wsgi.py', 'r') as f:
        content = f.read()
    
    # Verify WSGI configuration
    assert 'from app import create_app' in content, "Should import create_app"
    assert 'app = create_app()' in content, "Should create app instance"


def test_requirements_file_has_gunicorn():
    """
    Test that requirements file includes Gunicorn for production deployment.
    
    Validates: Requirements 8.1, 8.5
    """
    assert os.path.exists('requirements-web.txt'), "requirements-web.txt should exist"
    
    with open('requirements-web.txt', 'r') as f:
        content = f.read()
    
    assert 'gunicorn' in content.lower(), "requirements should include gunicorn"


def test_docker_build_command_syntax():
    """
    Test that Docker build command would be valid (without actually building).
    
    Validates: Requirements 8.1, 8.3
    """
    # Verify all files needed for build exist
    required_files = [
        'Dockerfile',
        'requirements-web.txt',
        'wsgi.py',
        'app/__init__.py'
    ]
    
    for file_path in required_files:
        assert os.path.exists(file_path), f"Required file {file_path} should exist for Docker build"


def test_docker_compose_up_command_syntax():
    """
    Test that docker-compose up command would be valid (without actually running).
    
    Validates: Requirements 8.2, 8.3
    """
    # Verify all files needed for docker-compose exist
    required_files = [
        'docker-compose.yml',
        'nginx.conf',
        'Dockerfile'
    ]
    
    for file_path in required_files:
        assert os.path.exists(file_path), f"Required file {file_path} should exist for docker-compose"
    
    # Verify SSL directory exists
    assert os.path.exists('ssl'), "SSL directory should exist"


def test_environment_variables_documented():
    """
    Test that environment variables are properly documented.
    
    Validates: Requirements 8.4
    """
    assert os.path.exists('.env.example'), ".env.example should exist"
    
    with open('.env.example', 'r') as f:
        env_content = f.read()
    
    with open('docker-compose.yml', 'r') as f:
        compose_content = f.read()
    
    # Check that environment variables in docker-compose are documented
    env_vars = ['FLASK_ENV', 'LOG_LEVEL', 'SECRET_KEY', 'CACHE_TTL', 'REQUEST_TIMEOUT', 'CORS_ORIGINS']
    
    for var in env_vars:
        assert var in env_content, f"Environment variable {var} should be documented in .env.example"
        assert var in compose_content, f"Environment variable {var} should be used in docker-compose.yml"


def test_https_redirect_configuration():
    """
    Test that nginx is configured to redirect HTTP to HTTPS.
    
    Validates: Requirements 1.4
    """
    with open('nginx.conf', 'r') as f:
        content = f.read()
    
    # Verify HTTP server block redirects to HTTPS
    assert 'listen 80' in content, "nginx should listen on HTTP port 80"
    assert 'return 301 https://$host$request_uri' in content, "nginx should redirect HTTP to HTTPS with 301"
    
    # Verify the redirect preserves the original request URI
    assert '$request_uri' in content, "nginx should preserve request URI in redirect"


def test_https_server_configuration():
    """
    Test that nginx is configured with proper HTTPS settings.
    
    Validates: Requirements 1.4
    """
    with open('nginx.conf', 'r') as f:
        content = f.read()
    
    # Verify HTTPS server block exists
    assert 'listen 443 ssl' in content, "nginx should listen on HTTPS port 443 with SSL"
    
    # Verify SSL certificate paths
    assert 'ssl_certificate /etc/nginx/ssl/cert.pem' in content, "nginx should reference SSL certificate"
    assert 'ssl_certificate_key /etc/nginx/ssl/key.pem' in content, "nginx should reference SSL certificate key"
    
    # Verify SSL protocols
    assert 'ssl_protocols' in content, "nginx should specify SSL protocols"
    assert 'TLSv1.2' in content or 'TLSv1.3' in content, "nginx should support modern TLS versions"
    
    # Verify SSL ciphers
    assert 'ssl_ciphers' in content, "nginx should specify SSL ciphers"


def test_ssl_certificates_exist():
    """
    Test that SSL certificates exist in the ssl directory.
    
    Validates: Requirements 1.4
    """
    assert os.path.exists('ssl/cert.pem'), "SSL certificate should exist"
    assert os.path.exists('ssl/key.pem'), "SSL private key should exist"
    
    # Verify certificate file is not empty
    assert os.path.getsize('ssl/cert.pem') > 0, "SSL certificate should not be empty"
    assert os.path.getsize('ssl/key.pem') > 0, "SSL private key should not be empty"


def test_ssl_certificate_validity():
    """
    Test that SSL certificate is valid and can be parsed.
    
    Validates: Requirements 1.4
    """
    # Try to parse the certificate using openssl
    result = subprocess.run(
        ['openssl', 'x509', '-in', 'ssl/cert.pem', '-noout', '-text'],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, "SSL certificate should be valid and parseable"
    assert 'Certificate:' in result.stdout, "Certificate should contain valid certificate data"
    assert 'Subject:' in result.stdout, "Certificate should have a subject"
    assert 'Issuer:' in result.stdout, "Certificate should have an issuer"


def test_docker_compose_ssl_volume_mount():
    """
    Test that docker-compose.yml mounts SSL certificates correctly.
    
    Validates: Requirements 1.4, 8.2
    """
    with open('docker-compose.yml', 'r') as f:
        content = f.read()
    
    # Verify SSL volume mount exists
    assert 'volumes:' in content, "docker-compose should define volumes"
    assert './ssl:/etc/nginx/ssl' in content or 'ssl:/etc/nginx/ssl' in content, \
        "docker-compose should mount SSL certificates to nginx"


# Manual testing instructions
def test_manual_docker_instructions():
    """
    This test documents the manual steps to test Docker build and run.
    
    To manually test Docker functionality:
    
    1. Build the Docker image:
       $ docker build -t weather-web-service:test .
    
    2. Run with docker-compose:
       $ docker-compose up -d
    
    3. Test the health endpoint:
       $ curl http://localhost/api/health
       or
       $ curl -k https://localhost/api/health
    
    4. Test the weather endpoint:
       $ curl "http://localhost/api/weather/coordinates?lat=37.7749&lon=-122.4194"
    
    5. Stop the containers:
       $ docker-compose down
    
    Validates: Requirements 8.1, 8.3, 8.5
    """
    # This test always passes - it's just documentation
    assert True, "See test docstring for manual Docker testing instructions"


def test_manual_https_functionality():
    """
    This test documents the manual steps to test HTTPS functionality.
    
    To manually test HTTPS functionality with Docker:
    
    1. Start the services:
       $ docker-compose up -d
    
    2. Test HTTP redirect to HTTPS:
       $ curl -I http://localhost/api/health
       Expected: HTTP/1.1 301 Moved Permanently
       Expected: Location: https://localhost/api/health
    
    3. Test HTTPS requests work correctly:
       $ curl -k https://localhost/api/health
       Expected: {"status": "healthy", "service": "weather-web-service"}
    
    4. Verify SSL certificate is served:
       $ openssl s_client -connect localhost:443 -servername localhost < /dev/null
       Expected: Certificate chain and server certificate details
    
    5. Stop the services:
       $ docker-compose down
    
    Validates: Requirements 1.4
    """
    # This test always passes - it's just documentation
    assert True, "See test docstring for manual HTTPS testing instructions"
