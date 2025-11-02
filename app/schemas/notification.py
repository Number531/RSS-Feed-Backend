"""
Pydantic schemas for notification request/response validation.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# Notification Schemas
# ============================================================================


class NotificationBase(BaseModel):
    """Base schema for notification data."""

    type: str = Field(..., description="Notification type: 'vote', 'reply', 'mention'")
    title: str = Field(..., max_length=255, description="Notification title")
    message: str = Field(..., description="Notification message")
    related_entity_type: Optional[str] = Field(
        None, description="Type of related entity: 'article', 'comment'"
    )
    related_entity_id: Optional[UUID] = Field(None, description="ID of related entity")


class NotificationCreate(NotificationBase):
    """Schema for creating a new notification."""

    user_id: UUID = Field(..., description="ID of user to notify")
    actor_id: Optional[UUID] = Field(None, description="ID of user who triggered the notification")


class NotificationResponse(NotificationBase):
    """Schema for notification response."""

    id: UUID = Field(..., description="Notification ID")
    user_id: UUID = Field(..., description="User ID")
    actor_id: Optional[UUID] = Field(None, description="Actor user ID")
    is_read: bool = Field(..., description="Whether notification has been read")
    read_at: Optional[datetime] = Field(None, description="When notification was read")
    created_at: datetime = Field(..., description="When notification was created")

    # Optional actor information for display
    actor_username: Optional[str] = Field(None, description="Username of actor")

    model_config = ConfigDict(from_attributes=True)


class NotificationList(BaseModel):
    """Schema for paginated list of notifications."""

    notifications: List[NotificationResponse] = Field(..., description="List of notifications")
    total: int = Field(..., description="Total count of notifications")
    unread_count: int = Field(..., description="Count of unread notifications")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Number of items per page")

    model_config = ConfigDict(from_attributes=True)


class NotificationMarkRead(BaseModel):
    """Schema for marking notification(s) as read."""

    notification_ids: List[UUID] = Field(
        ..., description="List of notification IDs to mark as read"
    )


class NotificationMarkReadResponse(BaseModel):
    """Schema for mark read response."""

    marked_count: int = Field(..., description="Number of notifications marked as read")
    message: str = Field(..., description="Success message")


# ============================================================================
# Notification Preference Schemas
# ============================================================================


class NotificationPreferenceBase(BaseModel):
    """Base schema for notification preferences."""

    vote_notifications: bool = Field(True, description="Enable vote notifications")
    reply_notifications: bool = Field(True, description="Enable reply notifications")
    mention_notifications: bool = Field(True, description="Enable mention notifications")
    email_notifications: bool = Field(False, description="Enable email notifications")


class NotificationPreferenceCreate(NotificationPreferenceBase):
    """Schema for creating notification preferences."""

    user_id: UUID = Field(..., description="User ID")


class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating notification preferences."""

    vote_notifications: Optional[bool] = Field(None, description="Enable vote notifications")
    reply_notifications: Optional[bool] = Field(None, description="Enable reply notifications")
    mention_notifications: Optional[bool] = Field(None, description="Enable mention notifications")
    email_notifications: Optional[bool] = Field(None, description="Enable email notifications")


class NotificationPreferenceResponse(NotificationPreferenceBase):
    """Schema for notification preference response."""

    id: UUID = Field(..., description="Preference ID")
    user_id: UUID = Field(..., description="User ID")
    created_at: datetime = Field(..., description="When preferences were created")
    updated_at: datetime = Field(..., description="When preferences were last updated")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Statistics Schemas
# ============================================================================


class NotificationStats(BaseModel):
    """Schema for notification statistics."""

    total_notifications: int = Field(..., description="Total number of notifications")
    unread_count: int = Field(..., description="Number of unread notifications")
    vote_count: int = Field(0, description="Number of vote notifications")
    reply_count: int = Field(0, description="Number of reply notifications")
    mention_count: int = Field(0, description="Number of mention notifications")

    model_config = ConfigDict(from_attributes=True)
