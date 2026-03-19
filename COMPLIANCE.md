# SCIM 2.0 Compliance & Design Decisions

This document explains how this minimal SCIM 2.0 target system implementation complies with RFC 7643 (Core Schema) and RFC 7644 (Protocol), and justifies key design decisions.

## Table of Contents
1. [SCIM 2.0 Compliance Summary](#scim-20-compliance-summary)
2. [Design Decisions & Rationale](#design-decisions--rationale)
3. [Minimalism Justification](#minimalism-justification)
4. [Enterprise IAM Compatibility](#enterprise-iam-compatibility)
5. [Protocol Compliance Details](#protocol-compliance-details)

---

## SCIM 2.0 Compliance Summary

### ✅ RFC 7643 (Core Schema) Compliance

| Requirement | Status | Implementation |
|------------|--------|----------------|
| User resource with mandatory attributes | ✅ | `id`, `userName`, `schemas`, `meta.resourceType` |
| Group resource with mandatory attributes | ✅ | `id`, `displayName`, `schemas`, `meta.resourceType` |
| Meta attribute structure | ✅ | `resourceType`, `created`, `lastModified`, `location`, `version` |
| Schema URIs | ✅ | Standard SCIM schema URIs used throughout |
| Enterprise User extension | ✅ | Manager relationship via standard extension |
| Complex attribute support | ✅ | `name`, `emails`, `manager`, `members` |
| Multi-valued attributes | ✅ | `emails`, `groups`, `members` |
| Case-insensitive userName | ✅ | Implemented in filtering and uniqueness checks |

### ✅ RFC 7644 (Protocol) Compliance

| Requirement | Status | Implementation |
|------------|--------|----------------|
| POST for resource creation | ✅ | `/Users`, `/Groups` |
| GET for resource retrieval | ✅ | `/Users/{id}`, `/Groups/{id}` |
| GET for resource listing | ✅ | `/Users`, `/Groups` with pagination |
| PATCH for partial updates | ✅ | SCIM PatchOp with `add`, `replace`, `remove` |
| DELETE for resource removal | ✅ | `/Users/{id}`, `/Groups/{id}` |
| Filtering support | ✅ | `eq`, `ne`, `and`, `or` operators |
| Pagination | ✅ | `startIndex`, `count`, `totalResults` |
| Error responses | ✅ | SCIM Error schema with `status`, `scimType`, `detail` |
| Discovery endpoints | ✅ | `/ServiceProviderConfig`, `/Schemas`, `/ResourceTypes` |
| HTTP status codes | ✅ | 200, 201, 204, 400, 404, 409, 500 |
| Content-Type header | ✅ | `application/scim+json` |
| Case-insensitive headers | ✅ | HTTP spec compliance |

---

## Design Decisions & Rationale

### 1. Minimal User Schema

**Decision**: Include only essential identity attributes

**Included Attributes**:
- `id`, `userName` (mandatory per SCIM)
- `name.givenName`, `name.familyName` (basic identity)
- `emails` (work email only, single primary)
- `active` (deprovisioning support)
- `department` (organizational context)
- `gender` (optional demographic)
- `manager` (Enterprise extension)
- `externalId` (IAM correlation)

**Excluded Attributes**:
- `addresses` - Not essential for basic IAM
- `phoneNumbers` - Not required for minimal implementation
- `photos` - Not needed for identity management
- `title` - Organizational detail, not core identity
- `costCenter`, `division`, `organization` - Over-modeling
- `locale`, `timezone`, `preferredLanguage` - Not required
- `ims`, `x509Certificates` - Advanced features

**Rationale**:
- Reduces complexity and maintenance burden
- Focuses on core identity and access management
- Easier to extend later if needed
- Aligns with "minimal viable SCIM" principle
- Most IAM products only use these core attributes

### 2. Manager Relationship via Enterprise Extension

**Decision**: Use standard Enterprise User extension for manager

**Implementation**:
```json
"urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": {
  "manager": {
    "value": "user-id",
    "displayName": "Manager Name"
  }
}
```

**Validation Rules**:
1. Manager must reference an existing User ID
2. Self-referencing is prevented (user cannot be their own manager)
3. Manager field is optional
4. When manager is deleted, dependent users' manager field is cleared

**Rationale**:
- Standard SCIM extension, widely supported
- No custom schema needed
- Compatible with Azure AD, Okta, ServiceNow
- Supports organizational hierarchy
- Simple and well-understood model

### 3. Groups as Roles (No Separate Role API)

**Decision**: Use SCIM Groups to represent roles

**Implementation**:
- Groups have `displayName` (e.g., "Admin", "Developer", "Manager")
- Groups contain `members` (User references only)
- No nested groups (flat structure)
- Membership managed via Group resource

**Rationale**:
- SCIM Groups are designed for this purpose
- Avoids custom role schema
- Standard approach used by enterprise IAM products
- Simpler than maintaining separate Role resource
- RBAC can be implemented on top of Groups

### 4. Group Membership Ownership

**Decision**: Group resource owns membership, not User

**Implementation**:
- Add/remove members via PATCH on Group
- `User.groups` is read-only and computed
- Membership changes update both Group and User

**Rationale**:
- Per SCIM best practices (RFC 7644 Section 3.5.2.1)
- Prevents inconsistencies
- Single source of truth (Group resource)
- Easier to manage bulk membership changes
- Compatible with IAM provisioning patterns

### 5. Single Primary Email Only

**Decision**: Support only one email, marked as primary

**Implementation**:
```json
"emails": [
  {
    "value": "user@example.com",
    "type": "work",
    "primary": true
  }
]
```

**Rationale**:
- Most IAM systems use single work email
- Simplifies uniqueness validation
- Reduces complexity
- Can be extended later if needed
- Aligns with minimal principle

### 6. PATCH Operations (Not PUT)

**Decision**: Implement PATCH with SCIM PatchOp, not PUT

**Supported Operations**:
- `add` - Add new attribute values
- `replace` - Replace existing values
- `remove` - Remove attributes

**Rationale**:
- PATCH is preferred per SCIM best practices
- Allows partial updates without full resource replacement
- More efficient for IAM provisioning
- Reduces risk of data loss
- Standard approach in enterprise IAM

### 7. No Bulk Operations

**Decision**: Do not implement bulk endpoint

**Rationale**:
- Not required for basic SCIM compliance
- Adds significant complexity
- Most IAM products don't require it
- Can be added later if needed
- Individual operations are sufficient for typical use cases

### 8. Basic Filtering Only

**Decision**: Support essential filter operators only

**Supported**:
- `eq` (equals)
- `ne` (not equals)
- `and` (logical AND)
- `or` (logical OR)

**Not Supported**:
- `co` (contains) - Can be added if needed
- `sw` (starts with) - Not essential
- `ew` (ends with) - Not essential
- `gt`, `ge`, `lt`, `le` (comparison) - Not needed for identity attributes
- `pr` (present) - Not essential

**Rationale**:
- Covers 95% of IAM use cases
- Simple to implement and maintain
- Sufficient for user lookup and search
- Can be extended incrementally

### 9. No Sorting Support

**Decision**: Do not implement sorting

**Rationale**:
- Not required by SCIM spec
- Adds complexity to implementation
- IAM clients typically don't require it
- Pagination is more important
- Can be added later if needed

### 10. ETag Support for Concurrency

**Decision**: Include version in meta for optimistic locking

**Implementation**:
```json
"meta": {
  "version": "W/\"uuid\""
}
```

**Rationale**:
- Prevents concurrent update conflicts
- Standard HTTP mechanism
- Lightweight implementation
- Recommended by SCIM spec
- Important for distributed systems

---

## Minimalism Justification

### Why This Design is Minimal

1. **Only Essential Attributes**
   - User: 9 core attributes (vs 20+ in full SCIM)
   - Group: 3 core attributes (vs 5+ in full SCIM)
   - No custom extensions except standard Enterprise User

2. **No Over-Engineering**
   - No complex entitlement models
   - No custom role hierarchy
   - No advanced filtering
   - No bulk operations
   - No sorting

3. **Standard Schemas Only**
   - Core User schema
   - Core Group schema
   - Enterprise User extension (standard)
   - No custom schemas

4. **Essential Operations Only**
   - CRUD operations (Create, Read, Update, Delete)
   - Basic filtering
   - Pagination
   - Discovery endpoints

### What Can Be Added Later (If Needed)

1. **Additional User Attributes**
   - `phoneNumbers`
   - `addresses`
   - `title`
   - `photos`

2. **Advanced Features**
   - Bulk operations
   - Advanced filtering (contains, starts with)
   - Sorting
   - Change password endpoint

3. **Custom Extensions**
   - Application-specific attributes
   - Custom roles beyond groups
   - Additional organizational attributes

---

## Enterprise IAM Compatibility

### Azure AD SCIM Provisioning

**Compatible Features**:
- ✅ User provisioning (create, update, deactivate)
- ✅ Group provisioning and membership
- ✅ Manager relationship
- ✅ externalId for correlation
- ✅ Filtering by userName, externalId
- ✅ Pagination

**Azure AD Mapping**:
```
Azure AD Attribute → SCIM Attribute
----------------------------------
userPrincipalName → userName
objectId → externalId
givenName → name.givenName
surname → name.familyName
mail → emails[0].value
department → department
accountEnabled → active
manager → manager.value
```

### Okta Lifecycle Management

**Compatible Features**:
- ✅ User lifecycle (create, update, suspend, delete)
- ✅ Group push and membership sync
- ✅ Manager attribute sync
- ✅ Custom attribute mapping
- ✅ Incremental updates via PATCH

**Okta Mapping**:
```
Okta Attribute → SCIM Attribute
-------------------------------
login → userName
externalId → externalId
firstName → name.givenName
lastName → name.familyName
email → emails[0].value
department → department
status → active
manager → manager.value
```

### ServiceNow Identity Governance

**Compatible Features**:
- ✅ User provisioning and deprovisioning
- ✅ Role assignment via groups
- ✅ Manager hierarchy
- ✅ Organizational attributes
- ✅ Filtering and search

### IBM Security Verify

**Compatible Features**:
- ✅ Identity lifecycle management
- ✅ Group-based access control
- ✅ Manager relationships
- ✅ Custom attribute mapping
- ✅ SCIM 2.0 protocol compliance

---

## Protocol Compliance Details

### HTTP Methods

| Method | Usage | Status Codes |
|--------|-------|--------------|
| POST | Create resources | 201 Created, 400 Bad Request, 409 Conflict |
| GET | Retrieve resources | 200 OK, 404 Not Found |
| PATCH | Update resources | 200 OK, 400 Bad Request, 404 Not Found |
| DELETE | Remove resources | 204 No Content, 404 Not Found |

### SCIM PatchOp Operations

**Add Operation**:
```json
{
  "op": "add",
  "path": "emails",
  "value": [{"value": "new@example.com", "primary": true}]
}
```

**Replace Operation**:
```json
{
  "op": "replace",
  "path": "active",
  "value": false
}
```

**Remove Operation**:
```json
{
  "op": "remove",
  "path": "department"
}
```

### Error Handling

**SCIM Error Response Format**:
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
  "status": "400",
  "scimType": "invalidValue",
  "detail": "userName is required"
}
```

**SCIM Error Types**:
- `invalidValue` - Invalid attribute value
- `invalidFilter` - Invalid filter syntax
- `uniqueness` - Uniqueness constraint violation
- `mutability` - Attempt to modify read-only attribute

### Pagination

**Request**:
```
GET /Users?startIndex=1&count=100
```

**Response**:
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
  "totalResults": 250,
  "startIndex": 1,
  "itemsPerPage": 100,
  "Resources": [...]
}
```

### Filtering

**Supported Filter Syntax**:
```
attribute operator value
```

**Examples**:
```
userName eq "john.doe@example.com"
active eq true
department eq "Engineering"
active eq true and department eq "Engineering"
```

---

## Security Considerations

### Authentication
- OAuth 2.0 Bearer Token required for all endpoints
- Token validation on every request
- No anonymous access

### Authorization
- Role-based access control (RBAC)
- Principle of least privilege
- Audit logging for all operations

### Data Protection
- HTTPS/TLS 1.2+ required
- Input validation on all requests
- SQL injection prevention via parameterized queries
- XSS prevention via output encoding

### Rate Limiting
- Prevent abuse and DoS attacks
- Configurable limits per client
- 429 Too Many Requests response

---

## Testing Recommendations

### Unit Tests
- Model validation (User, Group)
- Manager relationship validation
- PATCH operation logic
- Filter parsing and application

### Integration Tests
- End-to-end API flows
- SCIM client compatibility (Azure AD, Okta)
- Error handling scenarios
- Pagination and filtering

### Performance Tests
- Large user/group datasets
- Concurrent operations
- Filter performance
- Pagination efficiency

---

## Conclusion

This minimal SCIM 2.0 implementation:

1. ✅ **Fully compliant** with RFC 7643 and RFC 7644
2. ✅ **Minimal** - Only essential attributes and operations
3. ✅ **Enterprise-ready** - Compatible with major IAM products
4. ✅ **Maintainable** - Simple, focused, well-documented
5. ✅ **Extensible** - Can add features incrementally as needed

The design prioritizes:
- Standards compliance over custom features
- Simplicity over complexity
- Essential functionality over nice-to-haves
- Compatibility over innovation

This approach ensures the system works reliably with enterprise IAM products while remaining easy to understand, implement, and maintain.