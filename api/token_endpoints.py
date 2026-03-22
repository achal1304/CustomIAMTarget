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
    
    # HARDCODED TEST KEYS - DO NOT CHANGE
    # These keys are fixed for consistent testing across all environments
    _HARDCODED_PRIVATE_KEY = b"""-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDAclQlu58shKzQ
WMnH+8ELZp8NXOvuKBUHCnBueW+PHWLeWY+Gfwn3So32ZvZ8JJR+x3Ao4hXc4CkS
GcuxBUUgmeWucOZ6GBmrHAqDDatoDZMab3j5rCDlIS6ox5c2IDzkSu6Edew963Lh
/UQb4CdMDJUCVCXAd1fm/848OksIqTGAkT4KSC4GdPYYz70rXR2qVXF0YrL2rxaC
U4+U3F0VA+jSCjoAmnMLK84BF+eVIUv71T8rPu7EQ/NXwvmugwZAWOmXmdn1GnVl
XeZ5rDGPZp25ktp6vNDvrY34WnP5UaaRwqQx12YMKzA/6FgY5wiwsUo4T9xMhdWI
BTz3XOApAgMBAAECggEABESU0qhm9uBeCm8ppxkmy8IDyCgAeyM27NV3BFrbleza
KYxgFzoVMRTdcfKQcqoyA99tle6GUG7FN7z24Y8NxykP6QQ2dvc2sdmDmdVGsPOk
yJrib9u4zV66GkKg5cb7FWSxsPeCMiZZAXjcgZIWn68OFUON+ccmcyhG/TAdbrdI
lp6qIIgYKEE52C8BnGQXQ/ujyYXWDNmeDloFJmMRmh/XzwAvYuMKdhefNveGNndR
B5q2P5Q2N+gXqpZBqH0quGH8Ad4eQCONwMnQRa1/CUsuA2xlfrEEtCQ8gH3bYIiN
pWPo5HQxT+YSku6NS9uKGxMWti7g7VxreMq50EplHQKBgQD/b3q/pMADrWZ28w0u
979DCgUKTis3rqA0bJqXFQ1VA5kMzWLz5W/oVPYYcYwDXclXsjMQtaHu9xy/SAJm
Xm7/KwbtpkxwDVH86lcZk1Hf3Lepns6iZg/EYuQdawnyZ/Q2WKr2FaPfmoNIIOfm
GQUcfCVZs84ZCehezsnCPZO21QKBgQDA3zYYnR9rPJ3Pd5KJJCAFU4zBa4i9ucET
nTPIHz9OUAOredvbGuZu29Rl+a94AuEIiuiHrh27bMBqLWLbXkI6CWjfNt50xBOV
JTE1ldNj3MV5a/79XiMnB8UsJDcQFOwIj9R6bGMfkGW6abDdXuwo5MQ5NtRSck07
zEOqdLQWBQKBgE2ayflFjYzQdsv2xe+aF4K/nY5m91xgco3a3RC/taA5iptIHyMo
dtpoTahZfwdazBwXqMoP1NXsP9ChiREe6awen2k+WATHFzy22aWMi5huz2H6PJ88
UNgCj3mclpYOHTURtUc0hegeYnpcfPf8bAAee56IMTqMNwvu2X9pA+LNAoGAUvAp
fRAj8KNSYWLT2rF0K5YwEwTA+oUkZ+DT4Zy+RljWGyj9yAybRtS1U1y5fewPBPNm
5uGS24P6gi4eMqMn63kcZdBcfO3MVfh2Xsqc6naHXJ16O03948zNlxvDqeC1V0Ey
Z6qwPWSEulK0wZ0OBM/LKadQSlvopmxCNMyWnFkCgYEAxOSF8PBjWKNxpzmFBEWU
+sHfVSncA9J7If+jId3EhM0ByIuJfF77NOPAVpjIjFKUsbLAxKJlpuP2TUfxXJ5j
chW8kYuPTcv/WUgOxOaFg2BHUVzgbu/BSt7IJf2kuHUvrikulPN6Mlw3+cT8O8PR
VYE1H3wWx/SM8WGYqB6KenE=
-----END PRIVATE KEY-----"""
    
    _HARDCODED_PUBLIC_KEY = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwHJUJbufLISs0FjJx/vB
C2afDVzr7igVBwpwbnlvjx1i3lmPhn8J90qN9mb2fCSUfsdwKOIV3OApEhnLsQVF
IJnlrnDmehgZqxwKgw2raA2TGm94+awg5SEuqMeXNiA85EruhHXsPety4f1EG+An
TAyVAlQlwHdX5v/OPDpLCKkxgJE+CkguBnT2GM+9K10dqlVxdGKy9q8WglOPlNxd
FQPo0go6AJpzCyvOARfnlSFL+9U/Kz7uxEPzV8L5roMGQFjpl5nZ9Rp1ZV3meawx
j2aduZLaerzQ762N+Fpz+VGmkcKkMddmDCswP+hYGOcIsLFKOE/cTIXViAU891zg
KQIDAQAB
-----END PUBLIC KEY-----"""
    
    def __init__(self):
        """Initialize with hardcoded test RSA key pair"""
        self.private_key = self._HARDCODED_PRIVATE_KEY
        self.public_key = self._HARDCODED_PUBLIC_KEY
        print("✓ Using hardcoded test RSA keys for consistent token generation")
    
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
            },
            'mtls': {
                'admin_client': {
                    'certificate': 'certs/client-admin.pem',
                    'identity': 'admin-client',
                    'scopes': ['scim.read', 'scim.write', 'supportingdata.read'],
                    'description': 'Admin client certificate with full access',
                    'curl_example': 'curl --cert certs/client-admin.pem --cacert certs/ca-cert.pem https://localhost:5000/scim/v2/Users'
                },
                'readonly_client': {
                    'certificate': 'certs/client-readonly.pem',
                    'identity': 'readonly-client',
                    'scopes': ['scim.read', 'supportingdata.read'],
                    'description': 'Read-only client certificate',
                    'curl_example': 'curl --cert certs/client-readonly.pem --cacert certs/ca-cert.pem https://localhost:5000/scim/v2/Users'
                },
                'scim_client': {
                    'certificate': 'certs/client-scim.pem',
                    'identity': 'scim-client',
                    'scopes': ['scim.read', 'scim.write'],
                    'description': 'SCIM-only client certificate (no supporting data access)',
                    'curl_example': 'curl --cert certs/client-scim.pem --cacert certs/ca-cert.pem https://localhost:5000/scim/v2/Users'
                },
                'note': 'Run ./tools/generate_mtls_certs.sh to generate certificates if not already present'
            }
        }
        
        # Add configuration instructions
        response = {
            'warning': '⚠️ These are TEST tokens/certificates only! Do NOT use in production!',
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
                'mtls': {
                    'description': 'To use mTLS (requires nginx/Apache configuration):',
                    'env_vars': {
                        'AUTH_MTLS_ENABLED': 'true',
                        'AUTH_MTLS_REQUIRE_CERT': 'true',
                        'AUTH_MTLS_CA_CERTS_PATH': 'certs/ca-cert.pem'
                    },
                    'note': 'Requires web server (nginx/Apache) configured for TLS client authentication. See MTLS_SETUP_GUIDE.md'
                },
                'no_auth': {
                    'description': 'To disable authentication (development only):',
                    'env_vars': {
                        'AUTH_OAUTH_ENABLED': 'false',
                        'AUTH_BASIC_ENABLED': 'false',
                        'AUTH_MTLS_ENABLED': 'false'
                    }
                }
            },
            'usage_examples': {
                'curl_jwt': f"curl -H 'Authorization: Bearer <token>' http://localhost:5000/scim/v2/Users",
                'curl_basic': "curl -u admin:admin123 http://localhost:5000/scim/v2/Users",
                'curl_mtls': "curl --cert certs/client-admin.pem --cacert certs/ca-cert.pem https://localhost:5000/scim/v2/Users",
                'python_jwt': "headers = {'Authorization': 'Bearer <token>'}",
                'python_basic': "auth = ('admin', 'admin123')",
                'python_mtls': "cert=('certs/client-admin.pem',), verify='certs/ca-cert.pem'"
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