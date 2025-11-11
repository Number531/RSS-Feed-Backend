"""
Comment Mention model for tracking @username mentions in comments.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class CommentMention(Base):
    """Track mentions of users in comments."""

    __tablename__ = "comment_mentions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # The comment containing the mention
    comment_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("comments.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    # The user who was mentioned
    mentioned_user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    # The user who made the mention (author of the comment)
    mentioned_by_user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    comment = relationship("Comment", back_populates="mentions", foreign_keys=[comment_id])
    mentioned_user = relationship("User", foreign_keys=[mentioned_user_id], back_populates="received_mentions")
    mentioned_by = relationship("User", foreign_keys=[mentioned_by_user_id], back_populates="made_mentions")
