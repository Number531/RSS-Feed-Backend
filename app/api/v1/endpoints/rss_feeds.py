"""RSS Feed management endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_admin_user, get_current_user, get_current_user_optional
from app.db.session import get_db
from app.models.user import User
from app.repositories.rss_source_repository import RSSSourceRepository
from app.schemas.rss_source import (
    RSSCategoryResponse,
    RSSSourceCreate,
    RSSSourceListResponse,
    RSSSourceResponse,
    RSSSourceUpdate,
)
from app.services.rss_source_service import RSSSourceService

router = APIRouter(prefix="/feeds", tags=["RSS Feeds"])


def get_rss_source_service(db: AsyncSession = Depends(get_db)) -> RSSSourceService:
    """Dependency to get RSS source service."""
    repository = RSSSourceRepository(db)
    return RSSSourceService(repository)


@router.get("", response_model=RSSSourceListResponse)
async def list_feeds(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    service: RSSSourceService = Depends(get_rss_source_service),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Get list of RSS feeds with pagination.

    **Public endpoint** - Authentication optional.

    - **page**: Page number (1-indexed)
    - **page_size**: Number of items per page (max 100)
    - **category**: Optional filter by category
    - **is_active**: Optional filter by active status (defaults to true for unauthenticated users)
    """
    # Default to showing only active feeds for unauthenticated users
    if current_user is None and is_active is None:
        is_active = True
    
    return await service.get_all_sources(
        page=page, page_size=page_size, category=category, is_active=is_active
    )


@router.get("/categories", response_model=list[RSSCategoryResponse])
async def list_categories(
    service: RSSSourceService = Depends(get_rss_source_service),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Get list of RSS feed categories with statistics.

    **Public endpoint** - Authentication optional.

    Returns:
    - Category name
    - Total number of feeds
    - Number of active feeds
    """
    return await service.get_categories()


# Subscription endpoints (must come before /{feed_id} to avoid routing conflicts)

from app.repositories.user_feed_subscription_repository import UserFeedSubscriptionRepository
from app.schemas.user_feed_subscription import (
    SubscriptionCreate,
    SubscriptionsListResponse,
    SubscriptionUpdate,
    SubscriptionWithFeedResponse,
)
from app.services.user_feed_subscription_service import UserFeedSubscriptionService


def get_subscription_service(db: AsyncSession = Depends(get_db)) -> UserFeedSubscriptionService:
    """Dependency to get user feed subscription service."""
    subscription_repo = UserFeedSubscriptionRepository(db)
    feed_repo = RSSSourceRepository(db)
    return UserFeedSubscriptionService(subscription_repo, feed_repo)


@router.get("/subscriptions", response_model=SubscriptionsListResponse)
async def get_my_subscriptions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    service: UserFeedSubscriptionService = Depends(get_subscription_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get current user's feed subscriptions.

    - **page**: Page number (1-indexed)
    - **page_size**: Number of items per page (max 100)
    - **is_active**: Filter by active status (default: true)
    """
    return await service.get_user_subscriptions(
        user_id=current_user.id, page=page, page_size=page_size, is_active=is_active
    )


@router.get("/subscribed", response_model=List[UUID])
async def get_subscribed_feed_ids(
    service: UserFeedSubscriptionService = Depends(get_subscription_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get list of feed IDs that the current user is subscribed to.

    Useful for quickly checking subscription status.
    """
    subscriptions_response = await service.get_user_subscriptions(
        user_id=current_user.id,
        page=1,
        page_size=100,  # Get up to 100 subscriptions (max allowed)
        is_active=True,
    )
    return [sub.feed_id for sub in subscriptions_response.subscriptions]


# Feed detail endpoint (must come after specific paths like /subscriptions, /subscribed)


@router.get("/{feed_id}", response_model=RSSSourceResponse)
async def get_feed(
    feed_id: UUID,
    service: RSSSourceService = Depends(get_rss_source_service),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Get detailed information about a specific RSS feed.

    **Public endpoint** - Authentication optional.

    - **feed_id**: UUID of the feed
    """
    return await service.get_source_by_id(feed_id)


# Admin endpoints - require admin privileges


@router.post("", response_model=RSSSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_feed(
    feed_data: RSSSourceCreate,
    service: RSSSourceService = Depends(get_rss_source_service),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Create a new RSS feed (Admin only).

    - **name**: Display name of the feed
    - **url**: RSS feed URL
    - **source_name**: Source organization (e.g., 'CNN', 'BBC')
    - **category**: Feed category
    - **is_active**: Whether the feed is active (default: true)
    """
    return await service.create_source(feed_data)


@router.put("/{feed_id}", response_model=RSSSourceResponse)
async def update_feed(
    feed_id: UUID,
    feed_data: RSSSourceUpdate,
    service: RSSSourceService = Depends(get_rss_source_service),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Update an existing RSS feed (Admin only).

    - **feed_id**: UUID of the feed to update
    - All fields are optional - only provided fields will be updated
    """
    return await service.update_source(feed_id, feed_data)


@router.delete("/{feed_id}", status_code=status.HTTP_200_OK)
async def delete_feed(
    feed_id: UUID,
    service: RSSSourceService = Depends(get_rss_source_service),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Delete an RSS feed (Admin only).

    - **feed_id**: UUID of the feed to delete

    Warning: This will also delete all articles associated with this feed.
    """
    return await service.delete_source(feed_id)


# Subscription action endpoints (with feed_id parameter)


@router.post(
    "/{feed_id}/subscribe",
    response_model=SubscriptionWithFeedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def subscribe_to_feed(
    feed_id: UUID,
    subscription_data: SubscriptionCreate = SubscriptionCreate(),
    service: UserFeedSubscriptionService = Depends(get_subscription_service),
    current_user: User = Depends(get_current_user),
):
    """
    Subscribe to an RSS feed.

    - **feed_id**: UUID of the feed to subscribe to
    - **notifications_enabled**: Enable notifications for this feed (default: true)
    """
    return await service.subscribe_to_feed(
        user_id=current_user.id, feed_id=feed_id, subscription_data=subscription_data
    )


@router.delete("/{feed_id}/unsubscribe", status_code=status.HTTP_200_OK)
async def unsubscribe_from_feed(
    feed_id: UUID,
    service: UserFeedSubscriptionService = Depends(get_subscription_service),
    current_user: User = Depends(get_current_user),
):
    """
    Unsubscribe from an RSS feed.

    - **feed_id**: UUID of the feed to unsubscribe from
    """
    return await service.unsubscribe_from_feed(user_id=current_user.id, feed_id=feed_id)


@router.put("/{feed_id}/subscription", response_model=SubscriptionWithFeedResponse)
async def update_subscription_preferences(
    feed_id: UUID,
    update_data: SubscriptionUpdate,
    service: UserFeedSubscriptionService = Depends(get_subscription_service),
    current_user: User = Depends(get_current_user),
):
    """
    Update subscription preferences for a feed.

    - **feed_id**: UUID of the feed
    - **is_active**: Whether the subscription is active
    - **notifications_enabled**: Enable/disable notifications
    """
    return await service.update_subscription_preferences(
        user_id=current_user.id, feed_id=feed_id, update_data=update_data
    )
