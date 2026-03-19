#!/bin/bash
# Start the SCIM 2.0 Service Provider Server

echo "Starting SCIM 2.0 Service Provider..."
echo ""

# Set default configuration
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-5000}
export BASE_URL=${BASE_URL:-http://localhost:5000}
export DEBUG=${DEBUG:-True}

# Configure JWT Authentication (required for token validation)
export AUTH_JWT_PUBLIC_KEY='-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwHJUJbufLISs0FjJx/vB
C2afDVzr7igVBwpwbnlvjx1i3lmPhn8J90qN9mb2fCSUfsdwKOIV3OApEhnLsQVF
IJnlrnDmehgZqxwKgw2raA2TGm94+awg5SEuqMeXNiA85EruhHXsPety4f1EG+An
TAyVAlQlwHdX5v/OPDpLCKkxgJE+CkguBnT2GM+9K10dqlVxdGKy9q8WglOPlNxd
FQPo0go6AJpzCyvOARfnlSFL+9U/Kz7uxEPzV8L5roMGQFjpl5nZ9Rp1ZV3meawx
j2aduZLaerzQ762N+Fpz+VGmkcKkMddmDCswP+hYGOcIsLFKOE/cTIXViAU891zg
KQIDAQAB
-----END PUBLIC KEY-----'
export AUTH_JWT_ISSUER="https://test-idp.example.com"
export AUTH_JWT_AUDIENCE="scim-service-provider"

echo "✓ Authentication configured (OAuth/JWT, Basic Auth, mTLS)"
echo "✓ Get tokens from: http://localhost:${PORT}/api/dev/tokens"
echo "✓ Swagger UI: http://localhost:${PORT}/api/docs"
echo ""

# Start the server
python3 app.py

# Made with Bob
