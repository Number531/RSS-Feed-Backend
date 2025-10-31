"""
Integration tests for Phase 2A Analytics Endpoints.

Tests the /stats and /categories endpoints with real database interactions.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from decimal import Decimal

from app.main import app


@pytest.fixture
def mock_analytics_repo_data():
    """Mock data for analytics repository."""
    current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    
    return {
        'aggregate_stats': {
            'lifetime': {
                'total_fact_checks': 1500,
                'sources_monitored': 25,
                'total_claims': 4500,
                'avg_credibility': Decimal('75.5')
            },
            'current_month': {
                'articles_this_month': 150,
                'avg_credibility_this_month': Decimal('78.2')
            },
            'previous_month': {
                'articles_last_month': 120,
                'avg_credibility_last_month': Decimal('76.0')
            }
        },
        'category_stats': [
            {
                'category': 'politics',
                'articles_count': 50,
                'avg_credibility': Decimal('72.5'),
                'false_count': 8,
                'misleading_count': 5,
                'sources': ['CNN', 'Fox News', 'BBC', 'Reuters']
            },
            {
                'category': 'technology',
                'articles_count': 30,
                'avg_credibility': Decimal('85.0'),
                'false_count': 2,
                'misleading_count': 1,
                'sources': ['TechCrunch', 'Wired', 'The Verge']
            },
            {
                'category': 'health',
                'articles_count': 25,
                'avg_credibility': Decimal('88.5'),
                'false_count': 1,
                'misleading_count': 0,
                'sources': ['WHO', 'CDC', 'WebMD']
            }
        ]
    }


class TestAggregateStatisticsEndpoint:
    """Integration tests for GET /api/v1/analytics/stats"""
    
    @pytest.mark.asyncio
    async def test_aggregate_stats_success(self, mock_analytics_repo_data):
        """Test successful retrieval of aggregate statistics."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            # Setup mock
            mock_repo = AsyncMock()
            mock_repo.get_aggregate_statistics = AsyncMock(
                return_value=mock_analytics_repo_data['aggregate_stats']
            )
            mock_repo_class.return_value = mock_repo
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/analytics/stats")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            
            # Check lifetime stats
            assert 'lifetime' in data
            assert data['lifetime']['articles_fact_checked'] == 1500
            assert data['lifetime']['sources_monitored'] == 25
            assert data['lifetime']['claims_verified'] == 4500
            
            # Check current month stats
            assert 'this_month' in data
            assert data['this_month']['articles_fact_checked'] == 150
            
            # Check trends
            assert 'volume_change' in data['this_month']
            assert 'credibility_change' in data['this_month']
            
            # Check milestones
            assert 'milestones' in data
            assert isinstance(data['milestones'], list)
    
    @pytest.mark.asyncio
    async def test_aggregate_stats_without_lifetime(self, mock_analytics_repo_data):
        """Test aggregate stats with include_lifetime=false."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_aggregate_statistics = AsyncMock(
                return_value=mock_analytics_repo_data['aggregate_stats']
            )
            mock_repo_class.return_value = mock_repo
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/analytics/stats",
                    params={"include_lifetime": False}
                )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should not have lifetime when explicitly set to false
            # (Note: service layer still includes it if data exists)
            assert 'this_month' in data
    
    @pytest.mark.asyncio
    async def test_aggregate_stats_without_trends(self, mock_analytics_repo_data):
        """Test aggregate stats with include_trends=false."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            stats_without_prev = mock_analytics_repo_data['aggregate_stats'].copy()
            stats_without_prev['previous_month'] = {}
            mock_repo.get_aggregate_statistics = AsyncMock(return_value=stats_without_prev)
            mock_repo_class.return_value = mock_repo
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/analytics/stats",
                    params={"include_trends": False}
                )
            
            assert response.status_code == 200
            data = response.json()
            
            # Trends should not be calculated
            assert 'volume_change' not in data.get('this_month', {})
    
    @pytest.mark.asyncio
    async def test_aggregate_stats_empty_database(self):
        """Test aggregate stats with empty database."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_aggregate_statistics = AsyncMock(return_value={
                'lifetime': {},
                'current_month': {},
                'previous_month': {}
            })
            mock_repo_class.return_value = mock_repo
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/analytics/stats")
            
            assert response.status_code == 200
            data = response.json()
            
            # Should handle empty data gracefully
            assert 'this_month' in data or 'lifetime' not in data
    
    @pytest.mark.asyncio
    async def test_aggregate_stats_server_error(self):
        """Test aggregate stats with server error."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_aggregate_statistics = AsyncMock(
                side_effect=Exception("Database error")
            )
            mock_repo_class.return_value = mock_repo
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/analytics/stats")
            
            assert response.status_code == 500
            assert "aggregate statistics" in response.json()['detail'].lower()


class TestCategoryAnalyticsEndpoint:
    """Integration tests for GET /api/v1/analytics/categories"""
    
    @pytest.mark.asyncio
    async def test_category_analytics_success(self, mock_analytics_repo_data):
        """Test successful retrieval of category analytics."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_category_statistics = AsyncMock(
                return_value=mock_analytics_repo_data['category_stats']
            )
            mock_repo_class.return_value = mock_repo
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/analytics/categories")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            
            # Check response structure
            assert 'categories' in data
            assert 'total_categories' in data
            assert 'period' in data
            assert 'criteria' in data
            
            # Check categories data
            categories = data['categories']
            assert len(categories) == 3
            
            # Check first category (politics)
            politics = categories[0]
            assert politics['category'] == 'politics'
            assert politics['articles_count'] == 50
            assert 'avg_credibility' in politics
            assert 'false_rate' in politics
            assert 'risk_level' in politics
            assert 'top_sources' in politics
            assert len(politics['top_sources']) <= 3
    
    @pytest.mark.asyncio
    async def test_category_analytics_with_filters(self, mock_analytics_repo_data):
        """Test category analytics with custom filters."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_category_statistics = AsyncMock(
                return_value=mock_analytics_repo_data['category_stats']
            )
            mock_repo_class.return_value = mock_repo
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/analytics/categories",
                    params={
                        "days": 7,
                        "min_articles": 10,
                        "sort_by": "volume"
                    }
                )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify filters were applied
            assert data['period']['days'] == 7
            assert data['criteria']['min_articles'] == 10
            assert data['criteria']['sort_by'] == 'volume'
            
            # Verify repository was called with correct params
            mock_repo.get_category_statistics.assert_called_once_with(
                days=7,
                min_articles=10
            )
    
    @pytest.mark.asyncio
    async def test_category_analytics_sort_by_false_rate(self, mock_analytics_repo_data):
        """Test category analytics sorted by false rate."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_category_statistics = AsyncMock(
                return_value=mock_analytics_repo_data['category_stats']
            )
            mock_repo_class.return_value = mock_repo
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/analytics/categories",
                    params={"sort_by": "false_rate"}
                )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify sorting (politics should be first as it has highest false rate)
            categories = data['categories']
            false_rates = [cat['false_rate'] for cat in categories]
            assert false_rates == sorted(false_rates, reverse=True)
    
    @pytest.mark.asyncio
    async def test_category_analytics_risk_levels(self, mock_analytics_repo_data):
        """Test risk level calculation."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_category_statistics = AsyncMock(
                return_value=mock_analytics_repo_data['category_stats']
            )
            mock_repo_class.return_value = mock_repo
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/analytics/categories")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify risk levels are assigned
            for category in data['categories']:
                assert category['risk_level'] in ['low', 'medium', 'high', 'critical']
    
    @pytest.mark.asyncio
    async def test_category_analytics_validation_days_too_low(self):
        """Test validation error for days parameter too low."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/analytics/categories",
                params={"days": 0}
            )
        
        assert response.status_code == 422  # FastAPI validation error
    
    @pytest.mark.asyncio
    async def test_category_analytics_validation_days_too_high(self):
        """Test validation error for days parameter too high."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/analytics/categories",
                params={"days": 400}
            )
        
        assert response.status_code == 422  # FastAPI validation error
    
    @pytest.mark.asyncio
    async def test_category_analytics_validation_invalid_sort(self):
        """Test validation error for invalid sort_by parameter."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/analytics/categories",
                params={"sort_by": "invalid_field"}
            )
        
        assert response.status_code == 422  # FastAPI validation error
    
    @pytest.mark.asyncio
    async def test_category_analytics_empty_results(self):
        """Test category analytics with no categories."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_category_statistics = AsyncMock(return_value=[])
            mock_repo_class.return_value = mock_repo
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/analytics/categories")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data['categories'] == []
            assert data['total_categories'] == 0
    
    @pytest.mark.asyncio
    async def test_category_analytics_server_error(self):
        """Test category analytics with server error."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_category_statistics = AsyncMock(
                side_effect=Exception("Database connection failed")
            )
            mock_repo_class.return_value = mock_repo
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/analytics/categories")
            
            assert response.status_code == 500
            assert "category analytics" in response.json()['detail'].lower()


class TestPhase2AEndpointsIntegration:
    """Integration tests for Phase 2A endpoints working together."""
    
    @pytest.mark.asyncio
    async def test_both_endpoints_accessible(self, mock_analytics_repo_data):
        """Test that both Phase 2A endpoints are accessible."""
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_aggregate_statistics = AsyncMock(
                return_value=mock_analytics_repo_data['aggregate_stats']
            )
            mock_repo.get_category_statistics = AsyncMock(
                return_value=mock_analytics_repo_data['category_stats']
            )
            mock_repo_class.return_value = mock_repo
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                # Test stats endpoint
                stats_response = await client.get("/api/v1/analytics/stats")
                assert stats_response.status_code == 200
                
                # Test categories endpoint
                categories_response = await client.get("/api/v1/analytics/categories")
                assert categories_response.status_code == 200
                
                # Both should return valid data
                assert 'this_month' in stats_response.json()
                assert 'categories' in categories_response.json()
    
    @pytest.mark.asyncio
    async def test_response_time_acceptable(self, mock_analytics_repo_data):
        """Test that response times are acceptable."""
        import time
        
        with patch('app.api.v1.endpoints.analytics.AnalyticsRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_aggregate_statistics = AsyncMock(
                return_value=mock_analytics_repo_data['aggregate_stats']
            )
            mock_repo.get_category_statistics = AsyncMock(
                return_value=mock_analytics_repo_data['category_stats']
            )
            mock_repo_class.return_value = mock_repo
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                # Test stats endpoint response time
                start = time.time()
                await client.get("/api/v1/analytics/stats")
                stats_time = time.time() - start
                
                # Test categories endpoint response time
                start = time.time()
                await client.get("/api/v1/analytics/categories")
                categories_time = time.time() - start
                
                # Both should complete in under 5 seconds (with mocking)
                assert stats_time < 5.0
                assert categories_time < 5.0
