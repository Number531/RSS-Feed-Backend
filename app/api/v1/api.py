"""API v1 router aggregator."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    analytics,
    articles,
    auth,
    bookmarks,
    comments,
    fact_check,
    notifications,
    reading_history,
    rss_feeds,
    search,
    users,
    votes,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(search.router, tags=["search"])  # Search & discovery endpoints
api_router.include_router(rss_feeds.router)  # Already has prefix and tags in router definition
api_router.include_router(votes.router, prefix="/votes", tags=["votes"])
api_router.include_router(comments.router, prefix="/comments", tags=["comments"])
api_router.include_router(articles.router, prefix="/articles", tags=["articles"])
api_router.include_router(
    fact_check.router, tags=["fact-check"]
)  # Uses /articles/{article_id}/fact-check
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(bookmarks.router, prefix="/bookmarks", tags=["bookmarks"])
api_router.include_router(
    reading_history.router, prefix="/reading-history", tags=["reading-history"]
)
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
