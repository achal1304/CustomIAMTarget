#!/usr/bin/env python3
"""
Test mTLS Authentication
Simulates mTLS by setting environment variables that Flask would receive from nginx
"""

import os
import sys
import requests
from flask import Flask
from auth.config import AuthConfig
from auth.middleware import AuthMiddleware

def test_mtls_authentication():
    """Test mTLS authentication with different certificates"""
    
    print("=" * 70)
    print("mTLS AUTHENTICATION TEST")
    print("=" * 70)
    print()
    
    # Load auth config
    config = AuthConfig.from_env()
    
    print("📋 Current mTLS Configuration:")
    print(f"   Enabled: {config.mtls.enabled}")
    print(f"   Require Cert: {config.mtls.require_client_cert}")
    print(f"   CA Certs Path: {config.mtls.trusted_ca_certs_path}")
    print()
    
    print("📋 Certificate Mappings:")
    for cn, identity in config.mtls.cert_subject_mapping.items():
        scopes = config.mtls.cert_scopes.get(identity, config.mtls.default_scopes)
        print(f"   CN={cn} → {identity}")
        print(f"      Scopes: {', '.join(scopes)}")
    print()
    
    # Test cases
    test_cases = [
        {
            'name': 'Admin Client (Full Access)',
            'cert_dn': 'CN=admin-client,O=SCIM Client,L=Test,ST=Test,C=US',
            'expected_identity': 'admin-client',
            'expected_scopes': ['scim.read', 'scim.write', 'supportingdata.read']
        },
        {
            'name': 'Read-Only Client',
            'cert_dn': 'CN=readonly-client,O=SCIM Client,L=Test,ST=Test,C=US',
            'expected_identity': 'readonly-client',
            'expected_scopes': ['scim.read', 'supportingdata.read']
        },
        {
            'name': 'SCIM Client (No Supporting Data)',
            'cert_dn': 'CN=scim-client,O=SCIM Client,L=Test,ST=Test,C=US',
            'expected_identity': 'scim-client',
            'expected_scopes': ['scim.read', 'scim.write']
        },
        {
            'name': 'Unknown Client (Default Scopes)',
            'cert_dn': 'CN=unknown-client,O=SCIM Client,L=Test,ST=Test,C=US',
            'expected_identity': 'unknown-client',
            'expected_scopes': ['scim.read']
        }
    ]
    
    print("=" * 70)
    print("RUNNING TESTS")
    print("=" * 70)
    print()
    
    from auth.authenticators import MutualTLSAuthenticator
    from flask import Request
    from werkzeug.test import EnvironBuilder
    
    authenticator = MutualTLSAuthenticator(config.mtls)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['name']}")
        print(f"   Certificate DN: {test['cert_dn']}")
        
        # Create mock request with certificate
        builder = EnvironBuilder(method='GET', path='/scim/v2/Users')
        env = builder.get_environ()
        env['SSL_CLIENT_CERT'] = 'present'
        env['SSL_CLIENT_S_DN'] = test['cert_dn']
        
        request = Request(env)
        
        # Authenticate
        result = authenticator.authenticate(request)
        
        # Check results
        if result.authenticated:
            print(f"   ✅ Authenticated: YES")
            print(f"   Identity: {result.identity}")
            print(f"   Scopes: {', '.join(result.scopes)}")
            
            # Verify identity and scopes
            if result.identity == test['expected_identity']:
                print(f"   ✅ Identity matches expected")
            else:
                print(f"   ❌ Identity mismatch! Expected: {test['expected_identity']}")
                failed += 1
                print()
                continue
            
            if set(result.scopes) == set(test['expected_scopes']):
                print(f"   ✅ Scopes match expected")
                passed += 1
            else:
                print(f"   ❌ Scopes mismatch!")
                print(f"      Expected: {', '.join(test['expected_scopes'])}")
                print(f"      Got: {', '.join(result.scopes)}")
                failed += 1
        else:
            print(f"   ❌ Authenticated: NO")
            print(f"   Error: {result.error}")
            failed += 1
        
        print()
    
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Total: {passed + failed}")
    print()
    
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed!")
        return 1


def test_with_server():
    """Test mTLS with running server (requires nginx)"""
    print()
    print("=" * 70)
    print("TESTING WITH RUNNING SERVER (requires nginx)")
    print("=" * 70)
    print()
    
    base_url = os.getenv('BASE_URL', 'http://localhost:5000')
    
    # Check if server is running
    try:
        response = requests.get(f"{base_url}/api/dev/tokens", timeout=2)
        print(f"✅ Server is running at {base_url}")
        print()
        
        # Show mTLS certificate info
        data = response.json()
        if 'tokens' in data and 'mtls' in data['tokens']:
            mtls_data = data['tokens']['mtls']
            if mtls_data and isinstance(mtls_data, dict) and len(mtls_data) > 0:
                print("📋 Available mTLS Certificates:")
                for cert_name, cert_info in mtls_data.items():
                    if isinstance(cert_info, dict):
                        print(f"\n   {cert_name.upper()}:")
                        print(f"      Identity: {cert_info.get('identity', 'N/A')}")
                        print(f"      Certificate: {cert_info.get('certificate', 'N/A')}")
                        scopes = cert_info.get('scopes', [])
                        if isinstance(scopes, list):
                            print(f"      Scopes: {', '.join(scopes)}")
                        print(f"      Description: {cert_info.get('description', 'N/A')}")
                print()
                print("⚠️  To test with real certificates, you need nginx configured for mTLS")
            else:
                print("⚠️  mTLS certificates not available in API response")
                print("   Restart server to load mTLS configuration")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not running at {base_url}")
        print(f"   Start server: python app.py")
    
    print()


if __name__ == '__main__':
    # Enable mTLS for testing
    os.environ['AUTH_MTLS_ENABLED'] = 'true'
    
    # Run unit tests
    exit_code = test_mtls_authentication()
    
    # Test with server if running
    test_with_server()
    
    sys.exit(exit_code)

# Made with Bob
