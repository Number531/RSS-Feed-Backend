"""Search service for business logic."""

import logging
from datetime import datetime
from typing import Optional

from app.repositories.search_repository import SearchRepository
from app.schemas.search import (
    SearchQuery,
    SearchResponse,
    SearchResult,
    TrendingArticleResponse,
    TrendingResponse,
)

logger = logging.getLogger(__name__)


class SearchService:
    """Service for search operations."""

    def __init__(self, repository: SearchRepository):
        self.repository = repository

    async def search_articles(
        self,
        q: str,
        category: Optional[str] = None,
        source: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = "relevance",
        page: int = 1,
        page_size: int = 20,
    ) -> SearchResponse:
        """
        Search articles with filters.

        Args:
            q: Search query string
            category: Filter by category
            source: Filter by source name
            date_from: Filter from date
            date_to: Filter to date
            sort_by: Sort by relevance, date, or votes
            page: Page number
            page_size: Items per page

        Returns:
            SearchResponse with results
        """
        # Validate and sanitize query
        if not q or len(q.strip()) == 0:
            return SearchResponse(
                results=[],
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0,
                query=q,
                execution_time_ms=0.0,
            )

        # Search articles
        articles, total, execution_time = await self.repository.search_articles(
            query=q,
            category=category,
            source=source,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
        )

        # Convert to search results
        results = []
        for article in articles:
            # Create snippet from description if available
            snippet = None
            if article.description:
                snippet = (
                    article.description[:200] + "..."
                    if len(article.description) > 200
                    else article.description
                )

            result = SearchResult(
                id=article.id,
                title=article.title,
                url=article.url,
                description=article.description,
                author=article.author,
                published_date=article.published_date,
                category=article.category,
                source_name=article.rss_source.source_name if article.rss_source else "Unknown",
                vote_score=article.vote_score or 0,
                comment_count=article.comment_count or 0,
                created_at=article.created_at,
                match_snippet=snippet,
            )
            results.append(result)

        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        logger.info(f"Search for '{q}' returned {total} results in {execution_time:.2f}ms")

        return SearchResponse(
            results=results,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            query=q,
            execution_time_ms=round(execution_time, 2),
        )

    async def get_trending_articles(self, period: str = "24h", limit: int = 20) -> TrendingResponse:
        """
        Get trending articles.

        Args:
            period: Time period (24h, 7d, 30d)
            limit: Maximum number of results

        Returns:
            TrendingResponse with trending articles
        """
        # Validate period
        valid_periods = {"24h", "7d", "30d"}
        if period not in valid_periods:
            period = "24h"

        # Get trending articles
        trending_data = await self.repository.get_trending_articles(period=period, limit=limit)

        # Convert to response
        articles = []
        for article, vote_velocity, engagement_score in trending_data:
            trending_article = TrendingArticleResponse(
                id=article.id,
                title=article.title,
                url=article.url,
                description=article.description,
                category=article.category,
                source_name=article.rss_source.source_name if article.rss_source else "Unknown",
                vote_score=article.vote_score or 0,
                comment_count=article.comment_count or 0,
                published_date=article.published_date,
                created_at=article.created_at,
                vote_velocity=round(vote_velocity, 2),
                engagement_score=round(engagement_score, 2),
            )
            articles.append(trending_article)

        logger.info(f"Retrieved {len(articles)} trending articles for period {period}")

        return TrendingResponse(articles=articles, total=len(articles), period=period)

    async def get_popular_articles(self, period: str = "all", limit: int = 20) -> TrendingResponse:
        """
        Get most popular articles by votes.

        Args:
            period: Time period (hour, day, week, month, year, all)
            limit: Maximum number of results

        Returns:
            TrendingResponse with popular articles
        """
        # Get popular articles
        articles = await self.repository.get_popular_articles(period=period, limit=limit)

        # Convert to response (reuse TrendingArticleResponse but with zero velocity)
        popular_articles = []
        for article in articles:
            popular_article = TrendingArticleResponse(
                id=article.id,
                title=article.title,
                url=article.url,
                description=article.description,
                category=article.category,
                source_name=article.rss_source.source_name if article.rss_source else "Unknown",
                vote_score=article.vote_score or 0,
                comment_count=article.comment_count or 0,
                published_date=article.published_date,
                created_at=article.created_at,
                vote_velocity=0.0,  # Not calculated for popular
                engagement_score=float(article.vote_score or 0),
            )
            popular_articles.append(popular_article)

        logger.info(f"Retrieved {len(articles)} popular articles for period {period}")

        return TrendingResponse(articles=popular_articles, total=len(articles), period=period)
