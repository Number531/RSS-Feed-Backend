"""Repository for RSS Source data access."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import Integer, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rss_source import RSSSource


class RSSSourceRepository:
    """Repository for managing RSS Source data access."""

    def __init__(self, db: AsyncSession):
        """
        Initialize repository.

        Args:
            db: Database session
        """
        self.db = db

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[List[RSSSource], int]:
        """
        Get all RSS sources with optional filtering and pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            category: Optional category filter
            is_active: Optional active status filter

        Returns:
            Tuple of (list of sources, total count)
        """
        # Build query with filters
        query = select(RSSSource)

        if category:
            query = query.where(RSSSource.category == category)
        if is_active is not None:
            query = query.where(RSSSource.is_active == is_active)

        # Get total count
        count_query = select(func.count()).select_from(RSSSource)
        if category:
            count_query = count_query.where(RSSSource.category == category)
        if is_active is not None:
            count_query = count_query.where(RSSSource.is_active == is_active)

        result = await self.db.execute(count_query)
        total = result.scalar_one()

        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(RSSSource.source_name, RSSSource.name)
        result = await self.db.execute(query)
        sources = list(result.scalars().all())

        return sources, total

    async def get_by_id(self, source_id: UUID) -> Optional[RSSSource]:
        """
        Get RSS source by ID.

        Args:
            source_id: Source UUID

        Returns:
            RSS source or None
        """
        result = await self.db.execute(select(RSSSource).where(RSSSource.id == source_id))
        return result.scalar_one_or_none()

    async def get_by_url(self, url: str) -> Optional[RSSSource]:
        """
        Get RSS source by URL.

        Args:
            url: Feed URL

        Returns:
            RSS source or None
        """
        result = await self.db.execute(select(RSSSource).where(RSSSource.url == url))
        return result.scalar_one_or_none()

    async def create(self, source_data: dict) -> RSSSource:
        """
        Create new RSS source.

        Args:
            source_data: Source data dictionary

        Returns:
            Created RSS source
        """
        source = RSSSource(**source_data)
        self.db.add(source)
        await self.db.commit()
        await self.db.refresh(source)
        return source

    async def update(self, source: RSSSource, update_data: dict) -> RSSSource:
        """
        Update RSS source.

        Args:
            source: RSS source to update
            update_data: Dictionary of fields to update

        Returns:
            Updated RSS source
        """
        for field, value in update_data.items():
            if value is not None:
                setattr(source, field, value)

        await self.db.commit()
        await self.db.refresh(source)
        return source

    async def delete(self, source: RSSSource) -> None:
        """
        Delete RSS source.

        Args:
            source: RSS source to delete
        """
        await self.db.delete(source)
        await self.db.commit()

    async def get_categories(self) -> List[dict]:
        """
        Get list of categories with counts.

        Returns:
            List of dictionaries with category stats
        """
        query = (
            select(
                RSSSource.category,
                func.count(RSSSource.id).label("count"),
                func.sum(func.cast(RSSSource.is_active, Integer)).label("active_count"),
            )
            .group_by(RSSSource.category)
            .order_by(RSSSource.category)
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {"category": row.category, "count": row.count, "active_count": row.active_count or 0}
            for row in rows
        ]

    async def get_active_sources(self) -> List[RSSSource]:
        """
        Get all active RSS sources.

        Returns:
            List of active RSS sources
        """
        result = await self.db.execute(
            select(RSSSource).where(RSSSource.is_active == True).order_by(RSSSource.source_name)
        )
        return list(result.scalars().all())
