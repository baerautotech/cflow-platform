# Deployment Knowledge Base

**Category:** deployment  
**Last Updated:** 2025-01-XX  
**Status:** Active

## Current Deployment Strategy

### SHA-Based Deployments
**Decision Date:** 2025-01-XX  
**Rationale:** Enables precise rollbacks and deployment traceability

**Implementation:**
- All Docker images tagged with `$GITHUB_SHA`
- Kubernetes deployments updated with SHA-based image tags
- GitHub Actions workflow handles deployment automation

**Commands:**
```bash
# Build with SHA tag
docker build -t cerebral/service:$GITHUB_SHA .

# Update Kubernetes deployment
kubectl set image deployment/service service=cerebral/service:$GITHUB_SHA
kubectl rollout status deployment/service --timeout=300s
```

### Cerebral Cluster Deployment
**Decision Date:** 2025-01-XX  
**Rationale:** SSH-based deployment ensures security and consistency

**Implementation:**
- SSH access via `cerebral@10.34.0.22`
- Files copied to `/opt/cerebral-platform/service/$SHA/`
- Docker builds executed on cluster

**Commands:**
```bash
# Copy files to cluster
scp -r service/ cerebral@10.34.0.22:/opt/cerebral-platform/service/$SHA/

# Build on cluster
ssh cerebral@10.34.0.22 "cd /opt/cerebral-platform/service/$SHA && docker build -t cerebral/service:$SHA ."
```

## Deployment Verification

### Health Checks
All deployments must include health verification:

```bash
# Check pods
kubectl get pods -l app=service

# Check service
kubectl get service service-service

# Health endpoint
curl -f https://service.dev.baerautotech.com/health
```

### Rollback Procedures
```bash
# Rollback to previous deployment
kubectl rollout undo deployment/service

# Rollback to specific SHA
kubectl set image deployment/service service=cerebral/service:$PREVIOUS_SHA
```

## Common Issues and Solutions

### Issue: Deployment fails with image pull error
**Solution:** Verify Docker image exists on cluster
```bash
ssh cerebral@10.34.0.22 "docker images | grep cerebral/service"
```

### Issue: Kubernetes deployment stuck
**Solution:** Check pod status and logs
```bash
kubectl describe pod -l app=service
kubectl logs -l app=service
```

## Related Decisions
- [Infrastructure Configuration](../infrastructure.md)
- [Security Policies](../security.md)
- [Troubleshooting Guide](../troubleshooting.md)

## Review Schedule
- **Next Review:** 2025-04-XX
- **Review Frequency:** Quarterly
- **Reviewer:** Technical Lead

