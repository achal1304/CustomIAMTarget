"""
SCIM 2.0 User Data Model
Minimal implementation with manager relationship validation
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4
import re


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class Email:
    """Email address with type and primary flag"""
    
    def __init__(self, value: str, type: str = "work", primary: bool = True):
        if not self._is_valid_email(value):
            raise ValidationError(f"Invalid email format: {value}")
        
        self.value = value.lower()
        self.type = type
        self.primary = primary
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Basic email validation"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "type": self.type,
            "primary": self.primary
        }


class Name:
    """User name components"""
    
    def __init__(self, given_name: Optional[str] = None, family_name: Optional[str] = None):
        self.given_name = given_name
        self.family_name = family_name
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.given_name:
            result["givenName"] = self.given_name
        if self.family_name:
            result["familyName"] = self.family_name
        return result


class Manager:
    """Manager reference with validation"""
    
    def __init__(self, value: str, display_name: Optional[str] = None, ref: Optional[str] = None):
        self.value = value  # User ID
        self.display_name = display_name
        self.ref = ref  # URI reference
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"value": self.value}
        if self.display_name:
            result["displayName"] = self.display_name
        if self.ref:
            result["$ref"] = self.ref
        return result


class GroupMembership:
    """Read-only group membership information"""
    
    def __init__(self, value: str, display: str, ref: Optional[str] = None, type: str = "direct"):
        self.value = value  # Group ID
        self.display = display
        self.ref = ref
        self.type = type
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "value": self.value,
            "display": self.display,
            "type": self.type
        }
        if self.ref:
            result["$ref"] = self.ref
        return result


class Meta:
    """Resource metadata"""
    
    def __init__(self, resource_type: str, location: str, created: Optional[datetime] = None,
                 last_modified: Optional[datetime] = None, version: Optional[str] = None):
        self.resource_type = resource_type
        self.location = location
        self.created = created or datetime.utcnow()
        self.last_modified = last_modified or datetime.utcnow()
        self.version = version or str(uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "resourceType": self.resource_type,
            "created": self.created.isoformat() + "Z",
            "lastModified": self.last_modified.isoformat() + "Z",
            "location": self.location,
            "version": self.version
        }


class User:
    """
    SCIM 2.0 User Resource - Minimal Implementation
    
    Implements:
    - Core User schema (urn:ietf:params:scim:schemas:core:2.0:User)
    - Enterprise User extension (urn:ietf:params:scim:schemas:extension:enterprise:2.0:User)
    
    Validation Rules:
    - userName is required and must be unique
    - Manager cannot be self-referencing
    - Manager must reference an existing User
    - Only one primary email allowed
    """
    
    CORE_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:User"
    ENTERPRISE_SCHEMA = "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
    CUSTOM_SCHEMA = "urn:ietf:params:scim:schemas:extension:custom:2.0:User"
    
    def __init__(
        self,
        user_name: str,
        id: Optional[str] = None,
        external_id: Optional[str] = None,
        name: Optional[Name] = None,
        emails: Optional[List[Email]] = None,
        active: bool = True,
        department: Optional[str] = None,
        employee_number: Optional[str] = None,
        gender: Optional[str] = None,
        manager: Optional[Manager] = None,
        groups: Optional[List[GroupMembership]] = None,
        meta: Optional[Meta] = None
    ):
        # Validate required fields
        if not user_name or not user_name.strip():
            raise ValidationError("userName is required and cannot be empty")
        
        # Generate ID if not provided
        self.id = id or str(uuid4())
        self.user_name = user_name.strip()
        self.external_id = external_id
        
        # Optional fields
        self.name = name or Name()
        self.emails = emails or []
        self.active = active
        self.department = department
        self.employee_number = employee_number
        self.gender = gender
        self.manager = manager
        self.groups = groups or []  # Read-only, computed from Group memberships
        
        # Metadata
        base_url = f"/Users/{self.id}"
        self.meta = meta or Meta(
            resource_type="User",
            location=base_url
        )
        
        # Validate email constraints
        self._validate_emails()
    
    def _validate_emails(self):
        """Ensure only one primary email"""
        primary_count = sum(1 for email in self.emails if email.primary)
        if primary_count > 1:
            raise ValidationError("Only one email can be marked as primary")
    
    def set_manager(self, manager_id: str, display_name: Optional[str] = None, 
                    user_repository=None):
        """
        Set the user's manager with validation
        
        Args:
            manager_id: ID of the manager user
            display_name: Optional display name for the manager
            user_repository: Repository to validate manager exists
        
        Raises:
            ValidationError: If manager_id equals user's id (self-reference)
            ValidationError: If manager doesn't exist (when repository provided)
        """
        # Prevent self-referencing
        if manager_id == self.id:
            raise ValidationError("A user cannot be their own manager")
        
        # Validate manager exists (if repository provided)
        if user_repository:
            manager_user = user_repository.get_by_id(manager_id)
            if not manager_user:
                raise ValidationError(f"Manager with id '{manager_id}' does not exist")
            
            # Use manager's name as display if not provided
            if not display_name and manager_user.name:
                display_name = f"{manager_user.name.given_name or ''} {manager_user.name.family_name or ''}".strip()
        
        ref = f"/Users/{manager_id}"
        self.manager = Manager(value=manager_id, display_name=display_name, ref=ref)
        self._update_last_modified()
    
    def clear_manager(self):
        """Remove the manager relationship"""
        self.manager = None
        self._update_last_modified()
    
    def add_group_membership(self, group_id: str, group_display_name: str):
        """
        Add a group membership (called when user is added to a group)
        This is read-only from the User perspective
        """
        ref = f"/Groups/{group_id}"
        membership = GroupMembership(
            value=group_id,
            display=group_display_name,
            ref=ref
        )
        
        # Avoid duplicates
        if not any(g.value == group_id for g in self.groups):
            self.groups.append(membership)
            self._update_last_modified()
    
    def remove_group_membership(self, group_id: str):
        """Remove a group membership (called when user is removed from a group)"""
        self.groups = [g for g in self.groups if g.value != group_id]
        self._update_last_modified()
    
    def _update_last_modified(self):
        """Update the lastModified timestamp"""
        self.meta.last_modified = datetime.utcnow()
        self.meta.version = str(uuid4())
    
    def to_dict(self, include_enterprise_extension: bool = True) -> Dict[str, Any]:
        """
        Convert User to SCIM-compliant dictionary
        
        Args:
            include_enterprise_extension: Whether to include Enterprise User extension
        
        Returns:
            Dictionary representation following SCIM 2.0 schema
        """
        schemas = [self.CORE_SCHEMA]
        has_enterprise_data = self.manager or self.department or self.employee_number
        has_custom_data = self.gender
        
        if include_enterprise_extension and has_enterprise_data:
            schemas.append(self.ENTERPRISE_SCHEMA)
        if has_custom_data:
            schemas.append(self.CUSTOM_SCHEMA)
        
        result = {
            "schemas": schemas,
            "id": self.id,
            "userName": self.user_name,
            "active": self.active,
            "meta": self.meta.to_dict()
        }
        
        # Optional fields
        if self.external_id:
            result["externalId"] = self.external_id
        
        if self.name and (self.name.given_name or self.name.family_name):
            result["name"] = self.name.to_dict()
        
        if self.emails:
            result["emails"] = [email.to_dict() for email in self.emails]
        
        if self.groups:
            result["groups"] = [group.to_dict() for group in self.groups]
        
        # Enterprise extension
        if include_enterprise_extension and has_enterprise_data:
            enterprise_ext = {}
            if self.employee_number:
                enterprise_ext["employeeNumber"] = self.employee_number
            if self.department:
                enterprise_ext["department"] = self.department
            if self.manager:
                enterprise_ext["manager"] = self.manager.to_dict()
            result[self.ENTERPRISE_SCHEMA] = enterprise_ext
        
        # Custom extension (for gender and other non-standard attributes)
        if has_custom_data:
            custom_ext = {}
            if self.gender:
                custom_ext["gender"] = self.gender
            result[self.CUSTOM_SCHEMA] = custom_ext
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], user_repository=None, supporting_data_repo=None) -> 'User':
        """
        Create User from SCIM-compliant dictionary
        
        Args:
            data: SCIM User resource dictionary
            user_repository: Optional repository for manager validation
            supporting_data_repo: Optional repository for department validation
        
        Returns:
            User instance
        
        Raises:
            ValidationError: If required fields are missing or invalid
        """
        # Required fields
        user_name = data.get("userName")
        if not user_name:
            raise ValidationError("userName is required")
        
        # Parse name
        name_data = data.get("name", {})
        name = Name(
            given_name=name_data.get("givenName"),
            family_name=name_data.get("familyName")
        )
        
        # Parse emails
        emails = []
        for email_data in data.get("emails", []):
            emails.append(Email(
                value=email_data["value"],
                type=email_data.get("type", "work"),
                primary=email_data.get("primary", True)
            ))
        
        # Parse Enterprise extension data
        manager = None
        department = None
        employee_number = None
        enterprise_data = data.get(cls.ENTERPRISE_SCHEMA, {})
        
        if enterprise_data:
            # Parse manager
            manager_data = enterprise_data.get("manager")
            if manager_data:
                manager_id = manager_data.get("value")
                if manager_id:
                    # Note: Manager validation is intentionally not enforced here
                    # to allow forward references. The manager may be created later.
                    # Validation can be done at the application level if needed.
                    manager = Manager(
                        value=manager_id,
                        display_name=manager_data.get("displayName"),
                        ref=manager_data.get("$ref")
                    )
            
            # Parse department and employeeNumber from enterprise extension
            department = enterprise_data.get("department")
            employee_number = enterprise_data.get("employeeNumber")
        
        # Also accept department at root level for convenience (non-standard but common)
        if not department and "department" in data:
            department = data.get("department")
        
        # Parse Custom extension data (gender and other non-standard attributes)
        gender = None
        custom_data = data.get(cls.CUSTOM_SCHEMA, {})
        if custom_data:
            gender = custom_data.get("gender")
        
        # Also accept gender at root level for backward compatibility (non-standard)
        if not gender and "gender" in data:
            gender = data.get("gender")
        
        # Validate department against predefined values
        if department and supporting_data_repo:
            if not supporting_data_repo.validate_department_name(department):
                valid_depts = [d.name for d in supporting_data_repo.get_all_departments()]
                raise ValidationError(
                    f"Invalid department '{department}'. Must be one of: {', '.join(valid_depts)}"
                )
        
        # Create user
        user = cls(
            user_name=user_name,
            id=data.get("id"),
            external_id=data.get("externalId"),
            name=name,
            emails=emails,
            active=data.get("active", True),
            department=department,
            employee_number=employee_number,
            gender=gender,
            manager=manager
        )
        
        # Validate manager is not self-referencing
        if user.manager and user.manager.value == user.id:
            raise ValidationError("A user cannot be their own manager")
        
        return user
    
    def __repr__(self) -> str:
        return f"User(id={self.id}, userName={self.user_name}, active={self.active})"

# Made with Bob
