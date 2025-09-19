# BMAD Cluster Epic Storage Design

## Problem Statement

In a multi-user cluster system, BMAD epics cannot be stored as local files because:
1. **Multi-user access**: Multiple users need to access the same epics
2. **Cluster architecture**: No local file system in containerized environment
3. **Centralized storage**: All documents must be stored centrally for consistency
4. **Database integration**: Epics need to be linked to other documents and workflows

## Solution: Database + Object Storage Hybrid

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │  Mobile Client  │    │   CLI Client    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     Cerebral Cluster      │
                    │                           │
                    │  ┌─────────────────────┐  │
                    │  │   Database Layer    │  │
                    │  │                     │  │
                    │  │ • Epic Metadata     │  │
                    │  │ • Epic References   │  │
                    │  │ • Epic Relationships│  │
                    │  │ • Epic Status       │  │
                    │  └─────────────────────┘  │
                    │                           │
                    │  ┌─────────────────────┐  │
                    │  │   Object Storage    │  │
                    │  │                     │  │
                    │  │ • Epic Content      │  │
                    │  │ • Epic Files        │  │
                    │  │ • Epic Attachments  │  │
                    │  └─────────────────────┘  │
                    └───────────────────────────┘
```

### Database Schema Updates

#### 1. Update Document Type Constraint

```sql
-- Update the existing constraint to include EPIC and other BMAD document types
ALTER TABLE cerebral_documents DROP CONSTRAINT IF EXISTS cerebral_documents_kind_check;
ALTER TABLE cerebral_documents ADD CONSTRAINT cerebral_documents_kind_check 
CHECK (kind IN ('PRD', 'ARCHITECTURE', 'STORY', 'EPIC', 'PROJECT_BRIEF', 'QA_GATE', 'QA_ASSESSMENT'));
```

#### 2. Epic-Specific Tables

```sql
-- Epic metadata and relationships
CREATE TABLE epic_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    epic_doc_id UUID REFERENCES cerebral_documents(id) ON DELETE CASCADE,
    epic_number INTEGER NOT NULL,
    epic_title VARCHAR(255) NOT NULL,
    epic_goal TEXT NOT NULL,
    epic_status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'approved', 'in_progress', 'completed'
    parent_prd_id UUID REFERENCES cerebral_documents(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Epic-story relationships
CREATE TABLE epic_stories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    epic_id UUID REFERENCES epic_metadata(id) ON DELETE CASCADE,
    story_doc_id UUID REFERENCES cerebral_documents(id) ON DELETE CASCADE,
    story_number INTEGER NOT NULL,
    story_title VARCHAR(255) NOT NULL,
    story_status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Epic content storage (for large epic content)
CREATE TABLE epic_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    epic_doc_id UUID REFERENCES cerebral_documents(id) ON DELETE CASCADE,
    content_type VARCHAR(50) DEFAULT 'markdown', -- 'markdown', 'html', 'json'
    content_size INTEGER,
    storage_location VARCHAR(500), -- S3 path or database reference
    content_hash VARCHAR(64), -- For integrity checking
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 3. Object Storage Integration

```sql
-- Object storage references
CREATE TABLE object_storage_refs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES cerebral_documents(id) ON DELETE CASCADE,
    storage_type VARCHAR(50) NOT NULL, -- 'epic_content', 'epic_files', 'attachments'
    bucket_name VARCHAR(100) NOT NULL,
    object_key VARCHAR(500) NOT NULL,
    object_size INTEGER,
    content_type VARCHAR(100),
    storage_metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Epic Creation Workflow

#### 1. Epic Creation Process

```python
async def bmad_epic_create_cluster(self, project_name: str, prd_id: str, arch_id: str) -> Dict[str, Any]:
    """Create epics in cluster database with proper multi-user support."""
    try:
        # 1. Run master checklist
        checklist_result = await self.bmad_master_checklist(prd_id, arch_id)
        if not checklist_result.get("checklist_passed", False):
            return {
                "success": False,
                "error": "Master checklist failed - cannot create epics",
                "checklist_results": checklist_result.get("results", {})
            }

        # 2. Get PRD document to extract epics
        prd_doc = await self._get_document(prd_id)
        if not prd_doc:
            return {"success": False, "error": "PRD document not found"}

        # 3. Parse PRD content to extract epic sections
        epics = await self._extract_epics_from_prd(prd_doc['content'])
        
        # 4. Create epic documents in database
        created_epics = []
        for epic_data in epics:
            epic_doc = await self._create_epic_document(
                project_id=prd_doc['project_id'],
                epic_data=epic_data,
                prd_id=prd_id,
                arch_id=arch_id
            )
            created_epics.append(epic_doc)

        return {
            "success": True,
            "epics_created": len(created_epics),
            "epic_ids": [epic['id'] for epic in created_epics],
            "message": f"Created {len(created_epics)} epics for {project_name}",
            "next_action": "create_stories_from_epics"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create epics: {str(e)}"
        }
```

#### 2. Epic Content Storage

```python
async def _create_epic_document(self, project_id: str, epic_data: Dict, prd_id: str, arch_id: str) -> Dict[str, Any]:
    """Create epic document in database with content storage."""
    
    # Create epic document record
    epic_doc_id = str(uuid.uuid4())
    epic_doc = {
        "id": epic_doc_id,
        "tenant_id": "00000000-0000-0000-0000-000000000100",
        "project_id": project_id,
        "kind": "EPIC",  # Now supported in database
        "version": 1,
        "status": "draft",
        "content": epic_data['content'],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Store in database
    result = await self.supabase_client.table("cerebral_documents").insert(epic_doc).execute()
    
    if result.data:
        # Create epic metadata
        epic_metadata = {
            "epic_doc_id": epic_doc_id,
            "epic_number": epic_data['number'],
            "epic_title": epic_data['title'],
            "epic_goal": epic_data['goal'],
            "epic_status": "draft",
            "parent_prd_id": prd_id
        }
        
        await self.supabase_client.table("epic_metadata").insert(epic_metadata).execute()
        
        # Store epic content in object storage if large
        if len(epic_data['content']) > 10000:  # 10KB threshold
            await self._store_epic_content_in_s3(epic_doc_id, epic_data['content'])
        
        # Index in Knowledge Graph
        await self._index_document_in_kg(epic_doc_id, epic_data['content'], 'EPIC')
        
        return epic_doc
    
    return None
```

#### 3. Epic Content Retrieval

```python
async def _get_epic_content(self, epic_doc_id: str) -> str:
    """Get epic content from database or object storage."""
    
    # Check if content is stored in object storage
    storage_ref = await self.supabase_client.table("object_storage_refs")\
        .select("*")\
        .eq("document_id", epic_doc_id)\
        .eq("storage_type", "epic_content")\
        .execute()
    
    if storage_ref.data:
        # Retrieve from S3
        return await self._get_content_from_s3(storage_ref.data[0])
    else:
        # Retrieve from database
        doc = await self._get_document(epic_doc_id)
        return doc['content'] if doc else ""
```

### API Endpoints for Epic Management

#### 1. Epic CRUD Operations

```python
# Create epic
POST /api/bmad/epics
{
  "project_id": "uuid",
  "prd_id": "uuid",
  "arch_id": "uuid",
  "epic_data": {
    "number": 1,
    "title": "Core Functionality",
    "goal": "Implement core business logic",
    "content": "Epic content..."
  }
}

# Get epic
GET /api/bmad/epics/{epic_id}

# Update epic
PUT /api/bmad/epics/{epic_id}
{
  "title": "Updated Title",
  "goal": "Updated Goal",
  "content": "Updated content..."
}

# List epics for project
GET /api/bmad/projects/{project_id}/epics
```

#### 2. Epic-Story Relationships

```python
# Create story from epic
POST /api/bmad/epics/{epic_id}/stories
{
  "story_data": {
    "number": 1,
    "title": "User Authentication",
    "content": "Story content..."
  }
}

# Get stories for epic
GET /api/bmad/epics/{epic_id}/stories
```

### Benefits of This Approach

1. **Multi-user Support**: All epics stored centrally in database
2. **Scalability**: Object storage for large epic content
3. **Consistency**: Database transactions ensure data integrity
4. **Searchability**: Epic content indexed in Knowledge Graph
5. **Relationships**: Proper linking between PRD, epics, and stories
6. **Versioning**: Database versioning for epic changes
7. **Access Control**: Database-level permissions and tenancy

### Migration Strategy

1. **Update Database Schema**: Add EPIC document type support
2. **Create Epic Tables**: Add epic-specific metadata tables
3. **Update Epic Creation**: Modify epic creation to use database
4. **Migrate Existing Data**: Convert any existing epic files to database records
5. **Update APIs**: Modify epic APIs to use database storage
6. **Test Multi-user Access**: Verify epic access across multiple users

### Implementation Priority

1. **High Priority**: Database schema updates and epic document type support
2. **Medium Priority**: Epic metadata tables and relationships
3. **Low Priority**: Object storage integration for large content

This approach ensures that epics are properly stored in the cluster database while maintaining the BMAD workflow and supporting multi-user access patterns.
