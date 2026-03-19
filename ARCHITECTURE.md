# SCIM 2.0 Target System Architecture

## Overview

This is a **minimal SCIM 2.0 Service Provider** implementation designed to be managed by enterprise IAM & Governance products (Azure AD, Okta, ServiceNow, IBM Security Verify).

## Design Principles

1. **Strict SCIM 2.0 Compliance**: Follows RFC 7643 (Core Schema) and RFC 7644 (Protocol)
2. **Minimal Schema**: Only mandatory and essential enterprise identity attributes
3. **No Over-Engineering**: Avoids custom extensions and unnecessary complexity
4. **Enterprise Ready**: Works with standard SCIM clients out of the box

## Architecture Components

### 1. Resource Models

#### User Resource
- **Core Schema**: `urn:ietf:params:scim:schemas:core:2.0:User`
- **Enterprise Extension**: `urn:ietf:params:scim:schemas:extension:enterprise:2.0:User`
- **Minimal Attributes**:
  - `id` (server-generated, immutable)
  - `userName` (unique, required)
  - `name.givenName`, `name.familyName`
  - `emails` (work email only, primary=true)
  - `active` (boolean, for deprovisioning)
  - `department` (organizational context)
  - `gender` (optional demographic)
  - `manager.value`, `manager.display` (Enterprise extension)
  - `externalId` (optional, for external system correlation)
  - `meta` (resourceType, created, lastModified, location)

#### Group Resource
- **Core Schema**: `urn:ietf:params:scim:schemas:core:2.0:Group`
- **Purpose**: Represents roles and access groups
- **Minimal Attributes**:
  - `id` (server-generated, immutable)
  - `displayName` (required)
  - `members` (array of User references)
  - `meta` (resourceType, created, lastModified, location)

### 2. Data Model

```
┌─────────────────────────────────────────────────────────────┐
│                         User                                 │
├─────────────────────────────────────────────────────────────┤
│ id: string (UUID)                                            │
│ userName: string (unique)                                    │
│ externalId: string (optional)                                │
│ name: { givenName, familyName }                              │
│ emails: [{ value, primary }]                                 │
│ active: boolean                                              │
│ department: string                                           │
│ gender: string (optional)                                    │
│ manager: { value: userId, display }  ──────┐                │
│ meta: { resourceType, created, ... }       │                │
└────────────────────────────────────────────┼────────────────┘
                                              │
                                              │ references
                                              │
                                              ▼
                                         ┌────────┐
                                         │  User  │
                                         └────────┘

┌─────────────────────────────────────────────────────────────┐
│                        Group                                 │
├─────────────────────────────────────────────────────────────┤
│ id: string (UUID)                                            │
│ displayName: string                                          │
│ members: [{ value: userId, $ref, type }]                     │
│ meta: { resourceType, created, ... }                         │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ references
                    ▼
               ┌────────┐
               │  User  │
               └────────┘
```

### 3. Manager Relationship Rules

1. **Self-Reference Prevention**: A user cannot be their own manager
2. **Validation**: `manager.value` must reference an existing User ID
3. **Optional**: Manager can be null/absent
4. **Cascading**: When a manager is deleted, dependent users' manager field is cleared
5. **Display Name**: `manager.display` is optional and informational only

### 4. Group Membership Model

- **Ownership**: Group resource owns membership (not User)
- **User.groups**: Optional, read-only, computed from Group.members
- **Operations**: Add/remove members via PATCH on Group resource
- **Member Type**: Only User members supported (no nested groups)

## API Endpoints

### User Operations
```
POST   /Users              - Create user
GET    /Users/{id}         - Retrieve user
GET    /Users              - List/search users (with filtering)
PATCH  /Users/{id}         - Update user (SCIM PatchOp)
DELETE /Users/{id}         - Delete user
```

### Group Operations
```
POST   /Groups             - Create group
GET    /Groups/{id}        - Retrieve group
GET    /Groups             - List/search groups
PATCH  /Groups/{id}        - Update group (add/remove members)
DELETE /Groups/{id}        - Delete group
```

### Discovery Endpoints (Required)
```
GET    /ServiceProviderConfig  - Provider capabilities
GET    /Schemas                - Supported schemas
GET    /ResourceTypes          - Supported resource types
```

## SCIM Protocol Compliance

### 1. HTTP Methods
- **POST**: Create resources
- **GET**: Retrieve resources (single or list)
- **PATCH**: Partial updates using SCIM PatchOp
- **DELETE**: Remove resources
- **PUT**: Not implemented (PATCH preferred per SCIM best practices)

### 2. PATCH Operations (RFC 7644 Section 3.5.2)

Supported operations:
- `add`: Add new attribute values
- `replace`: Replace existing attribute values
- `remove`: Remove attribute values

Example:
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [
    {
      "op": "replace",
      "path": "active",
      "value": false
    },
    {
      "op": "replace",
      "path": "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User:manager",
      "value": {
        "value": "user-id-123"
      }
    }
  ]
}
```

### 3. Filtering (RFC 7644 Section 3.4.2.2)

Supported operators:
- `eq` (equals)
- `ne` (not equals)
- `and` (logical AND)
- `or` (logical OR)

Example:
```
GET /Users?filter=userName eq "john.doe@example.com"
GET /Users?filter=active eq true and department eq "Engineering"
```

### 4. Pagination

- `startIndex`: 1-based index (default: 1)
- `count`: Number of results per page (default: 100)
- Response includes: `totalResults`, `startIndex`, `itemsPerPage`, `Resources`

### 5. HTTP Headers

**Case-Insensitive Handling**:
- `Content-Type: application/scim+json`
- `Authorization: Bearer <token>`

### 6. Error Responses (RFC 7644 Section 3.12)

```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
  "status": "400",
  "scimType": "invalidValue",
  "detail": "userName is required"
}
```

## Technology Stack Recommendations

### Backend Options
1. **Node.js + Express**: Fast development, good SCIM libraries
2. **Python + FastAPI**: Type safety, automatic OpenAPI docs
3. **Java + Spring Boot**: Enterprise-grade, robust
4. **Go**: High performance, simple deployment

### Database
- **PostgreSQL**: JSONB support for flexible schema storage
- **MongoDB**: Native JSON document storage
- **MySQL**: Traditional relational with JSON columns

### Authentication
- **OAuth 2.0 Bearer Tokens**: Standard for SCIM
- **API Keys**: Simple alternative for testing

## Security Considerations

1. **Authentication**: All endpoints require valid bearer token
2. **Authorization**: Role-based access control (RBAC)
3. **Input Validation**: Strict schema validation
4. **SQL Injection**: Use parameterized queries
5. **Rate Limiting**: Prevent abuse
6. **HTTPS Only**: TLS 1.2+ required
7. **Audit Logging**: Track all resource changes

## Deployment Architecture

```
┌─────────────────┐
│  IAM Provider   │
│  (Azure AD,     │
│   Okta, etc.)   │
└────────┬────────┘
         │ HTTPS/TLS
         │ Bearer Token
         ▼
┌─────────────────┐
│  Load Balancer  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SCIM Service   │
│  Provider API   │
│  (This System)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Database     │
│  (PostgreSQL)   │
└─────────────────┘
```

## Why This Design is SCIM-Compliant and Minimal

### SCIM Compliance
1. ✅ Implements mandatory User and Group resources
2. ✅ Uses standard SCIM schemas (no custom extensions except Enterprise User)
3. ✅ Follows SCIM PatchOp specification
4. ✅ Implements required discovery endpoints
5. ✅ Supports filtering and pagination
6. ✅ Uses proper SCIM error responses
7. ✅ Case-insensitive header handling
8. ✅ Supports externalId for correlation

### Minimalism
1. ✅ Only essential User attributes (no addresses, phones, photos, titles)
2. ✅ Single email (work only)
3. ✅ No custom schemas or extensions (except standard Enterprise User)
4. ✅ Groups represent roles (no separate Role API)
5. ✅ No complex entitlement models
6. ✅ No unnecessary demographic fields
7. ✅ Manager relationship uses standard Enterprise extension

### Enterprise Compatibility
- Works with Azure AD SCIM provisioning
- Compatible with Okta Lifecycle Management
- Supports ServiceNow Identity Governance
- Works with IBM Security Verify

## Next Steps

1. Choose technology stack
2. Implement data models with validation
3. Build API endpoints
4. Add authentication/authorization
5. Implement filtering and pagination
6. Add comprehensive error handling
7. Create integration tests with SCIM clients
8. Deploy with monitoring and logging