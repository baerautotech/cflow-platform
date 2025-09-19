# BMAD Setup Guide

Document version: 1.0  
Date: 2025-01-09  
Purpose: Complete setup guide for BMAD integration in cflow-platform

## Overview

This guide provides complete setup instructions for the BMAD (Breakthrough Method of Agile AI-driven Development) integration in the cflow-platform. BMAD replaces the CAEF orchestrator with a sophisticated multi-agent workflow system.

## Prerequisites

- Python 3.8+
- uv package manager
- Access to Supabase database
- Git repository access

## Installation

### 1. Install Dependencies

```bash
# Install required Python packages
uv add supabase httpx

# Verify installation
uv run python3 -c "import supabase, httpx; print('Dependencies installed successfully')"
```

### 2. Environment Configuration

Ensure your `.env` file in the project root contains:

```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### 3. Verify Installation

```bash
# Test BMAD workflow engine
cd /path/to/cflow-platform
PYTHONPATH=/path/to/cflow-platform uv run python3 -c "
from cflow_platform.core.bmad_workflow_engine import get_workflow_engine
engine = get_workflow_engine()
workflows = engine.get_available_workflows()
print(f'BMAD Workflows Available: {len(workflows)}')
for workflow in workflows[:3]:
    print(f'  - {workflow[\"id\"]}: {workflow[\"name\"]}')
"
```

## BMAD Components

### Core Components

1. **BMAD Workflow Engine** (`cflow_platform/core/bmad_workflow_engine.py`)
   - Executes BMAD workflows using YAML definitions
   - Integrates with BMAD agents and templates
   - Provides HIL (Human-in-the-Loop) integration

2. **BMAD Agents** (`cflow_platform/core/bmad_agents.py`)
   - Analyst, PM, Architect, SM, Dev, QA agents
   - Specialized personas with domain expertise
   - Integrated with Supabase for document storage

3. **BMAD Handlers** (`cflow_platform/handlers/bmad_handlers.py`)
   - MCP tool implementations for BMAD functionality
   - Document creation, management, and approval workflows
   - Git workflow integration

4. **BMAD HIL Integration** (`cflow_platform/core/bmad_hil_integration.py`)
   - Human-in-the-Loop session management
   - Interactive elicitation and approval workflows
   - Session state tracking

### Database Schema

BMAD uses the following Supabase tables:

- `cerebral_documents`: PRD, Architecture, Story documents
- `bmad_hil_sessions`: Human-in-the-Loop session tracking
- `bmad_commit_tracking`: Git workflow tracking
- `bmad_validation_results`: Validation and quality checks

## Usage

### Basic BMAD Workflow

```python
import asyncio
from cflow_platform.core.direct_client import execute_mcp_tool

async def create_prd():
    # Create a PRD document
    result = await execute_mcp_tool(
        'bmad_prd_create',
        project_name='My Project',
        goals=['Goal 1', 'Goal 2'],
        background='Project background'
    )
    print(f"PRD created: {result['doc_id']}")

# Run the workflow
asyncio.run(create_prd())
```

### Available BMAD Tools

The following BMAD tools are available via MCP:

#### Document Management
- `bmad_prd_create`: Create Product Requirements Document
- `bmad_prd_update`: Update PRD document
- `bmad_prd_get`: Get PRD document
- `bmad_arch_create`: Create Architecture Document
- `bmad_arch_update`: Update Architecture document
- `bmad_arch_get`: Get Architecture document
- `bmad_story_create`: Create Story document
- `bmad_story_update`: Update Story document
- `bmad_story_get`: Get Story document

#### Workflow Management
- `bmad_workflow_list`: List available workflows
- `bmad_workflow_get`: Get workflow details
- `bmad_workflow_execute`: Execute a workflow
- `bmad_workflow_status`: Get workflow status

#### HIL Sessions
- `bmad_hil_start_session`: Start HIL session
- `bmad_hil_continue_session`: Continue HIL session
- `bmad_hil_end_session`: End HIL session
- `bmad_hil_session_status`: Get session status

#### Git Integration
- `bmad_git_commit_changes`: Commit BMAD workflow changes
- `bmad_git_push_changes`: Push changes to remote
- `bmad_git_validate_changes`: Validate changes before commit
- `bmad_git_get_history`: Get commit history

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError: No module named 'supabase'**
   ```bash
   uv add supabase httpx
   ```

2. **Supabase client not available / "supabase_url is required"**
   - Check `.env` configuration in project root
   - Verify Supabase URL and keys are correct
   - Ensure `.env` file is in the project root directory

3. **BMAD workflow engine fails to load**
   - Ensure vendor/bmad directory exists
   - Check YAML files in vendor/bmad/bmad-core/workflows/

4. **Database connection issues**
   - Verify Supabase credentials
   - Check network connectivity
   - Ensure tables exist in database

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Development

### Adding New BMAD Tools

1. Add tool definition to `cflow_platform/core/tool_registry.py`
2. Implement handler in `cflow_platform/handlers/bmad_handlers.py`
3. Add routing in `cflow_platform/core/direct_client.py`
4. Test with `execute_mcp_tool`

### Testing

```bash
# Run BMAD integration tests
uv run python3 -m pytest cflow_platform/tests/test_bmad_*.py

# Test specific BMAD functionality
uv run python3 -c "
import asyncio
from cflow_platform.core.direct_client import execute_mcp_tool

async def test():
    result = await execute_mcp_tool('bmad_workflow_list')
    print(f'Workflows: {len(result.get(\"workflows\", []))}')

asyncio.run(test())
"
```

## Architecture

### BMAD Integration Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Cursor Agent  │    │  cflow-platform  │    │   Supabase DB   │
│                 │    │                  │    │                 │
│  @bmad-master   │───▶│  BMAD Handlers   │───▶│ cerebral_docs   │
│                 │    │                  │    │ bmad_hil_sess   │
│  Tool Calls     │    │  Workflow Engine │    │ bmad_commits    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  vendor/bmad/    │
                       │                  │
                       │  BMAD Templates  │
                       │  Agent Defs      │
                       │  Workflows       │
                       └──────────────────┘
```

### MCP Tool Flow

1. **Tool Call**: Cursor agent calls BMAD tool via MCP
2. **Routing**: `direct_client.py` routes to `bmad_handlers.py`
3. **Execution**: Handler executes BMAD functionality
4. **Storage**: Results stored in Supabase database
5. **Response**: Results returned to Cursor agent

## Migration from CAEF

### What Was Replaced

- ❌ `cflow_platform/core/orchestrator.py` (CAEF orchestrator)
- ❌ `cflow_platform/core/agent_loop.py` (CAEF agent loop)
- ❌ `cflow_platform/core/agents/` (CAEF generic agents)

### What Was Added

- ✅ `cflow_platform/core/bmad_workflow_engine.py` (BMAD workflow engine)
- ✅ `cflow_platform/core/bmad_agents.py` (BMAD specialized agents)
- ✅ `cflow_platform/core/bmad_hil_integration.py` (HIL integration)
- ✅ `cflow_platform/core/bmad_git_workflow.py` (Git workflow)
- ✅ `cflow_platform/handlers/bmad_handlers.py` (BMAD handlers)

### Rollback Plan

If BMAD integration fails, restore CAEF components:

```bash
# Restore CAEF files
git checkout HEAD~1 -- cflow_platform/core/orchestrator.py
git checkout HEAD~1 -- cflow_platform/core/agent_loop.py
git checkout HEAD~1 -- cflow_platform/core/agents/

# Revert imports in test files
git checkout HEAD~1 -- cflow_platform/tests/test_agent_loop_*.py
```

## Support

For issues with BMAD integration:

1. Check this setup guide
2. Review error logs
3. Test individual components
4. Check Supabase connectivity
5. Verify environment configuration

## References

- [BMAD-METHOD Repository](https://github.com/bmadcode/BMAD-METHOD)
- [BMAD Core Platform Integration Plan](docs/plans/BMAD_CORE_PLATFORM_INTEGRATION_PLAN.md)
- [BMAD Database Schema](docs/architecture/bmad_database_schema.md)
- [MCP Architecture](docs/architecture/MCP_ARCHITECTURE.md)
