"""Repository for User Feed Subscription data access."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.user_feed_subscription import UserFeedSubscription


class UserFeedSubscriptionRepository:
    """Repository for managing User Feed Subscription data access."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        self.db = db

    async def get_by_id(self, subscription_id: UUID) -> Optional[UserFeedSubscription]:
        """Get subscription by ID."""
        result = await self.db.execute(
            select(UserFeedSubscription)
            .options(joinedload(UserFeedSubscription.feed))
            .where(UserFeedSubscription.id == subscription_id)
        )
        return result.scalar_one_or_none()

    async def get_user_subscription(
        self, user_id: UUID, feed_id: UUID
    ) -> Optional[UserFeedSubscription]:
        """Get user's subscription to a specific feed."""
        result = await self.db.execute(
            select(UserFeedSubscription).where(
                UserFeedSubscription.user_id == user_id, UserFeedSubscription.feed_id == feed_id
            )
        )
        return result.scalar_one_or_none()

    async def get_user_subscriptions(
        self, user_id: UUID, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None
    ) -> tuple[List[UserFeedSubscription], int]:
        """Get all subscriptions for a user."""
        query = (
            select(UserFeedSubscription)
            .options(joinedload(UserFeedSubscription.feed))
            .where(UserFeedSubscription.user_id == user_id)
        )

        if is_active is not None:
            query = query.where(UserFeedSubscription.is_active == is_active)

        # Get total count
        count_query = (
            select(func.count())
            .select_from(UserFeedSubscription)
            .where(UserFeedSubscription.user_id == user_id)
        )
        if is_active is not None:
            count_query = count_query.where(UserFeedSubscription.is_active == is_active)

        result = await self.db.execute(count_query)
        total = result.scalar_one()

        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(UserFeedSubscription.subscribed_at.desc())
        result = await self.db.execute(query)
        subscriptions = list(result.scalars().all())

        return subscriptions, total

    async def create(self, subscription_data: dict) -> UserFeedSubscription:
        """Create new subscription."""
        subscription = UserFeedSubscription(**subscription_data)
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)

        # Load feed relationship
        await self.db.refresh(subscription, ["feed"])
        return subscription

    async def update(
        self, subscription: UserFeedSubscription, update_data: dict
    ) -> UserFeedSubscription:
        """Update subscription."""
        for field, value in update_data.items():
            if value is not None:
                setattr(subscription, field, value)

        await self.db.commit()
        await self.db.refresh(subscription, ["feed"])
        return subscription

    async def delete(self, subscription: UserFeedSubscription) -> None:
        """Delete subscription."""
        await self.db.delete(subscription)
        await self.db.commit()

    async def count_feed_subscribers(self, feed_id: UUID) -> int:
        """Count number of active subscribers for a feed."""
        result = await self.db.execute(
            select(func.count())
            .select_from(UserFeedSubscription)
            .where(UserFeedSubscription.feed_id == feed_id, UserFeedSubscription.is_active == True)
        )
        return result.scalar_one()
