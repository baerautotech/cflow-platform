# BMAD API Reference

## WebMCP Installer Tools

### bmad_webmcp_install_config
Install WebMCP configuration.

**Parameters**:
- server_url: WebMCP server URL
- api_key: API key for authentication
- timeout_seconds: Request timeout in seconds
- retry_attempts: Number of retry attempts
- enable_health_check: Enable health checking
- enable_feature_flags: Enable feature flags
- enable_performance_monitoring: Enable performance monitoring
- enable_security_testing: Enable security testing
- bmad_integration_enabled: Enable BMAD integration
- bmad_api_url: BMAD API service URL
- bmad_auth_token: BMAD authentication token
- circuit_breaker_enabled: Enable circuit breaker
- rate_limiting_enabled: Enable rate limiting
- logging_level: Logging level
- overwrite: Whether to overwrite existing configuration

### bmad_webmcp_validate_installation
Validate WebMCP installation.

### bmad_webmcp_test_integration
Test WebMCP integration.

### bmad_webmcp_uninstall_config
Uninstall WebMCP configuration.

### bmad_webmcp_get_config
Get current WebMCP configuration.

### bmad_webmcp_update_config
Update WebMCP configuration.

**Parameters**:
- config_updates: JSON string with configuration updates

### bmad_webmcp_backup_config
Backup WebMCP configuration.

### bmad_webmcp_restore_config
Restore WebMCP configuration from backup.

**Parameters**:
- backup_file_path: Path to backup file

## Installation Flow Testing Tools

### bmad_installation_flow_test
Test the complete installation flow.

**Parameters**:
- test_environment: Whether to test in a temporary environment
- skip_optional_steps: Whether to skip optional installation steps

### bmad_installation_step_test
Test a specific installation step.

**Parameters**:
- step_name: Name of the installation step to test
- custom_command: Custom command to execute (JSON string)

### bmad_installation_rollback_test
Test the rollback flow after installation.

### bmad_installation_validate_environment
Validate the installation environment.

### bmad_installation_validate_components
Validate all installation components.

### bmad_installation_get_flow_steps
Get the list of installation flow steps.

### bmad_installation_test_prerequisites
Test installation prerequisites.

### bmad_installation_generate_report
Generate installation flow test report.

## Uninstall and Rollback Tools

### bmad_uninstall_complete
Uninstall BMAD integration completely.

**Parameters**:
- create_backup: Whether to create backup before uninstall
- remove_vendor_bmad: Whether to remove vendor BMAD directory
- force: Whether to force uninstall even if some steps fail

### bmad_uninstall_step
Execute a specific uninstall step.

**Parameters**:
- step_name: Name of the uninstall step to execute
- force: Whether to force execution even if step fails

### bmad_rollback_create_point
Create a rollback point for future restoration.

**Parameters**:
- name: Name of the rollback point
- description: Description of the rollback point

### bmad_rollback_to_point
Rollback to a specific rollback point.

**Parameters**:
- rollback_point_name: Name of the rollback point to restore
- force: Whether to force rollback even if some steps fail

### bmad_rollback_list_points
List all available rollback points.

### bmad_rollback_delete_point
Delete a specific rollback point.

**Parameters**:
- rollback_point_name: Name of the rollback point to delete

### bmad_uninstall_validate
Validate uninstall prerequisites and current state.

### bmad_uninstall_simulate
Simulate uninstall process without actually performing it.

### bmad_rollback_get_point_info
Get detailed information about a specific rollback point.

**Parameters**:
- rollback_point_name: Name of the rollback point
