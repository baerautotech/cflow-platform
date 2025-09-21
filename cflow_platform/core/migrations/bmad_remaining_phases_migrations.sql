-- BMAD Remaining Phases Database Migrations
-- This file contains all database schema changes for Phases 4-6

-- ============================================================================
-- PHASE 4: TESTING & VALIDATION FRAMEWORK
-- ============================================================================

-- UAT Test Scenarios
CREATE TABLE IF NOT EXISTS uat_test_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    user_journey JSONB NOT NULL,
    acceptance_criteria JSONB NOT NULL,
    expected_outcomes JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- UAT Test Results
CREATE TABLE IF NOT EXISTS uat_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID REFERENCES uat_test_scenarios(id),
    test_session_id UUID NOT NULL,
    user_id UUID REFERENCES users(id),
    execution_status VARCHAR(50) NOT NULL,
    results JSONB NOT NULL,
    metrics JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Usability Test Results
CREATE TABLE IF NOT EXISTS usability_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    component_id VARCHAR(255) NOT NULL,
    test_type VARCHAR(100) NOT NULL,
    user_id UUID REFERENCES users(id),
    interaction_data JSONB NOT NULL,
    usability_score DECIMAL(5,2),
    issues JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Accessibility Test Results
CREATE TABLE IF NOT EXISTS accessibility_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interface_id VARCHAR(255) NOT NULL,
    wcag_level VARCHAR(10) NOT NULL,
    compliance_status VARCHAR(50) NOT NULL,
    violations JSONB,
    recommendations JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- System Metrics
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    metric_unit VARCHAR(50),
    tags JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Alert Rules
CREATE TABLE IF NOT EXISTS alert_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    metric_name VARCHAR(255) NOT NULL,
    threshold_value DECIMAL(15,4) NOT NULL,
    comparison_operator VARCHAR(10) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Alert History
CREATE TABLE IF NOT EXISTS alert_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID REFERENCES alert_rules(id),
    metric_value DECIMAL(15,4) NOT NULL,
    threshold_value DECIMAL(15,4) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    notification_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance Insights
CREATE TABLE IF NOT EXISTS performance_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insight_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    recommendations JSONB,
    metrics_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- PHASE 5: ADVANCED FEATURES & EXPANSION PACKS
-- ============================================================================

-- HIL Sessions
CREATE TABLE IF NOT EXISTS hil_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    session_data JSONB,
    context JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- HIL Session History
CREATE TABLE IF NOT EXISTS hil_session_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES hil_sessions(id),
    user_input JSONB NOT NULL,
    system_response JSONB NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- HIL Approval Workflows
CREATE TABLE IF NOT EXISTS hil_approval_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    workflow_config JSONB NOT NULL,
    approval_rules JSONB NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- HIL Approval Requests
CREATE TABLE IF NOT EXISTS hil_approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES hil_approval_workflows(id),
    requester_id UUID REFERENCES users(id),
    request_data JSONB NOT NULL,
    status VARCHAR(50) NOT NULL,
    approval_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP
);

-- Project Analyses
CREATE TABLE IF NOT EXISTS project_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_path VARCHAR(500) NOT NULL,
    project_type VARCHAR(50) NOT NULL,
    analysis_data JSONB NOT NULL,
    complexity_score DECIMAL(5,2),
    tech_stack JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Brownfield Workflow Executions
CREATE TABLE IF NOT EXISTS brownfield_workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES project_analyses(id),
    workflow_type VARCHAR(100) NOT NULL,
    execution_config JSONB NOT NULL,
    status VARCHAR(50) NOT NULL,
    results JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Greenfield Workflow Executions
CREATE TABLE IF NOT EXISTS greenfield_workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_spec JSONB NOT NULL,
    workflow_type VARCHAR(100) NOT NULL,
    execution_config JSONB NOT NULL,
    status VARCHAR(50) NOT NULL,
    results JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Workflow Analytics
CREATE TABLE IF NOT EXISTS workflow_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id VARCHAR(255) NOT NULL,
    execution_id UUID NOT NULL,
    performance_metrics JSONB NOT NULL,
    bottleneck_data JSONB,
    optimization_recommendations JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- User Behavior Analytics
CREATE TABLE IF NOT EXISTS user_behavior_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id UUID NOT NULL,
    behavior_data JSONB NOT NULL,
    interaction_patterns JSONB,
    engagement_metrics JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Deployment History
CREATE TABLE IF NOT EXISTS deployment_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deployment_id VARCHAR(255) UNIQUE NOT NULL,
    environment VARCHAR(100) NOT NULL,
    service_name VARCHAR(255) NOT NULL,
    version VARCHAR(100) NOT NULL,
    deployment_status VARCHAR(50) NOT NULL,
    deployment_config JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Production Health Status
CREATE TABLE IF NOT EXISTS production_health_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(255) NOT NULL,
    health_status VARCHAR(50) NOT NULL,
    performance_metrics JSONB,
    error_rates JSONB,
    resource_utilization JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Rollback History
CREATE TABLE IF NOT EXISTS rollback_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_deployment_id VARCHAR(255) NOT NULL,
    rollback_reason TEXT,
    rollback_status VARCHAR(50) NOT NULL,
    backup_id VARCHAR(255),
    rollback_config JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- PHASE 6: FINAL CLEANUP & VALIDATION
-- ============================================================================

-- Cleanup Operations
CREATE TABLE IF NOT EXISTS cleanup_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    results JSONB,
    files_processed INTEGER DEFAULT 0,
    files_modified INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Validation Results
CREATE TABLE IF NOT EXISTS validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    validation_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    results JSONB NOT NULL,
    test_coverage DECIMAL(5,2),
    performance_metrics JSONB,
    security_metrics JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Final Validation Summary
CREATE TABLE IF NOT EXISTS final_validation_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    validation_run_id UUID NOT NULL,
    overall_status VARCHAR(50) NOT NULL,
    functionality_score DECIMAL(5,2),
    performance_score DECIMAL(5,2),
    security_score DECIMAL(5,2),
    completion_percentage DECIMAL(5,2),
    summary_report JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- UAT Test Scenarios indexes
CREATE INDEX IF NOT EXISTS idx_uat_test_scenarios_name ON uat_test_scenarios(name);
CREATE INDEX IF NOT EXISTS idx_uat_test_scenarios_created_at ON uat_test_scenarios(created_at);

-- UAT Test Results indexes
CREATE INDEX IF NOT EXISTS idx_uat_test_results_scenario_id ON uat_test_results(scenario_id);
CREATE INDEX IF NOT EXISTS idx_uat_test_results_user_id ON uat_test_results(user_id);
CREATE INDEX IF NOT EXISTS idx_uat_test_results_created_at ON uat_test_results(created_at);

-- System Metrics indexes
CREATE INDEX IF NOT EXISTS idx_system_metrics_name ON system_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_metrics_name_timestamp ON system_metrics(metric_name, timestamp);

-- Alert Rules indexes
CREATE INDEX IF NOT EXISTS idx_alert_rules_enabled ON alert_rules(enabled);
CREATE INDEX IF NOT EXISTS idx_alert_rules_severity ON alert_rules(severity);

-- Alert History indexes
CREATE INDEX IF NOT EXISTS idx_alert_history_rule_id ON alert_history(rule_id);
CREATE INDEX IF NOT EXISTS idx_alert_history_status ON alert_history(status);
CREATE INDEX IF NOT EXISTS idx_alert_history_created_at ON alert_history(created_at);

-- HIL Sessions indexes
CREATE INDEX IF NOT EXISTS idx_hil_sessions_user_id ON hil_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_hil_sessions_status ON hil_sessions(status);
CREATE INDEX IF NOT EXISTS idx_hil_sessions_created_at ON hil_sessions(created_at);

-- HIL Session History indexes
CREATE INDEX IF NOT EXISTS idx_hil_session_history_session_id ON hil_session_history(session_id);
CREATE INDEX IF NOT EXISTS idx_hil_session_history_timestamp ON hil_session_history(timestamp);

-- Project Analyses indexes
CREATE INDEX IF NOT EXISTS idx_project_analyses_project_type ON project_analyses(project_type);
CREATE INDEX IF NOT EXISTS idx_project_analyses_created_at ON project_analyses(created_at);

-- Deployment History indexes
CREATE INDEX IF NOT EXISTS idx_deployment_history_deployment_id ON deployment_history(deployment_id);
CREATE INDEX IF NOT EXISTS idx_deployment_history_service_name ON deployment_history(service_name);
CREATE INDEX IF NOT EXISTS idx_deployment_history_status ON deployment_history(deployment_status);
CREATE INDEX IF NOT EXISTS idx_deployment_history_created_at ON deployment_history(created_at);

-- Production Health Status indexes
CREATE INDEX IF NOT EXISTS idx_production_health_service_name ON production_health_status(service_name);
CREATE INDEX IF NOT EXISTS idx_production_health_status ON production_health_status(health_status);
CREATE INDEX IF NOT EXISTS idx_production_health_timestamp ON production_health_status(timestamp);

-- Validation Results indexes
CREATE INDEX IF NOT EXISTS idx_validation_results_type ON validation_results(validation_type);
CREATE INDEX IF NOT EXISTS idx_validation_results_status ON validation_results(status);
CREATE INDEX IF NOT EXISTS idx_validation_results_created_at ON validation_results(created_at);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE uat_test_scenarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE uat_test_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE usability_test_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE accessibility_test_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE alert_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE alert_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE hil_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE hil_session_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE hil_approval_workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE hil_approval_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE brownfield_workflow_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE greenfield_workflow_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_behavior_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE deployment_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE production_health_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE rollback_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleanup_operations ENABLE ROW LEVEL SECURITY;
ALTER TABLE validation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE final_validation_summary ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for user-specific data
CREATE POLICY "Users can view their own UAT results" ON uat_test_results
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own usability test results" ON usability_test_results
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own HIL sessions" ON hil_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own HIL session history" ON hil_session_history
    FOR SELECT USING (EXISTS (
        SELECT 1 FROM hil_sessions 
        WHERE hil_sessions.id = hil_session_history.session_id 
        AND hil_sessions.user_id = auth.uid()
    ));

CREATE POLICY "Users can view their own behavior analytics" ON user_behavior_analytics
    FOR SELECT USING (auth.uid() = user_id);

-- Create RLS policies for admin/system data
CREATE POLICY "System can manage system metrics" ON system_metrics
    FOR ALL USING (true);

CREATE POLICY "System can manage alert rules" ON alert_rules
    FOR ALL USING (true);

CREATE POLICY "System can manage alert history" ON alert_history
    FOR ALL USING (true);

CREATE POLICY "System can manage performance insights" ON performance_insights
    FOR ALL USING (true);

CREATE POLICY "System can manage deployment history" ON deployment_history
    FOR ALL USING (true);

CREATE POLICY "System can manage production health status" ON production_health_status
    FOR ALL USING (true);

CREATE POLICY "System can manage rollback history" ON rollback_history
    FOR ALL USING (true);

CREATE POLICY "System can manage cleanup operations" ON cleanup_operations
    FOR ALL USING (true);

CREATE POLICY "System can manage validation results" ON validation_results
    FOR ALL USING (true);

CREATE POLICY "System can manage final validation summary" ON final_validation_summary
    FOR ALL USING (true);

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at columns
CREATE TRIGGER update_uat_test_scenarios_updated_at 
    BEFORE UPDATE ON uat_test_scenarios 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_hil_sessions_updated_at 
    BEFORE UPDATE ON hil_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to generate deployment ID
CREATE OR REPLACE FUNCTION generate_deployment_id()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.deployment_id IS NULL OR NEW.deployment_id = '' THEN
        NEW.deployment_id = 'deploy_' || NEW.service_name || '_' || 
                           TO_CHAR(NOW(), 'YYYYMMDD_HH24MISS') || '_' || 
                           SUBSTRING(NEW.id::text, 1, 8);
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for deployment ID generation
CREATE TRIGGER generate_deployment_id_trigger
    BEFORE INSERT ON deployment_history
    FOR EACH ROW EXECUTE FUNCTION generate_deployment_id();

-- Function to calculate overall validation score
CREATE OR REPLACE FUNCTION calculate_validation_score(
    functionality_score DECIMAL,
    performance_score DECIMAL,
    security_score DECIMAL
)
RETURNS DECIMAL AS $$
BEGIN
    RETURN (functionality_score * 0.4 + performance_score * 0.3 + security_score * 0.3);
END;
$$ language 'plpgsql';

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View for UAT test results with scenario details
CREATE OR REPLACE VIEW uat_test_results_with_scenarios AS
SELECT 
    utr.id,
    utr.test_session_id,
    utr.user_id,
    utr.execution_status,
    utr.results,
    utr.metrics,
    utr.created_at,
    uts.name as scenario_name,
    uts.description as scenario_description,
    uts.user_journey,
    uts.acceptance_criteria
FROM uat_test_results utr
JOIN uat_test_scenarios uts ON utr.scenario_id = uts.id;

-- View for HIL sessions with user details
CREATE OR REPLACE VIEW hil_sessions_with_users AS
SELECT 
    hs.id,
    hs.user_id,
    hs.session_type,
    hs.status,
    hs.session_data,
    hs.context,
    hs.created_at,
    hs.updated_at,
    u.email as user_email,
    u.full_name as user_name
FROM hil_sessions hs
JOIN users u ON hs.user_id = u.id;

-- View for deployment history with health status
CREATE OR REPLACE VIEW deployment_history_with_health AS
SELECT 
    dh.id,
    dh.deployment_id,
    dh.environment,
    dh.service_name,
    dh.version,
    dh.deployment_status,
    dh.deployment_config,
    dh.created_at,
    dh.completed_at,
    phs.health_status,
    phs.performance_metrics,
    phs.error_rates,
    phs.resource_utilization
FROM deployment_history dh
LEFT JOIN production_health_status phs ON dh.service_name = phs.service_name
WHERE phs.timestamp = (
    SELECT MAX(timestamp) 
    FROM production_health_status 
    WHERE service_name = dh.service_name
);

-- View for system metrics summary
CREATE OR REPLACE VIEW system_metrics_summary AS
SELECT 
    metric_name,
    COUNT(*) as metric_count,
    AVG(metric_value) as avg_value,
    MIN(metric_value) as min_value,
    MAX(metric_value) as max_value,
    MIN(timestamp) as first_metric,
    MAX(timestamp) as last_metric
FROM system_metrics
GROUP BY metric_name;

-- View for validation results summary
CREATE OR REPLACE VIEW validation_results_summary AS
SELECT 
    validation_type,
    COUNT(*) as total_validations,
    COUNT(CASE WHEN status = 'PASS' THEN 1 END) as passed_validations,
    COUNT(CASE WHEN status = 'FAIL' THEN 1 END) as failed_validations,
    COUNT(CASE WHEN status = 'PARTIAL' THEN 1 END) as partial_validations,
    AVG(test_coverage) as avg_test_coverage,
    MIN(created_at) as first_validation,
    MAX(created_at) as last_validation
FROM validation_results
GROUP BY validation_type;

-- ============================================================================
-- SAMPLE DATA FOR TESTING
-- ============================================================================

-- Insert sample UAT test scenarios
INSERT INTO uat_test_scenarios (name, description, user_journey, acceptance_criteria, expected_outcomes) VALUES
('User Login Flow', 'Test complete user login process', 
 '{"steps": ["navigate_to_login", "enter_credentials", "click_login", "verify_dashboard"]}',
 '{"criteria": ["login_form_visible", "credentials_accepted", "dashboard_displayed"]}',
 '{"outcomes": ["successful_login", "dashboard_access", "user_session_created"]}'),
('Document Creation', 'Test document creation workflow',
 '{"steps": ["navigate_to_documents", "click_create", "enter_title", "add_content", "save_document"]}',
 '{"criteria": ["create_button_visible", "title_required", "content_editable", "save_successful"]}',
 '{"outcomes": ["document_created", "title_saved", "content_saved", "document_listed"]}');

-- Insert sample alert rules
INSERT INTO alert_rules (name, description, metric_name, threshold_value, comparison_operator, severity) VALUES
('High CPU Usage', 'Alert when CPU usage exceeds 80%', 'cpu_usage', 80.0, '>', 'HIGH'),
('Low Memory', 'Alert when available memory is below 1GB', 'available_memory', 1024, '<', 'CRITICAL'),
('High Error Rate', 'Alert when error rate exceeds 5%', 'error_rate', 5.0, '>', 'HIGH'),
('Slow Response Time', 'Alert when response time exceeds 2 seconds', 'response_time', 2000, '>', 'MEDIUM');

-- Insert sample HIL approval workflows
INSERT INTO hil_approval_workflows (name, description, workflow_config, approval_rules) VALUES
('Document Approval', 'Workflow for document approval process',
 '{"steps": ["create_document", "submit_for_review", "review_document", "approve_or_reject"]}',
 '{"rules": ["reviewer_required", "approval_threshold": 1, "timeout_hours": 24]}'),
('Code Deployment', 'Workflow for code deployment approval',
 '{"steps": ["create_deployment", "run_tests", "security_scan", "approve_deployment"]}',
 '{"rules": ["tests_must_pass", "security_scan_required", "approval_threshold": 2]}');

-- ============================================================================
-- CLEANUP AND MAINTENANCE
-- ============================================================================

-- Function to clean up old metrics data
CREATE OR REPLACE FUNCTION cleanup_old_metrics(retention_days INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM system_metrics 
    WHERE timestamp < NOW() - INTERVAL '1 day' * retention_days;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ language 'plpgsql';

-- Function to clean up old alert history
CREATE OR REPLACE FUNCTION cleanup_old_alert_history(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM alert_history 
    WHERE created_at < NOW() - INTERVAL '1 day' * retention_days;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ language 'plpgsql';

-- Function to clean up old HIL session history
CREATE OR REPLACE FUNCTION cleanup_old_hil_sessions(retention_days INTEGER DEFAULT 180)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM hil_session_history 
    WHERE timestamp < NOW() - INTERVAL '1 day' * retention_days;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ language 'plpgsql';

-- ============================================================================
-- GRANTS AND PERMISSIONS
-- ============================================================================

-- Grant permissions to authenticated users
GRANT SELECT ON uat_test_scenarios TO authenticated;
GRANT SELECT ON uat_test_results TO authenticated;
GRANT SELECT ON usability_test_results TO authenticated;
GRANT SELECT ON accessibility_test_results TO authenticated;
GRANT SELECT ON hil_sessions TO authenticated;
GRANT SELECT ON hil_session_history TO authenticated;
GRANT SELECT ON hil_approval_workflows TO authenticated;
GRANT SELECT ON hil_approval_requests TO authenticated;
GRANT SELECT ON project_analyses TO authenticated;
GRANT SELECT ON deployment_history TO authenticated;
GRANT SELECT ON validation_results TO authenticated;

-- Grant permissions to service role
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- ============================================================================
-- MIGRATION COMPLETION
-- ============================================================================

-- Log migration completion
INSERT INTO migration_history (migration_name, applied_at, description) VALUES
('bmad_remaining_phases_migrations', NOW(), 'Database schema for BMAD Phases 4-6: Testing, Advanced Features, and Final Cleanup');

-- Update database version
UPDATE system_info SET 
    version = '2.0.0',
    last_updated = NOW(),
    description = 'BMAD Phases 4-6 Complete'
WHERE key = 'database_version';
