"""
API v1 router aggregator.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, votes, comments, articles, users, bookmarks, reading_history, notifications

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(votes.router, prefix="/votes", tags=["votes"])
api_router.include_router(comments.router, prefix="/comments", tags=["comments"])
api_router.include_router(articles.router, prefix="/articles", tags=["articles"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(bookmarks.router, prefix="/bookmarks", tags=["bookmarks"])
api_router.include_router(reading_history.router, prefix="/reading-history", tags=["reading-history"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
