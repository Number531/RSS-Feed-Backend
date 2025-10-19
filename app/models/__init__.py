"""
SQLAlchemy models.
"""
from app.models.user import User
from app.models.rss_source import RSSSource
from app.models.article import Article
from app.models.vote import Vote
from app.models.comment import Comment
from app.models.bookmark import Bookmark
from app.models.reading_history import ReadingHistory
from app.models.user_reading_preferences import UserReadingPreferences
from app.models.notification import Notification, UserNotificationPreference
from app.models.fact_check import ArticleFactCheck, SourceCredibilityScore

__all__ = [
    "User",
    "RSSSource",
    "Article",
    "Vote",
    "Comment",
    "Bookmark",
    "ReadingHistory",
    "UserReadingPreferences",
    "Notification",
    "UserNotificationPreference",
    "ArticleFactCheck",
    "SourceCredibilityScore",
]
