## Product Requirements Document (PRD)

### Purpose
Integrate BMAD-METHOD as the authoritative planning/PM/story core of the Cerebral platform, supporting both greenfield (new projects) and brownfield (existing system enhancement) development workflows with comprehensive project type detection and workflow routing.

### Users
- Software development teams (internal and external)
- Project managers and architects
- Developers working on new projects (greenfield)
- Developers enhancing existing systems (brownfield)

### Functional Requirements
- **Project Type Detection**: Automatic detection of greenfield vs brownfield projects based on context and existing codebase analysis
- **Greenfield Workflow**: Complete BMAD workflow for new project development (PRD → Architecture → Story → CAEF)
- **Brownfield Workflow**: Enhanced BMAD workflow for existing system enhancement with documentation generation and integration strategy
- **Workflow Routing**: Automatic routing to appropriate greenfield or brownfield workflow based on project type
- **Template Management**: Dynamic template selection based on project type (greenfield vs brownfield templates)
- **Documentation Generation**: Comprehensive documentation generation from existing codebases for brownfield projects
- **Integration Strategy**: Planning for integration with existing systems, migration strategies, and backwards compatibility
- **Multi-Client Support**: Web/Mobile/Wearable UIs, IDE integration, and CLI tools

### Non‑Functional Requirements
- **Performance**: Project type detection <100ms, workflow routing <50ms, API response time <200ms (95th percentile)
- **Scalability**: Support for multiple tenants and projects with proper isolation
- **Reliability**: >99% uptime for project type detection and workflow routing
- **Security**: JWT-based authentication, tenant isolation, encryption at rest and in transit
- **Compliance**: SOC2/GDPR/HIPAA alignment with complete audit trails

### Constraints
- **BMAD Integration**: Must preserve complete BMAD ecosystem (agents, templates, tasks, workflows, checklists)
- **Cerebral Platform**: Must integrate with existing Cerebral platform architecture and services
- **Multi-Tenancy**: Must support tenant isolation and security requirements
- **Expansion Packs**: Must support BMAD expansion packs for domain-specific workflows

