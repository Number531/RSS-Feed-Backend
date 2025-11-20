"""
Synthesis mode schemas for API validation.
Provides optimized endpoints for synthesis article display.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SynthesisListItem(BaseModel):
    """Schema for synthesis article in list view (optimized payload)."""
    
    id: str = Field(..., description="Article UUID as string")
    title: str = Field(..., min_length=1)
    synthesis_preview: Optional[str] = Field(None, description="First ~500 chars of synthesis")
    fact_check_verdict: Optional[str] = Field(None, description="TRUE, MOSTLY TRUE, MIXED, etc.")
    verdict_color: Optional[str] = Field(None, description="green, lime, yellow, orange, red, gray")
    fact_check_score: Optional[int] = Field(None, ge=0, le=100, description="Credibility score 0-100")
    synthesis_read_minutes: Optional[int] = Field(None, ge=0, description="Estimated read time")
    published_date: Optional[datetime] = Field(None, description="Original article publish date")
    source_name: str = Field(..., description="RSS source name from join")
    category: str = Field(..., description="Article category")
    has_timeline: bool = Field(default=False, description="Has event timeline")
    has_context_emphasis: bool = Field(default=False, description="Has context/emphasis notes")
    
    model_config = ConfigDict(from_attributes=True)


class SynthesisListResponse(BaseModel):
    """Paginated response for synthesis article list."""
    
    items: List[SynthesisListItem] = Field(default_factory=list)
    total: int = Field(..., ge=0, description="Total synthesis articles matching filter")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    has_next: bool = Field(..., description="Whether more pages exist")


class SynthesisDetailArticle(BaseModel):
    """Complete synthesis article with full content and metadata."""
    
    # Core article fields
    id: str = Field(..., description="Article UUID as string")
    title: str = Field(..., min_length=1)
    content: Optional[str] = Field(None, description="Original article content")
    synthesis_article: Optional[str] = Field(None, description="Full markdown synthesis (1,400-2,500 words)")
    
    # Fact check fields
    fact_check_verdict: Optional[str] = Field(None, description="TRUE, MOSTLY TRUE, MIXED, etc.")
    verdict_color: Optional[str] = Field(None, description="green, lime, yellow, orange, red, gray")
    fact_check_score: Optional[int] = Field(None, ge=0, le=100, description="Credibility score 0-100")
    
    # Synthesis metadata
    synthesis_word_count: Optional[int] = Field(None, ge=0)
    synthesis_read_minutes: Optional[int] = Field(None, ge=0)
    
    # Article metadata
    published_date: Optional[datetime] = Field(None, description="Original publish date")
    author: Optional[str] = Field(None, max_length=255)
    source_name: str = Field(..., description="RSS source name from join")
    category: str = Field(..., description="Article category")
    url: str = Field(..., description="Original article URL")
    
    # Feature flags
    has_timeline: bool = Field(default=False)
    has_context_emphasis: bool = Field(default=False)
    
    # Enrichment counts
    timeline_event_count: Optional[int] = Field(None, ge=0)
    reference_count: Optional[int] = Field(None, ge=0)
    margin_note_count: Optional[int] = Field(None, ge=0)
    
    # Processing metadata
    fact_check_mode: Optional[str] = Field(None, description="synthesis, standard, or NULL")
    fact_check_processing_time: Optional[int] = Field(None, ge=0, description="Processing time in seconds")
    synthesis_generated_at: Optional[datetime] = Field(None, description="When synthesis was generated")
    
    # JSONB extracted arrays
    references: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Citations from article_data JSONB"
    )
    event_timeline: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Timeline events from article_data JSONB"
    )
    margin_notes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Margin annotations from article_data JSONB"
    )
    context_and_emphasis: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Context items from article_data JSONB"
    )
    
    model_config = ConfigDict(from_attributes=True)


class SynthesisDetailResponse(BaseModel):
    """Response wrapper for synthesis detail endpoint."""
    
    article: SynthesisDetailArticle


class SynthesisStatsResponse(BaseModel):
    """Aggregate statistics for synthesis articles."""
    
    total_synthesis_articles: int = Field(..., ge=0, description="Total articles with synthesis")
    articles_with_timeline: int = Field(..., ge=0, description="Articles with event timeline")
    articles_with_context: int = Field(..., ge=0, description="Articles with context emphasis")
    average_credibility: float = Field(..., ge=0.0, le=1.0, description="Average fact_check_score / 100")
    verdict_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Count by fact_check_verdict (TRUE, MOSTLY TRUE, etc.)"
    )
    average_word_count: int = Field(..., ge=0, description="Average synthesis_word_count")
    average_read_minutes: int = Field(..., ge=0, description="Average synthesis_read_minutes")
