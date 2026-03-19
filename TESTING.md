# Testing Documentation

## Quick Start

Run all tests:
```bash
./tests/run_all_tests.sh
```

Or using pytest directly:
```bash
pytest tests/ -v --cov=. --cov-report=html
```

## Test Suites

### 1. SCIM Users API Tests
**File**: `tests/test_scim_users_api.py`  
**Coverage**: 20+ test cases covering all CRUD operations

```bash
pytest tests/test_scim_users_api.py -v
```

Tests include:
- User creation (minimal and full)
- User retrieval and listing
- User updates via PATCH
- User deletion
- Pagination and filtering
- Error handling (404, 409, 400)
- PUT not supported (501)

### 2. SCIM Groups API Tests
**File**: `tests/test_scim_groups_api.py`  
**Coverage**: 18+ test cases covering all group operations

```bash
pytest tests/test_scim_groups_api.py -v
```

Tests include:
- Group creation with/without members
- Group retrieval and listing
- Member management (add/remove)
- Group updates via PATCH
- Group deletion with membership cleanup
- Pagination and filtering
- Error handling
- PUT not supported (501)

### 3. SCIM Discovery API Tests
**File**: `tests/test_scim_discovery_api.py`  
**Coverage**: 12+ test cases for discovery endpoints

```bash
pytest tests/test_scim_discovery_api.py -v
```

Tests include:
- ServiceProviderConfig endpoint
- ResourceTypes endpoint (list and individual)
- Schemas endpoint (list and individual)
- Cross-endpoint consistency validation

### 4. Supporting Data API Tests
**File**: `tests/test_supporting_data_complete.py`  
**Coverage**: 25+ test cases for roles and departments

```bash
pytest tests/test_supporting_data_complete.py -v
```

Tests include:
- Roles API (list, get, pagination)
- Departments API (list, get, pagination)
- Read-only enforcement (405 for POST/PUT/DELETE)
- SCIM isolation validation
- Edge cases and error handling

## Test Statistics

- **Total Test Files**: 4 main test suites
- **Total Test Cases**: 75+ automated tests
- **Expected Coverage**: >80%
- **Execution Time**: ~5-10 seconds

## Installation

Install test dependencies:
```bash
pip install -r tests/requirements.txt
```

## Coverage Reports

After running tests with coverage, view the HTML report:
```bash
open tests/htmlcov/index.html
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines. Example GitHub Actions workflow:

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
```

## Test Architecture

All tests use:
- **Framework**: pytest with Flask test client
- **Fixtures**: Automatic repository cleanup between tests
- **Isolation**: Each test is independent
- **Coverage**: pytest-cov for code coverage analysis

## For More Details

See comprehensive documentation in `tests/TEST_GUIDE.md`

---

**Made with Bob**