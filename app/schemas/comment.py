"""
Comment schemas for API validation.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class CommentBase(BaseModel):
    """Base comment schema."""
    content: str = Field(..., min_length=1, max_length=10000)


class CommentCreate(CommentBase):
    """Schema for creating a comment."""
    article_id: UUID
    parent_comment_id: Optional[UUID] = None  # For threaded comments


class CommentUpdate(BaseModel):
    """Schema for updating a comment."""
    content: str = Field(..., min_length=1, max_length=10000)


class CommentResponse(CommentBase):
    """Schema for comment response."""
    id: UUID
    user_id: UUID
    article_id: UUID
    parent_comment_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    # Vote metrics
    vote_score: int = 0  # Sum of vote values (can be negative)
    vote_count: int = 0  # Total number of votes
    
    # Status flags
    is_deleted: bool = False
    is_edited: bool = False
    
    # User info (joined from user table)
    username: Optional[str] = None
    user_avatar: Optional[str] = None
    
    # User interaction (if authenticated)
    user_vote: Optional[int] = None  # -1 (downvote), 0 (no vote), 1 (upvote)
    
    model_config = ConfigDict(from_attributes=True)


class CommentTree(CommentResponse):
    """Schema for nested comment tree."""
    replies: List["CommentTree"] = []


class CommentList(BaseModel):
    """Schema for paginated comment list."""
    items: List[CommentResponse]
    total: int
    page: int
    page_size: int


# Update forward references for recursive model
CommentTree.model_rebuild()
