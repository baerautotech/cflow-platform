# Cerebral Platform Pod Framework

Document version: 1.0  
Date: 2025-09-20  
Purpose: Comprehensive framework for consistent pod deployment across all cerebral platform services

## 🎯 **Overview**

The Cerebral Platform Pod Framework provides a standardized, scalable approach to deploying Kubernetes pods across multiple environments. It supports **4 deployment variations** (development → enterprise production) and **10+ services** with consistent configuration patterns.

## 🏗️ **Architecture**

### **Framework Components**

1. **Pod Framework Configuration** (`infrastructure/framework/pod-framework.yaml`)
   - Environment-specific configurations
   - Common labels and annotations
   - Base templates for all Kubernetes resources

2. **Service Definitions** (`infrastructure/framework/services.yaml`)
   - Service-specific configurations
   - Component and tier classifications
   - Environment variables and secrets

3. **Pod Generator** (`scripts/generate-pod-simple.py`)
   - Python-based manifest generator
   - Template-free direct YAML generation
   - Environment-aware configuration

4. **Deployment Scripts**
   - `scripts/generate-all-services.sh` - Bulk generation
   - `scripts/deploy-all-services.sh` - Automated deployment

## 📋 **Supported Services**

### **Core Services**
1. **WebMCP Server** - Master Tool Pattern implementation
2. **BMAD HTTP API Facade** - Agent orchestration
3. **KnowledgeRAG Service** - Supabase + pgvector
4. **Provider Router Service** - LLM API routing
5. **Expansion Pack Manager** - Dynamic pack loading

### **Workflow Services**
6. **HIL Session Manager** - Human-in-the-Loop
7. **Workflow Orchestrator** - BMAD workflow engine
8. **Document Approval Service** - Approval workflows
9. **Project Type Detector** - Greenfield vs Brownfield
10. **Monitoring & Metrics Service** - Observability

## 🌍 **Environment Variations**

### **Development**
- **Replicas**: 1
- **Resources**: 256Mi/100m → 512Mi/250m
- **Security**: Relaxed (non-root, privilege escalation allowed)
- **Monitoring**: Disabled
- **Ingress**: Disabled
- **HPA**: Disabled
- **Secrets**: Basic integration only

### **Staging**
- **Replicas**: 2
- **Resources**: 512Mi/250m → 1Gi/500m
- **Security**: Moderate (non-root, no privilege escalation)
- **Monitoring**: Enabled
- **Ingress**: Enabled with TLS
- **HPA**: Enabled (2-5 replicas)
- **Secrets**: Full integration (Vault + Supabase)

### **Production**
- **Replicas**: 3
- **Resources**: 1Gi/500m → 2Gi/1000m
- **Security**: Strict (non-root, read-only filesystem)
- **Monitoring**: Enabled
- **Ingress**: Enabled with TLS
- **HPA**: Enabled (3-10 replicas)
- **Secrets**: Full integration

### **Enterprise**
- **Replicas**: 5
- **Resources**: 2Gi/1000m → 4Gi/2000m
- **Security**: Maximum (non-root, read-only, seccomp)
- **Monitoring**: Enhanced with detailed metrics
- **Ingress**: Enabled with TLS and rate limiting
- **HPA**: Enabled (5-20 replicas)
- **Secrets**: Full integration + enterprise secrets

## 🚀 **Usage**

### **Generate Single Service**
```bash
# Generate BMAD API for development
python3 scripts/generate-pod-simple.py bmad-api development

# Generate WebMCP for production
python3 scripts/generate-pod-simple.py webmcp production
```

### **Generate Multiple Services**
```bash
# Generate all services for development
./scripts/generate-all-services.sh -e development -s all

# Generate specific services for multiple environments
./scripts/generate-all-services.sh -e development,staging,production -s webmcp,bmad-api,knowledge-rag
```

### **Deploy Services**
```bash
# Deploy all services to development
./scripts/deploy-all-services.sh -e development -s all

# Deploy specific services to production
./scripts/deploy-all-services.sh -e production -s webmcp,bmad-api
```

## 📊 **Generated Resources**

Each service generates the following Kubernetes resources:

### **Core Resources**
- **Deployment** - Main application pods
- **Service** - Internal cluster communication
- **ServiceAccount** - Pod identity
- **ConfigMap** - Configuration data
- **Secret** - Sensitive data (empty, filled by deployment)

### **Environment-Specific Resources**
- **HorizontalPodAutoscaler** - Auto-scaling (staging+)
- **Ingress** - External access (staging+)

## 🔧 **Configuration**

### **Service Configuration**
```yaml
# Example from services.yaml
bmad-api:
  component: "api"
  tier: "backend"
  port: 8001
  image: "bmad-api"
  description: "BMAD HTTP API Facade for agent orchestration"
  health_path: "/health"
  env:
    BMAD_API_HOST: "0.0.0.0"
    BMAD_API_PORT: "8001"
    BMAD_LOG_LEVEL: "info"
  secrets:
    SUPABASE_URL: "supabase-url"
    SUPABASE_ANON_KEY: "supabase-anon-key"
    VAULT_URL: "vault-url"
    VAULT_TOKEN: "vault-token"
```

### **Environment Configuration**
```yaml
# Example from pod-framework.yaml
production:
  replicas: 3
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1000m"
  security:
    runAsNonRoot: true
    allowPrivilegeEscalation: false
    readOnlyRootFilesystem: true
  monitoring:
    enabled: true
  ingress:
    enabled: true
    tls: true
  hpa:
    enabled: true
    min_replicas: 3
    max_replicas: 10
```

## 🏷️ **Labels and Annotations**

### **Standard Labels**
- `app: <service-name>`
- `version: 1.0.0`
- `component: <component-type>`
- `tier: <tier-level>`
- `environment: <environment>`
- `app.kubernetes.io/managed-by: cerebral-platform`
- `app.kubernetes.io/part-of: cerebral-cluster`

### **Standard Annotations**
- `cerebral.baerautotech.com/created-by: pod-framework`
- `cerebral.baerautotech.com/framework-version: 1.0.0`
- `cerebral.baerautotech.com/last-updated: <timestamp>`

## 🔒 **Security Features**

### **Pod Security Context**
- **Non-root execution** (staging+)
- **No privilege escalation** (staging+)
- **Read-only root filesystem** (production+)
- **Seccomp profile** (enterprise)

### **Resource Limits**
- **CPU limits** prevent resource exhaustion
- **Memory limits** prevent OOM kills
- **Volume size limits** prevent disk exhaustion

### **Network Security**
- **TLS termination** at ingress (staging+)
- **Rate limiting** (enterprise)
- **Internal service communication** only

## 📈 **Monitoring and Observability**

### **Health Checks**
- **Liveness probe** - Restart unhealthy pods
- **Readiness probe** - Route traffic to ready pods
- **Health endpoints** - `/health` for all services

### **Metrics Collection**
- **Prometheus scraping** (staging+)
- **Resource metrics** (CPU, memory)
- **Custom application metrics**

### **Logging**
- **Structured logging** with service identification
- **Centralized log collection** via volumes
- **Log retention** policies per environment

## 🚀 **Deployment Process**

### **SHA-Based Images**
- All images tagged with Git SHA
- No `latest` or `dev` tags allowed
- Immutable deployments

### **Rolling Updates**
- Zero-downtime deployments
- Configurable rollout strategies
- Automatic rollback on failure

### **Health Validation**
- Post-deployment health checks
- Service endpoint validation
- Master Tool Pattern verification

## 📚 **Best Practices**

### **Service Development**
1. **Define service in `services.yaml`** before generation
2. **Use consistent naming** (kebab-case)
3. **Include health endpoints** (`/health`)
4. **Configure appropriate resources** per environment

### **Deployment**
1. **Test in development** before staging
2. **Use dry-run mode** for validation
3. **Monitor deployments** for issues
4. **Validate health checks** post-deployment

### **Maintenance**
1. **Update framework version** for changes
2. **Review resource limits** regularly
3. **Monitor HPA behavior** in production
4. **Rotate secrets** per security policy

## 🔄 **Framework Evolution**

### **Version 1.0.0** (Current)
- Basic pod generation
- 4 environment variations
- 10 service definitions
- SHA-based deployments

### **Future Enhancements**
- **Helm chart integration**
- **ArgoCD deployment**
- **Service mesh integration**
- **Advanced monitoring**

## 📞 **Support**

For questions or issues with the pod framework:
1. Check generated manifests for correctness
2. Validate service definitions in `services.yaml`
3. Review environment configurations
4. Test with dry-run mode first

---

**Framework Version**: 1.0.0  
**Last Updated**: 2025-09-20  
**Maintainer**: Cerebral Platform Architecture Team
