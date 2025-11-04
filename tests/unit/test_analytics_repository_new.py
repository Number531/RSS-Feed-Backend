"""
Unit tests for new AnalyticsRepository methods.

Tests cover:
- get_high_risk_articles
- get_source_breakdown
- get_source_quality_stats
- get_risk_correlation_stats
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from uuid import uuid4

from app.repositories.analytics_repository import AnalyticsRepository


@pytest.fixture
def mock_db_session():
    """Mock AsyncSession."""
    return AsyncMock()


@pytest.fixture
def analytics_repo(mock_db_session):
    """AnalyticsRepository with mocked session."""
    return AnalyticsRepository(mock_db_session)


def create_mock_mapping(data_dict):
    """Create a mock object that behaves like a dict mapping."""
    mock = MagicMock()
    mock.__getitem__ = lambda self, key: data_dict[key]
    mock.__contains__ = lambda self, key: key in data_dict
    mock.keys = lambda: data_dict.keys()
    mock.values = lambda: data_dict.values()
    mock.items = lambda: data_dict.items()
    mock.__iter__ = lambda self: iter(data_dict.keys())
    return mock


# === Test Data Fixtures ===


@pytest.fixture
def sample_high_risk_articles():
    """Sample high-risk articles data."""
    return [
        {
            'article_id': str(uuid4()),
            'title': 'High Risk Article 1',
            'author': 'Author 1',
            'url': 'https://example.com/article1',
            'source_name': 'Test Source 1',
            'published_at': datetime.utcnow() - timedelta(days=1),
            'fact_check_id': str(uuid4()),
            'verdict': 'FALSE',
            'credibility_score': 25,
            'confidence_score': Decimal('0.85'),
            'num_sources': 100,
            'high_risk_claims_count': 5,
        },
        {
            'article_id': str(uuid4()),
            'title': 'High Risk Article 2',
            'author': 'Author 2',
            'url': 'https://example.com/article2',
            'source_name': 'Test Source 2',
            'published_at': datetime.utcnow() - timedelta(days=2),
            'fact_check_id': str(uuid4()),
            'verdict': 'MOSTLY_FALSE',
            'credibility_score': 35,
            'confidence_score': Decimal('0.78'),
            'num_sources': 95,
            'high_risk_claims_count': 3,
        },
    ]


@pytest.fixture
def sample_source_breakdown():
    """Sample source breakdown data."""
    return {
        'article_id': str(uuid4()),
        'title': 'Test Article',
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
def sample_source_quality_stats():
    """Sample source quality statistics."""
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
def sample_risk_correlation_stats():
    """Sample risk correlation statistics."""
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


# === Test Classes ===


class TestGetHighRiskArticles:
    """Test get_high_risk_articles repository method."""

    @pytest.mark.asyncio
    async def test_get_high_risk_articles_success(
        self,
        analytics_repo,
        mock_db_session,
        sample_high_risk_articles
    ):
        """Test getting high-risk articles with data."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [
            create_mock_mapping(article) for article in sample_high_risk_articles
        ]
        mock_result.mappings.return_value = mock_mappings
        
        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = len(sample_high_risk_articles)
        
        # Execute method will be called twice (once for data, once for count)
        mock_db_session.execute = AsyncMock(
            side_effect=[mock_result, mock_count_result]
        )

        # Execute
        articles, total = await analytics_repo.get_high_risk_articles(
            days=30, limit=100, offset=0
        )

        # Verify
        assert len(articles) == 2
        assert total == 2
        assert articles[0]['title'] == 'High Risk Article 1'
        assert articles[0]['high_risk_claims_count'] == 5
        assert articles[1]['verdict'] == 'MOSTLY_FALSE'
        assert mock_db_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_get_high_risk_articles_empty(
        self,
        analytics_repo,
        mock_db_session
    ):
        """Test getting high-risk articles with no data."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = []
        mock_result.mappings.return_value = mock_mappings
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        
        mock_db_session.execute = AsyncMock(
            side_effect=[mock_result, mock_count_result]
        )

        # Execute
        articles, total = await analytics_repo.get_high_risk_articles(
            days=30, limit=100, offset=0
        )

        # Verify
        assert len(articles) == 0
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_high_risk_articles_pagination(
        self,
        analytics_repo,
        mock_db_session,
        sample_high_risk_articles
    ):
        """Test pagination parameters."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [
            create_mock_mapping(sample_high_risk_articles[0])
        ]
        mock_result.mappings.return_value = mock_mappings
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 10  # Total is more than returned
        
        mock_db_session.execute = AsyncMock(
            side_effect=[mock_result, mock_count_result]
        )

        # Execute with offset
        articles, total = await analytics_repo.get_high_risk_articles(
            days=30, limit=1, offset=5
        )

        # Verify pagination
        assert len(articles) == 1
        assert total == 10


class TestGetSourceBreakdown:
    """Test get_source_breakdown repository method."""

    @pytest.mark.asyncio
    async def test_get_source_breakdown_success(
        self,
        analytics_repo,
        mock_db_session,
        sample_source_breakdown
    ):
        """Test getting source breakdown with data."""
        # Setup
        mock_result = MagicMock()
        mock_result.mappings().first.return_value = create_mock_mapping(
            sample_source_breakdown
        )
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        result = await analytics_repo.get_source_breakdown(
            article_id=sample_source_breakdown['article_id']
        )

        # Verify
        assert result is not None
        assert result['title'] == 'Test Article'
        assert result['num_sources'] == 100
        assert result['primary_source_type'] == 'news'
        assert result['source_diversity_score'] == Decimal('0.95')
        assert 'news' in result['source_breakdown']
        assert result['source_breakdown']['news'] == 45

    @pytest.mark.asyncio
    async def test_get_source_breakdown_not_found(
        self,
        analytics_repo,
        mock_db_session
    ):
        """Test getting source breakdown for non-existent article."""
        # Setup
        mock_result = MagicMock()
        mock_result.mappings().first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        result = await analytics_repo.get_source_breakdown(
            article_id=str(uuid4())
        )

        # Verify
        assert result is None

    @pytest.mark.asyncio
    async def test_get_source_breakdown_null_fields(
        self,
        analytics_repo,
        mock_db_session
    ):
        """Test handling of null fields in source breakdown."""
        # Setup data with nulls
        data = {
            'article_id': str(uuid4()),
            'title': 'Test Article',
            'source_breakdown': None,
            'primary_source_type': None,
            'source_diversity_score': None,
            'num_sources': 0,
            'source_consensus': None,
        }
        
        mock_result = MagicMock()
        mock_result.mappings().first.return_value = create_mock_mapping(data)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        result = await analytics_repo.get_source_breakdown(article_id=data['article_id'])

        # Verify graceful handling
        assert result is not None
        assert result['source_breakdown'] is None
        assert result['primary_source_type'] is None


class TestGetSourceQualityStats:
    """Test get_source_quality_stats repository method."""

    @pytest.mark.asyncio
    async def test_get_source_quality_stats_success(
        self,
        analytics_repo,
        mock_db_session,
        sample_source_quality_stats
    ):
        """Test getting source quality stats with data."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [
            create_mock_mapping(stat) for stat in sample_source_quality_stats
        ]
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        results = await analytics_repo.get_source_quality_stats(days=30)

        # Verify
        assert len(results) == 3
        assert results[0]['primary_source_type'] == 'news'
        assert results[0]['article_count'] == 50
        assert results[1]['primary_source_type'] == 'government'
        assert results[2]['avg_credibility_score'] == Decimal('88.7')

    @pytest.mark.asyncio
    async def test_get_source_quality_stats_empty(
        self,
        analytics_repo,
        mock_db_session
    ):
        """Test getting source quality stats with no data."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = []
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        results = await analytics_repo.get_source_quality_stats(days=30)

        # Verify
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_get_source_quality_stats_single_type(
        self,
        analytics_repo,
        mock_db_session
    ):
        """Test with only one source type."""
        # Setup single source type
        single_type = [{
            'primary_source_type': 'news',
            'article_count': 100,
            'avg_credibility_score': Decimal('78.5'),
            'avg_num_sources': Decimal('95.0'),
            'avg_diversity_score': Decimal('0.93'),
        }]
        
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [create_mock_mapping(single_type[0])]
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        results = await analytics_repo.get_source_quality_stats(days=30)

        # Verify
        assert len(results) == 1
        assert results[0]['primary_source_type'] == 'news'


class TestGetRiskCorrelationStats:
    """Test get_risk_correlation_stats repository method."""

    @pytest.mark.asyncio
    async def test_get_risk_correlation_stats_success(
        self,
        analytics_repo,
        mock_db_session,
        sample_risk_correlation_stats
    ):
        """Test getting risk correlation stats with data."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [
            create_mock_mapping(stat) for stat in sample_risk_correlation_stats
        ]
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        results = await analytics_repo.get_risk_correlation_stats(days=30)

        # Verify
        assert len(results) == 3
        assert results[0]['risk_category'] == 'low'
        assert results[0]['false_verdict_rate'] == Decimal('0.067')
        assert results[2]['risk_category'] == 'high'
        assert results[2]['false_verdict_rate'] == Decimal('0.75')

    @pytest.mark.asyncio
    async def test_get_risk_correlation_stats_empty(
        self,
        analytics_repo,
        mock_db_session
    ):
        """Test getting risk correlation stats with no data."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = []
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        results = await analytics_repo.get_risk_correlation_stats(days=30)

        # Verify
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_get_risk_correlation_stats_partial_categories(
        self,
        analytics_repo,
        mock_db_session
    ):
        """Test with only some risk categories present."""
        # Setup with only high risk
        partial_data = [{
            'risk_category': 'high',
            'article_count': 15,
            'avg_credibility_score': Decimal('30.5'),
            'false_verdict_count': 12,
            'false_verdict_rate': Decimal('0.80'),
        }]
        
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [create_mock_mapping(partial_data[0])]
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        results = await analytics_repo.get_risk_correlation_stats(days=30)

        # Verify
        assert len(results) == 1
        assert results[0]['risk_category'] == 'high'
        assert results[0]['false_verdict_rate'] == Decimal('0.80')

    @pytest.mark.asyncio
    async def test_get_risk_correlation_stats_zero_false_rate(
        self,
        analytics_repo,
        mock_db_session
    ):
        """Test category with zero false verdicts."""
        # Setup with all true verdicts
        data = [{
            'risk_category': 'low',
            'article_count': 20,
            'avg_credibility_score': Decimal('90.0'),
            'false_verdict_count': 0,
            'false_verdict_rate': Decimal('0.00'),
        }]
        
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [create_mock_mapping(data[0])]
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        results = await analytics_repo.get_risk_correlation_stats(days=30)

        # Verify
        assert len(results) == 1
        assert results[0]['false_verdict_rate'] == Decimal('0.00')
