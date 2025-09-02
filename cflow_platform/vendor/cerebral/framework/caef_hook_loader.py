"""
CAEF Hook Loader
===============

Loads and manages hook configurations from various sources:
- Python modules in hooks directory
- YAML configuration files
- Shell script hooks
"""

import yaml
import importlib.util
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Callable
import logging

from .caef_hook_system import CAEFHookSystem, HookType, HookResult

logger = logging.getLogger(__name__)


class CAEFHookLoader:
    """Load and manage hook configurations"""
    
    def __init__(self, hook_system: CAEFHookSystem):
        self.hook_system = hook_system
        self.loaded_hooks = {}
        self.loaded_configs = {}
        
    def load_hooks_from_directory(self, hooks_dir: Path) -> int:
        """
        Load all Python hooks from a directory.
        
        Returns:
            Number of hooks loaded
        """
        if not hooks_dir.exists():
            logger.warning(f"Hooks directory {hooks_dir} does not exist")
            return 0
            
        hook_count = 0
        hook_files = list(hooks_dir.glob("*.py"))
        
        # Ensure local CLI integration is loaded first for context
        priority_hooks = ['local_cli_integration.py', 'pipeline_enforcement.py']
        other_hooks = []
        
        for hook_file in hook_files:
            if hook_file.name.startswith('_'):
                continue
            if hook_file.name in priority_hooks:
                continue
            other_hooks.append(hook_file)
        
        # Load priority hooks first
        for hook_name in priority_hooks:
            hook_file = hooks_dir / hook_name
            if hook_file.exists():
                hook_files = [hook_file] + other_hooks
                break
        
        for hook_file in hook_files:
            if hook_file.name.startswith('_'):
                continue
                
            try:
                # Load Python module
                spec = importlib.util.spec_from_file_location(
                    hook_file.stem, hook_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Register hooks from module
                    if hasattr(module, 'register_hooks'):
                        count = module.register_hooks(self.hook_system)
                        hook_count += count if isinstance(count, int) else 1
                        self.loaded_hooks[hook_file.stem] = module
                        logger.info(f"Loaded hooks from {hook_file.name}")
                    else:
                        logger.warning(f"No register_hooks function in {hook_file.name}")
                        
            except Exception as e:
                logger.error(f"Failed to load hook {hook_file}: {e}", exc_info=True)
        
        return hook_count
    
    def load_hook_config(self, config_file: Path) -> int:
        """
        Load hook configuration from YAML file.
        
        Returns:
            Number of hooks loaded
        """
        if not config_file.exists():
            logger.warning(f"Hook config file {config_file} does not exist")
            return 0
            
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            if not config or 'hooks' not in config:
                logger.warning(f"No hooks found in {config_file}")
                return 0
            
            hook_count = 0
            
            for hook_config in config.get('hooks', []):
                try:
                    hook_type = HookType[hook_config['type']]
                    
                    if hook_config['handler_type'] == 'shell':
                        # Create shell command hook
                        handler = self._create_shell_hook(
                            hook_config['command'],
                            hook_config.get('args', [])
                        )
                    elif hook_config['handler_type'] == 'python':
                        # Create Python function hook
                        handler = self._create_python_hook(
                            hook_config['module'], 
                            hook_config['function']
                        )
                    else:
                        logger.warning(f"Unknown handler type: {hook_config['handler_type']}")
                        continue
                    
                    self.hook_system.register_hook(
                        hook_type,
                        handler,
                        priority=hook_config.get('priority', 50),
                        timeout_seconds=hook_config.get('timeout', 60),
                        name=hook_config.get('name', hook_config['function']),
                        description=hook_config.get('description', '')
                    )
                    
                    hook_count += 1
                    
                except KeyError as e:
                    logger.error(f"Missing required field in hook config: {e}")
                except ValueError as e:
                    logger.error(f"Invalid hook type: {e}")
                    
            self.loaded_configs[str(config_file)] = config
            logger.info(f"Loaded {hook_count} hooks from {config_file}")
            return hook_count
            
        except Exception as e:
            logger.error(f"Failed to load hook config {config_file}: {e}", exc_info=True)
            return 0
    
    def _create_shell_hook(self, command: str, args: List[str] = None) -> Callable:
        """Create a hook that executes a shell command"""
        
        async def shell_hook(context: Dict) -> HookResult:
            try:
                # Prepare command with args
                full_command = [command]
                if args:
                    full_command.extend(args)
                
                # Pass context as JSON via stdin
                context_json = json.dumps(context)
                
                # Run command
                process = await asyncio.create_subprocess_exec(
                    *full_command,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate(context_json.encode())
                
                # Check exit code
                if process.returncode == 0:
                    # Try to parse JSON response
                    try:
                        response = json.loads(stdout.decode())
                        return HookResult(
                            continue_execution=response.get('continue', True),
                            modified_context=response.get('context', {}),
                            log_entry=response.get('log', ''),
                            reason=response.get('reason', '')
                        )
                    except json.JSONDecodeError:
                        # Plain text response
                        return HookResult(
                            continue_execution=True,
                            log_entry=stdout.decode().strip()
                        )
                        
                elif process.returncode == 2:
                    # Block execution
                    return HookResult(
                        continue_execution=False,
                        reason=stderr.decode().strip() or "Shell hook blocked execution"
                    )
                else:
                    # Error
                    raise Exception(f"Shell command failed: {stderr.decode()}")
                    
            except Exception as e:
                logger.error(f"Shell hook error: {e}")
                return HookResult(
                    continue_execution=True,
                    log_entry=f"Shell hook error: {str(e)}"
                )
        
        shell_hook.__name__ = f"shell_{Path(command).stem}"
        return shell_hook
    
    def _create_python_hook(self, module_name: str, function_name: str) -> Callable:
        """Create a hook from a Python module and function"""
        
        try:
            # Import module
            if module_name in self.loaded_hooks:
                module = self.loaded_hooks[module_name]
            else:
                module = importlib.import_module(module_name)
            
            # Get function
            if hasattr(module, function_name):
                return getattr(module, function_name)
            else:
                raise AttributeError(f"Function {function_name} not found in {module_name}")
                
        except Exception as e:
            logger.error(f"Failed to create Python hook: {e}")
            
            # Return a dummy hook that logs the error
            async def error_hook(context: Dict) -> HookResult:
                return HookResult(
                    continue_execution=True,
                    log_entry=f"Hook loading error: {str(e)}"
                )
            
            error_hook.__name__ = f"error_{function_name}"
            return error_hook
    
    def load_all_hooks(self, base_dir: Path = None) -> Dict[str, int]:
        """
        Load all hooks from standard locations.
        
        Returns:
            Dictionary with counts of hooks loaded from each source
        """
        if base_dir is None:
            base_dir = Path(".cerebraflow")
        
        counts = {}
        
        # Load from Python modules
        hooks_dir = base_dir / "hooks"
        if hooks_dir.exists():
            counts['python_modules'] = self.load_hooks_from_directory(hooks_dir)
        
        # Load from config files
        config_files = [
            base_dir / "hooks.yaml",
            base_dir / "hooks" / "config.yaml",
            base_dir / "hooks" / "library" / "*.yaml"
        ]
        
        counts['yaml_configs'] = 0
        for pattern in config_files:
            if '*' in str(pattern):
                # Glob pattern
                for config_file in Path(pattern).parent.glob(Path(pattern).name):
                    counts['yaml_configs'] += self.load_hook_config(config_file)
            else:
                # Single file
                if Path(pattern).exists():
                    counts['yaml_configs'] += self.load_hook_config(Path(pattern))
        
        total = sum(counts.values())
        logger.info(f"Loaded {total} hooks total: {counts}")
        
        return counts
    
    def reload_hooks(self) -> Dict[str, int]:
        """Reload all hooks (useful for development)"""
        # Clear existing hooks
        for hook_type in HookType:
            self.hook_system.hooks[hook_type].clear()
        
        self.loaded_hooks.clear()
        self.loaded_configs.clear()
        
        # Reload
        return self.load_all_hooks()
    
    def list_loaded_hooks(self) -> List[Dict]:
        """Get list of all loaded hooks with details"""
        hooks = []
        
        for hook_type in HookType:
            for hook in self.hook_system.hooks[hook_type]:
                hooks.append({
                    'type': hook_type.value,
                    'id': hook.id,
                    'name': hook.name,
                    'priority': hook.priority,
                    'timeout': hook.timeout,
                    'description': hook.description,
                    'source': self._find_hook_source(hook.id)
                })
        
        return sorted(hooks, key=lambda h: (h['type'], -h['priority']))
    
    def _find_hook_source(self, hook_id: str) -> str:
        """Find where a hook was loaded from"""
        # Check Python modules
        for module_name, module in self.loaded_hooks.items():
            if hook_id.startswith(f"{module_name}_"):
                return f"module:{module_name}"
        
        # Check configs
        for config_file in self.loaded_configs:
            return f"config:{Path(config_file).name}"
        
        return "unknown"


import json  # Add this import at the top