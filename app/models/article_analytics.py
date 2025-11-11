"""Article Analytics Model

Stores performance metrics and analytics data for articles.
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DECIMAL, Column, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class ArticleAnalytics(Base):
    """Analytics data for articles."""

    __tablename__ = "article_analytics"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    article_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # View metrics
    total_views = Column(Integer, default=0, nullable=False)
    unique_views = Column(Integer, default=0, nullable=False)
    direct_views = Column(Integer, default=0, nullable=False)
    rss_views = Column(Integer, default=0, nullable=False)
    search_views = Column(Integer, default=0, nullable=False)

    # Engagement metrics
    avg_read_time_seconds = Column(Integer, default=0, nullable=False)
    avg_scroll_percentage = Column(DECIMAL(5, 2), default=Decimal("0.00"), nullable=False)
    completion_rate = Column(DECIMAL(5, 4), default=Decimal("0.0000"), nullable=False)

    # Social metrics
    bookmark_count = Column(Integer, default=0, nullable=False)
    share_count = Column(Integer, default=0, nullable=False)

    # Performance scores
    trending_score = Column(DECIMAL(5, 2), default=Decimal("0.00"), nullable=False)
    performance_percentile = Column(Integer, default=0, nullable=False)

    # Timestamps
    last_calculated_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    article = relationship("Article", back_populates="analytics")

    def __repr__(self) -> str:
        return f"<ArticleAnalytics(article_id={self.article_id}, trending_score={self.trending_score})>"
