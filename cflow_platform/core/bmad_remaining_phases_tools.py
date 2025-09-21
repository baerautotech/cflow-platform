"""
BMAD Remaining Phases MCP Tool Definitions
This module defines all MCP tools for Phases 4-6 of the BMAD implementation.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class MCPTool:
    """Represents an MCP tool definition"""
    name: str
    description: str
    inputSchema: Dict[str, Any]

# ============================================================================
# PHASE 4: TESTING & VALIDATION FRAMEWORK TOOLS
# ============================================================================

# User Acceptance Testing Tools
UAT_TOOLS = [
    MCPTool(
        name="bmad_uat_create_scenario",
        description="Create a new UAT test scenario with user journey and acceptance criteria",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of the UAT scenario"},
                "description": {"type": "string", "description": "Description of the scenario"},
                "user_journey": {"type": "object", "description": "User journey steps as JSON"},
                "acceptance_criteria": {"type": "object", "description": "Acceptance criteria as JSON"},
                "expected_outcomes": {"type": "object", "description": "Expected outcomes as JSON"}
            },
            "required": ["name", "user_journey", "acceptance_criteria", "expected_outcomes"]
        }
    ),
    MCPTool(
        name="bmad_uat_execute_scenario",
        description="Execute a UAT test scenario and return results",
        inputSchema={
            "type": "object",
            "properties": {
                "scenario_id": {"type": "string", "description": "ID of the UAT scenario to execute"},
                "user_id": {"type": "string", "description": "ID of the user executing the test"},
                "test_session_id": {"type": "string", "description": "Unique test session identifier"}
            },
            "required": ["scenario_id", "user_id", "test_session_id"]
        }
    ),
    MCPTool(
        name="bmad_uat_list_scenarios",
        description="List all available UAT test scenarios",
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Maximum number of scenarios to return", "default": 50},
                "offset": {"type": "integer", "description": "Number of scenarios to skip", "default": 0}
            }
        }
    ),
    MCPTool(
        name="bmad_uat_get_results",
        description="Get UAT test results for a specific scenario or session",
        inputSchema={
            "type": "object",
            "properties": {
                "scenario_id": {"type": "string", "description": "ID of the UAT scenario"},
                "test_session_id": {"type": "string", "description": "ID of the test session"},
                "user_id": {"type": "string", "description": "ID of the user"}
            }
        }
    ),
    MCPTool(
        name="bmad_usability_test_component",
        description="Test UI component for usability issues",
        inputSchema={
            "type": "object",
            "properties": {
                "component_id": {"type": "string", "description": "ID of the UI component"},
                "test_type": {"type": "string", "description": "Type of usability test"},
                "user_id": {"type": "string", "description": "ID of the user performing the test"},
                "interaction_data": {"type": "object", "description": "User interaction data"}
            },
            "required": ["component_id", "test_type", "user_id", "interaction_data"]
        }
    ),
    MCPTool(
        name="bmad_accessibility_validate",
        description="Validate interface accessibility compliance",
        inputSchema={
            "type": "object",
            "properties": {
                "interface_id": {"type": "string", "description": "ID of the interface to validate"},
                "wcag_level": {"type": "string", "description": "WCAG compliance level (A, AA, AAA)"},
                "validation_type": {"type": "string", "description": "Type of accessibility validation"}
            },
            "required": ["interface_id", "wcag_level"]
        }
    )
]

# Production Monitoring Tools
MONITORING_TOOLS = [
    MCPTool(
        name="bmad_monitoring_start",
        description="Start comprehensive production monitoring",
        inputSchema={
            "type": "object",
            "properties": {
                "monitoring_config": {"type": "object", "description": "Monitoring configuration"},
                "alert_rules": {"type": "array", "items": {"type": "object"}, "description": "Alert rules configuration"}
            }
        }
    ),
    MCPTool(
        name="bmad_monitoring_stop",
        description="Stop production monitoring",
        inputSchema={
            "type": "object",
            "properties": {
                "graceful_shutdown": {"type": "boolean", "description": "Whether to perform graceful shutdown", "default": True}
            }
        }
    ),
    MCPTool(
        name="bmad_monitoring_get_metrics",
        description="Get current system metrics",
        inputSchema={
            "type": "object",
            "properties": {
                "metric_names": {"type": "array", "items": {"type": "string"}, "description": "Specific metrics to retrieve"},
                "time_range": {"type": "string", "description": "Time range for metrics (e.g., '1h', '24h')"},
                "aggregation": {"type": "string", "description": "Aggregation method (avg, min, max, sum)"}
            }
        }
    ),
    MCPTool(
        name="bmad_monitoring_create_alert_rule",
        description="Create a new alert rule",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of the alert rule"},
                "description": {"type": "string", "description": "Description of the alert rule"},
                "metric_name": {"type": "string", "description": "Metric to monitor"},
                "threshold_value": {"type": "number", "description": "Threshold value for the alert"},
                "comparison_operator": {"type": "string", "description": "Comparison operator (>, <, >=, <=, ==, !=)"},
                "severity": {"type": "string", "description": "Alert severity (LOW, MEDIUM, HIGH, CRITICAL)"}
            },
            "required": ["name", "metric_name", "threshold_value", "comparison_operator", "severity"]
        }
    ),
    MCPTool(
        name="bmad_monitoring_get_alerts",
        description="Get current alerts and alert history",
        inputSchema={
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Filter by alert status"},
                "severity": {"type": "string", "description": "Filter by alert severity"},
                "time_range": {"type": "string", "description": "Time range for alert history"},
                "limit": {"type": "integer", "description": "Maximum number of alerts to return", "default": 100}
            }
        }
    ),
    MCPTool(
        name="bmad_monitoring_get_dashboard_data",
        description="Get data for observability dashboard",
        inputSchema={
            "type": "object",
            "properties": {
                "dashboard_type": {"type": "string", "description": "Type of dashboard (overview, performance, health)"},
                "refresh_interval": {"type": "integer", "description": "Refresh interval in seconds", "default": 30}
            }
        }
    )
]

# ============================================================================
# PHASE 5: ADVANCED FEATURES & EXPANSION PACKS TOOLS
# ============================================================================

# HIL Integration Tools
HIL_TOOLS = [
    MCPTool(
        name="bmad_hil_start_session",
        description="Start a new HIL interactive session",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "ID of the user starting the session"},
                "session_type": {"type": "string", "description": "Type of HIL session"},
                "context": {"type": "object", "description": "Session context data"},
                "session_config": {"type": "object", "description": "Session configuration"}
            },
            "required": ["user_id", "session_type"]
        }
    ),
    MCPTool(
        name="bmad_hil_handle_input",
        description="Handle user input in HIL session",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "ID of the HIL session"},
                "user_input": {"type": "object", "description": "User input data"},
                "input_type": {"type": "string", "description": "Type of user input"}
            },
            "required": ["session_id", "user_input"]
        }
    ),
    MCPTool(
        name="bmad_hil_get_session",
        description="Get HIL session details and status",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "ID of the HIL session"},
                "include_history": {"type": "boolean", "description": "Whether to include session history", "default": False}
            },
            "required": ["session_id"]
        }
    ),
    MCPTool(
        name="bmad_hil_end_session",
        description="End a HIL interactive session",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "ID of the HIL session to end"},
                "reason": {"type": "string", "description": "Reason for ending the session"},
                "save_results": {"type": "boolean", "description": "Whether to save session results", "default": True}
            },
            "required": ["session_id"]
        }
    ),
    MCPTool(
        name="bmad_hil_create_approval_workflow",
        description="Create a new HIL approval workflow",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of the approval workflow"},
                "description": {"type": "string", "description": "Description of the workflow"},
                "workflow_config": {"type": "object", "description": "Workflow configuration"},
                "approval_rules": {"type": "object", "description": "Approval rules configuration"}
            },
            "required": ["name", "workflow_config", "approval_rules"]
        }
    ),
    MCPTool(
        name="bmad_hil_process_approval",
        description="Process an approval request in HIL workflow",
        inputSchema={
            "type": "object",
            "properties": {
                "workflow_id": {"type": "string", "description": "ID of the approval workflow"},
                "requester_id": {"type": "string", "description": "ID of the requester"},
                "request_data": {"type": "object", "description": "Approval request data"},
                "approval_data": {"type": "object", "description": "Approval decision data"}
            },
            "required": ["workflow_id", "requester_id", "request_data"]
        }
    ),
    MCPTool(
        name="bmad_hil_generate_questions",
        description="Generate elicitation questions for HIL session",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "ID of the HIL session"},
                "context": {"type": "object", "description": "Context for question generation"},
                "question_type": {"type": "string", "description": "Type of questions to generate"},
                "max_questions": {"type": "integer", "description": "Maximum number of questions", "default": 10}
            },
            "required": ["session_id", "context"]
        }
    ),
    MCPTool(
        name="bmad_hil_analyze_response",
        description="Analyze user response in HIL elicitation",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "ID of the HIL session"},
                "question": {"type": "object", "description": "Original question"},
                "response": {"type": "object", "description": "User response"},
                "analysis_type": {"type": "string", "description": "Type of analysis to perform"}
            },
            "required": ["session_id", "question", "response"]
        }
    )
]

# Brownfield/Greenfield Workflow Tools
WORKFLOW_TOOLS = [
    MCPTool(
        name="bmad_workflow_analyze_project",
        description="Analyze project to determine type (brownfield vs greenfield)",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to the project to analyze"},
                "analysis_depth": {"type": "string", "description": "Depth of analysis (shallow, deep, comprehensive)"},
                "include_dependencies": {"type": "boolean", "description": "Whether to analyze dependencies", "default": True}
            },
            "required": ["project_path"]
        }
    ),
    MCPTool(
        name="bmad_workflow_detect_project_type",
        description="Detect if project is brownfield, greenfield, or mixed",
        inputSchema={
            "type": "object",
            "properties": {
                "analysis_id": {"type": "string", "description": "ID of the project analysis"},
                "confidence_threshold": {"type": "number", "description": "Confidence threshold for detection", "default": 0.8}
            },
            "required": ["analysis_id"]
        }
    ),
    MCPTool(
        name="bmad_workflow_enhance_brownfield",
        description="Enhance existing brownfield project",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "ID of the brownfield project"},
                "enhancement_config": {"type": "object", "description": "Enhancement configuration"},
                "preserve_legacy": {"type": "boolean", "description": "Whether to preserve legacy code", "default": True}
            },
            "required": ["project_id", "enhancement_config"]
        }
    ),
    MCPTool(
        name="bmad_workflow_create_greenfield",
        description="Create new greenfield project",
        inputSchema={
            "type": "object",
            "properties": {
                "project_spec": {"type": "object", "description": "Project specification"},
                "architecture_type": {"type": "string", "description": "Type of architecture to generate"},
                "best_practices": {"type": "array", "items": {"type": "string"}, "description": "Best practices to enforce"}
            },
            "required": ["project_spec"]
        }
    ),
    MCPTool(
        name="bmad_workflow_plan_migration",
        description="Plan migration strategy for brownfield project",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "ID of the project to migrate"},
                "target_architecture": {"type": "object", "description": "Target architecture specification"},
                "migration_strategy": {"type": "string", "description": "Migration strategy (big-bang, incremental, strangler)"}
            },
            "required": ["project_id", "target_architecture"]
        }
    ),
    MCPTool(
        name="bmad_workflow_generate_architecture",
        description="Generate project architecture for greenfield project",
        inputSchema={
            "type": "object",
            "properties": {
                "requirements": {"type": "object", "description": "Project requirements"},
                "constraints": {"type": "object", "description": "Architectural constraints"},
                "patterns": {"type": "array", "items": {"type": "string"}, "description": "Architectural patterns to apply"}
            },
            "required": ["requirements"]
        }
    )
]

# Advanced Monitoring & Analytics Tools
ANALYTICS_TOOLS = [
    MCPTool(
        name="bmad_analytics_analyze_workflow",
        description="Analyze workflow performance and generate insights",
        inputSchema={
            "type": "object",
            "properties": {
                "workflow_id": {"type": "string", "description": "ID of the workflow to analyze"},
                "analysis_period": {"type": "string", "description": "Period for analysis (1d, 7d, 30d)"},
                "include_bottlenecks": {"type": "boolean", "description": "Whether to analyze bottlenecks", "default": True},
                "include_optimizations": {"type": "boolean", "description": "Whether to generate optimizations", "default": True}
            },
            "required": ["workflow_id"]
        }
    ),
    MCPTool(
        name="bmad_analytics_detect_bottlenecks",
        description="Detect bottlenecks in workflow execution",
        inputSchema={
            "type": "object",
            "properties": {
                "workflow_id": {"type": "string", "description": "ID of the workflow"},
                "execution_data": {"type": "object", "description": "Workflow execution data"},
                "threshold": {"type": "number", "description": "Bottleneck detection threshold", "default": 0.8}
            },
            "required": ["workflow_id", "execution_data"]
        }
    ),
    MCPTool(
        name="bmad_analytics_generate_insights",
        description="Generate performance insights and recommendations",
        inputSchema={
            "type": "object",
            "properties": {
                "insight_type": {"type": "string", "description": "Type of insights to generate"},
                "data_source": {"type": "string", "description": "Data source for insights"},
                "time_range": {"type": "string", "description": "Time range for analysis"},
                "include_recommendations": {"type": "boolean", "description": "Whether to include recommendations", "default": True}
            },
            "required": ["insight_type", "data_source"]
        }
    ),
    MCPTool(
        name="bmad_analytics_track_user_behavior",
        description="Track and analyze user behavior patterns",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "ID of the user to track"},
                "session_id": {"type": "string", "description": "ID of the user session"},
                "behavior_data": {"type": "object", "description": "User behavior data"},
                "tracking_type": {"type": "string", "description": "Type of behavior tracking"}
            },
            "required": ["user_id", "behavior_data"]
        }
    ),
    MCPTool(
        name="bmad_analytics_analyze_patterns",
        description="Analyze user behavior patterns and trends",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "ID of the user to analyze"},
                "pattern_type": {"type": "string", "description": "Type of patterns to analyze"},
                "analysis_period": {"type": "string", "description": "Period for pattern analysis"},
                "include_predictions": {"type": "boolean", "description": "Whether to include predictions", "default": False}
            },
            "required": ["user_id", "pattern_type"]
        }
    )
]

# Production Deployment Tools
DEPLOYMENT_TOOLS = [
    MCPTool(
        name="bmad_deployment_deploy_to_production",
        description="Deploy service to production environment",
        inputSchema={
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Name of the service to deploy"},
                "version": {"type": "string", "description": "Version to deploy"},
                "environment": {"type": "string", "description": "Target environment"},
                "deployment_config": {"type": "object", "description": "Deployment configuration"},
                "create_backup": {"type": "boolean", "description": "Whether to create backup before deployment", "default": True}
            },
            "required": ["service_name", "version", "environment", "deployment_config"]
        }
    ),
    MCPTool(
        name="bmad_deployment_validate_deployment",
        description="Validate deployment health and functionality",
        inputSchema={
            "type": "object",
            "properties": {
                "deployment_id": {"type": "string", "description": "ID of the deployment to validate"},
                "validation_type": {"type": "string", "description": "Type of validation to perform"},
                "health_checks": {"type": "array", "items": {"type": "string"}, "description": "Health checks to run"}
            },
            "required": ["deployment_id"]
        }
    ),
    MCPTool(
        name="bmad_deployment_monitor_production",
        description="Monitor production system health",
        inputSchema={
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Name of the service to monitor"},
                "monitoring_config": {"type": "object", "description": "Monitoring configuration"},
                "alert_thresholds": {"type": "object", "description": "Alert thresholds configuration"}
            },
            "required": ["service_name"]
        }
    ),
    MCPTool(
        name="bmad_deployment_create_backup",
        description="Create backup before deployment",
        inputSchema={
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Name of the service to backup"},
                "backup_type": {"type": "string", "description": "Type of backup (full, incremental, differential)"},
                "backup_config": {"type": "object", "description": "Backup configuration"}
            },
            "required": ["service_name", "backup_type"]
        }
    ),
    MCPTool(
        name="bmad_deployment_execute_rollback",
        description="Execute production rollback",
        inputSchema={
            "type": "object",
            "properties": {
                "deployment_id": {"type": "string", "description": "ID of the deployment to rollback"},
                "backup_id": {"type": "string", "description": "ID of the backup to restore"},
                "rollback_reason": {"type": "string", "description": "Reason for rollback"},
                "rollback_config": {"type": "object", "description": "Rollback configuration"}
            },
            "required": ["deployment_id", "backup_id"]
        }
    )
]

# ============================================================================
# PHASE 6: FINAL CLEANUP & VALIDATION TOOLS
# ============================================================================

# Final Cleanup Tools
CLEANUP_TOOLS = [
    MCPTool(
        name="bmad_cleanup_remove_caef_references",
        description="Remove all CAEF references from codebase",
        inputSchema={
            "type": "object",
            "properties": {
                "scan_paths": {"type": "array", "items": {"type": "string"}, "description": "Paths to scan for CAEF references"},
                "dry_run": {"type": "boolean", "description": "Whether to perform dry run without making changes", "default": True},
                "backup_changes": {"type": "boolean", "description": "Whether to backup files before changes", "default": True}
            }
        }
    ),
    MCPTool(
        name="bmad_cleanup_remove_unused_dependencies",
        description="Remove unused dependencies and imports",
        inputSchema={
            "type": "object",
            "properties": {
                "dependency_files": {"type": "array", "items": {"type": "string"}, "description": "Dependency files to analyze"},
                "scan_imports": {"type": "boolean", "description": "Whether to scan for unused imports", "default": True},
                "remove_dead_code": {"type": "boolean", "description": "Whether to remove dead code", "default": True}
            }
        }
    ),
    MCPTool(
        name="bmad_cleanup_update_documentation",
        description="Update documentation to reflect BMAD integration",
        inputSchema={
            "type": "object",
            "properties": {
                "doc_paths": {"type": "array", "items": {"type": "string"}, "description": "Documentation paths to update"},
                "update_readme": {"type": "boolean", "description": "Whether to update README files", "default": True},
                "update_api_docs": {"type": "boolean", "description": "Whether to update API documentation", "default": True},
                "generate_changelog": {"type": "boolean", "description": "Whether to generate changelog", "default": True}
            }
        }
    ),
    MCPTool(
        name="bmad_cleanup_clean_test_suite",
        description="Clean up test suite and remove CAEF test files",
        inputSchema={
            "type": "object",
            "properties": {
                "test_paths": {"type": "array", "items": {"type": "string"}, "description": "Test paths to clean"},
                "remove_caef_tests": {"type": "boolean", "description": "Whether to remove CAEF test files", "default": True},
                "update_fixtures": {"type": "boolean", "description": "Whether to update test fixtures", "default": True},
                "validate_tests": {"type": "boolean", "description": "Whether to validate test suite", "default": True}
            }
        }
    )
]

# Final Validation Tools
VALIDATION_TOOLS = [
    MCPTool(
        name="bmad_validation_comprehensive_functionality",
        description="Validate all BMAD functionality end-to-end",
        inputSchema={
            "type": "object",
            "properties": {
                "validation_scope": {"type": "string", "description": "Scope of validation (full, core, specific)"},
                "include_integration_tests": {"type": "boolean", "description": "Whether to include integration tests", "default": True},
                "include_api_tests": {"type": "boolean", "description": "Whether to include API contract tests", "default": True},
                "include_workflow_tests": {"type": "boolean", "description": "Whether to include workflow tests", "default": True}
            }
        }
    ),
    MCPTool(
        name="bmad_validation_performance_under_load",
        description="Validate system performance under load",
        inputSchema={
            "type": "object",
            "properties": {
                "load_type": {"type": "string", "description": "Type of load test (stress, spike, volume)"},
                "load_config": {"type": "object", "description": "Load test configuration"},
                "performance_thresholds": {"type": "object", "description": "Performance thresholds"},
                "duration": {"type": "integer", "description": "Test duration in minutes", "default": 30}
            },
            "required": ["load_type", "load_config"]
        }
    ),
    MCPTool(
        name="bmad_validation_security_audit",
        description="Perform comprehensive security validation and audit",
        inputSchema={
            "type": "object",
            "properties": {
                "audit_type": {"type": "string", "description": "Type of security audit (full, vulnerability, compliance)"},
                "scan_scope": {"type": "array", "items": {"type": "string"}, "description": "Scope of security scan"},
                "compliance_standards": {"type": "array", "items": {"type": "string"}, "description": "Compliance standards to check"},
                "include_penetration_test": {"type": "boolean", "description": "Whether to include penetration testing", "default": False}
            },
            "required": ["audit_type"]
        }
    ),
    MCPTool(
        name="bmad_validation_generate_report",
        description="Generate comprehensive validation report",
        inputSchema={
            "type": "object",
            "properties": {
                "report_type": {"type": "string", "description": "Type of validation report"},
                "include_metrics": {"type": "boolean", "description": "Whether to include detailed metrics", "default": True},
                "include_recommendations": {"type": "boolean", "description": "Whether to include recommendations", "default": True},
                "format": {"type": "string", "description": "Report format (json, html, pdf)", "default": "json"}
            },
            "required": ["report_type"]
        }
    )
]

# ============================================================================
# ALL TOOLS REGISTRY
# ============================================================================

ALL_BMAD_REMAINING_PHASES_TOOLS = {
    # Phase 4: Testing & Validation Framework
    **{tool.name: tool for tool in UAT_TOOLS},
    **{tool.name: tool for tool in MONITORING_TOOLS},
    
    # Phase 5: Advanced Features & Expansion Packs
    **{tool.name: tool for tool in HIL_TOOLS},
    **{tool.name: tool for tool in WORKFLOW_TOOLS},
    **{tool.name: tool for tool in ANALYTICS_TOOLS},
    **{tool.name: tool for tool in DEPLOYMENT_TOOLS},
    
    # Phase 6: Final Cleanup & Validation
    **{tool.name: tool for tool in CLEANUP_TOOLS},
    **{tool.name: tool for tool in VALIDATION_TOOLS}
}

def get_bmad_remaining_phases_tools() -> Dict[str, MCPTool]:
    """Get all BMAD remaining phases MCP tools"""
    return ALL_BMAD_REMAINING_PHASES_TOOLS

def get_tools_by_phase(phase: str) -> Dict[str, MCPTool]:
    """Get tools for a specific phase"""
    phase_tools = {
        "4": {**{tool.name: tool for tool in UAT_TOOLS}, **{tool.name: tool for tool in MONITORING_TOOLS}},
        "5": {**{tool.name: tool for tool in HIL_TOOLS}, **{tool.name: tool for tool in WORKFLOW_TOOLS}, 
              **{tool.name: tool for tool in ANALYTICS_TOOLS}, **{tool.name: tool for tool in DEPLOYMENT_TOOLS}},
        "6": {**{tool.name: tool for tool in CLEANUP_TOOLS}, **{tool.name: tool for tool in VALIDATION_TOOLS}}
    }
    return phase_tools.get(phase, {})

def get_tools_by_priority(priority: str) -> Dict[str, MCPTool]:
    """Get tools by priority level"""
    priority_tools = {
        "HIGH": {**{tool.name: tool for tool in UAT_TOOLS}, **{tool.name: tool for tool in MONITORING_TOOLS}, **{tool.name: tool for tool in DEPLOYMENT_TOOLS}},
        "MEDIUM": {**{tool.name: tool for tool in HIL_TOOLS}, **{tool.name: tool for tool in WORKFLOW_TOOLS}, **{tool.name: tool for tool in ANALYTICS_TOOLS}},
        "LOW": {**{tool.name: tool for tool in CLEANUP_TOOLS}, **{tool.name: tool for tool in VALIDATION_TOOLS}}
    }
    return priority_tools.get(priority, {})

# ============================================================================
# TOOL CATEGORIES
# ============================================================================

TOOL_CATEGORIES = {
    "User Acceptance Testing": UAT_TOOLS,
    "Production Monitoring": MONITORING_TOOLS,
    "HIL Integration": HIL_TOOLS,
    "Brownfield/Greenfield Workflows": WORKFLOW_TOOLS,
    "Advanced Analytics": ANALYTICS_TOOLS,
    "Production Deployment": DEPLOYMENT_TOOLS,
    "Final Cleanup": CLEANUP_TOOLS,
    "Final Validation": VALIDATION_TOOLS
}

def get_tools_by_category(category: str) -> List[MCPTool]:
    """Get tools by category"""
    return TOOL_CATEGORIES.get(category, [])

def get_all_categories() -> List[str]:
    """Get all tool categories"""
    return list(TOOL_CATEGORIES.keys())

# ============================================================================
# TOOL STATISTICS
# ============================================================================

def get_tool_statistics() -> Dict[str, Any]:
    """Get statistics about BMAD remaining phases tools"""
    total_tools = len(ALL_BMAD_REMAINING_PHASES_TOOLS)
    
    phase_counts = {
        "Phase 4": len(UAT_TOOLS) + len(MONITORING_TOOLS),
        "Phase 5": len(HIL_TOOLS) + len(WORKFLOW_TOOLS) + len(ANALYTICS_TOOLS) + len(DEPLOYMENT_TOOLS),
        "Phase 6": len(CLEANUP_TOOLS) + len(VALIDATION_TOOLS)
    }
    
    priority_counts = {
        "HIGH": len(UAT_TOOLS) + len(MONITORING_TOOLS) + len(DEPLOYMENT_TOOLS),
        "MEDIUM": len(HIL_TOOLS) + len(WORKFLOW_TOOLS) + len(ANALYTICS_TOOLS),
        "LOW": len(CLEANUP_TOOLS) + len(VALIDATION_TOOLS)
    }
    
    category_counts = {category: len(tools) for category, tools in TOOL_CATEGORIES.items()}
    
    return {
        "total_tools": total_tools,
        "phase_counts": phase_counts,
        "priority_counts": priority_counts,
        "category_counts": category_counts,
        "categories": get_all_categories()
    }
