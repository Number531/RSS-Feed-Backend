"""
Pydantic schemas for request/response validation.
"""

from app.schemas.article import (
    ArticleBase,
    ArticleCreate,
    ArticleFeed,
    ArticleList,
    ArticleResponse,
)
from app.schemas.comment import (
    CommentBase,
    CommentCreate,
    CommentList,
    CommentResponse,
    CommentTree,
    CommentUpdate,
)
from app.schemas.notification import (
    NotificationBase,
    NotificationCreate,
    NotificationList,
    NotificationMarkRead,
    NotificationMarkReadResponse,
    NotificationPreferenceBase,
    NotificationPreferenceCreate,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationResponse,
    NotificationStats,
)
from app.schemas.rss_source import (
    RSSSourceBase,
    RSSSourceCreate,
    RSSSourceResponse,
    RSSSourceUpdate,
)
from app.schemas.user import (
    Token,
    TokenData,
    TokenRefresh,
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from app.schemas.vote import (
    VoteCreate,
    VoteDelete,
    VoteResponse,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "Token",
    "TokenRefresh",
    "TokenData",
    # Article schemas
    "ArticleBase",
    "ArticleCreate",
    "ArticleResponse",
    "ArticleList",
    "ArticleFeed",
    # Vote schemas
    "VoteCreate",
    "VoteResponse",
    "VoteDelete",
    # Comment schemas
    "CommentBase",
    "CommentCreate",
    "CommentUpdate",
    "CommentResponse",
    "CommentTree",
    "CommentList",
    # RSS Source schemas
    "RSSSourceBase",
    "RSSSourceCreate",
    "RSSSourceUpdate",
    "RSSSourceResponse",
    # Notification schemas
    "NotificationBase",
    "NotificationCreate",
    "NotificationResponse",
    "NotificationList",
    "NotificationMarkRead",
    "NotificationMarkReadResponse",
    "NotificationPreferenceBase",
    "NotificationPreferenceCreate",
    "NotificationPreferenceUpdate",
    "NotificationPreferenceResponse",
    "NotificationStats",
]
