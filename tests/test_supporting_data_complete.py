"""
Complete Automated Tests for Supporting Data API
Tests /api/supporting-data/roles and /api/supporting-data/departments endpoints

Framework: pytest + Flask test client
Target: Supporting Data APIs (READ-ONLY, paginated list only)
"""

import pytest
import json
from app import app, supporting_data_repo


@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestRolesAPI:
    """Test suite for Roles Supporting Data API"""
    
    def test_list_roles_success(self, client):
        """Test listing all roles"""
        response = client.get('/api/supporting-data/roles')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify pagination structure
        assert 'totalResults' in data
        assert 'startIndex' in data
        assert 'itemsPerPage' in data
        assert 'roles' in data
        
        # Verify we have predefined roles
        assert data['totalResults'] == 7
        assert len(data['roles']) == 7
    
    def test_list_roles_pagination(self, client):
        """Test roles pagination"""
        # Get first page
        response = client.get('/api/supporting-data/roles?startIndex=1&count=3')
        data = response.get_json()
        
        assert data['totalResults'] == 7
        assert data['startIndex'] == 1
        assert data['itemsPerPage'] == 3
        assert len(data['roles']) == 3
        
        # Get second page
        response2 = client.get('/api/supporting-data/roles?startIndex=4&count=3')
        data2 = response2.get_json()
        
        assert data2['startIndex'] == 4
        assert data2['itemsPerPage'] == 3
    
    def test_list_roles_structure(self, client):
        """Test role object structure"""
        response = client.get('/api/supporting-data/roles')
        data = response.get_json()
        
        # Check first role structure
        role = data['roles'][0]
        assert 'id' in role
        assert 'name' in role
        assert 'description' in role
        
        # Verify no SCIM fields
        assert 'schemas' not in role
        assert 'meta' not in role
        assert 'externalId' not in role
    
    def test_list_roles_predefined_data(self, client):
        """Test that predefined roles exist"""
        response = client.get('/api/supporting-data/roles')
        data = response.get_json()
        
        role_names = {role['name'] for role in data['roles']}
        
        expected_roles = {
            'Administrator',
            'Developer',
            'Analyst',
            'Manager',
            'Auditor',
            'Support',
            'Read-Only User'
        }
        
        assert role_names == expected_roles
    
    def test_get_role_by_id_not_supported(self, client):
        """Test that individual GET by ID is not supported"""
        response = client.get('/api/supporting-data/roles/role-admin')
        
        assert response.status_code == 405
        data = response.get_json()
        assert 'error' in data
        
        # Should NOT be SCIM error format
        assert 'schemas' not in data
        assert 'scimType' not in data
    
    def test_roles_read_only_post_not_allowed(self, client):
        """Test that POST is not allowed on roles"""
        role_data = {
            "name": "New Role",
            "description": "Should not be created"
        }
        
        response = client.post('/api/supporting-data/roles',
                              json=role_data,
                              content_type='application/json')
        
        assert response.status_code == 405  # Method Not Allowed
    
    def test_roles_read_only_put_not_allowed(self, client):
        """Test that PUT is not allowed on roles"""
        role_data = {
            "name": "Updated Role",
            "description": "Should not be updated"
        }
        
        response = client.put('/api/supporting-data/roles/role-admin',
                             json=role_data,
                             content_type='application/json')
        
        assert response.status_code == 405
    
    def test_roles_read_only_delete_not_allowed(self, client):
        """Test that DELETE is not allowed on roles"""
        response = client.delete('/api/supporting-data/roles/role-admin')
        
        assert response.status_code == 405


class TestDepartmentsAPI:
    """Test suite for Departments Supporting Data API"""
    
    def test_list_departments_success(self, client):
        """Test listing all departments"""
        response = client.get('/api/supporting-data/departments')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify pagination structure
        assert 'totalResults' in data
        assert 'startIndex' in data
        assert 'itemsPerPage' in data
        assert 'departments' in data
        
        # Verify we have predefined departments
        assert data['totalResults'] == 10
        assert len(data['departments']) == 10
    
    def test_list_departments_pagination(self, client):
        """Test departments pagination"""
        # Get first page
        response = client.get('/api/supporting-data/departments?startIndex=1&count=5')
        data = response.get_json()
        
        assert data['totalResults'] == 10
        assert data['startIndex'] == 1
        assert data['itemsPerPage'] == 5
        assert len(data['departments']) == 5
        
        # Get second page
        response2 = client.get('/api/supporting-data/departments?startIndex=6&count=5')
        data2 = response2.get_json()
        
        assert data2['startIndex'] == 6
        assert data2['itemsPerPage'] == 5
    
    def test_list_departments_structure(self, client):
        """Test department object structure"""
        response = client.get('/api/supporting-data/departments')
        data = response.get_json()
        
        # Check first department structure
        dept = data['departments'][0]
        assert 'id' in dept
        assert 'name' in dept
        
        # Verify no SCIM fields
        assert 'schemas' not in dept
        assert 'meta' not in dept
        assert 'externalId' not in dept
    
    def test_list_departments_predefined_data(self, client):
        """Test that predefined departments exist"""
        response = client.get('/api/supporting-data/departments')
        data = response.get_json()
        
        dept_names = {dept['name'] for dept in data['departments']}
        
        expected_departments = {
            'Engineering',
            'Product Management',
            'Sales',
            'Marketing',
            'Human Resources',
            'Finance',
            'Legal',
            'Operations',
            'Customer Support',
            'Executive'
        }
        
        assert dept_names == expected_departments
    
    def test_get_department_by_id_not_supported(self, client):
        """Test that individual GET by ID is not supported"""
        response = client.get('/api/supporting-data/departments/dept-eng')
        
        assert response.status_code == 405
        data = response.get_json()
        assert 'error' in data
        
        # Should NOT be SCIM error format
        assert 'schemas' not in data
        assert 'scimType' not in data
    
    def test_departments_read_only_post_not_allowed(self, client):
        """Test that POST is not allowed on departments"""
        dept_data = {
            "name": "New Department"
        }
        
        response = client.post('/api/supporting-data/departments',
                              json=dept_data,
                              content_type='application/json')
        
        assert response.status_code == 405
    
    def test_departments_read_only_put_not_allowed(self, client):
        """Test that PUT is not allowed on departments"""
        dept_data = {
            "name": "Updated Department"
        }
        
        response = client.put('/api/supporting-data/departments/dept-eng',
                             json=dept_data,
                             content_type='application/json')
        
        assert response.status_code == 405
    
    def test_departments_read_only_delete_not_allowed(self, client):
        """Test that DELETE is not allowed on departments"""
        response = client.delete('/api/supporting-data/departments/dept-eng')
        
        assert response.status_code == 405


class TestSupportingDataIsolation:
    """Test that supporting data is isolated from SCIM"""
    
    def test_supporting_data_not_in_scim_users(self, client):
        """Test that supporting data doesn't appear in SCIM Users"""
        response = client.get('/scim/v2/Users')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should be SCIM ListResponse
        assert 'urn:ietf:params:scim:api:messages:2.0:ListResponse' in data['schemas']
        assert 'Resources' in data
        
        # Should not have supporting data fields
        assert 'data' not in data
    
    def test_supporting_data_not_in_scim_groups(self, client):
        """Test that supporting data doesn't appear in SCIM Groups"""
        response = client.get('/scim/v2/Groups')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should be SCIM ListResponse
        assert 'urn:ietf:params:scim:api:messages:2.0:ListResponse' in data['schemas']
        assert 'Resources' in data
        
        # Should not have supporting data fields
        assert 'data' not in data
    
    def test_scim_not_in_supporting_data(self, client):
        """Test that SCIM fields don't appear in supporting data"""
        # Check roles
        roles_response = client.get('/api/supporting-data/roles')
        roles_data = roles_response.get_json()
        
        assert 'schemas' not in roles_data
        assert 'Resources' not in roles_data
        
        # Check departments
        depts_response = client.get('/api/supporting-data/departments')
        depts_data = depts_response.get_json()
        
        assert 'schemas' not in depts_data
        assert 'Resources' not in depts_data


class TestSupportingDataEdgeCases:
    """Test edge cases and error handling"""
    
    def test_invalid_pagination_parameters(self, client):
        """Test invalid pagination parameters"""
        # Negative startIndex
        response = client.get('/api/supporting-data/roles?startIndex=-1')
        assert response.status_code == 400
        
        # Negative count
        response = client.get('/api/supporting-data/roles?count=-5')
        assert response.status_code == 400
    
    def test_large_pagination_count(self, client):
        """Test requesting more items than exist"""
        response = client.get('/api/supporting-data/roles?startIndex=1&count=1000')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should return all available items
        assert data['itemsPerPage'] == 7
        assert len(data['roles']) == 7
    
    def test_pagination_beyond_results(self, client):
        """Test pagination starting beyond available results"""
        response = client.get('/api/supporting-data/roles?startIndex=100&count=10')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['totalResults'] == 7
        assert data['itemsPerPage'] == 0
        assert len(data['roles']) == 0
    
    def test_content_type_json(self, client):
        """Test that responses have correct content type"""
        endpoints = [
            '/api/supporting-data/roles',
            '/api/supporting-data/departments'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.content_type == 'application/json'


# Made with Bob