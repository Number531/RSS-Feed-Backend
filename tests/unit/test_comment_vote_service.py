"""
Unit tests for Comment Vote Service.

Tests voting operations on comments including:
- Vote casting (upvote/downvote)
- Vote toggling
- Vote removal
- Vote retrieval
- Validation
- Edge cases
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.comment_vote_service import CommentVoteService
from app.repositories.vote_repository import VoteRepository
from app.repositories.comment_repository import CommentRepository
from app.models.vote import Vote
from app.models.comment import Comment
from app.core.exceptions import (
    NotFoundError,
    InvalidVoteTypeError,
    ValidationError
)


@pytest.fixture
def mock_vote_repo():
    """Mock vote repository."""
    return AsyncMock(spec=VoteRepository)


@pytest.fixture
def mock_comment_repo():
    """Mock comment repository."""
    return AsyncMock(spec=CommentRepository)


@pytest.fixture
def comment_vote_service(mock_vote_repo, mock_comment_repo):
    """Create comment vote service with mocked dependencies."""
    return CommentVoteService(
        vote_repository=mock_vote_repo,
        comment_repository=mock_comment_repo
    )


@pytest.fixture
def sample_comment():
    """Create a sample comment for testing."""
    comment = Comment(
        id=uuid4(),
        user_id=uuid4(),
        article_id=uuid4(),
        content="Test comment",
        vote_score=0,
        vote_count=0
    )
    return comment


@pytest.fixture
def sample_vote():
    """Create a sample vote for testing."""
    vote = Vote(
        id=uuid4(),
        user_id=uuid4(),
        comment_id=uuid4(),
        vote_value=1
    )
    return vote


# ========== VOTE CASTING TESTS ==========

@pytest.mark.asyncio
async def test_cast_upvote_on_comment(
    comment_vote_service,
    mock_vote_repo,
    mock_comment_repo,
    sample_comment,
    sample_vote
):
    """Test casting an upvote on a comment."""
    user_id = uuid4()
    comment_id = sample_comment.id
    
    # Setup mocks
    mock_comment_repo.get_comment_by_id.return_value = sample_comment
    mock_vote_repo.get_comment_vote.return_value = None  # No existing vote
    mock_vote_repo.create_comment_vote.return_value = sample_vote
    
    # Cast vote
    result = await comment_vote_service.cast_vote(
        user_id=user_id,
        comment_id=comment_id,
        vote_value=1
    )
    
    # Assertions
    assert result == sample_vote
    mock_comment_repo.get_comment_by_id.assert_called_once_with(comment_id)
    mock_vote_repo.get_comment_vote.assert_called_once_with(user_id, comment_id)
    mock_vote_repo.create_comment_vote.assert_called_once_with(
        user_id=user_id,
        comment_id=comment_id,
        vote_value=1
    )


@pytest.mark.asyncio
async def test_cast_downvote_on_comment(
    comment_vote_service,
    mock_vote_repo,
    mock_comment_repo,
    sample_comment,
    sample_vote
):
    """Test casting a downvote on a comment."""
    user_id = uuid4()
    comment_id = sample_comment.id
    sample_vote.vote_value = -1
    
    # Setup mocks
    mock_comment_repo.get_comment_by_id.return_value = sample_comment
    mock_vote_repo.get_comment_vote.return_value = None
    mock_vote_repo.create_comment_vote.return_value = sample_vote
    
    # Cast vote
    result = await comment_vote_service.cast_vote(
        user_id=user_id,
        comment_id=comment_id,
        vote_value=-1
    )
    
    # Assertions
    assert result == sample_vote
    assert result.vote_value == -1
    mock_vote_repo.create_comment_vote.assert_called_once_with(
        user_id=user_id,
        comment_id=comment_id,
        vote_value=-1
    )


@pytest.mark.asyncio
async def test_cast_vote_on_nonexistent_comment(
    comment_vote_service,
    mock_vote_repo,
    mock_comment_repo
):
    """Test that voting on non-existent comment raises NotFoundError."""
    user_id = uuid4()
    comment_id = uuid4()
    
    # Setup mock
    mock_comment_repo.get_comment_by_id.return_value = None
    
    # Attempt to cast vote
    with pytest.raises(NotFoundError) as exc_info:
        await comment_vote_service.cast_vote(
            user_id=user_id,
            comment_id=comment_id,
            vote_value=1
        )
    
    assert "Comment" in str(exc_info.value)
    assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_cast_vote_with_invalid_value(
    comment_vote_service,
    mock_comment_repo
):
    """Test that invalid vote value raises InvalidVoteTypeError."""
    user_id = uuid4()
    comment_id = uuid4()
    
    # Attempt to cast vote with invalid value
    with pytest.raises(InvalidVoteTypeError) as exc_info:
        await comment_vote_service.cast_vote(
            user_id=user_id,
            comment_id=comment_id,
            vote_value=5  # Invalid
        )
    
    assert "must be -1" in str(exc_info.value)
    
    # Verify comment wasn't queried
    mock_comment_repo.get_comment_by_id.assert_not_called()


# ========== VOTE TOGGLING TESTS ==========

@pytest.mark.asyncio
async def test_toggle_same_vote_removes_it(
    comment_vote_service,
    mock_vote_repo,
    mock_comment_repo,
    sample_comment,
    sample_vote
):
    """Test that casting the same vote again toggles it off (removes it)."""
    user_id = uuid4()
    comment_id = sample_comment.id
    sample_vote.vote_value = 1
    
    # Setup mocks - existing upvote
    mock_comment_repo.get_comment_by_id.return_value = sample_comment
    mock_vote_repo.get_comment_vote.return_value = sample_vote
    mock_vote_repo.delete_comment_vote.return_value = None
    
    # Cast same vote (upvote again)
    result = await comment_vote_service.cast_vote(
        user_id=user_id,
        comment_id=comment_id,
        vote_value=1
    )
    
    # Assertions
    assert result is None  # Vote was removed
    mock_vote_repo.delete_comment_vote.assert_called_once_with(sample_vote)


@pytest.mark.asyncio
async def test_change_vote_from_upvote_to_downvote(
    comment_vote_service,
    mock_vote_repo,
    mock_comment_repo,
    sample_comment,
    sample_vote
):
    """Test changing vote from upvote to downvote."""
    user_id = uuid4()
    comment_id = sample_comment.id
    sample_vote.vote_value = 1  # Existing upvote
    
    # Setup mocks
    mock_comment_repo.get_comment_by_id.return_value = sample_comment
    mock_vote_repo.get_comment_vote.return_value = sample_vote
    
    updated_vote = Vote(
        id=sample_vote.id,
        user_id=user_id,
        comment_id=comment_id,
        vote_value=-1
    )
    mock_vote_repo.update_comment_vote.return_value = updated_vote
    
    # Change vote to downvote
    result = await comment_vote_service.cast_vote(
        user_id=user_id,
        comment_id=comment_id,
        vote_value=-1
    )
    
    # Assertions
    assert result == updated_vote
    assert result.vote_value == -1
    mock_vote_repo.update_comment_vote.assert_called_once_with(
        vote=sample_vote,
        new_value=-1
    )


@pytest.mark.asyncio
async def test_change_vote_from_downvote_to_upvote(
    comment_vote_service,
    mock_vote_repo,
    mock_comment_repo,
    sample_comment,
    sample_vote
):
    """Test changing vote from downvote to upvote."""
    user_id = uuid4()
    comment_id = sample_comment.id
    sample_vote.vote_value = -1  # Existing downvote
    
    # Setup mocks
    mock_comment_repo.get_comment_by_id.return_value = sample_comment
    mock_vote_repo.get_comment_vote.return_value = sample_vote
    
    updated_vote = Vote(
        id=sample_vote.id,
        user_id=user_id,
        comment_id=comment_id,
        vote_value=1
    )
    mock_vote_repo.update_comment_vote.return_value = updated_vote
    
    # Change vote to upvote
    result = await comment_vote_service.cast_vote(
        user_id=user_id,
        comment_id=comment_id,
        vote_value=1
    )
    
    # Assertions
    assert result == updated_vote
    assert result.vote_value == 1
    mock_vote_repo.update_comment_vote.assert_called_once()


# ========== VOTE REMOVAL TESTS ==========

@pytest.mark.asyncio
async def test_remove_vote_with_zero_value(
    comment_vote_service,
    mock_vote_repo,
    mock_comment_repo,
    sample_comment,
    sample_vote
):
    """Test removing vote by casting 0."""
    user_id = uuid4()
    comment_id = sample_comment.id
    
    # Setup mocks - existing vote
    mock_comment_repo.get_comment_by_id.return_value = sample_comment
    mock_vote_repo.get_comment_vote.return_value = sample_vote
    mock_vote_repo.delete_comment_vote.return_value = None
    
    # Remove vote with 0
    result = await comment_vote_service.cast_vote(
        user_id=user_id,
        comment_id=comment_id,
        vote_value=0
    )
    
    # Assertions
    assert result is None
    mock_vote_repo.delete_comment_vote.assert_called_once_with(sample_vote)


@pytest.mark.asyncio
async def test_remove_vote_when_no_vote_exists(
    comment_vote_service,
    mock_vote_repo,
    mock_comment_repo,
    sample_comment
):
    """Test removing vote when no vote exists returns None."""
    user_id = uuid4()
    comment_id = sample_comment.id
    
    # Setup mocks - no existing vote
    mock_comment_repo.get_comment_by_id.return_value = sample_comment
    mock_vote_repo.get_comment_vote.return_value = None
    
    # Remove vote with 0
    result = await comment_vote_service.cast_vote(
        user_id=user_id,
        comment_id=comment_id,
        vote_value=0
    )
    
    # Assertions
    assert result is None
    mock_vote_repo.delete_comment_vote.assert_not_called()


@pytest.mark.asyncio
async def test_remove_vote_method(
    comment_vote_service,
    mock_vote_repo,
    mock_comment_repo,
    sample_comment,
    sample_vote
):
    """Test the remove_vote method directly."""
    user_id = uuid4()
    comment_id = sample_comment.id
    
    # Setup mocks
    mock_comment_repo.get_comment_by_id.return_value = sample_comment
    mock_vote_repo.get_comment_vote.return_value = sample_vote
    mock_vote_repo.delete_comment_vote.return_value = None
    
    # Remove vote
    await comment_vote_service.remove_vote(
        user_id=user_id,
        comment_id=comment_id
    )
    
    # Assertions
    mock_vote_repo.delete_comment_vote.assert_called_once_with(sample_vote)


@pytest.mark.asyncio
async def test_remove_vote_when_none_exists_raises_error(
    comment_vote_service,
    mock_vote_repo,
    mock_comment_repo,
    sample_comment
):
    """Test that removing non-existent vote raises NotFoundError."""
    user_id = uuid4()
    comment_id = sample_comment.id
    
    # Setup mocks
    mock_comment_repo.get_comment_by_id.return_value = sample_comment
    mock_vote_repo.get_comment_vote.return_value = None
    
    # Attempt to remove vote
    with pytest.raises(NotFoundError) as exc_info:
        await comment_vote_service.remove_vote(
            user_id=user_id,
            comment_id=comment_id
        )
    
    assert "No vote found" in str(exc_info.value)


# ========== VOTE RETRIEVAL TESTS ==========

@pytest.mark.asyncio
async def test_get_user_vote(
    comment_vote_service,
    mock_vote_repo,
    sample_vote
):
    """Test getting user's vote on a comment."""
    user_id = uuid4()
    comment_id = uuid4()
    
    # Setup mock
    mock_vote_repo.get_comment_vote.return_value = sample_vote
    
    # Get vote
    result = await comment_vote_service.get_user_vote(
        user_id=user_id,
        comment_id=comment_id
    )
    
    # Assertions
    assert result == sample_vote
    mock_vote_repo.get_comment_vote.assert_called_once_with(user_id, comment_id)


@pytest.mark.asyncio
async def test_get_user_vote_when_none_exists(
    comment_vote_service,
    mock_vote_repo
):
    """Test getting user's vote when none exists returns None."""
    user_id = uuid4()
    comment_id = uuid4()
    
    # Setup mock
    mock_vote_repo.get_comment_vote.return_value = None
    
    # Get vote
    result = await comment_vote_service.get_user_vote(
        user_id=user_id,
        comment_id=comment_id
    )
    
    # Assertions
    assert result is None


@pytest.mark.asyncio
async def test_get_comment_vote_summary(
    comment_vote_service,
    mock_comment_repo,
    sample_comment
):
    """Test getting vote summary for a comment."""
    comment_id = sample_comment.id
    sample_comment.vote_score = 42
    sample_comment.vote_count = 50
    
    # Setup mock
    mock_comment_repo.get_comment_by_id.return_value = sample_comment
    
    # Get summary
    result = await comment_vote_service.get_comment_vote_summary(comment_id)
    
    # Assertions
    assert result["comment_id"] == comment_id
    assert result["vote_score"] == 42
    assert result["vote_count"] == 50


@pytest.mark.asyncio
async def test_get_comment_vote_summary_nonexistent_comment(
    comment_vote_service,
    mock_comment_repo
):
    """Test getting vote summary for non-existent comment raises error."""
    comment_id = uuid4()
    
    # Setup mock
    mock_comment_repo.get_comment_by_id.return_value = None
    
    # Attempt to get summary
    with pytest.raises(NotFoundError) as exc_info:
        await comment_vote_service.get_comment_vote_summary(comment_id)
    
    assert "Comment" in str(exc_info.value)


# ========== TOGGLE VOTE TESTS ==========

@pytest.mark.asyncio
async def test_toggle_vote_with_upvote(
    comment_vote_service,
    mock_vote_repo,
    mock_comment_repo,
    sample_comment,
    sample_vote
):
    """Test toggle_vote method with upvote."""
    user_id = uuid4()
    comment_id = sample_comment.id
    
    # Setup mocks
    mock_comment_repo.get_comment_by_id.return_value = sample_comment
    mock_vote_repo.get_comment_vote.return_value = None
    mock_vote_repo.create_comment_vote.return_value = sample_vote
    
    # Toggle vote
    result = await comment_vote_service.toggle_vote(
        user_id=user_id,
        comment_id=comment_id,
        vote_type="upvote"
    )
    
    # Assertions
    assert result == sample_vote
    mock_vote_repo.create_comment_vote.assert_called_once()


@pytest.mark.asyncio
async def test_toggle_vote_with_downvote(
    comment_vote_service,
    mock_vote_repo,
    mock_comment_repo,
    sample_comment,
    sample_vote
):
    """Test toggle_vote method with downvote."""
    user_id = uuid4()
    comment_id = sample_comment.id
    sample_vote.vote_value = -1
    
    # Setup mocks
    mock_comment_repo.get_comment_by_id.return_value = sample_comment
    mock_vote_repo.get_comment_vote.return_value = None
    mock_vote_repo.create_comment_vote.return_value = sample_vote
    
    # Toggle vote
    result = await comment_vote_service.toggle_vote(
        user_id=user_id,
        comment_id=comment_id,
        vote_type="downvote"
    )
    
    # Assertions
    assert result == sample_vote


@pytest.mark.asyncio
async def test_toggle_vote_with_invalid_type(
    comment_vote_service,
    mock_comment_repo
):
    """Test toggle_vote with invalid vote type raises ValidationError."""
    user_id = uuid4()
    comment_id = uuid4()
    
    # Attempt to toggle with invalid type
    with pytest.raises(ValidationError) as exc_info:
        await comment_vote_service.toggle_vote(
            user_id=user_id,
            comment_id=comment_id,
            vote_type="superlike"  # Invalid
        )
    
    assert "upvote" in str(exc_info.value) or "downvote" in str(exc_info.value)


# ========== VALIDATION TESTS ==========

@pytest.mark.asyncio
async def test_validate_vote_value_valid():
    """Test vote value validation with valid values."""
    service = CommentVoteService(
        vote_repository=AsyncMock(),
        comment_repository=AsyncMock()
    )
    
    # Should not raise
    service.validate_vote_value(-1)
    service.validate_vote_value(0)
    service.validate_vote_value(1)


@pytest.mark.asyncio
async def test_validate_vote_value_invalid():
    """Test vote value validation with invalid values."""
    service = CommentVoteService(
        vote_repository=AsyncMock(),
        comment_repository=AsyncMock()
    )
    
    # Should raise for invalid values
    with pytest.raises(InvalidVoteTypeError):
        service.validate_vote_value(2)
    
    with pytest.raises(InvalidVoteTypeError):
        service.validate_vote_value(-2)
    
    with pytest.raises(InvalidVoteTypeError):
        service.validate_vote_value(100)


# ========== EDGE CASE TESTS ==========

@pytest.mark.asyncio
async def test_concurrent_votes_on_same_comment(
    comment_vote_service,
    mock_vote_repo,
    mock_comment_repo,
    sample_comment
):
    """Test handling multiple votes on same comment (simulated concurrency)."""
    comment_id = sample_comment.id
    
    # Setup mocks
    mock_comment_repo.get_comment_by_id.return_value = sample_comment
    mock_vote_repo.get_comment_vote.return_value = None
    
    # Create different votes
    vote1 = Vote(id=uuid4(), user_id=uuid4(), comment_id=comment_id, vote_value=1)
    vote2 = Vote(id=uuid4(), user_id=uuid4(), comment_id=comment_id, vote_value=-1)
    
    mock_vote_repo.create_comment_vote.side_effect = [vote1, vote2]
    
    # Cast votes from different users
    result1 = await comment_vote_service.cast_vote(uuid4(), comment_id, 1)
    result2 = await comment_vote_service.cast_vote(uuid4(), comment_id, -1)
    
    # Assertions
    assert result1.vote_value == 1
    assert result2.vote_value == -1
    assert mock_vote_repo.create_comment_vote.call_count == 2
