"""
Feature Flags Management for WebMCP Server

This module provides feature flag management for controlling BMAD tool routing
and enabling gradual migration from local to cluster execution.
"""

import os
import logging
from typing import Dict, Any, Optional, Set
from enum import Enum
import json

logger = logging.getLogger(__name__)


class FeatureFlagType(Enum):
    """Types of feature flags."""
    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    USER_LIST = "user_list"


class FeatureFlag:
    """Represents a single feature flag."""
    
    def __init__(self, name: str, flag_type: FeatureFlagType, default_value: Any = False):
        """
        Initialize a feature flag.
        
        Args:
            name: Name of the feature flag
            flag_type: Type of the feature flag
            default_value: Default value for the flag
        """
        self.name = name
        self.flag_type = flag_type
        self.default_value = default_value
        self.enabled = default_value
        self.rollout_percentage = 100
        self.enabled_users: Set[str] = set()
        self.disabled_users: Set[str] = set()
        self.description = ""
        self.last_updated = None
    
    def is_enabled_for_user(self, user_id: str) -> bool:
        """
        Check if the flag is enabled for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if the flag is enabled for the user
        """
        # Check if user is explicitly disabled
        if user_id in self.disabled_users:
            return False
        
        # Check if user is explicitly enabled
        if user_id in self.enabled_users:
            return True
        
        # For boolean flags, return the enabled state
        if self.flag_type == FeatureFlagType.BOOLEAN:
            return self.enabled
        
        # For percentage flags, use hash-based rollout
        if self.flag_type == FeatureFlagType.PERCENTAGE:
            if not self.enabled:
                return False
            
            # Use hash of user_id for consistent rollout
            user_hash = hash(user_id) % 100
            return user_hash < self.rollout_percentage
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert flag to dictionary."""
        return {
            "name": self.name,
            "type": self.flag_type.value,
            "enabled": self.enabled,
            "rollout_percentage": self.rollout_percentage,
            "enabled_users": list(self.enabled_users),
            "disabled_users": list(self.disabled_users),
            "description": self.description,
            "last_updated": self.last_updated
        }


class FeatureFlags:
    """
    Feature flags manager for WebMCP server.
    
    This class manages feature flags for controlling BMAD tool routing
    and other server behaviors.
    """
    
    def __init__(self):
        """Initialize the feature flags manager."""
        self._flags: Dict[str, FeatureFlag] = {}
        self._config_file = os.getenv("FEATURE_FLAGS_CONFIG", "feature_flags.json")
        self._load_default_flags()
        self._load_from_config()
    
    def _load_default_flags(self) -> None:
        """Load default feature flags."""
        default_flags = [
            FeatureFlag("bmad_cluster_execution", FeatureFlagType.BOOLEAN, True),
            FeatureFlag("bmad_api_health_check", FeatureFlagType.BOOLEAN, True),
            FeatureFlag("bmad_performance_monitoring", FeatureFlagType.BOOLEAN, True),
            FeatureFlag("bmad_fallback_enabled", FeatureFlagType.BOOLEAN, True),
            FeatureFlag("bmad_gradual_rollout", FeatureFlagType.PERCENTAGE, False),
            FeatureFlag("bmad_debug_logging", FeatureFlagType.BOOLEAN, False),
            FeatureFlag("bmad_metrics_collection", FeatureFlagType.BOOLEAN, True),
            FeatureFlag("bmad_circuit_breaker", FeatureFlagType.BOOLEAN, True),
        ]
        
        for flag in default_flags:
            self._flags[flag.name] = flag
    
    def _load_from_config(self) -> None:
        """Load feature flags from configuration file."""
        try:
            if os.path.exists(self._config_file):
                with open(self._config_file, 'r') as f:
                    config = json.load(f)
                
                for flag_name, flag_config in config.items():
                    if flag_name in self._flags:
                        flag = self._flags[flag_name]
                        flag.enabled = flag_config.get("enabled", flag.default_value)
                        flag.rollout_percentage = flag_config.get("rollout_percentage", 100)
                        flag.enabled_users = set(flag_config.get("enabled_users", []))
                        flag.disabled_users = set(flag_config.get("disabled_users", []))
                        flag.description = flag_config.get("description", "")
                        flag.last_updated = flag_config.get("last_updated")
                        
                        logger.info(f"Loaded feature flag: {flag_name} = {flag.enabled}")
        except Exception as e:
            logger.warning(f"Failed to load feature flags config: {e}")
    
    def is_enabled(self, flag_name: str, user_id: Optional[str] = None) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            flag_name: Name of the feature flag
            user_id: Optional user identifier for user-specific flags
            
        Returns:
            True if the flag is enabled
        """
        if flag_name not in self._flags:
            logger.warning(f"Unknown feature flag: {flag_name}")
            return False
        
        flag = self._flags[flag_name]
        
        if user_id:
            return flag.is_enabled_for_user(user_id)
        else:
            return flag.enabled
    
    def set_flag(self, flag_name: str, enabled: bool, user_id: Optional[str] = None) -> None:
        """
        Set a feature flag value.
        
        Args:
            flag_name: Name of the feature flag
            enabled: Whether the flag should be enabled
            user_id: Optional user identifier for user-specific flags
        """
        if flag_name not in self._flags:
            logger.warning(f"Unknown feature flag: {flag_name}")
            return
        
        flag = self._flags[flag_name]
        
        if user_id:
            if enabled:
                flag.enabled_users.add(user_id)
                flag.disabled_users.discard(user_id)
            else:
                flag.disabled_users.add(user_id)
                flag.enabled_users.discard(user_id)
        else:
            flag.enabled = enabled
        
        logger.info(f"Set feature flag {flag_name} = {enabled} for user {user_id or 'all'}")
        self._save_config()
    
    def set_rollout_percentage(self, flag_name: str, percentage: int) -> None:
        """
        Set rollout percentage for a feature flag.
        
        Args:
            flag_name: Name of the feature flag
            percentage: Rollout percentage (0-100)
        """
        if flag_name not in self._flags:
            logger.warning(f"Unknown feature flag: {flag_name}")
            return
        
        if not 0 <= percentage <= 100:
            logger.error(f"Invalid rollout percentage: {percentage}")
            return
        
        flag = self._flags[flag_name]
        flag.rollout_percentage = percentage
        flag.enabled = True  # Enable the flag when setting rollout
        
        logger.info(f"Set rollout percentage for {flag_name} to {percentage}%")
        self._save_config()
    
    def get_flag_info(self, flag_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a feature flag.
        
        Args:
            flag_name: Name of the feature flag
            
        Returns:
            Dictionary with flag information or None if not found
        """
        if flag_name not in self._flags:
            return None
        
        return self._flags[flag_name].to_dict()
    
    def list_flags(self) -> Dict[str, Dict[str, Any]]:
        """
        List all feature flags.
        
        Returns:
            Dictionary with all feature flags
        """
        return {name: flag.to_dict() for name, flag in self._flags.items()}
    
    def _save_config(self) -> None:
        """Save feature flags configuration to file."""
        try:
            config = {}
            for flag_name, flag in self._flags.items():
                config[flag_name] = {
                    "enabled": flag.enabled,
                    "rollout_percentage": flag.rollout_percentage,
                    "enabled_users": list(flag.enabled_users),
                    "disabled_users": list(flag.disabled_users),
                    "description": flag.description,
                    "last_updated": flag.last_updated
                }
            
            with open(self._config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save feature flags config: {e}")
    
    def reload_config(self) -> None:
        """Reload feature flags from configuration file."""
        self._load_from_config()
        logger.info("Feature flags configuration reloaded")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get feature flags statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_flags = len(self._flags)
        enabled_flags = sum(1 for flag in self._flags.values() if flag.enabled)
        percentage_flags = sum(1 for flag in self._flags.values() if flag.flag_type == FeatureFlagType.PERCENTAGE)
        
        return {
            "total_flags": total_flags,
            "enabled_flags": enabled_flags,
            "disabled_flags": total_flags - enabled_flags,
            "percentage_flags": percentage_flags,
            "boolean_flags": total_flags - percentage_flags
        }
