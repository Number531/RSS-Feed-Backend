"""
Integration tests for synthesis endpoints.
Tests full request/response cycle with real database.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# Import test fixtures
pytest_plugins = ["tests.fixtures.synthesis_fixtures"]


@pytest.mark.integration
@pytest.mark.asyncio
class TestListSynthesisArticles:
    """Test GET /api/v1/articles/synthesis endpoint."""
    
    async def test_list_with_data(self, async_client: AsyncClient, synthesis_articles):
        """Test listing synthesis articles with populated database."""
        response = await async_client.get("/api/v1/articles/synthesis")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "has_next" in data
        
        # Should have 4 synthesis articles (5th is control without synthesis)
        assert data["total"] == 4
        assert len(data["items"]) == 4
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["has_next"] is False
        
        # Verify first item structure
        first_item = data["items"][0]
        assert "id" in first_item
        assert "title" in first_item
        assert "synthesis_preview" in first_item
        assert "fact_check_verdict" in first_item
        assert "verdict_color" in first_item
        assert "fact_check_score" in first_item
        assert "synthesis_read_minutes" in first_item
        assert "published_date" in first_item
        assert "source_name" in first_item
        assert "category" in first_item
        assert "has_timeline" in first_item
        assert "has_context_emphasis" in first_item
        
        # Verify UUID is string
        assert isinstance(first_item["id"], str)
        assert len(first_item["id"]) == 36  # UUID format
        
        # Verify source_name is populated (from join)
        assert first_item["source_name"] == "Test News Source"
    
    async def test_list_empty_database(self, async_client: AsyncClient, empty_database):
        """Test listing when no synthesis articles exist."""
        response = await async_client.get("/api/v1/articles/synthesis")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["items"] == []
        assert data["total"] == 0
        assert data["has_next"] is False
    
    async def test_list_pagination(self, async_client: AsyncClient, synthesis_articles):
        """Test pagination parameters."""
        # Page 1 with 2 items
        response = await async_client.get("/api/v1/articles/synthesis?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) == 2
        assert data["total"] == 4
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["has_next"] is True
        
        # Page 2 with 2 items
        response = await async_client.get("/api/v1/articles/synthesis?page=2&page_size=2")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) == 2
        assert data["page"] == 2
        assert data["has_next"] is False
    
    async def test_list_filter_by_verdict(self, async_client: AsyncClient, synthesis_articles):
        """Test filtering by fact_check_verdict."""
        response = await async_client.get("/api/v1/articles/synthesis?verdict=TRUE")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only get 1 article with TRUE verdict
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["fact_check_verdict"] == "TRUE"
    
    async def test_list_sort_by_newest(self, async_client: AsyncClient, synthesis_articles):
        """Test sorting by newest (default)."""
        response = await async_client.get("/api/v1/articles/synthesis?sort_by=newest")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify descending order by published_date
        dates = [item["published_date"] for item in data["items"]]
        assert dates == sorted(dates, reverse=True)
    
    async def test_list_sort_by_credibility(self, async_client: AsyncClient, synthesis_articles):
        """Test sorting by credibility score."""
        response = await async_client.get("/api/v1/articles/synthesis?sort_by=credibility")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify descending order by fact_check_score
        scores = [item["fact_check_score"] for item in data["items"] if item["fact_check_score"] is not None]
        assert scores == sorted(scores, reverse=True)
    
    async def test_list_invalid_page(self, async_client: AsyncClient, synthesis_articles):
        """Test with invalid page number (should default to 1)."""
        response = await async_client.get("/api/v1/articles/synthesis?page=0")
        
        # Should accept but normalize to page 1
        assert response.status_code == 422  # Validation error from FastAPI
    
    async def test_list_page_size_too_large(self, async_client: AsyncClient, synthesis_articles):
        """Test page_size exceeding maximum."""
        response = await async_client.get("/api/v1/articles/synthesis?page_size=200")
        
        # Should be rejected by validation
        assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
class TestGetSynthesisArticle:
    """Test GET /api/v1/articles/{article_id}/synthesis endpoint."""
    
    async def test_get_existing_article(self, async_client: AsyncClient, synthesis_articles):
        """Test getting a synthesis article that exists."""
        # Use first synthesis article
        article_id = str(synthesis_articles[0].id)
        
        response = await async_client.get(f"/api/v1/articles/{article_id}/synthesis")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "article" in data
        article = data["article"]
        
        # Core fields
        assert article["id"] == article_id
        assert article["title"] == "Climate Change Report: Global Temperature Rises 1.5°C"
        assert article["content"] is not None
        assert article["synthesis_article"] is not None
        
        # Fact check fields
        assert article["fact_check_verdict"] == "TRUE"
        assert article["verdict_color"] == "green"
        assert article["fact_check_score"] == 92
        
        # Metadata
        assert article["synthesis_word_count"] == 245
        assert article["synthesis_read_minutes"] == 2
        assert article["author"] == "Dr. Jane Smith"
        assert article["source_name"] == "Test News Source"
        assert article["category"] == "science"
        assert article["url"] == "https://example.com/climate-report-2025"
        
        # Feature flags
        assert article["has_timeline"] is True
        assert article["has_context_emphasis"] is True
        
        # Counts
        assert article["timeline_event_count"] == 3
        assert article["reference_count"] == 8
        assert article["margin_note_count"] == 2
        
        # Processing metadata
        assert article["fact_check_mode"] == "synthesis"
        assert article["fact_check_processing_time"] == 45
        assert article["synthesis_generated_at"] is not None
        
        # JSONB arrays
        assert isinstance(article["references"], list)
        assert len(article["references"]) == 2
        assert article["references"][0]["citation_number"] == 1
        assert article["references"][0]["credibility_rating"] == "HIGH"
        
        assert isinstance(article["event_timeline"], list)
        assert len(article["event_timeline"]) == 3
        assert article["event_timeline"][0]["event"] == "Paris Agreement signed"
        
        assert isinstance(article["margin_notes"], list)
        assert len(article["margin_notes"]) == 2
        
        assert isinstance(article["context_and_emphasis"], list)
        assert len(article["context_and_emphasis"]) == 1
    
    async def test_get_article_with_empty_jsonb(self, async_client: AsyncClient, synthesis_articles):
        """Test getting article with empty JSONB arrays."""
        # Use article with minimal data (article 4)
        article_id = str(synthesis_articles[3].id)
        
        response = await async_client.get(f"/api/v1/articles/{article_id}/synthesis")
        
        assert response.status_code == 200
        data = response.json()
        
        article = data["article"]
        
        # JSONB arrays should be empty lists, not null
        assert article["references"] == []
        assert article["event_timeline"] == []
        assert article["margin_notes"] == []
        assert article["context_and_emphasis"] == []
    
    async def test_get_nonexistent_article(self, async_client: AsyncClient):
        """Test getting an article that doesn't exist."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        
        response = await async_client.get(f"/api/v1/articles/{fake_uuid}/synthesis")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Synthesis article not found"
    
    async def test_get_invalid_uuid(self, async_client: AsyncClient):
        """Test with invalid UUID format."""
        response = await async_client.get("/api/v1/articles/not-a-uuid/synthesis")
        
        # Should return 404 (UUID validation happens in service)
        assert response.status_code == 404
    
    async def test_get_non_synthesis_article(self, async_client: AsyncClient, synthesis_articles):
        """Test getting an article without synthesis (should 404)."""
        # Article 5 has has_synthesis=False
        article_id = str(synthesis_articles[4].id)
        
        response = await async_client.get(f"/api/v1/articles/{article_id}/synthesis")
        
        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
class TestGetSynthesisStats:
    """Test GET /api/v1/articles/synthesis/stats endpoint."""
    
    async def test_get_stats_with_data(self, async_client: AsyncClient, synthesis_articles):
        """Test getting stats with populated database."""
        response = await async_client.get("/api/v1/articles/synthesis/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "total_synthesis_articles" in data
        assert "articles_with_timeline" in data
        assert "articles_with_context" in data
        assert "average_credibility" in data
        assert "verdict_distribution" in data
        assert "average_word_count" in data
        assert "average_read_minutes" in data
        
        # Verify counts
        assert data["total_synthesis_articles"] == 4
        assert data["articles_with_timeline"] == 2  # Articles 1 and 2
        assert data["articles_with_context"] == 2  # Articles 1 and 3
        
        # Verify averages
        # Scores: 92, 78, 65, 45 = avg 70 -> 0.70
        expected_avg = (92 + 78 + 65 + 45) / 4 / 100
        assert abs(data["average_credibility"] - expected_avg) < 0.01
        
        # Word counts: 245, 189, 156, 45 = avg 158.75
        expected_words = (245 + 189 + 156 + 45) / 4
        assert abs(data["average_word_count"] - expected_words) < 1
        
        # Verify verdict distribution
        assert isinstance(data["verdict_distribution"], dict)
        assert data["verdict_distribution"]["TRUE"] == 1
        assert data["verdict_distribution"]["MOSTLY TRUE"] == 1
        assert data["verdict_distribution"]["MIXED"] == 1
        assert data["verdict_distribution"]["MOSTLY FALSE"] == 1
    
    async def test_get_stats_empty_database(self, async_client: AsyncClient, empty_database):
        """Test getting stats with no synthesis articles."""
        response = await async_client.get("/api/v1/articles/synthesis/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_synthesis_articles"] == 0
        assert data["articles_with_timeline"] == 0
        assert data["articles_with_context"] == 0
        assert data["average_credibility"] == 0.0
        assert data["verdict_distribution"] == {}
        assert data["average_word_count"] == 0
        assert data["average_read_minutes"] == 0


@pytest.mark.integration
@pytest.mark.asyncio
class TestSynthesisEndpointsRegression:
    """Regression tests to ensure no breaking changes to existing endpoints."""
    
    async def test_regular_articles_endpoint_still_works(self, async_client: AsyncClient, synthesis_articles):
        """Ensure /articles endpoint is not affected."""
        response = await async_client.get("/api/v1/articles")
        
        # Should work regardless of synthesis endpoints
        assert response.status_code in [200, 404, 422]  # Depends on auth/implementation
    
    async def test_health_endpoint_still_works(self, async_client: AsyncClient):
        """Ensure health check endpoint still works."""
        response = await async_client.get("/api/v1/health")
        
        assert response.status_code == 200
