"""User reading preferences model."""

import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class UserReadingPreferences(Base):
    """User preferences for reading history tracking and privacy."""

    __tablename__ = "user_reading_preferences"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Tracking preferences
    tracking_enabled = Column(Boolean, default=True, nullable=False)
    analytics_opt_in = Column(Boolean, default=True, nullable=False)

    # Auto-cleanup settings
    auto_cleanup_enabled = Column(Boolean, default=False, nullable=False)
    retention_days = Column(Integer, default=365, nullable=False)

    # Privacy settings
    exclude_categories = Column(ARRAY(String), default=[], nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="reading_preferences")

    def __repr__(self):
        return f"<UserReadingPreferences(user_id='{self.user_id}', tracking_enabled={self.tracking_enabled})>"
