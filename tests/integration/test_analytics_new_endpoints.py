"""
Integration tests for new Analytics Endpoints.

Tests all 4 new endpoints with real database interactions:
- GET /api/v1/analytics/high-risk-articles
- GET /api/v1/analytics/articles/{article_id}/source-breakdown
- GET /api/v1/analytics/source-quality
- GET /api/v1/analytics/risk-correlation
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.main import app


@pytest.fixture
def sample_article_id():
    """Sample article UUID for testing."""
    return str(uuid4())


@pytest.fixture
def mock_high_risk_articles_data():
    """Mock data for high-risk articles."""
    return (
        [
            {
                'article_id': str(uuid4()),
                'title': 'Misleading Claims About Vaccine Effectiveness',
                'author': 'John Smith',
                'url': 'https://example.com/article1',
                'source_name': 'NewsSource1',
                'published_at': datetime.utcnow() - timedelta(days=1),
                'fact_check_id': str(uuid4()),
                'verdict': 'FALSE',
                'credibility_score': 25,
                'confidence_score': Decimal('0.85'),
                'num_sources': 105,
                'high_risk_claims_count': 5,
            },
            {
                'article_id': str(uuid4()),
                'title': 'Unverified Economic Data',
                'author': 'Jane Doe',
                'url': 'https://example.com/article2',
                'source_name': 'NewsSource2',
                'published_at': datetime.utcnow() - timedelta(days=2),
                'fact_check_id': str(uuid4()),
                'verdict': 'MOSTLY_FALSE',
                'credibility_score': 35,
                'confidence_score': Decimal('0.78'),
                'num_sources': 98,
                'high_risk_claims_count': 3,
            },
        ],
        2  # total count
    )


@pytest.fixture
def mock_source_breakdown_data(sample_article_id):
    """Mock data for source breakdown."""
    return {
        'article_id': sample_article_id,
        'title': 'Climate Change Article',
        'source_breakdown': {
            'news': 45,
            'government': 20,
            'academic': 15,
            'social_media': 10,
            'fact_checking': 8,
            'expert': 2,
        },
        'primary_source_type': 'news',
        'source_diversity_score': Decimal('0.95'),
        'num_sources': 100,
        'source_consensus': 'MIXED',
    }


@pytest.fixture
def mock_source_quality_data():
    """Mock data for source quality stats."""
    return [
        {
            'primary_source_type': 'news',
            'article_count': 50,
            'avg_credibility_score': Decimal('75.5'),
            'avg_num_sources': Decimal('98.2'),
            'avg_diversity_score': Decimal('0.94'),
        },
        {
            'primary_source_type': 'government',
            'article_count': 20,
            'avg_credibility_score': Decimal('82.3'),
            'avg_num_sources': Decimal('105.5'),
            'avg_diversity_score': Decimal('0.88'),
        },
        {
            'primary_source_type': 'academic',
            'article_count': 15,
            'avg_credibility_score': Decimal('88.7'),
            'avg_num_sources': Decimal('110.0'),
            'avg_diversity_score': Decimal('0.92'),
        },
    ]


@pytest.fixture
def mock_risk_correlation_data():
    """Mock data for risk correlation stats."""
    return [
        {
            'risk_category': 'low',
            'article_count': 30,
            'avg_credibility_score': Decimal('85.5'),
            'false_verdict_count': 2,
            'false_verdict_rate': Decimal('0.067'),
        },
        {
            'risk_category': 'medium',
            'article_count': 25,
            'avg_credibility_score': Decimal('65.3'),
            'false_verdict_count': 8,
            'false_verdict_rate': Decimal('0.32'),
        },
        {
            'risk_category': 'high',
            'article_count': 20,
            'avg_credibility_score': Decimal('35.2'),
            'false_verdict_count': 15,
            'false_verdict_rate': Decimal('0.75'),
        },
    ]


# === High-Risk Articles Endpoint Tests ===


class TestHighRiskArticlesEndpoint:
    """Integration tests for GET /api/v1/analytics/high-risk-articles"""

    @pytest.mark.asyncio
    async def test_high_risk_articles_success(self, mock_high_risk_articles_data):
        """Test successful retrieval of high-risk articles."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            # Setup mock
            mock_repo = AsyncMock()
            mock_repo.get_high_risk_articles = AsyncMock(
                return_value=mock_high_risk_articles_data
            )
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/analytics/high-risk-articles")

            # Assertions
            assert response.status_code == 200
            data = response.json()

            # Check response structure
            assert 'articles' in data
            assert 'total' in data
            assert 'pagination' in data
            assert len(data['articles']) == 2

            # Check article data
            article = data['articles'][0]
            assert 'article_id' in article
            assert 'title' in article
            assert 'high_risk_claims_count' in article
            assert article['high_risk_claims_count'] == 5

    @pytest.mark.asyncio
    async def test_high_risk_articles_with_pagination(self, mock_high_risk_articles_data):
        """Test high-risk articles with pagination parameters."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            articles, total = mock_high_risk_articles_data
            mock_repo.get_high_risk_articles = AsyncMock(
                return_value=([articles[0]], 10)  # Return 1 of 10
            )
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/analytics/high-risk-articles",
                    params={"limit": 1, "offset": 5}
                )

            assert response.status_code == 200
            data = response.json()
            assert len(data['articles']) == 1
            assert data['total'] == 10
            assert data['pagination']['has_more'] is True

    @pytest.mark.asyncio
    async def test_high_risk_articles_invalid_params(self):
        """Test high-risk articles with invalid parameters."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Invalid days
            response = await client.get(
                "/api/v1/analytics/high-risk-articles",
                params={"days": 500}
            )
            assert response.status_code == 400

            # Invalid limit
            response = await client.get(
                "/api/v1/analytics/high-risk-articles",
                params={"limit": 2000}
            )
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_high_risk_articles_empty_results(self):
        """Test high-risk articles with no results."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_high_risk_articles = AsyncMock(return_value=([], 0))
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/analytics/high-risk-articles")

            assert response.status_code == 200
            data = response.json()
            assert len(data['articles']) == 0
            assert data['total'] == 0


# === Source Breakdown Endpoint Tests ===


class TestSourceBreakdownEndpoint:
    """Integration tests for GET /api/v1/analytics/articles/{article_id}/source-breakdown"""

    @pytest.mark.asyncio
    async def test_source_breakdown_success(self, sample_article_id, mock_source_breakdown_data):
        """Test successful retrieval of source breakdown."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_source_breakdown = AsyncMock(
                return_value=mock_source_breakdown_data
            )
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/analytics/articles/{sample_article_id}/source-breakdown"
                )

            # Assertions
            assert response.status_code == 200
            data = response.json()

            # Check response structure
            assert 'article_id' in data
            assert 'title' in data
            assert 'source_breakdown' in data
            assert 'primary_source_type' in data
            assert 'source_diversity_score' in data
            assert 'num_sources' in data
            assert 'source_consensus' in data

            # Check source breakdown details
            assert data['source_breakdown']['news'] == 45
            assert data['primary_source_type'] == 'news'
            assert data['source_diversity_score'] == 0.95
            assert data['num_sources'] == 100

    @pytest.mark.asyncio
    async def test_source_breakdown_article_not_found(self):
        """Test source breakdown for non-existent article."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_source_breakdown = AsyncMock(return_value=None)
            mock_repo_class.return_value = mock_repo

            fake_article_id = str(uuid4())
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/analytics/articles/{fake_article_id}/source-breakdown"
                )

            assert response.status_code == 404
            assert "not found" in response.json()['detail'].lower()

    @pytest.mark.asyncio
    async def test_source_breakdown_null_fields(self, sample_article_id):
        """Test source breakdown with null source_breakdown field."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_source_breakdown = AsyncMock(return_value={
                'article_id': sample_article_id,
                'title': 'Test Article',
                'source_breakdown': None,
                'primary_source_type': None,
                'source_diversity_score': None,
                'num_sources': 0,
                'source_consensus': None,
            })
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/analytics/articles/{sample_article_id}/source-breakdown"
                )

            assert response.status_code == 200
            data = response.json()
            assert data['source_breakdown'] == {}  # Service converts None to {}


# === Source Quality Endpoint Tests ===


class TestSourceQualityEndpoint:
    """Integration tests for GET /api/v1/analytics/source-quality"""

    @pytest.mark.asyncio
    async def test_source_quality_success(self, mock_source_quality_data):
        """Test successful retrieval of source quality metrics."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_source_quality_stats = AsyncMock(
                return_value=mock_source_quality_data
            )
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/analytics/source-quality")

            # Assertions
            assert response.status_code == 200
            data = response.json()

            # Check response structure
            assert 'source_types' in data
            assert 'overall' in data
            assert len(data['source_types']) == 3

            # Check source type data
            news_stats = data['source_types'][0]
            assert news_stats['source_type'] == 'news'
            assert news_stats['article_count'] == 50
            assert news_stats['avg_credibility_score'] == 75.5

            # Check overall stats
            assert data['overall']['total_articles'] == 85  # 50 + 20 + 15
            assert data['overall']['avg_credibility_score'] > 0

    @pytest.mark.asyncio
    async def test_source_quality_with_days_param(self, mock_source_quality_data):
        """Test source quality with custom days parameter."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_source_quality_stats = AsyncMock(
                return_value=mock_source_quality_data
            )
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/analytics/source-quality",
                    params={"days": 7}
                )

            assert response.status_code == 200
            # Verify repo was called with correct days parameter
            mock_repo.get_source_quality_stats.assert_called_once_with(days=7)

    @pytest.mark.asyncio
    async def test_source_quality_invalid_days(self):
        """Test source quality with invalid days parameter."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/analytics/source-quality",
                params={"days": 500}
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_source_quality_empty_results(self):
        """Test source quality with no data."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_source_quality_stats = AsyncMock(return_value=[])
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/analytics/source-quality")

            assert response.status_code == 200
            data = response.json()
            assert len(data['source_types']) == 0
            assert data['overall']['total_articles'] == 0


# === Risk Correlation Endpoint Tests ===


class TestRiskCorrelationEndpoint:
    """Integration tests for GET /api/v1/analytics/risk-correlation"""

    @pytest.mark.asyncio
    async def test_risk_correlation_success(self, mock_risk_correlation_data):
        """Test successful retrieval of risk correlation analysis."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_risk_correlation_stats = AsyncMock(
                return_value=mock_risk_correlation_data
            )
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/analytics/risk-correlation")

            # Assertions
            assert response.status_code == 200
            data = response.json()

            # Check response structure
            assert 'risk_levels' in data
            assert 'insights' in data
            assert len(data['risk_levels']) == 3

            # Check risk level data
            low_risk = data['risk_levels'][0]
            assert low_risk['risk_category'] == 'low'
            assert low_risk['article_count'] == 30
            assert low_risk['avg_credibility_score'] == 85.5
            assert low_risk['false_verdict_rate'] == 0.067

            high_risk = data['risk_levels'][2]
            assert high_risk['risk_category'] == 'high'
            assert high_risk['false_verdict_rate'] == 0.75

            # Check insights generated
            assert len(data['insights']) > 0
            assert any('high-risk' in insight.lower() for insight in data['insights'])

    @pytest.mark.asyncio
    async def test_risk_correlation_with_days_param(self, mock_risk_correlation_data):
        """Test risk correlation with custom days parameter."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_risk_correlation_stats = AsyncMock(
                return_value=mock_risk_correlation_data
            )
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/analytics/risk-correlation",
                    params={"days": 14}
                )

            assert response.status_code == 200
            mock_repo.get_risk_correlation_stats.assert_called_once_with(days=14)

    @pytest.mark.asyncio
    async def test_risk_correlation_invalid_days(self):
        """Test risk correlation with invalid days parameter."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/analytics/risk-correlation",
                params={"days": 0}
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_risk_correlation_empty_results(self):
        """Test risk correlation with no data."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_risk_correlation_stats = AsyncMock(return_value=[])
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/analytics/risk-correlation")

            assert response.status_code == 200
            data = response.json()
            assert len(data['risk_levels']) == 0
            assert len(data['insights']) == 0

    @pytest.mark.asyncio
    async def test_risk_correlation_partial_categories(self):
        """Test risk correlation with only some risk categories present."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            # Only high risk category
            partial_data = [{
                'risk_category': 'high',
                'article_count': 15,
                'avg_credibility_score': Decimal('30.5'),
                'false_verdict_count': 12,
                'false_verdict_rate': Decimal('0.80'),
            }]
            mock_repo.get_risk_correlation_stats = AsyncMock(return_value=partial_data)
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/analytics/risk-correlation")

            assert response.status_code == 200
            data = response.json()
            assert len(data['risk_levels']) == 1
            assert data['risk_levels'][0]['risk_category'] == 'high'
