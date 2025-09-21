"""
Documentation Manager

This module provides comprehensive documentation and runbook management
capabilities for BMAD integration, including documentation generation,
runbook creation, and maintenance.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class DocumentationSection:
    """Represents a documentation section."""
    title: str
    content: str
    subsections: List['DocumentationSection'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RunbookStep:
    """Represents a runbook step."""
    step_number: int
    title: str
    description: str
    commands: List[str] = field(default_factory=list)
    expected_output: str = ""
    troubleshooting: str = ""
    prerequisites: List[str] = field(default_factory=list)


@dataclass
class DocumentationResult:
    """Result of documentation operation."""
    success: bool
    message: str
    files_created: List[str] = field(default_factory=list)
    files_updated: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class DocumentationManager:
    """
    Documentation Manager for BMAD Integration.
    
    This class provides comprehensive documentation management capabilities,
    including:
    - Documentation generation
    - Runbook creation
    - Maintenance and updates
    - Version control integration
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the documentation manager."""
        self.project_root = project_root or Path.cwd()
        self.docs_dir = self.project_root / "docs"
        self.runbooks_dir = self.docs_dir / "runbooks"
        
        # Ensure directories exist
        self.docs_dir.mkdir(exist_ok=True)
        self.runbooks_dir.mkdir(exist_ok=True)
    
    def generate_bmad_documentation(self) -> DocumentationResult:
        """
        Generate comprehensive BMAD documentation.
        
        Returns:
            DocumentationResult with generation details
        """
        logger.info("Generating BMAD documentation...")
        
        try:
            files_created = []
            files_updated = []
            errors = []
            warnings = []
            
            # Generate main documentation files
            doc_files = [
                ("BMAD_INTEGRATION_GUIDE.md", self._generate_integration_guide()),
                ("BMAD_INSTALLATION_GUIDE.md", self._generate_installation_guide()),
                ("BMAD_TROUBLESHOOTING_GUIDE.md", self._generate_troubleshooting_guide()),
                ("BMAD_API_REFERENCE.md", self._generate_api_reference()),
                ("BMAD_CONFIGURATION_GUIDE.md", self._generate_configuration_guide())
            ]
            
            for filename, content in doc_files:
                file_path = self.docs_dir / filename
                with open(file_path, 'w') as f:
                    f.write(content)
                files_created.append(str(file_path))
            
            # Generate runbooks
            runbook_files = [
                ("INSTALLATION_RUNBOOK.md", self._generate_installation_runbook()),
                ("UNINSTALL_RUNBOOK.md", self._generate_uninstall_runbook()),
                ("TROUBLESHOOTING_RUNBOOK.md", self._generate_troubleshooting_runbook()),
                ("MAINTENANCE_RUNBOOK.md", self._generate_maintenance_runbook())
            ]
            
            for filename, content in runbook_files:
                file_path = self.runbooks_dir / filename
                with open(file_path, 'w') as f:
                    f.write(content)
                files_created.append(str(file_path))
            
            return DocumentationResult(
                success=True,
                message=f"BMAD documentation generated successfully. Created {len(files_created)} files.",
                files_created=files_created,
                files_updated=files_updated,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Failed to generate BMAD documentation: {e}")
            return DocumentationResult(
                success=False,
                message=f"Failed to generate BMAD documentation: {e}",
                errors=[str(e)]
            )
    
    def update_documentation(self, section: str, content: str) -> DocumentationResult:
        """
        Update specific documentation section.
        
        Args:
            section: Documentation section to update
            content: New content for the section
            
        Returns:
            DocumentationResult with update details
        """
        logger.info(f"Updating documentation section: {section}")
        
        try:
            # Map section to file
            section_files = {
                "integration": "BMAD_INTEGRATION_GUIDE.md",
                "installation": "BMAD_INSTALLATION_GUIDE.md",
                "troubleshooting": "BMAD_TROUBLESHOOTING_GUIDE.md",
                "api": "BMAD_API_REFERENCE.md",
                "configuration": "BMAD_CONFIGURATION_GUIDE.md"
            }
            
            if section not in section_files:
                return DocumentationResult(
                    success=False,
                    message=f"Unknown documentation section: {section}",
                    errors=[f"Section '{section}' not found"]
                )
            
            filename = section_files[section]
            file_path = self.docs_dir / filename
            
            # Update the file
            with open(file_path, 'w') as f:
                f.write(content)
            
            return DocumentationResult(
                success=True,
                message=f"Documentation section '{section}' updated successfully",
                files_updated=[str(file_path)]
            )
            
        except Exception as e:
            logger.error(f"Failed to update documentation section {section}: {e}")
            return DocumentationResult(
                success=False,
                message=f"Failed to update documentation section {section}: {e}",
                errors=[str(e)]
            )
    
    def generate_runbook(self, runbook_type: str, steps: List[RunbookStep]) -> DocumentationResult:
        """
        Generate a specific runbook.
        
        Args:
            runbook_type: Type of runbook to generate
            steps: List of runbook steps
            
        Returns:
            DocumentationResult with generation details
        """
        logger.info(f"Generating runbook: {runbook_type}")
        
        try:
            content = self._format_runbook(runbook_type, steps)
            filename = f"{runbook_type.upper()}_RUNBOOK.md"
            file_path = self.runbooks_dir / filename
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            return DocumentationResult(
                success=True,
                message=f"Runbook '{runbook_type}' generated successfully",
                files_created=[str(file_path)]
            )
            
        except Exception as e:
            logger.error(f"Failed to generate runbook {runbook_type}: {e}")
            return DocumentationResult(
                success=False,
                message=f"Failed to generate runbook {runbook_type}: {e}",
                errors=[str(e)]
            )
    
    def validate_documentation(self) -> DocumentationResult:
        """
        Validate existing documentation.
        
        Returns:
            DocumentationResult with validation details
        """
        logger.info("Validating documentation...")
        
        try:
            errors = []
            warnings = []
            
            # Check required documentation files
            required_files = [
                "BMAD_INTEGRATION_GUIDE.md",
                "BMAD_INSTALLATION_GUIDE.md",
                "BMAD_TROUBLESHOOTING_GUIDE.md",
                "BMAD_API_REFERENCE.md",
                "BMAD_CONFIGURATION_GUIDE.md"
            ]
            
            for filename in required_files:
                file_path = self.docs_dir / filename
                if not file_path.exists():
                    errors.append(f"Missing documentation file: {filename}")
                elif file_path.stat().st_size == 0:
                    warnings.append(f"Empty documentation file: {filename}")
            
            # Check required runbooks
            required_runbooks = [
                "INSTALLATION_RUNBOOK.md",
                "UNINSTALL_RUNBOOK.md",
                "TROUBLESHOOTING_RUNBOOK.md",
                "MAINTENANCE_RUNBOOK.md"
            ]
            
            for filename in required_runbooks:
                file_path = self.runbooks_dir / filename
                if not file_path.exists():
                    errors.append(f"Missing runbook: {filename}")
                elif file_path.stat().st_size == 0:
                    warnings.append(f"Empty runbook: {filename}")
            
            success = len(errors) == 0
            
            return DocumentationResult(
                success=success,
                message=f"Documentation validation completed. {len(errors)} errors, {len(warnings)} warnings.",
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Failed to validate documentation: {e}")
            return DocumentationResult(
                success=False,
                message=f"Failed to validate documentation: {e}",
                errors=[str(e)]
            )
    
    def _generate_integration_guide(self) -> str:
        """Generate BMAD integration guide."""
        return """# BMAD Integration Guide

## Overview
This guide provides comprehensive information about integrating BMAD (Breakthrough Method of Agile AI-driven Development) with the CFlow platform.

## Architecture
The BMAD integration consists of several key components:
- WebMCP Server
- BMAD API Service
- Vendor BMAD Workflows
- MCP Tool Registry
- Direct Client Routing

## Components

### WebMCP Server
The WebMCP server provides the central MCP instance running in the Cerebral cloud cluster.

### BMAD API Service
A dedicated Kubernetes deployment in the Cerebral cluster exposing BMAD functionality via HTTP.

### Vendor BMAD
The core BMAD-METHOD codebase vendored into vendor/bmad/.

## Integration Flow
1. WebMCP receives tool calls
2. Routes to BMAD API Service
3. BMAD API Service executes vendor BMAD workflows
4. Results returned through the chain

## Configuration
See BMAD_CONFIGURATION_GUIDE.md for detailed configuration information.

## Troubleshooting
See BMAD_TROUBLESHOOTING_GUIDE.md for common issues and solutions.
"""
    
    def _generate_installation_guide(self) -> str:
        """Generate BMAD installation guide."""
        return """# BMAD Installation Guide

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
python -m cflow_platform.cli.one_touch_installer --setup-webmcp \\
  --webmcp-server-url http://localhost:8000 \\
  --bmad-api-url http://localhost:8001
```

## Verification
Verify installation:

```bash
python -m cflow_platform.cli.test_webmcp_installer
```

## Troubleshooting
See BMAD_TROUBLESHOOTING_GUIDE.md for common installation issues.
"""
    
    def _generate_troubleshooting_guide(self) -> str:
        """Generate BMAD troubleshooting guide."""
        return """# BMAD Troubleshooting Guide

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
"""
    
    def _generate_api_reference(self) -> str:
        """Generate BMAD API reference."""
        return """# BMAD API Reference

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
"""
    
    def _generate_configuration_guide(self) -> str:
        """Generate BMAD configuration guide."""
        return """# BMAD Configuration Guide

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
python -c "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_webmcp_update_config', config_updates='{\"webmcp\": {\"timeout_seconds\": 60}}')))"
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
"""
    
    def _generate_installation_runbook(self) -> str:
        """Generate installation runbook."""
        return """# Installation Runbook

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
python -m cflow_platform.cli.one_touch_installer --setup-webmcp \\
  --webmcp-server-url http://localhost:8000 \\
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
"""
    
    def _generate_uninstall_runbook(self) -> str:
        """Generate uninstall runbook."""
        return """# Uninstall Runbook

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
"""
    
    def _generate_troubleshooting_runbook(self) -> str:
        """Generate troubleshooting runbook."""
        return """# Troubleshooting Runbook

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
"""
    
    def _generate_maintenance_runbook(self) -> str:
        """Generate maintenance runbook."""
        return """# Maintenance Runbook

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
"""
    
    def _format_runbook(self, runbook_type: str, steps: List[RunbookStep]) -> str:
        """Format runbook content."""
        content = f"# {runbook_type.title()} Runbook\n\n"
        
        for step in steps:
            content += f"## Step {step.step_number}: {step.title}\n\n"
            content += f"{step.description}\n\n"
            
            if step.prerequisites:
                content += "**Prerequisites**:\n"
                for prereq in step.prerequisites:
                    content += f"- {prereq}\n"
                content += "\n"
            
            if step.commands:
                content += "**Commands**:\n"
                for command in step.commands:
                    content += f"```bash\n{command}\n```\n"
                content += "\n"
            
            if step.expected_output:
                content += f"**Expected Output**: {step.expected_output}\n\n"
            
            if step.troubleshooting:
                content += f"**Troubleshooting**: {step.troubleshooting}\n\n"
        
        return content
