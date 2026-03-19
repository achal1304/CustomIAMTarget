#!/usr/bin/env python3
"""
JWT Token Generator for Testing
Generates valid JWT tokens for testing authentication
"""

import jwt
import datetime
import hashlib
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import json


def generate_rsa_keys():
    """Generate RSA key pair"""
    print("Generating RSA key pair...")
    
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


def create_jwt_token(private_key, scopes, issuer='https://test-idp.example.com',
                     audience='scim-service-provider', subject='test-user',
                     expires_in_hours=24):
    """Create JWT token with specified scopes"""
    now = datetime.datetime.utcnow()
    
    payload = {
        'iss': issuer,
        'aud': audience,
        'sub': subject,
        'scope': ' '.join(scopes),
        'exp': now + datetime.timedelta(hours=expires_in_hours),
        'iat': now,
        'nbf': now,
        'jti': f'test-token-{int(now.timestamp())}'
    }
    
    token = jwt.encode(payload, private_key, algorithm='RS256')
    return token


def decode_token(token, public_key=None):
    """Decode JWT token (without verification for inspection)"""
    try:
        # Decode without verification to inspect
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded
    except Exception as e:
        return f"Error decoding: {e}"


def generate_basic_auth_hash(password):
    """Generate SHA-256 hash for Basic Auth password"""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_basic_auth_header(username, password):
    """Generate Basic Auth header value"""
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║         JWT Token Generator for Testing                      ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    # Generate RSA keys
    private_key, public_key = generate_rsa_keys()
    
    print("\n" + "="*70)
    print("RSA KEYS (Save these for configuration)")
    print("="*70)
    
    print("\nPRIVATE KEY (Keep secret!):")
    print(private_key.decode())
    
    print("\nPUBLIC KEY (Use in AUTH_JWT_PUBLIC_KEY):")
    print(public_key.decode())
    
    # Generate tokens with different scopes
    print("\n" + "="*70)
    print("GENERATED JWT TOKENS")
    print("="*70)
    
    tokens = {
        'read_only': {
            'scopes': ['scim.read'],
            'description': 'Can only read SCIM resources'
        },
        'write_only': {
            'scopes': ['scim.write'],
            'description': 'Can only write SCIM resources'
        },
        'full_scim': {
            'scopes': ['scim.read', 'scim.write'],
            'description': 'Full SCIM access'
        },
        'full_access': {
            'scopes': ['scim.read', 'scim.write', 'supportingdata.read'],
            'description': 'Full access to all endpoints'
        },
        'supporting_data': {
            'scopes': ['supportingdata.read'],
            'description': 'Can only read supporting data'
        }
    }
    
    generated_tokens = {}
    
    for name, config in tokens.items():
        token = create_jwt_token(private_key, config['scopes'])
        generated_tokens[name] = token
        
        print(f"\n{name.upper().replace('_', ' ')} TOKEN:")
        print(f"Description: {config['description']}")
        print(f"Scopes: {', '.join(config['scopes'])}")
        print(f"Token: {token}")
        
        # Decode and show payload
        decoded = decode_token(token)
        print(f"Payload: {json.dumps(decoded, indent=2)}")
    
    # Generate Basic Auth examples
    print("\n" + "="*70)
    print("BASIC AUTHENTICATION")
    print("="*70)
    
    basic_auth_examples = [
        {'username': 'admin', 'password': 'admin123'},
        {'username': 'testuser', 'password': 'testpass123'},
        {'username': 'readonly', 'password': 'readonly123'}
    ]
    
    for example in basic_auth_examples:
        username = example['username']
        password = example['password']
        password_hash = generate_basic_auth_hash(password)
        auth_header = generate_basic_auth_header(username, password)
        
        print(f"\nUsername: {username}")
        print(f"Password: {password}")
        print(f"SHA-256 Hash: {password_hash}")
        print(f"Authorization Header: {auth_header}")
        print(f"Config: AUTH_BASIC_USERS={username}:{password_hash}")
    
    # Generate curl examples
    print("\n" + "="*70)
    print("CURL EXAMPLES")
    print("="*70)
    
    base_url = "http://localhost:5000"
    
    print(f"\n1. List Users with READ-ONLY token:")
    print(f"curl -X GET {base_url}/scim/v2/Users \\")
    print(f"  -H 'Authorization: Bearer {generated_tokens['read_only'][:50]}...'")
    
    print(f"\n2. Create User with FULL ACCESS token:")
    print(f"curl -X POST {base_url}/scim/v2/Users \\")
    print(f"  -H 'Authorization: Bearer {generated_tokens['full_access'][:50]}...' \\")
    print(f"  -H 'Content-Type: application/scim+json' \\")
    print(f"  -d '{{...}}'")
    
    print(f"\n3. List Users with Basic Auth:")
    print(f"curl -X GET {base_url}/scim/v2/Users \\")
    print(f"  -u admin:admin123")
    
    print(f"\n4. Get Supporting Data:")
    print(f"curl -X GET {base_url}/api/supporting-data/roles \\")
    print(f"  -H 'Authorization: Bearer {generated_tokens['full_access'][:50]}...'")
    
    # Configuration instructions
    print("\n" + "="*70)
    print("CONFIGURATION INSTRUCTIONS")
    print("="*70)
    
    print("\nTo use these tokens, configure your environment:")
    print("\n# For JWT validation:")
    print("export AUTH_OAUTH_ENABLED=true")
    print("export AUTH_JWT_ENABLED=true")
    print("export AUTH_JWT_ISSUER=https://test-idp.example.com")
    print("export AUTH_JWT_AUDIENCE=scim-service-provider")
    print("export AUTH_JWT_ALGORITHM=RS256")
    print("# Copy the PUBLIC KEY above and set:")
    print("export AUTH_JWT_PUBLIC_KEY='-----BEGIN PUBLIC KEY-----...'")
    
    print("\n# For Basic Auth:")
    print("export AUTH_OAUTH_ENABLED=false")
    print("export AUTH_BASIC_ENABLED=true")
    print("export AUTH_BASIC_USERS='admin:8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918'")
    
    print("\n# For no authentication (development only):")
    print("export AUTH_OAUTH_ENABLED=false")
    print("export AUTH_BASIC_ENABLED=false")
    
    # Save tokens to file
    print("\n" + "="*70)
    print("SAVING TOKENS TO FILE")
    print("="*70)
    
    output = {
        'private_key': private_key.decode(),
        'public_key': public_key.decode(),
        'tokens': generated_tokens,
        'basic_auth': {
            ex['username']: {
                'password': ex['password'],
                'hash': generate_basic_auth_hash(ex['password'])
            }
            for ex in basic_auth_examples
        }
    }
    
    with open('test_tokens.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n✅ Tokens saved to: test_tokens.json")
    print("\n⚠️  WARNING: These are TEST tokens only!")
    print("   - Do NOT use in production")
    print("   - Private key is exposed")
    print("   - Tokens are long-lived (24 hours)")
    
    print("\n" + "="*70)


if __name__ == '__main__':
    main()

# Made with Bob
