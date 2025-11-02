"""Service for User Feed Subscription management."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status

from app.repositories.rss_source_repository import RSSSourceRepository
from app.repositories.user_feed_subscription_repository import UserFeedSubscriptionRepository
from app.schemas.user_feed_subscription import (
    SubscriptionCreate,
    SubscriptionsListResponse,
    SubscriptionUpdate,
    SubscriptionWithFeedResponse,
)

logger = logging.getLogger(__name__)


class UserFeedSubscriptionService:
    """Service for managing user feed subscriptions."""

    def __init__(
        self, subscription_repo: UserFeedSubscriptionRepository, feed_repo: RSSSourceRepository
    ):
        """Initialize service."""
        self.subscription_repo = subscription_repo
        self.feed_repo = feed_repo

    async def subscribe_to_feed(
        self, user_id: UUID, feed_id: UUID, subscription_data: SubscriptionCreate
    ) -> SubscriptionWithFeedResponse:
        """
        Subscribe user to a feed.

        Raises:
            HTTPException: If feed doesn't exist or already subscribed
        """
        # Check if feed exists
        feed = await self.feed_repo.get_by_id(feed_id)
        if not feed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Feed with ID {feed_id} not found"
            )

        # Check if already subscribed
        existing = await self.subscription_repo.get_user_subscription(user_id, feed_id)
        if existing:
            if existing.is_active:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail="Already subscribed to this feed"
                )
            else:
                # Reactivate existing subscription
                update_data = {
                    "is_active": True,
                    "notifications_enabled": subscription_data.notifications_enabled,
                }
                subscription = await self.subscription_repo.update(existing, update_data)
                logger.info(f"Reactivated subscription: user={user_id}, feed={feed_id}")
                return SubscriptionWithFeedResponse.model_validate(subscription)

        # Create new subscription
        sub_dict = subscription_data.model_dump()
        sub_dict["user_id"] = user_id
        sub_dict["feed_id"] = feed_id
        subscription = await self.subscription_repo.create(sub_dict)

        logger.info(f"Created subscription: user={user_id}, feed={feed_id}")
        return SubscriptionWithFeedResponse.model_validate(subscription)

    async def unsubscribe_from_feed(self, user_id: UUID, feed_id: UUID) -> dict:
        """
        Unsubscribe user from a feed.

        Raises:
            HTTPException: If not subscribed
        """
        subscription = await self.subscription_repo.get_user_subscription(user_id, feed_id)
        if not subscription or not subscription.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Not subscribed to this feed"
            )

        # Soft delete - just mark as inactive
        await self.subscription_repo.update(subscription, {"is_active": False})

        logger.info(f"Unsubscribed: user={user_id}, feed={feed_id}")
        return {"message": "Successfully unsubscribed from feed"}

    async def get_user_subscriptions(
        self, user_id: UUID, page: int = 1, page_size: int = 50, is_active: Optional[bool] = True
    ) -> SubscriptionsListResponse:
        """Get all user subscriptions with pagination."""
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Page number must be >= 1"
            )
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100",
            )

        skip = (page - 1) * page_size
        subscriptions, total = await self.subscription_repo.get_user_subscriptions(
            user_id=user_id, skip=skip, limit=page_size, is_active=is_active
        )

        total_pages = (total + page_size - 1) // page_size

        return SubscriptionsListResponse(
            subscriptions=[SubscriptionWithFeedResponse.model_validate(s) for s in subscriptions],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_subscription_preferences(
        self, user_id: UUID, feed_id: UUID, update_data: SubscriptionUpdate
    ) -> SubscriptionWithFeedResponse:
        """
        Update subscription preferences.

        Raises:
            HTTPException: If subscription not found
        """
        subscription = await self.subscription_repo.get_user_subscription(user_id, feed_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
            )

        update_dict = update_data.model_dump(exclude_unset=True)
        updated_subscription = await self.subscription_repo.update(subscription, update_dict)

        logger.info(f"Updated subscription preferences: user={user_id}, feed={feed_id}")
        return SubscriptionWithFeedResponse.model_validate(updated_subscription)

    async def is_subscribed(self, user_id: UUID, feed_id: UUID) -> bool:
        """Check if user is subscribed to a feed."""
        subscription = await self.subscription_repo.get_user_subscription(user_id, feed_id)
        return subscription is not None and subscription.is_active
