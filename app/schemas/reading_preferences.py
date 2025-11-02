"""Schemas for user reading preferences."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReadingPreferencesBase(BaseModel):
    """Base schema for reading preferences."""

    tracking_enabled: bool = Field(True, description="Enable reading history tracking")
    analytics_opt_in: bool = Field(True, description="Opt-in to analytics")
    auto_cleanup_enabled: bool = Field(False, description="Enable automatic cleanup")
    retention_days: int = Field(365, ge=1, le=3650, description="Days to retain history (1-3650)")
    exclude_categories: List[str] = Field(
        default_factory=list, description="Categories to exclude from tracking"
    )


class ReadingPreferencesCreate(ReadingPreferencesBase):
    """Schema for creating preferences."""

    pass


class ReadingPreferencesUpdate(BaseModel):
    """Schema for updating preferences (all fields optional)."""

    tracking_enabled: Optional[bool] = None
    analytics_opt_in: Optional[bool] = None
    auto_cleanup_enabled: Optional[bool] = None
    retention_days: Optional[int] = Field(None, ge=1, le=3650)
    exclude_categories: Optional[List[str]] = None

    @field_validator("retention_days")
    @classmethod
    def validate_retention_days(cls, v):
        if v is not None and (v < 1 or v > 3650):
            raise ValueError("retention_days must be between 1 and 3650")
        return v


class ReadingPreferencesResponse(ReadingPreferencesBase):
    """Schema for reading preferences response."""

    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_preferences(cls, prefs):
        """Convert ORM model to response schema."""
        return cls(
            id=str(prefs.id),
            user_id=str(prefs.user_id),
            tracking_enabled=prefs.tracking_enabled,
            analytics_opt_in=prefs.analytics_opt_in,
            auto_cleanup_enabled=prefs.auto_cleanup_enabled,
            retention_days=prefs.retention_days,
            exclude_categories=prefs.exclude_categories or [],
            created_at=prefs.created_at,
            updated_at=prefs.updated_at,
        )
