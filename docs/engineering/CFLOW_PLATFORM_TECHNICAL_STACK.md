# CFlow Platform Technical Stack - Authoritative Reference

**Document Version**: 2.0  
**Date**: 2025-01-09  
**Status**: ✅ **AUTHORITATIVE & COMPLETE**  
**Scope**: Complete technical stack for cflow-platform ecosystem

## 🎯 **Executive Summary**

CFlow Platform is a **full Python FastAPI backend** with **React Native + React Native Web frontend**, designed for cross-platform mobile/web/wearable development with hardware-agnostic AI acceleration and self-hosted infrastructure.

## 🏗️ **Platform Architecture**

### **Frontend Stack (Cross-Platform)**
```yaml
Primary Framework: React Native + React Native Web + TypeScript
Mobile Platforms: iOS, Android native apps
Web Platform: Browser-based applications via React Native Web
Wearable Platforms: Apple Watch, WearOS support
Architecture: Single codebase, multiple platform targets
State Management: Redux Toolkit (when needed)
UI Components: React Native components + React Native Web adaptations
```

### **Backend Stack (Full Python)**
```yaml
Language: Python 3.11
Framework: FastAPI (all backend services)
Package Management: UV (modern Python tooling)
Virtual Environment: .venv (isolated dependencies)
API Documentation: OpenAPI/Swagger (auto-generated)
Async Support: Native async/await throughout
WebSocket Support: Built-in FastAPI WebSocket support
```

### **AI/ML Infrastructure (Hardware-Agnostic)**
```yaml
GPU Acceleration: Hardware-agnostic support
  - Apple Silicon MPS (when available)
  - NVIDIA CUDA (when available) 
  - CPU fallback (universal compatibility)
Embeddings: Vector embeddings with automatic hardware detection
Model Provider: Cerebral Server (private cluster)
Fallback Chain: Cerebral Server → OpenRouter → Ollama (local)
BMAD Integration: Headless BMAD services for AI agents
```

### **Data & Storage Stack**
```yaml
Primary Database: PostgreSQL (Supabase)
Vector Storage: Supabase + pgvector (remote)
Local Vector DB: ChromaDB (development)
Object Storage: MinIO S3 (self-hosted, not AWS cloud)
Caching: Redis
Session Storage: Redis
File Storage: MinIO S3 buckets
```

### **Infrastructure Stack**
```yaml
Containerization: Docker
Orchestration: Kubernetes
Package Management: UV (Python)
Environment Management: Virtual environments (.venv)
CI/CD: GitHub Actions (when applicable)
Monitoring: Prometheus + Grafana
Logging: Structured JSON logging
```

## 🔧 **Development Environment**

### **Core Development Tools**
```yaml
Python Version: 3.11
Package Manager: UV (replaces pip/poetry)
Virtual Environment: .venv
Test Framework: pytest 8.x
Linting: ruff (fast Python linter)
Type Checking: mypy
Code Formatting: black
Pre-commit Hooks: ruff, black, mypy
```

### **Frontend Development**
```yaml
React Native CLI: Latest stable
React Native Web: Latest stable
TypeScript: Latest stable
Metro Bundler: React Native bundler
Expo (Optional): For rapid prototyping
```

### **Backend Development**
```yaml
FastAPI: Latest stable
Uvicorn: ASGI server
Pydantic: Data validation
SQLAlchemy: ORM (when needed)
Alembic: Database migrations
```

## 🧠 **AI/ML Stack Details**

### **Embedding Services**
```yaml
Primary: Hardware-accelerated embeddings
Apple Silicon: MPS acceleration (automatic detection)
NVIDIA GPU: CUDA acceleration (automatic detection)
CPU Fallback: Universal compatibility
Model: SentenceTransformers with hardware optimization
Caching: Redis-based embedding cache
```

### **BMAD Integration**
```yaml
BMAD Core: Node v20 (headless, vendored in vendor/bmad/)
HTTP API Facade: Python FastAPI (on cerebral cluster)
CAEF Orchestrator: Python (gated execution)
WebMCP Server: Python FastAPI (on cerebral cluster)
Tool Registry: Python (cflow_platform.core.tool_registry)
```

### **Knowledge Management**
```yaml
Knowledge Graph: Supabase + pgvector indexing
RAG System: KnowledgeRAG with vector search
Document Storage: Supabase (cerebral_documents table)
Local Development: ChromaDB for testing
Sync: Bidirectional sync between local and remote
```

## 🌐 **Deployment Architecture**

### **Cerebral Cluster (Production)**
```yaml
WebMCP Server: mcp.cerebral.baerautotech.com
BMAD HTTP API: Python FastAPI facade
KnowledgeRAG: Supabase + pgvector
Deployment: Kubernetes manifests
Ingress: API Gateway with JWT auth
Service Mesh: istio/linkerd (if applicable)
Secrets: Vault-managed
```

### **cflow-platform (Development)**
```yaml
Tool Definitions: Python tool registry
Local Testing: HTTP client to cluster APIs
No Local MCP: All MCP servers run on cluster
Direct Client: execute_mcp_tool() for local testing
```

## 📱 **Cross-Platform Strategy**

### **React Native + React Native Web**
```yaml
Mobile Apps: Native iOS/Android performance
Web Apps: React Native Web compilation to web
Wearable Apps: React Native for Apple Watch/WearOS
Shared Components: Single component library
Platform-Specific: Conditional rendering when needed
Performance: Native performance on all platforms
```

### **Code Sharing Benefits**
```yaml
Business Logic: 100% shared across platforms
UI Components: 90%+ shared with platform adaptations
State Management: Shared Redux stores
API Integration: Shared HTTP clients
Testing: Shared test suites
```

## 🔒 **Security & Compliance**

### **Security Stack**
```yaml
Authentication: JWT tokens
Authorization: Role-based access control
Secrets Management: Vault
Data Encryption: At rest and in transit
API Security: FastAPI built-in security features
Network Security: Service mesh (when applicable)
```

### **Compliance**
```yaml
SOC2: Change management, logical access, monitoring
GDPR: Data minimization, right to erasure
HIPAA: PHI segregation, access logs, encryption
Data Retention: Automated deletion workflows
Audit Logging: Complete activity tracking
```

## 🚀 **Performance & Scalability**

### **Backend Performance**
```yaml
FastAPI: High-performance async framework
Database: PostgreSQL with connection pooling
Caching: Redis for session and data caching
CDN: MinIO S3 with CDN capabilities
Load Balancing: Kubernetes ingress
Auto-scaling: HPA based on metrics
```

### **Frontend Performance**
```yaml
React Native: Native performance on mobile
React Native Web: Optimized web compilation
Code Splitting: Dynamic imports
Lazy Loading: Component-level lazy loading
Caching: HTTP caching + local storage
```

## 📊 **Monitoring & Observability**

### **Monitoring Stack**
```yaml
Metrics: Prometheus
Dashboards: Grafana
Logging: Structured JSON logs
Tracing: OpenTelemetry (when implemented)
Alerts: Prometheus alerting
Health Checks: FastAPI health endpoints
```

### **Key Metrics**
```yaml
API Performance: p95 latency, throughput
Database: Query performance, connection pools
Cache: Hit rates, memory usage
AI/ML: Token usage, model performance
Infrastructure: CPU, memory, disk usage
```

## 🔄 **Integration Points**

### **BMAD Integration**
```yaml
Planning Agents: Analyst, PM, Architect, SM, Dev, QA
Document Types: PRD, Architecture, Story
Workflow: PRD → Architecture → Story → CAEF execution
Storage: Supabase (cerebral_documents table)
Indexing: Knowledge Graph (agentic_knowledge_chunks)
```

### **CAEF Integration**
```yaml
Orchestrator: Python-based multi-agent execution
Gates: Planning completion gates before codegen
Execution: Code/test/validation agents
Results: Stored in Supabase with audit trails
```

### **Knowledge Management**
```yaml
RAG: KnowledgeRAG for semantic search
KG: Knowledge Graph for relationship mapping
Sync: Bidirectional sync between local and remote
Search: Vector-based semantic search
```

## 📚 **Documentation Standards**

### **Documentation Stack**
```yaml
Format: Markdown for developer docs
Diagrams: Mermaid for architecture diagrams
API Docs: OpenAPI/Swagger (auto-generated)
Code Docs: Python docstrings + TypeScript JSDoc
Architecture: Architecture Decision Records (ADRs)
```

### **Documentation Locations**
```yaml
Engineering: docs/engineering/
Plans: docs/plans/
Architecture: docs/architecture/
Agentic Plan: docs/agentic-plan/
BMAD: vendor/bmad/docs/
```

## 🎯 **Key Differentiators**

### **❌ What We DON'T Use**
```yaml
Backend: Node.js/Express (we use Python FastAPI)
Cloud Storage: AWS S3 (we use MinIO S3)
Web Framework: React (we use React Native Web)
AI Acceleration: Vendor-specific only (we support any GPU)
Package Management: pip/poetry (we use UV)
```

### **✅ What We DO Use**
```yaml
Backend: Full Python FastAPI stack
Frontend: React Native + React Native Web
Storage: Self-hosted MinIO S3
AI/ML: Hardware-agnostic GPU acceleration
Package Management: Modern UV tooling
Infrastructure: Self-hosted and cloud-agnostic
```

## 🔍 **Verification Checklist**

### **Tech Stack Verification**
- [x] Frontend: React Native + React Native Web + TypeScript
- [x] Backend: Python 3.11 + FastAPI (no Node.js/Express)
- [x] AI/ML: Hardware-agnostic GPU support
- [x] Storage: MinIO S3 (not AWS cloud)
- [x] Package Management: UV (not pip/poetry)
- [x] Database: PostgreSQL (Supabase)
- [x] Caching: Redis
- [x] Containerization: Docker + Kubernetes

### **Integration Verification**
- [x] BMAD: Headless services with Python FastAPI facade
- [x] CAEF: Python orchestrator with gated execution
- [x] Knowledge Graph: Supabase + pgvector indexing
- [x] MCP: WebMCP server on cerebral cluster
- [x] Sync: Bidirectional local/remote sync

## 📋 **Summary**

**CFlow Platform** is a **modern, self-hosted, cross-platform development ecosystem** featuring:

- **Full Python FastAPI Backend**: No Node.js/Express dependencies
- **React Native + React Native Web Frontend**: True cross-platform development
- **Hardware-Agnostic AI/ML**: Supports any available GPU hardware
- **Self-Hosted Infrastructure**: MinIO S3, private Cerebral cluster
- **Modern Python Tooling**: UV package management, virtual environments
- **Comprehensive Integration**: BMAD, CAEF, Knowledge Graph, MCP

This architecture provides **maximum flexibility**, **vendor independence**, and **cross-platform compatibility** while maintaining **high performance** and **modern development practices**.

---

**This document is the authoritative reference for CFlow Platform technical stack. All other documentation should reference this document for consistency.**
