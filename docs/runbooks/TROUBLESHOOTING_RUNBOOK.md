# Troubleshooting Runbook

## Common Issues and Solutions

### Issue 1: WebMCP Connection Failed
**Symptoms**: Cannot connect to WebMCP server
**Diagnosis**:
```bash
python -c "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_webmcp_validate_installation')))"
```

**Solutions**:
1. Check server URL configuration
2. Verify network connectivity
3. Check authentication credentials
4. Restart WebMCP server

### Issue 2: BMAD API Service Not Responding
**Symptoms**: BMAD API service not responding
**Diagnosis**:
```bash
python -c "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_webmcp_test_integration')))"
```

**Solutions**:
1. Check service status in Kubernetes
2. Verify service endpoints
3. Check authentication tokens
4. Restart BMAD API service

### Issue 3: Tool Execution Failed
**Symptoms**: MCP tools not executing
**Diagnosis**:
```bash
python -c "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_installation_test_prerequisites')))"
```

**Solutions**:
1. Check tool registry configuration
2. Verify direct client routing
3. Check handler implementations
4. Review error logs

### Issue 4: Configuration Issues
**Symptoms**: Configuration not loading
**Diagnosis**:
```bash
python -c "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_webmcp_get_config')))"
```

**Solutions**:
1. Check configuration file syntax
2. Verify file permissions
3. Check environment variables
4. Restore from backup

## Diagnostic Commands
- Check installation: `python -m cflow_platform.cli.test_webmcp_installer`
- Validate configuration: `bmad_webmcp_validate_installation`
- Test integration: `bmad_webmcp_test_integration`
- Check prerequisites: `bmad_installation_test_prerequisites`
