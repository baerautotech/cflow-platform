# Uninstall Runbook

## Prerequisites
- BMAD integration installed
- Access to uninstall tools
- Backup of current state (recommended)

## Uninstall Steps

### Step 1: Create Backup
```bash
python -c "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_webmcp_backup_config')))"
```

**Expected Output**: Backup created successfully

### Step 2: Validate Uninstall
```bash
python -c "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_uninstall_validate')))"
```

**Expected Output**: Uninstall prerequisites validated

### Step 3: Simulate Uninstall
```bash
python -c "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_uninstall_simulate')))"
```

**Expected Output**: Uninstall simulation completed

### Step 4: Execute Uninstall
```bash
python -c "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_uninstall_complete', create_backup=True)))"
```

**Expected Output**: BMAD integration uninstalled successfully

### Step 5: Verify Cleanup
```bash
python -c "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_installation_validate_components')))"
```

**Expected Output**: Cleanup verification completed

## Troubleshooting
- Check backup creation
- Verify uninstall steps
- Review error messages
- Use force option if needed
