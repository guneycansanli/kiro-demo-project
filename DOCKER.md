# Docker Deployment Guide

This comprehensive guide explains how to build, deploy, and manage the Weather Web Service using Docker in both development and production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start (Development)](#quick-start-development)
- [Production Deployment](#production-deployment)
- [Configuration](#configuration)
- [Monitoring and Logging](#monitoring-and-logging)
- [Scaling](#scaling)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)

## Prerequisites

- Docker Engine 20.10 or later
- Docker Compose 2.0 or later
- 2GB RAM minimum (4GB recommended for production)
- 10GB disk space

## Quick Start

### 1. Generate SSL Certificates

For development/testing, generate self-signed certificates:

```bash
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -nodes \
  -out ssl/cert.pem \
  -keyout ssl/key.pem \
  -days 365 \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

For production, use certificates from a trusted Certificate Authority (CA) like Let's Encrypt.

### 2. Configure Environment Variables

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

Edit `.env` and set appropriate values:

```bash
FLASK_ENV=production
LOG_LEVEL=INFO
SECRET_KEY=your-secure-random-secret-key-here
CACHE_TTL=300
REQUEST_TIMEOUT=10
CORS_ORIGINS=*
```

**Important:** Generate a secure random secret key for production:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Build and Run with Docker Compose

Build and start all services:

```bash
docker-compose up -d
```

This will:
- Build the Flask application container
- Start the Nginx reverse proxy
- Configure HTTPS with your SSL certificates
- Expose the service on ports 80 (HTTP) and 443 (HTTPS)

### 4. Verify Deployment

Check that containers are running:

```bash
docker-compose ps
```

Test the health endpoint:

```bash
# HTTP (will redirect to HTTPS)
curl http://localhost/api/health

# HTTPS (use -k for self-signed certificates)
curl -k https://localhost/api/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "weather-web-service"
}
```

Test the weather endpoint:

```bash
curl -k "https://localhost/api/weather/coordinates?lat=37.7749&lon=-122.4194"
```

### 5. View Logs

View logs from all services:

```bash
docker-compose logs -f
```

View logs from a specific service:

```bash
docker-compose logs -f flask-app
docker-compose logs -f nginx
```

### 6. Stop Services

Stop all services:

```bash
docker-compose down
```

Stop and remove volumes:

```bash
docker-compose down -v
```

## Manual Docker Build

If you prefer to build the Docker image manually:

```bash
# Build the image
docker build -t weather-web-service:latest .

# Run the container
docker run -d \
  -p 5000:5000 \
  -e FLASK_ENV=production \
  -e LOG_LEVEL=INFO \
  -e SECRET_KEY=your-secret-key \
  --name weather-app \
  weather-web-service:latest

# Test the application
curl http://localhost:5000/api/health
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment (development/production) | `production` |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL) | `INFO` |
| `SECRET_KEY` | Secret key for Flask sessions | `dev-secret-key` |
| `CACHE_TTL` | Cache time-to-live in seconds | `300` |
| `REQUEST_TIMEOUT` | HTTP request timeout in seconds | `10` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated or *) | `*` |

### Port Configuration

By default, the application exposes:
- Port 80 (HTTP) - Redirects to HTTPS
- Port 443 (HTTPS) - Main application endpoint

To change the exposed ports, edit `docker-compose.yml`:

```yaml
services:
  nginx:
    ports:
      - "8080:80"    # Change HTTP port
      - "8443:443"   # Change HTTPS port
```

### SSL/TLS Configuration

The Nginx configuration expects SSL certificates at:
- Certificate: `/etc/nginx/ssl/cert.pem`
- Private Key: `/etc/nginx/ssl/key.pem`

These are mounted from the `./ssl` directory on the host.

For production, replace the self-signed certificates with certificates from a trusted CA.

## Troubleshooting

### Container won't start

Check logs:

```bash
docker-compose logs flask-app
```

Common issues:
- Missing SSL certificates in `./ssl` directory
- Port conflicts (80 or 443 already in use)
- Invalid environment variables

### Cannot connect to external APIs

The application needs internet access to:
- weather.gov (weather data)
- nominatim.openstreetmap.org (geocoding)

Ensure your Docker network allows outbound connections.

### HTTPS certificate errors

For development with self-signed certificates, use `-k` flag with curl:

```bash
curl -k https://localhost/api/health
```

For browsers, you'll need to accept the security warning.

For production, use certificates from a trusted CA.

## Production Deployment

For production deployment:

1. **Use trusted SSL certificates** from Let's Encrypt or another CA
2. **Set a secure SECRET_KEY** (use a cryptographically random value)
3. **Configure CORS_ORIGINS** to restrict allowed origins
4. **Set LOG_LEVEL** to INFO or WARNING
5. **Use a reverse proxy** or load balancer in front of Nginx
6. **Enable monitoring** and log aggregation
7. **Set up automated backups** if using persistent storage
8. **Configure resource limits** in docker-compose.yml:

```yaml
services:
  flask-app:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

## Health Checks

The application provides a health check endpoint at `/api/health`.

Add health checks to docker-compose.yml:

```yaml
services:
  flask-app:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## Scaling

To run multiple Flask application instances:

```bash
docker-compose up -d --scale flask-app=3
```

Nginx will automatically load balance between instances.

## Support

For issues or questions:
- Check the logs: `docker-compose logs -f`
- Review the configuration files
- Ensure all prerequisites are met
- Verify network connectivity to external APIs


---

## Production Deployment (Detailed)

### Cloud Platform Deployment

#### AWS ECS/Fargate

1. **Build and push Docker image to ECR**:

```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and tag image
docker build -t weather-web-service:latest .
docker tag weather-web-service:latest \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/weather-web-service:latest

# Push to ECR
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/weather-web-service:latest
```

2. **Create ECS Task Definition**:

```json
{
  "family": "weather-web-service",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "flask-app",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/weather-web-service:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "FLASK_ENV", "value": "production"},
        {"name": "LOG_LEVEL", "value": "INFO"}
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:weather-secret-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/weather-web-service",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

3. **Create ECS Service with Application Load Balancer**:

```bash
aws ecs create-service \
  --cluster weather-cluster \
  --service-name weather-service \
  --task-definition weather-web-service \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=flask-app,containerPort=5000"
```

#### Google Cloud Run

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/weather-web-service

# Deploy to Cloud Run
gcloud run deploy weather-web-service \
  --image gcr.io/PROJECT_ID/weather-web-service \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars FLASK_ENV=production,LOG_LEVEL=INFO \
  --set-secrets SECRET_KEY=weather-secret-key:latest
```

#### Azure Container Instances

```bash
# Create resource group
az group create --name weather-rg --location eastus

# Create container registry
az acr create --resource-group weather-rg --name weatherregistry --sku Basic

# Build and push image
az acr build --registry weatherregistry --image weather-web-service:latest .

# Deploy container
az container create \
  --resource-group weather-rg \
  --name weather-web-service \
  --image weatherregistry.azurecr.io/weather-web-service:latest \
  --dns-name-label weather-service \
  --ports 443 \
  --environment-variables FLASK_ENV=production LOG_LEVEL=INFO \
  --secure-environment-variables SECRET_KEY=<your-secret-key>
```

### Kubernetes Deployment

1. **Create Kubernetes manifests**:

**deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: weather-web-service
  labels:
    app: weather-web-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: weather-web-service
  template:
    metadata:
      labels:
        app: weather-web-service
    spec:
      containers:
      - name: flask-app
        image: weather-web-service:latest
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: "production"
        - name: LOG_LEVEL
          value: "INFO"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: weather-secrets
              key: secret-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
```

**service.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: weather-web-service
spec:
  type: LoadBalancer
  ports:
  - port: 443
    targetPort: 5000
    protocol: TCP
  selector:
    app: weather-web-service
```

**ingress.yaml**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: weather-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - weather.yourdomain.com
    secretName: weather-tls
  rules:
  - host: weather.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: weather-web-service
            port:
              number: 443
```

2. **Deploy to Kubernetes**:

```bash
# Create namespace
kubectl create namespace weather

# Create secrets
kubectl create secret generic weather-secrets \
  --from-literal=secret-key=<your-secret-key> \
  -n weather

# Apply manifests
kubectl apply -f deployment.yaml -n weather
kubectl apply -f service.yaml -n weather
kubectl apply -f ingress.yaml -n weather

# Check deployment status
kubectl get pods -n weather
kubectl get services -n weather
kubectl get ingress -n weather
```

### SSL Certificate Setup for Production

#### Let's Encrypt with Certbot

1. **Install Certbot**:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install certbot

# CentOS/RHEL
sudo yum install certbot

# macOS
brew install certbot
```

2. **Generate certificates**:

```bash
# Standalone mode (requires port 80 to be available)
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Webroot mode (if you have a running web server)
sudo certbot certonly --webroot -w /var/www/html -d yourdomain.com
```

3. **Copy certificates to project**:

```bash
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem
sudo chmod 644 ssl/cert.pem
sudo chmod 600 ssl/key.pem
```

4. **Set up automatic renewal**:

```bash
# Test renewal
sudo certbot renew --dry-run

# Add cron job for automatic renewal
sudo crontab -e

# Add this line to renew certificates twice daily
0 0,12 * * * certbot renew --quiet --post-hook "docker-compose restart nginx"
```

#### Let's Encrypt with Docker

Use the `certbot/certbot` Docker image:

```yaml
# Add to docker-compose.yml
services:
  certbot:
    image: certbot/certbot
    volumes:
      - ./ssl:/etc/letsencrypt
      - ./certbot-webroot:/var/www/certbot
    command: certonly --webroot --webroot-path=/var/www/certbot --email your@email.com --agree-tos --no-eff-email -d yourdomain.com
```

Run certificate generation:

```bash
docker-compose run --rm certbot
```

#### Commercial SSL Certificates

1. **Generate CSR (Certificate Signing Request)**:

```bash
openssl req -new -newkey rsa:2048 -nodes \
  -keyout ssl/key.pem \
  -out ssl/csr.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=yourdomain.com"
```

2. **Submit CSR to Certificate Authority** (e.g., DigiCert, Comodo, GoDaddy)

3. **Download and install certificate**:

```bash
# Copy the certificate files
cp downloaded-certificate.crt ssl/cert.pem
cp downloaded-key.key ssl/key.pem

# If you have intermediate certificates, concatenate them
cat certificate.crt intermediate.crt > ssl/cert.pem
```

### Environment Configuration for Production

Create a production `.env` file:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=<generate-with-python-secrets-token-hex-32>

# Cache Configuration
CACHE_TTL=300

# Request Configuration
REQUEST_TIMEOUT=10

# Logging Configuration
LOG_LEVEL=INFO

# CORS Configuration (restrict to your domain)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Optional: External service configuration
NOMINATIM_USER_AGENT=YourApp/1.0 (your@email.com)
```

**Generate secure SECRET_KEY**:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Monitoring and Logging

#### Application Logs

View logs in real-time:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f flask-app

# Last 100 lines
docker-compose logs --tail=100 flask-app

# Since specific time
docker-compose logs --since 2024-12-07T10:00:00 flask-app
```

#### Log Aggregation

**Using ELK Stack (Elasticsearch, Logstash, Kibana)**:

Add to `docker-compose.yml`:

```yaml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

  flask-app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=flask-app"

volumes:
  elasticsearch-data:
```

**Using CloudWatch (AWS)**:

Install CloudWatch agent in container:

```dockerfile
# Add to Dockerfile
RUN pip install watchtower

# In your Flask app
import watchtower
import logging

logger = logging.getLogger(__name__)
logger.addHandler(watchtower.CloudWatchLogHandler(
    log_group='/aws/ecs/weather-web-service',
    stream_name='flask-app'
))
```

#### Monitoring with Prometheus and Grafana

Add metrics endpoint to Flask app:

```python
# Install prometheus_flask_exporter
pip install prometheus-flask-exporter

# In app/__init__.py
from prometheus_flask_exporter import PrometheusMetrics

def create_app():
    app = Flask(__name__)
    metrics = PrometheusMetrics(app)
    # ... rest of app setup
```

Add to `docker-compose.yml`:

```yaml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus

volumes:
  prometheus-data:
  grafana-data:
```

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'weather-web-service'
    static_configs:
      - targets: ['flask-app:5000']
```

#### Health Monitoring

Set up health check monitoring:

```bash
# Simple health check script
#!/bin/bash
# health-check.sh

ENDPOINT="https://yourdomain.com/api/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $ENDPOINT)

if [ $RESPONSE -eq 200 ]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy (HTTP $RESPONSE)"
    # Send alert (email, Slack, PagerDuty, etc.)
    exit 1
fi
```

Add to crontab:

```bash
*/5 * * * * /path/to/health-check.sh
```

### Performance Optimization

#### Enable Nginx Caching

Add to `nginx.conf`:

```nginx
http {
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=weather_cache:10m max_size=100m inactive=60m;

    server {
        location /api/ {
            proxy_cache weather_cache;
            proxy_cache_valid 200 5m;
            proxy_cache_key "$scheme$request_method$host$request_uri";
            add_header X-Cache-Status $upstream_cache_status;
            
            proxy_pass http://flask-app:5000;
        }
    }
}
```

#### Use Redis for Distributed Caching

Add Redis to `docker-compose.yml`:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes

  flask-app:
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0

volumes:
  redis-data:
```

Update Flask app to use Redis:

```python
# Install redis
pip install redis

# In app/services/cache_service.py
import redis
import os

redis_client = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))

class CacheService:
    def get(self, key):
        return redis_client.get(key)
    
    def set(self, key, value, ttl=300):
        redis_client.setex(key, ttl, value)
```

### Backup and Disaster Recovery

#### Backup Strategy

1. **Configuration Backup**:

```bash
#!/bin/bash
# backup-config.sh

BACKUP_DIR="/backups/weather-service"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup configuration files
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
    docker-compose.yml \
    nginx.conf \
    .env \
    ssl/

# Keep only last 30 days of backups
find $BACKUP_DIR -name "config_*.tar.gz" -mtime +30 -delete
```

2. **Automated Backups**:

```bash
# Add to crontab
0 2 * * * /path/to/backup-config.sh
```

#### Disaster Recovery Plan

1. **Document recovery procedures**
2. **Test recovery regularly**
3. **Store backups off-site** (S3, Google Cloud Storage, etc.)
4. **Maintain infrastructure as code** (Terraform, CloudFormation)
5. **Keep runbooks updated**

### Security Best Practices

1. **Use secrets management**:
   - AWS Secrets Manager
   - HashiCorp Vault
   - Kubernetes Secrets

2. **Enable security scanning**:

```bash
# Scan Docker image for vulnerabilities
docker scan weather-web-service:latest

# Use Trivy
trivy image weather-web-service:latest
```

3. **Implement rate limiting** (add to nginx.conf):

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://flask-app:5000;
    }
}
```

4. **Enable security headers** (add to nginx.conf):

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

5. **Regular security updates**:

```bash
# Update base images regularly
docker-compose pull
docker-compose up -d

# Update Python dependencies
pip install --upgrade -r requirements-web.txt
```

### Rollback Procedures

1. **Tag Docker images with versions**:

```bash
docker build -t weather-web-service:v1.0.0 .
docker tag weather-web-service:v1.0.0 weather-web-service:latest
```

2. **Keep previous versions**:

```bash
# Rollback to previous version
docker-compose down
docker tag weather-web-service:v1.0.0 weather-web-service:latest
docker-compose up -d
```

3. **Use blue-green deployment**:

```yaml
# docker-compose-blue.yml
services:
  flask-app-blue:
    image: weather-web-service:v1.0.0
    # ... configuration

# docker-compose-green.yml
services:
  flask-app-green:
    image: weather-web-service:v1.1.0
    # ... configuration
```

Switch traffic between blue and green deployments in Nginx configuration.

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Flask Deployment Options](https://flask.palletsprojects.com/en/latest/deploying/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)

---

**Last Updated**: December 7, 2024  
**Version**: 1.0.0
