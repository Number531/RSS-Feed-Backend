"""
Unit tests for AnalyticsService.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal

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


@pytest.fixture
def sample_reliability_stats():
    """Sample source reliability statistics."""
    return [
        {
            'source_id': 'uuid-1',
            'source_name': 'Test Source',
            'category': 'technology',
            'articles_count': 10,
            'avg_score': Decimal('85.5'),
            'avg_confidence': Decimal('0.90')
        }
    ]


@pytest.fixture
def sample_temporal_trends():
    """Sample temporal trends data."""
    return [
        {
            'period': datetime.utcnow(),
            'articles_count': 5,
            'avg_score': Decimal('80.0'),
            'avg_confidence': Decimal('0.85')
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
        {'verdict': 'TRUE', 'count': 12, 'avg_score': Decimal('88.5')},
        {'verdict': 'FALSE', 'count': 5, 'avg_score': Decimal('25.0')}
    ]


class TestGetSourceReliabilityStats:
    """Test get_source_reliability_stats method."""
    
    @pytest.mark.asyncio
    async def test_success_with_valid_params(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_reliability_stats
    ):
        """Test successful retrieval with valid parameters."""
        # Setup
        mock_analytics_repo.get_source_reliability_stats.return_value = sample_reliability_stats
        
        # Execute
        result = await analytics_service.get_source_reliability_stats(days=30, min_articles=5)
        
        # Verify
        assert result == sample_reliability_stats
        mock_analytics_repo.get_source_reliability_stats.assert_called_once_with(
            days=30,
            min_articles=5
        )
    
    @pytest.mark.asyncio
    async def test_invalid_days_too_low(self, analytics_service):
        """Test ValidationError when days < 1."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_source_reliability_stats(days=0, min_articles=5)
        
        assert "Days parameter must be between 1 and 365" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_days_too_high(self, analytics_service):
        """Test ValidationError when days > 365."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_source_reliability_stats(days=366, min_articles=5)
        
        assert "Days parameter must be between 1 and 365" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_min_articles_too_low(self, analytics_service):
        """Test ValidationError when min_articles < 1."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_source_reliability_stats(days=30, min_articles=0)
        
        assert "min_articles parameter must be between 1 and 100" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_min_articles_too_high(self, analytics_service):
        """Test ValidationError when min_articles > 100."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_source_reliability_stats(days=30, min_articles=101)
        
        assert "min_articles parameter must be between 1 and 100" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_empty_results(self, analytics_service, mock_analytics_repo):
        """Test handling of empty results."""
        # Setup
        mock_analytics_repo.get_source_reliability_stats.return_value = []
        
        # Execute
        result = await analytics_service.get_source_reliability_stats(days=30, min_articles=5)
        
        # Verify
        assert result == []
        assert mock_analytics_repo.get_source_reliability_stats.called


class TestGetTemporalTrends:
    """Test get_temporal_trends method."""
    
    @pytest.mark.asyncio
    async def test_success_with_valid_params(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_temporal_trends
    ):
        """Test successful retrieval with valid parameters."""
        # Setup
        mock_analytics_repo.get_temporal_trends.return_value = sample_temporal_trends
        
        # Execute
        result = await analytics_service.get_temporal_trends(
            source_id='uuid-1',
            category='technology',
            days=30,
            granularity='daily'
        )
        
        # Verify
        assert result == sample_temporal_trends
        mock_analytics_repo.get_temporal_trends.assert_called_once_with(
            source_id='uuid-1',
            category='technology',
            days=30,
            granularity='daily'
        )
    
    @pytest.mark.asyncio
    async def test_invalid_days_too_low(self, analytics_service):
        """Test ValidationError when days < 1."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_temporal_trends(days=0)
        
        assert "Days parameter must be between 1 and 365" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_days_too_high(self, analytics_service):
        """Test ValidationError when days > 365."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_temporal_trends(days=400)
        
        assert "Days parameter must be between 1 and 365" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_granularity(self, analytics_service):
        """Test ValidationError with invalid granularity."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_temporal_trends(days=30, granularity='monthly')
        
        assert "Granularity must be one of" in str(exc_info.value)


class TestGetVerdictAnalytics:
    """Test get_verdict_analytics method."""
    
    @pytest.mark.asyncio
    async def test_success_with_valid_params(
        self,
        analytics_service,
        mock_analytics_repo
    ):
        """Test successful retrieval of verdict analytics."""
        # Setup mock data
        mock_distribution = [
            {'verdict': 'TRUE', 'count': 50, 'avg_score': Decimal('85.5')},
            {'verdict': 'FALSE', 'count': 20, 'avg_score': Decimal('25.0')},
            {'verdict': 'MISLEADING', 'count': 10, 'avg_score': Decimal('40.5')}
        ]
        
        mock_confidence = [
            {
                'verdict': 'TRUE',
                'avg_confidence': Decimal('0.890'),
                'min_confidence': Decimal('0.750'),
                'max_confidence': Decimal('0.990'),
                'count': 50
            },
            {
                'verdict': 'FALSE',
                'avg_confidence': Decimal('0.820'),
                'min_confidence': Decimal('0.700'),
                'max_confidence': Decimal('0.950'),
                'count': 20
            }
        ]
        
        mock_trends = [
            {'date': datetime.utcnow(), 'verdict': 'TRUE', 'count': 5},
            {'date': datetime.utcnow(), 'verdict': 'FALSE', 'count': 2}
        ]
        
        mock_risk = [
            {
                'verdict': 'FALSE',
                'count': 20,
                'avg_credibility': Decimal('25.0'),
                'avg_confidence': Decimal('0.820')
            }
        ]
        
        # Setup mock returns
        mock_analytics_repo.get_verdict_distribution.return_value = mock_distribution
        mock_analytics_repo.get_verdict_confidence_correlation.return_value = mock_confidence
        mock_analytics_repo.get_verdict_temporal_trends.return_value = mock_trends
        mock_analytics_repo.get_high_risk_verdicts.return_value = mock_risk
        
        # Execute
        result = await analytics_service.get_verdict_analytics(days=30)
        
        # Verify structure
        assert 'period' in result
        assert 'verdict_distribution' in result
        assert 'confidence_by_verdict' in result
        assert 'temporal_trends' in result
        assert 'risk_indicators' in result
        assert 'summary' in result
        
        # Verify distribution calculations
        assert len(result['verdict_distribution']) == 3
        assert result['verdict_distribution'][0]['verdict'] == 'TRUE'
        assert result['verdict_distribution'][0]['count'] == 50
        assert result['verdict_distribution'][0]['percentage'] == 62.5  # 50/80
        
        # Verify confidence data
        assert 'TRUE' in result['confidence_by_verdict']
        assert result['confidence_by_verdict']['TRUE']['avg_confidence'] == 0.890
        
        # Verify risk calculations
        assert result['risk_indicators']['total_risk_count'] == 20
        assert result['risk_indicators']['risk_percentage'] == 25.0  # 20/80
        assert result['risk_indicators']['overall_risk_level'] == 'high'
        
        # Verify summary
        assert result['summary']['total_verdicts'] == 80
        assert result['summary']['unique_verdict_types'] == 3
        assert result['summary']['most_common_verdict'] == 'TRUE'
    
    @pytest.mark.asyncio
    async def test_invalid_days_too_low(self, analytics_service):
        """Test ValidationError when days < 1."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_verdict_analytics(days=0)
        
        assert "Days parameter must be between 1 and 365" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_days_too_high(self, analytics_service):
        """Test ValidationError when days > 365."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_verdict_analytics(days=400)
        
        assert "Days parameter must be between 1 and 365" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_empty_distribution(self, analytics_service, mock_analytics_repo):
        """Test handling of empty verdict distribution."""
        # Setup empty mock data
        mock_analytics_repo.get_verdict_distribution.return_value = []
        mock_analytics_repo.get_verdict_confidence_correlation.return_value = []
        mock_analytics_repo.get_verdict_temporal_trends.return_value = []
        mock_analytics_repo.get_high_risk_verdicts.return_value = []
        
        # Execute
        result = await analytics_service.get_verdict_analytics(days=30)
        
        # Verify graceful handling
        assert result['summary']['total_verdicts'] == 0
        assert result['summary']['unique_verdict_types'] == 0
        assert result['summary']['most_common_verdict'] is None
        assert result['risk_indicators']['total_risk_count'] == 0
    
    @pytest.mark.asyncio
    async def test_risk_level_critical(self, analytics_service, mock_analytics_repo):
        """Test critical risk level calculation."""
        # Setup data with 50% false/misleading (critical threshold >= 40%)
        mock_distribution = [
            {'verdict': 'TRUE', 'count': 50, 'avg_score': Decimal('85.5')},
            {'verdict': 'FALSE', 'count': 50, 'avg_score': Decimal('25.0')}
        ]
        
        mock_risk = [
            {
                'verdict': 'FALSE',
                'count': 50,
                'avg_credibility': Decimal('25.0'),
                'avg_confidence': Decimal('0.820')
            }
        ]
        
        mock_analytics_repo.get_verdict_distribution.return_value = mock_distribution
        mock_analytics_repo.get_verdict_confidence_correlation.return_value = []
        mock_analytics_repo.get_verdict_temporal_trends.return_value = []
        mock_analytics_repo.get_high_risk_verdicts.return_value = mock_risk
        
        # Execute
        result = await analytics_service.get_verdict_analytics(days=30)
        
        # Verify critical risk level
        assert result['risk_indicators']['risk_percentage'] == 50.0
        assert result['risk_indicators']['overall_risk_level'] == 'critical'
    
    @pytest.mark.asyncio
    async def test_risk_level_low(self, analytics_service, mock_analytics_repo):
        """Test low risk level calculation."""
        # Setup data with <15% false/misleading (low threshold)
        mock_distribution = [
            {'verdict': 'TRUE', 'count': 90, 'avg_score': Decimal('85.5')},
            {'verdict': 'FALSE', 'count': 10, 'avg_score': Decimal('25.0')}
        ]
        
        mock_risk = [
            {
                'verdict': 'FALSE',
                'count': 10,
                'avg_credibility': Decimal('25.0'),
                'avg_confidence': Decimal('0.820')
            }
        ]
        
        mock_analytics_repo.get_verdict_distribution.return_value = mock_distribution
        mock_analytics_repo.get_verdict_confidence_correlation.return_value = []
        mock_analytics_repo.get_verdict_temporal_trends.return_value = []
        mock_analytics_repo.get_high_risk_verdicts.return_value = mock_risk
        
        # Execute
        result = await analytics_service.get_verdict_analytics(days=30)
        
        # Verify low risk level
        assert result['risk_indicators']['risk_percentage'] == 10.0
        assert result['risk_indicators']['overall_risk_level'] == 'low'
    
    @pytest.mark.asyncio
    async def test_hourly_granularity_with_too_many_days(self, analytics_service):
        """Test ValidationError when hourly granularity with days > 7."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_temporal_trends(days=8, granularity='hourly')
        
        assert "Hourly granularity is only supported for up to 7 days" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_hourly_granularity_allowed(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_temporal_trends
    ):
        """Test hourly granularity works with days <= 7."""
        # Setup
        mock_analytics_repo.get_temporal_trends.return_value = sample_temporal_trends
        
        # Execute
        result = await analytics_service.get_temporal_trends(days=7, granularity='hourly')
        
        # Verify
        assert result == sample_temporal_trends
        assert mock_analytics_repo.get_temporal_trends.called
    
    @pytest.mark.asyncio
    async def test_optional_params_none(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_temporal_trends
    ):
        """Test with None source_id and category."""
        # Setup
        mock_analytics_repo.get_temporal_trends.return_value = sample_temporal_trends
        
        # Execute
        result = await analytics_service.get_temporal_trends(
            source_id=None,
            category=None,
            days=30,
            granularity='daily'
        )
        
        # Verify
        assert result == sample_temporal_trends
        mock_analytics_repo.get_temporal_trends.assert_called_once_with(
            source_id=None,
            category=None,
            days=30,
            granularity='daily'
        )
    
    @pytest.mark.asyncio
    async def test_weekly_granularity(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_temporal_trends
    ):
        """Test weekly granularity."""
        # Setup
        mock_analytics_repo.get_temporal_trends.return_value = sample_temporal_trends
        
        # Execute
        result = await analytics_service.get_temporal_trends(days=60, granularity='weekly')
        
        # Verify
        assert result == sample_temporal_trends
        mock_analytics_repo.get_temporal_trends.assert_called_once()


class TestGetClaimsStatistics:
    """Test get_claims_statistics method."""
    
    @pytest.mark.asyncio
    async def test_success_with_verdict(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_claims_stats
    ):
        """Test successful retrieval with verdict filter."""
        # Setup
        mock_analytics_repo.get_claims_statistics.return_value = sample_claims_stats
        
        # Execute
        result = await analytics_service.get_claims_statistics(verdict='TRUE', days=30)
        
        # Verify
        assert result == sample_claims_stats
        mock_analytics_repo.get_claims_statistics.assert_called_once_with(
            verdict='TRUE',
            days=30
        )
    
    @pytest.mark.asyncio
    async def test_invalid_days_too_low(self, analytics_service):
        """Test ValidationError when days < 1."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_claims_statistics(days=0)
        
        assert "Days parameter must be between 1 and 365" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_days_too_high(self, analytics_service):
        """Test ValidationError when days > 365."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_claims_statistics(days=366)
        
        assert "Days parameter must be between 1 and 365" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_verdict(self, analytics_service):
        """Test ValidationError with invalid verdict."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_claims_statistics(verdict='INVALID_VERDICT', days=30)
        
        assert "Verdict must be one of" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_empty_results_handling(self, analytics_service, mock_analytics_repo):
        """Test handling of empty results returns default structure."""
        # Setup
        mock_analytics_repo.get_claims_statistics.return_value = {}
        
        # Execute
        result = await analytics_service.get_claims_statistics(days=30)
        
        # Verify default structure
        assert result['total_fact_checks'] == 0
        assert result['total_claims'] == 0
        assert result['claims_true'] == 0
        assert result['claims_false'] == 0
        assert result['claims_misleading'] == 0
        assert result['claims_unverified'] == 0
        assert result['avg_credibility'] is None
        assert result['avg_confidence'] is None
    
    @pytest.mark.asyncio
    async def test_valid_verdict_true(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_claims_stats
    ):
        """Test with verdict='TRUE'."""
        # Setup
        mock_analytics_repo.get_claims_statistics.return_value = sample_claims_stats
        
        # Execute
        result = await analytics_service.get_claims_statistics(verdict='TRUE', days=30)
        
        # Verify
        assert result == sample_claims_stats
        mock_analytics_repo.get_claims_statistics.assert_called_once_with(
            verdict='TRUE',
            days=30
        )
    
    @pytest.mark.asyncio
    async def test_valid_verdict_lowercase_converted(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_claims_stats
    ):
        """Test verdict is converted to uppercase."""
        # Setup
        mock_analytics_repo.get_claims_statistics.return_value = sample_claims_stats
        
        # Execute
        result = await analytics_service.get_claims_statistics(verdict='false', days=30)
        
        # Verify verdict was uppercased
        mock_analytics_repo.get_claims_statistics.assert_called_once_with(
            verdict='FALSE',
            days=30
        )
    
    @pytest.mark.asyncio
    async def test_verdict_mostly_true(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_claims_stats
    ):
        """Test with verdict='MOSTLY_TRUE'."""
        # Setup
        mock_analytics_repo.get_claims_statistics.return_value = sample_claims_stats
        
        # Execute
        result = await analytics_service.get_claims_statistics(verdict='MOSTLY_TRUE', days=30)
        
        # Verify
        mock_analytics_repo.get_claims_statistics.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verdict_misleading(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_claims_stats
    ):
        """Test with verdict='MISLEADING'."""
        # Setup
        mock_analytics_repo.get_claims_statistics.return_value = sample_claims_stats
        
        # Execute
        result = await analytics_service.get_claims_statistics(verdict='MISLEADING', days=30)
        
        # Verify
        assert result == sample_claims_stats
    
    @pytest.mark.asyncio
    async def test_none_verdict(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_claims_stats
    ):
        """Test with verdict=None (all verdicts)."""
        # Setup
        mock_analytics_repo.get_claims_statistics.return_value = sample_claims_stats
        
        # Execute
        result = await analytics_service.get_claims_statistics(verdict=None, days=30)
        
        # Verify None was passed through
        mock_analytics_repo.get_claims_statistics.assert_called_once_with(
            verdict=None,
            days=30
        )


class TestGetVerdictDistribution:
    """Test get_verdict_distribution method."""
    
    @pytest.mark.asyncio
    async def test_success(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_verdict_distribution
    ):
        """Test successful retrieval."""
        # Setup
        mock_analytics_repo.get_verdict_distribution.return_value = sample_verdict_distribution
        
        # Execute
        result = await analytics_service.get_verdict_distribution(days=30)
        
        # Verify
        assert result == sample_verdict_distribution
        mock_analytics_repo.get_verdict_distribution.assert_called_once_with(days=30)
    
    @pytest.mark.asyncio
    async def test_invalid_days_too_low(self, analytics_service):
        """Test ValidationError when days < 1."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_verdict_distribution(days=0)
        
        assert "Days parameter must be between 1 and 365" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_days_too_high(self, analytics_service):
        """Test ValidationError when days > 365."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_verdict_distribution(days=500)
        
        assert "Days parameter must be between 1 and 365" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_repository_call(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_verdict_distribution
    ):
        """Test repository is called with correct parameters."""
        # Setup
        mock_analytics_repo.get_verdict_distribution.return_value = sample_verdict_distribution
        
        # Execute
        await analytics_service.get_verdict_distribution(days=60)
        
        # Verify
        mock_analytics_repo.get_verdict_distribution.assert_called_once_with(days=60)
    
    @pytest.mark.asyncio
    async def test_return_value_unchanged(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_verdict_distribution
    ):
        """Test service returns repository result unchanged."""
        # Setup
        mock_analytics_repo.get_verdict_distribution.return_value = sample_verdict_distribution
        
        # Execute
        result = await analytics_service.get_verdict_distribution(days=30)
        
        # Verify result matches exactly
        assert result == sample_verdict_distribution
        assert len(result) == 2
        assert result[0]['verdict'] == 'TRUE'


class TestGetAnalyticsSummary:
    """Test get_analytics_summary method."""
    
    @pytest.mark.asyncio
    async def test_success(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_reliability_stats,
        sample_claims_stats,
        sample_verdict_distribution
    ):
        """Test successful summary generation."""
        # Setup
        mock_analytics_repo.get_source_reliability_stats.return_value = sample_reliability_stats
        mock_analytics_repo.get_claims_statistics.return_value = sample_claims_stats
        mock_analytics_repo.get_verdict_distribution.return_value = sample_verdict_distribution
        
        # Execute
        result = await analytics_service.get_analytics_summary(days=30)
        
        # Verify structure
        assert 'period_days' in result
        assert result['period_days'] == 30
        assert 'generated_at' in result
        assert 'source_reliability' in result
        assert 'claims_statistics' in result
        assert 'verdict_distribution' in result
        assert 'summary_metrics' in result
        
        # Verify data
        assert result['source_reliability'] == sample_reliability_stats
        assert result['claims_statistics'] == sample_claims_stats
        assert result['verdict_distribution'] == sample_verdict_distribution
    
    @pytest.mark.asyncio
    async def test_invalid_days(self, analytics_service):
        """Test ValidationError with invalid days."""
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_analytics_summary(days=0)
        
        assert "Days parameter must be between 1 and 365" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_summary_metrics(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_reliability_stats,
        sample_claims_stats,
        sample_verdict_distribution
    ):
        """Test summary metrics are correctly calculated."""
        # Setup
        mock_analytics_repo.get_source_reliability_stats.return_value = sample_reliability_stats
        mock_analytics_repo.get_claims_statistics.return_value = sample_claims_stats
        mock_analytics_repo.get_verdict_distribution.return_value = sample_verdict_distribution
        
        # Execute
        result = await analytics_service.get_analytics_summary(days=30)
        
        # Verify summary metrics
        metrics = result['summary_metrics']
        assert metrics['total_sources_analyzed'] == 1  # len(sample_reliability_stats)
        assert metrics['total_fact_checks'] == 25  # from sample_claims_stats
        assert metrics['avg_credibility_score'] == Decimal('78.5')
        assert metrics['avg_confidence'] == Decimal('0.87')
    
    @pytest.mark.asyncio
    async def test_concurrent_execution(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_reliability_stats,
        sample_claims_stats,
        sample_verdict_distribution
    ):
        """Test that methods are called concurrently via asyncio.gather."""
        # Setup
        mock_analytics_repo.get_source_reliability_stats.return_value = sample_reliability_stats
        mock_analytics_repo.get_claims_statistics.return_value = sample_claims_stats
        mock_analytics_repo.get_verdict_distribution.return_value = sample_verdict_distribution
        
        # Execute
        result = await analytics_service.get_analytics_summary(days=30)
        
        # Verify all three methods were called
        assert mock_analytics_repo.get_source_reliability_stats.called
        assert mock_analytics_repo.get_claims_statistics.called
        assert mock_analytics_repo.get_verdict_distribution.called
        
        # Result should contain data from all three
        assert 'source_reliability' in result
        assert 'claims_statistics' in result
        assert 'verdict_distribution' in result


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_repository_error_propagation(self, analytics_service, mock_analytics_repo):
        """Test that repository errors are propagated."""
        # Setup
        mock_analytics_repo.get_source_reliability_stats.side_effect = Exception("Database error")
        
        # Execute & Verify
        with pytest.raises(Exception) as exc_info:
            await analytics_service.get_source_reliability_stats(days=30, min_articles=5)
        
        assert "Database error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_multiple_validation_errors_days_first(self, analytics_service):
        """Test that days validation happens before min_articles."""
        # Days validation should fail first
        with pytest.raises(ValidationError) as exc_info:
            await analytics_service.get_source_reliability_stats(days=0, min_articles=0)
        
        assert "Days parameter must be between 1 and 365" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_trends_error_propagation(self, analytics_service, mock_analytics_repo):
        """Test error propagation in get_temporal_trends."""
        # Setup
        mock_analytics_repo.get_temporal_trends.side_effect = Exception("Query failed")
        
        # Execute & Verify
        with pytest.raises(Exception) as exc_info:
            await analytics_service.get_temporal_trends(days=30, granularity='daily')
        
        assert "Query failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_claims_error_propagation(self, analytics_service, mock_analytics_repo):
        """Test error propagation in get_claims_statistics."""
        # Setup
        mock_analytics_repo.get_claims_statistics.side_effect = RuntimeError("Connection lost")
        
        # Execute & Verify
        with pytest.raises(RuntimeError) as exc_info:
            await analytics_service.get_claims_statistics(days=30)
        
        assert "Connection lost" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_verdict_distribution_error(self, analytics_service, mock_analytics_repo):
        """Test error handling in get_verdict_distribution."""
        # Setup
        mock_analytics_repo.get_verdict_distribution.side_effect = ValueError("Invalid data")
        
        # Execute & Verify
        with pytest.raises(ValueError) as exc_info:
            await analytics_service.get_verdict_distribution(days=30)
        
        assert "Invalid data" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_summary_partial_failure(
        self,
        analytics_service,
        mock_analytics_repo,
        sample_reliability_stats
    ):
        """Test summary method when one sub-method fails."""
        # Setup - make one method fail
        mock_analytics_repo.get_source_reliability_stats.return_value = sample_reliability_stats
        mock_analytics_repo.get_claims_statistics.side_effect = Exception("Stats failed")
        mock_analytics_repo.get_verdict_distribution.return_value = []
        
        # Execute & Verify - should propagate the error
        with pytest.raises(Exception) as exc_info:
            await analytics_service.get_analytics_summary(days=30)
        
        assert "Stats failed" in str(exc_info.value)
