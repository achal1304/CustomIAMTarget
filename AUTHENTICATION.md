# Authentication & Authorization Guide

## Overview

This SCIM 2.0 Service Provider implements industry-standard authentication and authorization mechanisms to secure all endpoints without modifying any SCIM logic.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Request                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Flask @app.before_request                       │
│              Authentication Middleware                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         Try Authentication Mechanisms (in order):            │
│         1. OAuth 2.0 Bearer Token (JWT/Introspection)       │
│         2. HTTP Basic Authentication                         │
│         3. Mutual TLS (Client Certificate)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                    Authenticated?
                         │
            ┌────────────┴────────────┐
            │                         │
           NO                        YES
            │                         │
            ▼                         ▼
    ┌──────────────┐      ┌──────────────────────┐
    │ Return 401   │      │ Check Authorization  │
    │ Unauthorized │      │ (Scope Validation)   │
    └──────────────┘      └──────────┬───────────┘
                                     │
                              Authorized?
                                     │
                        ┌────────────┴────────────┐
                        │                         │
                       NO                        YES
                        │                         │
                        ▼                         ▼
                ┌──────────────┐      ┌──────────────────────┐
                │ Return 403   │      │ Continue to SCIM     │
                │ Forbidden    │      │ Endpoint Logic       │
                └──────────────┘      └──────────────────────┘
```

## Supported Authentication Mechanisms

### 1. OAuth 2.0 Bearer Token (MANDATORY)

**Recommended for production environments.**

#### JWT Validation

Validates JSON Web Tokens (JWT) issued by external Identity Providers.

**Configuration:**
```bash
AUTH_OAUTH_ENABLED=true
AUTH_JWT_ENABLED=true
AUTH_JWT_ISSUER=https://your-idp.example.com
AUTH_JWT_AUDIENCE=scim-service-provider
AUTH_JWT_ALGORITHM=RS256
AUTH_JWT_PUBLIC_KEY_URL=https://your-idp.example.com/.well-known/jwks.json
```

**Request Example:**
```bash
curl -X GET https://scim.example.com/scim/v2/Users \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**JWT Claims:**
- `iss` (issuer): Must match `AUTH_JWT_ISSUER`
- `aud` (audience): Must match `AUTH_JWT_AUDIENCE`
- `exp` (expiration): Token must not be expired
- `sub` or `client_id`: Used as identity
- `scope` or `scopes`: Space-separated or array of scopes

#### Token Introspection

Alternative to JWT validation. Validates tokens by calling an OAuth 2.0 introspection endpoint.

**Configuration:**
```bash
AUTH_OAUTH_ENABLED=true
AUTH_INTROSPECTION_ENABLED=true
AUTH_INTROSPECTION_URL=https://your-idp.example.com/oauth2/introspect
AUTH_INTROSPECTION_CLIENT_ID=scim-service-provider
AUTH_INTROSPECTION_CLIENT_SECRET=your-secret
```

### 2. HTTP Basic Authentication (OPTIONAL)

**For legacy integrations and non-production environments only.**

**Configuration:**
```bash
AUTH_BASIC_ENABLED=true
# Format: username:sha256_hash
# Generate hash: echo -n "password" | sha256sum
AUTH_BASIC_USERS=admin:8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918
```

**Request Example:**
```bash
curl -X GET https://scim.example.com/scim/v2/Users \
  -u admin:password
```

**Security Notes:**
- Must be used over HTTPS only
- Credentials are base64-encoded (not encrypted)
- Passwords stored as SHA-256 hashes
- Disable in production; use OAuth 2.0 instead

### 3. Mutual TLS (OPTIONAL)

**For enterprise environments requiring certificate-based authentication.**

**Configuration:**
```bash
AUTH_MTLS_ENABLED=true
AUTH_MTLS_REQUIRE_CERT=true
AUTH_MTLS_CA_CERTS_PATH=/path/to/ca-certs.pem
```

**Requirements:**
- Web server (nginx, Apache) must be configured for TLS client authentication
- Client must present valid certificate signed by trusted CA
- Certificate subject DN is mapped to identity

**Request Example:**
```bash
curl -X GET https://scim.example.com/scim/v2/Users \
  --cert client-cert.pem \
  --key client-key.pem \
  --cacert ca-cert.pem
```

## Authorization (Scopes)

### Scope Definitions

| Scope | Description | Grants Access To |
|-------|-------------|------------------|
| `scim.read` | Read SCIM resources | GET /scim/v2/Users, GET /scim/v2/Groups |
| `scim.write` | Create, update, delete SCIM resources | POST, PATCH, DELETE on Users and Groups |
| `supportingdata.read` | Read supporting data | GET /api/supporting-data/roles, /departments |

### Endpoint Access Rules

| Endpoint | HTTP Method | Required Scopes |
|----------|-------------|-----------------|
| `/scim/v2/ServiceProviderConfig` | GET | None (public) |
| `/scim/v2/Schemas` | GET | None (public) |
| `/scim/v2/ResourceTypes` | GET | None (public) |
| `/scim/v2/Users` | GET | `scim.read` |
| `/scim/v2/Users` | POST | `scim.write` |
| `/scim/v2/Users/{id}` | GET | `scim.read` |
| `/scim/v2/Users/{id}` | PATCH | `scim.write` |
| `/scim/v2/Users/{id}` | DELETE | `scim.write` |
| `/scim/v2/Groups` | GET | `scim.read` |
| `/scim/v2/Groups` | POST | `scim.write` |
| `/scim/v2/Groups/{id}` | GET | `scim.read` |
| `/scim/v2/Groups/{id}` | PATCH | `scim.write` |
| `/scim/v2/Groups/{id}` | DELETE | `scim.write` |
| `/api/supporting-data/roles` | GET | `supportingdata.read` |
| `/api/supporting-data/departments` | GET | `supportingdata.read` |

### Scope Validation

- User must have **at least one** of the required scopes
- Missing scopes result in HTTP 403 Forbidden
- Scopes are extracted from JWT claims or introspection response

## Error Responses

### 401 Unauthorized

Returned when authentication fails.

**SCIM-Compliant Error:**
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
  "status": "401",
  "detail": "Authentication required"
}
```

**Common Causes:**
- Missing `Authorization` header
- Invalid token format
- Expired token
- Invalid signature
- Token not active (introspection)

### 403 Forbidden

Returned when authentication succeeds but authorization fails.

**SCIM-Compliant Error:**
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
  "status": "403",
  "detail": "Insufficient permissions. Required scopes: scim.write"
}
```

**Common Causes:**
- Missing required scope
- Token has `scim.read` but endpoint requires `scim.write`

## Configuration Examples

### Example 1: Azure AD (Production)

```bash
AUTH_OAUTH_ENABLED=true
AUTH_JWT_ENABLED=true
AUTH_JWT_ISSUER=https://login.microsoftonline.com/{tenant-id}/v2.0
AUTH_JWT_AUDIENCE=api://scim-service-provider
AUTH_JWT_ALGORITHM=RS256
AUTH_JWT_PUBLIC_KEY_URL=https://login.microsoftonline.com/{tenant-id}/discovery/v2.0/keys
```

**Azure AD Token Request:**
```bash
# Get access token
curl -X POST https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token \
  -d "client_id={client-id}" \
  -d "client_secret={client-secret}" \
  -d "scope=api://scim-service-provider/.default" \
  -d "grant_type=client_credentials"

# Use token
curl -X GET https://scim.example.com/scim/v2/Users \
  -H "Authorization: Bearer {access_token}"
```

### Example 2: Okta (Production)

```bash
AUTH_OAUTH_ENABLED=true
AUTH_JWT_ENABLED=true
AUTH_JWT_ISSUER=https://your-domain.okta.com/oauth2/default
AUTH_JWT_AUDIENCE=api://scim-service-provider
AUTH_JWT_ALGORITHM=RS256
AUTH_JWT_PUBLIC_KEY_URL=https://your-domain.okta.com/oauth2/default/v1/keys
```

**Okta Token Request:**
```bash
# Get access token
curl -X POST https://your-domain.okta.com/oauth2/default/v1/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id={client-id}" \
  -d "client_secret={client-secret}" \
  -d "scope=scim.read scim.write" \
  -d "grant_type=client_credentials"

# Use token
curl -X GET https://scim.example.com/scim/v2/Users \
  -H "Authorization: Bearer {access_token}"
```

### Example 3: IBM Security Verify (Production)

```bash
AUTH_OAUTH_ENABLED=true
AUTH_JWT_ENABLED=true
AUTH_JWT_ISSUER=https://your-tenant.verify.ibm.com/v1.0/endpoint/default
AUTH_JWT_AUDIENCE=scim-service-provider
AUTH_JWT_ALGORITHM=RS256
AUTH_JWT_PUBLIC_KEY_URL=https://your-tenant.verify.ibm.com/v1.0/endpoint/default/jwks
```

### Example 4: Development/Testing (Basic Auth)

```bash
AUTH_OAUTH_ENABLED=false
AUTH_BASIC_ENABLED=true
# Password: "admin123"
AUTH_BASIC_USERS=admin:240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9
```

**Usage:**
```bash
curl -X GET http://localhost:5000/scim/v2/Users \
  -u admin:admin123
```

### Example 5: Local Development (No Auth)

```bash
AUTH_OAUTH_ENABLED=false
AUTH_BASIC_ENABLED=false
AUTH_MTLS_ENABLED=false
```

**⚠️ WARNING:** Only use for local development. Never deploy without authentication.

## Testing Authentication

### Test OAuth 2.0 with Mock JWT

```python
import jwt
import datetime

# Create test JWT
payload = {
    'iss': 'https://test-idp.example.com',
    'aud': 'scim-service-provider',
    'sub': 'test-user',
    'scope': 'scim.read scim.write',
    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    'iat': datetime.datetime.utcnow()
}

# Sign with test key (use matching public key in config)
token = jwt.encode(payload, private_key, algorithm='RS256')

# Use token
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('http://localhost:5000/scim/v2/Users', headers=headers)
```

### Test Basic Auth

```bash
# Generate password hash
echo -n "mypassword" | sha256sum
# Output: 89e01536ac207279409d4de1e5253e01f4a1769e696db0d6062ca9b8f56767c8

# Configure
export AUTH_BASIC_ENABLED=true
export AUTH_BASIC_USERS="testuser:89e01536ac207279409d4de1e5253e01f4a1769e696db0d6062ca9b8f56767c8"

# Test
curl -X GET http://localhost:5000/scim/v2/Users -u testuser:mypassword
```

## Security Best Practices

1. **Always use HTTPS in production**
   - TLS 1.2 or higher
   - Valid SSL/TLS certificates

2. **Use OAuth 2.0 with JWT validation**
   - Preferred authentication mechanism
   - Supports token expiration and revocation
   - Integrates with enterprise IdPs

3. **Disable Basic Auth in production**
   - Only for development/testing
   - Credentials can be intercepted if not over HTTPS

4. **Rotate secrets regularly**
   - JWT signing keys
   - Client secrets
   - Basic auth passwords

5. **Monitor authentication failures**
   - Log all 401/403 responses
   - Alert on suspicious patterns
   - Implement rate limiting

6. **Validate token claims**
   - Check issuer, audience, expiration
   - Verify signature with trusted keys
   - Validate scopes match requirements

7. **Use least privilege**
   - Grant minimum required scopes
   - Separate read and write access
   - Use service accounts for automation

## Troubleshooting

### Issue: 401 "Missing Authorization header"

**Cause:** No `Authorization` header in request

**Solution:**
```bash
# Add Authorization header
curl -X GET https://scim.example.com/scim/v2/Users \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Issue: 401 "Token expired"

**Cause:** JWT `exp` claim is in the past

**Solution:** Request a new token from your IdP

### Issue: 401 "Invalid token"

**Cause:** Token signature validation failed

**Solution:**
- Verify `AUTH_JWT_PUBLIC_KEY_URL` is correct
- Ensure token was signed by expected IdP
- Check `AUTH_JWT_ISSUER` and `AUTH_JWT_AUDIENCE` match token claims

### Issue: 403 "Insufficient permissions"

**Cause:** Token doesn't have required scope

**Solution:**
- Request token with correct scopes
- Check IdP scope configuration
- Verify scope claim name (`scope`, `scopes`, or `scp`)

### Issue: Headers not recognized (case sensitivity)

**Cause:** Some clients send lowercase headers

**Solution:** Already handled! Middleware performs case-insensitive header matching.

## Integration with IAM Products

### Azure AD SCIM Provisioning

1. Register application in Azure AD
2. Configure API permissions with custom scopes
3. Set SCIM endpoint URL
4. Configure authentication with OAuth 2.0
5. Azure AD automatically includes required scopes in tokens

### Okta Lifecycle Management

1. Create OAuth 2.0 client in Okta
2. Configure custom authorization server
3. Define scopes: `scim.read`, `scim.write`
4. Set SCIM base URL
5. Configure OAuth 2.0 client credentials flow

### IBM Security Verify

1. Create API client in Verify
2. Configure OAuth 2.0 settings
3. Set SCIM endpoint
4. Map Verify roles to scopes
5. Enable provisioning

## Compliance

This implementation follows:
- **RFC 7644** (SCIM Protocol) - Error responses
- **RFC 6750** (OAuth 2.0 Bearer Token Usage)
- **RFC 7519** (JSON Web Token)
- **RFC 7662** (OAuth 2.0 Token Introspection)
- **RFC 2617** (HTTP Basic Authentication)
- **RFC 5246** (TLS 1.2)

## Summary

✅ **Implemented:**
- OAuth 2.0 Bearer Token (JWT + Introspection)
- HTTP Basic Authentication
- Mutual TLS support
- Scope-based authorization
- SCIM-compliant error responses
- Case-insensitive header handling
- Pluggable, config-driven architecture

✅ **NOT Modified:**
- SCIM User schema
- SCIM Group schema
- SCIM endpoint logic
- SCIM PATCH operations
- Supporting Data APIs
- Discovery endpoints

🔒 **Security:** Industry-standard authentication without breaking SCIM compliance.