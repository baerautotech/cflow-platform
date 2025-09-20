#!/bin/bash
# WebMCP Server Deployment Script
# Deploys WebMCP server to cerebral cluster with nginx and cert-manager

set -euo pipefail

# Configuration
NAMESPACE="cerebral"
IMAGE_NAME="webmcp"
REGISTRY="registry.baerautotech.com"
VERSION=$(git rev-parse --short HEAD)
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${VERSION}"

echo "🚀 Deploying WebMCP Server"
echo "=========================="
echo "Image: ${FULL_IMAGE}"
echo "Namespace: ${NAMESPACE}"
echo "Version: ${VERSION}"
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl."
    exit 1
fi

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ docker not found. Please install docker."
    exit 1
fi

# Check if we're connected to the cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Not connected to Kubernetes cluster. Please configure kubectl."
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Build Docker image
echo "🔨 Building Docker image..."
docker build -f infrastructure/docker/Dockerfile.webmcp -t "${FULL_IMAGE}" .
echo "✅ Docker image built: ${FULL_IMAGE}"
echo ""

# Push image to registry
echo "📤 Pushing image to registry..."
docker push "${FULL_IMAGE}"
echo "✅ Image pushed to registry"
echo ""

# Update image tag in deployment
echo "📝 Updating deployment with new image..."
sed -i.bak "s|image: webmcp:latest|image: ${FULL_IMAGE}|g" infrastructure/kubernetes/webmcp-deployment.yaml
echo "✅ Deployment updated with image: ${FULL_IMAGE}"
echo ""

# Apply Kubernetes manifests
echo "🚀 Applying Kubernetes manifests..."

# Apply cert-manager configuration
echo "  📜 Applying cert-manager configuration..."
kubectl apply -f infrastructure/kubernetes/cert-manager-config.yaml

# Apply WebMCP deployment
echo "  📜 Applying WebMCP deployment..."
kubectl apply -f infrastructure/kubernetes/webmcp-deployment.yaml

echo "✅ Kubernetes manifests applied"
echo ""

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl rollout status deployment/webmcp-deployment -n "${NAMESPACE}" --timeout=300s
echo "✅ Deployment is ready"
echo ""

# Check pod status
echo "📊 Checking pod status..."
kubectl get pods -n "${NAMESPACE}" -l app=webmcp
echo ""

# Check service status
echo "📊 Checking service status..."
kubectl get svc -n "${NAMESPACE}" -l app=webmcp
echo ""

# Check ingress status
echo "📊 Checking ingress status..."
kubectl get ingress -n "${NAMESPACE}" -l app=webmcp
echo ""

# Check certificate status
echo "📊 Checking certificate status..."
kubectl get certificate -n "${NAMESPACE}" -l app=webmcp
echo ""

# Test the deployment
echo "🧪 Testing deployment..."
echo "  Testing health endpoint..."
if kubectl run test-pod --image=curlimages/curl --rm -i --restart=Never -- curl -f http://webmcp-service:8000/health; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi

echo ""
echo "🎉 WebMCP Server deployment completed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "  Image: ${FULL_IMAGE}"
echo "  Namespace: ${NAMESPACE}"
echo "  Service: webmcp-service"
echo "  Ingress: webmcp-ingress"
echo "  Certificate: webmcp-cert"
echo ""
echo "🌐 Access URLs:"
echo "  Production: https://mcp.cerebral.baerautotech.com"
echo "  Development: https://mcp.dev.baerautotech.com"
echo ""
echo "📚 API Documentation:"
echo "  Swagger UI: https://mcp.cerebral.baerautotech.com/docs"
echo "  ReDoc: https://mcp.cerebral.baerautotech.com/redoc"
echo ""

# Restore original deployment file
mv infrastructure/kubernetes/webmcp-deployment.yaml.bak infrastructure/kubernetes/webmcp-deployment.yaml

echo "✨ Deployment script completed!"
