"""
User Repository Module

Handles database operations for user management including retrieval,
updates, and deletion.
"""

from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Repository for user database operations."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize user repository.
        
        Args:
            db: Async database session
        """
        self.db = db
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User UUID
            
        Returns:
            User instance or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: User email address
            
        Returns:
            User instance or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username
            
        Returns:
            User instance or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def update(
        self,
        user_id: UUID,
        **kwargs
    ) -> Optional[User]:
        """
        Update user fields.
        
        Args:
            user_id: User UUID
            **kwargs: Fields to update (email, username, full_name, avatar_url)
            
        Returns:
            Updated user instance or None if not found
        """
        user = await self.get_by_id(user_id)
        
        if not user:
            return None
        
        # Update allowed fields
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def update_password(
        self,
        user_id: UUID,
        new_password: str
    ) -> Optional[User]:
        """
        Update user password.
        
        Args:
            user_id: User UUID
            new_password: Plain text password to hash and set
            
        Returns:
            Updated user instance or None if not found
        """
        user = await self.get_by_id(user_id)
        
        if not user:
            return None
        
        user.set_password(new_password)
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def delete(self, user_id: UUID) -> bool:
        """
        Soft delete user by marking as inactive.
        
        Args:
            user_id: User UUID
            
        Returns:
            True if user was deleted, False if not found
        """
        user = await self.get_by_id(user_id)
        
        if not user:
            return False
        
        user.is_active = False
        await self.db.commit()
        
        return True
    
    async def hard_delete(self, user_id: UUID) -> bool:
        """
        Permanently delete user from database.
        
        WARNING: This will cascade delete all user's votes and comments!
        
        Args:
            user_id: User UUID
            
        Returns:
            True if user was deleted, False if not found
        """
        user = await self.get_by_id(user_id)
        
        if not user:
            return False
        
        await self.db.delete(user)
        await self.db.commit()
        
        return True
    
    async def email_exists(self, email: str, exclude_user_id: Optional[UUID] = None) -> bool:
        """
        Check if email is already taken by another user.
        
        Args:
            email: Email to check
            exclude_user_id: Optional user ID to exclude from check (for updates)
            
        Returns:
            True if email exists, False otherwise
        """
        query = select(User).where(User.email == email)
        
        if exclude_user_id:
            query = query.where(User.id != exclude_user_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def username_exists(self, username: str, exclude_user_id: Optional[UUID] = None) -> bool:
        """
        Check if username is already taken by another user.
        
        Args:
            username: Username to check
            exclude_user_id: Optional user ID to exclude from check (for updates)
            
        Returns:
            True if username exists, False otherwise
        """
        query = select(User).where(User.username == username)
        
        if exclude_user_id:
            query = query.where(User.id != exclude_user_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
