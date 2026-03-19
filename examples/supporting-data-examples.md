# Supporting Data API Examples

This document provides complete examples of Supporting Data API requests and responses.

**IMPORTANT**: These are NOT SCIM endpoints. They are separate, read-only APIs for lookup data.
**NOTE**: Only paginated GET list endpoints are supported. Individual GET by ID is not supported.

---

## Table of Contents
1. [Roles API Examples](#roles-api-examples)
2. [Departments API Examples](#departments-api-examples)
3. [Integration Workflows](#integration-workflows)
4. [Error Examples](#error-examples)

---

## Roles API Examples

### 1. List All Roles

**Request:**
```http
GET /api/supporting-data/roles HTTP/1.1
Host: example.com
Authorization: Bearer <token-with-supportingdata.read>
```

**Response (200 OK):**
```json
{
  "totalResults": 7,
  "startIndex": 1,
  "itemsPerPage": 7,
  "roles": [
    {
      "id": "role-admin",
      "name": "Administrator",
      "description": "Full system access and administrative privileges"
    },
    {
      "id": "role-developer",
      "name": "Developer",
      "description": "Development and deployment access"
    },
    {
      "id": "role-analyst",
      "name": "Analyst",
      "description": "Read-only access for analysis and reporting"
    },
    {
      "id": "role-manager",
      "name": "Manager",
      "description": "Team management and approval capabilities"
    },
    {
      "id": "role-auditor",
      "name": "Auditor",
      "description": "Audit and compliance review access"
    },
    {
      "id": "role-support",
      "name": "Support",
      "description": "Customer support and helpdesk access"
    },
    {
      "id": "role-readonly",
      "name": "Read-Only User",
      "description": "Basic read-only access"
    }
  ]
}
```

---

### 2. List Roles with Pagination

**Request:**
```http
GET /api/supporting-data/roles?startIndex=1&count=3 HTTP/1.1
Host: example.com
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "totalResults": 7,
  "startIndex": 1,
  "itemsPerPage": 3,
  "roles": [
    {
      "id": "role-admin",
      "name": "Administrator",
      "description": "Full system access and administrative privileges"
    },
    {
      "id": "role-developer",
      "name": "Developer",
      "description": "Development and deployment access"
    },
    {
      "id": "role-analyst",
      "name": "Analyst",
      "description": "Read-only access for analysis and reporting"
    }
  ]
}
```

**Next Page:**
```http
GET /api/supporting-data/roles?startIndex=4&count=3
```


---

## Departments API Examples

### 1. List All Departments

**Request:**
```http
GET /api/supporting-data/departments HTTP/1.1
Host: example.com
Authorization: Bearer <token-with-supportingdata.read>
```

**Response (200 OK):**
```json
{
  "totalResults": 10,
  "startIndex": 1,
  "itemsPerPage": 10,
  "departments": [
    {
      "id": "dept-eng",
      "name": "Engineering"
    },
    {
      "id": "dept-product",
      "name": "Product Management"
    },
    {
      "id": "dept-sales",
      "name": "Sales"
    },
    {
      "id": "dept-marketing",
      "name": "Marketing"
    },
    {
      "id": "dept-hr",
      "name": "Human Resources"
    },
    {
      "id": "dept-finance",
      "name": "Finance"
    },
    {
      "id": "dept-legal",
      "name": "Legal"
    },
    {
      "id": "dept-ops",
      "name": "Operations"
    },
    {
      "id": "dept-support",
      "name": "Customer Support"
    },
    {
      "id": "dept-exec",
      "name": "Executive"
    }
  ]
}
```

---

### 2. List Departments with Pagination

**Request:**
```http
GET /api/supporting-data/departments?startIndex=1&count=5 HTTP/1.1
```

**Response (200 OK):**
```json
{
  "totalResults": 10,
  "startIndex": 1,
  "itemsPerPage": 5,
  "departments": [
    {"id": "dept-eng", "name": "Engineering"},
    {"id": "dept-product", "name": "Product Management"},
    {"id": "dept-sales", "name": "Sales"},
    {"id": "dept-marketing", "name": "Marketing"},
    {"id": "dept-hr", "name": "Human Resources"}
  ]
}
```


---

## Integration Workflows

### Workflow 1: Onboard User with Role and Department

**Step 1: Query Available Roles**
```http
GET /api/supporting-data/roles
```
Response: List of 7 predefined roles

**Step 2: Query Available Departments**
```http
GET /api/supporting-data/departments
```
Response: List of 10 predefined departments

**Step 3: Create SCIM User with Department**
```http
POST /scim/v2/Users
Content-Type: application/scim+json

{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "userName": "alice.smith@example.com",
  "name": {
    "givenName": "Alice",
    "familyName": "Smith"
  },
  "emails": [{
    "value": "alice.smith@example.com",
    "type": "work",
    "primary": true
  }],
  "department": "Engineering",
  "active": true
}
```

**Step 4: Create SCIM Group for Role (if not exists)**
```http
POST /scim/v2/Groups
Content-Type: application/scim+json

{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
  "displayName": "Developer",
  "externalId": "role-developer"
}
```

**Step 5: Assign User to Role Group**
```http
PATCH /scim/v2/Groups/{developer-group-id}
Content-Type: application/scim+json

{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [{
    "op": "add",
    "path": "members",
    "value": [{"value": "alice-user-id"}]
  }]
}
```

**Result**:
- User created with department "Engineering" (from supporting data)
- User assigned "Developer" role via SCIM Group
- No SCIM code modified

---

### Workflow 2: Transfer User to Different Department

**Step 1: Query Departments to Find Target Department**
```http
GET /api/supporting-data/departments
```
Response: List of all departments (find "Product Management" in the list)

**Step 2: Update SCIM User Department**
```http
PATCH /scim/v2/Users/{user-id}
Content-Type: application/scim+json

{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [{
    "op": "replace",
    "path": "department",
    "value": "Product Management"
  }]
}
```

**Result**:
- User department updated via standard SCIM PATCH
- Department value validated against supporting data
- No SCIM code modified

---

### Workflow 3: Assign Additional Role

**Step 1: Query Roles to Find Target Role**
```http
GET /api/supporting-data/roles
```
Response: List of all roles (find "Manager" in the list)

**Step 2: Find SCIM Group for Role**
```http
GET /scim/v2/Groups?filter=displayName eq "Manager"
```

**Step 3: Add User to Manager Group**
```http
PATCH /scim/v2/Groups/{manager-group-id}
Content-Type: application/scim+json

{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [{
    "op": "add",
    "path": "members",
    "value": [{"value": "user-id"}]
  }]
}
```

**Result**:
- User assigned additional "Manager" role
- Role validated against supporting data
- No SCIM code modified

---

### Workflow 4: List Users by Department (Using SCIM)

**Step 1: Query Departments (Optional)**
```http
GET /api/supporting-data/departments
```

**Step 2: Filter SCIM Users by Department**
```http
GET /scim/v2/Users?filter=department eq "Engineering"
```

Response:
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
  "totalResults": 15,
  "Resources": [
    {
      "id": "user-1",
      "userName": "alice@example.com",
      "department": "Engineering",
      "active": true
    }
  ]
}
```

**Result**:
- Users filtered by department using standard SCIM filtering
- Department value matches supporting data
- No SCIM code modified

---

### Workflow 5: List Users with Specific Role (Using SCIM)

**Step 1: Query Role (Optional)**
```http
GET /api/supporting-data/roles/role-developer
```

**Step 2: Find SCIM Group for Role**
```http
GET /scim/v2/Groups?filter=displayName eq "Developer"
```

Response:
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
  "totalResults": 1,
  "Resources": [{
    "id": "group-123",
    "displayName": "Developer",
    "members": [
      {"value": "user-1", "display": "Alice Smith"},
      {"value": "user-2", "display": "Bob Jones"}
    ]
  }]
}
```

**Step 3: Extract User IDs from Group Members**

**Result**:
- Users with "Developer" role identified via SCIM Group membership
- Role validated against supporting data
- No SCIM code modified

---

## Error Examples

### 1. Invalid Pagination Parameters

**Request:**
```http
GET /api/supporting-data/roles?startIndex=0&count=10
```

**Response (400 Bad Request):**
```json
{
  "error": {
    "status": 400,
    "message": "startIndex must be >= 1"
  }
}
```

---

### 2. Missing Authentication

**Request:**
```http
GET /api/supporting-data/roles
```

**Response (401 Unauthorized):**
```json
{
  "error": {
    "status": 401,
    "message": "Authentication required"
  }
}
```

---

### 3. Insufficient Permissions

**Request:**
```http
GET /api/supporting-data/roles
Authorization: Bearer <token-without-supportingdata.read>
```

**Response (403 Forbidden):**
```json
{
  "error": {
    "status": 403,
    "message": "Insufficient permissions. Required scope: supportingdata.read"
  }
}
```

---

### 4. Attempt to Create Role (Not Allowed)

**Request:**
```http
POST /api/supporting-data/roles
Content-Type: application/json

{
  "name": "New Role",
  "description": "Custom role"
}
```

**Response (405 Method Not Allowed):**
```json
{
  "error": {
    "status": 405,
    "message": "Method not allowed. Supporting data is read-only."
  }
}
```

---

### 5. Attempt to Update Department (Not Allowed)

**Request:**
```http
PATCH /api/supporting-data/departments/dept-eng
Content-Type: application/json

{
  "name": "Software Engineering"
}
```

**Response (405 Method Not Allowed):**
```json
{
  "error": {
    "status": 405,
    "message": "Method not allowed. Supporting data is read-only."
  }
}
```

---

### 6. Attempt to Delete Role (Not Allowed)

**Request:**
```http
DELETE /api/supporting-data/roles/role-admin
```

**Response (405 Method Not Allowed):**
```json
{
  "error": {
    "status": 405,
    "message": "Method not allowed. Supporting data endpoints only support paginated GET list operations."
  }
}
```

---

### 7. Attempt to GET Individual Role by ID (Not Supported)

**Request:**
```http
GET /api/supporting-data/roles/role-admin
```

**Response (405 Method Not Allowed):**
```json
{
  "error": {
    "status": 405,
    "message": "Method not allowed. Supporting data endpoints only support paginated GET list operations."
  }
}
```

---

## Comparison: Supporting Data vs SCIM

### Supporting Data API (Read-Only)

```http
# List roles
GET /api/supporting-data/roles

# Response format
{
  "totalResults": 7,
  "startIndex": 1,
  "itemsPerPage": 7,
  "roles": [...]
}

# Characteristics:
# - Simple JSON format
# - Read-only (GET only)
# - Predefined data
# - No SCIM schemas
```

### SCIM API (Full CRUD)

```http
# List groups
GET /scim/v2/Groups

# Response format
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
  "totalResults": 5,
  "startIndex": 1,
  "itemsPerPage": 5,
  "Resources": [...]
}

# Characteristics:
# - SCIM JSON format
# - Full CRUD (POST, GET, PATCH, DELETE)
# - Dynamic data
# - SCIM schemas required
```

---

## Notes

1. **Authentication**: All supporting data endpoints require Bearer token with `supportingdata.read` scope
2. **Pagination**: Uses same pattern as SCIM (startIndex, count) but simpler response format
3. **Read-Only**: No POST, PATCH, PUT, or DELETE operations allowed
4. **Predefined**: Roles and Departments are fixed, configured sets
5. **Not SCIM**: These are NOT SCIM resources and don't follow SCIM schema format
6. **Integration**: Used for lookup and validation, actual provisioning happens via SCIM

---

## Quick Reference

### Roles Endpoints
```
GET /api/supporting-data/roles              # List all roles (paginated)
```

### Departments Endpoints
```
GET /api/supporting-data/departments        # List all departments (paginated)
```

### Pagination Parameters
```
?startIndex=1    # 1-based index (default: 1)
&count=100       # Results per page (default: 100)
```

### Required Scope
```
supportingdata.read
```

### Not Allowed
```
GET    /api/supporting-data/roles/{id}      # ❌ 405 Method Not Allowed
POST   /api/supporting-data/roles           # ❌ 405 Method Not Allowed
PATCH  /api/supporting-data/roles/{id}      # ❌ 405 Method Not Allowed
DELETE /api/supporting-data/roles/{id}      # ❌ 405 Method Not Allowed
GET    /api/supporting-data/departments/{id} # ❌ 405 Method Not Allowed
POST   /api/supporting-data/departments     # ❌ 405 Method Not Allowed
PATCH  /api/supporting-data/departments/{id} # ❌ 405 Method Not Allowed
DELETE /api/supporting-data/departments/{id} # ❌ 405 Method Not Allowed