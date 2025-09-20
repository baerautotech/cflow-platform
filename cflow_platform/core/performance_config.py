"""
Performance Configuration Management for WebMCP

This module provides centralized configuration management for all performance-related
settings, including hot-reload capability and environment-based configuration.
"""

import os
import json
import logging
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
import yaml
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class AsyncExecutorConfig:
    """Configuration for async tool executor"""
    max_concurrent: int = 100
    memory_limit_mb: int = 512
    enable_monitoring: bool = True
    queue_timeout_seconds: float = 300.0
    execution_timeout_seconds: float = 30.0
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: float = 60.0
    cleanup_interval_seconds: float = 300.0


@dataclass
class ConnectionPoolConfig:
    """Configuration for connection pools"""
    max_connections: int = 20
    min_connections: int = 5
    max_idle_time_seconds: float = 300.0
    connection_timeout_seconds: float = 10.0
    read_timeout_seconds: float = 30.0
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    enable_pool_reuse: bool = True
    pool_cleanup_interval_seconds: float = 60.0


@dataclass
class StreamingConfig:
    """Configuration for response streaming"""
    max_streams: int = 100
    cleanup_interval_seconds: float = 300.0
    heartbeat_interval_seconds: float = 10.0
    default_timeout_seconds: float = 300.0
    buffer_size: int = 100
    max_subscribers_per_stream: int = 50


@dataclass
class PerformanceMonitorConfig:
    """Configuration for performance monitoring"""
    retention_hours: int = 24
    max_points_per_metric: int = 1000
    system_monitoring_interval_seconds: float = 10.0
    health_check_interval_seconds: float = 30.0
    metrics_export_interval_seconds: float = 3600.0
    enable_system_metrics: bool = True
    enable_health_checks: bool = True
    enable_custom_metrics: bool = True


@dataclass
class CachingConfig:
    """Configuration for caching"""
    enable_response_caching: bool = True
    default_ttl_seconds: float = 300.0  # 5 minutes
    max_cache_size_mb: int = 100
    cache_cleanup_interval_seconds: float = 600.0
    enable_intelligent_caching: bool = True
    cache_compression: bool = True


@dataclass
class LoadBalancingConfig:
    """Configuration for load balancing"""
    enable_load_balancing: bool = True
    max_workers: int = 10
    worker_timeout_seconds: float = 30.0
    health_check_interval_seconds: float = 15.0
    auto_scaling_enabled: bool = True
    min_workers: int = 2
    max_workers: int = 20
    scale_up_threshold: float = 0.8
    scale_down_threshold: float = 0.3


@dataclass
class PerformanceConfig:
    """Complete performance configuration"""
    async_executor: AsyncExecutorConfig = field(default_factory=AsyncExecutorConfig)
    connection_pool: ConnectionPoolConfig = field(default_factory=ConnectionPoolConfig)
    streaming: StreamingConfig = field(default_factory=StreamingConfig)
    performance_monitor: PerformanceMonitorConfig = field(default_factory=PerformanceMonitorConfig)
    caching: CachingConfig = field(default_factory=CachingConfig)
    load_balancing: LoadBalancingConfig = field(default_factory=LoadBalancingConfig)
    
    # Global settings
    environment: str = "development"
    debug_mode: bool = False
    hot_reload_enabled: bool = True
    config_file_path: Optional[str] = None
    last_updated: Optional[datetime] = None


class PerformanceConfigManager:
    """
    Manages performance configuration with hot-reload capability.
    
    Features:
    - Environment-based configuration
    - Hot-reload on file changes
    - Validation and defaults
    - Export/import capabilities
    - Runtime configuration updates
    """
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_path()
        self._config: PerformanceConfig = PerformanceConfig()
        self._watchers: list = []
        self._file_watcher_task: Optional[Any] = None
        self._last_file_mtime: Optional[float] = None
        
        # Load initial configuration
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        # Try environment variable first
        env_path = os.environ.get("CFLOW_PERFORMANCE_CONFIG")
        if env_path:
            return env_path
        
        # Try common locations
        possible_paths = [
            "cflow_platform/config/performance.yaml",
            "config/performance.yaml",
            ".cerebraflow/performance.yaml",
            "performance.yaml"
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                return path
        
        # Return default path
        return "cflow_platform/config/performance.yaml"
    
    def _load_config(self):
        """Load configuration from file or environment"""
        try:
            if Path(self.config_file).exists():
                self._load_from_file()
            else:
                logger.info(f"Config file {self.config_file} not found, using defaults")
                self._load_from_environment()
            
            self._config.last_updated = datetime.now()
            self._notify_watchers()
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._load_from_environment()
    
    def _load_from_file(self):
        """Load configuration from YAML file"""
        with open(self.config_file, 'r') as f:
            if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        # Update configuration with loaded data
        self._update_config_from_dict(data)
        logger.info(f"Loaded configuration from {self.config_file}")
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        # Async executor config
        self._config.async_executor.max_concurrent = int(
            os.environ.get("CFLOW_MAX_CONCURRENT", self._config.async_executor.max_concurrent)
        )
        self._config.async_executor.memory_limit_mb = int(
            os.environ.get("CFLOW_MEMORY_LIMIT_MB", self._config.async_executor.memory_limit_mb)
        )
        self._config.async_executor.enable_monitoring = (
            os.environ.get("CFLOW_ENABLE_MONITORING", "true").lower() == "true"
        )
        
        # Connection pool config
        self._config.connection_pool.max_connections = int(
            os.environ.get("CFLOW_MAX_CONNECTIONS", self._config.connection_pool.max_connections)
        )
        self._config.connection_pool.connection_timeout_seconds = float(
            os.environ.get("CFLOW_CONNECTION_TIMEOUT", self._config.connection_pool.connection_timeout_seconds)
        )
        
        # Streaming config
        self._config.streaming.max_streams = int(
            os.environ.get("CFLOW_MAX_STREAMS", self._config.streaming.max_streams)
        )
        self._config.streaming.default_timeout_seconds = float(
            os.environ.get("CFLOW_STREAM_TIMEOUT", self._config.streaming.default_timeout_seconds)
        )
        
        # Performance monitor config
        self._config.performance_monitor.retention_hours = int(
            os.environ.get("CFLOW_METRICS_RETENTION_HOURS", self._config.performance_monitor.retention_hours)
        )
        self._config.performance_monitor.enable_system_metrics = (
            os.environ.get("CFLOW_ENABLE_SYSTEM_METRICS", "true").lower() == "true"
        )
        
        # Caching config
        self._config.caching.enable_response_caching = (
            os.environ.get("CFLOW_ENABLE_CACHING", "true").lower() == "true"
        )
        self._config.caching.default_ttl_seconds = float(
            os.environ.get("CFLOW_CACHE_TTL", self._config.caching.default_ttl_seconds)
        )
        
        # Global settings
        self._config.environment = os.environ.get("CFLOW_ENV", "development")
        self._config.debug_mode = (
            os.environ.get("CFLOW_DEBUG", "false").lower() == "true"
        )
        self._config.hot_reload_enabled = (
            os.environ.get("CFLOW_HOT_RELOAD", "true").lower() == "true"
        )
        
        logger.info("Loaded configuration from environment variables")
    
    def _update_config_from_dict(self, data: Dict[str, Any]):
        """Update configuration from dictionary"""
        # Update async executor config
        if "async_executor" in data:
            for key, value in data["async_executor"].items():
                if hasattr(self._config.async_executor, key):
                    setattr(self._config.async_executor, key, value)
        
        # Update connection pool config
        if "connection_pool" in data:
            for key, value in data["connection_pool"].items():
                if hasattr(self._config.connection_pool, key):
                    setattr(self._config.connection_pool, key, value)
        
        # Update streaming config
        if "streaming" in data:
            for key, value in data["streaming"].items():
                if hasattr(self._config.streaming, key):
                    setattr(self._config.streaming, key, value)
        
        # Update performance monitor config
        if "performance_monitor" in data:
            for key, value in data["performance_monitor"].items():
                if hasattr(self._config.performance_monitor, key):
                    setattr(self._config.performance_monitor, key, value)
        
        # Update caching config
        if "caching" in data:
            for key, value in data["caching"].items():
                if hasattr(self._config.caching, key):
                    setattr(self._config.caching, key, value)
        
        # Update load balancing config
        if "load_balancing" in data:
            for key, value in data["load_balancing"].items():
                if hasattr(self._config.load_balancing, key):
                    setattr(self._config.load_balancing, key, value)
        
        # Update global settings
        for key, value in data.items():
            if hasattr(self._config, key) and key not in [
                "async_executor", "connection_pool", "streaming",
                "performance_monitor", "caching", "load_balancing"
            ]:
                setattr(self._config, key, value)
    
    def get_config(self) -> PerformanceConfig:
        """Get current configuration"""
        return self._config
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration at runtime"""
        self._update_config_from_dict(updates)
        self._config.last_updated = datetime.now()
        self._notify_watchers()
        
        # Save to file if configured
        if self.config_file and Path(self.config_file).exists():
            self.save_config()
        
        logger.info("Configuration updated at runtime")
    
    def save_config(self, file_path: Optional[str] = None):
        """Save current configuration to file"""
        save_path = file_path or self.config_file
        
        # Ensure directory exists
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dictionary
        config_dict = asdict(self._config)
        
        # Remove non-serializable fields
        config_dict.pop("last_updated", None)
        
        # Save as YAML
        with open(save_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        
        logger.info(f"Configuration saved to {save_path}")
    
    def watch_config_changes(self, callback):
        """Register a callback for configuration changes"""
        self._watchers.append(callback)
        logger.debug(f"Registered config watcher: {callback.__name__}")
    
    def unwatch_config_changes(self, callback):
        """Unregister a configuration change callback"""
        if callback in self._watchers:
            self._watchers.remove(callback)
            logger.debug(f"Unregistered config watcher: {callback.__name__}")
    
    def _notify_watchers(self):
        """Notify all watchers of configuration changes"""
        for callback in self._watchers:
            try:
                callback(self._config)
            except Exception as e:
                logger.error(f"Config watcher callback failed: {e}")
    
    async def start_file_watcher(self):
        """Start file watcher for hot-reload"""
        if not self._config.hot_reload_enabled:
            return
        
        import asyncio
        
        async def _watch_file():
            while True:
                try:
                    if Path(self.config_file).exists():
                        current_mtime = Path(self.config_file).stat().st_mtime
                        
                        if self._last_file_mtime is None:
                            self._last_file_mtime = current_mtime
                        elif current_mtime > self._last_file_mtime:
                            logger.info(f"Configuration file changed, reloading...")
                            self._load_config()
                            self._last_file_mtime = current_mtime
                    
                    await asyncio.sleep(1.0)  # Check every second
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"File watcher error: {e}")
                    await asyncio.sleep(5.0)  # Wait longer on error
        
        self._file_watcher_task = asyncio.create_task(_watch_file())
        logger.info("Started configuration file watcher")
    
    async def stop_file_watcher(self):
        """Stop file watcher"""
        if self._file_watcher_task:
            self._file_watcher_task.cancel()
            self._file_watcher_task = None
            logger.info("Stopped configuration file watcher")
    
    def export_config(self, format: str = "yaml") -> str:
        """Export configuration in specified format"""
        config_dict = asdict(self._config)
        config_dict.pop("last_updated", None)
        
        if format.lower() == "json":
            return json.dumps(config_dict, indent=2, default=str)
        elif format.lower() in ["yaml", "yml"]:
            return yaml.dump(config_dict, default_flow_style=False, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def validate_config(self) -> Dict[str, list]:
        """Validate current configuration and return any issues"""
        issues = {
            "errors": [],
            "warnings": []
        }
        
        # Validate async executor config
        if self._config.async_executor.max_concurrent <= 0:
            issues["errors"].append("max_concurrent must be positive")
        
        if self._config.async_executor.memory_limit_mb <= 0:
            issues["errors"].append("memory_limit_mb must be positive")
        
        if self._config.async_executor.max_concurrent > 1000:
            issues["warnings"].append("max_concurrent > 1000 may cause resource issues")
        
        # Validate connection pool config
        if self._config.connection_pool.max_connections <= 0:
            issues["errors"].append("max_connections must be positive")
        
        if self._config.connection_pool.min_connections > self._config.connection_pool.max_connections:
            issues["errors"].append("min_connections cannot exceed max_connections")
        
        # Validate streaming config
        if self._config.streaming.max_streams <= 0:
            issues["errors"].append("max_streams must be positive")
        
        if self._config.streaming.default_timeout_seconds <= 0:
            issues["errors"].append("default_timeout_seconds must be positive")
        
        # Validate performance monitor config
        if self._config.performance_monitor.retention_hours <= 0:
            issues["errors"].append("retention_hours must be positive")
        
        if self._config.performance_monitor.max_points_per_metric <= 0:
            issues["errors"].append("max_points_per_metric must be positive")
        
        # Validate caching config
        if self._config.caching.default_ttl_seconds <= 0:
            issues["errors"].append("default_ttl_seconds must be positive")
        
        if self._config.caching.max_cache_size_mb <= 0:
            issues["errors"].append("max_cache_size_mb must be positive")
        
        return issues


# Global configuration manager
_config_manager: Optional[PerformanceConfigManager] = None


def get_config_manager() -> PerformanceConfigManager:
    """Get the global configuration manager"""
    global _config_manager
    if _config_manager is None:
        _config_manager = PerformanceConfigManager()
    return _config_manager


def get_performance_config() -> PerformanceConfig:
    """Get current performance configuration"""
    return get_config_manager().get_config()


def update_performance_config(updates: Dict[str, Any]):
    """Update performance configuration"""
    get_config_manager().update_config(updates)


def watch_performance_config(callback):
    """Watch for performance configuration changes"""
    get_config_manager().watch_config_changes(callback)


def create_default_config_file(file_path: str = "cflow_platform/config/performance.yaml"):
    """Create a default configuration file"""
    config = PerformanceConfig()
    manager = PerformanceConfigManager()
    manager._config = config
    manager.save_config(file_path)
    
    logger.info(f"Created default configuration file: {file_path}")
    return file_path
