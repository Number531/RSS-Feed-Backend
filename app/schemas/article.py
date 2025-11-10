"""
Article schemas for API validation.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ArticleBase(BaseModel):
    """Base article schema."""

    title: str = Field(..., min_length=1, max_length=500)
    url: str = Field(..., pattern=r"^https?://")
    description: Optional[str] = Field(None, max_length=1000)
    author: Optional[str] = Field(None, max_length=255)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    category: str = Field(..., pattern="^(general|politics|us|world|science)$")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class ArticleCreate(ArticleBase):
    """Schema for creating articles (internal use)."""

    rss_source_id: UUID
    content: Optional[str] = None
    published_date: Optional[datetime] = None
    tags: Optional[List[str]] = None


class ArticleResponse(ArticleBase):
    """Schema for article response."""

    id: UUID
    rss_source_id: UUID
    published_date: Optional[datetime]
    created_at: datetime
    vote_score: int = 0  # Net vote score (upvotes - downvotes)
    vote_count: int = 0  # Total vote count
    comment_count: int = 0
    tags: List[str] = []

    # User interaction (if authenticated)
    user_vote: Optional[int] = None  # -1, 0, or 1

    # Full article content (from Railway API)
    crawled_content: Optional[str] = None  # Raw scraped content
    article_text: Optional[str] = None  # Clean Railway-generated content

    model_config = ConfigDict(from_attributes=True)


class ArticleList(BaseModel):
    """Schema for paginated article list."""

    items: List[ArticleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ArticleFeed(BaseModel):
    """Schema for article feed query parameters."""

    category: Optional[str] = Field(None, pattern="^(general|politics|us|world|science)$")
    sort_by: str = Field("hot", pattern="^(hot|new|top)$")
    time_range: Optional[str] = Field(None, pattern="^(hour|day|week|month|year|all)$")
    page: int = Field(1, ge=1)
    page_size: int = Field(25, ge=1, le=100)
    search: Optional[str] = Field(None, max_length=200)
