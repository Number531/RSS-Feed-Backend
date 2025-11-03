"""
API Dependencies

Provides dependency injection for repositories and services.
Manages database sessions and service instantiation.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.article_repository import ArticleRepository
from app.repositories.comment_repository import CommentRepository
from app.repositories.fact_check_repository import FactCheckRepository
from app.repositories.reading_history_repository import ReadingHistoryRepository
from app.repositories.reading_preferences_repository import ReadingPreferencesRepository
from app.repositories.user_repository import UserRepository
from app.repositories.vote_repository import VoteRepository
from app.services.article_service import ArticleService
from app.services.comment_service import CommentService
from app.services.comment_vote_service import CommentVoteService
from app.services.fact_check_service import FactCheckService
from app.services.reading_history_service import ReadingHistoryService
from app.services.user_service import UserService
from app.services.vote_service import VoteService

# Repository Dependencies


def get_article_repository(db: AsyncSession = Depends(get_db)) -> ArticleRepository:
    """
    Get article repository instance.

    Args:
        db: Database session

    Returns:
        ArticleRepository instance
    """
    return ArticleRepository(db)


def get_vote_repository(db: AsyncSession = Depends(get_db)) -> VoteRepository:
    """
    Get vote repository instance.

    Args:
        db: Database session

    Returns:
        VoteRepository instance
    """
    return VoteRepository(db)


def get_comment_repository(db: AsyncSession = Depends(get_db)) -> CommentRepository:
    """
    Get comment repository instance.

    Args:
        db: Database session

    Returns:
        CommentRepository instance
    """
    return CommentRepository(db)


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """
    Get user repository instance.

    Args:
        db: Database session

    Returns:
        UserRepository instance
    """
    return UserRepository(db)


def get_reading_history_repository(db: AsyncSession = Depends(get_db)) -> ReadingHistoryRepository:
    """
    Get reading history repository instance.

    Args:
        db: Database session

    Returns:
        ReadingHistoryRepository instance
    """
    return ReadingHistoryRepository(db)


def get_reading_preferences_repository(
    db: AsyncSession = Depends(get_db),
) -> ReadingPreferencesRepository:
    """
    Get reading preferences repository instance.

    Args:
        db: Database session

    Returns:
        ReadingPreferencesRepository instance
    """
    return ReadingPreferencesRepository(db)


def get_fact_check_repository(db: AsyncSession = Depends(get_db)) -> FactCheckRepository:
    """
    Get fact check repository instance.

    Args:
        db: Database session

    Returns:
        FactCheckRepository instance
    """
    return FactCheckRepository(db)


# Service Dependencies


def get_article_service(
    article_repo: ArticleRepository = Depends(get_article_repository),
) -> ArticleService:
    """
    Get article service instance.

    Args:
        article_repo: Article repository

    Returns:
        ArticleService instance
    """
    return ArticleService(article_repo)


def get_vote_service(
    vote_repo: VoteRepository = Depends(get_vote_repository),
    article_repo: ArticleRepository = Depends(get_article_repository),
) -> VoteService:
    """
    Get vote service instance.

    Args:
        vote_repo: Vote repository
        article_repo: Article repository

    Returns:
        VoteService instance
    """
    return VoteService(vote_repo, article_repo)


def get_comment_service(
    comment_repo: CommentRepository = Depends(get_comment_repository),
    article_repo: ArticleRepository = Depends(get_article_repository),
) -> CommentService:
    """
    Get comment service instance.

    Args:
        comment_repo: Comment repository
        article_repo: Article repository

    Returns:
        CommentService instance
    """
    return CommentService(comment_repo, article_repo)


def get_comment_vote_service(
    vote_repo: VoteRepository = Depends(get_vote_repository),
    comment_repo: CommentRepository = Depends(get_comment_repository),
) -> CommentVoteService:
    """
    Get comment vote service instance.

    Args:
        vote_repo: Vote repository
        comment_repo: Comment repository

    Returns:
        CommentVoteService instance
    """
    return CommentVoteService(vote_repo, comment_repo)


def get_user_service(user_repo: UserRepository = Depends(get_user_repository)) -> UserService:
    """
    Get user service instance.

    Args:
        user_repo: User repository

    Returns:
        UserService instance
    """
    return UserService(user_repo)


def get_reading_history_service(
    reading_history_repo: ReadingHistoryRepository = Depends(get_reading_history_repository),
    reading_preferences_repo: ReadingPreferencesRepository = Depends(
        get_reading_preferences_repository
    ),
    article_repo: ArticleRepository = Depends(get_article_repository),
) -> ReadingHistoryService:
    """
    Get reading history service instance.

    Args:
        reading_history_repo: Reading history repository
        reading_preferences_repo: Reading preferences repository
        article_repo: Article repository

    Returns:
        ReadingHistoryService instance
    """
    return ReadingHistoryService(
        reading_history_repo=reading_history_repo,
        reading_preferences_repo=reading_preferences_repo,
        article_repo=article_repo,
    )


def get_fact_check_service(
    fact_check_repo: FactCheckRepository = Depends(get_fact_check_repository),
    article_repo: ArticleRepository = Depends(get_article_repository),
) -> FactCheckService:
    """
    Get fact check service instance.

    Args:
        fact_check_repo: Fact check repository
        article_repo: Article repository

    Returns:
        FactCheckService instance
    """
    return FactCheckService(fact_check_repo, article_repo)
