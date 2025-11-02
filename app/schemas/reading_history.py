"""Pydantic schemas for reading history API."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ReadingHistoryBase(BaseModel):
    """Base schema for reading history."""

    duration_seconds: Optional[int] = Field(None, ge=0, description="Reading duration in seconds")
    scroll_percentage: Optional[float] = Field(
        None, ge=0, le=100, description="Scroll depth percentage (0-100)"
    )


class ReadingHistoryCreate(ReadingHistoryBase):
    """Schema for creating a reading history entry."""

    article_id: str = Field(..., description="ID of the article being viewed")


class ReadingHistoryResponse(ReadingHistoryBase):
    """Schema for reading history response."""

    id: str
    user_id: str
    article_id: str
    viewed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReadingHistoryWithArticle(ReadingHistoryResponse):
    """Schema for reading history with article details."""

    article_title: Optional[str] = None
    article_url: Optional[str] = None
    article_published_at: Optional[datetime] = None

    @classmethod
    def from_orm_with_article(cls, history):
        """Create from ORM model with article details."""
        data = {
            "id": str(history.id),
            "user_id": str(history.user_id),
            "article_id": str(history.article_id),
            "viewed_at": history.viewed_at,
            "duration_seconds": history.duration_seconds,
            "scroll_percentage": history.scroll_percentage,
        }

        if history.article:
            data.update(
                {
                    "article_title": history.article.title,
                    "article_url": history.article.url,
                    "article_published_at": history.article.published_date,
                }
            )

        return cls(**data)


class ReadingHistoryList(BaseModel):
    """Schema for paginated reading history list."""

    items: list[ReadingHistoryWithArticle]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(from_attributes=True)


class ReadingStatsResponse(BaseModel):
    """Schema for reading statistics response."""

    total_views: int = Field(..., description="Total number of article views")
    total_reading_time_seconds: int = Field(..., description="Total reading time in seconds")
    average_reading_time_seconds: float = Field(..., description="Average reading time per article")
    period_start: Optional[datetime] = Field(None, description="Start of statistics period")
    period_end: Optional[datetime] = Field(None, description="End of statistics period")


class ClearHistoryRequest(BaseModel):
    """Schema for clear history request."""

    before_date: Optional[datetime] = Field(None, description="Only clear history before this date")


class ClearHistoryResponse(BaseModel):
    """Schema for clear history response."""

    deleted_count: int = Field(..., description="Number of history records deleted")
    message: str = Field(..., description="Success message")


class ExportFormat(str, Enum):
    """Export format options."""

    JSON = "json"
    CSV = "csv"


class ExportHistoryRequest(BaseModel):
    """Schema for history export request."""

    format: ExportFormat = Field(ExportFormat.JSON, description="Export format")
    start_date: Optional[datetime] = Field(None, description="Start date for export range")
    end_date: Optional[datetime] = Field(None, description="End date for export range")
    include_articles: bool = Field(True, description="Include full article details")


class ExportHistoryResponse(BaseModel):
    """Schema for export response."""

    export_format: str
    records_count: int
    file_name: str
    generated_at: datetime
    file_content: Optional[str] = None  # For small exports
    download_url: Optional[str] = None  # For large exports

    # Pydantic V2 handles datetime serialization automatically
