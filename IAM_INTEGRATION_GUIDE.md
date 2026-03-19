# IAM System Integration Guide

This guide explains how to integrate your IAM governance product with this SCIM 2.0 target system.

## Overview

This SCIM target system supports **all major authentication methods** simultaneously, allowing your IAM system to connect using whichever method it prefers:

✅ **OAuth 2.0 / JWT** (Bearer Token) - Most common for modern IAM systems  
✅ **HTTP Basic Authentication** - Simple username/password  
✅ **Mutual TLS (mTLS)** - Certificate-based authentication  

All authentication types are **enabled by default** and work simultaneously. The system tries them in order until one succeeds.

## Quick Start

### 1. Start the SCIM Target System

```bash
# Clone and start
git clone <repository>
cd CustomTarget
python3 app.py
```

The server starts on `http://localhost:5000` by default.

### 2. Configure Authentication

Run the automatic setup script:

```bash
# In another terminal
./setup_auth.sh

# Load the configuration
source auth.config

# Restart the server
python3 app.py
```

This configures all authentication types with test credentials.

### 3. Get Authentication Credentials

```bash
# Get all tokens and credentials
curl http://localhost:5000/api/dev/tokens | jq

# Or use the helper script
./get_tokens.sh
```

### 4. Test the Connection

```bash
# Test with JWT
TOKEN=$(./get_tokens.sh full_access)
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/scim/v2/Users

# Test with Basic Auth
curl -u admin:admin123 http://localhost:5000/scim/v2/Users

# Test discovery endpoints (no auth required)
curl http://localhost:5000/scim/v2/ServiceProviderConfig
```

## Authentication Methods

### Method 1: OAuth 2.0 / JWT (Recommended)

Most modern IAM systems (Azure AD, Okta, Auth0, etc.) use OAuth 2.0 with JWT tokens.

**Configuration:**

1. Get the public key:
```bash
curl http://localhost:5000/api/dev/tokens/public-key
```

2. Configure your IAM system:
   - **SCIM Base URL**: `http://localhost:5000/scim/v2`
   - **Authentication**: Bearer Token / OAuth 2.0
   - **Token Endpoint**: `http://localhost:5000/api/dev/tokens/generate`
   - **Public Key**: (from step 1)

3. Generate a token with required scopes:
```bash
curl -X POST http://localhost:5000/api/dev/tokens/generate \
  -H "Content-Type: application/json" \
  -d '{
    "scopes": ["scim.read", "scim.write", "supportingdata.read"],
    "subject": "iam-system",
    "expires_in_hours": 8760
  }'
```

**Available Scopes:**
- `scim.read` - Read Users and Groups
- `scim.write` - Create, update, delete Users and Groups
- `supportingdata.read` - Read Roles and Departments

**Example Request:**
```bash
curl -X GET http://localhost:5000/scim/v2/Users \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Method 2: HTTP Basic Authentication

Simple username/password authentication, useful for legacy systems or simple integrations.

**Pre-configured Users:**
- `admin` / `admin123` - Full access
- `testuser` / `testpass123` - Standard user
- `readonly` / `readonly123` - Read-only access

**Configuration in IAM System:**
- **SCIM Base URL**: `http://localhost:5000/scim/v2`
- **Authentication**: Basic Authentication
- **Username**: `admin`
- **Password**: `admin123`

**Example Request:**
```bash
curl -X GET http://localhost:5000/scim/v2/Users \
  -u admin:admin123
```

**Adding Custom Users:**

1. Generate password hash:
```bash
echo -n "mypassword" | shasum -a 256
```

2. Add to configuration:
```bash
export AUTH_BASIC_USERS="admin:hash1,myuser:hash2"
```

### Method 3: Mutual TLS (mTLS)

Certificate-based authentication for high-security environments.

**Configuration:**

1. Enable mTLS:
```bash
export AUTH_MTLS_ENABLED=true
export AUTH_MTLS_REQUIRE_CERT=true
export AUTH_MTLS_CA_CERTS_PATH=/path/to/ca-certs.pem
```

2. Configure your IAM system with client certificate

3. Make requests with certificate:
```bash
curl -X GET http://localhost:5000/scim/v2/Users \
  --cert client.crt \
  --key client.key \
  --cacert ca.crt
```

## IAM System Configuration Examples

### Azure AD (Entra ID)

1. In Azure AD, go to **Enterprise Applications** → **Provisioning**
2. Set **Provisioning Mode**: Automatic
3. Configure:
   - **Tenant URL**: `http://localhost:5000/scim/v2`
   - **Secret Token**: (JWT token from `/api/dev/tokens`)
4. Test connection and start provisioning

### Okta

1. In Okta Admin, go to **Applications** → **Create App Integration**
2. Choose **SCIM 2.0**
3. Configure:
   - **SCIM Base URL**: `http://localhost:5000/scim/v2`
   - **Authentication**: Bearer Token
   - **Token**: (JWT token from `/api/dev/tokens`)
4. Enable provisioning features

### ServiceNow

1. In ServiceNow, configure **Identity Provider**
2. Set:
   - **SCIM Endpoint**: `http://localhost:5000/scim/v2`
   - **Authentication**: Basic or OAuth
   - **Credentials**: admin / admin123 (or JWT token)
3. Test and activate

### IBM Security Verify

1. Configure **Target System**
2. Set:
   - **Connector Type**: SCIM 2.0
   - **Base URL**: `http://localhost:5000/scim/v2`
   - **Authentication**: Bearer Token or Basic
3. Map attributes and test

### Custom IAM System

For custom integrations, use the SCIM 2.0 API directly:

```python
import requests

# Configuration
BASE_URL = "http://localhost:5000/scim/v2"
TOKEN = "your-jwt-token"  # or use Basic Auth

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/scim+json"
}

# List users
response = requests.get(f"{BASE_URL}/Users", headers=headers)
users = response.json()

# Create user
new_user = {
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
    "userName": "john.doe@example.com",
    "name": {
        "givenName": "John",
        "familyName": "Doe"
    },
    "emails": [{
        "value": "john.doe@example.com",
        "type": "work",
        "primary": True
    }],
    "active": True
}

response = requests.post(f"{BASE_URL}/Users", headers=headers, json=new_user)
created_user = response.json()

# Update user
patch_ops = {
    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
    "Operations": [{
        "op": "replace",
        "path": "active",
        "value": False
    }]
}

response = requests.patch(
    f"{BASE_URL}/Users/{created_user['id']}", 
    headers=headers, 
    json=patch_ops
)
```

## Supported SCIM Operations

### Users

| Operation | Endpoint | Method | Scopes Required |
|-----------|----------|--------|-----------------|
| List Users | `/scim/v2/Users` | GET | `scim.read` |
| Get User | `/scim/v2/Users/{id}` | GET | `scim.read` |
| Create User | `/scim/v2/Users` | POST | `scim.write` |
| Update User | `/scim/v2/Users/{id}` | PATCH | `scim.write` |
| Delete User | `/scim/v2/Users/{id}` | DELETE | `scim.write` |

### Groups

| Operation | Endpoint | Method | Scopes Required |
|-----------|----------|--------|-----------------|
| List Groups | `/scim/v2/Groups` | GET | `scim.read` |
| Get Group | `/scim/v2/Groups/{id}` | GET | `scim.read` |
| Create Group | `/scim/v2/Groups` | POST | `scim.write` |
| Update Group | `/scim/v2/Groups/{id}` | PATCH | `scim.write` |
| Delete Group | `/scim/v2/Groups/{id}` | DELETE | `scim.write` |

### Supporting Data (Read-Only)

| Operation | Endpoint | Method | Scopes Required |
|-----------|----------|--------|-----------------|
| List Roles | `/api/supporting-data/roles` | GET | `supportingdata.read` |
| List Departments | `/api/supporting-data/departments` | GET | `supportingdata.read` |

### Discovery (Public)

| Operation | Endpoint | Method | Auth Required |
|-----------|----------|--------|---------------|
| Service Provider Config | `/scim/v2/ServiceProviderConfig` | GET | No |
| Schemas | `/scim/v2/Schemas` | GET | No |
| Resource Types | `/scim/v2/ResourceTypes` | GET | No |

## Filtering and Pagination

### Filtering Users

```bash
# Filter by userName
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:5000/scim/v2/Users?filter=userName eq \"john.doe@example.com\""

# Filter by active status
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:5000/scim/v2/Users?filter=active eq true"
```

### Pagination

```bash
# Get first 10 users
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:5000/scim/v2/Users?startIndex=1&count=10"

# Get next 10 users
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:5000/scim/v2/Users?startIndex=11&count=10"
```

## Error Handling

The system returns SCIM-compliant error responses:

```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
  "status": "401",
  "detail": "Authentication required"
}
```

**Common Status Codes:**
- `200` - Success
- `201` - Created
- `204` - No Content (successful delete)
- `400` - Bad Request (invalid data)
- `401` - Unauthorized (authentication failed)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `409` - Conflict (duplicate resource)

## Testing Your Integration

### 1. Test Discovery Endpoints (No Auth)

```bash
curl http://localhost:5000/scim/v2/ServiceProviderConfig
curl http://localhost:5000/scim/v2/Schemas
curl http://localhost:5000/scim/v2/ResourceTypes
```

### 2. Test Authentication

```bash
# Should succeed
curl -u admin:admin123 http://localhost:5000/scim/v2/Users

# Should fail with 401
curl http://localhost:5000/scim/v2/Users
```

### 3. Test User Lifecycle

```bash
TOKEN=$(./get_tokens.sh full_access)

# Create
USER_ID=$(curl -X POST http://localhost:5000/scim/v2/Users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/scim+json" \
  -d '{"schemas":["urn:ietf:params:scim:schemas:core:2.0:User"],"userName":"test@example.com"}' \
  | jq -r '.id')

# Read
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/scim/v2/Users/$USER_ID

# Update
curl -X PATCH http://localhost:5000/scim/v2/Users/$USER_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/scim+json" \
  -d '{"schemas":["urn:ietf:params:scim:api:messages:2.0:PatchOp"],"Operations":[{"op":"replace","path":"active","value":false}]}'

# Delete
curl -X DELETE http://localhost:5000/scim/v2/Users/$USER_ID \
  -H "Authorization: Bearer $TOKEN"
```

## Production Considerations

When deploying for production use with your IAM system:

1. **Disable Token Generation Endpoints**
   ```bash
   # Remove or comment out in app.py:
   # @app.route('/api/dev/tokens', ...)
   ```

2. **Use Real Authentication**
   - Configure with your actual OAuth provider
   - Use production certificates for mTLS
   - Rotate credentials regularly

3. **Enable HTTPS**
   - Use a reverse proxy (nginx, Apache)
   - Configure SSL/TLS certificates
   - Enforce HTTPS-only

4. **Configure Proper Scopes**
   - Map IAM roles to SCIM scopes
   - Implement least-privilege access
   - Audit scope usage

5. **Monitor and Log**
   - Enable request logging
   - Monitor authentication failures
   - Track provisioning operations

## Troubleshooting

### Authentication Fails

1. Check if authentication is enabled:
```bash
curl http://localhost:5000/api/dev/tokens | jq '.configuration'
```

2. Verify credentials:
```bash
# For JWT
curl http://localhost:5000/api/dev/tokens/public-key

# For Basic Auth
./get_tokens.sh
```

3. Check server logs for errors

### IAM System Can't Connect

1. Verify the SCIM base URL is correct
2. Check network connectivity
3. Ensure authentication credentials are valid
4. Test with curl first before configuring IAM system

### Provisioning Fails

1. Check required scopes are granted
2. Verify request format matches SCIM 2.0 spec
3. Review error messages in response
4. Check server logs

## Support

For issues or questions:
- Review [TOKEN_GENERATION_GUIDE.md](TOKEN_GENERATION_GUIDE.md)
- Check [AUTHENTICATION.md](AUTHENTICATION.md)
- See [TESTING_AUTHENTICATION.md](TESTING_AUTHENTICATION.md)

---

Made with Bob