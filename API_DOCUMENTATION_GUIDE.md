# API Documentation Guide

This guide explains how to use the interactive API documentation tools available for testing the SCIM 2.0 Service Provider.

## Available Documentation

### 1. Swagger UI (Interactive API Documentation) 🎯

**URL**: http://localhost:5000/api/docs

**Features**:
- Interactive API explorer
- Try out API calls directly from the browser
- See request/response examples
- View all endpoints organized by category
- Built-in authentication support

**How to Use**:

1. Start the server:
   ```bash
   python3 app.py
   ```

2. Open your browser and go to: http://localhost:5000/api/docs

3. Get authentication token:
   - Scroll to "Development - Token Generation" section
   - Click on "GET /api/dev/tokens"
   - Click "Try it out" → "Execute"
   - Copy a token from the response (e.g., `tokens.jwt.full_access.token`)

4. Authorize:
   - Click the "Authorize" button at the top
   - Paste your token in the "BearerAuth" field
   - Click "Authorize" → "Close"

5. Test endpoints:
   - Navigate to any endpoint (e.g., "SCIM Users" → "GET /scim/v2/Users")
   - Click "Try it out"
   - Modify parameters if needed
   - Click "Execute"
   - See the response below

**Tips**:
- Use the filter bar to search for specific endpoints
- All endpoints show example requests and responses
- Authentication is automatically included once you authorize
- You can switch between Bearer Token and Basic Auth

### 2. Postman Collection 📮

**Download**: http://localhost:5000/postman_collection.json

**Features**:
- Complete collection of all API endpoints
- Pre-configured authentication
- Auto-saves IDs for chained requests
- Organized by category
- Includes test scripts

**How to Use**:

1. **Import Collection**:
   - Open Postman
   - Click "Import"
   - Choose "Link" tab
   - Paste: `http://localhost:5000/postman_collection.json`
   - Click "Continue" → "Import"

2. **Get Authentication Token**:
   - Open "1. Development - Token Generation" folder
   - Run "Get All Tokens" request
   - Token is automatically saved to collection variable

3. **Test Endpoints**:
   - Navigate to any request (e.g., "3. SCIM Users" → "List Users")
   - Click "Send"
   - View response

4. **Create and Test Workflow**:
   - Run "Create User" - User ID is auto-saved
   - Run "Get User" - Uses saved user ID
   - Run "Update User (PATCH)" - Updates the same user
   - Run "Delete User" - Deletes the user

**Collection Variables**:
- `baseUrl`: Server URL (default: http://localhost:5000)
- `bearerToken`: JWT token (auto-populated)
- `userId`: Last created user ID (auto-populated)
- `groupId`: Last created group ID (auto-populated)

**Authentication Methods**:
- Most requests use Bearer Token (default)
- Switch to "Authorization" tab → "Basic Auth" to use username/password
- Default credentials: admin/admin123

### 3. OpenAPI Specification (swagger.yaml)

**Download**: http://localhost:5000/swagger.yaml

**Use Cases**:
- Generate client SDKs
- Import into other API tools
- API contract validation
- Documentation generation

**How to Use**:

```bash
# Download the spec
curl http://localhost:5000/swagger.yaml > swagger.yaml

# Generate Python client
openapi-generator-cli generate -i swagger.yaml -g python -o ./client

# Generate Java client
openapi-generator-cli generate -i swagger.yaml -g java -o ./client

# Validate the spec
swagger-cli validate swagger.yaml
```

## Quick Start Workflows

### Workflow 1: Test with Swagger UI

```
1. Open http://localhost:5000/api/docs
2. Get token from "Development > Get All Tokens"
3. Click "Authorize" and paste token
4. Test "SCIM Users > List Users"
5. Test "SCIM Users > Create User"
6. Test "SCIM Users > Get User" with created ID
```

### Workflow 2: Test with Postman

```
1. Import collection from http://localhost:5000/postman_collection.json
2. Run "Get All Tokens" (token auto-saved)
3. Run "Create User" (ID auto-saved)
4. Run "Get User" (uses saved ID)
5. Run "Update User" (updates same user)
6. Run "Delete User" (deletes user)
```

### Workflow 3: Test with curl

```bash
# Get token
TOKEN=$(curl -s http://localhost:5000/api/dev/tokens | jq -r '.tokens.jwt.full_access.token')

# List users
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/scim/v2/Users

# Create user
curl -X POST http://localhost:5000/scim/v2/Users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/scim+json" \
  -d '{"schemas":["urn:ietf:params:scim:schemas:core:2.0:User"],"userName":"test@example.com"}'
```

## Endpoint Categories

### 🔓 Public Endpoints (No Auth Required)

- **API Root**: `/`
- **Service Provider Config**: `/scim/v2/ServiceProviderConfig`
- **Schemas**: `/scim/v2/Schemas`
- **Resource Types**: `/scim/v2/ResourceTypes`
- **Token Generation**: `/api/dev/tokens`
- **Swagger UI**: `/api/docs`
- **OpenAPI Spec**: `/swagger.yaml`
- **Postman Collection**: `/postman_collection.json`

### 🔒 Protected Endpoints (Auth Required)

#### SCIM Users (scim.read / scim.write)
- `GET /scim/v2/Users` - List users
- `POST /scim/v2/Users` - Create user
- `GET /scim/v2/Users/{id}` - Get user
- `PATCH /scim/v2/Users/{id}` - Update user
- `DELETE /scim/v2/Users/{id}` - Delete user

#### SCIM Groups (scim.read / scim.write)
- `GET /scim/v2/Groups` - List groups
- `POST /scim/v2/Groups` - Create group
- `GET /scim/v2/Groups/{id}` - Get group
- `PATCH /scim/v2/Groups/{id}` - Update group
- `DELETE /scim/v2/Groups/{id}` - Delete group

#### Supporting Data (supportingdata.read)
- `GET /api/supporting-data/roles` - List roles
- `GET /api/supporting-data/departments` - List departments

## Authentication in Documentation Tools

### Swagger UI

**Bearer Token**:
1. Click "Authorize" button
2. Enter token in "BearerAuth (http, Bearer)" field
3. Click "Authorize"

**Basic Auth**:
1. Click "Authorize" button
2. Enter username and password in "BasicAuth (http, Basic)" field
3. Click "Authorize"

### Postman

**Bearer Token** (Default):
- Token is automatically used from collection variable
- Manually set: Authorization tab → Type: Bearer Token → Token: `{{bearerToken}}`

**Basic Auth**:
- Authorization tab → Type: Basic Auth
- Username: `admin`
- Password: `admin123`

## Troubleshooting

### Swagger UI Not Loading

```bash
# Check if server is running
curl http://localhost:5000/

# Check if Swagger UI is accessible
curl http://localhost:5000/api/docs

# Reinstall dependencies
pip3 install -r requirements.txt
```

### Postman Collection Import Fails

```bash
# Download collection manually
curl http://localhost:5000/postman_collection.json > collection.json

# Import the downloaded file in Postman
```

### Authentication Fails

```bash
# Get fresh token
curl http://localhost:5000/api/dev/tokens | jq -r '.tokens.jwt.full_access.token'

# Test with curl first
TOKEN="<paste-token>"
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/scim/v2/Users
```

### 401 Unauthorized

- Token might be expired (default: 24 hours)
- Get a new token from `/api/dev/tokens`
- Make sure you clicked "Authorize" in Swagger UI
- Check that token is set in Postman collection variables

### 403 Forbidden

- Token is valid but lacks required scopes
- Use `full_access` token for all operations
- Check endpoint scope requirements in Swagger UI

## Advanced Usage

### Generate Client SDK

```bash
# Install OpenAPI Generator
npm install @openapitools/openapi-generator-cli -g

# Download spec
curl http://localhost:5000/swagger.yaml > swagger.yaml

# Generate Python client
openapi-generator-cli generate \
  -i swagger.yaml \
  -g python \
  -o ./python-client \
  --additional-properties=packageName=scim_client

# Generate TypeScript client
openapi-generator-cli generate \
  -i swagger.yaml \
  -g typescript-axios \
  -o ./typescript-client
```

### Use in CI/CD

```yaml
# .github/workflows/api-test.yml
name: API Tests
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start API
        run: python3 app.py &
      - name: Run Newman (Postman CLI)
        run: |
          npm install -g newman
          newman run http://localhost:5000/postman_collection.json
```

### API Contract Testing

```bash
# Validate OpenAPI spec
npx swagger-cli validate http://localhost:5000/swagger.yaml

# Test with Dredd
npm install -g dredd
dredd http://localhost:5000/swagger.yaml http://localhost:5000
```

## Best Practices

1. **Start with Swagger UI** for quick exploration
2. **Use Postman** for complex workflows and testing
3. **Download OpenAPI spec** for client generation
4. **Always get fresh tokens** before testing
5. **Use collection variables** in Postman for IDs
6. **Test public endpoints first** (no auth needed)
7. **Check response status codes** and error messages
8. **Use filters and pagination** for large datasets

## Resources

- **Swagger UI**: http://localhost:5000/api/docs
- **Postman Collection**: http://localhost:5000/postman_collection.json
- **OpenAPI Spec**: http://localhost:5000/swagger.yaml
- **Token Generator**: http://localhost:5000/api/dev/tokens
- **API Root**: http://localhost:5000/

## Support

For issues or questions:
- Check [TOKEN_GENERATION_GUIDE.md](TOKEN_GENERATION_GUIDE.md) for authentication help
- See [IAM_INTEGRATION_GUIDE.md](IAM_INTEGRATION_GUIDE.md) for integration guidance
- Review [README.md](README.md) for general documentation

---

Made with Bob