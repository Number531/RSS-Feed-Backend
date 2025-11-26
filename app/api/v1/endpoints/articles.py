"""
Articles API Endpoints

Provides endpoints for browsing, viewing, and searching articles from RSS feeds.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status

from app.api.dependencies import (
    get_article_service,
    get_comment_service,
    get_fact_check_service,
    get_vote_service,
)
from app.core.security import get_current_user_optional
from app.models.user import User
from app.schemas.article import ArticleResponse
from app.services.article_service import ArticleService
from app.services.comment_service import CommentService
from app.services.fact_check_service import FactCheckService
from app.services.vote_service import VoteService

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
async def get_articles_feed(
    response: Response,
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
            "has_synthesis": article.has_synthesis,  # Synthesis/fact-check availability
        }
        for article in articles
    ]

    # Set cache headers for browser/CDN caching
    # Cache for 1 minute for feed endpoints (frequently changing content)
    response.headers["Cache-Control"] = "public, max-age=60, s-maxage=60"

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
            "has_synthesis": article.has_synthesis,  # Synthesis/fact-check availability
        }
        for article in articles
    ]

    # Return response with metadata
    return {"articles": articles_data, **metadata}


# Combined endpoint must come BEFORE /{article_id} to avoid route conflicts
@router.get("/{article_id}/full", status_code=status.HTTP_200_OK)
async def get_article_full(
    article_id: UUID,
    request: Request,
    response: Response,
    current_user: Optional[User] = Depends(get_current_user_optional),
    article_service: ArticleService = Depends(get_article_service),
    comment_service: CommentService = Depends(get_comment_service),
    vote_service: VoteService = Depends(get_vote_service),
    fact_check_service: FactCheckService = Depends(get_fact_check_service),
):
    """
    Get a complete article package with all related data in one request.

    **Path Parameters**:
    - **article_id**: UUID of the article

    **Returns**:
    - Article details
    - User's vote status (if authenticated)
    - Top 10 comments
    - Fact-check data (if available)

    **Benefits**:
    - Reduces frontend latency by eliminating multiple round trips
    - Single request for article detail page
    - Optimized for mobile and high-latency connections

    **Raises**:
    - **404**: Article not found

    **Example**:
    ```
    GET /api/v1/articles/550e8400-e29b-41d4-a716-446655440000/full
    ```
    """
    # Get user ID if authenticated
    user_id = current_user.id if current_user else None

    # 1. Get article details
    article = await article_service.get_article_by_id(article_id=article_id, user_id=user_id)

    # Temporarily disable caching to ensure fresh fact-check data with validation_results
    # TODO: Re-enable with proper cache invalidation once frontend handles new data format
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    # 2. Get user vote (if authenticated)
    user_vote = None
    if user_id:
        try:
            vote = await vote_service.get_user_vote(user_id=user_id, article_id=article_id)
            user_vote = vote.vote_type if vote else None
        except Exception:
            # Non-critical, continue without vote
            pass

    # 3. Get top comments
    comments = []
    try:
        comments_list = await comment_service.get_article_comments(
            article_id=article_id, page=1, page_size=10
        )
        comments = [
            {
                "id": str(comment.id),
                "user_id": str(comment.user_id),
                "content": comment.content,
                "vote_score": comment.vote_score,
                "created_at": comment.created_at,
                "is_deleted": comment.is_deleted,
            }
            for comment in comments_list
        ]
    except Exception:
        # Non-critical, continue without comments
        pass

    # 4. Get fact-check data (if available)
    fact_check = None
    try:
        fact_check_data = await fact_check_service.fact_check_repo.get_by_article_id(
            article_id
        )
        if fact_check_data:
            # Handle both old and new validation_results formats
            validation_results = fact_check_data.validation_results
            if isinstance(validation_results, list):
                # Convert list format to dict format for API compatibility
                validation_results = {
                    "claims": validation_results,
                    "mode": "iterative",
                    "total_claims": len(validation_results)
                }
            fact_check = {
                "id": str(fact_check_data.id),
                "verdict": fact_check_data.verdict,
                "credibility_score": fact_check_data.credibility_score,
                "confidence": fact_check_data.confidence,
                "summary": fact_check_data.summary,
                "claims_analyzed": fact_check_data.claims_analyzed,
                "claims_true": fact_check_data.claims_true,
                "claims_false": fact_check_data.claims_false,
                "claims_misleading": fact_check_data.claims_misleading,
                "source_consensus": fact_check_data.source_consensus,
                "validation_mode": fact_check_data.validation_mode,
                "validation_results": validation_results,
            }
    except Exception:
        # Non-critical, continue without fact-check
        pass

    # Return combined response
    return {
        "article": {
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
            "has_synthesis": article.has_synthesis,
            "crawled_content": article.crawled_content,
            "article_data": article.article_data,
        },
        "user_vote": user_vote or getattr(article, "user_vote", None),
        "comments": comments,
        "fact_check": fact_check,
    }


# Dynamic route must come LAST to avoid conflicts
@router.get("/{article_id}", response_model=ArticleResponse, status_code=status.HTTP_200_OK)
async def get_article(
    article_id: UUID,
    request: Request,
    response: Response,
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

    # Generate ETag based on article updated timestamp
    # Use updated_at if available, fallback to created_at
    timestamp = getattr(article, "updated_at", article.created_at)
    etag = f'"{timestamp.timestamp()}"'

    # Check If-None-Match header for 304 Not Modified response
    if_none_match = request.headers.get("if-none-match")
    if if_none_match == etag:
        return Response(status_code=304)

    # Set cache headers
    response.headers["Cache-Control"] = "public, max-age=300, s-maxage=300"  # 5 minutes
    response.headers["ETag"] = etag

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
        has_synthesis=article.has_synthesis,
    )
