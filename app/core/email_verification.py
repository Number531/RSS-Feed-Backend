"""
Email verification token management.

Handles secure token generation, Redis storage, and validation
for email verification during user registration.
"""

import logging
import secrets
from typing import Optional
from uuid import UUID

from app.utils.cache import cache_manager

logger = logging.getLogger(__name__)

# Token expiration time in seconds (1 hour)
TOKEN_EXPIRATION = 3600


def generate_verification_token() -> str:
    """
    Generate a secure random token for email verification.
    
    Uses secrets.token_urlsafe for cryptographically strong random tokens
    that are safe to use in URLs.
    
    Returns:
        32-character URL-safe token string
    """
    return secrets.token_urlsafe(32)


async def store_verification_token(user_id: UUID, token: str) -> bool:
    """
    Store verification token in Redis with expiration.
    
    The token is stored with a 1-hour TTL. Multiple tokens can exist
    for the same user (if they request resend), but only the latest
    token will be valid.
    
    Args:
        user_id: User UUID to associate with token
        token: Verification token to store
        
    Returns:
        True if stored successfully, False otherwise
    """
    try:
        if not cache_manager._is_connected or not cache_manager.redis_client:
            logger.warning("Redis not connected, cannot store verification token")
            return False
        
        # Store token with user_id as value
        key = f"verify:{token}"
        await cache_manager.redis_client.setex(
            key,
            TOKEN_EXPIRATION,
            str(user_id)
        )
        
        logger.info(
            f"Stored verification token for user {user_id}",
            extra={"user_id": str(user_id), "token_prefix": token[:8]}
        )
        return True
        
    except Exception as e:
        logger.error(
            f"Failed to store verification token: {e}",
            extra={"user_id": str(user_id)}
        )
        return False


async def validate_verification_token(token: str) -> Optional[UUID]:
    """
    Validate verification token and return associated user ID.
    
    Checks if token exists in Redis and hasn't expired. Does NOT
    delete the token - use delete_verification_token after successful
    verification.
    
    Args:
        token: Verification token to validate
        
    Returns:
        User UUID if token is valid, None otherwise
    """
    try:
        if not cache_manager._is_connected or not cache_manager.redis_client:
            logger.warning("Redis not connected, cannot validate verification token")
            return None
        
        # Get user_id from token
        key = f"verify:{token}"
        user_id_str = await cache_manager.redis_client.get(key)
        
        if not user_id_str:
            logger.debug(
                "Verification token not found or expired",
                extra={"token_prefix": token[:8]}
            )
            return None
        
        # Convert string back to UUID
        user_id = UUID(user_id_str)
        
        logger.info(
            f"Verified token for user {user_id}",
            extra={"user_id": str(user_id), "token_prefix": token[:8]}
        )
        return user_id
        
    except ValueError as e:
        logger.warning(
            f"Invalid UUID in verification token: {e}",
            extra={"token_prefix": token[:8]}
        )
        return None
    except Exception as e:
        logger.error(
            f"Failed to validate verification token: {e}",
            extra={"token_prefix": token[:8]}
        )
        return None


async def delete_verification_token(token: str) -> bool:
    """
    Delete verification token from Redis.
    
    Should be called after successful email verification to prevent
    token reuse.
    
    Args:
        token: Verification token to delete
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        if not cache_manager._is_connected or not cache_manager.redis_client:
            logger.warning("Redis not connected, cannot delete verification token")
            return False
        
        key = f"verify:{token}"
        deleted = await cache_manager.redis_client.delete(key)
        
        if deleted:
            logger.info(
                "Deleted verification token",
                extra={"token_prefix": token[:8]}
            )
        
        return bool(deleted)
        
    except Exception as e:
        logger.error(
            f"Failed to delete verification token: {e}",
            extra={"token_prefix": token[:8]}
        )
        return False


async def delete_user_verification_tokens(user_id: UUID) -> int:
    """
    Delete all verification tokens for a specific user.
    
    Useful when user changes email or when cleaning up after verification.
    Uses pattern matching to find all tokens associated with the user.
    
    Args:
        user_id: User UUID to delete tokens for
        
    Returns:
        Number of tokens deleted
    """
    try:
        if not cache_manager._is_connected or not cache_manager.redis_client:
            logger.warning("Redis not connected, cannot delete user tokens")
            return 0
        
        # Find all verification tokens
        keys = []
        pattern = "verify:*"
        async for key in cache_manager.redis_client.scan_iter(match=pattern):
            # Check if this token belongs to the user
            user_id_str = await cache_manager.redis_client.get(key)
            if user_id_str == str(user_id):
                keys.append(key)
        
        if keys:
            deleted = await cache_manager.redis_client.delete(*keys)
            logger.info(
                f"Deleted {deleted} verification token(s) for user {user_id}",
                extra={"user_id": str(user_id), "count": deleted}
            )
            return deleted
        
        return 0
        
    except Exception as e:
        logger.error(
            f"Failed to delete user verification tokens: {e}",
            extra={"user_id": str(user_id)}
        )
        return 0
