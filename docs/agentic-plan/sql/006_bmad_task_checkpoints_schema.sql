-- BMAD Task Checkpoints Schema Migration
-- This migration creates tables for task state checkpointing in Phase 2:
-- Unified Persona Activation

-- 1. Create bmad_task_checkpoints table for task state persistence
CREATE TABLE IF NOT EXISTS public.bmad_task_checkpoints (
  checkpoint_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid NOT NULL REFERENCES public.bmad_sessions(session_id) ON DELETE CASCADE,
  persona_id uuid REFERENCES public.bmad_persona_contexts(persona_id) ON DELETE CASCADE,
  checkpoint_type text NOT NULL CHECK (checkpoint_type IN (
    'manual', 'automatic', 'workflow', 'error_recovery', 'persona_switch'
  )),
  scope text NOT NULL CHECK (scope IN ('task', 'workflow', 'session', 'persona')),
  checkpoint_name text,
  timestamp timestamptz NOT NULL DEFAULT now(),
  task_states jsonb NOT NULL DEFAULT '{}',
  context_snapshot jsonb NOT NULL DEFAULT '{}',
  dependencies jsonb DEFAULT '[]',
  metadata jsonb DEFAULT '{}',
  checksum text NOT NULL,
  
  CONSTRAINT unique_checkpoint_name_per_session UNIQUE (session_id, checkpoint_name)
);

-- 2. Create bmad_active_tasks table for tracking current task states
CREATE TABLE IF NOT EXISTS public.bmad_active_tasks (
  task_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid NOT NULL REFERENCES public.bmad_sessions(session_id) ON DELETE CASCADE,
  persona_id uuid REFERENCES public.bmad_persona_contexts(persona_id) ON DELETE CASCADE,
  task_name text NOT NULL,
  persona_type text NOT NULL,
  status text NOT NULL DEFAULT 'started' CHECK (status IN (
    'started', 'in_progress', 'paused', 'completed', 'failed', 'cancelled'
  )),
  progress real DEFAULT 0.0 CHECK (progress >= 0.0 AND progress <= 1.0),
  input_data jsonb DEFAULT '{}',
  output_data jsonb DEFAULT '{}',
  intermediate_results jsonb DEFAULT '{}',
  error_state jsonb,
  dependencies jsonb DEFAULT '[]',
  metadata jsonb DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  
  CONSTRAINT unique_task_name_per_session UNIQUE (session_id, task_name)
);

-- 3. Create bmad_task_dependencies table for tracking task relationships
CREATE TABLE IF NOT EXISTS public.bmad_task_dependencies (
  dependency_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id uuid NOT NULL REFERENCES public.bmad_active_tasks(task_id) ON DELETE CASCADE,
  depends_on_task_id uuid NOT NULL REFERENCES public.bmad_active_tasks(task_id) ON DELETE CASCADE,
  dependency_type text DEFAULT 'prerequisite' CHECK (dependency_type IN (
    'prerequisite', 'blocking', 'informational', 'optional'
  )),
  created_at timestamptz NOT NULL DEFAULT now(),
  
  CONSTRAINT unique_task_dependency UNIQUE (task_id, depends_on_task_id),
  CONSTRAINT no_self_dependency CHECK (task_id != depends_on_task_id)
);

-- 4. Create bmad_task_history table for audit trail
CREATE TABLE IF NOT EXISTS public.bmad_task_history (
  history_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id uuid NOT NULL REFERENCES public.bmad_active_tasks(task_id) ON DELETE CASCADE,
  action text NOT NULL CHECK (action IN (
    'created', 'started', 'updated', 'paused', 'resumed', 'completed', 'failed', 'cancelled'
  )),
  previous_state jsonb,
  new_state jsonb,
  change_description text,
  timestamp timestamptz NOT NULL DEFAULT now(),
  user_id uuid,
  persona_type text
);

-- 5. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_bmad_task_checkpoints_session ON public.bmad_task_checkpoints(session_id);
CREATE INDEX IF NOT EXISTS idx_bmad_task_checkpoints_persona ON public.bmad_task_checkpoints(persona_id);
CREATE INDEX IF NOT EXISTS idx_bmad_task_checkpoints_type ON public.bmad_task_checkpoints(checkpoint_type);
CREATE INDEX IF NOT EXISTS idx_bmad_task_checkpoints_timestamp ON public.bmad_task_checkpoints(timestamp);
CREATE INDEX IF NOT EXISTS idx_bmad_active_tasks_session ON public.bmad_active_tasks(session_id);
CREATE INDEX IF NOT EXISTS idx_bmad_active_tasks_persona ON public.bmad_active_tasks(persona_id);
CREATE INDEX IF NOT EXISTS idx_bmad_active_tasks_status ON public.bmad_active_tasks(status);
CREATE INDEX IF NOT EXISTS idx_bmad_active_tasks_updated_at ON public.bmad_active_tasks(updated_at);
CREATE INDEX IF NOT EXISTS idx_bmad_task_dependencies_task ON public.bmad_task_dependencies(task_id);
CREATE INDEX IF NOT EXISTS idx_bmad_task_dependencies_depends_on ON public.bmad_task_dependencies(depends_on_task_id);
CREATE INDEX IF NOT EXISTS idx_bmad_task_history_task ON public.bmad_task_history(task_id);
CREATE INDEX IF NOT EXISTS idx_bmad_task_history_timestamp ON public.bmad_task_history(timestamp);

-- 6. Create GIN indexes for JSONB fields
CREATE INDEX IF NOT EXISTS idx_bmad_task_checkpoints_task_states_gin ON public.bmad_task_checkpoints USING gin(task_states);
CREATE INDEX IF NOT EXISTS idx_bmad_task_checkpoints_context_snapshot_gin ON public.bmad_task_checkpoints USING gin(context_snapshot);
CREATE INDEX IF NOT EXISTS idx_bmad_active_tasks_input_data_gin ON public.bmad_active_tasks USING gin(input_data);
CREATE INDEX IF NOT EXISTS idx_bmad_active_tasks_output_data_gin ON public.bmad_active_tasks USING gin(output_data);
CREATE INDEX IF NOT EXISTS idx_bmad_active_tasks_intermediate_results_gin ON public.bmad_active_tasks USING gin(intermediate_results);

-- 7. Row Level Security (RLS) Policies
ALTER TABLE public.bmad_task_checkpoints ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bmad_active_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bmad_task_dependencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bmad_task_history ENABLE ROW LEVEL SECURITY;

-- Policy for bmad_task_checkpoints
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='bmad_task_checkpoints' AND policyname='btc_tenant_isolation') THEN
    CREATE POLICY btc_tenant_isolation ON public.bmad_task_checkpoints
      FOR ALL TO authenticated
      USING (
        session_id IN (
          SELECT session_id FROM public.bmad_sessions 
          WHERE user_id::text = coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb ->> 'user_id'
        )
      )
      WITH CHECK (
        session_id IN (
          SELECT session_id FROM public.bmad_sessions 
          WHERE user_id::text = coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb ->> 'user_id'
        )
      );
  END IF;
END $$;

-- Policy for bmad_active_tasks
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='bmad_active_tasks' AND policyname='bat_tenant_isolation') THEN
    CREATE POLICY bat_tenant_isolation ON public.bmad_active_tasks
      FOR ALL TO authenticated
      USING (
        session_id IN (
          SELECT session_id FROM public.bmad_sessions 
          WHERE user_id::text = coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb ->> 'user_id'
        )
      )
      WITH CHECK (
        session_id IN (
          SELECT session_id FROM public.bmad_sessions 
          WHERE user_id::text = coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb ->> 'user_id'
        )
      );
  END IF;
END $$;

-- Policy for bmad_task_dependencies
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='bmad_task_dependencies' AND policyname='btd_tenant_isolation') THEN
    CREATE POLICY btd_tenant_isolation ON public.bmad_task_dependencies
      FOR ALL TO authenticated
      USING (
        task_id IN (
          SELECT task_id FROM public.bmad_active_tasks 
          WHERE session_id IN (
            SELECT session_id FROM public.bmad_sessions 
            WHERE user_id::text = coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb ->> 'user_id'
          )
        )
      )
      WITH CHECK (
        task_id IN (
          SELECT task_id FROM public.bmad_active_tasks 
          WHERE session_id IN (
            SELECT session_id FROM public.bmad_sessions 
            WHERE user_id::text = coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb ->> 'user_id'
          )
        )
      );
  END IF;
END $$;

-- Policy for bmad_task_history
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='bmad_task_history' AND policyname='bth_tenant_isolation') THEN
    CREATE POLICY bth_tenant_isolation ON public.bmad_task_history
      FOR ALL TO authenticated
      USING (
        task_id IN (
          SELECT task_id FROM public.bmad_active_tasks 
          WHERE session_id IN (
            SELECT session_id FROM public.bmad_sessions 
            WHERE user_id::text = coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb ->> 'user_id'
          )
        )
      )
      WITH CHECK (
        task_id IN (
          SELECT task_id FROM public.bmad_active_tasks 
          WHERE session_id IN (
            SELECT session_id FROM public.bmad_sessions 
            WHERE user_id::text = coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb ->> 'user_id'
          )
        )
      );
  END IF;
END $$;

-- 8. Grant necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON public.bmad_task_checkpoints TO authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.bmad_active_tasks TO authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.bmad_task_dependencies TO authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.bmad_task_history TO authenticated, service_role;

-- 9. Create utility functions for task management
CREATE OR REPLACE FUNCTION public.create_bmad_task(
    p_session_id uuid,
    p_persona_id uuid,
    p_task_name text,
    p_persona_type text,
    p_input_data jsonb DEFAULT '{}',
    p_dependencies jsonb DEFAULT '[]'
)
RETURNS uuid AS $$
DECLARE
    new_task_id uuid;
    session_user_id uuid;
BEGIN
    -- Verify session access
    SELECT user_id INTO session_user_id
    FROM public.bmad_sessions 
    WHERE session_id = p_session_id;
    
    IF session_user_id IS NULL THEN
        RAISE EXCEPTION 'Session not found or access denied';
    END IF;
    
    -- Create task
    INSERT INTO public.bmad_active_tasks (
        session_id, persona_id, task_name, persona_type, input_data, dependencies
    )
    VALUES (
        p_session_id, p_persona_id, p_task_name, p_persona_type, p_input_data, p_dependencies
    )
    RETURNING task_id INTO new_task_id;
    
    -- Log task creation
    INSERT INTO public.bmad_task_history (
        task_id, action, new_state, change_description, user_id, persona_type
    )
    VALUES (
        new_task_id, 'created', 
        jsonb_build_object('task_name', p_task_name, 'status', 'started'),
        'Task created',
        session_user_id, p_persona_type
    );
    
    RETURN new_task_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION public.update_bmad_task_state(
    p_task_id uuid,
    p_status text DEFAULT NULL,
    p_progress real DEFAULT NULL,
    p_output_data jsonb DEFAULT NULL,
    p_intermediate_results jsonb DEFAULT NULL,
    p_metadata jsonb DEFAULT NULL
)
RETURNS boolean AS $$
DECLARE
    task_session_id uuid;
    session_user_id uuid;
    previous_state jsonb;
BEGIN
    -- Get task and verify access
    SELECT session_id INTO task_session_id
    FROM public.bmad_active_tasks 
    WHERE task_id = p_task_id;
    
    IF task_session_id IS NULL THEN
        RAISE EXCEPTION 'Task not found';
    END IF;
    
    SELECT user_id INTO session_user_id
    FROM public.bmad_sessions 
    WHERE session_id = task_session_id;
    
    IF session_user_id IS NULL THEN
        RAISE EXCEPTION 'Access denied';
    END IF;
    
    -- Get previous state for history
    SELECT row_to_json(bmad_active_tasks) INTO previous_state
    FROM public.bmad_active_tasks
    WHERE task_id = p_task_id;
    
    -- Update task
    UPDATE public.bmad_active_tasks
    SET 
        status = COALESCE(p_status, status),
        progress = COALESCE(p_progress, progress),
        output_data = COALESCE(p_output_data, output_data),
        intermediate_results = COALESCE(p_intermediate_results, intermediate_results),
        metadata = COALESCE(p_metadata, metadata),
        updated_at = now()
    WHERE task_id = p_task_id;
    
    -- Log state change
    INSERT INTO public.bmad_task_history (
        task_id, action, previous_state, new_state, change_description, user_id
    )
    VALUES (
        p_task_id, 'updated', previous_state,
        (SELECT row_to_json(bmad_active_tasks) FROM public.bmad_active_tasks WHERE task_id = p_task_id),
        'Task state updated',
        session_user_id
    );
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION public.create_bmad_task_checkpoint(
    p_task_id uuid,
    p_checkpoint_type text DEFAULT 'manual',
    p_checkpoint_name text DEFAULT NULL,
    p_scope text DEFAULT 'task'
)
RETURNS uuid AS $$
DECLARE
    new_checkpoint_id uuid;
    task_session_id uuid;
    task_persona_id uuid;
    task_data jsonb;
    session_user_id uuid;
BEGIN
    -- Get task data and verify access
    SELECT session_id, persona_id INTO task_session_id, task_persona_id
    FROM public.bmad_active_tasks 
    WHERE task_id = p_task_id;
    
    IF task_session_id IS NULL THEN
        RAISE EXCEPTION 'Task not found';
    END IF;
    
    SELECT user_id INTO session_user_id
    FROM public.bmad_sessions 
    WHERE session_id = task_session_id;
    
    IF session_user_id IS NULL THEN
        RAISE EXCEPTION 'Access denied';
    END IF;
    
    -- Get current task state
    SELECT row_to_json(bmad_active_tasks) INTO task_data
    FROM public.bmad_active_tasks
    WHERE task_id = p_task_id;
    
    -- Create checkpoint
    INSERT INTO public.bmad_task_checkpoints (
        session_id, persona_id, checkpoint_type, scope, checkpoint_name,
        task_states, context_snapshot, checksum
    )
    VALUES (
        task_session_id, task_persona_id, p_checkpoint_type, p_scope, p_checkpoint_name,
        jsonb_build_object(p_task_id::text, task_data),
        jsonb_build_object('task_id', p_task_id, 'timestamp', now()),
        encode(sha256(task_data::text::bytea), 'hex')
    )
    RETURNING checkpoint_id INTO new_checkpoint_id;
    
    RETURN new_checkpoint_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 10. Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION public.create_bmad_task(uuid, uuid, text, text, jsonb, jsonb) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.update_bmad_task_state(uuid, text, real, jsonb, jsonb, jsonb) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.create_bmad_task_checkpoint(uuid, text, text, text) TO authenticated, service_role;

-- 11. Create triggers for automatic timestamp updates
CREATE OR REPLACE FUNCTION public.update_bmad_task_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_bmad_task_timestamp
    BEFORE UPDATE ON public.bmad_active_tasks
    FOR EACH ROW
    EXECUTE FUNCTION public.update_bmad_task_timestamp();

-- 12. Create view for task dependency analysis
CREATE OR REPLACE VIEW public.bmad_task_dependency_graph AS
SELECT 
    t.task_id,
    t.task_name,
    t.status,
    t.progress,
    t.persona_type,
    t.session_id,
    COALESCE(
        json_agg(
            json_build_object(
                'task_id', d.depends_on_task_id,
                'task_name', dep_task.task_name,
                'dependency_type', d.dependency_type,
                'status', dep_task.status
            )
        ) FILTER (WHERE d.depends_on_task_id IS NOT NULL),
        '[]'::json
    ) as dependencies,
    COALESCE(
        json_agg(
            json_build_object(
                'task_id', dep_task.task_id,
                'task_name', dep_task.task_name,
                'dependency_type', 'dependent',
                'status', dep_task.status
            )
        ) FILTER (WHERE dep_task.task_id IS NOT NULL),
        '[]'::json
    ) as dependents
FROM public.bmad_active_tasks t
LEFT JOIN public.bmad_task_dependencies d ON t.task_id = d.task_id
LEFT JOIN public.bmad_active_tasks dep_task ON d.depends_on_task_id = dep_task.task_id
LEFT JOIN public.bmad_task_dependencies dep_dep ON t.task_id = dep_dep.depends_on_task_id
LEFT JOIN public.bmad_active_tasks dep_task2 ON dep_dep.task_id = dep_task2.task_id
GROUP BY t.task_id, t.task_name, t.status, t.progress, t.persona_type, t.session_id;

-- Grant access to the view
GRANT SELECT ON public.bmad_task_dependency_graph TO authenticated, service_role;
