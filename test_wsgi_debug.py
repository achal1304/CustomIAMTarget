#!/usr/bin/env python3
"""Debug WSGI middleware"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Set up test environment
os.environ['AUTH_OAUTH_ENABLED'] = 'true'
os.environ['AUTH_JWT_ENABLED'] = 'true'
os.environ['AUTH_JWT_ISSUER'] = 'https://test-idp.example.com'
os.environ['AUTH_JWT_AUDIENCE'] = 'scim-service-provider'
os.environ['AUTH_JWT_ALGORITHM'] = 'RS256'

TEST_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxtbvLqWCvinUeJvj3U17
jONV2SWDDb/bepaAkPuRFOUjGZKug4x48AVOI5PY1EofKnOUQd/nV6IcuXMkF8v+
kso8sastv1JuEz191aWp7GAXxsEKAfwx6CDbiSwwJ7vlh3iAerXIqaqpIoz3T8Db
JFoS2rTrJbh2kI2RacMcllNIEDloBS4ksprRrl2dDEKIotoLx3ETsVDhYHKBi0Cw
o/xuZN443pQvh53xKnGtFD/GRO8rLC8XR7b8P7dYZ+3WnrrFEgeQXxdWfk1Ofj6y
t9iWY3ChbayaqQr0408sy2NUV1Eh7WVRzHuAdVx+KMVHBxTJJWXAmcLWtsTQ4sPV
xwIDAQAB
-----END PUBLIC KEY-----"""

os.environ['AUTH_JWT_PUBLIC_KEY'] = TEST_PUBLIC_KEY
os.environ['AUTH_BASIC_ENABLED'] = 'false'
os.environ['AUTH_MTLS_ENABLED'] = 'false'

TEST_TOKEN = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3Rlc3QtaWRwLmV4YW1wbGUuY29tIiwiYXVkIjoic2NpbS1zZXJ2aWNlLXByb3ZpZGVyIiwic3ViIjoidGVzdC11c2VyIiwic2NvcGUiOiJzY2ltLnJlYWQgc2NpbS53cml0ZSBzdXBwb3J0aW5nZGF0YS5yZWFkIiwiZXhwIjoxNzc0MDAzODIzLCJpYXQiOjE3NzM5MTc0MjMsIm5iZiI6MTc3MzkxNzQyMywianRpIjoidGVzdC10b2tlbi0xNzczODk3NjIzIn0.t15b_iP3Hnqe7ycYU_-3xnYyOlYQ0hx-lE-pJJKZB352B4uKcKBlxk5sW33ORA7VrG2RjzS1KEKbK-4GvpRHPcwmd9VMDXKIk5aAu7tji8dxN_d0Z0akvUwdsDho6pCKyp4IIkQnoUwGk4WJqqGrD95EIjKlhMyG5WQ-W7bJoNQtzIzld60JlWRzrTCZd2mtZ5zdEiYy8xMCDgPAgci1AHrrKFPnYr81kYQQdvQ_PCTcxmpbIf4rQyWrUgvCciqThCrRHbnxqTT8rTrP6RlknBqvDZnVv-vDZQH2EYA2Oz569eehuvY1cCSo6BxmtSe6H2xevl3Sgb-kQXXPjCA-Jw'

from app import app

class AuthInjectingMiddleware:
    """WSGI middleware that injects auth header into all requests"""
    def __init__(self, wsgi_app):
        self.app = wsgi_app
    
    def __call__(self, environ, start_response):
        print(f"[WSGI] Before injection: HTTP_AUTHORIZATION = {environ.get('HTTP_AUTHORIZATION', 'NOT SET')}")
        # Inject Authorization header if not present
        if 'HTTP_AUTHORIZATION' not in environ:
            environ['HTTP_AUTHORIZATION'] = f'Bearer {TEST_TOKEN}'
            print(f"[WSGI] Injected auth header")
        print(f"[WSGI] After injection: HTTP_AUTHORIZATION = {environ.get('HTTP_AUTHORIZATION', 'NOT SET')}")
        return self.app(environ, start_response)

app.config['TESTING'] = True
app.wsgi_app = AuthInjectingMiddleware(app.wsgi_app)

client = app.test_client()

print("\n=== Test without explicit auth header ===")
response = client.post('/scim/v2/Users',
                      json={"schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                            "userName": "test@example.com",
                            "active": True},
                      content_type='application/json')
print(f"Status: {response.status_code}")
print(f"Response: {response.get_json()}")

# Made with Bob
