#!/bin/bash

# WebMCP Production Deployment Script
# This script builds and deploys the WebMCP server with Master Tool Pattern to the cerebral cluster

set -euo pipefail

# Configuration
REGISTRY="registry.baerautotech.com"
IMAGE_NAME="webmcp"
NAMESPACE="cerebral-development"
DEPLOYMENT_NAME="webmcp-production"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get current SHA
get_sha() {
    local sha=$(git rev-parse --short HEAD)
    echo "$sha"
}

# Build Docker image
build_image() {
    local sha=$1
    local image_tag="${REGISTRY}/${IMAGE_NAME}:${sha}"
    
    log_info "Building Docker image: ${image_tag}"
    
    # Build the image
    docker build -f infrastructure/docker/Dockerfile.webmcp -t "${image_tag}" .
    
    if [ $? -eq 0 ]; then
        log_success "Docker image built successfully: ${image_tag}"
        echo "${image_tag}"
    else
        log_error "Failed to build Docker image"
        exit 1
    fi
}

# Push Docker image
push_image() {
    local image_tag=$1
    
    log_info "Pushing Docker image: ${image_tag}"
    
    docker push "${image_tag}"
    
    if [ $? -eq 0 ]; then
        log_success "Docker image pushed successfully: ${image_tag}"
    else
        log_error "Failed to push Docker image"
        exit 1
    fi
}

# Deploy to Kubernetes
deploy_to_k8s() {
    local image_tag=$1
    
    log_info "Deploying to Kubernetes namespace: ${NAMESPACE}"
    
    # Update the deployment with the new image
    kubectl set image deployment/${DEPLOYMENT_NAME} webmcp="${image_tag}" -n ${NAMESPACE}
    
    if [ $? -eq 0 ]; then
        log_success "Deployment updated successfully"
    else
        log_error "Failed to update deployment"
        exit 1
    fi
    
    # Wait for rollout to complete
    log_info "Waiting for rollout to complete..."
    kubectl rollout status deployment/${DEPLOYMENT_NAME} -n ${NAMESPACE} --timeout=300s
    
    if [ $? -eq 0 ]; then
        log_success "Rollout completed successfully"
    else
        log_error "Rollout failed or timed out"
        exit 1
    fi
}

# Health check
health_check() {
    log_info "Performing health check..."
    
    # Get pod name
    local pod_name=$(kubectl get pods -n ${NAMESPACE} -l app=${DEPLOYMENT_NAME} -o jsonpath='{.items[0].metadata.name}')
    
    if [ -z "$pod_name" ]; then
        log_error "No pods found for deployment ${DEPLOYMENT_NAME}"
        exit 1
    fi
    
    # Check health endpoint
    kubectl exec -n ${NAMESPACE} ${pod_name} -- curl -f http://localhost:8000/health
    
    if [ $? -eq 0 ]; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        exit 1
    fi
}

# Test Master Tool Pattern
test_master_tools() {
    log_info "Testing Master Tool Pattern..."
    
    # Get pod name
    local pod_name=$(kubectl get pods -n ${NAMESPACE} -l app=${DEPLOYMENT_NAME} -o jsonpath='{.items[0].metadata.name}')
    
    if [ -z "$pod_name" ]; then
        log_error "No pods found for deployment ${DEPLOYMENT_NAME}"
        exit 1
    fi
    
    # Test help endpoint
    kubectl exec -n ${NAMESPACE} ${pod_name} -- curl -f http://localhost:8000/help > /dev/null
    
    if [ $? -eq 0 ]; then
        log_success "Help endpoint working"
    else
        log_error "Help endpoint failed"
        exit 1
    fi
    
    # Test master tools endpoint
    kubectl exec -n ${NAMESPACE} ${pod_name} -- curl -f http://localhost:8000/mcp/master-tools > /dev/null
    
    if [ $? -eq 0 ]; then
        log_success "Master tools endpoint working"
    else
        log_error "Master tools endpoint failed"
        exit 1
    fi
    
    log_success "Master Tool Pattern test passed"
}

# Main deployment function
main() {
    log_info "Starting WebMCP Production Deployment"
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not in a git repository"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi
    
    # Check if kubectl is available
    if ! command -v kubectl > /dev/null 2>&1; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Get SHA
    local sha=$(get_sha)
    log_info "Using SHA: ${sha}"
    
    # Build image
    local image_tag=$(build_image "${sha}")
    
    # Push image
    push_image "${image_tag}"
    
    # Deploy to Kubernetes
    deploy_to_k8s "${image_tag}"
    
    # Health check
    health_check
    
    # Test Master Tool Pattern
    test_master_tools
    
    log_success "WebMCP Production Deployment completed successfully!"
    log_info "Image: ${image_tag}"
    log_info "Namespace: ${NAMESPACE}"
    log_info "Deployment: ${DEPLOYMENT_NAME}"
}

# Run main function
main "$@"
