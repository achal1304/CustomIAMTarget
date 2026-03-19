# Implementation Notes

## File Structure

The project uses proper Python package structure with `__init__.py` files in each directory to enable proper imports.

### Directory Structure
```
CustomTarget/
├── ARCHITECTURE.md                      # System architecture
├── COMPLIANCE.md                        # SCIM 2.0 compliance details
├── README.md                            # Project overview
├── IMPLEMENTATION_NOTES.md              # This file
├── api/
│   ├── __init__.py
│   ├── user-endpoints.py
│   ├── group-endpoints.py
│   └── discovery-endpoints.py
├── models/
│   ├── __init__.py
│   ├── user_model.py                    # Note: underscore (not hyphen)
│   └── group_model.py                   # Note: underscore (not hyphen)
├── schemas/
│   ├── __init__.py
│   ├── user-schema.json
│   ├── enterprise-user-extension.json
│   └── group-schema.json
└── examples/
    ├── __init__.py
    └── request-response-examples.md
```

## Important Notes

### Python Module Naming
- **Model files** use underscores: `user_model.py`, `group_model.py`
- This is required for Python imports to work correctly
- Python doesn't allow hyphens in module names

### Import Statements
The endpoint files import from models using:
```python
from models.user_model import User, ValidationError
from models.group_model import Group, ValidationError
```

### Type Checker Warnings
You may see warnings like "ValidationError is possibly unbound" in the endpoint files. These are false positives from the type checker because:
1. ValidationError is imported inside a try block
2. It's used in the except block
3. This is a valid Python pattern for conditional imports

These warnings can be safely ignored or suppressed with type checker configuration.

## Running the Code

### Prerequisites
```bash
# Python 3.8+
pip install typing-extensions  # if needed for older Python versions
```

### Usage Example
```python
# Import models
from models.user_model import User, Name, Email
from models.group_model import Group

# Import endpoints
from api.user_endpoints import UserEndpoints
from api.group_endpoints import GroupEndpoints
from api.discovery_endpoints import DiscoveryEndpoints

# Create instances (requires repository implementations)
user_endpoints = UserEndpoints(user_repo, group_repo)
group_endpoints = GroupEndpoints(group_repo, user_repo)
discovery_endpoints = DiscoveryEndpoints(base_url="https://example.com/scim/v2")
```

## Repository Pattern

The endpoint implementations expect repository objects with these methods:

### UserRepository Interface
```python
class UserRepository:
    def save(self, user: User) -> None: ...
    def get_by_id(self, user_id: str) -> Optional[User]: ...
    def get_by_username(self, username: str) -> Optional[User]: ...
    def get_by_external_id(self, external_id: str) -> Optional[User]: ...
    def get_all(self) -> List[User]: ...
    def delete(self, user_id: str) -> None: ...
```

### GroupRepository Interface
```python
class GroupRepository:
    def save(self, group: Group) -> None: ...
    def get_by_id(self, group_id: str) -> Optional[Group]: ...
    def get_by_display_name(self, display_name: str) -> Optional[Group]: ...
    def get_by_external_id(self, external_id: str) -> Optional[Group]: ...
    def get_all(self) -> List[Group]: ...
    def delete(self, group_id: str) -> None: ...
```

## Next Steps for Production

1. **Implement Repository Layer**
   - Create concrete implementations for UserRepository and GroupRepository
   - Use PostgreSQL, MongoDB, or MySQL as backend
   - Implement proper transaction handling

2. **Add Web Framework**
   - Use FastAPI, Flask, or Django REST Framework
   - Wire up the endpoint classes to HTTP routes
   - Add request/response serialization

3. **Implement Authentication**
   - OAuth 2.0 Bearer Token validation
   - JWT token verification
   - API key authentication (for testing)

4. **Add Middleware**
   - Request logging
   - Error handling
   - Rate limiting
   - CORS configuration

5. **Testing**
   - Unit tests for models
   - Integration tests for endpoints
   - SCIM client compatibility tests

6. **Deployment**
   - Containerize with Docker
   - Set up CI/CD pipeline
   - Configure monitoring and logging
   - Set up database migrations

## Example Web Framework Integration (FastAPI)

```python
from fastapi import FastAPI, HTTPException, Header
from typing import Optional

app = FastAPI()

# Initialize repositories (implement these)
user_repo = PostgreSQLUserRepository()
group_repo = PostgreSQLGroupRepository()

# Initialize endpoints
user_endpoints = UserEndpoints(user_repo, group_repo)
group_endpoints = GroupEndpoints(group_repo, user_repo)
discovery = DiscoveryEndpoints(base_url="https://api.example.com/scim/v2")

@app.post("/Users", status_code=201)
async def create_user(body: dict, authorization: Optional[str] = Header(None)):
    # Validate token
    if not validate_token(authorization):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        response, status = user_endpoints.create_user(body, "https://api.example.com")
        return response
    except SCIMError as e:
        raise HTTPException(status_code=e.status, detail=e.to_dict())

@app.get("/Users/{user_id}")
async def get_user(user_id: str, authorization: Optional[str] = Header(None)):
    if not validate_token(authorization):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        response, status = user_endpoints.get_user(user_id)
        return response
    except SCIMError as e:
        raise HTTPException(status_code=e.status, detail=e.to_dict())

# Add more routes...
```

## Database Schema Example (PostgreSQL)

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_name VARCHAR(255) UNIQUE NOT NULL,
    external_id VARCHAR(255) UNIQUE,
    given_name VARCHAR(255),
    family_name VARCHAR(255),
    email VARCHAR(255),
    active BOOLEAN DEFAULT true,
    department VARCHAR(255),
    gender VARCHAR(50),
    manager_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    version UUID DEFAULT gen_random_uuid()
);

-- Groups table
CREATE TABLE groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    display_name VARCHAR(255) NOT NULL,
    external_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    version UUID DEFAULT gen_random_uuid()
);

-- Group memberships table
CREATE TABLE group_members (
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY (group_id, user_id)
);

-- Indexes for performance
CREATE INDEX idx_users_username ON users(user_name);
CREATE INDEX idx_users_external_id ON users(external_id);
CREATE INDEX idx_users_active ON users(active);
CREATE INDEX idx_users_department ON users(department);
CREATE INDEX idx_groups_display_name ON groups(display_name);
CREATE INDEX idx_groups_external_id ON groups(external_id);
```

## Security Checklist

- [ ] Implement OAuth 2.0 Bearer Token authentication
- [ ] Use HTTPS/TLS 1.2+ only
- [ ] Validate all input data
- [ ] Use parameterized queries (prevent SQL injection)
- [ ] Implement rate limiting
- [ ] Add audit logging for all operations
- [ ] Sanitize error messages (don't leak sensitive info)
- [ ] Implement RBAC for admin operations
- [ ] Set up security headers (HSTS, CSP, etc.)
- [ ] Regular security audits and updates

## Performance Considerations

1. **Database Indexes**: Index userName, externalId, active, department
2. **Pagination**: Always use pagination for list operations
3. **Caching**: Consider caching for discovery endpoints
4. **Connection Pooling**: Use database connection pooling
5. **Async Operations**: Use async/await for I/O operations
6. **Query Optimization**: Optimize filter queries with proper indexes

## Monitoring & Observability

1. **Metrics to Track**:
   - Request rate and latency
   - Error rates by endpoint
   - Database query performance
   - Authentication failures
   - Resource creation/deletion rates

2. **Logging**:
   - All SCIM operations (create, update, delete)
   - Authentication attempts
   - Error details
   - Performance metrics

3. **Alerting**:
   - High error rates
   - Slow response times
   - Authentication failures
   - Database connection issues

## Compliance & Auditing

- Log all user and group modifications
- Track who made changes (via bearer token)
- Retain audit logs per compliance requirements
- Implement data retention policies
- Support GDPR/privacy requirements

## Support & Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `__init__.py` files exist in all directories
2. **Manager Validation**: Check that manager user exists before assignment
3. **Uniqueness Violations**: userName and externalId must be unique
4. **Filter Syntax**: Use proper SCIM filter syntax (e.g., `eq`, not `==`)
5. **Pagination**: startIndex is 1-based, not 0-based

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License & Attribution

This is a reference implementation for educational and integration purposes.
Based on SCIM 2.0 specifications (RFC 7643 and RFC 7644).