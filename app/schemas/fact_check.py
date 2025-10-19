"""
Fact-Check schemas for API responses.
"""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class FactCheckResponse(BaseModel):
    """Complete fact-check details for an article."""
    
    # Basic info
    id: UUID
    article_id: UUID
    job_id: str
    
    # Core results
    verdict: str = Field(..., description="Primary verdict (TRUE, FALSE, MISLEADING, etc.)")
    credibility_score: int = Field(..., ge=0, le=100, description="Credibility score 0-100")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI confidence level 0.0-1.0")
    summary: str = Field(..., description="Brief summary of fact-check findings")
    
    # Claim statistics
    claims_analyzed: Optional[int] = Field(None, description="Total claims extracted")
    claims_validated: Optional[int] = Field(None, description="Claims that were validated")
    claims_true: Optional[int] = Field(None, description="Claims verified as true")
    claims_false: Optional[int] = Field(None, description="Claims verified as false")
    claims_misleading: Optional[int] = Field(None, description="Claims marked as misleading")
    claims_unverified: Optional[int] = Field(None, description="Claims that could not be verified")
    
    # Full validation data (JSONB)
    validation_results: Dict[str, Any] = Field(..., description="Complete API response with claims, evidence, references")
    
    # Evidence quality
    num_sources: Optional[int] = Field(None, description="Number of sources consulted")
    source_consensus: Optional[str] = Field(None, description="Source agreement level (STRONG_AGREEMENT, MIXED, etc.)")
    
    # Processing metadata
    validation_mode: Optional[str] = Field(None, description="Validation mode used (summary, standard, thorough)")
    processing_time_seconds: Optional[int] = Field(None, description="Time taken to complete fact-check")
    api_costs: Optional[Dict[str, Any]] = Field(None, description="API costs breakdown")
    
    # Timestamps
    fact_checked_at: datetime = Field(..., description="When fact-check completed")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "article_id": "650e8400-e29b-41d4-a716-446655440001",
                "job_id": "9aa51885-c336-4de0-aa17-88a1944379c7",
                "verdict": "TRUE",
                "credibility_score": 87,
                "confidence": 0.9,
                "summary": "The UK did announce its decision to cede sovereignty of the Chagos Islands to Mauritius on 3 October 2024...",
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
