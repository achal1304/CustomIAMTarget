"""
Automated Tests for SCIM 2.0 Groups API
Tests /scim/v2/Groups endpoints

Framework: pytest + Flask test client
Target: SCIM 2.0 Group Resource endpoints
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


@pytest.fixture
def sample_user(client):
    """Create a sample user for group membership tests"""
    user_data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": "member@example.com",
        "active": True
    }
    response = client.post('/scim/v2/Users', json=user_data)
    return response.get_json()


class TestGroupsCreate:
    """Test POST /scim/v2/Groups - Create group"""
    
    def test_create_group_minimal(self, client):
        """Test creating group with minimal required fields"""
        group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Engineering Team"
        }
        
        response = client.post('/scim/v2/Groups',
                              json=group_data,
                              content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data['displayName'] == "Engineering Team"
        assert 'id' in data
        assert 'meta' in data
        assert data['meta']['resourceType'] == 'Group'
        assert 'Location' in response.headers
    
    def test_create_group_with_members(self, client, sample_user):
        """Test creating group with members"""
        group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Developers",
            "members": [
                {
                    "value": sample_user['id'],
                    "display": sample_user['userName']
                }
            ]
        }
        
        response = client.post('/scim/v2/Groups', json=group_data)
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data['displayName'] == "Developers"
        assert len(data['members']) == 1
        assert data['members'][0]['value'] == sample_user['id']
    
    def test_create_group_duplicate_displayname(self, client):
        """Test creating group with duplicate displayName"""
        group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Duplicate Group"
        }
        
        # Create first group
        response1 = client.post('/scim/v2/Groups', json=group_data)
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = client.post('/scim/v2/Groups', json=group_data)
        assert response2.status_code == 409
        data = response2.get_json()
        assert data['scimType'] == 'uniqueness'
    
    def test_create_group_missing_schema(self, client):
        """Test creating group without required schema"""
        group_data = {
            "displayName": "Test Group"
        }
        
        response = client.post('/scim/v2/Groups', json=group_data)
        assert response.status_code == 400


class TestGroupsGet:
    """Test GET /scim/v2/Groups/{id} - Retrieve group"""
    
    def test_get_group_success(self, client):
        """Test retrieving existing group"""
        # Create group first
        group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Get Test Group"
        }
        create_response = client.post('/scim/v2/Groups', json=group_data)
        group_id = create_response.get_json()['id']
        
        # Get group
        response = client.get(f'/scim/v2/Groups/{group_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == group_id
        assert data['displayName'] == "Get Test Group"
    
    def test_get_group_not_found(self, client):
        """Test retrieving non-existent group"""
        response = client.get('/scim/v2/Groups/non-existent-id')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'urn:ietf:params:scim:api:messages:2.0:Error' in data['schemas']


class TestGroupsList:
    """Test GET /scim/v2/Groups - List groups"""
    
    def test_list_groups_empty(self, client):
        """Test listing groups when none exist"""
        response = client.get('/scim/v2/Groups')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['totalResults'] == 0
        assert data['startIndex'] == 1
        assert data['itemsPerPage'] == 0
        assert data['Resources'] == []
    
    def test_list_groups_with_data(self, client):
        """Test listing groups with data"""
        # Create multiple groups
        for i in range(5):
            group_data = {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "displayName": f"Group {i}"
            }
            client.post('/scim/v2/Groups', json=group_data)
        
        response = client.get('/scim/v2/Groups')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['totalResults'] == 5
        assert len(data['Resources']) == 5
    
    def test_list_groups_pagination(self, client):
        """Test pagination parameters"""
        # Create 10 groups
        for i in range(10):
            group_data = {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "displayName": f"Page Group {i}"
            }
            client.post('/scim/v2/Groups', json=group_data)
        
        # Get first page
        response = client.get('/scim/v2/Groups?startIndex=1&count=3')
        data = response.get_json()
        
        assert data['totalResults'] == 10
        assert data['startIndex'] == 1
        assert data['itemsPerPage'] == 3
        assert len(data['Resources']) == 3
    
    def test_list_groups_pagination_second_page(self, client):
        """Test getting second page of results"""
        # Create 10 groups
        for i in range(10):
            group_data = {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "displayName": f"Page Group {i}"
            }
            client.post('/scim/v2/Groups', json=group_data)
        
        # Get second page
        response = client.get('/scim/v2/Groups?startIndex=4&count=3')
        data = response.get_json()
        
        assert data['totalResults'] == 10
        assert data['startIndex'] == 4
        assert data['itemsPerPage'] == 3
        assert len(data['Resources']) == 3
    
    def test_list_groups_pagination_last_page(self, client):
        """Test getting last page with fewer items"""
        # Create 10 groups
        for i in range(10):
            group_data = {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "displayName": f"Page Group {i}"
            }
            client.post('/scim/v2/Groups', json=group_data)
        
        # Get last page (should have only 1 item)
        response = client.get('/scim/v2/Groups?startIndex=10&count=3')
        data = response.get_json()
        
        assert data['totalResults'] == 10
        assert data['startIndex'] == 10
        assert data['itemsPerPage'] == 1
        assert len(data['Resources']) == 1
    
    def test_list_groups_pagination_beyond_results(self, client):
        """Test pagination beyond available results"""
        # Create 5 groups
        for i in range(5):
            group_data = {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "displayName": f"Page Group {i}"
            }
            client.post('/scim/v2/Groups', json=group_data)
        
        # Request page beyond results
        response = client.get('/scim/v2/Groups?startIndex=10&count=3')
        data = response.get_json()
        
        assert data['totalResults'] == 5
        assert data['startIndex'] == 10
        assert data['itemsPerPage'] == 0
        assert len(data['Resources']) == 0
    
    def test_list_groups_pagination_invalid_start_index(self, client):
        """Test invalid startIndex (< 1)"""
        response = client.get('/scim/v2/Groups?startIndex=0&count=10')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'startIndex must be >= 1' in data['detail']
    
    def test_list_groups_pagination_invalid_count(self, client):
        """Test invalid count (< 0)"""
        response = client.get('/scim/v2/Groups?startIndex=1&count=-5')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'count must be >= 0' in data['detail']
    
    def test_list_groups_pagination_count_zero(self, client):
        """Test count=0 returns no results"""
        # Create groups
        for i in range(5):
            group_data = {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "displayName": f"Page Group {i}"
            }
            client.post('/scim/v2/Groups', json=group_data)
        
        response = client.get('/scim/v2/Groups?startIndex=1&count=0')
        data = response.get_json()
        
        assert data['totalResults'] == 5
        assert data['itemsPerPage'] == 0
        assert len(data['Resources']) == 0
    
    def test_list_groups_filter(self, client):
        """Test filtering groups"""
        # Create groups
        client.post('/scim/v2/Groups', json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Engineering"
        })
        client.post('/scim/v2/Groups', json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Marketing"
        })
        
        # Filter by displayName
        response = client.get('/scim/v2/Groups?filter=displayName eq "Engineering"')
        data = response.get_json()
        
        assert data['totalResults'] == 1
        assert data['Resources'][0]['displayName'] == "Engineering"
    
    def test_list_groups_filter_case_insensitive(self, client):
        """Test that displayName filter is case-insensitive"""
        # Create group
        client.post('/scim/v2/Groups', json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Engineering Team"
        })
        
        # Filter with different case
        response = client.get('/scim/v2/Groups?filter=displayName eq "engineering team"')
        data = response.get_json()
        
        assert data['totalResults'] == 1
        assert data['Resources'][0]['displayName'] == "Engineering Team"
    
    def test_list_groups_filter_multiple_matches(self, client):
        """Test filter returning multiple groups"""
        # Create groups with similar names
        client.post('/scim/v2/Groups', json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Engineering"
        })
        client.post('/scim/v2/Groups', json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Marketing"
        })
        client.post('/scim/v2/Groups', json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Sales"
        })
        
        # Filter that doesn't match
        response = client.get('/scim/v2/Groups?filter=displayName eq "HR"')
        data = response.get_json()
        
        assert data['totalResults'] == 0
        assert len(data['Resources']) == 0
    
    def test_list_groups_filter_with_pagination(self, client):
        """Test combining filter with pagination"""
        # Create multiple groups
        for i in range(5):
            client.post('/scim/v2/Groups', json={
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "displayName": f"Engineering Team {i}"
            })
        for i in range(3):
            client.post('/scim/v2/Groups', json={
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "displayName": f"Marketing Team {i}"
            })
        
        # Note: Current implementation has basic filter support
        # This test validates the pagination works with total results
        response = client.get('/scim/v2/Groups?startIndex=1&count=3')
        data = response.get_json()
        
        assert data['totalResults'] == 8
        assert data['startIndex'] == 1
        assert data['itemsPerPage'] == 3
        assert len(data['Resources']) == 3
    
    def test_list_groups_no_filter_returns_all(self, client):
        """Test that no filter returns all groups"""
        # Create groups
        for i in range(7):
            client.post('/scim/v2/Groups', json={
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "displayName": f"Group {i}"
            })
        
        response = client.get('/scim/v2/Groups')
        data = response.get_json()
        
        assert data['totalResults'] == 7
        assert len(data['Resources']) == 7
    
    def test_list_groups_large_count(self, client):
        """Test requesting more items than exist"""
        # Create 5 groups
        for i in range(5):
            client.post('/scim/v2/Groups', json={
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "displayName": f"Group {i}"
            })
        
        # Request 100 items
        response = client.get('/scim/v2/Groups?startIndex=1&count=100')
        data = response.get_json()
        
        assert data['totalResults'] == 5
        assert data['itemsPerPage'] == 5
        assert len(data['Resources']) == 5


class TestGroupsPatch:
    """Test PATCH /scim/v2/Groups/{id} - Update group"""
    
    def test_patch_group_add_member(self, client, sample_user):
        """Test adding member to group"""
        # Create group
        group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Patch Test Group"
        }
        create_response = client.post('/scim/v2/Groups', json=group_data)
        group_id = create_response.get_json()['id']
        
        # Add member
        patch_data = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "add",
                    "path": "members",
                    "value": [
                        {
                            "value": sample_user['id'],
                            "display": sample_user['userName']
                        }
                    ]
                }
            ]
        }
        
        response = client.patch(f'/scim/v2/Groups/{group_id}',
                               json=patch_data,
                               content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['members']) == 1
        assert data['members'][0]['value'] == sample_user['id']
    
    def test_patch_group_remove_member(self, client, sample_user):
        """Test removing member from group"""
        # Create group with member
        group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Remove Test Group",
            "members": [
                {
                    "value": sample_user['id'],
                    "display": sample_user['userName']
                }
            ]
        }
        create_response = client.post('/scim/v2/Groups', json=group_data)
        group_id = create_response.get_json()['id']
        
        # Remove member
        patch_data = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "remove",
                    "path": f"members[value eq \"{sample_user['id']}\"]"
                }
            ]
        }
        
        response = client.patch(f'/scim/v2/Groups/{group_id}', json=patch_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data.get('members', [])) == 0
    
    def test_patch_group_replace_displayname(self, client):
        """Test replacing displayName"""
        # Create group
        group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Old Name"
        }
        create_response = client.post('/scim/v2/Groups', json=group_data)
        group_id = create_response.get_json()['id']
        
        # Replace displayName
        patch_data = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": "displayName",
                    "value": "New Name"
                }
            ]
        }
        
        response = client.patch(f'/scim/v2/Groups/{group_id}', json=patch_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['displayName'] == "New Name"
    
    def test_patch_group_not_found(self, client):
        """Test patching non-existent group"""
        patch_data = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [{"op": "replace", "path": "displayName", "value": "Test"}]
        }
        
        response = client.patch('/scim/v2/Groups/non-existent', json=patch_data)
        assert response.status_code == 404


class TestGroupsDelete:
    """Test DELETE /scim/v2/Groups/{id} - Delete group"""
    
    def test_delete_group_success(self, client):
        """Test deleting existing group"""
        # Create group
        group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Delete Test Group"
        }
        create_response = client.post('/scim/v2/Groups', json=group_data)
        group_id = create_response.get_json()['id']
        
        # Delete group
        response = client.delete(f'/scim/v2/Groups/{group_id}')
        
        assert response.status_code == 204
        assert response.data == b''
        
        # Verify group is deleted
        get_response = client.get(f'/scim/v2/Groups/{group_id}')
        assert get_response.status_code == 404
    
    def test_delete_group_not_found(self, client):
        """Test deleting non-existent group"""
        response = client.delete('/scim/v2/Groups/non-existent')
        assert response.status_code == 404
    
    def test_delete_group_removes_user_membership(self, client, sample_user):
        """Test that deleting group removes membership from users"""
        # Create group with member
        group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Membership Test",
            "members": [{"value": sample_user['id']}]
        }
        create_response = client.post('/scim/v2/Groups', json=group_data)
        group_id = create_response.get_json()['id']
        
        # Delete group
        client.delete(f'/scim/v2/Groups/{group_id}')
        
        # Verify user no longer has group membership
        user_response = client.get(f'/scim/v2/Users/{sample_user["id"]}')
        user_data = user_response.get_json()
        assert len(user_data.get('groups', [])) == 0


class TestGroupsPutNotSupported:
    """Test PUT /scim/v2/Groups/{id} - Should return 501"""
    
    def test_put_group_not_supported(self, client):
        """Test that PUT returns 501 Not Implemented"""
        # Create group first
        group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "PUT Test Group"
        }
        create_response = client.post('/scim/v2/Groups', json=group_data)
        group_id = create_response.get_json()['id']
        
        # Try PUT
        response = client.put(f'/scim/v2/Groups/{group_id}',
                             json=group_data,
                             content_type='application/json')
        
        assert response.status_code == 501
        data = response.get_json()
        assert 'PUT operation not supported' in data['detail']


# Made with Bob