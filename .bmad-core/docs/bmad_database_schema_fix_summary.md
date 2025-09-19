# BMAD Database Schema Fix Summary

## Issue Identified

The original issue was that we were trying to create `EPIC` documents in the database, but the database constraint `cerebral_documents_kind_check` only allows `PRD`, `ARCHITECTURE`, and `STORY` document types.

## Root Cause Analysis

After analyzing the BMAD documentation and source code, I discovered that **epics are NOT separate documents in BMAD**. Instead:

1. **Epics are sections within the PRD**: The PRD template includes epic sections that contain epic definitions
2. **Epics are created by sharding**: The PO agent uses the `shard-doc` task to split the PRD into separate epic files
3. **Epics are stored as files**: Epic files are stored in `docs/epics/` directory, not in the database

## BMAD Standard Workflow

The correct BMAD workflow for epic creation is:

1. **PRD Creation**: Contains epic sections with epic definitions
2. **PRD Sharding**: PO agent executes `shard-doc` task to split PRD into epic files
3. **Epic Files**: Individual epic files are created in `docs/epics/` directory
4. **Story Creation**: Stories are created from sharded epic files

## Fixes Implemented

### 1. Updated Epic Creation Method

**Before**: Tried to create `EPIC` document type in database
```python
"kind": "EPIC",  # This caused database constraint violation
```

**After**: Creates epic sharding task for PO agent to execute
```python
task_data = {
    "task_type": "epic_sharding",
    "status": "pending",
    "input_doc_id": prd_id,
    "output_path": "docs/epics/",
    "description": f"Execute shard-doc task to split PRD {prd_id} into epic files"
}
```

### 2. Updated Tool Registry

**Before**: Listed `EPIC` as valid document type
```python
"enum": ["PRD", "ARCH", "STORY", "EPIC"]
```

**After**: Removed `EPIC` from valid document types
```python
"enum": ["PRD", "ARCH", "STORY"]
```

### 3. Added Missing Helper Method

Added `_get_document()` method to retrieve documents from Supabase:
```python
async def _get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
    """Get a document by ID from Supabase."""
```

## Current Status

✅ **Database Schema**: No changes needed - the constraint is correct
✅ **Epic Creation Method**: Updated to follow BMAD standard workflow
✅ **Tool Registry**: Updated to remove invalid EPIC document type
✅ **Helper Methods**: Added missing `_get_document()` method

## Next Steps

### 1. Complete Epic Sharding Implementation

The epic creation now creates a sharding task, but we need to:
- Create `cerebral_tasks` table in Supabase
- Implement task execution by PO agent
- Add file system operations for epic file creation

### 2. Implement HIL Approval System

As identified in the previous analysis, we still need to implement:
- Interactive document creation with Q&A sessions
- Human approval gates throughout the workflow
- Workflow gate enforcement

### 3. Test Complete Workflow

Once both fixes are implemented, test the complete BMAD workflow:
- PRD → Architecture → Epic Sharding → Story Creation
- With proper HIL approval gates

## Key Learnings

1. **BMAD Architecture**: Epics are not database documents but file-based artifacts
2. **Sharding Process**: PRD sections are split into separate files using the `shard-doc` task
3. **PO Agent Role**: The PO agent is responsible for document sharding operations
4. **File-Based Workflow**: BMAD uses a hybrid approach of database documents + file artifacts

## Conclusion

The database schema was actually correct - we were trying to use it incorrectly. The fix involved understanding the true BMAD workflow and implementing epic creation as a sharding task rather than a document creation operation. This aligns with BMAD's philosophy of keeping the core lean while using file-based artifacts for complex document structures.
