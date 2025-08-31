"""
CAEF Hook System
================

Enterprise-grade hook system for intercepting and controlling CAEF operations.
Provides real-time monitoring, validation, and flow control.

Features:
- 16 distinct hook points covering full lifecycle
- Priority-based execution
- Timeout protection
- Real-time monitoring via terminal and web
- Context modification capabilities
- Blocking/validation support
"""

from typing import Dict, List, Callable, Optional, Any, Union
from enum import Enum
import asyncio
import json
import time
import re
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


class HookType(Enum):
    """All available hook points in CAEF system"""
    # Task lifecycle
    TASK_PRE_SUBMIT = "task_pre_submit"
    TASK_POST_SUBMIT = "task_post_submit"
    TASK_PRE_EXECUTE = "task_pre_execute"
    TASK_POST_EXECUTE = "task_post_execute"
    
    # Agent operations
    AGENT_PRE_DECISION = "agent_pre_decision"
    AGENT_POST_DECISION = "agent_post_decision"
    
    # Tool usage
    TOOL_PRE_USE = "tool_pre_use"
    TOOL_POST_USE = "tool_post_use"
    
    # Validation gates
    GATE_PRE_VALIDATION = "gate_pre_validation"
    GATE_POST_VALIDATION = "gate_post_validation"
    
    # Git operations
    GIT_PRE_COMMIT = "git_pre_commit"
    GIT_POST_COMMIT = "git_post_commit"
    
    # Error handling
    ERROR_OCCURRED = "error_occurred"
    ERROR_RECOVERED = "error_recovered"
    
    # Completion
    WORKFLOW_COMPLETE = "workflow_complete"
    SESSION_END = "session_end"


@dataclass
class HookResult:
    """Standardized hook result format"""
    continue_execution: bool = True
    modified_context: Optional[Dict[str, Any]] = None
    log_entry: Optional[str] = None
    reason: Optional[str] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.modified_context is None:
            self.modified_context = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class HookEntry:
    """Internal hook entry structure"""
    id: str
    handler: Callable
    priority: int
    timeout: int
    registered_at: str
    name: str = ""
    description: str = ""
    
    def __post_init__(self):
        if not self.name:
            self.name = self.handler.__name__


class CAEFHookSystem:
    """Central hook management system for CAEF"""
    
    def __init__(self):
        self.hooks: Dict[HookType, List[HookEntry]] = {
            hook_type: [] for hook_type in HookType
        }
        self.hook_stats = {
            hook_type: {
                'total_calls': 0,
                'blocked_count': 0,
                'error_count': 0,
                'timeout_count': 0,
                'total_duration_ms': 0,
                'avg_duration_ms': 0,
                'last_called': None,
                'last_error': None
            } for hook_type in HookType
        }
        self.monitoring_enabled = True
        self.web_socket_clients = []
        self.event_history = []  # Circular buffer of last 1000 events
        self.max_history = 1000
        
    def register_hook(self, 
                     hook_type: HookType, 
                     handler: Callable,
                     priority: int = 50,
                     timeout_seconds: int = 60,
                     name: Optional[str] = None,
                     description: Optional[str] = None) -> str:
        """
        Register a hook handler with priority and timeout.
        
        Args:
            hook_type: The type of hook to register
            handler: Async callable that takes context dict and returns HookResult
            priority: Higher priority hooks run first (0-100)
            timeout_seconds: Maximum execution time
            name: Optional friendly name
            description: Optional description
            
        Returns:
            Hook ID for later reference
        """
        hook_id = f"{hook_type.value}_{handler.__name__}_{id(handler)}"
        
        hook_entry = HookEntry(
            id=hook_id,
            handler=handler,
            priority=priority,
            timeout=timeout_seconds,
            registered_at=datetime.now().isoformat(),
            name=name or handler.__name__,
            description=description or handler.__doc__ or ""
        )
        
        # Insert sorted by priority (higher priority first)
        self.hooks[hook_type].append(hook_entry)
        self.hooks[hook_type].sort(key=lambda x: x.priority, reverse=True)
        
        logger.info(f"Registered hook {hook_id} for {hook_type.value} with priority {priority}")
        
        return hook_id
    
    def unregister_hook(self, hook_id: str) -> bool:
        """Unregister a hook by ID"""
        for hook_type, hook_list in self.hooks.items():
            for hook in hook_list:
                if hook.id == hook_id:
                    hook_list.remove(hook)
                    logger.info(f"Unregistered hook {hook_id}")
                    return True
        return False
    
    async def trigger_hook(self, 
                          hook_type: HookType,
                          context: Dict[str, Any]) -> HookResult:
        """
        Trigger all hooks for a given type with context.
        
        Args:
            hook_type: Type of hook to trigger
            context: Context dictionary passed to hooks
            
        Returns:
            Combined HookResult from all hooks
        """
        start_time = time.time()
        
        # Update stats
        self.hook_stats[hook_type]['total_calls'] += 1
        self.hook_stats[hook_type]['last_called'] = datetime.now().isoformat()
        
        # Broadcast to monitoring
        await self._broadcast_hook_event(hook_type, context, 'triggered')
        
        combined_result = HookResult()
        hooks_executed = 0
        
        for hook_entry in self.hooks[hook_type]:
            try:
                # Run hook with timeout
                hook_result = await asyncio.wait_for(
                    hook_entry.handler(context.copy()),
                    timeout=hook_entry.timeout
                )
                
                hooks_executed += 1
                
                # Ensure we got a HookResult
                if not isinstance(hook_result, HookResult):
                    logger.warning(f"Hook {hook_entry.id} returned non-HookResult: {type(hook_result)}")
                    hook_result = HookResult()
                
                # Process result
                if not hook_result.continue_execution:
                    combined_result.continue_execution = False
                    combined_result.reason = hook_result.reason
                    self.hook_stats[hook_type]['blocked_count'] += 1
                    
                    # Broadcast block event
                    await self._broadcast_hook_event(
                        hook_type, context, 'blocked', hook_result.reason
                    )
                    break
                
                # Merge context modifications
                if hook_result.modified_context:
                    combined_result.modified_context.update(hook_result.modified_context)
                
                # Append log entries
                if hook_result.log_entry:
                    if combined_result.log_entry:
                        combined_result.log_entry += f"\n{hook_result.log_entry}"
                    else:
                        combined_result.log_entry = hook_result.log_entry
                    
            except asyncio.TimeoutError:
                self.hook_stats[hook_type]['timeout_count'] += 1
                error_msg = f"Hook {hook_entry.name} timed out after {hook_entry.timeout}s"
                logger.error(error_msg)
                await self._broadcast_hook_event(hook_type, context, 'timeout', error_msg)
                
            except Exception as e:
                self.hook_stats[hook_type]['error_count'] += 1
                self.hook_stats[hook_type]['last_error'] = str(e)
                error_msg = f"Hook {hook_entry.name} failed: {str(e)}"
                logger.error(error_msg, exc_info=True)
                await self._broadcast_hook_event(hook_type, context, 'error', error_msg)
        
        # Update duration stats
        duration_ms = (time.time() - start_time) * 1000
        stats = self.hook_stats[hook_type]
        stats['total_duration_ms'] += duration_ms
        if stats['total_calls'] > 0:
            stats['avg_duration_ms'] = stats['total_duration_ms'] / stats['total_calls']
        
        # Broadcast completion
        await self._broadcast_hook_event(
            hook_type, context, 'completed', 
            f"Executed {hooks_executed} hooks in {duration_ms:.2f}ms"
        )
        
        return combined_result
    
    async def _broadcast_hook_event(self, 
                                   hook_type: HookType,
                                   context: Dict,
                                   event_type: str,
                                   message: Optional[str] = None):
        """Broadcast hook events to monitoring systems"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'hook_type': hook_type.value,
            'event_type': event_type,
            'context_summary': self._summarize_context(context),
            'message': message,
            'stats': self.hook_stats[hook_type].copy()
        }
        
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        # Terminal monitoring
        if self.monitoring_enabled:
            self._print_terminal_event(event)
        
        # Web socket broadcast
        dead_clients = []
        for client in self.web_socket_clients:
            try:
                await client.send_json(event)
            except Exception as e:
                logger.debug(f"Failed to send to websocket: {e}")
                dead_clients.append(client)
        
        # Remove dead clients
        for client in dead_clients:
            self.web_socket_clients.remove(client)
    
    def _summarize_context(self, context: Dict) -> Dict:
        """Create safe summary of context for monitoring"""
        summary = {}
        
        # Extract key fields
        safe_fields = [
            'task_id', 'agent_id', 'service_name', 'operation',
            'file_path', 'tool_name', 'validation_type', 'error_type'
        ]
        
        for field in safe_fields:
            if field in context:
                summary[field] = str(context[field])[:100]  # Truncate long values
        
        # Add counts for collections
        for key, value in context.items():
            if isinstance(value, (list, dict, set)):
                summary[f"{key}_count"] = len(value)
        
        return summary
    
    def _print_terminal_event(self, event: Dict):
        """Pretty print event to terminal with colors"""
        event_type = event['event_type']
        hook_type = event['hook_type']
        
        # ANSI color codes
        colors = {
            'triggered': '\033[94m',  # Blue
            'blocked': '\033[91m',    # Red
            'error': '\033[93m',      # Yellow
            'timeout': '\033[95m',    # Magenta
            'completed': '\033[92m'   # Green
        }
        color = colors.get(event_type, '\033[0m')
        reset = '\033[0m'
        
        # Format timestamp
        timestamp = datetime.fromisoformat(event['timestamp']).strftime('%H:%M:%S.%f')[:-3]
        
        # Main event line
        print(f"{color}[{timestamp}] {hook_type} - {event_type.upper()}{reset}")
        
        # Additional details
        if event.get('message'):
            print(f"  └─ {event['message']}")
            
        if event.get('context_summary'):
            summary = event['context_summary']
            if summary.get('task_id'):
                print(f"  └─ Task: {summary['task_id']}")
            if summary.get('service_name'):
                print(f"  └─ Service: {summary['service_name']}")
            if summary.get('operation'):
                print(f"  └─ Operation: {summary['operation']}")
    
    def get_hook_info(self, hook_type: Optional[HookType] = None) -> Dict:
        """Get information about registered hooks"""
        info = {}
        
        hook_types = [hook_type] if hook_type else list(HookType)
        
        for ht in hook_types:
            info[ht.value] = {
                'registered_hooks': [
                    {
                        'id': hook.id,
                        'name': hook.name,
                        'priority': hook.priority,
                        'timeout': hook.timeout,
                        'description': hook.description
                    }
                    for hook in self.hooks[ht]
                ],
                'stats': self.hook_stats[ht]
            }
        
        return info
    
    def reset_stats(self, hook_type: Optional[HookType] = None):
        """Reset statistics for hooks"""
        hook_types = [hook_type] if hook_type else list(HookType)
        
        for ht in hook_types:
            self.hook_stats[ht] = {
                'total_calls': 0,
                'blocked_count': 0,
                'error_count': 0,
                'timeout_count': 0,
                'total_duration_ms': 0,
                'avg_duration_ms': 0,
                'last_called': None,
                'last_error': None
            }


# Global hook system instance
_hook_system = None


def get_hook_system() -> CAEFHookSystem:
    """Get or create the global hook system instance"""
    global _hook_system
    if _hook_system is None:
        _hook_system = CAEFHookSystem()
    return _hook_system