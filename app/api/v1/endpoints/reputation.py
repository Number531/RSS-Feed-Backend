"""User reputation and leaderboard API endpoints."""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.reputation_service import ReputationService

router = APIRouter()


@router.get(
    "/leaderboard",
    summary="Get user leaderboard",
    description="""
    Get top users ranked by reputation score.
    
    **Reputation Formula:**
    - Votes received: +10 points each
    - Comments posted: +5 points each  
    - Bookmarks received: +15 points each
    
    **Response includes:**
    - User profile data
    - Reputation score
    - Activity stats
    - Global rank
    - Earned badges
    
    **Use Cases:**
    - Gamification dashboards
    - Community engagement
    - Top contributors showcase
    - User motivation
    """,
    tags=["reputation"],
)
async def get_leaderboard(
    limit: int = Query(50, ge=1, le=100, description="Number of users to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get user leaderboard ranked by reputation."""
    service = ReputationService(db)
    leaderboard = await service.get_leaderboard(limit=limit)
    
    return {
        "leaderboard": leaderboard,
        "total_users": len(leaderboard),
        "limit": limit
    }


@router.get(
    "/users/{user_id}",
    summary="Get user reputation",
    description="""
    Get detailed reputation information for a specific user.
    
    **Includes:**
    - Total reputation score
    - Global rank
    - Activity statistics
    - Earned badges
    
    **Badges:**
    - `expert`: 1000+ reputation
    - `veteran`: 500+ reputation
    - `contributor`: 100+ reputation
    - `commentator`: 100+ comments
    - `voter`: 50+ votes
    """,
    tags=["reputation"],
)
async def get_user_reputation(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get reputation for a specific user."""
    service = ReputationService(db)
    
    try:
        reputation = await service.get_user_reputation(user_id)
        return reputation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
