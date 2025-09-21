# Maintenance Runbook

## Regular Maintenance Tasks

### Daily Tasks
- Check service health
- Monitor logs for errors
- Verify configuration integrity

### Weekly Tasks
- Update documentation
- Review performance metrics
- Check for security updates

### Monthly Tasks
- Full system backup
- Performance optimization
- Security audit

## Maintenance Commands

### Health Check
```bash
python -c "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_webmcp_validate_installation')))"
```

### Configuration Backup
```bash
python -c "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_webmcp_backup_config')))"
```

### Performance Test
```bash
python -c "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_installation_flow_test')))"
```

### Security Test
```bash
python -c "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_security_test_suite')))"
```

## Rollback Procedures
- Create rollback point: `bmad_rollback_create_point`
- List rollback points: `bmad_rollback_list_points`
- Rollback to point: `bmad_rollback_to_point`
- Delete rollback point: `bmad_rollback_delete_point`
