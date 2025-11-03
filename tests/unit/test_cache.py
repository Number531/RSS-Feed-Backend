"""
Unit tests for cache functionality.

Tests cache manager operations and cached analytics decorators.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal

from app.utils.cache import CacheManager, cached_analytics


@pytest.fixture
def mock_redis_client():
    """Mock Redis client."""
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    client.get = AsyncMock(return_value=None)
    client.setex = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=1)
    client.scan_iter = AsyncMock(return_value=iter([]))
    client.close = AsyncMock()
    return client


@pytest.fixture
async def cache_manager(mock_redis_client):
    """Cache manager with mocked Redis client."""
    manager = CacheManager()
    manager.redis_client = mock_redis_client
    manager._is_connected = True
    return manager


class TestCacheManager:
    """Test CacheManager operations."""
    
    @pytest.mark.asyncio
    async def test_generate_cache_key(self):
        """Test cache key generation with parameters."""
        manager = CacheManager()
        
        key1 = manager._generate_cache_key("analytics:test", days=30, sort="asc")
        key2 = manager._generate_cache_key("analytics:test", days=30, sort="asc")
        key3 = manager._generate_cache_key("analytics:test", days=60, sort="asc")
        
        # Same parameters should generate same key
        assert key1 == key2
        # Different parameters should generate different key
        assert key1 != key3
        # Key should include prefix
        assert key1.startswith("analytics:test:")
    
    @pytest.mark.asyncio
    async def test_get_cache_miss(self, cache_manager, mock_redis_client):
        """Test cache get with miss."""
        mock_redis_client.get.return_value = None
        
        result = await cache_manager.get("test_key")
        
        assert result is None
        mock_redis_client.get.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_get_cache_hit(self, cache_manager, mock_redis_client):
        """Test cache get with hit."""
        import json
        test_data = {"foo": "bar", "count": 42}
        mock_redis_client.get.return_value = json.dumps(test_data)
        
        result = await cache_manager.get("test_key")
        
        assert result == test_data
        mock_redis_client.get.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_set_cache(self, cache_manager, mock_redis_client):
        """Test cache set operation."""
        test_data = {"foo": "bar"}
        
        result = await cache_manager.set("test_key", test_data, ttl=300)
        
        assert result is True
        mock_redis_client.setex.assert_called_once()
        # Verify setex was called with correct parameters
        call_args = mock_redis_client.setex.call_args
        assert call_args[0][0] == "test_key"
        assert call_args[0][1] == 300  # TTL
    
    @pytest.mark.asyncio
    async def test_delete_cache(self, cache_manager, mock_redis_client):
        """Test cache delete operation."""
        result = await cache_manager.delete("test_key")
        
        assert result is True
        mock_redis_client.delete.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_delete_pattern(self, cache_manager, mock_redis_client):
        """Test delete by pattern."""
        # Mock scan_iter to return some keys
        async def mock_scan():
            for key in ["analytics:key1", "analytics:key2"]:
                yield key
        
        # Properly mock scan_iter
        mock_redis_client.scan_iter = MagicMock(return_value=mock_scan())
        mock_redis_client.delete = AsyncMock(return_value=2)
        
        deleted_count = await cache_manager.delete_pattern("analytics:*")
        
        assert deleted_count == 2
        mock_redis_client.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_clear_analytics_cache(self, cache_manager):
        """Test clearing analytics cache."""
        # Mock delete_pattern
        cache_manager.delete_pattern = AsyncMock(return_value=5)
        
        result = await cache_manager.clear_analytics_cache()
        
        assert result == 5
        cache_manager.delete_pattern.assert_called_once_with("analytics:*")


class TestCachedAnalyticsDecorator:
    """Test cached_analytics decorator."""
    
    @pytest.mark.asyncio
    async def test_decorator_cache_miss(self, cache_manager):
        """Test decorator with cache miss."""
        # Mock cache manager
        cache_manager.get = AsyncMock(return_value=None)
        cache_manager.set = AsyncMock(return_value=True)
        cache_manager._generate_cache_key = lambda prefix, **kwargs: f"{prefix}:test"
        
        # Create test function with decorator
        @cached_analytics(prefix="test", ttl=300, cache_key_params=["param1"])
        async def test_function(param1="value"):
            return {"result": "computed"}
        
        # Patch the global cache_manager
        with patch("app.utils.cache.cache_manager", cache_manager):
            result = await test_function(param1="value")
        
        # Should return computed result
        assert result == {"result": "computed"}
        # Should have tried to get from cache
        cache_manager.get.assert_called_once()
        # Should have cached the result
        cache_manager.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_decorator_cache_hit(self, cache_manager):
        """Test decorator with cache hit."""
        cached_data = {"result": "from_cache"}
        cache_manager.get = AsyncMock(return_value=cached_data)
        cache_manager.set = AsyncMock(return_value=True)
        cache_manager._generate_cache_key = lambda prefix, **kwargs: f"{prefix}:test"
        
        call_count = 0
        
        @cached_analytics(prefix="test", ttl=300, cache_key_params=["param1"])
        async def test_function(param1="value"):
            nonlocal call_count
            call_count += 1
            return {"result": "computed"}
        
        with patch("app.utils.cache.cache_manager", cache_manager):
            result = await test_function(param1="value")
        
        # Should return cached result
        assert result == cached_data
        # Should have tried to get from cache
        cache_manager.get.assert_called_once()
        # Should NOT have called the actual function
        assert call_count == 0
        # Should NOT have set cache (already cached)
        cache_manager.set.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_decorator_with_multiple_params(self, cache_manager):
        """Test decorator with multiple cache key parameters."""
        cache_manager.get = AsyncMock(return_value=None)
        cache_manager.set = AsyncMock(return_value=True)
        
        generated_keys = []
        def mock_generate_key(prefix, **kwargs):
            key = f"{prefix}:{kwargs}"
            generated_keys.append(key)
            return key
        
        cache_manager._generate_cache_key = mock_generate_key
        
        @cached_analytics(
            prefix="test",
            ttl=300,
            cache_key_params=["param1", "param2", "param3"]
        )
        async def test_function(param1, param2, param3="default"):
            return {"p1": param1, "p2": param2, "p3": param3}
        
        with patch("app.utils.cache.cache_manager", cache_manager):
            result = await test_function(param1="a", param2="b", param3="c")
        
        assert result == {"p1": "a", "p2": "b", "p3": "c"}
        # Verify cache key was generated with all params
        assert len(generated_keys) == 1
        assert "param1" in generated_keys[0]
        assert "param2" in generated_keys[0]
        assert "param3" in generated_keys[0]


class TestCacheIntegration:
    """Integration tests for cache with analytics."""
    
    @pytest.mark.asyncio
    async def test_cached_analytics_method(self):
        """Test caching on actual analytics-like method."""
        cache_manager = CacheManager()
        cache_manager.get = AsyncMock(return_value=None)
        cache_manager.set = AsyncMock(return_value=True)
        cache_manager._generate_cache_key = lambda prefix, **kwargs: f"{prefix}:test"
        
        call_count = 0
        
        class MockAnalyticsService:
            @cached_analytics(
                prefix="analytics:stats",
                ttl=900,
                cache_key_params=["days"]
            )
            async def get_stats(self, days=30):
                nonlocal call_count
                call_count += 1
                return {"days": days, "count": 100}
        
        service = MockAnalyticsService()
        
        with patch("app.utils.cache.cache_manager", cache_manager):
            # First call - cache miss
            result1 = await service.get_stats(days=30)
            assert result1 == {"days": 30, "count": 100}
            assert call_count == 1
            
            # Simulate cache hit for next call
            cache_manager.get = AsyncMock(return_value={"days": 30, "count": 100})
            
            # Second call - cache hit
            result2 = await service.get_stats(days=30)
            assert result2 == {"days": 30, "count": 100}
            # Function should not be called again
            assert call_count == 1
