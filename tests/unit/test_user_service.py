"""
Unit tests for UserService.create_user method.

Tests cover:
- Successful user creation with notification preferences
- Conflict error handling (email and username collisions)
- Audit logging for successful and failed registrations
- IP address and user agent capture
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.models.audit import RegistrationAudit
from app.models.user import User
from app.models.notification import UserNotificationPreference
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.services.user_service import UserService


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock(spec=AsyncSession)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    
    # Mock nested transaction context manager
    nested_transaction = MagicMock()
    nested_transaction.__aenter__ = AsyncMock()
    nested_transaction.__aexit__ = AsyncMock()
    db.begin_nested = MagicMock(return_value=nested_transaction)
    
    return db


@pytest.fixture
def user_repository(mock_db):
    """Create UserRepository with mock database."""
    repo = UserRepository(mock_db)
    return repo


@pytest.fixture
def user_service(user_repository):
    """Create UserService for testing."""
    return UserService(user_repository)


@pytest.fixture
def sample_user_data():
    """Sample user registration data."""
    return UserCreate(
        email="test@example.com",
        username="testuser",
        password="SecurePass123!",
        full_name="Test User"
    )


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserServiceCreateUser:
    """Tests for UserService.create_user method."""
    
    async def test_create_user_success(self, user_service, sample_user_data, mock_db):
        """Test successful user creation with notification preferences."""
        # Act
        user = await user_service.create_user(sample_user_data)
        
        # Assert - User was created
        assert user is not None
        assert user.email == sample_user_data.email
        assert user.username == sample_user_data.username
        assert user.full_name == sample_user_data.full_name
        
        # Assert - Database operations called
        assert mock_db.add.call_count == 3  # User + Notification Prefs + Audit
        assert mock_db.commit.call_count == 2  # Main transaction + Audit
        assert mock_db.flush.call_count == 1  # After user creation
        
        # Assert - Nested transaction used for atomicity
        mock_db.begin_nested.assert_called_once()
    
    async def test_create_user_with_ip_and_user_agent(
        self, user_service, sample_user_data, mock_db
    ):
        """Test user creation captures IP address and user agent in audit log."""
        ip_address = "192.168.1.100"
        user_agent = "Mozilla/5.0 (Test Browser)"
        
        # Track audit entries added
        audit_entries = []
        
        def track_add(obj):
            if isinstance(obj, RegistrationAudit):
                audit_entries.append(obj)
        
        mock_db.add.side_effect = track_add
        
        # Act
        await user_service.create_user(
            sample_user_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Assert - Audit entry was created with correct data
        assert len(audit_entries) == 1
        audit = audit_entries[0]
        assert audit.email == sample_user_data.email
        assert audit.username == sample_user_data.username
        assert audit.ip_address == ip_address
        assert audit.user_agent == user_agent
        assert audit.success is True
        assert audit.failure_reason is None
    
    async def test_create_user_email_conflict(
        self, user_service, sample_user_data, mock_db
    ):
        """Test user creation fails gracefully on email conflict."""
        # Mock IntegrityError with email constraint violation
        error = IntegrityError(
            "duplicate key",
            params={},
            orig=Exception("ix_users_email")
        )
        
        # Track audit entries
        audit_entries = []
        
        def track_add_with_error(obj):
            if isinstance(obj, User):
                # Simulate constraint violation on commit
                mock_db.commit.side_effect = error
            elif isinstance(obj, RegistrationAudit):
                # Allow audit log to be added
                audit_entries.append(obj)
        
        mock_db.add.side_effect = track_add_with_error
        
        # Nested transaction needs to raise the error
        async def nested_error(*args, **kwargs):
            raise error
        
        nested_transaction = MagicMock()
        nested_transaction.__aenter__ = AsyncMock()
        nested_transaction.__aexit__ = nested_error
        mock_db.begin_nested = MagicMock(return_value=nested_transaction)
        
        # Act & Assert
        with pytest.raises(ConflictError) as exc_info:
            await user_service.create_user(sample_user_data)
        
        assert "Email already registered" in str(exc_info.value)
        
        # Assert - Rollback was called
        mock_db.rollback.assert_called()
        
        # Assert - Audit log captured the failure
        assert len(audit_entries) == 1
        audit = audit_entries[0]
        assert audit.success is False
        assert audit.failure_reason == "Email already registered"
    
    async def test_create_user_username_conflict(
        self, user_service, sample_user_data, mock_db
    ):
        """Test user creation fails gracefully on username conflict."""
        # Mock IntegrityError with username constraint violation
        error = IntegrityError(
            "duplicate key",
            params={},
            orig=Exception("ix_users_username")
        )
        
        # Track audit entries
        audit_entries = []
        
        def track_add(obj):
            if isinstance(obj, RegistrationAudit):
                audit_entries.append(obj)
        
        mock_db.add.side_effect = track_add
        
        # Nested transaction raises error
        async def nested_error(*args, **kwargs):
            raise error
        
        nested_transaction = MagicMock()
        nested_transaction.__aenter__ = AsyncMock()
        nested_transaction.__aexit__ = nested_error
        mock_db.begin_nested = MagicMock(return_value=nested_transaction)
        
        # Act & Assert
        with pytest.raises(ConflictError) as exc_info:
            await user_service.create_user(sample_user_data)
        
        assert "Username already taken" in str(exc_info.value)
        
        # Assert - Audit log captured the failure
        assert len(audit_entries) == 1
        audit = audit_entries[0]
        assert audit.success is False
        assert audit.failure_reason == "Username already taken"
    
    async def test_create_user_general_exception(
        self, user_service, sample_user_data, mock_db
    ):
        """Test user creation handles unexpected exceptions with audit logging."""
        # Mock unexpected error
        error = RuntimeError("Database connection lost")
        
        # Track audit entries
        audit_entries = []
        
        def track_add(obj):
            if isinstance(obj, RegistrationAudit):
                audit_entries.append(obj)
        
        mock_db.add.side_effect = track_add
        
        # Nested transaction raises unexpected error
        async def nested_error(*args, **kwargs):
            raise error
        
        nested_transaction = MagicMock()
        nested_transaction.__aenter__ = AsyncMock()
        nested_transaction.__aexit__ = nested_error
        mock_db.begin_nested = MagicMock(return_value=nested_transaction)
        
        # Act & Assert
        with pytest.raises(RuntimeError):
            await user_service.create_user(sample_user_data)
        
        # Assert - Rollback was called
        mock_db.rollback.assert_called()
        
        # Assert - Audit log captured the failure
        assert len(audit_entries) == 1
        audit = audit_entries[0]
        assert audit.success is False
        assert "Database connection lost" in audit.failure_reason
    
    async def test_create_user_notification_preferences(
        self, user_service, sample_user_data, mock_db
    ):
        """Test notification preferences are created with user atomically."""
        # Track what gets added to the database
        added_objects = []
        
        def track_add(obj):
            added_objects.append(obj)
        
        mock_db.add.side_effect = track_add
        
        # Act
        await user_service.create_user(sample_user_data)
        
        # Assert - User and notification preferences were both added
        user_added = any(isinstance(obj, User) for obj in added_objects)
        prefs_added = any(isinstance(obj, UserNotificationPreference) for obj in added_objects)
        
        assert user_added, "User should be added to session"
        assert prefs_added, "Notification preferences should be added to session"
        
        # Assert - Notification preferences have correct defaults
        prefs = next(obj for obj in added_objects if isinstance(obj, UserNotificationPreference))
        assert prefs.vote_notifications is True
        assert prefs.reply_notifications is True
        assert prefs.mention_notifications is True
        assert prefs.email_notifications is False
    
    async def test_create_user_audit_log_failure_reason_truncated(
        self, user_service, sample_user_data, mock_db
    ):
        """Test audit log truncates failure reasons longer than 500 characters."""
        # Create a very long error message
        long_error = "x" * 600
        error = RuntimeError(long_error)
        
        # Track audit entries
        audit_entries = []
        
        def track_add(obj):
            if isinstance(obj, RegistrationAudit):
                audit_entries.append(obj)
        
        mock_db.add.side_effect = track_add
        
        # Nested transaction raises error
        async def nested_error(*args, **kwargs):
            raise error
        
        nested_transaction = MagicMock()
        nested_transaction.__aenter__ = AsyncMock()
        nested_transaction.__aexit__ = nested_error
        mock_db.begin_nested = MagicMock(return_value=nested_transaction)
        
        # Act & Assert
        with pytest.raises(RuntimeError):
            await user_service.create_user(sample_user_data)
        
        # Assert - Failure reason is truncated to 500 characters
        assert len(audit_entries) == 1
        audit = audit_entries[0]
        assert len(audit.failure_reason) <= 500
    
    async def test_create_user_without_optional_fields(
        self, user_service, mock_db
    ):
        """Test user creation works without optional IP and user agent fields."""
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="SecurePass123!"
            # No full_name
        )
        
        # Track audit entries
        audit_entries = []
        
        def track_add(obj):
            if isinstance(obj, RegistrationAudit):
                audit_entries.append(obj)
        
        mock_db.add.side_effect = track_add
        
        # Act
        await user_service.create_user(user_data)
        
        # Assert - Audit entry created with None values for optional fields
        assert len(audit_entries) == 1
        audit = audit_entries[0]
        assert audit.ip_address is None
        assert audit.user_agent is None
        assert audit.success is True
    
    async def test_create_user_password_hashing(
        self, user_service, sample_user_data, mock_db
    ):
        """Test password is properly hashed during user creation."""
        # Track created user
        created_user = None
        
        def track_add(obj):
            nonlocal created_user
            if isinstance(obj, User):
                created_user = obj
        
        mock_db.add.side_effect = track_add
        
        # Act
        await user_service.create_user(sample_user_data)
        
        # Assert - Password was hashed
        assert created_user is not None
        assert created_user.hashed_password is not None
        assert created_user.hashed_password != sample_user_data.password
        assert created_user.hashed_password.startswith("$2b$")  # BCrypt hash prefix
