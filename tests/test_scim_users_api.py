"""
Automated Tests for SCIM 2.0 Users API
Tests /scim/v2/Users endpoints

Framework: pytest + Flask test client
Target: SCIM 2.0 User Resource endpoints
"""

import pytest
import json
from app import app, user_repo, group_repo


@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_repos():
    """Reset repositories before each test"""
    user_repo._users.clear()
    group_repo._groups.clear()
    yield
    user_repo._users.clear()
    group_repo._groups.clear()


class TestUsersCreate:
    """Test POST /scim/v2/Users - Create user"""
    
    def test_create_user_minimal(self, client):
        """Test creating user with minimal required fields"""
        user_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "john.doe@example.com",
            "active": True
        }
        
        response = client.post('/scim/v2/Users',
                              json=user_data,
                              content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data['userName'] == "john.doe@example.com"
        assert data['active'] is True
        assert 'id' in data
        assert 'meta' in data
        assert data['meta']['resourceType'] == 'User'
        assert 'Location' in response.headers
    
    def test_create_user_full(self, client):
        """Test creating user with all fields"""
        user_data = {
            "schemas": [
                "urn:ietf:params:scim:schemas:core:2.0:User",
                "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
            ],
            "userName": "jane.smith@example.com",
            "name": {
                "givenName": "Jane",
                "familyName": "Smith",
                "formatted": "Jane Smith"
            },
            "emails": [
                {
                    "value": "jane.smith@example.com",
                    "type": "work",
                    "primary": True
                }
            ],
            "active": True,
            "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": {
                "employeeNumber": "12345",
                "department": "Engineering",
                "manager": {
                    "value": "mgr-123"
                }
            }
        }
        
        response = client.post('/scim/v2/Users',
                              json=user_data,
                              content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data['userName'] == "jane.smith@example.com"
        assert data['name']['givenName'] == "Jane"
        assert data['emails'][0]['value'] == "jane.smith@example.com"
        assert data['urn:ietf:params:scim:schemas:extension:enterprise:2.0:User']['department'] == "Engineering"
    
    def test_create_user_duplicate_username(self, client):
        """Test creating user with duplicate userName"""
        user_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "duplicate@example.com",
            "active": True
        }
        
        # Create first user
        response1 = client.post('/scim/v2/Users', json=user_data)
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = client.post('/scim/v2/Users', json=user_data)
        assert response2.status_code == 409
        data = response2.get_json()
        assert data['scimType'] == 'uniqueness'
    
    def test_create_user_missing_schema(self, client):
        """Test creating user without required schema"""
        user_data = {
            "userName": "test@example.com",
            "active": True
        }
        
        response = client.post('/scim/v2/Users', json=user_data)
        assert response.status_code == 400


class TestUsersGet:
    """Test GET /scim/v2/Users/{id} - Retrieve user"""
    
    def test_get_user_success(self, client):
        """Test retrieving existing user"""
        # Create user first
        user_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "get.test@example.com",
            "active": True
        }
        create_response = client.post('/scim/v2/Users', json=user_data)
        user_id = create_response.get_json()['id']
        
        # Get user
        response = client.get(f'/scim/v2/Users/{user_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == user_id
        assert data['userName'] == "get.test@example.com"
    
    def test_get_user_not_found(self, client):
        """Test retrieving non-existent user"""
        response = client.get('/scim/v2/Users/non-existent-id')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'urn:ietf:params:scim:api:messages:2.0:Error' in data['schemas']


class TestUsersList:
    """Test GET /scim/v2/Users - List users"""
    
    def test_list_users_empty(self, client):
        """Test listing users when none exist"""
        response = client.get('/scim/v2/Users')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['totalResults'] == 0
        assert data['startIndex'] == 1
        assert data['itemsPerPage'] == 0
        assert data['Resources'] == []
    
    def test_list_users_with_data(self, client):
        """Test listing users with data"""
        # Create multiple users
        for i in range(5):
            user_data = {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": f"user{i}@example.com",
                "active": True
            }
            client.post('/scim/v2/Users', json=user_data)
        
        response = client.get('/scim/v2/Users')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['totalResults'] == 5
        assert len(data['Resources']) == 5
    
    def test_list_users_pagination(self, client):
        """Test pagination parameters"""
        # Create 10 users
        for i in range(10):
            user_data = {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": f"page{i}@example.com",
                "active": True
            }
            client.post('/scim/v2/Users', json=user_data)
        
        # Get first page
        response = client.get('/scim/v2/Users?startIndex=1&count=3')
        data = response.get_json()
        
        assert data['totalResults'] == 10
        assert data['startIndex'] == 1
        assert data['itemsPerPage'] == 3
        assert len(data['Resources']) == 3
    
    def test_list_users_pagination_second_page(self, client):
        """Test getting second page of results"""
        # Create 10 users
        for i in range(10):
            user_data = {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": f"page{i}@example.com",
                "active": True
            }
            client.post('/scim/v2/Users', json=user_data)
        
        # Get second page
        response = client.get('/scim/v2/Users?startIndex=4&count=3')
        data = response.get_json()
        
        assert data['totalResults'] == 10
        assert data['startIndex'] == 4
        assert data['itemsPerPage'] == 3
        assert len(data['Resources']) == 3
    
    def test_list_users_pagination_last_page(self, client):
        """Test getting last page with fewer items"""
        # Create 10 users
        for i in range(10):
            user_data = {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": f"page{i}@example.com",
                "active": True
            }
            client.post('/scim/v2/Users', json=user_data)
        
        # Get last page (should have only 1 item)
        response = client.get('/scim/v2/Users?startIndex=10&count=3')
        data = response.get_json()
        
        assert data['totalResults'] == 10
        assert data['startIndex'] == 10
        assert data['itemsPerPage'] == 1
        assert len(data['Resources']) == 1
    
    def test_list_users_pagination_beyond_results(self, client):
        """Test pagination beyond available results"""
        # Create 5 users
        for i in range(5):
            user_data = {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": f"page{i}@example.com",
                "active": True
            }
            client.post('/scim/v2/Users', json=user_data)
        
        # Request page beyond results
        response = client.get('/scim/v2/Users?startIndex=10&count=3')
        data = response.get_json()
        
        assert data['totalResults'] == 5
        assert data['startIndex'] == 10
        assert data['itemsPerPage'] == 0
        assert len(data['Resources']) == 0
    
    def test_list_users_pagination_invalid_start_index(self, client):
        """Test invalid startIndex (< 1)"""
        response = client.get('/scim/v2/Users?startIndex=0&count=10')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'startIndex must be >= 1' in data['detail']
    
    def test_list_users_pagination_invalid_count(self, client):
        """Test invalid count (< 0)"""
        response = client.get('/scim/v2/Users?startIndex=1&count=-5')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'count must be >= 0' in data['detail']
    
    def test_list_users_pagination_count_zero(self, client):
        """Test count=0 returns no results"""
        # Create users
        for i in range(5):
            user_data = {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": f"page{i}@example.com",
                "active": True
            }
            client.post('/scim/v2/Users', json=user_data)
        
        response = client.get('/scim/v2/Users?startIndex=1&count=0')
        data = response.get_json()
        
        assert data['totalResults'] == 5
        assert data['itemsPerPage'] == 0
        assert len(data['Resources']) == 0
    
    def test_list_users_filter(self, client):
        """Test filtering users"""
        # Create users
        client.post('/scim/v2/Users', json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "active@example.com",
            "active": True
        })
        client.post('/scim/v2/Users', json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "inactive@example.com",
            "active": False
        })
        
        # Filter by active
        response = client.get('/scim/v2/Users?filter=active eq true')
        data = response.get_json()
        
        assert data['totalResults'] == 1
        assert data['Resources'][0]['userName'] == "active@example.com"
    
    def test_list_users_filter_username_eq(self, client):
        """Test filtering by userName with eq operator"""
        # Create users
        client.post('/scim/v2/Users', json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "john.doe@example.com",
            "active": True
        })
        client.post('/scim/v2/Users', json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "jane.smith@example.com",
            "active": True
        })
        
        # Filter by userName
        response = client.get('/scim/v2/Users?filter=userName eq "john.doe@example.com"')
        data = response.get_json()
        
        assert data['totalResults'] == 1
        assert data['Resources'][0]['userName'] == "john.doe@example.com"
    
    def test_list_users_filter_username_co(self, client):
        """Test filtering by userName with co (contains) operator"""
        # Create users
        client.post('/scim/v2/Users', json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "john.doe@example.com",
            "active": True
        })
        client.post('/scim/v2/Users', json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "jane.smith@example.com",
            "active": True
        })
        client.post('/scim/v2/Users', json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "bob.jones@test.com",
            "active": True
        })
        
        # Filter by userName contains "example"
        response = client.get('/scim/v2/Users?filter=userName co "example"')
        data = response.get_json()
        
        assert data['totalResults'] == 2
        usernames = [u['userName'] for u in data['Resources']]
        assert "john.doe@example.com" in usernames
        assert "jane.smith@example.com" in usernames
    
    def test_list_users_filter_username_sw(self, client):
        """Test filtering by userName with sw (starts with) operator"""
        # Create users
        client.post('/scim/v2/Users', json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "john.doe@example.com",
            "active": True
        })
        client.post('/scim/v2/Users', json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "jane.smith@example.com",
            "active": True
        })
        client.post('/scim/v2/Users', json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "bob.jones@test.com",
            "active": True
        })
        
        # Filter by userName starts with "john"
        response = client.get('/scim/v2/Users?filter=userName sw "john"')
        data = response.get_json()
        
        assert data['totalResults'] == 1
        assert data['Resources'][0]['userName'] == "john.doe@example.com"
    
    def test_list_users_filter_username_ew(self, client):
        """Test filtering by userName with ew (ends with) operator"""
        # Create users
        client.post('/scim/v2/Users', json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "john.doe@example.com",
            "active": True
        })
        client.post('/scim/v2/Users', json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "jane.smith@test.com",
            "active": True
        })
        
        # Filter by userName ends with "example.com"
        response = client.get('/scim/v2/Users?filter=userName ew "example.com"')
        data = response.get_json()
        
        assert data['totalResults'] == 1
        assert data['Resources'][0]['userName'] == "john.doe@example.com"
    
    def test_list_users_filter_department(self, client):
        """Test filtering by department (enterprise extension)"""
        # Create users with departments
        client.post('/scim/v2/Users', json={
            "schemas": [
                "urn:ietf:params:scim:schemas:core:2.0:User",
                "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
            ],
            "userName": "eng1@example.com",
            "active": True,
            "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": {
                "department": "Engineering"
            }
        })
        client.post('/scim/v2/Users', json={
            "schemas": [
                "urn:ietf:params:scim:schemas:core:2.0:User",
                "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
            ],
            "userName": "sales1@example.com",
            "active": True,
            "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": {
                "department": "Sales"
            }
        })
        
        # Filter by department
        response = client.get('/scim/v2/Users?filter=department eq "Engineering"')
        data = response.get_json()
        
        assert data['totalResults'] == 1
        assert data['Resources'][0]['userName'] == "eng1@example.com"
    
    def test_list_users_filter_with_pagination(self, client):
        """Test combining filter with pagination"""
        # Create 10 active and 5 inactive users
        for i in range(10):
            client.post('/scim/v2/Users', json={
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": f"active{i}@example.com",
                "active": True
            })
        for i in range(5):
            client.post('/scim/v2/Users', json={
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": f"inactive{i}@example.com",
                "active": False
            })
        
        # Filter active users with pagination
        response = client.get('/scim/v2/Users?filter=active eq true&startIndex=1&count=3')
        data = response.get_json()
        
        assert data['totalResults'] == 10
        assert data['startIndex'] == 1
        assert data['itemsPerPage'] == 3
        assert len(data['Resources']) == 3
        # Verify all returned users are active
        for user in data['Resources']:
            assert user['active'] is True
    
    def test_list_users_filter_invalid_syntax(self, client):
        """Test invalid filter syntax"""
        response = client.get('/scim/v2/Users?filter=invalid filter syntax')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['scimType'] == 'invalidFilter'
    
    def test_list_users_filter_case_insensitive(self, client):
        """Test that string filters are case-insensitive"""
        # Create user
        client.post('/scim/v2/Users', json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "John.Doe@Example.COM",
            "active": True
        })
        
        # Filter with different case
        response = client.get('/scim/v2/Users?filter=userName eq "john.doe@example.com"')
        data = response.get_json()
        
        assert data['totalResults'] == 1
        assert data['Resources'][0]['userName'] == "John.Doe@Example.COM"


class TestUsersPatch:
    """Test PATCH /scim/v2/Users/{id} - Update user"""
    
    def test_patch_user_replace_active(self, client):
        """Test replacing active status"""
        # Create user
        user_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "patch@example.com",
            "active": True
        }
        create_response = client.post('/scim/v2/Users', json=user_data)
        user_id = create_response.get_json()['id']
        
        # Patch user
        patch_data = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": "active",
                    "value": False
                }
            ]
        }
        
        response = client.patch(f'/scim/v2/Users/{user_id}',
                               json=patch_data,
                               content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['active'] is False
    
    def test_patch_user_replace_name(self, client):
        """Test replacing name"""
        # Create user
        user_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "name@example.com",
            "name": {
                "givenName": "Old",
                "familyName": "Name"
            }
        }
        create_response = client.post('/scim/v2/Users', json=user_data)
        user_id = create_response.get_json()['id']
        
        # Patch name
        patch_data = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": "name.givenName",
                    "value": "New"
                }
            ]
        }
        
        response = client.patch(f'/scim/v2/Users/{user_id}', json=patch_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['name']['givenName'] == "New"
    
    def test_patch_user_not_found(self, client):
        """Test patching non-existent user"""
        patch_data = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [{"op": "replace", "path": "active", "value": False}]
        }
        
        response = client.patch('/scim/v2/Users/non-existent', json=patch_data)
        assert response.status_code == 404


class TestUsersDelete:
    """Test DELETE /scim/v2/Users/{id} - Delete user"""
    
    def test_delete_user_success(self, client):
        """Test deleting existing user"""
        # Create user
        user_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "delete@example.com",
            "active": True
        }
        create_response = client.post('/scim/v2/Users', json=user_data)
        user_id = create_response.get_json()['id']
        
        # Delete user
        response = client.delete(f'/scim/v2/Users/{user_id}')
        
        assert response.status_code == 204
        assert response.data == b''
        
        # Verify user is deleted
        get_response = client.get(f'/scim/v2/Users/{user_id}')
        assert get_response.status_code == 404
    
    def test_delete_user_not_found(self, client):
        """Test deleting non-existent user"""
        response = client.delete('/scim/v2/Users/non-existent')
        assert response.status_code == 404


class TestUsersPutNotSupported:
    """Test PUT /scim/v2/Users/{id} - Should return 501"""
    
    def test_put_user_not_supported(self, client):
        """Test that PUT returns 501 Not Implemented"""
        # Create user first
        user_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "put@example.com",
            "active": True
        }
        create_response = client.post('/scim/v2/Users', json=user_data)
        user_id = create_response.get_json()['id']
        
        # Try PUT
        response = client.put(f'/scim/v2/Users/{user_id}',
                             json=user_data,
                             content_type='application/json')
        
        assert response.status_code == 501
        data = response.get_json()
        assert 'PUT operation not supported' in data['detail']


# Made with Bob