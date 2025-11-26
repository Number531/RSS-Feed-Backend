"""
Unit tests for rate limiting middleware.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from slowapi.errors import RateLimitExceeded

from app.middleware.rate_limit import (
    get_rate_limit_key,
    get_redis_connection_string,
    RateLimitMiddleware,
)


@pytest.mark.unit
class TestGetRateLimitKey:
    """Tests for rate limit key generation."""
    
    def test_uses_x_forwarded_for_header(self):
        """Should use X-Forwarded-For header when present."""
        request = MagicMock(spec=Request)
        request.headers.get.side_effect = lambda key: {
            "X-Forwarded-For": "203.0.113.1, 198.51.100.1",
        }.get(key)
        
        result = get_rate_limit_key(request)
        
        assert result == "203.0.113.1"
    
    def test_uses_x_real_ip_header(self):
        """Should use X-Real-IP header when X-Forwarded-For is absent."""
        request = MagicMock(spec=Request)
        request.headers.get.side_effect = lambda key: {
            "X-Real-IP": "203.0.113.1",
        }.get(key)
        
        result = get_rate_limit_key(request)
        
        assert result == "203.0.113.1"
    
    @patch("app.middleware.rate_limit.get_remote_address")
    def test_fallback_to_remote_address(self, mock_get_remote_address):
        """Should fall back to remote address when no headers present."""
        mock_get_remote_address.return_value = "192.168.1.100"
        request = MagicMock(spec=Request)
        request.headers.get.return_value = None
        
        result = get_rate_limit_key(request)
        
        assert result == "192.168.1.100"
        mock_get_remote_address.assert_called_once_with(request)
    
    def test_strips_whitespace_from_forwarded_for(self):
        """Should strip whitespace from X-Forwarded-For IP."""
        request = MagicMock(spec=Request)
        request.headers.get.side_effect = lambda key: {
            "X-Forwarded-For": "  203.0.113.1  , 198.51.100.1",
        }.get(key)
        
        result = get_rate_limit_key(request)
        
        assert result == "203.0.113.1"


@pytest.mark.unit
class TestGetRedisConnectionString:
    """Tests for Redis connection string retrieval."""
    
    @patch("app.middleware.rate_limit.settings")
    def test_returns_redis_url_from_settings(self, mock_settings):
        """Should return REDIS_URL from settings."""
        mock_settings.REDIS_URL = "redis://localhost:6379/0"
        
        result = get_redis_connection_string()
        
        assert result == "redis://localhost:6379/0"


@pytest.mark.unit
class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware class."""
    
    @pytest.mark.asyncio
    async def test_allows_request_when_no_rate_limit(self):
        """Should pass request through when rate limit not exceeded."""
        middleware = RateLimitMiddleware(app=MagicMock())
        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/test"
        request.method = "GET"
        
        # Mock successful response
        mock_response = MagicMock()
        call_next = AsyncMock(return_value=mock_response)
        
        result = await middleware.dispatch(request, call_next)
        
        assert result == mock_response
        call_next.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_returns_429_when_rate_limit_exceeded(self):
        """Should return 429 response when rate limit exceeded."""
        middleware = RateLimitMiddleware(app=MagicMock())
        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/auth/register"
        request.method = "POST"
        request.headers.get.return_value = "203.0.113.1"
        
        # Mock rate limit exceeded exception with required Limit object
        mock_limit = MagicMock()
        mock_limit.error_message = "rate limit exceeded"
        rate_limit_error = RateLimitExceeded(mock_limit)
        rate_limit_error.retry_after = 60
        rate_limit_error.limit = "3 per minute"
        rate_limit_error.reset = "1234567890"
        
        call_next = AsyncMock(side_effect=rate_limit_error)
        
        with patch("app.middleware.rate_limit.logger") as mock_logger:
            result = await middleware.dispatch(request, call_next)
        
        # Verify response
        assert result.status_code == 429
        assert result.headers["Retry-After"] == "60"
        assert result.headers["X-RateLimit-Limit"] == "3 per minute"
        assert result.headers["X-RateLimit-Remaining"] == "0"
        
        # Verify logging
        mock_logger.warning.assert_called_once()
        log_args = mock_logger.warning.call_args
        assert "Rate limit exceeded" in log_args[0][0]
    
    @pytest.mark.asyncio
    async def test_includes_default_retry_after_when_missing(self):
        """Should include default retry_after when not in exception."""
        middleware = RateLimitMiddleware(app=MagicMock())
        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/test"
        request.method = "POST"
        request.headers.get.return_value = None
        
        # Mock rate limit exceeded without retry_after
        mock_limit = MagicMock()
        mock_limit.error_message = "rate limit exceeded"
        rate_limit_error = RateLimitExceeded(mock_limit)
        call_next = AsyncMock(side_effect=rate_limit_error)
        
        with patch("app.middleware.rate_limit.logger"):
            result = await middleware.dispatch(request, call_next)
        
        # Should use default of 60 seconds
        assert result.headers["Retry-After"] == "60"
        response_body = result.body.decode()
        assert "60" in response_body
    
    @pytest.mark.asyncio
    async def test_logs_rate_limit_violation_details(self):
        """Should log IP, path, and method when rate limit exceeded."""
        middleware = RateLimitMiddleware(app=MagicMock())
        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/auth/register"
        request.method = "POST"
        request.headers.get.side_effect = lambda key: {
            "X-Forwarded-For": "203.0.113.1",
        }.get(key)
        
        mock_limit = MagicMock()
        mock_limit.error_message = "rate limit exceeded"
        rate_limit_error = RateLimitExceeded(mock_limit)
        call_next = AsyncMock(side_effect=rate_limit_error)
        
        with patch("app.middleware.rate_limit.logger") as mock_logger:
            await middleware.dispatch(request, call_next)
        
        # Verify logging details
        log_call = mock_logger.warning.call_args
        assert "203.0.113.1" in log_call[0][0]
        log_extra = log_call[1]["extra"]
        assert log_extra["ip"] == "203.0.113.1"
        assert log_extra["path"] == "/api/v1/auth/register"
        assert log_extra["method"] == "POST"
