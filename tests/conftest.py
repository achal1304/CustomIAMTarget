"""
Pytest Configuration and Shared Fixtures
For Supporting Data API Tests

This file contains shared configuration, fixtures, and utilities
used across all test modules.
"""

import pytest
import os
from typing import Dict


# ==================== CONFIGURATION ====================

def pytest_configure(config):
    """
    Pytest configuration hook
    Register custom markers
    """
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security-related"
    )
    config.addinivalue_line(
        "markers", "contract: mark test as contract validation"
    )


# ==================== ENVIRONMENT CONFIGURATION ====================

@pytest.fixture(scope="session")
def base_url():
    """
    Base URL for the API
    Can be overridden via environment variable
    """
    return os.getenv("API_BASE_URL", "https://example.com")


@pytest.fixture(scope="session")
def api_timeout():
    """
    Default timeout for API requests in seconds
    """
    return int(os.getenv("API_TIMEOUT", "30"))


# ==================== AUTHENTICATION FIXTURES ====================

@pytest.fixture(scope="session")
def valid_token():
    """
    Valid OAuth token with supportingdata.read scope
    
    In production, this would:
    - Fetch token from OAuth provider
    - Use service account credentials
    - Cache token for session duration
    """
    token = os.getenv("SUPPORTING_DATA_READ_TOKEN")
    if not token:
        # For testing, use a placeholder
        # In CI, this should be a real token
        token = "valid-token-with-supportingdata-read"
    return token


@pytest.fixture(scope="session")
def invalid_token():
    """
    Invalid OAuth token for negative testing
    """
    return "invalid-token-12345"


@pytest.fixture(scope="session")
def expired_token():
    """
    Expired OAuth token for testing token expiration
    """
    return "expired-token-67890"


# ==================== HTTP HEADERS FIXTURES ====================

@pytest.fixture
def headers_with_auth(valid_token):
    """
    Standard HTTP headers with valid authentication
    """
    return {
        "Authorization": f"Bearer {valid_token}",
        "Accept": "application/json",
        "User-Agent": "SupportingDataAPITests/1.0"
    }


@pytest.fixture
def headers_without_auth():
    """
    HTTP headers without authentication
    """
    return {
        "Accept": "application/json",
        "User-Agent": "SupportingDataAPITests/1.0"
    }


@pytest.fixture
def headers_with_invalid_auth(invalid_token):
    """
    HTTP headers with invalid authentication
    """
    return {
        "Authorization": f"Bearer {invalid_token}",
        "Accept": "application/json",
        "User-Agent": "SupportingDataAPITests/1.0"
    }


# ==================== ENDPOINT FIXTURES ====================

@pytest.fixture(scope="session")
def roles_endpoint(base_url):
    """Roles API endpoint"""
    return f"{base_url}/api/supporting-data/roles"


@pytest.fixture(scope="session")
def departments_endpoint(base_url):
    """Departments API endpoint"""
    return f"{base_url}/api/supporting-data/departments"


# ==================== TEST DATA FIXTURES ====================

@pytest.fixture(scope="session")
def expected_role_count():
    """Expected number of predefined roles"""
    return 7


@pytest.fixture(scope="session")
def expected_department_count():
    """Expected number of predefined departments"""
    return 10


@pytest.fixture(scope="session")
def expected_role_names():
    """Expected predefined role names"""
    return {
        "Administrator",
        "Developer",
        "Analyst",
        "Manager",
        "Auditor",
        "Support",
        "Read-Only User"
    }


@pytest.fixture(scope="session")
def expected_department_names():
    """Expected predefined department names"""
    return {
        "Engineering",
        "Product Management",
        "Sales",
        "Marketing",
        "Human Resources",
        "Finance",
        "Legal",
        "Operations",
        "Customer Support",
        "Executive"
    }


# ==================== UTILITY FUNCTIONS ====================

def assert_valid_json_response(response):
    """
    Assert that response is valid JSON with correct content type
    
    Args:
        response: requests.Response object
    """
    assert response.headers.get("Content-Type") == "application/json", \
        f"Expected application/json, got {response.headers.get('Content-Type')}"
    
    # Should not raise JSONDecodeError
    data = response.json()
    assert isinstance(data, dict), "Response must be a JSON object"
    return data


def assert_pagination_fields(data, expected_start_index=None, expected_count=None):
    """
    Assert that response contains valid pagination fields
    
    Args:
        data: Response JSON data
        expected_start_index: Expected startIndex value (optional)
        expected_count: Expected itemsPerPage value (optional)
    """
    required_fields = ["totalResults", "startIndex", "itemsPerPage"]
    for field in required_fields:
        assert field in data, f"Missing required pagination field: {field}"
    
    assert isinstance(data["totalResults"], int), "totalResults must be integer"
    assert isinstance(data["startIndex"], int), "startIndex must be integer"
    assert isinstance(data["itemsPerPage"], int), "itemsPerPage must be integer"
    
    assert data["totalResults"] >= 0, "totalResults must be non-negative"
    assert data["startIndex"] >= 1, "startIndex must be >= 1"
    assert data["itemsPerPage"] >= 0, "itemsPerPage must be non-negative"
    
    if expected_start_index is not None:
        assert data["startIndex"] == expected_start_index, \
            f"Expected startIndex {expected_start_index}, got {data['startIndex']}"
    
    if expected_count is not None:
        assert data["itemsPerPage"] == expected_count, \
            f"Expected itemsPerPage {expected_count}, got {data['itemsPerPage']}"


def assert_no_scim_fields(data):
    """
    Assert that response does not contain SCIM-specific fields
    
    Args:
        data: Response JSON data or individual resource object
    """
    scim_fields = ["schemas", "meta", "members", "externalId"]
    for field in scim_fields:
        assert field not in data, \
            f"Supporting data must not include SCIM field: {field}"


def assert_error_response(response, expected_status):
    """
    Assert that error response has correct format
    
    Args:
        response: requests.Response object
        expected_status: Expected HTTP status code
    """
    assert response.status_code == expected_status, \
        f"Expected status {expected_status}, got {response.status_code}"
    
    data = response.json()
    
    # Should have error field
    assert "error" in data, "Error response must have 'error' field"
    
    # Should NOT be SCIM error format
    assert "schemas" not in data, "Error must not use SCIM Error schema"
    assert "scimType" not in data, "Error must not include scimType"


# ==================== PYTEST HOOKS ====================

def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers based on test names
    """
    for item in items:
        # Add integration marker to all tests
        if "test_" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add security marker to auth/security tests
        if any(keyword in item.name for keyword in ["auth", "token", "401", "403", "security"]):
            item.add_marker(pytest.mark.security)
        
        # Add contract marker to contract validation tests
        if any(keyword in item.name for keyword in ["contract", "structure", "snapshot"]):
            item.add_marker(pytest.mark.contract)


def pytest_report_header(config):
    """
    Add custom header to pytest report
    """
    return [
        "Supporting Data API Test Suite",
        f"Base URL: {os.getenv('API_BASE_URL', 'https://example.com')}",
        "Target: READ-ONLY Supporting Data APIs (Roles, Departments)"
    ]

# Made with Bob
