#!/bin/bash
# Start SCIM server with NO AUTHENTICATION for easy testing
# Use this for development and testing with Swagger UI / Postman

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   Starting SCIM Server - NO AUTHENTICATION (Testing Mode)   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "⚠️  WARNING: Authentication is DISABLED"
echo "   This is for development and testing only!"
echo ""

# Disable all authentication
export AUTH_OAUTH_ENABLED=false
export AUTH_BASIC_ENABLED=false
export AUTH_MTLS_ENABLED=false

echo "Configuration:"
echo "  - OAuth/JWT: DISABLED"
echo "  - Basic Auth: DISABLED"
echo "  - mTLS: DISABLED"
echo ""
echo "All endpoints are now publicly accessible!"
echo ""
echo "Available Documentation:"
echo "  - Swagger UI: http://localhost:5000/api/docs"
echo "  - Postman Collection: http://localhost:5000/postman_collection.json"
echo "  - OpenAPI Spec: http://localhost:5000/swagger.yaml"
echo ""
echo "Starting server..."
echo ""

# Start the server
python3 app.py

# Made with Bob
