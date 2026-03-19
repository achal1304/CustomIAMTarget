"""
Automated Tests for SCIM 2.0 Discovery Endpoints
Tests /scim/v2/ServiceProviderConfig, /scim/v2/ResourceTypes, /scim/v2/Schemas

Framework: pytest + Flask test client
Target: SCIM 2.0 Discovery endpoints
"""

import pytest
import json
from app import app


@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestServiceProviderConfig:
    """Test GET /scim/v2/ServiceProviderConfig"""
    
    def test_get_service_provider_config(self, client):
        """Test retrieving service provider configuration"""
        response = client.get('/scim/v2/ServiceProviderConfig')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify required fields
        assert 'schemas' in data
        assert 'urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig' in data['schemas']
        
        # Verify feature support
        assert 'patch' in data
        assert 'bulk' in data
        assert 'filter' in data
        assert 'changePassword' in data
        assert 'sort' in data
        assert 'etag' in data
        
        # Verify authentication schemes
        assert 'authenticationSchemes' in data
        assert isinstance(data['authenticationSchemes'], list)
    
    def test_service_provider_config_structure(self, client):
        """Test service provider config has correct structure"""
        response = client.get('/scim/v2/ServiceProviderConfig')
        data = response.get_json()
        
        # Check patch support
        assert data['patch']['supported'] is True
        
        # Check bulk support
        assert 'supported' in data['bulk']
        assert 'maxOperations' in data['bulk']
        assert 'maxPayloadSize' in data['bulk']
        
        # Check filter support
        assert 'supported' in data['filter']
        assert 'maxResults' in data['filter']


class TestResourceTypes:
    """Test GET /scim/v2/ResourceTypes"""
    
    def test_get_resource_types(self, client):
        """Test retrieving resource types"""
        response = client.get('/scim/v2/ResourceTypes')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should be a list response
        assert 'schemas' in data
        assert 'urn:ietf:params:scim:api:messages:2.0:ListResponse' in data['schemas']
        assert 'Resources' in data
        assert isinstance(data['Resources'], list)
        
        # Should have at least User and Group resource types
        resource_names = [r['name'] for r in data['Resources']]
        assert 'User' in resource_names
        assert 'Group' in resource_names
    
    def test_get_user_resource_type(self, client):
        """Test retrieving User resource type"""
        response = client.get('/scim/v2/ResourceTypes/User')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['name'] == 'User'
        assert data['endpoint'] == '/Users'
        assert 'urn:ietf:params:scim:schemas:core:2.0:User' in data['schema']
        assert 'schemaExtensions' in data
    
    def test_get_group_resource_type(self, client):
        """Test retrieving Group resource type"""
        response = client.get('/scim/v2/ResourceTypes/Group')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['name'] == 'Group'
        assert data['endpoint'] == '/Groups'
        assert data['schema'] == 'urn:ietf:params:scim:schemas:core:2.0:Group'


class TestSchemas:
    """Test GET /scim/v2/Schemas"""
    
    def test_get_all_schemas(self, client):
        """Test retrieving all schemas"""
        response = client.get('/scim/v2/Schemas')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should be a list response
        assert 'schemas' in data
        assert 'urn:ietf:params:scim:api:messages:2.0:ListResponse' in data['schemas']
        assert 'Resources' in data
        assert isinstance(data['Resources'], list)
        
        # Should have core schemas
        schema_ids = [s['id'] for s in data['Resources']]
        assert 'urn:ietf:params:scim:schemas:core:2.0:User' in schema_ids
        assert 'urn:ietf:params:scim:schemas:core:2.0:Group' in schema_ids
    
    def test_get_user_schema(self, client):
        """Test retrieving User schema"""
        response = client.get('/scim/v2/Schemas/urn:ietf:params:scim:schemas:core:2.0:User')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['id'] == 'urn:ietf:params:scim:schemas:core:2.0:User'
        assert data['name'] == 'User'
        assert 'attributes' in data
        assert isinstance(data['attributes'], list)
        
        # Check for required attributes
        attr_names = [a['name'] for a in data['attributes']]
        assert 'userName' in attr_names
        assert 'name' in attr_names
        assert 'emails' in attr_names
    
    def test_get_group_schema(self, client):
        """Test retrieving Group schema"""
        response = client.get('/scim/v2/Schemas/urn:ietf:params:scim:schemas:core:2.0:Group')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['id'] == 'urn:ietf:params:scim:schemas:core:2.0:Group'
        assert data['name'] == 'Group'
        assert 'attributes' in data
        
        # Check for required attributes
        attr_names = [a['name'] for a in data['attributes']]
        assert 'displayName' in attr_names
        assert 'members' in attr_names
    
    def test_get_enterprise_user_extension_schema(self, client):
        """Test retrieving Enterprise User extension schema"""
        response = client.get('/scim/v2/Schemas/urn:ietf:params:scim:schemas:extension:enterprise:2.0:User')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['id'] == 'urn:ietf:params:scim:schemas:extension:enterprise:2.0:User'
        assert 'attributes' in data
        
        # Check for enterprise attributes
        attr_names = [a['name'] for a in data['attributes']]
        assert 'employeeNumber' in attr_names
        assert 'department' in attr_names
        assert 'manager' in attr_names
    
    def test_get_nonexistent_schema(self, client):
        """Test retrieving non-existent schema"""
        response = client.get('/scim/v2/Schemas/urn:invalid:schema')
        
        assert response.status_code == 404


class TestDiscoveryEndpointsIntegration:
    """Integration tests for discovery endpoints"""
    
    def test_discovery_endpoints_consistency(self, client):
        """Test that discovery endpoints are consistent with each other"""
        # Get resource types
        rt_response = client.get('/scim/v2/ResourceTypes')
        resource_types = rt_response.get_json()['Resources']
        
        # Get schemas
        schema_response = client.get('/scim/v2/Schemas')
        schemas = schema_response.get_json()['Resources']
        
        # Verify each resource type references valid schemas
        schema_ids = {s['id'] for s in schemas}
        
        for rt in resource_types:
            assert rt['schema'] in schema_ids, \
                f"Resource type {rt['name']} references unknown schema {rt['schema']}"
            
            # Check schema extensions
            for ext in rt.get('schemaExtensions', []):
                assert ext['schema'] in schema_ids, \
                    f"Resource type {rt['name']} references unknown extension {ext['schema']}"
    
    def test_all_discovery_endpoints_accessible(self, client):
        """Test that all discovery endpoints are accessible"""
        endpoints = [
            '/scim/v2/ServiceProviderConfig',
            '/scim/v2/ResourceTypes',
            '/scim/v2/Schemas'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, \
                f"Discovery endpoint {endpoint} returned {response.status_code}"
            assert response.content_type == 'application/json'


# Made with Bob