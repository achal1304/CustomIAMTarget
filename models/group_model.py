"""
SCIM 2.0 Group Data Model
Minimal implementation for role-based access control
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class Member:
    """Group member reference (User only)"""
    
    def __init__(self, value: str, display: Optional[str] = None, 
                 ref: Optional[str] = None, type: str = "User"):
        self.value = value  # User ID
        self.display = display
        self.ref = ref or f"/Users/{value}"
        self.type = type  # Always "User" in this minimal implementation
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "value": self.value,
            "$ref": self.ref,
            "type": self.type
        }
        if self.display:
            result["display"] = self.display
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


class Group:
    """
    SCIM 2.0 Group Resource - Minimal Implementation
    
    Implements:
    - Core Group schema (urn:ietf:params:scim:schemas:core:2.0:Group)
    
    Purpose:
    - Represents roles and access groups
    - Manages user membership
    
    Validation Rules:
    - displayName is required
    - Members must be User references only (no nested groups)
    - No duplicate members
    """
    
    CORE_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:Group"
    
    def __init__(
        self,
        display_name: str,
        id: Optional[str] = None,
        external_id: Optional[str] = None,
        members: Optional[List[Member]] = None,
        meta: Optional[Meta] = None
    ):
        # Validate required fields
        if not display_name or not display_name.strip():
            raise ValidationError("displayName is required and cannot be empty")
        
        # Generate ID if not provided
        self.id = id or str(uuid4())
        self.display_name = display_name.strip()
        self.external_id = external_id
        self.members = members or []
        
        # Metadata
        base_url = f"/Groups/{self.id}"
        self.meta = meta or Meta(
            resource_type="Group",
            location=base_url
        )
        
        # Validate no duplicate members
        self._validate_members()
    
    def _validate_members(self):
        """Ensure no duplicate members"""
        member_ids = [m.value for m in self.members]
        if len(member_ids) != len(set(member_ids)):
            raise ValidationError("Duplicate members are not allowed")
    
    def add_member(self, user_id: str, display_name: Optional[str] = None, 
                   user_repository=None) -> bool:
        """
        Add a user to the group
        
        Args:
            user_id: ID of the user to add
            display_name: Optional display name for the user
            user_repository: Optional repository to validate user exists
        
        Returns:
            True if member was added, False if already exists
        
        Raises:
            ValidationError: If user doesn't exist (when repository provided)
        """
        # Check if already a member
        if any(m.value == user_id for m in self.members):
            return False
        
        # Validate user exists (if repository provided)
        if user_repository:
            user = user_repository.get_by_id(user_id)
            if not user:
                raise ValidationError(f"User with id '{user_id}' does not exist")
            
            # Use user's name as display if not provided
            if not display_name and user.name:
                display_name = f"{user.name.given_name or ''} {user.name.family_name or ''}".strip()
                if not display_name:
                    display_name = user.user_name
        
        # Add member
        member = Member(value=user_id, display=display_name)
        self.members.append(member)
        self._update_last_modified()
        
        return True
    
    def remove_member(self, user_id: str) -> bool:
        """
        Remove a user from the group
        
        Args:
            user_id: ID of the user to remove
        
        Returns:
            True if member was removed, False if not found
        """
        initial_count = len(self.members)
        self.members = [m for m in self.members if m.value != user_id]
        
        if len(self.members) < initial_count:
            self._update_last_modified()
            return True
        
        return False
    
    def has_member(self, user_id: str) -> bool:
        """Check if a user is a member of this group"""
        return any(m.value == user_id for m in self.members)
    
    def get_member_ids(self) -> List[str]:
        """Get list of all member user IDs"""
        return [m.value for m in self.members]
    
    def _update_last_modified(self):
        """Update the lastModified timestamp"""
        self.meta.last_modified = datetime.utcnow()
        self.meta.version = str(uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Group to SCIM-compliant dictionary
        
        Returns:
            Dictionary representation following SCIM 2.0 schema
        """
        result = {
            "schemas": [self.CORE_SCHEMA],
            "id": self.id,
            "displayName": self.display_name,
            "meta": self.meta.to_dict()
        }
        
        # Optional fields
        if self.external_id:
            result["externalId"] = self.external_id
        
        if self.members:
            result["members"] = [member.to_dict() for member in self.members]
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], user_repository=None) -> 'Group':
        """
        Create Group from SCIM-compliant dictionary
        
        Args:
            data: SCIM Group resource dictionary
            user_repository: Optional repository for member validation
        
        Returns:
            Group instance
        
        Raises:
            ValidationError: If required fields are missing or invalid
        """
        # Required fields
        display_name = data.get("displayName")
        if not display_name:
            raise ValidationError("displayName is required")
        
        # Parse members
        members = []
        for member_data in data.get("members", []):
            user_id = member_data.get("value")
            if not user_id:
                raise ValidationError("Member value (user ID) is required")
            
            # Validate user exists if repository provided
            if user_repository:
                user = user_repository.get_by_id(user_id)
                if not user:
                    raise ValidationError(f"User with id '{user_id}' does not exist")
            
            members.append(Member(
                value=user_id,
                display=member_data.get("display"),
                ref=member_data.get("$ref"),
                type=member_data.get("type", "User")
            ))
        
        # Create group
        group = cls(
            display_name=display_name,
            id=data.get("id"),
            external_id=data.get("externalId"),
            members=members
        )
        
        return group
    
    def __repr__(self) -> str:
        return f"Group(id={self.id}, displayName={self.display_name}, members={len(self.members)})"

# Made with Bob
