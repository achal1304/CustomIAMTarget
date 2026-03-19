#!/bin/bash
# Start the SCIM 2.0 Service Provider Server

echo "Starting SCIM 2.0 Service Provider..."
echo ""

# Set default configuration
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-5000}
export BASE_URL=${BASE_URL:-http://localhost:5000}
export DEBUG=${DEBUG:-True}

# Start the server
python3 app.py

# Made with Bob
