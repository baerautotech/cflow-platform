# BMAD API Enhanced Monitoring & Alerting Guide

## Overview

This guide covers the comprehensive monitoring and alerting system for the BMAD API service, including Supabase integration, provider router monitoring, performance optimization tracking, and advanced analytics.

## 🚀 **Enhanced Monitoring Features**

### **Core Monitoring**
- **API Health Status**: Real-time service availability
- **Request Rate & Error Rate**: Traffic and error monitoring
- **Response Time**: Performance metrics with percentiles
- **Resource Usage**: CPU and memory monitoring

### **Supabase Integration Monitoring**
- **Connection Status**: Real-time Supabase connectivity
- **Task Operations**: Create, update, delete operations tracking
- **Operation Latency**: Database operation performance
- **Connection Failures**: Database connectivity issues

### **Provider Router Monitoring**
- **Router Status**: Multi-provider routing health
- **Provider Performance**: Individual provider metrics (OpenAI, Anthropic, Azure)
- **Response Latency**: Provider-specific response times
- **Failover Tracking**: Provider switching and failures

### **Performance Optimization Monitoring**
- **Cache Hit Rate**: Caching effectiveness
- **Circuit Breaker Status**: Circuit breaker state monitoring
- **Rate Limiting**: Rate limit enforcement tracking
- **Connection Pooling**: Connection pool utilization

### **Advanced Analytics**
- **User Activity**: Active users and request patterns
- **Workflow Executions**: BMAD workflow performance
- **Expansion Pack Activity**: Installation and activation tracking
- **Analytics Processing**: Event processing and failures

## 📊 **Grafana Dashboard**

### **Dashboard Panels**

#### **Status Overview (Row 1)**
1. **BMAD API Health Status** - Service availability indicator
2. **Supabase Connection Status** - Database connectivity
3. **Provider Router Status** - Multi-provider routing health
4. **Circuit Breaker Status** - Circuit breaker state

#### **Performance Metrics (Row 2)**
5. **Request Rate** - API requests per second
6. **Error Rate** - Error percentage
7. **Cache Hit Rate** - Caching effectiveness

#### **Response Times (Row 3)**
8. **Response Time** - API response time percentiles
9. **Supabase Operation Latency** - Database operation times

#### **Resource Usage (Row 4)**
10. **CPU Usage** - Container CPU utilization
11. **Memory Usage** - Container memory consumption
12. **Workflow Executions** - Workflow success/failure rates

#### **Operations Tracking (Row 5)**
13. **Supabase Task Operations** - Task CRUD operations
14. **Provider Performance** - Individual provider metrics

#### **User & Business Metrics (Row 6)**
15. **User Activity** - Active users and request patterns
16. **Expansion Pack Activity** - Installation and activation

#### **System Health (Row 7)**
17. **Analytics Processing** - Event processing metrics
18. **Rate Limiting** - Rate limit enforcement

## 🚨 **Alert Rules**

### **Critical Alerts**
- **BMADAPIDown**: Service unavailable for >5 minutes
- **BMADAPISupabaseConnectionIssues**: Database connection failures >5/min
- **BMADAPICircuitBreakerOpen**: Circuit breaker open for >5 minutes

### **Warning Alerts**
- **BMADAPIHighErrorRate**: Error rate >5% for >5 minutes
- **BMADAPIHighResponseTime**: Response time >2s for >5 minutes
- **BMADAPIHighCPUUsage**: CPU usage >80% for >10 minutes
- **BMADAPIHighMemoryUsage**: Memory usage >90% for >10 minutes
- **BMADAPIWorkflowFailures**: Workflow failure rate >10% for >5 minutes
- **BMADAPIWorkflowSlowExecution**: Workflow execution >30s for >5 minutes
- **BMADAPISupabaseTaskCreationFailures**: Task creation failures >3/min
- **BMADAPISupabaseHighLatency**: Supabase operations >1s for >5 minutes
- **BMADAPIProviderRouterFailures**: Provider router failures >5/min
- **BMADAPIProviderHighLatency**: Provider responses >5s for >5 minutes
- **BMADAPICacheHitRateLow**: Cache hit rate <70% for >10 minutes
- **BMADAPIRateLimitExceeded**: Rate limit exceeded >10 times/min
- **BMADAPIAnalyticsProcessingFailures**: Analytics failures >3/min
- **BMADAPIUserActivityDrop**: User activity drop >50% vs previous hour
- **BMADAPIExpansionPackIssues**: Expansion pack failures >3/min
- **BMADAPIExpansionPackActivationFailures**: Activation failures >2/min

## 🛠️ **Setup Instructions**

### **Prerequisites**
- Kubernetes cluster with Prometheus Operator installed
- Grafana deployment (optional but recommended)
- kubectl configured and connected to cluster

### **Installation**

1. **Run the enhanced monitoring setup script:**
   ```bash
   ./scripts/setup-bmad-enhanced-monitoring.sh setup
   ```

2. **Verify the installation:**
   ```bash
   ./scripts/setup-bmad-enhanced-monitoring.sh verify
   ```

3. **View monitoring information:**
   ```bash
   ./scripts/setup-bmad-enhanced-monitoring.sh info
   ```

### **Manual Installation**

1. **Apply monitoring configuration:**
   ```bash
   kubectl apply -f infrastructure/kubernetes/bmad-api-enhanced-monitoring.yaml
   ```

2. **Apply dashboard configuration:**
   ```bash
   kubectl apply -f infrastructure/kubernetes/bmad-api-enhanced-dashboard.yaml
   ```

3. **Verify resources:**
   ```bash
   kubectl get servicemonitor bmad-api-enhanced-monitor -n cerebral-production
   kubectl get prometheusrule bmad-api-enhanced-alerts -n cerebral-production
   kubectl get configmap bmad-api-enhanced-dashboard -n cerebral-production
   ```

## 📈 **Metrics Reference**

### **API Metrics**
- `bmad_api_requests_total` - Total API requests
- `bmad_api_errors_total` - Total API errors
- `bmad_api_request_duration_seconds` - Request duration histogram

### **Supabase Metrics**
- `bmad_supabase_connection_status` - Connection status (0/1)
- `bmad_supabase_task_creations_total` - Task creation counter
- `bmad_supabase_task_updates_total` - Task update counter
- `bmad_supabase_task_deletions_total` - Task deletion counter
- `bmad_supabase_operation_duration_seconds` - Operation duration histogram

### **Provider Metrics**
- `bmad_provider_router_status` - Router status (0/1)
- `bmad_provider_openai_requests_total` - OpenAI request counter
- `bmad_provider_anthropic_requests_total` - Anthropic request counter
- `bmad_provider_azure_requests_total` - Azure request counter
- `bmad_provider_response_duration_seconds` - Provider response duration

### **Performance Metrics**
- `bmad_cache_hits_total` - Cache hit counter
- `bmad_cache_requests_total` - Cache request counter
- `bmad_circuit_breaker_state` - Circuit breaker state (0=closed, 1=open, 2=half-open)
- `bmad_rate_limit_exceeded_total` - Rate limit exceeded counter

### **Workflow Metrics**
- `bmad_workflow_executions_total` - Workflow execution counter
- `bmad_workflow_failures_total` - Workflow failure counter
- `bmad_workflow_duration_seconds` - Workflow duration histogram

### **User Metrics**
- `bmad_user_requests_total` - User request counter
- `bmad_active_users_total` - Active users gauge

### **Expansion Pack Metrics**
- `bmad_expansion_pack_installs_total` - Installation counter
- `bmad_expansion_pack_activations_total` - Activation counter
- `bmad_expansion_pack_failures_total` - Failure counter

### **Analytics Metrics**
- `bmad_analytics_events_processed_total` - Events processed counter
- `bmad_analytics_processing_failures_total` - Processing failure counter

## 🔧 **Troubleshooting**

### **Common Issues**

1. **Metrics endpoint not accessible:**
   ```bash
   kubectl port-forward -n cerebral-production service/bmad-api-metrics 8080:8001
   curl http://localhost:8080/bmad/metrics
   ```

2. **ServiceMonitor not working:**
   ```bash
   kubectl get servicemonitor bmad-api-enhanced-monitor -n cerebral-production -o yaml
   kubectl describe servicemonitor bmad-api-enhanced-monitor -n cerebral-production
   ```

3. **Prometheus targets not showing:**
   - Check if Prometheus Operator is installed
   - Verify ServiceMonitor labels match service labels
   - Check Prometheus configuration

4. **Alerts not firing:**
   ```bash
   kubectl get prometheusrule bmad-api-enhanced-alerts -n cerebral-production -o yaml
   ```

5. **Dashboard not importing:**
   - Verify ConfigMap exists and has correct JSON
   - Check Grafana permissions
   - Validate JSON format

### **Useful Commands**

```bash
# Check monitoring resources
kubectl get servicemonitor,prometheusrule,configmap -n cerebral-production | grep bmad

# View metrics
kubectl port-forward -n cerebral-production service/bmad-api-metrics 8080:8001
curl http://localhost:8080/bmad/metrics

# Check health
curl http://localhost:8080/bmad/health

# View logs
kubectl logs -n cerebral-production deployment/bmad-api-production -f

# Check Prometheus targets
kubectl port-forward -n monitoring service/prometheus-operated 9090:9090
# Then visit http://localhost:9090/targets
```

## 📚 **Additional Resources**

- [Prometheus Operator Documentation](https://prometheus-operator.dev/)
- [Grafana Dashboard Import Guide](https://grafana.com/docs/grafana/latest/dashboards/import-dashboard/)
- [Kubernetes Monitoring Best Practices](https://kubernetes.io/docs/tasks/debug-application-cluster/resource-usage-monitoring/)

## 🆘 **Support**

For monitoring issues:
1. Check the troubleshooting section above
2. Verify all prerequisites are met
3. Review logs for specific error messages
4. Contact the development team with specific error details
