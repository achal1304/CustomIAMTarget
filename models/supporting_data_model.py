"""
Supporting Data Models - READ-ONLY
Roles and Departments for IAM lookup and mapping

IMPORTANT: These are NOT SCIM resources.
They are predefined, fixed reference data for IAM operations.
"""

from typing import Optional, List
from datetime import datetime


class Role:
    """
    Role - Predefined, immutable reference data
    
    Roles map to SCIM Groups but are exposed separately for lookup.
    This is NOT a SCIM resource - it's supporting data only.
    
    Attributes:
        id: Stable, immutable identifier
        name: Display name (matches SCIM Group displayName)
        description: Optional description
        scim_group_id: Reference to corresponding SCIM Group (optional)
    """
    
    def __init__(
        self,
        id: str,
        name: str,
        description: Optional[str] = None,
        scim_group_id: Optional[str] = None
    ):
        self.id = id
        self.name = name
        self.description = description
        self.scim_group_id = scim_group_id
    
    def to_dict(self) -> dict:
        """Convert to API response format"""
        result = {
            "id": self.id,
            "name": self.name
        }
        if self.description:
            result["description"] = self.description
        if self.scim_group_id:
            result["scimGroupId"] = self.scim_group_id
        return result
    
    def __repr__(self) -> str:
        return f"Role(id={self.id}, name={self.name})"


class Department:
    """
    Department - Predefined, immutable reference data
    
    Departments are referenced by SCIM Users via the department attribute.
    This is NOT a SCIM resource - it's supporting data only.
    
    Attributes:
        id: Stable, immutable identifier
        name: Display name (matches SCIM User department value)
    """
    
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
    
    def to_dict(self) -> dict:
        """Convert to API response format"""
        return {
            "id": self.id,
            "name": self.name
        }
    
    def __repr__(self) -> str:
        return f"Department(id={self.id}, name={self.name})"


class SupportingDataRepository:
    """
    Repository for predefined supporting data
    
    This is a READ-ONLY repository. Data is loaded from configuration
    or seed data and cannot be modified at runtime.
    """
    
    def __init__(self):
        """Initialize with predefined data"""
        self._roles = self._load_predefined_roles()
        self._departments = self._load_predefined_departments()
    
    def _load_predefined_roles(self) -> List[Role]:
        """
        Load predefined roles from configuration
        
        In production, this would load from:
        - Configuration file (YAML, JSON)
        - Environment variables
        - Database seed data
        - External configuration service
        
        These roles map to SCIM Groups by name.
        """
        return [
            Role(
                id="role-admin",
                name="Administrator",
                description="Full system access and administrative privileges"
            ),
            Role(
                id="role-developer",
                name="Developer",
                description="Development and deployment access"
            ),
            Role(
                id="role-analyst",
                name="Analyst",
                description="Read-only access for analysis and reporting"
            ),
            Role(
                id="role-manager",
                name="Manager",
                description="Team management and approval capabilities"
            ),
            Role(
                id="role-auditor",
                name="Auditor",
                description="Audit and compliance review access"
            ),
            Role(
                id="role-support",
                name="Support",
                description="Customer support and helpdesk access"
            ),
            Role(
                id="role-readonly",
                name="Read-Only User",
                description="Basic read-only access"
            )
        ]
    
    def _load_predefined_departments(self) -> List[Department]:
        """
        Load predefined departments from configuration
        
        In production, this would load from:
        - Configuration file (YAML, JSON)
        - Environment variables
        - Database seed data
        - HR system integration
        
        These departments are referenced by SCIM User.department attribute.
        """
        return [
            Department(id="dept-eng", name="Engineering"),
            Department(id="dept-product", name="Product Management"),
            Department(id="dept-sales", name="Sales"),
            Department(id="dept-marketing", name="Marketing"),
            Department(id="dept-hr", name="Human Resources"),
            Department(id="dept-finance", name="Finance"),
            Department(id="dept-legal", name="Legal"),
            Department(id="dept-ops", name="Operations"),
            Department(id="dept-support", name="Customer Support"),
            Department(id="dept-exec", name="Executive")
        ]
    
    # READ-ONLY OPERATIONS ONLY
    
    def get_all_roles(self) -> List[Role]:
        """Get all predefined roles"""
        return self._roles.copy()
    
    def get_role_by_id(self, role_id: str) -> Optional[Role]:
        """Get role by ID"""
        for role in self._roles:
            if role.id == role_id:
                return role
        return None
    
    def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name (case-insensitive)"""
        name_lower = name.lower()
        for role in self._roles:
            if role.name.lower() == name_lower:
                return role
        return None
    
    def get_all_departments(self) -> List[Department]:
        """Get all predefined departments"""
        return self._departments.copy()
    
    def get_department_by_id(self, dept_id: str) -> Optional[Department]:
        """Get department by ID"""
        for dept in self._departments:
            if dept.id == dept_id:
                return dept
        return None
    
    def get_department_by_name(self, name: str) -> Optional[Department]:
        """Get department by name (case-insensitive)"""
        name_lower = name.lower()
        for dept in self._departments:
            if dept.name.lower() == name_lower:
                return dept
        return None
    
    def validate_role_name(self, name: str) -> bool:
        """Check if a role name exists in predefined set"""
        return self.get_role_by_name(name) is not None
    
    def validate_department_name(self, name: str) -> bool:
        """Check if a department name exists in predefined set"""
        return self.get_department_by_name(name) is not None

# Made with Bob
