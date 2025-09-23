# BMAD Enhanced Deployment Guide

## Overview

This guide covers the complete deployment of the enhanced BMAD API service with Supabase integration, performance optimization, advanced analytics, and comprehensive monitoring.

## 🚀 **Deployment Architecture**

### **Components**
- **BMAD API Service**: FastAPI-based service with enhanced capabilities
- **Supabase Integration**: Direct database integration for task management
- **Provider Router**: Multi-provider LLM routing with failover
- **Performance Optimizer**: Caching, rate limiting, and circuit breaking
- **Analytics Engine**: Real-time metrics and business intelligence
- **Monitoring System**: Prometheus metrics and Grafana dashboards

### **Kubernetes Resources**
- **Deployment**: `bmad-api-production`
- **Service**: `bmad-api-service` (port 8000)
- **Metrics Service**: `bmad-api-metrics` (port 8001)
- **ServiceMonitor**: `bmad-api-enhanced-monitor`
- **PrometheusRule**: `bmad-api-enhanced-alerts`
- **ConfigMap**: `bmad-api-enhanced-dashboard`

## 📋 **Prerequisites**

### **Kubernetes Cluster**
- Kubernetes 1.20+
- Prometheus Operator installed
- Grafana deployment (optional but recommended)
- kubectl configured and connected

### **External Services**
- Supabase project with API keys
- LLM provider API keys (OpenAI, Anthropic, Azure)

### **Required Environment Variables**
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

# Provider Configuration
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-key

# Production Configuration
BMAD_PRODUCTION_MODE=true
BMAD_ALLOW_MOCK_MODE=false
```

## 🛠️ **Deployment Steps**

### **Step 1: Deploy BMAD API Service**

1. **Apply the enhanced deployment:**
   ```bash
   kubectl apply -f infrastructure/kubernetes/bmad-api-enhanced-deployment.yaml
   ```

2. **Verify deployment:**
   ```bash
   kubectl get deployment bmad-api-production -n cerebral-production
   kubectl get pods -n cerebral-production -l app=bmad-api-production
   ```

3. **Check service:**
   ```bash
   kubectl get service bmad-api-service -n cerebral-production
   kubectl get service bmad-api-metrics -n cerebral-production
   ```

### **Step 2: Set Up Enhanced Monitoring**

1. **Run the enhanced monitoring setup script:**
   ```bash
   ./scripts/setup-bmad-enhanced-monitoring.sh setup
   ```

2. **Verify monitoring resources:**
   ```bash
   kubectl get servicemonitor bmad-api-enhanced-monitor -n cerebral-production
   kubectl get prometheusrule bmad-api-enhanced-alerts -n cerebral-production
   kubectl get configmap bmad-api-enhanced-dashboard -n cerebral-production
   ```

### **Step 3: Configure Grafana Dashboard**

1. **Access Grafana:**
   ```bash
   kubectl port-forward -n monitoring service/grafana 3000:3000
   ```

2. **Import the dashboard:**
   - Go to http://localhost:3000
   - Navigate to Dashboards > Import
   - Copy the JSON from the ConfigMap:
     ```bash
     kubectl get configmap bmad-api-enhanced-dashboard -n cerebral-production -o jsonpath='{.data.dashboard\.json}'
     ```
   - Paste and import the dashboard

### **Step 4: Verify Deployment**

1. **Check health endpoint:**
   ```bash
   kubectl port-forward -n cerebral-production service/bmad-api-service 8080:8000
   curl http://localhost:8080/bmad/health
   ```

2. **Test metrics endpoint:**
   ```bash
   kubectl port-forward -n cerebral-production service/bmad-api-metrics 8081:8001
   curl http://localhost:8081/bmad/metrics
   ```

3. **Verify Supabase integration:**
   ```bash
   curl http://localhost:8080/bmad/task-management/stats
   ```

## 🔧 **Configuration**

### **Environment Variables**

#### **Required Configuration**
```yaml
env:
- name: SUPABASE_URL
  value: "https://your-project.supabase.co"
- name: SUPABASE_SERVICE_ROLE_KEY
  valueFrom:
    secretKeyRef:
      name: bmad-secrets
      key: supabase-service-role-key
- name: BMAD_PRODUCTION_MODE
  value: "true"
```

#### **Optional Configuration**
```yaml
env:
- name: BMAD_CACHE_TTL
  value: "600"
- name: BMAD_RATE_LIMIT_MAX_CALLS
  value: "100"
- name: BMAD_RATE_LIMIT_PERIOD
  value: "60"
- name: BMAD_CIRCUIT_BREAKER_FAILURE_THRESHOLD
  value: "5"
- name: BMAD_CIRCUIT_BREAKER_RECOVERY_TIMEOUT
  value: "30"
```

### **Secrets Management**

1. **Create secrets:**
   ```bash
   kubectl create secret generic bmad-secrets -n cerebral-production \
     --from-literal=supabase-service-role-key=your-key \
     --from-literal=openai-api-key=your-key \
     --from-literal=anthropic-api-key=your-key \
     --from-literal=azure-openai-api-key=your-key
   ```

2. **Verify secrets:**
   ```bash
   kubectl get secret bmad-secrets -n cerebral-production
   ```

## 📊 **Monitoring & Alerting**

### **Available Metrics**
- **API Metrics**: Requests, errors, response times
- **Supabase Metrics**: Connection status, task operations, latency
- **Provider Metrics**: Router status, response times, failures
- **Performance Metrics**: Cache hit rate, circuit breaker status, rate limiting
- **Workflow Metrics**: Executions, failures, duration
- **User Metrics**: Activity, active users
- **Analytics Metrics**: Event processing, business intelligence

### **Alert Rules**
- **Critical**: Service down, Supabase connection issues, circuit breaker open
- **Warning**: High error rate, slow response times, resource usage, workflow failures

### **Dashboard Panels**
- **Status Overview**: Service health, Supabase status, provider status, circuit breaker
- **Performance**: Request rate, error rate, cache hit rate, response times
- **Resources**: CPU usage, memory usage
- **Operations**: Workflow executions, Supabase operations, provider performance
- **Analytics**: User activity, expansion pack activity, analytics processing

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Deployment Issues**
```bash
# Check deployment status
kubectl describe deployment bmad-api-production -n cerebral-production

# Check pod logs
kubectl logs -n cerebral-production deployment/bmad-api-production -f

# Check service endpoints
kubectl get endpoints bmad-api-service -n cerebral-production
```

#### **Supabase Connection Issues**
```bash
# Check Supabase credentials
kubectl get secret bmad-secrets -n cerebral-production -o yaml

# Test Supabase connection
kubectl port-forward -n cerebral-production service/bmad-api-service 8080:8000
curl http://localhost:8080/bmad/health | jq '.task_management'
```

#### **Monitoring Issues**
```bash
# Check ServiceMonitor
kubectl describe servicemonitor bmad-api-enhanced-monitor -n cerebral-production

# Check Prometheus targets
kubectl port-forward -n monitoring service/prometheus-operated 9090:9090
# Visit http://localhost:9090/targets

# Check alert rules
kubectl get prometheusrule bmad-api-enhanced-alerts -n cerebral-production -o yaml
```

#### **Performance Issues**
```bash
# Check resource usage
kubectl top pods -n cerebral-production

# Check metrics
kubectl port-forward -n cerebral-production service/bmad-api-metrics 8081:8001
curl http://localhost:8081/bmad/metrics | grep bmad_api_request_duration
```

### **Debug Commands**

```bash
# Check all resources
kubectl get all -n cerebral-production -l app=bmad-api-production

# Check ConfigMaps
kubectl get configmap -n cerebral-production | grep bmad

# Check secrets
kubectl get secret -n cerebral-production | grep bmad

# Check events
kubectl get events -n cerebral-production --sort-by='.lastTimestamp'

# Check logs with timestamps
kubectl logs -n cerebral-production deployment/bmad-api-production --timestamps=true
```

## 🔄 **Updates & Maintenance**

### **Updating the Service**

1. **Update deployment:**
   ```bash
   kubectl set image deployment/bmad-api-production \
     bmad-api=ghcr.io/baerautotech/bmad-api:latest \
     -n cerebral-production
   ```

2. **Monitor rollout:**
   ```bash
   kubectl rollout status deployment/bmad-api-production -n cerebral-production
   ```

3. **Rollback if needed:**
   ```bash
   kubectl rollout undo deployment/bmad-api-production -n cerebral-production
   ```

### **Scaling**

1. **Scale horizontally:**
   ```bash
   kubectl scale deployment bmad-api-production --replicas=3 -n cerebral-production
   ```

2. **Check scaling:**
   ```bash
   kubectl get pods -n cerebral-production -l app=bmad-api-production
   ```

### **Backup & Recovery**

1. **Backup configuration:**
   ```bash
   kubectl get configmap bmad-api-enhanced-dashboard -n cerebral-production -o yaml > dashboard-backup.yaml
   kubectl get prometheusrule bmad-api-enhanced-alerts -n cerebral-production -o yaml > alerts-backup.yaml
   ```

2. **Restore configuration:**
   ```bash
   kubectl apply -f dashboard-backup.yaml
   kubectl apply -f alerts-backup.yaml
   ```

## 📚 **Additional Resources**

- [BMAD Enhanced Capabilities User Guide](BMAD_ENHANCED_CAPABILITIES_USER_GUIDE.md)
- [BMAD API Reference](BMAD_API_REFERENCE.md)
- [BMAD Enhanced Monitoring Guide](BMAD_ENHANCED_MONITORING_GUIDE.md)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Prometheus Operator Guide](https://prometheus-operator.dev/)

## 🆘 **Support**

For deployment issues:
1. Check the troubleshooting section above
2. Review logs and metrics
3. Verify all prerequisites are met
4. Contact the development team with specific error details
