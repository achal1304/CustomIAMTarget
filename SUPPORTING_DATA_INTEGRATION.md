# Supporting Data Integration Guide

## Overview

This document explains how **Supporting Data APIs** (Roles and Departments) integrate with the existing **SCIM 2.0 implementation** without modifying it.

## Key Principles

1. ✅ **SCIM Code Remains Untouched** - No modifications to SCIM endpoints, schemas, or logic
2. ✅ **Separate API Namespace** - Supporting data uses `/api/supporting-data/`, not `/scim/v2/`
3. ✅ **Read-Only** - Supporting data cannot be created, updated, or deleted
4. ✅ **Predefined Values** - Roles and Departments are fixed, configured sets
5. ✅ **Lookup Only** - Used for validation and mapping, not provisioning

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    IAM Product / Client                      │
└────────────┬────────────────────────────────┬────────────────┘
             │                                │
             │ 1. Query Supporting Data       │ 2. Use SCIM APIs
             │    (Read-Only)                 │    (Full CRUD)
             ▼                                ▼
┌────────────────────────────┐  ┌────────────────────────────┐
│  Supporting Data APIs      │  │     SCIM 2.0 APIs          │
│  (Non-SCIM)                │  │                            │
├────────────────────────────┤  ├────────────────────────────┤
│ GET /api/supporting-data/  │  │ POST   /scim/v2/Users      │
│     roles                  │  │ GET    /scim/v2/Users      │
│ GET /api/supporting-data/  │  │ PATCH  /scim/v2/Users/{id} │
│     departments            │  │ DELETE /scim/v2/Users/{id} │
│                            │  │                            │
│ READ-ONLY                  │  │ POST   /scim/v2/Groups     │
│ Predefined Data            │  │ PATCH  /scim/v2/Groups/{id}│
└────────────────────────────┘  └────────────────────────────┘
             │                                │
             │                                │
             ▼                                ▼
┌────────────────────────────────────────────────────────────┐
│              Supporting Data Repository                     │
│              (Predefined Roles & Departments)               │
└────────────────────────────────────────────────────────────┘
```

---

## Integration Patterns

### Pattern 1: Roles → SCIM Groups

**Concept**: Roles are exposed as supporting data, but actual role assignment happens via SCIM Groups.

**Mapping**:
```
Role.name (Supporting Data) ←→ Group.displayName (SCIM)
```

**Workflow**:

1. **IAM Product queries available roles**:
   ```http
   GET /api/supporting-data/roles
   ```
   Response:
   ```json
   {
     "totalResults": 7,
     "roles": [
       {"id": "role-admin", "name": "Administrator"},
       {"id": "role-developer", "name": "Developer"}
     ]
   }
   ```

2. **IAM Product creates SCIM Groups matching role names**:
   ```http
   POST /scim/v2/Groups
   ```
   Request:
   ```json
   {
     "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
     "displayName": "Administrator",
     "externalId": "role-admin"
   }
   ```

3. **IAM Product assigns users to groups** (standard SCIM):
   ```http
   PATCH /scim/v2/Groups/{group-id}
   ```
   Request:
   ```json
   {
     "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
     "Operations": [{
       "op": "add",
       "path": "members",
       "value": [{"value": "user-id-123"}]
     }]
   }
   ```

**Key Points**:
- Supporting Data provides the **list of valid roles**
- SCIM Groups provide the **actual role assignments**
- No SCIM modifications needed
- Role names are validated against supporting data (optional)

---

### Pattern 2: Departments → SCIM User Attribute

**Concept**: Departments are exposed as supporting data, and SCIM Users reference them via the `department` attribute.

**Mapping**:
```
Department.name (Supporting Data) ←→ User.department (SCIM)
```

**Workflow**:

1. **IAM Product queries available departments**:
   ```http
   GET /api/supporting-data/departments
   ```
   Response:
   ```json
   {
     "totalResults": 10,
     "departments": [
       {"id": "dept-eng", "name": "Engineering"},
       {"id": "dept-product", "name": "Product Management"}
     ]
   }
   ```

2. **IAM Product creates SCIM User with department**:
   ```http
   POST /scim/v2/Users
   ```
   Request:
   ```json
   {
     "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
     "userName": "john.doe@example.com",
     "department": "Engineering",
     "active": true
   }
   ```

3. **IAM Product updates user department** (standard SCIM):
   ```http
   PATCH /scim/v2/Users/{user-id}
   ```
   Request:
   ```json
   {
     "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
     "Operations": [{
       "op": "replace",
       "path": "department",
       "value": "Product Management"
     }]
   }
   ```

**Key Points**:
- Supporting Data provides the **list of valid departments**
- SCIM User.department stores the **actual department assignment**
- No SCIM modifications needed
- Department names are validated against supporting data (optional)

---

## API Comparison

### Supporting Data APIs (Non-SCIM)

| Endpoint | Method | Purpose | Modifiable |
|----------|--------|---------|------------|
| `/api/supporting-data/roles` | GET | List all roles (paginated) | ❌ No |
| `/api/supporting-data/departments` | GET | List all departments (paginated) | ❌ No |

**Characteristics**:
- Read-only (GET paginated list only)
- Predefined, fixed data
- Simple JSON responses (not SCIM format)
- Pagination support (startIndex, count)
- No individual GET by ID
- No authentication scopes for write operations

### SCIM 2.0 APIs (Unchanged)

| Endpoint | Methods | Purpose | Modifiable |
|----------|---------|---------|------------|
| `/scim/v2/Users` | POST, GET, PATCH, DELETE | Manage users | ✅ Yes |
| `/scim/v2/Groups` | POST, GET, PATCH, DELETE | Manage groups | ✅ Yes |
| `/scim/v2/ServiceProviderConfig` | GET | Provider capabilities | ❌ No |
| `/scim/v2/Schemas` | GET | SCIM schemas | ❌ No |
| `/scim/v2/ResourceTypes` | GET | Resource types | ❌ No |

**Characteristics**:
- Full CRUD operations
- SCIM 2.0 compliant (RFC 7643, RFC 7644)
- SCIM JSON format
- SCIM PatchOp support
- SCIM filtering and pagination

---

## Data Flow Examples

### Example 1: Onboard User with Role and Department

**Step 1**: IAM Product queries supporting data
```http
GET /api/supporting-data/roles
GET /api/supporting-data/departments
```

**Step 2**: IAM Product creates SCIM User
```http
POST /scim/v2/Users
{
  "userName": "alice@example.com",
  "name": {"givenName": "Alice", "familyName": "Smith"},
  "department": "Engineering",
  "active": true
}
```

**Step 3**: IAM Product creates/finds SCIM Group for role
```http
POST /scim/v2/Groups
{
  "displayName": "Developer",
  "externalId": "role-developer"
}
```

**Step 4**: IAM Product assigns user to group
```http
PATCH /scim/v2/Groups/{group-id}
{
  "Operations": [{
    "op": "add",
    "path": "members",
    "value": [{"value": "alice-user-id"}]
  }]
}
```

**Result**:
- User created with department from supporting data
- User assigned to role via SCIM Group
- No SCIM code modified

---

### Example 2: Transfer User to Different Department

**Step 1**: IAM Product queries departments to find the target department
```http
GET /api/supporting-data/departments
```

**Step 2**: IAM Product updates SCIM User
```http
PATCH /scim/v2/Users/{user-id}
{
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

### Example 3: Assign Additional Role

**Step 1**: IAM Product queries roles to find the target role
```http
GET /api/supporting-data/roles
```

**Step 2**: IAM Product finds/creates SCIM Group
```http
GET /scim/v2/Groups?filter=displayName eq "Manager"
```

**Step 3**: IAM Product adds user to group
```http
PATCH /scim/v2/Groups/{manager-group-id}
{
  "Operations": [{
    "op": "add",
    "path": "members",
    "value": [{"value": "user-id"}]
  }]
}
```

**Result**:
- User assigned additional role via SCIM Group membership
- Role validated against supporting data
- No SCIM code modified

---

## Validation Integration (Optional)

Supporting data APIs provide validation helpers that can be used by SCIM endpoints:

### Department Validation in User Creation

```python
# In SCIM User endpoint (optional enhancement)
from api.supporting_data_endpoints import SupportingDataEndpoints

def create_user(request_body):
    department = request_body.get("department")
    
    # Optional: Validate department against supporting data
    if department:
        supporting_data = SupportingDataEndpoints(supporting_data_repo)
        if not supporting_data.validate_department_reference(department):
            raise ValidationError(f"Invalid department: {department}")
    
    # Continue with standard SCIM user creation
    user = User.from_dict(request_body)
    # ...
```

### Role Validation in Group Creation

```python
# In SCIM Group endpoint (optional enhancement)
def create_group(request_body):
    display_name = request_body.get("displayName")
    
    # Optional: Validate role name against supporting data
    supporting_data = SupportingDataEndpoints(supporting_data_repo)
    if not supporting_data.validate_role_reference(display_name):
        # Warning: Group name doesn't match any predefined role
        logger.warning(f"Group '{display_name}' doesn't match any role")
    
    # Continue with standard SCIM group creation
    group = Group.from_dict(request_body)
    # ...
```

**Note**: Validation is **optional** and does not modify SCIM behavior. It's a helper for stricter enforcement if desired.

---

## Authentication & Authorization

### Supporting Data APIs

**Required Scope**: `supportingdata.read`

```http
GET /api/supporting-data/roles
Authorization: Bearer <token-with-supportingdata.read>
```

**No Write Scopes**:
- `supportingdata.write` does NOT exist
- `supportingdata.create` does NOT exist
- `supportingdata.delete` does NOT exist

### SCIM APIs (Unchanged)

**Required Scopes**: `scim.read`, `scim.write`

```http
POST /scim/v2/Users
Authorization: Bearer <token-with-scim.write>
```

---

## Error Handling

### Supporting Data API Errors

**Format**: Simple JSON (not SCIM Error schema)

```json
{
  "error": {
    "status": 404,
    "message": "Role with id 'invalid-role' not found"
  }
}
```

### SCIM API Errors (Unchanged)

**Format**: SCIM Error schema

```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
  "status": "404",
  "detail": "User with id 'invalid-id' not found"
}
```

---

## Configuration

### Predefined Roles (Example)

```yaml
# config/roles.yaml
roles:
  - id: role-admin
    name: Administrator
    description: Full system access
  - id: role-developer
    name: Developer
    description: Development access
  - id: role-analyst
    name: Analyst
    description: Read-only analysis access
```

### Predefined Departments (Example)

```yaml
# config/departments.yaml
departments:
  - id: dept-eng
    name: Engineering
  - id: dept-product
    name: Product Management
  - id: dept-sales
    name: Sales
```

---

## Summary

### What Changed
✅ **Added**: Supporting data models (Role, Department)  
✅ **Added**: Supporting data repository (read-only)  
✅ **Added**: Supporting data API endpoints (GET only)  
✅ **Added**: Integration documentation  

### What Did NOT Change
❌ **SCIM User schema** - Unchanged  
❌ **SCIM Group schema** - Unchanged  
❌ **SCIM endpoints** - Unchanged  
❌ **SCIM PATCH logic** - Unchanged  
❌ **SCIM discovery endpoints** - Unchanged  
❌ **SCIM error handling** - Unchanged  

### Integration Points
1. **Roles** map to **SCIM Groups** by name
2. **Departments** map to **SCIM User.department** by name
3. Supporting data provides **lookup and validation**
4. SCIM provides **actual provisioning and lifecycle**

### Benefits
- ✅ Clean separation of concerns
- ✅ SCIM remains standards-compliant
- ✅ Supporting data is centrally managed
- ✅ No breaking changes to existing SCIM clients
- ✅ Easy to extend with additional supporting data types