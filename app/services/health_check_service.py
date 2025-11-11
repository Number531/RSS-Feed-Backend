"""Enhanced health check service for monitoring system components."""

import time
from typing import Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis


class HealthCheckService:
    """Service for checking health of system components."""

    def __init__(self, db: AsyncSession, redis_client: redis.Redis = None):
        self.db = db
        self.redis_client = redis_client

    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive health status of all system components.
        
        Returns:
            Dict with overall status and component details
        """
        components = {}
        overall_healthy = True

        # Check database
        db_health = await self._check_database()
        components["database"] = db_health
        if db_health["status"] != "healthy":
            overall_healthy = False

        # Check Redis
        redis_health = await self._check_redis()
        components["redis"] = redis_health
        if redis_health["status"] != "healthy":
            overall_healthy = False

        # Check API responsiveness
        api_health = self._check_api()
        components["api"] = api_health

        return {
            "status": "healthy" if overall_healthy else "degraded",
            "timestamp": time.time(),
            "components": components
        }

    async def _check_database(self) -> Dict[str, Any]:
        """Check PostgreSQL database connectivity and responsiveness."""
        try:
            start_time = time.time()
            
            # Simple query to test connection
            result = await self.db.execute(text("SELECT 1"))
            result.scalar()
            
            # Get connection pool stats
            pool_size = self.db.bind.pool.size()
            pool_overflow = self.db.bind.pool.overflow()
            
            response_time = (time.time() - start_time) * 1000  # ms
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "pool_size": pool_size,
                "pool_overflow": pool_overflow,
                "message": "Database connection OK"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Database connection failed"
            }

    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and responsiveness."""
        if not self.redis_client:
            return {
                "status": "unknown",
                "message": "Redis client not configured"
            }
        
        try:
            start_time = time.time()
            
            # Ping Redis
            await self.redis_client.ping()
            
            # Get Redis info
            info = await self.redis_client.info()
            used_memory_mb = info.get('used_memory', 0) / (1024 * 1024)
            
            response_time = (time.time() - start_time) * 1000  # ms
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "used_memory_mb": round(used_memory_mb, 2),
                "connected_clients": info.get('connected_clients', 0),
                "message": "Redis connection OK"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Redis connection failed"
            }

    def _check_api(self) -> Dict[str, Any]:
        """Check API server health."""
        return {
            "status": "healthy",
            "message": "API server responding"
        }
