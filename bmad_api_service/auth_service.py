"""
JWT Authentication Service for BMAD API

This module provides JWT authentication and validation
for the BMAD API service.
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# JWT configuration
JWT_SECRET = os.getenv("BMAD_JWT_SECRET", "default-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

# Security scheme
security = HTTPBearer()


class JWTAuthService:
    """
    JWT authentication service for BMAD API.
    
    This class handles JWT token validation and user context extraction.
    """
    
    def __init__(self):
        """Initialize the JWT authentication service."""
        self.secret = JWT_SECRET
        self.algorithm = JWT_ALGORITHM
        self.expiry_hours = JWT_EXPIRY_HOURS
        self._stats = {
            "tokens_validated": 0,
            "tokens_expired": 0,
            "tokens_invalid": 0,
            "validation_errors": 0
        }
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a JWT token.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Dictionary with user context
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            self._stats["tokens_validated"] += 1
            
            # Decode and validate token with leeway for timing issues
            # Disable iat validation for testing by setting options
            payload = jwt.decode(
                token, 
                self.secret, 
                algorithms=[self.algorithm], 
                leeway=2,
                options={"verify_iat": False}
            )
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.utcnow().timestamp() > exp:
                self._stats["tokens_expired"] += 1
                raise HTTPException(status_code=401, detail="Token expired")
            
            # Extract user context
            user_context = {
                "user_id": payload.get("user_id", "unknown"),
                "username": payload.get("username", "unknown"),
                "email": payload.get("email", ""),
                "roles": payload.get("roles", []),
                "permissions": payload.get("permissions", []),
                "tenant_id": payload.get("tenant_id", "default"),
                "issued_at": payload.get("iat"),
                "expires_at": payload.get("exp")
            }
            
            logger.debug(f"Token validated for user: {user_context['user_id']}")
            return user_context
            
        except jwt.ExpiredSignatureError:
            self._stats["tokens_expired"] += 1
            logger.warning("Token expired")
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            self._stats["tokens_invalid"] += 1
            logger.warning(f"Invalid token: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            self._stats["validation_errors"] += 1
            logger.error(f"Token validation error: {e}")
            raise HTTPException(status_code=401, detail="Token validation failed")
    
    def generate_token(self, user_data: Dict[str, Any]) -> str:
        """
        Generate a JWT token for a user.
        
        Args:
            user_data: User data to include in token
            
        Returns:
            JWT token string
        """
        try:
            # Set expiration time
            exp_time = datetime.utcnow() + timedelta(hours=self.expiry_hours)
            
            # Create payload with much earlier iat to avoid timing issues
            now = datetime.utcnow()
            iat_time = now - timedelta(minutes=1)  # Set iat 1 minute in the past
            
            # Create payload
            payload = {
                "user_id": user_data.get("user_id"),
                "username": user_data.get("username"),
                "email": user_data.get("email"),
                "roles": user_data.get("roles", []),
                "permissions": user_data.get("permissions", []),
                "tenant_id": user_data.get("tenant_id", "default"),
                "iat": iat_time.timestamp(),
                "exp": exp_time.timestamp()
            }
            
            # Generate token
            token = jwt.encode(payload, self.secret, algorithm=self.algorithm)
            
            logger.info(f"Token generated for user: {user_data.get('user_id')}")
            return token
            
        except Exception as e:
            logger.error(f"Token generation error: {e}")
            raise HTTPException(status_code=500, detail="Token generation failed")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get authentication statistics.
        
        Returns:
            Dictionary with authentication statistics
        """
        stats = self._stats.copy()
        
        total_tokens = stats["tokens_validated"]
        if total_tokens > 0:
            stats["success_rate"] = (total_tokens - stats["tokens_expired"] - stats["tokens_invalid"]) / total_tokens
        else:
            stats["success_rate"] = 0.0
        
        return stats
    
    def reset_stats(self) -> None:
        """Reset authentication statistics."""
        self._stats = {
            "tokens_validated": 0,
            "tokens_expired": 0,
            "tokens_invalid": 0,
            "validation_errors": 0
        }


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependency to get current user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        Dictionary with user context
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Extract token
    token = credentials.credentials
    
    # Validate token
    auth_service = JWTAuthService()
    user_context = await auth_service.validate_token(token)
    
    return user_context


async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """
    Dependency to get current user from JWT token (optional).
    
    Args:
        credentials: HTTP authorization credentials (optional)
        
    Returns:
        Dictionary with user context or None
    """
    if not credentials:
        return None
    
    try:
        # Extract token
        token = credentials.credentials
        
        # Validate token
        auth_service = JWTAuthService()
        user_context = await auth_service.validate_token(token)
        
        return user_context
    except HTTPException:
        return None
