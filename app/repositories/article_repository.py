"""Article repository for database operations."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.vote import Vote


class ArticleRepository:
    """Repository for article database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_articles_feed(
        self,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
        sort_by: str = "hot",
        time_range: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> Tuple[List[Article], int]:
        """
        Get paginated articles feed with sorting and filtering.

        Hot Algorithm: Score = vote_score / (age_in_hours + 2)^1.5
        """
        # Base query
        query = select(Article)

        # Filter by category
        if category and category != "general":
            query = query.where(Article.category == category)

        # Filter by time range
        if time_range:
            cutoff = self._get_time_cutoff(time_range)
            query = query.where(Article.created_at >= cutoff)

        # Sorting
        if sort_by == "hot":
            # Hot algorithm: vote_score / (hours + 2)^1.5
            # Safe version with NULL handling
            hours_age = func.coalesce(
                func.extract("epoch", func.now() - Article.created_at) / 3600, 0
            )
            denominator = func.power(func.greatest(hours_age + 2, 2), 1.5)
            hot_score = func.coalesce(Article.vote_score, 0) / denominator
            query = query.order_by(hot_score.desc())
        elif sort_by == "new":
            query = query.order_by(Article.created_at.desc())
        elif sort_by == "top":
            # FIXED: Use vote_score for "top" sorting
            query = query.order_by(Article.vote_score.desc())

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Pagination
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute
        result = await self.db.execute(query)
        articles = list(result.scalars().all())

        # Load user votes if authenticated
        if user_id and articles:
            await self._load_user_votes(articles, user_id)

        return articles, total or 0

    async def get_article_by_id(
        self, article_id: UUID, user_id: Optional[UUID] = None
    ) -> Optional[Article]:
        """Get article by ID with optional user vote."""
        query = select(Article).where(Article.id == article_id)
        result = await self.db.execute(query)
        article = result.scalar_one_or_none()

        if article and user_id:
            await self._load_user_votes([article], user_id)

        return article

    async def search_articles(
        self, query: str, page: int = 1, page_size: int = 25
    ) -> Tuple[List[Article], int]:
        """Full-text search for articles."""
        # PostgreSQL full-text search using @@ operator explicitly
        # Create the tsvector and tsquery
        search_vector = func.to_tsvector(
            "english", Article.title + " " + func.coalesce(Article.description, "")
        )
        search_query = func.plainto_tsquery("english", query)

        # Use the @@ operator (op function) instead of .match()
        stmt = select(Article).where(search_vector.op("@@")(search_query))
        stmt = stmt.order_by(Article.created_at.desc())

        # Count
        count_query = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_query)

        # Paginate
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)

        return list(result.scalars().all()), total or 0

    async def _load_user_votes(self, articles: List[Article], user_id: UUID):
        """Load user's votes for articles."""
        article_ids = [a.id for a in articles]

        vote_query = select(Vote).where(
            and_(Vote.user_id == user_id, Vote.article_id.in_(article_ids))
        )
        result = await self.db.execute(vote_query)
        votes = {v.article_id: v.vote_value for v in result.scalars().all()}

        # Set dynamic attribute (not a column)
        for article in articles:
            article.user_vote = votes.get(article.id, 0)

    def _get_time_cutoff(self, time_range: str) -> datetime:
        """Get datetime cutoff for time range filter."""
        now = datetime.now(timezone.utc)

        if time_range == "hour":
            return now - timedelta(hours=1)
        elif time_range == "day":
            return now - timedelta(days=1)
        elif time_range == "week":
            return now - timedelta(weeks=1)
        elif time_range == "month":
            return now - timedelta(days=30)
        elif time_range == "year":
            return now - timedelta(days=365)
        else:
            return datetime.min.replace(tzinfo=timezone.utc)
