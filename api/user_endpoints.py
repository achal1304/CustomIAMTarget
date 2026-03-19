"""
SCIM 2.0 User Endpoints Implementation
Compliant with RFC 7644 (SCIM Protocol)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re
from models.user_model import User, ValidationError, Email, Name, Manager


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


class FilterParser:
    """Parse SCIM filter expressions (RFC 7644 Section 3.4.2.2)"""
    
    @staticmethod
    def parse_simple_filter(filter_str: str) -> Dict[str, Any]:
        """
        Parse simple filter expressions like:
        - userName eq "john.doe@example.com"
        - active eq true
        - department eq "Engineering"
        
        Returns dict with: attribute, operator, value
        """
        # Remove extra whitespace
        filter_str = ' '.join(filter_str.split())
        
        # Match pattern: attribute operator value
        pattern = r'(\S+)\s+(eq|ne|co|sw|ew|gt|ge|lt|le)\s+(.+)'
        match = re.match(pattern, filter_str, re.IGNORECASE)
        
        if not match:
            raise SCIMError(400, "invalidFilter", f"Invalid filter syntax: {filter_str}")
        
        attribute = match.group(1)
        operator = match.group(2).lower()
        value_str = match.group(3).strip()
        
        # Parse value (remove quotes for strings, convert booleans)
        if value_str.startswith('"') and value_str.endswith('"'):
            value = value_str[1:-1]
        elif value_str.lower() == 'true':
            value = True
        elif value_str.lower() == 'false':
            value = False
        elif value_str.lower() == 'null':
            value = None
        else:
            try:
                value = int(value_str)
            except ValueError:
                try:
                    value = float(value_str)
                except ValueError:
                    value = value_str
        
        return {
            "attribute": attribute,
            "operator": operator,
            "value": value
        }
    
    @staticmethod
    def apply_filter(user, filter_expr: Dict[str, Any]) -> bool:
        """Apply filter expression to a user object"""
        attribute = filter_expr["attribute"]
        operator = filter_expr["operator"]
        filter_value = filter_expr["value"]
        
        # Get attribute value from user
        user_value = FilterParser._get_attribute_value(user, attribute)
        
        # Apply operator
        if operator == "eq":
            if isinstance(user_value, str) and isinstance(filter_value, str):
                return user_value.lower() == filter_value.lower()
            return user_value == filter_value
        elif operator == "ne":
            return user_value != filter_value
        elif operator == "co":  # contains
            if isinstance(user_value, str) and isinstance(filter_value, str):
                return filter_value.lower() in user_value.lower()
            return False
        elif operator == "sw":  # starts with
            if isinstance(user_value, str) and isinstance(filter_value, str):
                return user_value.lower().startswith(filter_value.lower())
            return False
        elif operator == "ew":  # ends with
            if isinstance(user_value, str) and isinstance(filter_value, str):
                return user_value.lower().endswith(filter_value.lower())
            return False
        elif operator in ["gt", "ge", "lt", "le"]:
            if user_value is None or filter_value is None:
                return False
            if operator == "gt":
                return user_value > filter_value
            elif operator == "ge":
                return user_value >= filter_value
            elif operator == "lt":
                return user_value < filter_value
            elif operator == "le":
                return user_value <= filter_value
        
        return False
    
    @staticmethod
    def _get_attribute_value(user, attribute: str):
        """Get attribute value from user object, supporting dot notation"""
        # Handle common attributes
        if attribute == "userName":
            return user.user_name
        elif attribute == "active":
            return user.active
        elif attribute == "department":
            return user.department
        elif attribute == "externalId":
            return user.external_id
        elif attribute == "id":
            return user.id
        elif attribute.startswith("name."):
            sub_attr = attribute.split(".")[1]
            if sub_attr == "givenName":
                return user.name.given_name if user.name else None
            elif sub_attr == "familyName":
                return user.name.family_name if user.name else None
        elif attribute.startswith("emails"):
            # For simplicity, check primary email
            if user.emails:
                return user.emails[0].value
        
        return None


class UserEndpoints:
    """
    SCIM 2.0 User Resource Endpoints
    
    Implements:
    - POST /Users - Create user
    - GET /Users/{id} - Retrieve user
    - GET /Users - List/search users
    - PATCH /Users/{id} - Update user
    - DELETE /Users/{id} - Delete user
    """
    
    def __init__(self, user_repository, group_repository):
        """
        Initialize endpoints with repositories
        
        Args:
            user_repository: Repository for user persistence
            group_repository: Repository for group persistence
        """
        self.user_repo = user_repository
        self.group_repo = group_repository
    
    def create_user(self, request_body: Dict[str, Any], base_url: str) -> tuple[Dict[str, Any], int]:
        """
        POST /Users
        Create a new user
        
        Args:
            request_body: SCIM User resource
            base_url: Base URL for location header
        
        Returns:
            Tuple of (response_body, status_code)
        """
        try:
            # Validate schemas
            schemas = request_body.get("schemas", [])
            if User.CORE_SCHEMA not in schemas:
                raise SCIMError(400, "invalidValue", "Missing required schema")
            
            # Create user from request
            user = User.from_dict(request_body, self.user_repo)
            
            # Check userName uniqueness
            if self.user_repo.get_by_username(user.user_name):
                raise SCIMError(409, "uniqueness", f"userName '{user.user_name}' already exists")
            
            # Check externalId uniqueness if provided
            if user.external_id and self.user_repo.get_by_external_id(user.external_id):
                raise SCIMError(409, "uniqueness", f"externalId '{user.external_id}' already exists")
            
            # Save user
            self.user_repo.save(user)
            
            # Return created user
            response = user.to_dict()
            return response, 201
            
        except ValidationError as e:
            raise SCIMError(400, "invalidValue", str(e))
        except SCIMError:
            raise
        except Exception as e:
            raise SCIMError(500, None, f"Internal server error: {str(e)}")
    
    def get_user(self, user_id: str) -> tuple[Dict[str, Any], int]:
        """
        GET /Users/{id}
        Retrieve a single user
        
        Args:
            user_id: User identifier
        
        Returns:
            Tuple of (response_body, status_code)
        """
        try:
            user = self.user_repo.get_by_id(user_id)
            if not user:
                raise SCIMError(404, None, f"User with id '{user_id}' not found")
            
            response = user.to_dict()
            return response, 200
            
        except SCIMError:
            raise
        except Exception as e:
            raise SCIMError(500, None, f"Internal server error: {str(e)}")
    
    def list_users(self, filter_str: Optional[str] = None, start_index: int = 1,
                   count: int = 100) -> tuple[Dict[str, Any], int]:
        """
        GET /Users
        List and search users with filtering and pagination
        
        Args:
            filter_str: SCIM filter expression (optional)
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
            
            # Get all users
            all_users = self.user_repo.get_all()
            
            # Apply filter if provided
            if filter_str:
                try:
                    filter_expr = FilterParser.parse_simple_filter(filter_str)
                    filtered_users = [
                        user for user in all_users
                        if FilterParser.apply_filter(user, filter_expr)
                    ]
                except Exception as e:
                    raise SCIMError(400, "invalidFilter", str(e))
            else:
                filtered_users = all_users
            
            # Calculate pagination
            total_results = len(filtered_users)
            start_idx = start_index - 1  # Convert to 0-based
            end_idx = start_idx + count
            
            # Get page of results
            page_users = filtered_users[start_idx:end_idx]
            
            # Build response
            response = {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "totalResults": total_results,
                "startIndex": start_index,
                "itemsPerPage": len(page_users),
                "Resources": [user.to_dict() for user in page_users]
            }
            
            return response, 200
            
        except SCIMError:
            raise
        except Exception as e:
            raise SCIMError(500, None, f"Internal server error: {str(e)}")
    
    def patch_user(self, user_id: str, request_body: Dict[str, Any]) -> tuple[Dict[str, Any], int]:
        """
        PATCH /Users/{id}
        Update user using SCIM PatchOp (RFC 7644 Section 3.5.2)
        
        Supported operations:
        - add: Add new attribute values
        - replace: Replace existing attribute values
        - remove: Remove attribute values
        
        Args:
            user_id: User identifier
            request_body: SCIM PatchOp request
        
        Returns:
            Tuple of (response_body, status_code)
        """
        try:
            # Validate schemas
            schemas = request_body.get("schemas", [])
            if "urn:ietf:params:scim:api:messages:2.0:PatchOp" not in schemas:
                raise SCIMError(400, "invalidValue", "Missing PatchOp schema")
            
            # Get user
            user = self.user_repo.get_by_id(user_id)
            if not user:
                raise SCIMError(404, None, f"User with id '{user_id}' not found")
            
            # Process operations
            operations = request_body.get("Operations", [])
            if not operations:
                raise SCIMError(400, "invalidValue", "Operations array is required")
            
            for operation in operations:
                op = operation.get("op", "").lower()
                path = operation.get("path", "")
                value = operation.get("value")
                
                if op == "replace":
                    self._apply_replace_operation(user, path, value)
                elif op == "add":
                    self._apply_add_operation(user, path, value)
                elif op == "remove":
                    self._apply_remove_operation(user, path)
                else:
                    raise SCIMError(400, "invalidValue", f"Unsupported operation: {op}")
            
            # Save updated user
            self.user_repo.save(user)
            
            # Return updated user
            response = user.to_dict()
            return response, 200
            
        except ValidationError as e:
            raise SCIMError(400, "invalidValue", str(e))
        except SCIMError:
            raise
        except Exception as e:
            raise SCIMError(500, None, f"Internal server error: {str(e)}")
    
    def _apply_replace_operation(self, user, path: str, value: Any):
        """Apply PATCH replace operation"""
        if not path:
            # Replace multiple attributes
            if isinstance(value, dict):
                for key, val in value.items():
                    self._apply_replace_operation(user, key, val)
            return
        
        # Handle specific paths
        if path == "active":
            user.active = bool(value)
        elif path == "userName":
            # Check uniqueness
            existing = self.user_repo.get_by_username(value)
            if existing and existing.id != user.id:
                raise SCIMError(409, "uniqueness", f"userName '{value}' already exists")
            user.user_name = value
        elif path == "externalId":
            user.external_id = value
        elif path == "department":
            user.department = value
        elif path == "gender":
            user.gender = value
        elif path == "name.givenName":
            if not user.name:
                user.name = Name()
            user.name.given_name = value
        elif path == "name.familyName":
            if not user.name:
                user.name = Name()
            user.name.family_name = value
        elif path == "emails":
            if isinstance(value, list):
                user.emails = [Email(**email) for email in value]
        elif path.startswith("urn:ietf:params:scim:schemas:extension:enterprise:2.0:User:manager"):
            if value:
                manager_id = value.get("value") if isinstance(value, dict) else value
                display_name = value.get("displayName") if isinstance(value, dict) else None
                user.set_manager(manager_id, display_name, self.user_repo)
            else:
                user.clear_manager()
        
        user._update_last_modified()
    
    def _apply_add_operation(self, user, path: str, value: Any):
        """Apply PATCH add operation"""
        # For most attributes, add is same as replace
        self._apply_replace_operation(user, path, value)
    
    def _apply_remove_operation(self, user, path: str):
        """Apply PATCH remove operation"""
        if path == "department":
            user.department = None
        elif path == "gender":
            user.gender = None
        elif path == "externalId":
            user.external_id = None
        elif path.startswith("urn:ietf:params:scim:schemas:extension:enterprise:2.0:User:manager"):
            user.clear_manager()
        
        user._update_last_modified()
    
    def delete_user(self, user_id: str) -> tuple[None, int]:
        """
        DELETE /Users/{id}
        Delete a user
        
        Args:
            user_id: User identifier
        
        Returns:
            Tuple of (None, status_code)
        """
        try:
            user = self.user_repo.get_by_id(user_id)
            if not user:
                raise SCIMError(404, None, f"User with id '{user_id}' not found")
            
            # Remove user from all groups
            all_groups = self.group_repo.get_all()
            for group in all_groups:
                if group.has_member(user_id):
                    group.remove_member(user_id)
                    self.group_repo.save(group)
            
            # Clear manager references (users who report to this user)
            all_users = self.user_repo.get_all()
            for other_user in all_users:
                if other_user.manager and other_user.manager.value == user_id:
                    other_user.clear_manager()
                    self.user_repo.save(other_user)
            
            # Delete user
            self.user_repo.delete(user_id)
            
            return None, 204
            
        except SCIMError:
            raise
        except Exception as e:
            raise SCIMError(500, None, f"Internal server error: {str(e)}")

# Made with Bob
