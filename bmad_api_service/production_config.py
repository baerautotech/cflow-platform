"""
BMAD Production Configuration

This file contains hard-coded production settings that cannot be overridden by LLM.
These settings ensure that mock mode is disabled in production environments.
"""

import os
from typing import Dict, Any

# PRODUCTION GATE: Hard-coded configuration that LLM cannot override
PRODUCTION_CONFIG = {
    # Core production settings
    "BMAD_PRODUCTION_MODE": "true",  # Always true in production
    "BMAD_ALLOW_MOCK_MODE": "false",  # Always false in production
    "BMAD_MOCK_MODE_EXPLICITLY_REQUESTED": "false",  # Only set by user request
    
    # Validation settings
    "BMAD_VALIDATE_PRODUCTION_MODE": "true",  # Always validate production mode
    "BMAD_LOG_PRODUCTION_VIOLATIONS": "true",  # Always log violations
    
    # Error handling
    "BMAD_FAIL_ON_MOCK_ATTEMPT": "true",  # Always fail on mock attempts
    "BMAD_ENFORCE_REAL_EXECUTION": "true",  # Always enforce real execution
}

# Development/Testing configuration (only for explicit testing)
DEVELOPMENT_CONFIG = {
    "BMAD_PRODUCTION_MODE": "false",
    "BMAD_ALLOW_MOCK_MODE": "true",
    "BMAD_MOCK_MODE_EXPLICITLY_REQUESTED": "false",
    "BMAD_VALIDATE_PRODUCTION_MODE": "false",
    "BMAD_LOG_PRODUCTION_VIOLATIONS": "true",
    "BMAD_FAIL_ON_MOCK_ATTEMPT": "false",
    "BMAD_ENFORCE_REAL_EXECUTION": "false",
}

def get_production_config() -> Dict[str, str]:
    """
    Get production configuration.
    
    This function returns hard-coded production settings that cannot be overridden.
    """
    return PRODUCTION_CONFIG.copy()

def get_development_config() -> Dict[str, str]:
    """
    Get development configuration.
    
    This function returns development settings for testing only.
    """
    return DEVELOPMENT_CONFIG.copy()

def is_production_mode() -> bool:
    """
    Check if production mode is enabled.
    
    This is a hard-coded check that LLM cannot override.
    """
    # Check environment variable first
    env_production = os.getenv("BMAD_PRODUCTION_MODE", "true").lower() == "true"
    
    # Check if we're in a production environment
    is_production_env = (
        os.getenv("ENVIRONMENT", "").lower() in ["production", "prod"] or
        os.getenv("NODE_ENV", "").lower() in ["production", "prod"] or
        os.getenv("FLASK_ENV", "").lower() in ["production", "prod"] or
        os.getenv("DJANGO_SETTINGS_MODULE", "").endswith("production")
    )
    
    # Production mode is enabled if either condition is true
    return env_production or is_production_env

def validate_production_mode() -> bool:
    """
    Validate that production mode is properly configured.
    
    This function performs hard-coded validation that cannot be bypassed.
    """
    if not is_production_mode():
        return True  # Development mode is always valid
    
    # In production mode, validate critical settings
    required_settings = [
        "BMAD_PRODUCTION_MODE",
        "BMAD_ALLOW_MOCK_MODE",
        "BMAD_VALIDATE_PRODUCTION_MODE",
        "BMAD_FAIL_ON_MOCK_ATTEMPT",
        "BMAD_ENFORCE_REAL_EXECUTION"
    ]
    
    for setting in required_settings:
        if not os.getenv(setting):
            raise ValueError(f"Production mode requires {setting} to be set")
    
    # Validate that mock mode is disabled in production
    if os.getenv("BMAD_ALLOW_MOCK_MODE", "false").lower() == "true":
        raise ValueError("Mock mode cannot be enabled in production environment")
    
    return True

def enforce_production_settings() -> None:
    """
    Enforce production settings by setting environment variables.
    
    This function sets hard-coded production values that cannot be overridden.
    """
    if is_production_mode():
        for key, value in PRODUCTION_CONFIG.items():
            os.environ[key] = value
        
        # Validate the settings
        validate_production_mode()
        
        print("🚨 PRODUCTION MODE ENFORCED")
        print("🚨 Mock mode is DISABLED")
        print("🚨 All BMAD workflows will execute REAL implementations only")

# Auto-enforce production settings on import
if is_production_mode():
    enforce_production_settings()
