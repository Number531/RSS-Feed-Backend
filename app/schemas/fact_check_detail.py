"""
Detailed fact-check schemas for granular claim inspection.

These schemas expose the full iterative mode output including:
- Individual source references
- Evidence quotes and context
- Citation IDs for traceability
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SourceReference(BaseModel):
    """Individual source citation with credibility metadata."""

    citation_id: int = Field(..., description="Unique citation identifier")
    title: str = Field(..., description="Source article/document title")
    url: str = Field(..., description="Direct URL to source")
    source: str = Field(..., description="Source name (e.g., 'Reuters', 'AP News')")
    credibility: str = Field(..., description="Source credibility rating (HIGH, MEDIUM, LOW)")
    relevance_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Relevance to claim (0.0-1.0)"
    )
    published_date: Optional[str] = Field(None, description="Source publication date")
    
    class Config:
        json_schema_extra = {
            "example": {
                "citation_id": 1,
                "title": "Judge orders Trump admin to restore SNAP funding",
                "url": "https://apnews.com/article/snap-funding-court-order",
                "source": "AP News",
                "credibility": "HIGH",
                "relevance_score": 0.95,
                "published_date": "2025-11-06"
            }
        }


class KeyEvidence(BaseModel):
    """Categorized evidence quotes supporting claim analysis."""

    supporting: List[str] = Field(
        default_factory=list, description="Evidence supporting the claim"
    )
    contradicting: List[str] = Field(
        default_factory=list, description="Evidence contradicting the claim"
    )
    context: List[str] = Field(
        default_factory=list, description="Additional context and background"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "supporting": [
                    "Court order dated November 6, 2025 explicitly requires full SNAP funding by November 7",
                    "Judge John McConnell's ruling cited administration's failure to comply with federal law"
                ],
                "contradicting": [],
                "context": [
                    "SNAP provides food assistance to over 40 million Americans",
                    "Previous administration had attempted to reduce SNAP funding through regulatory changes"
                ]
            }
        }


class ClaimAnalysis(BaseModel):
    """Complete analysis for a single claim with all evidence."""

    # Claim identification
    claim_text: str = Field(..., description="Original claim statement")
    claim_index: int = Field(..., ge=0, description="Zero-based index in article")
    category: str = Field(..., description="Claim category (e.g., 'Iterative Claim')")
    risk_level: str = Field(..., description="Risk level (HIGH, MEDIUM, LOW)")
    
    # Validation results
    verdict: str = Field(..., description="Claim verdict (TRUE, FALSE, MOSTLY TRUE, etc.)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence (0.0-1.0)")
    summary: str = Field(..., description="Detailed analysis summary")
    
    # Evidence details
    key_evidence: Optional[KeyEvidence] = Field(
        None, description="Categorized evidence quotes"
    )
    references: List[SourceReference] = Field(
        default_factory=list, description="Source citations"
    )
    
    # Evidence metrics
    evidence_count: int = Field(..., description="Total evidence items consulted")
    evidence_breakdown: Dict[str, int] = Field(
        ..., description="Evidence by type (news, research, historical, etc.)"
    )
    validation_mode: str = Field(..., description="Validation mode (summary, thorough, etc.)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "claim_text": "U.S. District Judge ordered Trump admin to fund SNAP by Friday",
                "claim_index": 0,
                "category": "Iterative Claim",
                "risk_level": "HIGH",
                "verdict": "MOSTLY TRUE",
                "confidence": 0.9,
                "summary": "The claim is largely accurate. Judge John McConnell...",
                "key_evidence": {
                    "supporting": ["Court order evidence..."],
                    "contradicting": [],
                    "context": ["SNAP background..."]
                },
                "references": [
                    {
                        "citation_id": 1,
                        "title": "Judge orders SNAP funding",
                        "url": "https://apnews.com/...",
                        "source": "AP News",
                        "credibility": "HIGH",
                        "relevance_score": 0.95
                    }
                ],
                "evidence_count": 35,
                "evidence_breakdown": {
                    "news": 10,
                    "general": 10,
                    "research": 10,
                    "historical": 5
                },
                "validation_mode": "thorough"
            }
        }


class DetailedFactCheckResponse(BaseModel):
    """Complete fact-check with all claims, evidence, and sources."""

    # Basic info
    id: UUID
    article_id: UUID
    job_id: str
    
    # Overall results
    verdict: str = Field(..., description="Overall article verdict")
    credibility_score: int = Field(..., ge=0, le=100)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    summary: str
    
    # Claim statistics
    claims_analyzed: Optional[int] = None
    claims_validated: Optional[int] = None
    claims_true: Optional[int] = None
    claims_false: Optional[int] = None
    claims_misleading: Optional[int] = None
    claims_unverified: Optional[int] = None
    
    # Detailed claims
    claims: List[ClaimAnalysis] = Field(
        ..., description="Detailed analysis for each claim"
    )
    
    # Overall evidence metrics
    total_sources: int = Field(..., description="Total unique sources consulted")
    source_consensus: Optional[str] = None
    validation_mode: Optional[str] = None
    
    # Processing metadata
    processing_time_seconds: Optional[int] = None
    api_costs: Optional[Dict[str, Any]] = None
    fact_checked_at: str
    
    class Config:
        from_attributes = True


class ClaimListResponse(BaseModel):
    """List of claims with basic info (without full evidence)."""

    article_id: UUID
    total_claims: int
    claims: List[Dict[str, Any]] = Field(
        ..., description="Simplified claim summaries"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "article_id": "650e8400-e29b-41d4-a716-446655440001",
                "total_claims": 4,
                "claims": [
                    {
                        "claim_index": 0,
                        "claim_text": "Judge ordered SNAP funding...",
                        "verdict": "MOSTLY TRUE",
                        "confidence": 0.9,
                        "evidence_count": 35
                    }
                ]
            }
        }
