"""
Pydantic schemas for request/response validation.
"""
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    Token,
    TokenRefresh,
    TokenData,
)
from app.schemas.article import (
    ArticleBase,
    ArticleCreate,
    ArticleResponse,
    ArticleList,
    ArticleFeed,
)
from app.schemas.vote import (
    VoteCreate,
    VoteResponse,
    VoteDelete,
)
from app.schemas.comment import (
    CommentBase,
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentTree,
    CommentList,
)
from app.schemas.rss_source import (
    RSSSourceBase,
    RSSSourceCreate,
    RSSSourceUpdate,
    RSSSourceResponse,
)
from app.schemas.notification import (
    NotificationBase,
    NotificationCreate,
    NotificationResponse,
    NotificationList,
    NotificationMarkRead,
    NotificationMarkReadResponse,
    NotificationPreferenceBase,
    NotificationPreferenceCreate,
    NotificationPreferenceUpdate,
    NotificationPreferenceResponse,
    NotificationStats,
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
