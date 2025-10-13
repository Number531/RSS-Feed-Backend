"""
Integration tests for Phase 3.5 notification system integrations.

Tests:
- User registration creates default preferences
- Comment votes trigger notifications
- Comment replies trigger notifications
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
class TestUserRegistrationIntegration:
    """Test that user registration creates default notification preferences."""
    
    async def test_registration_creates_preferences(
        self,
        client: AsyncClient,
        db_session
    ):
        """Test that registering a new user creates default notification preferences."""
        from app.models.notification import UserNotificationPreference
        from app.models.user import User
        from sqlalchemy import select
        
        # Register a new user
        user_data = {
            "username": f"test_{uuid4().hex[:8]}",
            "email": f"test_{uuid4().hex[:8]}@example.com",
            "password": "TestPassword123!"
        }
        
        register_response = await client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        # Get the created user from DB
        result = await db_session.execute(
            select(User).where(User.email == user_data["email"])
        )
        user = result.scalar_one()
        
        # Check that preferences were created
        result = await db_session.execute(
            select(UserNotificationPreference).where(
                UserNotificationPreference.user_id == user.id
            )
        )
        preferences = result.scalar_one_or_none()
        
        assert preferences is not None, "Preferences should be created"
        assert preferences.vote_notifications is True
        assert preferences.reply_notifications is True
        assert preferences.mention_notifications is True
        assert preferences.email_notifications is False
        
        print("✅ User registration creates default preferences")
    
    async def test_multiple_registrations(
        self,
        client: AsyncClient,
        db_session
    ):
        """Test that multiple user registrations each get their own preferences."""
        from app.models.notification import UserNotificationPreference
        from app.models.user import User
        from sqlalchemy import select
        
        users = []
        
        # Register 3 users
        for i in range(3):
            user_data = {
                "username": f"test_{uuid4().hex[:8]}",
                "email": f"test_{uuid4().hex[:8]}@example.com",
                "password": "TestPassword123!"
            }
            
            register_response = await client.post("/api/v1/auth/register", json=user_data)
            assert register_response.status_code == 201
            
            # Get user from DB
            result = await db_session.execute(
                select(User).where(User.email == user_data["email"])
            )
            user = result.scalar_one()
            users.append(user)
        
        # Verify each user has their own preferences
        for user in users:
            result = await db_session.execute(
                select(UserNotificationPreference).where(
                    UserNotificationPreference.user_id == user.id
                )
            )
            preferences = result.scalar_one_or_none()
            
            assert preferences is not None
            assert preferences.vote_notifications is True
        
        print("✅ Multiple users each get their own preferences")


@pytest.mark.asyncio
class TestVoteNotificationIntegration:
    """Test that voting on comments triggers notifications."""
    
    async def test_comment_upvote_creates_notification(
        self,
        client: AsyncClient,
        test_user: dict,
        test_user_2: dict,
        auth_headers: dict,
        auth_headers_2: dict,
        test_article: dict
    ):
        """Test that upvoting a comment creates a notification for the comment author."""
        # User 1 creates a comment
        comment_data = {
            "article_id": test_article["id"],
            "content": "This is a test comment for voting"
        }
        
        comment_response = await client.post(
            "/api/v1/comments/",
            json=comment_data,
            headers=auth_headers
        )
        assert comment_response.status_code == 201
        comment = comment_response.json()
        comment_id = comment["id"]
        
        # Check User 1 has no notifications initially
        notifs_before = await client.get("/api/v1/notifications/", headers=auth_headers)
        initial_count = notifs_before.json()["total"]
        
        # User 2 upvotes the comment
        vote_response = await client.post(
            f"/api/v1/comments/{comment_id}/vote?vote_type=upvote",
            headers=auth_headers_2
        )
        assert vote_response.status_code in [200, 201]
        
        # Wait a moment for async notification creation
        import asyncio
        await asyncio.sleep(0.5)
        
        # Check that User 1 received a notification
        notifs_after = await client.get("/api/v1/notifications/", headers=auth_headers)
        assert notifs_after.status_code == 200
        
        notifs = notifs_after.json()
        assert notifs["total"] == initial_count + 1
        
        # Verify the notification is a vote notification
        latest_notif = notifs["notifications"][0]
        assert latest_notif["type"] == "vote"
        assert "upvote" in latest_notif["message"].lower()
        assert latest_notif["related_entity_type"] == "comment"
        assert latest_notif["related_entity_id"] == comment_id
        assert latest_notif["is_read"] is False
        
        print("✅ Comment upvote creates notification")
    
    async def test_own_vote_no_notification(
        self,
        client: AsyncClient,
        test_user: dict,
        auth_headers: dict,
        test_article: dict
    ):
        """Test that upvoting your own comment does not create a notification."""
        # User creates a comment
        comment_data = {
            "article_id": test_article["id"],
            "content": "Test comment for self-voting"
        }
        
        comment_response = await client.post(
            "/api/v1/comments/",
            json=comment_data,
            headers=auth_headers
        )
        assert comment_response.status_code == 201
        comment = comment_response.json()
        
        initial_notifs = await client.get("/api/v1/notifications/", headers=auth_headers)
        initial_count = initial_notifs.json()["total"]
        
        # User upvotes their own comment
        await client.post(
            f"/api/v1/comments/{comment['id']}/vote?vote_type=upvote",
            headers=auth_headers
        )
        
        # Wait a moment
        import asyncio
        await asyncio.sleep(0.5)
        
        # Verify no new notification
        after_notifs = await client.get("/api/v1/notifications/", headers=auth_headers)
        assert after_notifs.json()["total"] == initial_count
        
        print("✅ Self-vote does not create notification")
    
    async def test_downvote_no_notification(
        self,
        client: AsyncClient,
        test_user: dict,
        test_user_2: dict,
        auth_headers: dict,
        auth_headers_2: dict,
        test_article: dict
    ):
        """Test that downvoting a comment does not create a notification."""
        # User 1 creates a comment
        comment_data = {
            "article_id": test_article["id"],
            "content": "Test comment for downvoting"
        }
        
        comment_response = await client.post(
            "/api/v1/comments/",
            json=comment_data,
            headers=auth_headers
        )
        comment = comment_response.json()
        
        initial_notifs = await client.get("/api/v1/notifications/", headers=auth_headers)
        initial_count = initial_notifs.json()["total"]
        
        # User 2 downvotes the comment
        await client.post(
            f"/api/v1/comments/{comment['id']}/vote?vote_type=downvote",
            headers=auth_headers_2
        )
        
        # Wait a moment
        import asyncio
        await asyncio.sleep(0.5)
        
        # Verify no new notification (only upvotes trigger notifications)
        after_notifs = await client.get("/api/v1/notifications/", headers=auth_headers)
        assert after_notifs.json()["total"] == initial_count
        
        print("✅ Downvote does not create notification")


@pytest.mark.asyncio
class TestReplyNotificationIntegration:
    """Test that replying to comments triggers notifications."""
    
    async def test_comment_reply_creates_notification(
        self,
        client: AsyncClient,
        test_user: dict,
        test_user_2: dict,
        auth_headers: dict,
        auth_headers_2: dict,
        test_article: dict
    ):
        """Test that replying to a comment creates a notification for the original author."""
        # User 1 creates a parent comment
        parent_comment_data = {
            "article_id": test_article["id"],
            "content": "This is the parent comment"
        }
        
        parent_response = await client.post(
            "/api/v1/comments/",
            json=parent_comment_data,
            headers=auth_headers
        )
        assert parent_response.status_code == 201
        parent_comment = parent_response.json()
        
        initial_notifs = await client.get("/api/v1/notifications/", headers=auth_headers)
        initial_count = initial_notifs.json()["total"]
        
        # User 2 replies to the comment
        reply_data = {
            "article_id": test_article["id"],
            "content": "This is a reply",
            "parent_comment_id": parent_comment["id"]
        }
        
        reply_response = await client.post(
            "/api/v1/comments/",
            json=reply_data,
            headers=auth_headers_2
        )
        assert reply_response.status_code == 201
        
        # Wait for async notification
        import asyncio
        await asyncio.sleep(0.5)
        
        # Check that User 1 received a reply notification
        notifs_after = await client.get("/api/v1/notifications/", headers=auth_headers)
        assert notifs_after.status_code == 200
        
        notifs = notifs_after.json()
        assert notifs["total"] == initial_count + 1
        
        # Verify the notification
        latest_notif = notifs["notifications"][0]
        assert latest_notif["type"] == "reply"
        assert "replied" in latest_notif["message"].lower()
        assert latest_notif["related_entity_type"] == "comment"
        assert latest_notif["is_read"] is False
        
        print("✅ Comment reply creates notification")
    
    async def test_self_reply_no_notification(
        self,
        client: AsyncClient,
        test_user: dict,
        auth_headers: dict,
        test_article: dict
    ):
        """Test that replying to your own comment does not create a notification."""
        # User creates a parent comment
        parent_comment_data = {
            "article_id": test_article["id"],
            "content": "Parent comment"
        }
        
        parent_response = await client.post(
            "/api/v1/comments/",
            json=parent_comment_data,
            headers=auth_headers
        )
        parent_comment = parent_response.json()
        
        initial_notifs = await client.get("/api/v1/notifications/", headers=auth_headers)
        initial_count = initial_notifs.json()["total"]
        
        # User replies to their own comment
        reply_data = {
            "article_id": test_article["id"],
            "content": "Self reply",
            "parent_comment_id": parent_comment["id"]
        }
        
        await client.post("/api/v1/comments/", json=reply_data, headers=auth_headers)
        
        # Wait
        import asyncio
        await asyncio.sleep(0.5)
        
        # Verify no new notification
        after_notifs = await client.get("/api/v1/notifications/", headers=auth_headers)
        assert after_notifs.json()["total"] == initial_count
        
        print("✅ Self-reply does not create notification")
    
    async def test_multiple_replies_create_multiple_notifications(
        self,
        client: AsyncClient,
        test_user: dict,
        test_user_2: dict,
        auth_headers: dict,
        auth_headers_2: dict,
        test_article: dict
    ):
        """Test that multiple replies create multiple notifications."""
        # User 1 creates a parent comment
        parent_comment_data = {
            "article_id": test_article["id"],
            "content": "Parent for multiple replies"
        }
        
        parent_response = await client.post(
            "/api/v1/comments/",
            json=parent_comment_data,
            headers=auth_headers
        )
        parent_comment = parent_response.json()
        
        initial_notifs = await client.get("/api/v1/notifications/", headers=auth_headers)
        initial_count = initial_notifs.json()["total"]
        
        # User 2 creates 3 replies
        for i in range(3):
            reply_data = {
                "article_id": test_article["id"],
                "content": f"Reply number {i+1}",
                "parent_comment_id": parent_comment["id"]
            }
            
            reply_response = await client.post(
                "/api/v1/comments/",
                json=reply_data,
                headers=auth_headers_2
            )
            assert reply_response.status_code == 201
        
        # Wait for all notifications
        import asyncio
        await asyncio.sleep(1.0)
        
        # User 1 should have 3 new reply notifications
        notifs_after = await client.get("/api/v1/notifications/", headers=auth_headers)
        notifs = notifs_after.json()
        assert notifs["total"] == initial_count + 3
        
        # Verify all are reply notifications
        reply_notifs = [n for n in notifs["notifications"] if n["type"] == "reply"]
        assert len(reply_notifs) == 3
        
        print("✅ Multiple replies create multiple notifications")


@pytest.mark.asyncio
class TestNotificationPreferences:
    """Test that notification preferences are respected."""
    
    async def test_disabled_vote_notifications(
        self,
        client: AsyncClient,
        test_user: dict,
        test_user_2: dict,
        auth_headers: dict,
        auth_headers_2: dict,
        test_article: dict
    ):
        """Test that disabling vote notifications prevents vote notifications."""
        # User 1 disables vote notifications
        update_response = await client.put(
            "/api/v1/notifications/preferences",
            json={"vote_notifications": False},
            headers=auth_headers
        )
        assert update_response.status_code == 200
        
        # User 1 creates a comment
        comment_data = {
            "article_id": test_article["id"],
            "content": "Comment with disabled notifications"
        }
        
        comment_response = await client.post(
            "/api/v1/comments/",
            json=comment_data,
            headers=auth_headers
        )
        comment = comment_response.json()
        
        initial_notifs = await client.get("/api/v1/notifications/", headers=auth_headers)
        initial_count = initial_notifs.json()["total"]
        
        # User 2 upvotes
        vote_data = {"comment_id": comment["id"], "vote_value": 1}
        await client.post("/api/v1/comments/vote", json=vote_data, headers=auth_headers_2)
        
        # Wait
        import asyncio
        await asyncio.sleep(0.5)
        
        # User 1 should NOT receive notification
        after_notifs = await client.get("/api/v1/notifications/", headers=auth_headers)
        assert after_notifs.json()["total"] == initial_count
        
        print("✅ Disabled vote notifications are respected")
    
    async def test_disabled_reply_notifications(
        self,
        client: AsyncClient,
        test_user: dict,
        test_user_2: dict,
        auth_headers: dict,
        auth_headers_2: dict,
        test_article: dict
    ):
        """Test that disabling reply notifications prevents reply notifications."""
        # User 1 disables reply notifications
        update_response = await client.put(
            "/api/v1/notifications/preferences",
            json={"reply_notifications": False},
            headers=auth_headers
        )
        assert update_response.status_code == 200
        
        # User 1 creates a comment
        comment_data = {
            "article_id": test_article["id"],
            "content": "Comment with disabled reply notifications"
        }
        
        comment_response = await client.post(
            "/api/v1/comments/",
            json=comment_data,
            headers=auth_headers
        )
        comment = comment_response.json()
        
        initial_notifs = await client.get("/api/v1/notifications/", headers=auth_headers)
        initial_count = initial_notifs.json()["total"]
        
        # User 2 replies
        reply_data = {
            "article_id": test_article["id"],
            "content": "Reply that should be ignored",
            "parent_comment_id": comment["id"]
        }
        await client.post("/api/v1/comments/", json=reply_data, headers=auth_headers_2)
        
        # Wait
        import asyncio
        await asyncio.sleep(0.5)
        
        # User 1 should NOT receive notification
        after_notifs = await client.get("/api/v1/notifications/", headers=auth_headers)
        assert after_notifs.json()["total"] == initial_count
        
        print("✅ Disabled reply notifications are respected")
