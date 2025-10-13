"""
Integration tests for Votes API endpoints.

Tests cover:
- Casting votes (upvote/downvote)
- Updating votes
- Removing votes
- Getting user votes
- Edge cases and error handling
"""

import pytest
from httpx import AsyncClient


class TestVotesEndpoints:
    """Test suite for votes API endpoints."""
    
    @pytest.mark.asyncio
    async def test_cast_upvote(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test casting an upvote on an article."""
        vote_data = {
            "article_id": test_article["id"],
            "vote_value": 1
        }
        
        response = await client.post(
            "/api/v1/votes/",
            json=vote_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["article_id"] == test_article["id"]
        assert data["vote_value"] == 1
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_cast_downvote(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test casting a downvote on an article."""
        vote_data = {
            "article_id": test_article["id"],
            "vote_value": -1
        }
        
        response = await client.post(
            "/api/v1/votes/",
            json=vote_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["article_id"] == test_article["id"]
        assert data["vote_value"] == -1
    
    @pytest.mark.asyncio
    async def test_update_vote(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test updating an existing vote."""
        # First cast upvote
        vote_data = {
            "article_id": test_article["id"],
            "vote_value": 1
        }
        response = await client.post(
            "/api/v1/votes/",
            json=vote_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        
        # Update to downvote
        vote_data["vote_value"] = -1
        response = await client.post(
            "/api/v1/votes/",
            json=vote_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["vote_value"] == -1
        
        # Verify only one vote exists
        response = await client.get(
            f"/api/v1/votes/article/{test_article['id']}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["vote_value"] == -1
    
    @pytest.mark.asyncio
    async def test_remove_vote_with_zero(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test removing vote by setting vote_value to 0."""
        # First cast vote
        vote_data = {
            "article_id": test_article["id"],
            "vote_value": 1
        }
        response = await client.post(
            "/api/v1/votes/",
            json=vote_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        
        # Remove by setting to 0
        vote_data["vote_value"] = 0
        response = await client.post(
            "/api/v1/votes/",
            json=vote_data,
            headers=auth_headers
        )
        
        # Should succeed (service handles removal)
        assert response.status_code in [200, 201, 204]
        
        # Verify vote is removed
        response = await client.get(
            f"/api/v1/votes/article/{test_article['id']}",
            headers=auth_headers
        )
        # Should return null or 404
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert response.json() is None
    
    @pytest.mark.asyncio
    async def test_remove_vote_with_delete(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test removing vote using DELETE endpoint."""
        # First cast vote
        vote_data = {
            "article_id": test_article["id"],
            "vote_value": 1
        }
        response = await client.post(
            "/api/v1/votes/",
            json=vote_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        
        # Remove with DELETE
        response = await client.delete(
            f"/api/v1/votes/{test_article['id']}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify vote is removed
        response = await client.get(
            f"/api/v1/votes/article/{test_article['id']}",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert response.json() is None
    
    @pytest.mark.asyncio
    async def test_get_user_vote(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test getting user's vote on an article."""
        # Cast vote
        vote_data = {
            "article_id": test_article["id"],
            "vote_value": 1
        }
        response = await client.post(
            "/api/v1/votes/",
            json=vote_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        
        # Get vote
        response = await client.get(
            f"/api/v1/votes/article/{test_article['id']}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["article_id"] == test_article["id"]
        assert data["vote_value"] == 1
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_vote(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test getting vote when user hasn't voted."""
        response = await client.get(
            f"/api/v1/votes/article/{test_article['id']}",
            headers=auth_headers
        )
        
        # Should return null or empty
        assert response.status_code == 200
        assert response.json() is None
    
    @pytest.mark.asyncio
    async def test_vote_without_auth(
        self,
        client: AsyncClient,
        test_article: dict
    ):
        """Test that voting requires authentication."""
        vote_data = {
            "article_id": test_article["id"],
            "vote_value": 1
        }
        
        response = await client.post("/api/v1/votes/", json=vote_data)
        
        assert response.status_code in [401, 403]
    
    @pytest.mark.asyncio
    async def test_vote_invalid_value(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test voting with invalid vote value."""
        vote_data = {
            "article_id": test_article["id"],
            "vote_value": 5  # Invalid
        }
        
        response = await client.post(
            "/api/v1/votes/",
            json=vote_data,
            headers=auth_headers
        )
        
        # Should fail validation
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_vote_nonexistent_article(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test voting on non-existent article."""
        vote_data = {
            "article_id": "550e8400-e29b-41d4-a716-446655440000",  # Random UUID
            "vote_value": 1
        }
        
        response = await client.post(
            "/api/v1/votes/",
            json=vote_data,
            headers=auth_headers
        )
        
        # Should fail with 404
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_multiple_users_voting(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict,
        auth_headers_2: dict
    ):
        """Test that multiple users can vote on the same article."""
        # User 1 upvotes
        vote_data = {
            "article_id": test_article["id"],
            "vote_value": 1
        }
        response = await client.post(
            "/api/v1/votes/",
            json=vote_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        
        # User 2 downvotes
        vote_data["vote_value"] = -1
        response = await client.post(
            "/api/v1/votes/",
            json=vote_data,
            headers=auth_headers_2
        )
        assert response.status_code == 201
        
        # Verify both votes exist separately
        response = await client.get(
            f"/api/v1/votes/article/{test_article['id']}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["vote_value"] == 1
        
        response = await client.get(
            f"/api/v1/votes/article/{test_article['id']}",
            headers=auth_headers_2
        )
        assert response.status_code == 200
        assert response.json()["vote_value"] == -1
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_vote(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test deleting a vote that doesn't exist."""
        response = await client.delete(
            f"/api/v1/votes/{test_article['id']}",
            headers=auth_headers
        )
        
        # Should fail with 404
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_vote_invalid_uuid(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test voting with invalid article UUID format."""
        vote_data = {
            "article_id": "not-a-uuid",
            "vote_value": 1
        }
        
        response = await client.post(
            "/api/v1/votes/",
            json=vote_data,
            headers=auth_headers
        )
        
        # Should fail validation
        assert response.status_code == 422
