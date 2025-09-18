# MCP Architecture - Cerebral Cluster Strategy

Document version: 1.0  
Date: 2025-09-17  
Purpose: Clarify MCP deployment strategy and architectural decisions

## 🎯 **Architectural Decision**

**All MCP services run on the cerebral cluster, not locally.**

### **Cerebral Cluster (Production)**
- **WebMCP Server**: `mcp.cerebral.baerautotech.com`
- **Tool Registry**: Imported from `cflow_platform.core.tool_registry`
- **BMAD Integration**: HTTP API facade for BMAD agents
- **BMAD Project Type Detection**: Automatic greenfield vs brownfield workflow routing
- **BMAD Brownfield Support**: Comprehensive existing system analysis and documentation generation
- **BMAD Expansion Packs**: Dynamic pack loading and domain-specific agents
- **KnowledgeRAG**: Supabase + pgvector on cluster
- **Deployment**: Kubernetes manifests in `cerebral-deployment/k8s/`

### **cflow-platform (Development)**
- **Tool Definitions**: `tool_registry.py` (for cluster import)
- **Local Testing**: HTTP client to call cluster APIs
- **No Local MCP**: All MCP servers run on cluster

## 🏗️ **Current Architecture**

### **WebMCP Server (Cerebral Cluster)**
```python
# Location: /Users/bbaer/Development/Cerebral/.cerebraflow/core/mcp/web_mcp_server.py
# Deployment: cerebral-deployment/k8s/cerebraflow-webmcp.yaml
# Features:
# - Dual transport: STDIO + HTTP
# - Imports tools from cflow_platform.core.tool_registry
# - Routes tool calls to appropriate services
# - Production ready with FastAPI + Uvicorn
```

### **Tool Registry (cflow-platform)**
```python
# Location: cflow_platform/core/tool_registry.py
# Purpose: Define tool specifications for cluster import
# Tools: 50+ tools including system, tasks, memory, code intelligence
# Integration: Imported by WebMCP server on cluster
```

### **Direct Client (cflow-platform)**
```python
# Location: cflow_platform/core/direct_client.py
# Purpose: Local testing and development
# Usage: HTTP client to call cluster APIs
# Note: Not for production MCP server
```

## 🔄 **BMAD Integration Strategy**

### **Phase 1: Tool Registry Updates**
1. **Add BMAD Tools**: Update `tool_registry.py` with BMAD agent tools
2. **Tool Specifications**: Define input/output schemas for BMAD agents
3. **Integration Points**: Map BMAD tools to HTTP API calls

### **Phase 2: HTTP API Facade**
1. **BMAD Service**: Deploy BMAD HTTP API facade to cerebral cluster
2. **Project Type Detection**: `/bmad/project-type/detect` - Automatic greenfield vs brownfield detection
3. **Greenfield Endpoints**: `/bmad/greenfield/prd-create`, `/bmad/greenfield/arch-create`, `/bmad/greenfield/story-create`
4. **Brownfield Endpoints**: `/bmad/brownfield/document-project`, `/bmad/brownfield/prd-create`, `/bmad/brownfield/arch-create`, `/bmad/brownfield/story-create`
5. **Expansion Pack Endpoints**: `/bmad/expansion-packs/install`, `/bmad/expansion-packs/list`, `/bmad/expansion-packs/enable`
6. **Authentication**: JWT-based auth with tenant isolation
7. **Provider Router**: Route BMAD agent calls to hosted LLM APIs
8. **Dynamic Pack Loading**: Load expansion packs on-demand based on project requirements
9. **Workflow Routing**: Route projects to appropriate greenfield or brownfield workflows

### **Phase 3: WebMCP Integration**
1. **Tool Import**: WebMCP server imports BMAD tools from cflow-platform
2. **HTTP Routing**: Route BMAD tool calls to BMAD API facade
3. **Response Handling**: Process BMAD responses and return to clients

## 📋 **Implementation Tasks**

### **Immediate (Local Development)**
- [x] **Task 1.1**: Vendor BMAD into `vendor/bmad/`
- [x] **Task 1.2**: Define upstream sync policy
- [x] **Task 2.1**: Inventory BMAD interfaces
- [ ] **Task 2.2**: Map artifacts to DB schema
- [ ] **Task 2.3**: UX scope for PRD/Architecture/Story forms

### **Cluster Deployment (When Ready)**
- [ ] **Task 3.1**: Scaffold BMAD HTTP API service (cerebral-deployment)
- [ ] **Task 3.2**: Implement BMAD HTTP API facade endpoints
- [ ] **Task 3.3**: Implement BMAD project type detection system
- [ ] **Task 3.4**: Implement BMAD brownfield support (document-project, brownfield templates)
- [ ] **Task 3.5**: Implement BMAD expansion pack endpoints
- [ ] **Task 3.6**: WebMCP integration for BMAD tools
- [ ] **Task 3.7**: Provider router integration
- [ ] **Task 3.8**: Dynamic expansion pack loading system
- [ ] **Task 3.9**: Workflow routing system for greenfield vs brownfield

### **Local Development Tools**
- [ ] **Task 10.1**: `cflow-local bmad` CLI (HTTP client)
- [ ] **Task 10.2**: WebMCP tool integration
- [ ] **Task 10.3**: Sync engine (bidirectional)

## 🚨 **Migration Notes**

### **Removed Local MCP Servers**
- **cerebraflow**: Was pointing to local `.cerebraflow/core/mcp/start_mcp_server.sh`
- **supabase**: Was running NPX package locally
- **context7**: Was running NPX package locally

### **New Configuration**
- **cerebraflow-webmcp**: HTTP client to `mcp.cerebral.baerautotech.com`
- **Environment**: Production mode with cluster URL
- **Transport**: HTTP instead of stdio

## 🔍 **Verification Steps**

### **Cluster Status**
1. **WebMCP Server**: Verify `mcp.cerebral.baerautotech.com` is accessible
2. **Tool Registry**: Confirm tools are imported from cflow-platform
3. **KnowledgeRAG**: Test Supabase + pgvector connectivity
4. **BMAD API**: Verify BMAD HTTP API facade is deployed

### **Local Development**
1. **HTTP Client**: Test local HTTP client to cluster APIs
2. **Tool Definitions**: Verify BMAD tools are defined in `tool_registry.py`
3. **Integration**: Confirm WebMCP server imports BMAD tools

## 📚 **References**

- [BMAD Core Platform Integration Plan](../plans/BMAD_CORE_PLATFORM_INTEGRATION_PLAN.md)
- [BMAD Task Breakdown](../plans/BMAD_CORE_PLATFORM_INTEGRATION_TASKS.md)
- [API Inventory](../architecture/bmad_api_inventory.md)
- [Upstream Sync Policy](../engineering/bmad_upstream_sync.md)
