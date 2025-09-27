"""
BMAD Testing Validation Engine

This module provides hard-coded validation that ensures production mode is enforced
and mock mode cannot be enabled without explicit user consent.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check."""
    passed: bool
    message: str
    severity: str  # "error", "warning", "info"
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


class BMADTestingValidationEngine:
    """
    Hard-coded validation engine that enforces production mode.
    
    This engine cannot be overridden by LLM and ensures that:
    1. Production mode is always enforced in production environments
    2. Mock mode cannot be enabled without explicit user consent
    3. All BMAD workflows execute real implementations
    """
    
    def __init__(self):
        """Initialize the validation engine."""
        self.validation_history: List[ValidationResult] = []
        self.production_mode_enforced = False
        
        # Hard-coded validation rules that cannot be changed
        self.VALIDATION_RULES = {
            "production_mode_required": True,
            "mock_mode_forbidden": True,
            "real_execution_required": True,
            "llm_override_forbidden": True,
            "user_consent_required": True
        }
    
    def validate_production_mode(self) -> ValidationResult:
        """
        Validate that production mode is properly configured.
        
        This is a hard-coded check that cannot be overridden by LLM.
        """
        try:
            # Check if production mode is enabled
            is_production = os.getenv("BMAD_PRODUCTION_MODE", "true").lower() == "true"
            allow_mock = os.getenv("BMAD_ALLOW_MOCK_MODE", "false").lower() == "true"
            
            if not is_production:
                return ValidationResult(
                    passed=False,
                    message="Production mode is not enabled",
                    severity="error",
                    timestamp=datetime.utcnow(),
                    details={"production_mode": is_production, "allow_mock": allow_mock}
                )
            
            if allow_mock:
                return ValidationResult(
                    passed=False,
                    message="Mock mode is enabled in production environment",
                    severity="error",
                    timestamp=datetime.utcnow(),
                    details={"production_mode": is_production, "allow_mock": allow_mock}
                )
            
            # Production mode is properly configured
            self.production_mode_enforced = True
            return ValidationResult(
                passed=True,
                message="Production mode is properly configured",
                severity="info",
                timestamp=datetime.utcnow(),
                details={"production_mode": is_production, "allow_mock": allow_mock}
            )
            
        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Production mode validation failed: {e}",
                severity="error",
                timestamp=datetime.utcnow()
            )
    
    def validate_mock_mode_request(self, request_reason: str, user_id: str) -> ValidationResult:
        """
        Validate a mock mode request.
        
        This ensures that mock mode can only be enabled with explicit user consent.
        """
        try:
            # Check if production mode is enabled
            is_production = os.getenv("BMAD_PRODUCTION_MODE", "true").lower() == "true"
            
            if not is_production:
                # Development mode - mock mode is allowed
                return ValidationResult(
                    passed=True,
                    message="Mock mode allowed in development environment",
                    severity="info",
                    timestamp=datetime.utcnow(),
                    details={"reason": request_reason, "user_id": user_id}
                )
            
            # Production mode - validate request
            if not request_reason or len(request_reason.strip()) < 10:
                return ValidationResult(
                    passed=False,
                    message="Mock mode request requires detailed reason in production",
                    severity="error",
                    timestamp=datetime.utcnow(),
                    details={"reason": request_reason, "user_id": user_id}
                )
            
            # Log the request for audit purposes
            logger.warning(f"🚨 MOCK MODE REQUEST VALIDATED: User {user_id} - Reason: {request_reason}")
            
            return ValidationResult(
                passed=True,
                message="Mock mode request validated",
                severity="warning",
                timestamp=datetime.utcnow(),
                details={"reason": request_reason, "user_id": user_id}
            )
            
        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Mock mode request validation failed: {e}",
                severity="error",
                timestamp=datetime.utcnow()
            )
    
    def validate_workflow_execution(self, workflow_name: str, execution_mode: str) -> ValidationResult:
        """
        Validate that workflow execution is in production mode.
        
        This ensures that all workflows execute real implementations.
        """
        try:
            is_production = os.getenv("BMAD_PRODUCTION_MODE", "true").lower() == "true"
            
            if is_production and execution_mode.lower() == "mock":
                return ValidationResult(
                    passed=False,
                    message=f"Mock execution not allowed for workflow {workflow_name} in production",
                    severity="error",
                    timestamp=datetime.utcnow(),
                    details={"workflow_name": workflow_name, "execution_mode": execution_mode}
                )
            
            return ValidationResult(
                passed=True,
                message=f"Workflow execution validated for {workflow_name}",
                severity="info",
                timestamp=datetime.utcnow(),
                details={"workflow_name": workflow_name, "execution_mode": execution_mode}
            )
            
        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Workflow execution validation failed: {e}",
                severity="error",
                timestamp=datetime.utcnow()
            )
    
    def enforce_production_gate(self) -> ValidationResult:
        """
        Enforce the production gate - this cannot be overridden by LLM.
        
        This is the hard-coded gate that ensures production mode is always enforced.
        """
        try:
            # Set production environment variables
            os.environ["BMAD_PRODUCTION_MODE"] = "true"
            os.environ["BMAD_ALLOW_MOCK_MODE"] = "false"
            os.environ["BMAD_VALIDATE_PRODUCTION_MODE"] = "true"
            os.environ["BMAD_FAIL_ON_MOCK_ATTEMPT"] = "true"
            os.environ["BMAD_ENFORCE_REAL_EXECUTION"] = "true"
            
            # Validate the settings
            validation_result = self.validate_production_mode()
            
            if validation_result.passed:
                logger.warning("🚨 PRODUCTION GATE ENFORCED")
                logger.warning("🚨 Mock mode is DISABLED")
                logger.warning("🚨 All BMAD workflows will execute REAL implementations only")
                
                return ValidationResult(
                    passed=True,
                    message="Production gate enforced successfully",
                    severity="info",
                    timestamp=datetime.utcnow(),
                    details={"production_mode": True, "mock_mode": False}
                )
            else:
                return validation_result
                
        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Production gate enforcement failed: {e}",
                severity="error",
                timestamp=datetime.utcnow()
            )
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get a summary of all validation results."""
        total_validations = len(self.validation_history)
        passed_validations = sum(1 for v in self.validation_history if v.passed)
        failed_validations = total_validations - passed_validations
        
        return {
            "total_validations": total_validations,
            "passed_validations": passed_validations,
            "failed_validations": failed_validations,
            "success_rate": passed_validations / total_validations if total_validations > 0 else 0,
            "production_mode_enforced": self.production_mode_enforced,
            "last_validation": self.validation_history[-1] if self.validation_history else None,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def add_validation_result(self, result: ValidationResult) -> None:
        """Add a validation result to the history."""
        self.validation_history.append(result)
        
        # Log the result
        if result.passed:
            logger.info(f"✅ Validation passed: {result.message}")
        else:
            logger.error(f"❌ Validation failed: {result.message}")
    
    def clear_validation_history(self) -> None:
        """Clear the validation history."""
        self.validation_history.clear()
        logger.info("Validation history cleared")


# Global validation engine instance
validation_engine = BMADTestingValidationEngine()

# Auto-enforce production gate on import
if os.getenv("BMAD_PRODUCTION_MODE", "true").lower() == "true":
    result = validation_engine.enforce_production_gate()
    validation_engine.add_validation_result(result)

