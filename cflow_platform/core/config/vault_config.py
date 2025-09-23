"""
Vault-aware Configuration System for BMAD

This module provides configuration access that prioritizes Vault over environment variables.
"""

import os
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

from ..vault_integration import get_vault_integration

# Load environment variables from project root
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")


class VaultConfig:
    """Vault-aware configuration manager."""
    
    def __init__(self):
        self.vault = get_vault_integration()
        self._config_cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def get_config_value(
        self, 
        key: str, 
        category: Optional[str] = None,
        fallback_to_env: bool = True
    ) -> Optional[str]:
        """Get configuration value from Vault with fallback to environment."""
        try:
            # Try Vault first if category is specified
            if category:
                vault_result = await self.vault.get_secret_category(category)
                if vault_result.get("success"):
                    secrets = vault_result.get("secrets", {})
                    value = secrets.get(key.lower())
                    if value:
                        return value
            
            # Fallback to environment variables
            if fallback_to_env:
                return os.getenv(key)
            
            return None
            
        except Exception as e:
            print(f"[WARN] Failed to get config value for {key}: {e}")
            if fallback_to_env:
                return os.getenv(key)
            return None
    
    def get_config_value_sync(
        self, 
        key: str, 
        category: Optional[str] = None,
        fallback_to_env: bool = True
    ) -> Optional[str]:
        """Get configuration value synchronously from Vault with fallback to environment."""
        try:
            import asyncio
            
            # Try to get from Vault synchronously if possible
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, use environment fallback
                if fallback_to_env:
                    return os.getenv(key)
                return None
            else:
                # Run async function in new event loop
                return loop.run_until_complete(self.get_config_value(key, category, fallback_to_env))
                
        except Exception as e:
            print(f"[WARN] Failed to get config value synchronously for {key}: {e}")
            if fallback_to_env:
                return os.getenv(key)
            return None
    
    async def get_supabase_config(self) -> Dict[str, Optional[str]]:
        """Get Supabase configuration from Vault with fallback to environment."""
        try:
            vault_result = await self.vault.get_supabase_config()
            
            if vault_result.get("success"):
                config = vault_result.get("config", {})
                return {
                    "url": config.get("url"),
                    "anon_key": config.get("anon_key"),
                    "service_role_key": config.get("service_role_key"),
                    "project_ref": config.get("project_ref"),
                    "db_pass": config.get("db_pass")
                }
            else:
                # Fallback to environment variables
                return {
                    "url": os.getenv("SUPABASE_URL"),
                    "anon_key": os.getenv("SUPABASE_ANON_KEY"),
                    "service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
                    "project_ref": os.getenv("SUPABASE_PROJECT_REF"),
                    "db_pass": os.getenv("SUPABASE_DB_PASS")
                }
                
        except Exception as e:
            print(f"[WARN] Failed to get Supabase config from Vault: {e}")
            # Fallback to environment variables
            return {
                "url": os.getenv("SUPABASE_URL"),
                "anon_key": os.getenv("SUPABASE_ANON_KEY"),
                "service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
                "project_ref": os.getenv("SUPABASE_PROJECT_REF"),
                "db_pass": os.getenv("SUPABASE_DB_PASS")
            }
    
    async def get_openai_config(self) -> Dict[str, Optional[str]]:
        """Get OpenAI configuration from Vault with fallback to environment."""
        try:
            vault_result = await self.vault.get_secret_category("openai")
            
            if vault_result.get("success"):
                secrets = vault_result.get("secrets", {})
                return {
                    "api_key": secrets.get("openai_api_key"),
                    "organization": secrets.get("openai_organization")
                }
            else:
                # Fallback to environment variables
                return {
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "organization": os.getenv("OPENAI_ORGANIZATION")
                }
                
        except Exception as e:
            print(f"[WARN] Failed to get OpenAI config from Vault: {e}")
            # Fallback to environment variables
            return {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "organization": os.getenv("OPENAI_ORGANIZATION")
            }
    
    async def get_anthropic_config(self) -> Dict[str, Optional[str]]:
        """Get Anthropic configuration from Vault with fallback to environment."""
        try:
            vault_result = await self.vault.get_secret_category("anthropic")
            
            if vault_result.get("success"):
                secrets = vault_result.get("secrets", {})
                return {
                    "api_key": secrets.get("anthropic_api_key")
                }
            else:
                # Fallback to environment variables
                return {
                    "api_key": os.getenv("ANTHROPIC_API_KEY")
                }
                
        except Exception as e:
            print(f"[WARN] Failed to get Anthropic config from Vault: {e}")
            # Fallback to environment variables
            return {
                "api_key": os.getenv("ANTHROPIC_API_KEY")
            }
    
    async def get_github_config(self) -> Dict[str, Optional[str]]:
        """Get GitHub configuration from Vault with fallback to environment."""
        try:
            vault_result = await self.vault.get_secret_category("github")
            
            if vault_result.get("success"):
                secrets = vault_result.get("secrets", {})
                return {
                    "token": secrets.get("github_token"),
                    "username": secrets.get("github_username")
                }
            else:
                # Fallback to environment variables
                return {
                    "token": os.getenv("GITHUB_TOKEN"),
                    "username": os.getenv("GITHUB_USERNAME")
                }
                
        except Exception as e:
            print(f"[WARN] Failed to get GitHub config from Vault: {e}")
            # Fallback to environment variables
            return {
                "token": os.getenv("GITHUB_TOKEN"),
                "username": os.getenv("GITHUB_USERNAME")
            }
    
    async def get_minio_config(self) -> Dict[str, Optional[str]]:
        """Get MinIO configuration from Vault with fallback to environment."""
        try:
            vault_result = await self.vault.get_secret_category("minio")
            
            if vault_result.get("success"):
                secrets = vault_result.get("secrets", {})
                return {
                    "endpoint": secrets.get("minio_endpoint"),
                    "access_key": secrets.get("minio_access_key"),
                    "secret_key": secrets.get("minio_secret_key"),
                    "secure": secrets.get("minio_secure")
                }
            else:
                # Fallback to environment variables
                return {
                    "endpoint": os.getenv("MINIO_ENDPOINT"),
                    "access_key": os.getenv("MINIO_ACCESS_KEY"),
                    "secret_key": os.getenv("MINIO_SECRET_KEY"),
                    "secure": os.getenv("MINIO_SECURE")
                }
                
        except Exception as e:
            print(f"[WARN] Failed to get MinIO config from Vault: {e}")
            # Fallback to environment variables
            return {
                "endpoint": os.getenv("MINIO_ENDPOINT"),
                "access_key": os.getenv("MINIO_ACCESS_KEY"),
                "secret_key": os.getenv("MINIO_SECRET_KEY"),
                "secure": os.getenv("MINIO_SECURE")
            }
    
    async def get_redis_config(self) -> Dict[str, Optional[str]]:
        """Get Redis configuration from Vault with fallback to environment."""
        try:
            vault_result = await self.vault.get_secret_category("redis")
            
            if vault_result.get("success"):
                secrets = vault_result.get("secrets", {})
                return {
                    "url": secrets.get("redis_url"),
                    "password": secrets.get("redis_password")
                }
            else:
                # Fallback to environment variables
                return {
                    "url": os.getenv("REDIS_URL"),
                    "password": os.getenv("REDIS_PASSWORD")
                }
                
        except Exception as e:
            print(f"[WARN] Failed to get Redis config from Vault: {e}")
            # Fallback to environment variables
            return {
                "url": os.getenv("REDIS_URL"),
                "password": os.getenv("REDIS_PASSWORD")
            }


# Global instance
_vault_config = VaultConfig()


def get_vault_config() -> VaultConfig:
    """Get global Vault configuration instance."""
    return _vault_config


# Convenience functions for backward compatibility
async def get_supabase_url() -> Optional[str]:
    """Get Supabase URL from Vault with fallback to environment."""
    config = await _vault_config.get_supabase_config()
    return config.get("url")


async def get_supabase_key(secure: Optional[bool] = None) -> Optional[str]:
    """Get Supabase API key from Vault with fallback to environment."""
    config = await _vault_config.get_supabase_config()
    
    if secure is None:
        secure = is_secure_mode()
    
    if secure:
        return config.get("service_role_key")
    else:
        return config.get("service_role_key") or config.get("anon_key")


async def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key from Vault with fallback to environment."""
    config = await _vault_config.get_openai_config()
    return config.get("api_key")


async def get_anthropic_api_key() -> Optional[str]:
    """Get Anthropic API key from Vault with fallback to environment."""
    config = await _vault_config.get_anthropic_config()
    return config.get("api_key")


async def get_github_token() -> Optional[str]:
    """Get GitHub token from Vault with fallback to environment."""
    config = await _vault_config.get_github_config()
    return config.get("token")


async def get_redis_url() -> Optional[str]:
    """Get Redis URL from Vault with fallback to environment."""
    config = await _vault_config.get_redis_config()
    return config.get("url")


def is_secure_mode() -> bool:
    """Check if secure mode is enabled."""
    val = os.getenv("CFLOW_SECURE_MODE", "").strip().lower()
    return val in {"1", "true", "yes", "on"}


# Synchronous fallback functions for immediate compatibility
def get_supabase_url_sync() -> Optional[str]:
    """Get Supabase URL synchronously (fallback to environment only)."""
    return os.getenv("SUPABASE_URL")


def get_supabase_key_sync(secure: Optional[bool] = None) -> Optional[str]:
    """Get Supabase API key synchronously (fallback to environment only)."""
    if secure is None:
        secure = is_secure_mode()
    if secure:
        return (
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            or os.getenv("SUPABASE_KEY")
        )
    return (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
    )


def get_openai_api_key_sync() -> Optional[str]:
    """Get OpenAI API key synchronously (fallback to environment only)."""
    return os.getenv("OPENAI_API_KEY")


def get_anthropic_api_key_sync() -> Optional[str]:
    """Get Anthropic API key synchronously (fallback to environment only)."""
    return os.getenv("ANTHROPIC_API_KEY")


def get_github_token_sync() -> Optional[str]:
    """Get GitHub token synchronously (fallback to environment only)."""
    return os.getenv("GITHUB_TOKEN")


def get_redis_url_sync() -> Optional[str]:
    """Get Redis URL synchronously (fallback to environment only)."""
    return os.getenv("REDIS_URL")
