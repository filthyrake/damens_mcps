# TrueNAS MCP Server Deployment Guide

This guide covers deploying the TrueNAS MCP Server in various environments, from local development to production cloud deployments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Configuration](#configuration)
7. [Security Considerations](#security-considerations)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- Python 3.8+ (for local development)
- Docker (for containerized deployment)
- Kubernetes cluster (for K8s deployment)
- TrueNAS Scale server with API access

### TrueNAS Setup
1. Enable API access in TrueNAS Scale
2. Create an API key or use username/password authentication
3. Ensure network connectivity between MCP server and TrueNAS

## Local Development

### Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd truenas-mcp
   pip install -r requirements.txt
   ```

2. **Initialize configuration**:
   ```bash
   python -m src.http_cli init
   ```

3. **Update configuration**:
   Edit `.env` file with your TrueNAS details:
   ```env
   TRUENAS_HOST=your-truenas-host.example.com
   TRUENAS_API_KEY=your-api-key-here
   SECRET_KEY=your-generated-secret-key
   ```

4. **Start server**:
   ```bash
   python -m src.http_cli serve
   ```

5. **Test connection**:
   ```bash
   python -m src.http_cli health
   ```

### Development with Auto-reload

```bash
python -m src.http_cli serve --reload --debug
```

## Docker Deployment

### Using Docker Compose (Recommended)

1. **Create environment file**:
   ```bash
   cp examples/env.example .env
   # Edit .env with your configuration
   ```

2. **Start with Docker Compose**:
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

3. **Check logs**:
   ```bash
   docker-compose -f docker/docker-compose.yml logs -f
   ```

### Using Docker directly

1. **Build image**:
   ```bash
   docker build -f docker/Dockerfile -t truenas-mcp .
   ```

2. **Run container**:
   ```bash
   docker run -d \
     --name truenas-mcp \
     -p 8000:8000 \
     -e TRUENAS_HOST=your-truenas-host \
     -e TRUENAS_API_KEY=your-api-key \
     -e SECRET_KEY=your-secret-key \
     truenas-mcp
   ```

### Docker with persistent storage

```bash
docker run -d \
  --name truenas-mcp \
  -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/.env:/app/.env \
  truenas-mcp
```

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (1.19+)
- kubectl configured
- Helm (optional)

### Quick Deployment

1. **Create namespace**:
   ```bash
   kubectl create namespace truenas-mcp
   ```

2. **Create ConfigMap**:
   ```bash
   kubectl apply -f k8s/configmap.yaml
   ```

3. **Create Secrets**:
   ```bash
   kubectl create secret generic truenas-mcp-secrets \
     --from-literal=truenas_api_key=your-api-key \
     --from-literal=secret_key=your-secret-key \
     --from-literal=admin_token=your-admin-token \
     -n truenas-mcp
   ```

4. **Deploy application**:
   ```bash
   kubectl apply -f k8s/deployment.yaml
   kubectl apply -f k8s/service.yaml
   ```

5. **Check deployment**:
   ```bash
   kubectl get pods -n truenas-mcp
   kubectl get services -n truenas-mcp
   ```

### Using LoadBalancer

```bash
kubectl apply -f k8s/service.yaml
# Use the LoadBalancer service for external access
```

### Using Ingress (if available)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: truenas-mcp-ingress
  namespace: truenas-mcp
spec:
  rules:
  - host: truenas-mcp.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: truenas-mcp-service
            port:
              number: 80
```

## Cloud Deployment

### AWS EKS

1. **Create EKS cluster**:
   ```bash
   eksctl create cluster --name truenas-mcp --region us-west-2
   ```

2. **Deploy to EKS**:
   ```bash
   kubectl apply -f k8s/
   ```

3. **Create LoadBalancer**:
   ```bash
   kubectl apply -f k8s/service.yaml
   ```

### Google Cloud GKE

1. **Create GKE cluster**:
   ```bash
   gcloud container clusters create truenas-mcp \
     --zone us-central1-a \
     --num-nodes 3
   ```

2. **Deploy application**:
   ```bash
   kubectl apply -f k8s/
   ```

### Azure AKS

1. **Create AKS cluster**:
   ```bash
   az aks create \
     --resource-group myResourceGroup \
     --name truenas-mcp \
     --node-count 3
   ```

2. **Deploy application**:
   ```bash
   kubectl apply -f k8s/
   ```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TRUENAS_HOST` | TrueNAS server hostname | - | Yes |
| `TRUENAS_PORT` | TrueNAS server port | 443 | No |
| `TRUENAS_API_KEY` | API key for authentication | - | Yes* |
| `TRUENAS_USERNAME` | Username for authentication | - | Yes* |
| `TRUENAS_PASSWORD` | Password for authentication | - | Yes* |
| `TRUENAS_VERIFY_SSL` | Verify SSL certificates | true | No |
| `SERVER_HOST` | MCP server host | 0.0.0.0 | No |
| `SERVER_PORT` | MCP server port | 8000 | No |
| `SECRET_KEY` | JWT secret key | - | Yes |
| `ADMIN_TOKEN` | Admin token for setup | - | No |
| `DEBUG` | Enable debug mode | false | No |
| `LOG_LEVEL` | Logging level | INFO | No |

*Either API key or username/password is required.

### Configuration Files

#### .env file
```env
# TrueNAS Configuration
TRUENAS_HOST=your-truenas-host.example.com
TRUENAS_PORT=443
TRUENAS_API_KEY=your-api-key-here
TRUENAS_VERIFY_SSL=true

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=false

# Authentication Configuration
SECRET_KEY=your-secret-key-here-minimum-32-characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ADMIN_TOKEN=your-admin-token-here

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/truenas-mcp.log
```

#### Docker Compose
```yaml
version: '3.8'
services:
  truenas-mcp:
    image: truenas-mcp:latest
    ports:
      - "8000:8000"
    environment:
      - TRUENAS_HOST=${TRUENAS_HOST}
      - TRUENAS_API_KEY=${TRUENAS_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./logs:/app/logs
```

## Security Considerations

### Network Security
- Use HTTPS in production
- Configure firewall rules
- Use VPN for internal deployments
- Implement rate limiting

### Authentication
- Use strong secret keys (32+ characters)
- Rotate API keys regularly
- Use admin tokens for initial setup only
- Implement proper JWT token management

### Access Control
- Limit CORS origins in production
- Use trusted host middleware
- Implement proper user management
- Audit all access logs

### Secrets Management
- Use Kubernetes secrets or external secret managers
- Never commit secrets to version control
- Use environment-specific configurations
- Implement secret rotation

## Monitoring and Logging

### Health Checks
```bash
# Check server health
curl http://localhost:8000/health

# Using CLI
python -m src.http_cli health
```

### Logging
- Logs are written to `/app/logs/truenas-mcp.log` in containers
- Use structured logging for better analysis
- Implement log rotation
- Monitor log levels in production

### Metrics
- Health check endpoint provides basic metrics
- Consider adding Prometheus metrics
- Monitor resource usage
- Set up alerts for failures

### Monitoring Stack
```yaml
# Example Prometheus configuration
scrape_configs:
  - job_name: 'truenas-mcp'
    static_configs:
      - targets: ['truenas-mcp:8000']
    metrics_path: '/health'
```

## Troubleshooting

### Common Issues

#### Connection to TrueNAS fails
```bash
# Check network connectivity
curl -k https://your-truenas-host/api/v2.0/system/info

# Verify API key
curl -H "Authorization: Bearer your-api-key" \
  https://your-truenas-host/api/v2.0/system/info
```

#### Authentication issues
```bash
# Check JWT token
python -m src.http_cli login

# Verify token
python -m src.http_cli list-tools
```

#### Container won't start
```bash
# Check logs
docker logs truenas-mcp

# Check environment variables
docker exec truenas-mcp env | grep TRUENAS
```

#### Kubernetes pod issues
```bash
# Check pod status
kubectl get pods -n truenas-mcp

# Check logs
kubectl logs -f deployment/truenas-mcp -n truenas-mcp

# Check events
kubectl get events -n truenas-mcp
```

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# Start server with debug
python -m src.http_cli serve --debug
```

### Performance Issues
- Monitor resource usage
- Check TrueNAS API response times
- Implement connection pooling
- Use caching where appropriate

## Integration with Cursor

### Configuration
Add to your Cursor MCP configuration:

```json
{
  "mcpServers": {
    "truenas": {
      "url": "http://your-mcp-server:8000/mcp/",
      "headers": {
        "Authorization": "Bearer your-jwt-token"
      }
    }
  }
}
```

### Getting JWT Token
```bash
# Login to get token
python -m src.http_cli login

# Or create token with admin token
python -m src.http_cli create-token --admin-token your-admin-token
```

### Testing Integration
```bash
# List available tools
python -m src.http_cli list-tools

# Test a tool call
python -m src.http_cli call-tool truenas_system_get_info
```

## Support

For issues and questions:
- Check the troubleshooting section
- Review logs for error messages
- Test with curl commands
- Verify TrueNAS API access
- Check network connectivity

## Next Steps

After deployment:
1. Test all MCP tools
2. Configure monitoring
3. Set up backups
4. Document your specific setup
5. Train users on the new capabilities
