# SCIM 2.0 Request/Response Examples

This document provides comprehensive examples of SCIM 2.0 API requests and responses for the minimal target system implementation.

## Table of Contents
1. [User Operations](#user-operations)
2. [Group Operations](#group-operations)
3. [Discovery Operations](#discovery-operations)
4. [Error Responses](#error-responses)

---

## User Operations

### 1. Create User (POST /Users)

**Request:**
```http
POST /Users HTTP/1.1
Host: example.com
Content-Type: application/scim+json
Authorization: Bearer <token>

{
  "schemas": [
    "urn:ietf:params:scim:schemas:core:2.0:User",
    "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
  ],
  "userName": "john.doe@example.com",
  "externalId": "azure-ad-12345",
  "name": {
    "givenName": "John",
    "familyName": "Doe"
  },
  "emails": [
    {
      "value": "john.doe@example.com",
      "type": "work",
      "primary": true
    }
  ],
  "active": true,
  "department": "Engineering",
  "gender": "male",
  "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": {
    "manager": {
      "value": "manager-user-id-123",
      "displayName": "Jane Smith"
    }
  }
}
```

**Response (201 Created):**
```json
{
  "schemas": [
    "urn:ietf:params:scim:schemas:core:2.0:User",
    "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
  ],
  "id": "user-id-456",
  "userName": "john.doe@example.com",
  "externalId": "azure-ad-12345",
  "name": {
    "givenName": "John",
    "familyName": "Doe"
  },
  "emails": [
    {
      "value": "john.doe@example.com",
      "type": "work",
      "primary": true
    }
  ],
  "active": true,
  "department": "Engineering",
  "gender": "male",
  "groups": [],
  "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": {
    "manager": {
      "value": "manager-user-id-123",
      "$ref": "https://example.com/Users/manager-user-id-123",
      "displayName": "Jane Smith"
    }
  },
  "meta": {
    "resourceType": "User",
    "created": "2026-03-19T09:00:00.000Z",
    "lastModified": "2026-03-19T09:00:00.000Z",
    "location": "https://example.com/Users/user-id-456",
    "version": "W/\"version-uuid\""
  }
}
```

### 2. List Users with Filter

**Request:**
```http
GET /Users?filter=department%20eq%20%22Engineering%22&startIndex=1&count=10 HTTP/1.1
```

**Response:**
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
  "totalResults": 25,
  "startIndex": 1,
  "itemsPerPage": 10,
  "Resources": [
    {
      "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
      "id": "user-id-456",
      "userName": "john.doe@example.com",
      "active": true,
      "department": "Engineering"
    }
  ]
}
```

### 3. Update User - Deactivate (PATCH)

**Request:**
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [
    {
      "op": "replace",
      "path": "active",
      "value": false
    }
  ]
}
```

### 4. Update User - Change Manager

**Request:**
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [
    {
      "op": "replace",
      "path": "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User:manager",
      "value": {
        "value": "new-manager-id-999"
      }
    }
  ]
}
```

---

## Group Operations

### 1. Create Group (POST /Groups)

**Request:**
```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
  "displayName": "Engineering Team",
  "externalId": "azure-ad-group-789",
  "members": [
    {
      "value": "user-id-456",
      "display": "John Doe"
    },
    {
      "value": "user-id-789",
      "display": "Jane Smith"
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
  "id": "group-id-123",
  "displayName": "Engineering Team",
  "externalId": "azure-ad-group-789",
  "members": [
    {
      "value": "user-id-456",
      "$ref": "https://example.com/Users/user-id-456",
      "type": "User",
      "display": "John Doe"
    },
    {
      "value": "user-id-789",
      "$ref": "https://example.com/Users/user-id-789",
      "type": "User",
      "display": "Jane Smith"
    }
  ],
  "meta": {
    "resourceType": "Group",
    "created": "2026-03-19T09:00:00.000Z",
    "lastModified": "2026-03-19T09:00:00.000Z",
    "location": "https://example.com/Groups/group-id-123",
    "version": "W/\"version-uuid\""
  }
}
```

### 2. Get Group (GET /Groups/{id})

**Response:**
```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
  "id": "group-id-123",
  "displayName": "Engineering Team",
  "members": [
    {
      "value": "user-id-456",
      "$ref": "https://example.com/Users/user-id-456",
      "type": "User",
      "display": "John Doe"
    }
  ],
  "meta": {
    "resourceType": "Group",
    "location": "https://example.com/Groups/group-id-123"
  }
}
```

### 3. Add Members to Group (PATCH /Groups/{id})

**Request:**
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [
    {
      "op": "add",
      "path": "members",
      "value": [
        {
          "value": "user-id-999",
          "display": "Bob Johnson"
        }
      ]
    }
  ]
}
```

### 4. Remove Member from Group (PATCH /Groups/{id})

**Request:**
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [
    {
      "op": "remove",
      "path": "members[value eq \"user-id-456\"]"
    }
  ]
}
```

**Alternative syntax:**
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [
    {
      "op": "remove",
      "path": "members",
      "value": {
        "value": "user-id-456"
      }
    }
  ]
}
```

---

## Discovery Operations

### 1. Service Provider Config (GET /ServiceProviderConfig)

**Response:**
```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
  "documentationUri": "https://example.com/scim/v2/docs",
  "patch": {
    "supported": true
  },
  "bulk": {
    "supported": false,
    "maxOperations": 0,
    "maxPayloadSize": 0
  },
  "filter": {
    "supported": true,
    "maxResults": 1000
  },
  "changePassword": {
    "supported": false
  },
  "sort": {
    "supported": false
  },
  "etag": {
    "supported": true
  },
  "authenticationSchemes": [
    {
      "type": "oauthbearertoken",
      "name": "OAuth Bearer Token",
      "description": "Authentication using OAuth Bearer Token",
      "specUri": "https://tools.ietf.org/html/rfc6750",
      "primary": true
    }
  ],
  "meta": {
    "resourceType": "ServiceProviderConfig",
    "location": "https://example.com/ServiceProviderConfig"
  }
}
```

### 2. Schemas (GET /Schemas)

**Response:**
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
  "totalResults": 3,
  "Resources": [
    {
      "id": "urn:ietf:params:scim:schemas:core:2.0:User",
      "name": "User",
      "description": "SCIM 2.0 User Resource"
    },
    {
      "id": "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
      "name": "EnterpriseUser",
      "description": "Enterprise User Extension"
    },
    {
      "id": "urn:ietf:params:scim:schemas:core:2.0:Group",
      "name": "Group",
      "description": "SCIM 2.0 Group Resource"
    }
  ]
}
```

### 3. Resource Types (GET /ResourceTypes)

**Response:**
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
  "totalResults": 2,
  "Resources": [
    {
      "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
      "id": "User",
      "name": "User",
      "endpoint": "/Users",
      "description": "SCIM 2.0 User Resource",
      "schema": "urn:ietf:params:scim:schemas:core:2.0:User",
      "schemaExtensions": [
        {
          "schema": "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
          "required": false
        }
      ]
    },
    {
      "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
      "id": "Group",
      "name": "Group",
      "endpoint": "/Groups",
      "description": "SCIM 2.0 Group Resource",
      "schema": "urn:ietf:params:scim:schemas:core:2.0:Group"
    }
  ]
}
```

---

## Error Responses

### 1. Invalid Request (400 Bad Request)

**Response:**
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
  "status": "400",
  "scimType": "invalidValue",
  "detail": "userName is required and cannot be empty"
}
```

### 2. Resource Not Found (404 Not Found)

**Response:**
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
  "status": "404",
  "detail": "User with id 'invalid-id' not found"
}
```

### 3. Uniqueness Violation (409 Conflict)

**Response:**
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
  "status": "409",
  "scimType": "uniqueness",
  "detail": "userName 'john.doe@example.com' already exists"
}
```

### 4. Invalid Filter (400 Bad Request)

**Response:**
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
  "status": "400",
  "scimType": "invalidFilter",
  "detail": "Invalid filter syntax: invalid expression"
}
```

### 5. Self-Referencing Manager (400 Bad Request)

**Response:**
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
  "status": "400",
  "scimType": "invalidValue",
  "detail": "A user cannot be their own manager"
}
```

---

## Common SCIM Filter Examples

```
# Exact match
filter=userName eq "john.doe@example.com"

# Active users only
filter=active eq true

# Department filter
filter=department eq "Engineering"

# Logical AND
filter=active eq true and department eq "Engineering"

# Logical OR
filter=department eq "Engineering" or department eq "Product"

# Not equal
filter=active ne false

# External ID lookup
filter=externalId eq "azure-ad-12345"
```

---

## Pagination Examples

```
# First page (default)
GET /Users?startIndex=1&count=100

# Second page
GET /Users?startIndex=101&count=100

# Small page size
GET /Users?startIndex=1&count=10

# With filter and pagination
GET /Users?filter=active eq true&startIndex=1&count=50
```

---

## Notes

1. **Case-Insensitive Headers**: All HTTP headers are case-insensitive per HTTP spec
2. **Content-Type**: Use `application/scim+json` for SCIM requests/responses
3. **Authentication**: All endpoints require valid Bearer token
4. **Timestamps**: All timestamps are in ISO 8601 format with UTC timezone (Z suffix)
5. **IDs**: All resource IDs are UUIDs generated by the server
6. **Manager Validation**: Manager must reference an existing user and cannot be self-referencing
7. **Group Membership**: Managed via Group resource, User.groups is read-only