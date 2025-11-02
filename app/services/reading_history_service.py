"""Reading history service with business logic."""

import csv
import io
import json
from datetime import datetime
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reading_history import ReadingHistory
from app.models.user_reading_preferences import UserReadingPreferences
from app.repositories.article_repository import ArticleRepository
from app.repositories.reading_history_repository import ReadingHistoryRepository
from app.repositories.reading_preferences_repository import ReadingPreferencesRepository


class ReadingHistoryService:
    """Service for managing user reading history."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.session = session
        self.history_repo = ReadingHistoryRepository(session)
        self.article_repo = ArticleRepository(session)
        self.preferences_repo = ReadingPreferencesRepository(session)

    async def record_view(
        self,
        user_id: str,
        article_id: str,
        duration_seconds: Optional[int] = None,
        scroll_percentage: Optional[float] = None,
    ) -> ReadingHistory:
        """
        Record a new article view with optional engagement metrics.

        Args:
            user_id: ID of the user viewing the article
            article_id: ID of the article being viewed
            duration_seconds: Optional reading duration in seconds
            scroll_percentage: Optional scroll depth percentage (0-100)

        Returns:
            Created ReadingHistory object

        Raises:
            HTTPException: If article not found or validation fails
        """
        # Validate article exists
        article = await self.article_repo.get_article_by_id(article_id)
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Article with ID {article_id} not found",
            )

        # Validate engagement metrics
        if duration_seconds is not None and duration_seconds < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Duration must be non-negative"
            )

        if scroll_percentage is not None:
            if scroll_percentage < 0 or scroll_percentage > 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Scroll percentage must be between 0 and 100",
                )

        # Record view
        history = await self.history_repo.record_view(
            user_id=user_id,
            article_id=article_id,
            duration_seconds=duration_seconds,
            scroll_percentage=scroll_percentage,
        )

        await self.session.commit()
        await self.session.refresh(history)

        return history

    async def get_user_history(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Tuple[List[ReadingHistory], int]:
        """
        Get paginated reading history for a user.

        Args:
            user_id: ID of the user
            skip: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 20)
            start_date: Optional filter for views after this date
            end_date: Optional filter for views before this date

        Returns:
            Tuple of (history list, total count)

        Raises:
            HTTPException: If validation fails
        """
        # Validate pagination
        if skip < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Skip must be non-negative"
            )

        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Limit must be between 1 and 100"
            )

        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Start date must be before end date"
            )

        history_list, total = await self.history_repo.get_user_history(
            user_id=user_id, skip=skip, limit=limit, start_date=start_date, end_date=end_date
        )

        return history_list, total

    async def get_recently_read(
        self, user_id: str, days: int = 7, limit: int = 10
    ) -> List[ReadingHistory]:
        """
        Get recently read articles for a user.

        Args:
            user_id: ID of the user
            days: Number of days to look back (default: 7)
            limit: Maximum number of articles to return (default: 10)

        Returns:
            List of ReadingHistory objects

        Raises:
            HTTPException: If validation fails
        """
        if days < 1 or days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Days must be between 1 and 365"
            )

        if limit < 1 or limit > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Limit must be between 1 and 50"
            )

        return await self.history_repo.get_recently_read(user_id=user_id, days=days, limit=limit)

    async def get_reading_stats(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """
        Get reading statistics for a user.

        Args:
            user_id: ID of the user
            start_date: Optional filter for views after this date
            end_date: Optional filter for views before this date

        Returns:
            Dictionary with reading statistics

        Raises:
            HTTPException: If validation fails
        """
        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Start date must be before end date"
            )

        # Get statistics
        total_views = await self.history_repo.count_views_by_user(
            user_id=user_id, start_date=start_date, end_date=end_date
        )

        total_reading_time = await self.history_repo.get_total_reading_time(
            user_id=user_id, start_date=start_date, end_date=end_date
        )

        # Calculate average reading time per article
        avg_reading_time = 0
        if total_views > 0:
            avg_reading_time = total_reading_time / total_views

        return {
            "total_views": total_views,
            "total_reading_time_seconds": total_reading_time,
            "average_reading_time_seconds": round(avg_reading_time, 2),
            "period_start": start_date,
            "period_end": end_date,
        }

    async def clear_history(self, user_id: str, before_date: Optional[datetime] = None) -> int:
        """
        Clear reading history for a user.

        Args:
            user_id: ID of the user
            before_date: Optional - only clear history before this date

        Returns:
            Number of records deleted
        """
        deleted_count = await self.history_repo.clear_history(
            user_id=user_id, before_date=before_date
        )

        await self.session.commit()

        return deleted_count

    # Export methods

    async def export_history(
        self,
        user_id: str,
        format: str = "json",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_articles: bool = True,
    ) -> Tuple[str, str]:
        """
        Export reading history in specified format.

        Args:
            user_id: ID of the user
            format: Export format (json or csv)
            start_date: Optional start date for export range
            end_date: Optional end date for export range
            include_articles: Include full article details

        Returns:
            Tuple of (content, filename)
        """
        # Get all history (no pagination for export)
        history_list, total = await self.history_repo.get_user_history(
            user_id=user_id,
            skip=0,
            limit=10000,  # Max export limit
            start_date=start_date,
            end_date=end_date,
        )

        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"reading_history_{timestamp}.{format}"

        if format == "json":
            content = self._export_json(history_list, include_articles)
        elif format == "csv":
            content = self._export_csv(history_list, include_articles)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported export format: {format}",
            )

        return content, filename

    def _export_json(self, history_list: List[ReadingHistory], include_articles: bool) -> str:
        """Export history as JSON."""
        data = []
        for h in history_list:
            item = {
                "id": str(h.id),
                "viewed_at": h.viewed_at.isoformat(),
                "duration_seconds": h.duration_seconds,
                "scroll_percentage": float(h.scroll_percentage) if h.scroll_percentage else None,
            }

            if include_articles and h.article:
                item["article"] = {
                    "id": str(h.article.id),
                    "title": h.article.title,
                    "url": h.article.url,
                    "category": h.article.category,
                    "published_date": (
                        h.article.published_date.isoformat() if h.article.published_date else None
                    ),
                }
            else:
                item["article_id"] = str(h.article_id)

            data.append(item)

        export_data = {
            "export_date": datetime.utcnow().isoformat(),
            "total_records": len(data),
            "records": data,
        }

        return json.dumps(export_data, indent=2)

    def _export_csv(self, history_list: List[ReadingHistory], include_articles: bool) -> str:
        """Export history as CSV."""
        output = io.StringIO()

        if include_articles:
            fieldnames = [
                "viewed_at",
                "duration_seconds",
                "scroll_percentage",
                "article_title",
                "article_url",
                "article_category",
                "article_published_date",
            ]
        else:
            fieldnames = ["article_id", "viewed_at", "duration_seconds", "scroll_percentage"]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for h in history_list:
            if include_articles and h.article:
                row = {
                    "viewed_at": h.viewed_at.isoformat(),
                    "duration_seconds": h.duration_seconds or "",
                    "scroll_percentage": h.scroll_percentage or "",
                    "article_title": h.article.title,
                    "article_url": h.article.url,
                    "article_category": h.article.category,
                    "article_published_date": (
                        h.article.published_date.isoformat() if h.article.published_date else ""
                    ),
                }
            else:
                row = {
                    "article_id": str(h.article_id),
                    "viewed_at": h.viewed_at.isoformat(),
                    "duration_seconds": h.duration_seconds or "",
                    "scroll_percentage": h.scroll_percentage or "",
                }

            writer.writerow(row)

        return output.getvalue()

    # Preferences methods

    async def get_user_preferences(self, user_id: str) -> UserReadingPreferences:
        """Get or create user reading preferences."""
        return await self.preferences_repo.get_or_create(user_id=user_id)

    async def update_user_preferences(self, user_id: str, **kwargs) -> UserReadingPreferences:
        """Update user reading preferences."""
        prefs = await self.preferences_repo.update(user_id=user_id, **kwargs)

        if not prefs:
            # Create if doesn't exist
            prefs = await self.preferences_repo.create(user_id=user_id, **kwargs)

        await self.session.commit()
        await self.session.refresh(prefs)

        return prefs

    async def should_track_reading(self, user_id: str, category: Optional[str] = None) -> bool:
        """Check if reading should be tracked based on user preferences."""
        prefs = await self.get_user_preferences(user_id)

        # Check if tracking is enabled
        if not prefs.tracking_enabled:
            return False

        # Check if category is excluded
        if category and category in prefs.exclude_categories:
            return False

        return True
