# BMAD Basic Workflow Implementations (Story 1.5)

This document describes the basic BMAD workflow implementations that provide simplified workflows for creating PRD, Architecture, and Story documents using BMAD templates and Cerebral storage.

## Overview

The basic workflow implementations provide:

1. **Basic PRD Creation Workflow** - Creates PRD documents using BMAD templates
2. **Basic Architecture Creation Workflow** - Creates Architecture documents using BMAD templates  
3. **Basic Story Creation Workflow** - Creates Story documents using BMAD templates
4. **Complete Basic Workflow** - Orchestrates all three workflows in sequence
5. **Workflow Status Management** - Tracks and reports workflow progress

## Architecture

### Core Components

- **`BasicWorkflowImplementations`** - Main class containing workflow logic
- **`BMADHandlers`** - Handles document creation and storage
- **`BMADHILIntegration`** - Manages Human-in-the-Loop interactions
- **Tool Registry Integration** - Exposes workflows as MCP tools

### Workflow Flow

```
Project Input → PRD Creation → Architecture Creation → Story Creation → Implementation Ready
     ↓              ↓              ↓              ↓              ↓
   Goals      BMAD Template   BMAD Template   BMAD Template   Dev Agent
 Background   Cerebral Storage Cerebral Storage Cerebral Storage   Ready
 Tech Stack      HIL Check      HIL Check      HIL Check
 User Stories    (if needed)    (if needed)    (if needed)
```

## Available Tools

### 1. Basic PRD Workflow

**Tool**: `bmad_basic_prd_workflow`

Creates a basic PRD document using BMAD templates and Cerebral storage.

**Parameters**:
- `project_name` (required): Name of the project
- `goals` (optional): List of project goals
- `background` (optional): Background context for the project

**Returns**:
- `workflow_status`: "completed", "paused_for_hil", or "error"
- `doc_id`: ID of created PRD document
- `hil_session_id`: ID of HIL session (if paused)
- `next_action`: Recommended next step
- `step_results`: Detailed results for each workflow step

**Example**:
```json
{
  "project_name": "My Web App",
  "goals": ["Create user management", "Implement dashboard"],
  "background": "A modern web application for task management"
}
```

### 2. Basic Architecture Workflow

**Tool**: `bmad_basic_architecture_workflow`

Creates a basic Architecture document using BMAD templates and Cerebral storage.

**Parameters**:
- `project_name` (required): Name of the project
- `prd_id` (required): ID of the PRD document
- `tech_stack` (optional): List of technologies to use

**Returns**:
- `workflow_status`: "completed", "paused_for_hil", or "error"
- `doc_id`: ID of created Architecture document
- `prd_id`: ID of the PRD document
- `hil_session_id`: ID of HIL session (if paused)
- `next_action`: Recommended next step
- `step_results`: Detailed results for each workflow step

**Example**:
```json
{
  "project_name": "My Web App",
  "prd_id": "prd-12345",
  "tech_stack": ["Python", "React", "PostgreSQL"]
}
```

### 3. Basic Story Workflow

**Tool**: `bmad_basic_story_workflow`

Creates a basic Story document using BMAD templates and Cerebral storage.

**Parameters**:
- `project_name` (required): Name of the project
- `prd_id` (required): ID of the PRD document
- `arch_id` (required): ID of the Architecture document
- `user_stories` (optional): List of user stories

**Returns**:
- `workflow_status`: "completed", "paused_for_hil", or "error"
- `doc_id`: ID of created Story document
- `prd_id`: ID of the PRD document
- `arch_id`: ID of the Architecture document
- `hil_session_id`: ID of HIL session (if paused)
- `next_action`: Recommended next step
- `step_results`: Detailed results for each workflow step

**Example**:
```json
{
  "project_name": "My Web App",
  "prd_id": "prd-12345",
  "arch_id": "arch-67890",
  "user_stories": ["As a user, I want to login", "As a user, I want to view my dashboard"]
}
```

### 4. Complete Basic Workflow

**Tool**: `bmad_basic_complete_workflow`

Runs the complete basic workflow: PRD → Architecture → Story in sequence.

**Parameters**:
- `project_name` (required): Name of the project
- `goals` (optional): List of project goals
- `background` (optional): Background context for the project
- `tech_stack` (optional): List of technologies to use
- `user_stories` (optional): List of user stories

**Returns**:
- `workflow_status`: "completed", "paused_for_hil", or "error"
- `project_context`: Complete project context
- `documents`: Object containing all document IDs
- `next_action`: Recommended next step
- `step_results`: Detailed results for all workflow steps
- `completion_percentage`: Overall completion percentage

**Example**:
```json
{
  "project_name": "My Web App",
  "goals": ["Create user management", "Implement dashboard"],
  "background": "A modern web application for task management",
  "tech_stack": ["Python", "React", "PostgreSQL"],
  "user_stories": ["As a user, I want to login", "As a user, I want to view my dashboard"]
}
```

### 5. Workflow Status

**Tool**: `bmad_basic_workflow_status`

Gets the current status of basic BMAD workflows for a project.

**Parameters**:
- `project_id` (required): ID of the project

**Returns**:
- `success`: Boolean indicating if status retrieval was successful
- `workflow_status`: Object containing workflow status information
- `message`: Status message

**Example**:
```json
{
  "project_id": "project-12345"
}
```

## Human-in-the-Loop (HIL) Integration

The basic workflows automatically detect when documents need additional input and trigger HIL sessions:

### HIL Triggers

- **PRD**: When template placeholders are detected in the document
- **Architecture**: When template placeholders are detected in the document
- **Story**: When template placeholders are detected in the document

### HIL Session Flow

1. **Detection**: Workflow detects incomplete sections
2. **Session Creation**: HIL session is automatically created
3. **User Interaction**: User completes document via interactive session
4. **Resume**: Workflow can be resumed after HIL completion

### HIL Session Management

- **Session ID**: Each HIL session has a unique identifier
- **Document Context**: Session includes document and workflow context
- **Completion Tracking**: Progress is tracked throughout the session
- **Resume Capability**: Workflows can be resumed after HIL completion

## Workflow States

### Workflow Status Values

- **`completed`**: Workflow completed successfully
- **`paused_for_hil`**: Workflow paused for HIL interaction
- **`error`**: Workflow failed with error

### Current Step Values

- **`"Workflow Not Started"`**: No documents created yet
- **`"PRD Created"`**: PRD document exists
- **`"Architecture Created"`**: Architecture document exists
- **`"Stories Created"`**: Story document exists

### Next Action Values

- **`"Create PRD"`**: Start by creating PRD
- **`"Create Architecture"`**: Create Architecture document
- **`"Create Stories"`**: Create Story document
- **`"Review Stories"`**: Review completed stories
- **`"Begin implementation with Dev agent"`**: Ready for development

## Error Handling

### Common Error Scenarios

1. **Document Creation Failures**: When BMAD handlers fail to create documents
2. **Validation Failures**: When required documents don't exist
3. **HIL Integration Failures**: When HIL sessions can't be created
4. **Storage Failures**: When Cerebral storage is unavailable

### Error Response Format

```json
{
  "workflow_status": "error",
  "message": "Descriptive error message",
  "error": "Technical error details",
  "step_results": [
    {
      "step": "step_name",
      "status": "error",
      "result": "error_details"
    }
  ]
}
```

## Usage Examples

### Example 1: Create PRD Only

```python
from cflow_platform.core.basic_workflow_implementations import create_basic_prd

result = await create_basic_prd(
    project_name="Task Management App",
    goals=["User authentication", "Task CRUD operations"],
    background="A web application for managing personal tasks"
)

if result["workflow_status"] == "paused_for_hil":
    print(f"HIL session started: {result['hil_session_id']}")
elif result["workflow_status"] == "completed":
    print(f"PRD created: {result['doc_id']}")
```

### Example 2: Complete Workflow

```python
from cflow_platform.core.basic_workflow_implementations import run_complete_basic_workflow

result = await run_complete_basic_workflow(
    project_name="E-commerce Platform",
    goals=["Product catalog", "Shopping cart", "Payment processing"],
    background="A modern e-commerce platform",
    tech_stack=["Python", "React", "PostgreSQL", "Redis"],
    user_stories=["As a customer, I want to browse products", "As a customer, I want to add items to cart"]
)

if result["workflow_status"] == "completed":
    print(f"All documents created successfully!")
    print(f"PRD: {result['documents']['prd_id']}")
    print(f"Architecture: {result['documents']['arch_id']}")
    print(f"Story: {result['documents']['story_id']}")
```

### Example 3: Check Workflow Status

```python
from cflow_platform.core.basic_workflow_implementations import get_basic_workflows

workflows = get_basic_workflows()
status = await workflows.get_workflow_status("project-12345")

print(f"Current step: {status['workflow_status']['current_step']}")
print(f"Next action: {status['workflow_status']['next_action']}")
print(f"Completion: {status['workflow_status']['completion_percentage']}%")
```

## Integration with BMAD Ecosystem

### BMAD Templates

The basic workflows use BMAD templates from `vendor/bmad/bmad-core/templates/`:

- **PRD Template**: `prd-tmpl.yaml`
- **Architecture Template**: `architecture-tmpl.yaml`
- **Story Template**: `story-tmpl.yaml`

### Cerebral Storage

Documents are stored in Cerebral storage (Supabase) with:

- **Document Table**: `cerebral_documents`
- **Knowledge Graph**: `agentic_knowledge_chunks`
- **Activity Tracking**: `cerebral_activities`

### MCP Integration

The workflows are exposed as MCP tools through:

- **Tool Registry**: `cflow_platform/core/tool_registry.py`
- **Direct Client**: `cflow_platform/core/direct_client.py`
- **WebMCP Server**: Available via HTTP API

## Testing

Comprehensive test suite available in `cflow_platform/tests/test_basic_workflow_implementations.py`:

- **Unit Tests**: Individual workflow component testing
- **Integration Tests**: End-to-end workflow testing
- **Error Handling Tests**: Error scenario testing
- **HIL Integration Tests**: Human-in-the-Loop testing
- **Mock-based Testing**: Isolated testing with mocks

Run tests with:
```bash
pytest cflow_platform/tests/test_basic_workflow_implementations.py -v
```

## Future Enhancements

### Planned Features

1. **Workflow Templates**: Pre-defined workflow templates for common project types
2. **Advanced HIL**: More sophisticated HIL interaction patterns
3. **Workflow Customization**: Customizable workflow steps and validation
4. **Integration Hooks**: Hooks for custom workflow extensions
5. **Performance Optimization**: Async optimization and caching

### Extension Points

1. **Custom Templates**: Support for custom BMAD templates
2. **Custom Validators**: Custom document validation logic
3. **Custom Storage**: Alternative storage backends
4. **Custom HIL**: Custom HIL interaction patterns

## Dependencies

### Required Dependencies

- **BMAD Core**: BMAD template system and workflow engine
- **Cerebral Storage**: Supabase for document storage
- **HIL Integration**: Human-in-the-Loop interaction system
- **MCP Framework**: Multi-Agent Coordination Platform

### Optional Dependencies

- **Redis**: For caching and session management
- **Monitoring**: For workflow performance tracking
- **Analytics**: For workflow usage analytics

## Conclusion

The BMAD Basic Workflow Implementations provide a solid foundation for creating PRD, Architecture, and Story documents using BMAD templates and Cerebral storage. They integrate seamlessly with the broader BMAD ecosystem and provide a clear path from project inception to implementation readiness.

The workflows are designed to be:
- **Simple**: Easy to use and understand
- **Robust**: Comprehensive error handling and validation
- **Flexible**: Support for HIL interactions and customization
- **Integrated**: Seamless integration with BMAD ecosystem
- **Testable**: Comprehensive test coverage

This implementation fulfills the requirements of Story 1.5 in the BMAD Phased Implementation Plan and provides a solid foundation for future workflow enhancements.
