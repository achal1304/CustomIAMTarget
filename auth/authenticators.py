"""
Authentication Mechanisms
Implements OAuth 2.0, Basic Auth, and Mutual TLS
"""

import base64
import hashlib
import jwt
import requests
from typing import Optional, List, Dict, Any, cast
from dataclasses import dataclass, field
from flask import Request


@dataclass
class AuthenticationResult:
    """Result of authentication attempt"""
    authenticated: bool
    identity: Optional[str] = None  # User/client identifier
    scopes: List[str] = field(default_factory=list)  # Granted scopes
    error: Optional[str] = None


class OAuthAuthenticator:
    """
    OAuth 2.0 Bearer Token Authentication
    Supports JWT validation and token introspection
    """
    
    def __init__(self, config):
        """
        Initialize OAuth authenticator
        
        Args:
            config: OAuthConfig instance
        """
        self.config = config
        self._jwks_cache = None
    
    def authenticate(self, request: Request) -> AuthenticationResult:
        """
        Authenticate request using OAuth 2.0 Bearer token
        
        Args:
            request: Flask request object
        
        Returns:
            AuthenticationResult
        """
        if not self.config.enabled:
            return AuthenticationResult(authenticated=False, error="OAuth not enabled")
        
        # Extract Bearer token (case-insensitive header handling)
        auth_header = None
        for header_name in request.headers.keys():
            if header_name.lower() == 'authorization':
                auth_header = request.headers[header_name]
                break
        
        if not auth_header:
            return AuthenticationResult(authenticated=False, error="Missing Authorization header")
        
        if not auth_header.lower().startswith('bearer '):
            return AuthenticationResult(authenticated=False, error="Invalid Authorization header format")
        
        token = auth_header[7:].strip()  # Remove "Bearer " prefix
        
        # Try JWT validation first
        if self.config.jwt_enabled:
            result = self._validate_jwt(token)
            if result.authenticated:
                return result
        
        # Try token introspection
        if self.config.introspection_enabled:
            result = self._introspect_token(token)
            if result.authenticated:
                return result
        
        return AuthenticationResult(authenticated=False, error="Token validation failed")
    
    def _validate_jwt(self, token: str) -> AuthenticationResult:
        """
        Validate JWT token
        
        Args:
            token: JWT token string
        
        Returns:
            AuthenticationResult
        """
        try:
            # Get public key
            public_key = self._get_public_key()
            if not public_key:
                return AuthenticationResult(authenticated=False, error="No public key configured")
            
            # Decode and validate JWT
            # Cast to Any to work around strict type checking in PyJWT
            payload = jwt.decode(
                token,
                public_key,
                algorithms=[self.config.jwt_algorithm],
                issuer=self.config.jwt_issuer,
                audience=self.config.jwt_audience,
                options=cast(Any, {
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_iat': True,
                    'require_exp': True
                })
            )
            
            # Extract identity and scopes
            identity = payload.get('sub') or payload.get('client_id') or payload.get('azp')
            scopes = self._extract_scopes(payload)
            
            return AuthenticationResult(
                authenticated=True,
                identity=identity,
                scopes=scopes
            )
            
        except jwt.ExpiredSignatureError:
            return AuthenticationResult(authenticated=False, error="Token expired")
        except jwt.InvalidTokenError as e:
            return AuthenticationResult(authenticated=False, error=f"Invalid token: {str(e)}")
        except Exception as e:
            return AuthenticationResult(authenticated=False, error=f"JWT validation error: {str(e)}")
    
    def _get_public_key(self) -> Optional[str]:
        """Get public key for JWT validation"""
        if self.config.jwt_public_key:
            return self.config.jwt_public_key
        
        if self.config.jwt_public_key_url:
            # Fetch JWKS (simplified - production should cache and handle key rotation)
            try:
                response = requests.get(self.config.jwt_public_key_url, timeout=5)
                response.raise_for_status()
                jwks = response.json()
                # Return first key (simplified - production should match kid)
                if jwks.get('keys'):
                    return jwks['keys'][0]
            except Exception:
                pass
        
        return None
    
    def _introspect_token(self, token: str) -> AuthenticationResult:
        """
        Introspect token using OAuth 2.0 introspection endpoint
        
        Args:
            token: Access token
        
        Returns:
            AuthenticationResult
        """
        if not self.config.introspection_url:
            return AuthenticationResult(authenticated=False, error="Introspection URL not configured")
        
        try:
            # Call introspection endpoint
            response = requests.post(
                self.config.introspection_url,
                data={'token': token},
                auth=(self.config.introspection_client_id, self.config.introspection_client_secret),
                timeout=5
            )
            response.raise_for_status()
            
            introspection_result = response.json()
            
            # Check if token is active
            if not introspection_result.get('active', False):
                return AuthenticationResult(authenticated=False, error="Token not active")
            
            # Extract identity and scopes
            identity = introspection_result.get('sub') or introspection_result.get('client_id')
            scopes = self._extract_scopes(introspection_result)
            
            return AuthenticationResult(
                authenticated=True,
                identity=identity,
                scopes=scopes
            )
            
        except Exception as e:
            return AuthenticationResult(authenticated=False, error=f"Introspection error: {str(e)}")
    
    def _extract_scopes(self, payload: Dict[str, Any]) -> List[str]:
        """
        Extract scopes from JWT payload or introspection result
        
        Args:
            payload: JWT payload or introspection result
        
        Returns:
            List of scopes
        """
        # Try different scope claim names
        scopes_value = payload.get('scope') or payload.get('scopes') or payload.get('scp')
        
        if isinstance(scopes_value, str):
            # Space-separated string
            return scopes_value.split()
        elif isinstance(scopes_value, list):
            # Array of scopes
            return scopes_value
        
        return []


class BasicAuthAuthenticator:
    """
    HTTP Basic Authentication
    For legacy integrations and non-production environments
    """
    
    def __init__(self, config):
        """
        Initialize Basic Auth authenticator
        
        Args:
            config: BasicAuthConfig instance
        """
        self.config = config
    
    def authenticate(self, request: Request) -> AuthenticationResult:
        """
        Authenticate request using HTTP Basic Auth
        
        Args:
            request: Flask request object
        
        Returns:
            AuthenticationResult
        """
        print(f"[DEBUG] BasicAuth: enabled={self.config.enabled}, credentials={list(self.config.credentials.keys())}")
        
        if not self.config.enabled:
            return AuthenticationResult(authenticated=False, error="Basic Auth not enabled")
        
        # Extract Basic Auth credentials (case-insensitive header handling)
        auth_header = None
        for header_name in request.headers.keys():
            if header_name.lower() == 'authorization':
                auth_header = request.headers[header_name]
                break
        
        print(f"[DEBUG] BasicAuth: auth_header={auth_header[:50] if auth_header else None}")
        
        if not auth_header:
            return AuthenticationResult(authenticated=False, error="Missing Authorization header")
        
        if not auth_header.lower().startswith('basic '):
            return AuthenticationResult(authenticated=False, error="Invalid Authorization header format")
        
        try:
            # Decode credentials
            encoded_credentials = auth_header[6:].strip()
            decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
            username, password = decoded_credentials.split(':', 1)
            
            print(f"[DEBUG] BasicAuth: username={username}, password={'*' * len(password)}")
            
            # Validate credentials
            if username in self.config.credentials:
                stored_hash = self.config.credentials[username]
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                print(f"[DEBUG] BasicAuth: stored_hash={stored_hash[:20]}..., computed_hash={password_hash[:20]}...")
                
                if password_hash == stored_hash:
                    # Get user-specific scopes
                    user_scopes = self.config.user_scopes.get(username, ['scim.read'])
                    print(f"[DEBUG] BasicAuth: SUCCESS for user {username}, scopes={user_scopes}")
                    return AuthenticationResult(
                        authenticated=True,
                        identity=username,
                        scopes=user_scopes
                    )
                else:
                    print(f"[DEBUG] BasicAuth: FAILED - hash mismatch")
            else:
                print(f"[DEBUG] BasicAuth: FAILED - username not found")
            
            return AuthenticationResult(authenticated=False, error="Invalid credentials")
            
        except Exception as e:
            print(f"[DEBUG] BasicAuth: EXCEPTION - {str(e)}")
            return AuthenticationResult(authenticated=False, error=f"Basic Auth error: {str(e)}")


class MutualTLSAuthenticator:
    """
    Mutual TLS (mTLS) Authentication
    Validates client certificates
    """
    
    def __init__(self, config):
        """
        Initialize mTLS authenticator
        
        Args:
            config: MutualTLSConfig instance
        """
        self.config = config
    
    def authenticate(self, request: Request) -> AuthenticationResult:
        """
        Authenticate request using client certificate
        
        Args:
            request: Flask request object
        
        Returns:
            AuthenticationResult
        """
        if not self.config.enabled:
            return AuthenticationResult(authenticated=False, error="mTLS not enabled")
        
        # Check if client certificate is present
        # Note: In production, this requires proper TLS configuration at the web server level
        # Flask's request.environ contains certificate info when configured
        # Headers from nginx are converted: SSL-Client-Cert -> HTTP_SSL_CLIENT_CERT
        
        client_cert = request.headers.get('SSL-Client-Cert') or request.environ.get('SSL_CLIENT_CERT')
        if not client_cert and self.config.require_client_cert:
            return AuthenticationResult(authenticated=False, error="Client certificate required")
        
        if client_cert:
            # Extract certificate subject
            # In production, use proper certificate parsing
            cert_subject = request.headers.get('SSL-Client-S-DN') or request.environ.get('SSL_CLIENT_S_DN', '')
            
            # Map certificate to identity
            identity = self._map_cert_to_identity(cert_subject)
            
            if identity:
                # Get scopes for this identity (or use default scopes)
                scopes = self.config.cert_scopes.get(identity, self.config.default_scopes)
                
                return AuthenticationResult(
                    authenticated=True,
                    identity=identity,
                    scopes=scopes
                )
        
        return AuthenticationResult(authenticated=False, error="Certificate validation failed")
    
    def _map_cert_to_identity(self, cert_subject: str) -> Optional[str]:
        """
        Map certificate subject to identity
        
        Args:
            cert_subject: Certificate subject DN
        
        Returns:
            Identity string or None
        """
        # Check configured mappings
        for pattern, identity in self.config.cert_subject_mapping.items():
            if pattern in cert_subject:
                return identity
        
        # Default: use CN from subject
        if 'CN=' in cert_subject:
            cn_start = cert_subject.index('CN=') + 3
            cn_end = cert_subject.find(',', cn_start)
            if cn_end == -1:
                cn_end = len(cert_subject)
            return cert_subject[cn_start:cn_end]
        
        return None

# Made with Bob
