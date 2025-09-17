# BMAD Database Schema Design

Document version: 1.0  
Date: 2025-09-17  
Purpose: Map BMAD artifacts to cerebral database schema

## Overview

This document maps BMAD planning artifacts (PRD, Architecture, Story) to the cerebral database schema, ensuring proper storage, versioning, and RAG/KG integration.

## Database Schema Mapping

### Core Tables

#### 1. cerebral_documents
```sql
CREATE TABLE cerebral_documents (
  doc_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  project_id uuid NOT NULL,
  type text NOT NULL CHECK (type IN ('PRD', 'ARCH', 'STORY')),
  version int NOT NULL DEFAULT 1,
  status text NOT NULL CHECK (status IN ('draft', 'review', 'approved', 'archived')),
  title text NOT NULL,
  content text NOT NULL,
  metadata jsonb,
  authored_by uuid,
  artifacts jsonb, -- BMAD-specific artifacts
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  
  -- Indexes
  CONSTRAINT unique_doc_version UNIQUE (tenant_id, project_id, type, version)
);

-- Indexes
CREATE INDEX idx_cerebral_documents_tenant_project ON cerebral_documents(tenant_id, project_id);
CREATE INDEX idx_cerebral_documents_type_status ON cerebral_documents(type, status);
CREATE INDEX idx_cerebral_documents_created_at ON cerebral_documents(created_at);
```

#### 2. cerebral_tasks
```sql
CREATE TABLE cerebral_tasks (
  task_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  project_id uuid NOT NULL,
  derived_from_story uuid REFERENCES cerebral_documents(doc_id),
  status text NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'blocked', 'cancelled')),
  priority text NOT NULL CHECK (priority IN ('low', 'medium', 'high', 'critical')),
  title text NOT NULL,
  description text,
  dependencies jsonb, -- Array of task_ids
  metadata jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX idx_cerebral_tasks_tenant_project ON cerebral_tasks(tenant_id, project_id);
CREATE INDEX idx_cerebral_tasks_status_priority ON cerebral_tasks(status, priority);
CREATE INDEX idx_cerebral_tasks_derived_from_story ON cerebral_tasks(derived_from_story);
```

#### 3. cerebral_activities
```sql
CREATE TABLE cerebral_activities (
  activity_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  actor uuid NOT NULL, -- User ID
  action text NOT NULL, -- 'create', 'update', 'approve', 'reject', etc.
  resource_type text NOT NULL, -- 'document', 'task', 'gate'
  resource_id uuid NOT NULL,
  metadata jsonb,
  timestamp timestamptz NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX idx_cerebral_activities_tenant_actor ON cerebral_activities(tenant_id, actor);
CREATE INDEX idx_cerebral_activities_resource ON cerebral_activities(resource_type, resource_id);
CREATE INDEX idx_cerebral_activities_timestamp ON cerebral_activities(timestamp);
```

### RAG/KG Integration

#### 4. knowledge_items (Enhanced)
```sql
-- Extend existing knowledge_items table
ALTER TABLE knowledge_items ADD COLUMN IF NOT EXISTS doc_id uuid REFERENCES cerebral_documents(doc_id);
ALTER TABLE knowledge_items ADD COLUMN IF NOT EXISTS content_type text CHECK (content_type IN ('PRD', 'ARCH', 'STORY', 'TASK', 'GENERAL'));

-- Index for BMAD integration
CREATE INDEX IF NOT EXISTS idx_knowledge_items_doc_id ON knowledge_items(doc_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_content_type ON knowledge_items(content_type);
```

#### 5. knowledge_embeddings (Enhanced)
```sql
-- Extend existing knowledge_embeddings table
ALTER TABLE knowledge_embeddings ADD COLUMN IF NOT EXISTS doc_id uuid REFERENCES cerebral_documents(doc_id);
ALTER TABLE knowledge_embeddings ADD COLUMN IF NOT EXISTS chunk_type text CHECK (chunk_type IN ('section', 'requirement', 'story', 'task', 'general'));

-- Index for BMAD integration
CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_doc_id ON knowledge_embeddings(doc_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_chunk_type ON knowledge_embeddings(chunk_type);
```

## BMAD Artifact Mapping

### PRD Document Mapping
```yaml
BMAD Template: prd-tmpl.yaml
Database Table: cerebral_documents
Type: 'PRD'
Content Structure:
  - goals-context: Goals and Background Context
  - user-research: User Research and Personas
  - requirements: Functional Requirements
  - non-functional: Non-Functional Requirements
  - success-metrics: Success Metrics and KPIs
  - risks-assumptions: Risks and Assumptions
  - timeline: Timeline and Milestones
  - appendices: Appendices and References

RAG Chunking Strategy:
  - Each section becomes a separate knowledge_embeddings entry
  - chunk_type: 'section'
  - content_chunk: Section content
  - metadata: {section_id, section_title, doc_version}
```

### Architecture Document Mapping
```yaml
BMAD Template: architecture-tmpl.yaml
Database Table: cerebral_documents
Type: 'ARCH'
Content Structure:
  - introduction: Introduction and Context
  - tech-stack: Technology Stack
  - system-architecture: System Architecture
  - data-architecture: Data Architecture
  - security-architecture: Security Architecture
  - deployment-architecture: Deployment Architecture
  - integration-patterns: Integration Patterns
  - performance-considerations: Performance Considerations

RAG Chunking Strategy:
  - Each section becomes a separate knowledge_embeddings entry
  - chunk_type: 'section'
  - content_chunk: Section content
  - metadata: {section_id, section_title, doc_version, tech_stack}
```

### Story Document Mapping
```yaml
BMAD Template: story-tmpl.yaml
Database Table: cerebral_documents
Type: 'STORY'
Content Structure:
  - story-overview: Story Overview
  - user-stories: User Stories
  - acceptance-criteria: Acceptance Criteria
  - implementation-notes: Implementation Notes
  - testing-strategy: Testing Strategy
  - dependencies: Dependencies

RAG Chunking Strategy:
  - Each user story becomes a separate knowledge_embeddings entry
  - chunk_type: 'story'
  - content_chunk: Story content
  - metadata: {story_id, story_title, doc_version, acceptance_criteria}
```

## API Integration Points

### Document Creation Flow
1. **BMAD Agent**: Creates PRD/Architecture/Story using BMAD templates
2. **HTTP API**: POST `/bmad/planning/prd` → `cerebral_documents` table
3. **RAG Indexing**: Automatically chunk and embed content → `knowledge_embeddings`
4. **KG Linking**: Create edges between documents and related tasks

### Document Retrieval Flow
1. **Search Query**: User searches for information
2. **RAG Lookup**: Query `knowledge_embeddings` for relevant chunks
3. **Document Resolution**: Resolve chunks to full documents via `doc_id`
4. **Context Assembly**: Return relevant document sections with sources

### Task Generation Flow
1. **Story Approval**: Story document status → 'approved'
2. **Task Creation**: Generate tasks from story → `cerebral_tasks` table
3. **Dependency Mapping**: Link tasks to story via `derived_from_story`
4. **CAEF Trigger**: Enable CAEF orchestration for approved stories

## Migration Strategy

### Phase 1: Schema Creation
```sql
-- Create core tables
CREATE TABLE cerebral_documents (...);
CREATE TABLE cerebral_tasks (...);
CREATE TABLE cerebral_activities (...);

-- Add indexes
CREATE INDEX ...;
```

### Phase 2: RAG Integration
```sql
-- Extend existing tables
ALTER TABLE knowledge_items ADD COLUMN doc_id uuid;
ALTER TABLE knowledge_embeddings ADD COLUMN doc_id uuid;

-- Add indexes
CREATE INDEX ...;
```

### Phase 3: Data Migration
```sql
-- Migrate existing documents to new schema
INSERT INTO cerebral_documents (...)
SELECT ... FROM existing_documents;

-- Update knowledge_items references
UPDATE knowledge_items SET doc_id = ...;
```

## Security & Compliance

### Row Level Security (RLS)
```sql
-- Enable RLS on all tables
ALTER TABLE cerebral_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE cerebral_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE cerebral_activities ENABLE ROW LEVEL SECURITY;

-- Tenant isolation policies
CREATE POLICY tenant_isolation_documents ON cerebral_documents
  FOR ALL TO authenticated
  USING (tenant_id::text = current_setting('request.jwt.claims')::jsonb ->> 'tenant_id');

CREATE POLICY tenant_isolation_tasks ON cerebral_tasks
  FOR ALL TO authenticated
  USING (tenant_id::text = current_setting('request.jwt.claims')::jsonb ->> 'tenant_id');

CREATE POLICY tenant_isolation_activities ON cerebral_activities
  FOR ALL TO authenticated
  USING (tenant_id::text = current_setting('request.jwt.claims')::jsonb ->> 'tenant_id');
```

### Audit Trail
- All document changes logged in `cerebral_activities`
- Version history maintained in `cerebral_documents`
- Immutable audit trail for compliance

## Performance Considerations

### Indexing Strategy
- Composite indexes on (tenant_id, project_id, type)
- Partial indexes on status for active documents
- GIN indexes on JSONB metadata fields

### Query Optimization
- Use tenant_id in all queries for RLS efficiency
- Leverage pgvector for semantic search
- Cache frequently accessed documents

## References

- [BMAD API Inventory](../architecture/bmad_api_inventory.md)
- [MCP Architecture](../architecture/MCP_ARCHITECTURE.md)
- [Database Schema](../agentic-plan/DatabaseSchema.md)
- [Knowledge Graph Schema](../agentic-plan/sql/002_knowledge_schema_soc2.sql)
