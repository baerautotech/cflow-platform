"""
Error Handler for BMAD API Service

This module provides comprehensive error handling and logging
for the BMAD API service.
"""

import logging
import os
import traceback
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ErrorHandler:
    """
    Error handler for BMAD API service.
    
    This class handles errors, logs them, and provides
    user-friendly error responses.
    """
    
    def __init__(self):
        """Initialize the error handler."""
        self._error_stats = {
            "total_errors": 0,
            "error_types": {},
            "error_counts": {},
            "last_error_time": None
        }
    
    async def handle_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an error and return user-friendly response.
        
        Args:
            error: Exception that occurred
            context: Context information about the error
            
        Returns:
            Dictionary with error information
        """
        try:
            # Update error statistics
            self._update_error_stats(error, context)
            
            # Log the error
            await self._log_error(error, context)
            
            # Generate user-friendly error response
            error_response = self._generate_error_response(error, context)
            
            return error_response
            
        except Exception as e:
            logger.error(f"Error handler failed: {e}")
            return {
                "error": "Internal error handler failure",
                "success": False,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _update_error_stats(self, error: Exception, context: Dict[str, Any]) -> None:
        """
        Update error statistics.
        
        Args:
            error: Exception that occurred
            context: Context information
        """
        self._error_stats["total_errors"] += 1
        self._error_stats["last_error_time"] = datetime.utcnow().isoformat()
        
        # Track error types
        error_type = type(error).__name__
        if error_type not in self._error_stats["error_types"]:
            self._error_stats["error_types"][error_type] = 0
        self._error_stats["error_types"][error_type] += 1
        
        # Track error counts by tool
        tool_name = context.get("tool_name", "unknown")
        if tool_name not in self._error_stats["error_counts"]:
            self._error_stats["error_counts"][tool_name] = 0
        self._error_stats["error_counts"][tool_name] += 1
    
    async def _log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """
        Log error with context.
        
        Args:
            error: Exception that occurred
            context: Context information
        """
        try:
            # Create error log entry
            error_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context,
                "traceback": traceback.format_exc()
            }
            
            # Log based on error severity
            if isinstance(error, (ValueError, TypeError, KeyError)):
                logger.warning(f"BMAD API error: {error}", extra=error_log)
            elif isinstance(error, (ConnectionError, TimeoutError)):
                logger.error(f"BMAD API connection error: {error}", extra=error_log)
            else:
                logger.error(f"BMAD API error: {error}", extra=error_log)
                
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
    
    def _generate_error_response(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate user-friendly error response.
        
        Args:
            error: Exception that occurred
            context: Context information
            
        Returns:
            Dictionary with error response
        """
        # Determine error category
        if isinstance(error, ValueError):
            error_category = "validation_error"
            user_message = "Invalid input provided"
        elif isinstance(error, TypeError):
            error_category = "type_error"
            user_message = "Invalid data type provided"
        elif isinstance(error, KeyError):
            error_category = "missing_field"
            user_message = "Required field missing"
        elif isinstance(error, ConnectionError):
            error_category = "connection_error"
            user_message = "Service temporarily unavailable"
        elif isinstance(error, TimeoutError):
            error_category = "timeout_error"
            user_message = "Request timed out"
        elif isinstance(error, PermissionError):
            error_category = "permission_error"
            user_message = "Insufficient permissions"
        else:
            error_category = "unknown_error"
            user_message = "An unexpected error occurred"
        
        # Create error response
        error_response = {
            "error": user_message,
            "error_category": error_category,
            "error_type": type(error).__name__,
            "success": False,
            "timestamp": datetime.utcnow().isoformat(),
            "context": {
                "tool_name": context.get("tool_name", "unknown"),
                "user_id": context.get("user_id", "unknown"),
                "execution_time": context.get("execution_time", 0)
            }
        }
        
        # Add debug information in development
        if os.getenv("BMAD_API_DEBUG", "false").lower() == "true":
            error_response["debug"] = {
                "error_message": str(error),
                "traceback": traceback.format_exc()
            }
        
        return error_response
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        Get error statistics.
        
        Returns:
            Dictionary with error statistics
        """
        return self._error_stats.copy()
    
    def reset_error_stats(self) -> None:
        """Reset error statistics."""
        self._error_stats = {
            "total_errors": 0,
            "error_types": {},
            "error_counts": {},
            "last_error_time": None
        }
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get error summary.
        
        Returns:
            Dictionary with error summary
        """
        stats = self._error_stats.copy()
        
        # Calculate error rates
        if stats["total_errors"] > 0:
            # Most common error types
            most_common_error = max(stats["error_types"].items(), key=lambda x: x[1]) if stats["error_types"] else ("none", 0)
            
            # Most problematic tools
            most_problematic_tool = max(stats["error_counts"].items(), key=lambda x: x[1]) if stats["error_counts"] else ("none", 0)
            
            return {
                "total_errors": stats["total_errors"],
                "most_common_error": {
                    "type": most_common_error[0],
                    "count": most_common_error[1]
                },
                "most_problematic_tool": {
                    "tool": most_problematic_tool[0],
                    "count": most_problematic_tool[1]
                },
                "last_error_time": stats["last_error_time"],
                "error_types": stats["error_types"],
                "error_counts": stats["error_counts"]
            }
        else:
            return {
                "total_errors": 0,
                "most_common_error": {"type": "none", "count": 0},
                "most_problematic_tool": {"tool": "none", "count": 0},
                "last_error_time": None,
                "error_types": {},
                "error_counts": {}
            }
