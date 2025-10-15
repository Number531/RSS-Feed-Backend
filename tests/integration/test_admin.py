"""
Integration tests for admin dashboard endpoints.

Tests Celery control, RSS source management, and system statistics.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.rss_source import RSSSource


@pytest.mark.integration
class TestAdminAuthentication:
    """Test admin authentication and authorization."""
    
    async def test_admin_endpoints_require_auth(
        self,
        client: AsyncClient
    ):
        """Admin endpoints should return 403 without authentication."""
        response = await client.get("/api/v1/admin/celery/status")
        assert response.status_code == 403  # FastAPI returns 403 for missing Bearer token
    
    async def test_admin_endpoints_require_superuser(
        self,
        client: AsyncClient,
        authenticated_user: tuple[User, str]
    ):
        """Admin endpoints should return 403 for non-superuser."""
        user, token = authenticated_user
        
        # Ensure user is NOT a superuser
        assert not user.is_superuser
        
        response = await client.get(
            "/api/v1/admin/celery/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403


@pytest.mark.integration
class TestCeleryStatus:
    """Test Celery status and monitoring endpoints."""
    
    async def test_get_celery_status(
        self,
        client: AsyncClient,
        admin_user: dict
    ):
        """Should return Celery status (may be unavailable if not running)."""
        token = admin_user["token"]
        
        response = await client.get(
            "/api/v1/admin/celery/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Response should contain status info
        assert "celery_available" in data
        assert isinstance(data["celery_available"], bool)
        
        # If Celery is available, check structure
        if data["celery_available"]:
            assert "active_workers" in data
            assert "worker_count" in data
    
    async def test_get_active_tasks(
        self,
        client: AsyncClient,
        admin_user: dict
    ):
        """Should return active Celery tasks."""
        token = admin_user["token"]
        
        response = await client.get(
            "/api/v1/admin/celery/active-tasks",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 500]  # 500 if Celery not running
        
        if response.status_code == 200:
            data = response.json()
            assert "active_tasks" in data
            assert "reserved_tasks" in data
            assert "total_active" in data
            assert "total_reserved" in data


@pytest.mark.integration
class TestCeleryControl:
    """Test Celery control endpoints (trigger tasks)."""
    
    @pytest.mark.skip(reason="Requires Celery running - manual test only")
    async def test_trigger_fetch_now(
        self,
        client: AsyncClient,
        admin_user: dict
    ):
        """Should trigger immediate RSS feed fetch."""
        token = admin_user["token"]
        
        response = await client.post(
            "/api/v1/admin/celery/fetch-now",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "dispatched"
        assert "task_id" in data
        assert "check_status_url" in data
    
    @pytest.mark.skip(reason="Requires Celery running - manual test only")
    async def test_trigger_single_feed_fetch(
        self,
        client: AsyncClient,
        admin_user: dict,
        sample_rss_source: RSSSource
    ):
        """Should trigger fetch for a single feed."""
        token = admin_user["token"]
        
        response = await client.post(
            f"/api/v1/admin/celery/fetch-feed/{sample_rss_source.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "dispatched"
        assert "task_id" in data
        assert data["feed_id"] == str(sample_rss_source.id)
    
    async def test_get_task_status_structure(
        self,
        client: AsyncClient,
        admin_user: dict
    ):
        """Should return task status structure (even for fake task ID)."""
        token = admin_user["token"]
        
        fake_task_id = "fake-task-id-12345"
        
        response = await client.get(
            f"/api/v1/admin/celery/task/{fake_task_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # May return 200 or 500 depending on Celery state
        if response.status_code == 200:
            data = response.json()
            assert "task_id" in data
            assert "status" in data


@pytest.mark.integration  
class TestRSSSourceManagement:
    """Test RSS source CRUD operations via admin API."""
    
    async def test_create_rss_source(
        self,
        client: AsyncClient,
        admin_user: dict
    ):
        """Admin can create new RSS source."""
        token = admin_user["token"]
        
        source_data = {
            "name": "Test RSS Feed",
            "url": "https://example.com/feed.xml",
            "source_name": "Test Feed",
            "category": "technology",
            "is_active": True
        }
        
        response = await client.post(
            "/api/v1/admin/feeds",
            headers={"Authorization": f"Bearer {token}"},
            json=source_data
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == source_data["name"]
        assert data["url"] == source_data["url"]
        assert data["category"] == source_data["category"]
        assert "id" in data
    
    async def test_update_rss_source(
        self,
        client: AsyncClient,
        admin_user: dict,
        sample_rss_source: RSSSource
    ):
        """Admin can update existing RSS source."""
        token = admin_user["token"]
        
        update_data = {
            "name": "Updated Feed Name",
            "is_active": False
        }
        
        response = await client.put(
            f"/api/v1/admin/feeds/{sample_rss_source.id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == update_data["name"]
        assert data["is_active"] == update_data["is_active"]
    
    async def test_update_nonexistent_source(
        self,
        client: AsyncClient,
        admin_user: dict
    ):
        """Should return 404 for nonexistent source."""
        token = admin_user["token"]
        
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = await client.put(
            f"/api/v1/admin/feeds/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "test"}
        )
        
        assert response.status_code == 404
    
    async def test_delete_rss_source(
        self,
        client: AsyncClient,
        admin_user: dict,
        test_db: AsyncSession
    ):
        """Admin can delete (soft delete) RSS source."""
        token = admin_user["token"]
        
        # Create a source to delete
        source = RSSSource(
            name="To Delete",
            url="https://example.com/delete.xml",
            source_name="Delete Me",
            category="technology",
            is_active=True
        )
        test_db.add(source)
        await test_db.commit()
        await test_db.refresh(source)
        
        response = await client.delete(
            f"/api/v1/admin/feeds/{source.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 204
    
    async def test_delete_nonexistent_source(
        self,
        client: AsyncClient,
        admin_user: dict
    ):
        """Should return 404 when deleting nonexistent source."""
        token = admin_user["token"]
        
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = await client.delete(
            f"/api/v1/admin/feeds/{fake_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404


@pytest.mark.integration
class TestFeedHealth:
    """Test feed health monitoring endpoint."""
    
    async def test_get_feeds_health(
        self,
        client: AsyncClient,
        admin_user: dict,
        sample_rss_sources: list[RSSSource]
    ):
        """Should return health status of all feeds."""
        token = admin_user["token"]
        
        response = await client.get(
            "/api/v1/admin/feeds/health",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "total_sources" in data
        assert "healthy" in data
        assert "unhealthy" in data
        assert "inactive" in data
        assert "health_rate" in data
        assert "unhealthy_feeds" in data
        
        # Verify counts
        assert isinstance(data["total_sources"], int)
        assert isinstance(data["healthy"], int)
        assert isinstance(data["unhealthy"], int)
        assert isinstance(data["health_rate"], float)
        assert isinstance(data["unhealthy_feeds"], list)
        
        # Health rate should be between 0 and 1
        assert 0 <= data["health_rate"] <= 1


@pytest.mark.integration
class TestSystemStats:
    """Test system statistics endpoint."""
    
    async def test_get_system_overview(
        self,
        client: AsyncClient,
        admin_user: dict,
        sample_rss_sources: list[RSSSource]
    ):
        """Should return system statistics."""
        token = admin_user["token"]
        
        response = await client.get(
            "/api/v1/admin/stats/overview",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "users" in data
        assert "articles" in data
        assert "rss_sources" in data
        
        assert "total" in data["users"]
        assert "total" in data["articles"]
        assert "total" in data["rss_sources"]
        assert "active" in data["rss_sources"]
        assert "inactive" in data["rss_sources"]
        
        # Verify counts are non-negative
        assert data["users"]["total"] >= 0
        assert data["articles"]["total"] >= 0
        assert data["rss_sources"]["total"] >= 0
        assert data["rss_sources"]["active"] >= 0
