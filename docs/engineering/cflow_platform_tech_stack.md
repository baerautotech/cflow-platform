# CFlow Platform Technical Stack

**Date**: 2025-01-09  
**Status**: ✅ **AUTHORITATIVE**  
**Scope**: Complete technical stack for cflow-platform

## 🎯 **Platform Architecture**

### **Frontend (Cross-Platform)**
- **React Native + React Native Web + TypeScript**
  - Mobile: iOS/Android native apps
  - Web: Browser-based applications via React Native Web
  - Wearable: Apple Watch/WearOS support
  - Single codebase across all platforms

### **Backend (Full Python)**
- **Python 3.11** in virtual environment using **UV** for package management
- **FastAPI** for all backend services and APIs
- **No Node.js/Express** - pure Python backend architecture

### **AI/ML Infrastructure**
- **GPU Acceleration**: Supports any available GPU hardware
  - Apple Silicon MPS (when available)
  - NVIDIA CUDA (when available)
  - CPU fallback (universal compatibility)
- **Embeddings**: Vector embeddings with hardware acceleration
- **BMAD Integration**: Headless BMAD services for AI agents

### **Data & Storage**
- **Database**: PostgreSQL (Supabase)
- **Vector Storage**: Supabase + pgvector
- **Object Storage**: **MinIO S3** (not AWS cloud)
- **Caching**: Redis
- **Local Development**: ChromaDB

### **Infrastructure**
- **Containerization**: Docker
- **Orchestration**: Kubernetes
- **Package Management**: UV (Python)
- **Environment**: Virtual environments (.venv)

## 🔧 **Development Stack**

### **Core Technologies**
```yaml
Language: Python 3.11
Package Manager: UV
Virtual Environment: .venv
Test Framework: pytest 8.x
Backend Framework: FastAPI
Frontend: React Native + React Native Web + TypeScript
```

### **AI/ML Stack**
```yaml
Embeddings: Hardware-accelerated (GPU-aware)
Vector DB: ChromaDB (local), Supabase pgvector (remote)
AI Agents: BMAD headless services
Model Provider: Cerebral Server (private cluster)
Fallback: OpenRouter → Ollama (local)
```

### **Data Stack**
```yaml
Primary DB: PostgreSQL (Supabase)
Vector Storage: Supabase + pgvector
Object Storage: MinIO S3
Caching: Redis
Local Development: ChromaDB
```

### **Infrastructure Stack**
```yaml
Containerization: Docker
Orchestration: Kubernetes
Package Management: UV
Environment Management: Virtual environments
```

## 🏗️ **Architecture Principles**

### **1. Full Python Backend**
- All backend services use Python FastAPI
- No Node.js/Express in the backend
- Unified Python ecosystem for consistency

### **2. Cross-Platform Frontend**
- React Native for mobile/wearable
- React Native Web for web
- Single codebase, multiple platforms

### **3. Hardware-Agnostic AI/ML**
- Supports any available GPU (Apple Silicon MPS, NVIDIA CUDA)
- Automatic fallback to CPU
- No vendor lock-in for AI acceleration

### **4. Self-Hosted Infrastructure**
- MinIO S3 instead of AWS cloud
- Private Cerebral cluster for AI services
- Full control over data and infrastructure

## 📋 **BMAD Integration Stack**

### **BMAD Services**
- **BMAD Core**: Node v20 (headless, vendored)
- **HTTP API Facade**: Python FastAPI (on cerebral cluster)
- **CAEF Orchestrator**: Python (gated execution)
- **WebMCP Server**: Python FastAPI (on cerebral cluster)

### **Integration Points**
- **Tool Registry**: Python (`cflow_platform.core.tool_registry`)
- **Direct Client**: Python HTTP client for local testing
- **Knowledge Graph**: Supabase + pgvector indexing
- **Document Storage**: Supabase (`cerebral_documents` table)

## 🚀 **Deployment Architecture**

### **Cerebral Cluster (Production)**
- **WebMCP Server**: `mcp.cerebral.baerautotech.com`
- **BMAD HTTP API**: Python FastAPI facade
- **KnowledgeRAG**: Supabase + pgvector
- **Deployment**: Kubernetes manifests

### **cflow-platform (Development)**
- **Tool Definitions**: Python tool registry
- **Local Testing**: HTTP client to cluster APIs
- **No Local MCP**: All MCP servers run on cluster

## 🔍 **Key Differences from Common Stacks**

### **❌ What We DON'T Use**
- Node.js/Express for backend services
- AWS cloud services (using MinIO S3)
- React for web (using React Native Web)
- Vendor-specific AI acceleration only

### **✅ What We DO Use**
- Full Python FastAPI backend
- React Native + React Native Web frontend
- Hardware-agnostic GPU acceleration
- Self-hosted MinIO S3 storage
- UV for Python package management

## 📚 **Documentation References**

- **Technical Stack**: `docs/agentic-plan/TechnicalStack.md`
- **Architecture**: `docs/agentic-plan/Architecture.md`
- **BMAD Integration**: `docs/plans/BMAD_CORE_PLATFORM_INTEGRATION_PLAN.md`
- **MCP Architecture**: `docs/architecture/MCP_ARCHITECTURE.md`

## 🎯 **Summary**

**CFlow Platform** uses:
- **Frontend**: React Native + React Native Web + TypeScript
- **Backend**: Python 3.11 + FastAPI (full Python stack)
- **AI/ML**: Hardware-agnostic GPU acceleration
- **Storage**: MinIO S3 (self-hosted)
- **Package Management**: UV
- **Infrastructure**: Docker + Kubernetes

This provides a unified, self-hosted, cross-platform development environment with full Python backend and hardware-agnostic AI acceleration.
