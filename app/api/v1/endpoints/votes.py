"""
Votes API Endpoints

Handles voting operations on articles.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_vote_service
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.vote import VoteCreate, VoteResponse
from app.services.vote_service import VoteService

router = APIRouter()


@router.post("/", response_model=Optional[VoteResponse], status_code=status.HTTP_201_CREATED)
async def cast_vote(
    vote_data: VoteCreate,
    current_user: User = Depends(get_current_user),
    vote_service: VoteService = Depends(get_vote_service),
):
    """
    Cast or update a vote on an article.

    - **article_id**: UUID of the article to vote on
    - **vote_value**: Vote value (1 for upvote, -1 for downvote, 0 to remove)

    If user has already voted, this will update their vote.
    If vote_value is 0, the vote will be removed and None is returned.

    Returns the created or updated vote, or None if removed.
    """
    vote = await vote_service.cast_vote(
        user_id=current_user.id, article_id=vote_data.article_id, vote_value=vote_data.vote_value
    )

    return vote


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_vote(
    article_id: UUID,
    current_user: User = Depends(get_current_user),
    vote_service: VoteService = Depends(get_vote_service),
):
    """
    Remove user's vote from an article.

    - **article_id**: UUID of the article

    Returns 204 No Content on success.
    Raises 404 if no vote exists.
    """
    await vote_service.remove_vote(user_id=current_user.id, article_id=article_id)

    return None


@router.get("/article/{article_id}", response_model=Optional[VoteResponse])
async def get_user_vote(
    article_id: UUID,
    current_user: User = Depends(get_current_user),
    vote_service: VoteService = Depends(get_vote_service),
):
    """
    Get current user's vote on an article.

    - **article_id**: UUID of the article

    Returns the vote if it exists, null otherwise.
    """
    vote = await vote_service.get_user_vote(user_id=current_user.id, article_id=article_id)

    return vote
