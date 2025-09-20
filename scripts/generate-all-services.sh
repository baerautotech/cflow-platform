#!/bin/bash

# Generate All Cerebral Platform Services
# Uses the simple pod generator to create deployments for all services

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

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

# Parse command line arguments
ENVIRONMENTS="development"
SERVICES="all"
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environments)
            ENVIRONMENTS="$2"
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
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -e, --environments ENVS  Comma-separated list of environments (development,staging,production,enterprise)"
            echo "  -s, --services SERVICES  Services to generate (all|webmcp|bmad-api|...) or comma-separated list"
            echo "  -d, --dry-run           Show what would be generated without actually generating"
            echo "  -h, --help              Show this help message"
            echo ""
            echo "Available services:"
            echo "  webmcp, bmad-api, knowledge-rag, provider-router, expansion-manager,"
            echo "  hil-session-manager, workflow-orchestrator, document-approval,"
            echo "  project-detector, monitoring-metrics"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Get services to generate
get_services_to_generate() {
    if [[ "$SERVICES" == "all" ]]; then
        echo "webmcp bmad-api knowledge-rag provider-router expansion-manager hil-session-manager workflow-orchestrator document-approval project-detector monitoring-metrics"
    else
        echo "$SERVICES" | tr ',' ' '
    fi
}

# Get environments to generate
get_environments_to_generate() {
    echo "$ENVIRONMENTS" | tr ',' ' '
}

# Generate service for environment
generate_service_for_environment() {
    local service_name="$1"
    local environment="$2"
    
    log_info "Generating $service_name for $environment"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would generate $service_name-$environment.yaml"
        return 0
    fi
    
    # Generate the service
    cd "$PROJECT_ROOT"
    if python3 "$SCRIPT_DIR/generate-pod-simple.py" "$service_name" "$environment"; then
        log_success "Generated $service_name for $environment"
        return 0
    else
        log_error "Failed to generate $service_name for $environment"
        return 1
    fi
}

# Main execution
main() {
    log_info "Starting Cerebral Platform service generation"
    log_info "Environments: $ENVIRONMENTS"
    log_info "Services: $SERVICES"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN MODE - No actual files will be generated"
    fi
    
    # Get services and environments
    local services_to_generate=($(get_services_to_generate))
    local environments_to_generate=($(get_environments_to_generate))
    
    if [[ ${#services_to_generate[@]} -eq 0 ]]; then
        log_error "No services to generate"
        exit 1
    fi
    
    if [[ ${#environments_to_generate[@]} -eq 0 ]]; then
        log_error "No environments to generate"
        exit 1
    fi
    
    log_info "Services to generate: ${services_to_generate[*]}"
    log_info "Environments to generate: ${environments_to_generate[*]}"
    
    # Generate each service for each environment
    local total_generations=0
    local successful_generations=0
    local failed_generations=0
    
    for service in "${services_to_generate[@]}"; do
        for environment in "${environments_to_generate[@]}"; do
            total_generations=$((total_generations + 1))
            
            if generate_service_for_environment "$service" "$environment"; then
                successful_generations=$((successful_generations + 1))
            else
                failed_generations=$((failed_generations + 1))
            fi
        done
    done
    
    # Report results
    log_info "Generation complete!"
    log_info "Total generations: $total_generations"
    log_success "Successful: $successful_generations"
    
    if [[ $failed_generations -gt 0 ]]; then
        log_error "Failed: $failed_generations"
        exit 1
    else
        log_success "All generations successful!"
    fi
}

# Run main function
main "$@"
