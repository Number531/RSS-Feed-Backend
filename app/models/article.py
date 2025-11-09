"""
Article model for storing aggregated news articles.
"""

import uuid
from datetime import datetime

from sqlalchemy import ARRAY, DECIMAL, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class Article(Base):
    """News article from RSS feeds."""

    __tablename__ = "articles"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    rss_source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rss_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Article content
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    url_hash = Column(
        String(64), unique=True, nullable=False, index=True
    )  # SHA-256 hash for deduplication
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)  # RSS feed description/summary
    crawled_content = Column(Text, nullable=True)  # Full article text from Railway API

    # Metadata
    author = Column(String(255), nullable=True)
    published_date = Column(DateTime(timezone=True), nullable=True, index=True)
    thumbnail_url = Column(Text, nullable=True)

    # Categorization
    category = Column(String(50), nullable=False, index=True)
    tags = Column(ARRAY(String), nullable=True)

    # Engagement metrics (denormalized for performance)
    vote_score = Column(Integer, default=0, nullable=False, index=True)
    vote_count = Column(Integer, default=0, nullable=False)
    comment_count = Column(Integer, default=0, nullable=False)

    # Trending algorithm
    trending_score = Column(DECIMAL(10, 4), default=0, nullable=False, index=True)

    # Fact-check cache (denormalized for performance)
    fact_check_score = Column(Integer, nullable=True, index=True)
    fact_check_verdict = Column(String(50), nullable=True, index=True)
    fact_checked_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Full-text search vector
    search_vector = Column(TSVECTOR, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    rss_source = relationship("RSSSource", back_populates="articles")
    votes = relationship("Vote", back_populates="article", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="article", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="article", cascade="all, delete-orphan")
    reading_history = relationship(
        "ReadingHistory", back_populates="article", cascade="all, delete-orphan"
    )
    fact_check = relationship(
        "ArticleFactCheck", back_populates="article", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Article(title='{self.title[:50]}...', source='{self.rss_source_id}')>"
