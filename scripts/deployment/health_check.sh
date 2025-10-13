#!/bin/bash
# Health Check Script for RSS Feed Backend
# Usage: ./health_check.sh <base_url>

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="${1:-http://localhost:8000}"
MAX_RETRIES=30
RETRY_DELAY=2

echo "========================================="
echo "RSS Feed Backend Health Check"
echo "========================================="
echo "Base URL: $BASE_URL"
echo "========================================="

# Function to make HTTP request with retries
check_endpoint() {
    local endpoint=$1
    local description=$2
    local retries=0
    
    echo -n "Checking $description... "
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -f -s -o /dev/null "$BASE_URL$endpoint"; then
            echo -e "${GREEN}✓ PASS${NC}"
            return 0
        fi
        
        retries=$((retries + 1))
        if [ $retries -lt $MAX_RETRIES ]; then
            sleep $RETRY_DELAY
        fi
    done
    
    echo -e "${RED}✗ FAIL${NC}"
    return 1
}

# Function to check endpoint with JSON response
check_json_endpoint() {
    local endpoint=$1
    local description=$2
    
    echo -n "Checking $description... "
    
    response=$(curl -f -s "$BASE_URL$endpoint" || echo "FAILED")
    
    if [ "$response" != "FAILED" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        echo "  Response: $response"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        return 1
    fi
}

# Run health checks
echo ""
echo "Running health checks..."
echo ""

FAILED=0

# 1. Basic Health Check
check_endpoint "/health" "Application Health" || FAILED=$((FAILED + 1))

# 2. Database Health Check
check_endpoint "/api/v1/health/db" "Database Connection" || FAILED=$((FAILED + 1))

# 3. API V1 Root
check_endpoint "/api/v1/" "API V1 Root" || FAILED=$((FAILED + 1))

# 4. OpenAPI Docs
check_endpoint "/docs" "OpenAPI Documentation" || FAILED=$((FAILED + 1))

# 5. Reading History Endpoints (if authenticated)
echo ""
echo "Note: Some endpoints require authentication and will return 401 (expected)"
echo ""

# Summary
echo ""
echo "========================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All health checks passed! ✓${NC}"
    echo "========================================="
    exit 0
else
    echo -e "${RED}$FAILED health check(s) failed! ✗${NC}"
    echo "========================================="
    exit 1
fi
