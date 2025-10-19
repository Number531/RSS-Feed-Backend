"""
Fact-check models for storing article validation results.
"""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.db.session import Base


class ArticleFactCheck(Base):
    """Detailed fact-check results for an article."""
    
    __tablename__ = "article_fact_checks"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key (1:1 relationship with articles)
    article_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("articles.id", ondelete="CASCADE"), 
        nullable=False, 
        unique=True,
        index=True
    )
    
    # Core fact-check results
    verdict = Column(String(50), nullable=False, index=True)
    credibility_score = Column(Integer, nullable=False, index=True)
    confidence = Column(DECIMAL(3, 2), nullable=True)
    summary = Column(Text, nullable=False)
    
    # Claim statistics
    claims_analyzed = Column(Integer, nullable=True)
    claims_validated = Column(Integer, nullable=True)
    claims_true = Column(Integer, nullable=True)
    claims_false = Column(Integer, nullable=True)
    claims_misleading = Column(Integer, nullable=True)
    claims_unverified = Column(Integer, nullable=True)
    
    # Full validation data (complete API response)
    validation_results = Column(JSONB, nullable=False)
    
    # Evidence quality metrics
    num_sources = Column(Integer, nullable=True)
    source_consensus = Column(String(20), nullable=True)
    
    # Processing metadata
    job_id = Column(String(255), nullable=False, unique=True, index=True)
    validation_mode = Column(String(20), nullable=True)
    processing_time_seconds = Column(Integer, nullable=True)
    api_costs = Column(JSONB, nullable=True)
    
    # Timestamps
    fact_checked_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    article = relationship("Article", back_populates="fact_check")
    
    def __repr__(self):
        return f"<ArticleFactCheck(article_id='{self.article_id}', verdict='{self.verdict}', score={self.credibility_score})>"


class SourceCredibilityScore(Base):
    """Aggregated credibility scores for news outlets over time."""
    
    __tablename__ = "source_credibility_scores"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    rss_source_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("rss_sources.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Aggregated credibility metrics
    average_score = Column(DECIMAL(5, 2), nullable=False, index=True)
    total_articles_checked = Column(Integer, nullable=False, default=0)
    true_count = Column(Integer, nullable=False, default=0)
    false_count = Column(Integer, nullable=False, default=0)
    misleading_count = Column(Integer, nullable=False, default=0)
    unverified_count = Column(Integer, nullable=False, default=0)
    
    # Time period for scoring
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), nullable=False, index=True)  # 'daily', 'weekly', 'monthly', 'all_time'
    
    # Trend analysis (historical data points)
    trend_data = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    rss_source = relationship("RSSSource", back_populates="credibility_scores")
    
    def __repr__(self):
        return f"<SourceCredibilityScore(source_id='{self.rss_source_id}', period='{self.period_type}', score={self.average_score})>"
