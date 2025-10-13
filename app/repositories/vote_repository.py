"""Vote repository for database operations."""
from typing import Optional
from uuid import UUID
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vote import Vote
from app.models.article import Article
from app.models.comment import Comment


class VoteRepository:
    """Repository for vote database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_vote(
        self,
        user_id: UUID,
        article_id: UUID
    ) -> Optional[Vote]:
        """Get user's vote on an article."""
        query = select(Vote).where(
            and_(
                Vote.user_id == user_id,
                Vote.article_id == article_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_vote(
        self,
        user_id: UUID,
        article_id: UUID,
        vote_value: int
    ) -> Vote:
        """Create a new vote."""
        vote = Vote(
            user_id=user_id,
            article_id=article_id,
            vote_value=vote_value
        )
        self.db.add(vote)
        await self.db.commit()
        await self.db.refresh(vote)
        
        # Update article metrics (BOTH score and count)
        await self.update_article_vote_metrics(article_id)
        
        return vote
    
    async def update_vote(
        self,
        vote: Vote,
        new_value: int
    ) -> Vote:
        """Update existing vote."""
        vote.vote_value = new_value
        await self.db.commit()
        await self.db.refresh(vote)
        
        # Update article metrics
        await self.update_article_vote_metrics(vote.article_id)
        
        return vote
    
    async def delete_vote(
        self,
        vote: Vote
    ) -> None:
        """Delete a vote."""
        article_id = vote.article_id
        await self.db.delete(vote)
        await self.db.commit()
        
        # Update article metrics
        await self.update_article_vote_metrics(article_id)
    
    async def update_article_vote_metrics(
        self,
        article_id: UUID
    ) -> None:
        """
        CORRECTED: Update BOTH vote_score and vote_count for an article.
        
        - vote_score: Sum of all vote values (can be negative)
        - vote_count: Total number of votes cast
        """
        # Get sum of vote values (score)
        vote_sum_query = select(func.sum(Vote.vote_value)).where(
            Vote.article_id == article_id
        )
        vote_sum = await self.db.scalar(vote_sum_query)
        
        # Get count of votes (total number)
        vote_count_query = select(func.count(Vote.id)).where(
            Vote.article_id == article_id
        )
        vote_cnt = await self.db.scalar(vote_count_query)
        
        # Update article with BOTH metrics
        article_query = select(Article).where(Article.id == article_id)
        result = await self.db.execute(article_query)
        article = result.scalar_one_or_none()
        
        if article:
            article.vote_score = int(vote_sum) if vote_sum else 0  # Sum of vote values
            article.vote_count = int(vote_cnt) if vote_cnt else 0  # Count of votes
            await self.db.commit()
    
    # ========== COMMENT VOTING METHODS ==========
    
    async def get_comment_vote(
        self,
        user_id: UUID,
        comment_id: UUID
    ) -> Optional[Vote]:
        """Get user's vote on a comment."""
        query = select(Vote).where(
            and_(
                Vote.user_id == user_id,
                Vote.comment_id == comment_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_comment_vote(
        self,
        user_id: UUID,
        comment_id: UUID,
        vote_value: int
    ) -> Vote:
        """Create a new comment vote."""
        vote = Vote(
            user_id=user_id,
            comment_id=comment_id,
            vote_value=vote_value
        )
        self.db.add(vote)
        await self.db.commit()
        await self.db.refresh(vote)
        
        # Update comment metrics
        await self.update_comment_vote_metrics(comment_id)
        
        return vote
    
    async def update_comment_vote(
        self,
        vote: Vote,
        new_value: int
    ) -> Vote:
        """Update existing comment vote."""
        vote.vote_value = new_value
        await self.db.commit()
        await self.db.refresh(vote)
        
        # Update comment metrics
        await self.update_comment_vote_metrics(vote.comment_id)
        
        return vote
    
    async def delete_comment_vote(
        self,
        vote: Vote
    ) -> None:
        """Delete a comment vote."""
        comment_id = vote.comment_id
        await self.db.delete(vote)
        await self.db.commit()
        
        # Update comment metrics
        await self.update_comment_vote_metrics(comment_id)
    
    async def update_comment_vote_metrics(
        self,
        comment_id: UUID
    ) -> None:
        """
        Update BOTH vote_score and vote_count for a comment.
        
        - vote_score: Sum of all vote values (can be negative)
        - vote_count: Total number of votes cast
        """
        # Get sum of vote values (score)
        vote_sum_query = select(func.sum(Vote.vote_value)).where(
            Vote.comment_id == comment_id
        )
        vote_sum = await self.db.scalar(vote_sum_query)
        
        # Get count of votes (total number)
        vote_count_query = select(func.count(Vote.id)).where(
            Vote.comment_id == comment_id
        )
        vote_cnt = await self.db.scalar(vote_count_query)
        
        # Update comment with BOTH metrics
        comment_query = select(Comment).where(Comment.id == comment_id)
        result = await self.db.execute(comment_query)
        comment = result.scalar_one_or_none()
        
        if comment:
            comment.vote_score = int(vote_sum) if vote_sum else 0
            comment.vote_count = int(vote_cnt) if vote_cnt else 0
            await self.db.commit()
