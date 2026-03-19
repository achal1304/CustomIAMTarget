"""
Authentication & Authorization Middleware
Flask middleware for enforcing auth on all endpoints
"""

from flask import Request, jsonify, g
from typing import Optional, Tuple, Any, Dict
from auth.config import AuthConfig, get_required_scopes
from auth.authenticators import (
    AuthenticationResult,
    OAuthAuthenticator,
    BasicAuthAuthenticator,
    MutualTLSAuthenticator
)


class AuthMiddleware:
    """
    Authentication and Authorization Middleware
    
    Enforces authentication and authorization before SCIM logic executes.
    Pluggable, config-driven, and framework-level.
    """
    
    def __init__(self, config: AuthConfig):
        """
        Initialize middleware with configuration
        
        Args:
            config: AuthConfig instance
        """
        self.config = config
        
        # Initialize authenticators
        self.oauth_authenticator = OAuthAuthenticator(config.oauth)
        self.basic_auth_authenticator = BasicAuthAuthenticator(config.basic_auth)
        self.mtls_authenticator = MutualTLSAuthenticator(config.mtls)
    
    def authenticate_request(self, request: Request) -> AuthenticationResult:
        """
        Authenticate request using configured mechanisms
        
        Tries authenticators in order:
        1. OAuth 2.0 Bearer Token
        2. HTTP Basic Auth
        3. Mutual TLS
        
        Args:
            request: Flask request object
        
        Returns:
            AuthenticationResult
        """
        # Try OAuth first (most common)
        if self.config.oauth.enabled:
            result = self.oauth_authenticator.authenticate(request)
            if result.authenticated:
                return result
        
        # Try Basic Auth
        if self.config.basic_auth.enabled:
            result = self.basic_auth_authenticator.authenticate(request)
            if result.authenticated:
                return result
        
        # Try mTLS
        if self.config.mtls.enabled:
            result = self.mtls_authenticator.authenticate(request)
            if result.authenticated:
                return result
        
        # No authentication succeeded
        return AuthenticationResult(
            authenticated=False,
            error="Authentication failed: No valid credentials provided"
        )
    
    def authorize_request(self, auth_result: AuthenticationResult, 
                         method: str, path: str) -> Tuple[bool, Optional[str]]:
        """
        Authorize request based on scopes
        
        Args:
            auth_result: Authentication result with granted scopes
            method: HTTP method
            path: Request path
        
        Returns:
            Tuple of (authorized: bool, error_message: Optional[str])
        """
        if not self.config.enforce_authorization:
            return True, None
        
        # Get required scopes for endpoint
        required_scopes = get_required_scopes(method, path)
        
        # If no scopes required, allow access
        if not required_scopes:
            return True, None
        
        # Check if user has required scopes
        granted_scopes = set(auth_result.scopes)
        required_scopes_set = set(required_scopes)
        
        # User must have at least one of the required scopes
        if granted_scopes.intersection(required_scopes_set):
            return True, None
        
        # Authorization failed
        return False, f"Insufficient permissions. Required scopes: {', '.join(required_scopes)}"
    
    def process_request(self, request: Request) -> Optional[Tuple[Dict[str, Any], int]]:
        """
        Process request through authentication and authorization
        
        Args:
            request: Flask request object
        
        Returns:
            None if authorized, or (error_response, status_code) tuple if not
        """
        # Skip auth if no mechanisms are enabled
        if not self.config.is_any_auth_enabled():
            return None
        
        method = request.method
        path = request.path
        
        # Skip authentication for Swagger UI and documentation routes
        if path.startswith('/api/docs'):
            return None
        
        # Check if endpoint requires authentication
        required_scopes = get_required_scopes(method, path)
        
        # Public endpoints (no scopes required)
        if not required_scopes:
            return None
        
        # Authenticate
        auth_result = self.authenticate_request(request)
        
        if not auth_result.authenticated:
            # Return 401 Unauthorized with SCIM-compliant error
            return self._create_auth_error_response(auth_result.error), 401
        
        # Authorize
        authorized, error_message = self.authorize_request(auth_result, method, path)
        
        if not authorized:
            # Return 403 Forbidden with SCIM-compliant error
            return self._create_authz_error_response(error_message), 403
        
        # Store auth info in request context for potential use by endpoints
        g.auth_identity = auth_result.identity
        g.auth_scopes = auth_result.scopes
        
        # Request is authorized
        return None
    
    def _create_auth_error_response(self, detail: Optional[str] = None) -> Dict[str, Any]:
        """
        Create SCIM-compliant 401 error response
        
        Args:
            detail: Error detail message
        
        Returns:
            SCIM error response dict
        """
        error = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "status": "401",
            "detail": detail or "Authentication required"
        }
        return error
    
    def _create_authz_error_response(self, detail: Optional[str] = None) -> Dict[str, Any]:
        """
        Create SCIM-compliant 403 error response
        
        Args:
            detail: Error detail message
        
        Returns:
            SCIM error response dict
        """
        error = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "status": "403",
            "detail": detail or "Insufficient permissions"
        }
        return error


def create_auth_middleware(config: Optional[AuthConfig] = None) -> AuthMiddleware:
    """
    Factory function to create auth middleware
    
    Args:
        config: AuthConfig instance (if None, loads from environment)
    
    Returns:
        AuthMiddleware instance
    """
    if config is None:
        config = AuthConfig.from_env()
    
    return AuthMiddleware(config)

# Made with Bob
