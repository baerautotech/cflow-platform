"""
Security and Authentication Testing Handlers

This module provides MCP handlers for security and authentication testing
of the BMAD integration.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from cflow_platform.core.security_authentication_testing_engine import (
    SecurityAuthenticationTestingEngine,
    SecurityTestType,
    VulnerabilitySeverity
)

logger = logging.getLogger(__name__)


async def bmad_security_authentication_test(
    endpoint: str,
    auth_method: str = "jwt",
    test_credentials: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Test authentication mechanisms for an endpoint.
    
    Args:
        endpoint: API endpoint to test
        auth_method: Authentication method (jwt, basic, bearer, etc.)
        test_credentials: Test credentials to use
        
    Returns:
        Dictionary with authentication test results
    """
    try:
        logger.info(f"Testing authentication for {endpoint} using {auth_method}")
        
        engine = SecurityAuthenticationTestingEngine()
        
        result = await engine.test_authentication(
            endpoint=endpoint,
            auth_method=auth_method,
            test_credentials=test_credentials
        )
        
        return {
            "success": True,
            "test_name": result.test_name,
            "authentication_method": result.authentication_method,
            "authentication_success": result.success,
            "token_valid": result.token_valid,
            "token_expired": result.token_expired,
            "permissions_valid": result.permissions_valid,
            "security_headers_present": result.security_headers_present,
            "test_duration": result.test_duration,
            "response_data": result.response_data,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Authentication test failed for {endpoint}: {e}")
        return {
            "success": False,
            "error": str(e),
            "endpoint": endpoint,
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_security_authorization_test(
    endpoint: str,
    user_roles: str,
    required_permissions: str
) -> Dict[str, Any]:
    """
    Test authorization mechanisms for an endpoint.
    
    Args:
        endpoint: API endpoint to test
        user_roles: JSON string with list of user roles to test
        required_permissions: JSON string with list of required permissions
        
    Returns:
        Dictionary with authorization test results
    """
    try:
        logger.info(f"Testing authorization for {endpoint}")
        
        # Parse user roles
        try:
            user_roles_list = json.loads(user_roles)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON in user_roles: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        if not isinstance(user_roles_list, list):
            return {
                "success": False,
                "error": "user_roles must be a list",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Parse required permissions
        try:
            required_permissions_list = json.loads(required_permissions)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON in required_permissions: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        if not isinstance(required_permissions_list, list):
            return {
                "success": False,
                "error": "required_permissions must be a list",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        engine = SecurityAuthenticationTestingEngine()
        
        result = await engine.test_authorization(
            endpoint=endpoint,
            user_roles=user_roles_list,
            required_permissions=required_permissions_list
        )
        
        return {
            "success": True,
            "test_name": result.test_name,
            "test_type": result.test_type.value,
            "target_endpoint": result.target_endpoint,
            "authorization_success": result.success,
            "vulnerability_found": result.vulnerability_found,
            "severity": result.severity.value if result.severity else None,
            "vulnerability_details": result.vulnerability_details,
            "test_duration": result.test_duration,
            "recommendations": result.recommendations,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Authorization test failed for {endpoint}: {e}")
        return {
            "success": False,
            "error": str(e),
            "endpoint": endpoint,
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_security_input_validation_test(
    endpoint: str,
    input_fields: str,
    malicious_inputs: Optional[str] = None
) -> Dict[str, Any]:
    """
    Test input validation and sanitization for an endpoint.
    
    Args:
        endpoint: API endpoint to test
        input_fields: JSON string with list of input fields to test
        malicious_inputs: JSON string with list of malicious inputs to test
        
    Returns:
        Dictionary with input validation test results
    """
    try:
        logger.info(f"Testing input validation for {endpoint}")
        
        # Parse input fields
        try:
            input_fields_list = json.loads(input_fields)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON in input_fields: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        if not isinstance(input_fields_list, list):
            return {
                "success": False,
                "error": "input_fields must be a list",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Parse malicious inputs if provided
        malicious_inputs_list = None
        if malicious_inputs:
            try:
                malicious_inputs_list = json.loads(malicious_inputs)
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Invalid JSON in malicious_inputs: {e}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            if not isinstance(malicious_inputs_list, list):
                return {
                    "success": False,
                    "error": "malicious_inputs must be a list",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        engine = SecurityAuthenticationTestingEngine()
        
        result = await engine.test_input_validation(
            endpoint=endpoint,
            input_fields=input_fields_list,
            malicious_inputs=malicious_inputs_list
        )
        
        return {
            "success": True,
            "test_name": result.test_name,
            "test_type": result.test_type.value,
            "target_endpoint": result.target_endpoint,
            "validation_success": result.success,
            "vulnerability_found": result.vulnerability_found,
            "severity": result.severity.value if result.severity else None,
            "vulnerability_details": result.vulnerability_details,
            "test_duration": result.test_duration,
            "recommendations": result.recommendations,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Input validation test failed for {endpoint}: {e}")
        return {
            "success": False,
            "error": str(e),
            "endpoint": endpoint,
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_security_rate_limiting_test(
    endpoint: str,
    rate_limit: int = 100,
    time_window: int = 60
) -> Dict[str, Any]:
    """
    Test rate limiting mechanisms for an endpoint.
    
    Args:
        endpoint: API endpoint to test
        rate_limit: Expected rate limit (requests per time window)
        time_window: Time window in seconds
        
    Returns:
        Dictionary with rate limiting test results
    """
    try:
        logger.info(f"Testing rate limiting for {endpoint} (limit: {rate_limit}/{time_window}s)")
        
        engine = SecurityAuthenticationTestingEngine()
        
        result = await engine.test_rate_limiting(
            endpoint=endpoint,
            rate_limit=rate_limit,
            time_window=time_window
        )
        
        return {
            "success": True,
            "test_name": result.test_name,
            "test_type": result.test_type.value,
            "target_endpoint": result.target_endpoint,
            "rate_limiting_success": result.success,
            "vulnerability_found": result.vulnerability_found,
            "severity": result.severity.value if result.severity else None,
            "vulnerability_details": result.vulnerability_details,
            "test_duration": result.test_duration,
            "recommendations": result.recommendations,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Rate limiting test failed for {endpoint}: {e}")
        return {
            "success": False,
            "error": str(e),
            "endpoint": endpoint,
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_security_test_suite(
    endpoints: str,
    test_types: str,
    user_roles: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run a comprehensive security test suite.
    
    Args:
        endpoints: JSON string with list of endpoints to test
        test_types: JSON string with list of security test types to perform
        user_roles: JSON string with list of user roles to test with
        
    Returns:
        Dictionary with comprehensive security test results
    """
    try:
        logger.info("Running comprehensive security test suite")
        
        # Parse endpoints
        try:
            endpoints_list = json.loads(endpoints)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON in endpoints: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        if not isinstance(endpoints_list, list):
            return {
                "success": False,
                "error": "endpoints must be a list",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Parse test types
        try:
            test_types_list = json.loads(test_types)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON in test_types: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        if not isinstance(test_types_list, list):
            return {
                "success": False,
                "error": "test_types must be a list",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Validate test types
        test_type_enums = []
        for test_type in test_types_list:
            try:
                test_type_enums.append(SecurityTestType(test_type))
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid test type: {test_type}. Valid types: {[t.value for t in SecurityTestType]}",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        # Parse user roles if provided
        user_roles_list = None
        if user_roles:
            try:
                user_roles_list = json.loads(user_roles)
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Invalid JSON in user_roles: {e}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            if not isinstance(user_roles_list, list):
                return {
                    "success": False,
                    "error": "user_roles must be a list",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        engine = SecurityAuthenticationTestingEngine()
        
        result = await engine.run_security_test_suite(
            endpoints=endpoints_list,
            test_types=test_type_enums,
            user_roles=user_roles_list
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Security test suite failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_security_vulnerability_scan(
    endpoint: str,
    scan_types: str
) -> Dict[str, Any]:
    """
    Perform a comprehensive vulnerability scan on an endpoint.
    
    Args:
        endpoint: API endpoint to scan
        scan_types: JSON string with list of vulnerability scan types
        
    Returns:
        Dictionary with vulnerability scan results
    """
    try:
        logger.info(f"Performing vulnerability scan on {endpoint}")
        
        # Parse scan types
        try:
            scan_types_list = json.loads(scan_types)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON in scan_types: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        if not isinstance(scan_types_list, list):
            return {
                "success": False,
                "error": "scan_types must be a list",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        engine = SecurityAuthenticationTestingEngine()
        
        # Run multiple security tests based on scan types
        test_results = []
        vulnerabilities_found = 0
        
        for scan_type in scan_types_list:
            try:
                if scan_type == "authentication":
                    result = await engine.test_authentication(endpoint)
                    test_results.append({
                        "scan_type": scan_type,
                        "success": result.success,
                        "vulnerability_found": not result.success,
                        "details": result.response_data
                    })
                    if not result.success:
                        vulnerabilities_found += 1
                
                elif scan_type == "authorization":
                    result = await engine.test_authorization(endpoint, ["user"], ["read"])
                    test_results.append({
                        "scan_type": scan_type,
                        "success": result.success,
                        "vulnerability_found": result.vulnerability_found,
                        "severity": result.severity.value if result.severity else None,
                        "details": result.vulnerability_details
                    })
                    if result.vulnerability_found:
                        vulnerabilities_found += 1
                
                elif scan_type == "input_validation":
                    result = await engine.test_input_validation(endpoint, ["input", "data"])
                    test_results.append({
                        "scan_type": scan_type,
                        "success": result.success,
                        "vulnerability_found": result.vulnerability_found,
                        "severity": result.severity.value if result.severity else None,
                        "details": result.vulnerability_details
                    })
                    if result.vulnerability_found:
                        vulnerabilities_found += 1
                
                elif scan_type == "rate_limiting":
                    result = await engine.test_rate_limiting(endpoint)
                    test_results.append({
                        "scan_type": scan_type,
                        "success": result.success,
                        "vulnerability_found": result.vulnerability_found,
                        "severity": result.severity.value if result.severity else None,
                        "details": result.vulnerability_details
                    })
                    if result.vulnerability_found:
                        vulnerabilities_found += 1
                
            except Exception as e:
                logger.error(f"Vulnerability scan failed for {scan_type}: {e}")
                test_results.append({
                    "scan_type": scan_type,
                    "success": False,
                    "vulnerability_found": True,
                    "error": str(e)
                })
                vulnerabilities_found += 1
        
        return {
            "success": True,
            "endpoint": endpoint,
            "scan_types": scan_types_list,
            "total_scans": len(scan_types_list),
            "vulnerabilities_found": vulnerabilities_found,
            "scan_results": test_results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Vulnerability scan failed for {endpoint}: {e}")
        return {
            "success": False,
            "error": str(e),
            "endpoint": endpoint,
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_security_test_history() -> Dict[str, Any]:
    """
    Get history of all security and authentication tests.
    
    Returns:
        Dictionary with test history
    """
    try:
        logger.info("Retrieving security test history")
        
        engine = SecurityAuthenticationTestingEngine()
        history = engine.get_security_test_history()
        
        return {
            "success": True,
            "history": history,
            "security_tests_count": len(history["security_tests"]),
            "authentication_tests_count": len(history["authentication_tests"]),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve security test history: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_security_test_clear_history() -> Dict[str, Any]:
    """
    Clear all security and authentication test history.
    
    Returns:
        Dictionary with operation result
    """
    try:
        logger.info("Clearing security test history")
        
        engine = SecurityAuthenticationTestingEngine()
        engine.clear_security_test_history()
        
        return {
            "success": True,
            "message": "Security test history cleared successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to clear security test history: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
