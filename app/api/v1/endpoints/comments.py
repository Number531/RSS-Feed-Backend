"""
Comments API Endpoints

Handles comment operations including creation, retrieval, updates, and deletion.
Supports threaded comments with replies.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_comment_service, get_comment_vote_service
from app.core.security import get_current_user, get_current_user_optional
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentResponse, CommentTree, CommentUpdate
from app.services.comment_service import CommentService
from app.services.comment_vote_service import CommentVoteService

router = APIRouter()


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
):
    """
    Create a new comment on an article.

    - **article_id**: UUID of the article
    - **content**: Comment text (1-10,000 characters)
    - **parent_comment_id**: Optional UUID of parent comment for replies

    Returns the created comment.

    Requires authentication.
    """
    comment = await comment_service.create_comment(
        user_id=current_user.id,
        article_id=comment_data.article_id,
        content=comment_data.content,
        parent_comment_id=comment_data.parent_comment_id,
    )

    return comment


@router.get("/article/{article_id}", response_model=List[CommentResponse])
async def get_article_comments(
    article_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    comment_service: CommentService = Depends(get_comment_service),
):
    """
    Get top-level comments for an article.

    - **article_id**: UUID of the article
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 50, max: 100)

    Returns list of top-level comments (not replies).
    Use GET /{comment_id}/replies to get replies.

    Does not require authentication.
    """
    comments = await comment_service.get_article_comments(
        article_id=article_id, page=page, page_size=page_size
    )

    return comments


@router.get("/article/{article_id}/tree", response_model=List[CommentTree])
async def get_article_comment_tree(
    article_id: UUID,
    max_depth: int = Query(10, ge=1, le=20),
    comment_service: CommentService = Depends(get_comment_service),
):
    """
    Get nested comment tree for an article.

    - **article_id**: UUID of the article
    - **max_depth**: Maximum nesting depth (default: 10, max: 20)

    Returns a nested tree structure of comments with replies.
    Useful for displaying threaded discussions.

    Does not require authentication.
    """
    tree = await comment_service.build_comment_tree(article_id=article_id, max_depth=max_depth)

    return tree


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: UUID, comment_service: CommentService = Depends(get_comment_service)
):
    """
    Get a single comment by ID.

    - **comment_id**: UUID of the comment

    Returns the comment details.
    Raises 404 if comment not found.

    Does not require authentication.
    """
    comment = await comment_service.get_comment_by_id(comment_id)

    return comment


@router.get("/{comment_id}/replies", response_model=List[CommentResponse])
async def get_comment_replies(
    comment_id: UUID, comment_service: CommentService = Depends(get_comment_service)
):
    """
    Get all replies to a comment.

    - **comment_id**: UUID of the parent comment

    Returns list of direct replies to this comment.
    Does not include nested replies (use tree endpoint for that).

    Does not require authentication.
    """
    replies = await comment_service.get_comment_replies(comment_id)

    return replies


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: UUID,
    comment_data: CommentUpdate,
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
):
    """
    Update a comment's content.

    - **comment_id**: UUID of the comment
    - **content**: New comment text (1-10,000 characters)

    Returns the updated comment.

    Only the comment author can update their comment.
    Raises 403 if user is not the author.
    Raises 404 if comment not found.

    Requires authentication.
    """
    updated_comment = await comment_service.update_comment(
        comment_id=comment_id, user_id=current_user.id, content=comment_data.content
    )

    return updated_comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
):
    """
    Delete a comment (soft delete).

    - **comment_id**: UUID of the comment

    Soft deletes the comment (marks as deleted, preserves thread structure).
    Content is replaced with "[deleted]".

    Only the comment author can delete their comment.
    Raises 403 if user is not the author.
    Raises 404 if comment not found.

    Returns 204 No Content on success.

    Requires authentication.
    """
    await comment_service.delete_comment(comment_id=comment_id, user_id=current_user.id)


# ========== COMMENT VOTING ENDPOINTS ==========


@router.post("/{comment_id}/vote", status_code=status.HTTP_200_OK, summary="Vote on comment")
async def vote_on_comment(
    comment_id: UUID,
    vote_type: str = Query(..., pattern="^(upvote|downvote)$"),
    current_user: User = Depends(get_current_user),
    vote_service: CommentVoteService = Depends(get_comment_vote_service),
):
    """
    Cast or toggle a vote on a comment.

    - **comment_id**: UUID of the comment
    - **vote_type**: "upvote" or "downvote"

    Behavior:
    - First vote: Creates the vote
    - Same vote again: Removes the vote (toggle off)
    - Different vote: Changes the vote type

    Returns:
    - **voted**: Whether vote is active (true) or removed (false)
    - **vote_type**: Current vote type or null if removed
    - **vote_score**: Updated vote score
    - **vote_count**: Updated total vote count

    Requires authentication.
    """
    # Convert vote_type to value
    vote_value = 1 if vote_type == "upvote" else -1

    # Cast vote (toggle logic is built into cast_vote)
    vote = await vote_service.cast_vote(
        user_id=current_user.id, comment_id=comment_id, vote_value=vote_value
    )

    # Get updated comment vote summary
    summary = await vote_service.get_comment_vote_summary(comment_id)

    return {
        "voted": vote is not None,
        "vote_type": vote_type if vote is not None else None,
        "vote_score": summary["vote_score"],
        "vote_count": summary["vote_count"],
    }


@router.delete(
    "/{comment_id}/vote", status_code=status.HTTP_200_OK, summary="Remove vote from comment"
)
async def remove_comment_vote(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    vote_service: CommentVoteService = Depends(get_comment_vote_service),
):
    """
    Remove user's vote from a comment.

    - **comment_id**: UUID of the comment

    Removes the user's vote if it exists.
    Does nothing if no vote exists.

    Returns:
    - **removed**: Whether a vote was removed
    - **vote_score**: Updated vote score
    - **vote_count**: Updated total vote count

    Requires authentication.
    """
    try:
        await vote_service.remove_vote(user_id=current_user.id, comment_id=comment_id)
        removed = True
    except Exception:
        removed = False

    # Get updated comment vote summary
    summary = await vote_service.get_comment_vote_summary(comment_id)

    return {
        "removed": removed,
        "vote_score": summary["vote_score"],
        "vote_count": summary["vote_count"],
    }


@router.get(
    "/{comment_id}/vote", status_code=status.HTTP_200_OK, summary="Get user's vote on comment"
)
async def get_comment_vote(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    vote_service: CommentVoteService = Depends(get_comment_vote_service),
):
    """
    Get user's current vote on a comment.

    - **comment_id**: UUID of the comment

    Returns:
    - **voted**: Whether user has voted
    - **vote_type**: "upvote", "downvote", or null
    - **vote_value**: 1 (upvote), -1 (downvote), or 0 (no vote)

    Requires authentication.
    """
    vote = await vote_service.get_user_vote(user_id=current_user.id, comment_id=comment_id)

    if vote:
        vote_type = "upvote" if vote.vote_value == 1 else "downvote"
        return {"voted": True, "vote_type": vote_type, "vote_value": vote.vote_value}
    else:
        return {"voted": False, "vote_type": None, "vote_value": 0}


@router.get(
    "/{comment_id}/vote/summary",
    status_code=status.HTTP_200_OK,
    summary="Get vote summary for comment",
)
async def get_comment_vote_summary_endpoint(
    comment_id: UUID, vote_service: CommentVoteService = Depends(get_comment_vote_service)
):
    """
    Get vote summary for a comment (public endpoint).

    - **comment_id**: UUID of the comment

    Returns:
    - **comment_id**: UUID of the comment
    - **vote_score**: Sum of all vote values
    - **vote_count**: Total number of votes

    Does not require authentication.
    """
    return await vote_service.get_comment_vote_summary(comment_id)
