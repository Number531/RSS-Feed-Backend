"""
Vote Service Module

Handles business logic for voting operations including vote casting,
removal, and retrieval. Enforces voting rules and manages vote state.
"""

from typing import Optional
from uuid import UUID

from app.core.exceptions import (
    DuplicateVoteError,
    InvalidVoteTypeError,
    NotFoundError,
    ValidationError,
)
from app.models.vote import Vote
from app.repositories.article_repository import ArticleRepository
from app.repositories.vote_repository import VoteRepository
from app.services.base_service import BaseService


class VoteService(BaseService):
    """
    Service for vote-related business logic.

    Handles:
    - Vote creation (upvote/downvote)
    - Vote updates (changing vote type)
    - Vote removal
    - Vote retrieval
    - Vote validation
    """

    def __init__(self, vote_repository: VoteRepository, article_repository: ArticleRepository):
        """
        Initialize vote service.

        Args:
            vote_repository: Vote repository instance
            article_repository: Article repository for validation
        """
        super().__init__()
        self.vote_repo = vote_repository
        self.article_repo = article_repository

    async def cast_vote(self, user_id: UUID, article_id: UUID, vote_value: int) -> Vote:
        """
        Cast a vote on an article (upvote or downvote).

        If the user has already voted, updates the existing vote.
        If vote_value is 0, removes the vote.

        Args:
            user_id: User UUID
            article_id: Article UUID
            vote_value: Vote value (-1 for downvote, 1 for upvote, 0 to remove)

        Returns:
            Vote instance (or None if removed)

        Raises:
            ValidationError: If vote value is invalid
            NotFoundError: If article doesn't exist
        """
        # Validate vote value
        if vote_value not in [-1, 0, 1]:
            raise InvalidVoteTypeError(
                "Vote value must be -1 (downvote), 0 (remove), or 1 (upvote)"
            )

        # Log operation
        self.log_operation(
            "cast_vote", user_id=user_id, article_id=str(article_id), vote_value=vote_value
        )

        try:
            # Verify article exists
            article = await self.article_repo.get_article_by_id(article_id)
            if not article:
                raise NotFoundError(f"Article with ID {article_id} not found")

            # Check for existing vote
            existing_vote = await self.vote_repo.get_user_vote(
                user_id=user_id, article_id=article_id
            )

            # Handle different scenarios
            if vote_value == 0:
                # Remove vote
                if existing_vote:
                    await self.vote_repo.delete_vote(existing_vote)
                    self.logger.info(f"Vote removed for user {user_id} on article {article_id}")
                    return None
                else:
                    # No vote to remove
                    return None

            elif existing_vote:
                # Update existing vote
                if existing_vote.vote_value == vote_value:
                    # Same vote value - no change needed
                    self.logger.info(f"Vote unchanged for user {user_id} on article {article_id}")
                    return existing_vote
                else:
                    # Change vote (e.g., from upvote to downvote)
                    updated_vote = await self.vote_repo.update_vote(
                        vote=existing_vote, new_value=vote_value
                    )
                    self.logger.info(
                        f"Vote updated for user {user_id} on article {article_id}: "
                        f"{existing_vote.vote_value} -> {vote_value}"
                    )
                    return updated_vote

            else:
                # Create new vote
                new_vote = await self.vote_repo.create_vote(
                    user_id=user_id, article_id=article_id, vote_value=vote_value
                )
                self.logger.info(
                    f"New vote created for user {user_id} on article {article_id}: {vote_value}"
                )

                # TODO: Trigger notification for article author (Phase 3 integration)
                # Notification will be created via background task or database trigger
                # to avoid async/sync session complexity

                return new_vote

        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            self.log_error("cast_vote", e, user_id=user_id)
            raise

    async def remove_vote(self, user_id: UUID, article_id: UUID) -> None:
        """
        Remove a user's vote from an article.

        Args:
            user_id: User UUID
            article_id: Article UUID

        Raises:
            NotFoundError: If article doesn't exist or no vote exists
        """
        self.log_operation("remove_vote", user_id=user_id, article_id=str(article_id))

        try:
            # Verify article exists
            article = await self.article_repo.get_article_by_id(article_id)
            if not article:
                raise NotFoundError(f"Article with ID {article_id} not found")

            # Get existing vote
            existing_vote = await self.vote_repo.get_user_vote(
                user_id=user_id, article_id=article_id
            )

            if not existing_vote:
                raise NotFoundError("No vote found to remove")

            # Delete vote
            await self.vote_repo.delete_vote(existing_vote)
            self.logger.info(f"Vote removed for user {user_id} on article {article_id}")

        except NotFoundError:
            raise
        except Exception as e:
            self.log_error("remove_vote", e, user_id=user_id)
            raise

    async def get_user_vote(self, user_id: UUID, article_id: UUID) -> Optional[Vote]:
        """
        Get a user's vote on an article.

        Args:
            user_id: User UUID
            article_id: Article UUID

        Returns:
            Vote instance or None if no vote exists
        """
        self.log_operation("get_user_vote", user_id=user_id, article_id=str(article_id))

        try:
            vote = await self.vote_repo.get_user_vote(user_id=user_id, article_id=article_id)
            return vote

        except Exception as e:
            self.log_error("get_user_vote", e, user_id=user_id)
            raise

    def validate_vote_value(self, vote_value: int) -> None:
        """
        Validate vote value.

        Args:
            vote_value: Vote value to validate

        Raises:
            InvalidVoteTypeError: If vote value is invalid
        """
        if vote_value not in [-1, 0, 1]:
            raise InvalidVoteTypeError(
                "Vote value must be -1 (downvote), 0 (remove), or 1 (upvote)"
            )

    async def toggle_vote(self, user_id: UUID, article_id: UUID, vote_type: str) -> Optional[Vote]:
        """
        Toggle a vote on an article.

        If the user has already cast the same vote type, removes it.
        If the user has cast a different vote type, changes it.
        If the user hasn't voted, creates a new vote.

        Args:
            user_id: User UUID
            article_id: Article UUID
            vote_type: Vote type ("upvote" or "downvote")

        Returns:
            Vote instance or None if removed

        Raises:
            ValidationError: If vote type is invalid
            NotFoundError: If article doesn't exist
        """
        # Convert vote type string to value
        if vote_type == "upvote":
            vote_value = 1
        elif vote_type == "downvote":
            vote_value = -1
        else:
            raise ValidationError("Vote type must be 'upvote' or 'downvote'")

        # Log operation
        self.log_operation(
            "toggle_vote", user_id=user_id, article_id=str(article_id), vote_type=vote_type
        )

        try:
            # Get existing vote
            existing_vote = await self.vote_repo.get_user_vote(
                user_id=user_id, article_id=article_id
            )

            if existing_vote and existing_vote.vote_value == vote_value:
                # Same vote exists - toggle it off (remove)
                await self.vote_repo.delete_vote(existing_vote)
                self.logger.info(f"Vote toggled off for user {user_id} on article {article_id}")
                return None
            else:
                # Cast or update vote
                return await self.cast_vote(user_id, article_id, vote_value)

        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            self.log_error("toggle_vote", e, user_id=user_id)
            raise
