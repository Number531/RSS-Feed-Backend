"""Pydantic schemas for bookmarks."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.article import ArticleResponse


class BookmarkCreate(BaseModel):
    """Schema for creating a bookmark."""
    article_id: UUID = Field(..., description="ID of the article to bookmark")
    collection: Optional[str] = Field(None, max_length=100, description="Optional collection/folder name")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional notes about the bookmark")


class BookmarkUpdate(BaseModel):
    """Schema for updating a bookmark."""
    collection: Optional[str] = Field(None, max_length=100, description="Collection/folder name")
    notes: Optional[str] = Field(None, max_length=1000, description="Notes about the bookmark")


class BookmarkResponse(BaseModel):
    """Schema for bookmark response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    article_id: UUID
    collection: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    article: Optional[ArticleResponse] = None


class BookmarkListResponse(BaseModel):
    """Schema for paginated bookmark list."""
    items: list[BookmarkResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class BookmarkStatusResponse(BaseModel):
    """Schema for bookmark status check."""
    article_id: UUID
    is_bookmarked: bool


class CollectionListResponse(BaseModel):
    """Schema for collections list."""
    collections: list[str]
    total: int
