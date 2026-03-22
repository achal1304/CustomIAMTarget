#!/bin/bash
# Quick script to get authentication tokens for testing
# Usage: ./get_tokens.sh [base_url] [token_type]
# Examples:
#   ./get_tokens.sh                                           # Show all tokens (localhost)
#   ./get_tokens.sh https://myapp.onrender.com                # Show all tokens (remote)
#   ./get_tokens.sh https://myapp.onrender.com full_access    # Get specific token (remote)
#   ./get_tokens.sh localhost full_access                     # Get specific token (localhost)

set -e

# Parse arguments - first arg is URL if it contains http/https or is "localhost"
if [[ "$1" =~ ^https?:// ]] || [[ "$1" == "localhost" ]]; then
    # First arg is URL
    if [ "$1" == "localhost" ]; then
        BASE_URL="http://localhost:5000"
    else
        BASE_URL="$1"
    fi
    TOKEN_TYPE="${2:-}"
elif [ -n "$BASE_URL" ]; then
    # Use environment variable
    TOKEN_TYPE="${1:-}"
else
    # Default to localhost, first arg is token type
    BASE_URL="http://localhost:5000"
    TOKEN_TYPE="${1:-}"
fi

TOKEN_ENDPOINT="$BASE_URL/api/dev/tokens"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         SCIM Token Generator - Quick Access                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Server: $BASE_URL${NC}"
echo ""

# Check if server is running
if ! curl -s -f "$BASE_URL" > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Server is not running at $BASE_URL${NC}"
    if [[ "$BASE_URL" == *"localhost"* ]]; then
        echo -e "${YELLOW}   Start the server first: python3 app.py${NC}"
    else
        echo -e "${YELLOW}   Check if the server is deployed and accessible${NC}"
    fi
    exit 1
fi

# Fetch tokens
echo -e "${BLUE}Fetching tokens from $TOKEN_ENDPOINT...${NC}"
RESPONSE=$(curl -s "$TOKEN_ENDPOINT")

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to fetch tokens${NC}"
    exit 1
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️  jq not found. Install it for better formatting: brew install jq${NC}"
    echo ""
    echo "$RESPONSE"
    exit 0
fi

# TOKEN_TYPE was already set during argument parsing above (line 20 or 23 or 27)
# Don't override it here

if [ -z "$TOKEN_TYPE" ]; then
    # Show all tokens
    echo -e "${GREEN}✓ Tokens fetched successfully!${NC}"
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}JWT TOKENS${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    
    echo "$RESPONSE" | jq -r '.tokens.jwt | to_entries[] | "\n\(.key | ascii_upcase):\n  Description: \(.value.description)\n  Scopes: \(.value.scopes | join(", "))\n  Token: \(.value.token)"'
    
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}BASIC AUTH CREDENTIALS${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    
    echo "$RESPONSE" | jq -r '.tokens.basic_auth | to_entries[] | "\n\(.key | ascii_upcase):\n  Username: \(.value.username)\n  Password: \(.value.password)\n  Auth Header: \(.value.authorization_header)"'
    
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}MTLS CERTIFICATES${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    
    echo "$RESPONSE" | jq -r '.tokens.mtls | to_entries[] | "\n\(.key | ascii_upcase):\n  Identity: \(.value.identity)\n  Certificate: \(.value.certificate)\n  Scopes: \(.value.scopes | join(", "))\n  Description: \(.value.description)"'
    
    echo ""
    echo -e "${YELLOW}Note: Run ./tools/generate_mtls_certs.sh to generate certificates${NC}"
    
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}QUICK USAGE${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${GREEN}Get specific token:${NC}"
    echo "  ./get_tokens.sh full_access"
    echo "  ./get_tokens.sh read_only"
    echo "  ./get_tokens.sh admin"
    echo ""
    echo -e "${GREEN}Use JWT in curl:${NC}"
    echo "  TOKEN=\$(./get_tokens.sh full_access)"
    echo "  curl -H \"Authorization: Bearer \$TOKEN\" $BASE_URL/scim/v2/Users"
    echo ""
    echo -e "${GREEN}Use Basic Auth:${NC}"
    echo "  curl -u admin:admin123 $BASE_URL/scim/v2/Users"
    echo ""
    echo -e "${GREEN}Use mTLS (requires nginx setup):${NC}"
    echo "  curl --cert certs/client-admin.pem --cacert certs/ca-cert.pem https://localhost/scim/v2/Users"
    echo ""
    echo -e "${YELLOW}See TOKEN_GENERATION_GUIDE.md and MTLS_SETUP_GUIDE.md for more examples${NC}"
    
else
    # Get specific token
    case "$TOKEN_TYPE" in
        full_access|read_only|write_only|full_scim|supporting_data)
            TOKEN=$(echo "$RESPONSE" | jq -r ".tokens.jwt.$TOKEN_TYPE.token")
            if [ "$TOKEN" = "null" ]; then
                echo -e "${RED}❌ Token type '$TOKEN_TYPE' not found${NC}"
                exit 1
            fi
            echo "$TOKEN"
            ;;
        admin|testuser|readonly)
            # For basic auth, return the password
            PASSWORD=$(echo "$RESPONSE" | jq -r ".tokens.basic_auth.$TOKEN_TYPE.password")
            if [ "$PASSWORD" = "null" ]; then
                echo -e "${RED}❌ User '$TOKEN_TYPE' not found${NC}"
                exit 1
            fi
            echo "$PASSWORD"
            ;;
        admin_client|readonly_client|scim_client)
            # For mTLS, return the certificate path
            CERT_PATH=$(echo "$RESPONSE" | jq -r ".tokens.mtls.$TOKEN_TYPE.certificate")
            if [ "$CERT_PATH" = "null" ]; then
                echo -e "${RED}❌ Certificate '$TOKEN_TYPE' not found${NC}"
                exit 1
            fi
            echo "$CERT_PATH"
            ;;
        *)
            echo -e "${RED}❌ Unknown token type: $TOKEN_TYPE${NC}"
            echo ""
            echo -e "${YELLOW}Available JWT tokens:${NC}"
            echo "  full_access, read_only, write_only, full_scim, supporting_data"
            echo ""
            echo -e "${YELLOW}Available Basic Auth users:${NC}"
            echo "  admin, testuser, readonly"
            echo ""
            echo -e "${YELLOW}Available mTLS certificates:${NC}"
            echo "  admin_client, readonly_client, scim_client"
            exit 1
            ;;
    esac
fi

# Made with Bob
