"""
Complete Automated Tests for Supporting Data API
Tests /api/supporting-data/roles and /api/supporting-data/departments endpoints

Framework: pytest + Flask test client
Target: Supporting Data APIs (READ-ONLY, paginated list only)
"""

import pytest
import json
from app import app, supporting_data_repo



class TestRolesAPI:
    """Test suite for Roles Supporting Data API"""
    
    def test_list_roles_success(self, client, auth_headers):
        """Test listing all roles"""
        response = client.get('/api/supporting-data/roles', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify SCIM-like structure
        assert 'schemas' in data
        assert data['schemas'] == ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
        assert 'totalResults' in data
        assert 'startIndex' in data
        assert 'itemsPerPage' in data
        assert 'Resources' in data
        
        # Verify we have predefined roles
        assert data['totalResults'] == 7
        assert len(data['Resources']) == 7
    
    def test_list_roles_pagination(self, client, auth_headers):
        """Test roles pagination"""
        # Get first page
        response = client.get('/api/supporting-data/roles?startIndex=1&count=3', headers=auth_headers)
        data = response.get_json()
        
        assert data['schemas'] == ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
        assert data['totalResults'] == 7
        assert data['startIndex'] == 1
        assert data['itemsPerPage'] == 3
        assert len(data['Resources']) == 3
        
        # Get second page
        response2 = client.get('/api/supporting-data/roles?startIndex=4&count=3', headers=auth_headers)
        data2 = response2.get_json()
        
        assert data2['schemas'] == ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
        assert data2['startIndex'] == 4
        assert data2['itemsPerPage'] == 3
    
    def test_list_roles_structure(self, client, auth_headers):
        """Test role object structure"""
        response = client.get('/api/supporting-data/roles', headers=auth_headers)
        data = response.get_json()
        
        # Verify response has SCIM schema
        assert 'schemas' in data
        assert data['schemas'] == ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
        
        # Check first role structure
        role = data['Resources'][0]
        assert 'id' in role
        assert 'name' in role
        assert 'description' in role
        
        # Verify individual resources don't have SCIM meta fields
        assert 'schemas' not in role
        assert 'meta' not in role
        assert 'externalId' not in role
    
    def test_list_roles_predefined_data(self, client, auth_headers):
        """Test that predefined roles exist"""
        response = client.get('/api/supporting-data/roles', headers=auth_headers)
        data = response.get_json()
        
        role_names = {role['name'] for role in data['Resources']}
        
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
    
    def test_get_role_by_id_not_supported(self, client, auth_headers):
        """Test that individual GET by ID is not supported"""
        response = client.get('/api/supporting-data/roles/role-admin', headers=auth_headers)
        
        assert response.status_code == 405
        data = response.get_json()
        assert 'error' in data
        
        # Should NOT be SCIM error format
        assert 'schemas' not in data
        assert 'scimType' not in data
    
    def test_roles_read_only_post_not_allowed(self, client, auth_headers):
        """Test that POST is not allowed on roles"""
        role_data = {
            "name": "New Role",
            "description": "Should not be created"
        }
        
        response = client.post('/api/supporting-data/roles',
                              json=role_data,
                              content_type='application/json', headers=auth_headers)
        
        assert response.status_code == 405  # Method Not Allowed
    
    def test_roles_read_only_put_not_allowed(self, client, auth_headers):
        """Test that PUT is not allowed on roles"""
        role_data = {
            "name": "Updated Role",
            "description": "Should not be updated"
        }
        
        response = client.put('/api/supporting-data/roles/role-admin',
                             json=role_data,
                             content_type='application/json', headers=auth_headers)
        
        assert response.status_code == 405
    
    def test_roles_read_only_delete_not_allowed(self, client, auth_headers):
        """Test that DELETE is not allowed on roles"""
        response = client.delete('/api/supporting-data/roles/role-admin', headers=auth_headers)
        
        assert response.status_code == 405


class TestDepartmentsAPI:
    """Test suite for Departments Supporting Data API"""
    
    def test_list_departments_success(self, client, auth_headers):
        """Test listing all departments"""
        response = client.get('/api/supporting-data/departments', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify SCIM-like structure
        assert 'schemas' in data
        assert data['schemas'] == ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
        assert 'totalResults' in data
        assert 'startIndex' in data
        assert 'itemsPerPage' in data
        assert 'Resources' in data
        
        # Verify we have predefined departments
        assert data['totalResults'] == 10
        assert len(data['Resources']) == 10
    
    def test_list_departments_pagination(self, client, auth_headers):
        """Test departments pagination"""
        # Get first page
        response = client.get('/api/supporting-data/departments?startIndex=1&count=5', headers=auth_headers)
        data = response.get_json()
        
        assert data['schemas'] == ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
        assert data['totalResults'] == 10
        assert data['startIndex'] == 1
        assert data['itemsPerPage'] == 5
        assert len(data['Resources']) == 5
        
        # Get second page
        response2 = client.get('/api/supporting-data/departments?startIndex=6&count=5', headers=auth_headers)
        data2 = response2.get_json()
        
        assert data2['schemas'] == ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
        assert data2['startIndex'] == 6
        assert data2['itemsPerPage'] == 5
    
    def test_list_departments_structure(self, client, auth_headers):
        """Test department object structure"""
        response = client.get('/api/supporting-data/departments', headers=auth_headers)
        data = response.get_json()
        
        # Verify response has SCIM schema
        assert 'schemas' in data
        assert data['schemas'] == ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
        
        # Check first department structure
        dept = data['Resources'][0]
        assert 'id' in dept
        assert 'name' in dept
        
        # Verify individual resources don't have SCIM meta fields
        assert 'schemas' not in dept
        assert 'meta' not in dept
        assert 'externalId' not in dept
    
    def test_list_departments_predefined_data(self, client, auth_headers):
        """Test that predefined departments exist"""
        response = client.get('/api/supporting-data/departments', headers=auth_headers)
        data = response.get_json()
        
        dept_names = {dept['name'] for dept in data['Resources']}
        
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
    
    def test_get_department_by_id_not_supported(self, client, auth_headers):
        """Test that individual GET by ID is not supported"""
        response = client.get('/api/supporting-data/departments/dept-eng', headers=auth_headers)
        
        assert response.status_code == 405
        data = response.get_json()
        assert 'error' in data
        
        # Should NOT be SCIM error format
        assert 'schemas' not in data
        assert 'scimType' not in data
    
    def test_departments_read_only_post_not_allowed(self, client, auth_headers):
        """Test that POST is not allowed on departments"""
        dept_data = {
            "name": "New Department"
        }
        
        response = client.post('/api/supporting-data/departments',
                              json=dept_data,
                              content_type='application/json', headers=auth_headers)
        
        assert response.status_code == 405
    
    def test_departments_read_only_put_not_allowed(self, client, auth_headers):
        """Test that PUT is not allowed on departments"""
        dept_data = {
            "name": "Updated Department"
        }
        
        response = client.put('/api/supporting-data/departments/dept-eng',
                             json=dept_data,
                             content_type='application/json', headers=auth_headers)
        
        assert response.status_code == 405
    
    def test_departments_read_only_delete_not_allowed(self, client, auth_headers):
        """Test that DELETE is not allowed on departments"""
        response = client.delete('/api/supporting-data/departments/dept-eng', headers=auth_headers)
        
        assert response.status_code == 405


class TestSupportingDataIsolation:
    """Test that supporting data is isolated from SCIM"""
    
    def test_supporting_data_not_in_scim_users(self, client, auth_headers):
        """Test that supporting data doesn't appear in SCIM Users"""
        response = client.get('/scim/v2/Users', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should be SCIM ListResponse
        assert 'urn:ietf:params:scim:api:messages:2.0:ListResponse' in data['schemas']
        assert 'Resources' in data
        
        # Should not have supporting data fields
        assert 'data' not in data
    
    def test_supporting_data_not_in_scim_groups(self, client, auth_headers):
        """Test that supporting data doesn't appear in SCIM Groups"""
        response = client.get('/scim/v2/Groups', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should be SCIM ListResponse
        assert 'urn:ietf:params:scim:api:messages:2.0:ListResponse' in data['schemas']
        assert 'Resources' in data
        
        # Should not have supporting data fields
        assert 'data' not in data
    
    def test_scim_not_in_supporting_data(self, client, auth_headers):
        """Test that supporting data now uses SCIM-like format"""
        # Check roles - should now have SCIM format
        roles_response = client.get('/api/supporting-data/roles', headers=auth_headers)
        roles_data = roles_response.get_json()
        
        # Now uses SCIM ListResponse format
        assert 'schemas' in roles_data
        assert roles_data['schemas'] == ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
        assert 'Resources' in roles_data
        
        # Check departments - should now have SCIM format
        depts_response = client.get('/api/supporting-data/departments', headers=auth_headers)
        depts_data = depts_response.get_json()
        
        # Now uses SCIM ListResponse format
        assert 'schemas' in depts_data
        assert depts_data['schemas'] == ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
        assert 'Resources' in depts_data


class TestSupportingDataEdgeCases:
    """Test edge cases and error handling"""
    
    def test_invalid_pagination_parameters(self, client, auth_headers):
        """Test invalid pagination parameters"""
        # Negative startIndex
        response = client.get('/api/supporting-data/roles?startIndex=-1', headers=auth_headers)
        assert response.status_code == 400
        
        # Negative count
        response = client.get('/api/supporting-data/roles?count=-5', headers=auth_headers)
        assert response.status_code == 400
    
    def test_large_pagination_count(self, client, auth_headers):
        """Test requesting more items than exist"""
        response = client.get('/api/supporting-data/roles?startIndex=1&count=1000', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should return all available items
        assert data['schemas'] == ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
        assert data['itemsPerPage'] == 7
        assert len(data['Resources']) == 7
    
    def test_pagination_beyond_results(self, client, auth_headers):
        """Test pagination starting beyond available results"""
        response = client.get('/api/supporting-data/roles?startIndex=100&count=10', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['schemas'] == ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
        assert data['totalResults'] == 7
        assert data['itemsPerPage'] == 0
        assert len(data['Resources']) == 0
    
    def test_content_type_json(self, client, auth_headers):
        """Test that responses have correct content type"""
        endpoints = [
            '/api/supporting-data/roles',
            '/api/supporting-data/departments'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.content_type == 'application/json'


# Made with Bob