"""
Cache utilities for analytics data.

Provides Redis-based caching with TTL support for expensive analytics queries.
"""

import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable, Optional

import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Manager for Redis-based caching with analytics-specific utilities."""

    def __init__(self):
        """Initialize cache manager with Redis connection pool."""
        self.redis_client: Optional[redis.Redis] = None
        self._is_connected = False

    async def connect(self):
        """Establish Redis connection."""
        if not self._is_connected:
            try:
                self.redis_client = await redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                )
                # Test connection
                await self.redis_client.ping()
                self._is_connected = True
                logger.info("Redis cache connected successfully")
            except Exception as e:
                logger.error(f"Failed to connect to Redis cache: {e}")
                self.redis_client = None
                self._is_connected = False

    async def disconnect(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self._is_connected = False
            logger.info("Redis cache disconnected")

    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """
        Generate a unique cache key based on prefix and parameters.

        Args:
            prefix: Cache key prefix (e.g., 'analytics:sources')
            **kwargs: Parameters to include in cache key

        Returns:
            Cache key string
        """
        # Sort kwargs for consistent key generation
        sorted_params = sorted(kwargs.items())
        params_str = json.dumps(sorted_params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:12]
        return f"{prefix}:{params_hash}"

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self._is_connected or not self.redis_client:
            return None

        try:
            cached_data = await self.redis_client.get(key)
            if cached_data:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(cached_data)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds (defaults to REDIS_CACHE_TTL)

        Returns:
            True if successful, False otherwise
        """
        if not self._is_connected or not self.redis_client:
            return False

        try:
            ttl = ttl or settings.REDIS_CACHE_TTL
            serialized_value = json.dumps(value)
            await self.redis_client.setex(key, ttl, serialized_value)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        if not self._is_connected or not self.redis_client:
            return False

        try:
            await self.redis_client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.

        Args:
            pattern: Redis key pattern (e.g., 'analytics:*')

        Returns:
            Number of keys deleted
        """
        if not self._is_connected or not self.redis_client:
            return 0

        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"Cache DELETE PATTERN: {pattern} ({deleted} keys)")
                return deleted
            return 0
        except Exception as e:
            logger.warning(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    async def clear_analytics_cache(self) -> int:
        """
        Clear all analytics-related cache entries.

        Returns:
            Number of keys deleted
        """
        return await self.delete_pattern("analytics:*")


# Global cache manager instance
cache_manager = CacheManager()


def cached_analytics(
    prefix: str,
    ttl: Optional[int] = None,
    cache_key_params: Optional[list[str]] = None
):
    """
    Decorator for caching analytics service methods.

    Usage:
        @cached_analytics(prefix='analytics:sources', ttl=300, cache_key_params=['days', 'min_articles'])
        async def get_source_reliability_stats(self, days: int, min_articles: int):
            ...

    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds (default: settings.REDIS_CACHE_TTL)
        cache_key_params: List of parameter names to include in cache key

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract parameters for cache key
            cache_params = {}
            if cache_key_params:
                for param_name in cache_key_params:
                    if param_name in kwargs:
                        cache_params[param_name] = kwargs[param_name]
                    # Handle positional args by inspecting function signature
                    else:
                        import inspect
                        sig = inspect.signature(func)
                        param_list = list(sig.parameters.keys())
                        # Skip 'self' if present
                        if param_list and param_list[0] == 'self':
                            param_list = param_list[1:]
                        # Map positional args to param names
                        for i, param in enumerate(param_list):
                            if param == param_name and i < len(args) - 1:
                                cache_params[param_name] = args[i + 1]

            # Generate cache key
            cache_key = cache_manager._generate_cache_key(prefix, **cache_params)

            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await cache_manager.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator
