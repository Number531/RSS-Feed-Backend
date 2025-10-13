"""Business logic for bookmarks."""
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status

from app.repositories.bookmark_repository import BookmarkRepository
from app.repositories.article_repository import ArticleRepository
from app.models.bookmark import Bookmark
from app.core.exceptions import NotFoundError, ConflictError


class BookmarkService:
    """Service for bookmark business logic."""
    
    def __init__(
        self,
        bookmark_repo: BookmarkRepository,
        article_repo: ArticleRepository,
    ):
        self.bookmark_repo = bookmark_repo
        self.article_repo = article_repo
    
    async def create_bookmark(
        self,
        user_id: UUID,
        article_id: UUID,
        collection: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Bookmark:
        """Create a bookmark for an article."""
        # Check if article exists
        article = await self.article_repo.get_article_by_id(article_id)
        if not article:
            raise NotFoundError(f"Article {article_id} not found")
        
        # Check if bookmark already exists
        existing = await self.bookmark_repo.get_by_user_and_article(user_id, article_id)
        if existing:
            raise ConflictError(f"Article {article_id} is already bookmarked")
        
        # Create bookmark
        return await self.bookmark_repo.create(
            user_id=user_id,
            article_id=article_id,
            collection=collection,
            notes=notes,
        )
    
    async def get_bookmark(self, bookmark_id: UUID, user_id: UUID) -> Bookmark:
        """Get a bookmark by ID (with ownership check)."""
        bookmark = await self.bookmark_repo.get_by_id(bookmark_id)
        if not bookmark:
            raise NotFoundError(f"Bookmark {bookmark_id} not found")
        
        if bookmark.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this bookmark"
            )
        
        return bookmark
    
    async def check_bookmarked(self, user_id: UUID, article_id: UUID) -> bool:
        """Check if an article is bookmarked by user."""
        return await self.bookmark_repo.exists(user_id, article_id)
    
    async def list_bookmarks(
        self,
        user_id: UUID,
        collection: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[Bookmark], int]:
        """List user's bookmarks with pagination."""
        skip = (page - 1) * page_size
        return await self.bookmark_repo.list_by_user(
            user_id=user_id,
            collection=collection,
            skip=skip,
            limit=page_size,
        )
    
    async def get_collections(self, user_id: UUID) -> list[str]:
        """Get user's bookmark collections."""
        return await self.bookmark_repo.get_collections(user_id)
    
    async def update_bookmark(
        self,
        bookmark_id: UUID,
        user_id: UUID,
        collection: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Bookmark:
        """Update a bookmark."""
        # Check ownership
        bookmark = await self.get_bookmark(bookmark_id, user_id)
        
        # Update
        updated = await self.bookmark_repo.update(
            bookmark_id=bookmark_id,
            collection=collection,
            notes=notes,
        )
        
        if not updated:
            raise NotFoundError(f"Bookmark {bookmark_id} not found")
        
        return updated
    
    async def delete_bookmark(self, bookmark_id: UUID, user_id: UUID) -> None:
        """Delete a bookmark."""
        # Check ownership
        await self.get_bookmark(bookmark_id, user_id)
        
        # Delete
        deleted = await self.bookmark_repo.delete(bookmark_id)
        if not deleted:
            raise NotFoundError(f"Bookmark {bookmark_id} not found")
    
    async def delete_by_article(self, user_id: UUID, article_id: UUID) -> None:
        """Delete a bookmark by article ID."""
        deleted = await self.bookmark_repo.delete_by_user_and_article(user_id, article_id)
        if not deleted:
            raise NotFoundError(f"Bookmark for article {article_id} not found")
    
    async def get_bookmark_count(self, user_id: UUID) -> int:
        """Get total bookmark count for user."""
        return await self.bookmark_repo.count_by_user(user_id)
