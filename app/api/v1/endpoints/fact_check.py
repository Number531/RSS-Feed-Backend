"""
Fact-Check API endpoints.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.models.fact_check import FactCheck
from app.schemas.fact_check import FactCheckResponse
from sqlalchemy import select

router = APIRouter()


@router.get(
    "/articles/{article_id}/fact-check",
    response_model=FactCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Get fact-check details for an article",
    description="""
    Retrieve complete fact-check information for a specific article.
    
    Returns the full fact-check report including:
    - Verdict and credibility score
    - Detailed claim analysis
    - Supporting/contradicting evidence
    - Source references and citations
    - Processing metadata
    
    **Note:** Articles are fact-checked automatically upon creation.
    If no fact-check exists, the article may still be processing.
    """,
    responses={
        200: {
            "description": "Fact-check details retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "article_id": "650e8400-e29b-41d4-a716-446655440001",
                        "job_id": "9aa51885-c336-4de0-aa17-88a1944379c7",
                        "verdict": "TRUE",
                        "credibility_score": 87,
                        "confidence": 0.9,
                        "summary": "The UK announced its decision to cede sovereignty...",
                        "claims_analyzed": 1,
                        "claims_validated": 1,
                        "claims_true": 1,
                        "claims_false": 0,
                        "claims_misleading": 0,
                        "claims_unverified": 0,
                        "validation_results": {
                            "claim": "Full claim text...",
                            "verdict": "TRUE",
                            "confidence": 0.9,
                            "key_evidence": {
                                "supporting": ["Evidence 1", "Evidence 2"],
                                "contradicting": [],
                                "context": ["Context 1"]
                            },
                            "references": [
                                {
                                    "citation_id": 1,
                                    "title": "Source Title",
                                    "url": "https://example.com",
                                    "source": "AP News",
                                    "credibility": "HIGH"
                                }
                            ]
                        },
                        "num_sources": 25,
                        "source_consensus": "STRONG_AGREEMENT",
                        "validation_mode": "summary",
                        "processing_time_seconds": 137,
                        "api_costs": {"total": 0.008},
                        "fact_checked_at": "2025-10-19T14:22:54Z",
                        "created_at": "2025-10-19T14:22:55Z",
                        "updated_at": "2025-10-19T14:22:55Z"
                    }
                }
            }
        },
        404: {
            "description": "Article or fact-check not found",
            "content": {
                "application/json": {
                    "examples": {
                        "article_not_found": {
                            "summary": "Article doesn't exist",
                            "value": {"detail": "Article not found"}
                        },
                        "no_fact_check": {
                            "summary": "No fact-check available",
                            "value": {"detail": "No fact-check found for this article"}
                        }
                    }
                }
            }
        }
    }
)
async def get_article_fact_check(
    article_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> FactCheckResponse:
    """
    Get detailed fact-check information for an article.
    
    Args:
        article_id: UUID of the article
        db: Database session
        
    Returns:
        Complete fact-check details
        
    Raises:
        HTTPException: 404 if article or fact-check not found
    """
    # Query for fact-check by article_id
    result = await db.execute(
        select(FactCheck).where(FactCheck.article_id == article_id)
    )
    fact_check = result.scalar_one_or_none()
    
    if not fact_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No fact-check found for this article"
        )
    
    return fact_check
