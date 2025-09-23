# BMAD Master Orchestration System

## Overview

The BMAD Master Orchestration System coordinates multi-agent parallel background workflows for codedev → testing → validation → commit/push cycles. This system integrates BMAD workflows with Cerebral's task management and agent coordination.

## Architecture Components

### 1. BMAD Master Orchestrator
- **Role**: Master coordinator for all BMAD workflows
- **Capabilities**: Can execute any BMAD agent task without switching
- **Integration**: Connects to Cerebral task management system

### 2. Story Shard Management
- **PO Agent**: Shards PRD/Architecture documents into manageable pieces
- **SM Agent**: Creates stories from sharded documents
- **Task Manager**: Tracks story completion and status

### 3. Multi-Agent Parallel Background Workflow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   BMAD Master   │───▶│   Task Manager   │───▶│  CodeDev Agent  │
│  Orchestrator   │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Story Shards   │    │  Completion      │    │  Implementation │
│  Creation       │    │  Tracking        │    │  & Testing      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  QA Validation  │    │  Auto-Commit     │    │  Push to Repo   │
│  & Review       │    │  & Push          │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Workflow Initiation

### 1. BMAD Master Workflow Trigger
```python
# BMAD Master initiates workflow
bmad_master.orchestrate_workflow({
    "workflow_type": "greenfield-fullstack",
    "project_context": {...},
    "parallel_execution": True
})
```

### 2. Story Shard Creation
```python
# PO Agent shards documents
po_agent.shard_documents(
    prd_path="docs/prd.md",
    architecture_path="docs/architecture.md",
    output_dir="docs/sharded/"
)
```

### 3. Task Manager Integration
```python
# Task Manager tracks story completion
task_manager.create_story_tasks(
    shard_paths=["docs/sharded/epic1/", "docs/sharded/epic2/"],
    completion_callback=trigger_codedev_agent
)
```

### 4. CodeDev Agent Activation
```python
# CodeDev Agent implements stories
codedev_agent.implement_story(
    story_id="story_001",
    implementation_context={
        "files": [...],
        "tests": [...],
        "dependencies": [...]
    }
)
```

## Parallel Background Components

### 1. Testing Pipeline
- **Unit Tests**: Automated pytest execution
- **Integration Tests**: End-to-end validation
- **Linting**: Pre-commit hooks validation

### 2. Validation Pipeline
- **QA Review**: Code quality assessment
- **Security Scan**: Vulnerability detection
- **Performance Check**: Performance metrics validation

### 3. Commit/Push Pipeline
- **Auto-Commit**: When tests pass and hooks succeed
- **Branch Management**: Feature branch creation and merging
- **CI/CD Integration**: Automated deployment triggers

## Task Manager Integration

### Story Completion Tracking
```python
class BMADTaskManager:
    def track_story_completion(self, story_id: str):
        """Track story completion and trigger next workflow step"""
        story = self.get_story(story_id)
        
        if story.status == "completed":
            # Trigger CodeDev Agent
            self.trigger_codedev_agent(story)
            
        elif story.status == "review":
            # Trigger QA Agent
            self.trigger_qa_agent(story)
            
        elif story.status == "approved":
            # Trigger implementation
            self.trigger_implementation(story)
```

### Multi-Agent Coordination
```python
class BMADOrchestrator:
    def coordinate_agents(self, workflow_context: Dict):
        """Coordinate multiple agents in parallel"""
        
        # Parallel agent execution
        tasks = [
            self.execute_agent("po", "shard_documents"),
            self.execute_agent("sm", "create_stories"),
            self.execute_agent("architect", "validate_architecture")
        ]
        
        # Wait for completion
        results = await asyncio.gather(*tasks)
        
        # Trigger next phase
        self.trigger_implementation_phase(results)
```

## Integration Points

### 1. Cerebral Task Management
- **Task Creation**: BMAD workflows create tasks in Cerebral
- **Status Updates**: Real-time status synchronization
- **Completion Tracking**: Automated workflow progression

### 2. Git Operations
- **Auto-Commit**: `cflow_platform/core/git_ops.py`
- **Branch Management**: Feature branch creation
- **Merge Coordination**: Automated merge when ready

### 3. Vectorization Service
- **Commit Processing**: `cflow_platform/core/services/enterprise_codebase_vectorization_service.py`
- **RAG Integration**: Knowledge base updates
- **Context Assembly**: Enhanced agent context

## Workflow States

### Story Lifecycle
1. **Draft**: Story created by SM Agent
2. **Approved**: Story reviewed and approved
3. **In Progress**: CodeDev Agent implementing
4. **Review**: QA Agent reviewing implementation
5. **Completed**: Story fully implemented and tested
6. **Merged**: Changes committed and pushed

### Task Manager States
1. **Pending**: Task created, waiting for execution
2. **Running**: Agent actively working on task
3. **Completed**: Task finished successfully
4. **Failed**: Task encountered errors
5. **Retrying**: Task being retried after failure

## Orchestration Commands

### BMAD Master Commands
```bash
# Initiate full workflow
bmad-master orchestrate --workflow greenfield-fullstack --parallel

# Check workflow status
bmad-master status --workflow-id <id>

# Trigger specific phase
bmad-master trigger --phase implementation --story-id <id>
```

### Task Manager Commands
```bash
# List active stories
task-manager list --status in-progress

# Check story completion
task-manager status --story-id <id>

# Trigger next workflow step
task-manager trigger-next --story-id <id>
```

## Monitoring and Observability

### Workflow Metrics
- **Story Completion Rate**: Percentage of stories completed
- **Agent Performance**: Time per agent task
- **Pipeline Efficiency**: End-to-end workflow time

### Error Handling
- **Retry Logic**: Automatic retry on transient failures
- **Fallback Strategies**: Alternative execution paths
- **Error Reporting**: Detailed error logs and notifications

## Configuration

### BMAD Master Configuration
```yaml
bmad_master:
  orchestrator:
    parallel_execution: true
    max_concurrent_agents: 5
    timeout_seconds: 3600
  
  workflows:
    greenfield-fullstack:
      phases: [planning, sharding, story_creation, implementation, testing, validation]
      parallel_phases: [story_creation, testing]
    
    brownfield-enhancement:
      phases: [analysis, enhancement_planning, implementation, testing]
      parallel_phases: [analysis, testing]
```

### Task Manager Configuration
```yaml
task_manager:
  story_tracking:
    auto_trigger_codedev: true
    completion_threshold: 0.8
    retry_attempts: 3
  
  integration:
    cerebral_sync: true
    git_ops: true
    vectorization: true
```

## Future Enhancements

### 1. Advanced Orchestration
- **Dynamic Workflow**: Adaptive workflow based on project context
- **Agent Learning**: ML-based agent performance optimization
- **Predictive Analytics**: Workflow completion time prediction

### 2. Enhanced Integration
- **CI/CD Pipeline**: Direct integration with deployment systems
- **Monitoring Integration**: Real-time workflow monitoring
- **Alert System**: Proactive issue detection and notification

### 3. Scalability Improvements
- **Distributed Execution**: Multi-node agent execution
- **Load Balancing**: Intelligent agent workload distribution
- **Resource Optimization**: Dynamic resource allocation

---

*This document describes the BMAD Master Orchestration System that coordinates multi-agent parallel background workflows for codedev → testing → validation → commit/push cycles.*
