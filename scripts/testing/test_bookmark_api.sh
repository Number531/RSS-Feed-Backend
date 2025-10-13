#!/bin/bash
# Comprehensive Bookmark API Test Script

BASE_URL="http://localhost:8000/api/v1"
PASSED=0
FAILED=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "🔖 Bookmark API Integration Tests"
echo "============================================================"
echo ""

# Test 1: Login to get token
echo "Test 1: User Login"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"tech@example.com","password":"TechPass123!"}')

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Got authentication token"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Failed to get token"
    ((FAILED++))
    exit 1
fi
echo ""

# Test 2: Get an article ID to bookmark
echo "Test 2: Get Article ID"
ARTICLES_RESPONSE=$(curl -s "$BASE_URL/articles/?page_size=1")
ARTICLE_ID=$(echo $ARTICLES_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['articles'][0]['id'])" 2>/dev/null)

if [ -n "$ARTICLE_ID" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Got article ID: $ARTICLE_ID"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Failed to get article"
    ((FAILED++))
fi
echo ""

# Test 3: Create a bookmark
echo "Test 3: Create Bookmark"
CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/bookmarks/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"article_id\":\"$ARTICLE_ID\",\"collection\":\"To Read\",\"notes\":\"Test bookmark\"}")

BOOKMARK_ID=$(echo $CREATE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)

if [ -n "$BOOKMARK_ID" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Created bookmark: $BOOKMARK_ID"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Failed to create bookmark"
    echo "Response: $CREATE_RESPONSE"
    ((FAILED++))
fi
echo ""

# Test 4: Try to create duplicate bookmark (should fail)
echo "Test 4: Create Duplicate Bookmark (should fail with 409)"
DUPLICATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/bookmarks/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"article_id\":\"$ARTICLE_ID\",\"collection\":\"To Read\"}")

HTTP_CODE=$(echo "$DUPLICATE_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "409" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Correctly rejected duplicate bookmark (409)"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Expected 409, got $HTTP_CODE"
    ((FAILED++))
fi
echo ""

# Test 5: List bookmarks
echo "Test 5: List Bookmarks"
LIST_RESPONSE=$(curl -s "$BASE_URL/bookmarks/" \
  -H "Authorization: Bearer $TOKEN")

TOTAL=$(echo $LIST_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])" 2>/dev/null)

if [ -n "$TOTAL" ] && [ "$TOTAL" -ge 1 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Listed $TOTAL bookmark(s)"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Failed to list bookmarks"
    ((FAILED++))
fi
echo ""

# Test 6: Get collections
echo "Test 6: Get Collections"
COLLECTIONS_RESPONSE=$(curl -s "$BASE_URL/bookmarks/collections" \
  -H "Authorization: Bearer $TOKEN")

COLLECTION_COUNT=$(echo $COLLECTIONS_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])" 2>/dev/null)

if [ -n "$COLLECTION_COUNT" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Found $COLLECTION_COUNT collection(s)"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Failed to get collections"
    ((FAILED++))
fi
echo ""

# Test 7: Check bookmark status
echo "Test 7: Check Bookmark Status"
CHECK_RESPONSE=$(curl -s "$BASE_URL/bookmarks/check/$ARTICLE_ID" \
  -H "Authorization: Bearer $TOKEN")

IS_BOOKMARKED=$(echo $CHECK_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['is_bookmarked'])" 2>/dev/null)

if [ "$IS_BOOKMARKED" = "True" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Bookmark status is True"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Expected is_bookmarked=True"
    ((FAILED++))
fi
echo ""

# Test 8: Get single bookmark
echo "Test 8: Get Single Bookmark"
GET_RESPONSE=$(curl -s "$BASE_URL/bookmarks/$BOOKMARK_ID" \
  -H "Authorization: Bearer $TOKEN")

RETRIEVED_ID=$(echo $GET_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)

if [ "$RETRIEVED_ID" = "$BOOKMARK_ID" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Retrieved bookmark: $BOOKMARK_ID"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Failed to retrieve bookmark"
    ((FAILED++))
fi
echo ""

# Test 9: Update bookmark
echo "Test 9: Update Bookmark"
UPDATE_RESPONSE=$(curl -s -X PATCH "$BASE_URL/bookmarks/$BOOKMARK_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"collection":"Archive","notes":"Updated notes"}')

UPDATED_COLLECTION=$(echo $UPDATE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['collection'])" 2>/dev/null)

if [ "$UPDATED_COLLECTION" = "Archive" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Updated bookmark collection to Archive"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Failed to update bookmark"
    ((FAILED++))
fi
echo ""

# Test 10: Filter by collection
echo "Test 10: Filter by Collection"
FILTER_RESPONSE=$(curl -s "$BASE_URL/bookmarks/?collection=Archive" \
  -H "Authorization: Bearer $TOKEN")

FILTERED_COUNT=$(echo $FILTER_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])" 2>/dev/null)

if [ -n "$FILTERED_COUNT" ] && [ "$FILTERED_COUNT" -ge 1 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Filtered bookmarks: $FILTERED_COUNT in Archive"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Failed to filter bookmarks"
    ((FAILED++))
fi
echo ""

# Test 11: Delete bookmark
echo "Test 11: Delete Bookmark"
DELETE_RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE_URL/bookmarks/$BOOKMARK_ID" \
  -H "Authorization: Bearer $TOKEN")

DELETE_CODE=$(echo "$DELETE_RESPONSE" | tail -n1)

if [ "$DELETE_CODE" = "204" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Deleted bookmark (204)"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Failed to delete bookmark (expected 204, got $DELETE_CODE)"
    ((FAILED++))
fi
echo ""

# Test 12: Verify deletion
echo "Test 12: Verify Deletion"
VERIFY_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/bookmarks/$BOOKMARK_ID" \
  -H "Authorization: Bearer $TOKEN")

VERIFY_CODE=$(echo "$VERIFY_RESPONSE" | tail -n1)

if [ "$VERIFY_CODE" = "404" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Bookmark not found after deletion (404)"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Bookmark still exists (expected 404, got $VERIFY_CODE)"
    ((FAILED++))
fi
echo ""

# Test 13: Unauthorized access
echo "Test 13: Unauthorized Access (no token)"
UNAUTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/bookmarks/")
UNAUTH_CODE=$(echo "$UNAUTH_RESPONSE" | tail -n1)

if [ "$UNAUTH_CODE" = "401" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Correctly rejected unauthorized request (401)"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Expected 401, got $UNAUTH_CODE"
    ((FAILED++))
fi
echo ""

# Summary
echo "============================================================"
echo "📊 Test Summary"
echo "============================================================"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo -e "Total:  $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    exit 1
fi
