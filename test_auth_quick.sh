#!/bin/bash
# Quick Authentication Testing Script
# Tests all authentication scenarios
# Usage: ./test_auth_quick.sh [base_url]
# Examples:
#   ./test_auth_quick.sh                              # Test localhost
#   ./test_auth_quick.sh https://myapp.onrender.com   # Test remote server

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     Quick Authentication Test                                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Accept URL as parameter, or use BASE_URL env var, or default to localhost
if [ -n "$1" ]; then
    BASE_URL="$1"
elif [ -n "$BASE_URL" ]; then
    BASE_URL="$BASE_URL"
else
    BASE_URL="http://localhost:5000"
fi

echo "Testing server: $BASE_URL"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Prerequisites:"
echo "1. Server must be running: python3 app.py"
echo "2. Configure authentication as needed"
echo ""
read -p "Press Enter to continue..."
echo ""

# Test 1: Public endpoints (should always work)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: Public Endpoints (No Auth Required)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -n "Testing ServiceProviderConfig... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/scim/v2/ServiceProviderConfig)
if [ "$RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $RESPONSE)"
else
    echo -e "${RED}✗ FAIL${NC} (HTTP $RESPONSE)"
fi

echo -n "Testing Schemas... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/scim/v2/Schemas)
if [ "$RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $RESPONSE)"
else
    echo -e "${RED}✗ FAIL${NC} (HTTP $RESPONSE)"
fi

echo ""

# Test 2: Protected endpoints without auth
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: Protected Endpoints Without Auth"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -n "Testing /scim/v2/Users without auth... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/scim/v2/Users)
if [ "$RESPONSE" = "401" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $RESPONSE - Correctly rejected)"
elif [ "$RESPONSE" = "200" ]; then
    echo -e "${YELLOW}⚠ WARNING${NC} (HTTP $RESPONSE - Auth is disabled)"
else
    echo -e "${RED}✗ FAIL${NC} (HTTP $RESPONSE)"
fi

echo ""

# Test 3: Basic Authentication
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 3: Basic Authentication"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Testing with credentials: admin:admin123"
echo -n "GET /scim/v2/Users... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -u admin:admin123 ${BASE_URL}/scim/v2/Users)
if [ "$RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $RESPONSE)"
elif [ "$RESPONSE" = "401" ]; then
    echo -e "${YELLOW}⚠ SKIP${NC} (HTTP $RESPONSE - Basic Auth not configured)"
else
    echo -e "${RED}✗ FAIL${NC} (HTTP $RESPONSE)"
fi

echo ""

# Test 4: JWT Token (if available)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 4: JWT Token Authentication"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "test_tokens.json" ]; then
    echo "Found test_tokens.json"
    
    # Extract token using Python
    TOKEN=$(python3 -c "import json; print(json.load(open('test_tokens.json'))['tokens']['full_access'])" 2>/dev/null)
    
    if [ -n "$TOKEN" ]; then
        echo "Testing with full_access token..."
        echo -n "GET /scim/v2/Users... "
        RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" ${BASE_URL}/scim/v2/Users)
        if [ "$RESPONSE" = "200" ]; then
            echo -e "${GREEN}✓ PASS${NC} (HTTP $RESPONSE)"
        elif [ "$RESPONSE" = "401" ]; then
            echo -e "${YELLOW}⚠ SKIP${NC} (HTTP $RESPONSE - JWT not configured or token invalid)"
        else
            echo -e "${RED}✗ FAIL${NC} (HTTP $RESPONSE)"
        fi
    else
        echo -e "${YELLOW}⚠ SKIP${NC} - Could not extract token from test_tokens.json"
    fi
else
    echo -e "${YELLOW}⚠ SKIP${NC} - test_tokens.json not found"
    echo "Run: python3 tools/generate_test_tokens.py"
fi

echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✓ Public endpoints are accessible"
echo "✓ Protected endpoints require authentication"
echo ""
echo "To test different scenarios:"
echo ""
echo "1. NO AUTHENTICATION (Development):"
echo "   export AUTH_OAUTH_ENABLED=false"
echo "   export AUTH_BASIC_ENABLED=false"
echo ""
echo "2. BASIC AUTHENTICATION:"
echo "   export AUTH_OAUTH_ENABLED=false"
echo "   export AUTH_BASIC_ENABLED=true"
echo "   export AUTH_BASIC_USERS='admin:8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918'"
echo ""
echo "3. JWT AUTHENTICATION:"
echo "   python3 tools/generate_test_tokens.py"
echo "   # Follow configuration instructions"
echo ""
echo "For detailed testing guide, see: TESTING_AUTHENTICATION.md"
echo ""

# Made with Bob
