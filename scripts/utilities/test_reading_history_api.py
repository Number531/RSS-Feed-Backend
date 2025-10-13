#!/usr/bin/env python
"""Comprehensive integration tests for reading history API."""
import sys
import asyncio
import httpx
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "test.history@example.com"
TEST_PASSWORD = "TestHistory123!"


async def get_auth_token() -> str:
    """Get authentication token for test user."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to login: {response.text}")
        
        data = response.json()
        return data["access_token"]


async def get_test_article_id(token: str) -> str:
    """Get a test article ID."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(
            f"{API_BASE_URL}/articles",
            headers={"Authorization": f"Bearer {token}"},
            params={"page": 1, "page_size": 1}
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get articles (status {response.status_code}): {response.text}")
        
        data = response.json()
        if not data.get("articles") or len(data["articles"]) == 0:
            raise Exception(f"No articles found. Response: {data}")
        
        return data["articles"][0]["id"]


async def test_api():
    """Test reading history API endpoints."""
    print("=" * 60)
    print("🔐 Authenticating...")
    token = await get_auth_token()
    print(f"✅ Got auth token: {token[:20]}...")
    print()
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("=" * 60)
    print("📖 Getting test article...")
    article_id = await get_test_article_id(token)
    print(f"✅ Test article ID: {article_id}")
    print()
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        
        # Test 1: Record a basic view
        print("Test 1: Record basic article view")
        response = await client.post(
            f"{API_BASE_URL}/reading-history/",
            headers=headers,
            json={
                "article_id": article_id
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Recorded view: {data['id']}")
            print(f"   - Article ID: {data['article_id']}")
            print(f"   - Viewed at: {data['viewed_at']}")
        else:
            print(f"❌ Failed: {response.text}")
        print()
        
        # Test 2: Record view with engagement metrics
        print("Test 2: Record view with engagement metrics")
        response = await client.post(
            f"{API_BASE_URL}/reading-history/",
            headers=headers,
            json={
                "article_id": article_id,
                "duration_seconds": 180,
                "scroll_percentage": 95.5
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Recorded view with metrics: {data['id']}")
            print(f"   - Duration: {data.get('duration_seconds')}s")
            print(f"   - Scroll: {data.get('scroll_percentage')}%")
        else:
            print(f"❌ Failed: {response.text}")
        print()
        
        # Test 3: Get reading history
        print("Test 3: Get reading history")
        response = await client.get(
            f"{API_BASE_URL}/reading-history/",
            headers=headers,
            params={"skip": 0, "limit": 10}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved {len(data['items'])} items (total: {data['total']})")
            for item in data['items'][:3]:
                print(f"   - {item['viewed_at']}: {item.get('article_title', 'N/A')[:40]}...")
        else:
            print(f"❌ Failed: {response.text}")
        print()
        
        # Test 4: Get recently read articles
        print("Test 4: Get recently read articles")
        response = await client.get(
            f"{API_BASE_URL}/reading-history/recent",
            headers=headers,
            params={"days": 7, "limit": 5}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved {len(data)} recent articles")
        else:
            print(f"❌ Failed: {response.text}")
        print()
        
        # Test 5: Get reading statistics
        print("Test 5: Get reading statistics")
        response = await client.get(
            f"{API_BASE_URL}/reading-history/stats",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Statistics retrieved:")
            print(f"   - Total views: {data['total_views']}")
            print(f"   - Total time: {data['total_reading_time_seconds']}s ({data['total_reading_time_seconds'] // 60}m)")
            print(f"   - Avg time: {data['average_reading_time_seconds']}s")
        else:
            print(f"❌ Failed: {response.text}")
        print()
        
        # Test 6: Get statistics with date range
        print("Test 6: Get statistics with date range")
        start_date = (datetime.utcnow() - timedelta(days=1)).isoformat()
        end_date = datetime.utcnow().isoformat()
        response = await client.get(
            f"{API_BASE_URL}/reading-history/stats",
            headers=headers,
            params={
                "start_date": start_date,
                "end_date": end_date
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Statistics (last 24h): {data['total_views']} views")
        else:
            print(f"❌ Failed: {response.text}")
        print()
        
        # Test 7: Pagination
        print("Test 7: Test pagination")
        response1 = await client.get(
            f"{API_BASE_URL}/reading-history/",
            headers=headers,
            params={"skip": 0, "limit": 1}
        )
        response2 = await client.get(
            f"{API_BASE_URL}/reading-history/",
            headers=headers,
            params={"skip": 1, "limit": 1}
        )
        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()
            print(f"✅ Page 1: {len(data1['items'])} items")
            print(f"✅ Page 2: {len(data2['items'])} items")
        else:
            print("❌ Failed pagination test")
        print()
        
        # Test 8: Invalid requests
        print("Test 8: Test validation errors")
        
        # Invalid scroll percentage
        response = await client.post(
            f"{API_BASE_URL}/reading-history/",
            headers=headers,
            json={
                "article_id": article_id,
                "scroll_percentage": 150  # Invalid: > 100
            }
        )
        if response.status_code == 422:
            print("✅ Validation error for invalid scroll percentage")
        else:
            print(f"❌ Expected 422, got {response.status_code}")
        
        # Invalid limit
        response = await client.get(
            f"{API_BASE_URL}/reading-history/",
            headers=headers,
            params={"limit": 200}  # Invalid: > 100
        )
        if response.status_code in (400, 422):  # Accept both 400 and 422
            print("✅ Validation error for invalid limit")
        else:
            print(f"❌ Expected 400 or 422, got {response.status_code}")
        print()
        
        # Test 9: Clear partial history
        print("Test 9: Clear partial history")
        cutoff = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        response = await client.request(
            "DELETE",
            f"{API_BASE_URL}/reading-history/",
            headers=headers,
            json={"before_date": cutoff}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Cleared {data['deleted_count']} records")
            print(f"   Message: {data['message']}")
        else:
            print(f"❌ Failed: {response.text}")
        print()
        
        # Test 10: Clear all remaining history
        print("Test 10: Clear all remaining history")
        response = await client.request(
            "DELETE",
            f"{API_BASE_URL}/reading-history/",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Cleared {data['deleted_count']} records")
        else:
            print(f"❌ Failed: {response.text}")
        print()
        
        # Test 11: Verify empty history
        print("Test 11: Verify history is empty")
        response = await client.get(
            f"{API_BASE_URL}/reading-history/",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            if data['total'] == 0:
                print("✅ History is empty as expected")
            else:
                print(f"❌ Expected empty, but found {data['total']} items")
        else:
            print(f"❌ Failed: {response.text}")
        print()
    
    print("=" * 60)
    print("✅ All API tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("📖 Reading History API Integration Tests")
    print("=" * 60 + "\n")
    
    print("⚠️  Make sure the FastAPI server is running on port 8000")
    print("   (Run: uvicorn app.main:app --reload)")
    print()
    
    try:
        asyncio.run(test_api())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
