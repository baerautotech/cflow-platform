#!/bin/bash

# Cerebral Platform - Deploy All Services
# Uses the pod framework to deploy all services consistently

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRAMEWORK_DIR="$PROJECT_ROOT/infrastructure/framework"
K8S_DIR="$PROJECT_ROOT/infrastructure/kubernetes"
REGISTRY="registry.baerautotech.com"

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

# Parse command line arguments
ENVIRONMENT="development"
SERVICES="all"
DRY_RUN=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -s|--services)
            SERVICES="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -e, --environment ENV    Deployment environment (development|staging|production|enterprise)"
            echo "  -s, --services SERVICES  Services to deploy (all|webmcp|bmad-api|knowledge-rag|...) or comma-separated list"
            echo "  -d, --dry-run           Show what would be deployed without actually deploying"
            echo "  -f, --force             Force deployment even if services are already running"
            echo "  -h, --help              Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production|enterprise)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT"
    log_error "Valid environments: development, staging, production, enterprise"
    exit 1
fi

# Get SHA
SHA=$(get_sha)
log_info "Using SHA: $SHA"

# Load service definitions
load_services() {
    local services_file="$FRAMEWORK_DIR/services.yaml"
    if [[ ! -f "$services_file" ]]; then
        log_error "Services definition file not found: $services_file"
        exit 1
    fi
    
    # Extract service names from YAML
    yq eval '.services | keys | .[]' "$services_file"
}

# Get services to deploy
get_services_to_deploy() {
    if [[ "$SERVICES" == "all" ]]; then
        load_services
    else
        echo "$SERVICES" | tr ',' ' '
    fi
}

# Generate service deployment
generate_service_deployment() {
    local service_name="$1"
    local environment="$2"
    local sha="$3"
    
    log_info "Generating deployment for $service_name ($environment)"
    
    # Check if service is defined
    local service_def=$(yq eval ".services.$service_name" "$FRAMEWORK_DIR/services.yaml")
    if [[ "$service_def" == "null" ]]; then
        log_error "Service $service_name not found in services.yaml"
        return 1
    fi
    
    # Extract service configuration
    local component=$(yq eval ".services.$service_name.component" "$FRAMEWORK_DIR/services.yaml")
    local tier=$(yq eval ".services.$service_name.tier" "$FRAMEWORK_DIR/services.yaml")
    local port=$(yq eval ".services.$service_name.port" "$FRAMEWORK_DIR/services.yaml")
    local image=$(yq eval ".services.$service_name.image" "$FRAMEWORK_DIR/services.yaml")
    
    # Generate deployment using the pod generator
    cd "$PROJECT_ROOT"
    python3 "$SCRIPT_DIR/generate-pod.py" \
        "$service_name" \
        "$component" \
        "$tier" \
        "$environment" \
        --port "$port" \
        --image "$image"
    
    if [[ $? -eq 0 ]]; then
        log_success "Generated deployment for $service_name"
    else
        log_error "Failed to generate deployment for $service_name"
        return 1
    fi
}

# Build Docker image
build_image() {
    local service_name="$1"
    local sha="$2"
    local image_tag="$REGISTRY/$service_name:$sha"
    
    log_info "Building Docker image: $image_tag"
    
    # Check if Dockerfile exists
    local dockerfile="$PROJECT_ROOT/infrastructure/docker/Dockerfile.$service_name"
    if [[ ! -f "$dockerfile" ]]; then
        log_warning "Dockerfile not found: $dockerfile"
        log_warning "Using generic Dockerfile for $service_name"
        dockerfile="$PROJECT_ROOT/infrastructure/docker/Dockerfile.generic"
    fi
    
    if [[ ! -f "$dockerfile" ]]; then
        log_error "No Dockerfile found for $service_name"
        return 1
    fi
    
    # Build the image
    docker build -f "$dockerfile" -t "$image_tag" "$PROJECT_ROOT"
    
    if [[ $? -eq 0 ]]; then
        log_success "Built Docker image: $image_tag"
        echo "$image_tag"
    else
        log_error "Failed to build Docker image: $image_tag"
        return 1
    fi
}

# Push Docker image
push_image() {
    local image_tag="$1"
    
    log_info "Pushing Docker image: $image_tag"
    
    docker push "$image_tag"
    
    if [[ $? -eq 0 ]]; then
        log_success "Pushed Docker image: $image_tag"
    else
        log_error "Failed to push Docker image: $image_tag"
        return 1
    fi
}

# Deploy to Kubernetes
deploy_to_k8s() {
    local service_name="$1"
    local environment="$2"
    local image_tag="$3"
    
    log_info "Deploying $service_name to Kubernetes ($environment)"
    
    # Apply the generated manifests
    local manifest_file="$K8S_DIR/$service_name-$environment.yaml"
    if [[ ! -f "$manifest_file" ]]; then
        log_error "Manifest file not found: $manifest_file"
        return 1
    fi
    
    # Update image in deployment
    kubectl set image deployment/$service_name $service_name="$image_tag" -n cerebral-$environment
    
    if [[ $? -eq 0 ]]; then
        log_success "Updated deployment for $service_name"
    else
        log_error "Failed to update deployment for $service_name"
        return 1
    fi
    
    # Wait for rollout
    log_info "Waiting for rollout to complete..."
    kubectl rollout status deployment/$service_name -n cerebral-$environment --timeout=300s
    
    if [[ $? -eq 0 ]]; then
        log_success "Rollout completed for $service_name"
    else
        log_error "Rollout failed for $service_name"
        return 1
    fi
}

# Health check
health_check() {
    local service_name="$1"
    local environment="$2"
    local port="$3"
    
    log_info "Performing health check for $service_name"
    
    # Get pod name
    local pod_name=$(kubectl get pods -n cerebral-$environment -l app=$service_name -o jsonpath='{.items[0].metadata.name}')
    
    if [[ -z "$pod_name" ]]; then
        log_error "No pods found for service $service_name"
        return 1
    fi
    
    # Check health endpoint
    kubectl exec -n cerebral-$environment $pod_name -- curl -f http://localhost:$port/health
    
    if [[ $? -eq 0 ]]; then
        log_success "Health check passed for $service_name"
    else
        log_error "Health check failed for $service_name"
        return 1
    fi
}

# Main deployment function
deploy_service() {
    local service_name="$1"
    local environment="$2"
    local sha="$3"
    
    log_info "Deploying service: $service_name"
    
    # Get service configuration
    local port=$(yq eval ".services.$service_name.port" "$FRAMEWORK_DIR/services.yaml")
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would deploy $service_name ($environment) with SHA $sha"
        return 0
    fi
    
    # Generate deployment
    generate_service_deployment "$service_name" "$environment" "$sha"
    
    # Build image
    local image_tag=$(build_image "$service_name" "$sha")
    
    # Push image
    push_image "$image_tag"
    
    # Deploy to Kubernetes
    deploy_to_k8s "$service_name" "$environment" "$image_tag"
    
    # Health check
    health_check "$service_name" "$environment" "$port"
    
    log_success "Successfully deployed $service_name"
}

# Main execution
main() {
    log_info "Starting Cerebral Platform deployment"
    log_info "Environment: $ENVIRONMENT"
    log_info "Services: $SERVICES"
    log_info "SHA: $SHA"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN MODE - No actual deployment will occur"
    fi
    
    # Check prerequisites
    if [[ "$DRY_RUN" == "false" ]]; then
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
        
        # Check if yq is available
        if ! command -v yq > /dev/null 2>&1; then
            log_error "yq is not installed or not in PATH"
            exit 1
        fi
    fi
    
    # Get services to deploy
    local services_to_deploy=($(get_services_to_deploy))
    
    if [[ ${#services_to_deploy[@]} -eq 0 ]]; then
        log_error "No services to deploy"
        exit 1
    fi
    
    log_info "Services to deploy: ${services_to_deploy[*]}"
    
    # Deploy each service
    local failed_services=()
    for service in "${services_to_deploy[@]}"; do
        if ! deploy_service "$service" "$ENVIRONMENT" "$SHA"; then
            failed_services+=("$service")
        fi
    done
    
    # Report results
    if [[ ${#failed_services[@]} -eq 0 ]]; then
        log_success "All services deployed successfully!"
        log_info "Environment: $ENVIRONMENT"
        log_info "SHA: $SHA"
        log_info "Services: ${services_to_deploy[*]}"
    else
        log_error "Some services failed to deploy: ${failed_services[*]}"
        exit 1
    fi
}

# Run main function
main "$@"
