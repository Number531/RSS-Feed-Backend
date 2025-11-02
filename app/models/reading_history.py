"""Reading history model for tracking article views."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import DECIMAL, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.article import Article
    from app.models.user import User


class ReadingHistory(Base):
    """Reading history model for tracking when users view articles."""

    __tablename__ = "reading_history"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=sa.text("gen_random_uuid()"),
    )

    # Foreign Keys
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    article_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), nullable=False
    )

    # Timestamp
    viewed_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, server_default=sa.func.now(), nullable=False
    )

    # Optional engagement metrics
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scroll_percentage: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="reading_history")
    article: Mapped["Article"] = relationship("Article", back_populates="reading_history")

    # Indexes
    __table_args__ = (
        Index("idx_reading_history_user_id", "user_id"),
        Index("idx_reading_history_article_id", "article_id"),
        Index("idx_reading_history_viewed_at", "viewed_at"),
        Index("idx_reading_history_user_viewed", "user_id", "viewed_at"),
    )

    def __repr__(self) -> str:
        return f"<ReadingHistory user={self.user_id} article={self.article_id} viewed={self.viewed_at}>"
