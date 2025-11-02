"""
Notification models for user interaction notifications.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class Notification(Base):
    """User notification for votes, replies, and mentions."""

    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Notification type: 'vote', 'reply', 'mention'
    type = Column(String(50), nullable=False, index=True)

    # Human-readable notification content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Optional reference to related entity (article, comment, etc.)
    related_entity_type = Column(String(50), nullable=True)  # 'article', 'comment'
    related_entity_id = Column(UUID(as_uuid=True), nullable=True)

    # User who triggered the notification (nullable for system notifications)
    actor_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Read status
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="notifications")
    actor = relationship("User", foreign_keys=[actor_id])


class UserNotificationPreference(Base):
    """User preferences for notification types."""

    __tablename__ = "user_notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Notification type toggles
    vote_notifications = Column(Boolean, default=True, nullable=False)
    reply_notifications = Column(Boolean, default=True, nullable=False)
    mention_notifications = Column(Boolean, default=True, nullable=False)

    # Email notification toggle (for future email integration)
    email_notifications = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="notification_preferences")
