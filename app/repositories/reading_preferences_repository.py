"""Repository for user reading preferences."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_reading_preferences import UserReadingPreferences


class ReadingPreferencesRepository:
    """Repository for reading preferences operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: UUID) -> Optional[UserReadingPreferences]:
        """Get preferences for a user."""
        result = await self.db.execute(
            select(UserReadingPreferences).where(UserReadingPreferences.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: UUID, **kwargs) -> UserReadingPreferences:
        """Create preferences for a user."""
        prefs = UserReadingPreferences(user_id=user_id, **kwargs)
        self.db.add(prefs)
        await self.db.flush()
        await self.db.refresh(prefs)
        return prefs

    async def update(self, user_id: UUID, **kwargs) -> Optional[UserReadingPreferences]:
        """Update preferences for a user."""
        prefs = await self.get_by_user_id(user_id)
        if not prefs:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(prefs, key):
                setattr(prefs, key, value)

        await self.db.flush()
        await self.db.refresh(prefs)
        return prefs

    async def get_or_create(self, user_id: UUID) -> UserReadingPreferences:
        """Get existing preferences or create default ones."""
        prefs = await self.get_by_user_id(user_id)
        if not prefs:
            prefs = await self.create(user_id=user_id)
        return prefs
