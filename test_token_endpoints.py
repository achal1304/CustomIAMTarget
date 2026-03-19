#!/usr/bin/env python3
"""
Quick test script for token generation endpoints
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from api.token_endpoints import TokenEndpoints
import json

def test_token_endpoints():
    """Test token endpoint functionality"""
    print("Testing Token Endpoints...")
    print("=" * 70)
    
    # Initialize
    token_endpoints = TokenEndpoints()
    
    # Test 1: Get all tokens
    print("\n1. Testing get_all_tokens()...")
    response, status = token_endpoints.get_all_tokens()
    assert status == 200, f"Expected 200, got {status}"
    assert 'tokens' in response, "Response should have 'tokens' key"
    assert 'jwt' in response['tokens'], "Should have JWT tokens"
    assert 'basic_auth' in response['tokens'], "Should have basic auth"
    print("   ✓ get_all_tokens() works")
    print(f"   - Generated {len(response['tokens']['jwt'])} JWT token types")
    print(f"   - Generated {len(response['tokens']['basic_auth'])} basic auth credentials")
    
    # Test 2: Generate custom token
    print("\n2. Testing generate_custom_token()...")
    request_data = {
        'scopes': ['scim.read', 'scim.write'],
        'subject': 'test-user',
        'expires_in_hours': 24
    }
    response, status = token_endpoints.generate_custom_token(request_data)
    assert status == 200, f"Expected 200, got {status}"
    assert 'token' in response, "Response should have 'token' key"
    assert 'payload' in response, "Response should have 'payload' key"
    print("   ✓ generate_custom_token() works")
    print(f"   - Token subject: {response['payload']['sub']}")
    print(f"   - Token scopes: {response['payload']['scope']}")
    
    # Test 3: Invalid scopes
    print("\n3. Testing invalid scopes...")
    request_data = {
        'scopes': ['invalid.scope']
    }
    response, status = token_endpoints.generate_custom_token(request_data)
    assert status == 400, f"Expected 400, got {status}"
    assert 'error' in response, "Should return error"
    print("   ✓ Invalid scopes rejected correctly")
    
    # Test 4: Get public key
    print("\n4. Testing get_public_key()...")
    response, status = token_endpoints.get_public_key()
    assert status == 200, f"Expected 200, got {status}"
    assert 'public_key' in response, "Response should have 'public_key' key"
    assert response['public_key'].startswith('-----BEGIN PUBLIC KEY-----'), "Should be PEM format"
    print("   ✓ get_public_key() works")
    print(f"   - Algorithm: {response['algorithm']}")
    
    print("\n" + "=" * 70)
    print("✅ All tests passed!")
    print("\nToken endpoints are ready to use:")
    print("  GET  /api/dev/tokens")
    print("  POST /api/dev/tokens/generate")
    print("  GET  /api/dev/tokens/public-key")
    print("\nSee TOKEN_GENERATION_GUIDE.md for usage instructions.")

if __name__ == '__main__':
    try:
        test_token_endpoints()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Made with Bob
