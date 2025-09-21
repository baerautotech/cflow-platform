# BMAD WebMCP Integration - Brownfield Implementation Plan

**Document Version**: 1.0  
**Date**: 2025-01-09  
**Project Type**: Brownfield Enhancement  
**Implementation Level**: Detailed Implementation  
**Status**: Draft  

## 🎯 **Implementation Overview**

This document provides the detailed implementation plan for enhancing the existing Cerebral cluster WebMCP server to integrate BMAD tools via a dedicated BMAD API service.

## 📋 **Implementation Phases**

### **Phase 1: WebMCP Server Enhancement (Week 1-2)**

#### **Task 1.1: Add BMAD Tool Detection and Routing Logic**
```python
# File: cflow_platform/core/webmcp_server.py
# Add BMAD tool routing logic

class BMADToolRouter:
    def __init__(self):
        self.bmad_api_client = BMADAPIClient()
        self.feature_flags = FeatureFlags()
        self.health_checker = HealthChecker()
    
    async def route_bmad_tool(self, tool_name: str, arguments: dict):
        if not self.feature_flags.is_enabled("bmad_cluster_execution"):
            return await self.route_to_local(tool_name, arguments)
        
        if not await self.health_checker.is_bmad_api_healthy():
            return await self.route_to_local(tool_name, arguments)
        
        return await self.bmad_api_client.execute_tool(tool_name, arguments)
```

#### **Task 1.2: Implement BMAD API Service Client**
```python
# File: cflow_platform/core/bmad_api_client.py
# New BMAD API client

class BMADAPIClient:
    def __init__(self):
        self.base_url = os.getenv("BMAD_API_URL")
        self.jwt_token = os.getenv("BMAD_JWT_TOKEN")
        self.session = aiohttp.ClientSession()
    
    async def execute_tool(self, tool_name: str, arguments: dict):
        url = f"{self.base_url}/bmad/tools/{tool_name}/execute"
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        
        async with self.session.post(url, json=arguments, headers=headers) as response:
            return await response.json()
```

#### **Task 1.3: Add Feature Flags for Gradual Migration**
```python
# File: cflow_platform/core/feature_flags.py
# Feature flag management

class FeatureFlags:
    def __init__(self):
        self.flags = {
            "bmad_cluster_execution": True,
            "bmad_api_health_check": True,
            "bmad_performance_monitoring": True
        }
    
    def is_enabled(self, flag_name: str) -> bool:
        return self.flags.get(flag_name, False)
```

#### **Task 1.4: Implement Fallback to Local Handlers**
```python
# File: cflow_platform/core/webmcp_server.py
# Enhanced call_tool method

async def call_tool(self, request: Request):
    body = await request.json()
    tool_name = body.get("name")
    arguments = body.get("arguments", {})
    
    if tool_name.startswith("bmad_"):
        try:
            return await self.bmad_router.route_bmad_tool(tool_name, arguments)
        except Exception as e:
            logger.warning(f"BMAD cluster execution failed: {e}, falling back to local")
            return await execute_mcp_tool(tool_name, **arguments)
    else:
        return await execute_mcp_tool(tool_name, **arguments)
```

#### **Task 1.5: Add Health Checking for BMAD API Service**
```python
# File: cflow_platform/core/health_checker.py
# Health checking for BMAD API

class HealthChecker:
    def __init__(self):
        self.bmad_api_url = os.getenv("BMAD_API_URL")
        self.session = aiohttp.ClientSession()
    
    async def is_bmad_api_healthy(self) -> bool:
        try:
            url = f"{self.bmad_api_url}/bmad/health"
            async with self.session.get(url, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False
```

### **Phase 2: BMAD API Service Implementation (Week 3-4)**

#### **Task 2.1: Implement HTTP Endpoints for All BMAD Tools**
```python
# File: bmad_api_service/main.py
# FastAPI service for BMAD API

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="BMAD API Service", version="1.0.0")

@app.post("/bmad/tools/{tool_name}/execute")
async def execute_bmad_tool(tool_name: str, request: Request):
    """Execute a BMAD tool via vendor BMAD workflows"""
    try:
        body = await request.json()
        arguments = body.get("arguments", {})
        
        # Validate JWT token
        jwt_token = request.headers.get("Authorization", "").replace("Bearer ", "")
        user_context = await auth_service.validate_token(jwt_token)
        
        # Execute vendor BMAD workflow
        result = await vendor_bmad.execute_workflow(tool_name, arguments)
        
        return {"result": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### **Task 2.2: Add JWT Authentication and Validation**
```python
# File: bmad_api_service/auth_service.py
# JWT authentication service

class JWTAuthService:
    def __init__(self):
        self.jwt_secret = os.getenv("BMAD_JWT_SECRET")
        self.algorithm = "HS256"
    
    async def validate_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
```

#### **Task 2.3: Integrate with Vendor BMAD Workflows**
```python
# File: bmad_api_service/vendor_bmad_integration.py
# Vendor BMAD integration

class VendorBMADIntegration:
    def __init__(self):
        self.workflow_engine = WorkflowEngine()
        self.template_loader = BMADTemplateLoader()
    
    async def execute_workflow(self, tool_name: str, arguments: dict):
        # Map tool name to vendor BMAD workflow
        workflow_path = self.map_tool_to_workflow(tool_name)
        
        # Execute vendor BMAD workflow
        result = await self.workflow_engine.execute(workflow_path, arguments)
        
        # Format result for MCP response
        return self.format_mcp_response(result)
    
    def map_tool_to_workflow(self, tool_name: str) -> str:
        tool_mapping = {
            "bmad_prd_create": "vendor/bmad/bmad-core/workflows/greenfield-prd.yaml",
            "bmad_arch_create": "vendor/bmad/bmad-core/workflows/greenfield-arch.yaml",
            "bmad_story_create": "vendor/bmad/bmad-core/workflows/greenfield-story.yaml",
            # ... more mappings
        }
        return tool_mapping.get(tool_name)
```

#### **Task 2.4: Add Error Handling and Logging**
```python
# File: bmad_api_service/error_handler.py
# Error handling and logging

class ErrorHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def handle_error(self, error: Exception, context: dict):
        # Log error
        self.logger.error(f"BMAD API error: {error}", extra=context)
        
        # Return user-friendly error
        return {
            "error": str(error),
            "success": False,
            "timestamp": datetime.utcnow().isoformat()
        }
```

#### **Task 2.5: Implement Performance Monitoring**
```python
# File: bmad_api_service/performance_monitor.py
# Performance monitoring

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}
    
    async def record_execution_time(self, tool_name: str, execution_time: float):
        if tool_name not in self.metrics:
            self.metrics[tool_name] = []
        self.metrics[tool_name].append(execution_time)
    
    def get_average_execution_time(self, tool_name: str) -> float:
        if tool_name not in self.metrics:
            return 0.0
        return sum(self.metrics[tool_name]) / len(self.metrics[tool_name])
```

### **Phase 3: Integration Testing (Week 5)**

#### **Task 3.1: Test WebMCP → BMAD API → Vendor BMAD Flow**
```python
# File: tests/test_webmcp_bmad_integration.py
# Integration tests

class TestWebMCPBMADIntegration:
    async def test_bmad_tool_execution_flow(self):
        # Test complete flow
        response = await webmcp_client.call_tool("bmad_prd_create", {
            "project_name": "test_project",
            "description": "Test project description"
        })
        
        assert response["success"] == True
        assert "result" in response
```

#### **Task 3.2: Validate Existing MCP Functionality Preserved**
```python
# File: tests/test_regression_mcp_tools.py
# Regression tests

class TestRegressionMCPTools:
    async def test_non_bmad_tools_still_work(self):
        # Test that non-BMAD tools still work
        response = await webmcp_client.call_tool("sys_test", {})
        assert response["status"] == "success"
```

#### **Task 3.3: Performance and Load Testing**
```python
# File: tests/test_performance.py
# Performance tests

class TestPerformance:
    async def test_bmad_tool_performance(self):
        # Test BMAD tool performance
        start_time = time.time()
        response = await webmcp_client.call_tool("bmad_prd_create", {})
        execution_time = time.time() - start_time
        
        assert execution_time < 10.0  # Should be under 10 seconds
```

#### **Task 3.4: Error Handling and Recovery Testing**
```python
# File: tests/test_error_handling.py
# Error handling tests

class TestErrorHandling:
    async def test_bmad_api_unavailable_fallback(self):
        # Test fallback when BMAD API unavailable
        with mock.patch('bmad_api_client.is_healthy', return_value=False):
            response = await webmcp_client.call_tool("bmad_prd_create", {})
            assert response["success"] == True  # Should still work via fallback
```

#### **Task 3.5: Security and Authentication Testing**
```python
# File: tests/test_security.py
# Security tests

class TestSecurity:
    async def test_jwt_authentication(self):
        # Test JWT authentication
        response = await bmad_api_client.execute_tool("bmad_prd_create", {}, "invalid_token")
        assert response["status_code"] == 401
```

### **Phase 4: One-Touch Installer Updates (Week 6)**

#### **Task 4.1: Add WebMCP Configuration to Installer**
```yaml
# File: installer/webmcp_config.yaml
# WebMCP configuration

webmcp:
  server:
    url: "https://mcp.cerebral.baerautotech.com"
    timeout: 30s
    
  bmad_api:
    url: "https://bmad-api.cerebral.baerautotech.com"
    timeout: 30s
    retry_attempts: 3
    
  authentication:
    jwt_token: "${BMAD_JWT_TOKEN}"
    
  fallback:
    local_execution: true
    timeout: 10s
```

#### **Task 4.2: Test Complete Installation Flow**
```bash
# File: installer/test_installation.sh
# Test installation script

#!/bin/bash
echo "Testing WebMCP installation..."

# Install WebMCP
./install_webmcp.sh

# Test WebMCP connection
curl -X GET https://mcp.cerebral.baerautotech.com/health

# Test BMAD API connection
curl -X GET https://bmad-api.cerebral.baerautotech.com/bmad/health

echo "Installation test completed successfully!"
```

#### **Task 4.3: Add Uninstall/Rollback Capabilities**
```bash
# File: installer/uninstall_webmcp.sh
# Uninstall script

#!/bin/bash
echo "Uninstalling WebMCP..."

# Remove WebMCP configuration
rm -f ~/.cerebraflow/webmcp_config.yaml

# Remove BMAD API configuration
rm -f ~/.cerebraflow/bmad_api_config.yaml

echo "WebMCP uninstalled successfully!"
```

#### **Task 4.4: Update Documentation and Runbooks**
```markdown
# File: docs/installation/webmcp_installation_guide.md
# Installation guide

# WebMCP Installation Guide

## Prerequisites
- Cerebral cluster access
- JWT token for authentication

## Installation Steps
1. Run the one-touch installer
2. Configure WebMCP connection
3. Test BMAD tool execution
4. Verify fallback functionality

## Troubleshooting
- Check WebMCP server health
- Verify BMAD API connectivity
- Test JWT authentication
- Check fallback to local execution
```

## 🔧 **Implementation Details**

### **File Structure**
```
cflow_platform/
├── core/
│   ├── webmcp_server.py          # Enhanced WebMCP server
│   ├── bmad_api_client.py        # New BMAD API client
│   ├── feature_flags.py          # Feature flag management
│   └── health_checker.py         # Health checking
├── handlers/
│   └── bmad_handlers.py          # Existing BMAD handlers (fallback)
└── tests/
    ├── test_webmcp_bmad_integration.py
    ├── test_regression_mcp_tools.py
    ├── test_performance.py
    ├── test_error_handling.py
    └── test_security.py

bmad_api_service/
├── main.py                       # FastAPI service
├── auth_service.py              # JWT authentication
├── vendor_bmad_integration.py   # Vendor BMAD integration
├── error_handler.py             # Error handling
└── performance_monitor.py       # Performance monitoring
```

### **Configuration Files**
```
config/
├── webmcp_config.yaml           # WebMCP configuration
├── bmad_api_config.yaml        # BMAD API configuration
├── feature_flags.yaml          # Feature flags
└── monitoring.yaml              # Monitoring configuration
```

### **Kubernetes Manifests**
```
infrastructure/kubernetes/
├── webmcp-deployment.yaml       # WebMCP deployment
├── bmad-api-deployment.yaml    # BMAD API deployment
├── webmcp-service.yaml         # WebMCP service
├── bmad-api-service.yaml       # BMAD API service
└── secrets.yaml                # Secrets configuration
```

## 📊 **Testing Strategy**

### **Unit Tests**
- WebMCP server routing logic
- BMAD API client functionality
- Feature flag management
- Health checking
- Error handling

### **Integration Tests**
- WebMCP → BMAD API → Vendor BMAD flow
- Authentication and authorization
- Error handling and recovery
- Performance and load testing

### **Regression Tests**
- All existing MCP tools functionality
- WebMCP server performance
- Cluster stability
- One-touch installer functionality

### **User Acceptance Tests**
- End-to-end BMAD workflow execution
- Client installation and configuration
- Error scenarios and recovery
- Performance under load

## 🚀 **Deployment Strategy**

### **Rollout Plan**
1. **Phase 1**: Deploy BMAD API service to cluster
2. **Phase 2**: Enable feature flags for internal testing
3. **Phase 3**: Gradual rollout to beta users
4. **Phase 4**: Full rollout to all users
5. **Phase 5**: Disable local BMAD execution

### **Rollback Plan**
1. **Immediate**: Disable feature flags
2. **Short-term**: Rollback WebMCP server changes
3. **Medium-term**: Remove BMAD API service
4. **Long-term**: Restore local BMAD execution

## 📋 **Quality Gates**

### **Code Quality**
- [ ] All code reviewed by senior developers
- [ ] 100% test coverage for new code
- [ ] No linting errors
- [ ] Security review completed

### **Performance**
- [ ] No regression in existing tool performance
- [ ] BMAD tool execution latency < 2x current
- [ ] Memory usage within acceptable limits
- [ ] CPU usage within acceptable limits

### **Security**
- [ ] JWT authentication working
- [ ] Input validation implemented
- [ ] Audit logging active
- [ ] Security review passed

### **Documentation**
- [ ] Technical documentation updated
- [ ] Operational runbooks updated
- [ ] User documentation updated
- [ ] Troubleshooting guides updated

---

**Document Status**: Draft  
**Next Steps**: Implementation review and approval  
**Stakeholders**: Development Team, Operations Team, QA Team  
**Approval Required**: Technical Lead, Development Lead, QA Lead
