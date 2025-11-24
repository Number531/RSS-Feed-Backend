"""
Audit models for tracking system events.

Provides models for logging registration attempts, security events,
and other audit trail requirements.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class RegistrationAudit(Base):
    """
    Audit log for user registration attempts.
    
    Tracks both successful and failed registration attempts with
    IP address, user agent, and failure reasons for security analysis.
    """
    
    __tablename__ = "registration_audit"
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )
    
    # User information (null if registration failed before user creation)
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Request metadata
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv6 support
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Registration outcome
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    failure_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    
    def __repr__(self) -> str:
        """String representation of audit entry."""
        status = "SUCCESS" if self.success else "FAILED"
        return (
            f"<RegistrationAudit(id={self.id}, email={self.email}, "
            f"status={status}, created_at={self.created_at})>"
        )
