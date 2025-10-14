"""
Integration tests for RSS Feed Management endpoints.

Tests all 11 RSS feed management endpoints:
- Feed CRUD operations (admin)
- User subscriptions
- Feed listing and filtering
- Category statistics
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.rss_source import RSSSource
from app.models.user import User


@pytest.mark.integration
class TestRSSFeedEndpoints:
    """Test RSS feed management endpoints."""
    
    @pytest.fixture
    async def sample_feed(self, db: AsyncSession) -> RSSSource:
        """Create a sample RSS feed for testing."""
        feed = RSSSource(
            name="Test Tech News",
            url="https://example.com/rss/tech",
            source_name="Example News",
            category="technology",
            is_active=True
        )
        db.add(feed)
        await db.commit()
        await db.refresh(feed)
        return feed
    
    @pytest.fixture
    async def admin_headers(self, admin_token: str) -> dict:
        """Get headers with admin token."""
        return {"Authorization": f"Bearer {admin_token}"}
    
    @pytest.fixture
    async def user_headers(self, auth_token: str) -> dict:
        """Get headers with regular user token."""
        return {"Authorization": f"Bearer {auth_token}"}
    
    # Feed Listing Tests
    
    async def test_list_feeds_success(
        self,
        client: AsyncClient,
        sample_feed: RSSSource,
        user_headers: dict
    ):
        """Test listing RSS feeds with pagination."""
        response = await client.get(
            "/api/v1/feeds?page=1&page_size=10",
            headers=user_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "sources" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert len(data["sources"]) > 0
    
    async def test_list_feeds_with_category_filter(
        self,
        client: AsyncClient,
        sample_feed: RSSSource,
        user_headers: dict
    ):
        """Test filtering feeds by category."""
        response = await client.get(
            "/api/v1/feeds?category=technology",
            headers=user_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(feed["category"] == "technology" for feed in data["sources"])
    
    async def test_list_feeds_with_active_filter(
        self,
        client: AsyncClient,
        sample_feed: RSSSource,
        user_headers: dict
    ):
        """Test filtering feeds by active status."""
        response = await client.get(
            "/api/v1/feeds?is_active=true",
            headers=user_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(feed["is_active"] for feed in data["sources"])
    
    async def test_list_feeds_unauthorized(self, client: AsyncClient):
        """Test listing feeds without authentication fails."""
        response = await client.get("/api/v1/feeds")
        assert response.status_code == 403
    
    # Feed Details Tests
    
    async def test_get_feed_by_id_success(
        self,
        client: AsyncClient,
        sample_feed: RSSSource,
        user_headers: dict
    ):
        """Test getting feed details by ID."""
        response = await client.get(
            f"/api/v1/feeds/{sample_feed.id}",
            headers=user_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_feed.id)
        assert data["name"] == sample_feed.name
        assert data["url"] == sample_feed.url
        assert "success_rate" in data
        assert "is_healthy" in data
    
    async def test_get_feed_by_id_not_found(
        self,
        client: AsyncClient,
        user_headers: dict
    ):
        """Test getting non-existent feed returns 404."""
        fake_id = uuid4()
        response = await client.get(
            f"/api/v1/feeds/{fake_id}",
            headers=user_headers
        )
        
        assert response.status_code == 404
        response_data = response.json()
        error_message = response_data.get("detail", response_data.get("message", ""))
        assert "not found" in error_message.lower()
    
    # Category Tests
    
    async def test_get_categories_success(
        self,
        client: AsyncClient,
        sample_feed: RSSSource,
        user_headers: dict
    ):
        """Test getting feed categories with statistics."""
        response = await client.get(
            "/api/v1/feeds/categories",
            headers=user_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "category" in data[0]
            assert "count" in data[0]
            assert "active_count" in data[0]
    
    # Admin CRUD Tests
    
    async def test_create_feed_success(
        self,
        client: AsyncClient,
        admin_headers: dict
    ):
        """Test creating a new RSS feed (admin only)."""
        feed_data = {
            "name": "New Tech Feed",
            "url": "https://newtechfeed.com/rss",
            "source_name": "NewTech",
            "category": "technology",
            "is_active": True
        }
        
        response = await client.post(
            "/api/v1/feeds",
            json=feed_data,
            headers=admin_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == feed_data["name"]
        assert data["url"] == feed_data["url"]
        assert "id" in data
    
    async def test_create_feed_duplicate_url(
        self,
        client: AsyncClient,
        sample_feed: RSSSource,
        admin_headers: dict
    ):
        """Test creating feed with duplicate URL fails."""
        feed_data = {
            "name": "Duplicate Feed",
            "url": sample_feed.url,
            "source_name": "Duplicate",
            "category": "general",
            "is_active": True
        }
        
        response = await client.post(
            "/api/v1/feeds",
            json=feed_data,
            headers=admin_headers
        )
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()
    
    async def test_create_feed_forbidden_for_regular_user(
        self,
        client: AsyncClient,
        user_headers: dict
    ):
        """Test regular user cannot create feeds."""
        feed_data = {
            "name": "Unauthorized Feed",
            "url": "https://unauthorized.com/rss",
            "source_name": "Unauthorized",
            "category": "general",
            "is_active": True
        }
        
        response = await client.post(
            "/api/v1/feeds",
            json=feed_data,
            headers=user_headers
        )
        
        assert response.status_code == 403
    
    async def test_update_feed_success(
        self,
        client: AsyncClient,
        sample_feed: RSSSource,
        admin_headers: dict
    ):
        """Test updating an RSS feed (admin only)."""
        update_data = {
            "name": "Updated Feed Name",
            "is_active": False
        }
        
        response = await client.put(
            f"/api/v1/feeds/{sample_feed.id}",
            json=update_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["is_active"] == update_data["is_active"]
    
    async def test_update_feed_not_found(
        self,
        client: AsyncClient,
        admin_headers: dict
    ):
        """Test updating non-existent feed returns 404."""
        fake_id = uuid4()
        update_data = {"name": "Updated Name"}
        
        response = await client.put(
            f"/api/v1/feeds/{fake_id}",
            json=update_data,
            headers=admin_headers
        )
        
        assert response.status_code == 404
    
    async def test_update_feed_forbidden_for_regular_user(
        self,
        client: AsyncClient,
        sample_feed: RSSSource,
        user_headers: dict
    ):
        """Test regular user cannot update feeds."""
        update_data = {"name": "Unauthorized Update"}
        
        response = await client.put(
            f"/api/v1/feeds/{sample_feed.id}",
            json=update_data,
            headers=user_headers
        )
        
        assert response.status_code == 403
    
    async def test_delete_feed_success(
        self,
        client: AsyncClient,
        admin_headers: dict,
        db: AsyncSession
    ):
        """Test deleting an RSS feed (admin only)."""
        # Create a feed to delete
        feed = RSSSource(
            name="Feed to Delete",
            url="https://todelete.com/rss",
            source_name="ToDelete",
            category="general",
            is_active=True
        )
        db.add(feed)
        await db.commit()
        await db.refresh(feed)
        
        response = await client.delete(
            f"/api/v1/feeds/{feed.id}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"].lower()
    
    async def test_delete_feed_forbidden_for_regular_user(
        self,
        client: AsyncClient,
        sample_feed: RSSSource,
        user_headers: dict
    ):
        """Test regular user cannot delete feeds."""
        response = await client.delete(
            f"/api/v1/feeds/{sample_feed.id}",
            headers=user_headers
        )
        
        assert response.status_code == 403


@pytest.mark.integration
class TestSubscriptionEndpoints:
    """Test user subscription endpoints."""
    
    @pytest.fixture
    async def sample_feed(self, db: AsyncSession) -> RSSSource:
        """Create a sample RSS feed for testing."""
        feed = RSSSource(
            name="Subscription Test Feed",
            url="https://subtest.com/rss",
            source_name="SubTest",
            category="technology",
            is_active=True
        )
        db.add(feed)
        await db.commit()
        await db.refresh(feed)
        return feed
    
    @pytest.fixture
    async def user_headers(self, auth_token: str) -> dict:
        """Get headers with user token."""
        return {"Authorization": f"Bearer {auth_token}"}
    
    # Subscription Tests
    
    async def test_subscribe_to_feed_success(
        self,
        client: AsyncClient,
        sample_feed: RSSSource,
        user_headers: dict
    ):
        """Test subscribing to a feed."""
        subscription_data = {
            "notifications_enabled": True
        }
        
        response = await client.post(
            f"/api/v1/feeds/{sample_feed.id}/subscribe",
            json=subscription_data,
            headers=user_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["feed_id"] == str(sample_feed.id)
        assert data["is_active"] is True
        assert data["notifications_enabled"] is True
        assert "feed" in data
    
    async def test_subscribe_to_nonexistent_feed(
        self,
        client: AsyncClient,
        user_headers: dict
    ):
        """Test subscribing to non-existent feed fails."""
        fake_id = uuid4()
        
        response = await client.post(
            f"/api/v1/feeds/{fake_id}/subscribe",
            json={"notifications_enabled": True},
            headers=user_headers
        )
        
        assert response.status_code == 404
    
    async def test_subscribe_twice_returns_conflict(
        self,
        client: AsyncClient,
        sample_feed: RSSSource,
        user_headers: dict
    ):
        """Test subscribing twice to same feed returns 409."""
        # First subscription
        await client.post(
            f"/api/v1/feeds/{sample_feed.id}/subscribe",
            json={"notifications_enabled": True},
            headers=user_headers
        )
        
        # Second subscription attempt
        response = await client.post(
            f"/api/v1/feeds/{sample_feed.id}/subscribe",
            json={"notifications_enabled": True},
            headers=user_headers
        )
        
        assert response.status_code == 409
        assert "already subscribed" in response.json()["detail"].lower()
    
    async def test_get_my_subscriptions_success(
        self,
        client: AsyncClient,
        sample_feed: RSSSource,
        user_headers: dict
    ):
        """Test getting user's subscriptions."""
        # Subscribe first
        await client.post(
            f"/api/v1/feeds/{sample_feed.id}/subscribe",
            json={"notifications_enabled": True},
            headers=user_headers
        )
        
        # Get subscriptions
        response = await client.get(
            "/api/v1/feeds/subscriptions",
            headers=user_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "subscriptions" in data
        assert "total" in data
        assert len(data["subscriptions"]) > 0
        assert data["subscriptions"][0]["feed_id"] == str(sample_feed.id)
    
    async def test_get_subscriptions_with_pagination(
        self,
        client: AsyncClient,
        user_headers: dict
    ):
        """Test subscription pagination."""
        response = await client.get(
            "/api/v1/feeds/subscriptions?page=1&page_size=5",
            headers=user_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
    
    async def test_unsubscribe_from_feed_success(
        self,
        client: AsyncClient,
        sample_feed: RSSSource,
        user_headers: dict
    ):
        """Test unsubscribing from a feed."""
        # Subscribe first
        await client.post(
            f"/api/v1/feeds/{sample_feed.id}/subscribe",
            json={"notifications_enabled": True},
            headers=user_headers
        )
        
        # Unsubscribe
        response = await client.delete(
            f"/api/v1/feeds/{sample_feed.id}/unsubscribe",
            headers=user_headers
        )
        
        assert response.status_code == 200
        assert "unsubscribed" in response.json()["message"].lower()
    
    async def test_unsubscribe_from_not_subscribed_feed(
        self,
        client: AsyncClient,
        sample_feed: RSSSource,
        user_headers: dict
    ):
        """Test unsubscribing from feed not subscribed to fails."""
        response = await client.delete(
            f"/api/v1/feeds/{sample_feed.id}/unsubscribe",
            headers=user_headers
        )
        
        assert response.status_code == 404
        # Note: Custom 404 handler in main.py intercepts the HTTPException,
        # so we just verify we got a 404 (which is correct behavior)
    
    async def test_update_subscription_preferences_success(
        self,
        client: AsyncClient,
        sample_feed: RSSSource,
        user_headers: dict
    ):
        """Test updating subscription preferences."""
        # Subscribe first
        await client.post(
            f"/api/v1/feeds/{sample_feed.id}/subscribe",
            json={"notifications_enabled": True},
            headers=user_headers
        )
        
        # Update preferences
        update_data = {
            "notifications_enabled": False
        }
        
        response = await client.put(
            f"/api/v1/feeds/{sample_feed.id}/subscription",
            json=update_data,
            headers=user_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["notifications_enabled"] is False
    
    async def test_get_subscribed_feed_ids_success(
        self,
        client: AsyncClient,
        sample_feed: RSSSource,
        user_headers: dict
    ):
        """Test getting list of subscribed feed IDs."""
        # Subscribe first
        await client.post(
            f"/api/v1/feeds/{sample_feed.id}/subscribe",
            json={"notifications_enabled": True},
            headers=user_headers
        )
        
        # Get subscribed IDs
        response = await client.get(
            "/api/v1/feeds/subscribed",
            headers=user_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert str(sample_feed.id) in data
    
    async def test_subscription_unauthorized(
        self,
        client: AsyncClient,
        sample_feed: RSSSource
    ):
        """Test subscription operations require authentication."""
        # Try to subscribe without auth
        response = await client.post(
            f"/api/v1/feeds/{sample_feed.id}/subscribe",
            json={"notifications_enabled": True}
        )
        assert response.status_code == 403
        
        # Try to get subscriptions without auth
        response = await client.get("/api/v1/feeds/subscriptions")
        assert response.status_code == 403
