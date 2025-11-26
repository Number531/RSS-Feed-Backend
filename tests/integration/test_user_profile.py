"""
Integration tests for user profile endpoints.

Tests GET /me, PATCH /me, DELETE /me, GET /me/stats, POST /me/change-password
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.vote import Vote
from app.models.comment import Comment
from app.models.bookmark import Bookmark


@pytest.mark.integration
class TestGetUserProfile:
    """Test GET /api/v1/users/me endpoint."""
    
    async def test_get_profile_requires_auth(
        self,
        client: AsyncClient
    ):
        """Should return 403 without authentication."""
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 403
    
    async def test_get_profile_success(
        self,
        client: AsyncClient,
        authenticated_user: tuple[User, str]
    ):
        """Should return current user profile."""
        user, token = authenticated_user
        
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(user.id)
        assert data["email"] == user.email
        assert data["username"] == user.username
        assert data["is_active"] == user.is_active
        assert data["is_verified"] == user.is_verified
        assert "created_at" in data
    
    async def test_get_profile_includes_display_name(
        self,
        client: AsyncClient,
        authenticated_user: tuple[User, str]
    ):
        """Should include display_name field (alias for full_name)."""
        user, token = authenticated_user
        
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # display_name should be present (computed field)
        assert "display_name" in data
        # Should match full_name value
        assert data["display_name"] == user.full_name


@pytest.mark.integration
class TestUpdateUserProfile:
    """Test PATCH /api/v1/users/me endpoint."""
    
    async def test_update_profile_requires_auth(
        self,
        client: AsyncClient
    ):
        """Should return 403 without authentication."""
        response = await client.patch(
            "/api/v1/users/me",
            json={"full_name": "New Name"}
        )
        assert response.status_code == 403
    
    async def test_update_full_name(
        self,
        client: AsyncClient,
        authenticated_user: tuple[User, str]
    ):
        """Should update user's full name."""
        user, token = authenticated_user
        
        response = await client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Updated Name"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["full_name"] == "Updated Name"
        assert data["display_name"] == "Updated Name"  # Computed field
    
    async def test_update_display_name_maps_to_full_name(
        self,
        client: AsyncClient,
        authenticated_user: tuple[User, str]
    ):
        """Should accept display_name and map to full_name."""
        user, token = authenticated_user
        
        response = await client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"display_name": "Display Name Test"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Both should show the updated value
        assert data["full_name"] == "Display Name Test"
        assert data["display_name"] == "Display Name Test"
    
    async def test_update_avatar_url(
        self,
        client: AsyncClient,
        authenticated_user: tuple[User, str]
    ):
        """Should update user's avatar URL."""
        user, token = authenticated_user
        
        new_avatar = "https://example.com/avatar.jpg"
        
        response = await client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"avatar_url": new_avatar}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["avatar_url"] == new_avatar
    
    async def test_update_multiple_fields(
        self,
        client: AsyncClient,
        authenticated_user: tuple[User, str]
    ):
        """Should update multiple profile fields at once."""
        user, token = authenticated_user
        
        update_data = {
            "display_name": "Multi Update",
            "avatar_url": "https://example.com/new.jpg"
        }
        
        response = await client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["display_name"] == "Multi Update"
        assert data["avatar_url"] == "https://example.com/new.jpg"
    
    @pytest.mark.skip(reason="Rate limiting requires Redis - manual test only")
    async def test_update_profile_rate_limit(
        self,
        client: AsyncClient,
        authenticated_user: tuple[User, str]
    ):
        """Should enforce 10 updates per hour rate limit."""
        user, token = authenticated_user
        
        # Make 11 requests (should hit rate limit)
        for i in range(11):
            response = await client.patch(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {token}"},
                json={"full_name": f"Name {i}"}
            )
            
            if i < 10:
                assert response.status_code == 200
            else:
                assert response.status_code == 429  # Too Many Requests


@pytest.mark.integration
class TestDeleteUserAccount:
    """Test DELETE /api/v1/users/me endpoint."""
    
    async def test_delete_account_requires_auth(
        self,
        client: AsyncClient
    ):
        """Should return 403 without authentication."""
        response = await client.delete("/api/v1/users/me")
        assert response.status_code == 403
    
    async def test_delete_account_soft_delete(
        self,
        client: AsyncClient,
        authenticated_user: tuple[User, str],
        db: AsyncSession
    ):
        """Should soft delete user account (set is_active=false)."""
        user, token = authenticated_user
        
        response = await client.delete(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 204
        
        # Verify user is marked inactive
        await db.refresh(user)
        assert user.is_active is False
    
    @pytest.mark.skip(reason="Rate limiting requires Redis - manual test only")
    async def test_delete_account_rate_limit(
        self,
        client: AsyncClient,
        authenticated_user: tuple[User, str]
    ):
        """Should enforce 1 deletion per hour rate limit."""
        user, token = authenticated_user
        
        # First deletion should succeed
        response1 = await client.delete(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response1.status_code == 204
        
        # Second immediate deletion should be rate limited
        # (Would need new user/token for real test)


@pytest.mark.integration
class TestUserStatistics:
    """Test GET /api/v1/users/me/stats endpoint."""
    
    async def test_get_stats_requires_auth(
        self,
        client: AsyncClient
    ):
        """Should return 403 without authentication."""
        response = await client.get("/api/v1/users/me/stats")
        assert response.status_code == 403
    
    async def test_get_stats_zero_activity(
        self,
        client: AsyncClient,
        authenticated_user: tuple[User, str]
    ):
        """Should return zero stats for new user."""
        user, token = authenticated_user
        
        response = await client.get(
            "/api/v1/users/me/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_votes"] == 0
        assert data["total_comments"] == 0
        assert data["bookmarks_count"] == 0
        assert data["reading_history_count"] == 0
    
    async def test_get_stats_with_activity(
        self,
        client: AsyncClient,
        authenticated_user: tuple[User, str],
        db: AsyncSession,
        sample_article
    ):
        """Should return accurate counts when user has activity."""
        user, token = authenticated_user
        
        # Create some activity for the user
        # Add votes
        vote1 = Vote(
            user_id=user.id,
            article_id=sample_article.id,
            vote_value=1
        )
        db.add(vote1)
        
        # Add comments
        comment1 = Comment(
            user_id=user.id,
            article_id=sample_article.id,
            content="Test comment",
            is_deleted=False
        )
        db.add(comment1)
        
        # Add bookmarks
        bookmark1 = Bookmark(
            user_id=user.id,
            article_id=sample_article.id
        )
        db.add(bookmark1)
        
        await db.commit()
        
        response = await client.get(
            "/api/v1/users/me/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_votes"] == 1
        assert data["total_comments"] == 1
        assert data["bookmarks_count"] == 1


@pytest.mark.integration
class TestChangePassword:
    """Test POST /api/v1/users/me/change-password endpoint."""
    
    async def test_change_password_requires_auth(
        self,
        client: AsyncClient
    ):
        """Should return 403 without authentication."""
        response = await client.post(
            "/api/v1/users/me/change-password",
            json={
                "current_password": "OldPass123!",
                "new_password": "NewPass456!"
            }
        )
        assert response.status_code == 403
    
    async def test_change_password_success(
        self,
        client: AsyncClient,
        authenticated_user: tuple[User, str]
    ):
        """Should change password successfully."""
        user, token = authenticated_user
        
        # User's original password from fixture
        original_password = "TestPassword123!"
        new_password = "NewSecurePass456!"
        
        response = await client.post(
            "/api/v1/users/me/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": original_password,
                "new_password": new_password
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Password changed successfully"
        assert "updated_at" in data
    
    async def test_change_password_wrong_current(
        self,
        client: AsyncClient,
        authenticated_user: tuple[User, str]
    ):
        """Should return 403 if current password is incorrect."""
        user, token = authenticated_user
        
        response = await client.post(
            "/api/v1/users/me/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "WrongPassword123!",
                "new_password": "NewSecurePass456!"
            }
        )
        
        assert response.status_code == 403
        assert "incorrect" in response.json()["detail"].lower()
    
    async def test_change_password_same_as_current(
        self,
        client: AsyncClient,
        authenticated_user: tuple[User, str]
    ):
        """Should return 422 if new password same as current."""
        user, token = authenticated_user
        
        original_password = "TestPassword123!"
        
        response = await client.post(
            "/api/v1/users/me/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": original_password,
                "new_password": original_password
            }
        )
        
        assert response.status_code == 422
        assert "same" in response.json()["detail"].lower()
    
    async def test_change_password_weak_password(
        self,
        client: AsyncClient,
        authenticated_user: tuple[User, str]
    ):
        """Should return 422 if new password is weak."""
        user, token = authenticated_user
        
        original_password = "TestPassword123!"
        
        # Weak password (no special char)
        response = await client.post(
            "/api/v1/users/me/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": original_password,
                "new_password": "WeakPass123"  # No special char
            }
        )
        
        assert response.status_code == 422
        assert "special character" in response.json()["detail"].lower()
    
    async def test_change_password_login_with_new(
        self,
        client: AsyncClient,
        authenticated_user: tuple[User, str]
    ):
        """Should be able to login with new password after change."""
        user, token = authenticated_user
        
        original_password = "TestPassword123!"
        new_password = "NewSecurePass456!"
        
        # Change password
        change_response = await client.post(
            "/api/v1/users/me/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": original_password,
                "new_password": new_password
            }
        )
        
        assert change_response.status_code == 200
        
        # Try to login with new password
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": user.email,
                "password": new_password
            }
        )
        
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()
    
    @pytest.mark.skip(reason="Rate limiting requires Redis - manual test only")
    async def test_change_password_rate_limit(
        self,
        client: AsyncClient,
        authenticated_user: tuple[User, str]
    ):
        """Should enforce 5 attempts per hour rate limit."""
        user, token = authenticated_user
        
        # Make 6 password change attempts
        for i in range(6):
            response = await client.post(
                "/api/v1/users/me/change-password",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "current_password": f"Wrong{i}!",
                    "new_password": f"NewPass{i}!"
                }
            )
            
            if i < 5:
                assert response.status_code in [403, 422]  # Wrong password
            else:
                assert response.status_code == 429  # Rate limited
