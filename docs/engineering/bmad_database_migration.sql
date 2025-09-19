-- BMAD Database Migration Script
-- This script updates the database to support EPIC document type and HIL approval system

-- Step 1: Update document type constraint to include EPIC and other BMAD document types
ALTER TABLE cerebral_documents DROP CONSTRAINT IF EXISTS cerebral_documents_kind_check;
ALTER TABLE cerebral_documents ADD CONSTRAINT cerebral_documents_kind_check 
CHECK (kind IN ('PRD', 'ARCHITECTURE', 'STORY', 'EPIC', 'PROJECT_BRIEF', 'QA_GATE', 'QA_ASSESSMENT'));

-- Step 2: Add approval workflow columns to cerebral_documents
ALTER TABLE cerebral_documents ADD COLUMN IF NOT EXISTS approval_status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE cerebral_documents ADD COLUMN IF NOT EXISTS last_approval_id UUID;
ALTER TABLE cerebral_documents ADD COLUMN IF NOT EXISTS requires_approval BOOLEAN DEFAULT true;
ALTER TABLE cerebral_documents ADD COLUMN IF NOT EXISTS approval_deadline TIMESTAMP;

-- Step 3: Create epic metadata table
CREATE TABLE IF NOT EXISTS epic_metadata (
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

-- Step 4: Create epic-story relationships table
CREATE TABLE IF NOT EXISTS epic_stories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    epic_id UUID REFERENCES epic_metadata(id) ON DELETE CASCADE,
    story_doc_id UUID REFERENCES cerebral_documents(id) ON DELETE CASCADE,
    story_number INTEGER NOT NULL,
    story_title VARCHAR(255) NOT NULL,
    story_status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Step 5: Create epic content storage table
CREATE TABLE IF NOT EXISTS epic_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    epic_doc_id UUID REFERENCES cerebral_documents(id) ON DELETE CASCADE,
    content_type VARCHAR(50) DEFAULT 'markdown', -- 'markdown', 'html', 'json'
    content_size INTEGER,
    storage_location VARCHAR(500), -- S3 path or database reference
    content_hash VARCHAR(64), -- For integrity checking
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Step 6: Create object storage references table
CREATE TABLE IF NOT EXISTS object_storage_refs (
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

-- Step 7: Create interactive sessions table
CREATE TABLE IF NOT EXISTS interactive_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000100',
    project_id UUID,
    agent_type VARCHAR(50) NOT NULL, -- 'PM', 'Architect', 'PO', etc.
    document_type VARCHAR(50) NOT NULL, -- 'PRD', 'Architecture', 'Story'
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'completed', 'cancelled'
    current_question_index INTEGER DEFAULT 0,
    total_questions INTEGER DEFAULT 0,
    session_data JSONB, -- Stores session state, questions, responses
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Step 8: Create interactive responses table
CREATE TABLE IF NOT EXISTS interactive_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES interactive_sessions(id) ON DELETE CASCADE,
    question_index INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    human_response TEXT NOT NULL,
    agent_feedback TEXT,
    response_metadata JSONB, -- Additional context, timestamps, etc.
    created_at TIMESTAMP DEFAULT NOW()
);

-- Step 9: Create document approvals table
CREATE TABLE IF NOT EXISTS document_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000100',
    doc_id UUID REFERENCES cerebral_documents(id) ON DELETE CASCADE,
    approver VARCHAR(255) NOT NULL, -- User ID or name
    approval_type VARCHAR(50) NOT NULL, -- 'prd_approval', 'arch_approval', 'story_approval'
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    feedback TEXT, -- Human feedback or rejection reason
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Step 10: Create workflow gates table
CREATE TABLE IF NOT EXISTS workflow_gates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000100',
    project_id UUID,
    gate_type VARCHAR(50) NOT NULL, -- 'prd_gate', 'arch_gate', 'story_gate', 'dev_gate'
    gate_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'passed', 'failed', 'waived'
    required_approvals JSONB, -- List of required approval types
    completed_approvals JSONB, -- List of completed approvals
    gate_metadata JSONB, -- Additional gate context
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    passed_at TIMESTAMP
);

-- Step 11: Create approval notifications table
CREATE TABLE IF NOT EXISTS approval_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000100',
    approval_id UUID REFERENCES document_approvals(id) ON DELETE CASCADE,
    recipient VARCHAR(255) NOT NULL, -- User ID or email
    notification_type VARCHAR(50) NOT NULL, -- 'approval_request', 'approval_reminder', 'approval_completed'
    status VARCHAR(20) DEFAULT 'sent', -- 'sent', 'delivered', 'read', 'acted'
    notification_data JSONB, -- Email content, UI data, etc.
    sent_at TIMESTAMP DEFAULT NOW(),
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,
    acted_at TIMESTAMP
);

-- Step 12: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_epic_metadata_epic_doc_id ON epic_metadata(epic_doc_id);
CREATE INDEX IF NOT EXISTS idx_epic_metadata_parent_prd_id ON epic_metadata(parent_prd_id);
CREATE INDEX IF NOT EXISTS idx_epic_stories_epic_id ON epic_stories(epic_id);
CREATE INDEX IF NOT EXISTS idx_epic_stories_story_doc_id ON epic_stories(story_doc_id);
CREATE INDEX IF NOT EXISTS idx_epic_content_epic_doc_id ON epic_content(epic_doc_id);
CREATE INDEX IF NOT EXISTS idx_object_storage_refs_document_id ON object_storage_refs(document_id);
CREATE INDEX IF NOT EXISTS idx_interactive_sessions_project_id ON interactive_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_interactive_sessions_status ON interactive_sessions(status);
CREATE INDEX IF NOT EXISTS idx_interactive_responses_session_id ON interactive_responses(session_id);
CREATE INDEX IF NOT EXISTS idx_document_approvals_doc_id ON document_approvals(doc_id);
CREATE INDEX IF NOT EXISTS idx_document_approvals_status ON document_approvals(status);
CREATE INDEX IF NOT EXISTS idx_workflow_gates_project_id ON workflow_gates(project_id);
CREATE INDEX IF NOT EXISTS idx_workflow_gates_gate_type ON workflow_gates(gate_type);
CREATE INDEX IF NOT EXISTS idx_approval_notifications_approval_id ON approval_notifications(approval_id);
CREATE INDEX IF NOT EXISTS idx_approval_notifications_recipient ON approval_notifications(recipient);

-- Step 13: Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_epic_metadata_updated_at ON epic_metadata;
CREATE TRIGGER update_epic_metadata_updated_at BEFORE UPDATE ON epic_metadata FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_epic_content_updated_at ON epic_content;
CREATE TRIGGER update_epic_content_updated_at BEFORE UPDATE ON epic_content FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_interactive_sessions_updated_at ON interactive_sessions;
CREATE TRIGGER update_interactive_sessions_updated_at BEFORE UPDATE ON interactive_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_document_approvals_updated_at ON document_approvals;
CREATE TRIGGER update_document_approvals_updated_at BEFORE UPDATE ON document_approvals FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_workflow_gates_updated_at ON workflow_gates;
CREATE TRIGGER update_workflow_gates_updated_at BEFORE UPDATE ON workflow_gates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Step 14: Create views for common queries
CREATE OR REPLACE VIEW active_interactive_sessions AS
SELECT 
    s.*,
    COUNT(r.id) as response_count
FROM interactive_sessions s
LEFT JOIN interactive_responses r ON s.id = r.session_id
WHERE s.status = 'active'
GROUP BY s.id;

CREATE OR REPLACE VIEW pending_approvals AS
SELECT 
    da.*,
    cd.kind as document_type,
    cd.content as document_content
FROM document_approvals da
JOIN cerebral_documents cd ON da.doc_id = cd.id
WHERE da.status = 'pending';

CREATE OR REPLACE VIEW workflow_gate_status AS
SELECT 
    wg.*,
    COUNT(da.id) as pending_approvals
FROM workflow_gates wg
LEFT JOIN document_approvals da ON da.doc_id IN (
    SELECT id FROM cerebral_documents WHERE project_id = wg.project_id
) AND da.status = 'pending'
GROUP BY wg.id;

-- Step 15: Insert sample workflow gates
INSERT INTO workflow_gates (project_id, gate_type, gate_status, required_approvals) VALUES
('00000000-0000-0000-0000-000000000100', 'prd_gate', 'pending', '["prd_approval"]'),
('00000000-0000-0000-0000-000000000100', 'arch_gate', 'pending', '["arch_approval"]'),
('00000000-0000-0000-0000-000000000100', 'story_gate', 'pending', '["story_approval"]'),
('00000000-0000-0000-0000-000000000100', 'dev_gate', 'pending', '["dev_approval"]')
ON CONFLICT DO NOTHING;

-- Migration complete
SELECT 'BMAD Database Migration Complete' as status;
