"""Service for article analytics operations."""

from datetime import datetime, timezone
from math import log10
from typing import Any, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.article_analytics_repository import ArticleAnalyticsRepository
from app.repositories.article_repository import ArticleRepository


class ArticleAnalyticsService:
    """Handle business logic for article analytics."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics_repo = ArticleAnalyticsRepository(db)
        self.article_repo = ArticleRepository(db)

    async def get_article_analytics(self, article_id: UUID) -> Dict[str, Any]:
        """Get comprehensive analytics for an article."""
        # Get stored analytics
        analytics = await self.analytics_repo.get_by_article_id(article_id)

        if not analytics:
            # If no analytics exist, create empty record
            analytics = await self.analytics_repo.create_or_update(article_id=article_id)

        # Get article for vote/comment counts
        article = await self.article_repo.get_by_id(article_id)
        if not article:
            raise ValueError("Article not found")

        return {
            "article_id": str(article_id),
            "views": {
                "total": analytics.total_views,
                "unique": analytics.unique_views,
                "by_source": {
                    "direct": analytics.direct_views,
                    "rss": analytics.rss_views,
                    "search": analytics.search_views,
                },
            },
            "engagement": {
                "avg_read_time_seconds": analytics.avg_read_time_seconds,
                "avg_scroll_percentage": float(analytics.avg_scroll_percentage),
                "completion_rate": float(analytics.completion_rate),
            },
            "social": {
                "shares": analytics.share_count,
                "bookmarks": analytics.bookmark_count,
                "votes": {
                    "upvotes": max(0, (article.vote_score + article.vote_count) // 2),
                    "downvotes": max(0, (article.vote_count - article.vote_score) // 2),
                },
                "comments": article.comment_count,
            },
            "trending_score": float(analytics.trending_score),
            "performance_percentile": analytics.performance_percentile,
            "last_updated": analytics.last_calculated_at.isoformat(),
        }

    def _calculate_trending_score(
        self, vote_score: int, created_at: datetime, comment_count: int
    ) -> float:
        """Calculate trending score using modified Reddit hot algorithm."""
        # Vote component (logarithmic)
        vote_component = log10(max(abs(vote_score), 1))
        if vote_score < 0:
            vote_component *= -1

        # Comment component (linear with weight)
        comment_component = comment_count * 0.5

        # Age penalty (newer = higher score)
        age_hours = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600
        age_penalty = age_hours / 24  # Decay over days

        trending_score = vote_component + comment_component - age_penalty
        return round(max(0, trending_score), 2)
