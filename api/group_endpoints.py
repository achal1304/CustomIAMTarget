"""
SCIM 2.0 Group Endpoints Implementation
Compliant with RFC 7644 (SCIM Protocol)
"""

from typing import Dict, Any, List, Optional
from models.group_model import Group, ValidationError


class SCIMError(Exception):
    """SCIM protocol error"""
    
    def __init__(self, status: int, scim_type: Optional[str] = None, detail: Optional[str] = None):
        self.status = status
        self.scim_type = scim_type
        self.detail = detail
        super().__init__(detail)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to SCIM error response"""
        error = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "status": str(self.status)
        }
        if self.scim_type:
            error["scimType"] = self.scim_type
        if self.detail:
            error["detail"] = self.detail
        return error


class GroupEndpoints:
    """
    SCIM 2.0 Group Resource Endpoints
    
    Implements:
    - POST /Groups - Create group
    - GET /Groups/{id} - Retrieve group
    - GET /Groups - List groups
    - PATCH /Groups/{id} - Update group (add/remove members)
    - DELETE /Groups/{id} - Delete group
    """
    
    def __init__(self, group_repository, user_repository):
        """
        Initialize endpoints with repositories
        
        Args:
            group_repository: Repository for group persistence
            user_repository: Repository for user persistence
        """
        self.group_repo = group_repository
        self.user_repo = user_repository
    
    def create_group(self, request_body: Dict[str, Any], base_url: str) -> tuple[Dict[str, Any], int]:
        """
        POST /Groups
        Create a new group
        
        Args:
            request_body: SCIM Group resource
            base_url: Base URL for location header
        
        Returns:
            Tuple of (response_body, status_code)
        """
        try:
            # Validate schemas
            schemas = request_body.get("schemas", [])
            if Group.CORE_SCHEMA not in schemas:
                raise SCIMError(400, "invalidValue", "Missing required schema")
            
            # Create group from request
            group = Group.from_dict(request_body, self.user_repo)
            
            # Check displayName uniqueness (optional but recommended)
            existing = self.group_repo.get_by_display_name(group.display_name)
            if existing:
                raise SCIMError(409, "uniqueness", f"Group with displayName '{group.display_name}' already exists")
            
            # Save group
            self.group_repo.save(group)
            
            # Update user group memberships
            for member in group.members:
                user = self.user_repo.get_by_id(member.value)
                if user:
                    user.add_group_membership(group.id, group.display_name)
                    self.user_repo.save(user)
            
            # Return created group
            response = group.to_dict()
            return response, 201
            
        except ValidationError as e:
            raise SCIMError(400, "invalidValue", str(e))
        except SCIMError:
            raise
        except Exception as e:
            raise SCIMError(500, None, f"Internal server error: {str(e)}")
    
    def get_group(self, group_id: str) -> tuple[Dict[str, Any], int]:
        """
        GET /Groups/{id}
        Retrieve a single group
        
        Args:
            group_id: Group identifier
        
        Returns:
            Tuple of (response_body, status_code)
        """
        try:
            group = self.group_repo.get_by_id(group_id)
            if not group:
                raise SCIMError(404, None, f"Group with id '{group_id}' not found")
            
            response = group.to_dict()
            return response, 200
            
        except SCIMError:
            raise
        except Exception as e:
            raise SCIMError(500, None, f"Internal server error: {str(e)}")
    
    def list_groups(self, filter_str: Optional[str] = None, start_index: int = 1,
                    count: int = 100) -> tuple[Dict[str, Any], int]:
        """
        GET /Groups
        List groups with pagination
        
        Args:
            filter_str: SCIM filter expression (optional, basic support)
            start_index: 1-based index for pagination (default: 1)
            count: Number of results per page (default: 100)
        
        Returns:
            Tuple of (response_body, status_code)
        """
        try:
            # Validate pagination parameters
            if start_index < 1:
                raise SCIMError(400, "invalidValue", "startIndex must be >= 1")
            if count < 0:
                raise SCIMError(400, "invalidValue", "count must be >= 0")
            
            # Get all groups
            all_groups = self.group_repo.get_all()
            
            # Apply basic filter if provided (displayName eq "value")
            if filter_str:
                filtered_groups = []
                for group in all_groups:
                    # Simple filter support for displayName
                    if 'displayName eq' in filter_str:
                        value = filter_str.split('eq')[1].strip().strip('"')
                        if group.display_name.lower() == value.lower():
                            filtered_groups.append(group)
                    else:
                        filtered_groups.append(group)
            else:
                filtered_groups = all_groups
            
            # Calculate pagination
            total_results = len(filtered_groups)
            start_idx = start_index - 1  # Convert to 0-based
            end_idx = start_idx + count
            
            # Get page of results
            page_groups = filtered_groups[start_idx:end_idx]
            
            # Build response
            response = {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "totalResults": total_results,
                "startIndex": start_index,
                "itemsPerPage": len(page_groups),
                "Resources": [group.to_dict() for group in page_groups]
            }
            
            return response, 200
            
        except SCIMError:
            raise
        except Exception as e:
            raise SCIMError(500, None, f"Internal server error: {str(e)}")
    
    def patch_group(self, group_id: str, request_body: Dict[str, Any]) -> tuple[Dict[str, Any], int]:
        """
        PATCH /Groups/{id}
        Update group using SCIM PatchOp (RFC 7644 Section 3.5.2)
        
        Primary use case: Add/remove members
        
        Supported operations:
        - add: Add members to group
        - remove: Remove members from group
        - replace: Replace group attributes
        
        Args:
            group_id: Group identifier
            request_body: SCIM PatchOp request
        
        Returns:
            Tuple of (response_body, status_code)
        """
        try:
            # Validate schemas
            schemas = request_body.get("schemas", [])
            if "urn:ietf:params:scim:api:messages:2.0:PatchOp" not in schemas:
                raise SCIMError(400, "invalidValue", "Missing PatchOp schema")
            
            # Get group
            group = self.group_repo.get_by_id(group_id)
            if not group:
                raise SCIMError(404, None, f"Group with id '{group_id}' not found")
            
            # Process operations
            operations = request_body.get("Operations", [])
            if not operations:
                raise SCIMError(400, "invalidValue", "Operations array is required")
            
            for operation in operations:
                op = operation.get("op", "").lower()
                path = operation.get("path", "")
                value = operation.get("value")
                
                if op == "add":
                    self._apply_add_operation(group, path, value)
                elif op == "remove":
                    self._apply_remove_operation(group, path, value)
                elif op == "replace":
                    self._apply_replace_operation(group, path, value)
                else:
                    raise SCIMError(400, "invalidValue", f"Unsupported operation: {op}")
            
            # Save updated group
            self.group_repo.save(group)
            
            # Return updated group
            response = group.to_dict()
            return response, 200
            
        except ValidationError as e:
            raise SCIMError(400, "invalidValue", str(e))
        except SCIMError:
            raise
        except Exception as e:
            raise SCIMError(500, None, f"Internal server error: {str(e)}")
    
    def _apply_add_operation(self, group, path: str, value: Any):
        """
        Apply PATCH add operation
        
        Examples:
        - Add single member: {"op": "add", "path": "members", "value": {"value": "user-id"}}
        - Add multiple members: {"op": "add", "path": "members", "value": [{"value": "id1"}, {"value": "id2"}]}
        """
        if path == "members" or not path:
            # Add members
            members_to_add = value if isinstance(value, list) else [value]
            
            for member_data in members_to_add:
                if isinstance(member_data, dict):
                    user_id = member_data.get("value")
                    display_name = member_data.get("display")
                else:
                    user_id = member_data
                    display_name = None
                
                if user_id:
                    # Add member to group
                    added = group.add_member(user_id, display_name, self.user_repo)
                    
                    # Update user's group membership
                    if added:
                        user = self.user_repo.get_by_id(user_id)
                        if user:
                            user.add_group_membership(group.id, group.display_name)
                            self.user_repo.save(user)
        elif path == "displayName":
            group.display_name = value
            group._update_last_modified()
    
    def _apply_remove_operation(self, group, path: str, value: Any):
        """
        Apply PATCH remove operation
        
        Examples:
        - Remove by path: {"op": "remove", "path": "members[value eq \"user-id\"]"}
        - Remove with value: {"op": "remove", "path": "members", "value": {"value": "user-id"}}
        """
        if "members" in path:
            # Extract user ID from path or value
            user_id = None
            
            # Parse path like: members[value eq "user-id"]
            if "[value eq" in path:
                import re
                match = re.search(r'value eq "([^"]+)"', path)
                if match:
                    user_id = match.group(1)
            elif value:
                if isinstance(value, dict):
                    user_id = value.get("value")
                elif isinstance(value, list):
                    # Remove multiple members
                    for member_data in value:
                        if isinstance(member_data, dict):
                            uid = member_data.get("value")
                            if uid:
                                self._remove_member_from_group(group, uid)
                    return
                else:
                    user_id = value
            
            if user_id:
                self._remove_member_from_group(group, user_id)
    
    def _apply_replace_operation(self, group, path: str, value: Any):
        """Apply PATCH replace operation"""
        if path == "displayName":
            group.display_name = value
            group._update_last_modified()
        elif path == "members":
            # Replace all members
            # First, remove all existing members
            old_member_ids = group.get_member_ids()
            for user_id in old_member_ids:
                self._remove_member_from_group(group, user_id)
            
            # Then add new members
            self._apply_add_operation(group, "members", value)
    
    def _remove_member_from_group(self, group, user_id: str):
        """Helper to remove a member from group and update user"""
        removed = group.remove_member(user_id)
        
        # Update user's group membership
        if removed:
            user = self.user_repo.get_by_id(user_id)
            if user:
                user.remove_group_membership(group.id)
                self.user_repo.save(user)
    
    def delete_group(self, group_id: str) -> tuple[None, int]:
        """
        DELETE /Groups/{id}
        Delete a group
        
        Args:
            group_id: Group identifier
        
        Returns:
            Tuple of (None, status_code)
        """
        try:
            group = self.group_repo.get_by_id(group_id)
            if not group:
                raise SCIMError(404, None, f"Group with id '{group_id}' not found")
            
            # Remove group membership from all users
            for member in group.members:
                user = self.user_repo.get_by_id(member.value)
                if user:
                    user.remove_group_membership(group_id)
                    self.user_repo.save(user)
            
            # Delete group
            self.group_repo.delete(group_id)
            
            return None, 204
            
        except SCIMError:
            raise
        except Exception as e:
            raise SCIMError(500, None, f"Internal server error: {str(e)}")

# Made with Bob
