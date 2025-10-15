"""
Integration tests for search endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.models.article import Article
from app.models.rss_source import RSSSource
from tests.utils import generate_url_hash


@pytest.mark.integration
class TestSearchEndpoint:
    """Test article search endpoint."""
    
    async def test_basic_search(
        self,
        client: AsyncClient,
        test_db: AsyncSession
    ):
        """Test basic article search."""
        # Create RSS source
        source = RSSSource(
            name="Test Source",
            url="https://example.com/feed.xml",
            source_name="Test Source",
            category="technology",
            is_active=True
        )
        test_db.add(source)
        await test_db.commit()
        await test_db.refresh(source)
        
        # Create test articles
        articles = [
            Article(
                rss_source_id=source.id,
                title="Machine Learning Tutorial",
                url="https://example.com/ml-tutorial",
                url_hash=generate_url_hash("https://example.com/ml-tutorial"),
                description="Learn about machine learning algorithms",
                content="Deep dive into machine learning",
                category="technology",
                vote_score=10,
                comment_count=5
            ),
            Article(
                rss_source_id=source.id,
                title="Python Programming Guide",
                url="https://example.com/python-guide",
                url_hash=generate_url_hash("https://example.com/python-guide"),
                description="Complete Python programming tutorial",
                content="Learn Python from scratch",
                category="technology",
                vote_score=5,
                comment_count=2
            ),
            Article(
                rss_source_id=source.id,
                title="Web Development Best Practices",
                url="https://example.com/web-dev",
                url_hash=generate_url_hash("https://example.com/web-dev"),
                description="Modern web development techniques",
                content="Best practices for building websites",
                category="technology",
                vote_score=8,
                comment_count=3
            )
        ]
        
        for article in articles:
            test_db.add(article)
        await test_db.commit()
        
        # Search for "machine learning"
        response = await client.get("/api/v1/search?q=machine learning")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "total" in data
        assert "query" in data
        assert data["query"] == "machine learning"
        assert data["total"] >= 1
        
        # Verify the ML article is in results
        titles = [r["title"] for r in data["results"]]
        assert "Machine Learning Tutorial" in titles
    
    async def test_search_with_filters(
        self,
        client: AsyncClient,
        test_db: AsyncSession
    ):
        """Test search with category filter."""
        # Create RSS sources
        tech_source = RSSSource(
            name="Tech Source",
            url="https://example.com/tech.xml",
            source_name="Tech Source",
            category="technology",
            is_active=True
        )
        politics_source = RSSSource(
            name="Politics Source",
            url="https://example.com/politics.xml",
            source_name="Politics Source",
            category="politics",
            is_active=True
        )
        test_db.add(tech_source)
        test_db.add(politics_source)
        await test_db.commit()
        await test_db.refresh(tech_source)
        await test_db.refresh(politics_source)
        
        # Create articles in different categories
        tech_article = Article(
            rss_source_id=tech_source.id,
            title="Technology News Article",
            url="https://example.com/tech-news",
            url_hash=generate_url_hash("https://example.com/tech-news"),
            description="Latest in technology",
            content="Technology update",
            category="technology"
        )
        politics_article = Article(
            rss_source_id=politics_source.id,
            title="Politics News Article",
            url="https://example.com/politics-news",
            url_hash=generate_url_hash("https://example.com/politics-news"),
            description="Latest in politics",
            content="Politics update",
            category="politics"
        )
        
        test_db.add(tech_article)
        test_db.add(politics_article)
        await test_db.commit()
        
        # Search with category filter
        response = await client.get("/api/v1/search?q=news&category=technology")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify only technology articles are returned
        for result in data["results"]:
            assert result["category"] == "technology"
    
    async def test_search_pagination(
        self,
        client: AsyncClient,
        test_db: AsyncSession
    ):
        """Test search pagination."""
        # Create RSS source
        source = RSSSource(
            name="Test Source",
            url="https://example.com/feed.xml",
            source_name="Test Source",
            category="technology",
            is_active=True
        )
        test_db.add(source)
        await test_db.commit()
        await test_db.refresh(source)
        
        # Create multiple articles
        for i in range(15):
            url = f"https://example.com/article-{i}"
            article = Article(
                rss_source_id=source.id,
                title=f"Test Article {i}",
                url=url,
                url_hash=generate_url_hash(url),
                description="Test article description",
                content="Test article content",
                category="technology"
            )
            test_db.add(article)
        await test_db.commit()
        
        # Get first page
        response = await client.get("/api/v1/search?q=test&page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert len(data["results"]) == 10
        assert data["total"] == 15
        assert data["total_pages"] == 2
        
        # Get second page
        response = await client.get("/api/v1/search?q=test&page=2&page_size=10")
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 2
        assert len(data["results"]) == 5
    
    async def test_search_empty_query(
        self,
        client: AsyncClient
    ):
        """Test search with empty query."""
        response = await client.get("/api/v1/search?q=")
        
        # Should return 422 validation error
        assert response.status_code == 422
    
    async def test_search_no_results(
        self,
        client: AsyncClient
    ):
        """Test search with no matching results."""
        response = await client.get("/api/v1/search?q=nonexistent12345xyz")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 0
        assert len(data["results"]) == 0


@pytest.mark.integration
class TestTrendingEndpoint:
    """Test trending articles endpoint."""
    
    async def test_get_trending_articles(
        self,
        client: AsyncClient,
        test_db: AsyncSession
    ):
        """Test getting trending articles."""
        # Create RSS source
        source = RSSSource(
            name="Test Source",
            url="https://example.com/feed.xml",
            source_name="Test Source",
            category="technology",
            is_active=True
        )
        test_db.add(source)
        await test_db.commit()
        await test_db.refresh(source)
        
        # Create recent articles with votes
        now = datetime.utcnow()
        articles = [
            Article(
                rss_source_id=source.id,
                title="Trending Article 1",
                url="https://example.com/trending-1",
                url_hash=generate_url_hash("https://example.com/trending-1"),
                description="Hot trending article",
                content="Trending content",
                category="technology",
                vote_score=50,
                comment_count=20,
                created_at=now - timedelta(hours=2)
            ),
            Article(
                rss_source_id=source.id,
                title="Trending Article 2",
                url="https://example.com/trending-2",
                url_hash=generate_url_hash("https://example.com/trending-2"),
                description="Another trending article",
                content="More trending content",
                category="technology",
                vote_score=30,
                comment_count=15,
                created_at=now - timedelta(hours=3)
            )
        ]
        
        for article in articles:
            test_db.add(article)
        await test_db.commit()
        
        # Get trending articles
        response = await client.get("/api/v1/trending")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "articles" in data
        assert "total" in data
        assert "period" in data
        assert data["period"] == "24h"
        
        # Verify articles have velocity metrics
        if len(data["articles"]) > 0:
            article = data["articles"][0]
            assert "vote_velocity" in article
            assert "engagement_score" in article
            assert isinstance(article["vote_velocity"], (int, float))
            assert isinstance(article["engagement_score"], (int, float))
    
    async def test_trending_period_filter(
        self,
        client: AsyncClient
    ):
        """Test trending articles with different time periods."""
        # Test 24h period
        response = await client.get("/api/v1/trending?period=24h")
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "24h"
        
        # Test 7d period
        response = await client.get("/api/v1/trending?period=7d")
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "7d"
        
        # Test 30d period
        response = await client.get("/api/v1/trending?period=30d")
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "30d"
    
    async def test_trending_limit(
        self,
        client: AsyncClient
    ):
        """Test trending articles with limit."""
        response = await client.get("/api/v1/trending?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should not return more than 5 articles
        assert len(data["articles"]) <= 5


@pytest.mark.integration
class TestPopularEndpoint:
    """Test popular articles endpoint."""
    
    async def test_get_popular_articles(
        self,
        client: AsyncClient,
        test_db: AsyncSession
    ):
        """Test getting popular articles."""
        # Create RSS source
        source = RSSSource(
            name="Test Source",
            url="https://example.com/feed.xml",
            source_name="Test Source",
            category="technology",
            is_active=True
        )
        test_db.add(source)
        await test_db.commit()
        await test_db.refresh(source)
        
        # Create articles with different vote scores
        articles = [
            Article(
                rss_source_id=source.id,
                title="Most Popular Article",
                url="https://example.com/popular-1",
                url_hash=generate_url_hash("https://example.com/popular-1"),
                description="Most popular",
                content="Very popular content",
                category="technology",
                vote_score=100
            ),
            Article(
                rss_source_id=source.id,
                title="Second Popular Article",
                url="https://example.com/popular-2",
                url_hash=generate_url_hash("https://example.com/popular-2"),
                description="Second most popular",
                content="Popular content",
                category="technology",
                vote_score=50
            ),
            Article(
                rss_source_id=source.id,
                title="Third Popular Article",
                url="https://example.com/popular-3",
                url_hash=generate_url_hash("https://example.com/popular-3"),
                description="Third most popular",
                content="Less popular content",
                category="technology",
                vote_score=25
            )
        ]
        
        for article in articles:
            test_db.add(article)
        await test_db.commit()
        
        # Get popular articles
        response = await client.get("/api/v1/popular")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "articles" in data
        assert "total" in data
        assert data["period"] == "all"
        
        # Verify articles are sorted by vote_score (descending)
        if len(data["articles"]) >= 2:
            assert data["articles"][0]["vote_score"] >= data["articles"][1]["vote_score"]
    
    async def test_popular_period_filter(
        self,
        client: AsyncClient
    ):
        """Test popular articles with different time periods."""
        # Test all time
        response = await client.get("/api/v1/popular?period=all")
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "all"
        
        # Test day
        response = await client.get("/api/v1/popular?period=day")
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "day"
        
        # Test week
        response = await client.get("/api/v1/popular?period=week")
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "week"
    
    async def test_popular_limit(
        self,
        client: AsyncClient
    ):
        """Test popular articles with limit."""
        response = await client.get("/api/v1/popular?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should not return more than 10 articles
        assert len(data["articles"]) <= 10
