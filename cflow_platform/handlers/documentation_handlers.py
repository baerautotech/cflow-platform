"""
Documentation Handlers

This module provides MCP handlers for documentation management functionality,
including documentation generation, runbook creation, and maintenance.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from cflow_platform.core.documentation_manager import (
    DocumentationManager,
    DocumentationResult,
    RunbookStep
)

logger = logging.getLogger(__name__)


async def bmad_documentation_generate() -> Dict[str, Any]:
    """
    Generate comprehensive BMAD documentation.
    
    Returns:
        Dictionary with documentation generation result
    """
    try:
        logger.info("Generating BMAD documentation...")
        
        # Create documentation manager
        manager = DocumentationManager()
        
        # Generate documentation
        result = manager.generate_bmad_documentation()
        
        return {
            "success": result.success,
            "message": result.message,
            "files_created": result.files_created,
            "files_updated": result.files_updated,
            "errors": result.errors,
            "warnings": result.warnings,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate BMAD documentation: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_documentation_update(
    section: str,
    content: str
) -> Dict[str, Any]:
    """
    Update specific documentation section.
    
    Args:
        section: Documentation section to update
        content: New content for the section
        
    Returns:
        Dictionary with update result
    """
    try:
        logger.info(f"Updating documentation section: {section}")
        
        # Create documentation manager
        manager = DocumentationManager()
        
        # Update documentation
        result = manager.update_documentation(section, content)
        
        return {
            "success": result.success,
            "message": result.message,
            "files_created": result.files_created,
            "files_updated": result.files_updated,
            "errors": result.errors,
            "warnings": result.warnings,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to update documentation section {section}: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_runbook_generate(
    runbook_type: str,
    steps: str
) -> Dict[str, Any]:
    """
    Generate a specific runbook.
    
    Args:
        runbook_type: Type of runbook to generate
        steps: JSON string with runbook steps
        
    Returns:
        Dictionary with runbook generation result
    """
    try:
        logger.info(f"Generating runbook: {runbook_type}")
        
        # Parse steps
        try:
            steps_data = json.loads(steps)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON in steps: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Convert to RunbookStep objects
        runbook_steps = []
        for step_data in steps_data:
            step = RunbookStep(
                step_number=step_data.get("step_number", 0),
                title=step_data.get("title", ""),
                description=step_data.get("description", ""),
                commands=step_data.get("commands", []),
                expected_output=step_data.get("expected_output", ""),
                troubleshooting=step_data.get("troubleshooting", ""),
                prerequisites=step_data.get("prerequisites", [])
            )
            runbook_steps.append(step)
        
        # Create documentation manager
        manager = DocumentationManager()
        
        # Generate runbook
        result = manager.generate_runbook(runbook_type, runbook_steps)
        
        return {
            "success": result.success,
            "message": result.message,
            "files_created": result.files_created,
            "files_updated": result.files_updated,
            "errors": result.errors,
            "warnings": result.warnings,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate runbook {runbook_type}: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_documentation_validate() -> Dict[str, Any]:
    """
    Validate existing documentation.
    
    Returns:
        Dictionary with validation result
    """
    try:
        logger.info("Validating documentation...")
        
        # Create documentation manager
        manager = DocumentationManager()
        
        # Validate documentation
        result = manager.validate_documentation()
        
        return {
            "success": result.success,
            "message": result.message,
            "files_created": result.files_created,
            "files_updated": result.files_updated,
            "errors": result.errors,
            "warnings": result.warnings,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to validate documentation: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_documentation_list() -> Dict[str, Any]:
    """
    List all documentation files.
    
    Returns:
        Dictionary with documentation files list
    """
    try:
        logger.info("Listing documentation files...")
        
        # Create documentation manager
        manager = DocumentationManager()
        
        # List documentation files
        docs_files = []
        runbooks_files = []
        
        # Check docs directory
        if manager.docs_dir.exists():
            for file_path in manager.docs_dir.iterdir():
                if file_path.is_file() and file_path.suffix == '.md':
                    docs_files.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
        
        # Check runbooks directory
        if manager.runbooks_dir.exists():
            for file_path in manager.runbooks_dir.iterdir():
                if file_path.is_file() and file_path.suffix == '.md':
                    runbooks_files.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
        
        return {
            "success": True,
            "documentation_files": docs_files,
            "runbook_files": runbooks_files,
            "total_docs": len(docs_files),
            "total_runbooks": len(runbooks_files),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list documentation files: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_documentation_get_content(
    file_path: str
) -> Dict[str, Any]:
    """
    Get content of a specific documentation file.
    
    Args:
        file_path: Path to the documentation file
        
    Returns:
        Dictionary with file content
    """
    try:
        logger.info(f"Getting documentation file content: {file_path}")
        
        # Create documentation manager
        manager = DocumentationManager()
        
        # Check if file exists
        full_path = manager.project_root / file_path
        if not full_path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Read file content
        with open(full_path, 'r') as f:
            content = f.read()
        
        return {
            "success": True,
            "file_path": file_path,
            "content": content,
            "size": len(content),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get documentation file content {file_path}: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_documentation_create_section(
    section_name: str,
    title: str,
    content: str,
    parent_section: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new documentation section.
    
    Args:
        section_name: Name of the section
        title: Title of the section
        content: Content of the section
        parent_section: Parent section (optional)
        
    Returns:
        Dictionary with section creation result
    """
    try:
        logger.info(f"Creating documentation section: {section_name}")
        
        # Create documentation manager
        manager = DocumentationManager()
        
        # Create section content
        section_content = f"# {title}\n\n{content}\n"
        
        # Determine file path
        if parent_section:
            file_path = manager.docs_dir / f"{parent_section}_{section_name}.md"
        else:
            file_path = manager.docs_dir / f"{section_name}.md"
        
        # Write section file
        with open(file_path, 'w') as f:
            f.write(section_content)
        
        return {
            "success": True,
            "message": f"Documentation section '{section_name}' created successfully",
            "file_path": str(file_path),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to create documentation section {section_name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_documentation_update_runbook(
    runbook_name: str,
    content: str
) -> Dict[str, Any]:
    """
    Update a specific runbook.
    
    Args:
        runbook_name: Name of the runbook to update
        content: New content for the runbook
        
    Returns:
        Dictionary with runbook update result
    """
    try:
        logger.info(f"Updating runbook: {runbook_name}")
        
        # Create documentation manager
        manager = DocumentationManager()
        
        # Determine file path
        file_path = manager.runbooks_dir / f"{runbook_name}.md"
        
        # Write runbook file
        with open(file_path, 'w') as f:
            f.write(content)
        
        return {
            "success": True,
            "message": f"Runbook '{runbook_name}' updated successfully",
            "file_path": str(file_path),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to update runbook {runbook_name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
