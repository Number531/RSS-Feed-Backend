"""
RSS Source schemas for API validation.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl, ConfigDict


class RSSSourceBase(BaseModel):
    """Base RSS source schema."""
    name: str = Field(..., min_length=1, max_length=255)
    url: HttpUrl
    category: str = Field(..., pattern="^(general|politics|us|world|science)$")
    is_active: bool = True


class RSSSourceCreate(RSSSourceBase):
    """Schema for creating RSS source."""
    pass


class RSSSourceUpdate(BaseModel):
    """Schema for updating RSS source."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[HttpUrl] = None
    category: Optional[str] = Field(None, pattern="^(general|politics|us|world|science)$")
    is_active: Optional[bool] = None


class RSSSourceResponse(RSSSourceBase):
    """Schema for RSS source response."""
    id: UUID
    last_fetched: Optional[datetime]
    last_successful_fetch: Optional[datetime]
    fetch_success_count: int
    fetch_failure_count: int
    consecutive_failures: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
