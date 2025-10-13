"""
Vote model (placeholder for Phase 4).
"""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, SmallInteger, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.session import Base


class Vote(Base):
    """User vote on an article or comment.
    
    Supports polymorphic voting:
    - Either article_id OR comment_id must be set (but not both)
    - vote_value: 1 for upvote, -1 for downvote
    """
    
    __tablename__ = "votes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Polymorphic voting: can vote on article OR comment
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), nullable=True, index=True)
    comment_id = Column(UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)
    
    vote_value = Column(SmallInteger, nullable=False)  # 1 for upvote, -1 for downvote
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    article = relationship("Article", back_populates="votes", foreign_keys=[article_id])
    comment = relationship("Comment", back_populates="votes", foreign_keys=[comment_id])
    user = relationship("User", back_populates="votes")
    
    __table_args__ = (
        # Ensure either article_id OR comment_id is set (but not both or neither)
        CheckConstraint(
            '(article_id IS NOT NULL AND comment_id IS NULL) OR '
            '(article_id IS NULL AND comment_id IS NOT NULL)',
            name='vote_target_check'
        ),
        # Unique constraint for article votes
        UniqueConstraint('user_id', 'article_id', name='unique_user_article_vote'),
        # Unique constraint for comment votes
        UniqueConstraint('user_id', 'comment_id', name='unique_user_comment_vote'),
    )
