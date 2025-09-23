#!/bin/bash
set -euo pipefail

# Grafana Dashboard Import Helper Script
# This script helps extract dashboard JSON from ConfigMaps and provides import instructions

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
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

extract_dashboard_json() {
    local configmap_name=$1
    local output_file=$2
    
    log_info "Extracting dashboard JSON from ConfigMap: $configmap_name"
    
    # Try to get the ConfigMap (this will work if kubectl is configured)
    if kubectl get configmap "$configmap_name" -n "$NAMESPACE_PROD" &> /dev/null; then
        kubectl get configmap "$configmap_name" -n "$NAMESPACE_PROD" -o jsonpath='{.data.dashboard\.json}' > "$output_file"
        log_success "Dashboard JSON extracted to: $output_file"
    else
        log_warning "Cannot access ConfigMap via kubectl. Creating template file instead."
        create_template_dashboard "$output_file"
    fi
}

create_template_dashboard() {
    local output_file=$1
    
    cat > "$output_file" << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "BMAD API Enhanced Production Dashboard",
    "tags": ["bmad", "api", "production", "enhanced"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "BMAD API Health Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"bmad-api-production\"}",
            "legendFormat": "API Status"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "mappings": [
              {
                "options": {
                  "0": {"text": "DOWN"},
                  "1": {"text": "UP"}
                },
                "type": "value"
              }
            ],
            "color": {"mode": "thresholds"},
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "green", "value": 1}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(bmad_api_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 6, "y": 0}
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(bmad_api_errors_total[5m]) / rate(bmad_api_requests_total[5m]) * 100",
            "legendFormat": "Error Rate %"
          }
        ],
        "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0}
      }
    ],
    "time": {"from": "now-1h", "to": "now"},
    "refresh": "30s"
  }
}
EOF
    
    log_success "Template dashboard created at: $output_file"
}

show_import_instructions() {
    log_info "Grafana Dashboard Import Instructions"
    echo "=========================================="
    echo ""
    echo "1. Open Grafana in your browser:"
    echo "   $GRAFANA_URL"
    echo ""
    echo "2. Login with your admin/developer credentials"
    echo ""
    echo "3. Navigate to Dashboards > Import"
    echo ""
    echo "4. Copy the JSON content from the dashboard file:"
    echo "   cat bmad-enhanced-dashboard.json"
    echo ""
    echo "5. Paste the JSON into the 'Import via panel json' text area"
    echo ""
    echo "6. Click 'Load' to preview the dashboard"
    echo ""
    echo "7. Configure the data source if prompted:"
    echo "   - Select your Prometheus data source"
    echo "   - Ensure it's configured to scrape the BMAD API metrics"
    echo ""
    echo "8. Click 'Import' to create the dashboard"
    echo ""
    echo "9. The dashboard will be available to all users with appropriate permissions"
    echo ""
    echo "📋 Additional Dashboards Available:"
    echo "   - bmad-enhanced-dashboard.json (18 panels)"
    echo "   - bmad-basic-dashboard.json (8 panels)"
    echo ""
}

check_grafana_access() {
    log_info "Checking Grafana accessibility..."
    
    if curl -f -s "$GRAFANA_URL/api/health" &> /dev/null; then
        log_success "Grafana is accessible at: $GRAFANA_URL"
    else
        log_warning "Cannot access Grafana at: $GRAFANA_URL"
        log_info "Please verify the URL and ensure Grafana is running"
    fi
}

main() {
    local command=${1:-help}
    
    case $command in
        extract)
            extract_dashboard_json "bmad-api-enhanced-dashboard" "bmad-enhanced-dashboard.json"
            extract_dashboard_json "bmad-api-dashboard" "bmad-basic-dashboard.json"
            show_import_instructions
            ;;
        instructions)
            show_import_instructions
            ;;
        check)
            check_grafana_access
            ;;
        help|--help|-h)
            echo "Grafana Dashboard Import Helper"
            echo ""
            echo "Usage: $0 [COMMAND]"
            echo ""
            echo "Commands:"
            echo "  extract      Extract dashboard JSON from ConfigMaps"
            echo "  instructions Show import instructions"
            echo "  check        Check Grafana accessibility"
            echo "  help         Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 extract"
            echo "  $0 instructions"
            echo "  $0 check"
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
