"""
Synthesis mode API endpoints.
Provides optimized endpoints for displaying synthesis articles.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.schemas.synthesis import (
    SynthesisDetailResponse,
    SynthesisListResponse,
    SynthesisStatsResponse,
)
from app.services.synthesis_service import SynthesisService

router = APIRouter()


@router.get(
    "/synthesis",
    response_model=SynthesisListResponse,
    summary="List synthesis articles",
    description="Get paginated list of articles with synthesis mode content. Optimized payload for list views.",
    response_description="Paginated list of synthesis articles with preview data",
)
async def list_synthesis_articles(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    verdict: Optional[str] = Query(
        None,
        description="Filter by fact check verdict (TRUE, MOSTLY TRUE, MIXED, MOSTLY FALSE, FALSE)",
    ),
    sort_by: str = Query(
        "newest",
        regex="^(newest|oldest|credibility)$",
        description="Sort order: newest (default), oldest, or credibility (by score desc)",
    ),
    db: AsyncSession = Depends(get_db),
) -> SynthesisListResponse:
    """
    List synthesis articles with pagination and filtering.
    
    **Features:**
    - Paginated results (default: 20 per page, max: 100)
    - Filter by fact check verdict
    - Sort by date or credibility score
    - Optimized payload (95% smaller than full article)
    
    **Use case:** Display synthesis articles in feed/list view
    """
    service = SynthesisService(db)
    result = await service.list_synthesis_articles(
        page=page,
        page_size=page_size,
        verdict=verdict,
        sort_by=sort_by,
    )
    
    return SynthesisListResponse(**result)


@router.get(
    "/{article_id}/synthesis",
    response_model=SynthesisDetailResponse,
    summary="Get synthesis article details",
    description="Get complete synthesis article with full markdown content and extracted JSONB arrays.",
    response_description="Full synthesis article details",
    responses={
        404: {
            "description": "Synthesis article not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Synthesis article not found"}
                }
            },
        }
    },
)
async def get_synthesis_article(
    article_id: str,
    db: AsyncSession = Depends(get_db),
) -> SynthesisDetailResponse:
    """
    Get a single synthesis article with complete details.
    
    **Includes:**
    - Full markdown synthesis article (1,400-2,500 words)
    - Original article content
    - Fact check verdict and credibility score
    - Extracted JSONB arrays:
      - References (citations with credibility ratings)
      - Event timeline (chronological events)
      - Margin notes (contextual annotations)
      - Context and emphasis (important context items)
    
    **Use case:** Display full synthesis article in reader view
    """
    service = SynthesisService(db)
    article = await service.get_synthesis_article(article_id)
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Synthesis article not found",
        )
    
    return SynthesisDetailResponse(article=article)


@router.get(
    "/synthesis/stats",
    response_model=SynthesisStatsResponse,
    summary="Get synthesis statistics",
    description="Get aggregate statistics for all synthesis articles.",
    response_description="Synthesis article statistics",
)
async def get_synthesis_stats(
    db: AsyncSession = Depends(get_db),
) -> SynthesisStatsResponse:
    """
    Get aggregate statistics for synthesis articles.
    
    **Metrics:**
    - Total synthesis articles count
    - Articles with timeline features
    - Articles with context emphasis
    - Average credibility score (0-1 range)
    - Verdict distribution (count by verdict type)
    - Average word count
    - Average estimated read time
    
    **Use case:** Display synthesis mode analytics dashboard
    """
    service = SynthesisService(db)
    stats = await service.get_synthesis_stats()
    
    return SynthesisStatsResponse(**stats)
