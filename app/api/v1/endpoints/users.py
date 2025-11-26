"""
User Profile API Endpoints

Provides endpoints for user profile management including viewing,
updating, and deleting user accounts.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_user_service
from app.core.exceptions import ValidationError
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.middleware.rate_limit import limiter
from app.models.bookmark import Bookmark
from app.models.comment import Comment
from app.models.reading_history import ReadingHistory
from app.models.user import User
from app.models.vote import Vote
from app.schemas.user import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    UserResponse,
    UserStatsResponse,
    UserUpdate,
)
from app.services.user_service import UserService

router = APIRouter()


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get current user's profile.

    **Authentication Required**: Yes (Bearer token)

    **Returns**:
    - User profile information including:
      - id, email, username
      - full_name, avatar_url
      - is_active, is_verified
      - created_at, last_login_at

    **Example**:
    ```
    GET /api/v1/users/me
    Authorization: Bearer <token>
    ```

    **Response**:
    ```json
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "username": "johndoe",
      "full_name": "John Doe",
      "avatar_url": "https://example.com/avatar.jpg",
      "is_active": true,
      "is_verified": true,
      "oauth_provider": null,
      "created_at": "2025-01-01T00:00:00Z",
      "last_login_at": "2025-01-10T12:00:00Z"
    }
    ```
    """
    return current_user


@router.patch("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
@limiter.limit("10/hour")
async def update_current_user_profile(
    request: Request,
    response: Response,
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update current user's profile.

    **Authentication Required**: Yes (Bearer token)

    **Request Body** (all fields optional):
    - **email**: New email address (must be unique)
    - **username**: New username (must be unique, 3-50 chars)
    - **full_name**: User's full name (max 255 chars)
    - **avatar_url**: URL to user's avatar image
    - **password**: New password (min 8 chars, will be hashed)

    **Returns**:
    - Updated user profile

    **Raises**:
    - **409 Conflict**: Email or username already taken
    - **422 Validation Error**: Invalid data format

    **Example**:
    ```
    PATCH /api/v1/users/me
    Authorization: Bearer <token>
    Content-Type: application/json

    {
      "full_name": "John Smith",
      "avatar_url": "https://example.com/new-avatar.jpg"
    }
    ```

    **Notes**:
    - Only provided fields will be updated
    - Email and username uniqueness is validated
    - Password will be securely hashed before storage
    """
    try:
        updated_user = await user_service.update_user_profile(
            user_id=current_user.id, update_data=update_data
        )
        return updated_user
    except Exception as e:
        # Let the exception handler middleware handle specific exceptions
        raise


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("1/hour")
async def delete_current_user_account(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Delete current user's account (soft delete).

    **Authentication Required**: Yes (Bearer token)

    **Behavior**:
    - Marks user account as **inactive** (soft delete)
    - User can no longer log in
    - User data is retained in database
    - All user's votes and comments remain but are anonymized

    **Returns**:
    - 204 No Content on success

    **Example**:
    ```
    DELETE /api/v1/users/me
    Authorization: Bearer <token>
    ```

    **Notes**:
    - This is a **soft delete** - account is deactivated not removed
    - For permanent deletion, contact support
    - After deletion, JWT tokens will no longer be valid
    - Consider implementing account recovery period

    **Security**:
    - Requires valid authentication
    - User must be currently active
    """
    await user_service.delete_user_account(
        user_id=current_user.id, hard_delete=False  # Soft delete by default for safety
    )
    # FastAPI automatically returns 204 with no content


@router.get("/me/stats", response_model=UserStatsResponse, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def get_current_user_stats(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user's activity statistics.

    **Authentication Required**: Yes (Bearer token)

    **Returns**:
    - User activity statistics including:
      - Total votes cast
      - Total comments made  
      - Total bookmarks saved
      - Total articles read

    **Example**:
    ```
    GET /api/v1/users/me/stats
    Authorization: Bearer <token>
    ```

    **Response**:
    ```json
    {
      "total_votes": 145,
      "total_comments": 32,
      "bookmarks_count": 67,
      "reading_history_count": 234
    }
    ```
    """
    # Query vote count
    vote_result = await db.execute(
        select(func.count(Vote.id)).where(Vote.user_id == current_user.id)
    )
    total_votes = vote_result.scalar() or 0
    
    # Query comment count (exclude deleted)
    comment_result = await db.execute(
        select(func.count(Comment.id)).where(
            Comment.user_id == current_user.id,
            Comment.is_deleted == False
        )
    )
    total_comments = comment_result.scalar() or 0
    
    # Query bookmark count
    bookmark_result = await db.execute(
        select(func.count(Bookmark.id)).where(Bookmark.user_id == current_user.id)
    )
    bookmarks_count = bookmark_result.scalar() or 0
    
    # Query reading history count
    reading_result = await db.execute(
        select(func.count(ReadingHistory.id)).where(ReadingHistory.user_id == current_user.id)
    )
    reading_history_count = reading_result.scalar() or 0
    
    return UserStatsResponse(
        total_votes=total_votes,
        total_comments=total_comments,
        bookmarks_count=bookmarks_count,
        reading_history_count=reading_history_count,
    )


@router.post("/me/change-password", response_model=ChangePasswordResponse, status_code=status.HTTP_200_OK)
@limiter.limit("5/hour")
async def change_password(
    request: Request,
    response: Response,
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Change current user's password.

    **Authentication Required**: Yes (Bearer token)

    **Request Body**:
    - **current_password**: Current password for verification
    - **new_password**: New password (must meet security requirements)

    **Returns**:
    - Success message with timestamp

    **Raises**:
    - **400 Bad Request**: Password validation failed
    - **401 Unauthorized**: Not authenticated
    - **403 Forbidden**: Current password is incorrect
    - **422 Unprocessable Entity**: New password same as current

    **Example**:
    ```
    POST /api/v1/users/me/change-password
    Authorization: Bearer <token>
    Content-Type: application/json

    {
      "current_password": "OldSecurePass123!",
      "new_password": "NewSecurePass456!"
    }
    ```

    **Response**:
    ```json
    {
      "message": "Password changed successfully",
      "updated_at": "2025-11-26T06:45:00Z"
    }
    ```

    **Security Notes**:
    - Rate limited to 5 attempts per hour
    - Current password must be verified
    - New password must meet strength requirements
    - New password cannot be same as current
    """
    try:
        updated_user = await user_service.change_password(
            user_id=current_user.id,
            current_password=password_data.current_password,
            new_password=password_data.new_password,
        )
        
        return ChangePasswordResponse(
            message="Password changed successfully",
            updated_at=updated_user.updated_at or datetime.now(timezone.utc),
        )
    except ValidationError as e:
        # Convert ValidationError to HTTPException
        if "incorrect" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e),
            )
    except Exception as e:
        # Let other exceptions be handled by middleware
        raise
