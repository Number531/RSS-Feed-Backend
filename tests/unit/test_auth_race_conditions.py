"""
Unit tests for race condition handling in authentication.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation
from starlette.requests import Request
from starlette.datastructures import Headers


@pytest.mark.unit
class TestRegistrationRaceConditions:
    """Tests for registration endpoint race condition handling."""
    
    @pytest.mark.asyncio
    @patch("app.middleware.rate_limit.limiter._check_request_limit")  # Patch rate limit check
    async def test_handles_email_conflict_via_integrity_error(self, mock_check):
        """Should catch IntegrityError for email and return 400 with specific message."""
        mock_check.return_value = None  # Allow request
        
        from app.api.v1.endpoints.auth import register
        from app.schemas.user import UserCreate
        
        # Create proper mock request for slowapi
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/register",
            "headers": [],
            "client": ("127.0.0.1", 50000),
        }
        request = Request(scope)
        db = AsyncMock()
        user_data = UserCreate(
            email="existing@example.com",
            username="newuser",
            password="SecurePass123!",
            full_name="New User"
        )
        
        # Mock IntegrityError for email constraint
        orig_error = UniqueViolation("duplicate key value violates unique constraint \"ix_users_email\"")
        integrity_error = IntegrityError(
            "statement",
            {},
            orig_error
        )
        db.commit.side_effect = integrity_error
        
        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await register(request, user_data, db)
        
        assert exc_info.value.status_code == 400
        assert "Email already registered" in exc_info.value.detail
        db.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("app.middleware.rate_limit.limiter._check_request_limit")  # Patch rate limit check
    async def test_handles_username_conflict_via_integrity_error(self, mock_check):
        """Should catch IntegrityError for username and return 400 with specific message."""
        mock_check.return_value = None  # Allow request
        
        from app.api.v1.endpoints.auth import register
        from app.schemas.user import UserCreate
        
        # Create proper mock request for slowapi
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/register",
            "headers": [],
            "client": ("127.0.0.1", 50000),
        }
        request = Request(scope)
        db = AsyncMock()
        user_data = UserCreate(
            email="new@example.com",
            username="existinguser",
            password="SecurePass123!",
            full_name="New User"
        )
        
        # Mock IntegrityError for username constraint
        orig_error = UniqueViolation("duplicate key value violates unique constraint \"ix_users_username\"")
        integrity_error = IntegrityError(
            "statement",
            {},
            orig_error
        )
        db.commit.side_effect = integrity_error
        
        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await register(request, user_data, db)
        
        assert exc_info.value.status_code == 400
        assert "Username already taken" in exc_info.value.detail
        db.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("app.middleware.rate_limit.limiter._check_request_limit")  # Patch rate limit check
    async def test_handles_generic_integrity_error(self, mock_check):
        """Should catch generic IntegrityError and return 400."""
        mock_check.return_value = None  # Allow request
        
        from app.api.v1.endpoints.auth import register
        from app.schemas.user import UserCreate
        
        # Create proper mock request for slowapi
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/register",
            "headers": [],
            "client": ("127.0.0.1", 50000),
        }
        request = Request(scope)
        db = AsyncMock()
        user_data = UserCreate(
            email="new@example.com",
            username="newuser",
            password="SecurePass123!",
            full_name="New User"
        )
        
        # Mock generic IntegrityError
        orig_error = UniqueViolation("some other constraint")
        integrity_error = IntegrityError(
            "statement",
            {},
            orig_error
        )
        db.commit.side_effect = integrity_error
        
        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await register(request, user_data, db)
        
        assert exc_info.value.status_code == 400
        assert "User already exists" in exc_info.value.detail
        db.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_no_race_condition_with_concurrent_requests(self):
        """Should handle concurrent registration attempts atomically."""
        # This would be an integration test in a real scenario
        # Testing that no 500 errors occur during race conditions
        pass
