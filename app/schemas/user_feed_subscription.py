"""Schemas for User Feed Subscriptions."""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

if TYPE_CHECKING:
    from app.schemas.rss_source import RSSSourceResponse


class SubscriptionBase(BaseModel):
    """Base subscription schema."""
    notifications_enabled: bool = Field(default=True, description="Enable notifications for this feed")


class SubscriptionCreate(SubscriptionBase):
    """Schema for subscribing to a feed."""
    pass


class SubscriptionUpdate(BaseModel):
    """Schema for updating subscription preferences."""
    is_active: Optional[bool] = Field(None, description="Whether the subscription is active")
    notifications_enabled: Optional[bool] = Field(None, description="Enable/disable notifications")


class SubscriptionResponse(SubscriptionBase):
    """Schema for subscription response."""
    id: UUID
    user_id: UUID
    feed_id: UUID
    is_active: bool
    subscribed_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SubscriptionWithFeedResponse(SubscriptionResponse):
    """Schema for subscription with feed details."""
    feed: "RSSSourceResponse"
    
    model_config = ConfigDict(from_attributes=True)


class SubscriptionsListResponse(BaseModel):
    """Schema for list of subscriptions."""
    subscriptions: List[SubscriptionWithFeedResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Resolve forward references
from app.schemas.rss_source import RSSSourceResponse
SubscriptionWithFeedResponse.model_rebuild()
