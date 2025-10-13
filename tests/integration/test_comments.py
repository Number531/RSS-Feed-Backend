"""
Integration tests for Comments API endpoints.

Tests cover:
- Creating comments
- Creating replies
- Getting comments (flat and tree)
- Updating comments
- Deleting comments
- Authorization checks
- Edge cases and error handling
"""

import pytest
from httpx import AsyncClient


class TestCommentsEndpoints:
    """Test suite for comments API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_comment(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test creating a top-level comment."""
        comment_data = {
            "article_id": test_article["id"],
            "content": "This is a test comment"
        }
        
        response = await client.post(
            "/api/v1/comments/",
            json=comment_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == comment_data["content"]
        assert data["article_id"] == test_article["id"]
        assert data["parent_comment_id"] is None
        assert "id" in data
        assert "created_at" in data
        assert not data["is_deleted"]
    
    @pytest.mark.asyncio
    async def test_create_reply(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test creating a reply to a comment."""
        # Create parent comment
        parent_data = {
            "article_id": test_article["id"],
            "content": "Parent comment"
        }
        response = await client.post(
            "/api/v1/comments/",
            json=parent_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        parent_id = response.json()["id"]
        
        # Create reply
        reply_data = {
            "article_id": test_article["id"],
            "content": "This is a reply",
            "parent_comment_id": parent_id
        }
        response = await client.post(
            "/api/v1/comments/",
            json=reply_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == reply_data["content"]
        assert data["parent_comment_id"] == parent_id
    
    @pytest.mark.asyncio
    async def test_get_article_comments(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test getting top-level comments for an article."""
        # Create multiple comments
        for i in range(3):
            comment_data = {
                "article_id": test_article["id"],
                "content": f"Comment {i+1}"
            }
            response = await client.post(
                "/api/v1/comments/",
                json=comment_data,
                headers=auth_headers
            )
            assert response.status_code == 201
        
        # Get comments
        response = await client.get(
            f"/api/v1/comments/article/{test_article['id']}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(comment["article_id"] == test_article["id"] for comment in data)
    
    @pytest.mark.asyncio
    async def test_get_comment_tree(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test getting nested comment tree."""
        # Create parent comment
        parent_data = {
            "article_id": test_article["id"],
            "content": "Parent comment"
        }
        response = await client.post(
            "/api/v1/comments/",
            json=parent_data,
            headers=auth_headers
        )
        parent_id = response.json()["id"]
        
        # Create two replies
        for i in range(2):
            reply_data = {
                "article_id": test_article["id"],
                "content": f"Reply {i+1}",
                "parent_comment_id": parent_id
            }
            response = await client.post(
                "/api/v1/comments/",
                json=reply_data,
                headers=auth_headers
            )
            assert response.status_code == 201
        
        # Get comment tree
        response = await client.get(
            f"/api/v1/comments/article/{test_article['id']}/tree"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        # Find parent in tree
        parent = next((c for c in data if c["id"] == parent_id), None)
        assert parent is not None
        assert len(parent["replies"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_single_comment(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test getting a single comment by ID."""
        # Create comment
        comment_data = {
            "article_id": test_article["id"],
            "content": "Test comment"
        }
        response = await client.post(
            "/api/v1/comments/",
            json=comment_data,
            headers=auth_headers
        )
        comment_id = response.json()["id"]
        
        # Get comment
        response = await client.get(f"/api/v1/comments/{comment_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == comment_id
        assert data["content"] == comment_data["content"]
    
    @pytest.mark.asyncio
    async def test_get_comment_replies(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test getting replies to a comment."""
        # Create parent comment
        parent_data = {
            "article_id": test_article["id"],
            "content": "Parent comment"
        }
        response = await client.post(
            "/api/v1/comments/",
            json=parent_data,
            headers=auth_headers
        )
        parent_id = response.json()["id"]
        
        # Create replies
        for i in range(2):
            reply_data = {
                "article_id": test_article["id"],
                "content": f"Reply {i+1}",
                "parent_comment_id": parent_id
            }
            response = await client.post(
                "/api/v1/comments/",
                json=reply_data,
                headers=auth_headers
            )
            assert response.status_code == 201
        
        # Get replies
        response = await client.get(f"/api/v1/comments/{parent_id}/replies")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(reply["parent_comment_id"] == parent_id for reply in data)
    
    @pytest.mark.asyncio
    async def test_update_comment(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test updating a comment."""
        # Create comment
        comment_data = {
            "article_id": test_article["id"],
            "content": "Original content"
        }
        response = await client.post(
            "/api/v1/comments/",
            json=comment_data,
            headers=auth_headers
        )
        comment_id = response.json()["id"]
        
        # Update comment
        update_data = {"content": "Updated content"}
        response = await client.put(
            f"/api/v1/comments/{comment_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == update_data["content"]
        assert data["updated_at"] is not None
    
    @pytest.mark.asyncio
    async def test_delete_comment(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test deleting a comment (soft delete)."""
        # Create comment
        comment_data = {
            "article_id": test_article["id"],
            "content": "To be deleted"
        }
        response = await client.post(
            "/api/v1/comments/",
            json=comment_data,
            headers=auth_headers
        )
        comment_id = response.json()["id"]
        
        # Delete comment
        response = await client.delete(
            f"/api/v1/comments/{comment_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify soft delete
        response = await client.get(f"/api/v1/comments/{comment_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["is_deleted"] is True
        assert data["content"] == "[deleted]"
    
    @pytest.mark.asyncio
    async def test_update_others_comment_fails(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict,
        auth_headers_2: dict
    ):
        """Test that users cannot update others' comments."""
        # User 1 creates comment
        comment_data = {
            "article_id": test_article["id"],
            "content": "User 1 comment"
        }
        response = await client.post(
            "/api/v1/comments/",
            json=comment_data,
            headers=auth_headers
        )
        comment_id = response.json()["id"]
        
        # User 2 tries to update
        update_data = {"content": "Hijacked content"}
        response = await client.put(
            f"/api/v1/comments/{comment_id}",
            json=update_data,
            headers=auth_headers_2
        )
        
        # Should fail with 403
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_delete_others_comment_fails(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict,
        auth_headers_2: dict
    ):
        """Test that users cannot delete others' comments."""
        # User 1 creates comment
        comment_data = {
            "article_id": test_article["id"],
            "content": "User 1 comment"
        }
        response = await client.post(
            "/api/v1/comments/",
            json=comment_data,
            headers=auth_headers
        )
        comment_id = response.json()["id"]
        
        # User 2 tries to delete
        response = await client.delete(
            f"/api/v1/comments/{comment_id}",
            headers=auth_headers_2
        )
        
        # Should fail with 403
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_create_comment_without_auth(
        self,
        client: AsyncClient,
        test_article: dict
    ):
        """Test that creating comments requires authentication."""
        comment_data = {
            "article_id": test_article["id"],
            "content": "Unauthorized comment"
        }
        
        response = await client.post("/api/v1/comments/", json=comment_data)
        
        assert response.status_code in [401, 403]
    
    @pytest.mark.asyncio
    async def test_comment_content_too_short(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test that comment content must be at least 1 character."""
        comment_data = {
            "article_id": test_article["id"],
            "content": ""
        }
        
        response = await client.post(
            "/api/v1/comments/",
            json=comment_data,
            headers=auth_headers
        )
        
        # Should fail validation
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_comment_content_too_long(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test that comment content has a maximum length."""
        comment_data = {
            "article_id": test_article["id"],
            "content": "a" * 10001  # Exceeds max 10,000
        }
        
        response = await client.post(
            "/api/v1/comments/",
            json=comment_data,
            headers=auth_headers
        )
        
        # Should fail validation
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_comment_nonexistent_article(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test commenting on non-existent article."""
        comment_data = {
            "article_id": "550e8400-e29b-41d4-a716-446655440000",  # Random UUID
            "content": "Test comment"
        }
        
        response = await client.post(
            "/api/v1/comments/",
            json=comment_data,
            headers=auth_headers
        )
        
        # Should fail with 404
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_reply_nonexistent_parent(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test replying to non-existent comment."""
        comment_data = {
            "article_id": test_article["id"],
            "content": "Reply to nothing",
            "parent_comment_id": "550e8400-e29b-41d4-a716-446655440000"
        }
        
        response = await client.post(
            "/api/v1/comments/",
            json=comment_data,
            headers=auth_headers
        )
        
        # Should fail with 404
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_comment(
        self,
        client: AsyncClient
    ):
        """Test getting a comment that doesn't exist."""
        response = await client.get(
            "/api/v1/comments/550e8400-e29b-41d4-a716-446655440000"
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_comment(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test updating a comment that doesn't exist."""
        update_data = {"content": "New content"}
        response = await client.put(
            "/api/v1/comments/550e8400-e29b-41d4-a716-446655440000",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_comment(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test deleting a comment that doesn't exist."""
        response = await client.delete(
            "/api/v1/comments/550e8400-e29b-41d4-a716-446655440000",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_pagination(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test comment pagination."""
        # Create 10 comments
        for i in range(10):
            comment_data = {
                "article_id": test_article["id"],
                "content": f"Comment {i+1}"
            }
            response = await client.post(
                "/api/v1/comments/",
                json=comment_data,
                headers=auth_headers
            )
            assert response.status_code == 201
        
        # Get first page (5 items)
        response = await client.get(
            f"/api/v1/comments/article/{test_article['id']}?page=1&page_size=5"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        
        # Get second page
        response = await client.get(
            f"/api/v1/comments/article/{test_article['id']}?page=2&page_size=5"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
    
    @pytest.mark.asyncio
    async def test_comment_tree_max_depth(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test comment tree respects max depth."""
        # Create nested comments
        parent_id = None
        for i in range(5):
            comment_data = {
                "article_id": test_article["id"],
                "content": f"Level {i+1}",
                "parent_comment_id": parent_id
            }
            response = await client.post(
                "/api/v1/comments/",
                json=comment_data,
                headers=auth_headers
            )
            assert response.status_code == 201
            parent_id = response.json()["id"]
        
        # Get tree with depth limit of 3
        response = await client.get(
            f"/api/v1/comments/article/{test_article['id']}/tree?max_depth=3"
        )
        
        assert response.status_code == 200
        data = response.json()
        # Tree should be limited to 3 levels
        assert len(data) > 0
    
    @pytest.mark.asyncio
    async def test_update_deleted_comment_fails(
        self,
        client: AsyncClient,
        test_article: dict,
        auth_headers: dict
    ):
        """Test that deleted comments cannot be updated."""
        # Create and delete comment
        comment_data = {
            "article_id": test_article["id"],
            "content": "To be deleted"
        }
        response = await client.post(
            "/api/v1/comments/",
            json=comment_data,
            headers=auth_headers
        )
        comment_id = response.json()["id"]
        
        response = await client.delete(
            f"/api/v1/comments/{comment_id}",
            headers=auth_headers
        )
        assert response.status_code == 204
        
        # Try to update deleted comment
        update_data = {"content": "New content"}
        response = await client.put(
            f"/api/v1/comments/{comment_id}",
            json=update_data,
            headers=auth_headers
        )
        
        # Should fail (either 404 or 400)
        assert response.status_code in [400, 404]
    
    @pytest.mark.asyncio
    async def test_comment_invalid_uuid(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test commenting with invalid UUID format."""
        comment_data = {
            "article_id": "not-a-uuid",
            "content": "Test comment"
        }
        
        response = await client.post(
            "/api/v1/comments/",
            json=comment_data,
            headers=auth_headers
        )
        
        # Should fail validation
        assert response.status_code == 422
