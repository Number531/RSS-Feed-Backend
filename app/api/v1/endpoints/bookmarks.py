"""Bookmark management endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.article_repository import ArticleRepository
from app.repositories.bookmark_repository import BookmarkRepository
from app.schemas.bookmark import (
    BookmarkCreate,
    BookmarkListResponse,
    BookmarkResponse,
    BookmarkStatusResponse,
    BookmarkUpdate,
    CollectionListResponse,
)
from app.services.bookmark_service import BookmarkService

router = APIRouter()


def get_bookmark_service(db: AsyncSession = Depends(get_db)) -> BookmarkService:
    """Dependency for bookmark service."""
    bookmark_repo = BookmarkRepository(db)
    article_repo = ArticleRepository(db)
    return BookmarkService(bookmark_repo, article_repo)


@router.post(
    "/",
    response_model=BookmarkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a bookmark",
    description="Save an article for later reading",
)
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    service: BookmarkService = Depends(get_bookmark_service),
) -> BookmarkResponse:
    """Create a new bookmark."""
    bookmark = await service.create_bookmark(
        user_id=current_user.id,
        article_id=bookmark_data.article_id,
        collection=bookmark_data.collection,
        notes=bookmark_data.notes,
    )
    return BookmarkResponse.model_validate(bookmark)


@router.get(
    "/",
    response_model=BookmarkListResponse,
    summary="List bookmarks",
    description="Get all bookmarks for the current user with pagination",
)
async def list_bookmarks(
    collection: Optional[str] = Query(None, description="Filter by collection name"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    service: BookmarkService = Depends(get_bookmark_service),
) -> BookmarkListResponse:
    """List user's bookmarks."""
    bookmarks, total = await service.list_bookmarks(
        user_id=current_user.id,
        collection=collection,
        page=page,
        page_size=page_size,
    )

    return BookmarkListResponse(
        items=[BookmarkResponse.model_validate(b) for b in bookmarks],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get(
    "/collections",
    response_model=CollectionListResponse,
    summary="List collections",
    description="Get all bookmark collection names for the current user",
)
async def list_collections(
    current_user: User = Depends(get_current_user),
    service: BookmarkService = Depends(get_bookmark_service),
) -> CollectionListResponse:
    """Get user's bookmark collections."""
    collections = await service.get_collections(current_user.id)
    return CollectionListResponse(
        collections=collections,
        total=len(collections),
    )


@router.get(
    "/check/{article_id}",
    response_model=BookmarkStatusResponse,
    summary="Check bookmark status",
    description="Check if an article is bookmarked by the current user",
)
async def check_bookmark_status(
    article_id: UUID,
    current_user: User = Depends(get_current_user),
    service: BookmarkService = Depends(get_bookmark_service),
) -> BookmarkStatusResponse:
    """Check if article is bookmarked."""
    is_bookmarked = await service.check_bookmarked(current_user.id, article_id)
    return BookmarkStatusResponse(
        article_id=article_id,
        is_bookmarked=is_bookmarked,
    )


@router.get(
    "/{bookmark_id}",
    response_model=BookmarkResponse,
    summary="Get bookmark",
    description="Get a specific bookmark by ID",
)
async def get_bookmark(
    bookmark_id: UUID,
    current_user: User = Depends(get_current_user),
    service: BookmarkService = Depends(get_bookmark_service),
) -> BookmarkResponse:
    """Get bookmark by ID."""
    bookmark = await service.get_bookmark(bookmark_id, current_user.id)
    return BookmarkResponse.model_validate(bookmark)


@router.patch(
    "/{bookmark_id}",
    response_model=BookmarkResponse,
    summary="Update bookmark",
    description="Update bookmark collection or notes",
)
async def update_bookmark(
    bookmark_id: UUID,
    update_data: BookmarkUpdate,
    current_user: User = Depends(get_current_user),
    service: BookmarkService = Depends(get_bookmark_service),
) -> BookmarkResponse:
    """Update a bookmark."""
    bookmark = await service.update_bookmark(
        bookmark_id=bookmark_id,
        user_id=current_user.id,
        collection=update_data.collection,
        notes=update_data.notes,
    )
    return BookmarkResponse.model_validate(bookmark)


@router.delete(
    "/{bookmark_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete bookmark",
    description="Remove a bookmark by ID",
)
async def delete_bookmark(
    bookmark_id: UUID,
    current_user: User = Depends(get_current_user),
    service: BookmarkService = Depends(get_bookmark_service),
) -> None:
    """Delete a bookmark."""
    await service.delete_bookmark(bookmark_id, current_user.id)


@router.delete(
    "/article/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete bookmark by article",
    description="Remove a bookmark by article ID",
)
async def delete_bookmark_by_article(
    article_id: UUID,
    current_user: User = Depends(get_current_user),
    service: BookmarkService = Depends(get_bookmark_service),
) -> None:
    """Delete bookmark by article ID."""
    await service.delete_by_article(current_user.id, article_id)
