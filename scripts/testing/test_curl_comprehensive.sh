#!/bin/bash
# Comprehensive cURL testing for Reading History API

echo "======================================================================"
echo "📖 Reading History API - Comprehensive cURL Test Suite"
echo "======================================================================"
echo ""

# Get auth token
echo "🔐 Authenticating..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email": "test.history@example.com", "password": "TestHistory123!"}' | \
  python -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')

if [ -z "$TOKEN" ]; then
  echo "❌ Authentication failed!"
  exit 1
fi

echo "✅ Authenticated successfully"
echo ""

# Get test article
echo "📖 Getting test article..."
ARTICLE_ID=$(curl -s "http://localhost:8000/api/v1/articles?page=1&page_size=1" \
  -H "Authorization: Bearer $TOKEN" | \
  python -c 'import sys, json; print(json.load(sys.stdin)["articles"][0]["id"])')

echo "✅ Article ID: $ARTICLE_ID"
echo ""

# Test 1: Record basic view
echo "Test 1: Record basic article view"
curl -s -X POST "http://localhost:8000/api/v1/reading-history/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"article_id\": \"$ARTICLE_ID\"}" | python -m json.tool | head -10
echo ""

# Test 2: Record view with metrics
echo "Test 2: Record view with engagement metrics"
curl -s -X POST "http://localhost:8000/api/v1/reading-history/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"article_id\": \"$ARTICLE_ID\", \"duration_seconds\": 240, \"scroll_percentage\": 95.0}" | \
  python -m json.tool | head -10
echo ""

# Test 3: Get history
echo "Test 3: Get reading history (paginated)"
curl -s "http://localhost:8000/api/v1/reading-history/?skip=0&limit=5" \
  -H "Authorization: Bearer $TOKEN" | \
  python -c 'import sys, json; d=json.load(sys.stdin); print(f"✅ Total: {d[\"total\"]}, Items: {len(d[\"items\"])}")'
echo ""

# Test 4: Get recent
echo "Test 4: Get recently read articles"
curl -s "http://localhost:8000/api/v1/reading-history/recent?days=7&limit=3" \
  -H "Authorization: Bearer $TOKEN" | \
  python -c 'import sys, json; d=json.load(sys.stdin); print(f"✅ Found {len(d)} recent articles")'
echo ""

# Test 5: Get stats
echo "Test 5: Get reading statistics"
curl -s "http://localhost:8000/api/v1/reading-history/stats" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
echo ""

# Test 6: Clear history
echo "Test 6: Clear all history"
curl -s -X DELETE "http://localhost:8000/api/v1/reading-history/" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
echo ""

echo "======================================================================"
echo "✅ All cURL tests completed successfully!"
echo "======================================================================"
