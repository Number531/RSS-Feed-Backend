"""
Comment Service Module

Handles business logic for comment operations including creation,
retrieval, updates, deletion, and threading. Manages comment
permissions and validation.
"""

from typing import List, Optional
from uuid import UUID

from app.services.base_service import BaseService
from app.repositories.comment_repository import CommentRepository
from app.repositories.article_repository import ArticleRepository
from app.models.comment import Comment
from app.core.exceptions import (
    ValidationError,
    NotFoundError,
    AuthorizationError
)


class CommentService(BaseService):
    """
    Service for comment-related business logic.
    
    Handles:
    - Comment creation (top-level and replies)
    - Comment retrieval (flat and threaded)
    - Comment updates
    - Comment deletion (soft delete)
    - Permission checks
    """
    
    def __init__(
        self,
        comment_repository: CommentRepository,
        article_repository: ArticleRepository
    ):
        """
        Initialize comment service.
        
        Args:
            comment_repository: Comment repository instance
            article_repository: Article repository for validation
        """
        super().__init__()
        self.comment_repo = comment_repository
        self.article_repo = article_repository
    
    async def create_comment(
        self,
        user_id: UUID,
        article_id: UUID,
        content: str,
        parent_comment_id: Optional[UUID] = None
    ) -> Comment:
        """
        Create a new comment on an article.
        
        Args:
            user_id: User UUID
            article_id: Article UUID
            content: Comment content
            parent_comment_id: Optional parent comment ID for replies
            
        Returns:
            Created comment
            
        Raises:
            ValidationError: If content is invalid
            NotFoundError: If article or parent comment doesn't exist
        """
        # Validate content
        if not content or len(content.strip()) == 0:
            raise ValidationError("Comment content cannot be empty")
        
        if len(content) > 10000:
            raise ValidationError("Comment content too long (max 10,000 characters)")
        
        # Log operation
        self.log_operation(
            "create_comment",
            user_id=user_id,
            article_id=str(article_id),
            parent_comment_id=str(parent_comment_id) if parent_comment_id else None
        )
        
        try:
            # Verify article exists
            article = await self.article_repo.get_article_by_id(article_id)
            if not article:
                raise NotFoundError(f"Article with ID {article_id} not found")
            
            # Verify parent comment exists (if provided)
            if parent_comment_id:
                parent_comment = await self.comment_repo.get_comment_by_id(parent_comment_id)
                if not parent_comment:
                    raise NotFoundError(f"Parent comment with ID {parent_comment_id} not found")
                
                # Ensure parent comment belongs to the same article
                if parent_comment.article_id != article_id:
                    raise ValidationError("Parent comment must belong to the same article")
                
                # Prevent commenting on deleted comments
                if parent_comment.is_deleted:
                    raise ValidationError("Cannot reply to a deleted comment")
            
            # Create comment
            comment = await self.comment_repo.create_comment(
                user_id=user_id,
                article_id=article_id,
                content=content,
                parent_comment_id=parent_comment_id
            )
            
            comment_type = "reply" if parent_comment_id else "comment"
            self.logger.info(
                f"New {comment_type} created by user {user_id} on article {article_id}"
            )
            
            # Create reply notification if this is a reply to another comment
            if parent_comment_id and parent_comment:
                if parent_comment.user_id and parent_comment.user_id != user_id:
                    try:
                        from app.services.notification_service import NotificationService
                        
                        # Create notification using the same db session from repository
                        db_session = self.comment_repo.db
                        await NotificationService.create_reply_notification(
                            db=db_session,
                            recipient_id=parent_comment.user_id,
                            actor_id=user_id,
                            comment_id=comment.id,
                            article_id=article_id
                        )
                    except Exception as e:
                        self.logger.warning(f"Failed to create reply notification: {e}")
            
            return comment
        
        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            self.log_error("create_comment", e, user_id=user_id)
            raise
    
    async def get_article_comments(
        self,
        article_id: UUID,
        page: int = 1,
        page_size: int = 50
    ) -> List[Comment]:
        """
        Get top-level comments for an article with pagination.
        
        Args:
            article_id: Article UUID
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            List of top-level comments
            
        Raises:
            ValidationError: If pagination parameters are invalid
            NotFoundError: If article doesn't exist
        """
        # Validate pagination
        skip = (page - 1) * page_size
        self.validate_pagination(skip, page_size, max_limit=100)
        
        # Log operation
        self.log_operation(
            "get_article_comments",
            article_id=str(article_id),
            page=page,
            page_size=page_size
        )
        
        try:
            # Verify article exists
            article = await self.article_repo.get_article_by_id(article_id)
            if not article:
                raise NotFoundError(f"Article with ID {article_id} not found")
            
            # Get comments
            comments = await self.comment_repo.get_article_comments(
                article_id=article_id,
                page=page,
                page_size=page_size
            )
            
            return comments
        
        except NotFoundError:
            raise
        except Exception as e:
            self.log_error("get_article_comments", e, article_id=str(article_id))
            raise
    
    async def get_comment_replies(self, parent_id: UUID) -> List[Comment]:
        """
        Get all replies to a comment.
        
        Args:
            parent_id: Parent comment UUID
            
        Returns:
            List of reply comments
            
        Raises:
            NotFoundError: If parent comment doesn't exist
        """
        # Log operation
        self.log_operation(
            "get_comment_replies",
            parent_id=str(parent_id)
        )
        
        try:
            # Verify parent comment exists
            parent_comment = await self.comment_repo.get_comment_by_id(parent_id)
            if not parent_comment:
                raise NotFoundError(f"Comment with ID {parent_id} not found")
            
            # Get replies
            replies = await self.comment_repo.get_comment_replies(parent_id)
            
            return replies
        
        except NotFoundError:
            raise
        except Exception as e:
            self.log_error("get_comment_replies", e, parent_id=str(parent_id))
            raise
    
    async def get_comment_by_id(self, comment_id: UUID) -> Comment:
        """
        Get a single comment by ID.
        
        Args:
            comment_id: Comment UUID
            
        Returns:
            Comment instance
            
        Raises:
            NotFoundError: If comment doesn't exist
        """
        self.log_operation(
            "get_comment_by_id",
            comment_id=str(comment_id)
        )
        
        try:
            comment = await self.comment_repo.get_comment_by_id(comment_id)
            
            if not comment:
                raise NotFoundError(f"Comment with ID {comment_id} not found")
            
            return comment
        
        except NotFoundError:
            raise
        except Exception as e:
            self.log_error("get_comment_by_id", e, comment_id=str(comment_id))
            raise
    
    async def update_comment(
        self,
        comment_id: UUID,
        user_id: UUID,
        content: str
    ) -> Comment:
        """
        Update a comment's content.
        
        Args:
            comment_id: Comment UUID
            user_id: User UUID (must be comment author)
            content: New content
            
        Returns:
            Updated comment
            
        Raises:
            ValidationError: If content is invalid
            NotFoundError: If comment doesn't exist
            AuthorizationError: If user is not the comment author
        """
        # Validate content
        if not content or len(content.strip()) == 0:
            raise ValidationError("Comment content cannot be empty")
        
        if len(content) > 10000:
            raise ValidationError("Comment content too long (max 10,000 characters)")
        
        # Log operation
        self.log_operation(
            "update_comment",
            user_id=user_id,
            comment_id=str(comment_id)
        )
        
        try:
            # Get comment
            comment = await self.comment_repo.get_comment_by_id(comment_id)
            
            if not comment:
                raise NotFoundError(f"Comment with ID {comment_id} not found")
            
            # Check if comment is deleted
            if comment.is_deleted:
                raise ValidationError("Cannot update a deleted comment")
            
            # Check authorization
            if comment.user_id != user_id:
                raise AuthorizationError("You can only edit your own comments")
            
            # Update comment
            updated_comment = await self.comment_repo.update_comment(
                comment=comment,
                content=content
            )
            
            self.logger.info(f"Comment {comment_id} updated by user {user_id}")
            
            return updated_comment
        
        except (ValidationError, NotFoundError, AuthorizationError):
            raise
        except Exception as e:
            self.log_error("update_comment", e, user_id=user_id)
            raise
    
    async def delete_comment(
        self,
        comment_id: UUID,
        user_id: UUID
    ) -> Comment:
        """
        Soft delete a comment (mark as deleted).
        
        Args:
            comment_id: Comment UUID
            user_id: User UUID (must be comment author)
            
        Returns:
            Deleted comment
            
        Raises:
            NotFoundError: If comment doesn't exist
            AuthorizationError: If user is not the comment author
        """
        # Log operation
        self.log_operation(
            "delete_comment",
            user_id=user_id,
            comment_id=str(comment_id)
        )
        
        try:
            # Get comment
            comment = await self.comment_repo.get_comment_by_id(comment_id)
            
            if not comment:
                raise NotFoundError(f"Comment with ID {comment_id} not found")
            
            # Check if already deleted
            if comment.is_deleted:
                raise ValidationError("Comment is already deleted")
            
            # Check authorization
            if comment.user_id != user_id:
                raise AuthorizationError("You can only delete your own comments")
            
            # Soft delete comment
            deleted_comment = await self.comment_repo.soft_delete_comment(comment)
            
            self.logger.info(f"Comment {comment_id} deleted by user {user_id}")
            
            return deleted_comment
        
        except (ValidationError, NotFoundError, AuthorizationError):
            raise
        except Exception as e:
            self.log_error("delete_comment", e, user_id=user_id)
            raise
    
    async def build_comment_tree(
        self,
        article_id: UUID,
        max_depth: int = 10
    ) -> List[dict]:
        """
        Build a nested comment tree for an article.
        
        Args:
            article_id: Article UUID
            max_depth: Maximum nesting depth
            
        Returns:
            List of comment dictionaries with nested replies
            
        Raises:
            NotFoundError: If article doesn't exist
        """
        # Log operation
        self.log_operation(
            "build_comment_tree",
            article_id=str(article_id),
            max_depth=max_depth
        )
        
        try:
            # Get top-level comments
            top_comments = await self.comment_repo.get_article_comments(
                article_id=article_id,
                page=1,
                page_size=100
            )
            
            # Build tree recursively
            tree = []
            for comment in top_comments:
                comment_dict = self._comment_to_dict(comment)
                comment_dict['replies'] = await self._get_replies_recursive(
                    comment.id,
                    current_depth=1,
                    max_depth=max_depth
                )
                tree.append(comment_dict)
            
            return tree
        
        except Exception as e:
            self.log_error("build_comment_tree", e, article_id=str(article_id))
            raise
    
    async def _get_replies_recursive(
        self,
        parent_id: UUID,
        current_depth: int,
        max_depth: int
    ) -> List[dict]:
        """
        Recursively get replies for a comment.
        
        Args:
            parent_id: Parent comment UUID
            current_depth: Current nesting depth
            max_depth: Maximum allowed depth
            
        Returns:
            List of reply dictionaries with nested replies
        """
        if current_depth >= max_depth:
            return []
        
        replies = await self.comment_repo.get_comment_replies(parent_id)
        result = []
        
        for reply in replies:
            reply_dict = self._comment_to_dict(reply)
            reply_dict['replies'] = await self._get_replies_recursive(
                reply.id,
                current_depth + 1,
                max_depth
            )
            result.append(reply_dict)
        
        return result
    
    def _comment_to_dict(self, comment: Comment) -> dict:
        """
        Convert comment model to dictionary.
        
        Args:
            comment: Comment instance
            
        Returns:
            Comment dictionary
        """
        return {
            'id': comment.id,
            'user_id': comment.user_id,
            'article_id': comment.article_id,
            'parent_comment_id': comment.parent_comment_id,
            'content': comment.content,
            'created_at': comment.created_at,
            'updated_at': comment.updated_at,
            'is_deleted': comment.is_deleted,
            'is_edited': comment.is_edited,
            'vote_score': comment.vote_score,
        }
