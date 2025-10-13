#!/usr/bin/env python3
"""
Manual API Testing Script for Comment Voting System (Phase 1)

This script tests all the comment voting endpoints to ensure they work correctly.
"""

import asyncio
import httpx
from uuid import uuid4

# Configuration
BASE_URL = "http://localhost:8081/api/v1"
TEST_EMAIL = f"test_voter_{uuid4().hex[:8]}@example.com"
TEST_USERNAME = f"voter_{uuid4().hex[:8]}"
TEST_PASSWORD = "TestPassword123!"

# Global variables to store test data
auth_token = None
user_id = None
article_id = None
comment_id = None
comment_id_2 = None


async def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


async def print_test(name: str, success: bool, details: str = ""):
    """Print test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {name}")
    if details:
        print(f"    {details}")


async def register_user(client: httpx.AsyncClient):
    """Register a new test user."""
    global auth_token, user_id
    
    await print_section("STEP 1: User Registration & Authentication")
    
    # Register
    response = await client.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": TEST_EMAIL,
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }
    )
    
    success = response.status_code == 201
    await print_test(
        "Register new user",
        success,
        f"Status: {response.status_code}"
    )
    
    if success:
        data = response.json()
        user_id = data.get("id")
        print(f"    User ID: {user_id}")
        
        # Now login to get token
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        
        if response.status_code == 200:
            token_data = response.json()
            auth_token = token_data.get("access_token")
            print(f"    Auth Token: {auth_token[:50] if auth_token else 'None'}...")
            await print_test(
                "Login and get token",
                True,
                f"Token received"
            )
        else:
            print(f"    ❌ Login failed: {response.status_code}")
            return False
    
    return success


async def create_test_article(client: httpx.AsyncClient):
    """Get or create a test article."""
    global article_id
    
    await print_section("STEP 2: Get Test Article")
    
    # Try to get existing articles
    response = await client.get(
        f"{BASE_URL}/articles?page=1&page_size=1"
    )
    
    if response.status_code == 200 and response.json().get("articles"):
        articles = response.json()["articles"]
        if articles:
            article_id = articles[0]["id"]
            success = True
            await print_test(
                "Get existing article for testing",
                success,
                f"Using existing article"
            )
            print(f"    Article ID: {article_id}")
            return success
    
    # If no articles exist, we'll need to create one manually via SQL
    # For now, let's fail gracefully
    print("    ⚠️  No articles found in database")
    print("    Please add at least one article to the database first")
    return False


async def create_test_comments(client: httpx.AsyncClient):
    """Create test comments."""
    global comment_id, comment_id_2
    
    await print_section("STEP 3: Create Test Comments")
    
    # Create first comment
    response = await client.post(
        f"{BASE_URL}/comments",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "article_id": article_id,
            "content": "This is a test comment for voting!"
        }
    )
    
    success = response.status_code == 201
    await print_test(
        "Create first comment",
        success,
        f"Status: {response.status_code}"
    )
    
    if success:
        comment_id = response.json()["id"]
        print(f"    Comment ID: {comment_id}")
    
    # Create second comment
    response = await client.post(
        f"{BASE_URL}/comments",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "article_id": article_id,
            "content": "Another test comment!"
        }
    )
    
    if response.status_code == 201:
        comment_id_2 = response.json()["id"]
        print(f"    Comment 2 ID: {comment_id_2}")
    
    return success


async def test_cast_upvote(client: httpx.AsyncClient):
    """Test casting an upvote."""
    await print_section("PHASE 1 TEST 1: Cast Upvote")
    
    response = await client.post(
        f"{BASE_URL}/comments/{comment_id}/vote?vote_type=upvote",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    success = response.status_code == 200
    await print_test(
        "Cast upvote on comment",
        success,
        f"Status: {response.status_code}, Response: {response.json() if success else response.text}"
    )
    
    if success:
        data = response.json()
        print(f"    Vote Value: {data.get('vote_value')}")
        print(f"    Message: {data.get('message')}")
    
    return success


async def test_cast_downvote(client: httpx.AsyncClient):
    """Test casting a downvote."""
    await print_section("PHASE 1 TEST 2: Cast Downvote")
    
    response = await client.post(
        f"{BASE_URL}/comments/{comment_id_2}/vote?vote_type=downvote",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    success = response.status_code == 200
    await print_test(
        "Cast downvote on comment",
        success,
        f"Status: {response.status_code}, Response: {response.json() if success else response.text}"
    )
    
    return success


async def test_toggle_vote(client: httpx.AsyncClient):
    """Test toggling a vote (same vote removes it)."""
    await print_section("PHASE 1 TEST 3: Toggle Vote (Same Vote Removes)")
    
    response = await client.post(
        f"{BASE_URL}/comments/{comment_id}/vote?vote_type=upvote",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # When toggling the same vote, it should be removed (voted=False)
    success = response.status_code == 200 and response.json().get("voted") == False
    await print_test(
        "Toggle upvote (should remove)",
        success,
        f"Status: {response.status_code}, Voted: {response.json().get('voted') if response.status_code == 200 else response.text}"
    )
    
    return success


async def test_change_vote(client: httpx.AsyncClient):
    """Test changing vote from one type to another."""
    await print_section("PHASE 1 TEST 4: Change Vote Type")
    
    # First cast an upvote
    await client.post(
        f"{BASE_URL}/comments/{comment_id}/vote?vote_type=upvote",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Then change to downvote
    response = await client.post(
        f"{BASE_URL}/comments/{comment_id}/vote?vote_type=downvote",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # When changing vote, it should still be voted=True but type changes
    success = response.status_code == 200 and response.json().get("voted") == True and response.json().get("vote_type") == "downvote"
    await print_test(
        "Change vote from upvote to downvote",
        success,
        f"Status: {response.status_code}, Voted: {response.json().get('voted')}, Type: {response.json().get('vote_type') if response.status_code == 200 else response.text}"
    )
    
    return success


async def test_remove_vote(client: httpx.AsyncClient):
    """Test removing a vote."""
    await print_section("PHASE 1 TEST 5: Remove Vote")
    
    response = await client.delete(
        f"{BASE_URL}/comments/{comment_id}/vote",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    success = response.status_code == 200
    await print_test(
        "Remove vote from comment",
        success,
        f"Status: {response.status_code}, Response: {response.json() if success else response.text}"
    )
    
    return success


async def test_get_user_vote(client: httpx.AsyncClient):
    """Test getting user's vote on a comment."""
    await print_section("PHASE 1 TEST 6: Get User Vote")
    
    # First cast a vote
    await client.post(
        f"{BASE_URL}/comments/{comment_id}/vote?vote_type=upvote",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Then get the vote
    response = await client.get(
        f"{BASE_URL}/comments/{comment_id}/vote",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    success = response.status_code == 200
    await print_test(
        "Get user's vote on comment",
        success,
        f"Status: {response.status_code}, Response: {response.json() if success else response.text}"
    )
    
    return success


async def test_get_vote_summary(client: httpx.AsyncClient):
    """Test getting vote summary for a comment."""
    await print_section("PHASE 1 TEST 7: Get Vote Summary")
    
    response = await client.get(
        f"{BASE_URL}/comments/{comment_id}/vote/summary"
    )
    
    success = response.status_code == 200
    await print_test(
        "Get vote summary for comment",
        success,
        f"Status: {response.status_code}, Response: {response.json() if success else response.text}"
    )
    
    if success:
        data = response.json()
        print(f"    Upvotes: {data.get('upvotes')}")
        print(f"    Downvotes: {data.get('downvotes')}")
        print(f"    Total: {data.get('total_votes')}")
        print(f"    Score: {data.get('vote_score')}")
    
    return success


async def test_unauthenticated_vote(client: httpx.AsyncClient):
    """Test that voting requires authentication."""
    await print_section("PHASE 1 TEST 8: Unauthenticated Vote (Should Fail)")
    
    response = await client.post(
        f"{BASE_URL}/comments/{comment_id}/vote?vote_type=upvote"
    )
    
    # FastAPI returns 403 Forbidden when authentication is required but not provided
    success = response.status_code == 403
    await print_test(
        "Voting without authentication should fail",
        success,
        f"Status: {response.status_code} (expected 403 Forbidden)"
    )
    
    return success


async def test_invalid_vote_type(client: httpx.AsyncClient):
    """Test that invalid vote types are rejected."""
    await print_section("PHASE 1 TEST 9: Invalid Vote Type (Should Fail)")
    
    response = await client.post(
        f"{BASE_URL}/comments/{comment_id}/vote?vote_type=invalid",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    success = response.status_code == 422
    await print_test(
        "Invalid vote type should be rejected",
        success,
        f"Status: {response.status_code} (expected 422)"
    )
    
    return success


async def test_nonexistent_comment(client: httpx.AsyncClient):
    """Test voting on a nonexistent comment."""
    await print_section("PHASE 1 TEST 10: Vote on Nonexistent Comment (Should Fail)")
    
    fake_comment_id = str(uuid4())
    response = await client.post(
        f"{BASE_URL}/comments/{fake_comment_id}/vote?vote_type=upvote",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    success = response.status_code == 404
    await print_test(
        "Voting on nonexistent comment should fail",
        success,
        f"Status: {response.status_code} (expected 404)"
    )
    
    return success


async def main():
    """Run all API tests."""
    print("\n" + "🚀" * 40)
    print("  COMMENT VOTING SYSTEM - PHASE 1 API TESTS")
    print("🚀" * 40)
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        # Setup phase
        if not await register_user(client):
            print("\n❌ Failed to register user. Aborting tests.")
            return
        
        if not await create_test_article(client):
            print("\n❌ Failed to create test article. Aborting tests.")
            return
        
        if not await create_test_comments(client):
            print("\n❌ Failed to create test comments. Aborting tests.")
            return
        
        # Core voting tests
        results = []
        results.append(await test_cast_upvote(client))
        results.append(await test_cast_downvote(client))
        results.append(await test_toggle_vote(client))
        results.append(await test_change_vote(client))
        results.append(await test_remove_vote(client))
        results.append(await test_get_user_vote(client))
        results.append(await test_get_vote_summary(client))
        results.append(await test_unauthenticated_vote(client))
        results.append(await test_invalid_vote_type(client))
        results.append(await test_nonexistent_comment(client))
        
        # Summary
        await print_section("TEST SUMMARY")
        passed = sum(results)
        total = len(results)
        percentage = (passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {total - passed} ❌")
        print(f"Success Rate: {percentage:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! The Comment Voting API is working correctly!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")


if __name__ == "__main__":
    asyncio.run(main())
