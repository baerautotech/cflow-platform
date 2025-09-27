# BMAD Cloud Migration - Architecture Document

## Architecture Overview

**Project Name**: BMAD Cloud Migration  
**Architecture Type**: Service Integration & API Evolution  
**Created By**: BMAD Master Persona (Architect Agent)  
**Date**: 2025-01-09  
**Requires**: PRD.md (BMAD_CLOUD_MIGRATION_PRD.md)  

## Service Integration Strategy

### Current System Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Local Development Environment             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   cflow-        │  │   vendor/       │  │   MCP       │ │
│  │   platform      │  │   bmad/         │  │   Tools     │ │
│  │                 │  │                 │  │             │ │
│  │ • tool_registry │  │ • workflows/    │  │ • bmad_*    │ │
│  │ • handlers/     │  │ • agents/       │  │ • workflow_*│ │
│  │ • direct_client │  │ • templates/    │  │ • persona_* │ │
│  │ • vendor_wrapper│  │ • tasks/        │  │             │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Target Cloud Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Cerebral Cloud Cluster                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   BMAD Core     │  │   BMAD Agents   │  │   BMAD      │ │
│  │   Workflows     │  │   & Personas    │  │   Templates │ │
│  │   Service       │  │   Service       │  │   Service   │ │
│  │                 │  │                 │  │             │ │
│  │ • 6 workflows   │  │ • @bmad-master  │  │ • prd-tmpl  │ │
│  │ • brownfield-*  │  │ • @architect    │  │ • arch-tmpl │ │
│  │ • greenfield-*  │  │ • @pm           │  │ • story-tmpl│ │
│  │ • workflow exec │  │ • @dev          │  │ • task-tmpl │ │
│  └─────────────────┘  │ • @qa           │  └─────────────┘ │
│                       └─────────────────┘                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   MCP Router    │  │   Session       │  │   Production│ │
│  │   Service       │  │   Manager       │  │   Gate      │ │
│  │                 │  │   Service       │  │   Service   │ │
│  │ • tool routing  │  │ • Supabase      │  │ • validation│ │
│  │ • API gateway   │  │ • session state │  │ • enforcement│ │
│  │ • load balancer │  │ • persistence   │  │ • logging   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## API Evolution Planning

### Current MCP Tool Contracts
```python
# Existing tool contracts (maintained for backward compatibility)
bmad_workflow_discover() -> Dict[str, Any]
bmad_workflow_start(workflow_id, project_path, project_context) -> Dict[str, Any]
bmad_workflow_next(project_id) -> Dict[str, Any]
bmad_workflow_status(project_id) -> Dict[str, Any]
bmad_workflow_execute_step(session_id, step_result) -> Dict[str, Any]
```

### New Cloud APIs
```python
# Cloud workflow execution APIs
POST /api/v1/workflows/{workflow_id}/start
POST /api/v1/workflows/{workflow_id}/execute
GET  /api/v1/workflows/{workflow_id}/status
GET  /api/v1/workflows/{workflow_id}/steps
POST /api/v1/workflows/{workflow_id}/complete

# Session management APIs
POST /api/v1/sessions
GET  /api/v1/sessions/{session_id}
PUT  /api/v1/sessions/{session_id}
DELETE /api/v1/sessions/{session_id}

# Production gate APIs
GET  /api/v1/production/status
POST /api/v1/production/validate
GET  /api/v1/production/violations
```

### Backward Compatibility Strategy
1. **Maintain existing MCP tool contracts** - No breaking changes
2. **Route MCP calls to cloud services** - Transparent migration
3. **Preserve response formats** - Same data structures
4. **Support both local and cloud** - Gradual migration

## Cloud Deployment Strategy

### Containerization
```dockerfile
# BMAD Workflow Service Container
FROM python:3.11-slim@sha256:a0939570b38cddeb861b8e75d20b1c8218b21562b18f301171904b544e8cf228

# Security context
USER 1001:1001
RUN adduser --disabled-password --gecos '' --uid 1001 bmad

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . /app/
WORKDIR /app

# Non-root execution
USER bmad

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["python", "main.py"]
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bmad-workflow-service
  namespace: cerebral-development
spec:
  replicas: 3
  selector:
    matchLabels:
      app: bmad-workflow-service
  template:
    metadata:
      labels:
        app: bmad-workflow-service
    spec:
      securityContext:
        runAsNonRoot: true
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: bmad-workflow-service
        image: ghcr.io/baerautotech/bmad-workflow-service@sha256:...
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
          runAsNonRoot: true
          seccompProfile:
            type: RuntimeDefault
        ports:
        - containerPort: 8000
        env:
        - name: SUPABASE_URL
          valueFrom:
            secretKeyRef:
              name: supabase-secrets
              key: url
        - name: SUPABASE_KEY
          valueFrom:
            secretKeyRef:
              name: supabase-secrets
              key: key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Service Configuration
```yaml
apiVersion: v1
kind: Service
metadata:
  name: bmad-workflow-service
  namespace: cerebral-development
spec:
  selector:
    app: bmad-workflow-service
  ports:
  - name: http
    port: 80
    targetPort: 8000
  type: ClusterIP
```

## Security Architecture

### Kyverno Policy Compliance
```yaml
# Production gate enforcement
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: bmad-production-gate
spec:
  validationFailureAction: enforce
  background: true
  rules:
  - name: enforce-production-mode
    match:
      any:
      - resources:
          kinds:
          - Pod
          namespaces:
          - cerebral-development
    validate:
      message: "BMAD workflows must run in production mode"
      pattern:
        spec:
          containers:
          - name: "bmad-*"
            env:
            - name: BMAD_PRODUCTION_MODE
              value: "true"
            - name: BMAD_ALLOW_MOCK_MODE
              value: "false"
```

### Security Context Template
```yaml
# Pod-level security context
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        seccompProfile:
          type: RuntimeDefault

# Container-level security context
containers:
- name: bmad-workflow-service
  image: ghcr.io/baerautotech/bmad-workflow-service@sha256:...
  securityContext:
    allowPrivilegeEscalation: false
    capabilities:
      drop: ["ALL"]
    runAsNonRoot: true
    seccompProfile:
      type: RuntimeDefault
```

## Data Flow Architecture

### Workflow Execution Flow
```
1. MCP Tool Call (cflow-platform)
   ↓
2. Direct Client Router (cflow_platform/core/direct_client.py)
   ↓
3. BMAD Handler (cflow_platform/handlers/bmad_handlers.py)
   ↓
4. Vendor BMAD Wrapper (cflow_platform/core/vendor_bmad_wrapper.py)
   ↓
5. Cloud Workflow Service (Cerebral cluster)
   ↓
6. Real Vendor BMAD Execution (vendor/bmad/ in cloud)
   ↓
7. Session State Persistence (Supabase)
   ↓
8. Response to MCP Client
```

### Session Management Flow
```
1. Workflow Start Request
   ↓
2. Create Session (Supabase bmad_workflow_sessions)
   ↓
3. Load Workflow Config (vendor/bmad/bmad-core/workflows/)
   ↓
4. Execute First Step
   ↓
5. Update Session State
   ↓
6. Return Next Step
   ↓
7. Repeat until Complete
```

## Integration Points

### MCP Tool Registry Integration
```python
# cflow_platform/core/tool_registry.py
def get_tools_for_mcp() -> List[Dict[str, Any]]:
    tools = []
    
    # BMAD Master Tools (33 tools)
    tools += [
        tool("bmad_workflow_discover", "Discover available BMAD workflows"),
        tool("bmad_workflow_start", "Start a BMAD workflow"),
        tool("bmad_workflow_next", "Get next workflow step"),
        tool("bmad_workflow_status", "Get workflow status"),
        # ... 29 more BMAD tools
    ]
    
    return tools
```

### Direct Client Integration
```python
# cflow_platform/core/direct_client.py
async def execute_mcp_tool(tool_name: str, **kwargs: Any) -> Dict[str, Any]:
    if tool_name.startswith("bmad_"):
        mod = load_handler_module("bmad_handlers")
        handler = mod.BMADHandlers()
        
        if tool_name == "bmad_workflow_start":
            return await handler.bmad_workflow_start(**kwargs)
        # ... other BMAD tools
```

### Vendor BMAD Wrapper Integration
```python
# cflow_platform/core/vendor_bmad_wrapper.py
class VendorBMADWrapper:
    async def start_brownfield_workflow(self, project_path: str, 
                                      workflow_type: str = "brownfield-service") -> Dict[str, Any]:
        # Load vendor BMAD workflow
        workflow_file = self.workflows_dir / f"{workflow_type}.yaml"
        with open(workflow_file, 'r') as f:
            workflow_config = yaml.safe_load(f)
        
        # Create workflow session
        session_id = str(uuid.uuid4())
        # ... session creation logic
```

## Performance Architecture

### Horizontal Scaling
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: bmad-workflow-service-hpa
  namespace: cerebral-development
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: bmad-workflow-service
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Load Balancing
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: bmad-workflow-service-ingress
  namespace: cerebral-development
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
spec:
  rules:
  - host: bmad-workflow.cerebral.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: bmad-workflow-service
            port:
              number: 80
```

## Monitoring Architecture

### Health Checks
```python
# Health check endpoints
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/ready")
async def readiness_check():
    # Check Supabase connection
    # Check vendor BMAD availability
    # Check workflow session state
    return {"status": "ready", "checks": {"supabase": "ok", "bmad": "ok"}}
```

### Metrics Collection
```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

workflow_executions = Counter('bmad_workflow_executions_total', 
                             'Total workflow executions', ['workflow_type', 'status'])
workflow_duration = Histogram('bmad_workflow_duration_seconds', 
                             'Workflow execution duration', ['workflow_type'])
active_sessions = Gauge('bmad_active_sessions', 'Active workflow sessions')
```

## Migration Strategy

### Phase 1: Infrastructure Setup
1. Deploy BMAD workflows to cloud cluster
2. Configure Kubernetes security contexts
3. Update MCP tool routing
4. Implement production gate system

### Phase 2: Workflow Migration
1. Test all 6 workflows in cloud
2. Implement session management
3. Validate workflow execution
4. Performance optimization

### Phase 3: Production Validation
1. Security compliance validation
2. Performance testing
3. Load testing
4. User acceptance testing

### Phase 4: Go-Live
1. Gradual migration of users
2. Monitor performance metrics
3. Handle any issues
4. Complete migration

## Conclusion

This architecture document provides a comprehensive plan for migrating BMAD-Method from local installation to the Cerebral cloud cluster. The architecture ensures:

- **Service Integration**: Seamless integration with existing cflow-platform
- **API Evolution**: Backward compatibility with new cloud capabilities
- **Security Compliance**: Kyverno policy compliance and production gate enforcement
- **Scalability**: Horizontal scaling and load balancing
- **Reliability**: Health checks, monitoring, and session persistence

The migration will establish BMAD-Method as a core, cloud-native component of the Cerebral platform while maintaining all existing functionality and ensuring production-grade deployment.

