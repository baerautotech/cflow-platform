# Technical Decision Log

## Decision: SHA-Based Deployments
**Date:** 2025-01-XX  
**Context:** Need for reliable, traceable deployments to cerebral cluster  
**Decision:** Implement SHA-based Docker image tagging and Kubernetes deployment updates  
**Rationale:** 
- Enables precise rollbacks to specific commits
- Provides deployment traceability and audit trail
- Prevents deployment confusion and version mismatches
- Supports GitHub CI/CD integration
**Consequences:**
- All deployments must use GitHub CI/CD workflows
- Docker images must be tagged with commit SHA
- Kubernetes deployments must be updated with SHA tags
- Direct cluster pushes are prohibited
**Status:** Implemented  
**Review Date:** 2025-04-XX

## Decision: SSH-Based Cerebral Cluster Deployment
**Date:** 2025-01-XX  
**Context:** Need for secure deployment to cerebral cluster (10.34.0.0/24)  
**Decision:** Use SSH-based deployment via GitHub Actions  
**Rationale:**
- Maintains security by using SSH keys
- Enables automated deployment via CI/CD
- Provides consistent deployment process
- Supports file transfer and remote command execution
**Consequences:**
- SSH keys must be configured in GitHub Secrets
- All deployments go through SSH connection
- Files must be copied to cluster before building
- Docker builds execute on cluster, not locally
**Status:** Implemented  
**Review Date:** 2025-04-XX

## Decision: GitHub CI/CD Integration
**Date:** 2025-01-XX  
**Context:** Need for automated, reliable deployment pipeline  
**Decision:** Use GitHub Actions for all deployments  
**Rationale:**
- Provides automated testing and validation
- Enables deployment audit trail
- Supports environment-specific configurations
- Integrates with GitHub's security features
**Consequences:**
- All deployments must be triggered by GitHub events
- Workflow files must be maintained in `.github/workflows/`
- Secrets must be managed via GitHub Secrets
- Manual deployments are discouraged
**Status:** Implemented  
**Review Date:** 2025-04-XX

## Decision: File Organization Structure
**Date:** 2025-01-XX  
**Context:** Need for consistent file organization across project  
**Decision:** Implement strict directory structure for different file types  
**Rationale:**
- Prevents files from being placed in root directory
- Enables better project organization
- Supports automated tooling and validation
- Improves maintainability
**Consequences:**
- Docker files must be in `infrastructure/docker/`
- Kubernetes manifests must be in `infrastructure/kubernetes/`
- Scripts must be in `scripts/`
- Documentation must be in `docs/`
- Pre-commit hooks must validate file placement
**Status:** Implemented  
**Review Date:** 2025-04-XX

## Decision: No Emojis in Source Code
**Date:** 2025-01-XX  
**Context:** Linting rules prohibit emojis in source files  
**Decision:** Remove all emoji characters from Python source files  
**Rationale:**
- Maintains code professionalism
- Prevents linting errors
- Ensures consistent logging format
- Supports automated tooling
**Consequences:**
- All emoji characters must be removed from `.py` files
- Logging must use plain text format
- Pre-commit hooks must validate emoji absence
- Runtime logs may still include emojis
**Status:** Implemented  
**Review Date:** 2025-04-XX

## Decision: Company Memory System
**Date:** 2025-01-XX  
**Context:** Need for institutional knowledge management  
**Decision:** Implement centralized knowledge base in `.cerebraflow/`  
**Rationale:**
- Prevents repeated mistakes and decisions
- Enables knowledge sharing across team
- Provides decision audit trail
- Facilitates troubleshooting and onboarding
**Consequences:**
- All decisions must be documented
- Knowledge base must be regularly updated
- Progress must be tracked in iterations
- Troubleshooting guides must be maintained
**Status:** Implemented  
**Review Date:** 2025-04-XX
