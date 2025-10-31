"""
Unit tests for AnalyticsRepository.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

from app.repositories.analytics_repository import AnalyticsRepository


@pytest.fixture
def mock_db_session():
    """Mock AsyncSession."""
    return AsyncMock()


@pytest.fixture
def analytics_repo(mock_db_session):
    """AnalyticsRepository with mocked session."""
    return AnalyticsRepository(mock_db_session)


@pytest.fixture
def sample_source_stats():
    """Sample source reliability statistics."""
    return [
        {
            'source_id': 'uuid-1',
            'source_name': 'Test Source 1',
            'category': 'technology',
            'articles_count': 10,
            'avg_score': Decimal('85.5'),
            'avg_confidence': Decimal('0.92'),
            'true_count': 6,
            'false_count': 1,
            'mixed_count': 2,
            'mostly_true_count': 1,
            'mostly_false_count': 0,
            'misleading_count': 0,
            'unverified_count': 0,
            'total_claims': 50,
            'total_claims_true': 35,
            'total_claims_false': 5
        },
        {
            'source_id': 'uuid-2',
            'source_name': 'Test Source 2',
            'category': 'politics',
            'articles_count': 8,
            'avg_score': Decimal('72.3'),
            'avg_confidence': Decimal('0.85'),
            'true_count': 4,
            'false_count': 2,
            'mixed_count': 2,
            'mostly_true_count': 0,
            'mostly_false_count': 0,
            'misleading_count': 0,
            'unverified_count': 0,
            'total_claims': 40,
            'total_claims_true': 25,
            'total_claims_false': 10
        }
    ]


@pytest.fixture
def sample_temporal_trends():
    """Sample temporal trend data."""
    now = datetime.utcnow()
    return [
        {
            'period': now - timedelta(days=2),
            'articles_count': 5,
            'avg_score': Decimal('80.0'),
            'avg_confidence': Decimal('0.88'),
            'true_count': 3,
            'false_count': 1
        },
        {
            'period': now - timedelta(days=1),
            'articles_count': 7,
            'avg_score': Decimal('75.5'),
            'avg_confidence': Decimal('0.85'),
            'true_count': 4,
            'false_count': 2
        },
        {
            'period': now,
            'articles_count': 6,
            'avg_score': Decimal('82.0'),
            'avg_confidence': Decimal('0.90'),
            'true_count': 5,
            'false_count': 1
        }
    ]


@pytest.fixture
def sample_claims_stats():
    """Sample claims statistics."""
    return {
        'total_fact_checks': 25,
        'total_claims': 150,
        'claims_true': 90,
        'claims_false': 30,
        'claims_misleading': 20,
        'claims_unverified': 10,
        'avg_credibility': Decimal('78.5'),
        'avg_confidence': Decimal('0.87')
    }


@pytest.fixture
def sample_verdict_distribution():
    """Sample verdict distribution data."""
    return [
        {
            'verdict': 'TRUE',
            'count': 12,
            'avg_score': Decimal('88.5')
        },
        {
            'verdict': 'MOSTLY_TRUE',
            'count': 8,
            'avg_score': Decimal('75.0')
        },
        {
            'verdict': 'MIXED',
            'count': 5,
            'avg_score': Decimal('60.0')
        },
        {
            'verdict': 'MOSTLY_FALSE',
            'count': 3,
            'avg_score': Decimal('35.0')
        },
        {
            'verdict': 'FALSE',
            'count': 2,
            'avg_score': Decimal('15.0')
        }
    ]


def create_mock_mapping(data_dict):
    """Create a mock object that behaves like a dict mapping."""
    mock = MagicMock()
    # Make it subscriptable like a dict
    mock.__getitem__ = lambda self, key: data_dict[key]
    mock.__contains__ = lambda self, key: key in data_dict
    mock.keys = lambda: data_dict.keys()
    mock.values = lambda: data_dict.values()
    mock.items = lambda: data_dict.items()
    # Make dict() constructor work
    mock.__iter__ = lambda self: iter(data_dict.keys())
    return mock


class TestAnalyticsRepositorySourceReliability:
    """Test source reliability statistics queries."""
    
    @pytest.mark.asyncio
    async def test_get_source_reliability_stats_success(
        self,
        analytics_repo,
        mock_db_session,
        sample_source_stats
    ):
        """Test getting source reliability stats with data."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [create_mock_mapping(stat) for stat in sample_source_stats]
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        results = await analytics_repo.get_source_reliability_stats(days=30, min_articles=5)
        
        # Verify
        assert len(results) == 2
        assert results[0]['source_name'] == 'Test Source 1'
        assert results[0]['articles_count'] == 10
        assert results[1]['source_name'] == 'Test Source 2'
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_source_reliability_stats_empty(
        self,
        analytics_repo,
        mock_db_session
    ):
        """Test getting source reliability stats with no data."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = []
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        results = await analytics_repo.get_source_reliability_stats(days=30, min_articles=5)
        
        # Verify
        assert results == []
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_source_reliability_stats_custom_params(
        self,
        analytics_repo,
        mock_db_session,
        sample_source_stats
    ):
        """Test getting source reliability stats with custom parameters."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [create_mock_mapping(sample_source_stats[0])]
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        results = await analytics_repo.get_source_reliability_stats(days=7, min_articles=10)
        
        # Verify
        assert len(results) == 1
        assert results[0]['articles_count'] == 10
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_source_reliability_stats_fields(
        self,
        analytics_repo,
        mock_db_session,
        sample_source_stats
    ):
        """Test that all expected fields are present in results."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [create_mock_mapping(sample_source_stats[0])]
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        results = await analytics_repo.get_source_reliability_stats()
        
        # Verify
        result = results[0]
        assert 'source_id' in result
        assert 'source_name' in result
        assert 'category' in result
        assert 'articles_count' in result
        assert 'avg_score' in result
        assert 'avg_confidence' in result
        assert 'true_count' in result
        assert 'false_count' in result
        assert 'mixed_count' in result
        assert 'total_claims' in result
        assert 'total_claims_true' in result
        assert 'total_claims_false' in result


class TestAnalyticsRepositoryTemporalTrends:
    """Test temporal trends queries."""
    
    @pytest.mark.asyncio
    async def test_get_temporal_trends_success(
        self,
        analytics_repo,
        mock_db_session,
        sample_temporal_trends
    ):
        """Test getting temporal trends with data."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [create_mock_mapping(trend) for trend in sample_temporal_trends]
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        results = await analytics_repo.get_temporal_trends(days=30, granularity='daily')
        
        # Verify
        assert len(results) == 3
        assert results[0]['articles_count'] == 5
        assert results[1]['articles_count'] == 7
        assert results[2]['articles_count'] == 6
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_temporal_trends_empty(
        self,
        analytics_repo,
        mock_db_session
    ):
        """Test getting temporal trends with no data."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = []
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        results = await analytics_repo.get_temporal_trends(days=30)
        
        # Verify
        assert results == []
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_temporal_trends_with_source_filter(
        self,
        analytics_repo,
        mock_db_session,
        sample_temporal_trends
    ):
        """Test getting temporal trends filtered by source."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [create_mock_mapping(sample_temporal_trends[0])]
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        results = await analytics_repo.get_temporal_trends(
            source_id='uuid-1',
            days=30,
            granularity='daily'
        )
        
        # Verify
        assert len(results) == 1
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_temporal_trends_with_category_filter(
        self,
        analytics_repo,
        mock_db_session,
        sample_temporal_trends
    ):
        """Test getting temporal trends filtered by category."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [create_mock_mapping(trend) for trend in sample_temporal_trends[:2]]
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        results = await analytics_repo.get_temporal_trends(
            category='technology',
            days=30,
            granularity='daily'
        )
        
        # Verify
        assert len(results) == 2
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_temporal_trends_hourly_granularity(
        self,
        analytics_repo,
        mock_db_session,
        sample_temporal_trends
    ):
        """Test getting temporal trends with hourly granularity."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [create_mock_mapping(trend) for trend in sample_temporal_trends]
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        results = await analytics_repo.get_temporal_trends(days=7, granularity='hourly')
        
        # Verify
        assert len(results) == 3
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_temporal_trends_weekly_granularity(
        self,
        analytics_repo,
        mock_db_session,
        sample_temporal_trends
    ):
        """Test getting temporal trends with weekly granularity."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [create_mock_mapping(sample_temporal_trends[0])]
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        results = await analytics_repo.get_temporal_trends(days=60, granularity='weekly')
        
        # Verify
        assert len(results) == 1
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_temporal_trends_fields(
        self,
        analytics_repo,
        mock_db_session,
        sample_temporal_trends
    ):
        """Test that all expected fields are present in results."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [create_mock_mapping(sample_temporal_trends[0])]
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        results = await analytics_repo.get_temporal_trends()
        
        # Verify
        result = results[0]
        assert 'period' in result
        assert 'articles_count' in result
        assert 'avg_score' in result
        assert 'avg_confidence' in result
        assert 'true_count' in result
        assert 'false_count' in result


class TestAnalyticsRepositoryClaimsStatistics:
    """Test claims statistics queries."""
    
    @pytest.mark.asyncio
    async def test_get_claims_statistics_success(
        self,
        analytics_repo,
        mock_db_session,
        sample_claims_stats
    ):
        """Test getting claims statistics with data."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.first.return_value = create_mock_mapping(sample_claims_stats)
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await analytics_repo.get_claims_statistics(days=30)
        
        # Verify
        assert result['total_fact_checks'] == 25
        assert result['total_claims'] == 150
        assert result['claims_true'] == 90
        assert result['claims_false'] == 30
        assert result['claims_misleading'] == 20
        assert result['claims_unverified'] == 10
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_claims_statistics_empty(
        self,
        analytics_repo,
        mock_db_session
    ):
        """Test getting claims statistics with no data."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.first.return_value = None
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await analytics_repo.get_claims_statistics(days=30)
        
        # Verify
        assert result == {}
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_claims_statistics_with_verdict_filter(
        self,
        analytics_repo,
        mock_db_session,
        sample_claims_stats
    ):
        """Test getting claims statistics filtered by verdict."""
        # Setup
        filtered_stats = sample_claims_stats.copy()
        filtered_stats['total_fact_checks'] = 12
        
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.first.return_value = create_mock_mapping(filtered_stats)
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await analytics_repo.get_claims_statistics(verdict='TRUE', days=30)
        
        # Verify
        assert result['total_fact_checks'] == 12
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_claims_statistics_custom_days(
        self,
        analytics_repo,
        mock_db_session,
        sample_claims_stats
    ):
        """Test getting claims statistics with custom days parameter."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.first.return_value = create_mock_mapping(sample_claims_stats)
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await analytics_repo.get_claims_statistics(days=7)
        
        # Verify
        assert result['total_fact_checks'] == 25
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_claims_statistics_fields(
        self,
        analytics_repo,
        mock_db_session,
        sample_claims_stats
    ):
        """Test that all expected fields are present in results."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.first.return_value = create_mock_mapping(sample_claims_stats)
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await analytics_repo.get_claims_statistics()
        
        # Verify
        assert 'total_fact_checks' in result
        assert 'total_claims' in result
        assert 'claims_true' in result
        assert 'claims_false' in result
        assert 'claims_misleading' in result
        assert 'claims_unverified' in result
        assert 'avg_credibility' in result
        assert 'avg_confidence' in result


class TestAnalyticsRepositoryVerdictDistribution:
    """Test verdict distribution queries."""
    
    @pytest.mark.asyncio
    async def test_get_verdict_distribution_success(
        self,
        analytics_repo,
        mock_db_session,
        sample_verdict_distribution
    ):
        """Test getting verdict distribution with data."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [create_mock_mapping(verdict) for verdict in sample_verdict_distribution]
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        results = await analytics_repo.get_verdict_distribution(days=30)
        
        # Verify
        assert len(results) == 5
        assert results[0]['verdict'] == 'TRUE'
        assert results[0]['count'] == 12
        assert results[1]['verdict'] == 'MOSTLY_TRUE'
        assert results[1]['count'] == 8
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_verdict_distribution_empty(
        self,
        analytics_repo,
        mock_db_session
    ):
        """Test getting verdict distribution with no data."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = []
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        results = await analytics_repo.get_verdict_distribution(days=30)
        
        # Verify
        assert results == []
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_verdict_distribution_custom_days(
        self,
        analytics_repo,
        mock_db_session,
        sample_verdict_distribution
    ):
        """Test getting verdict distribution with custom days parameter."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [create_mock_mapping(verdict) for verdict in sample_verdict_distribution[:3]]
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        results = await analytics_repo.get_verdict_distribution(days=7)
        
        # Verify
        assert len(results) == 3
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_verdict_distribution_fields(
        self,
        analytics_repo,
        mock_db_session,
        sample_verdict_distribution
    ):
        """Test that all expected fields are present in results."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [create_mock_mapping(sample_verdict_distribution[0])]
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        results = await analytics_repo.get_verdict_distribution()
        
        # Verify
        result = results[0]
        assert 'verdict' in result
        assert 'count' in result
        assert 'avg_score' in result
    
    @pytest.mark.asyncio
    async def test_get_verdict_distribution_ordering(
        self,
        analytics_repo,
        mock_db_session,
        sample_verdict_distribution
    ):
        """Test that verdict distribution results are ordered by count."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [create_mock_mapping(verdict) for verdict in sample_verdict_distribution]
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        results = await analytics_repo.get_verdict_distribution(days=30)
        
        # Verify ordering (descending by count)
        assert results[0]['count'] >= results[1]['count']
        assert results[1]['count'] >= results[2]['count']
        assert results[2]['count'] >= results[3]['count']
        assert results[3]['count'] >= results[4]['count']


class TestAnalyticsRepositoryEdgeCases:
    """Test edge cases and error scenarios."""
    
    @pytest.mark.asyncio
    async def test_get_source_reliability_stats_zero_days(
        self,
        analytics_repo,
        mock_db_session
    ):
        """Test that zero days parameter is handled."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = []
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        results = await analytics_repo.get_source_reliability_stats(days=0, min_articles=1)
        
        # Verify - should still execute without error
        assert results == []
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_temporal_trends_invalid_granularity_defaults_to_daily(
        self,
        analytics_repo,
        mock_db_session,
        sample_temporal_trends
    ):
        """Test that invalid granularity defaults to daily."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [create_mock_mapping(trend) for trend in sample_temporal_trends]
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute with invalid granularity
        results = await analytics_repo.get_temporal_trends(
            days=30,
            granularity='invalid_granularity'
        )
        
        # Verify - should execute with daily as fallback
        assert len(results) == 3
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_claims_statistics_none_verdict_filter(
        self,
        analytics_repo,
        mock_db_session,
        sample_claims_stats
    ):
        """Test getting claims statistics with None verdict (no filter)."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.first.return_value = create_mock_mapping(sample_claims_stats)
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await analytics_repo.get_claims_statistics(verdict=None, days=30)
        
        # Verify
        assert result['total_fact_checks'] == 25
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_database_session_called_correctly(
        self,
        analytics_repo,
        mock_db_session
    ):
        """Test that database session execute is called with proper query."""
        # Setup
        mock_result = MagicMock()
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = []
        mock_result.mappings.return_value = mock_mappings
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        await analytics_repo.get_source_reliability_stats()
        
        # Verify that execute was called exactly once
        assert mock_db_session.execute.call_count == 1
        
        # Verify execute was called with a query object (not None)
        call_args = mock_db_session.execute.call_args
        assert call_args is not None
        assert len(call_args[0]) > 0  # Has positional arguments (the query)
