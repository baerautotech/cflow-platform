#!/bin/bash

# Deploy Cerebral Platform to Cerebral Cluster
# This script ensures MCP endpoints are deployed via Git

set -e

echo "🚀 Deploying Cerebral Platform to Cerebral Cluster..."

# Configuration
CEREBRAL_CLUSTER="10.34.0.22"  # worker-02
NAMESPACE="cerebral-platform"
SHA=${GITHUB_SHA:-$(git rev-parse HEAD)}
IMAGE_TAG="${SHA}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "cflow_platform/api/mcp_endpoints.py" ]; then
    print_error "MCP endpoints not found. Run this script from the project root."
    exit 1
fi

# Build Docker image with SHA
print_status "Building Docker image with SHA: $SHA..."
docker build -f Dockerfile.mcp-api -t cerebral-platform/mcp-api:$IMAGE_TAG .

# Tag for cerebral cluster registry
docker tag cerebral-platform/mcp-api:$IMAGE_TAG cerebral-platform/mcp-api:latest

print_status "Docker image built successfully with SHA: $SHA"

# Copy deployment files to cerebral cluster
print_status "Copying deployment files to cerebral cluster..."

# Copy Kubernetes manifests
scp deploy/cerebral-cluster.yaml cerebral@$CEREBRAL_CLUSTER:/tmp/

# Copy Docker image (if registry is available)
print_status "Pushing Docker image to cerebral cluster registry..."
# Note: This assumes a registry is running on the cerebral cluster
# docker push cerebral-platform/mcp-api:$IMAGE_TAG

# Deploy to Kubernetes
print_status "Deploying to Kubernetes..."

ssh cerebral@$CEREBRAL_CLUSTER << EOF
    # Create namespace if it doesn't exist
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply secrets (these need to be configured with actual values)
    kubectl apply -f /tmp/cerebral-cluster.yaml
    
    # Wait for deployment to be ready
    kubectl wait --for=condition=available --timeout=300s deployment/cerebral-mcp-api -n $NAMESPACE
    
    # Check deployment status
    kubectl get pods -n $NAMESPACE -l app=cerebral-mcp-api
    
    # Check service
    kubectl get svc -n $NAMESPACE cerebral-mcp-api-service
    
    # Check ingress
    kubectl get ingress -n $NAMESPACE cerebral-mcp-api-ingress
EOF

print_status "Deployment completed successfully!"

# Test the deployment
print_status "Testing MCP API deployment..."

# Wait a moment for the service to be ready
sleep 10

# Test health endpoint
HEALTH_URL="https://mcp.dev.baerautotech.com/health"
print_status "Testing health endpoint: $HEALTH_URL"

if curl -f -s "$HEALTH_URL" > /dev/null; then
    print_status "✅ MCP API is healthy and responding"
else
    print_warning "⚠️ MCP API health check failed. Check the deployment."
fi

# Test tools endpoint
TOOLS_URL="https://mcp.dev.baerautotech.com/tools"
print_status "Testing tools endpoint: $TOOLS_URL"

if curl -f -s "$TOOLS_URL" > /dev/null; then
    print_status "✅ MCP API tools endpoint is responding"
else
    print_warning "⚠️ MCP API tools endpoint failed. Check the deployment."
fi

print_status "🎉 Deployment to Cerebral Cluster completed!"
print_status "MCP API available at: https://mcp.dev.baerautotech.com"
print_status "Health check: https://mcp.dev.baerautotech.com/health"
print_status "Tools list: https://mcp.dev.baerautotech.com/tools"

echo ""
print_status "Next steps:"
echo "1. Configure DNS for mcp.dev.baerautotech.com to point to cerebral cluster"
echo "2. Set up SSL certificates (Let's Encrypt)"
echo "3. Configure secrets in Kubernetes with actual values"
echo "4. Test token generation and user authentication"
echo "5. Create one-touch installers for end users"
