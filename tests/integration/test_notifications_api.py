"""
Integration tests for Notification API endpoints.
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
class TestNotificationPreferences:
    """Test notification preference endpoints."""
    
    async def test_get_default_preferences(
        self,
        client: AsyncClient,
        test_user: dict,
        auth_headers: dict
    ):
        """Test getting default notification preferences."""
        response = await client.get(
            "/api/v1/notifications/preferences",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check default values
        assert data["vote_notifications"] is True
        assert data["reply_notifications"] is True
        assert data["mention_notifications"] is True
        assert data["email_notifications"] is False
        assert data["user_id"] == test_user["user_id"]
    
    async def test_update_preferences(
        self,
        client: AsyncClient,
        test_user: dict,
        auth_headers: dict
    ):
        """Test updating notification preferences."""
        update_data = {
            "vote_notifications": False,
            "reply_notifications": True,
            "mention_notifications": False,
            "email_notifications": True
        }
        
        response = await client.put(
            "/api/v1/notifications/preferences",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check updated values
        assert data["vote_notifications"] is False
        assert data["reply_notifications"] is True
        assert data["mention_notifications"] is False
        assert data["email_notifications"] is True
    
    async def test_partial_update_preferences(
        self,
        client: AsyncClient,
        test_user: dict,
        auth_headers: dict
    ):
        """Test partial update of preferences."""
        # Only update one field
        update_data = {
            "vote_notifications": False
        }
        
        response = await client.put(
            "/api/v1/notifications/preferences",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that only vote_notifications changed
        assert data["vote_notifications"] is False
        assert data["reply_notifications"] is True  # Still default
        assert data["mention_notifications"] is True  # Still default
    
    async def test_preferences_unauthorized(
        self,
        client: AsyncClient
    ):
        """Test accessing preferences without authentication."""
        response = await client.get("/api/v1/notifications/preferences")
        assert response.status_code in [401, 403]


@pytest.mark.asyncio
class TestNotificationList:
    """Test notification listing endpoints."""
    
    async def test_get_empty_notifications(
        self,
        client: AsyncClient,
        test_user: dict,
        auth_headers: dict
    ):
        """Test getting notifications when none exist."""
        response = await client.get(
            "/api/v1/notifications/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 0
        assert data["unread_count"] == 0
        assert len(data["notifications"]) == 0
        assert data["page"] == 1
        assert data["page_size"] == 20
    
    async def test_get_unread_count(
        self,
        client: AsyncClient,
        test_user: dict,
        auth_headers: dict
    ):
        """Test getting unread notification count."""
        response = await client.get(
            "/api/v1/notifications/unread-count",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "unread_count" in data
        assert data["unread_count"] == 0
    
    async def test_get_notification_stats(
        self,
        client: AsyncClient,
        test_user: dict,
        auth_headers: dict
    ):
        """Test getting notification statistics."""
        response = await client.get(
            "/api/v1/notifications/stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_notifications" in data
        assert "unread_count" in data
        assert "vote_count" in data
        assert "reply_count" in data
        assert "mention_count" in data
        
        # All should be 0 initially
        assert data["total_notifications"] == 0
        assert data["unread_count"] == 0
    
    async def test_pagination_parameters(
        self,
        client: AsyncClient,
        test_user: dict,
        auth_headers: dict
    ):
        """Test pagination parameters."""
        response = await client.get(
            "/api/v1/notifications/?page=2&page_size=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 2
        assert data["page_size"] == 10
    
    async def test_invalid_pagination(
        self,
        client: AsyncClient,
        test_user: dict,
        auth_headers: dict
    ):
        """Test invalid pagination parameters."""
        # Page must be >= 1
        response = await client.get(
            "/api/v1/notifications/?page=0",
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Page size must be <= 100
        response = await client.get(
            "/api/v1/notifications/?page_size=101",
            headers=auth_headers
        )
        assert response.status_code == 422
    
    async def test_unauthorized_access(
        self,
        client: AsyncClient
    ):
        """Test accessing notifications without authentication."""
        response = await client.get("/api/v1/notifications/")
        assert response.status_code in [401, 403]


@pytest.mark.asyncio
class TestNotificationMarkRead:
    """Test marking notifications as read."""
    
    async def test_mark_all_read_empty(
        self,
        client: AsyncClient,
        test_user: dict,
        auth_headers: dict
    ):
        """Test marking all as read when no notifications exist."""
        response = await client.post(
            "/api/v1/notifications/mark-all-read",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["marked_count"] == 0
        assert "message" in data
    
    async def test_mark_specific_read_empty(
        self,
        client: AsyncClient,
        test_user: dict,
        auth_headers: dict
    ):
        """Test marking specific notifications as read when none exist."""
        notification_ids = [str(uuid4()), str(uuid4())]
        
        response = await client.post(
            "/api/v1/notifications/mark-read",
            json={"notification_ids": notification_ids},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["marked_count"] == 0
    
    async def test_mark_read_unauthorized(
        self,
        client: AsyncClient
    ):
        """Test marking notifications as read without authentication."""
        response = await client.post("/api/v1/notifications/mark-all-read")
        assert response.status_code in [401, 403]


@pytest.mark.asyncio
class TestNotificationDelete:
    """Test notification deletion."""
    
    async def test_delete_nonexistent_notification(
        self,
        client: AsyncClient,
        test_user: dict,
        auth_headers: dict
    ):
        """Test deleting a notification that doesn't exist."""
        fake_id = str(uuid4())
        
        response = await client.delete(
            f"/api/v1/notifications/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    async def test_get_nonexistent_notification(
        self,
        client: AsyncClient,
        test_user: dict,
        auth_headers: dict
    ):
        """Test getting a notification that doesn't exist."""
        fake_id = str(uuid4())
        
        response = await client.get(
            f"/api/v1/notifications/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    async def test_delete_unauthorized(
        self,
        client: AsyncClient
    ):
        """Test deleting notification without authentication."""
        fake_id = str(uuid4())
        response = await client.delete(f"/api/v1/notifications/{fake_id}")
        assert response.status_code in [401, 403]


@pytest.mark.asyncio
class TestNotificationFilters:
    """Test notification filtering."""
    
    async def test_filter_by_type(
        self,
        client: AsyncClient,
        test_user: dict,
        auth_headers: dict
    ):
        """Test filtering notifications by type."""
        response = await client.get(
            "/api/v1/notifications/?notification_type=vote",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
    
    async def test_filter_unread_only(
        self,
        client: AsyncClient,
        test_user: dict,
        auth_headers: dict
    ):
        """Test filtering to show only unread notifications."""
        response = await client.get(
            "/api/v1/notifications/?unread_only=true",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data


@pytest.mark.asyncio
class TestNotificationEndpoints:
    """Test all notification API endpoints comprehensively."""
    
    async def test_complete_workflow(
        self,
        client: AsyncClient,
        test_user: dict,
        auth_headers: dict
    ):
        """Test complete notification workflow."""
        # 1. Get preferences (should create defaults)
        prefs_response = await client.get(
            "/api/v1/notifications/preferences",
            headers=auth_headers
        )
        assert prefs_response.status_code == 200
        
        # 2. Get notifications (should be empty)
        notifs_response = await client.get(
            "/api/v1/notifications/",
            headers=auth_headers
        )
        assert notifs_response.status_code == 200
        assert notifs_response.json()["total"] == 0
        
        # 3. Get stats (should be zero)
        stats_response = await client.get(
            "/api/v1/notifications/stats",
            headers=auth_headers
        )
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["total_notifications"] == 0
        
        # 4. Update preferences
        update_response = await client.put(
            "/api/v1/notifications/preferences",
            json={"vote_notifications": False},
            headers=auth_headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["vote_notifications"] is False
        
        # 5. Mark all as read (should work even with no notifications)
        mark_response = await client.post(
            "/api/v1/notifications/mark-all-read",
            headers=auth_headers
        )
        assert mark_response.status_code == 200
    
    async def test_endpoints_require_authentication(
        self,
        client: AsyncClient
    ):
        """Test that all notification endpoints require authentication."""
        endpoints = [
            ("/api/v1/notifications/", "GET"),
            ("/api/v1/notifications/stats", "GET"),
            ("/api/v1/notifications/unread-count", "GET"),
            ("/api/v1/notifications/preferences", "GET"),
            ("/api/v1/notifications/preferences", "PUT"),
            ("/api/v1/notifications/mark-all-read", "POST"),
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = await client.get(endpoint)
            elif method == "PUT":
                response = await client.put(endpoint, json={})
            elif method == "POST":
                response = await client.post(endpoint)
            
            assert response.status_code in [401, 403], f"{method} {endpoint} should require auth"
