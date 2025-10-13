"""Unit tests for ReadingPreferencesRepository."""
import pytest
from uuid import uuid4

from app.repositories.reading_preferences_repository import ReadingPreferencesRepository
from app.models.user_reading_preferences import UserReadingPreferences


@pytest.mark.asyncio
class TestReadingPreferencesRepository:
    """Test suite for ReadingPreferencesRepository."""
    
    async def test_create_preferences(self, db_session, test_user):
        """Test creating user preferences."""
        repo = ReadingPreferencesRepository(db_session)
        user_id = test_user["user_id"]
        
        prefs = await repo.create(
            user_id=user_id,
            tracking_enabled=True,
            retention_days=90
        )
        await db_session.commit()
        
        from uuid import UUID
        expected_id = UUID(user_id) if isinstance(user_id, str) else user_id
        assert prefs.user_id == expected_id
        assert prefs.tracking_enabled is True
        assert prefs.retention_days == 90
        assert prefs.analytics_opt_in is True  # Default value
        assert prefs.auto_cleanup_enabled is False  # Default value
    
    async def test_get_by_user_id(self, db_session, test_user):
        """Test getting preferences by user ID."""
        repo = ReadingPreferencesRepository(db_session)
        user_id = test_user["user_id"]
        
        # Create preferences
        created_prefs = await repo.create(user_id=user_id)
        await db_session.commit()
        
        # Get preferences
        prefs = await repo.get_by_user_id(user_id)
        
        assert prefs is not None
        assert prefs.id == created_prefs.id
        assert str(prefs.user_id) == user_id
    
    async def test_get_by_user_id_not_found(self, db_session):
        """Test getting preferences for non-existent user."""
        repo = ReadingPreferencesRepository(db_session)
        
        prefs = await repo.get_by_user_id(uuid4())
        
        assert prefs is None
    
    async def test_get_or_create_creates_new(self, db_session, test_user):
        """Test get_or_create creates preferences when they don't exist."""
        repo = ReadingPreferencesRepository(db_session)
        user_id = test_user["user_id"]
        
        # First call should create
        prefs1 = await repo.get_or_create(user_id=user_id)
        await db_session.commit()
        
        assert prefs1 is not None
        assert str(prefs1.user_id) == user_id
        assert prefs1.tracking_enabled is True  # Default
    
    async def test_get_or_create_returns_existing(self, db_session, test_user):
        """Test get_or_create returns existing preferences."""
        repo = ReadingPreferencesRepository(db_session)
        user_id = test_user["user_id"]
        
        # Create preferences
        prefs1 = await repo.get_or_create(user_id=user_id)
        await db_session.commit()
        prefs1_id = prefs1.id
        
        # Second call should return existing
        prefs2 = await repo.get_or_create(user_id=user_id)
        
        assert prefs2 is not None
        assert prefs2.id == prefs1_id
    
    async def test_update_preferences(self, db_session, test_user):
        """Test updating preferences."""
        repo = ReadingPreferencesRepository(db_session)
        user_id = test_user["user_id"]
        
        # Create preferences
        await repo.create(user_id=user_id, tracking_enabled=True)
        await db_session.commit()
        
        # Update preferences
        updated = await repo.update(
            user_id=user_id,
            tracking_enabled=False,
            retention_days=30,
            exclude_categories=["politics", "sports"]
        )
        await db_session.commit()
        
        assert updated is not None
        assert updated.tracking_enabled is False
        assert updated.retention_days == 30
        assert "politics" in updated.exclude_categories
        assert "sports" in updated.exclude_categories
    
    async def test_update_non_existent(self, db_session):
        """Test updating non-existent preferences returns None."""
        repo = ReadingPreferencesRepository(db_session)
        
        updated = await repo.update(
            user_id=uuid4(),
            tracking_enabled=False
        )
        
        assert updated is None
    
    async def test_update_partial(self, db_session, test_user):
        """Test partial update (only some fields)."""
        repo = ReadingPreferencesRepository(db_session)
        user_id = test_user["user_id"]
        
        # Create with defaults
        await repo.create(user_id=user_id)
        await db_session.commit()
        
        # Update only retention_days
        updated = await repo.update(
            user_id=user_id,
            retention_days=180
        )
        await db_session.commit()
        
        assert updated is not None
        assert updated.retention_days == 180
        assert updated.tracking_enabled is True  # Should remain unchanged
    
    async def test_create_with_all_fields(self, db_session, test_user):
        """Test creating preferences with all fields specified."""
        repo = ReadingPreferencesRepository(db_session)
        user_id = test_user["user_id"]
        
        prefs = await repo.create(
            user_id=user_id,
            tracking_enabled=False,
            analytics_opt_in=False,
            auto_cleanup_enabled=True,
            retention_days=180,
            exclude_categories=["sports", "entertainment"]
        )
        await db_session.commit()
        
        assert prefs.tracking_enabled is False
        assert prefs.analytics_opt_in is False
        assert prefs.auto_cleanup_enabled is True
        assert prefs.retention_days == 180
        assert len(prefs.exclude_categories) == 2
    
    async def test_exclude_categories_empty_list(self, db_session, test_user):
        """Test that exclude_categories defaults to empty list."""
        repo = ReadingPreferencesRepository(db_session)
        user_id = test_user["user_id"]
        
        prefs = await repo.create(user_id=user_id)
        await db_session.commit()
        
        assert prefs.exclude_categories == [] or prefs.exclude_categories is None
    
    async def test_timestamps_set_on_create(self, db_session, test_user):
        """Test that timestamps are set on creation."""
        repo = ReadingPreferencesRepository(db_session)
        user_id = test_user["user_id"]
        
        prefs = await repo.create(user_id=user_id)
        await db_session.commit()
        
        assert prefs.created_at is not None
        assert prefs.updated_at is not None
    
    async def test_unique_user_constraint(self, db_session, test_user):
        """Test that only one preferences record per user is allowed."""
        repo = ReadingPreferencesRepository(db_session)
        user_id = test_user["user_id"]
        
        # Create first preferences
        await repo.create(user_id=user_id)
        await db_session.commit()
        
        # Try to create second preferences for same user
        with pytest.raises(Exception):  # Should raise IntegrityError
            await repo.create(user_id=user_id)
            await db_session.commit()
