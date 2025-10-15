"""
Search schemas for API validation.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class SearchQuery(BaseModel):
    """Schema for search query parameters."""
    q: str = Field(..., min_length=1, max_length=200, description="Search query")
    category: Optional[str] = Field(None, pattern="^(general|politics|us|world|science|technology|business|entertainment|sports|health)$")
    source: Optional[str] = Field(None, max_length=100, description="Filter by source name")
    date_from: Optional[datetime] = Field(None, description="Filter articles from this date")
    date_to: Optional[datetime] = Field(None, description="Filter articles to this date")
    sort_by: str = Field("relevance", pattern="^(relevance|date|votes)$", description="Sort by relevance, date, or votes")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")


class SearchResult(BaseModel):
    """Schema for a single search result."""
    id: UUID
    title: str
    url: str
    description: Optional[str]
    author: Optional[str]
    published_date: Optional[datetime]
    category: str
    source_name: str
    vote_score: int
    comment_count: int
    created_at: datetime
    
    # Highlight matched text (optional)
    match_snippet: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class SearchResponse(BaseModel):
    """Schema for search response."""
    results: List[SearchResult]
    total: int
    page: int
    page_size: int
    total_pages: int
    query: str
    execution_time_ms: Optional[float] = None


class TrendingArticleResponse(BaseModel):
    """Schema for trending article response."""
    id: UUID
    title: str
    url: str
    description: Optional[str]
    category: str
    source_name: str
    vote_score: int
    comment_count: int
    published_date: Optional[datetime]
    created_at: datetime
    
    # Trending metrics
    vote_velocity: float = Field(..., description="Votes per hour")
    engagement_score: float = Field(..., description="Combined engagement metric")
    
    model_config = ConfigDict(from_attributes=True)


class TrendingResponse(BaseModel):
    """Schema for trending articles response."""
    articles: List[TrendingArticleResponse]
    total: int
    period: str = Field(..., description="Time period (24h, 7d, 30d)")
