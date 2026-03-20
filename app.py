"""
SCIM 2.0 Service Provider - Main Application
Wires all existing endpoint classes into a runnable Flask application
"""

from flask import Flask, request, jsonify, make_response, g, send_from_directory, Response
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from typing import Dict, Any, Optional, List
import os
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
# override=False ensures test environment variables are not overwritten
load_dotenv(override=False)

# Import existing endpoint classes
from api.user_endpoints import UserEndpoints, SCIMError as UserSCIMError
from api.group_endpoints import GroupEndpoints, SCIMError as GroupSCIMError
from api.discovery_endpoints import DiscoveryEndpoints
from api.supporting_data_endpoints import SupportingDataEndpoints
from api.token_endpoints import TokenEndpoints

# Import models
from models.user_model import User
from models.group_model import Group
from models.supporting_data_model import SupportingDataRepository

# Import authentication & authorization
from auth.middleware import create_auth_middleware
from auth.config import AuthConfig

# Import seed data
from seed_data import seed_all_data


# ==================== IN-MEMORY REPOSITORIES ====================

class UserRepository:
    """Simple in-memory user repository"""
    def __init__(self):
        self._users: Dict[str, User] = {}
    
    def save(self, user: User) -> None:
        self._users[user.id] = user
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)
    
    def get_by_username(self, username: str) -> Optional[User]:
        for user in self._users.values():
            if user.user_name.lower() == username.lower():
                return user
        return None
    
    def get_by_external_id(self, external_id: str) -> Optional[User]:
        for user in self._users.values():
            if user.external_id == external_id:
                return user
        return None
    
    def get_all(self) -> List[User]:
        return list(self._users.values())
    
    def delete(self, user_id: str) -> bool:
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False


class GroupRepository:
    """Simple in-memory group repository"""
    def __init__(self):
        self._groups: Dict[str, Group] = {}
    
    def save(self, group: Group) -> None:
        self._groups[group.id] = group
    
    def get_by_id(self, group_id: str) -> Optional[Group]:
        return self._groups.get(group_id)
    
    def get_by_display_name(self, display_name: str) -> Optional[Group]:
        for group in self._groups.values():
            if group.display_name.lower() == display_name.lower():
                return group
        return None
    
    def get_by_external_id(self, external_id: str) -> Optional[Group]:
        for group in self._groups.values():
            if group.external_id == external_id:
                return group
        return None
    
    def get_all(self) -> List[Group]:
        return list(self._groups.values())
    
    def delete(self, group_id: str) -> bool:
        if group_id in self._groups:
            del self._groups[group_id]
            return True
        return False


# ==================== APPLICATION SETUP ====================

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Configure CORS
CORS(app, resources={
    r"/*": {
        "origins": os.getenv('CORS_ORIGINS', '*').split(','),
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Location"],
        "supports_credentials": True
    }
})

# Get base URL from environment or use default
BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
SCIM_BASE_URL = f"{BASE_URL}/scim/v2"

# Initialize repositories
user_repo = UserRepository()
group_repo = GroupRepository()
supporting_data_repo = SupportingDataRepository()

# Initialize endpoint controllers
user_endpoints = UserEndpoints(user_repo, group_repo, supporting_data_repo)
group_endpoints = GroupEndpoints(group_repo, user_repo)
discovery_endpoints = DiscoveryEndpoints(SCIM_BASE_URL)
supporting_data_endpoints = SupportingDataEndpoints(supporting_data_repo)
token_endpoints = TokenEndpoints()

# Initialize authentication & authorization middleware
auth_config = AuthConfig.from_env()
auth_middleware = create_auth_middleware(auth_config)

# Seed data on startup (100 users, 20 groups with memberships)
seed_all_data(user_repo, group_repo, supporting_data_repo)

# ==================== SWAGGER UI SETUP ====================

# Swagger UI configuration
SWAGGER_URL = '/api/docs'
API_URL = '/swagger.yaml'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "SCIM 2.0 Service Provider API",
        'defaultModelsExpandDepth': -1,  # Hide models section by default
        'docExpansion': 'list',  # Expand operations by default
        'filter': True,  # Enable filter bar
        'tryItOutEnabled': True,  # Enable "Try it out" by default
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Serve swagger.yaml file with dynamic server URL
@app.route('/swagger.yaml')
def swagger_spec():
    """Serve the Swagger/OpenAPI specification file with dynamic server URL"""
    try:
        # Read the swagger.yaml file
        with open('swagger.yaml', 'r') as f:
            swagger_content = yaml.safe_load(f)
        
        # Update the servers section with the current BASE_URL
        swagger_content['servers'] = [
            {
                'url': BASE_URL,
                'description': 'Current server'
            }
        ]
        
        # Convert back to YAML and return
        yaml_output = yaml.dump(swagger_content, default_flow_style=False, sort_keys=False)
        return Response(yaml_output, mimetype='text/yaml')
    except Exception as e:
        # Fallback to static file if there's an error
        return send_from_directory('.', 'swagger.yaml')

# Serve Postman collection
@app.route('/postman_collection.json')
def postman_collection():
    """Serve the Postman collection file"""
    return send_from_directory('.', 'postman_collection.json')


# ==================== AUTHENTICATION MIDDLEWARE ====================

@app.before_request
def authenticate_and_authorize():
    """
    Authentication and authorization middleware
    Executes before every request to enforce security
    """
    # Process authentication and authorization
    error_response = auth_middleware.process_request(request)
    
    if error_response:
        # Authentication or authorization failed
        response_body, status_code = error_response
        return jsonify(response_body), status_code
    
    # Request is authenticated and authorized, continue to endpoint
    return None


# ==================== ERROR HANDLERS ====================

@app.errorhandler(UserSCIMError)
def handle_user_scim_error(error):
    """Handle SCIM errors from user endpoints"""
    response = jsonify(error.to_dict())
    response.status_code = error.status
    return response


@app.errorhandler(GroupSCIMError)
def handle_group_scim_error(error):
    """Handle SCIM errors from group endpoints"""
    response = jsonify(error.to_dict())
    response.status_code = error.status
    return response


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
        "status": "404",
        "detail": "Resource not found"
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 Method Not Allowed"""
    return jsonify({
        "error": {
            "status": 405,
            "message": "Method not allowed"
        }
    }), 405


# ==================== SCIM DISCOVERY ENDPOINTS ====================

@app.route('/scim/v2/ServiceProviderConfig', methods=['GET'])
def get_service_provider_config():
    """GET /scim/v2/ServiceProviderConfig"""
    response_body, status_code = discovery_endpoints.get_service_provider_config()
    return jsonify(response_body), status_code


@app.route('/scim/v2/Schemas', methods=['GET'])
@app.route('/scim/v2/Schemas/<schema_id>', methods=['GET'])
def get_schemas(schema_id=None):
    """GET /scim/v2/Schemas or /scim/v2/Schemas/{id}"""
    if schema_id:
        response_body, status_code = discovery_endpoints.get_schema(schema_id)
    else:
        response_body, status_code = discovery_endpoints.get_schemas()
    return jsonify(response_body), status_code


@app.route('/scim/v2/ResourceTypes', methods=['GET'])
@app.route('/scim/v2/ResourceTypes/<resource_type>', methods=['GET'])
def get_resource_types(resource_type=None):
    """GET /scim/v2/ResourceTypes or /scim/v2/ResourceTypes/{type}"""
    if resource_type:
        response_body, status_code = discovery_endpoints.get_resource_type(resource_type)
    else:
        response_body, status_code = discovery_endpoints.get_resource_types()
    return jsonify(response_body), status_code


# ==================== SCIM USER ENDPOINTS ====================

@app.route('/scim/v2/Users', methods=['GET', 'POST'])
def users():
    """
    GET /scim/v2/Users - List users
    POST /scim/v2/Users - Create user
    """
    if request.method == 'GET':
        # Extract query parameters
        start_index = request.args.get('startIndex', 1, type=int)
        count = request.args.get('count', 100, type=int)
        filter_str = request.args.get('filter', None)
        
        response_body, status_code = user_endpoints.list_users(
            filter_str=filter_str,
            start_index=start_index,
            count=count
        )
        return jsonify(response_body), status_code
    
    else:  # POST
        response_body, status_code = user_endpoints.create_user(
            request.get_json(),
            SCIM_BASE_URL
        )
        response = jsonify(response_body)
        if status_code == 201:
            response.headers['Location'] = f"{SCIM_BASE_URL}/Users/{response_body['id']}"
        return response, status_code


@app.route('/scim/v2/Users/<user_id>', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
def user_by_id(user_id):
    """
    GET /scim/v2/Users/{id} - Get user
    PUT /scim/v2/Users/{id} - Replace user (not supported, use PATCH)
    PATCH /scim/v2/Users/{id} - Update user
    DELETE /scim/v2/Users/{id} - Delete user
    """
    if request.method == 'GET':
        response_body, status_code = user_endpoints.get_user(user_id)
        return jsonify(response_body), status_code
    
    elif request.method == 'PUT':
        # PUT is not implemented for users in SCIM 2.0 - use PATCH instead
        return jsonify({
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "status": "501",
            "detail": "PUT operation not supported for Users. Use PATCH instead."
        }), 501
    
    elif request.method == 'PATCH':
        response_body, status_code = user_endpoints.patch_user(
            user_id,
            request.get_json()
        )
        return jsonify(response_body), status_code
    
    elif request.method == 'DELETE':
        response_body, status_code = user_endpoints.delete_user(user_id)
        if status_code == 204:
            return '', 204
        return jsonify(response_body), status_code
    
    # This should never be reached due to Flask's method filtering
    return jsonify({"error": "Method not allowed"}), 405


# ==================== SCIM GROUP ENDPOINTS ====================

@app.route('/scim/v2/Groups', methods=['GET', 'POST'])
def groups():
    """
    GET /scim/v2/Groups - List groups
    POST /scim/v2/Groups - Create group
    """
    if request.method == 'GET':
        start_index = request.args.get('startIndex', 1, type=int)
        count = request.args.get('count', 100, type=int)
        filter_str = request.args.get('filter', None)
        
        response_body, status_code = group_endpoints.list_groups(
            filter_str=filter_str,
            start_index=start_index,
            count=count
        )
        return jsonify(response_body), status_code
    
    elif request.method == 'POST':
        response_body, status_code = group_endpoints.create_group(
            request.get_json(),
            SCIM_BASE_URL
        )
        response = jsonify(response_body)
        response.status_code = status_code
        if status_code == 201:
            response.headers['Location'] = f"{SCIM_BASE_URL}/Groups/{response_body['id']}"
        return response
    
    # This should never be reached due to Flask's method filtering
    return jsonify({"error": "Method not allowed"}), 405


@app.route('/scim/v2/Groups/<group_id>', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
def group_by_id(group_id):
    """
    GET /scim/v2/Groups/{id} - Get group
    PUT /scim/v2/Groups/{id} - Replace group
    PATCH /scim/v2/Groups/{id} - Update group
    DELETE /scim/v2/Groups/{id} - Delete group
    """
    if request.method == 'GET':
        response_body, status_code = group_endpoints.get_group(group_id)
        return jsonify(response_body), status_code
    
    elif request.method == 'PUT':
        # PUT is not implemented for groups in SCIM 2.0 - use PATCH instead
        return jsonify({
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "status": "501",
            "detail": "PUT operation not supported for Groups. Use PATCH instead."
        }), 501
    
    elif request.method == 'PATCH':
        response_body, status_code = group_endpoints.patch_group(
            group_id,
            request.get_json()
        )
        return jsonify(response_body), status_code
    
    elif request.method == 'DELETE':
        response_body, status_code = group_endpoints.delete_group(group_id)
        if status_code == 204:
            return '', 204
        return jsonify(response_body), status_code
    
    # This should never be reached due to Flask's method filtering
    return jsonify({"error": "Method not allowed"}), 405


# ==================== SUPPORTING DATA ENDPOINTS ====================

@app.route('/api/supporting-data/roles', methods=['GET'])
def list_roles():
    """GET /api/supporting-data/roles - List all roles (paginated)"""
    start_index = request.args.get('startIndex', 1, type=int)
    count = request.args.get('count', 100, type=int)
    
    response_body, status_code = supporting_data_endpoints.list_roles(
        start_index=start_index,
        count=count
    )
    return jsonify(response_body), status_code


@app.route('/api/supporting-data/departments', methods=['GET'])
def list_departments():
    """GET /api/supporting-data/departments - List all departments (paginated)"""
    start_index = request.args.get('startIndex', 1, type=int)
    count = request.args.get('count', 100, type=int)
    
    response_body, status_code = supporting_data_endpoints.list_departments(
        start_index=start_index,
        count=count
    )
    return jsonify(response_body), status_code


# Block all unsupported operations on supporting data (read-only enforcement)
@app.route('/api/supporting-data/roles', methods=['POST', 'PUT', 'PATCH', 'DELETE'])
@app.route('/api/supporting-data/roles/<role_id>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@app.route('/api/supporting-data/departments', methods=['POST', 'PUT', 'PATCH', 'DELETE'])
@app.route('/api/supporting-data/departments/<dept_id>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def supporting_data_unsupported_operations(role_id=None, dept_id=None):
    """Block all unsupported operations on supporting data endpoints"""
    return jsonify({
        "error": {
            "status": 405,
            "message": "Method not allowed. Supporting data endpoints only support paginated GET list operations."
        }
    }), 405


# ==================== TOKEN GENERATION ENDPOINTS (DEV/TEST ONLY) ====================

@app.route('/api/dev/tokens', methods=['GET'])
def get_all_tokens():
    """GET /api/dev/tokens - Get all pre-generated test tokens"""
    response_body, status_code = token_endpoints.get_all_tokens()
    return jsonify(response_body), status_code


@app.route('/api/dev/tokens/generate', methods=['POST'])
def generate_custom_token():
    """POST /api/dev/tokens/generate - Generate custom token with specified scopes"""
    response_body, status_code = token_endpoints.generate_custom_token(request.get_json() or {})
    return jsonify(response_body), status_code


@app.route('/api/dev/tokens/public-key', methods=['GET'])
def get_public_key():
    """GET /api/dev/tokens/public-key - Get public key for JWT validation"""
    response_body, status_code = token_endpoints.get_public_key()
    return jsonify(response_body), status_code


# ==================== ROOT ENDPOINT ====================

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information"""
    return jsonify({
        "name": "SCIM 2.0 Service Provider",
        "version": "1.0.0",
        "documentation": {
            "swagger": f"{BASE_URL}/api/docs",
            "openapi": f"{BASE_URL}/swagger.yaml",
            "postman": f"{BASE_URL}/postman_collection.json",
            "readme": "See README.md for getting started"
        },
        "endpoints": {
            "scim": {
                "discovery": {
                    "serviceProviderConfig": f"{SCIM_BASE_URL}/ServiceProviderConfig",
                    "schemas": f"{SCIM_BASE_URL}/Schemas",
                    "resourceTypes": f"{SCIM_BASE_URL}/ResourceTypes"
                },
                "users": f"{SCIM_BASE_URL}/Users",
                "groups": f"{SCIM_BASE_URL}/Groups"
            },
            "supportingData": {
                "roles": f"{BASE_URL}/api/supporting-data/roles",
                "departments": f"{BASE_URL}/api/supporting-data/departments"
            },
            "development": {
                "tokens": f"{BASE_URL}/api/dev/tokens",
                "generateToken": f"{BASE_URL}/api/dev/tokens/generate",
                "publicKey": f"{BASE_URL}/api/dev/tokens/public-key",
                "warning": "⚠️ Development endpoints - do not use in production!"
            }
        }
    }), 200


# ==================== APPLICATION ENTRY POINT ====================

if __name__ == '__main__':
    # Get configuration from environment
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Authentication status
    auth_status = "ENABLED" if auth_config.is_any_auth_enabled() else "DISABLED"
    auth_mechanisms = []
    if auth_config.oauth.enabled:
        auth_mechanisms.append("OAuth 2.0 Bearer Token")
    if auth_config.basic_auth.enabled:
        auth_mechanisms.append("HTTP Basic Auth")
    if auth_config.mtls.enabled:
        auth_mechanisms.append("Mutual TLS")
    
    auth_info = f"  Authentication: {auth_status}"
    if auth_mechanisms:
        auth_info += f"\n  Mechanisms: {', '.join(auth_mechanisms)}"
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║         SCIM 2.0 Service Provider - Starting Server          ║
╚══════════════════════════════════════════════════════════════╝

Server Configuration:
  Host: {host}
  Port: {port}
  Debug: {debug}
  Base URL: {BASE_URL}
{auth_info}

Available Endpoints:
  
  📋 SCIM Discovery (Public):
    GET  {SCIM_BASE_URL}/ServiceProviderConfig
    GET  {SCIM_BASE_URL}/Schemas
    GET  {SCIM_BASE_URL}/ResourceTypes
  
  👤 SCIM Users (Requires: scim.read / scim.write):
    GET    {SCIM_BASE_URL}/Users
    POST   {SCIM_BASE_URL}/Users
    GET    {SCIM_BASE_URL}/Users/{{id}}
    PUT    {SCIM_BASE_URL}/Users/{{id}}
    PATCH  {SCIM_BASE_URL}/Users/{{id}}
    DELETE {SCIM_BASE_URL}/Users/{{id}}
  
  👥 SCIM Groups (Requires: scim.read / scim.write):
    GET    {SCIM_BASE_URL}/Groups
    POST   {SCIM_BASE_URL}/Groups
    GET    {SCIM_BASE_URL}/Groups/{{id}}
    PUT    {SCIM_BASE_URL}/Groups/{{id}}
    PATCH  {SCIM_BASE_URL}/Groups/{{id}}
    DELETE {SCIM_BASE_URL}/Groups/{{id}}
  
  🔧 Supporting Data (Requires: supportingdata.read):
    GET  {BASE_URL}/api/supporting-data/roles
    GET  {BASE_URL}/api/supporting-data/departments

Server starting...
""")
    
    # Disable reloader to avoid double-loading and environment variable issues
    app.run(host=host, port=port, debug=debug, use_reloader=False)

# Made with Bob
