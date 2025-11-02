"""Search repository for database operations."""

import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.rss_source import RSSSource


class SearchRepository:
    """Repository for search database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_articles(
        self,
        query: str,
        category: Optional[str] = None,
        source: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = "relevance",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Article], int, float]:
        """
        Advanced full-text search with filters and relevance ranking.

        Returns: (articles, total_count, execution_time_ms)
        """
        start_time = time.time()

        # PostgreSQL full-text search
        search_vector = func.to_tsvector(
            "english",
            Article.title
            + " "
            + func.coalesce(Article.description, "")
            + " "
            + func.coalesce(Article.content, ""),
        )
        search_query_ts = func.plainto_tsquery("english", query)

        # Base query with relevance ranking
        relevance = func.ts_rank(search_vector, search_query_ts)

        stmt = select(Article, relevance.label("rank")).where(
            search_vector.op("@@")(search_query_ts)
        )

        # Apply filters
        if category:
            stmt = stmt.where(Article.category == category)

        if source:
            stmt = stmt.join(RSSSource).where(RSSSource.source_name.ilike(f"%{source}%"))

        if date_from:
            stmt = stmt.where(Article.created_at >= date_from)

        if date_to:
            stmt = stmt.where(Article.created_at <= date_to)

        # Sorting
        if sort_by == "relevance":
            stmt = stmt.order_by(relevance.desc())
        elif sort_by == "date":
            stmt = stmt.order_by(Article.created_at.desc())
        elif sort_by == "votes":
            stmt = stmt.order_by(Article.vote_score.desc())

        # Count total results
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_stmt) or 0

        # Pagination
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(stmt)
        articles = [row[0] for row in result.all()]

        execution_time = (time.time() - start_time) * 1000  # Convert to ms

        return articles, total, execution_time

    async def get_trending_articles(
        self, period: str = "24h", limit: int = 20
    ) -> List[Tuple[Article, float, float]]:
        """
        Get trending articles based on engagement velocity.

        Returns: List of (Article, vote_velocity, engagement_score)

        Algorithm:
        - vote_velocity = votes_per_hour
        - engagement_score = (vote_velocity * 2) + (comments_per_hour * 3)
        """
        # Determine time cutoff
        cutoff = self._get_time_cutoff(period)

        # Calculate hours since creation
        hours_age = func.extract("epoch", func.now() - Article.created_at) / 3600.0

        # Avoid division by zero: use max(hours_age, 0.1)
        safe_hours = func.greatest(hours_age, 0.1)

        # Calculate velocity metrics
        vote_velocity = func.coalesce(Article.vote_score, 0) / safe_hours
        comment_velocity = func.coalesce(Article.comment_count, 0) / safe_hours

        # Engagement score: weighted combination
        engagement_score = (vote_velocity * 2.0) + (comment_velocity * 3.0)

        # Query
        stmt = (
            select(
                Article,
                vote_velocity.label("vote_velocity"),
                engagement_score.label("engagement_score"),
            )
            .where(and_(Article.created_at >= cutoff, Article.vote_score > 0))  # Minimum threshold
            .order_by(engagement_score.desc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return [(row[0], float(row[1]), float(row[2])) for row in result.all()]

    async def get_popular_articles(self, period: str = "all", limit: int = 20) -> List[Article]:
        """
        Get most popular articles by vote score.

        Period options: hour, day, week, month, year, all
        """
        stmt = select(Article)

        # Apply time filter if not "all"
        if period != "all":
            cutoff = self._get_time_cutoff(period)
            stmt = stmt.where(Article.created_at >= cutoff)

        # Order by vote score
        stmt = stmt.order_by(Article.vote_score.desc()).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def _get_time_cutoff(self, period: str) -> datetime:
        """Get datetime cutoff for time period."""
        now = datetime.now(timezone.utc)

        if period in ("24h", "day"):
            return now - timedelta(days=1)
        elif period in ("7d", "week"):
            return now - timedelta(days=7)
        elif period in ("30d", "month"):
            return now - timedelta(days=30)
        elif period == "hour":
            return now - timedelta(hours=1)
        elif period == "year":
            return now - timedelta(days=365)
        else:
            return datetime.min.replace(tzinfo=timezone.utc)
