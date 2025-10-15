#!/usr/bin/env python3
"""
Comprehensive RSS Feed Endpoints Testing Script
Tests all RSS feed endpoints with proper authentication.
"""
import asyncio
import httpx
from typing import Optional

BASE_URL = "http://localhost:8000/api/v1"
# Using credentials from seed_database.py
TEST_USER = {"username": "tech_enthusiast", "email": "tech@example.com", "password": "TechPass123!"}
TEST_ADMIN = {"username": "news_reader", "email": "reader@example.com", "password": "ReadPass123!"}  # Note: Not actually admin, just second user for testing

# Global variables to store tokens and test data
user_token: Optional[str] = None
admin_token: Optional[str] = None
test_feed_id: Optional[str] = None
existing_feed_id: Optional[str] = None


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_result(endpoint: str, status: int, success: bool, data: dict = None):
    """Print test result in a formatted way."""
    status_icon = "✅" if success else "❌"
    print(f"\n{status_icon} {endpoint}")
    print(f"   Status: {status}")
    if data:
        print(f"   Response: {data}")


async def register_user(client: httpx.AsyncClient, user_data: dict) -> bool:
    """Register a test user."""
    try:
        response = await client.post(f"{BASE_URL}/auth/register", json=user_data)
        return response.status_code in [200, 201, 409]  # 409 = already exists
    except Exception as e:
        print(f"   Warning: Could not register user: {e}")
        return True  # Continue anyway


async def login_user(client: httpx.AsyncClient, credentials: dict) -> Optional[str]:
    """Login and get access token."""
    try:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": credentials["email"],
                "password": credentials["password"]
            }
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    except Exception as e:
        print(f"   Error logging in: {e}")
        return None


async def test_list_feeds(client: httpx.AsyncClient, token: str) -> bool:
    """Test GET /feeds - List all RSS feeds."""
    print_header("TEST 1: List All Feeds")
    
    try:
        # Test basic list
        response = await client.get(
            f"{BASE_URL}/feeds",
            headers={"Authorization": f"Bearer {token}"}
        )
        success = response.status_code == 200
        data = response.json() if success else {"error": response.text}
        print_result("GET /feeds", response.status_code, success, 
                    {"total": data.get("total"), "count": len(data.get("feeds", []))})
        
        # Test with pagination
        response = await client.get(
            f"{BASE_URL}/feeds?page=1&page_size=10",
            headers={"Authorization": f"Bearer {token}"}
        )
        success2 = response.status_code == 200
        data2 = response.json() if success2 else {}
        print_result("GET /feeds?page=1&page_size=10", response.status_code, success2,
                    {"page": data2.get("page"), "page_size": data2.get("page_size")})
        
        # Test with category filter
        response = await client.get(
            f"{BASE_URL}/feeds?category=politics",
            headers={"Authorization": f"Bearer {token}"}
        )
        success3 = response.status_code == 200
        data3 = response.json() if success3 else {}
        print_result("GET /feeds?category=politics", response.status_code, success3,
                    {"filtered_count": len(data3.get("feeds", []))})
        
        # Test with is_active filter
        response = await client.get(
            f"{BASE_URL}/feeds?is_active=true",
            headers={"Authorization": f"Bearer {token}"}
        )
        success4 = response.status_code == 200
        data4 = response.json() if success4 else {}
        print_result("GET /feeds?is_active=true", response.status_code, success4,
                    {"active_feeds": len(data4.get("feeds", []))})
        
        # Store a feed ID for later tests
        global existing_feed_id
        if success and data.get("feeds"):
            existing_feed_id = data["feeds"][0]["id"]
        
        return success and success2 and success3 and success4
    except Exception as e:
        print_result("GET /feeds", 0, False, {"error": str(e)})
        return False


async def test_list_categories(client: httpx.AsyncClient, token: str) -> bool:
    """Test GET /feeds/categories - List feed categories with stats."""
    print_header("TEST 2: List Feed Categories")
    
    try:
        response = await client.get(
            f"{BASE_URL}/feeds/categories",
            headers={"Authorization": f"Bearer {token}"}
        )
        success = response.status_code == 200
        data = response.json() if success else {"error": response.text}
        
        if success:
            print_result("GET /feeds/categories", response.status_code, success,
                        {"categories_count": len(data), "categories": [c.get("category") for c in data[:5]]})
        else:
            print_result("GET /feeds/categories", response.status_code, success, data)
        
        return success
    except Exception as e:
        print_result("GET /feeds/categories", 0, False, {"error": str(e)})
        return False


async def test_get_feed_detail(client: httpx.AsyncClient, token: str) -> bool:
    """Test GET /feeds/{feed_id} - Get single feed details."""
    print_header("TEST 3: Get Feed Detail")
    
    if not existing_feed_id:
        print("⚠️  Skipping: No feed ID available")
        return False
    
    try:
        response = await client.get(
            f"{BASE_URL}/feeds/{existing_feed_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        success = response.status_code == 200
        data = response.json() if success else {"error": response.text}
        
        if success:
            print_result(f"GET /feeds/{existing_feed_id}", response.status_code, success,
                        {"name": data.get("name"), "category": data.get("category"), 
                         "is_active": data.get("is_active")})
        else:
            print_result(f"GET /feeds/{existing_feed_id}", response.status_code, success, data)
        
        return success
    except Exception as e:
        print_result(f"GET /feeds/{existing_feed_id}", 0, False, {"error": str(e)})
        return False


async def test_subscribe_to_feed(client: httpx.AsyncClient, token: str) -> bool:
    """Test POST /feeds/{feed_id}/subscribe - Subscribe to a feed."""
    print_header("TEST 4: Subscribe to Feed")
    
    if not existing_feed_id:
        print("⚠️  Skipping: No feed ID available")
        return False
    
    try:
        response = await client.post(
            f"{BASE_URL}/feeds/{existing_feed_id}/subscribe",
            headers={"Authorization": f"Bearer {token}"},
            json={"notifications_enabled": True}
        )
        success = response.status_code in [200, 201, 409]  # 409 = already subscribed
        data = response.json() if success else {"error": response.text}
        
        if success:
            print_result(f"POST /feeds/{existing_feed_id}/subscribe", response.status_code, success,
                        {"feed_name": data.get("feed", {}).get("name"), 
                         "notifications": data.get("notifications_enabled")})
        else:
            print_result(f"POST /feeds/{existing_feed_id}/subscribe", response.status_code, success, data)
        
        return success
    except Exception as e:
        print_result(f"POST /feeds/{existing_feed_id}/subscribe", 0, False, {"error": str(e)})
        return False


async def test_get_subscriptions(client: httpx.AsyncClient, token: str) -> bool:
    """Test GET /feeds/subscriptions - Get user's subscriptions."""
    print_header("TEST 5: Get User Subscriptions")
    
    try:
        response = await client.get(
            f"{BASE_URL}/feeds/subscriptions",
            headers={"Authorization": f"Bearer {token}"}
        )
        success = response.status_code == 200
        data = response.json() if success else {"error": response.text}
        
        if success:
            print_result("GET /feeds/subscriptions", response.status_code, success,
                        {"total": data.get("total"), "subscriptions": len(data.get("subscriptions", []))})
        else:
            print_result("GET /feeds/subscriptions", response.status_code, success, data)
        
        return success
    except Exception as e:
        print_result("GET /feeds/subscriptions", 0, False, {"error": str(e)})
        return False


async def test_get_subscribed_feed_ids(client: httpx.AsyncClient, token: str) -> bool:
    """Test GET /feeds/subscribed - Get list of subscribed feed IDs."""
    print_header("TEST 6: Get Subscribed Feed IDs")
    
    try:
        response = await client.get(
            f"{BASE_URL}/feeds/subscribed",
            headers={"Authorization": f"Bearer {token}"}
        )
        success = response.status_code == 200
        data = response.json() if success else {"error": response.text}
        
        if success:
            print_result("GET /feeds/subscribed", response.status_code, success,
                        {"subscribed_feeds_count": len(data)})
        else:
            print_result("GET /feeds/subscribed", response.status_code, success, data)
        
        return success
    except Exception as e:
        print_result("GET /feeds/subscribed", 0, False, {"error": str(e)})
        return False


async def test_update_subscription(client: httpx.AsyncClient, token: str) -> bool:
    """Test PUT /feeds/{feed_id}/subscription - Update subscription preferences."""
    print_header("TEST 7: Update Subscription Preferences")
    
    if not existing_feed_id:
        print("⚠️  Skipping: No feed ID available")
        return False
    
    try:
        response = await client.put(
            f"{BASE_URL}/feeds/{existing_feed_id}/subscription",
            headers={"Authorization": f"Bearer {token}"},
            json={"notifications_enabled": False}
        )
        success = response.status_code == 200
        data = response.json() if success else {"error": response.text}
        
        if success:
            print_result(f"PUT /feeds/{existing_feed_id}/subscription", response.status_code, success,
                        {"notifications_enabled": data.get("notifications_enabled")})
        else:
            print_result(f"PUT /feeds/{existing_feed_id}/subscription", response.status_code, success, data)
        
        return success
    except Exception as e:
        print_result(f"PUT /feeds/{existing_feed_id}/subscription", 0, False, {"error": str(e)})
        return False


async def test_unsubscribe_from_feed(client: httpx.AsyncClient, token: str) -> bool:
    """Test DELETE /feeds/{feed_id}/unsubscribe - Unsubscribe from a feed."""
    print_header("TEST 8: Unsubscribe from Feed")
    
    if not existing_feed_id:
        print("⚠️  Skipping: No feed ID available")
        return False
    
    try:
        response = await client.delete(
            f"{BASE_URL}/feeds/{existing_feed_id}/unsubscribe",
            headers={"Authorization": f"Bearer {token}"}
        )
        success = response.status_code == 200
        data = response.json() if success else {"error": response.text}
        
        print_result(f"DELETE /feeds/{existing_feed_id}/unsubscribe", response.status_code, success, data)
        
        return success
    except Exception as e:
        print_result(f"DELETE /feeds/{existing_feed_id}/unsubscribe", 0, False, {"error": str(e)})
        return False


async def test_create_feed_admin(client: httpx.AsyncClient, token: str) -> bool:
    """Test POST /feeds - Create new feed (Admin only)."""
    print_header("TEST 9: Create Feed (Admin)")
    
    try:
        new_feed = {
            "name": "Test Tech News",
            "url": "https://example.com/test-feed.xml",
            "source_name": "TestSource",
            "category": "technology",
            "is_active": True
        }
        
        response = await client.post(
            f"{BASE_URL}/feeds",
            headers={"Authorization": f"Bearer {token}"},
            json=new_feed
        )
        success = response.status_code in [200, 201]
        data = response.json() if success else {"error": response.text}
        
        if success:
            global test_feed_id
            test_feed_id = data.get("id")
            print_result("POST /feeds", response.status_code, success,
                        {"id": test_feed_id, "name": data.get("name")})
        else:
            print_result("POST /feeds", response.status_code, success, data)
        
        return success
    except Exception as e:
        print_result("POST /feeds", 0, False, {"error": str(e)})
        return False


async def test_update_feed_admin(client: httpx.AsyncClient, token: str) -> bool:
    """Test PUT /feeds/{feed_id} - Update feed (Admin only)."""
    print_header("TEST 10: Update Feed (Admin)")
    
    if not test_feed_id:
        print("⚠️  Skipping: No test feed created")
        return False
    
    try:
        update_data = {
            "name": "Updated Test Tech News",
            "is_active": False
        }
        
        response = await client.put(
            f"{BASE_URL}/feeds/{test_feed_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data
        )
        success = response.status_code == 200
        data = response.json() if success else {"error": response.text}
        
        if success:
            print_result(f"PUT /feeds/{test_feed_id}", response.status_code, success,
                        {"name": data.get("name"), "is_active": data.get("is_active")})
        else:
            print_result(f"PUT /feeds/{test_feed_id}", response.status_code, success, data)
        
        return success
    except Exception as e:
        print_result(f"PUT /feeds/{test_feed_id}", 0, False, {"error": str(e)})
        return False


async def test_delete_feed_admin(client: httpx.AsyncClient, token: str) -> bool:
    """Test DELETE /feeds/{feed_id} - Delete feed (Admin only)."""
    print_header("TEST 11: Delete Feed (Admin)")
    
    if not test_feed_id:
        print("⚠️  Skipping: No test feed to delete")
        return False
    
    try:
        response = await client.delete(
            f"{BASE_URL}/feeds/{test_feed_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        success = response.status_code == 200
        data = response.json() if success else {"error": response.text}
        
        print_result(f"DELETE /feeds/{test_feed_id}", response.status_code, success, data)
        
        return success
    except Exception as e:
        print_result(f"DELETE /feeds/{test_feed_id}", 0, False, {"error": str(e)})
        return False


async def main():
    """Run all RSS feed endpoint tests."""
    print("\n" + "🚀" * 40)
    print("  RSS FEED ENDPOINTS - COMPREHENSIVE TEST SUITE")
    print("🚀" * 40)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Setup: Register and login users
        print_header("SETUP: Authentication")
        
        await register_user(client, TEST_USER)
        global user_token
        user_token = await login_user(client, TEST_USER)
        
        if user_token:
            print("✅ User authenticated successfully")
        else:
            print("❌ Failed to authenticate user")
            return
        
        await register_user(client, TEST_ADMIN)
        global admin_token
        admin_token = await login_user(client, TEST_ADMIN)
        
        if admin_token:
            print("✅ Admin authenticated successfully")
        else:
            print("⚠️  Admin authentication failed - will skip admin tests")
        
        # Run all tests
        results = []
        
        # User tests (with user token)
        results.append(("List Feeds", await test_list_feeds(client, user_token)))
        results.append(("List Categories", await test_list_categories(client, user_token)))
        results.append(("Get Feed Detail", await test_get_feed_detail(client, user_token)))
        results.append(("Subscribe to Feed", await test_subscribe_to_feed(client, user_token)))
        results.append(("Get Subscriptions", await test_get_subscriptions(client, user_token)))
        results.append(("Get Subscribed IDs", await test_get_subscribed_feed_ids(client, user_token)))
        results.append(("Update Subscription", await test_update_subscription(client, user_token)))
        results.append(("Unsubscribe from Feed", await test_unsubscribe_from_feed(client, user_token)))
        
        # Admin tests (with admin token, if available)
        if admin_token:
            results.append(("Create Feed (Admin)", await test_create_feed_admin(client, admin_token)))
            results.append(("Update Feed (Admin)", await test_update_feed_admin(client, admin_token)))
            results.append(("Delete Feed (Admin)", await test_delete_feed_admin(client, admin_token)))
        
        # Summary
        print_header("TEST SUMMARY")
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        print(f"\n✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        
        if passed == total:
            print("\n🎉 All tests passed!")
        else:
            print("\n⚠️  Some tests failed. Check details above.")
            print("\nFailed tests:")
            for test_name, result in results:
                if not result:
                    print(f"  • {test_name}")


if __name__ == "__main__":
    asyncio.run(main())
