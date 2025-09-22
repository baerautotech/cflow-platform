# One-Touch Installer - Cluster Deployment Guide

## 🎯 **Overview**

The One-Touch Installer has been updated to support cluster deployment configuration for the Cerebral cloud platform. It can now automatically configure WebMCP connections for both local development and cluster deployment environments.

## 🚀 **New Features**

### **Cluster Deployment Support**
- **Automatic Detection**: Detects cluster vs local deployment based on URLs
- **Cluster Endpoints**: Pre-configured endpoints for Cerebral cloud services
- **DNS Integration**: Uses cluster DNS resolution (`cerebral.baerautotech.com`)
- **Authentication**: Integrates with Dex OIDC authentication
- **Certificates**: Uses Let's Encrypt certificates via cert-manager

### **Enhanced Configuration**
- **Dual Mode**: Supports both local and cluster deployment modes
- **Validation**: Validates cluster endpoint connectivity
- **Custom URLs**: Allows custom cluster endpoint URLs
- **Configuration Management**: Creates and manages WebMCP configuration files

## 📋 **Usage Examples**

### **Basic Cluster Deployment Setup**
```bash
# Setup WebMCP for cluster deployment
python -m cflow_platform.cli.one_touch_installer --setup-webmcp --cluster-deployment

# Setup with BMAD integration
python -m cflow_platform.cli.one_touch_installer --setup-webmcp --setup-bmad --cluster-deployment

# Full setup with all components
python -m cflow_platform.cli.one_touch_installer \
  --setup-webmcp \
  --setup-bmad \
  --verify-bmad \
  --cluster-deployment \
  --overwrite-config
```

### **Cluster Validation**
```bash
# Validate cluster endpoints
python -m cflow_platform.cli.one_touch_installer --validate-cluster

# Validate and setup in one command
python -m cflow_platform.cli.one_touch_installer \
  --validate-cluster \
  --setup-webmcp \
  --cluster-deployment
```

### **Custom Cluster URLs**
```bash
# Use custom cluster endpoints
python -m cflow_platform.cli.one_touch_installer \
  --setup-webmcp \
  --cluster-deployment \
  --cluster-webmcp-url "https://custom-webmcp.example.com" \
  --cluster-bmad-api-url "https://custom-bmad-api.example.com" \
  --cluster-bmad-method-url "https://custom-bmad-method.example.com"
```

### **Local Development Setup**
```bash
# Setup for local development
python -m cflow_platform.cli.one_touch_installer \
  --setup-webmcp \
  --webmcp-server-url "http://localhost:8000" \
  --bmad-api-url "http://localhost:8001"
```

## 🔧 **Configuration Details**

### **Cluster Deployment Configuration**
When using `--cluster-deployment`, the installer creates a configuration with:

```json
{
  "deployment_type": "cluster",
  "webmcp": {
    "server_url": "https://webmcp-bmad.dev.cerebral.baerautotech.com",
    "api_key": "your-api-key",
    "timeout": 30,
    "health_endpoint": "https://webmcp-bmad.dev.cerebral.baerautotech.com/health",
    "tools_endpoint": "https://webmcp-bmad.dev.cerebral.baerautotech.com/mcp/tools",
    "call_endpoint": "https://webmcp-bmad.dev.cerebral.baerautotech.com/mcp/tools/call"
  },
  "bmad_api": {
    "server_url": "https://bmad-api.dev.cerebral.baerautotech.com",
    "auth_token": "your-auth-token",
    "timeout": 30,
    "health_endpoint": "https://bmad-api.dev.cerebral.baerautotech.com/health",
    "project_type_endpoint": "https://bmad-api.dev.cerebral.baerautotech.com/bmad/project-type/detect",
    "prd_create_endpoint": "https://bmad-api.dev.cerebral.baerautotech.com/bmad/greenfield/prd-create"
  },
  "bmad_method": {
    "server_url": "https://bmad-method.dev.cerebral.baerautotech.com",
    "timeout": 30,
    "health_endpoint": "https://bmad-method.dev.cerebral.baerautotech.com/health",
    "agents_endpoint": "https://bmad-method.dev.cerebral.baerautotech.com/bmad/agents",
    "workflows_endpoint": "https://bmad-method.dev.cerebral.baerautotech.com/bmad/workflows"
  },
  "cluster_info": {
    "dns_resolution": "cerebral.baerautotech.com",
    "certificates": "Let's Encrypt via cert-manager",
    "authentication": "Dex OIDC",
    "load_balancer": "MetalLB"
  }
}
```

### **Local Deployment Configuration**
For local development, the configuration includes:

```json
{
  "deployment_type": "local",
  "webmcp": {
    "server_url": "http://localhost:8000",
    "api_key": "your-api-key",
    "timeout": 30,
    "health_endpoint": "http://localhost:8000/health",
    "tools_endpoint": "http://localhost:8000/mcp/tools",
    "call_endpoint": "http://localhost:8000/mcp/tools/call"
  },
  "bmad_api": {
    "server_url": "http://localhost:8001",
    "auth_token": "your-auth-token",
    "timeout": 30,
    "health_endpoint": "http://localhost:8001/health"
  },
  "bmad_method": {
    "server_url": "http://localhost:8080",
    "timeout": 30,
    "health_endpoint": "http://localhost:8080/health"
  }
}
```

## 📁 **Configuration File Location**

The WebMCP configuration is stored at:
- **Path**: `~/.cerebraflow/webmcp/config.json`
- **Format**: JSON
- **Permissions**: User-readable/writable

## 🔍 **Validation and Testing**

### **Cluster Endpoint Validation**
The `--validate-cluster` option tests connectivity to:
- WebMCP Server: `https://webmcp-bmad.dev.cerebral.baerautotech.com`
- BMAD API Service: `https://bmad-api.dev.cerebral.baerautotech.com`
- BMAD-Method Service: `https://bmad-method.dev.cerebral.baerautotech.com`

### **Health Check Endpoints**
Each service provides health check endpoints:
- `/health` - Service health status
- `/mcp/tools` - Available MCP tools (WebMCP only)
- `/bmad/agents` - Available BMAD agents (BMAD-Method only)
- `/bmad/workflows` - Available BMAD workflows (BMAD-Method only)

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Connection Refused**
```bash
# Check if services are running
python -m cflow_platform.cli.one_touch_installer --validate-cluster
```

#### **Configuration Not Found**
```bash
# Recreate configuration
python -m cflow_platform.cli.one_touch_installer --setup-webmcp --cluster-deployment --overwrite-config
```

#### **DNS Resolution Issues**
- Ensure cluster DNS is properly configured
- Check CoreDNS configuration in `kube-system` namespace
- Verify MetalLB IP assignments

#### **Authentication Issues**
- Verify Dex OIDC is running
- Check JWT token validity
- Ensure proper API keys are configured

### **Debug Commands**
```bash
# Test individual components
python -m cflow_platform.cli.one_touch_installer --verify-bmad
python -m cflow_platform.cli.one_touch_installer --validate-cluster

# Check configuration file
cat ~/.cerebraflow/webmcp/config.json | jq '.'

# Test connectivity manually
curl -s https://webmcp-bmad.dev.cerebral.baerautotech.com/health | jq '.'
curl -s https://bmad-api.dev.cerebral.baerautotech.com/health | jq '.'
curl -s https://bmad-method.dev.cerebral.baerautotech.com/health | jq '.'
```

## 📚 **Command Reference**

### **New Options**
- `--cluster-deployment`: Configure for cluster deployment
- `--validate-cluster`: Validate cluster endpoint connectivity
- `--cluster-webmcp-url`: Custom WebMCP server URL
- `--cluster-bmad-api-url`: Custom BMAD API service URL
- `--cluster-bmad-method-url`: Custom BMAD-Method service URL

### **Existing Options**
- `--setup-webmcp`: Setup WebMCP configuration
- `--setup-bmad`: Setup BMAD integration components
- `--verify-bmad`: Verify BMAD templates and handlers
- `--overwrite-config`: Overwrite existing configuration
- `--webmcp-server-url`: WebMCP server URL (local)
- `--webmcp-api-key`: WebMCP API key
- `--bmad-api-url`: BMAD API service URL (local)
- `--bmad-auth-token`: BMAD authentication token

## 🎉 **Success Indicators**

### **Successful Cluster Setup**
```
✅ WebMCP configuration installed successfully
🌐 Cluster endpoints configured:
  WebMCP: https://webmcp-bmad.dev.cerebral.baerautotech.com
  BMAD API: https://bmad-api.dev.cerebral.baerautotech.com
  BMAD-Method: https://bmad-method.dev.cerebral.baerautotech.com
✅ Cluster deployment validation successful
```

### **Configuration File Created**
```bash
# Verify configuration
ls -la ~/.cerebraflow/webmcp/config.json
cat ~/.cerebraflow/webmcp/config.json | jq '.deployment_type'
# Should output: "cluster"
```

---

**The One-Touch Installer is now ready for both local development and cluster deployment!** 🚀
