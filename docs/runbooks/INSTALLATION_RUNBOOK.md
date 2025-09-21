# Installation Runbook

## Prerequisites
- Python 3.8+
- Git repository
- Access to Cerebral cloud cluster
- Required environment variables

## Installation Steps

### Step 1: Environment Validation
```bash
python -m cflow_platform.verify_env --mode migrations --mode ragkg --mode llm --scope both
```

**Expected Output**: Environment validation success

### Step 2: Install Hooks
```bash
python -m cflow_platform.install_hooks
```

**Expected Output**: Git hooks installed successfully

### Step 3: Setup Cursor
```bash
python -m cflow_platform.cli.setup_cursor
```

**Expected Output**: Cursor workspace configured

### Step 4: Memory Connectivity
```bash
python -m cflow_platform.cli.memory_check
```

**Expected Output**: Memory connectivity established

### Step 5: BMAD Integration Setup
```bash
python -m cflow_platform.cli.one_touch_installer --setup-bmad
```

**Expected Output**: BMAD integration components verified

### Step 6: WebMCP Configuration
```bash
python -m cflow_platform.cli.one_touch_installer --setup-webmcp \
  --webmcp-server-url http://localhost:8000 \
  --bmad-api-url http://localhost:8001
```

**Expected Output**: WebMCP configuration installed

### Step 7: Verification
```bash
python -m cflow_platform.cli.test_webmcp_installer
```

**Expected Output**: All tests passed

## Troubleshooting
- Check prerequisites
- Verify environment variables
- Check network connectivity
- Review logs for errors
