"""
Notification service for managing user notifications and preferences.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.notification import Notification, UserNotificationPreference
from app.models.user import User
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationPreferenceCreate,
    NotificationPreferenceUpdate,
    NotificationStats,
)


class NotificationService:
    """Service for managing notifications and user preferences."""
    
    @staticmethod
    async def create_notification(
        db: AsyncSession,
        notification_data: NotificationCreate,
    ) -> Notification:
        """
        Create a new notification for a user.
        
        Args:
            db: Database session
            notification_data: Notification creation data
            
        Returns:
            Created notification
            
        Raises:
            HTTPException: If user preferences prevent the notification
        """
        # Check if user has notifications enabled for this type
        preferences = await NotificationService.get_user_preferences(db, notification_data.user_id)
        
        if preferences:
            # Check if user has disabled this notification type
            if notification_data.type == "vote" and not preferences.vote_notifications:
                return None  # Silently skip if disabled
            elif notification_data.type == "reply" and not preferences.reply_notifications:
                return None
            elif notification_data.type == "mention" and not preferences.mention_notifications:
                return None
        
        # Create notification
        notification = Notification(
            user_id=notification_data.user_id,
            type=notification_data.type,
            title=notification_data.title,
            message=notification_data.message,
            related_entity_type=notification_data.related_entity_type,
            related_entity_id=notification_data.related_entity_id,
            actor_id=notification_data.actor_id,
        )
        
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        
        return notification
    
    @staticmethod
    async def create_vote_notification(
        db: AsyncSession,
        recipient_id: UUID,
        actor_id: UUID,
        entity_type: str,
        entity_id: UUID,
        vote_value: int,
    ) -> Optional[Notification]:
        """
        Create a notification for a vote on a comment or article.
        
        Args:
            db: Database session
            recipient_id: ID of user to notify (content author)
            actor_id: ID of user who voted
            entity_type: Type of entity ('article' or 'comment')
            entity_id: ID of the voted entity
            vote_value: Vote value (1 for upvote, -1 for downvote)
            
        Returns:
            Created notification or None if skipped
        """
        # Don't notify users of their own votes
        if recipient_id == actor_id:
            return None
        
        # Get actor username for notification message
        result = await db.execute(select(User).where(User.id == actor_id))
        actor = result.scalar_one_or_none()
        if not actor:
            return None
        
        # Only notify on upvotes (not downvotes)
        if vote_value != 1:
            return None
        
        # Create notification
        vote_notification = NotificationCreate(
            user_id=recipient_id,
            actor_id=actor_id,
            type="vote",
            title=f"New upvote on your {entity_type}",
            message=f"{actor.username} upvoted your {entity_type}",
            related_entity_type=entity_type,
            related_entity_id=entity_id,
        )
        
        return await NotificationService.create_notification(db, vote_notification)
    
    @staticmethod
    async def create_reply_notification(
        db: AsyncSession,
        recipient_id: UUID,
        actor_id: UUID,
        comment_id: UUID,
        article_id: UUID,
    ) -> Optional[Notification]:
        """
        Create a notification for a reply to a comment.
        
        Args:
            db: Database session
            recipient_id: ID of user to notify (parent comment author)
            actor_id: ID of user who replied
            comment_id: ID of the reply comment
            article_id: ID of the article
            
        Returns:
            Created notification or None if skipped
        """
        # Don't notify users of their own replies
        if recipient_id == actor_id:
            return None
        
        # Get actor username for notification message
        result = await db.execute(select(User).where(User.id == actor_id))
        actor = result.scalar_one_or_none()
        if not actor:
            return None
        
        # Create notification
        reply_notification = NotificationCreate(
            user_id=recipient_id,
            actor_id=actor_id,
            type="reply",
            title="New reply to your comment",
            message=f"{actor.username} replied to your comment",
            related_entity_type="comment",
            related_entity_id=comment_id,
        )
        
        return await NotificationService.create_notification(db, reply_notification)
    
    @staticmethod
    async def get_user_notifications(
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False,
        notification_type: Optional[str] = None,
    ) -> tuple[List[Notification], int]:
        """
        Get notifications for a user with pagination.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            unread_only: If True, only return unread notifications
            notification_type: Filter by notification type
            
        Returns:
            Tuple of (notifications list, total count)
        """
        # Build query
        stmt = select(Notification).where(Notification.user_id == user_id)
        
        # Apply filters
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)
        
        if notification_type:
            stmt = stmt.where(Notification.type == notification_type)
        
        # Get total count before pagination
        count_stmt = select(func.count()).select_from(Notification).where(Notification.user_id == user_id)
        if unread_only:
            count_stmt = count_stmt.where(Notification.is_read == False)
        if notification_type:
            count_stmt = count_stmt.where(Notification.type == notification_type)
        
        result = await db.execute(count_stmt)
        total = result.scalar()
        
        # Apply pagination and ordering with eager loading
        stmt = (
            stmt
            .options(selectinload(Notification.actor))  # Load actor user data
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        notifications = result.scalars().all()
        
        return notifications, total
    
    @staticmethod
    async def get_notification_by_id(
        db: AsyncSession,
        notification_id: UUID,
        user_id: UUID,
    ) -> Optional[Notification]:
        """
        Get a specific notification by ID.
        
        Args:
            db: Database session
            notification_id: Notification ID
            user_id: User ID (for authorization)
            
        Returns:
            Notification or None if not found
        """
        stmt = (
            select(Notification)
            .options(selectinload(Notification.actor))
            .where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def mark_as_read(
        db: AsyncSession,
        notification_ids: List[UUID],
        user_id: UUID,
    ) -> int:
        """
        Mark one or more notifications as read.
        
        Args:
            db: Database session
            notification_ids: List of notification IDs to mark as read
            user_id: User ID (for authorization)
            
        Returns:
            Number of notifications marked as read
        """
        # Fetch notifications to update
        stmt = select(Notification).where(
            Notification.id.in_(notification_ids),
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
        result = await db.execute(stmt)
        notifications = result.scalars().all()
        
        # Update each notification
        count = 0
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            count += 1
        
        await db.commit()
        return count
    
    @staticmethod
    async def mark_all_as_read(db: AsyncSession, user_id: UUID) -> int:
        """
        Mark all notifications as read for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Number of notifications marked as read
        """
        # Fetch unread notifications
        stmt = select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
        result = await db.execute(stmt)
        notifications = result.scalars().all()
        
        # Update each notification
        count = 0
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            count += 1
        
        await db.commit()
        return count
    
    @staticmethod
    async def delete_notification(
        db: AsyncSession,
        notification_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Delete a notification.
        
        Args:
            db: Database session
            notification_id: Notification ID
            user_id: User ID (for authorization)
            
        Returns:
            True if deleted, False if not found
        """
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        result = await db.execute(stmt)
        notification = result.scalar_one_or_none()
        
        if not notification:
            return False
        
        await db.delete(notification)
        await db.commit()
        return True
    
    @staticmethod
    async def get_unread_count(db: AsyncSession, user_id: UUID) -> int:
        """
        Get count of unread notifications for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Count of unread notifications
        """
        stmt = select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
        result = await db.execute(stmt)
        return result.scalar()
    
    @staticmethod
    async def get_notification_stats(db: AsyncSession, user_id: UUID) -> NotificationStats:
        """
        Get notification statistics for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Notification statistics
        """
        # Get total count
        total_stmt = select(func.count()).select_from(Notification).where(Notification.user_id == user_id)
        result = await db.execute(total_stmt)
        total = result.scalar()
        
        # Get unread count
        unread = await NotificationService.get_unread_count(db, user_id)
        
        # Get counts by type
        type_stmt = (
            select(Notification.type, func.count(Notification.id))
            .where(Notification.user_id == user_id)
            .group_by(Notification.type)
        )
        result = await db.execute(type_stmt)
        type_counts = result.all()
        
        # Build type count dictionary
        type_dict = {ntype: count for ntype, count in type_counts}
        
        return NotificationStats(
            total_notifications=total,
            unread_count=unread,
            vote_count=type_dict.get("vote", 0),
            reply_count=type_dict.get("reply", 0),
            mention_count=type_dict.get("mention", 0),
        )
    
    # ========================================================================
    # User Notification Preferences
    # ========================================================================
    
    @staticmethod
    async def create_default_preferences(
        db: AsyncSession,
        user_id: UUID,
    ) -> UserNotificationPreference:
        """
        Create default notification preferences for a new user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Created preferences
        """
        from datetime import datetime, timezone
        from uuid import uuid4
        
        now = datetime.now(timezone.utc)
        
        preferences = UserNotificationPreference(
            id=uuid4(),
            user_id=user_id,
            vote_notifications=True,
            reply_notifications=True,
            mention_notifications=True,
            email_notifications=False,
            created_at=now,
            updated_at=now,
        )
        
        db.add(preferences)
        await db.commit()
        await db.refresh(preferences)
        
        return preferences
    
    @staticmethod
    async def get_user_preferences(
        db: AsyncSession,
        user_id: UUID,
    ) -> Optional[UserNotificationPreference]:
        """
        Get notification preferences for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User preferences or None if not found
        """
        stmt = select(UserNotificationPreference).where(UserNotificationPreference.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_or_create_preferences(
        db: AsyncSession,
        user_id: UUID,
    ) -> UserNotificationPreference:
        """
        Get or create notification preferences for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User preferences
        """
        preferences = await NotificationService.get_user_preferences(db, user_id)
        
        if not preferences:
            preferences = await NotificationService.create_default_preferences(db, user_id)
        
        return preferences
    
    @staticmethod
    async def update_user_preferences(
        db: AsyncSession,
        user_id: UUID,
        update_data: NotificationPreferenceUpdate,
    ) -> UserNotificationPreference:
        """
        Update notification preferences for a user.
        
        Args:
            db: Database session
            user_id: User ID
            update_data: Preference update data
            
        Returns:
            Updated preferences
        """
        preferences = await NotificationService.get_or_create_preferences(db, user_id)
        
        # Update fields if provided
        if update_data.vote_notifications is not None:
            preferences.vote_notifications = update_data.vote_notifications
        
        if update_data.reply_notifications is not None:
            preferences.reply_notifications = update_data.reply_notifications
        
        if update_data.mention_notifications is not None:
            preferences.mention_notifications = update_data.mention_notifications
        
        if update_data.email_notifications is not None:
            preferences.email_notifications = update_data.email_notifications
        
        await db.commit()
        await db.refresh(preferences)
        
        return preferences
