#!/usr/bin/env python3
"""
CAEF Research Hooks
===================
Date: August 1, 2025
Authority: AEMI - Atomic Enterprise Methodology Implementation

Provides hooks to integrate comprehensive research into all CAEF execution stages.
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from functools import wraps
import asyncio

from caef_task_research_integration import get_research_integration

logger = logging.getLogger(__name__)


class CAEFResearchHooks:
    """
    Hook system for integrating research into CAEF task execution
    
    Provides decorators and utilities to ensure all tasks benefit from
    comprehensive research throughout their lifecycle.
    """
    
    def __init__(self):
        """Initialize research hooks"""
        self.research_integration = get_research_integration()
        self.hooks_enabled = True
        self.hook_stats = {
            "pre_execution": 0,
            "post_execution": 0,
            "research_used": 0,
            "tdd_generated": 0
        }
    
    def with_research(self, task_type: str = "general"):
        """
        Decorator to add research capabilities to any task execution function
        
        Args:
            task_type: Type of task (implementation, analysis, validation, etc.)
        """
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not self.hooks_enabled:
                    return await func(*args, **kwargs)
                
                # Extract task information from arguments
                task_info = self._extract_task_info(args, kwargs, task_type)
                
                if task_info:
                    # Perform research
                    logger.info(f"🔬 Performing research for {func.__name__}")
                    enhanced_task = await self.research_integration.prepare_task_with_research(task_info)
                    
                    # Update kwargs with research context
                    kwargs["research_context"] = enhanced_task
                    self.hook_stats["research_used"] += 1
                    
                    if enhanced_task.get("tdd"):
                        self.hook_stats["tdd_generated"] += 1
                
                self.hook_stats["pre_execution"] += 1
                
                # Execute the original function
                result = await func(*args, **kwargs)
                
                # Post-execution tracking
                if task_info:
                    task_id = task_info.get("task_id", "unknown")
                    await self.research_integration.hook_post_task_execution(
                        task_id,
                        {"success": True, "result": result}
                    )
                
                self.hook_stats["post_execution"] += 1
                
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                if not self.hooks_enabled:
                    return func(*args, **kwargs)
                
                # For sync functions, run async operations in event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # Extract task information
                    task_info = self._extract_task_info(args, kwargs, task_type)
                    
                    if task_info:
                        # Perform research
                        logger.info(f"🔬 Performing research for {func.__name__}")
                        enhanced_task = loop.run_until_complete(
                            self.research_integration.prepare_task_with_research(task_info)
                        )
                        
                        # Update kwargs with research context
                        kwargs["research_context"] = enhanced_task
                        self.hook_stats["research_used"] += 1
                        
                        if enhanced_task.get("tdd"):
                            self.hook_stats["tdd_generated"] += 1
                    
                    self.hook_stats["pre_execution"] += 1
                    
                    # Execute the original function
                    result = func(*args, **kwargs)
                    
                    # Post-execution tracking
                    if task_info:
                        task_id = task_info.get("task_id", "unknown")
                        loop.run_until_complete(
                            self.research_integration.hook_post_task_execution(
                                task_id,
                                {"success": True, "result": result}
                            )
                        )
                    
                    self.hook_stats["post_execution"] += 1
                    
                    return result
                    
                finally:
                    loop.close()
            
            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def _extract_task_info(self, args: tuple, kwargs: dict, task_type: str) -> Optional[Dict[str, Any]]:
        """Extract task information from function arguments"""
        task_info = None
        
        # Check kwargs first
        if "task" in kwargs:
            task_info = kwargs["task"]
        elif "task_data" in kwargs:
            task_info = kwargs["task_data"]
        elif "task_id" in kwargs:
            task_info = {"task_id": kwargs["task_id"]}
        
        # Check positional args
        elif len(args) > 0:
            # Common patterns:
            # 1. First arg is self/cls
            # 2. Second arg might be task_id or task_data
            start_idx = 1 if hasattr(args[0], '__class__') else 0
            
            if len(args) > start_idx:
                first_arg = args[start_idx]
                if isinstance(first_arg, dict):
                    task_info = first_arg
                elif isinstance(first_arg, str):
                    # Assume it's task_id
                    task_info = {"task_id": first_arg}
        
        # Add task type if we found task info
        if task_info and "type" not in task_info:
            task_info["type"] = task_type
        
        return task_info
    
    def enable_hooks(self):
        """Enable research hooks"""
        self.hooks_enabled = True
        logger.info("Research hooks enabled")
    
    def disable_hooks(self):
        """Disable research hooks"""
        self.hooks_enabled = False
        logger.info("Research hooks disabled")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get hook statistics"""
        return {
            "enabled": self.hooks_enabled,
            "hook_stats": self.hook_stats.copy(),
            "research_metrics": self.research_integration.get_research_metrics()
        }


# Create singleton instance
_research_hooks_instance = None

def get_research_hooks() -> CAEFResearchHooks:
    """Get or create research hooks instance"""
    global _research_hooks_instance
    if _research_hooks_instance is None:
        _research_hooks_instance = CAEFResearchHooks()
    return _research_hooks_instance


# Convenience decorators
research_hooks = get_research_hooks()

# Export decorators for easy use
with_research = research_hooks.with_research
with_implementation_research = research_hooks.with_research("implementation")
with_analysis_research = research_hooks.with_research("analysis")
with_validation_research = research_hooks.with_research("validation")