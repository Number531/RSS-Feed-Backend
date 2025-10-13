"""
Notifications API Endpoints

Handles user notifications and preference management.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.notification import (
    NotificationResponse,
    NotificationList,
    NotificationMarkRead,
    NotificationMarkReadResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationStats,
)
from app.services.notification_service import NotificationService

router = APIRouter()


# ============================================================================
# Notification Endpoints
# ============================================================================

@router.get("/", response_model=NotificationList)
async def get_notifications(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    unread_only: bool = Query(False, description="Show only unread notifications"),
    notification_type: Optional[str] = Query(None, description="Filter by type: vote, reply, mention"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated list of notifications for the current user.
    
    - **page**: Page number (default: 1)
    - **page_size**: Number of items per page (default: 20, max: 100)
    - **unread_only**: Filter to show only unread notifications (default: false)
    - **notification_type**: Filter by notification type: vote, reply, mention
    
    Returns paginated notification list with statistics.
    """
    skip = (page - 1) * page_size
    
    notifications, total = await NotificationService.get_user_notifications(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=page_size,
        unread_only=unread_only,
        notification_type=notification_type,
    )
    
    # Get unread count
    unread_count = await NotificationService.get_unread_count(db, current_user.id)
    
    # Convert to response format with actor username
    notification_responses = []
    for notif in notifications:
        notif_dict = {
            "id": notif.id,
            "user_id": notif.user_id,
            "type": notif.type,
            "title": notif.title,
            "message": notif.message,
            "related_entity_type": notif.related_entity_type,
            "related_entity_id": notif.related_entity_id,
            "actor_id": notif.actor_id,
            "is_read": notif.is_read,
            "read_at": notif.read_at,
            "created_at": notif.created_at,
            "actor_username": notif.actor.username if notif.actor else None,
        }
        notification_responses.append(NotificationResponse(**notif_dict))
    
    return NotificationList(
        notifications=notification_responses,
        total=total,
        unread_count=unread_count,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get notification statistics for the current user.
    
    Returns:
    - Total notification count
    - Unread count
    - Counts by type (vote, reply, mention)
    """
    stats = await NotificationService.get_notification_stats(db, current_user.id)
    return stats


@router.get("/unread-count", response_model=dict)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get count of unread notifications for the current user.
    
    Lightweight endpoint for badge display.
    """
    count = await NotificationService.get_unread_count(db, current_user.id)
    return {"unread_count": count}


# ============================================================================
# Notification Preference Endpoints (must be before /{notification_id})
# ============================================================================

@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get notification preferences for the current user.
    
    Returns current preference settings. Creates default preferences if none exist.
    """
    preferences = await NotificationService.get_or_create_preferences(
        db=db,
        user_id=current_user.id,
    )
    
    return NotificationPreferenceResponse(
        id=preferences.id,
        user_id=preferences.user_id,
        vote_notifications=preferences.vote_notifications,
        reply_notifications=preferences.reply_notifications,
        mention_notifications=preferences.mention_notifications,
        email_notifications=preferences.email_notifications,
        created_at=preferences.created_at,
        updated_at=preferences.updated_at,
    )


@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    update_data: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update notification preferences for the current user.
    
    - **vote_notifications**: Enable/disable vote notifications
    - **reply_notifications**: Enable/disable reply notifications
    - **mention_notifications**: Enable/disable mention notifications
    - **email_notifications**: Enable/disable email notifications (future feature)
    
    Only provided fields will be updated. Others remain unchanged.
    Returns updated preference settings.
    """
    preferences = await NotificationService.update_user_preferences(
        db=db,
        user_id=current_user.id,
        update_data=update_data,
    )
    
    return NotificationPreferenceResponse(
        id=preferences.id,
        user_id=preferences.user_id,
        vote_notifications=preferences.vote_notifications,
        reply_notifications=preferences.reply_notifications,
        mention_notifications=preferences.mention_notifications,
        email_notifications=preferences.email_notifications,
        created_at=preferences.created_at,
        updated_at=preferences.updated_at,
    )


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific notification by ID.
    
    - **notification_id**: UUID of the notification
    
    Returns the notification details if found and belongs to current user.
    Raises 404 if not found or unauthorized.
    """
    notification = await NotificationService.get_notification_by_id(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id,
    )
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Convert to response format
    return NotificationResponse(
        id=notification.id,
        user_id=notification.user_id,
        type=notification.type,
        title=notification.title,
        message=notification.message,
        related_entity_type=notification.related_entity_type,
        related_entity_id=notification.related_entity_id,
        actor_id=notification.actor_id,
        is_read=notification.is_read,
        read_at=notification.read_at,
        created_at=notification.created_at,
        actor_username=notification.actor.username if notification.actor else None,
    )


@router.post("/mark-read", response_model=NotificationMarkReadResponse)
async def mark_notifications_read(
    mark_data: NotificationMarkRead,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark one or more notifications as read.
    
    - **notification_ids**: List of notification UUIDs to mark as read
    
    Returns count of successfully marked notifications.
    """
    marked_count = await NotificationService.mark_as_read(
        db=db,
        notification_ids=mark_data.notification_ids,
        user_id=current_user.id,
    )
    
    return NotificationMarkReadResponse(
        marked_count=marked_count,
        message=f"Successfully marked {marked_count} notification(s) as read"
    )


@router.post("/mark-all-read", response_model=NotificationMarkReadResponse)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark all notifications as read for the current user.
    
    Returns count of notifications marked as read.
    """
    marked_count = await NotificationService.mark_all_as_read(
        db=db,
        user_id=current_user.id,
    )
    
    return NotificationMarkReadResponse(
        marked_count=marked_count,
        message=f"Successfully marked all {marked_count} notifications as read"
    )


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a notification.
    
    - **notification_id**: UUID of the notification to delete
    
    Returns 204 No Content on success.
    Raises 404 if notification not found or unauthorized.
    """
    deleted = await NotificationService.delete_notification(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id,
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return None
