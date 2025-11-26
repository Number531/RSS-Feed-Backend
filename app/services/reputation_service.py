"""User reputation and leaderboard service."""

from typing import Dict, Any, List
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.vote import Vote
from app.models.comment import Comment
from app.models.bookmark import Bookmark


class ReputationService:
    """Calculate user reputation scores and generate leaderboards."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_leaderboard(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get top users by reputation score.
        
        Reputation calculated as:
        - Upvotes received: +10 points each
        - Comments posted: +5 points each
        - Bookmarks received on articles: +15 points each
        
        Args:
            limit: Number of users to return (default: 50, max: 100)
            
        Returns:
            List of users with reputation scores
        """
        limit = min(limit, 100)
        
        # Get all users with aggregated stats
        query = (
            select(
                User.id,
                User.username,
                User.full_name,
                User.avatar_url,
                User.created_at,
                func.count(Vote.id).label('total_votes_received'),
                func.count(Comment.id).label('total_comments'),
                func.count(Bookmark.id).label('total_bookmarks_received')
            )
            .outerjoin(Vote, Vote.user_id == User.id)
            .outerjoin(Comment, Comment.user_id == User.id)
            .outerjoin(Bookmark, Bookmark.user_id == User.id)
            .group_by(User.id, User.username, User.full_name, User.avatar_url, User.created_at)
        )
        
        result = await self.db.execute(query)
        users = result.all()
        
        # Calculate reputation scores
        leaderboard = []
        for user in users:
            reputation_score = (
                user.total_votes_received * 10 +
                user.total_comments * 5 +
                user.total_bookmarks_received * 15
            )
            
            leaderboard.append({
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "display_name": user.full_name,
                    "avatar_url": user.avatar_url,
                    "is_admin": False  # Would need to add is_admin field to User model
                },
                "total_reputation": reputation_score,
                "vote_count": user.total_votes_received,
                "comment_count": user.total_comments,
                "bookmark_count": user.total_bookmarks_received,
                "badges": [],  # Will be populated below
                "rank": None  # Will be populated in loop below
            })
        
        # Sort by reputation score descending
        leaderboard.sort(key=lambda x: x["total_reputation"], reverse=True)
        
        # Add rank and badges
        for i, user_data in enumerate(leaderboard[:limit], start=1):
            user_data["rank"] = i
            # Calculate badges based on reputation and activity
            user_data["badges"] = self._calculate_badges_for_leaderboard(
                user_data["total_reputation"],
                user_data["comment_count"],
                user_data["vote_count"]
            )
        
        return leaderboard[:limit]

    async def get_user_reputation(self, user_id: str) -> Dict[str, Any]:
        """
        Get reputation details for a specific user.
        
        Args:
            user_id: User UUID
            
        Returns:
            User reputation data with stats and rank
        """
        # Get user
        user_query = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Get stats
        votes_query = select(func.count(Vote.id)).where(Vote.user_id == user_id)
        votes_count = (await self.db.execute(votes_query)).scalar_one()
        
        comments_query = select(func.count(Comment.id)).where(Comment.user_id == user_id)
        comments_count = (await self.db.execute(comments_query)).scalar_one()
        
        bookmarks_query = select(func.count(Bookmark.id)).where(Bookmark.user_id == user_id)
        bookmarks_count = (await self.db.execute(bookmarks_query)).scalar_one()
        
        # Calculate reputation
        reputation_score = (
            votes_count * 10 +
            comments_count * 5 +
            bookmarks_count * 15
        )
        
        # Get user's rank from leaderboard
        leaderboard = await self.get_leaderboard(limit=1000)
        user_rank = next((u["rank"] for u in leaderboard if u["user"]["id"] == user_id), None)
        
        return {
            "user": {
                "id": user_id,
                "username": user.username,
                "display_name": user.full_name,
                "avatar_url": user.avatar_url,
                "is_admin": False  # Would need to add is_admin field to User model
            },
            "total_reputation": reputation_score,
            "vote_count": votes_count,
            "comment_count": comments_count,
            "bookmark_count": bookmarks_count,
            "badges": self._calculate_badges_for_leaderboard(
                reputation_score, comments_count, votes_count
            ),
            "rank": user_rank
        }

    def _calculate_badges(self, reputation: int, comments: int, votes: int) -> List[str]:
        """Calculate badges earned by user."""
        badges = []
        
        if reputation >= 1000:
            badges.append("expert")
        elif reputation >= 500:
            badges.append("veteran")
        elif reputation >= 100:
            badges.append("contributor")
        
        if comments >= 100:
            badges.append("commentator")
        
        if votes >= 50:
            badges.append("voter")
        
        return badges

    def _calculate_badges_for_leaderboard(
        self, reputation: int, comments: int, votes: int
    ) -> List[Dict[str, Any]]:
        """Calculate badges with full structure for leaderboard."""
        badges = []
        from datetime import datetime
        
        now = datetime.utcnow().isoformat()
        
        if reputation >= 1000:
            badges.append({
                "type": "expert",
                "name": "Expert",
                "earned_at": now
            })
        elif reputation >= 500:
            badges.append({
                "type": "veteran",
                "name": "Veteran",
                "earned_at": now
            })
        elif reputation >= 100:
            badges.append({
                "type": "contributor",
                "name": "Contributor",
                "earned_at": now
            })
        
        if comments >= 100:
            badges.append({
                "type": "commentator",
                "name": "Commentator",
                "earned_at": now
            })
        
        if votes >= 50:
            badges.append({
                "type": "voter",
                "name": "Voter",
                "earned_at": now
            })
        
        return badges
