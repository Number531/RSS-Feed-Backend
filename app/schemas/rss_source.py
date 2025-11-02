"""RSS Source schemas for API validation."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class RSSSourceBase(BaseModel):
    """Base RSS source schema."""

    name: str = Field(..., min_length=1, max_length=255, description="Display name of the feed")
    url: HttpUrl = Field(..., description="RSS feed URL")
    source_name: str = Field(
        ..., min_length=1, max_length=100, description="Source organization (e.g., 'CNN', 'BBC')"
    )
    category: str = Field(
        ...,
        pattern="^(general|politics|us|world|science|technology|business|entertainment|sports|health)$",
        description="Feed category",
    )
    is_active: bool = Field(default=True, description="Whether the feed is active")


class RSSSourceCreate(RSSSourceBase):
    """Schema for creating RSS source (admin only)."""

    pass


class RSSSourceUpdate(BaseModel):
    """Schema for updating RSS source (admin only)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[HttpUrl] = None
    source_name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(
        None,
        pattern="^(general|politics|us|world|science|technology|business|entertainment|sports|health)$",
    )
    is_active: Optional[bool] = None


class RSSSourceResponse(RSSSourceBase):
    """Schema for RSS source response."""

    id: UUID
    last_fetched: Optional[datetime] = None
    last_successful_fetch: Optional[datetime] = None
    fetch_success_count: int
    fetch_failure_count: int
    consecutive_failures: int
    success_rate: float = Field(..., description="Feed success rate as percentage")
    is_healthy: bool = Field(..., description="Whether the feed is healthy")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RSSSourceListResponse(BaseModel):
    """Schema for paginated list of RSS sources."""

    sources: List[RSSSourceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class RSSCategoryResponse(BaseModel):
    """Schema for RSS category information."""

    category: str
    count: int
    active_count: int
