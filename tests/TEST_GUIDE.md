# SCIM 2.0 Service Provider - Test Guide

## Overview

Comprehensive automated test suite for the SCIM 2.0 Service Provider implementation, covering all endpoints including Users, Groups, Discovery, and Supporting Data APIs.

## Test Structure

```
tests/
├── conftest.py                          # Shared fixtures and configuration
├── pytest.ini                           # Pytest configuration
├── requirements.txt                     # Test dependencies
├── run_all_tests.sh                     # Test runner script
├── TEST_GUIDE.md                        # This file
├── test_scim_users_api.py              # SCIM Users endpoint tests
├── test_scim_groups_api.py             # SCIM Groups endpoint tests
├── test_scim_discovery_api.py          # SCIM Discovery endpoint tests
├── test_supporting_data_complete.py    # Supporting Data API tests
├── test_departments_api.py             # Legacy department tests
└── test_roles_api.py                   # Legacy role tests
```

## Test Coverage

### 1. SCIM Users API (`test_scim_users_api.py`)
- **Create User** (POST /scim/v2/Users)
  - Minimal required fields
  - Full user with all attributes
  - Enterprise extension support
  - Duplicate username validation
  - Schema validation
  
- **Get User** (GET /scim/v2/Users/{id})
  - Retrieve existing user
  - Handle non-existent user (404)
  
- **List Users** (GET /scim/v2/Users)
  - Empty list
  - Pagination (startIndex, count)
  - Filtering (active, userName, etc.)
  - SCIM ListResponse format
  
- **Update User** (PATCH /scim/v2/Users/{id})
  - Replace operations (active, name, etc.)
  - Add operations
  - Remove operations
  - PatchOp schema validation
  
- **Delete User** (DELETE /scim/v2/Users/{id})
  - Successful deletion (204)
  - Non-existent user (404)
  
- **PUT Not Supported** (PUT /scim/v2/Users/{id})
  - Returns 501 Not Implemented

**Total: 20+ test cases**

### 2. SCIM Groups API (`test_scim_groups_api.py`)
- **Create Group** (POST /scim/v2/Groups)
  - Minimal required fields
  - Group with members
  - Duplicate displayName validation
  - Schema validation
  
- **Get Group** (GET /scim/v2/Groups/{id})
  - Retrieve existing group
  - Handle non-existent group (404)
  
- **List Groups** (GET /scim/v2/Groups)
  - Empty list
  - Pagination
  - Filtering by displayName
  - SCIM ListResponse format
  
- **Update Group** (PATCH /scim/v2/Groups/{id})
  - Add members
  - Remove members
  - Replace displayName
  - Member path filtering
  
- **Delete Group** (DELETE /scim/v2/Groups/{id})
  - Successful deletion
  - User membership cleanup
  - Non-existent group (404)
  
- **PUT Not Supported** (PUT /scim/v2/Groups/{id})
  - Returns 501 Not Implemented

**Total: 18+ test cases**

### 3. SCIM Discovery API (`test_scim_discovery_api.py`)
- **Service Provider Config** (GET /scim/v2/ServiceProviderConfig)
  - Configuration structure
  - Feature support flags
  - Authentication schemes
  
- **Resource Types** (GET /scim/v2/ResourceTypes)
  - List all resource types
  - Get User resource type
  - Get Group resource type
  - Schema references
  
- **Schemas** (GET /scim/v2/Schemas)
  - List all schemas
  - Get User schema
  - Get Group schema
  - Get Enterprise User extension
  - Schema attributes validation
  - Non-existent schema (404)
  
- **Integration Tests**
  - Cross-endpoint consistency
  - All endpoints accessible

**Total: 12+ test cases**

### 4. Supporting Data API (`test_supporting_data_complete.py`)
- **Roles API** (/api/supporting-data/roles)
  - List all roles (7 predefined)
  - Pagination support
  - Get role by ID
  - Non-existent role (404)
  - Read-only enforcement (POST/PUT/DELETE return 405)
  - No SCIM fields in response
  
- **Departments API** (/api/supporting-data/departments)
  - List all departments (10 predefined)
  - Pagination support
  - Get department by ID
  - Non-existent department (404)
  - Read-only enforcement (POST/PUT/DELETE return 405)
  - No SCIM fields in response
  
- **Isolation Tests**
  - Supporting data not in SCIM endpoints
  - SCIM fields not in supporting data
  
- **Edge Cases**
  - Invalid pagination parameters
  - Large pagination counts
  - Pagination beyond results
  - Content-Type validation

**Total: 25+ test cases**

## Running Tests

### Run All Tests
```bash
# From project root
./tests/run_all_tests.sh

# Or using pytest directly
pytest tests/ -v
```

### Run Specific Test Suite
```bash
# Users API tests
pytest tests/test_scim_users_api.py -v

# Groups API tests
pytest tests/test_scim_groups_api.py -v

# Discovery API tests
pytest tests/test_scim_discovery_api.py -v

# Supporting Data tests
pytest tests/test_supporting_data_complete.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_scim_users_api.py::TestUsersCreate -v
pytest tests/test_scim_groups_api.py::TestGroupsPatch -v
```

### Run Specific Test
```bash
pytest tests/test_scim_users_api.py::TestUsersCreate::test_create_user_minimal -v
```

### Run with Coverage
```bash
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing
```

### Run Tests by Marker
```bash
# Run integration tests
pytest -m integration -v

# Run security tests
pytest -m security -v

# Run contract tests
pytest -m contract -v
```

## Test Configuration

### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --tb=short
    --disable-warnings
markers =
    integration: Integration tests
    security: Security-related tests
    contract: Contract validation tests
```

### conftest.py
Provides shared fixtures:
- `client`: Flask test client
- `reset_repos`: Auto-reset repositories between tests
- `sample_user`: Pre-created user for group tests
- Utility functions for assertions

## Test Dependencies

Install test dependencies:
```bash
pip install -r tests/requirements.txt
```

Required packages:
- pytest
- pytest-cov
- Flask (for test client)

## Coverage Reports

After running tests with coverage:
- **HTML Report**: `tests/htmlcov/index.html`
- **JSON Report**: `tests/coverage.json`
- **Terminal**: Displayed after test run

View HTML coverage:
```bash
open tests/htmlcov/index.html  # macOS
xdg-open tests/htmlcov/index.html  # Linux
start tests/htmlcov/index.html  # Windows
```

## Test Best Practices

### 1. Test Isolation
- Each test is independent
- Repositories are reset before each test
- No shared state between tests

### 2. Fixtures
- Use fixtures for common setup
- `autouse=True` for automatic cleanup
- Scope appropriately (function, class, module, session)

### 3. Assertions
- Use descriptive assertion messages
- Test both success and failure cases
- Verify response structure and content

### 4. Test Organization
- Group related tests in classes
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)

### 5. Error Testing
- Test error responses (400, 404, 409, 501)
- Verify error message format
- Check SCIM error schema compliance

## Continuous Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install -r tests/requirements.txt
      - run: pytest tests/ --cov=. --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Troubleshooting

### Import Errors
```bash
# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Flask App Not Found
Ensure `app.py` is in the project root and properly imports all modules.

### Repository State Issues
The `reset_repos` fixture should handle cleanup. If issues persist, check fixture scope.

### Coverage Not Working
```bash
# Install coverage
pip install pytest-cov

# Run with explicit coverage
pytest --cov=app --cov=api --cov=models tests/
```

## Test Statistics

- **Total Test Files**: 5
- **Total Test Cases**: 75+
- **Coverage Target**: >80%
- **Test Execution Time**: ~5-10 seconds

## Future Enhancements

1. **Performance Tests**: Load testing for pagination and filtering
2. **Security Tests**: Authentication and authorization testing
3. **Contract Tests**: API contract validation with Pact
4. **E2E Tests**: Full workflow testing
5. **Mutation Tests**: Code quality validation with mutpy

## Contributing

When adding new features:
1. Write tests first (TDD)
2. Ensure all tests pass
3. Maintain >80% coverage
4. Update this guide

## Support

For issues or questions:
- Check test output for detailed error messages
- Review test code for examples
- Consult SCIM 2.0 RFC 7644 for protocol details

---

**Made with Bob**