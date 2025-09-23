#!/bin/bash
set -euo pipefail

# Grafana Dashboard Setup Script
# This script sets up automatic dashboard provisioning for Grafana

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE_MONITORING="monitoring"
NAMESPACE_PROD="cerebral-production"
GRAFANA_URL="https://grafana.dev.cerebral.baerautotech.com"

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
        log_info "Please configure kubectl to connect to your cluster"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

setup_dashboard_provisioning() {
    log_info "Setting up Grafana dashboard provisioning..."
    
    # Apply dashboard provisioning configuration
    kubectl apply -f infrastructure/kubernetes/grafana-dashboard-provisioning.yaml
    
    log_success "Dashboard provisioning configuration applied"
    
    # Verify ConfigMaps
    if kubectl get configmap grafana-dashboard-provisioning -n $NAMESPACE_MONITORING &> /dev/null; then
        log_success "Dashboard provisioning ConfigMap created"
    else
        log_error "Dashboard provisioning ConfigMap creation failed"
        exit 1
    fi
    
    if kubectl get configmap bmad-dashboard-enhanced -n $NAMESPACE_MONITORING &> /dev/null; then
        log_success "BMAD dashboard ConfigMap created"
    else
        log_error "BMAD dashboard ConfigMap creation failed"
        exit 1
    fi
}

restart_grafana() {
    log_info "Restarting Grafana to apply dashboard provisioning..."
    
    # Restart Grafana deployment
    kubectl rollout restart deployment/grafana -n $NAMESPACE_MONITORING
    
    # Wait for rollout to complete
    kubectl rollout status deployment/grafana -n $NAMESPACE_MONITORING --timeout=300s
    
    log_success "Grafana restarted successfully"
}

verify_dashboard_provisioning() {
    log_info "Verifying dashboard provisioning..."
    
    # Check if Grafana is running
    if kubectl get pods -n $NAMESPACE_MONITORING -l app.kubernetes.io/name=grafana | grep -q Running; then
        log_success "Grafana is running"
    else
        log_warning "Grafana may not be running or accessible"
    fi
    
    # Check ConfigMaps
    local configmap_count=$(kubectl get configmap -n $NAMESPACE_MONITORING | grep -c dashboard || true)
    log_info "Found $configmap_count dashboard ConfigMaps in monitoring namespace"
    
    # Check if BMAD API is running
    if kubectl get pods -n $NAMESPACE_PROD -l app=bmad-api-production | grep -q Running; then
        log_success "BMAD API is running"
    else
        log_warning "BMAD API may not be running"
    fi
}

show_access_instructions() {
    log_info "Dashboard Access Instructions"
    echo "=============================="
    echo ""
    echo "1. Access Grafana:"
    echo "   $GRAFANA_URL"
    echo ""
    echo "2. Login with your credentials (admin/developer)"
    echo ""
    echo "3. Navigate to Dashboards (left sidebar)"
    echo ""
    echo "4. Look for the 'BMAD Monitoring' folder"
    echo ""
    echo "5. You should see:"
    echo "   - BMAD API Enhanced Production Dashboard"
    echo "   - Any other dashboards in the folder"
    echo ""
    echo "6. If dashboards don't appear:"
    echo "   - Check that Prometheus is scraping BMAD API metrics"
    echo "   - Verify the data source is configured correctly"
    echo "   - Check Grafana logs for any errors"
    echo ""
    echo "📋 Troubleshooting Commands:"
    echo "   kubectl logs -n monitoring deployment/grafana"
    echo "   kubectl get configmap -n monitoring | grep dashboard"
    echo "   kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana"
    echo ""
}

check_grafana_connectivity() {
    log_info "Checking Grafana connectivity..."
    
    # Try to access Grafana health endpoint
    if curl -f -s "$GRAFANA_URL/api/health" &> /dev/null; then
        log_success "Grafana is accessible at: $GRAFANA_URL"
    else
        log_warning "Cannot access Grafana at: $GRAFANA_URL"
        log_info "This may be normal if Grafana is not exposed externally"
    fi
}

manual_import_fallback() {
    log_info "Setting up manual import fallback..."
    
    # Extract dashboard JSON for manual import
    kubectl get configmap bmad-dashboard-enhanced -n $NAMESPACE_MONITORING -o jsonpath='{.data.bmad-enhanced\.json}' > bmad-dashboard-manual.json
    
    log_success "Dashboard JSON extracted to: bmad-dashboard-manual.json"
    log_info "You can manually import this dashboard if automatic provisioning doesn't work"
    
    echo ""
    echo "Manual Import Steps:"
    echo "1. Go to $GRAFANA_URL"
    echo "2. Login and go to Dashboards > Import"
    echo "3. Copy the content of bmad-dashboard-manual.json"
    echo "4. Paste into the 'Import via panel json' text area"
    echo "5. Click Load and then Import"
    echo ""
}

main() {
    local command=${1:-setup}
    
    case $command in
        setup)
            check_prerequisites
            setup_dashboard_provisioning
            restart_grafana
            verify_dashboard_provisioning
            check_grafana_connectivity
            show_access_instructions
            manual_import_fallback
            ;;
        verify)
            verify_dashboard_provisioning
            check_grafana_connectivity
            ;;
        restart)
            restart_grafana
            ;;
        manual)
            manual_import_fallback
            ;;
        help|--help|-h)
            echo "Grafana Dashboard Setup Script"
            echo ""
            echo "Usage: $0 [COMMAND]"
            echo ""
            echo "Commands:"
            echo "  setup      Set up automatic dashboard provisioning (default)"
            echo "  verify     Verify dashboard provisioning setup"
            echo "  restart    Restart Grafana to apply changes"
            echo "  manual     Extract dashboard JSON for manual import"
            echo "  help       Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 setup"
            echo "  $0 verify"
            echo "  $0 manual"
            ;;
        *)
            log_error "Unknown command: $command"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
