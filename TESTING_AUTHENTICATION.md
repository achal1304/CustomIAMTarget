# Authentication Testing Guide

## Quick Start - Testing in 5 Minutes

### Option 1: No Authentication (Fastest)

```bash
# Disable all authentication
export AUTH_OAUTH_ENABLED=false
export AUTH_BASIC_ENABLED=false
export AUTH_MTLS_ENABLED=false

# Start server
python3 app.py

# Test (in another terminal)
curl http://localhost:5000/scim/v2/Users
```

### Option 2: Basic Authentication (Simple)

```bash
# Enable Basic Auth
export AUTH_OAUTH_ENABLED=false
export AUTH_BASIC_ENABLED=true

# Set credentials (username: admin, password: admin123)
export AUTH_BASIC_USERS="admin:8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"

# Start server
python3 app.py

# Test
curl -u admin:admin123 http://localhost:5000/scim/v2/Users
```

### Option 3: OAuth 2.0 / JWT (Production-like)

```bash
# Generate test tokens
python3 tools/generate_test_tokens.py

# Follow the configuration instructions printed
# Then test with generated tokens
```

## Detailed Testing Instructions

### Step 1: Generate Test Tokens

Run the token generator:

```bash
cd /Users/achal/CustomTarget
python3 tools/generate_test_tokens.py
```

This will:
1. Generate RSA key pair
2. Create JWT tokens with different scopes
3. Generate Basic Auth credentials
4. Save everything to `test_tokens.json`
5. Print curl examples

**Output includes:**
- Private key (for signing tokens)
- Public key (for validating tokens)
- Multiple JWT tokens with different scopes
- Basic Auth credentials and hashes
- Ready-to-use curl commands

### Step 2: Configure Authentication

Choose one of the following configurations:

#### A. JWT Authentication (Recommended for Testing OAuth)

```bash
# Copy the PUBLIC KEY from token generator output
export AUTH_OAUTH_ENABLED=true
export AUTH_JWT_ENABLED=true
export AUTH_JWT_ISSUER=https://test-idp.example.com
export AUTH_JWT_AUDIENCE=scim-service-provider
export AUTH_JWT_ALGORITHM=RS256

# Set the public key (copy from generator output)
export AUTH_JWT_PUBLIC_KEY='-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END PUBLIC KEY-----'
```

#### B. Basic Authentication

```bash
export AUTH_OAUTH_ENABLED=false
export AUTH_BASIC_ENABLED=true

# Use credentials from generator output
# Format: username:sha256_hash
export AUTH_BASIC_USERS="admin:8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"
```

#### C. No Authentication (Development Only)

```bash
export AUTH_OAUTH_ENABLED=false
export AUTH_BASIC_ENABLED=false
export AUTH_MTLS_ENABLED=false
```

### Step 3: Start the Server

```bash
python3 app.py
```

You should see:

```
╔══════════════════════════════════════════════════════════════╗
║         SCIM 2.0 Service Provider - Starting Server          ║
╚══════════════════════════════════════════════════════════════╝

Server Configuration:
  Host: 0.0.0.0
  Port: 5000
  Debug: True
  Base URL: http://localhost:5000
  Authentication: ENABLED
  Mechanisms: OAuth 2.0 Bearer Token
```

### Step 4: Test Authentication

#### Test 1: Public Endpoints (No Auth Required)

```bash
# These should always work
curl http://localhost:5000/scim/v2/ServiceProviderConfig
curl http://localhost:5000/scim/v2/Schemas
curl http://localhost:5000/scim/v2/ResourceTypes
```

#### Test 2: Protected Endpoints Without Auth (Should Fail)

```bash
# Should return 401 Unauthorized
curl http://localhost:5000/scim/v2/Users

# Expected response:
# {
#   "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
#   "status": "401",
#   "detail": "Authentication required"
# }
```

#### Test 3: With Basic Authentication

```bash
# Should succeed
curl -u admin:admin123 http://localhost:5000/scim/v2/Users

# Expected response:
# {
#   "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
#   "totalResults": 0,
#   "startIndex": 1,
#   "itemsPerPage": 0,
#   "Resources": []
# }
```

#### Test 4: With JWT Token

```bash
# Get token from test_tokens.json or generator output
TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."

# List users (requires scim.read)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/scim/v2/Users

# Create user (requires scim.write)
curl -X POST http://localhost:5000/scim/v2/Users \
  -H "Authorization: Bearer $TOKEN" \
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
```

#### Test 5: Insufficient Scope (Should Return 403)

```bash
# Use READ-ONLY token to try to create a user
READ_ONLY_TOKEN="..." # Token with only scim.read scope

curl -X POST http://localhost:5000/scim/v2/Users \
  -H "Authorization: Bearer $READ_ONLY_TOKEN" \
  -H "Content-Type: application/scim+json" \
  -d '{...}'

# Expected response:
# {
#   "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
#   "status": "403",
#   "detail": "Insufficient permissions. Required scopes: scim.write"
# }
```

## Manual Token Generation

### Generate Basic Auth Password Hash

```bash
# Method 1: Using echo and sha256sum (Linux/Mac)
echo -n "mypassword" | sha256sum

# Method 2: Using Python
python3 -c "import hashlib; print(hashlib.sha256('mypassword'.encode()).hexdigest())"

# Method 3: Using openssl
echo -n "mypassword" | openssl dgst -sha256
```

### Generate Basic Auth Header

```bash
# Method 1: Using base64
echo -n "username:password" | base64

# Method 2: Using Python
python3 -c "import base64; print(base64.b64encode(b'username:password').decode())"

# Use in curl:
curl -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=" http://localhost:5000/scim/v2/Users
```

### Create Custom JWT Token

```python
import jwt
import datetime

# Your private key (from generator or your own)
private_key = """-----BEGIN PRIVATE KEY-----
...
-----END PRIVATE KEY-----"""

# Create payload
payload = {
    'iss': 'https://test-idp.example.com',
    'aud': 'scim-service-provider',
    'sub': 'test-user',
    'scope': 'scim.read scim.write',
    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
    'iat': datetime.datetime.utcnow()
}

# Sign token
token = jwt.encode(payload, private_key, algorithm='RS256')
print(token)
```

## Testing Different Scenarios

### Scenario 1: Read-Only Access

```bash
# Use token with only scim.read scope
TOKEN="..." # READ-ONLY token from generator

# ✅ Should work
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/scim/v2/Users
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/scim/v2/Groups

# ❌ Should fail with 403
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/scim+json" \
  http://localhost:5000/scim/v2/Users -d '{...}'
```

### Scenario 2: Write-Only Access

```bash
# Use token with only scim.write scope
TOKEN="..." # WRITE-ONLY token from generator

# ❌ Should fail with 403 (needs scim.read)
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/scim/v2/Users

# ✅ Should work (has scim.write)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/scim+json" \
  http://localhost:5000/scim/v2/Users -d '{...}'
```

### Scenario 3: Full Access

```bash
# Use token with all scopes
TOKEN="..." # FULL ACCESS token from generator

# ✅ All operations should work
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/scim/v2/Users
curl -X POST -H "Authorization: Bearer $TOKEN" http://localhost:5000/scim/v2/Users -d '{...}'
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/supporting-data/roles
```

### Scenario 4: Expired Token

```bash
# Use expired token from generator
TOKEN="..." # EXPIRED token

# ❌ Should fail with 401
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/scim/v2/Users

# Expected: "Token expired"
```

### Scenario 5: Invalid Token

```bash
# Use malformed token
TOKEN="invalid.token.here"

# ❌ Should fail with 401
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/scim/v2/Users

# Expected: "Invalid token"
```

## Automated Testing

### Run Authentication Tests

```bash
# Install test dependencies
pip install pytest

# Run authentication tests
cd tests
pytest test_authentication.py -v

# Run specific test
pytest test_authentication.py::test_basic_auth_valid_credentials -v
```

### Generate and Test in One Command

```bash
# Generate tokens and save to file
python3 tools/generate_test_tokens.py > /dev/null

# Extract token from JSON
TOKEN=$(python3 -c "import json; print(json.load(open('test_tokens.json'))['tokens']['full_access'])")

# Test with token
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/scim/v2/Users
```

## Troubleshooting

### Issue: "Import jwt could not be resolved"

```bash
pip install PyJWT cryptography
```

### Issue: "401 Unauthorized" with valid token

**Check:**
1. Is AUTH_OAUTH_ENABLED=true?
2. Is AUTH_JWT_PUBLIC_KEY set correctly?
3. Does token issuer match AUTH_JWT_ISSUER?
4. Does token audience match AUTH_JWT_AUDIENCE?
5. Is token expired?

**Debug:**
```bash
# Decode token without verification to inspect
python3 -c "
import jwt
token = 'YOUR_TOKEN'
decoded = jwt.decode(token, options={'verify_signature': False})
print(decoded)
"
```

### Issue: "403 Forbidden" with valid token

**Check:**
1. Does token have required scope?
2. For GET requests: Need `scim.read`
3. For POST/PATCH/DELETE: Need `scim.write`
4. For supporting data: Need `supportingdata.read`

**Debug:**
```bash
# Check token scopes
python3 -c "
import jwt
token = 'YOUR_TOKEN'
decoded = jwt.decode(token, options={'verify_signature': False})
print('Scopes:', decoded.get('scope'))
"
```

### Issue: Basic Auth not working

**Check:**
1. Is AUTH_BASIC_ENABLED=true?
2. Is password hash correct?
3. Is username:hash format correct in AUTH_BASIC_USERS?

**Generate correct hash:**
```bash
python3 -c "import hashlib; print(hashlib.sha256(b'your_password').hexdigest())"
```

## Integration with Real IdPs

### Azure AD

1. Register application in Azure AD
2. Configure API permissions
3. Get tenant ID and client credentials
4. Configure:

```bash
export AUTH_JWT_ISSUER=https://login.microsoftonline.com/{tenant-id}/v2.0
export AUTH_JWT_AUDIENCE=api://your-app-id
export AUTH_JWT_PUBLIC_KEY_URL=https://login.microsoftonline.com/{tenant-id}/discovery/v2.0/keys
```

### Okta

1. Create OAuth 2.0 client
2. Configure custom authorization server
3. Configure:

```bash
export AUTH_JWT_ISSUER=https://your-domain.okta.com/oauth2/default
export AUTH_JWT_AUDIENCE=api://scim-service-provider
export AUTH_JWT_PUBLIC_KEY_URL=https://your-domain.okta.com/oauth2/default/v1/keys
```

## Summary

✅ **Quick Testing:** Use Basic Auth or disable auth
✅ **Token Generation:** Use `tools/generate_test_tokens.py`
✅ **JWT Testing:** Configure public key and use generated tokens
✅ **Scope Testing:** Use different tokens for different access levels
✅ **Production Testing:** Integrate with real IdP (Azure AD, Okta, etc.)

📚 **See also:**
- `AUTHENTICATION.md` - Complete authentication guide
- `examples/authentication-examples.sh` - More curl examples
- `auth.config.example` - Configuration reference