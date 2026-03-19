"""
Authentication & Authorization Configuration
Supports multiple authentication mechanisms in a pluggable, config-driven way
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class OAuthConfig:
    """OAuth 2.0 Bearer Token configuration"""
    enabled: bool = True
    # JWT validation settings
    jwt_enabled: bool = True
    jwt_issuer: Optional[str] = None
    jwt_audience: Optional[str] = None
    jwt_algorithm: str = "RS256"
    jwt_public_key_url: Optional[str] = None  # JWKS URL
    jwt_public_key: Optional[str] = None  # Direct public key
    
    # Token introspection settings (alternative to JWT)
    introspection_enabled: bool = False
    introspection_url: Optional[str] = None
    introspection_client_id: Optional[str] = None
    introspection_client_secret: Optional[str] = None


@dataclass
class BasicAuthConfig:
    """HTTP Basic Authentication configuration"""
    enabled: bool = False
    # Credentials stored as username:password_hash pairs
    credentials: Dict[str, str] = field(default_factory=dict)


@dataclass
class MutualTLSConfig:
    """Mutual TLS (mTLS) configuration"""
    enabled: bool = False
    # Certificate validation settings
    require_client_cert: bool = False
    trusted_ca_certs_path: Optional[str] = None
    # Certificate-to-identity mapping
    cert_subject_mapping: Dict[str, str] = field(default_factory=dict)


@dataclass
class AuthConfig:
    """Main authentication configuration"""
    # Authentication mechanisms
    oauth: OAuthConfig = field(default_factory=OAuthConfig)
    basic_auth: BasicAuthConfig = field(default_factory=BasicAuthConfig)
    mtls: MutualTLSConfig = field(default_factory=MutualTLSConfig)
    
    # Authorization settings
    enforce_authorization: bool = True
    
    # Scope definitions
    scopes: Dict[str, str] = field(default_factory=lambda: {
        "scim.read": "Read SCIM resources (Users, Groups)",
        "scim.write": "Create, update, delete SCIM resources",
        "supportingdata.read": "Read supporting data (Roles, Departments)"
    })
    
    @classmethod
    def from_env(cls) -> 'AuthConfig':
        """Load configuration from environment variables"""
        
        # Load JWT public key and convert escaped newlines to actual newlines
        jwt_public_key = os.getenv('AUTH_JWT_PUBLIC_KEY')
        if jwt_public_key:
            # Replace literal \n with actual newlines for PEM format
            jwt_public_key = jwt_public_key.replace('\\n', '\n')
        
        # OAuth configuration - ENABLED BY DEFAULT for IAM integration
        oauth = OAuthConfig(
            enabled=os.getenv('AUTH_OAUTH_ENABLED', 'true').lower() == 'true',
            jwt_enabled=os.getenv('AUTH_JWT_ENABLED', 'true').lower() == 'true',
            jwt_issuer=os.getenv('AUTH_JWT_ISSUER'),
            jwt_audience=os.getenv('AUTH_JWT_AUDIENCE'),
            jwt_algorithm=os.getenv('AUTH_JWT_ALGORITHM', 'RS256'),
            jwt_public_key_url=os.getenv('AUTH_JWT_PUBLIC_KEY_URL'),
            jwt_public_key=jwt_public_key,
            introspection_enabled=os.getenv('AUTH_INTROSPECTION_ENABLED', 'false').lower() == 'true',
            introspection_url=os.getenv('AUTH_INTROSPECTION_URL'),
            introspection_client_id=os.getenv('AUTH_INTROSPECTION_CLIENT_ID'),
            introspection_client_secret=os.getenv('AUTH_INTROSPECTION_CLIENT_SECRET')
        )
        
        # Basic Auth configuration - ENABLED BY DEFAULT for IAM integration
        basic_auth = BasicAuthConfig(
            enabled=os.getenv('AUTH_BASIC_ENABLED', 'true').lower() == 'true',
            credentials=cls._load_basic_auth_credentials()
        )
        
        # mTLS configuration - ENABLED BY DEFAULT for IAM integration
        mtls = MutualTLSConfig(
            enabled=os.getenv('AUTH_MTLS_ENABLED', 'true').lower() == 'true',
            require_client_cert=os.getenv('AUTH_MTLS_REQUIRE_CERT', 'false').lower() == 'true',
            trusted_ca_certs_path=os.getenv('AUTH_MTLS_CA_CERTS_PATH')
        )
        
        return cls(
            oauth=oauth,
            basic_auth=basic_auth,
            mtls=mtls,
            enforce_authorization=os.getenv('AUTH_ENFORCE_AUTHZ', 'true').lower() == 'true'
        )
    
    @staticmethod
    def _load_basic_auth_credentials() -> Dict[str, str]:
        """Load basic auth credentials from environment"""
        credentials = {}
        # Format: AUTH_BASIC_USERS=user1:hash1,user2:hash2
        users_str = os.getenv('AUTH_BASIC_USERS', '')
        if users_str:
            for user_pair in users_str.split(','):
                if ':' in user_pair:
                    username, password_hash = user_pair.split(':', 1)
                    credentials[username.strip()] = password_hash.strip()
        return credentials
    
    def is_any_auth_enabled(self) -> bool:
        """Check if any authentication mechanism is enabled"""
        return self.oauth.enabled or self.basic_auth.enabled or self.mtls.enabled


# Endpoint to scope mapping
ENDPOINT_SCOPES = {
    # SCIM Discovery endpoints (public, no auth required)
    'GET:/scim/v2/ServiceProviderConfig': [],
    'GET:/scim/v2/Schemas': [],
    'GET:/scim/v2/Schemas/*': [],  # Individual schemas
    'GET:/scim/v2/ResourceTypes': [],
    'GET:/scim/v2/ResourceTypes/*': [],  # Individual resource types
    
    # API Documentation endpoints (public)
    'GET:/swagger.yaml': [],
    'GET:/postman_collection.json': [],
    'GET:/api/docs': [],  # Swagger UI
    
    # Token generation endpoints (public, for development/testing)
    'GET:/api/dev/tokens': [],
    'POST:/api/dev/tokens/generate': [],
    'GET:/api/dev/tokens/public-key': [],
    
    # SCIM User endpoints
    'GET:/scim/v2/Users': ['scim.read'],
    'POST:/scim/v2/Users': ['scim.write'],
    'GET:/scim/v2/Users/*': ['scim.read'],
    'PATCH:/scim/v2/Users/*': ['scim.write'],
    'DELETE:/scim/v2/Users/*': ['scim.write'],
    
    # SCIM Group endpoints
    'GET:/scim/v2/Groups': ['scim.read'],
    'POST:/scim/v2/Groups': ['scim.write'],
    'GET:/scim/v2/Groups/*': ['scim.read'],
    'PATCH:/scim/v2/Groups/*': ['scim.write'],
    'DELETE:/scim/v2/Groups/*': ['scim.write'],
    
    # Supporting Data endpoints
    'GET:/api/supporting-data/roles': ['supportingdata.read'],
    'GET:/api/supporting-data/departments': ['supportingdata.read'],
}


def get_required_scopes(method: str, path: str) -> List[str]:
    """
    Get required scopes for an endpoint
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
    
    Returns:
        List of required scopes (empty list = no auth required)
    """
    # Exact match
    key = f"{method}:{path}"
    if key in ENDPOINT_SCOPES:
        return ENDPOINT_SCOPES[key]
    
    # Wildcard match
    for pattern, scopes in ENDPOINT_SCOPES.items():
        if pattern.endswith('/*'):
            pattern_prefix = pattern[:-2]  # Remove /*
            if key.startswith(pattern_prefix.split(':')[0] + ':' + pattern_prefix.split(':')[1]):
                return scopes
    
    # Default: require authentication for all other endpoints
    return ['scim.read']

# Made with Bob
