-- BMAD Persona Context Schema Migration
-- This migration creates tables for Phase 2: Unified Persona Activation
-- Supporting context preservation and session management

-- 1. Create bmad_sessions table for session management
CREATE TABLE IF NOT EXISTS public.bmad_sessions (
  session_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  project_id uuid NOT NULL,
  active_persona_id uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  last_activity timestamptz NOT NULL DEFAULT now(),
  global_context jsonb DEFAULT '{}',
  workflow_state jsonb,
  
  CONSTRAINT unique_user_project_session UNIQUE (user_id, project_id, created_at)
);

-- 2. Create bmad_persona_contexts table for persona state management
CREATE TABLE IF NOT EXISTS public.bmad_persona_contexts (
  persona_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid NOT NULL REFERENCES public.bmad_sessions(session_id) ON DELETE CASCADE,
  persona_type text NOT NULL CHECK (persona_type IN (
    'bmad-orchestrator', 'pm', 'arch', 'dev', 'sm', 'analyst', 'ux', 'tester', 'bmad-master'
  )),
  state text NOT NULL DEFAULT 'active' CHECK (state IN ('active', 'suspended', 'checkpointed', 'archived')),
  created_at timestamptz NOT NULL DEFAULT now(),
  last_accessed timestamptz NOT NULL DEFAULT now(),
  context_data jsonb DEFAULT '{}',
  checkpoint_data jsonb,
  parent_context_id uuid REFERENCES public.bmad_persona_contexts(persona_id) ON DELETE SET NULL,
  child_contexts jsonb DEFAULT '[]',
  
  CONSTRAINT unique_session_persona_type UNIQUE (session_id, persona_type)
);

-- 3. Create bmad_checkpoints table for context checkpointing
CREATE TABLE IF NOT EXISTS public.bmad_checkpoints (
  checkpoint_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid NOT NULL REFERENCES public.bmad_sessions(session_id) ON DELETE CASCADE,
  persona_id uuid REFERENCES public.bmad_persona_contexts(persona_id) ON DELETE CASCADE,
  checkpoint_name text,
  timestamp timestamptz NOT NULL DEFAULT now(),
  checkpoint_data jsonb NOT NULL,
  description text,
  
  CONSTRAINT unique_checkpoint_name_per_session UNIQUE (session_id, checkpoint_name)
);

-- 4. Create bmad_persona_transitions table for tracking persona switches
CREATE TABLE IF NOT EXISTS public.bmad_persona_transitions (
  transition_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid NOT NULL REFERENCES public.bmad_sessions(session_id) ON DELETE CASCADE,
  from_persona_id uuid REFERENCES public.bmad_persona_contexts(persona_id) ON DELETE SET NULL,
  to_persona_id uuid NOT NULL REFERENCES public.bmad_persona_contexts(persona_id) ON DELETE CASCADE,
  transition_reason text,
  context_preserved boolean DEFAULT true,
  transition_data jsonb DEFAULT '{}',
  timestamp timestamptz NOT NULL DEFAULT now()
);

-- 5. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_bmad_sessions_user_project ON public.bmad_sessions(user_id, project_id);
CREATE INDEX IF NOT EXISTS idx_bmad_sessions_last_activity ON public.bmad_sessions(last_activity);
CREATE INDEX IF NOT EXISTS idx_bmad_persona_contexts_session ON public.bmad_persona_contexts(session_id);
CREATE INDEX IF NOT EXISTS idx_bmad_persona_contexts_type ON public.bmad_persona_contexts(persona_type);
CREATE INDEX IF NOT EXISTS idx_bmad_persona_contexts_state ON public.bmad_persona_contexts(state);
CREATE INDEX IF NOT EXISTS idx_bmad_checkpoints_session ON public.bmad_checkpoints(session_id);
CREATE INDEX IF NOT EXISTS idx_bmad_checkpoints_persona ON public.bmad_checkpoints(persona_id);
CREATE INDEX IF NOT EXISTS idx_bmad_transitions_session ON public.bmad_persona_transitions(session_id);
CREATE INDEX IF NOT EXISTS idx_bmad_transitions_timestamp ON public.bmad_persona_transitions(timestamp);

-- 6. Row Level Security (RLS) Policies
ALTER TABLE public.bmad_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bmad_persona_contexts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bmad_checkpoints ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bmad_persona_transitions ENABLE ROW LEVEL SECURITY;

-- Policy for bmad_sessions
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='bmad_sessions' AND policyname='bs_tenant_isolation') THEN
    CREATE POLICY bs_tenant_isolation ON public.bmad_sessions
      FOR ALL TO authenticated
      USING (user_id::text = coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb ->> 'user_id')
      WITH CHECK (user_id::text = coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb ->> 'user_id');
  END IF;
END $$;

-- Policy for bmad_persona_contexts
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='bmad_persona_contexts' AND policyname='bpc_tenant_isolation') THEN
    CREATE POLICY bpc_tenant_isolation ON public.bmad_persona_contexts
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

-- Policy for bmad_checkpoints
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='bmad_checkpoints' AND policyname='bc_tenant_isolation') THEN
    CREATE POLICY bc_tenant_isolation ON public.bmad_checkpoints
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

-- Policy for bmad_persona_transitions
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='bmad_persona_transitions' AND policyname='bpt_tenant_isolation') THEN
    CREATE POLICY bpt_tenant_isolation ON public.bmad_persona_transitions
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

-- 7. Grant necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON public.bmad_sessions TO authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.bmad_persona_contexts TO authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.bmad_checkpoints TO authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.bmad_persona_transitions TO authenticated, service_role;

-- 8. Create utility functions for persona context management
CREATE OR REPLACE FUNCTION public.create_bmad_session(
    p_user_id uuid,
    p_project_id uuid,
    p_initial_persona_type text DEFAULT 'bmad-orchestrator'
)
RETURNS uuid AS $$
DECLARE
    new_session_id uuid;
    new_persona_id uuid;
BEGIN
    -- Create session
    INSERT INTO public.bmad_sessions (user_id, project_id)
    VALUES (p_user_id, p_project_id)
    RETURNING session_id INTO new_session_id;
    
    -- Create initial persona context
    INSERT INTO public.bmad_persona_contexts (
        session_id, persona_type, state, context_data
    )
    VALUES (
        new_session_id, 
        p_initial_persona_type, 
        'active',
        jsonb_build_object(
            'persona_type', p_initial_persona_type,
            'activation_time', now()::text,
            'conversation_history', '[]'::jsonb,
            'current_task', null,
            'workflow_state', '{}'::jsonb
        )
    )
    RETURNING persona_id INTO new_persona_id;
    
    -- Update session with active persona
    UPDATE public.bmad_sessions 
    SET active_persona_id = new_persona_id
    WHERE session_id = new_session_id;
    
    RETURN new_session_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION public.switch_bmad_persona(
    p_session_id uuid,
    p_target_persona_type text,
    p_context_preserved boolean DEFAULT true
)
RETURNS uuid AS $$
DECLARE
    new_persona_id uuid;
    current_persona_id uuid;
    session_user_id uuid;
BEGIN
    -- Get current session info
    SELECT active_persona_id, user_id INTO current_persona_id, session_user_id
    FROM public.bmad_sessions 
    WHERE session_id = p_session_id;
    
    IF session_user_id IS NULL THEN
        RAISE EXCEPTION 'Session not found or access denied';
    END IF;
    
    -- Check if target persona already exists
    SELECT persona_id INTO new_persona_id
    FROM public.bmad_persona_contexts
    WHERE session_id = p_session_id AND persona_type = p_target_persona_type;
    
    IF new_persona_id IS NULL THEN
        -- Create new persona context
        INSERT INTO public.bmad_persona_contexts (
            session_id, persona_type, state, context_data
        )
        VALUES (
            p_session_id, 
            p_target_persona_type, 
            'active',
            jsonb_build_object(
                'persona_type', p_target_persona_type,
                'activation_time', now()::text,
                'conversation_history', '[]'::jsonb,
                'current_task', null,
                'workflow_state', '{}'::jsonb
            )
        )
        RETURNING persona_id INTO new_persona_id;
    ELSE
        -- Update existing persona to active
        UPDATE public.bmad_persona_contexts
        SET state = 'active', last_accessed = now()
        WHERE persona_id = new_persona_id;
    END IF;
    
    -- Update previous persona to suspended
    UPDATE public.bmad_persona_contexts
    SET state = 'suspended'
    WHERE persona_id = current_persona_id;
    
    -- Update session active persona
    UPDATE public.bmad_sessions
    SET active_persona_id = new_persona_id, last_activity = now()
    WHERE session_id = p_session_id;
    
    -- Log transition
    INSERT INTO public.bmad_persona_transitions (
        session_id, from_persona_id, to_persona_id, 
        transition_reason, context_preserved
    )
    VALUES (
        p_session_id, current_persona_id, new_persona_id,
        'user_requested_switch', p_context_preserved
    );
    
    RETURN new_persona_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION public.create_bmad_checkpoint(
    p_session_id uuid,
    p_checkpoint_name text DEFAULT NULL
)
RETURNS uuid AS $$
DECLARE
    new_checkpoint_id uuid;
    current_persona_id uuid;
    session_user_id uuid;
    persona_context jsonb;
BEGIN
    -- Get current session and persona info
    SELECT active_persona_id, user_id INTO current_persona_id, session_user_id
    FROM public.bmad_sessions 
    WHERE session_id = p_session_id;
    
    IF session_user_id IS NULL THEN
        RAISE EXCEPTION 'Session not found or access denied';
    END IF;
    
    -- Get persona context
    SELECT context_data INTO persona_context
    FROM public.bmad_persona_contexts
    WHERE persona_id = current_persona_id;
    
    -- Create checkpoint
    INSERT INTO public.bmad_checkpoints (
        session_id, persona_id, checkpoint_name, checkpoint_data
    )
    VALUES (
        p_session_id,
        current_persona_id,
        p_checkpoint_name,
        jsonb_build_object(
            'checkpoint_id', gen_random_uuid(),
            'timestamp', now()::text,
            'session_id', p_session_id,
            'persona_id', current_persona_id,
            'persona_context', persona_context,
            'checkpoint_name', p_checkpoint_name
        )
    )
    RETURNING checkpoint_id INTO new_checkpoint_id;
    
    -- Update persona state to checkpointed
    UPDATE public.bmad_persona_contexts
    SET state = 'checkpointed', last_accessed = now()
    WHERE persona_id = current_persona_id;
    
    RETURN new_checkpoint_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 9. Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION public.create_bmad_session(uuid, uuid, text) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.switch_bmad_persona(uuid, text, boolean) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.create_bmad_checkpoint(uuid, text) TO authenticated, service_role;

-- 10. Create indexes on JSONB fields for better query performance
CREATE INDEX IF NOT EXISTS idx_bmad_sessions_global_context_gin ON public.bmad_sessions USING gin(global_context);
CREATE INDEX IF NOT EXISTS idx_bmad_persona_contexts_context_data_gin ON public.bmad_persona_contexts USING gin(context_data);
CREATE INDEX IF NOT EXISTS idx_bmad_checkpoints_checkpoint_data_gin ON public.bmad_checkpoints USING gin(checkpoint_data);
CREATE INDEX IF NOT EXISTS idx_bmad_transitions_transition_data_gin ON public.bmad_persona_transitions USING gin(transition_data);
