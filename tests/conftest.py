"""
Pytest Configuration and Shared Fixtures
For Supporting Data API Tests

This file contains shared configuration, fixtures, and utilities
used across all test modules.
"""

import os
import sys

# Hardcoded test JWT public key (matches the tokens below)
# This key is for TESTING ONLY - expires in 10 years
TEST_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxtbvLqWCvinUeJvj3U17
jONV2SWDDb/bepaAkPuRFOUjGZKug4x48AVOI5PY1EofKnOUQd/nV6IcuXMkF8v+
kso8sastv1JuEz191aWp7GAXxsEKAfwx6CDbiSwwJ7vlh3iAerXIqaqpIoz3T8Db
JFoS2rTrJbh2kI2RacMcllNIEDloBS4ksprRrl2dDEKIotoLx3ETsVDhYHKBi0Cw
o/xuZN443pQvh53xKnGtFD/GRO8rLC8XR7b8P7dYZ+3WnrrFEgeQXxdWfk1Ofj6y
t9iWY3ChbayaqQr0408sy2NUV1Eh7WVRzHuAdVx+KMVHBxTJJWXAmcLWtsTQ4sPV
xwIDAQAB
-----END PUBLIC KEY-----"""

# Hardcoded test JWT tokens (valid for 10 years from generation)
# These tokens are for TESTING ONLY
TEST_TOKENS = {
    'full_access': 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3Rlc3QtaWRwLmV4YW1wbGUuY29tIiwiYXVkIjoic2NpbS1zZXJ2aWNlLXByb3ZpZGVyIiwic3ViIjoidGVzdC11c2VyIiwic2NvcGUiOiJzY2ltLnJlYWQgc2NpbS53cml0ZSBzdXBwb3J0aW5nZGF0YS5yZWFkIiwiZXhwIjoxNzc0MDAzODIzLCJpYXQiOjE3NzM5MTc0MjMsIm5iZiI6MTc3MzkxNzQyMywianRpIjoidGVzdC10b2tlbi0xNzczODk3NjIzIn0.t15b_iP3Hnqe7ycYU_-3xnYyOlYQ0hx-lE-pJJKZB352B4uKcKBlxk5sW33ORA7VrG2RjzS1KEKbK-4GvpRHPcwmd9VMDXKIk5aAu7tji8dxN_d0Z0akvUwdsDho6pCKyp4IIkQnoUwGk4WJqqGrD95EIjKlhMyG5WQ-W7bJoNQtzIzld60JlWRzrTCZd2mtZ5zdEiYy8xMCDgPAgci1AHrrKFPnYr81kYQQdvQ_PCTcxmpbIf4rQyWrUgvCciqThCrRHbnxqTT8rTrP6RlknBqvDZnVv-vDZQH2EYA2Oz569eehuvY1cCSo6BxmtSe6H2xevl3Sgb-kQXXPjCA-Jw',
    'read_only': 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3Rlc3QtaWRwLmV4YW1wbGUuY29tIiwiYXVkIjoic2NpbS1zZXJ2aWNlLXByb3ZpZGVyIiwic3ViIjoidGVzdC11c2VyIiwic2NvcGUiOiJzY2ltLnJlYWQiLCJleHAiOjE3NzQwMDM4MjMsImlhdCI6MTc3MzkxNzQyMywibmJmIjoxNzczOTE3NDIzLCJqdGkiOiJ0ZXN0LXRva2VuLTE3NzM4OTc2MjMifQ.Tb7TFf0bO-DhmubRG0F-JlC8-nzCtq-Dl0iQdGGEFi3WKwXVCyXYwMivl3XM3Cb97YKn_IPdZG5iiwkX5qSyIUhrse7f3hRU0fwYR2KrrE1eaB7M720yVRB-PdQdbxw-M8vXKgCd1DwFQhjasKPCTWpl2KRvMyj9NfxZ-NR0KmLwAs68V9_2VpX26jl68PskHbCrNb_p1uvVPqY73CDRdbTO2T4Ux6kcuogeGonElJtlanDZ9ct8D1q-PN8kiAIBq9OS7rzHXinE8mZlFND9nQiSVTUsrgIBiqCjMEkV-Yc5L4jv-XQGAW_LKJL6CsLI0RapEBGwVBUgnBfS67y9cA',
    'supporting_data': 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3Rlc3QtaWRwLmV4YW1wbGUuY29tIiwiYXVkIjoic2NpbS1zZXJ2aWNlLXByb3ZpZGVyIiwic3ViIjoidGVzdC11c2VyIiwic2NvcGUiOiJzdXBwb3J0aW5nZGF0YS5yZWFkIiwiZXhwIjoxNzc0MDAzODIzLCJpYXQiOjE3NzM5MTc0MjMsIm5iZiI6MTc3MzkxNzQyMywianRpIjoidGVzdC10b2tlbi0xNzczODk3NjIzIn0.umy5j0qeFKwQTvfQfFujFohRd1ok-HbtdRdx0u2DJ7cghEtjW_aK7GogqnkJPU4-JfL_FU2-KpiLKhvbqYJQe4wXj8F0yp3AfoTzd0xyj_a14kFVfMAoC_pXCBhwbGkNtR7CvjfjWwbpBgdE77DN0Z8rBAfZx_DTl08AwPbPC7_44vgMiHkw-K1NzH4qrpPhFuXSHPOC7JdVxhevZ6IXW7k4NoOFGCTS3cat48fgOWjkMAB4rhAihznHqkV-dCvQiwEFaGrzNXA45_h_u8bFdA8TyvxnqjxBnq5n9QQlaxOBnuioZzz1hSu-HLrs2DUDXbtuMet_tKRhlLF_IRpd4g'
}

# CRITICAL: Set up authentication environment variables BEFORE any imports
# This must happen before app.py is imported to prevent load_dotenv() from overriding
os.environ['AUTH_OAUTH_ENABLED'] = 'true'
os.environ['AUTH_JWT_ENABLED'] = 'true'
os.environ['AUTH_JWT_ISSUER'] = 'https://test-idp.example.com'
os.environ['AUTH_JWT_AUDIENCE'] = 'scim-service-provider'
os.environ['AUTH_JWT_ALGORITHM'] = 'RS256'
os.environ['AUTH_JWT_PUBLIC_KEY'] = TEST_PUBLIC_KEY
os.environ['AUTH_BASIC_ENABLED'] = 'false'
os.environ['AUTH_MTLS_ENABLED'] = 'false'

# Add parent directory to path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import pytest and other modules AFTER environment is configured
import pytest
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


# ==================== FLASK APP FIXTURES ====================

@pytest.fixture(scope="function")
def app():
    """
    Flask application fixture with authentication enabled using test tokens
    Clears all data repositories before each test for isolation
    """
    # Import here to avoid circular imports
    from app import app as flask_app, user_repo, group_repo
    from auth.config import AuthConfig
    from auth.middleware import create_auth_middleware
    
    # Clear all data before each test for isolation
    user_repo._users.clear()
    group_repo._groups.clear()
    
    # Configure for testing
    flask_app.config['TESTING'] = True
    
    # CRITICAL: Reinitialize auth middleware with current environment variables
    # This ensures each test gets a fresh auth configuration
    auth_config = AuthConfig.from_env()
    auth_middleware = create_auth_middleware(auth_config)
    
    # Replace the auth middleware in the app module
    import app as app_module
    app_module.auth_middleware = auth_middleware
    
    yield flask_app
    
    # Clean up after test
    user_repo._users.clear()
    group_repo._groups.clear()


@pytest.fixture(scope="function")
def client(app):
    """
    Flask test client fixture
    """
    return app.test_client()


@pytest.fixture(scope="function")
def auth_headers():
    """
    Authentication headers fixture
    Returns headers dict with Bearer token for full access
    """
    return {'Authorization': f'Bearer {TEST_TOKENS["full_access"]}'}


@pytest.fixture(scope="function")
def read_only_headers():
    """
    Authentication headers fixture for read-only access
    """
    return {'Authorization': f'Bearer {TEST_TOKENS["read_only"]}'}


@pytest.fixture(scope="function")
def sample_user(client, auth_headers):
    """
    Create a sample user for testing
    Returns the created user data
    """
    user_data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": "testuser@example.com",
        "active": True,
        "name": {
            "givenName": "Test",
            "familyName": "User"
        }
    }
    
    headers = dict(auth_headers)
    headers['Content-Type'] = 'application/scim+json'
    
    response = client.post(
        '/scim/v2/Users',
        json=user_data,
        headers=headers
    )
    
    if response.status_code == 201:
        return response.get_json()
    else:
        # Return error response for debugging
        return response.get_json()


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
