"""
User Profile API Endpoints

Provides endpoints for user profile management including viewing,
updating, and deleting user accounts.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_user_service
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
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
async def update_current_user_profile(
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
async def delete_current_user_account(
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


@router.get("/me/stats", status_code=status.HTTP_200_OK)
async def get_current_user_stats(current_user: User = Depends(get_current_active_user)):
    """
    Get current user's activity statistics.

    **Authentication Required**: Yes (Bearer token)

    **Returns**:
    - User activity statistics including:
      - Total votes cast
      - Total comments made
      - Account age
      - Karma score (upvotes received)

    **Example**:
    ```
    GET /api/v1/users/me/stats
    Authorization: Bearer <token>
    ```

    **Status**: Coming soon - Implementation pending
    """
    # TODO: Implement user statistics
    # This would require aggregating data from votes and comments tables
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User statistics endpoint not yet implemented",
    )
