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
    
    def __init__(self, user_repository, group_repository, supporting_data_repository=None):
        """
        Initialize endpoints with repositories
        
        Args:
            user_repository: Repository for user persistence
            group_repository: Repository for group persistence
            supporting_data_repository: Repository for supporting data (roles, departments)
        """
        self.user_repo = user_repository
        self.group_repo = group_repository
        self.supporting_data_repo = supporting_data_repository
    
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
            user = User.from_dict(request_body, self.user_repo, self.supporting_data_repo)
            
            # Check userName uniqueness
            if self.user_repo.get_by_username(user.user_name):
                raise SCIMError(409, "uniqueness", f"userName '{user.user_name}' already exists")
            
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
    
    def put_user(self, user_id: str, request_body: Dict[str, Any]) -> tuple[Dict[str, Any], int]:
        """
        PUT /Users/{id}
        Replace user (SCIM 2.0 RFC 7644 Section 3.5.1)
        
        PUT replaces the entire resource with the provided representation.
        All attributes must be provided; missing attributes will be removed.
        
        Args:
            user_id: User identifier
            request_body: Complete SCIM User resource
        
        Returns:
            Tuple of (response_body, status_code)
        """
        try:
            # Validate schemas
            schemas = request_body.get("schemas", [])
            if User.CORE_SCHEMA not in schemas:
                raise SCIMError(400, "invalidValue", "Missing required schema")
            
            # Get existing user
            existing_user = self.user_repo.get_by_id(user_id)
            if not existing_user:
                raise SCIMError(404, None, f"User with id '{user_id}' not found")
            
            # Validate userName uniqueness if changed
            new_username = request_body.get("userName")
            if not new_username:
                raise SCIMError(400, "invalidValue", "userName is required")
            
            if new_username.lower() != existing_user.user_name.lower():
                existing_by_username = self.user_repo.get_by_username(new_username)
                if existing_by_username:
                    raise SCIMError(409, "uniqueness", f"userName '{new_username}' already exists")
            
            # Create new user object from request (preserving id and meta.created)
            new_user = User.from_dict(request_body, self.user_repo, self.supporting_data_repo)
            
            # Preserve immutable attributes
            new_user.id = existing_user.id
            new_user.meta.created = existing_user.meta.created
            new_user.meta.location = existing_user.meta.location
            
            # Update last modified
            new_user._update_last_modified()
            
            # Save replaced user
            self.user_repo.save(new_user)
            
            # Return updated user
            response = new_user.to_dict()
            return response, 200
            
        except ValidationError as e:
            raise SCIMError(400, "invalidValue", str(e))
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
        
        # Normalize path - extract attribute name from schema URN if present
        # Supports both "department" and "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User.department"
        normalized_path = self._normalize_path(path)
        
        # Handle specific paths
        if normalized_path == "active":
            user.active = bool(value)
        elif normalized_path == "userName":
            # Check uniqueness
            existing = self.user_repo.get_by_username(value)
            if existing and existing.id != user.id:
                raise SCIMError(409, "uniqueness", f"userName '{value}' already exists")
            user.user_name = value
        elif normalized_path == "externalId":
            user.external_id = value
        elif normalized_path == "department":
            # Validate department against predefined values
            if value and self.supporting_data_repo:
                if not self.supporting_data_repo.validate_department_name(value):
                    valid_depts = [d.name for d in self.supporting_data_repo.get_all_departments()]
                    raise SCIMError(400, "invalidValue",
                        f"Invalid department '{value}'. Must be one of: {', '.join(valid_depts)}")
            user.department = value
        elif normalized_path == "gender" or path.startswith("urn:ietf:params:scim:schemas:extension:custom:2.0:User"):
            # Gender should be in custom extension, but accept both for backward compatibility
            user.gender = value
        elif normalized_path == "name.givenName":
            if not user.name:
                user.name = Name()
            user.name.given_name = value
        elif normalized_path == "name.familyName":
            if not user.name:
                user.name = Name()
            user.name.family_name = value
        elif normalized_path == "emails":
            if isinstance(value, list):
                user.emails = [Email(**email) for email in value]
        elif normalized_path == "manager" or path.startswith("urn:ietf:params:scim:schemas:extension:enterprise:2.0:User:manager"):
            if value:
                manager_id = value.get("value") if isinstance(value, dict) else value
                display_name = value.get("displayName") if isinstance(value, dict) else None
                user.set_manager(manager_id, display_name, self.user_repo)
            else:
                user.clear_manager()
        
        user._update_last_modified()
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize SCIM path to extract attribute name
        
        Handles both simple paths and schema-qualified paths:
        - "department" -> "department"
        - "urn:ietf:params:scim:schemas:core:2.0:User:department" -> "department"
        - "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User.department" -> "department"
        - "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User:manager" -> "manager"
        - "name.givenName" -> "name.givenName"
        """
        if not path:
            return path
        
        # Check if path contains a schema URN
        if path.startswith("urn:ietf:params:scim:schemas:"):
            # Extract attribute name after the schema URN
            # Handle both ":" and "." as separators
            if ":User:" in path:
                # Format: urn:ietf:params:scim:schemas:extension:enterprise:2.0:User:manager
                return path.split(":User:")[-1]
            elif ":User." in path or ".User." in path:
                # Format: urn:ietf:params:scim:schemas:extension:enterprise:2.0:User.department
                parts = path.split(".")
                return parts[-1] if parts else path
        
        # Return as-is for simple paths
        return path
    
    def _apply_add_operation(self, user, path: str, value: Any):
        """Apply PATCH add operation"""
        # For most attributes, add is same as replace
        self._apply_replace_operation(user, path, value)
    
    def _apply_remove_operation(self, user, path: str):
        """Apply PATCH remove operation"""
        # Normalize path to handle schema-qualified paths
        normalized_path = self._normalize_path(path)
        
        if normalized_path == "department":
            user.department = None
        elif normalized_path == "gender" or path.startswith("urn:ietf:params:scim:schemas:extension:custom:2.0:User"):
            user.gender = None
        elif normalized_path == "externalId":
            user.external_id = None
        elif normalized_path == "manager" or path.startswith("urn:ietf:params:scim:schemas:extension:enterprise:2.0:User:manager"):
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
