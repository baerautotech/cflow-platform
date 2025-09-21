"""
BMAD API Service Package

This package provides the BMAD API service for executing
BMAD tools via HTTP endpoints.
"""

__version__ = "1.0.0"
__author__ = "BMAD Team"
__description__ = "HTTP API service for BMAD tool execution"

from .main import create_app, run_server
from .auth_service import JWTAuthService, get_current_user, get_optional_user
from .vendor_bmad_integration import VendorBMADIntegration
from .error_handler import ErrorHandler
from .performance_monitor import PerformanceMonitor

__all__ = [
    "create_app",
    "run_server",
    "JWTAuthService",
    "get_current_user",
    "get_optional_user",
    "VendorBMADIntegration",
    "ErrorHandler",
    "PerformanceMonitor"
]
