"""
Unit tests for analytics endpoints.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from decimal import Decimal

from app.api.v1.endpoints.analytics import (
    get_source_reliability,
    get_fact_check_trends,
    get_claims_analytics
)
from app.core.exceptions import ValidationError


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def sample_source_stats():
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
def sample_trends():
    """Sample trends data."""
    from datetime import datetime
    return [
        {
            'period': datetime.utcnow(),
            'articles_count': 5,
            'avg_score': Decimal('80.0'),
            'avg_confidence': Decimal('0.85'),
            'true_count': 3,
            'false_count': 2
        }
    ]


@pytest.fixture
def sample_claims():
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
def sample_verdict_dist():
    """Sample verdict distribution."""
    return [
        {'verdict': 'TRUE', 'count': 12, 'avg_score': Decimal('88.5')},
        {'verdict': 'FALSE', 'count': 5, 'avg_score': Decimal('25.0')}
    ]


class TestGetSourceReliability:
    """Test GET /analytics/sources endpoint."""
    
    @pytest.mark.asyncio
    async def test_success(self, mock_db, sample_source_stats):
        """Test successful retrieval."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_source_reliability_stats = AsyncMock(return_value=sample_source_stats)
            
            result = await get_source_reliability(days=30, min_articles=5, db=mock_db)
            
            assert 'sources' in result
            assert result['sources'] == sample_source_stats
            assert result['total_sources'] == 1
            assert result['period']['days'] == 30
            assert result['criteria']['min_articles'] == 5
    
    @pytest.mark.asyncio
    async def test_validation_error(self, mock_db):
        """Test ValidationError handling."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_source_reliability_stats = AsyncMock(
                side_effect=ValidationError("Invalid days")
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await get_source_reliability(days=30, min_articles=5, db=mock_db)
            
            assert exc_info.value.status_code == 400
            assert "Invalid days" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_server_error(self, mock_db):
        """Test server error handling."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_source_reliability_stats = AsyncMock(
                side_effect=Exception("Database error")
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await get_source_reliability(days=30, min_articles=5, db=mock_db)
            
            assert exc_info.value.status_code == 500
            assert "Failed to retrieve source reliability" in str(exc_info.value.detail)


class TestGetFactCheckTrends:
    """Test GET /analytics/trends endpoint."""
    
    @pytest.mark.asyncio
    async def test_success(self, mock_db, sample_trends):
        """Test successful retrieval."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_temporal_trends = AsyncMock(return_value=sample_trends)
            
            result = await get_fact_check_trends(
                days=30,
                granularity='daily',
                source_id=None,
                category=None,
                db=mock_db
            )
            
            assert 'time_series' in result
            assert 'granularity' in result
            assert result['granularity'] == 'daily'
            assert len(result['time_series']) == 1
            assert result['summary']['total_periods'] == 1
    
    @pytest.mark.asyncio
    async def test_with_filters(self, mock_db, sample_trends):
        """Test with source and category filters."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_temporal_trends = AsyncMock(return_value=sample_trends)
            
            result = await get_fact_check_trends(
                days=7,
                granularity='hourly',
                source_id='uuid-1',
                category='technology',
                db=mock_db
            )
            
            assert result['filters']['source_id'] == 'uuid-1'
            assert result['filters']['category'] == 'technology'
            assert result['filters']['days'] == 7
    
    @pytest.mark.asyncio
    async def test_empty_results(self, mock_db):
        """Test with empty results."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_temporal_trends = AsyncMock(return_value=[])
            
            result = await get_fact_check_trends(
                days=30,
                granularity='daily',
                source_id=None,
                category=None,
                db=mock_db
            )
            
            assert result['time_series'] == []
            assert result['summary']['total_periods'] == 0
            assert result['summary']['overall_avg_score'] == 0.0
    
    @pytest.mark.asyncio
    async def test_validation_error(self, mock_db):
        """Test ValidationError handling."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_temporal_trends = AsyncMock(
                side_effect=ValidationError("Hourly granularity is only supported for up to 7 days")
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await get_fact_check_trends(
                    days=30,
                    granularity='hourly',
                    source_id=None,
                    category=None,
                    db=mock_db
                )
            
            assert exc_info.value.status_code == 400


class TestGetClaimsAnalytics:
    """Test GET /analytics/claims endpoint."""
    
    @pytest.mark.asyncio
    async def test_success(self, mock_db, sample_claims, sample_verdict_dist):
        """Test successful retrieval."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_claims_statistics = AsyncMock(return_value=sample_claims)
            mock_service.get_verdict_distribution = AsyncMock(return_value=sample_verdict_dist)
            
            result = await get_claims_analytics(days=30, verdict=None, db=mock_db)
            
            assert result['period_days'] == 30
            assert result['total_fact_checks'] == 25
            assert 'claims_summary' in result
            assert result['claims_summary']['total_claims'] == 150
            assert result['claims_summary']['accuracy_rate'] == 60.0
            assert len(result['verdict_distribution']) == 2
            assert 'quality_metrics' in result
    
    @pytest.mark.asyncio
    async def test_with_verdict_filter(self, mock_db, sample_claims, sample_verdict_dist):
        """Test with verdict filter."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_claims_statistics = AsyncMock(return_value=sample_claims)
            mock_service.get_verdict_distribution = AsyncMock(return_value=sample_verdict_dist)
            
            result = await get_claims_analytics(days=30, verdict='TRUE', db=mock_db)
            
            assert result['total_fact_checks'] == 25
            mock_service.get_claims_statistics.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_empty_claims(self, mock_db, sample_verdict_dist):
        """Test with no claims."""
        empty_claims = {
            'total_fact_checks': 0,
            'total_claims': 0,
            'claims_true': 0,
            'claims_false': 0,
            'claims_misleading': 0,
            'claims_unverified': 0,
            'avg_credibility': None,
            'avg_confidence': None
        }
        
        with patch('app.api.v1.endpoints.analytics.AnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_claims_statistics = AsyncMock(return_value=empty_claims)
            mock_service.get_verdict_distribution = AsyncMock(return_value=[])
            
            result = await get_claims_analytics(days=30, verdict=None, db=mock_db)
            
            assert result['total_fact_checks'] == 0
            assert result['claims_summary']['total_claims'] == 0
            assert result['claims_summary']['accuracy_rate'] == 0.0
            assert result['verdict_distribution'] == []
    
    @pytest.mark.asyncio
    async def test_validation_error(self, mock_db):
        """Test ValidationError handling."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_claims_statistics = AsyncMock(
                side_effect=ValidationError("Invalid verdict")
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await get_claims_analytics(days=30, verdict='INVALID', db=mock_db)
            
            assert exc_info.value.status_code == 400
            assert "Invalid verdict" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_server_error(self, mock_db):
        """Test server error handling."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_claims_statistics = AsyncMock(
                side_effect=Exception("Database connection failed")
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await get_claims_analytics(days=30, verdict=None, db=mock_db)
            
            assert exc_info.value.status_code == 500
            assert "Failed to retrieve claims analytics" in str(exc_info.value.detail)
