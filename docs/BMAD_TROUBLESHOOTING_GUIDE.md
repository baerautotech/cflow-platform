# BMAD Troubleshooting Guide

## Common Issues

### WebMCP Connection Issues
**Problem**: Cannot connect to WebMCP server
**Solution**: 
1. Check server URL configuration
2. Verify network connectivity
3. Check authentication credentials

### BMAD API Service Issues
**Problem**: BMAD API service not responding
**Solution**:
1. Check service status in Kubernetes
2. Verify service endpoints
3. Check authentication tokens

### Tool Execution Issues
**Problem**: MCP tools not executing
**Solution**:
1. Check tool registry configuration
2. Verify direct client routing
3. Check handler implementations

## Diagnostic Commands

### Check Installation
```bash
python -m cflow_platform.cli.test_webmcp_installer
```

### Validate Configuration
```bash
python -c "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_webmcp_validate_installation')))"
```

### Test Integration
```bash
python -c "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_webmcp_test_integration')))"
```

## Logs and Debugging
- Check application logs
- Enable debug logging
- Use diagnostic tools
