#!/usr/bin/env python3
"""
BMAD CLI for Local Development and Testing

This CLI provides local development tools for testing BMAD functionality
without requiring the full cerebral cluster deployment.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path
import click
import httpx
from datetime import datetime

# Add the parent directory to the path to import cflow_platform modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from cflow_platform.core.tool_registry import ToolRegistry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BMADCLIClient:
    """Client for interacting with BMAD API services."""
    
    def __init__(self, base_url: str = "http://localhost:8001", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {}
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check BMAD API service health."""
        try:
            response = await self.client.get(f"{self.base_url}/bmad/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def list_tools(self) -> Dict[str, Any]:
        """List all available BMAD tools."""
        try:
            response = await self.client.get(f"{self.base_url}/bmad/tools")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return {"tools": [], "error": str(e)}
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a BMAD tool."""
        try:
            response = await self.client.post(
                f"{self.base_url}/bmad/tools/{tool_name}/execute",
                json={"arguments": arguments}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def detect_project_type(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Detect project type (greenfield/brownfield)."""
        try:
            response = await self.client.post(
                f"{self.base_url}/bmad/project-type/detect",
                json={"project_info": project_info}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Project type detection failed: {e}")
            return {"error": str(e)}
    
    async def document_project(self, project_path: str, focus_areas: List[str] = None, output_format: str = "single_document") -> Dict[str, Any]:
        """Document an existing project."""
        try:
            response = await self.client.post(
                f"{self.base_url}/bmad/brownfield/document-project",
                json={
                    "project_path": project_path,
                    "focus_areas": focus_areas or [],
                    "output_format": output_format
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Project documentation failed: {e}")
            return {"error": str(e)}
    
    async def create_brownfield_prd(self, project_name: str, enhancement_scope: Dict[str, Any] = None, existing_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create PRD for brownfield project."""
        try:
            response = await self.client.post(
                f"{self.base_url}/bmad/brownfield/prd-create",
                json={
                    "project_name": project_name,
                    "enhancement_scope": enhancement_scope or {},
                    "existing_analysis": existing_analysis or {}
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Brownfield PRD creation failed: {e}")
            return {"error": str(e)}
    
    async def list_expansion_packs(self) -> Dict[str, Any]:
        """List available expansion packs."""
        try:
            response = await self.client.get(f"{self.base_url}/bmad/expansion-packs/list")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to list expansion packs: {e}")
            return {"expansion_packs": [], "error": str(e)}
    
    async def install_expansion_pack(self, pack_id: str, version: str = "latest") -> Dict[str, Any]:
        """Install an expansion pack."""
        try:
            response = await self.client.post(
                f"{self.base_url}/bmad/expansion-packs/install",
                json={"pack_id": pack_id, "version": version}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Expansion pack installation failed: {e}")
            return {"error": str(e)}
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        try:
            response = await self.client.get(f"{self.base_url}/bmad/stats")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


@click.group()
@click.option('--base-url', default='http://localhost:8001', help='BMAD API base URL')
@click.option('--api-key', help='API key for authentication')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, base_url, api_key, verbose):
    """BMAD CLI for local development and testing."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    ctx.ensure_object(dict)
    ctx.obj['client'] = BMADCLIClient(base_url, api_key)


@cli.command()
@click.pass_context
async def health(ctx):
    """Check BMAD API service health."""
    client = ctx.obj['client']
    result = await client.health_check()
    
    if result.get('status') == 'healthy':
        click.echo("✅ BMAD API service is healthy")
        click.echo(f"Tools count: {result.get('tools_count', 'unknown')}")
        click.echo(f"Vendor BMAD status: {result.get('vendor_bmad_status', {}).get('healthy', 'unknown')}")
    else:
        click.echo("❌ BMAD API service is unhealthy")
        if 'error' in result:
            click.echo(f"Error: {result['error']}")
    
    await client.close()


@cli.command()
@click.pass_context
async def list_tools(ctx):
    """List all available BMAD tools."""
    client = ctx.obj['client']
    result = await client.list_tools()
    
    if 'error' in result:
        click.echo(f"❌ Failed to list tools: {result['error']}")
    else:
        tools = result.get('tools', [])
        click.echo(f"📋 Available BMAD Tools ({len(tools)} total):")
        for tool in tools:
            click.echo(f"  • {tool}")
    
    await client.close()


@cli.command()
@click.argument('tool_name')
@click.option('--args', help='JSON string of tool arguments')
@click.pass_context
async def execute(ctx, tool_name, args):
    """Execute a BMAD tool."""
    client = ctx.obj['client']
    
    # Parse arguments
    arguments = {}
    if args:
        try:
            arguments = json.loads(args)
        except json.JSONDecodeError as e:
            click.echo(f"❌ Invalid JSON in arguments: {e}")
            return
    
    click.echo(f"🚀 Executing tool: {tool_name}")
    result = await client.execute_tool(tool_name, arguments)
    
    if result.get('success'):
        click.echo("✅ Tool execution successful")
        click.echo(f"Execution time: {result.get('execution_time', 'unknown')}s")
        if 'result' in result:
            click.echo(f"Result: {json.dumps(result['result'], indent=2)}")
    else:
        click.echo("❌ Tool execution failed")
        if 'error' in result:
            click.echo(f"Error: {result['error']}")
    
    await client.close()


@cli.command()
@click.option('--project-path', help='Path to project directory')
@click.option('--has-existing-code', is_flag=True, help='Project has existing code')
@click.option('--has-documentation', is_flag=True, help='Project has documentation')
@click.option('--has-tests', is_flag=True, help='Project has tests')
@click.option('--project-size', type=click.Choice(['small', 'medium', 'large']), help='Project size')
@click.pass_context
async def detect_project_type(ctx, project_path, has_existing_code, has_documentation, has_tests, project_size):
    """Detect if a project is greenfield or brownfield."""
    client = ctx.obj['client']
    
    project_info = {
        "has_existing_code": has_existing_code,
        "has_documentation": has_documentation,
        "has_tests": has_tests,
        "project_size": project_size or "unknown"
    }
    
    if project_path:
        project_info["project_path"] = project_path
    
    click.echo("🔍 Detecting project type...")
    result = await client.detect_project_type(project_info)
    
    if 'error' in result:
        click.echo(f"❌ Detection failed: {result['error']}")
    else:
        project_type = result.get('project_type', 'unknown')
        confidence = result.get('confidence', 0)
        
        click.echo(f"📊 Project Type: {project_type.upper()}")
        click.echo(f"🎯 Confidence: {confidence:.1%}")
        click.echo(f"🔄 Recommended Workflow: {result.get('recommended_workflow', 'unknown')}")
        
        analysis = result.get('analysis', {})
        click.echo("📋 Analysis:")
        for key, value in analysis.items():
            click.echo(f"  • {key}: {value}")
    
    await client.close()


@cli.command()
@click.argument('project_path')
@click.option('--focus-areas', help='Comma-separated list of focus areas')
@click.option('--output-format', default='single_document', help='Output format')
@click.pass_context
async def document_project(ctx, project_path, focus_areas, output_format):
    """Document an existing project for brownfield development."""
    client = ctx.obj['client']
    
    focus_areas_list = []
    if focus_areas:
        focus_areas_list = [area.strip() for area in focus_areas.split(',')]
    
    click.echo(f"📝 Documenting project: {project_path}")
    result = await client.document_project(project_path, focus_areas_list, output_format)
    
    if 'error' in result:
        click.echo(f"❌ Documentation failed: {result['error']}")
    else:
        click.echo("✅ Project documentation completed")
        if 'documentation' in result:
            click.echo(f"Documentation: {json.dumps(result['documentation'], indent=2)}")
    
    await client.close()


@cli.command()
@click.argument('project_name')
@click.option('--enhancement-scope', help='JSON string of enhancement scope')
@click.option('--existing-analysis', help='JSON string of existing analysis')
@click.pass_context
async def create_brownfield_prd(ctx, project_name, enhancement_scope, existing_analysis):
    """Create PRD for brownfield project enhancement."""
    client = ctx.obj['client']
    
    # Parse enhancement scope
    scope = {}
    if enhancement_scope:
        try:
            scope = json.loads(enhancement_scope)
        except json.JSONDecodeError as e:
            click.echo(f"❌ Invalid JSON in enhancement scope: {e}")
            return
    
    # Parse existing analysis
    analysis = {}
    if existing_analysis:
        try:
            analysis = json.loads(existing_analysis)
        except json.JSONDecodeError as e:
            click.echo(f"❌ Invalid JSON in existing analysis: {e}")
            return
    
    click.echo(f"📋 Creating brownfield PRD for: {project_name}")
    result = await client.create_brownfield_prd(project_name, scope, analysis)
    
    if 'error' in result:
        click.echo(f"❌ PRD creation failed: {result['error']}")
    else:
        click.echo("✅ Brownfield PRD created successfully")
        if 'prd' in result:
            click.echo(f"PRD: {json.dumps(result['prd'], indent=2)}")
    
    await client.close()


@cli.command()
@click.pass_context
async def list_expansion_packs(ctx):
    """List available BMAD expansion packs."""
    client = ctx.obj['client']
    result = await client.list_expansion_packs()
    
    if 'error' in result:
        click.echo(f"❌ Failed to list expansion packs: {result['error']}")
    else:
        packs = result.get('expansion_packs', [])
        click.echo(f"📦 Available Expansion Packs ({len(packs)} total):")
        for pack in packs:
            click.echo(f"  • {pack.get('name', pack.get('pack_id', 'Unknown'))}")
            click.echo(f"    ID: {pack.get('pack_id', 'Unknown')}")
            click.echo(f"    Version: {pack.get('version', 'Unknown')}")
            click.echo(f"    Category: {pack.get('category', 'Unknown')}")
            click.echo(f"    Agents: {pack.get('agents_count', 0)}")
            click.echo(f"    Workflows: {pack.get('workflows_count', 0)}")
            click.echo()
    
    await client.close()


@cli.command()
@click.argument('pack_id')
@click.option('--version', default='latest', help='Version to install')
@click.pass_context
async def install_pack(ctx, pack_id, version):
    """Install a BMAD expansion pack."""
    client = ctx.obj['client']
    
    click.echo(f"📦 Installing expansion pack: {pack_id} (version: {version})")
    result = await client.install_expansion_pack(pack_id, version)
    
    if 'error' in result:
        click.echo(f"❌ Installation failed: {result['error']}")
    else:
        click.echo("✅ Expansion pack installed successfully")
        click.echo(f"Status: {result.get('status', 'unknown')}")
        click.echo(f"Installation path: {result.get('installation_path', 'unknown')}")
    
    await client.close()


@cli.command()
@click.pass_context
async def stats(ctx):
    """Get BMAD API service statistics."""
    client = ctx.obj['client']
    result = await client.get_stats()
    
    if 'error' in result:
        click.echo(f"❌ Failed to get stats: {result['error']}")
    else:
        click.echo("📊 BMAD API Service Statistics:")
        click.echo(f"Tools count: {result.get('tools_count', 'unknown')}")
        
        perf_stats = result.get('performance_stats', {})
        if perf_stats:
            click.echo("Performance Stats:")
            for key, value in perf_stats.items():
                click.echo(f"  • {key}: {value}")
    
    await client.close()


@cli.command()
@click.pass_context
def local_tool_registry(ctx):
    """Show local tool registry information."""
    click.echo("🔧 Local BMAD Tool Registry:")
    
    tools = ToolRegistry.get_tools_for_mcp()
    bmad_tools = [tool for tool in tools if tool['name'].startswith('bmad_')]
    
    click.echo(f"Total tools: {len(tools)}")
    click.echo(f"BMAD tools: {len(bmad_tools)}")
    
    registry_info = ToolRegistry.get_tool_registry_info()
    click.echo(f"Registry version: {registry_info.get('registry_version', 'unknown')}")
    click.echo(f"Total tools: {registry_info.get('total_tools', 'unknown')}")
    
    # Group BMAD tools by category
    categories = {}
    for tool in bmad_tools:
        category = tool['name'].split('_')[1] if '_' in tool['name'] else 'general'
        if category not in categories:
            categories[category] = []
        categories[category].append(tool['name'])
    
    click.echo("\n📋 BMAD Tools by Category:")
    for category, tools in categories.items():
        click.echo(f"  {category}: {len(tools)} tools")


# Make the CLI functions async-compatible
def run_async_command(coro):
    """Helper to run async commands in click."""
    return asyncio.run(coro)


# Update async commands to use the helper
def make_sync(async_func):
    def sync_func(*args, **kwargs):
        return run_async_command(async_func(*args, **kwargs))
    return sync_func

# Apply sync wrapper to async commands
health.callback = make_sync(health.callback)
list_tools.callback = make_sync(list_tools.callback)
execute.callback = make_sync(execute.callback)
detect_project_type.callback = make_sync(detect_project_type.callback)
document_project.callback = make_sync(document_project.callback)
create_brownfield_prd.callback = make_sync(create_brownfield_prd.callback)
list_expansion_packs.callback = make_sync(list_expansion_packs.callback)
install_pack.callback = make_sync(install_pack.callback)
stats.callback = make_sync(stats.callback)


if __name__ == '__main__':
    cli()
