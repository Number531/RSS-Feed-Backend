"""
Vote schemas for API validation.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VoteCreate(BaseModel):
    """Schema for creating a vote."""

    article_id: UUID
    vote_value: int = Field(..., ge=-1, le=1, description="Vote value: -1 (downvote), 1 (upvote)")


class VoteResponse(BaseModel):
    """Schema for vote response."""

    id: UUID
    user_id: UUID
    article_id: UUID
    vote_value: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VoteDelete(BaseModel):
    """Schema for deleting a vote."""

    article_id: UUID
