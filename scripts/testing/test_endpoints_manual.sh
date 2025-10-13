#!/bin/bash

# Manual Endpoint Testing Script
# Tests votes and comments endpoints

BASE_URL="http://localhost:8000"
API_PREFIX="/api/v1"

echo "======================================"
echo "🧪 Testing Votes & Comments Endpoints"
echo "======================================"
echo ""

# Colors
GREEN='\033[0.32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local expected_status=$3
    local description=$4
    local data=$5
    local headers=$6
    
    echo -n "Testing: $description... "
    
    if [ -n "$data" ] && [ -n "$headers" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$API_PREFIX$endpoint" \
            -H "Content-Type: application/json" \
            -H "$headers" \
            -d "$data")
    elif [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$API_PREFIX$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    elif [ -n "$headers" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$API_PREFIX$endpoint" \
            -H "$headers")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$API_PREFIX$endpoint")
    fi
    
    status_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$status_code" == "$expected_status" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $status_code)"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (Expected HTTP $expected_status, got $status_code)"
        echo "  Response: $body"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo "Step 1: Testing Authentication Endpoints"
echo "----------------------------------------"

# Register a test user
USER_DATA='{"username":"testuser","email":"test@example.com","password":"testpass123"}'
test_endpoint "POST" "/auth/register" "201" "Register user" "$USER_DATA"
sleep 1

# Login
LOGIN_DATA='{"email":"test@example.com","password":"testpass123"}'
RESPONSE=$(curl -s -X POST "$BASE_URL$API_PREFIX/auth/login" \
    -H "Content-Type: application/json" \
    -d "$LOGIN_DATA")

TOKEN=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}✗ Failed to get access token${NC}"
    echo "Login response: $RESPONSE"
    exit 1
else
    echo -e "${GREEN}✓ Got access token${NC}"
    AUTH_HEADER="Authorization: Bearer $TOKEN"
fi

echo ""
echo "Step 2: Testing Votes Endpoints (WITHOUT AUTH - should fail)"
echo "------------------------------------------------------------"

# Test votes without authentication (should fail with 401)
VOTE_DATA='{"article_id":"550e8400-e29b-41d4-a716-446655440000","vote_value":1}'
test_endpoint "POST" "/votes/" "401" "Cast vote without auth (expect 401)" "$VOTE_DATA"

echo ""
echo "Step 3: Testing Comments Endpoints (WITHOUT AUTH - should fail)"
echo "----------------------------------------------------------------"

# Test comments without authentication (should fail with 401)
COMMENT_DATA='{"article_id":"550e8400-e29b-41d4-a716-446655440000","content":"Test comment"}'
test_endpoint "POST" "/comments/" "401" "Create comment without auth (expect 401)" "$COMMENT_DATA"

echo ""
echo "Step 4: Testing Votes Endpoints (WITH AUTH - should fail with 404 for non-existent article)"
echo "-----------------------------------------------------------------------------------------"

# Test votes with authentication but non-existent article (should fail with 404)
test_endpoint "POST" "/votes/" "404" "Cast vote on non-existent article (expect 404)" "$VOTE_DATA" "$AUTH_HEADER"

echo ""
echo "Step 5: Testing Comments Endpoints (WITH AUTH - should fail with 404 for non-existent article)"
echo "---------------------------------------------------------------------------------------------"

# Test comments with authentication but non-existent article (should fail with 404)
test_endpoint "POST" "/comments/" "404" "Create comment on non-existent article (expect 404)" "$COMMENT_DATA" "$AUTH_HEADER"

echo ""
echo "Step 6: Testing GET endpoints (should work without auth)"
echo "--------------------------------------------------------"

# Test GET endpoints
test_endpoint "GET" "/votes/article/550e8400-e29b-41d4-a716-446655440000" "401" "Get user vote (expect 401 without auth)" "" ""
test_endpoint "GET" "/comments/article/550e8400-e29b-41d4-a716-446655440000" "200" "Get article comments (should work)" "" ""

echo ""
echo "========================================"
echo "📊 Test Summary"
echo "========================================"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo "Total:  $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
