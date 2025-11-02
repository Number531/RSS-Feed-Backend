"""User Feed Subscription model for managing user RSS feed subscriptions."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class UserFeedSubscription(Base):
    """User subscription to RSS feeds."""

    __tablename__ = "user_feed_subscriptions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    feed_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rss_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Subscription settings
    is_active = Column(Boolean, default=True, nullable=False)
    notifications_enabled = Column(Boolean, default=True, nullable=False)

    # Timestamps
    subscribed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", backref="feed_subscriptions")
    feed = relationship("RSSSource", backref="user_subscriptions")

    # Constraints - one subscription per user per feed
    __table_args__ = (UniqueConstraint("user_id", "feed_id", name="unique_user_feed_subscription"),)

    def __repr__(self):
        return f"<UserFeedSubscription(user_id={self.user_id}, feed_id={self.feed_id}, active={self.is_active})>"
