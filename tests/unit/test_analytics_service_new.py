"""
Unit tests for new AnalyticsService methods.

Tests cover:
- get_high_risk_articles
- get_source_breakdown
- get_source_quality
- get_risk_correlation
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from decimal import Decimal
from uuid import uuid4

from app.services.analytics_service import AnalyticsService
from app.core.exceptions import ValidationError


@pytest.fixture
def mock_analytics_repo():
    """Mock AnalyticsRepository."""
    return AsyncMock()


@pytest.fixture
def analytics_service(mock_analytics_repo):
    """AnalyticsService with mocked repository."""
    return AnalyticsService(mock_analytics_repo)


# === Test Data Fixtures ===


@pytest.fixture
def sample_high_risk_articles_data():
    """Sample high-risk articles repository data."""
    return (
        [
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
        ],
        2  # total count
    )


@pytest.fixture
def sample_source_breakdown_data():
    """Sample source breakdown repository data."""
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
def sample_source_quality_data():
    """Sample source quality repository data."""
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
    ]


@pytest.fixture
def sample_risk_correlation_data():
    """Sample risk correlation repository data."""
    return [
        {
            'risk_category': 'low',
            'article_count': 30,
            'avg_credibility_score': Decimal('85.5'),
            'false_verdict_count': 2,
            'false_verdict_rate': Decimal('0.067'),
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
    """Test get_high_risk_articles service method."""

    @pytest.mark.asyncio
    async def test_success_with_valid_params(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_high_risk_articles_data
    ):
        """Test successful retrieval with valid parameters."""
        # Setup
        mock_analytics_repo.get_high_risk_articles.return_value = sample_high_risk_articles_data

        # Execute
        result = await analytics_service.get_high_risk_articles(
            days=30, limit=100, offset=0
        )

        # Verify
        assert result['total'] == 2
        assert len(result['articles']) == 2
        assert result['articles'][0]['title'] == 'High Risk Article 1'
        assert result['articles'][0]['high_risk_claims_count'] == 5
        assert result['pagination']['limit'] == 100
        assert result['pagination']['offset'] == 0
        mock_analytics_repo.get_high_risk_articles.assert_called_once_with(
            days=30, limit=100, offset=0
        )

    @pytest.mark.asyncio
    async def test_empty_results(
        self,
        analytics_service,
        mock_analytics_repo
    ):
        """Test handling of empty results."""
        # Setup
        mock_analytics_repo.get_high_risk_articles.return_value = ([], 0)

        # Execute
        result = await analytics_service.get_high_risk_articles(
            days=30, limit=100, offset=0
        )

        # Verify
        assert result['total'] == 0
        assert len(result['articles']) == 0

    @pytest.mark.asyncio
    async def test_invalid_days_too_low(self, analytics_service):
        """Test ValidationError when days < 1."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_high_risk_articles(
                days=0, limit=100, offset=0
            )

        assert "Days parameter must be between 1 and 365" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_days_too_high(self, analytics_service):
        """Test ValidationError when days > 365."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_high_risk_articles(
                days=366, limit=100, offset=0
            )

        assert "Days parameter must be between 1 and 365" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_limit_too_low(self, analytics_service):
        """Test ValidationError when limit < 1."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_high_risk_articles(
                days=30, limit=0, offset=0
            )

        assert "Limit parameter must be between 1 and 1000" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_limit_too_high(self, analytics_service):
        """Test ValidationError when limit > 1000."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_high_risk_articles(
                days=30, limit=1001, offset=0
            )

        assert "Limit parameter must be between 1 and 1000" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_offset_negative(self, analytics_service):
        """Test ValidationError when offset < 0."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_high_risk_articles(
                days=30, limit=100, offset=-1
            )

        assert "Offset parameter must be >= 0" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_pagination_metadata(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_high_risk_articles_data
    ):
        """Test pagination metadata in response."""
        # Setup
        articles, total = sample_high_risk_articles_data
        mock_analytics_repo.get_high_risk_articles.return_value = ([articles[0]], 10)

        # Execute with pagination
        result = await analytics_service.get_high_risk_articles(
            days=30, limit=1, offset=5
        )

        # Verify
        assert result['total'] == 10
        assert result['pagination']['has_more'] is True
        assert len(result['articles']) == 1


class TestGetSourceBreakdown:
    """Test get_source_breakdown service method."""

    @pytest.mark.asyncio
    async def test_success_with_valid_article(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_source_breakdown_data
    ):
        """Test successful retrieval for existing article."""
        # Setup
        mock_analytics_repo.get_source_breakdown.return_value = sample_source_breakdown_data

        # Execute
        result = await analytics_service.get_source_breakdown(
            article_id=sample_source_breakdown_data['article_id']
        )

        # Verify
        assert result['article_id'] == sample_source_breakdown_data['article_id']
        assert result['title'] == 'Test Article'
        assert result['num_sources'] == 100
        assert result['source_diversity_score'] == 0.95
        assert 'news' in result['source_breakdown']
        mock_analytics_repo.get_source_breakdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_article_not_found(
        self,
        analytics_service,
        mock_analytics_repo
    ):
        """Test handling of non-existent article."""
        # Setup
        mock_analytics_repo.get_source_breakdown.return_value = None

        # Execute
        result = await analytics_service.get_source_breakdown(
            article_id=str(uuid4())
        )

        # Verify
        assert result is None

    @pytest.mark.asyncio
    async def test_null_source_breakdown(
        self,
        analytics_service,
        mock_analytics_repo
    ):
        """Test handling of null source_breakdown field."""
        # Setup
        data = {
            'article_id': str(uuid4()),
            'title': 'Test',
            'source_breakdown': None,
            'primary_source_type': None,
            'source_diversity_score': None,
            'num_sources': 0,
            'source_consensus': None,
        }
        mock_analytics_repo.get_source_breakdown.return_value = data

        # Execute
        result = await analytics_service.get_source_breakdown(
            article_id=data['article_id']
        )

        # Verify graceful handling
        assert result is not None
        assert result['source_breakdown'] == {}  # Service converts None to {}

    @pytest.mark.asyncio
    async def test_decimal_conversion(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_source_breakdown_data
    ):
        """Test Decimal to float conversion in response."""
        # Setup
        mock_analytics_repo.get_source_breakdown.return_value = sample_source_breakdown_data

        # Execute
        result = await analytics_service.get_source_breakdown(
            article_id=sample_source_breakdown_data['article_id']
        )

        # Verify type conversion
        assert isinstance(result['source_diversity_score'], float)
        assert result['source_diversity_score'] == 0.95


class TestGetSourceQuality:
    """Test get_source_quality service method."""

    @pytest.mark.asyncio
    async def test_success_with_valid_params(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_source_quality_data
    ):
        """Test successful retrieval with valid parameters."""
        # Setup
        mock_analytics_repo.get_source_quality_stats.return_value = sample_source_quality_data

        # Execute
        result = await analytics_service.get_source_quality(days=30)

        # Verify
        assert len(result['source_types']) == 2
        assert result['source_types'][0]['source_type'] == 'news'
        assert result['source_types'][0]['article_count'] == 50
        assert 'overall' in result
        assert result['overall']['avg_credibility_score'] > 0
        mock_analytics_repo.get_source_quality_stats.assert_called_once_with(days=30)

    @pytest.mark.asyncio
    async def test_empty_results(
        self,
        analytics_service,
        mock_analytics_repo
    ):
        """Test handling of empty results."""
        # Setup
        mock_analytics_repo.get_source_quality_stats.return_value = []

        # Execute
        result = await analytics_service.get_source_quality(days=30)

        # Verify
        assert len(result['source_types']) == 0
        assert result['overall']['avg_credibility_score'] == 0.0

    @pytest.mark.asyncio
    async def test_invalid_days_too_low(self, analytics_service):
        """Test ValidationError when days < 1."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_source_quality(days=0)

        assert "Days parameter must be between 1 and 365" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_days_too_high(self, analytics_service):
        """Test ValidationError when days > 365."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_source_quality(days=400)

        assert "Days parameter must be between 1 and 365" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_weighted_average_calculation(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_source_quality_data
    ):
        """Test weighted average calculation in overall stats."""
        # Setup
        mock_analytics_repo.get_source_quality_stats.return_value = sample_source_quality_data

        # Execute
        result = await analytics_service.get_source_quality(days=30)

        # Verify weighted calculations
        # news: 50 articles * 75.5 = 3775
        # government: 20 articles * 82.3 = 1646
        # total: 70 articles, sum: 5421, weighted avg: 77.44
        assert result['overall']['total_articles'] == 70
        expected_avg = round((50 * 75.5 + 20 * 82.3) / 70, 2)
        assert result['overall']['avg_credibility_score'] == expected_avg

    @pytest.mark.asyncio
    async def test_decimal_to_float_conversion(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_source_quality_data
    ):
        """Test Decimal to float conversion in response."""
        # Setup
        mock_analytics_repo.get_source_quality_stats.return_value = sample_source_quality_data

        # Execute
        result = await analytics_service.get_source_quality(days=30)

        # Verify all numeric values are floats
        for source_type in result['source_types']:
            assert isinstance(source_type['avg_credibility_score'], float)
            assert isinstance(source_type['avg_num_sources'], float)
            assert isinstance(source_type['avg_diversity_score'], float)


class TestGetRiskCorrelation:
    """Test get_risk_correlation service method."""

    @pytest.mark.asyncio
    async def test_success_with_valid_params(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_risk_correlation_data
    ):
        """Test successful retrieval with valid parameters."""
        # Setup
        mock_analytics_repo.get_risk_correlation_stats.return_value = sample_risk_correlation_data

        # Execute
        result = await analytics_service.get_risk_correlation(days=30)

        # Verify
        assert len(result['risk_levels']) == 2
        assert result['risk_levels'][0]['risk_category'] == 'low'
        assert result['risk_levels'][1]['risk_category'] == 'high'
        assert 'insights' in result
        assert len(result['insights']) > 0
        mock_analytics_repo.get_risk_correlation_stats.assert_called_once_with(days=30)

    @pytest.mark.asyncio
    async def test_empty_results(
        self,
        analytics_service,
        mock_analytics_repo
    ):
        """Test handling of empty results."""
        # Setup
        mock_analytics_repo.get_risk_correlation_stats.return_value = []

        # Execute
        result = await analytics_service.get_risk_correlation(days=30)

        # Verify
        assert len(result['risk_levels']) == 0
        assert len(result['insights']) == 0

    @pytest.mark.asyncio
    async def test_invalid_days_too_low(self, analytics_service):
        """Test ValidationError when days < 1."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_risk_correlation(days=0)

        assert "Days parameter must be between 1 and 365" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_days_too_high(self, analytics_service):
        """Test ValidationError when days > 365."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_risk_correlation(days=500)

        assert "Days parameter must be between 1 and 365" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_insights_generation_high_correlation(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_risk_correlation_data
    ):
        """Test insight generation when high-risk correlates with false verdicts."""
        # Setup
        mock_analytics_repo.get_risk_correlation_stats.return_value = sample_risk_correlation_data

        # Execute
        result = await analytics_service.get_risk_correlation(days=30)

        # Verify insights
        insights = result['insights']
        assert any('high-risk claims' in insight.lower() for insight in insights)
        assert any('false' in insight.lower() for insight in insights)

    @pytest.mark.asyncio
    async def test_insights_generation_low_correlation(
        self,
        analytics_service,
        mock_analytics_repo
    ):
        """Test insight generation when correlation is weak."""
        # Setup data with weak correlation
        weak_correlation_data = [
            {
                'risk_category': 'low',
                'article_count': 30,
                'avg_credibility_score': Decimal('80.0'),
                'false_verdict_count': 8,
                'false_verdict_rate': Decimal('0.27'),
            },
            {
                'risk_category': 'high',
                'article_count': 20,
                'avg_credibility_score': Decimal('75.0'),
                'false_verdict_count': 6,
                'false_verdict_rate': Decimal('0.30'),
            },
        ]
        mock_analytics_repo.get_risk_correlation_stats.return_value = weak_correlation_data

        # Execute
        result = await analytics_service.get_risk_correlation(days=30)

        # Verify insights reflect weak correlation
        insights = result['insights']
        assert any('not strong' in insight.lower() or 'moderate' in insight.lower() 
                   for insight in insights)

    @pytest.mark.asyncio
    async def test_decimal_to_float_conversion(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_risk_correlation_data
    ):
        """Test Decimal to float conversion in response."""
        # Setup
        mock_analytics_repo.get_risk_correlation_stats.return_value = sample_risk_correlation_data

        # Execute
        result = await analytics_service.get_risk_correlation(days=30)

        # Verify all numeric values are floats
        for risk_level in result['risk_levels']:
            assert isinstance(risk_level['avg_credibility_score'], float)
            assert isinstance(risk_level['false_verdict_rate'], float)

    @pytest.mark.asyncio
    async def test_all_risk_categories_present(
        self,
        analytics_service,
        mock_analytics_repo
    ):
        """Test with all three risk categories present."""
        # Setup complete data
        complete_data = [
            {'risk_category': 'low', 'article_count': 30, 
             'avg_credibility_score': Decimal('85.0'), 'false_verdict_count': 2,
             'false_verdict_rate': Decimal('0.067')},
            {'risk_category': 'medium', 'article_count': 25,
             'avg_credibility_score': Decimal('65.0'), 'false_verdict_count': 8,
             'false_verdict_rate': Decimal('0.32')},
            {'risk_category': 'high', 'article_count': 20,
             'avg_credibility_score': Decimal('35.0'), 'false_verdict_count': 15,
             'false_verdict_rate': Decimal('0.75')},
        ]
        mock_analytics_repo.get_risk_correlation_stats.return_value = complete_data

        # Execute
        result = await analytics_service.get_risk_correlation(days=30)

        # Verify all categories present
        assert len(result['risk_levels']) == 3
        categories = [r['risk_category'] for r in result['risk_levels']]
        assert 'low' in categories
        assert 'medium' in categories
        assert 'high' in categories
