"""
Comment model (placeholder for Phase 4).
"""
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.session import Base


class Comment(Base):
    """User comment on an article."""
    
    __tablename__ = "comments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)
    
    content = Column(Text, nullable=False)
    is_edited = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Vote metrics (score = sum of vote values, count = total votes)
    vote_score = Column(Integer, default=0, nullable=False)
    vote_count = Column(Integer, default=0, nullable=False, index=True)  # NEW: Track total vote count
    
    reply_count = Column(Integer, default=0, nullable=False)
    depth = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    article = relationship("Article", back_populates="comments")
    user = relationship("User", back_populates="comments")
    votes = relationship("Vote", back_populates="comment", foreign_keys="Vote.comment_id")
