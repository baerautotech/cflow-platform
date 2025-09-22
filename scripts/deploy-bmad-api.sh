#!/bin/bash
set -euo pipefail

# BMAD API Service Deployment Script
# Deploys BMAD API service to cerebral cluster

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE_DEV="cerebral-development"
NAMESPACE_PROD="cerebral-production"
DEPLOYMENT_FILE_DEV="infrastructure/kubernetes/bmad-api-development.yaml"
DEPLOYMENT_FILE_PROD="infrastructure/kubernetes/bmad-api-production.yaml"

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if we can connect to the cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

create_namespaces() {
    log_info "Creating namespaces if they don't exist..."
    
    # Create development namespace
    if ! kubectl get namespace $NAMESPACE_DEV &> /dev/null; then
        kubectl create namespace $NAMESPACE_DEV
        log_success "Created namespace: $NAMESPACE_DEV"
    else
        log_info "Namespace $NAMESPACE_DEV already exists"
    fi
    
    # Create production namespace
    if ! kubectl get namespace $NAMESPACE_PROD &> /dev/null; then
        kubectl create namespace $NAMESPACE_PROD
        log_success "Created namespace: $NAMESPACE_PROD"
    else
        log_info "Namespace $NAMESPACE_PROD already exists"
    fi
}

deploy_development() {
    log_info "Deploying BMAD API service to development environment..."
    
    # Validate deployment file
    if [ ! -f "$DEPLOYMENT_FILE_DEV" ]; then
        log_error "Development deployment file not found: $DEPLOYMENT_FILE_DEV"
        exit 1
    fi
    
    # Apply deployment
    kubectl apply -f "$DEPLOYMENT_FILE_DEV"
    log_success "Applied development deployment"
    
    # Wait for deployment to be ready
    log_info "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/bmad-api -n $NAMESPACE_DEV
    
    # Check deployment status
    kubectl get deployment bmad-api -n $NAMESPACE_DEV
    kubectl get pods -l app=bmad-api -n $NAMESPACE_DEV
    
    log_success "Development deployment completed"
}

deploy_production() {
    log_info "Deploying BMAD API service to production environment..."
    
    # Validate deployment file
    if [ ! -f "$DEPLOYMENT_FILE_PROD" ]; then
        log_error "Production deployment file not found: $DEPLOYMENT_FILE_PROD"
        exit 1
    fi
    
    # Apply deployment
    kubectl apply -f "$DEPLOYMENT_FILE_PROD"
    log_success "Applied production deployment"
    
    # Wait for deployment to be ready
    log_info "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=600s deployment/bmad-api-production -n $NAMESPACE_PROD
    
    # Check deployment status
    kubectl get deployment bmad-api-production -n $NAMESPACE_PROD
    kubectl get pods -l app=bmad-api-production -n $NAMESPACE_PROD
    
    log_success "Production deployment completed"
}

check_deployment_health() {
    local namespace=$1
    local deployment_name=$2
    
    log_info "Checking deployment health for $deployment_name in $namespace..."
    
    # Get pod status
    kubectl get pods -l app=$deployment_name -n $namespace
    
    # Check if all pods are running
    local running_pods=$(kubectl get pods -l app=$deployment_name -n $namespace --field-selector=status.phase=Running --no-headers | wc -l)
    local total_pods=$(kubectl get pods -l app=$deployment_name -n $namespace --no-headers | wc -l)
    
    if [ "$running_pods" -eq "$total_pods" ] && [ "$total_pods" -gt 0 ]; then
        log_success "All $total_pods pods are running"
    else
        log_warning "$running_pods/$total_pods pods are running"
    fi
    
    # Check service endpoints
    kubectl get endpoints -l app=$deployment_name -n $namespace
    
    # Test health endpoint (if service is accessible)
    local service_name="bmad-api-service"
    if kubectl get service $service_name -n $namespace &> /dev/null; then
        log_info "Service $service_name is available"
        
        # Try to port-forward and test health endpoint
        log_info "Testing health endpoint..."
        kubectl port-forward -n $namespace service/$service_name 8080:8001 &
        local port_forward_pid=$!
        
        sleep 5
        
        if curl -f http://localhost:8080/bmad/health &> /dev/null; then
            log_success "Health endpoint is responding"
        else
            log_warning "Health endpoint test failed"
        fi
        
        kill $port_forward_pid 2>/dev/null || true
    fi
}

show_deployment_info() {
    local environment=$1
    local namespace=$2
    local deployment_name=$3
    
    log_info "Deployment Information for $environment:"
    echo "=================================="
    echo "Environment: $environment"
    echo "Namespace: $namespace"
    echo "Deployment: $deployment_name"
    echo ""
    
    # Show service URLs
    if [ "$environment" = "production" ]; then
        echo "External URL: https://bmad-api.cerebral.baerautotech.com"
    else
        echo "Internal URL: http://bmad-api-service.$namespace.svc.cluster.local:8001"
    fi
    echo ""
    
    # Show useful kubectl commands
    echo "Useful commands:"
    echo "  kubectl get pods -l app=$deployment_name -n $namespace"
    echo "  kubectl logs -l app=$deployment_name -n $namespace"
    echo "  kubectl describe deployment $deployment_name -n $namespace"
    echo "  kubectl get service bmad-api-service -n $namespace"
    echo ""
}

cleanup_deployment() {
    local environment=$1
    
    if [ "$environment" = "development" ]; then
        log_info "Cleaning up development deployment..."
        kubectl delete -f "$DEPLOYMENT_FILE_DEV" || true
        log_success "Development deployment cleaned up"
    elif [ "$environment" = "production" ]; then
        log_info "Cleaning up production deployment..."
        kubectl delete -f "$DEPLOYMENT_FILE_PROD" || true
        log_success "Production deployment cleaned up"
    else
        log_error "Invalid environment: $environment"
        exit 1
    fi
}

show_help() {
    echo "BMAD API Service Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  deploy-dev     Deploy to development environment"
    echo "  deploy-prod    Deploy to production environment"
    echo "  deploy-all     Deploy to both environments"
    echo "  health-dev     Check development deployment health"
    echo "  health-prod    Check production deployment health"
    echo "  cleanup-dev    Remove development deployment"
    echo "  cleanup-prod   Remove production deployment"
    echo "  help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy-dev"
    echo "  $0 deploy-prod"
    echo "  $0 health-dev"
    echo "  $0 cleanup-dev"
}

# Main script logic
main() {
    local command=${1:-help}
    
    case $command in
        deploy-dev)
            check_prerequisites
            create_namespaces
            deploy_development
            check_deployment_health $NAMESPACE_DEV "bmad-api"
            show_deployment_info "development" $NAMESPACE_DEV "bmad-api"
            ;;
        deploy-prod)
            check_prerequisites
            create_namespaces
            deploy_production
            check_deployment_health $NAMESPACE_PROD "bmad-api-production"
            show_deployment_info "production" $NAMESPACE_PROD "bmad-api-production"
            ;;
        deploy-all)
            check_prerequisites
            create_namespaces
            deploy_development
            deploy_production
            check_deployment_health $NAMESPACE_DEV "bmad-api"
            check_deployment_health $NAMESPACE_PROD "bmad-api-production"
            show_deployment_info "development" $NAMESPACE_DEV "bmad-api"
            show_deployment_info "production" $NAMESPACE_PROD "bmad-api-production"
            ;;
        health-dev)
            check_deployment_health $NAMESPACE_DEV "bmad-api"
            ;;
        health-prod)
            check_deployment_health $NAMESPACE_PROD "bmad-api-production"
            ;;
        cleanup-dev)
            cleanup_deployment "development"
            ;;
        cleanup-prod)
            cleanup_deployment "production"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
