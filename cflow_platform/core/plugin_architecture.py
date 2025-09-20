"""
Plugin Architecture and Extensibility for WebMCP

This module provides dynamic tool loading, smart routing, hot-reload configuration,
A/B testing framework, and version management for the WebMCP server.
"""

import asyncio
import importlib
import json
import logging
import os
import time
import yaml
from typing import Any, Dict, List, Optional, Callable, Type, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import watchdog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


class PluginType(Enum):
    """Plugin types"""
    TOOL = "tool"
    HANDLER = "handler"
    MIDDLEWARE = "middleware"
    EXPANSION_PACK = "expansion_pack"


class PluginStatus(Enum):
    """Plugin status"""
    LOADED = "loaded"
    UNLOADED = "unloaded"
    ERROR = "error"
    LOADING = "loading"


@dataclass
class PluginMetadata:
    """Plugin metadata"""
    name: str
    version: str
    description: str
    plugin_type: PluginType
    author: str
    dependencies: List[str]
    config_schema: Dict[str, Any]
    entry_point: str
    load_time: float
    status: PluginStatus


@dataclass
class PluginConfig:
    """Plugin configuration"""
    enabled: bool = True
    priority: int = 100
    config: Dict[str, Any] = None
    hot_reload: bool = True
    version_constraints: Dict[str, str] = None


class PluginLoader:
    """Dynamic plugin loader"""
    
    def __init__(self, plugin_directory: str = "plugins"):
        self.plugin_directory = Path(plugin_directory)
        self.plugin_directory.mkdir(exist_ok=True)
        
        self.loaded_plugins: Dict[str, PluginMetadata] = {}
        self.plugin_instances: Dict[str, Any] = {}
        self.plugin_configs: Dict[str, PluginConfig] = {}
        
        # Plugin registry
        self.tool_plugins: Dict[str, Callable] = {}
        self.handler_plugins: Dict[str, Callable] = {}
        self.middleware_plugins: List[Callable] = []
        self.expansion_plugins: Dict[str, Any] = {}
    
    async def load_plugin(self, plugin_path: str) -> PluginMetadata:
        """Load a plugin from file path"""
        try:
            plugin_file = Path(plugin_path)
            if not plugin_file.exists():
                raise FileNotFoundError(f"Plugin file not found: {plugin_path}")
            
            # Load plugin metadata
            metadata = await self._load_plugin_metadata(plugin_file)
            
            # Load plugin module
            plugin_module = await self._load_plugin_module(plugin_file)
            
            # Initialize plugin
            plugin_instance = await self._initialize_plugin(plugin_module, metadata)
            
            # Register plugin
            await self._register_plugin(metadata, plugin_instance)
            
            # Update metadata
            metadata.status = PluginStatus.LOADED
            metadata.load_time = time.time()
            
            self.loaded_plugins[metadata.name] = metadata
            self.plugin_instances[metadata.name] = plugin_instance
            
            logger.info(f"Plugin loaded successfully: {metadata.name} v{metadata.version}")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_path}: {e}")
            metadata = PluginMetadata(
                name=os.path.basename(plugin_path),
                version="unknown",
                description="",
                plugin_type=PluginType.TOOL,
                author="unknown",
                dependencies=[],
                config_schema={},
                entry_point="",
                load_time=time.time(),
                status=PluginStatus.ERROR
            )
            metadata.status = PluginStatus.ERROR
            return metadata
    
    async def _load_plugin_metadata(self, plugin_file: Path) -> PluginMetadata:
        """Load plugin metadata from file"""
        # Try to load from plugin.yaml first
        metadata_file = plugin_file.parent / "plugin.yaml"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata_dict = yaml.safe_load(f)
        else:
            # Try to load from plugin.json
            metadata_file = plugin_file.parent / "plugin.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata_dict = json.load(f)
            else:
                # Default metadata
                metadata_dict = {
                    "name": plugin_file.stem,
                    "version": "1.0.0",
                    "description": f"Plugin {plugin_file.stem}",
                    "plugin_type": "tool",
                    "author": "unknown",
                    "dependencies": [],
                    "config_schema": {},
                    "entry_point": "main"
                }
        
        return PluginMetadata(
            name=metadata_dict["name"],
            version=metadata_dict["version"],
            description=metadata_dict["description"],
            plugin_type=PluginType(metadata_dict["plugin_type"]),
            author=metadata_dict["author"],
            dependencies=metadata_dict.get("dependencies", []),
            config_schema=metadata_dict.get("config_schema", {}),
            entry_point=metadata_dict.get("entry_point", "main"),
            load_time=time.time(),
            status=PluginStatus.LOADING
        )
    
    async def _load_plugin_module(self, plugin_file: Path):
        """Load plugin module"""
        # Add plugin directory to Python path
        plugin_dir = str(plugin_file.parent)
        if plugin_dir not in os.sys.path:
            os.sys.path.insert(0, plugin_dir)
        
        # Import plugin module
        module_name = plugin_file.stem
        try:
            # Remove module if already loaded
            if module_name in importlib.sys.modules:
                del importlib.sys.modules[module_name]
            
            module = importlib.import_module(module_name)
            return module
        except Exception as e:
            raise ImportError(f"Failed to import plugin module {module_name}: {e}")
    
    async def _initialize_plugin(self, plugin_module, metadata: PluginMetadata):
        """Initialize plugin instance"""
        try:
            # Get plugin class or function
            if hasattr(plugin_module, metadata.entry_point):
                plugin_class = getattr(plugin_module, metadata.entry_point)
            else:
                plugin_class = getattr(plugin_module, "main", None)
            
            if not plugin_class:
                raise ValueError(f"Plugin entry point not found: {metadata.entry_point}")
            
            # Initialize plugin
            if callable(plugin_class):
                if asyncio.iscoroutinefunction(plugin_class):
                    plugin_instance = await plugin_class()
                else:
                    plugin_instance = plugin_class()
            else:
                plugin_instance = plugin_class
            
            return plugin_instance
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize plugin {metadata.name}: {e}")
    
    async def _register_plugin(self, metadata: PluginMetadata, plugin_instance: Any):
        """Register plugin in appropriate registry"""
        if metadata.plugin_type == PluginType.TOOL:
            if hasattr(plugin_instance, 'execute'):
                self.tool_plugins[metadata.name] = plugin_instance.execute
            else:
                logger.warning(f"Tool plugin {metadata.name} missing execute method")
        
        elif metadata.plugin_type == PluginType.HANDLER:
            if hasattr(plugin_instance, 'handle'):
                self.handler_plugins[metadata.name] = plugin_instance.handle
            else:
                logger.warning(f"Handler plugin {metadata.name} missing handle method")
        
        elif metadata.plugin_type == PluginType.MIDDLEWARE:
            if hasattr(plugin_instance, 'process'):
                self.middleware_plugins.append(plugin_instance.process)
            else:
                logger.warning(f"Middleware plugin {metadata.name} missing process method")
        
        elif metadata.plugin_type == PluginType.EXPANSION_PACK:
            self.expansion_plugins[metadata.name] = plugin_instance
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin"""
        try:
            if plugin_name not in self.loaded_plugins:
                return False
            
            metadata = self.loaded_plugins[plugin_name]
            
            # Unregister plugin
            if metadata.plugin_type == PluginType.TOOL:
                self.tool_plugins.pop(plugin_name, None)
            elif metadata.plugin_type == PluginType.HANDLER:
                self.handler_plugins.pop(plugin_name, None)
            elif metadata.plugin_type == PluginType.MIDDLEWARE:
                # Remove from middleware list
                for i, middleware in enumerate(self.middleware_plugins):
                    if hasattr(middleware, '__self__') and middleware.__self__.__class__.__name__ == plugin_name:
                        self.middleware_plugins.pop(i)
                        break
            elif metadata.plugin_type == PluginType.EXPANSION_PACK:
                self.expansion_plugins.pop(plugin_name, None)
            
            # Clean up plugin instance
            if plugin_name in self.plugin_instances:
                plugin_instance = self.plugin_instances[plugin_name]
                if hasattr(plugin_instance, 'cleanup'):
                    if asyncio.iscoroutinefunction(plugin_instance.cleanup):
                        await plugin_instance.cleanup()
                    else:
                        plugin_instance.cleanup()
                
                del self.plugin_instances[plugin_name]
            
            # Update metadata
            metadata.status = PluginStatus.UNLOADED
            
            logger.info(f"Plugin unloaded: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False
    
    def get_loaded_plugins(self) -> List[PluginMetadata]:
        """Get list of loaded plugins"""
        return list(self.loaded_plugins.values())
    
    def get_plugin_tools(self) -> Dict[str, Callable]:
        """Get plugin tools"""
        return self.tool_plugins.copy()
    
    def get_plugin_handlers(self) -> Dict[str, Callable]:
        """Get plugin handlers"""
        return self.handler_plugins.copy()


class HotReloadManager:
    """Hot-reload configuration manager"""
    
    def __init__(self, config_directory: str = "config"):
        self.config_directory = Path(config_directory)
        self.config_directory.mkdir(exist_ok=True)
        
        self.config_files: Dict[str, Dict[str, Any]] = {}
        self.config_watchers: Dict[str, Observer] = {}
        self.reload_callbacks: List[Callable] = []
        
        # Start watching for changes
        self._start_config_watching()
    
    def _start_config_watching(self):
        """Start watching configuration files for changes"""
        class ConfigHandler(FileSystemEventHandler):
            def __init__(self, manager):
                self.manager = manager
            
            def on_modified(self, event):
                if not event.is_directory:
                    self.manager._handle_config_change(event.src_path)
        
        handler = ConfigHandler(self)
        observer = Observer()
        observer.schedule(handler, str(self.config_directory), recursive=True)
        observer.start()
        
        self.config_watchers["config"] = observer
        logger.info("Configuration file watching started")
    
    def _handle_config_change(self, file_path: str):
        """Handle configuration file change"""
        try:
            config_file = Path(file_path)
            if config_file.suffix in ['.yaml', '.yml', '.json']:
                logger.info(f"Configuration file changed: {file_path}")
                asyncio.create_task(self._reload_config(file_path))
        except Exception as e:
            logger.error(f"Error handling config change {file_path}: {e}")
    
    async def _reload_config(self, file_path: str):
        """Reload configuration file"""
        try:
            config_file = Path(file_path)
            
            # Load new configuration
            if config_file.suffix in ['.yaml', '.yml']:
                with open(config_file, 'r') as f:
                    new_config = yaml.safe_load(f)
            elif config_file.suffix == '.json':
                with open(config_file, 'r') as f:
                    new_config = json.load(f)
            else:
                return
            
            # Update configuration
            self.config_files[file_path] = new_config
            
            # Notify callbacks
            for callback in self.reload_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(file_path, new_config)
                    else:
                        callback(file_path, new_config)
                except Exception as e:
                    logger.error(f"Config reload callback error: {e}")
            
            logger.info(f"Configuration reloaded: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to reload config {file_path}: {e}")
    
    def add_reload_callback(self, callback: Callable):
        """Add configuration reload callback"""
        self.reload_callbacks.append(callback)
        logger.info("Configuration reload callback added")
    
    def load_config(self, file_path: str) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            config_file = Path(file_path)
            
            if config_file.suffix in ['.yaml', '.yml']:
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
            elif config_file.suffix == '.json':
                with open(config_file, 'r') as f:
                    config = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {config_file.suffix}")
            
            self.config_files[file_path] = config
            return config
            
        except Exception as e:
            logger.error(f"Failed to load config {file_path}: {e}")
            return {}
    
    def get_config(self, file_path: str) -> Dict[str, Any]:
        """Get configuration from memory"""
        return self.config_files.get(file_path, {})


class SmartRouter:
    """Smart routing system for tools"""
    
    def __init__(self):
        self.routing_rules: List[Dict[str, Any]] = []
        self.route_cache: Dict[str, str] = {}
        self.route_stats: Dict[str, Dict[str, int]] = {}
    
    def add_routing_rule(self, condition: Callable, target: str, priority: int = 100):
        """Add a routing rule"""
        rule = {
            "condition": condition,
            "target": target,
            "priority": priority,
            "hits": 0
        }
        self.routing_rules.append(rule)
        self.routing_rules.sort(key=lambda x: x["priority"], reverse=True)
        logger.info(f"Routing rule added: {target} (priority: {priority})")
    
    def route_request(self, request: Dict[str, Any]) -> str:
        """Route request to appropriate handler"""
        # Check cache first
        cache_key = self._generate_cache_key(request)
        if cache_key in self.route_cache:
            return self.route_cache[cache_key]
        
        # Find matching rule
        for rule in self.routing_rules:
            try:
                if rule["condition"](request):
                    rule["hits"] += 1
                    target = rule["target"]
                    
                    # Cache result
                    self.route_cache[cache_key] = target
                    
                    # Update stats
                    if target not in self.route_stats:
                        self.route_stats[target] = {"requests": 0, "cache_hits": 0}
                    self.route_stats[target]["requests"] += 1
                    
                    return target
            except Exception as e:
                logger.error(f"Routing rule error: {e}")
                continue
        
        # Default route
        return "default"
    
    def _generate_cache_key(self, request: Dict[str, Any]) -> str:
        """Generate cache key for request"""
        # Simple hash of request attributes
        key_data = {
            "tool": request.get("tool_name", ""),
            "client": request.get("client_type", ""),
            "project": request.get("project_type", "")
        }
        return str(hash(json.dumps(key_data, sort_keys=True)))
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        return {
            "rules": [
                {
                    "target": rule["target"],
                    "priority": rule["priority"],
                    "hits": rule["hits"]
                }
                for rule in self.routing_rules
            ],
            "stats": self.route_stats.copy(),
            "cache_size": len(self.route_cache)
        }


class ABTestingFramework:
    """A/B testing framework for tools"""
    
    def __init__(self):
        self.experiments: Dict[str, Dict[str, Any]] = {}
        self.participants: Dict[str, str] = {}  # user_id -> experiment_id
        self.results: Dict[str, Dict[str, Any]] = {}
    
    def create_experiment(self, experiment_id: str, variants: List[Dict[str, Any]], 
                         traffic_split: List[float] = None) -> bool:
        """Create an A/B test experiment"""
        if traffic_split is None:
            traffic_split = [1.0 / len(variants)] * len(variants)
        
        if len(variants) != len(traffic_split):
            raise ValueError("Variants and traffic split must have same length")
        
        if sum(traffic_split) != 1.0:
            raise ValueError("Traffic split must sum to 1.0")
        
        self.experiments[experiment_id] = {
            "variants": variants,
            "traffic_split": traffic_split,
            "start_time": time.time(),
            "status": "active",
            "participants": 0
        }
        
        logger.info(f"A/B test experiment created: {experiment_id}")
        return True
    
    def assign_variant(self, experiment_id: str, user_id: str) -> str:
        """Assign user to experiment variant"""
        if experiment_id not in self.experiments:
            return "control"
        
        experiment = self.experiments[experiment_id]
        
        # Check if user already assigned
        if user_id in self.participants:
            return self.participants[user_id]
        
        # Assign variant based on traffic split
        import random
        random.seed(hash(user_id + experiment_id))
        rand = random.random()
        
        cumulative = 0.0
        for i, split in enumerate(experiment["traffic_split"]):
            cumulative += split
            if rand <= cumulative:
                variant = experiment["variants"][i]["name"]
                self.participants[user_id] = variant
                experiment["participants"] += 1
                return variant
        
        return "control"
    
    def record_result(self, experiment_id: str, user_id: str, result: Dict[str, Any]):
        """Record experiment result"""
        if experiment_id not in self.experiments:
            return
        
        variant = self.participants.get(user_id, "control")
        
        if experiment_id not in self.results:
            self.results[experiment_id] = {}
        
        if variant not in self.results[experiment_id]:
            self.results[experiment_id][variant] = {
                "participants": 0,
                "results": []
            }
        
        self.results[experiment_id][variant]["participants"] += 1
        self.results[experiment_id][variant]["results"].append(result)
    
    def get_experiment_results(self, experiment_id: str) -> Dict[str, Any]:
        """Get experiment results"""
        if experiment_id not in self.experiments:
            return {}
        
        experiment = self.experiments[experiment_id]
        results = self.results.get(experiment_id, {})
        
        return {
            "experiment_id": experiment_id,
            "status": experiment["status"],
            "start_time": experiment["start_time"],
            "total_participants": experiment["participants"],
            "variants": results
        }


class VersionManager:
    """Version management for tools and plugins"""
    
    def __init__(self):
        self.versions: Dict[str, List[Dict[str, Any]]] = {}
        self.current_versions: Dict[str, str] = {}
        self.deprecation_schedule: Dict[str, Dict[str, Any]] = {}
    
    def register_version(self, tool_name: str, version: str, metadata: Dict[str, Any]):
        """Register a tool version"""
        if tool_name not in self.versions:
            self.versions[tool_name] = []
        
        version_info = {
            "version": version,
            "metadata": metadata,
            "registration_time": time.time(),
            "status": "active"
        }
        
        self.versions[tool_name].append(version_info)
        self.versions[tool_name].sort(key=lambda x: x["version"], reverse=True)
        
        # Set as current if first version or explicitly set
        if len(self.versions[tool_name]) == 1 or metadata.get("is_current", False):
            self.current_versions[tool_name] = version
        
        logger.info(f"Version registered: {tool_name} v{version}")
    
    def set_current_version(self, tool_name: str, version: str) -> bool:
        """Set current version for a tool"""
        if tool_name not in self.versions:
            return False
        
        # Check if version exists
        version_exists = any(v["version"] == version for v in self.versions[tool_name])
        if not version_exists:
            return False
        
        self.current_versions[tool_name] = version
        logger.info(f"Current version set: {tool_name} v{version}")
        return True
    
    def schedule_deprecation(self, tool_name: str, version: str, 
                           deprecation_date: str, removal_date: str):
        """Schedule version deprecation"""
        self.deprecation_schedule[f"{tool_name}:{version}"] = {
            "deprecation_date": deprecation_date,
            "removal_date": removal_date,
            "status": "scheduled"
        }
        
        logger.info(f"Deprecation scheduled: {tool_name} v{version}")
    
    def get_current_version(self, tool_name: str) -> Optional[str]:
        """Get current version for a tool"""
        return self.current_versions.get(tool_name)
    
    def get_version_history(self, tool_name: str) -> List[Dict[str, Any]]:
        """Get version history for a tool"""
        return self.versions.get(tool_name, [])
    
    def get_deprecation_status(self, tool_name: str, version: str) -> Dict[str, Any]:
        """Get deprecation status for a version"""
        key = f"{tool_name}:{version}"
        return self.deprecation_schedule.get(key, {"status": "active"})


class PluginArchitectureManager:
    """Main plugin architecture manager"""
    
    def __init__(self):
        self.plugin_loader = PluginLoader()
        self.hot_reload_manager = HotReloadManager()
        self.smart_router = SmartRouter()
        self.ab_testing = ABTestingFramework()
        self.version_manager = VersionManager()
        
        # Start hot-reload monitoring
        self._start_hot_reload_monitoring()
    
    def _start_hot_reload_monitoring(self):
        """Start hot-reload monitoring"""
        async def plugin_reload_callback(file_path: str, config: Dict[str, Any]):
            """Handle plugin configuration reload"""
            if "plugins" in config:
                await self._reload_plugin_configs(config["plugins"])
        
        self.hot_reload_manager.add_reload_callback(plugin_reload_callback)
        logger.info("Hot-reload monitoring started")
    
    async def _reload_plugin_configs(self, plugin_configs: Dict[str, Any]):
        """Reload plugin configurations"""
        for plugin_name, config in plugin_configs.items():
            if plugin_name in self.plugin_loader.loaded_plugins:
                # Update plugin configuration
                self.plugin_loader.plugin_configs[plugin_name] = PluginConfig(**config)
                logger.info(f"Plugin configuration reloaded: {plugin_name}")
    
    async def load_all_plugins(self, plugin_directory: str = "plugins"):
        """Load all plugins from directory"""
        plugin_dir = Path(plugin_directory)
        if not plugin_dir.exists():
            logger.warning(f"Plugin directory not found: {plugin_directory}")
            return
        
        # Find all plugin files
        plugin_files = []
        for file_path in plugin_dir.rglob("*.py"):
            if file_path.name != "__init__.py":
                plugin_files.append(str(file_path))
        
        # Load plugins
        for plugin_file in plugin_files:
            try:
                await self.plugin_loader.load_plugin(plugin_file)
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_file}: {e}")
        
        logger.info(f"Loaded {len(self.plugin_loader.loaded_plugins)} plugins")
    
    def get_plugin_architecture_status(self) -> Dict[str, Any]:
        """Get plugin architecture status"""
        return {
            "plugins": {
                "loaded": len(self.plugin_loader.loaded_plugins),
                "tools": len(self.plugin_loader.tool_plugins),
                "handlers": len(self.plugin_loader.handler_plugins),
                "middleware": len(self.plugin_loader.middleware_plugins),
                "expansion_packs": len(self.plugin_loader.expansion_plugins)
            },
            "routing": self.smart_router.get_routing_stats(),
            "experiments": {
                "active": len([e for e in self.ab_testing.experiments.values() if e["status"] == "active"]),
                "total": len(self.ab_testing.experiments)
            },
            "versions": {
                "tools": len(self.version_manager.current_versions),
                "total_versions": sum(len(versions) for versions in self.version_manager.versions.values())
            }
        }
