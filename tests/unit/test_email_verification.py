"""
Unit tests for email verification token system.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from app.core.email_verification import (
    delete_user_verification_tokens,
    delete_verification_token,
    generate_verification_token,
    store_verification_token,
    validate_verification_token,
)


@pytest.mark.unit
class TestGenerateVerificationToken:
    """Tests for token generation."""
    
    def test_generates_non_empty_token(self):
        """Should generate a non-empty token."""
        token = generate_verification_token()
        assert len(token) > 0
    
    def test_generates_unique_tokens(self):
        """Should generate unique tokens each time."""
        tokens = {generate_verification_token() for _ in range(100)}
        assert len(tokens) == 100  # All unique
    
    def test_token_is_url_safe(self):
        """Should generate URL-safe tokens."""
        token = generate_verification_token()
        # URL-safe tokens should only contain alphanumeric, -, and _
        assert all(c.isalnum() or c in ('-', '_') for c in token)


@pytest.mark.unit
class TestStoreVerificationToken:
    """Tests for storing verification tokens."""
    
    @pytest.mark.asyncio
    async def test_stores_token_successfully_when_redis_connected(self):
        """Should store token in Redis when connected."""
        user_id = uuid4()
        token = "test_token_123"
        
        # Mock Redis connection
        mock_redis = AsyncMock()
        
        with patch("app.core.email_verification.cache_manager") as mock_cache:
            mock_cache._is_connected = True
            mock_cache.redis_client = mock_redis
            
            result = await store_verification_token(user_id, token)
            
            assert result is True
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args[0]
            assert call_args[0] == f"verify:{token}"
            assert call_args[2] == str(user_id)
    
    @pytest.mark.asyncio
    async def test_returns_false_when_redis_not_connected(self):
        """Should return False when Redis not connected."""
        user_id = uuid4()
        token = "test_token_123"
        
        with patch("app.core.email_verification.cache_manager") as mock_cache:
            mock_cache._is_connected = False
            mock_cache.redis_client = None
            
            result = await store_verification_token(user_id, token)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_handles_redis_error_gracefully(self):
        """Should return False on Redis error."""
        user_id = uuid4()
        token = "test_token_123"
        
        mock_redis = AsyncMock()
        mock_redis.setex.side_effect = Exception("Redis error")
        
        with patch("app.core.email_verification.cache_manager") as mock_cache:
            mock_cache._is_connected = True
            mock_cache.redis_client = mock_redis
            
            result = await store_verification_token(user_id, token)
            
            assert result is False


@pytest.mark.unit
class TestValidateVerificationToken:
    """Tests for validating verification tokens."""
    
    @pytest.mark.asyncio
    async def test_validates_correct_token(self):
        """Should return user ID for valid token."""
        user_id = uuid4()
        token = "valid_token_123"
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = str(user_id)
        
        with patch("app.core.email_verification.cache_manager") as mock_cache:
            mock_cache._is_connected = True
            mock_cache.redis_client = mock_redis
            
            result = await validate_verification_token(token)
            
            assert result == user_id
            mock_redis.get.assert_called_once_with(f"verify:{token}")
    
    @pytest.mark.asyncio
    async def test_returns_none_for_expired_token(self):
        """Should return None for expired/non-existent token."""
        token = "expired_token"
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        
        with patch("app.core.email_verification.cache_manager") as mock_cache:
            mock_cache._is_connected = True
            mock_cache.redis_client = mock_redis
            
            result = await validate_verification_token(token)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_returns_none_for_invalid_uuid(self):
        """Should return None if stored value is not valid UUID."""
        token = "invalid_uuid_token"
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = "not-a-valid-uuid"
        
        with patch("app.core.email_verification.cache_manager") as mock_cache:
            mock_cache._is_connected = True
            mock_cache.redis_client = mock_redis
            
            result = await validate_verification_token(token)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_returns_none_when_redis_not_connected(self):
        """Should return None when Redis not connected."""
        token = "test_token"
        
        with patch("app.core.email_verification.cache_manager") as mock_cache:
            mock_cache._is_connected = False
            mock_cache.redis_client = None
            
            result = await validate_verification_token(token)
            
            assert result is None


@pytest.mark.unit
class TestDeleteVerificationToken:
    """Tests for deleting verification tokens."""
    
    @pytest.mark.asyncio
    async def test_deletes_token_successfully(self):
        """Should delete token from Redis."""
        token = "test_token_123"
        
        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 1
        
        with patch("app.core.email_verification.cache_manager") as mock_cache:
            mock_cache._is_connected = True
            mock_cache.redis_client = mock_redis
            
            result = await delete_verification_token(token)
            
            assert result is True
            mock_redis.delete.assert_called_once_with(f"verify:{token}")
    
    @pytest.mark.asyncio
    async def test_returns_false_when_redis_not_connected(self):
        """Should return False when Redis not connected."""
        token = "test_token"
        
        with patch("app.core.email_verification.cache_manager") as mock_cache:
            mock_cache._is_connected = False
            mock_cache.redis_client = None
            
            result = await delete_verification_token(token)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_handles_deletion_error_gracefully(self):
        """Should return False on deletion error."""
        token = "test_token"
        
        mock_redis = AsyncMock()
        mock_redis.delete.side_effect = Exception("Redis error")
        
        with patch("app.core.email_verification.cache_manager") as mock_cache:
            mock_cache._is_connected = True
            mock_cache.redis_client = mock_redis
            
            result = await delete_verification_token(token)
            
            assert result is False


@pytest.mark.unit
class TestDeleteUserVerificationTokens:
    """Tests for deleting all user tokens."""
    
    @pytest.mark.asyncio
    async def test_deletes_all_user_tokens(self):
        """Should delete all tokens for a user."""
        user_id = uuid4()
        
        # Mock scan_iter to return multiple tokens
        mock_redis = AsyncMock()
        
        async def mock_scan_iter(match):
            for key in [f"verify:token1", f"verify:token2", f"verify:token3"]:
                yield key
        
        mock_redis.scan_iter = mock_scan_iter
        mock_redis.get = AsyncMock(return_value=str(user_id))
        mock_redis.delete = AsyncMock(return_value=3)
        
        with patch("app.core.email_verification.cache_manager") as mock_cache:
            mock_cache._is_connected = True
            mock_cache.redis_client = mock_redis
            
            result = await delete_user_verification_tokens(user_id)
            
            assert result == 3
    
    @pytest.mark.asyncio
    async def test_returns_zero_when_no_tokens_found(self):
        """Should return 0 when no tokens found."""
        user_id = uuid4()
        
        mock_redis = AsyncMock()
        
        async def mock_scan_iter(match):
            return
            yield  # Empty generator
        
        mock_redis.scan_iter = mock_scan_iter
        
        with patch("app.core.email_verification.cache_manager") as mock_cache:
            mock_cache._is_connected = True
            mock_cache.redis_client = mock_redis
            
            result = await delete_user_verification_tokens(user_id)
            
            assert result == 0
    
    @pytest.mark.asyncio
    async def test_returns_zero_when_redis_not_connected(self):
        """Should return 0 when Redis not connected."""
        user_id = uuid4()
        
        with patch("app.core.email_verification.cache_manager") as mock_cache:
            mock_cache._is_connected = False
            mock_cache.redis_client = None
            
            result = await delete_user_verification_tokens(user_id)
            
            assert result == 0
