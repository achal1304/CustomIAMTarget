# Quick Start Guide - Running the SCIM Server

This guide shows how to start the SCIM 2.0 Service Provider application.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs Flask and required dependencies.

## Running the Server

### Option 1: Default Configuration (Recommended)

```bash
python app.py
```

The server will start on `http://localhost:5000`

### Option 2: Custom Configuration

Set environment variables before starting:

```bash
# Set custom host and port
export HOST=0.0.0.0
export PORT=8000
export BASE_URL=http://localhost:8000
export DEBUG=True

python app.py
```

### Option 3: Production Mode

```bash
# Disable debug mode for production
export DEBUG=False
python app.py
```

Or use a production WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Verify Server is Running

### Check Root Endpoint

```bash
curl http://localhost:5000/
```

Expected response:
```json
{
  "name": "SCIM 2.0 Service Provider",
  "version": "1.0.0",
  "endpoints": {
    "scim": {
      "discovery": {...},
      "users": "http://localhost:5000/scim/v2/Users",
      "groups": "http://localhost:5000/scim/v2/Groups"
    },
    "supportingData": {
      "roles": "http://localhost:5000/api/supporting-data/roles",
      "departments": "http://localhost:5000/api/supporting-data/departments"
    }
  }
}
```

### Test Supporting Data Endpoints

```bash
# List all roles
curl http://localhost:5000/api/supporting-data/roles

# List all departments
curl http://localhost:5000/api/supporting-data/departments
```

### Test SCIM Discovery

```bash
# Get service provider configuration
curl http://localhost:5000/scim/v2/ServiceProviderConfig

# Get supported schemas
curl http://localhost:5000/scim/v2/Schemas

# Get resource types
curl http://localhost:5000/scim/v2/ResourceTypes
```

## Running Tests

Once the server is running, you can run the integration tests:

### Terminal 1: Start Server
```bash
python app.py
```

### Terminal 2: Run Tests
```bash
export API_BASE_URL=http://localhost:5000
cd tests
pytest -v
```

## Available Endpoints

### SCIM Discovery Endpoints
- `GET /scim/v2/ServiceProviderConfig` - Provider capabilities
- `GET /scim/v2/Schemas` - Supported schemas
- `GET /scim/v2/ResourceTypes` - Resource types

### SCIM User Endpoints
- `GET /scim/v2/Users` - List users
- `POST /scim/v2/Users` - Create user
- `GET /scim/v2/Users/{id}` - Get user
- `PUT /scim/v2/Users/{id}` - Replace user
- `PATCH /scim/v2/Users/{id}` - Update user
- `DELETE /scim/v2/Users/{id}` - Delete user

### SCIM Group Endpoints
- `GET /scim/v2/Groups` - List groups
- `POST /scim/v2/Groups` - Create group
- `GET /scim/v2/Groups/{id}` - Get group
- `PUT /scim/v2/Groups/{id}` - Replace group
- `PATCH /scim/v2/Groups/{id}` - Update group
- `DELETE /scim/v2/Groups/{id}` - Delete group

### Supporting Data Endpoints (Read-Only)
- `GET /api/supporting-data/roles` - List roles
- `GET /api/supporting-data/roles/{id}` - Get role
- `GET /api/supporting-data/departments` - List departments
- `GET /api/supporting-data/departments/{id}` - Get department

## Troubleshooting

### Port Already in Use

If port 5000 is already in use:

```bash
export PORT=8000
python app.py
```

### Import Errors

If you see import errors, ensure you're in the project root directory and dependencies are installed:

```bash
pip install -r requirements.txt
```

### Module Not Found

Make sure you're running from the project root directory where `app.py` is located.

## Next Steps

1. ✅ Server is running
2. ✅ Test endpoints with curl or Postman
3. ✅ Run integration tests
4. ✅ Review API documentation in `examples/request-response-examples.md`
5. ✅ Check compliance documentation in `COMPLIANCE.md`

## Development Mode

The server runs in debug mode by default, which provides:
- Auto-reload on code changes
- Detailed error messages
- Interactive debugger

For production, set `DEBUG=False`.

## Support

- See `README.md` for project overview
- See `ARCHITECTURE.md` for system design
- See `examples/request-response-examples.md` for API examples
- See `tests/README.md` for testing documentation