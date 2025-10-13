"""
RSS Source model for storing feed configurations.
"""
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.session import Base


class RSSSource(Base):
    """RSS feed source configuration."""
    
    __tablename__ = "rss_sources"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Feed information
    name = Column(String(255), nullable=False)
    url = Column(Text, unique=True, nullable=False, index=True)
    source_name = Column(String(100), nullable=False, index=True)  # 'Fox News', 'CNN', etc.
    category = Column(String(50), nullable=False, index=True)  # 'general', 'politics', etc.
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Feed health tracking
    last_fetched = Column(DateTime(timezone=True), nullable=True)
    last_successful_fetch = Column(DateTime(timezone=True), nullable=True)
    fetch_success_count = Column(Integer, default=0, nullable=False)
    fetch_failure_count = Column(Integer, default=0, nullable=False)
    consecutive_failures = Column(Integer, default=0, nullable=False)
    
    # HTTP caching headers
    etag = Column(String(255), nullable=True)
    last_modified = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    articles = relationship("Article", back_populates="rss_source", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<RSSSource(name='{self.name}', source='{self.source_name}', active={self.is_active})>"
    
    @property
    def success_rate(self) -> float:
        """Calculate feed success rate as percentage."""
        total = self.fetch_success_count + self.fetch_failure_count
        if total == 0:
            return 0.0
        return (self.fetch_success_count / total) * 100
    
    @property
    def is_healthy(self) -> bool:
        """Check if feed is healthy (success rate > 80% and consecutive failures < 5)."""
        return self.success_rate > 80 and self.consecutive_failures < 5
