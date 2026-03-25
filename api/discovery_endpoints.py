"""
SCIM 2.0 Discovery Endpoints
Required by RFC 7644 Section 4

Implements:
- /ServiceProviderConfig - Provider capabilities and features
- /Schemas - Supported SCIM schemas
- /ResourceTypes - Supported resource types
"""

from typing import Dict, Any, List


class DiscoveryEndpoints:
    """
    SCIM 2.0 Discovery Endpoints
    
    These endpoints provide metadata about the SCIM service provider's
    capabilities, supported schemas, and resource types.
    """
    
    def __init__(self, base_url: str = "https://example.com/scim/v2"):
        """
        Initialize discovery endpoints
        
        Args:
            base_url: Base URL of the SCIM service provider
        """
        self.base_url = base_url.rstrip('/')
    
    def get_service_provider_config(self) -> tuple[Dict[str, Any], int]:
        """
        GET /ServiceProviderConfig
        
        Returns the service provider's configuration and capabilities
        per RFC 7644 Section 5
        
        Returns:
            Tuple of (response_body, status_code)
        """
        config = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
            "documentationUri": f"{self.base_url}/docs",
            "patch": {
                "supported": True
            },
            "bulk": {
                "supported": False,
                "maxOperations": 0,
                "maxPayloadSize": 0
            },
            "filter": {
                "supported": True,
                "maxResults": 1000
            },
            "changePassword": {
                "supported": False
            },
            "sort": {
                "supported": False
            },
            "etag": {
                "supported": True
            },
            "authenticationSchemes": [
                {
                    "type": "oauthbearertoken",
                    "name": "OAuth Bearer Token",
                    "description": "Authentication scheme using the OAuth Bearer Token Standard",
                    "specUri": "https://tools.ietf.org/html/rfc6750",
                    "documentationUri": f"{self.base_url}/docs/auth",
                    "primary": True
                }
            ],
            "meta": {
                "resourceType": "ServiceProviderConfig",
                "location": f"{self.base_url}/ServiceProviderConfig"
            }
        }
        
        return config, 200
    
    def get_schemas(self) -> tuple[Dict[str, Any], int]:
        """
        GET /Schemas
        
        Returns all supported SCIM schemas
        per RFC 7644 Section 4
        
        Returns:
            Tuple of (response_body, status_code)
        """
        schemas = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": 4,
            "startIndex": 1,
            "itemsPerPage": 4,
            "Resources": [
                self._get_user_schema(),
                self._get_enterprise_user_schema(),
                self._get_custom_user_schema(),
                self._get_group_schema()
            ]
        }
        
        return schemas, 200
    
    def get_schema(self, schema_id: str) -> tuple[Dict[str, Any], int]:
        """
        GET /Schemas/{id}
        
        Returns a specific SCIM schema
        
        Args:
            schema_id: Schema identifier (e.g., urn:ietf:params:scim:schemas:core:2.0:User)
        
        Returns:
            Tuple of (response_body, status_code)
        """
        if schema_id == "urn:ietf:params:scim:schemas:core:2.0:User":
            return self._get_user_schema(), 200
        elif schema_id == "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User":
            return self._get_enterprise_user_schema(), 200
        elif schema_id == "urn:ietf:params:scim:schemas:extension:custom:2.0:User":
            return self._get_custom_user_schema(), 200
        elif schema_id == "urn:ietf:params:scim:schemas:core:2.0:Group":
            return self._get_group_schema(), 200
        else:
            error = {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
                "status": "404",
                "detail": f"Schema '{schema_id}' not found"
            }
            return error, 404
    
    def get_resource_types(self) -> tuple[Dict[str, Any], int]:
        """
        GET /ResourceTypes
        
        Returns all supported resource types
        per RFC 7644 Section 6
        
        Returns:
            Tuple of (response_body, status_code)
        """
        resource_types = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": 2,
            "startIndex": 1,
            "itemsPerPage": 2,
            "Resources": [
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
                    "id": "User",
                    "name": "User",
                    "endpoint": "/Users",
                    "description": "SCIM 2.0 User Resource",
                    "schema": "urn:ietf:params:scim:schemas:core:2.0:User",
                    "schemaExtensions": [
                        {
                            "schema": "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
                            "required": False
                        },
                        {
                            "schema": "urn:ietf:params:scim:schemas:extension:custom:2.0:User",
                            "required": False
                        }
                    ],
                    "meta": {
                        "resourceType": "ResourceType",
                        "location": f"{self.base_url}/ResourceTypes/User"
                    }
                },
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
                    "id": "Group",
                    "name": "Group",
                    "endpoint": "/Groups",
                    "description": "SCIM 2.0 Group Resource",
                    "schema": "urn:ietf:params:scim:schemas:core:2.0:Group",
                    "meta": {
                        "resourceType": "ResourceType",
                        "location": f"{self.base_url}/ResourceTypes/Group"
                    }
                }
            ]
        }
        
        return resource_types, 200
    
    def get_resource_type(self, resource_type_id: str) -> tuple[Dict[str, Any], int]:
        """
        GET /ResourceTypes/{id}
        
        Returns a specific resource type
        
        Args:
            resource_type_id: Resource type identifier (User or Group)
        
        Returns:
            Tuple of (response_body, status_code)
        """
        if resource_type_id == "User":
            resource_type = {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
                "id": "User",
                "name": "User",
                "endpoint": "/Users",
                "description": "SCIM 2.0 User Resource",
                "schema": "urn:ietf:params:scim:schemas:core:2.0:User",
                "schemaExtensions": [
                    {
                        "schema": "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
                        "required": False
                    },
                    {
                        "schema": "urn:ietf:params:scim:schemas:extension:custom:2.0:User",
                        "required": False
                    }
                ],
                "meta": {
                    "resourceType": "ResourceType",
                    "location": f"{self.base_url}/ResourceTypes/User"
                }
            }
            return resource_type, 200
        elif resource_type_id == "Group":
            resource_type = {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
                "id": "Group",
                "name": "Group",
                "endpoint": "/Groups",
                "description": "SCIM 2.0 Group Resource",
                "schema": "urn:ietf:params:scim:schemas:core:2.0:Group",
                "meta": {
                    "resourceType": "ResourceType",
                    "location": f"{self.base_url}/ResourceTypes/Group"
                }
            }
            return resource_type, 200
        else:
            error = {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
                "status": "404",
                "detail": f"ResourceType '{resource_type_id}' not found"
            }
            return error, 404
    
    def _get_user_schema(self) -> Dict[str, Any]:
        """Get User schema definition (minimal attributes only)"""
        return {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Schema"],
            "id": "urn:ietf:params:scim:schemas:core:2.0:User",
            "name": "User",
            "description": "SCIM 2.0 User Resource - Minimal Implementation",
            "attributes": [
                {
                    "name": "id",
                    "type": "string",
                    "multiValued": False,
                    "description": "Unique identifier for the User",
                    "required": True,
                    "caseExact": True,
                    "mutability": "readOnly",
                    "returned": "always",
                    "uniqueness": "server"
                },
                {
                    "name": "userName",
                    "type": "string",
                    "multiValued": False,
                    "description": "Unique identifier for the User",
                    "required": True,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "always",
                    "uniqueness": "server"
                },
                {
                    "name": "externalId",
                    "type": "string",
                    "multiValued": False,
                    "description": "Identifier from the provisioning client",
                    "required": False,
                    "caseExact": True,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none"
                },
                {
                    "name": "name",
                    "type": "complex",
                    "multiValued": False,
                    "description": "The components of the user's name",
                    "required": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none",
                    "subAttributes": [
                        {
                            "name": "givenName",
                            "type": "string",
                            "multiValued": False,
                            "description": "The given name of the User",
                            "required": False,
                            "caseExact": False,
                            "mutability": "readWrite",
                            "returned": "default",
                            "uniqueness": "none"
                        },
                        {
                            "name": "familyName",
                            "type": "string",
                            "multiValued": False,
                            "description": "The family name of the User",
                            "required": False,
                            "caseExact": False,
                            "mutability": "readWrite",
                            "returned": "default",
                            "uniqueness": "none"
                        }
                    ]
                },
                {
                    "name": "emails",
                    "type": "complex",
                    "multiValued": True,
                    "description": "Email addresses for the user",
                    "required": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none"
                },
                {
                    "name": "active",
                    "type": "boolean",
                    "multiValued": False,
                    "description": "Indicates whether the user's account is active",
                    "required": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none"
                },
                {
                    "name": "department",
                    "type": "string",
                    "multiValued": False,
                    "description": "The organizational department",
                    "required": False,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none"
                },
                {
                    "name": "gender",
                    "type": "string",
                    "multiValued": False,
                    "description": "The user's gender",
                    "required": False,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none"
                },
                {
                    "name": "groups",
                    "type": "complex",
                    "multiValued": True,
                    "description": "Groups to which the user belongs",
                    "required": False,
                    "mutability": "readOnly",
                    "returned": "default",
                    "uniqueness": "none"
                }
            ],
            "meta": {
                "resourceType": "Schema",
                "location": f"{self.base_url}/Schemas/urn:ietf:params:scim:schemas:core:2.0:User"
            }
        }
    
    def _get_enterprise_user_schema(self) -> Dict[str, Any]:
        """Get Enterprise User extension schema"""
        return {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Schema"],
            "id": "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
            "name": "EnterpriseUser",
            "description": "SCIM 2.0 Enterprise User Extension",
            "attributes": [
                {
                    "name": "employeeNumber",
                    "type": "string",
                    "multiValued": False,
                    "description": "Numeric or alphanumeric identifier assigned to a person, typically based on order of hire or association with an organization",
                    "required": False,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none"
                },
                {
                    "name": "department",
                    "type": "string",
                    "multiValued": False,
                    "description": "Identifies the name of a department",
                    "required": False,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none"
                },
                {
                    "name": "manager",
                    "type": "complex",
                    "multiValued": False,
                    "description": "The user's manager",
                    "required": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none",
                    "subAttributes": [
                        {
                            "name": "value",
                            "type": "string",
                            "multiValued": False,
                            "description": "The id of the manager",
                            "required": True,
                            "caseExact": True,
                            "mutability": "readWrite",
                            "returned": "default",
                            "uniqueness": "none"
                        },
                        {
                            "name": "$ref",
                            "type": "reference",
                            "referenceTypes": ["User"],
                            "multiValued": False,
                            "description": "The URI of the manager",
                            "required": False,
                            "caseExact": True,
                            "mutability": "readWrite",
                            "returned": "default",
                            "uniqueness": "none"
                        },
                        {
                            "name": "displayName",
                            "type": "string",
                            "multiValued": False,
                            "description": "The displayName of the manager",
                            "required": False,
                            "caseExact": False,
                            "mutability": "readWrite",
                            "returned": "default",
                            "uniqueness": "none"
                        }
                    ]
                }
            ],
            "meta": {
                "resourceType": "Schema",
                "location": f"{self.base_url}/Schemas/urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
            }
        }
    
    def _get_custom_user_schema(self) -> Dict[str, Any]:
        """Get Custom User extension schema definition"""
        return {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Schema"],
            "id": "urn:ietf:params:scim:schemas:extension:custom:2.0:User",
            "name": "CustomUser",
            "description": "Custom User Extension - Contains demographic and organization-specific attributes not defined in SCIM core schema",
            "attributes": [
                {
                    "name": "gender",
                    "type": "string",
                    "multiValued": False,
                    "description": "The user's gender (optional demographic field)",
                    "required": False,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none"
                }
            ],
            "meta": {
                "resourceType": "Schema",
                "location": f"{self.base_url}/Schemas/urn:ietf:params:scim:schemas:extension:custom:2.0:User"
            }
        }
    
    def _get_group_schema(self) -> Dict[str, Any]:
        """Get Group schema definition"""
        return {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Schema"],
            "id": "urn:ietf:params:scim:schemas:core:2.0:Group",
            "name": "Group",
            "description": "SCIM 2.0 Group Resource - Minimal Implementation",
            "attributes": [
                {
                    "name": "id",
                    "type": "string",
                    "multiValued": False,
                    "description": "Unique identifier for the Group",
                    "required": True,
                    "caseExact": True,
                    "mutability": "readOnly",
                    "returned": "always",
                    "uniqueness": "server"
                },
                {
                    "name": "displayName",
                    "type": "string",
                    "multiValued": False,
                    "description": "A human-readable name for the Group",
                    "required": True,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "always",
                    "uniqueness": "none"
                },
                {
                    "name": "externalId",
                    "type": "string",
                    "multiValued": False,
                    "description": "Identifier from the provisioning client",
                    "required": False,
                    "caseExact": True,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none"
                },
                {
                    "name": "members",
                    "type": "complex",
                    "multiValued": True,
                    "description": "A list of members of the Group",
                    "required": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none",
                    "subAttributes": [
                        {
                            "name": "value",
                            "type": "string",
                            "multiValued": False,
                            "description": "Identifier of the member",
                            "required": True,
                            "caseExact": True,
                            "mutability": "readWrite",
                            "returned": "default",
                            "uniqueness": "none"
                        },
                        {
                            "name": "$ref",
                            "type": "reference",
                            "referenceTypes": ["User"],
                            "multiValued": False,
                            "description": "The URI of the member",
                            "required": False,
                            "caseExact": True,
                            "mutability": "readWrite",
                            "returned": "default",
                            "uniqueness": "none"
                        },
                        {
                            "name": "type",
                            "type": "string",
                            "multiValued": False,
                            "description": "Type of member",
                            "required": False,
                            "caseExact": False,
                            "mutability": "readWrite",
                            "returned": "default",
                            "uniqueness": "none",
                            "canonicalValues": ["User"]
                        }
                    ]
                }
            ],
            "meta": {
                "resourceType": "Schema",
                "location": f"{self.base_url}/Schemas/urn:ietf:params:scim:schemas:core:2.0:Group"
            }
        }

# Made with Bob
