-- BMAD Artifacts Database Schema Migration
-- Extends existing knowledge schema to support BMAD planning artifacts
-- Run with service role; review and tailor policies per environment.

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- CORE BMAD TABLES
-- ============================================================================

-- 1. cerebral_documents - Main table for BMAD artifacts (PRD, Architecture, Stories)
CREATE TABLE IF NOT EXISTS public.cerebral_documents (
  doc_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  project_id uuid NOT NULL,
  type text NOT NULL CHECK (type IN ('PRD', 'ARCH', 'STORY', 'EPIC', 'TASK')),
  version int NOT NULL DEFAULT 1,
  status text NOT NULL CHECK (status IN ('draft', 'review', 'approved', 'archived', 'rejected')),
  title text NOT NULL,
  content text NOT NULL,
  metadata jsonb DEFAULT '{}',
  authored_by uuid,
  artifacts jsonb DEFAULT '{}', -- BMAD-specific artifacts and workflow data
  bmad_template text, -- Template used to generate the document
  bmad_workflow text, -- Workflow that generated the document
  parent_doc_id uuid REFERENCES public.cerebral_documents(doc_id), -- For versioning
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  
  -- Constraints
  CONSTRAINT unique_doc_version UNIQUE (tenant_id, project_id, type, version),
  CONSTRAINT valid_doc_type CHECK (type IN ('PRD', 'ARCH', 'STORY', 'EPIC', 'TASK'))
);

-- 2. cerebral_tasks - Tasks derived from BMAD stories
CREATE TABLE IF NOT EXISTS public.cerebral_tasks (
  task_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  project_id uuid NOT NULL,
  derived_from_story uuid REFERENCES public.cerebral_documents(doc_id),
  status text NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'blocked', 'cancelled')),
  priority text NOT NULL CHECK (priority IN ('low', 'medium', 'high', 'critical')),
  title text NOT NULL,
  description text,
  acceptance_criteria jsonb DEFAULT '[]', -- Array of acceptance criteria
  dependencies jsonb DEFAULT '[]', -- Array of task_ids
  metadata jsonb DEFAULT '{}',
  bmad_story_id text, -- Original BMAD story identifier
  estimated_hours int,
  actual_hours int,
  assigned_to uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- 3. cerebral_activities - Audit trail for all BMAD operations
CREATE TABLE IF NOT EXISTS public.cerebral_activities (
  activity_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  actor uuid NOT NULL, -- User ID
  action text NOT NULL, -- 'create', 'update', 'approve', 'reject', 'archive', etc.
  resource_type text NOT NULL, -- 'document', 'task', 'gate', 'workflow'
  resource_id uuid NOT NULL,
  metadata jsonb DEFAULT '{}',
  bmad_workflow_id text, -- BMAD workflow that triggered this activity
  timestamp timestamptz NOT NULL DEFAULT now()
);

-- 4. cerebral_projects - Project metadata and BMAD configuration
CREATE TABLE IF NOT EXISTS public.cerebral_projects (
  project_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  name text NOT NULL,
  description text,
  project_type text CHECK (project_type IN ('greenfield', 'brownfield')),
  bmad_config jsonb DEFAULT '{}', -- BMAD-specific project configuration
  expansion_packs jsonb DEFAULT '[]', -- Installed expansion packs
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- cerebral_documents indexes
CREATE INDEX IF NOT EXISTS idx_cerebral_documents_tenant_project ON public.cerebral_documents(tenant_id, project_id);
CREATE INDEX IF NOT EXISTS idx_cerebral_documents_type_status ON public.cerebral_documents(type, status);
CREATE INDEX IF NOT EXISTS idx_cerebral_documents_created_at ON public.cerebral_documents(created_at);
CREATE INDEX IF NOT EXISTS idx_cerebral_documents_bmad_template ON public.cerebral_documents(bmad_template);
CREATE INDEX IF NOT EXISTS idx_cerebral_documents_bmad_workflow ON public.cerebral_documents(bmad_workflow);
CREATE INDEX IF NOT EXISTS idx_cerebral_documents_parent_doc ON public.cerebral_documents(parent_doc_id);

-- cerebral_tasks indexes
CREATE INDEX IF NOT EXISTS idx_cerebral_tasks_tenant_project ON public.cerebral_tasks(tenant_id, project_id);
CREATE INDEX IF NOT EXISTS idx_cerebral_tasks_status_priority ON public.cerebral_tasks(status, priority);
CREATE INDEX IF NOT EXISTS idx_cerebral_tasks_derived_from_story ON public.cerebral_tasks(derived_from_story);
CREATE INDEX IF NOT EXISTS idx_cerebral_tasks_assigned_to ON public.cerebral_tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_cerebral_tasks_bmad_story_id ON public.cerebral_tasks(bmad_story_id);

-- cerebral_activities indexes
CREATE INDEX IF NOT EXISTS idx_cerebral_activities_tenant_actor ON public.cerebral_activities(tenant_id, actor);
CREATE INDEX IF NOT EXISTS idx_cerebral_activities_resource ON public.cerebral_activities(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_cerebral_activities_timestamp ON public.cerebral_activities(timestamp);
CREATE INDEX IF NOT EXISTS idx_cerebral_activities_bmad_workflow ON public.cerebral_activities(bmad_workflow_id);

-- cerebral_projects indexes
CREATE INDEX IF NOT EXISTS idx_cerebral_projects_tenant ON public.cerebral_projects(tenant_id);
CREATE INDEX IF NOT EXISTS idx_cerebral_projects_status ON public.cerebral_projects(status);
CREATE INDEX IF NOT EXISTS idx_cerebral_projects_type ON public.cerebral_projects(project_type);

-- ============================================================================
-- EXTEND EXISTING KNOWLEDGE TABLES FOR BMAD INTEGRATION
-- ============================================================================

-- Extend knowledge_items to reference BMAD documents
ALTER TABLE public.knowledge_items 
  ADD COLUMN IF NOT EXISTS doc_id uuid REFERENCES public.cerebral_documents(doc_id),
  ADD COLUMN IF NOT EXISTS content_type text CHECK (content_type IN ('PRD', 'ARCH', 'STORY', 'TASK', 'EPIC', 'GENERAL'));

-- Extend knowledge_embeddings to reference BMAD documents
ALTER TABLE public.knowledge_embeddings 
  ADD COLUMN IF NOT EXISTS doc_id uuid REFERENCES public.cerebral_documents(doc_id),
  ADD COLUMN IF NOT EXISTS chunk_type text CHECK (chunk_type IN ('section', 'requirement', 'story', 'task', 'epic', 'general'));

-- Add indexes for new columns
CREATE INDEX IF NOT EXISTS idx_knowledge_items_doc_id ON public.knowledge_items(doc_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_content_type ON public.knowledge_items(content_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_doc_id ON public.knowledge_embeddings(doc_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_chunk_type ON public.knowledge_embeddings(chunk_type);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on all BMAD tables
ALTER TABLE public.cerebral_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cerebral_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cerebral_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cerebral_projects ENABLE ROW LEVEL SECURITY;

-- Tenant isolation policies for cerebral_documents
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='cerebral_documents' AND policyname='cd_tenant_select'
  ) THEN
    CREATE POLICY cd_tenant_select ON public.cerebral_documents
      FOR SELECT TO authenticated
      USING (tenant_id::text = coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb ->> 'tenant_id');
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='cerebral_documents' AND policyname='cd_service_all'
  ) THEN
    CREATE POLICY cd_service_all ON public.cerebral_documents
      FOR ALL TO service_role
      USING (true);
  END IF;
END $$;

-- Tenant isolation policies for cerebral_tasks
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='cerebral_tasks' AND policyname='ct_tenant_select'
  ) THEN
    CREATE POLICY ct_tenant_select ON public.cerebral_tasks
      FOR SELECT TO authenticated
      USING (tenant_id::text = coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb ->> 'tenant_id');
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='cerebral_tasks' AND policyname='ct_service_all'
  ) THEN
    CREATE POLICY ct_service_all ON public.cerebral_tasks
      FOR ALL TO service_role
      USING (true);
  END IF;
END $$;

-- Tenant isolation policies for cerebral_activities
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='cerebral_activities' AND policyname='ca_tenant_select'
  ) THEN
    CREATE POLICY ca_tenant_select ON public.cerebral_activities
      FOR SELECT TO authenticated
      USING (tenant_id::text = coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb ->> 'tenant_id');
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='cerebral_activities' AND policyname='ca_service_all'
  ) THEN
    CREATE POLICY ca_service_all ON public.cerebral_activities
      FOR ALL TO service_role
      USING (true);
  END IF;
END $$;

-- Tenant isolation policies for cerebral_projects
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='cerebral_projects' AND policyname='cp_tenant_select'
  ) THEN
    CREATE POLICY cp_tenant_select ON public.cerebral_projects
      FOR SELECT TO authenticated
      USING (tenant_id::text = coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb ->> 'tenant_id');
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='cerebral_projects' AND policyname='cp_service_all'
  ) THEN
    CREATE POLICY cp_service_all ON public.cerebral_projects
      FOR ALL TO service_role
      USING (true);
  END IF;
END $$;

-- ============================================================================
-- BMAD-SPECIFIC FUNCTIONS
-- ============================================================================

-- Function to create a new BMAD document
CREATE OR REPLACE FUNCTION public.create_bmad_document(
  p_tenant_id uuid,
  p_project_id uuid,
  p_type text,
  p_title text,
  p_content text,
  p_metadata jsonb DEFAULT '{}',
  p_artifacts jsonb DEFAULT '{}',
  p_bmad_template text DEFAULT NULL,
  p_bmad_workflow text DEFAULT NULL,
  p_authored_by uuid DEFAULT NULL
)
RETURNS uuid AS $$
DECLARE
  v_doc_id uuid;
BEGIN
  -- Validate document type
  IF p_type NOT IN ('PRD', 'ARCH', 'STORY', 'EPIC', 'TASK') THEN
    RAISE EXCEPTION 'Invalid document type: %', p_type;
  END IF;
  
  -- Insert new document
  INSERT INTO public.cerebral_documents (
    tenant_id, project_id, type, title, content, metadata, 
    artifacts, bmad_template, bmad_workflow, authored_by
  ) VALUES (
    p_tenant_id, p_project_id, p_type, p_title, p_content, p_metadata,
    p_artifacts, p_bmad_template, p_bmad_workflow, p_authored_by
  ) RETURNING doc_id INTO v_doc_id;
  
  -- Log activity
  INSERT INTO public.cerebral_activities (
    tenant_id, actor, action, resource_type, resource_id,
    metadata, bmad_workflow_id
  ) VALUES (
    p_tenant_id, p_authored_by, 'create', 'document', v_doc_id,
    jsonb_build_object('type', p_type, 'template', p_bmad_template), p_bmad_workflow
  );
  
  RETURN v_doc_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to update document status
CREATE OR REPLACE FUNCTION public.update_document_status(
  p_doc_id uuid,
  p_status text,
  p_actor uuid,
  p_metadata jsonb DEFAULT '{}'
)
RETURNS boolean AS $$
DECLARE
  v_tenant_id uuid;
  v_old_status text;
BEGIN
  -- Get current document info
  SELECT tenant_id, status INTO v_tenant_id, v_old_status
  FROM public.cerebral_documents 
  WHERE doc_id = p_doc_id;
  
  IF v_tenant_id IS NULL THEN
    RAISE EXCEPTION 'Document not found: %', p_doc_id;
  END IF;
  
  -- Update document status
  UPDATE public.cerebral_documents 
  SET status = p_status, updated_at = now()
  WHERE doc_id = p_doc_id;
  
  -- Log activity
  INSERT INTO public.cerebral_activities (
    tenant_id, actor, action, resource_type, resource_id,
    metadata
  ) VALUES (
    v_tenant_id, p_actor, 'status_change', 'document', p_doc_id,
    jsonb_build_object('old_status', v_old_status, 'new_status', p_status) || p_metadata
  );
  
  RETURN true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to create tasks from approved stories
CREATE OR REPLACE FUNCTION public.create_tasks_from_story(
  p_story_doc_id uuid,
  p_actor uuid
)
RETURNS int AS $$
DECLARE
  v_tenant_id uuid;
  v_project_id uuid;
  v_story_content text;
  v_story_metadata jsonb;
  v_tasks_created int := 0;
  v_task_record jsonb;
BEGIN
  -- Get story document info
  SELECT tenant_id, project_id, content, metadata 
  INTO v_tenant_id, v_project_id, v_story_content, v_story_metadata
  FROM public.cerebral_documents 
  WHERE doc_id = p_story_doc_id AND type = 'STORY';
  
  IF v_tenant_id IS NULL THEN
    RAISE EXCEPTION 'Story document not found: %', p_story_doc_id;
  END IF;
  
  -- Extract tasks from story metadata (assuming tasks are stored in metadata.tasks)
  IF v_story_metadata ? 'tasks' THEN
    FOR v_task_record IN SELECT * FROM jsonb_array_elements(v_story_metadata->'tasks')
    LOOP
      INSERT INTO public.cerebral_tasks (
        tenant_id, project_id, derived_from_story,
        title, description, acceptance_criteria, metadata, bmad_story_id
      ) VALUES (
        v_tenant_id, v_project_id, p_story_doc_id,
        v_task_record->>'title', v_task_record->>'description',
        v_task_record->'acceptance_criteria', v_task_record->'metadata',
        v_task_record->>'id'
      );
      
      v_tasks_created := v_tasks_created + 1;
    END LOOP;
  END IF;
  
  -- Log activity
  INSERT INTO public.cerebral_activities (
    tenant_id, actor, action, resource_type, resource_id,
    metadata
  ) VALUES (
    v_tenant_id, p_actor, 'create_tasks', 'story', p_story_doc_id,
    jsonb_build_object('tasks_created', v_tasks_created)
  );
  
  RETURN v_tasks_created;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to search BMAD documents with embeddings
CREATE OR REPLACE FUNCTION public.search_bmad_documents(
  query_embedding vector(1536),
  match_count int DEFAULT 8,
  tenant_filter uuid DEFAULT NULL,
  doc_type_filter text DEFAULT NULL
)
RETURNS TABLE(
  doc_id uuid, 
  title text, 
  content_chunk text, 
  score float4, 
  metadata jsonb,
  doc_type text
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    cd.doc_id,
    cd.title,
    ke.content_chunk,
    1 - (ke.embedding <=> query_embedding) AS score,
    ke.metadata,
    cd.type
  FROM public.knowledge_embeddings ke
  JOIN public.cerebral_documents cd ON ke.doc_id = cd.doc_id
  WHERE (tenant_filter IS NULL OR cd.tenant_id = tenant_filter)
    AND (doc_type_filter IS NULL OR cd.type = doc_type_filter)
  ORDER BY ke.embedding <=> query_embedding
  LIMIT greatest(1, coalesce(match_count, 8));
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- PERMISSIONS
-- ============================================================================

-- Grant permissions on functions
REVOKE ALL ON FUNCTION public.create_bmad_document(uuid, uuid, text, text, text, jsonb, jsonb, text, text, uuid) FROM public;
REVOKE ALL ON FUNCTION public.update_document_status(uuid, text, uuid, jsonb) FROM public;
REVOKE ALL ON FUNCTION public.create_tasks_from_story(uuid, uuid) FROM public;
REVOKE ALL ON FUNCTION public.search_bmad_documents(vector, int, uuid, text) FROM public;

GRANT EXECUTE ON FUNCTION public.create_bmad_document(uuid, uuid, text, text, text, jsonb, jsonb, text, text, uuid) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.update_document_status(uuid, text, uuid, jsonb) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.create_tasks_from_story(uuid, uuid) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.search_bmad_documents(vector, int, uuid, text) TO authenticated, service_role;

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ============================================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to all BMAD tables
CREATE TRIGGER update_cerebral_documents_updated_at
  BEFORE UPDATE ON public.cerebral_documents
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_cerebral_tasks_updated_at
  BEFORE UPDATE ON public.cerebral_tasks
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_cerebral_projects_updated_at
  BEFORE UPDATE ON public.cerebral_projects
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================================
-- SAMPLE DATA FOR TESTING (OPTIONAL)
-- ============================================================================

-- Uncomment the following section to insert sample data for testing

/*
-- Sample tenant and project (replace with actual UUIDs)
INSERT INTO public.cerebral_projects (tenant_id, project_id, name, description, project_type, bmad_config)
VALUES (
  '00000000-0000-0000-0000-000000000001'::uuid,
  gen_random_uuid(),
  'Sample BMAD Project',
  'A sample project to demonstrate BMAD integration',
  'greenfield',
  '{"template_version": "2.0", "workflow_type": "greenfield-service"}'::jsonb
);

-- Sample PRD document
SELECT public.create_bmad_document(
  '00000000-0000-0000-0000-000000000001'::uuid,
  (SELECT project_id FROM public.cerebral_projects LIMIT 1),
  'PRD',
  'Sample Product Requirements Document',
  'This is a sample PRD content...',
  '{"goals": ["Goal 1", "Goal 2"], "requirements": ["Req 1", "Req 2"]}'::jsonb,
  '{"template": "prd-tmpl", "workflow": "greenfield-service"}'::jsonb,
  'prd-tmpl.yaml',
  'greenfield-service.yaml',
  '00000000-0000-0000-0000-000000000002'::uuid
);
*/

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Log migration completion
INSERT INTO public.cerebral_activities (
  tenant_id, actor, action, resource_type, resource_id,
  metadata, bmad_workflow_id
) VALUES (
  '00000000-0000-0000-0000-000000000000'::uuid, -- System tenant
  '00000000-0000-0000-0000-000000000000'::uuid, -- System actor
  'migration', 'system', gen_random_uuid(),
  '{"migration": "004_bmad_artifacts_schema", "version": "1.0"}'::jsonb,
  'database-migration'
);
