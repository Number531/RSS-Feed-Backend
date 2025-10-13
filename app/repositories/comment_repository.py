"""Comment repository for database operations."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment


class CommentRepository:
    """Repository for comment database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_comment_by_id(self, comment_id: UUID) -> Optional[Comment]:
        """Get comment by ID."""
        query = select(Comment).where(Comment.id == comment_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_article_comments(
        self,
        article_id: UUID,
        page: int = 1,
        page_size: int = 50
    ) -> List[Comment]:
        """Get top-level comments for an article with pagination."""
        # FIXED: Use parent_comment_id instead of parent_id
        query = select(Comment).where(
            and_(
                Comment.article_id == article_id,
                Comment.parent_comment_id.is_(None),  # CORRECTED
                Comment.is_deleted == False
            )
        ).order_by(Comment.created_at.desc())
        
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_comment_replies(self, parent_id: UUID) -> List[Comment]:
        """Get all replies to a comment."""
        # FIXED: Use parent_comment_id instead of parent_id
        query = select(Comment).where(
            and_(
                Comment.parent_comment_id == parent_id,  # CORRECTED
                Comment.is_deleted == False
            )
        ).order_by(Comment.created_at.asc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def create_comment(
        self,
        user_id: UUID,
        article_id: UUID,
        content: str,
        parent_comment_id: Optional[UUID] = None  # CORRECTED parameter name
    ) -> Comment:
        """Create a new comment."""
        comment = Comment(
            user_id=user_id,
            article_id=article_id,
            content=content,
            parent_comment_id=parent_comment_id  # CORRECTED
        )
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment
    
    async def update_comment(
        self,
        comment: Comment,
        content: str
    ) -> Comment:
        """Update comment content."""
        comment.content = content
        comment.is_edited = True  # Mark as edited
        await self.db.commit()
        await self.db.refresh(comment)
        return comment
    
    async def soft_delete_comment(self, comment: Comment) -> Comment:
        """Soft delete a comment (mark as deleted)."""
        comment.is_deleted = True
        comment.content = "[deleted]"
        await self.db.commit()
        await self.db.refresh(comment)
        return comment
