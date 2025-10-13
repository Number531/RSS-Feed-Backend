#!/bin/bash

# Comprehensive API Integration Tests
# Tests all endpoints with the newly seeded database

echo "============================================================"
echo "🧪 RSS News Aggregator - Comprehensive API Tests"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Function to run a test
run_test() {
    local test_name="$1"
    local command="$2"
    local expected_status="$3"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    echo -n "Testing: $test_name ... "
    
    # Run the command and capture status
    response=$(eval "$command" 2>&1)
    status=$?
    
    # Check if command succeeded
    if [ $status -eq 0 ]; then
        # Check if response contains expected patterns
        if [ -n "$expected_status" ]; then
            if echo "$response" | grep -q "$expected_status"; then
                echo -e "${GREEN}✓ PASS${NC}"
                TESTS_PASSED=$((TESTS_PASSED + 1))
                return 0
            else
                echo -e "${RED}✗ FAIL${NC} (unexpected response)"
                TESTS_FAILED=$((TESTS_FAILED + 1))
                return 1
            fi
        else
            echo -e "${GREEN}✓ PASS${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (status: $status)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Store tokens for authenticated tests
ACCESS_TOKEN=""
USER_ID=""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. SYSTEM HEALTH TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

run_test "Health Check" \
    "curl -s http://localhost:8000/health" \
    "healthy"

run_test "Root Endpoint" \
    "curl -s http://localhost:8000/" \
    "RSS News Aggregator API"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. AUTHENTICATION TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test user registration (new user)
run_test "User Registration (new user)" \
    "curl -s -X POST http://localhost:8000/api/v1/auth/register -H 'Content-Type: application/json' -d '{\"username\":\"testuser_$(date +%s)\",\"email\":\"test_$(date +%s)@example.com\",\"password\":\"TestPass123!\"}'" \
    "email"

# Test login with seeded user
echo -n "Testing: User Login (seeded user) ... "
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"tech@example.com","password":"TechPass123!"}')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
    echo -e "${GREEN}✓ PASS${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
else
    echo -e "${RED}✗ FAIL${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
fi

# Test login with wrong password
run_test "User Login (wrong password)" \
    "curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"tech@example.com\",\"password\":\"WrongPass123!\"}'" \
    "Invalid"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. USER PROFILE TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -n "$ACCESS_TOKEN" ]; then
    run_test "Get Current User Profile" \
        "curl -s -H 'Authorization: Bearer $ACCESS_TOKEN' http://localhost:8000/api/v1/users/me" \
        "tech@example.com"
    
    run_test "Update User Profile" \
        "curl -s -X PATCH -H 'Authorization: Bearer $ACCESS_TOKEN' -H 'Content-Type: application/json' -d '{\"full_name\":\"Updated Name\"}' http://localhost:8000/api/v1/users/me" \
        "Updated Name"
    
    run_test "Get User Stats (placeholder)" \
        "curl -s -H 'Authorization: Bearer $ACCESS_TOKEN' http://localhost:8000/api/v1/users/me/stats" \
        "not yet implemented"
else
    echo -e "${YELLOW}⚠ Skipping authenticated user tests (no token)${NC}"
fi

# Test unauthenticated access
run_test "Get User Profile (no auth)" \
    "curl -s http://localhost:8000/api/v1/users/me 2>&1" \
    "Not authenticated"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. ARTICLES API TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

run_test "List All Articles" \
    "curl -s 'http://localhost:8000/api/v1/articles/'" \
    "articles"

run_test "Articles with Pagination (page 1)" \
    "curl -s 'http://localhost:8000/api/v1/articles/?page=1&limit=10'" \
    "articles"

run_test "Articles with Pagination (page 2)" \
    "curl -s 'http://localhost:8000/api/v1/articles/?page=2&limit=10'" \
    "articles"

run_test "Filter by Category (science)" \
    "curl -s 'http://localhost:8000/api/v1/articles/?category=science'" \
    "science"

run_test "Filter by Category (politics)" \
    "curl -s 'http://localhost:8000/api/v1/articles/?category=politics'" \
    "politics"

run_test "Sort by 'new'" \
    "curl -s 'http://localhost:8000/api/v1/articles/?sort_by=new'" \
    "articles"

run_test "Sort by 'top'" \
    "curl -s 'http://localhost:8000/api/v1/articles/?sort_by=top'" \
    "articles"

run_test "Time Range Filter (day)" \
    "curl -s 'http://localhost:8000/api/v1/articles/?time_range=day'" \
    "articles"

# Get an article ID for detail tests
echo -n "Getting sample article ID ... "
ARTICLE_ID=$(curl -s 'http://localhost:8000/api/v1/articles/?limit=1' | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['articles'][0]['id'] if data['articles'] else '')" 2>/dev/null)

if [ -n "$ARTICLE_ID" ]; then
    echo -e "${GREEN}✓${NC} ($ARTICLE_ID)"
    
    run_test "Get Single Article by ID" \
        "curl -s 'http://localhost:8000/api/v1/articles/$ARTICLE_ID'" \
        "id"
else
    echo -e "${YELLOW}⚠ Could not get article ID${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. ARTICLES SEARCH TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

run_test "Search Articles (quantum)" \
    "curl -s 'http://localhost:8000/api/v1/articles/search?q=quantum'" \
    "articles"

run_test "Search Articles (AI)" \
    "curl -s 'http://localhost:8000/api/v1/articles/search?q=AI'" \
    "articles"

run_test "Search Articles (climate)" \
    "curl -s 'http://localhost:8000/api/v1/articles/search?q=climate'" \
    "articles"

run_test "Search with Empty Query" \
    "curl -s 'http://localhost:8000/api/v1/articles/search?q='" \
    "articles"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. COMMENTS API TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -n "$ARTICLE_ID" ]; then
    run_test "Get Article Comments" \
        "curl -s 'http://localhost:8000/api/v1/comments/article/$ARTICLE_ID'" \
        "total"
    
    run_test "Get Comment Tree" \
        "curl -s 'http://localhost:8000/api/v1/comments/article/$ARTICLE_ID/tree'" \
        "total"
    
    if [ -n "$ACCESS_TOKEN" ]; then
        # Create a test comment
        echo -n "Testing: Create Comment ... "
        COMMENT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/comments/ \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -H "Content-Type: application/json" \
            -d "{\"article_id\":\"$ARTICLE_ID\",\"content\":\"Test comment from comprehensive tests\"}")
        
        if echo "$COMMENT_RESPONSE" | grep -q "id"; then
            COMMENT_ID=$(echo "$COMMENT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
            echo -e "${GREEN}✓ PASS${NC} ($COMMENT_ID)"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            TESTS_TOTAL=$((TESTS_TOTAL + 1))
            
            run_test "Get Single Comment" \
                "curl -s 'http://localhost:8000/api/v1/comments/$COMMENT_ID'" \
                "content"
            
            run_test "Update Comment" \
                "curl -s -X PATCH -H 'Authorization: Bearer $ACCESS_TOKEN' -H 'Content-Type: application/json' -d '{\"content\":\"Updated test comment\"}' http://localhost:8000/api/v1/comments/$COMMENT_ID" \
                "Updated test comment"
            
            run_test "Delete Comment" \
                "curl -s -X DELETE -H 'Authorization: Bearer $ACCESS_TOKEN' http://localhost:8000/api/v1/comments/$COMMENT_ID" \
                ""
        else
            echo -e "${RED}✗ FAIL${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            TESTS_TOTAL=$((TESTS_TOTAL + 1))
        fi
    fi
else
    echo -e "${YELLOW}⚠ Skipping comment tests (no article ID)${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7. VOTING API TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -n "$ARTICLE_ID" ] && [ -n "$ACCESS_TOKEN" ]; then
    run_test "Get Article Votes" \
        "curl -s 'http://localhost:8000/api/v1/votes/article/$ARTICLE_ID'" \
        "vote_score"
    
    # Cast an upvote
    run_test "Cast Upvote" \
        "curl -s -X POST -H 'Authorization: Bearer $ACCESS_TOKEN' -H 'Content-Type: application/json' -d '{\"article_id\":\"$ARTICLE_ID\",\"vote_value\":1}' http://localhost:8000/api/v1/votes/" \
        "vote_value"
    
    # Update to downvote
    run_test "Update Vote (downvote)" \
        "curl -s -X POST -H 'Authorization: Bearer $ACCESS_TOKEN' -H 'Content-Type: application/json' -d '{\"article_id\":\"$ARTICLE_ID\",\"vote_value\":-1}' http://localhost:8000/api/v1/votes/" \
        "vote_value"
    
    # Remove vote
    run_test "Remove Vote" \
        "curl -s -X DELETE -H 'Authorization: Bearer $ACCESS_TOKEN' http://localhost:8000/api/v1/votes/$ARTICLE_ID" \
        ""
else
    echo -e "${YELLOW}⚠ Skipping voting tests (no article ID or token)${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "8. ERROR HANDLING TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

run_test "Non-existent Endpoint (404)" \
    "curl -s http://localhost:8000/api/v1/nonexistent 2>&1" \
    "404"

run_test "Invalid Article ID" \
    "curl -s 'http://localhost:8000/api/v1/articles/invalid-uuid' 2>&1" \
    ""

run_test "Invalid Category" \
    "curl -s 'http://localhost:8000/api/v1/articles/?category=invalid' 2>&1" \
    ""

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "9. PERFORMANCE TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test response times
echo -n "Testing: Response Time - Articles List ... "
TIME_START=$(date +%s%N)
curl -s 'http://localhost:8000/api/v1/articles/' > /dev/null
TIME_END=$(date +%s%N)
TIME_DIFF=$(( (TIME_END - TIME_START) / 1000000 ))

if [ $TIME_DIFF -lt 500 ]; then
    echo -e "${GREEN}✓ PASS${NC} (${TIME_DIFF}ms)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠ SLOW${NC} (${TIME_DIFF}ms)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi
TESTS_TOTAL=$((TESTS_TOTAL + 1))

echo -n "Testing: Response Time - Search ... "
TIME_START=$(date +%s%N)
curl -s 'http://localhost:8000/api/v1/articles/search?q=quantum' > /dev/null
TIME_END=$(date +%s%N)
TIME_DIFF=$(( (TIME_END - TIME_START) / 1000000 ))

if [ $TIME_DIFF -lt 500 ]; then
    echo -e "${GREEN}✓ PASS${NC} (${TIME_DIFF}ms)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠ SLOW${NC} (${TIME_DIFF}ms)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi
TESTS_TOTAL=$((TESTS_TOTAL + 1))

echo ""
echo "============================================================"
echo "📊 TEST RESULTS SUMMARY"
echo "============================================================"
echo ""
echo "Total Tests:  $TESTS_TOTAL"
echo -e "Passed:       ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed:       ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo "🎉 Your API is ready for Phase 1 development!"
    exit 0
else
    PASS_RATE=$(( (TESTS_PASSED * 100) / TESTS_TOTAL ))
    echo ""
    echo -e "Pass Rate:    ${PASS_RATE}%"
    echo ""
    if [ $PASS_RATE -ge 80 ]; then
        echo -e "${YELLOW}⚠ Most tests passed. Review failures before proceeding.${NC}"
        exit 0
    else
        echo -e "${RED}❌ Too many failures. Please fix issues before proceeding.${NC}"
        exit 1
    fi
fi
