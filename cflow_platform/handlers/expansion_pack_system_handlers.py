"""
MCP Handlers for Expansion Pack System

This module provides MCP tool handlers for expansion pack system functionality
including pack installation, activation, and management.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..core.expansion_pack_system import (
    ExpansionPackSystem,
    ExpansionPackType,
    get_expansion_system
)
from ..core.git_workflow_manager import get_git_workflow_manager

logger = logging.getLogger(__name__)


async def bmad_expansion_system_status() -> Dict[str, Any]:
    """
    Get expansion pack system status.
    
    Returns:
        Dict containing expansion pack system status
    """
    try:
        system = get_expansion_system()
        
        # Initialize system if not already done
        if not system.system_active:
            await system.initialize_system()
        
        # Get system status
        status_data = system.get_system_status()
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="expansion_system_status",
            test_results={
                "system_active": status_data.get("system_active", False),
                "total_available": status_data.get("manager_status", {}).get("total_available", 0),
                "total_installed": status_data.get("manager_status", {}).get("total_installed", 0),
                "total_active": status_data.get("manager_status", {}).get("total_active", 0)
            }
        )
        
        return {
            "success": True,
            "system_status": status_data,
            "git_workflow_result": git_result,
            "message": "Expansion pack system status retrieved"
        }
        
    except Exception as e:
        logger.error(f"Failed to get expansion system status: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to get expansion system status: {e}"
        }


async def bmad_expansion_pack_install(
    pack_id: str
) -> Dict[str, Any]:
    """
    Install expansion packs.
    
    Args:
        pack_id: ID of the expansion pack to install
        
    Returns:
        Dict containing installation results
    """
    try:
        system = get_expansion_system()
        
        # Initialize system if not already done
        if not system.system_active:
            await system.initialize_system()
        
        # Install pack
        install_result = system.install_pack(pack_id)
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="expansion_pack_install",
            test_results={
                "pack_id": pack_id,
                "install_success": install_result.get("success", False),
                "pack_name": install_result.get("pack_metadata", {}).get("name", "Unknown")
            }
        )
        
        return {
            "success": install_result.get("success", False),
            "install_result": install_result,
            "git_workflow_result": git_result,
            "message": f"Expansion pack {pack_id} installation {'completed' if install_result.get('success', False) else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to install expansion pack {pack_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to install expansion pack {pack_id}: {e}"
        }


async def bmad_expansion_pack_uninstall(
    pack_id: str
) -> Dict[str, Any]:
    """
    Uninstall expansion packs.
    
    Args:
        pack_id: ID of the expansion pack to uninstall
        
    Returns:
        Dict containing uninstallation results
    """
    try:
        system = get_expansion_system()
        
        # Uninstall pack
        uninstall_result = system.uninstall_pack(pack_id)
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="expansion_pack_uninstall",
            test_results={
                "pack_id": pack_id,
                "uninstall_success": uninstall_result.get("success", False)
            }
        )
        
        return {
            "success": uninstall_result.get("success", False),
            "uninstall_result": uninstall_result,
            "git_workflow_result": git_result,
            "message": f"Expansion pack {pack_id} uninstallation {'completed' if uninstall_result.get('success', False) else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to uninstall expansion pack {pack_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to uninstall expansion pack {pack_id}: {e}"
        }


async def bmad_expansion_pack_list(
    filter_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    List available and installed expansion packs.
    
    Args:
        filter_type: Filter by pack type (game_dev, devops, technical_research)
        
    Returns:
        Dict containing expansion pack lists
    """
    try:
        system = get_expansion_system()
        
        # Initialize system if not already done
        if not system.system_active:
            await system.initialize_system()
        
        # Get pack lists
        available_packs = system.list_available_packs()
        installed_packs = system.list_installed_packs()
        active_packs = system.list_active_packs()
        
        # Filter by type if specified
        if filter_type:
            available_packs = [p for p in available_packs if p.pack_type.value == filter_type]
            installed_packs = [p for p in installed_packs if p.pack_type.value == filter_type]
            active_packs = [p for p in active_packs if p.pack_type.value == filter_type]
        
        # Convert to serializable format
        def pack_to_dict(pack):
            return {
                "pack_id": pack.pack_id,
                "name": pack.name,
                "version": pack.version,
                "description": pack.description,
                "pack_type": pack.pack_type.value,
                "author": pack.author,
                "agents_count": len(pack.agents),
                "tools_count": len(pack.tools),
                "templates_count": len(pack.templates),
                "workflows_count": len(pack.workflows)
            }
        
        packs_data = {
            "available_packs": [pack_to_dict(p) for p in available_packs],
            "installed_packs": [pack_to_dict(p) for p in installed_packs],
            "active_packs": [pack_to_dict(p) for p in active_packs],
            "filter_type": filter_type,
            "summary": {
                "total_available": len(available_packs),
                "total_installed": len(installed_packs),
                "total_active": len(active_packs)
            }
        }
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="expansion_pack_list",
            test_results={
                "total_available": len(available_packs),
                "total_installed": len(installed_packs),
                "total_active": len(active_packs),
                "filter_type": filter_type
            }
        )
        
        return {
            "success": True,
            "packs_data": packs_data,
            "git_workflow_result": git_result,
            "message": f"Listed {len(available_packs)} available, {len(installed_packs)} installed, {len(active_packs)} active expansion packs"
        }
        
    except Exception as e:
        logger.error(f"Failed to list expansion packs: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to list expansion packs: {e}"
        }


async def bmad_expansion_pack_activate(
    pack_id: str
) -> Dict[str, Any]:
    """
    Activate expansion pack capabilities.
    
    Args:
        pack_id: ID of the expansion pack to activate
        
    Returns:
        Dict containing activation results
    """
    try:
        system = get_expansion_system()
        
        # Activate pack
        activate_result = system.activate_pack(pack_id)
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="expansion_pack_activate",
            test_results={
                "pack_id": pack_id,
                "activate_success": activate_result.get("success", False),
                "pack_name": activate_result.get("pack_metadata", {}).get("name", "Unknown")
            }
        )
        
        return {
            "success": activate_result.get("success", False),
            "activate_result": activate_result,
            "git_workflow_result": git_result,
            "message": f"Expansion pack {pack_id} activation {'completed' if activate_result.get('success', False) else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to activate expansion pack {pack_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to activate expansion pack {pack_id}: {e}"
        }


async def bmad_expansion_pack_deactivate(
    pack_id: str
) -> Dict[str, Any]:
    """
    Deactivate expansion pack capabilities.
    
    Args:
        pack_id: ID of the expansion pack to deactivate
        
    Returns:
        Dict containing deactivation results
    """
    try:
        system = get_expansion_system()
        
        # Deactivate pack
        deactivate_result = system.deactivate_pack(pack_id)
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="expansion_pack_deactivate",
            test_results={
                "pack_id": pack_id,
                "deactivate_success": deactivate_result.get("success", False)
            }
        )
        
        return {
            "success": deactivate_result.get("success", False),
            "deactivate_result": deactivate_result,
            "git_workflow_result": git_result,
            "message": f"Expansion pack {pack_id} deactivation {'completed' if deactivate_result.get('success', False) else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to deactivate expansion pack {pack_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to deactivate expansion pack {pack_id}: {e}"
        }


async def bmad_expansion_pack_update(
    pack_id: str
) -> Dict[str, Any]:
    """
    Update expansion packs.
    
    Args:
        pack_id: ID of the expansion pack to update
        
    Returns:
        Dict containing update results
    """
    try:
        system = get_expansion_system()
        
        # For now, update means reinstall (in a real system, this would check for updates)
        uninstall_result = system.uninstall_pack(pack_id)
        if uninstall_result.get("success", False):
            install_result = system.install_pack(pack_id)
            if install_result.get("success", False):
                # Reactivate if it was active before
                activate_result = system.activate_pack(pack_id)
                update_success = True
            else:
                update_success = False
        else:
            update_success = False
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="expansion_pack_update",
            test_results={
                "pack_id": pack_id,
                "update_success": update_success
            }
        )
        
        return {
            "success": update_success,
            "update_result": {
                "uninstall_success": uninstall_result.get("success", False),
                "install_success": install_result.get("success", False) if 'install_result' in locals() else False,
                "activate_success": activate_result.get("success", False) if 'activate_result' in locals() else False
            },
            "git_workflow_result": git_result,
            "message": f"Expansion pack {pack_id} update {'completed' if update_success else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to update expansion pack {pack_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to update expansion pack {pack_id}: {e}"
        }


async def bmad_expansion_pack_validate(
    pack_id: str
) -> Dict[str, Any]:
    """
    Validate expansion pack integrity.
    
    Args:
        pack_id: ID of the expansion pack to validate
        
    Returns:
        Dict containing validation results
    """
    try:
        system = get_expansion_system()
        
        # Validate pack
        validate_result = system.validate_pack(pack_id)
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="expansion_pack_validate",
            test_results={
                "pack_id": pack_id,
                "validation_success": validate_result.get("success", False),
                "validation_passed": validate_result.get("success", False)
            }
        )
        
        return {
            "success": validate_result.get("success", False),
            "validation_result": validate_result,
            "git_workflow_result": git_result,
            "message": f"Expansion pack {pack_id} validation {'passed' if validate_result.get('success', False) else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to validate expansion pack {pack_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to validate expansion pack {pack_id}: {e}"
        }
