"""
Rate limiting middleware using slowapi with Redis backend.

Provides IP-based rate limiting to protect endpoints from abuse.
Falls back gracefully if Redis is unavailable.
"""

import logging
from typing import Callable

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_redis_connection_string() -> str:
    """
    Get Redis connection string for rate limiter.
    
    Returns:
        Redis URL from settings
    """
    return settings.REDIS_URL


def get_rate_limit_key(request: Request) -> str:
    """
    Generate rate limit key from request.
    
    Uses client IP address as the key. In production with reverse proxy,
    this should check X-Forwarded-For or X-Real-IP headers.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client IP address or identifier
    """
    # Check for forwarded IP (when behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, use the first one
        return forwarded_for.split(",")[0].strip()
    
    # Check for real IP header (Nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct connection IP
    return get_remote_address(request)


def create_rate_limiter() -> Limiter:
    """
    Create and configure the rate limiter instance.
    
    Returns:
        Configured Limiter instance
    """
    try:
        # Try to create limiter with Redis backend
        limiter = Limiter(
            key_func=get_rate_limit_key,
            storage_uri=get_redis_connection_string(),
            default_limits=[],  # No default limits, only explicit per-route
            application_limits=[],
            headers_enabled=True,  # Add rate limit headers to response
            swallow_errors=True,  # Don't crash if Redis is down
        )
        logger.info("Rate limiter initialized with Redis backend")
        return limiter
    except Exception as e:
        logger.error(f"Failed to initialize rate limiter with Redis: {e}")
        # Create in-memory fallback (not suitable for multi-process)
        limiter = Limiter(
            key_func=get_rate_limit_key,
            default_limits=[],
            headers_enabled=True,
            swallow_errors=True,
        )
        logger.warning("Rate limiter using in-memory storage (fallback mode)")
        return limiter


# Global rate limiter instance
limiter = create_rate_limiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle rate limit exceptions globally.
    
    Catches RateLimitExceeded exceptions and returns appropriate
    429 responses with retry-after headers.
    """
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process request through rate limiting.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response object
        """
        try:
            response = await call_next(request)
            return response
        except RateLimitExceeded as e:
            # Log rate limit violation
            logger.warning(
                f"Rate limit exceeded for {get_rate_limit_key(request)}",
                extra={
                    "ip": get_rate_limit_key(request),
                    "path": request.url.path,
                    "method": request.method,
                }
            )
            
            # Return 429 with retry-after header
            from fastapi.responses import JSONResponse
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": getattr(e, "retry_after", 60),
                },
                headers={
                    "Retry-After": str(getattr(e, "retry_after", 60)),
                    "X-RateLimit-Limit": str(getattr(e, "limit", "unknown")),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(getattr(e, "reset", "unknown")),
                }
            )
