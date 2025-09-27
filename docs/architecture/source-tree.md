## Source Tree (Dev Agent Always-Load)

Top-Level
- `bmad_api_service/`: BMAD API core service and integrations
- `cflow_platform/`: Core platform libs (MCP registry, executors)
- `infrastructure/kubernetes/`: Kubernetes manifests
- `docs/`: Architecture, stories, validation
- `vendor/bmad/`: Vendored BMAD core, agents, tasks, workflows

BMAD API Highlights
- `bmad_api_service/main.py`: Entry and route wiring
- `bmad_api_service/vendor_bmad_integration.py`: Vendor workflow execution
- `bmad_api_service/production_config.py`: Production guard config
- `bmad_api_service/performance_*`: Monitoring and optimization utilities

Platform Highlights
- `cflow_platform/core/tool_registry.py`: MCP tool registry
- `cflow_platform/core/direct_client.py`: MCP direct executor
- `cflow_platform/cli/`: Operational CLI utilities

Docs & Stories
- `docs/stories/`: Story files (e.g., `1.1.story.md`)
- `vendor/bmad/bmad-core/core-config.yaml`: Dev agent always-load list


