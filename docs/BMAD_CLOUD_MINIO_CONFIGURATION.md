# BMAD Cloud MinIO Configuration

## Overview

This document outlines the **cloud-native MinIO configuration** for BMAD expansion packs, ensuring all storage operations use the **Cerebral cloud platform** instead of localhost.

## Architecture

### Cloud Platform Integration
```
┌─────────────────────────────────────────────────────────────┐
│                    Cerebral Cloud Cluster                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   BMAD Core     │  │   MinIO S3      │  │   BMAD      │ │
│  │   Workflows     │  │   Storage       │  │   Templates │ │
│  │   Service       │  │   Service       │  │   Service   │ │
│  │                 │  │                 │  │             │ │
│  │ • 6 workflows   │  │ • bmad-expansion│  │ • prd-tmpl  │ │
│  │ • brownfield-*  │  │   -packs        │  │ • arch-tmpl │ │
│  │ • greenfield-*  │  │ • bmad-expansion│  │ • story-tmpl│ │
│  │ • workflow exec │  │   -metadata     │  │ • task-tmpl │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables
```bash
# Cloud Platform MinIO Configuration
MINIO_ENDPOINT=minio.cerebral.baerautotech.com
MINIO_ACCESS_KEY=<cloud-access-key>
MINIO_SECRET_KEY=<cloud-secret-key>
MINIO_SECURE=true  # HTTPS for cloud platform
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio-storage-service
  namespace: cerebral-development
spec:
  replicas: 3
  selector:
    matchLabels:
      app: minio-storage-service
  template:
    metadata:
      labels:
        app: minio-storage-service
    spec:
      securityContext:
        runAsNonRoot: true
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: minio-storage-service
        image: minio/minio@sha256:...
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
          runAsNonRoot: true
          seccompProfile:
            type: RuntimeDefault
        command: ["minio", "server", "/data", "--console-address", ":9001"]
        ports:
        - containerPort: 9000
        - containerPort: 9001
        env:
        - name: MINIO_ROOT_USER
          valueFrom:
            secretKeyRef:
              name: minio-secrets
              key: access-key
        - name: MINIO_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: minio-secrets
              key: secret-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        volumeMounts:
        - name: minio-data
          mountPath: /data
      volumes:
      - name: minio-data
        persistentVolumeClaim:
          claimName: minio-pvc
```

### Service Configuration
```yaml
apiVersion: v1
kind: Service
metadata:
  name: minio-storage-service
  namespace: cerebral-development
spec:
  selector:
    app: minio-storage-service
  ports:
  - name: api
    port: 9000
    targetPort: 9000
  - name: console
    port: 9001
    targetPort: 9001
  type: ClusterIP
```

### Ingress Configuration
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: minio-storage-ingress
  namespace: cerebral-development
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - minio.cerebral.baerautotech.com
    secretName: minio-tls
  rules:
  - host: minio.cerebral.baerautotech.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: minio-storage-service
            port:
              number: 9000
```

## Bucket Configuration

### Required Buckets
```bash
# BMAD Expansion Packs Storage
bmad-expansion-packs
bmad-expansion-metadata

# BMAD Templates Storage
bmad-templates-core
bmad-templates-brownfield
bmad-templates-greenfield

# BMAD Tasks Storage
bmad-tasks-core
bmad-tasks-expansion
```

### Bucket Policies
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": ["arn:aws:iam::*:user/cerebral-bmad-service"]
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::bmad-expansion-packs/*",
        "arn:aws:s3:::bmad-expansion-metadata/*",
        "arn:aws:s3:::bmad-templates-*/*",
        "arn:aws:s3:::bmad-tasks-*/*"
      ]
    }
  ]
}
```

## Integration Points

### BMAD Template Loading
```python
# cflow_platform/core/bmad_template_loader.py
class BMADTemplateLoader:
    def __init__(self):
        self.storage = get_expansion_pack_storage()
        self.minio_endpoint = "minio.cerebral.baerautotech.com"
    
    async def load_template(self, template_type: str, pack_name: str) -> Optional[Dict[str, Any]]:
        """Load template from cloud MinIO storage."""
        try:
            # Load from cloud MinIO
            template_data = await self.storage.get_pack_file(
                pack_name, 
                f"templates/{template_type}-tmpl.yaml"
            )
            
            if template_data:
                return yaml.safe_load(template_data.decode('utf-8'))
            
            return None
            
        except Exception as e:
            print(f"[ERROR] BMAD Template Loader: Failed to load template {template_type} from pack {pack_name}: {e}")
            return None
```

### Expansion Pack Discovery
```python
# cflow_platform/core/expansion_pack_storage.py
async def discover_cloud_packs() -> List[ExpansionPackMetadata]:
    """Discover expansion packs from cloud MinIO storage."""
    storage = get_expansion_pack_storage()
    
    # Ensure we're using cloud endpoint
    if not storage.minio_client:
        print("[ERROR] MinIO client not available - check cloud configuration")
        return []
    
    return await storage.list_available_packs()
```

## Security Configuration

### TLS/SSL
- **MinIO Console**: HTTPS on port 9001
- **MinIO API**: HTTPS on port 9000
- **Certificate**: Let's Encrypt via cert-manager
- **Domain**: `minio.cerebral.baerautotech.com`

### Authentication
- **Access Key**: Stored in Kubernetes secrets
- **Secret Key**: Stored in Kubernetes secrets
- **IAM Policies**: Role-based access control
- **Bucket Policies**: Resource-level permissions

### Network Security
- **Ingress**: Nginx ingress controller
- **TLS Termination**: At ingress level
- **Internal Communication**: ClusterIP services
- **External Access**: HTTPS only

## Monitoring

### Health Checks
```python
@app.get("/health")
async def minio_health_check():
    """Health check for MinIO service."""
    try:
        storage = get_expansion_pack_storage()
        if storage.minio_client:
            # Test bucket access
            buckets = storage.minio_client.list_buckets()
            return {
                "status": "healthy",
                "buckets": len(buckets),
                "endpoint": storage.minio_endpoint
            }
        else:
            return {"status": "unhealthy", "error": "MinIO client not available"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### Metrics
```python
# Prometheus metrics for MinIO
minio_requests_total = Counter('minio_requests_total', 'Total MinIO requests', ['method', 'bucket'])
minio_request_duration = Histogram('minio_request_duration_seconds', 'MinIO request duration', ['method', 'bucket'])
minio_storage_usage = Gauge('minio_storage_usage_bytes', 'MinIO storage usage', ['bucket'])
```

## Migration Strategy

### Phase 1: Cloud MinIO Deployment
1. Deploy MinIO service to Cerebral cluster
2. Configure buckets and policies
3. Set up ingress and TLS
4. Test connectivity

### Phase 2: Template Migration
1. Upload existing templates to cloud MinIO
2. Update template loader to use cloud storage
3. Test template loading
4. Validate expansion pack functionality

### Phase 3: Integration Testing
1. Test BMAD workflow execution
2. Validate document creation
3. Test expansion pack discovery
4. Performance validation

### Phase 4: Production Deployment
1. Update all environment variables
2. Deploy to production cluster
3. Monitor performance
4. Handle any issues

## Troubleshooting

### Common Issues

#### Connection Refused
```bash
# Check if MinIO service is running
kubectl get pods -n cerebral-development -l app=minio-storage-service

# Check service endpoints
kubectl get svc -n cerebral-development minio-storage-service

# Check ingress
kubectl get ingress -n cerebral-development minio-storage-ingress
```

#### Authentication Failures
```bash
# Check secrets
kubectl get secret -n cerebral-development minio-secrets

# Verify credentials
kubectl describe secret -n cerebral-development minio-secrets
```

#### Bucket Access Issues
```bash
# Check bucket policies
kubectl exec -it deployment/minio-storage-service -n cerebral-development -- mc admin policy list

# Test bucket access
kubectl exec -it deployment/minio-storage-service -n cerebral-development -- mc ls bmad-expansion-packs
```

## Conclusion

This cloud-native MinIO configuration ensures that:

- **All BMAD storage operations use the cloud platform**
- **No localhost dependencies**
- **Proper security and authentication**
- **Scalable and reliable storage**
- **Integration with Cerebral cluster**

The migration from localhost to cloud platform is **critical** for the success of the BMAD cloud migration and ensures that all documentation and task systems work properly in the cloud environment.
