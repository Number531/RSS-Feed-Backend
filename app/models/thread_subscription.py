"""Thread Subscription model for comment thread notifications."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class ThreadSubscription(Base):
    """User subscription to a comment thread for notifications."""

    __tablename__ = "thread_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    comment_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("comments.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    subscribed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_notified_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="thread_subscriptions")
    comment = relationship("Comment", back_populates="subscriptions")

    __table_args__ = (
        UniqueConstraint('user_id', 'comment_id', name='uq_user_comment_subscription'),
    )
