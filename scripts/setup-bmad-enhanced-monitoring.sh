#!/bin/bash
set -euo pipefail

# BMAD API Enhanced Monitoring Setup Script
# Sets up comprehensive monitoring and alerting for BMAD API service with Supabase integration

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE_PROD="cerebral-production"
MONITORING_FILE="infrastructure/kubernetes/bmad-api-enhanced-monitoring.yaml"
DASHBOARD_FILE="infrastructure/kubernetes/bmad-api-enhanced-dashboard.yaml"
LEGACY_MONITORING_FILE="infrastructure/kubernetes/bmad-api-monitoring.yaml"

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

log_enhanced() {
    echo -e "${PURPLE}🚀 $1${NC}"
}

check_prerequisites() {
    log_info "Checking enhanced monitoring prerequisites..."
    
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
    
    # Check if Grafana is available
    if ! kubectl get deployment grafana -n monitoring &> /dev/null; then
        log_warning "Grafana deployment not found in monitoring namespace"
        log_info "Dashboard will be created but may not be automatically imported"
    fi
    
    # Check if we can connect to the cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

cleanup_legacy_monitoring() {
    log_info "Cleaning up legacy monitoring configuration..."
    
    if [ -f "$LEGACY_MONITORING_FILE" ]; then
        kubectl delete -f "$LEGACY_MONITORING_FILE" || true
        log_success "Legacy monitoring configuration cleaned up"
    else
        log_info "No legacy monitoring configuration found"
    fi
}

setup_enhanced_monitoring() {
    log_enhanced "Setting up BMAD API enhanced monitoring..."
    
    # Validate monitoring files
    if [ ! -f "$MONITORING_FILE" ]; then
        log_error "Enhanced monitoring configuration file not found: $MONITORING_FILE"
        exit 1
    fi
    
    if [ ! -f "$DASHBOARD_FILE" ]; then
        log_error "Enhanced dashboard configuration file not found: $DASHBOARD_FILE"
        exit 1
    fi
    
    # Apply enhanced monitoring configuration
    kubectl apply -f "$MONITORING_FILE"
    log_success "Applied enhanced monitoring configuration"
    
    # Apply enhanced dashboard configuration
    kubectl apply -f "$DASHBOARD_FILE"
    log_success "Applied enhanced dashboard configuration"
    
    # Verify ServiceMonitor
    if kubectl get servicemonitor bmad-api-enhanced-monitor -n $NAMESPACE_PROD &> /dev/null; then
        log_success "Enhanced ServiceMonitor created successfully"
    else
        log_error "Enhanced ServiceMonitor creation failed"
        exit 1
    fi
    
    # Verify PrometheusRule
    if kubectl get prometheusrule bmad-api-enhanced-alerts -n $NAMESPACE_PROD &> /dev/null; then
        log_success "Enhanced PrometheusRule created successfully"
    else
        log_error "Enhanced PrometheusRule creation failed"
        exit 1
    fi
    
    # Verify Dashboard ConfigMap
    if kubectl get configmap bmad-api-enhanced-dashboard -n $NAMESPACE_PROD &> /dev/null; then
        log_success "Enhanced Dashboard ConfigMap created successfully"
    else
        log_error "Enhanced Dashboard ConfigMap creation failed"
        exit 1
    fi
}

verify_enhanced_monitoring() {
    log_info "Verifying enhanced monitoring setup..."
    
    # Check if metrics endpoint is accessible
    log_info "Checking enhanced metrics endpoint..."
    kubectl port-forward -n $NAMESPACE_PROD service/bmad-api-metrics 8080:8001 &
    local port_forward_pid=$!
    
    sleep 5
    
    if curl -f http://localhost:8080/bmad/metrics &> /dev/null; then
        log_success "Enhanced metrics endpoint is accessible"
    else
        log_warning "Enhanced metrics endpoint test failed"
    fi
    
    if curl -f http://localhost:8080/bmad/health &> /dev/null; then
        log_success "Health endpoint is accessible"
    else
        log_warning "Health endpoint test failed"
    fi
    
    kill $port_forward_pid 2>/dev/null || true
    
    # Check Prometheus targets
    log_info "Checking enhanced Prometheus targets..."
    if kubectl get servicemonitor bmad-api-enhanced-monitor -n $NAMESPACE_PROD -o yaml | grep -q "bmad-api-production"; then
        log_success "Enhanced ServiceMonitor configuration is correct"
    else
        log_warning "Enhanced ServiceMonitor configuration might be incorrect"
    fi
    
    # Check alert rules
    log_info "Checking enhanced alert rules..."
    local alert_count=$(kubectl get prometheusrule bmad-api-enhanced-alerts -n $NAMESPACE_PROD -o yaml | grep -c "alert:")
    log_info "Found $alert_count enhanced alert rules"
    
    if [ "$alert_count" -ge 15 ]; then
        log_success "Enhanced alert rules are properly configured"
    else
        log_warning "Enhanced alert rules might be incomplete"
    fi
    
    # Check dashboard
    log_info "Checking enhanced dashboard..."
    if kubectl get configmap bmad-api-enhanced-dashboard -n $NAMESPACE_PROD &> /dev/null; then
        log_success "Enhanced dashboard ConfigMap is available"
    else
        log_warning "Enhanced dashboard ConfigMap not found"
    fi
}

show_enhanced_monitoring_info() {
    log_enhanced "Enhanced Monitoring Setup Information:"
    echo "=============================================="
    echo "ServiceMonitor: bmad-api-enhanced-monitor"
    echo "PrometheusRule: bmad-api-enhanced-alerts"
    echo "Dashboard ConfigMap: bmad-api-enhanced-dashboard"
    echo "Metrics Service: bmad-api-metrics"
    echo ""
    
    echo "Enhanced Metrics Available:"
    echo "  - bmad_api_requests_total"
    echo "  - bmad_api_errors_total"
    echo "  - bmad_api_request_duration_seconds"
    echo "  - bmad_workflow_executions_total"
    echo "  - bmad_workflow_failures_total"
    echo "  - bmad_supabase_connection_status"
    echo "  - bmad_supabase_task_creations_total"
    echo "  - bmad_supabase_task_updates_total"
    echo "  - bmad_supabase_task_deletions_total"
    echo "  - bmad_supabase_operation_duration_seconds"
    echo "  - bmad_provider_router_status"
    echo "  - bmad_provider_response_duration_seconds"
    echo "  - bmad_cache_hits_total"
    echo "  - bmad_cache_requests_total"
    echo "  - bmad_circuit_breaker_state"
    echo "  - bmad_rate_limit_exceeded_total"
    echo "  - bmad_analytics_events_processed_total"
    echo "  - bmad_user_requests_total"
    echo "  - bmad_active_users_total"
    echo ""
    
    echo "Enhanced Alert Rules:"
    echo "  - BMADAPIDown (Critical)"
    echo "  - BMADAPIHighErrorRate (Warning)"
    echo "  - BMADAPIHighResponseTime (Warning)"
    echo "  - BMADAPIHighCPUUsage (Warning)"
    echo "  - BMADAPIHighMemoryUsage (Warning)"
    echo "  - BMADAPIWorkflowFailures (Warning)"
    echo "  - BMADAPIWorkflowSlowExecution (Warning)"
    echo "  - BMADAPISupabaseConnectionIssues (Critical)"
    echo "  - BMADAPISupabaseTaskCreationFailures (Warning)"
    echo "  - BMADAPISupabaseHighLatency (Warning)"
    echo "  - BMADAPIProviderRouterFailures (Warning)"
    echo "  - BMADAPIProviderHighLatency (Warning)"
    echo "  - BMADAPICacheHitRateLow (Warning)"
    echo "  - BMADAPICircuitBreakerOpen (Critical)"
    echo "  - BMADAPIRateLimitExceeded (Warning)"
    echo "  - BMADAPIAnalyticsProcessingFailures (Warning)"
    echo "  - BMADAPIUserActivityDrop (Warning)"
    echo "  - BMADAPIExpansionPackIssues (Warning)"
    echo "  - BMADAPIExpansionPackActivationFailures (Warning)"
    echo ""
    
    echo "Dashboard Panels:"
    echo "  - API Health Status"
    echo "  - Supabase Connection Status"
    echo "  - Provider Router Status"
    echo "  - Circuit Breaker Status"
    echo "  - Request Rate & Error Rate"
    echo "  - Cache Hit Rate"
    echo "  - Response Time & Supabase Latency"
    echo "  - CPU & Memory Usage"
    echo "  - Workflow Executions"
    echo "  - Supabase Task Operations"
    echo "  - Provider Performance"
    echo "  - User Activity"
    echo "  - Expansion Pack Activity"
    echo "  - Analytics Processing"
    echo "  - Rate Limiting"
    echo ""
    
    echo "Useful Commands:"
    echo "  kubectl get servicemonitor bmad-api-enhanced-monitor -n $NAMESPACE_PROD"
    echo "  kubectl get prometheusrule bmad-api-enhanced-alerts -n $NAMESPACE_PROD"
    echo "  kubectl get configmap bmad-api-enhanced-dashboard -n $NAMESPACE_PROD"
    echo "  kubectl port-forward -n $NAMESPACE_PROD service/bmad-api-metrics 8080:8001"
    echo "  curl http://localhost:8080/bmad/metrics"
    echo "  curl http://localhost:8080/bmad/health"
    echo ""
    
    echo "Grafana Dashboard Import:"
    echo "  1. Access Grafana at your cluster's Grafana URL"
    echo "  2. Go to Dashboards > Import"
    echo "  3. Copy the JSON from the ConfigMap:"
    echo "     kubectl get configmap bmad-api-enhanced-dashboard -n $NAMESPACE_PROD -o jsonpath='{.data.dashboard\.json}'"
    echo "  4. Paste and import the dashboard"
    echo ""
}

cleanup_enhanced_monitoring() {
    log_info "Cleaning up enhanced monitoring configuration..."
    
    kubectl delete -f "$MONITORING_FILE" || true
    kubectl delete -f "$DASHBOARD_FILE" || true
    log_success "Enhanced monitoring configuration cleaned up"
}

show_help() {
    echo "BMAD API Enhanced Monitoring Setup Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup      Set up enhanced monitoring and alerting"
    echo "  verify     Verify enhanced monitoring setup"
    echo "  info       Show enhanced monitoring information"
    echo "  cleanup    Remove enhanced monitoring configuration"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup"
    echo "  $0 verify"
    echo "  $0 info"
    echo ""
    echo "Features:"
    echo "  - Comprehensive Supabase integration monitoring"
    echo "  - Provider router performance tracking"
    echo "  - Performance optimization metrics (caching, rate limiting, circuit breaking)"
    echo "  - Advanced analytics and business intelligence"
    echo "  - Enhanced Grafana dashboard with 18 panels"
    echo "  - 20+ alert rules covering all aspects of the system"
}

# Main script logic
main() {
    local command=${1:-help}
    
    case $command in
        setup)
            check_prerequisites
            cleanup_legacy_monitoring
            setup_enhanced_monitoring
            verify_enhanced_monitoring
            show_enhanced_monitoring_info
            ;;
        verify)
            verify_enhanced_monitoring
            show_enhanced_monitoring_info
            ;;
        info)
            show_enhanced_monitoring_info
            ;;
        cleanup)
            cleanup_enhanced_monitoring
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
