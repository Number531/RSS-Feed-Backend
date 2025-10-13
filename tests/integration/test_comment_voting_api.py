"""
Integration tests for Comment Voting API.

Tests the full HTTP API flow for comment voting including:
- POST /comments/{id}/vote - Cast/toggle vote
- DELETE /comments/{id}/vote - Remove vote  
- GET /comments/{id}/vote - Get user's vote
- GET /comments/{id}/vote/summary - Get vote summary
- Authentication & authorization
- Error handling
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.user import User
from app.models.article import Article
from app.models.comment import Comment
from app.models.vote import Vote
from app.core.security import create_access_token


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="voter@test.com",
        username="voter",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_article(db_session: AsyncSession, test_user: User):
    """Create a test article."""
    from app.models.rss_source import RSSSource
    from tests.utils import generate_url_hash
    
    # Create RSS source first (foreign key requirement)
    feed_url = "https://example.com/feed"
    rss_source = RSSSource(
        id=uuid4(),
        name="Test Source",
        url=feed_url,
        source_name="Test Source",  # Required field
        category="Technology"
    )
    db_session.add(rss_source)
    await db_session.flush()
    
    # Create article with all required fields
    article_url = "https://example.com/article"
    article = Article(
        id=uuid4(),
        title="Test Article",
        url=article_url,
        url_hash=generate_url_hash(article_url),
        rss_source_id=rss_source.id,
        category="Technology"
    )
    db_session.add(article)
    await db_session.commit()
    await db_session.refresh(article)
    return article


@pytest.fixture
async def test_comment(db_session: AsyncSession, test_user: User, test_article: Article):
    """Create a test comment."""
    comment = Comment(
        id=uuid4(),
        user_id=test_user.id,
        article_id=test_article.id,
        content="Test comment for voting",
        vote_score=0,
        vote_count=0
    )
    db_session.add(comment)
    await db_session.commit()
    await db_session.refresh(comment)
    return comment


@pytest.fixture
def auth_headers(test_user: User):
    """Create authentication headers with JWT token."""
    token = create_access_token(test_user.id, test_user.email)
    return {"Authorization": f"Bearer {token}"}


# ========== VOTE CASTING TESTS ==========

@pytest.mark.asyncio
async def test_cast_upvote_on_comment(
    client: AsyncClient,
    test_comment: Comment,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test casting an upvote on a comment."""
    response = await client.post(
        f"/api/v1/comments/{test_comment.id}/vote?vote_type=upvote",
        headers=auth_headers
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["voted"] is True
    assert data["vote_type"] == "upvote"
    assert data["vote_score"] == 1
    assert data["vote_count"] == 1
    
    # Verify in database
    await db_session.refresh(test_comment)
    assert test_comment.vote_score == 1
    assert test_comment.vote_count == 1


@pytest.mark.asyncio
async def test_cast_downvote_on_comment(
    client: AsyncClient,
    test_comment: Comment,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test casting a downvote on a comment."""
    response = await client.post(
        f"/api/v1/comments/{test_comment.id}/vote?vote_type=downvote",
        headers=auth_headers
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["voted"] is True
    assert data["vote_type"] == "downvote"
    assert data["vote_score"] == -1
    assert data["vote_count"] == 1
    
    # Verify in database
    await db_session.refresh(test_comment)
    assert test_comment.vote_score == -1
    assert test_comment.vote_count == 1


@pytest.mark.asyncio
async def test_vote_requires_authentication(
    client: AsyncClient,
    test_comment: Comment
):
    """Test that voting requires authentication."""
    response = await client.post(
        f"/api/v1/comments/{test_comment.id}/vote?vote_type=upvote"
    )
    
    # Should return 401 or 403 (authentication/authorization error)
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_vote_on_nonexistent_comment(
    client: AsyncClient,
    auth_headers: dict
):
    """Test voting on non-existent comment returns 404."""
    fake_id = uuid4()
    response = await client.post(
        f"/api/v1/comments/{fake_id}/vote?vote_type=upvote",
        headers=auth_headers
    )
    
    # Should return 404 Not Found
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_vote_with_invalid_type(
    client: AsyncClient,
    test_comment: Comment,
    auth_headers: dict
):
    """Test voting with invalid vote type returns 422."""
    response = await client.post(
        f"/api/v1/comments/{test_comment.id}/vote?vote_type=superlike",
        headers=auth_headers
    )
    
    # Should return 422 Validation Error
    assert response.status_code == 422


# ========== VOTE TOGGLING TESTS ==========

@pytest.mark.asyncio
async def test_toggle_same_vote_removes_it(
    client: AsyncClient,
    test_comment: Comment,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test that casting the same vote twice toggles it off."""
    # First vote - upvote
    response1 = await client.post(
        f"/api/v1/comments/{test_comment.id}/vote?vote_type=upvote",
        headers=auth_headers
    )
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["voted"] is True
    assert data1["vote_score"] == 1
    
    # Second vote - upvote again (should toggle off)
    response2 = await client.post(
        f"/api/v1/comments/{test_comment.id}/vote?vote_type=upvote",
        headers=auth_headers
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["voted"] is False
    assert data2["vote_type"] is None
    assert data2["vote_score"] == 0
    assert data2["vote_count"] == 0
    
    # Verify in database
    await db_session.refresh(test_comment)
    assert test_comment.vote_score == 0
    assert test_comment.vote_count == 0


@pytest.mark.asyncio
async def test_change_vote_from_upvote_to_downvote(
    client: AsyncClient,
    test_comment: Comment,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test changing vote from upvote to downvote."""
    # First vote - upvote
    response1 = await client.post(
        f"/api/v1/comments/{test_comment.id}/vote?vote_type=upvote",
        headers=auth_headers
    )
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["vote_score"] == 1
    
    # Change to downvote
    response2 = await client.post(
        f"/api/v1/comments/{test_comment.id}/vote?vote_type=downvote",
        headers=auth_headers
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["voted"] is True
    assert data2["vote_type"] == "downvote"
    assert data2["vote_score"] == -1
    assert data2["vote_count"] == 1
    
    # Verify in database
    await db_session.refresh(test_comment)
    assert test_comment.vote_score == -1
    assert test_comment.vote_count == 1


# ========== VOTE REMOVAL TESTS ==========

@pytest.mark.asyncio
async def test_remove_vote(
    client: AsyncClient,
    test_comment: Comment,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test removing a vote using DELETE endpoint."""
    # First cast a vote
    await client.post(
        f"/api/v1/comments/{test_comment.id}/vote?vote_type=upvote",
        headers=auth_headers
    )
    
    # Remove the vote
    response = await client.delete(
        f"/api/v1/comments/{test_comment.id}/vote",
        headers=auth_headers
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["removed"] is True
    assert data["vote_score"] == 0
    assert data["vote_count"] == 0
    
    # Verify in database
    await db_session.refresh(test_comment)
    assert test_comment.vote_score == 0
    assert test_comment.vote_count == 0


@pytest.mark.asyncio
async def test_remove_vote_when_none_exists(
    client: AsyncClient,
    test_comment: Comment,
    auth_headers: dict
):
    """Test removing vote when none exists."""
    response = await client.delete(
        f"/api/v1/comments/{test_comment.id}/vote",
        headers=auth_headers
    )
    
    # Should still return 200 but removed=False
    assert response.status_code == 200
    data = response.json()
    assert data["removed"] is False


@pytest.mark.asyncio
async def test_remove_vote_requires_authentication(
    client: AsyncClient,
    test_comment: Comment
):
    """Test that removing vote requires authentication."""
    response = await client.delete(
        f"/api/v1/comments/{test_comment.id}/vote"
    )
    
    # Should return 401 Unauthorized or 403 Forbidden
    assert response.status_code in [401, 403]


# ========== VOTE RETRIEVAL TESTS ==========

@pytest.mark.asyncio
async def test_get_user_vote(
    client: AsyncClient,
    test_comment: Comment,
    auth_headers: dict
):
    """Test getting user's vote on a comment."""
    # First cast a vote
    await client.post(
        f"/api/v1/comments/{test_comment.id}/vote?vote_type=upvote",
        headers=auth_headers
    )
    
    # Get the vote
    response = await client.get(
        f"/api/v1/comments/{test_comment.id}/vote",
        headers=auth_headers
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["voted"] is True
    assert data["vote_type"] == "upvote"
    assert data["vote_value"] == 1


@pytest.mark.asyncio
async def test_get_user_vote_when_none_exists(
    client: AsyncClient,
    test_comment: Comment,
    auth_headers: dict
):
    """Test getting user's vote when none exists."""
    response = await client.get(
        f"/api/v1/comments/{test_comment.id}/vote",
        headers=auth_headers
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["voted"] is False
    assert data["vote_type"] is None
    assert data["vote_value"] == 0


@pytest.mark.asyncio
async def test_get_vote_summary(
    client: AsyncClient,
    test_comment: Comment,
    test_user: User,
    db_session: AsyncSession
):
    """Test getting vote summary (public endpoint)."""
    # Create additional users for votes
    user2 = User(id=uuid4(), email="user2@test.com", username="user2", hashed_password="hash")
    user3 = User(id=uuid4(), email="user3@test.com", username="user3", hashed_password="hash")
    db_session.add_all([user2, user3])
    await db_session.flush()
    
    # Create some votes in database
    vote1 = Vote(
        id=uuid4(),
        user_id=test_user.id,
        comment_id=test_comment.id,
        vote_value=1
    )
    vote2 = Vote(
        id=uuid4(),
        user_id=user2.id,
        comment_id=test_comment.id,
        vote_value=1
    )
    vote3 = Vote(
        id=uuid4(),
        user_id=user3.id,
        comment_id=test_comment.id,
        vote_value=-1
    )
    
    db_session.add_all([vote1, vote2, vote3])
    await db_session.commit()
    
    # Update comment metrics
    test_comment.vote_score = 1  # 1 + 1 - 1
    test_comment.vote_count = 3
    await db_session.commit()
    
    # Get summary (no auth required)
    response = await client.get(
        f"/api/v1/comments/{test_comment.id}/vote/summary"
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["comment_id"] == str(test_comment.id)
    assert data["vote_score"] == 1
    assert data["vote_count"] == 3


# ========== MULTIPLE USERS TESTS ==========

@pytest.mark.asyncio
async def test_multiple_users_voting(
    client: AsyncClient,
    test_comment: Comment,
    db_session: AsyncSession
):
    """Test that multiple users can vote on the same comment."""
    # Create multiple users
    user1 = User(id=uuid4(), email="user1@test.com", username="user1", hashed_password="hash")
    user2 = User(id=uuid4(), email="user2@test.com", username="user2", hashed_password="hash")
    user3 = User(id=uuid4(), email="user3@test.com", username="user3", hashed_password="hash")
    
    db_session.add_all([user1, user2, user3])
    await db_session.commit()
    
    # Create auth headers for each user
    token1 = create_access_token(user1.id, user1.email)
    token2 = create_access_token(user2.id, user2.email)
    token3 = create_access_token(user3.id, user3.email)
    
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}
    headers3 = {"Authorization": f"Bearer {token3}"}
    
    # User 1 upvotes
    response1 = await client.post(
        f"/api/v1/comments/{test_comment.id}/vote?vote_type=upvote",
        headers=headers1
    )
    assert response1.status_code == 200
    
    # User 2 upvotes
    response2 = await client.post(
        f"/api/v1/comments/{test_comment.id}/vote?vote_type=upvote",
        headers=headers2
    )
    assert response2.status_code == 200
    
    # User 3 downvotes
    response3 = await client.post(
        f"/api/v1/comments/{test_comment.id}/vote?vote_type=downvote",
        headers=headers3
    )
    assert response3.status_code == 200
    
    # Get final summary
    summary_response = await client.get(
        f"/api/v1/comments/{test_comment.id}/vote/summary"
    )
    data = summary_response.json()
    
    # Total: +1 +1 -1 = 1
    assert data["vote_score"] == 1
    assert data["vote_count"] == 3


# ========== COMMENT WITH VOTES IN LIST ==========

@pytest.mark.asyncio
async def test_comment_includes_vote_data(
    client: AsyncClient,
    test_comment: Comment,
    test_article: Article,
    auth_headers: dict
):
    """Test that comment response includes vote data."""
    # Cast a vote
    await client.post(
        f"/api/v1/comments/{test_comment.id}/vote?vote_type=upvote",
        headers=auth_headers
    )
    
    # Get the comment
    response = await client.get(
        f"/api/v1/comments/{test_comment.id}",
        headers=auth_headers
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "vote_score" in data
    assert "vote_count" in data
    assert data["vote_score"] == 1
    assert data["vote_count"] == 1


@pytest.mark.asyncio
async def test_comments_list_includes_vote_data(
    client: AsyncClient,
    test_comment: Comment,
    test_article: Article,
    auth_headers: dict
):
    """Test that comments list includes vote data."""
    # Cast a vote
    await client.post(
        f"/api/v1/comments/{test_comment.id}/vote?vote_type=upvote",
        headers=auth_headers
    )
    
    # Get article comments
    response = await client.get(
        f"/api/v1/comments/article/{test_article.id}",
        headers=auth_headers
    )
    
    # Assertions
    assert response.status_code == 200
    comments = response.json()
    assert len(comments) > 0
    
    # Find our test comment
    test_comment_data = next(
        (c for c in comments if c["id"] == str(test_comment.id)),
        None
    )
    assert test_comment_data is not None
    assert test_comment_data["vote_score"] == 1
    assert test_comment_data["vote_count"] == 1
