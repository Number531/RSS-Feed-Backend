"""
Comment Vote Service Module

Handles business logic for voting operations on comments including vote casting,
removal, and retrieval. Enforces voting rules and manages vote state for comments.
"""

from typing import Optional
from uuid import UUID

from app.core.exceptions import InvalidVoteTypeError, NotFoundError, ValidationError
from app.models.vote import Vote
from app.repositories.comment_repository import CommentRepository
from app.repositories.vote_repository import VoteRepository
from app.services.base_service import BaseService


class CommentVoteService(BaseService):
    """
    Service for comment vote-related business logic.

    Handles:
    - Comment vote creation (upvote/downvote)
    - Comment vote updates (changing vote type)
    - Comment vote removal
    - Comment vote retrieval
    - Comment vote validation
    """

    def __init__(self, vote_repository: VoteRepository, comment_repository: CommentRepository):
        """
        Initialize comment vote service.

        Args:
            vote_repository: Vote repository instance
            comment_repository: Comment repository for validation
        """
        super().__init__()
        self.vote_repo = vote_repository
        self.comment_repo = comment_repository

    async def cast_vote(self, user_id: UUID, comment_id: UUID, vote_value: int) -> Optional[Vote]:
        """
        Cast a vote on a comment (upvote or downvote).

        If the user has already voted, updates the existing vote.
        If vote_value is 0, removes the vote.
        If user casts same vote again, toggles it off (removes it).

        Args:
            user_id: User UUID
            comment_id: Comment UUID
            vote_value: Vote value (-1 for downvote, 1 for upvote, 0 to remove)

        Returns:
            Vote instance (or None if removed)

        Raises:
            ValidationError: If vote value is invalid
            NotFoundError: If comment doesn't exist
        """
        # Validate vote value
        if vote_value not in [-1, 0, 1]:
            raise InvalidVoteTypeError(
                "Vote value must be -1 (downvote), 0 (remove), or 1 (upvote)"
            )

        # Log operation
        self.log_operation(
            "cast_comment_vote", user_id=user_id, comment_id=str(comment_id), vote_value=vote_value
        )

        try:
            # Verify comment exists
            comment = await self.comment_repo.get_comment_by_id(comment_id)
            if not comment:
                raise NotFoundError(f"Comment with ID {comment_id} not found")

            # Check for existing vote
            existing_vote = await self.vote_repo.get_comment_vote(
                user_id=user_id, comment_id=comment_id
            )

            # Handle different scenarios
            if vote_value == 0:
                # Remove vote
                if existing_vote:
                    await self.vote_repo.delete_comment_vote(existing_vote)
                    self.logger.info(
                        f"Comment vote removed for user {user_id} on comment {comment_id}"
                    )
                    return None
                else:
                    # No vote to remove
                    return None

            elif existing_vote:
                # Update existing vote
                if existing_vote.vote_value == vote_value:
                    # Same vote value - toggle off (remove it)
                    await self.vote_repo.delete_comment_vote(existing_vote)
                    self.logger.info(
                        f"Comment vote toggled off for user {user_id} on comment {comment_id}"
                    )
                    return None
                else:
                    # Change vote (e.g., from upvote to downvote)
                    updated_vote = await self.vote_repo.update_comment_vote(
                        vote=existing_vote, new_value=vote_value
                    )
                    self.logger.info(
                        f"Comment vote updated for user {user_id} on comment {comment_id}: "
                        f"{existing_vote.vote_value} -> {vote_value}"
                    )
                    return updated_vote

            else:
                # Create new vote
                new_vote = await self.vote_repo.create_comment_vote(
                    user_id=user_id, comment_id=comment_id, vote_value=vote_value
                )
                self.logger.info(
                    f"New comment vote created for user {user_id} on comment {comment_id}: {vote_value}"
                )

                # Create notification for comment author (only for upvotes)
                if comment and comment.user_id and vote_value == 1 and comment.user_id != user_id:
                    try:
                        from app.services.notification_service import NotificationService

                        # Create notification using the same db session from repository
                        db_session = self.vote_repo.db
                        await NotificationService.create_vote_notification(
                            db=db_session,
                            recipient_id=comment.user_id,
                            actor_id=user_id,
                            entity_type="comment",
                            entity_id=comment_id,
                            vote_value=vote_value,
                        )
                    except Exception as e:
                        self.logger.warning(f"Failed to create vote notification: {e}")

                return new_vote

        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            self.log_error("cast_comment_vote", e, user_id=user_id)
            raise

    async def remove_vote(self, user_id: UUID, comment_id: UUID) -> None:
        """
        Remove a user's vote from a comment.

        Args:
            user_id: User UUID
            comment_id: Comment UUID

        Raises:
            NotFoundError: If comment doesn't exist or no vote exists
        """
        self.log_operation("remove_comment_vote", user_id=user_id, comment_id=str(comment_id))

        try:
            # Verify comment exists
            comment = await self.comment_repo.get_comment_by_id(comment_id)
            if not comment:
                raise NotFoundError(f"Comment with ID {comment_id} not found")

            # Get existing vote
            existing_vote = await self.vote_repo.get_comment_vote(
                user_id=user_id, comment_id=comment_id
            )

            if not existing_vote:
                raise NotFoundError("No vote found to remove")

            # Delete vote
            await self.vote_repo.delete_comment_vote(existing_vote)
            self.logger.info(f"Comment vote removed for user {user_id} on comment {comment_id}")

        except NotFoundError:
            raise
        except Exception as e:
            self.log_error("remove_comment_vote", e, user_id=user_id)
            raise

    async def get_user_vote(self, user_id: UUID, comment_id: UUID) -> Optional[Vote]:
        """
        Get a user's vote on a comment.

        Args:
            user_id: User UUID
            comment_id: Comment UUID

        Returns:
            Vote instance or None if no vote exists
        """
        self.log_operation("get_user_comment_vote", user_id=user_id, comment_id=str(comment_id))

        try:
            vote = await self.vote_repo.get_comment_vote(user_id=user_id, comment_id=comment_id)
            return vote

        except Exception as e:
            self.log_error("get_user_comment_vote", e, user_id=user_id)
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

    async def toggle_vote(self, user_id: UUID, comment_id: UUID, vote_type: str) -> Optional[Vote]:
        """
        Toggle a vote on a comment.

        If the user has already cast the same vote type, removes it.
        If the user has cast a different vote type, changes it.
        If the user hasn't voted, creates a new vote.

        Args:
            user_id: User UUID
            comment_id: Comment UUID
            vote_type: Vote type ("upvote" or "downvote")

        Returns:
            Vote instance or None if removed

        Raises:
            ValidationError: If vote type is invalid
            NotFoundError: If comment doesn't exist
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
            "toggle_comment_vote", user_id=user_id, comment_id=str(comment_id), vote_type=vote_type
        )

        try:
            # Cast vote (cast_vote handles toggle logic)
            return await self.cast_vote(user_id, comment_id, vote_value)

        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            self.log_error("toggle_comment_vote", e, user_id=user_id)
            raise

    async def get_comment_vote_summary(self, comment_id: UUID) -> dict:
        """
        Get vote summary for a comment.

        Args:
            comment_id: Comment UUID

        Returns:
            Dictionary with vote_score and vote_count

        Raises:
            NotFoundError: If comment doesn't exist
        """
        self.log_operation("get_comment_vote_summary", comment_id=str(comment_id))

        try:
            comment = await self.comment_repo.get_comment_by_id(comment_id)
            if not comment:
                raise NotFoundError(f"Comment with ID {comment_id} not found")

            return {
                "comment_id": comment_id,
                "vote_score": comment.vote_score,
                "vote_count": comment.vote_count,
            }

        except NotFoundError:
            raise
        except Exception as e:
            self.log_error("get_comment_vote_summary", e)
            raise
