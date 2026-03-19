"""
Supporting Data API Endpoints - READ-ONLY
Non-SCIM APIs for Roles and Departments lookup

IMPORTANT:
- These are NOT SCIM endpoints
- These are NOT under /scim/v2/
- These are READ-ONLY (GET paginated list only)
- Data is predefined and immutable
- No individual GET by ID, POST, PATCH, or DELETE operations
"""

from typing import Dict, Any, Optional


class SupportingDataEndpoints:
    """
    Read-only API endpoints for supporting data
    
    Endpoints:
    - GET /api/supporting-data/roles (paginated list only)
    - GET /api/supporting-data/departments (paginated list only)
    
    These endpoints provide lookup data for IAM operations.
    They do NOT support individual retrieval, create, update, or delete operations.
    """
    
    def __init__(self, supporting_data_repository):
        """
        Initialize with supporting data repository
        
        Args:
            supporting_data_repository: Repository containing predefined roles and departments
        """
        self.repo = supporting_data_repository
    
    # ==================== ROLES API ====================
    
    def list_roles(self, start_index: int = 1, count: int = 100) -> tuple[Dict[str, Any], int]:
        """
        GET /api/supporting-data/roles
        
        List all predefined roles with pagination
        
        Args:
            start_index: 1-based index for pagination (default: 1)
            count: Number of results per page (default: 100)
        
        Returns:
            Tuple of (response_body, status_code)
        
        Response Format (SCIM-like):
        {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": 7,
            "startIndex": 1,
            "itemsPerPage": 7,
            "Resources": [
                {
                    "id": "role-admin",
                    "name": "Administrator",
                    "description": "Full system access"
                }
            ]
        }
        """
        try:
            # Validate pagination parameters
            if start_index < 1:
                return self._error_response(400, "startIndex must be >= 1"), 400
            if count < 0:
                return self._error_response(400, "count must be >= 0"), 400
            
            # Get all roles
            all_roles = self.repo.get_all_roles()
            
            # Calculate pagination
            total_results = len(all_roles)
            start_idx = start_index - 1  # Convert to 0-based
            end_idx = start_idx + count
            
            # Get page of results
            page_roles = all_roles[start_idx:end_idx]
            
            # Build response (SCIM-like format)
            response = {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "totalResults": total_results,
                "startIndex": start_index,
                "itemsPerPage": len(page_roles),
                "Resources": [role.to_dict() for role in page_roles]
            }
            
            return response, 200
            
        except Exception as e:
            return self._error_response(500, f"Internal server error: {str(e)}"), 500
    
    # ==================== DEPARTMENTS API ====================
    
    def list_departments(self, start_index: int = 1, count: int = 100) -> tuple[Dict[str, Any], int]:
        """
        GET /api/supporting-data/departments
        
        List all predefined departments with pagination
        
        Args:
            start_index: 1-based index for pagination (default: 1)
            count: Number of results per page (default: 100)
        
        Returns:
            Tuple of (response_body, status_code)
        
        Response Format (SCIM-like):
        {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": 10,
            "startIndex": 1,
            "itemsPerPage": 10,
            "Resources": [
                {
                    "id": "dept-eng",
                    "name": "Engineering"
                }
            ]
        }
        """
        try:
            # Validate pagination parameters
            if start_index < 1:
                return self._error_response(400, "startIndex must be >= 1"), 400
            if count < 0:
                return self._error_response(400, "count must be >= 0"), 400
            
            # Get all departments
            all_departments = self.repo.get_all_departments()
            
            # Calculate pagination
            total_results = len(all_departments)
            start_idx = start_index - 1  # Convert to 0-based
            end_idx = start_idx + count
            
            # Get page of results
            page_departments = all_departments[start_idx:end_idx]
            
            # Build response (SCIM-like format)
            response = {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "totalResults": total_results,
                "startIndex": start_index,
                "itemsPerPage": len(page_departments),
                "Resources": [dept.to_dict() for dept in page_departments]
            }
            
            return response, 200
            
        except Exception as e:
            return self._error_response(500, f"Internal server error: {str(e)}"), 500
    
    # ==================== HELPER METHODS ====================
    
    def _error_response(self, status: int, message: str) -> Dict[str, Any]:
        """
        Create error response
        
        Note: This is NOT a SCIM error response.
        Supporting data APIs use simple JSON error format.
        """
        return {
            "error": {
                "status": status,
                "message": message
            }
        }
    
    # ==================== VALIDATION HELPERS ====================
    
    def validate_role_reference(self, role_name: str) -> bool:
        """
        Validate that a role name exists in predefined set
        
        This can be used by SCIM endpoints to validate role assignments
        before creating SCIM Groups.
        
        Args:
            role_name: Role name to validate
        
        Returns:
            True if role exists, False otherwise
        """
        return self.repo.validate_role_name(role_name)
    
    def validate_department_reference(self, department_name: str) -> bool:
        """
        Validate that a department name exists in predefined set
        
        This can be used by SCIM User endpoints to validate department
        attribute before creating/updating users.
        
        Args:
            department_name: Department name to validate
        
        Returns:
            True if department exists, False otherwise
        """
        return self.repo.validate_department_name(department_name)
    
    def get_role_by_scim_group_name(self, group_name: str) -> Optional[Dict[str, Any]]:
        """
        Map SCIM Group displayName to Role
        
        This helper allows mapping between SCIM Groups and Role supporting data.
        
        Args:
            group_name: SCIM Group displayName
        
        Returns:
            Role dict if found, None otherwise
        """
        role = self.repo.get_role_by_name(group_name)
        return role.to_dict() if role else None
    
    def get_department_by_scim_user_department(self, department_name: str) -> Optional[Dict[str, Any]]:
        """
        Map SCIM User department attribute to Department
        
        This helper allows mapping between SCIM User department and Department supporting data.
        
        Args:
            department_name: SCIM User department value
        
        Returns:
            Department dict if found, None otherwise
        """
        department = self.repo.get_department_by_name(department_name)
        return department.to_dict() if department else None


# ==================== IMPORTANT NOTES ====================
"""
INTEGRATION WITH SCIM:

1. ROLES → SCIM GROUPS
   - Roles are exposed via /api/supporting-data/roles (paginated list only)
   - SCIM Groups are managed via /scim/v2/Groups
   - Roles map to Groups by name (Role.name == Group.displayName)
   - IAM products can:
     a) Query /api/supporting-data/roles to get available roles
     b) Create SCIM Groups with matching displayName
     c) Assign users to those Groups

2. DEPARTMENTS → SCIM USER ATTRIBUTE
   - Departments are exposed via /api/supporting-data/departments (paginated list only)
   - SCIM Users have a department attribute
   - Departments map to User.department by name
   - IAM products can:
     a) Query /api/supporting-data/departments to get valid departments
     b) Set User.department to one of those values
     c) Validate department values before creating/updating users

3. NO SCIM MODIFICATIONS
   - SCIM User schema: UNCHANGED
   - SCIM Group schema: UNCHANGED
   - SCIM endpoints: UNCHANGED
   - SCIM PATCH logic: UNCHANGED
   - SCIM discovery: UNCHANGED

4. AUTHENTICATION
   - Supporting data APIs use same auth as SCIM
   - Require Bearer token with supportingdata.read scope
   - No write scopes (supportingdata.write) exist

5. READ-ONLY ENFORCEMENT
   - Only GET paginated list endpoints supported
   - No individual GET by ID
   - No POST, PATCH, PUT, or DELETE operations
   - Attempting unsupported operations returns 405 Method Not Allowed
"""

# Made with Bob
