# BMAD Git Workflow Implementation

## Overview

The BMAD Git Workflow provides automated git commit and push workflows specifically designed for BMAD workflow engine integration, including comprehensive change tracking and validation.

## Features

### 1. Automated Git Commit Workflow
- **BMAD Context Integration**: Commits are tagged with workflow ID, project ID, and document references
- **Structured Commit Messages**: Standardized commit message format with BMAD metadata
- **Change Tracking**: Comprehensive tracking of all changes with database persistence
- **Validation Integration**: Optional pre-commit validation with configurable checks

### 2. Automated Git Push Workflow
- **Remote Repository Integration**: Push to configured remote repositories
- **Branch Management**: Support for multiple branches and branch-specific pushes
- **Push Status Tracking**: Track push status and output in database
- **Error Handling**: Comprehensive error handling and rollback capabilities

### 3. Change Tracking and Validation
- **Comprehensive Validation**: Multi-level validation before commits
- **Git Repository Checks**: Verify repository status and uncommitted changes
- **BMAD Document Consistency**: Validate document state and relationships
- **Workflow State Validation**: Ensure workflow state consistency
- **Historical Tracking**: Complete audit trail of all git operations

## Database Schema

### bmad_commit_tracking
Tracks all BMAD-related commits with comprehensive metadata.

```sql
CREATE TABLE bmad_commit_tracking (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    commit_hash TEXT NOT NULL,
    branch TEXT NOT NULL,
    commit_message TEXT NOT NULL,
    document_ids TEXT[] DEFAULT '{}',
    validation_results JSONB DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'committed',
    pushed BOOLEAN DEFAULT FALSE,
    push_output TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### bmad_validation_results
Stores validation results for all git workflow operations.

```sql
CREATE TABLE bmad_validation_results (
    validation_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    validation_type TEXT NOT NULL DEFAULT 'comprehensive',
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    checks JSONB DEFAULT '{}',
    overall_status TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### bmad_git_workflow_status
Tracks the current status of git workflows.

```sql
CREATE TABLE bmad_git_workflow_status (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    current_step TEXT,
    last_commit_hash TEXT,
    last_push_hash TEXT,
    validation_status TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## MCP Tools

### bmad_git_commit_changes
Commit BMAD workflow changes with validation and tracking.

**Parameters:**
- `workflow_id` (string, required): BMAD workflow identifier
- `project_id` (string, required): Project identifier
- `changes_summary` (string, required): Human-readable summary of changes
- `document_ids` (array, optional): List of document IDs that were modified
- `validate` (boolean, optional): Whether to run validation before commit

**Example:**
```json
{
  "workflow_id": "prd_creation_workflow",
  "project_id": "project_123",
  "changes_summary": "Created PRD and updated Architecture documents",
  "document_ids": ["doc_456", "doc_789"],
  "validate": true
}
```

### bmad_git_push_changes
Push BMAD workflow changes to remote repository.

**Parameters:**
- `tracking_id` (string, required): BMAD commit tracking ID
- `remote` (string, optional): Remote repository name (default: "origin")
- `branch` (string, optional): Branch to push (defaults to current branch)

**Example:**
```json
{
  "tracking_id": "track_123",
  "remote": "origin",
  "branch": "main"
}
```

### bmad_git_validate_changes
Validate BMAD workflow changes before commit.

**Parameters:**
- `workflow_id` (string, required): BMAD workflow identifier
- `project_id` (string, required): Project identifier
- `validation_type` (string, optional): Type of validation to perform (default: "comprehensive")

**Example:**
```json
{
  "workflow_id": "prd_creation_workflow",
  "project_id": "project_123",
  "validation_type": "comprehensive"
}
```

### bmad_git_get_history
Get BMAD commit history for a project.

**Parameters:**
- `project_id` (string, required): Project identifier
- `limit` (integer, optional): Maximum number of commits to return (default: 10)

**Example:**
```json
{
  "project_id": "project_123",
  "limit": 20
}
```

## Usage Examples

### Complete Workflow Example

```python
from cflow_platform.core.bmad_git_workflow import BMADGitWorkflow

# Initialize git workflow
git_workflow = BMADGitWorkflow()

# Validate changes before commit
validation = await git_workflow.validate_bmad_changes(
    workflow_id="prd_creation_workflow",
    project_id="project_123",
    validation_type="comprehensive"
)

if validation["success"] and validation["validation_results"]["overall_status"] == "passed":
    # Commit changes
    commit_result = await git_workflow.commit_bmad_changes(
        workflow_id="prd_creation_workflow",
        project_id="project_123",
        changes_summary="Created PRD and updated Architecture documents",
        document_ids=["doc_456", "doc_789"],
        validation_results=validation["validation_results"]
    )
    
    if commit_result["success"]:
        # Push changes
        push_result = await git_workflow.push_bmad_changes(
            tracking_id=commit_result["tracking_id"],
            remote="origin",
            branch="main"
        )
        
        if push_result["success"]:
            print("Changes successfully committed and pushed!")
        else:
            print(f"Push failed: {push_result['error']}")
    else:
        print(f"Commit failed: {commit_result['error']}")
else:
    print("Validation failed, skipping commit")
```

### Convenience Functions

```python
from cflow_platform.core.bmad_git_workflow import (
    commit_bmad_workflow_changes,
    push_bmad_workflow_changes,
    validate_bmad_workflow_changes
)

# Use convenience functions
commit_result = await commit_bmad_workflow_changes(
    workflow_id="prd_creation_workflow",
    project_id="project_123",
    changes_summary="Created PRD document"
)

push_result = await push_bmad_workflow_changes(
    tracking_id=commit_result["tracking_id"]
)
```

## Validation Types

### Comprehensive Validation
- Git repository status check
- Uncommitted changes detection
- BMAD document consistency validation
- Workflow state consistency check
- Active HIL sessions verification

### Quick Validation
- Git repository status check
- Basic uncommitted changes detection

### Custom Validation
- Configurable validation checks
- Custom validation rules
- Integration with external validation systems

## Error Handling

The git workflow system includes comprehensive error handling:

- **Git Operation Failures**: Detailed error messages for git command failures
- **Database Connection Issues**: Graceful fallback when Supabase is unavailable
- **Validation Failures**: Clear reporting of validation issues
- **Network Issues**: Retry mechanisms for push operations
- **Permission Errors**: Clear error messages for git permission issues

## Migration and Setup

### Database Migration

```python
from cflow_platform.core.git_workflow_migration import run_git_workflow_migration

# Run migration to create required tables
migration_result = await run_git_workflow_migration()
if migration_result["success"]:
    print("Git workflow tables created successfully")
else:
    print(f"Migration failed: {migration_result['error']}")
```

### Verification

```python
from cflow_platform.core.git_workflow_migration import GitWorkflowMigration

migration = GitWorkflowMigration()
verification = await migration.verify_tables_exist()

if verification["all_tables_exist"]:
    print("All required tables exist")
else:
    print(f"Missing tables: {verification['missing_tables']}")
```

## Integration with BMAD Workflows

The git workflow system is fully integrated with BMAD workflows:

1. **Workflow Completion**: Automatic git operations when workflows complete
2. **HIL Integration**: Git operations respect HIL session states
3. **Document Tracking**: Automatic tracking of document changes
4. **Status Reporting**: Git status integrated into workflow status
5. **Error Recovery**: Git operations support workflow error recovery

## Security Considerations

- **Credential Management**: Uses existing Supabase authentication
- **Permission Checks**: Validates git repository permissions
- **Audit Trail**: Complete audit trail of all git operations
- **Access Control**: Respects existing project access controls
- **Data Protection**: Encrypted storage of sensitive git metadata

## Performance Considerations

- **Async Operations**: All operations are asynchronous for better performance
- **Connection Pooling**: Reuses Supabase connections
- **Batch Operations**: Supports batch commit and push operations
- **Caching**: Caches validation results to avoid redundant checks
- **Optimized Queries**: Database queries optimized for performance

## Troubleshooting

### Common Issues

1. **Supabase Connection Issues**
   - Check environment variables
   - Verify network connectivity
   - Check Supabase service status

2. **Git Repository Issues**
   - Ensure you're in a git repository
   - Check git configuration
   - Verify repository permissions

3. **Validation Failures**
   - Review validation results
   - Check document consistency
   - Verify workflow state

4. **Push Failures**
   - Check remote repository access
   - Verify branch permissions
   - Check for conflicts

### Debug Mode

Enable debug logging by setting environment variables:

```bash
export BMAD_GIT_DEBUG=1
export BMAD_GIT_VERBOSE=1
```

## Future Enhancements

- **Branch Management**: Advanced branch creation and management
- **Conflict Resolution**: Automatic conflict detection and resolution
- **Multi-Repository Support**: Support for multiple git repositories
- **Advanced Validation**: Custom validation plugins
- **Integration Hooks**: Pre/post commit hooks integration
- **Performance Monitoring**: Git operation performance metrics
