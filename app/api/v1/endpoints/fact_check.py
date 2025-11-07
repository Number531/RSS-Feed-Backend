"""
Fact-Check API endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.fact_check import ArticleFactCheck
from app.repositories.fact_check_repository import FactCheckRepository
from app.repositories.article_repository import ArticleRepository
from app.schemas.fact_check import FactCheckResponse
from app.schemas.fact_check_detail import (
    DetailedFactCheckResponse,
    ClaimAnalysis,
    ClaimListResponse,
    SourceReference,
    KeyEvidence,
)
from app.services.fact_check_service import FactCheckService

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
                                "context": ["Context 1"],
                            },
                            "references": [
                                {
                                    "citation_id": 1,
                                    "title": "Source Title",
                                    "url": "https://example.com",
                                    "source": "AP News",
                                    "credibility": "HIGH",
                                }
                            ],
                        },
                        "num_sources": 25,
                        "source_consensus": "STRONG_AGREEMENT",
                        "validation_mode": "summary",
                        "processing_time_seconds": 137,
                        "api_costs": {"total": 0.008},
                        "fact_checked_at": "2025-10-19T14:22:54Z",
                        "created_at": "2025-10-19T14:22:55Z",
                        "updated_at": "2025-10-19T14:22:55Z",
                    }
                }
            },
        },
        404: {
            "description": "Article or fact-check not found",
            "content": {
                "application/json": {
                    "examples": {
                        "article_not_found": {
                            "summary": "Article doesn't exist",
                            "value": {"detail": "Article not found"},
                        },
                        "no_fact_check": {
                            "summary": "No fact-check available",
                            "value": {"detail": "No fact-check found for this article"},
                        },
                    }
                }
            },
        },
    },
)
async def get_article_fact_check(
    article_id: UUID, db: AsyncSession = Depends(get_db)
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
        select(ArticleFactCheck).where(ArticleFactCheck.article_id == article_id)
    )
    fact_check = result.scalar_one_or_none()

    if not fact_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No fact-check found for this article"
        )

    # Handle both old and new validation_results formats
    # New format (iterative mode): list of claims
    # Old format (summary mode): dict with single claim
    validation_results = fact_check.validation_results
    if isinstance(validation_results, list):
        # Convert list format to dict format for API compatibility
        validation_results = {
            "claims": validation_results,
            "mode": "iterative",
            "total_claims": len(validation_results)
        }

    # Create response with normalized validation_results
    return FactCheckResponse(
        id=fact_check.id,
        article_id=fact_check.article_id,
        job_id=fact_check.job_id,
        verdict=fact_check.verdict,
        credibility_score=fact_check.credibility_score,
        confidence=fact_check.confidence,
        summary=fact_check.summary,
        claims_analyzed=fact_check.claims_analyzed,
        claims_validated=fact_check.claims_validated,
        claims_true=fact_check.claims_true,
        claims_false=fact_check.claims_false,
        claims_misleading=fact_check.claims_misleading,
        claims_unverified=fact_check.claims_unverified,
        validation_results=validation_results,
        num_sources=fact_check.num_sources,
        source_consensus=fact_check.source_consensus,
        validation_mode=fact_check.validation_mode,
        processing_time_seconds=fact_check.processing_time_seconds,
        api_costs=fact_check.api_costs,
        fact_checked_at=fact_check.fact_checked_at,
        created_at=fact_check.created_at,
        updated_at=fact_check.updated_at,
    )


@router.get(
    "/articles/{article_id}/fact-check/detailed",
    response_model=DetailedFactCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Get COMPLETE fact-check with all sources and evidence",
    description="""
    Retrieve the **complete** fact-check with EVERY detail from Railway API.
    
    This endpoint exposes ALL data that was NOT included in the summary endpoint:
    
    **What you get:**
    - ✅ Individual source references (title, URL, source name, credibility)
    - ✅ Evidence quotes (supporting, contradicting, context)
    - ✅ Citation IDs for traceability
    - ✅ Source relevance scores
    - ✅ Per-claim detailed analysis
    - ✅ Full validation results from Railway API
    
    **Performance note:** This endpoint returns cached data from the database,
    which includes all references and evidence from the original fact-check.
    
    **Typical use cases:**
    - Displaying full source list for transparency
    - Citation tracking and verification
    - Academic analysis requiring source metadata
    - Detailed evidence inspection
    """,
    responses={
        200: {
            "description": "Complete fact-check with all sources and evidence",
        },
        404: {
            "description": "Fact-check not found or Railway API job expired",
        },
        503: {
            "description": "Railway API unavailable",
        },
    },
)
async def get_detailed_fact_check(
    article_id: UUID, db: AsyncSession = Depends(get_db)
) -> DetailedFactCheckResponse:
    """
    Get complete fact-check with all sources and evidence from cached data.
    
    Args:
        article_id: UUID of the article
        db: Database session
        
    Returns:
        Complete fact-check with detailed claim analysis, sources, and evidence
        
    Raises:
        HTTPException: 404 if fact-check not found
    """
    # 1. Get basic fact-check record from database
    result = await db.execute(
        select(ArticleFactCheck).where(ArticleFactCheck.article_id == article_id)
    )
    fact_check = result.scalar_one_or_none()

    if not fact_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No fact-check found for this article",
        )

    # 2. Use cached validation_results from database (already contains references)
    validation_results = fact_check.validation_results
    
    # Handle both list and dict formats
    if isinstance(validation_results, list):
        claims_data = validation_results
    elif isinstance(validation_results, dict):
        claims_data = validation_results.get("claims", [])
    else:
        claims_data = []

    # 4. Build detailed claim analysis with all evidence
    detailed_claims = []
    for idx, claim_item in enumerate(claims_data):
        # Database format: claim_item contains both 'claim' dict and 'validation_result' dict
        claim = claim_item.get("claim", {})
        # Try both 'validation_result' and 'validation_output' (API may use either)
        validation_result = claim_item.get("validation_result", claim_item.get("validation_output", {}))

        # Extract references (sources)
        references = []
        for ref in validation_result.get("references", []):
            references.append(
                SourceReference(
                    citation_id=ref.get("citation_id"),
                    title=ref.get("title"),
                    url=ref.get("url"),
                    source=ref.get("source"),
                    credibility=ref.get("credibility"),
                    relevance_score=ref.get("relevance_score"),
                    published_date=ref.get("published_date"),
                )
            )

        # Extract key evidence
        evidence_data = validation_result.get("key_evidence", {})
        key_evidence = KeyEvidence(
            supporting=evidence_data.get("supporting", []),
            contradicting=evidence_data.get("contradicting", []),
            context=evidence_data.get("context", []),
        )

        # Build claim analysis
        claim_analysis = ClaimAnalysis(
            claim_text=claim.get("claim"),
            claim_index=idx,
            category=claim.get("category"),
            risk_level=claim.get("risk_level"),
            verdict=validation_result.get("verdict"),
            confidence=validation_result.get("confidence"),
            summary=validation_result.get("summary"),
            key_evidence=key_evidence,
            references=references,
            evidence_count=validation_result.get("evidence_count"),
            evidence_breakdown=validation_result.get("evidence_breakdown", {}),
            validation_mode=validation_result.get("validation_mode"),
        )
        detailed_claims.append(claim_analysis)

    # 5. Calculate total unique sources
    all_sources = set()
    for claim in detailed_claims:
        for ref in claim.references:
            all_sources.add(ref.url)

    # 6. Build complete response
    return DetailedFactCheckResponse(
        id=fact_check.id,
        article_id=fact_check.article_id,
        job_id=fact_check.job_id,
        verdict=fact_check.verdict,
        credibility_score=fact_check.credibility_score,
        confidence=fact_check.confidence,
        summary=fact_check.summary,
        claims_analyzed=fact_check.claims_analyzed,
        claims_validated=fact_check.claims_validated,
        claims_true=fact_check.claims_true,
        claims_false=fact_check.claims_false,
        claims_misleading=fact_check.claims_misleading,
        claims_unverified=fact_check.claims_unverified,
        claims=detailed_claims,
        total_sources=len(all_sources),
        source_consensus=fact_check.source_consensus,
        validation_mode=fact_check.validation_mode,
        processing_time_seconds=fact_check.processing_time_seconds,
        api_costs=fact_check.api_costs,
        fact_checked_at=fact_check.fact_checked_at.isoformat(),
    )


@router.get(
    "/articles/{article_id}/fact-check/claims",
    response_model=ClaimListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all claims in article (lightweight)",
    description="""
    Get a lightweight list of all claims analyzed in the article.
    
    This endpoint returns basic claim information WITHOUT fetching
    full evidence and sources. Use this for:
    - Overview of claims
    - Navigation UI
    - Quick claim count
    
    To get full details for a specific claim, use the detailed endpoint.
    """,
)
async def list_article_claims(
    article_id: UUID, db: AsyncSession = Depends(get_db)
) -> ClaimListResponse:
    """
    List all claims for an article with basic info.
    
    Args:
        article_id: UUID of the article
        db: Database session
        
    Returns:
        Simplified claim list with verdicts and evidence counts
    """
    result = await db.execute(
        select(ArticleFactCheck).where(ArticleFactCheck.article_id == article_id)
    )
    fact_check = result.scalar_one_or_none()

    if not fact_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No fact-check found for this article",
        )

    # Extract basic claim info from stored validation_results
    validation_results = fact_check.validation_results
    claims_data = []

    # Handle both storage formats (same normalization as standard endpoint)
    if isinstance(validation_results, list):
        # Raw Railway API format: validation_results is a list of claims
        claims_list = validation_results
    elif isinstance(validation_results, dict):
        # Normalized format: validation_results has 'claims' key
        claims_list = validation_results.get("claims", [])
    else:
        # Fallback for unexpected formats
        claims_list = []

    for idx, claim_item in enumerate(claims_list):
            claim = claim_item.get("claim", {})
            validation = claim_item.get("validation_result", {})

            claims_data.append(
                {
                    "claim_index": idx,
                    "claim_text": claim.get("claim"),
                    "category": claim.get("category"),
                    "risk_level": claim.get("risk_level"),
                    "verdict": validation.get("verdict"),
                    "confidence": validation.get("confidence"),
                    "evidence_count": validation.get("evidence_count"),
                }
            )

    return ClaimListResponse(
        article_id=article_id, total_claims=len(claims_data), claims=claims_data
    )
