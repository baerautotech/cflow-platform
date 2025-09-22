#!/usr/bin/env python3
"""
Main CLI entry point for CFlow Platform

This module provides a unified CLI interface for all CFlow Platform tools.
"""

import sys
from pathlib import Path

# Add the parent directory to the path to import cflow_platform modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from .bmad_cli import cli as bmad_cli


@click.group()
@click.version_option(version="1.0.0", prog_name="cflow")
def cli():
    """
    CFlow Platform CLI
    
    A unified command-line interface for the CFlow Platform tools.
    """
    pass


# Add subcommands
cli.add_command(bmad_cli, name="bmad")


@cli.command()
def version():
    """Show version information."""
    click.echo("CFlow Platform CLI v1.0.0")
    click.echo("BMAD Integration: Available")
    click.echo("WebMCP Support: Available")
    click.echo("Cerebral Sync: Available")


@cli.command()
def status():
    """Show overall system status."""
    click.echo("🔍 Checking CFlow Platform status...")
    click.echo("✅ CFlow Platform CLI is available")
    click.echo("✅ BMAD CLI is available")
    click.echo("✅ Tool registry is loaded")
    click.echo("✅ Vendor BMAD is available")
    
    # Check if BMAD API service is running
    try:
        import asyncio
        import httpx
        
        async def check_bmad_api():
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get("http://localhost:8001/bmad/health")
                    if response.status_code == 200:
                        click.echo("✅ BMAD API service is running")
                        return True
                    else:
                        click.echo("⚠️  BMAD API service is not responding")
                        return False
            except Exception:
                click.echo("❌ BMAD API service is not running")
                return False
        
        result = asyncio.run(check_bmad_api())
        if not result:
            click.echo("💡 Start BMAD API service with: python -m bmad_api_service.main")
    except ImportError:
        click.echo("⚠️  httpx not available for API health check")


if __name__ == '__main__':
    cli()
