# BMAD Installation Guide

## Prerequisites
- Python 3.8+
- Git repository
- Access to Cerebral cloud cluster
- Required environment variables

## Installation Methods

### One-Touch Installer
Use the one-touch installer for complete setup:

```bash
python -m cflow_platform.cli.one_touch_installer --setup-webmcp --setup-bmad
```

### Manual Installation
1. Install dependencies
2. Configure environment
3. Setup WebMCP configuration
4. Verify installation

## Configuration
Configure WebMCP and BMAD integration:

```bash
python -m cflow_platform.cli.one_touch_installer --setup-webmcp \
  --webmcp-server-url http://localhost:8000 \
  --bmad-api-url http://localhost:8001
```

## Verification
Verify installation:

```bash
python -m cflow_platform.cli.test_webmcp_installer
```

## Troubleshooting
See BMAD_TROUBLESHOOTING_GUIDE.md for common installation issues.
