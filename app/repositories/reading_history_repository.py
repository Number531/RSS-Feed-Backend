"""Repository for reading history data access."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.reading_history import ReadingHistory


class ReadingHistoryRepository:
    """Repository for reading history database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_view(
        self,
        user_id: UUID,
        article_id: UUID,
        duration_seconds: Optional[int] = None,
        scroll_percentage: Optional[float] = None,
    ) -> ReadingHistory:
        """Record an article view."""
        history = ReadingHistory(
            user_id=user_id,
            article_id=article_id,
            duration_seconds=duration_seconds,
            scroll_percentage=scroll_percentage,
        )
        self.db.add(history)
        await self.db.flush()
        await self.db.refresh(history, ["article"])
        return history

    async def get_user_history(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 25,
    ) -> tuple[list[ReadingHistory], int]:
        """Get user's reading history with pagination and date filtering."""
        # Build base query
        query = (
            select(ReadingHistory)
            .where(ReadingHistory.user_id == user_id)
            .options(selectinload(ReadingHistory.article))
            .order_by(desc(ReadingHistory.viewed_at))
        )

        # Apply date filters
        if start_date:
            query = query.where(ReadingHistory.viewed_at >= start_date)
        if end_date:
            query = query.where(ReadingHistory.viewed_at <= end_date)

        # Get total count
        count_query = (
            select(func.count())
            .select_from(ReadingHistory)
            .where(ReadingHistory.user_id == user_id)
        )
        if start_date:
            count_query = count_query.where(ReadingHistory.viewed_at >= start_date)
        if end_date:
            count_query = count_query.where(ReadingHistory.viewed_at <= end_date)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        history = result.scalars().all()

        return list(history), total

    async def get_recently_read(
        self,
        user_id: UUID,
        days: int = 7,
        limit: int = 10,
    ) -> list[ReadingHistory]:
        """Get recently read articles."""
        since_date = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(ReadingHistory)
            .where(and_(ReadingHistory.user_id == user_id, ReadingHistory.viewed_at >= since_date))
            .options(selectinload(ReadingHistory.article))
            .order_by(desc(ReadingHistory.viewed_at))
            .limit(limit)
        )

        return list(result.scalars().all())

    async def count_views_by_user(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Count total views for user within optional date range."""
        query = (
            select(func.count())
            .select_from(ReadingHistory)
            .where(ReadingHistory.user_id == user_id)
        )

        if start_date:
            query = query.where(ReadingHistory.viewed_at >= start_date)
        if end_date:
            query = query.where(ReadingHistory.viewed_at <= end_date)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_total_reading_time(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Get total reading time in seconds."""
        query = select(func.sum(ReadingHistory.duration_seconds)).where(
            and_(ReadingHistory.user_id == user_id, ReadingHistory.duration_seconds.isnot(None))
        )

        if start_date:
            query = query.where(ReadingHistory.viewed_at >= start_date)
        if end_date:
            query = query.where(ReadingHistory.viewed_at <= end_date)

        result = await self.db.execute(query)
        total = result.scalar_one()
        return total or 0

    async def clear_history(
        self,
        user_id: UUID,
        before_date: Optional[datetime] = None,
    ) -> int:
        """Clear user's reading history. Returns number of records deleted."""
        query = delete(ReadingHistory).where(ReadingHistory.user_id == user_id)

        if before_date:
            query = query.where(ReadingHistory.viewed_at < before_date)

        result = await self.db.execute(query)
        return result.rowcount
