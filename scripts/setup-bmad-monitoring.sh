#!/bin/bash
set -euo pipefail

# BMAD API Monitoring Setup Script
# Sets up monitoring and alerting for BMAD API service

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE_PROD="cerebral-production"
MONITORING_FILE="infrastructure/kubernetes/bmad-api-monitoring.yaml"

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
    log_info "Checking monitoring prerequisites..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Prometheus operator is installed
    if ! kubectl get crd servicemonitors.monitoring.coreos.com &> /dev/null; then
        log_error "Prometheus operator is not installed (ServiceMonitor CRD not found)"
        log_info "Please install Prometheus operator first"
        exit 1
    fi
    
    # Check if we can connect to the cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

setup_monitoring() {
    log_info "Setting up BMAD API monitoring..."
    
    # Validate monitoring file
    if [ ! -f "$MONITORING_FILE" ]; then
        log_error "Monitoring configuration file not found: $MONITORING_FILE"
        exit 1
    fi
    
    # Apply monitoring configuration
    kubectl apply -f "$MONITORING_FILE"
    log_success "Applied monitoring configuration"
    
    # Verify ServiceMonitor
    if kubectl get servicemonitor bmad-api-monitor -n $NAMESPACE_PROD &> /dev/null; then
        log_success "ServiceMonitor created successfully"
    else
        log_error "ServiceMonitor creation failed"
        exit 1
    fi
    
    # Verify PrometheusRule
    if kubectl get prometheusrule bmad-api-alerts -n $NAMESPACE_PROD &> /dev/null; then
        log_success "PrometheusRule created successfully"
    else
        log_error "PrometheusRule creation failed"
        exit 1
    fi
    
    # Verify ConfigMap
    if kubectl get configmap bmad-api-dashboard -n $NAMESPACE_PROD &> /dev/null; then
        log_success "Dashboard ConfigMap created successfully"
    else
        log_error "Dashboard ConfigMap creation failed"
        exit 1
    fi
}

verify_monitoring() {
    log_info "Verifying monitoring setup..."
    
    # Check if metrics endpoint is accessible
    log_info "Checking metrics endpoint..."
    kubectl port-forward -n $NAMESPACE_PROD service/bmad-api-metrics 8080:8001 &
    local port_forward_pid=$!
    
    sleep 5
    
    if curl -f http://localhost:8080/bmad/metrics &> /dev/null; then
        log_success "Metrics endpoint is accessible"
    else
        log_warning "Metrics endpoint test failed"
    fi
    
    kill $port_forward_pid 2>/dev/null || true
    
    # Check Prometheus targets
    log_info "Checking Prometheus targets..."
    if kubectl get servicemonitor bmad-api-monitor -n $NAMESPACE_PROD -o yaml | grep -q "bmad-api-production"; then
        log_success "ServiceMonitor configuration is correct"
    else
        log_warning "ServiceMonitor configuration might be incorrect"
    fi
    
    # Check alert rules
    log_info "Checking alert rules..."
    local alert_count=$(kubectl get prometheusrule bmad-api-alerts -n $NAMESPACE_PROD -o yaml | grep -c "alert:")
    log_info "Found $alert_count alert rules"
    
    if [ "$alert_count" -ge 5 ]; then
        log_success "Alert rules are properly configured"
    else
        log_warning "Alert rules might be incomplete"
    fi
}

show_monitoring_info() {
    log_info "Monitoring Setup Information:"
    echo "=================================="
    echo "ServiceMonitor: bmad-api-monitor"
    echo "PrometheusRule: bmad-api-alerts"
    echo "Dashboard ConfigMap: bmad-api-dashboard"
    echo "Metrics Service: bmad-api-metrics"
    echo ""
    
    echo "Available Metrics:"
    echo "  - bmad_api_requests_total"
    echo "  - bmad_api_errors_total"
    echo "  - bmad_api_request_duration_seconds"
    echo "  - bmad_workflow_executions_total"
    echo "  - bmad_workflow_failures_total"
    echo "  - bmad_expansion_pack_installs_total"
    echo "  - bmad_expansion_pack_activations_total"
    echo ""
    
    echo "Alert Rules:"
    echo "  - BMADAPIDown (Critical)"
    echo "  - BMADAPIHighErrorRate (Warning)"
    echo "  - BMADAPIHighResponseTime (Warning)"
    echo "  - BMADAPIHighCPUUsage (Warning)"
    echo "  - BMADAPIHighMemoryUsage (Warning)"
    echo "  - BMADAPIWorkflowFailures (Warning)"
    echo "  - BMADAPIDatabaseConnectionIssues (Critical)"
    echo "  - BMADAPIExpansionPackIssues (Warning)"
    echo ""
    
    echo "Useful Commands:"
    echo "  kubectl get servicemonitor bmad-api-monitor -n $NAMESPACE_PROD"
    echo "  kubectl get prometheusrule bmad-api-alerts -n $NAMESPACE_PROD"
    echo "  kubectl get configmap bmad-api-dashboard -n $NAMESPACE_PROD"
    echo "  kubectl port-forward -n $NAMESPACE_PROD service/bmad-api-metrics 8080:8001"
    echo "  curl http://localhost:8080/bmad/metrics"
    echo ""
}

cleanup_monitoring() {
    log_info "Cleaning up monitoring configuration..."
    
    kubectl delete -f "$MONITORING_FILE" || true
    log_success "Monitoring configuration cleaned up"
}

show_help() {
    echo "BMAD API Monitoring Setup Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup      Set up monitoring and alerting"
    echo "  verify     Verify monitoring setup"
    echo "  info       Show monitoring information"
    echo "  cleanup    Remove monitoring configuration"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup"
    echo "  $0 verify"
    echo "  $0 info"
}

# Main script logic
main() {
    local command=${1:-help}
    
    case $command in
        setup)
            check_prerequisites
            setup_monitoring
            verify_monitoring
            show_monitoring_info
            ;;
        verify)
            verify_monitoring
            show_monitoring_info
            ;;
        info)
            show_monitoring_info
            ;;
        cleanup)
            cleanup_monitoring
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
