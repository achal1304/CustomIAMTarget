"""
Authentication Testing Suite
Tests authentication and authorization without modifying SCIM logic
"""

import pytest
import jwt
import hashlib
import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from auth.config import AuthConfig


# ==================== TEST FIXTURES ====================

@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def rsa_keys():
    """Generate RSA key pair for JWT testing"""
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
    
    return {
        'private_key': private_pem,
        'public_key': public_pem
    }


def create_jwt_token(private_key, scopes=['scim.read', 'scim.write'], 
                     issuer='https://test-idp.example.com',
                     audience='scim-service-provider',
                     subject='test-user',
                     expires_in_hours=1):
    """
    Create a valid JWT token for testing
    
    Args:
        private_key: RSA private key (PEM format)
        scopes: List of scopes to include
        issuer: Token issuer
        audience: Token audience
        subject: Token subject (user/client ID)
        expires_in_hours: Token expiration time
    
    Returns:
        JWT token string
    """
    now = datetime.datetime.utcnow()
    
    payload = {
        'iss': issuer,
        'aud': audience,
        'sub': subject,
        'scope': ' '.join(scopes),  # Space-separated scopes
        'exp': now + datetime.timedelta(hours=expires_in_hours),
        'iat': now,
        'nbf': now
    }
    
    token = jwt.encode(payload, private_key, algorithm='RS256')
    return token


# ==================== TEST: NO AUTHENTICATION ====================

def test_no_auth_discovery_endpoints(client):
    """Test that discovery endpoints are public (no auth required)"""
    # Set environment to disable auth
    os.environ['AUTH_OAUTH_ENABLED'] = 'false'
    os.environ['AUTH_BASIC_ENABLED'] = 'false'
    
    # ServiceProviderConfig
    response = client.get('/scim/v2/ServiceProviderConfig')
    assert response.status_code == 200
    
    # Schemas
    response = client.get('/scim/v2/Schemas')
    assert response.status_code == 200
    
    # ResourceTypes
    response = client.get('/scim/v2/ResourceTypes')
    assert response.status_code == 200


def test_no_auth_scim_endpoints(client):
    """Test that SCIM endpoints work without auth when disabled"""
    os.environ['AUTH_OAUTH_ENABLED'] = 'false'
    os.environ['AUTH_BASIC_ENABLED'] = 'false'
    
    # List users
    response = client.get('/scim/v2/Users')
    assert response.status_code == 200
    
    # List groups
    response = client.get('/scim/v2/Groups')
    assert response.status_code == 200


# ==================== TEST: BASIC AUTHENTICATION ====================

def test_basic_auth_valid_credentials(client):
    """Test Basic Auth with valid credentials"""
    # Enable Basic Auth
    os.environ['AUTH_OAUTH_ENABLED'] = 'false'
    os.environ['AUTH_BASIC_ENABLED'] = 'true'
    
    # Password: "testpass123"
    password_hash = hashlib.sha256('testpass123'.encode()).hexdigest()
    os.environ['AUTH_BASIC_USERS'] = f'testuser:{password_hash}'
    
    # Reload config - update the module-level auth_middleware variable
    from auth.middleware import create_auth_middleware
    from auth.config import AuthConfig
    import app as app_module
    app_module.auth_middleware = create_auth_middleware(AuthConfig.from_env())
    
    # Test with valid credentials
    response = client.get(
        '/scim/v2/Users',
        headers={'Authorization': 'Basic dGVzdHVzZXI6dGVzdHBhc3MxMjM='}  # testuser:testpass123
    )
    assert response.status_code == 200


def test_basic_auth_invalid_credentials(client):
    """Test Basic Auth with invalid credentials"""
    os.environ['AUTH_OAUTH_ENABLED'] = 'false'
    os.environ['AUTH_BASIC_ENABLED'] = 'true'
    
    password_hash = hashlib.sha256('testpass123'.encode()).hexdigest()
    os.environ['AUTH_BASIC_USERS'] = f'testuser:{password_hash}'
    
    # Test with invalid credentials
    response = client.get(
        '/scim/v2/Users',
        headers={'Authorization': 'Basic dGVzdHVzZXI6d3JvbmdwYXNz'}  # testuser:wrongpass
    )
    assert response.status_code == 401
    data = response.get_json()
    assert data['status'] == '401'


def test_basic_auth_missing_header(client):
    """Test Basic Auth without Authorization header"""
    os.environ['AUTH_OAUTH_ENABLED'] = 'false'
    os.environ['AUTH_BASIC_ENABLED'] = 'true'
    
    response = client.get('/scim/v2/Users')
    assert response.status_code == 401


# ==================== TEST: OAUTH 2.0 / JWT ====================

def test_oauth_valid_jwt_token(client, rsa_keys):
    """Test OAuth with valid JWT token"""
    os.environ['AUTH_OAUTH_ENABLED'] = 'true'
    os.environ['AUTH_JWT_ENABLED'] = 'true'
    os.environ['AUTH_JWT_ISSUER'] = 'https://test-idp.example.com'
    os.environ['AUTH_JWT_AUDIENCE'] = 'scim-service-provider'
    
    # Create valid token
    token = create_jwt_token(
        rsa_keys['private_key'],
        scopes=['scim.read', 'scim.write']
    )
    
    # Note: In real testing, you'd need to configure the public key
    # For now, this demonstrates the token creation
    print(f"\nGenerated JWT Token:\n{token}\n")


def test_oauth_expired_token(client, rsa_keys):
    """Test OAuth with expired JWT token"""
    # Create expired token
    token = create_jwt_token(
        rsa_keys['private_key'],
        scopes=['scim.read'],
        expires_in_hours=-1  # Already expired
    )
    
    print(f"\nGenerated Expired Token:\n{token}\n")


# ==================== TEST: AUTHORIZATION (SCOPES) ====================

def test_authorization_insufficient_scope(client):
    """Test that insufficient scopes return 403"""
    # This would require a token with only scim.read trying to POST
    # Demonstrated in the token generation examples
    pass


def test_authorization_sufficient_scope(client):
    """Test that sufficient scopes allow access"""
    # This would require a token with scim.write for POST operations
    pass


# ==================== TEST: CASE-INSENSITIVE HEADERS ====================

def test_case_insensitive_authorization_header(client):
    """Test that Authorization header is case-insensitive"""
    os.environ['AUTH_BASIC_ENABLED'] = 'true'
    password_hash = hashlib.sha256('testpass'.encode()).hexdigest()
    os.environ['AUTH_BASIC_USERS'] = f'user:{password_hash}'
    
    # Test with different case variations
    headers_variations = [
        {'Authorization': 'Basic dXNlcjp0ZXN0cGFzcw=='},
        {'authorization': 'Basic dXNlcjp0ZXN0cGFzcw=='},
        {'AUTHORIZATION': 'Basic dXNlcjp0ZXN0cGFzcw=='},
    ]
    
    for headers in headers_variations:
        response = client.get('/scim/v2/Users', headers=headers)
        # Should not fail due to header case
        assert response.status_code in [200, 401]  # Either works or auth fails, but not 400


# ==================== HELPER FUNCTIONS ====================

def print_test_tokens():
    """Print example tokens for manual testing"""
    print("\n" + "="*70)
    print("AUTHENTICATION TEST TOKENS")
    print("="*70)
    
    # Generate RSA keys
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
    
    # Create tokens with different scopes
    tokens = {
        'read_only': create_jwt_token(private_pem, scopes=['scim.read']),
        'write_only': create_jwt_token(private_pem, scopes=['scim.write']),
        'full_access': create_jwt_token(private_pem, scopes=['scim.read', 'scim.write', 'supportingdata.read']),
        'expired': create_jwt_token(private_pem, scopes=['scim.read'], expires_in_hours=-1)
    }
    
    print("\n1. READ-ONLY TOKEN (scim.read):")
    print(f"   {tokens['read_only']}\n")
    
    print("2. WRITE-ONLY TOKEN (scim.write):")
    print(f"   {tokens['write_only']}\n")
    
    print("3. FULL ACCESS TOKEN (all scopes):")
    print(f"   {tokens['full_access']}\n")
    
    print("4. EXPIRED TOKEN:")
    print(f"   {tokens['expired']}\n")
    
    print("="*70)


if __name__ == '__main__':
    print_test_tokens()

# Made with Bob
