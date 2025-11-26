"""
User Service Module

Handles business logic for user operations including profile management,
validation, and account operations.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.audit import RegistrationAudit
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.services.base_service import BaseService


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
    
    async def create_user(
        self,
        user_data: UserCreate,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> User:
        """
        Create new user with notification preferences atomically.
        
        This method handles user creation and related setup in a single
        database transaction to ensure data consistency. Also logs the
        registration attempt for audit purposes.
        
        Args:
            user_data: User registration data
            ip_address: Client IP address (optional, for audit logging)
            user_agent: Client user agent (optional, for audit logging)
            
        Returns:
            Created user instance
            
        Raises:
            ConflictError: If email or username already exists
            ValidationError: If user data is invalid
        """
        self.log_operation(
            "create_user",
            email=user_data.email,
            username=user_data.username
        )
        
        try:
            # Use nested transaction (savepoint) for atomicity
            async with self.user_repo.db.begin_nested():
                # Create user instance
                user = User(
                    email=user_data.email,
                    username=user_data.username,
                    full_name=user_data.full_name,
                    avatar_url=user_data.avatar_url,
                )
                user.set_password(user_data.password)
                
                # Add user to session and flush to get ID
                self.user_repo.db.add(user)
                await self.user_repo.db.flush()
                
                # Create default notification preferences
                from app.models.notification import UserNotificationPreference
                
                preferences = UserNotificationPreference(
                    id=uuid4(),
                    user_id=user.id,
                    vote_notifications=True,
                    reply_notifications=True,
                    mention_notifications=True,
                    email_notifications=False,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                self.user_repo.db.add(preferences)
            
            # Commit the outer transaction
            await self.user_repo.db.commit()
            await self.user_repo.db.refresh(user)
            
            # Log successful registration
            await self._log_registration_audit(
                user_id=user.id,
                email=user_data.email,
                username=user_data.username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True,
                failure_reason=None,
            )
            
            self.log_operation(
                "create_user_success",
                user_id=str(user.id),
                email=user.email
            )
            
            return user
            
        except IntegrityError as e:
            await self.user_repo.db.rollback()
            # Parse error to determine which constraint was violated
            error_msg = str(e.orig).lower()
            
            if "email" in error_msg or "ix_users_email" in error_msg:
                failure_reason = "Email already registered"
                await self._log_registration_audit(
                    user_id=None,
                    email=user_data.email,
                    username=user_data.username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    failure_reason=failure_reason,
                )
                raise ConflictError(failure_reason)
            elif "username" in error_msg or "ix_users_username" in error_msg:
                failure_reason = "Username already taken"
                await self._log_registration_audit(
                    user_id=None,
                    email=user_data.email,
                    username=user_data.username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    failure_reason=failure_reason,
                )
                raise ConflictError(failure_reason)
            else:
                failure_reason = "User already exists"
                await self._log_registration_audit(
                    user_id=None,
                    email=user_data.email,
                    username=user_data.username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    failure_reason=failure_reason,
                )
                raise ConflictError(failure_reason)
                
        except Exception as e:
            await self.user_repo.db.rollback()
            
            # Log failed registration
            await self._log_registration_audit(
                user_id=None,
                email=user_data.email,
                username=user_data.username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                failure_reason=str(e)[:500],  # Truncate to field limit
            )
            
            self.log_error(
                "create_user",
                e,
                email=user_data.email,
                username=user_data.username
            )
            raise

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

    async def update_user_profile(self, user_id: UUID, update_data: UserUpdate) -> User:
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
            fields=list(update_data.model_dump(exclude_unset=True).keys()),
        )

        try:
            # Get current user
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise NotFoundError(f"User with ID {user_id} not found")

            update_dict = update_data.model_dump(exclude_unset=True)
            
            # Map display_name to full_name for frontend compatibility
            if "display_name" in update_dict:
                update_dict["full_name"] = update_dict.pop("display_name")

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

            self.log_operation("update_user_profile_success", user_id=str(user_id))

            return updated_user

        except (NotFoundError, ConflictError, ValidationError):
            raise
        except Exception as e:
            self.log_error("update_user_profile", e, user_id=str(user_id))
            raise

    async def delete_user_account(self, user_id: UUID, hard_delete: bool = False) -> bool:
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
        self.log_operation("delete_user_account", user_id=str(user_id), hard_delete=hard_delete)

        try:
            if hard_delete:
                success = await self.user_repo.hard_delete(user_id)
            else:
                success = await self.user_repo.delete(user_id)

            if not success:
                raise NotFoundError(f"User with ID {user_id} not found")

            self.log_operation(
                "delete_user_account_success", user_id=str(user_id), hard_delete=hard_delete
            )

            return True

        except NotFoundError:
            raise
        except Exception as e:
            self.log_error("delete_user_account", e, user_id=str(user_id))
            raise

    async def check_email_available(
        self, email: str, exclude_user_id: Optional[UUID] = None
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
        self, username: str, exclude_user_id: Optional[UUID] = None
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
    
    async def _log_registration_audit(
        self,
        email: str,
        username: str,
        success: bool,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None,
    ) -> None:
        """
        Log registration attempt to audit table.
        
        This is an internal helper method that creates audit log entries
        for both successful and failed registration attempts.
        
        Args:
            email: Email address attempted
            username: Username attempted
            success: Whether registration succeeded
            user_id: User ID if registration succeeded
            ip_address: Client IP address
            user_agent: Client user agent
            failure_reason: Reason for failure if not successful
        """
        try:
            audit_entry = RegistrationAudit(
                id=uuid4(),
                user_id=user_id,
                email=email,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                failure_reason=failure_reason,
            )
            
            # Use a separate session/transaction for audit logging
            # This ensures audit logs are recorded even if main transaction fails
            self.user_repo.db.add(audit_entry)
            await self.user_repo.db.commit()
            
        except Exception as e:
            # Don't let audit logging failure break registration flow
            self.log_error(
                "log_registration_audit",
                e,
                email=email,
                username=username,
                success=success,
            )
    
    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str
    ) -> User:
        """
        Change user password with verification.
        
        Args:
            user_id: User UUID
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            Updated user instance
            
        Raises:
            NotFoundError: If user doesn't exist
            ValidationError: If current password is incorrect or new password is same
        """
        self.log_operation("change_password", user_id=str(user_id))
        
        try:
            # Get user
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise NotFoundError(f"User with ID {user_id} not found")
            
            # Verify current password
            if not user.verify_password(current_password):
                raise ValidationError("Current password is incorrect")
            
            # Check new password is different
            if user.verify_password(new_password):
                raise ValidationError("New password cannot be the same as the current password")
            
            # Update password
            updated_user = await self.user_repo.update_password(user_id, new_password)
            
            if not updated_user:
                raise NotFoundError(f"User with ID {user_id} not found")
            
            self.log_operation("change_password_success", user_id=str(user_id))
            
            return updated_user
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.log_error("change_password", e, user_id=str(user_id))
            raise
