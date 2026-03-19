# SCIM 2.0 Minimal Target System

A **minimal, standards-compliant SCIM 2.0 Service Provider** implementation designed for enterprise Identity & Access Management (IAM) integration.

## Overview

This is a reference implementation of a SCIM 2.0 target system that strictly follows:
- **RFC 7643** - SCIM Core Schema
- **RFC 7644** - SCIM Protocol

The implementation is **intentionally minimal**, including only essential identity attributes and operations required for enterprise IAM provisioning.

## Key Features

✅ **SCIM 2.0 Compliant** - Fully compliant with RFC 7643 and RFC 7644
✅ **Minimal Schema** - Only essential User and Group attributes
✅ **Enterprise Ready** - Compatible with Azure AD, Okta, ServiceNow, IBM Security Verify
✅ **Interactive API Docs** - Swagger UI for testing endpoints in browser
✅ **Postman Collection** - Complete collection with auto-authentication
✅ **Multiple Auth Methods** - OAuth/JWT, Basic Auth, mTLS (all enabled)
✅ **Easy Token Generation** - Built-in endpoints for getting test credentials
✅ **Manager Relationships** - Supports organizational hierarchy via Enterprise User extension
✅ **Group-Based Roles** - Uses SCIM Groups for role-based access control
✅ **Self-Reference Prevention** - Validates manager relationships
✅ **Discovery Endpoints** - ServiceProviderConfig, Schemas, ResourceTypes
✅ **PATCH Operations** - Full SCIM PatchOp support (add, replace, remove)
✅ **Filtering & Pagination** - Search and paginate users/groups

## 🚀 Quick Start - Test the API

```bash
# 1. Start the server
python3 app.py

# 2. Open Swagger UI in your browser
open http://localhost:5000/api/docs

# 3. Or import Postman collection
# Download from: http://localhost:5000/postman_collection.json
```

**That's it!** You can now test all endpoints interactively.

## Project Structure

```
.
├── ARCHITECTURE.md                      # System architecture and design
├── COMPLIANCE.md                        # SCIM compliance documentation
├── README.md                            # This file
├── schemas/
│   ├── user-schema.json                 # SCIM User schema definition
│   ├── enterprise-user-extension.json   # Enterprise User extension (manager)
│   └── group-schema.json                # SCIM Group schema definition
├── models/
│   ├── __init__.py                      # Python package marker
│   ├── user_model.py                    # User data model with validation
│   └── group_model.py                   # Group data model with validation
├── api/
│   ├── __init__.py                      # Python package marker
│   ├── user-endpoints.py                # User CRUD endpoints
│   ├── group-endpoints.py               # Group CRUD endpoints
│   └── discovery-endpoints.py           # Discovery endpoints
├── schemas/
│   └── __init__.py                      # Python package marker
└── examples/
    ├── __init__.py                      # Python package marker
    └── request-response-examples.md     # API request/response examples
```

## User Resource (Minimal)

### Core Attributes
- `id` - Server-generated UUID
- `userName` - Unique identifier (required)
- `externalId` - External system correlation ID
- `name.givenName` - First name
- `name.familyName` - Last name
- `emails` - Work email (single, primary)
- `active` - Account status (for deprovisioning)
- `department` - Organizational unit
- `gender` - Optional demographic field

### Enterprise Extension
- `manager.value` - Manager's User ID
- `manager.displayName` - Manager's display name

### Read-Only Computed
- `groups` - Group memberships (computed from Group.members)
- `meta` - Resource metadata (created, lastModified, location, version)

### Excluded (Not Implemented)
- ❌ addresses
- ❌ phoneNumbers
- ❌ photos
- ❌ title
- ❌ costCenter, division, organization
- ❌ locale, timezone, preferredLanguage

## Group Resource (Minimal)

### Core Attributes
- `id` - Server-generated UUID
- `displayName` - Group name (required)
- `externalId` - External system correlation ID
- `members` - Array of User references
- `meta` - Resource metadata

### Purpose
Groups represent **roles** in the system. No separate Role API is needed.

## API Endpoints

### User Operations
```
POST   /Users              Create user
GET    /Users/{id}         Retrieve user
GET    /Users              List/search users (with filtering)
PATCH  /Users/{id}         Update user (SCIM PatchOp)
DELETE /Users/{id}         Delete user
```

### Group Operations
```
POST   /Groups             Create group
GET    /Groups/{id}        Retrieve group
GET    /Groups             List groups
PATCH  /Groups/{id}        Update group (add/remove members)
DELETE /Groups/{id}        Delete group
```

### Discovery Endpoints (Required)
```
GET    /ServiceProviderConfig   Provider capabilities
GET    /Schemas                 Supported schemas
GET    /Schemas/{id}            Specific schema
GET    /ResourceTypes           Supported resource types
GET    /ResourceTypes/{id}      Specific resource type

### Token Generation Endpoints (Development/Testing)
```
GET    /api/dev/tokens              Get all pre-generated test tokens
POST   /api/dev/tokens/generate     Generate custom token with specific scopes
GET    /api/dev/tokens/public-key   Get public key for JWT validation
```

⚠️ **Note**: These endpoints are for development/testing only and should be disabled in production.

## Authentication Setup

**All authentication types are ENABLED by default** for maximum IAM system compatibility:
- ✅ OAuth 2.0 / JWT (Bearer Token)
- ✅ HTTP Basic Authentication
- ✅ Mutual TLS (mTLS)

Your IAM system can use **any** of these authentication methods.

### Quick Setup

```bash
# 1. Start the server
python3 app.py

# 2. In another terminal, run the setup script
./setup_auth.sh

# 3. Load the configuration
source auth.config

# 4. Restart the server
python3 app.py
```

### Getting Tokens

```bash
# Get all available tokens
curl http://localhost:5000/api/dev/tokens | jq

# Or use the helper script
./get_tokens.sh

# Get a specific token
TOKEN=$(./get_tokens.sh full_access)
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/scim/v2/Users

# Use Basic Auth
curl -u admin:admin123 http://localhost:5000/scim/v2/Users
```

See [TOKEN_GENERATION_GUIDE.md](TOKEN_GENERATION_GUIDE.md) for complete documentation.
```

## Quick Start Examples

### Create User
```bash
curl -X POST https://example.com/Users \
  -H "Content-Type: application/scim+json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "schemas": [
      "urn:ietf:params:scim:schemas:core:2.0:User",
      "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
    ],
    "userName": "john.doe@example.com",
    "name": {
      "givenName": "John",
      "familyName": "Doe"
    },
    "emails": [{
      "value": "john.doe@example.com",
      "type": "work",
      "primary": true
    }],
    "active": true,
    "department": "Engineering",
    "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": {
      "manager": {
        "value": "manager-user-id"
      }
    }
  }'
```

### Search Users
```bash
curl -X GET "https://example.com/Users?filter=department%20eq%20%22Engineering%22&startIndex=1&count=10" \
  -H "Authorization: Bearer <token>"
```

### Deactivate User
```bash
curl -X PATCH https://example.com/Users/{id} \
  -H "Content-Type: application/scim+json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
    "Operations": [{
      "op": "replace",
      "path": "active",
      "value": false
    }]
  }'
```

### Create Group
```bash
curl -X POST https://example.com/Groups \
  -H "Content-Type: application/scim+json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
    "displayName": "Engineering Team",
    "members": [{
      "value": "user-id-123"
    }]
  }'
```

### Add Member to Group
```bash
curl -X PATCH https://example.com/Groups/{id} \
  -H "Content-Type: application/scim+json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
    "Operations": [{
      "op": "add",
      "path": "members",
      "value": [{
        "value": "user-id-456"
      }]
    }]
  }'
```

## Manager Relationship Rules

1. ✅ Manager must reference an existing User ID
2. ✅ Self-referencing is prevented (user cannot be their own manager)
3. ✅ Manager field is optional
4. ✅ When manager is deleted, dependent users' manager field is cleared
5. ✅ Manager changes are tracked in meta.lastModified

## Group Membership Model

- **Ownership**: Group resource owns membership (not User)
- **User.groups**: Read-only, computed from Group.members
- **Operations**: Add/remove members via PATCH on Group resource
- **Member Type**: Only User members supported (no nested groups)

## Filtering Support

### Supported Operators
- `eq` - Equals
- `ne` - Not equals
- `and` - Logical AND
- `or` - Logical OR

### Filter Examples
```
userName eq "john.doe@example.com"
active eq true
department eq "Engineering"
active eq true and department eq "Engineering"
externalId eq "azure-ad-12345"
```

## Pagination

```
GET /Users?startIndex=1&count=100
```

- `startIndex` - 1-based index (default: 1)
- `count` - Results per page (default: 100)
- Response includes: `totalResults`, `startIndex`, `itemsPerPage`, `Resources`

## Error Responses

All errors follow SCIM Error schema:

```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
  "status": "400",
  "scimType": "invalidValue",
  "detail": "userName is required"
}
```

### SCIM Error Types
- `invalidValue` - Invalid attribute value
- `invalidFilter` - Invalid filter syntax
- `uniqueness` - Uniqueness constraint violation
- `mutability` - Attempt to modify read-only attribute

## Enterprise IAM Compatibility

### Azure AD
✅ User provisioning (create, update, deactivate)  
✅ Group provisioning and membership  
✅ Manager relationship sync  
✅ externalId correlation  
✅ Filtering and pagination  

### Okta
✅ User lifecycle management  
✅ Group push and membership sync  
✅ Manager attribute sync  
✅ Custom attribute mapping  
✅ Incremental updates via PATCH  

### ServiceNow
✅ Identity governance integration  
✅ Role assignment via groups  
✅ Manager hierarchy  
✅ Organizational attributes  

### IBM Security Verify
✅ Identity lifecycle management  
✅ Group-based access control  
✅ Manager relationships  
✅ SCIM 2.0 protocol compliance  

## Implementation Notes

### Technology Stack (Recommended)
- **Backend**: Python (FastAPI), Node.js (Express), Java (Spring Boot), or Go
- **Database**: PostgreSQL (JSONB), MongoDB, or MySQL (JSON columns)
- **Authentication**: OAuth 2.0 Bearer Tokens
- **Transport**: HTTPS/TLS 1.2+

### Security Requirements
- OAuth 2.0 Bearer Token authentication
- HTTPS/TLS 1.2+ required
- Input validation on all requests
- SQL injection prevention
- Rate limiting
- Audit logging

### Data Model Considerations
- Use UUIDs for resource IDs
- Store timestamps in UTC (ISO 8601)
- Implement optimistic locking with ETags
- Index userName and externalId for performance
- Cascade delete for manager relationships

## Testing

### Unit Tests
- Model validation (User, Group)
- Manager relationship validation
- PATCH operation logic
- Filter parsing and application

### Integration Tests
- End-to-end API flows
- SCIM client compatibility
- Error handling scenarios
- Pagination and filtering

### Performance Tests
- Large datasets (10K+ users)
- Concurrent operations
- Filter performance
- Pagination efficiency

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design decisions
- **[COMPLIANCE.md](COMPLIANCE.md)** - SCIM 2.0 compliance details and justifications
- **[examples/request-response-examples.md](examples/request-response-examples.md)** - Complete API examples

## Why This Design is Minimal

1. **Only Essential Attributes** - 9 User attributes vs 20+ in full SCIM
2. **No Over-Engineering** - No complex entitlement models or custom schemas
3. **Standard Schemas Only** - Core User, Core Group, Enterprise User extension
4. **Essential Operations** - CRUD, filtering, pagination, discovery
5. **No Advanced Features** - No bulk operations, sorting, or change password

## What Can Be Added Later

- Additional user attributes (phoneNumbers, addresses, title)
- Bulk operations endpoint
- Advanced filtering (contains, starts with)
- Sorting support
- Change password endpoint
- Custom schema extensions

## Standards Compliance

This implementation is fully compliant with:
- ✅ **RFC 7643** - SCIM Core Schema 2.0
- ✅ **RFC 7644** - SCIM Protocol 2.0
- ✅ **RFC 6750** - OAuth 2.0 Bearer Token Usage
- ✅ **RFC 7231** - HTTP/1.1 Semantics and Content

## License

This is a reference implementation for educational and integration purposes.

## Support

For questions about SCIM 2.0 specification:
- RFC 7643: https://tools.ietf.org/html/rfc7643
- RFC 7644: https://tools.ietf.org/html/rfc7644

## Contributing

This is a minimal reference implementation. Extensions should maintain:
1. SCIM 2.0 compliance
2. Minimalism principle
3. Enterprise IAM compatibility
4. Clear documentation

---

**Built with ❤️ for enterprise IAM integration**