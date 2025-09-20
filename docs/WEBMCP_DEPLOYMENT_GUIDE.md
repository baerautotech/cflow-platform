# WebMCP Server Deployment Guide

## Overview

This guide covers the complete deployment of the WebMCP (Web Model Context Protocol) server using FastAPI + Uvicorn, nginx reverse proxy, and cert-manager for TLS certificates on the cerebral cluster.

## Architecture

```
Internet → nginx (TLS termination) → WebMCP Server (FastAPI) → Tool Registry → Handlers
```

### Components

1. **WebMCP Server**: FastAPI application with 92+ tools
2. **nginx**: Reverse proxy with SSL termination and security headers
3. **cert-manager**: Automatic TLS certificate management
4. **Kubernetes**: Container orchestration with HPA and network policies

## Prerequisites

### Cluster Requirements
- Kubernetes cluster with nginx-ingress-controller
- cert-manager installed
- Docker registry access
- kubectl configured

### Local Requirements
- Docker
- kubectl
- Git (for version tagging)

## Quick Deployment

```bash
# Deploy everything with one command
./scripts/deploy-webmcp.sh
```

## Manual Deployment Steps

### 1. Build and Push Image

```bash
# Build the Docker image
docker build -f infrastructure/docker/Dockerfile.webmcp -t webmcp:latest .

# Tag with registry and version
VERSION=$(git rev-parse --short HEAD)
docker tag webmcp:latest registry.baerautotech.com/webmcp:${VERSION}

# Push to registry
docker push registry.baerautotech.com/webmcp:${VERSION}
```

### 2. Configure Secrets

```bash
# Create secrets (replace with actual values)
kubectl create secret generic webmcp-secrets \
  --from-literal=supabase-url="your-supabase-url" \
  --from-literal=supabase-key="your-supabase-key" \
  --from-literal=vault-url="your-vault-url" \
  --from-literal=vault-token="your-vault-token" \
  -n cerebral
```

### 3. Deploy Kubernetes Resources

```bash
# Apply cert-manager configuration
kubectl apply -f infrastructure/kubernetes/cert-manager-config.yaml

# Apply WebMCP deployment
kubectl apply -f infrastructure/kubernetes/webmcp-deployment.yaml
```

### 4. Verify Deployment

```bash
# Check deployment status
kubectl rollout status deployment/webmcp-deployment -n cerebral

# Check pods
kubectl get pods -n cerebral -l app=webmcp

# Check services
kubectl get svc -n cerebral -l app=webmcp

# Check ingress
kubectl get ingress -n cerebral -l app=webmcp

# Check certificates
kubectl get certificate -n cerebral -l app=webmcp
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBMCP_HOST` | `0.0.0.0` | Server bind address |
| `WEBMCP_PORT` | `8000` | Server port |
| `WEBMCP_WORKERS` | `1` | Uvicorn workers |
| `WEBMCP_LOG_LEVEL` | `info` | Logging level |

### Security Configuration

- **TLS**: Automatic certificate management via cert-manager
- **Rate Limiting**: 10 requests/second per IP
- **Security Headers**: HSTS, CSP, XSS protection
- **Network Policies**: Restricted ingress/egress
- **Non-root User**: Container runs as user 1000

## API Endpoints

### Health & Status
- `GET /` - Basic health check
- `GET /health` - Detailed health information
- `GET /stats` - Server statistics (restricted)

### MCP Protocol
- `GET /mcp/tools` - List all available tools
- `POST /mcp/tools/call` - Execute a tool
- `POST /mcp/initialize` - MCP initialization
- `GET /mcp/tools/{name}` - Get tool information

### Documentation
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc documentation

## Monitoring & Observability

### Health Checks
- **Liveness Probe**: `/health` endpoint
- **Readiness Probe**: `/health` endpoint
- **Startup Probe**: Built into FastAPI

### Metrics
- **HPA**: CPU (70%) and Memory (80%) based scaling
- **Logging**: Structured JSON logs
- **Tracing**: Request/response correlation

### Alerts
- Pod restart frequency
- High error rates
- Certificate expiration
- Resource utilization

## Security Features

### TLS/SSL
- **Certificate Management**: Automatic renewal via cert-manager
- **Protocols**: TLS 1.2 and 1.3 only
- **Ciphers**: Strong cipher suites only

### Network Security
- **Network Policies**: Restricted pod-to-pod communication
- **Ingress Control**: nginx-based rate limiting
- **Egress Control**: DNS and HTTPS only

### Application Security
- **Input Validation**: All inputs validated via Pydantic
- **Error Handling**: Sanitized error responses
- **Authentication**: JWT-based (when implemented)

## Troubleshooting

### Common Issues

#### 1. Certificate Issues
```bash
# Check certificate status
kubectl describe certificate webmcp-cert -n cerebral

# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager
```

#### 2. Pod Startup Issues
```bash
# Check pod logs
kubectl logs -n cerebral deployment/webmcp-deployment

# Check pod events
kubectl describe pod -n cerebral -l app=webmcp
```

#### 3. Service Connectivity
```bash
# Test service from within cluster
kubectl run test-pod --image=curlimages/curl --rm -i --restart=Never -- curl -f http://webmcp-service:8000/health
```

### Debug Commands

```bash
# Get all resources
kubectl get all -n cerebral -l app=webmcp

# Check ingress controller
kubectl get pods -n ingress-nginx

# Check cert-manager
kubectl get pods -n cert-manager

# View logs
kubectl logs -n cerebral deployment/webmcp-deployment -f
```

## Scaling

### Horizontal Pod Autoscaler
- **Min Replicas**: 3
- **Max Replicas**: 10
- **CPU Target**: 70%
- **Memory Target**: 80%

### Manual Scaling
```bash
# Scale deployment
kubectl scale deployment webmcp-deployment --replicas=5 -n cerebral
```

## Backup & Recovery

### Configuration Backup
```bash
# Backup all WebMCP resources
kubectl get all,ingress,certificate,secret -n cerebral -l app=webmcp -o yaml > webmcp-backup.yaml
```

### Data Recovery
- **Secrets**: Recreate from Vault
- **Certificates**: Automatically renewed by cert-manager
- **Deployment**: Redeploy from Git

## Performance Tuning

### Resource Limits
- **CPU**: 250m request, 500m limit
- **Memory**: 256Mi request, 512Mi limit

### nginx Tuning
- **Worker Processes**: Auto (CPU cores)
- **Worker Connections**: 1024
- **Keepalive**: 32 upstream connections

### FastAPI Tuning
- **Workers**: 1 per CPU core (recommended)
- **Log Level**: `info` for production
- **Access Logs**: Enabled

## Maintenance

### Updates
1. Update code in repository
2. Run deployment script: `./scripts/deploy-webmcp.sh`
3. Monitor rollout: `kubectl rollout status deployment/webmcp-deployment -n cerebral`

### Certificate Renewal
- **Automatic**: cert-manager handles renewal
- **Manual Check**: `kubectl get certificate -n cerebral`

### Log Rotation
- **Container Logs**: Managed by Kubernetes
- **nginx Logs**: Managed by nginx-ingress-controller

## Support

### Documentation
- **API Docs**: https://mcp.cerebral.baerautotech.com/docs
- **Architecture**: See `docs/architecture/MCP_ARCHITECTURE.md`

### Monitoring
- **Health**: https://mcp.cerebral.baerautotech.com/health
- **Stats**: https://mcp.cerebral.baerautotech.com/stats (restricted)

### Logs
```bash
# Application logs
kubectl logs -n cerebral deployment/webmcp-deployment -f

# nginx logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller -f
```
