# Token Generation Guide (Development/Testing)

This guide explains how to easily generate authentication tokens for testing your SCIM 2.0 Service Provider.

⚠️ **WARNING**: These endpoints are for **DEVELOPMENT AND TESTING ONLY**. Do not use in production!

## Quick Start

### 1. Get All Pre-Generated Tokens

Simply call the token endpoint to get all types of tokens:

```bash
curl http://localhost:5000/api/dev/tokens
```

This returns:
- **JWT tokens** with different scopes (read-only, write-only, full access, etc.)
- **Basic Auth credentials** (username, password, hash)
- **Public key** for JWT validation
- **Configuration instructions**
- **Usage examples**

### 2. Use a Token

Copy any token from the response and use it:

```bash
# Using JWT token
curl -H "Authorization: Bearer <token>" http://localhost:5000/scim/v2/Users

# Using Basic Auth
curl -u admin:admin123 http://localhost:5000/scim/v2/Users
```

## Available Endpoints

### GET /api/dev/tokens
Get all pre-generated test tokens and credentials.

**Example:**
```bash
curl http://localhost:5000/api/dev/tokens | jq
```

**Response includes:**
- `tokens.jwt.full_access` - Token with all scopes
- `tokens.jwt.read_only` - Token with only read access
- `tokens.jwt.write_only` - Token with only write access
- `tokens.jwt.full_scim` - Token with SCIM read/write
- `tokens.jwt.supporting_data` - Token for supporting data only
- `tokens.basic_auth` - Basic auth credentials
- `keys.public_key` - Public key for JWT validation
- `configuration` - Environment variable setup instructions

### POST /api/dev/tokens/generate
Generate a custom token with specific scopes.

**Example:**
```bash
curl -X POST http://localhost:5000/api/dev/tokens/generate \
  -H "Content-Type: application/json" \
  -d '{
    "scopes": ["scim.read", "scim.write"],
    "subject": "my-test-user",
    "expires_in_hours": 48
  }'
```

**Request Body:**
- `scopes` (array): List of scopes (scim.read, scim.write, supportingdata.read)
- `subject` (string, optional): Token subject/user identifier (default: "test-user")
- `expires_in_hours` (number, optional): Token expiration in hours (default: 24)

### GET /api/dev/tokens/public-key
Get just the public key for JWT validation.

**Example:**
```bash
curl http://localhost:5000/api/dev/tokens/public-key
```

## Token Types and Scopes

### Available Scopes

| Scope | Description |
|-------|-------------|
| `scim.read` | Read SCIM resources (Users, Groups) |
| `scim.write` | Create, update, delete SCIM resources |
| `supportingdata.read` | Read supporting data (Roles, Departments) |

### Pre-Generated JWT Tokens

1. **Full Access Token**
   - Scopes: `scim.read`, `scim.write`, `supportingdata.read`
   - Use for: Complete access to all endpoints

2. **Read-Only Token**
   - Scopes: `scim.read`
   - Use for: Reading Users and Groups only

3. **Write-Only Token**
   - Scopes: `scim.write`
   - Use for: Creating/updating/deleting resources (but not listing)

4. **Full SCIM Token**
   - Scopes: `scim.read`, `scim.write`
   - Use for: All SCIM operations (Users and Groups)

5. **Supporting Data Token**
   - Scopes: `supportingdata.read`
   - Use for: Reading Roles and Departments only

### Pre-Generated Basic Auth Credentials

1. **admin / admin123**
   - Full access user

2. **testuser / testpass123**
   - Standard test user

3. **readonly / readonly123**
   - Read-only user

## Configuration

### Using JWT Tokens

1. Get the public key:
```bash
curl http://localhost:5000/api/dev/tokens/public-key
```

2. Set environment variables:
```bash
export AUTH_OAUTH_ENABLED=true
export AUTH_JWT_ENABLED=true
export AUTH_JWT_ISSUER=https://test-idp.example.com
export AUTH_JWT_AUDIENCE=scim-service-provider
export AUTH_JWT_ALGORITHM=RS256
export AUTH_JWT_PUBLIC_KEY='-----BEGIN PUBLIC KEY-----
<paste public key here>
-----END PUBLIC KEY-----'
```

3. Restart the server

4. Use any JWT token from `/api/dev/tokens`

### Using Basic Auth

1. Get credentials from `/api/dev/tokens`

2. Set environment variables:
```bash
export AUTH_OAUTH_ENABLED=false
export AUTH_BASIC_ENABLED=true
export AUTH_BASIC_USERS='admin:8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918'
```

3. Restart the server

4. Use username and password in requests

### Disabling Authentication (Development Only)

```bash
export AUTH_OAUTH_ENABLED=false
export AUTH_BASIC_ENABLED=false
```

## Usage Examples

### Example 1: List Users with Full Access Token

```bash
# Get tokens
TOKENS=$(curl -s http://localhost:5000/api/dev/tokens)
TOKEN=$(echo $TOKENS | jq -r '.tokens.jwt.full_access.token')

# Use token
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/scim/v2/Users
```

### Example 2: Create User with Custom Token

```bash
# Generate custom token
RESPONSE=$(curl -s -X POST http://localhost:5000/api/dev/tokens/generate \
  -H "Content-Type: application/json" \
  -d '{"scopes": ["scim.write"], "subject": "integration-test"}')

TOKEN=$(echo $RESPONSE | jq -r '.token')

# Create user
curl -X POST http://localhost:5000/scim/v2/Users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/scim+json" \
  -d '{
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
    "userName": "testuser@example.com",
    "name": {
      "givenName": "Test",
      "familyName": "User"
    }
  }'
```

### Example 3: Use Basic Auth

```bash
# Get credentials
CREDS=$(curl -s http://localhost:5000/api/dev/tokens)
USERNAME=$(echo $CREDS | jq -r '.tokens.basic_auth.admin.username')
PASSWORD=$(echo $CREDS | jq -r '.tokens.basic_auth.admin.password')

# Use credentials
curl -u $USERNAME:$PASSWORD \
  http://localhost:5000/scim/v2/Users
```

### Example 4: Test Different Scopes

```bash
# Get tokens
TOKENS=$(curl -s http://localhost:5000/api/dev/tokens)

# Try read-only token (should work)
READ_TOKEN=$(echo $TOKENS | jq -r '.tokens.jwt.read_only.token')
curl -H "Authorization: Bearer $READ_TOKEN" \
  http://localhost:5000/scim/v2/Users

# Try read-only token for write operation (should fail with 403)
curl -X POST http://localhost:5000/scim/v2/Users \
  -H "Authorization: Bearer $READ_TOKEN" \
  -H "Content-Type: application/scim+json" \
  -d '{"schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"], "userName": "test"}'
```

## Python Examples

### Using Requests Library

```python
import requests

# Get all tokens
response = requests.get('http://localhost:5000/api/dev/tokens')
tokens = response.json()

# Use full access token
token = tokens['tokens']['jwt']['full_access']['token']
headers = {'Authorization': f'Bearer {token}'}

# List users
users = requests.get('http://localhost:5000/scim/v2/Users', headers=headers)
print(users.json())

# Create user
new_user = {
    'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
    'userName': 'newuser@example.com',
    'name': {'givenName': 'New', 'familyName': 'User'}
}
response = requests.post(
    'http://localhost:5000/scim/v2/Users',
    headers={**headers, 'Content-Type': 'application/scim+json'},
    json=new_user
)
print(response.json())
```

### Using Basic Auth

```python
import requests

# Get credentials
response = requests.get('http://localhost:5000/api/dev/tokens')
tokens = response.json()

username = tokens['tokens']['basic_auth']['admin']['username']
password = tokens['tokens']['basic_auth']['admin']['password']

# Use basic auth
response = requests.get(
    'http://localhost:5000/scim/v2/Users',
    auth=(username, password)
)
print(response.json())
```

## Integration with External Systems

When integrating external systems (like identity providers) with your SCIM service:

1. **Get a token** from `/api/dev/tokens` with appropriate scopes
2. **Configure the external system** to use the token as a Bearer token
3. **Test the integration** using the SCIM endpoints

Example for configuring an IdP:
- **SCIM Base URL**: `http://localhost:5000/scim/v2`
- **Authentication**: Bearer Token
- **Token**: `<copy from /api/dev/tokens>`

## Troubleshooting

### Token Not Working

1. Check if authentication is enabled:
```bash
curl http://localhost:5000/api/dev/tokens | jq '.configuration'
```

2. Verify the public key is configured correctly

3. Check token expiration (default 24 hours)

### 401 Unauthorized

- Token is invalid or expired
- Public key mismatch
- Authentication not properly configured

### 403 Forbidden

- Token is valid but lacks required scopes
- Check the scope requirements for the endpoint

## Security Notes

⚠️ **IMPORTANT**:
- These endpoints expose private keys and generate tokens without authentication
- **NEVER** use these endpoints in production
- **NEVER** expose these endpoints to the internet
- Only use for local development and testing
- Consider disabling these endpoints in production builds

## See Also

- [AUTHENTICATION.md](AUTHENTICATION.md) - Full authentication documentation
- [TESTING_AUTHENTICATION.md](TESTING_AUTHENTICATION.md) - Authentication testing guide
- [tools/generate_test_tokens.py](tools/generate_test_tokens.py) - Standalone token generator

---

Made with Bob