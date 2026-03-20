#!/bin/bash
# Authentication Examples for SCIM 2.0 Service Provider
# Demonstrates various authentication mechanisms
# Usage: ./authentication-examples.sh [base_url]
# Examples:
#   ./authentication-examples.sh                              # Use localhost
#   ./authentication-examples.sh https://myapp.onrender.com   # Use remote server

# Accept URL as parameter, or use BASE_URL env var, or default to localhost
if [ -n "$1" ]; then
    BASE_URL="$1"
elif [ -n "$BASE_URL" ]; then
    BASE_URL="$BASE_URL"
else
    BASE_URL="http://localhost:5000"
fi

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     SCIM 2.0 Authentication Examples                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Testing server: $BASE_URL"
echo ""

# ==================== PUBLIC ENDPOINTS (NO AUTH) ====================
echo "1. Public Endpoints (No Authentication Required)"
echo "   Discovery endpoints are public and don't require authentication"
echo ""

echo "   ServiceProviderConfig:"
curl -s -X GET "${BASE_URL}/scim/v2/ServiceProviderConfig" | jq '.'
echo ""

echo "   Schemas:"
curl -s -X GET "${BASE_URL}/scim/v2/Schemas" | jq '.Resources[0].name'
echo ""

# ==================== OAUTH 2.0 BEARER TOKEN ====================
echo "2. OAuth 2.0 Bearer Token Authentication"
echo "   Most common authentication method for production"
echo ""

# Example JWT token (this is a mock token for demonstration)
# In production, obtain from your IdP (Azure AD, Okta, etc.)
JWT_TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3Rlc3QtaWRwLmV4YW1wbGUuY29tIiwiYXVkIjoic2NpbS1zZXJ2aWNlLXByb3ZpZGVyIiwic3ViIjoidGVzdC11c2VyIiwic2NvcGUiOiJzY2ltLnJlYWQgc2NpbS53cml0ZSIsImV4cCI6OTk5OTk5OTk5OSwiaWF0IjoxNjAwMDAwMDAwfQ.mock-signature"

echo "   List Users with Bearer Token:"
echo "   curl -X GET ${BASE_URL}/scim/v2/Users \\"
echo "     -H \"Authorization: Bearer \${JWT_TOKEN}\""
echo ""

# Uncomment to test (requires valid token and auth enabled)
# curl -X GET "${BASE_URL}/scim/v2/Users" \
#   -H "Authorization: Bearer ${JWT_TOKEN}" | jq '.'

echo "   Expected Response (with valid token):"
echo "   {\"schemas\":[...],\"totalResults\":0,\"Resources\":[]}"
echo ""

echo "   Expected Error (without token):"
echo "   {\"schemas\":[\"urn:ietf:params:scim:api:messages:2.0:Error\"],\"status\":\"401\",\"detail\":\"Authentication required\"}"
echo ""

# ==================== HTTP BASIC AUTHENTICATION ====================
echo "3. HTTP Basic Authentication"
echo "   For development/testing only - NOT recommended for production"
echo ""

echo "   List Users with Basic Auth:"
echo "   curl -X GET ${BASE_URL}/scim/v2/Users \\"
echo "     -u admin:password"
echo ""

# Uncomment to test (requires basic auth enabled)
# curl -X GET "${BASE_URL}/scim/v2/Users" \
#   -u admin:password | jq '.'

echo "   Generate password hash for configuration:"
echo "   echo -n \"mypassword\" | sha256sum"
echo ""

# ==================== AUTHENTICATED SCIM OPERATIONS ====================
echo "4. Authenticated SCIM Operations"
echo ""

echo "   Create User (requires scim.write scope):"
cat << 'EOF'
curl -X POST ${BASE_URL}/scim/v2/Users \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/scim+json" \
  -d '{
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
    "userName": "john.doe@example.com",
    "name": {
      "givenName": "John",
      "familyName": "Doe"
    },
    "emails": [{
      "value": "john.doe@example.com",
      "primary": true
    }],
    "active": true
  }'
EOF
echo ""

echo "   Update User (requires scim.write scope):"
cat << 'EOF'
curl -X PATCH ${BASE_URL}/scim/v2/Users/{user-id} \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/scim+json" \
  -d '{
    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
    "Operations": [{
      "op": "replace",
      "path": "active",
      "value": false
    }]
  }'
EOF
echo ""

echo "   List Groups (requires scim.read scope):"
echo "   curl -X GET ${BASE_URL}/scim/v2/Groups \\"
echo "     -H \"Authorization: Bearer \${JWT_TOKEN}\""
echo ""

echo "   Get Supporting Data (requires supportingdata.read scope):"
echo "   curl -X GET ${BASE_URL}/api/supporting-data/roles \\"
echo "     -H \"Authorization: Bearer \${JWT_TOKEN}\""
echo ""

# ==================== ERROR SCENARIOS ====================
echo "5. Error Scenarios"
echo ""

echo "   401 Unauthorized (missing token):"
echo "   curl -X GET ${BASE_URL}/scim/v2/Users"
echo ""

echo "   Expected Response:"
cat << 'EOF'
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
  "status": "401",
  "detail": "Authentication required"
}
EOF
echo ""

echo "   403 Forbidden (insufficient scope):"
echo "   # Token has scim.read but endpoint requires scim.write"
echo "   curl -X POST ${BASE_URL}/scim/v2/Users \\"
echo "     -H \"Authorization: Bearer \${READ_ONLY_TOKEN}\" \\"
echo "     -H \"Content-Type: application/scim+json\" \\"
echo "     -d '{...}'"
echo ""

echo "   Expected Response:"
cat << 'EOF'
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
  "status": "403",
  "detail": "Insufficient permissions. Required scopes: scim.write"
}
EOF
echo ""

# ==================== AZURE AD EXAMPLE ====================
echo "6. Azure AD Integration Example"
echo ""

echo "   Step 1: Get Access Token from Azure AD"
cat << 'EOF'
curl -X POST https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id={client-id}" \
  -d "client_secret={client-secret}" \
  -d "scope=api://scim-service-provider/.default" \
  -d "grant_type=client_credentials"
EOF
echo ""

echo "   Step 2: Extract access_token from response"
echo "   ACCESS_TOKEN=\$(echo \$RESPONSE | jq -r '.access_token')"
echo ""

echo "   Step 3: Use token with SCIM API"
echo "   curl -X GET ${BASE_URL}/scim/v2/Users \\"
echo "     -H \"Authorization: Bearer \${ACCESS_TOKEN}\""
echo ""

# ==================== OKTA EXAMPLE ====================
echo "7. Okta Integration Example"
echo ""

echo "   Step 1: Get Access Token from Okta"
cat << 'EOF'
curl -X POST https://your-domain.okta.com/oauth2/default/v1/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id={client-id}" \
  -d "client_secret={client-secret}" \
  -d "scope=scim.read scim.write supportingdata.read" \
  -d "grant_type=client_credentials"
EOF
echo ""

echo "   Step 2: Use token with SCIM API"
echo "   curl -X GET ${BASE_URL}/scim/v2/Users \\"
echo "     -H \"Authorization: Bearer \${ACCESS_TOKEN}\""
echo ""

# ==================== TESTING WITHOUT AUTH ====================
echo "8. Testing Without Authentication (Development Only)"
echo ""

echo "   Disable all authentication mechanisms:"
echo "   export AUTH_OAUTH_ENABLED=false"
echo "   export AUTH_BASIC_ENABLED=false"
echo "   export AUTH_MTLS_ENABLED=false"
echo ""

echo "   Then restart server and test:"
echo "   curl -X GET ${BASE_URL}/scim/v2/Users"
echo ""

echo "   ⚠️  WARNING: Never deploy to production without authentication!"
echo ""

# ==================== SCOPE REFERENCE ====================
echo "9. Scope Reference"
echo ""
echo "   Available Scopes:"
echo "   - scim.read          : Read SCIM Users and Groups"
echo "   - scim.write         : Create, update, delete SCIM resources"
echo "   - supportingdata.read: Read Roles and Departments"
echo ""

echo "   Endpoint to Scope Mapping:"
echo "   GET    /scim/v2/Users              → scim.read"
echo "   POST   /scim/v2/Users              → scim.write"
echo "   PATCH  /scim/v2/Users/{id}         → scim.write"
echo "   DELETE /scim/v2/Users/{id}         → scim.write"
echo "   GET    /scim/v2/Groups             → scim.read"
echo "   POST   /scim/v2/Groups             → scim.write"
echo "   GET    /api/supporting-data/roles  → supportingdata.read"
echo ""

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     For more details, see AUTHENTICATION.md                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# Made with Bob
