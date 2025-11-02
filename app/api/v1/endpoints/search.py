"""
Search API endpoints.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.search_repository import SearchRepository
from app.schemas.search import SearchResponse, TrendingResponse
from app.services.search_service import SearchService

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search_articles(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    category: Optional[str] = Query(
        None,
        pattern="^(general|politics|us|world|science|technology|business|entertainment|sports|health)$",
    ),
    source: Optional[str] = Query(None, max_length=100, description="Filter by source name"),
    date_from: Optional[datetime] = Query(
        None, description="Filter articles from this date (ISO 8601)"
    ),
    date_to: Optional[datetime] = Query(
        None, description="Filter articles to this date (ISO 8601)"
    ),
    sort_by: str = Query(
        "relevance",
        pattern="^(relevance|date|votes)$",
        description="Sort by relevance, date, or votes",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search articles with full-text search and filters.

    **Search Features:**
    - Full-text search across title, description, and content
    - Relevance ranking using PostgreSQL ts_rank
    - Filter by category, source, date range
    - Sort by relevance, date, or votes

    **Query Examples:**
    - `?q=climate change` - Search for "climate change"
    - `?q=election&category=politics` - Search politics articles
    - `?q=technology&sort_by=votes` - Search and sort by votes
    - `?q=covid&date_from=2025-01-01` - Search recent articles

    **Returns:**
    - Paginated search results with execution time
    - Match snippets for each result
    - Total count and relevance scoring
    """
    repository = SearchRepository(db)
    service = SearchService(repository)

    return await service.search_articles(
        q=q,
        category=category,
        source=source,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )


@router.get("/trending", response_model=TrendingResponse, tags=["discovery"])
async def get_trending_articles(
    period: str = Query("24h", pattern="^(24h|7d|30d)$", description="Time period"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get trending articles based on engagement velocity.

    **Trending Algorithm:**
    - Calculates vote velocity (votes per hour)
    - Calculates comment velocity (comments per hour)
    - Engagement score = (vote_velocity × 2) + (comment_velocity × 3)
    - Only includes articles with at least 1 vote

    **Period Options:**
    - `24h` - Last 24 hours (default)
    - `7d` - Last 7 days
    - `30d` - Last 30 days

    **Use Cases:**
    - Homepage trending section
    - Breaking news discovery
    - Real-time engagement tracking

    **Returns:**
    - Articles ranked by engagement velocity
    - Vote velocity and engagement scores for each article
    """
    repository = SearchRepository(db)
    service = SearchService(repository)

    return await service.get_trending_articles(period=period, limit=limit)


@router.get("/popular", response_model=TrendingResponse, tags=["discovery"])
async def get_popular_articles(
    period: str = Query(
        "all", pattern="^(hour|day|week|month|year|all)$", description="Time period"
    ),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get most popular articles by vote score.

    **Ranking:**
    - Sorted by total vote score (upvotes - downvotes)
    - Filtered by time period if specified

    **Period Options:**
    - `hour` - Last hour
    - `day` - Last 24 hours
    - `week` - Last 7 days
    - `month` - Last 30 days
    - `year` - Last 365 days
    - `all` - All time (default)

    **Use Cases:**
    - "Top Posts" sections
    - Historical popular content
    - Best of the week/month/year

    **Returns:**
    - Articles ranked by vote score
    - Filtered by specified time period
    """
    repository = SearchRepository(db)
    service = SearchService(repository)

    return await service.get_popular_articles(period=period, limit=limit)
