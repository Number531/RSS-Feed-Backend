"""Repository for article analytics operations."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article_analytics import ArticleAnalytics


class ArticleAnalyticsRepository:
    """Handle database operations for article analytics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_article_id(self, article_id: UUID) -> Optional[ArticleAnalytics]:
        """Get analytics for a specific article."""
        result = await self.db.execute(
            select(ArticleAnalytics).where(ArticleAnalytics.article_id == article_id)
        )
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        article_id: UUID,
        total_views: int = 0,
        unique_views: int = 0,
        direct_views: int = 0,
        rss_views: int = 0,
        search_views: int = 0,
        avg_read_time_seconds: int = 0,
        avg_scroll_percentage: float = 0.0,
        completion_rate: float = 0.0,
        bookmark_count: int = 0,
        share_count: int = 0,
        trending_score: float = 0.0,
        performance_percentile: int = 0,
    ) -> ArticleAnalytics:
        """Create or update analytics record."""
        existing = await self.get_by_article_id(article_id)

        if existing:
            # Update existing record
            existing.total_views = total_views
            existing.unique_views = unique_views
            existing.direct_views = direct_views
            existing.rss_views = rss_views
            existing.search_views = search_views
            existing.avg_read_time_seconds = avg_read_time_seconds
            existing.avg_scroll_percentage = avg_scroll_percentage
            existing.completion_rate = completion_rate
            existing.bookmark_count = bookmark_count
            existing.share_count = share_count
            existing.trending_score = trending_score
            existing.performance_percentile = performance_percentile
            existing.last_calculated_at = datetime.now(timezone.utc)

            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            # Create new record
            analytics = ArticleAnalytics(
                article_id=article_id,
                total_views=total_views,
                unique_views=unique_views,
                direct_views=direct_views,
                rss_views=rss_views,
                search_views=search_views,
                avg_read_time_seconds=avg_read_time_seconds,
                avg_scroll_percentage=avg_scroll_percentage,
                completion_rate=completion_rate,
                bookmark_count=bookmark_count,
                share_count=share_count,
                trending_score=trending_score,
                performance_percentile=performance_percentile,
            )

            self.db.add(analytics)
            await self.db.commit()
            await self.db.refresh(analytics)
            return analytics

    async def calculate_performance_percentile(self, article_id: UUID) -> int:
        """Calculate performance percentile for an article."""
        # Get article's trending score
        analytics = await self.get_by_article_id(article_id)
        if not analytics:
            return 0

        # Count articles with lower trending score
        result = await self.db.execute(
            select(func.count(ArticleAnalytics.id)).where(
                ArticleAnalytics.trending_score < analytics.trending_score
            )
        )
        lower_count = result.scalar() or 0

        # Get total articles
        result = await self.db.execute(select(func.count(ArticleAnalytics.id)))
        total_count = result.scalar() or 1

        # Calculate percentile
        percentile = int((lower_count / total_count) * 100)
        return percentile
