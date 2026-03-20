"""
Seed Data Module
Pre-populates the SCIM system with 100 users, 20 groups, and group memberships
"""

from models.user_model import User, Name, Email
from models.group_model import Group, Member
from datetime import datetime
from typing import List
import random


def seed_users(user_repo, supporting_data_repo) -> List[User]:
    """Create 100 test users with varied data"""
    
    first_names = [
        "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
        "William", "Barbara", "David", "Elizabeth", "Richard", "Susan", "Joseph", "Jessica",
        "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
        "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
        "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
        "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
        "Edward", "Deborah", "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Sharon",
        "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
        "Nicholas", "Shirley", "Eric", "Angela", "Jonathan", "Helen", "Stephen", "Anna",
        "Larry", "Brenda", "Justin", "Pamela", "Scott", "Nicole", "Brandon", "Emma",
        "Benjamin", "Samantha", "Samuel", "Katherine", "Raymond", "Christine", "Gregory", "Debra",
        "Frank", "Rachel", "Alexander", "Catherine", "Patrick", "Carolyn", "Jack", "Janet"
    ]
    
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
        "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
        "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
        "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
        "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
        "Carter", "Roberts"
    ]
    
    departments = [
        "Engineering", "Sales", "Marketing", "Human Resources", "Finance",
        "Operations", "Customer Support", "Product Management", "Legal", "IT"
    ]
    
    users = []
    
    for i in range(100):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        username = f"{first_name.lower()}.{last_name.lower()}{i}@company.com"
        email = username
        department = random.choice(departments)
        
        # Create user data
        user_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": username,
            "name": {
                "givenName": first_name,
                "familyName": last_name
            },
            "emails": [{
                "value": email,
                "type": "work",
                "primary": True
            }],
            "active": True,
            "department": department,
            "externalId": f"ext-{i:03d}"  # Some users will have same externalId to test non-uniqueness
        }
        
        # Add enterprise extension for some users (managers will be set later)
        if i % 3 == 0:  # Every 3rd user gets enterprise extension
            user_data["schemas"].append("urn:ietf:params:scim:schemas:extension:enterprise:2.0:User")
        
        # Create user object
        user = User.from_dict(user_data, user_repo, supporting_data_repo)
        user_repo.save(user)
        users.append(user)
    
    # Set up manager relationships (avoid circular references)
    from models.user_model import Manager
    for i in range(10, 100):  # Start from user 10 to ensure managers exist
        if i % 5 == 0:  # Every 5th user gets a manager
            manager_index = random.randint(0, i - 1)
            manager_user = users[manager_index]
            users[i].manager = Manager(
                value=manager_user.id,
                display_name=f"{manager_user.name.given_name} {manager_user.name.family_name}",
                ref=f"/Users/{manager_user.id}"
            )
    
    print(f"✅ Seeded {len(users)} users")
    return users


def seed_groups(group_repo, user_repo, users: List[User]) -> List[Group]:
    """Create 20 groups with varied membership"""
    
    group_names = [
        "Engineering Team", "Sales Team", "Marketing Team", "HR Team", "Finance Team",
        "Operations Team", "Support Team", "Product Team", "Legal Team", "IT Team",
        "Developers", "Managers", "Executives", "Analysts", "Designers",
        "Consultants", "Administrators", "Coordinators", "Specialists", "Directors"
    ]
    
    groups = []
    user_index = 0
    
    for i, group_name in enumerate(group_names):
        members = []
        
        # First group: 2 members
        if i == 0:
            member_count = 2
        # Second group: 3 members
        elif i == 1:
            member_count = 3
        # Rest: random between 3-8 members
        else:
            member_count = random.randint(3, 8)
        
        # Add members
        for _ in range(member_count):
            if user_index < len(users):
                user = users[user_index]
                member = Member(
                    value=user.id,
                    display=f"{user.name.given_name} {user.name.family_name}",
                    ref=f"/Users/{user.id}"
                )
                members.append(member)
                user_index += 1
        
        # Create group
        group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": group_name,
            "members": [m.to_dict() for m in members],
            "externalId": f"group-ext-{i:02d}"
        }
        
        group = Group.from_dict(group_data, user_repo)
        group_repo.save(group)
        groups.append(group)
        
        # Update user group memberships
        for member in members:
            user = user_repo.get_by_id(member.value)
            if user:
                if not user.groups:
                    user.groups = []
                user.groups.append({
                    "value": group.id,
                    "display": group.display_name,
                    "$ref": f"/Groups/{group.id}"
                })
    
    print(f"✅ Seeded {len(groups)} groups")
    print(f"   - Group 1 ('{groups[0].display_name}'): {len(groups[0].members)} members")
    print(f"   - Group 2 ('{groups[1].display_name}'): {len(groups[1].members)} members")
    print(f"   - Other groups: varied membership (3-8 members)")
    
    return groups


def seed_all_data(user_repo, group_repo, supporting_data_repo):
    """Seed all data: users, groups, and relationships"""
    
    print("\n" + "="*60)
    print("🌱 SEEDING DATABASE WITH TEST DATA")
    print("="*60)
    
    # Seed users
    users = seed_users(user_repo, supporting_data_repo)
    
    # Seed groups with memberships
    groups = seed_groups(group_repo, user_repo, users)
    
    # Summary
    total_memberships = sum(len(g.members) for g in groups)
    users_in_groups = len(set(m.value for g in groups for m in g.members))
    
    print("\n" + "="*60)
    print("📊 SEED DATA SUMMARY")
    print("="*60)
    print(f"  Total Users: {len(users)}")
    print(f"  Total Groups: {len(groups)}")
    print(f"  Total Group Memberships: {total_memberships}")
    print(f"  Users in at least one group: {users_in_groups}")
    print(f"  Users with managers: {sum(1 for u in users if u.manager)}")
    print("="*60 + "\n")

# Made with Bob
