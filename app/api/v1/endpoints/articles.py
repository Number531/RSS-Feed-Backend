"""
Articles API Endpoints

Provides endpoints for browsing, viewing, and searching articles from RSS feeds.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_article_service
from app.core.security import get_current_user_optional
from app.models.user import User
from app.schemas.article import ArticleResponse
from app.services.article_service import ArticleService

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
async def get_articles_feed(
    category: Optional[str] = Query(None, pattern="^(general|politics|us|world|science)$"),
    sort_by: str = Query("hot", pattern="^(hot|new|top)$"),
    time_range: Optional[str] = Query(None, pattern="^(hour|day|week|month|year|all)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user_optional),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Get paginated articles feed with filtering and sorting.

    **Query Parameters**:
    - **category**: Filter by category (general, politics, us, world, science)
    - **sort_by**: Sort order (hot, new, top) - default: hot
    - **time_range**: Time filter (hour, day, week, month, year, all)
    - **page**: Page number (1-indexed) - default: 1
    - **page_size**: Items per page (1-100) - default: 25

    **Sorting Algorithms**:
    - **hot**: Trending algorithm based on votes and time
    - **new**: Most recent articles first
    - **top**: Highest voted articles first

    **Returns**:
    - List of articles with pagination metadata
    - Includes user's vote status if authenticated

    **Example**:
    ```
    GET /api/v1/articles?category=politics&sort_by=hot&page=1
    ```
    """
    # Get user ID if authenticated
    user_id = current_user.id if current_user else None

    # Call service layer
    articles, metadata = await article_service.get_articles_feed(
        category=category,
        sort_by=sort_by,
        time_range=time_range,
        page=page,
        page_size=page_size,
        user_id=user_id,
    )

    # Convert articles to response format
    articles_data = [
        {
            "id": str(article.id),
            "rss_source_id": str(article.rss_source_id),
            "title": article.title,
            "url": article.url,
            "description": article.description,
            "author": article.author,
            "thumbnail_url": article.thumbnail_url,
            "category": article.category,
            "published_date": article.published_date,
            "created_at": article.created_at,
            "vote_score": article.vote_score,
            "vote_count": article.vote_count,
            "comment_count": article.comment_count,
            "tags": article.tags or [],
            "user_vote": getattr(article, "user_vote", None),  # Include if authenticated
        }
        for article in articles
    ]

    # Return response with metadata
    return {"articles": articles_data, **metadata}


# IMPORTANT: Search endpoint must come BEFORE /{article_id} to avoid route conflicts
@router.get("/search", status_code=status.HTTP_200_OK)
async def search_articles(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Search articles using full-text search.

    **Query Parameters**:
    - **q**: Search query (1-200 characters) - required
    - **page**: Page number (1-indexed) - default: 1
    - **page_size**: Items per page (1-100) - default: 25

    **Search Algorithm**:
    - Searches through article titles and descriptions
    - Uses PostgreSQL full-text search (TSVECTOR)
    - Results ordered by relevance and recency

    **Returns**:
    - List of matching articles with pagination metadata

    **Example**:
    ```
    GET /api/v1/articles/search?q=artificial+intelligence&page=1
    ```
    """
    # Call service layer
    articles, metadata = await article_service.search_articles(
        query=q, page=page, page_size=page_size
    )

    # Convert articles to response format
    articles_data = [
        {
            "id": str(article.id),
            "rss_source_id": str(article.rss_source_id),
            "title": article.title,
            "url": article.url,
            "description": article.description,
            "author": article.author,
            "thumbnail_url": article.thumbnail_url,
            "category": article.category,
            "published_date": article.published_date,
            "created_at": article.created_at,
            "vote_score": article.vote_score,
            "vote_count": article.vote_count,
            "comment_count": article.comment_count,
            "tags": article.tags or [],
            "user_vote": None,  # Search doesn't include user votes
        }
        for article in articles
    ]

    # Return response with metadata
    return {"articles": articles_data, **metadata}


# Dynamic route must come LAST to avoid conflicts
@router.get("/{article_id}", response_model=ArticleResponse, status_code=status.HTTP_200_OK)
async def get_article(
    article_id: UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Get a single article by ID.

    **Path Parameters**:
    - **article_id**: UUID of the article

    **Returns**:
    - Article details with vote counts and comment counts
    - Includes user's vote status if authenticated

    **Raises**:
    - **404**: Article not found

    **Example**:
    ```
    GET /api/v1/articles/550e8400-e29b-41d4-a716-446655440000
    ```
    """
    # Get user ID if authenticated
    user_id = current_user.id if current_user else None

    # Call service layer
    article = await article_service.get_article_by_id(article_id=article_id, user_id=user_id)

    # Convert to response format
    return ArticleResponse(
        id=article.id,
        rss_source_id=article.rss_source_id,
        title=article.title,
        url=article.url,
        description=article.description,
        author=article.author,
        thumbnail_url=article.thumbnail_url,
        category=article.category,
        published_date=article.published_date,
        created_at=article.created_at,
        vote_score=article.vote_score,
        vote_count=article.vote_count,
        comment_count=article.comment_count,
        tags=article.tags or [],
        user_vote=getattr(article, "user_vote", None),
    )
