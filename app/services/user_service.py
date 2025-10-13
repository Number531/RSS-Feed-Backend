"""
User Service Module

Handles business logic for user operations including profile management,
validation, and account operations.
"""

from typing import Optional
from uuid import UUID

from app.services.base_service import BaseService
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.user import UserUpdate
from app.core.exceptions import ValidationError, NotFoundError, ConflictError


class UserService(BaseService):
    """
    Service for user-related business logic.
    
    Handles:
    - User profile retrieval
    - Profile updates with validation
    - Account deletion
    - Email and username uniqueness checks
    """
    
    def __init__(self, user_repository: UserRepository):
        """
        Initialize user service.
        
        Args:
            user_repository: User repository instance
        """
        super().__init__()
        self.user_repo = user_repository
    
    async def get_user_by_id(self, user_id: UUID) -> User:
        """
        Get user by ID.
        
        Args:
            user_id: User UUID
            
        Returns:
            User instance
            
        Raises:
            NotFoundError: If user doesn't exist
        """
        self.log_operation("get_user_by_id", user_id=str(user_id))
        
        try:
            user = await self.user_repo.get_by_id(user_id)
            
            if not user:
                raise NotFoundError(f"User with ID {user_id} not found")
            
            return user
            
        except NotFoundError:
            raise
        except Exception as e:
            self.log_error("get_user_by_id", e, user_id=str(user_id))
            raise
    
    async def update_user_profile(
        self,
        user_id: UUID,
        update_data: UserUpdate
    ) -> User:
        """
        Update user profile.
        
        Args:
            user_id: User UUID
            update_data: Profile update data
            
        Returns:
            Updated user instance
            
        Raises:
            NotFoundError: If user doesn't exist
            ConflictError: If email/username already taken
            ValidationError: If data is invalid
        """
        self.log_operation(
            "update_user_profile",
            user_id=str(user_id),
            fields=list(update_data.model_dump(exclude_unset=True).keys())
        )
        
        try:
            # Get current user
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise NotFoundError(f"User with ID {user_id} not found")
            
            update_dict = update_data.model_dump(exclude_unset=True)
            
            # Validate email uniqueness if being updated
            if "email" in update_dict:
                email = update_dict["email"]
                if await self.user_repo.email_exists(email, exclude_user_id=user_id):
                    raise ConflictError("Email already registered")
            
            # Validate username uniqueness if being updated
            if "username" in update_dict:
                username = update_dict["username"]
                if await self.user_repo.username_exists(username, exclude_user_id=user_id):
                    raise ConflictError("Username already taken")
            
            # Handle password update separately
            password = update_dict.pop("password", None)
            
            # Update basic profile fields
            if update_dict:
                updated_user = await self.user_repo.update(user_id, **update_dict)
            else:
                updated_user = user
            
            # Update password if provided
            if password:
                updated_user = await self.user_repo.update_password(user_id, password)
            
            if not updated_user:
                raise NotFoundError(f"User with ID {user_id} not found")
            
            self.log_operation(
                "update_user_profile_success",
                user_id=str(user_id)
            )
            
            return updated_user
            
        except (NotFoundError, ConflictError, ValidationError):
            raise
        except Exception as e:
            self.log_error("update_user_profile", e, user_id=str(user_id))
            raise
    
    async def delete_user_account(
        self,
        user_id: UUID,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete user account.
        
        Args:
            user_id: User UUID
            hard_delete: If True, permanently delete; if False, soft delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If user doesn't exist
        """
        self.log_operation(
            "delete_user_account",
            user_id=str(user_id),
            hard_delete=hard_delete
        )
        
        try:
            if hard_delete:
                success = await self.user_repo.hard_delete(user_id)
            else:
                success = await self.user_repo.delete(user_id)
            
            if not success:
                raise NotFoundError(f"User with ID {user_id} not found")
            
            self.log_operation(
                "delete_user_account_success",
                user_id=str(user_id),
                hard_delete=hard_delete
            )
            
            return True
            
        except NotFoundError:
            raise
        except Exception as e:
            self.log_error("delete_user_account", e, user_id=str(user_id))
            raise
    
    async def check_email_available(
        self,
        email: str,
        exclude_user_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if email is available for use.
        
        Args:
            email: Email to check
            exclude_user_id: Optional user ID to exclude from check
            
        Returns:
            True if available, False if taken
        """
        try:
            exists = await self.user_repo.email_exists(email, exclude_user_id)
            return not exists
        except Exception as e:
            self.log_error("check_email_available", e, email=email)
            raise
    
    async def check_username_available(
        self,
        username: str,
        exclude_user_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if username is available for use.
        
        Args:
            username: Username to check
            exclude_user_id: Optional user ID to exclude from check
            
        Returns:
            True if available, False if taken
        """
        try:
            exists = await self.user_repo.username_exists(username, exclude_user_id)
            return not exists
        except Exception as e:
            self.log_error("check_username_available", e, username=username)
            raise
