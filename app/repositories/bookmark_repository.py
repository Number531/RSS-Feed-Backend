"""Repository for bookmark data access."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article
from app.models.bookmark import Bookmark


class BookmarkRepository:
    """Repository for bookmark database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: UUID,
        article_id: UUID,
        collection: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Bookmark:
        """Create a new bookmark."""
        bookmark = Bookmark(
            user_id=user_id,
            article_id=article_id,
            collection=collection,
            notes=notes,
        )
        self.db.add(bookmark)
        await self.db.commit()
        await self.db.refresh(bookmark, ["article"])
        return bookmark

    async def get_by_id(self, bookmark_id: UUID) -> Optional[Bookmark]:
        """Get a bookmark by ID."""
        result = await self.db.execute(
            select(Bookmark)
            .where(Bookmark.id == bookmark_id)
            .options(selectinload(Bookmark.article))
        )
        return result.scalar_one_or_none()

    async def get_by_user_and_article(self, user_id: UUID, article_id: UUID) -> Optional[Bookmark]:
        """Get a bookmark by user and article."""
        result = await self.db.execute(
            select(Bookmark).where(
                and_(Bookmark.user_id == user_id, Bookmark.article_id == article_id)
            )
        )
        return result.scalar_one_or_none()

    async def exists(self, user_id: UUID, article_id: UUID) -> bool:
        """Check if a bookmark exists."""
        result = await self.db.execute(
            select(func.count())
            .select_from(Bookmark)
            .where(and_(Bookmark.user_id == user_id, Bookmark.article_id == article_id))
        )
        count = result.scalar_one()
        return count > 0

    async def list_by_user(
        self,
        user_id: UUID,
        collection: Optional[str] = None,
        skip: int = 0,
        limit: int = 25,
    ) -> tuple[list[Bookmark], int]:
        """List bookmarks for a user with pagination."""
        # Build base query
        query = (
            select(Bookmark)
            .where(Bookmark.user_id == user_id)
            .options(selectinload(Bookmark.article))
            .order_by(Bookmark.created_at.desc())
        )

        # Filter by collection if provided
        if collection:
            query = query.where(Bookmark.collection == collection)

        # Get total count
        count_query = select(func.count()).select_from(Bookmark).where(Bookmark.user_id == user_id)
        if collection:
            count_query = count_query.where(Bookmark.collection == collection)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        bookmarks = result.scalars().all()

        return list(bookmarks), total

    async def get_collections(self, user_id: UUID) -> list[str]:
        """Get list of unique collection names for a user."""
        result = await self.db.execute(
            select(Bookmark.collection)
            .where(and_(Bookmark.user_id == user_id, Bookmark.collection.isnot(None)))
            .distinct()
            .order_by(Bookmark.collection)
        )
        return list(result.scalars().all())

    async def update(
        self,
        bookmark_id: UUID,
        collection: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[Bookmark]:
        """Update a bookmark."""
        bookmark = await self.get_by_id(bookmark_id)
        if not bookmark:
            return None

        if collection is not None:
            bookmark.collection = collection
        if notes is not None:
            bookmark.notes = notes

        await self.db.commit()
        await self.db.refresh(bookmark)
        return bookmark

    async def delete(self, bookmark_id: UUID) -> bool:
        """Delete a bookmark."""
        result = await self.db.execute(delete(Bookmark).where(Bookmark.id == bookmark_id))
        await self.db.commit()
        return result.rowcount > 0

    async def delete_by_user_and_article(self, user_id: UUID, article_id: UUID) -> bool:
        """Delete a bookmark by user and article."""
        result = await self.db.execute(
            delete(Bookmark).where(
                and_(Bookmark.user_id == user_id, Bookmark.article_id == article_id)
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    async def count_by_user(self, user_id: UUID) -> int:
        """Count total bookmarks for a user."""
        result = await self.db.execute(
            select(func.count()).select_from(Bookmark).where(Bookmark.user_id == user_id)
        )
        return result.scalar_one()
