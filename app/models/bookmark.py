"""Bookmark model for saved articles."""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import sqlalchemy as sa

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.article import Article


class Bookmark(Base):
    """Bookmark model for user-saved articles."""
    
    __tablename__ = "bookmarks"
    
    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=sa.text("gen_random_uuid()")
    )
    
    # Foreign Keys
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    article_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Data
    collection: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        server_default=sa.func.now(),
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="bookmarks")
    article: Mapped["Article"] = relationship("Article", back_populates="bookmarks")
    
    # Indexes
    __table_args__ = (
        Index("idx_bookmarks_user_id", "user_id"),
        Index("idx_bookmarks_article_id", "article_id"),
        Index("idx_bookmarks_created_at", "created_at"),
        Index(
            "idx_bookmarks_collection",
            "collection",
            postgresql_where=sa.text("collection IS NOT NULL")
        ),
        sa.UniqueConstraint("user_id", "article_id", name="uq_user_article_bookmark"),
    )
    
    def __repr__(self) -> str:
        return f"<Bookmark user={self.user_id} article={self.article_id}>"
