#!/usr/bin/env bash

#
# Comprehensive API Endpoint Testing Script
#
# Tests all major API endpoints of the RSS Feed Backend
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE="http://127.0.0.1:8000"
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((TESTS_FAILED++))
}

test_endpoint() {
    local method=$1
    local endpoint=$2
    local expected_status=$3
    local description=$4
    local data=$5
    
    log_test "$description"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$API_BASE$endpoint")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "$expected_status" ]; then
        log_success "$endpoint returned $http_code"
        if [ ! -z "$body" ]; then
            echo "    Response preview: $(echo $body | head -c 100)..."
        fi
    else
        log_error "$endpoint expected $expected_status but got $http_code"
        echo "    Response: $body"
    fi
    
    echo ""
}

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║             RSS Feed Backend - API Endpoint Tests                ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# Health & Status Endpoints
# ============================================================================

echo "═══════════════════════════════════════════════════════════════════"
echo "  1. HEALTH & STATUS ENDPOINTS"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

test_endpoint "GET" "/health" "200" "Health check endpoint"
test_endpoint "GET" "/health/db" "200" "Database health check"
test_endpoint "GET" "/health/redis" "200" "Redis health check"

# ============================================================================
# Authentication Endpoints
# ============================================================================

echo "═══════════════════════════════════════════════════════════════════"
echo "  2. AUTHENTICATION ENDPOINTS"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Note: Registration might fail if user exists, 400/422 is acceptable
test_endpoint "POST" "/api/v1/auth/register" "201" "User registration" \
    '{"username":"testuser_'$RANDOM'","email":"test'$RANDOM'@example.com","password":"TestPass123!"}'

# Login will fail without valid credentials (expected)
log_test "User login (expect 401 with invalid credentials)"
response=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=invalid&password=invalid")
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" = "401" ]; then
    log_success "/api/v1/auth/login returned 401 (as expected)"
else
    log_error "/api/v1/auth/login expected 401 but got $http_code"
fi
echo ""

# ============================================================================
# RSS Sources Endpoints
# ============================================================================

echo "═══════════════════════════════════════════════════════════════════"
echo "  3. RSS SOURCES ENDPOINTS"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

test_endpoint "GET" "/api/v1/rss-sources" "401" "List RSS sources (requires auth)"
test_endpoint "GET" "/api/v1/rss-sources/popular" "200" "Get popular RSS sources"

# ============================================================================
# Articles Endpoints
# ============================================================================

echo "═══════════════════════════════════════════════════════════════════"
echo "  4. ARTICLES ENDPOINTS"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

test_endpoint "GET" "/api/v1/articles" "200" "List articles"
test_endpoint "GET" "/api/v1/articles/trending" "200" "Get trending articles"
test_endpoint "GET" "/api/v1/articles/search?q=test" "200" "Search articles"

# ============================================================================
# User Profile Endpoints
# ============================================================================

echo "═══════════════════════════════════════════════════════════════════"
echo "  5. USER PROFILE ENDPOINTS"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

test_endpoint "GET" "/api/v1/users/me" "401" "Get current user (requires auth)"
test_endpoint "GET" "/api/v1/users/me/preferences" "401" "Get user preferences (requires auth)"

# ============================================================================
# Bookmarks Endpoints
# ============================================================================

echo "═══════════════════════════════════════════════════════════════════"
echo "  6. BOOKMARKS ENDPOINTS"
echo "═══════════================================================================"
echo ""

test_endpoint "GET" "/api/v1/bookmarks" "401" "List bookmarks (requires auth)"
test_endpoint "GET" "/api/v1/bookmarks/folders" "401" "List bookmark folders (requires auth)"

# ============================================================================
# Reading History Endpoints
# ============================================================================

echo "═══════════════════════════════════════════════════════════════════"
echo "  7. READING HISTORY ENDPOINTS"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

test_endpoint "GET" "/api/v1/reading-history" "401" "Get reading history (requires auth)"
test_endpoint "GET" "/api/v1/reading-history/stats" "401" "Get reading stats (requires auth)"

# ============================================================================
# Comments Endpoints
# ============================================================================

echo "═══════════════════════════════════════════════════════════════════"
echo "  8. COMMENTS ENDPOINTS"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

test_endpoint "GET" "/api/v1/comments?article_id=1" "200" "List comments for article"

# ============================================================================
# Notifications Endpoints
# ============================================================================

echo "═══════════════════════════════════════════════════════════════════"
echo "  9. NOTIFICATIONS ENDPOINTS"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

test_endpoint "GET" "/api/v1/notifications" "401" "List notifications (requires auth)"
test_endpoint "GET" "/api/v1/notifications/unread-count" "401" "Unread count (requires auth)"

# ============================================================================
# API Documentation Endpoints
# ============================================================================

echo "═══════════════════════════════════════════════════════════════════"
echo "  10. API DOCUMENTATION"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

test_endpoint "GET" "/docs" "200" "Swagger UI documentation"
test_endpoint "GET" "/redoc" "200" "ReDoc documentation"
test_endpoint "GET" "/openapi.json" "200" "OpenAPI schema"

# ============================================================================
# Metrics & Monitoring
# ============================================================================

echo "═══════════════════════════════════════════════════════════════════"
echo "  11. METRICS & MONITORING"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

test_endpoint "GET" "/metrics" "200" "Prometheus metrics"

# ============================================================================
# Results Summary
# ============================================================================

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                         TEST RESULTS                             ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Tests Passed:${NC} $TESTS_PASSED"
echo -e "${RED}Tests Failed:${NC} $TESTS_FAILED"
echo ""

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
SUCCESS_RATE=$((TESTS_PASSED * 100 / TOTAL_TESTS))

echo "Success Rate: $SUCCESS_RATE%"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All API endpoint tests passed!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed. Review output above.${NC}"
    exit 1
fi
