"""
Token Generation Endpoints (Development/Testing Only)
Provides easy token generation for testing authentication
⚠️ WARNING: Only use in development/testing environments!
"""

import jwt
import datetime
import hashlib
import base64
import os
from flask import jsonify, request
from typing import Dict, Any, List, Tuple
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


class TokenEndpoints:
    """Token generation endpoints for testing"""
    
    # Class-level key storage to persist across instances
    _private_key = None
    _public_key = None
    _keys_file = '.test_keys.pem'
    
    def __init__(self):
        """Initialize with a persistent test RSA key pair"""
        self.private_key, self.public_key = self._get_or_generate_keys()
    
    @classmethod
    def _get_or_generate_keys(cls) -> Tuple[bytes, bytes]:
        """Get existing keys or generate new ones (persisted to file)"""
        # Return cached keys if available
        if cls._private_key and cls._public_key:
            return cls._private_key, cls._public_key
        
        # Try to load from file
        if os.path.exists(cls._keys_file):
            try:
                with open(cls._keys_file, 'rb') as f:
                    content = f.read()
                    # Split by marker
                    parts = content.split(b'-----END PRIVATE KEY-----')
                    if len(parts) == 2:
                        private_pem = parts[0] + b'-----END PRIVATE KEY-----'
                        public_pem = parts[1].strip()
                        cls._private_key = private_pem
                        cls._public_key = public_pem
                        print(f"✓ Loaded existing RSA keys from {cls._keys_file}")
                        return cls._private_key, cls._public_key
            except Exception as e:
                print(f"⚠️  Failed to load keys from {cls._keys_file}: {e}")
        
        # Generate new keys
        print(f"Generating new RSA key pair and saving to {cls._keys_file}...")
        cls._private_key, cls._public_key = cls._generate_rsa_keys()
        
        # Save to file
        try:
            with open(cls._keys_file, 'wb') as f:
                f.write(cls._private_key)
                f.write(b'\n')
                f.write(cls._public_key)
            print(f"✓ Saved RSA keys to {cls._keys_file}")
            print(f"⚠️  IMPORTANT: Update your .env file with this public key:")
            print(f"   Run: curl http://localhost:5000/api/dev/tokens/public-key")
        except Exception as e:
            print(f"⚠️  Failed to save keys to {cls._keys_file}: {e}")
        
        return cls._private_key, cls._public_key
    
    @classmethod
    def _generate_rsa_keys(cls) -> Tuple[bytes, bytes]:
        """Generate RSA key pair for JWT signing"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem, public_pem
    
    def _create_jwt_token(self, scopes: List[str], subject: str = 'test-user',
                         expires_in_hours: int = 24) -> str:
        """Create JWT token with specified scopes"""
        now = datetime.datetime.utcnow()
        
        payload = {
            'iss': 'https://test-idp.example.com',
            'aud': 'scim-service-provider',
            'sub': subject,
            'scope': ' '.join(scopes),
            'exp': now + datetime.timedelta(hours=expires_in_hours),
            'iat': now,
            'nbf': now,
            'jti': f'test-token-{int(now.timestamp())}'
        }
        
        token = jwt.encode(payload, self.private_key, algorithm='RS256')
        return token
    
    def _generate_basic_auth_hash(self, password: str) -> str:
        """Generate SHA-256 hash for Basic Auth password"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_basic_auth_header(self, username: str, password: str) -> str:
        """Generate Basic Auth header value"""
        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    def get_all_tokens(self) -> tuple[Dict[str, Any], int]:
        """
        GET /api/dev/tokens
        Generate all types of tokens for testing
        """
        # Generate JWT tokens with different scopes
        tokens = {
            'jwt': {
                'read_only': {
                    'token': self._create_jwt_token(['scim.read']),
                    'scopes': ['scim.read'],
                    'description': 'Can only read SCIM resources (Users, Groups)'
                },
                'write_only': {
                    'token': self._create_jwt_token(['scim.write']),
                    'scopes': ['scim.write'],
                    'description': 'Can only write SCIM resources'
                },
                'full_scim': {
                    'token': self._create_jwt_token(['scim.read', 'scim.write']),
                    'scopes': ['scim.read', 'scim.write'],
                    'description': 'Full SCIM access (read and write)'
                },
                'supporting_data': {
                    'token': self._create_jwt_token(['supportingdata.read']),
                    'scopes': ['supportingdata.read'],
                    'description': 'Can only read supporting data (Roles, Departments)'
                },
                'full_access': {
                    'token': self._create_jwt_token(['scim.read', 'scim.write', 'supportingdata.read']),
                    'scopes': ['scim.read', 'scim.write', 'supportingdata.read'],
                    'description': 'Full access to all endpoints'
                }
            },
            'basic_auth': {
                'admin': {
                    'username': 'admin',
                    'password': 'admin123',
                    'password_hash': self._generate_basic_auth_hash('admin123'),
                    'authorization_header': self._generate_basic_auth_header('admin', 'admin123'),
                    'description': 'Admin user with full access'
                },
                'testuser': {
                    'username': 'testuser',
                    'password': 'testpass123',
                    'password_hash': self._generate_basic_auth_hash('testpass123'),
                    'authorization_header': self._generate_basic_auth_header('testuser', 'testpass123'),
                    'description': 'Test user'
                },
                'readonly': {
                    'username': 'readonly',
                    'password': 'readonly123',
                    'password_hash': self._generate_basic_auth_hash('readonly123'),
                    'authorization_header': self._generate_basic_auth_header('readonly', 'readonly123'),
                    'description': 'Read-only user'
                }
            }
        }
        
        # Add configuration instructions
        response = {
            'warning': '⚠️ These are TEST tokens only! Do NOT use in production!',
            'tokens': tokens,
            'keys': {
                'public_key': self.public_key.decode(),
                'note': 'Use this public key in AUTH_JWT_PUBLIC_KEY environment variable'
            },
            'configuration': {
                'jwt': {
                    'description': 'To use JWT tokens, configure:',
                    'env_vars': {
                        'AUTH_OAUTH_ENABLED': 'true',
                        'AUTH_JWT_ENABLED': 'true',
                        'AUTH_JWT_ISSUER': 'https://test-idp.example.com',
                        'AUTH_JWT_AUDIENCE': 'scim-service-provider',
                        'AUTH_JWT_ALGORITHM': 'RS256',
                        'AUTH_JWT_PUBLIC_KEY': '<copy public_key from above>'
                    }
                },
                'basic_auth': {
                    'description': 'To use Basic Auth, configure:',
                    'env_vars': {
                        'AUTH_OAUTH_ENABLED': 'false',
                        'AUTH_BASIC_ENABLED': 'true',
                        'AUTH_BASIC_USERS': 'admin:8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918'
                    },
                    'note': 'Use password_hash from tokens.basic_auth above'
                },
                'no_auth': {
                    'description': 'To disable authentication (development only):',
                    'env_vars': {
                        'AUTH_OAUTH_ENABLED': 'false',
                        'AUTH_BASIC_ENABLED': 'false'
                    }
                }
            },
            'usage_examples': {
                'curl_jwt': f"curl -H 'Authorization: Bearer <token>' http://localhost:5000/scim/v2/Users",
                'curl_basic': "curl -u admin:admin123 http://localhost:5000/scim/v2/Users",
                'python_jwt': "headers = {'Authorization': 'Bearer <token>'}",
                'python_basic': "auth = ('admin', 'admin123')"
            }
        }
        
        return response, 200
    
    def generate_custom_token(self, request_data: Dict[str, Any]) -> tuple[Dict[str, Any], int]:
        """
        POST /api/dev/tokens/generate
        Generate custom token with specified scopes
        """
        # Get parameters from request
        scopes = request_data.get('scopes', ['scim.read'])
        subject = request_data.get('subject', 'test-user')
        expires_in_hours = request_data.get('expires_in_hours', 24)
        
        # Validate scopes
        valid_scopes = {'scim.read', 'scim.write', 'supportingdata.read'}
        invalid_scopes = set(scopes) - valid_scopes
        if invalid_scopes:
            return {
                'error': f'Invalid scopes: {", ".join(invalid_scopes)}',
                'valid_scopes': list(valid_scopes)
            }, 400
        
        # Generate token
        token = self._create_jwt_token(scopes, subject, expires_in_hours)
        
        # Decode to show payload
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        return {
            'token': token,
            'payload': decoded,
            'usage': {
                'authorization_header': f'Bearer {token}',
                'curl_example': f"curl -H 'Authorization: Bearer {token}' http://localhost:5000/scim/v2/Users"
            }
        }, 200
    
    def get_public_key(self) -> tuple[Dict[str, Any], int]:
        """
        GET /api/dev/tokens/public-key
        Get the public key for JWT validation
        """
        return {
            'public_key': self.public_key.decode(),
            'algorithm': 'RS256',
            'usage': 'Set this as AUTH_JWT_PUBLIC_KEY environment variable',
            'format': 'PEM'
        }, 200


# Made with Bob