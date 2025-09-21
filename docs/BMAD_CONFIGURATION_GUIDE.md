# BMAD Configuration Guide

## Configuration Files

### WebMCP Configuration
Location: `.cerebraflow/webmcp_config.json`

```json
{
  "webmcp": {
    "server_url": "http://localhost:8000",
    "api_key": null,
    "timeout_seconds": 30,
    "retry_attempts": 3,
    "enable_health_check": true,
    "enable_feature_flags": true,
    "enable_performance_monitoring": true,
    "enable_security_testing": true,
    "logging_level": "INFO"
  },
  "bmad_integration": {
    "enabled": true,
    "api_url": "http://localhost:8001",
    "auth_token": null,
    "circuit_breaker_enabled": true,
    "rate_limiting_enabled": true
  },
  "metadata": {
    "config_version": "1.0.0",
    "installed_at": "2025-09-21T18:17:50.121555",
    "installer_version": "1.0.0"
  }
}
```

### Environment Configuration
Location: `.cerebraflow/.env`

```
# WebMCP Configuration
WEBMCP_SERVER_URL=http://localhost:8000
WEBMCP_TIMEOUT_SECONDS=30
WEBMCP_RETRY_ATTEMPTS=3
WEBMCP_ENABLE_HEALTH_CHECK=true
WEBMCP_ENABLE_FEATURE_FLAGS=true
WEBMCP_ENABLE_PERFORMANCE_MONITORING=true
WEBMCP_ENABLE_SECURITY_TESTING=true
WEBMCP_LOGGING_LEVEL=INFO

# BMAD Integration
BMAD_INTEGRATION_ENABLED=true
BMAD_API_URL=http://localhost:8001
BMAD_CIRCUIT_BREAKER_ENABLED=true
BMAD_RATE_LIMITING_ENABLED=true
```

## Configuration Options

### WebMCP Settings
- **server_url**: WebMCP server URL
- **api_key**: API key for authentication
- **timeout_seconds**: Request timeout in seconds
- **retry_attempts**: Number of retry attempts
- **enable_health_check**: Enable health checking
- **enable_feature_flags**: Enable feature flags
- **enable_performance_monitoring**: Enable performance monitoring
- **enable_security_testing**: Enable security testing
- **logging_level**: Logging level (DEBUG, INFO, WARNING, ERROR)

### BMAD Integration Settings
- **enabled**: Enable BMAD integration
- **api_url**: BMAD API service URL
- **auth_token**: BMAD authentication token
- **circuit_breaker_enabled**: Enable circuit breaker
- **rate_limiting_enabled**: Enable rate limiting

## Configuration Management

### Install Configuration
```bash
python -c "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_webmcp_install_config')))"
```

### Update Configuration
```bash
python -c "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_webmcp_update_config', config_updates='{"webmcp": {"timeout_seconds": 60}}')))"
```

### Backup Configuration
```bash
python -c "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_webmcp_backup_config')))"
```

### Restore Configuration
```bash
python -c "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_webmcp_restore_config', backup_file_path='/path/to/backup')))"
```

## Environment Variables
- **WEBMCP_SERVER_URL**: WebMCP server URL
- **WEBMCP_API_KEY**: WebMCP API key
- **BMAD_API_URL**: BMAD API service URL
- **BMAD_AUTH_TOKEN**: BMAD authentication token
