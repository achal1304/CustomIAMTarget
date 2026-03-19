# Supporting Data API Test Suite

Comprehensive automated test suite for Supporting Data APIs (Roles and Departments).

## Overview

This test suite validates the **READ-ONLY** Supporting Data APIs without testing or modifying SCIM endpoints.

### Scope
✅ **Tests ONLY**:
- `/api/supporting-data/roles`
- `/api/supporting-data/departments`

❌ **Does NOT test**:
- SCIM `/Users` endpoints
- SCIM `/Groups` endpoints
- SCIM PATCH operations
- SCIM discovery endpoints

## Test Coverage

### 1. Happy Path Tests
- ✅ Endpoint availability (HTTP 200)
- ✅ Valid JSON responses
- ✅ Required response fields
- ✅ Expected data counts
- ✅ Single resource retrieval
- ✅ 404 for nonexistent resources

### 2. Pagination Tests
- ✅ Default pagination behavior
- ✅ Custom startIndex and count
- ✅ Count enforcement
- ✅ No duplicate entries across pages
- ✅ Boundary handling (startIndex > totalResults)
- ✅ Invalid parameter validation (400 errors)

### 3. Data Integrity Tests
- ✅ Required fields present (id, name)
- ✅ ID stability across calls
- ✅ ID uniqueness
- ✅ Data consistency (list vs single retrieval)
- ✅ Optional field handling (description for roles)

### 4. Read-Only Enforcement Tests
- ✅ POST returns 405/403
- ✅ PUT returns 405/403
- ✅ PATCH returns 405/403
- ✅ DELETE returns 405/403

### 5. Authorization & Security Tests
- ✅ No auth header returns 401
- ✅ Invalid token returns 401/403
- ✅ Valid read scope succeeds
- ✅ Write scope doesn't allow mutation

### 6. SCIM Isolation Tests
- ✅ No SCIM schemas field
- ✅ No SCIM meta field
- ✅ No SCIM members field
- ✅ Error responses not in SCIM format

### 7. Contract Stability Tests
- ✅ Response structure validation
- ✅ No unexpected fields
- ✅ Snapshot validation (predefined data)

## Test Statistics

- **Total Test Cases**: 100+ tests
- **Roles API Tests**: 50+ tests
- **Departments API Tests**: 50+ tests
- **Test Files**: 3 files
  - `test_roles_api.py` - Roles endpoint tests
  - `test_departments_api.py` - Departments endpoint tests
  - `conftest.py` - Shared fixtures and configuration

## Installation

### Prerequisites
- Python 3.8+
- pip

### Install Dependencies
```bash
cd tests
pip install -r requirements.txt
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest test_roles_api.py
pytest test_departments_api.py
```

### Run Specific Test Class
```bash
pytest test_roles_api.py::TestRolesAPI
```

### Run Specific Test
```bash
pytest test_roles_api.py::TestRolesAPI::test_list_roles_returns_200
```

### Run with Coverage
```bash
pytest --cov=. --cov-report=html
```

### Run in Parallel
```bash
pytest -n auto
```

### Run with Verbose Output
```bash
pytest -v
```

### Run Only Security Tests
```bash
pytest -m security
```

### Run Only Contract Tests
```bash
pytest -m contract
```

## Configuration

### Environment Variables

Set these environment variables to configure test execution:

```bash
# API Base URL (required)
export API_BASE_URL="https://api.example.com"

# Authentication Token (required for real API testing)
export SUPPORTING_DATA_READ_TOKEN="your-oauth-token-here"

# API Timeout (optional, default: 30 seconds)
export API_TIMEOUT="30"
```

### pytest.ini

Test configuration is in `pytest.ini`:
- Test discovery patterns
- Output options
- Coverage settings
- Markers
- Logging configuration

## Test Structure

```
tests/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── pytest.ini                   # Pytest configuration
├── conftest.py                  # Shared fixtures and utilities
├── test_roles_api.py           # Roles API tests
└── test_departments_api.py     # Departments API tests
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Supporting Data API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        cd tests
        pip install -r requirements.txt
    
    - name: Run tests
      env:
        API_BASE_URL: ${{ secrets.API_BASE_URL }}
        SUPPORTING_DATA_READ_TOKEN: ${{ secrets.SUPPORTING_DATA_READ_TOKEN }}
      run: |
        cd tests
        pytest --cov=. --cov-report=xml --cov-report=term
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./tests/coverage.xml
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any
    
    environment {
        API_BASE_URL = credentials('api-base-url')
        SUPPORTING_DATA_READ_TOKEN = credentials('supporting-data-token')
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r tests/requirements.txt'
            }
        }
        
        stage('Test') {
            steps {
                sh 'cd tests && pytest --junitxml=results.xml --cov=. --cov-report=xml'
            }
        }
        
        stage('Report') {
            steps {
                junit 'tests/results.xml'
                cobertura coberturaReportFile: 'tests/coverage.xml'
            }
        }
    }
}
```

### GitLab CI Example

```yaml
test:
  image: python:3.10
  
  variables:
    API_BASE_URL: $API_BASE_URL
    SUPPORTING_DATA_READ_TOKEN: $SUPPORTING_DATA_READ_TOKEN
  
  before_script:
    - cd tests
    - pip install -r requirements.txt
  
  script:
    - pytest --cov=. --cov-report=xml --cov-report=term
  
  coverage: '/TOTAL.*\s+(\d+%)$/'
  
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: tests/coverage.xml
```

## Test Execution Examples

### Local Development
```bash
# Set environment variables
export API_BASE_URL="http://localhost:8000"
export SUPPORTING_DATA_READ_TOKEN="dev-token"

# Run tests
cd tests
pytest -v
```

### Staging Environment
```bash
export API_BASE_URL="https://staging-api.example.com"
export SUPPORTING_DATA_READ_TOKEN="staging-token"

cd tests
pytest -v --html=report.html
```

### Production Smoke Tests
```bash
export API_BASE_URL="https://api.example.com"
export SUPPORTING_DATA_READ_TOKEN="prod-readonly-token"

cd tests
pytest -v -m "not slow" --maxfail=1
```

## Test Markers

Tests are organized with markers for selective execution:

- `@pytest.mark.integration` - All API integration tests
- `@pytest.mark.security` - Authentication and authorization tests
- `@pytest.mark.contract` - Contract validation and snapshot tests
- `@pytest.mark.slow` - Tests that take longer to execute

### Run Only Security Tests
```bash
pytest -m security
```

### Skip Slow Tests
```bash
pytest -m "not slow"
```

## Troubleshooting

### Common Issues

#### 1. Connection Errors
```
Error: Connection refused
```
**Solution**: Verify API_BASE_URL is correct and API is running

#### 2. Authentication Failures
```
Error: 401 Unauthorized
```
**Solution**: Verify SUPPORTING_DATA_READ_TOKEN is valid and has correct scope

#### 3. Import Errors
```
Error: ModuleNotFoundError: No module named 'pytest'
```
**Solution**: Install dependencies: `pip install -r requirements.txt`

#### 4. Timeout Errors
```
Error: Test timeout exceeded
```
**Solution**: Increase API_TIMEOUT environment variable

### Debug Mode

Run tests with debug output:
```bash
pytest -v -s --log-cli-level=DEBUG
```

## Test Maintenance

### Updating Expected Data

When predefined roles or departments change:

1. Update expected counts in `conftest.py`:
   ```python
   expected_role_count = 7  # Update this
   expected_department_count = 10  # Update this
   ```

2. Update snapshot tests in test files:
   ```python
   expected_role_names = {
       "Administrator",
       # Add/remove role names
   }
   ```

3. Run tests to verify:
   ```bash
   pytest -v
   ```

### Adding New Tests

1. Add test method to appropriate test class
2. Use descriptive test name: `test_<what>_<expected_behavior>`
3. Add docstring explaining what is validated
4. Use shared fixtures from `conftest.py`
5. Run new test: `pytest -v -k "test_name"`

## Best Practices

1. ✅ **Deterministic Tests**: Tests should produce same results every run
2. ✅ **Independent Tests**: Tests should not depend on each other
3. ✅ **Clear Assertions**: Use descriptive assertion messages
4. ✅ **Shared Fixtures**: Reuse fixtures from conftest.py
5. ✅ **Proper Cleanup**: No test data left behind (read-only APIs)
6. ✅ **Fast Execution**: Keep tests fast, mark slow tests
7. ✅ **Comprehensive Coverage**: Test happy paths and edge cases

## Reporting

### HTML Report
```bash
pytest --html=report.html --self-contained-html
```

### Coverage Report
```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### JUnit XML (for CI)
```bash
pytest --junitxml=results.xml
```

## Support

For issues or questions:
1. Check this README
2. Review test output and logs
3. Verify environment configuration
4. Check API availability and authentication

## Summary

This test suite provides comprehensive validation of Supporting Data APIs:
- ✅ 100+ automated tests
- ✅ Full coverage of all requirements
- ✅ CI/CD ready
- ✅ No manual testing required
- ✅ SCIM endpoints untouched
- ✅ Read-only enforcement validated