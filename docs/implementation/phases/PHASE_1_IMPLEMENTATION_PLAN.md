# Phase 1: Core Features Implementation Plan

**Project**: RSS News Aggregator  
**Phase**: Phase 1 - Complete Core Features  
**Estimated Duration**: 6-7 days  
**Start Date**: 2025-10-10

---

## 📋 Overview

This plan covers the implementation of four essential features:
1. **Bookmarks/Saved Articles** (2-3 days)
2. **User Activity History** (2 days)
3. **User Preferences** (1-2 days)
4. **Complete User Stats** (1 day)

Each feature follows a consistent architecture:
- Database schema/migrations
- SQLAlchemy models
- Repository layer (data access)
- Service layer (business logic)
- API endpoints (REST interface)
- Pydantic schemas (validation)
- Comprehensive integration tests

---

## 🎯 Success Criteria

- [ ] All endpoints functional and documented
- [ ] 100% pass rate on integration tests
- [ ] Proper error handling and validation
- [ ] Authentication and authorization working
- [ ] Database migrations applied successfully
- [ ] API documentation updated in OpenAPI
- [ ] No breaking changes to existing endpoints
- [ ] Performance acceptable (< 200ms for most queries)

---

## 📅 Day-by-Day Plan

### **Day 1: Bookmarks - Foundation** (Database + Models + Repository)

#### **Step 1.1: Database Schema & Migration** (1 hour)

**File**: `backend/alembic/versions/XXX_add_bookmarks_table.py`

```python
"""add bookmarks table

Revision ID: xxx
Revises: previous_revision_id
Create Date: 2025-10-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'xxx'
down_revision = 'previous_revision_id'  # Get from latest migration
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create bookmarks table
    op.create_table(
        'bookmarks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('article_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('articles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('collection', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('user_id', 'article_id', name='uq_user_article_bookmark'),
    )
    
    # Create indexes for performance
    op.create_index('idx_bookmarks_user_id', 'bookmarks', ['user_id'])
    op.create_index('idx_bookmarks_article_id', 'bookmarks', ['article_id'])
    op.create_index('idx_bookmarks_created_at', 'bookmarks', ['created_at'])
    op.create_index('idx_bookmarks_collection', 'bookmarks', ['collection'], postgresql_where=sa.text('collection IS NOT NULL'))

def downgrade() -> None:
    op.drop_index('idx_bookmarks_collection', table_name='bookmarks')
    op.drop_index('idx_bookmarks_created_at', table_name='bookmarks')
    op.drop_index('idx_bookmarks_article_id', table_name='bookmarks')
    op.drop_index('idx_bookmarks_user_id', table_name='bookmarks')
    op.drop_table('bookmarks')
```

**Commands**:
```bash
# Generate migration (or create manually as above)
cd /Users/ej/Downloads/RSS-Feed/backend
alembic revision -m "add bookmarks table"

# Edit the generated file with the schema above

# Apply migration
alembic upgrade head

# Verify
alembic current
```

**Verification**:
- [ ] Migration file created
- [ ] Migration applied successfully
- [ ] Table `bookmarks` exists in database
- [ ] Indexes created
- [ ] Constraints in place

---

#### **Step 1.2: SQLAlchemy Model** (30 minutes)

**File**: `backend/app/models/bookmark.py`

```python
"""Bookmark model for saved articles."""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.article import Article


class Bookmark(Base):
    """Bookmark model for user-saved articles."""
    
    __tablename__ = "bookmarks"
    
    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=sa.text("gen_random_uuid()")
    )
    
    # Foreign Keys
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    article_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Data
    collection: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        server_default=sa.func.now(),
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="bookmarks")
    article: Mapped["Article"] = relationship("Article", back_populates="bookmarks")
    
    # Indexes
    __table_args__ = (
        Index("idx_bookmarks_user_id", "user_id"),
        Index("idx_bookmarks_article_id", "article_id"),
        Index("idx_bookmarks_created_at", "created_at"),
        Index(
            "idx_bookmarks_collection",
            "collection",
            postgresql_where=sa.text("collection IS NOT NULL")
        ),
        sa.UniqueConstraint("user_id", "article_id", name="uq_user_article_bookmark"),
    )
    
    def __repr__(self) -> str:
        return f"<Bookmark user={self.user_id} article={self.article_id}>"
```

**Update existing models**:

**File**: `backend/app/models/user.py` (add relationship)
```python
# Add to User model
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.bookmark import Bookmark

# Add to User class
bookmarks: Mapped[list["Bookmark"]] = relationship(
    "Bookmark",
    back_populates="user",
    cascade="all, delete-orphan"
)
```

**File**: `backend/app/models/article.py` (add relationship)
```python
# Add to Article model
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.bookmark import Bookmark

# Add to Article class
bookmarks: Mapped[list["Bookmark"]] = relationship(
    "Bookmark",
    back_populates="article",
    cascade="all, delete-orphan"
)
```

**File**: `backend/app/models/__init__.py` (register model)
```python
from app.models.bookmark import Bookmark

__all__ = [
    # ... existing exports
    "Bookmark",
]
```

**Verification**:
- [ ] Model created with all fields
- [ ] Relationships defined (User, Article)
- [ ] Constraints and indexes defined
- [ ] Model registered in `__init__.py`
- [ ] Python imports work without errors

---

#### **Step 1.3: Repository Layer** (1 hour)

**File**: `backend/app/repositories/bookmark_repository.py`

```python
"""Repository for bookmark data access."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.bookmark import Bookmark
from app.models.article import Article


class BookmarkRepository:
    """Repository for bookmark database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        user_id: UUID,
        article_id: UUID,
        collection: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Bookmark:
        """Create a new bookmark."""
        bookmark = Bookmark(
            user_id=user_id,
            article_id=article_id,
            collection=collection,
            notes=notes,
        )
        self.db.add(bookmark)
        await self.db.commit()
        await self.db.refresh(bookmark)
        return bookmark
    
    async def get_by_id(self, bookmark_id: UUID) -> Optional[Bookmark]:
        """Get a bookmark by ID."""
        result = await self.db.execute(
            select(Bookmark)
            .where(Bookmark.id == bookmark_id)
            .options(selectinload(Bookmark.article))
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_and_article(
        self,
        user_id: UUID,
        article_id: UUID
    ) -> Optional[Bookmark]:
        """Get a bookmark by user and article."""
        result = await self.db.execute(
            select(Bookmark)
            .where(
                and_(
                    Bookmark.user_id == user_id,
                    Bookmark.article_id == article_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def exists(self, user_id: UUID, article_id: UUID) -> bool:
        """Check if a bookmark exists."""
        result = await self.db.execute(
            select(func.count())
            .select_from(Bookmark)
            .where(
                and_(
                    Bookmark.user_id == user_id,
                    Bookmark.article_id == article_id
                )
            )
        )
        count = result.scalar_one()
        return count > 0
    
    async def list_by_user(
        self,
        user_id: UUID,
        collection: Optional[str] = None,
        skip: int = 0,
        limit: int = 25,
    ) -> tuple[list[Bookmark], int]:
        """List bookmarks for a user with pagination."""
        # Build base query
        query = (
            select(Bookmark)
            .where(Bookmark.user_id == user_id)
            .options(selectinload(Bookmark.article))
            .order_by(Bookmark.created_at.desc())
        )
        
        # Filter by collection if provided
        if collection:
            query = query.where(Bookmark.collection == collection)
        
        # Get total count
        count_query = select(func.count()).select_from(Bookmark).where(Bookmark.user_id == user_id)
        if collection:
            count_query = count_query.where(Bookmark.collection == collection)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        bookmarks = result.scalars().all()
        
        return list(bookmarks), total
    
    async def get_collections(self, user_id: UUID) -> list[str]:
        """Get list of unique collection names for a user."""
        result = await self.db.execute(
            select(Bookmark.collection)
            .where(
                and_(
                    Bookmark.user_id == user_id,
                    Bookmark.collection.isnot(None)
                )
            )
            .distinct()
            .order_by(Bookmark.collection)
        )
        return list(result.scalars().all())
    
    async def update(
        self,
        bookmark_id: UUID,
        collection: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[Bookmark]:
        """Update a bookmark."""
        bookmark = await self.get_by_id(bookmark_id)
        if not bookmark:
            return None
        
        if collection is not None:
            bookmark.collection = collection
        if notes is not None:
            bookmark.notes = notes
        
        await self.db.commit()
        await self.db.refresh(bookmark)
        return bookmark
    
    async def delete(self, bookmark_id: UUID) -> bool:
        """Delete a bookmark."""
        result = await self.db.execute(
            delete(Bookmark).where(Bookmark.id == bookmark_id)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def delete_by_user_and_article(
        self,
        user_id: UUID,
        article_id: UUID
    ) -> bool:
        """Delete a bookmark by user and article."""
        result = await self.db.execute(
            delete(Bookmark).where(
                and_(
                    Bookmark.user_id == user_id,
                    Bookmark.article_id == article_id
                )
            )
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def count_by_user(self, user_id: UUID) -> int:
        """Count total bookmarks for a user."""
        result = await self.db.execute(
            select(func.count())
            .select_from(Bookmark)
            .where(Bookmark.user_id == user_id)
        )
        return result.scalar_one()
```

**Verification**:
- [ ] All CRUD methods implemented
- [ ] Async/await properly used
- [ ] Type hints correct
- [ ] Pagination support
- [ ] Collection filtering
- [ ] Error handling in place

---

### **Day 2: Bookmarks - Service + API** (Service Layer + Endpoints + Tests)

#### **Step 2.1: Service Layer** (1 hour)

**File**: `backend/app/services/bookmark_service.py`

```python
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
        article = await self.article_repo.get_by_id(article_id)
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
```

**Verification**:
- [ ] All business logic methods implemented
- [ ] Authorization checks in place
- [ ] Custom exceptions used properly
- [ ] Article existence validated
- [ ] Duplicate bookmarks prevented

---

#### **Step 2.2: Pydantic Schemas** (30 minutes)

**File**: `backend/app/schemas/bookmark.py`

```python
"""Pydantic schemas for bookmarks."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.article import ArticleResponse


class BookmarkCreate(BaseModel):
    """Schema for creating a bookmark."""
    article_id: UUID = Field(..., description="ID of the article to bookmark")
    collection: Optional[str] = Field(None, max_length=100, description="Optional collection/folder name")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional notes about the bookmark")


class BookmarkUpdate(BaseModel):
    """Schema for updating a bookmark."""
    collection: Optional[str] = Field(None, max_length=100, description="Collection/folder name")
    notes: Optional[str] = Field(None, max_length=1000, description="Notes about the bookmark")


class BookmarkResponse(BaseModel):
    """Schema for bookmark response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    article_id: UUID
    collection: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    article: Optional[ArticleResponse] = None


class BookmarkListResponse(BaseModel):
    """Schema for paginated bookmark list."""
    items: list[BookmarkResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class BookmarkStatusResponse(BaseModel):
    """Schema for bookmark status check."""
    article_id: UUID
    is_bookmarked: bool


class CollectionListResponse(BaseModel):
    """Schema for collections list."""
    collections: list[str]
    total: int
```

**Verification**:
- [ ] All schemas defined
- [ ] Validation rules in place
- [ ] Documentation strings added
- [ ] Proper field types

---

#### **Step 2.3: API Endpoints** (1.5 hours)

**File**: `backend/app/api/v1/endpoints/bookmarks.py`

```python
"""Bookmark management endpoints."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.repositories.bookmark_repository import BookmarkRepository
from app.repositories.article_repository import ArticleRepository
from app.services.bookmark_service import BookmarkService
from app.schemas.bookmark import (
    BookmarkCreate,
    BookmarkUpdate,
    BookmarkResponse,
    BookmarkListResponse,
    BookmarkStatusResponse,
    CollectionListResponse,
)

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
```

**Register router in main API**:

**File**: `backend/app/api/v1/api.py`

```python
from app.api.v1.endpoints import bookmarks

# Add to router includes
api_router.include_router(
    bookmarks.router,
    prefix="/bookmarks",
    tags=["bookmarks"]
)
```

**Verification**:
- [ ] All endpoints defined
- [ ] Proper HTTP methods used
- [ ] Authentication required
- [ ] Response models correct
- [ ] Router registered
- [ ] OpenAPI docs generated

---

#### **Step 2.4: Integration Tests** (2 hours)

**File**: `backend/tests/integration/test_bookmarks.py`

```python
"""Integration tests for bookmark endpoints."""
import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.article import Article
from tests.conftest import create_test_user, create_test_article


class TestBookmarkEndpoints:
    """Test bookmark API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_bookmark_success(
        self,
        client: AsyncClient,
        test_user: User,
        test_article: Article,
        auth_headers: dict,
    ):
        """Test creating a bookmark successfully."""
        response = await client.post(
            "/api/v1/bookmarks/",
            json={
                "article_id": str(test_article.id),
                "collection": "To Read",
                "notes": "Interesting article",
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["article_id"] == str(test_article.id)
        assert data["user_id"] == str(test_user.id)
        assert data["collection"] == "To Read"
        assert data["notes"] == "Interesting article"
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_create_bookmark_duplicate(
        self,
        client: AsyncClient,
        test_user: User,
        test_article: Article,
        auth_headers: dict,
    ):
        """Test creating duplicate bookmark fails."""
        # Create first bookmark
        await client.post(
            "/api/v1/bookmarks/",
            json={"article_id": str(test_article.id)},
            headers=auth_headers,
        )
        
        # Try to create duplicate
        response = await client.post(
            "/api/v1/bookmarks/",
            json={"article_id": str(test_article.id)},
            headers=auth_headers,
        )
        
        assert response.status_code == 409
        assert "already bookmarked" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_create_bookmark_article_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating bookmark for non-existent article."""
        fake_article_id = str(uuid4())
        response = await client.post(
            "/api/v1/bookmarks/",
            json={"article_id": fake_article_id},
            headers=auth_headers,
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_create_bookmark_unauthorized(
        self,
        client: AsyncClient,
        test_article: Article,
    ):
        """Test creating bookmark without authentication."""
        response = await client.post(
            "/api/v1/bookmarks/",
            json={"article_id": str(test_article.id)},
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_list_bookmarks_success(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession,
        auth_headers: dict,
    ):
        """Test listing bookmarks with pagination."""
        # Create multiple bookmarks
        articles = []
        for i in range(5):
            article = await create_test_article(
                db_session,
                title=f"Article {i}",
                url=f"https://example.com/{i}",
            )
            articles.append(article)
            
            await client.post(
                "/api/v1/bookmarks/",
                json={
                    "article_id": str(article.id),
                    "collection": "Reading" if i < 3 else "Archive",
                },
                headers=auth_headers,
            )
        
        # List all bookmarks
        response = await client.get(
            "/api/v1/bookmarks/",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5
        assert data["page"] == 1
        assert data["page_size"] == 25
        assert not data["has_more"]
    
    @pytest.mark.asyncio
    async def test_list_bookmarks_pagination(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession,
        auth_headers: dict,
    ):
        """Test bookmark list pagination."""
        # Create 30 bookmarks
        for i in range(30):
            article = await create_test_article(
                db_session,
                title=f"Article {i}",
                url=f"https://example.com/{i}",
            )
            await client.post(
                "/api/v1/bookmarks/",
                json={"article_id": str(article.id)},
                headers=auth_headers,
            )
        
        # Get first page
        response = await client.get(
            "/api/v1/bookmarks/?page=1&page_size=10",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 30
        assert len(data["items"]) == 10
        assert data["page"] == 1
        assert data["has_more"] is True
        
        # Get second page
        response = await client.get(
            "/api/v1/bookmarks/?page=2&page_size=10",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["page"] == 2
    
    @pytest.mark.asyncio
    async def test_list_bookmarks_filter_by_collection(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession,
        auth_headers: dict,
    ):
        """Test filtering bookmarks by collection."""
        # Create bookmarks in different collections
        for i in range(5):
            article = await create_test_article(
                db_session,
                title=f"Article {i}",
                url=f"https://example.com/{i}",
            )
            collection = "Reading" if i < 3 else "Archive"
            await client.post(
                "/api/v1/bookmarks/",
                json={
                    "article_id": str(article.id),
                    "collection": collection,
                },
                headers=auth_headers,
            )
        
        # Filter by "Reading"
        response = await client.get(
            "/api/v1/bookmarks/?collection=Reading",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert all(item["collection"] == "Reading" for item in data["items"])
    
    @pytest.mark.asyncio
    async def test_get_bookmark_success(
        self,
        client: AsyncClient,
        test_user: User,
        test_article: Article,
        auth_headers: dict,
    ):
        """Test getting a specific bookmark."""
        # Create bookmark
        create_response = await client.post(
            "/api/v1/bookmarks/",
            json={"article_id": str(test_article.id)},
            headers=auth_headers,
        )
        bookmark_id = create_response.json()["id"]
        
        # Get bookmark
        response = await client.get(
            f"/api/v1/bookmarks/{bookmark_id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == bookmark_id
        assert data["article_id"] == str(test_article.id)
    
    @pytest.mark.asyncio
    async def test_get_bookmark_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting non-existent bookmark."""
        fake_bookmark_id = str(uuid4())
        response = await client.get(
            f"/api/v1/bookmarks/{fake_bookmark_id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_bookmark_forbidden(
        self,
        client: AsyncClient,
        test_article: Article,
        db_session: AsyncSession,
    ):
        """Test getting another user's bookmark is forbidden."""
        # Create user 1 and their bookmark
        user1 = await create_test_user(db_session, email="user1@example.com")
        headers1 = {"Authorization": f"Bearer {user1.access_token}"}
        
        create_response = await client.post(
            "/api/v1/bookmarks/",
            json={"article_id": str(test_article.id)},
            headers=headers1,
        )
        bookmark_id = create_response.json()["id"]
        
        # Create user 2
        user2 = await create_test_user(db_session, email="user2@example.com")
        headers2 = {"Authorization": f"Bearer {user2.access_token}"}
        
        # Try to access user1's bookmark as user2
        response = await client.get(
            f"/api/v1/bookmarks/{bookmark_id}",
            headers=headers2,
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_check_bookmark_status(
        self,
        client: AsyncClient,
        test_user: User,
        test_article: Article,
        db_session: AsyncSession,
        auth_headers: dict,
    ):
        """Test checking if article is bookmarked."""
        # Check before bookmarking
        response = await client.get(
            f"/api/v1/bookmarks/check/{test_article.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        assert response.json()["is_bookmarked"] is False
        
        # Create bookmark
        await client.post(
            "/api/v1/bookmarks/",
            json={"article_id": str(test_article.id)},
            headers=auth_headers,
        )
        
        # Check after bookmarking
        response = await client.get(
            f"/api/v1/bookmarks/check/{test_article.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        assert response.json()["is_bookmarked"] is True
    
    @pytest.mark.asyncio
    async def test_list_collections(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession,
        auth_headers: dict,
    ):
        """Test listing bookmark collections."""
        # Create bookmarks in different collections
        collections = ["Reading", "Archive", "Favorites", "Reading"]  # Reading appears twice
        
        for i, collection in enumerate(collections):
            article = await create_test_article(
                db_session,
                title=f"Article {i}",
                url=f"https://example.com/{i}",
            )
            await client.post(
                "/api/v1/bookmarks/",
                json={
                    "article_id": str(article.id),
                    "collection": collection,
                },
                headers=auth_headers,
            )
        
        # Get collections
        response = await client.get(
            "/api/v1/bookmarks/collections",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3  # Unique collections
        assert set(data["collections"]) == {"Archive", "Favorites", "Reading"}
    
    @pytest.mark.asyncio
    async def test_update_bookmark(
        self,
        client: AsyncClient,
        test_user: User,
        test_article: Article,
        auth_headers: dict,
    ):
        """Test updating a bookmark."""
        # Create bookmark
        create_response = await client.post(
            "/api/v1/bookmarks/",
            json={
                "article_id": str(test_article.id),
                "collection": "To Read",
                "notes": "Original notes",
            },
            headers=auth_headers,
        )
        bookmark_id = create_response.json()["id"]
        
        # Update bookmark
        response = await client.patch(
            f"/api/v1/bookmarks/{bookmark_id}",
            json={
                "collection": "Archive",
                "notes": "Updated notes",
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["collection"] == "Archive"
        assert data["notes"] == "Updated notes"
    
    @pytest.mark.asyncio
    async def test_delete_bookmark_by_id(
        self,
        client: AsyncClient,
        test_user: User,
        test_article: Article,
        auth_headers: dict,
    ):
        """Test deleting a bookmark by ID."""
        # Create bookmark
        create_response = await client.post(
            "/api/v1/bookmarks/",
            json={"article_id": str(test_article.id)},
            headers=auth_headers,
        )
        bookmark_id = create_response.json()["id"]
        
        # Delete bookmark
        response = await client.delete(
            f"/api/v1/bookmarks/{bookmark_id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 204
        
        # Verify deleted
        get_response = await client.get(
            f"/api/v1/bookmarks/{bookmark_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_bookmark_by_article(
        self,
        client: AsyncClient,
        test_user: User,
        test_article: Article,
        auth_headers: dict,
    ):
        """Test deleting a bookmark by article ID."""
        # Create bookmark
        await client.post(
            "/api/v1/bookmarks/",
            json={"article_id": str(test_article.id)},
            headers=auth_headers,
        )
        
        # Delete by article ID
        response = await client.delete(
            f"/api/v1/bookmarks/article/{test_article.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 204
        
        # Verify deleted
        check_response = await client.get(
            f"/api/v1/bookmarks/check/{test_article.id}",
            headers=auth_headers,
        )
        assert check_response.json()["is_bookmarked"] is False
    
    @pytest.mark.asyncio
    async def test_delete_bookmark_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test deleting non-existent bookmark."""
        fake_bookmark_id = str(uuid4())
        response = await client.delete(
            f"/api/v1/bookmarks/{fake_bookmark_id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 404
```

**Run tests**:
```bash
cd /Users/ej/Downloads/RSS-Feed/backend
pytest tests/integration/test_bookmarks.py -v
```

**Verification**:
- [ ] All tests pass
- [ ] Coverage > 90%
- [ ] Edge cases tested
- [ ] Authentication tested
- [ ] Authorization tested
- [ ] Error cases tested

---

### **Day 3: Reading History** (Complete Feature)

#### **Step 3.1: Database Schema & Migration** (1 hour)

**File**: `backend/alembic/versions/XXX_add_reading_history_table.py`

```python
"""add reading history table

Revision ID: xxx
Revises: previous_revision_id
Create Date: 2025-10-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'xxx'
down_revision = 'previous_revision_id'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create reading_history table
    op.create_table(
        'reading_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('article_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('articles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('viewed_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('duration_seconds', sa.Integer, nullable=True),
        sa.Column('scroll_percentage', sa.DECIMAL(5, 2), nullable=True),
    )
    
    # Create indexes
    op.create_index('idx_reading_history_user_id', 'reading_history', ['user_id'])
    op.create_index('idx_reading_history_article_id', 'reading_history', ['article_id'])
    op.create_index('idx_reading_history_viewed_at', 'reading_history', ['viewed_at'])
    op.create_index('idx_reading_history_user_viewed', 'reading_history', ['user_id', 'viewed_at'])

def downgrade() -> None:
    op.drop_index('idx_reading_history_user_viewed', table_name='reading_history')
    op.drop_index('idx_reading_history_viewed_at', table_name='reading_history')
    op.drop_index('idx_reading_history_article_id', table_name='reading_history')
    op.drop_index('idx_reading_history_user_id', table_name='reading_history')
    op.drop_table('reading_history')
```

**Apply migration**:
```bash
alembic upgrade head
```

---

#### **Step 3.2: Models, Repository, Service** (2 hours)

**File**: `backend/app/models/reading_history.py`

```python
"""Reading history model."""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, DECIMAL, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import sqlalchemy as sa

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.article import Article


class ReadingHistory(Base):
    """Reading history tracking."""
    
    __tablename__ = "reading_history"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=sa.text("gen_random_uuid()")
    )
    
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    article_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False
    )
    
    viewed_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        server_default=sa.func.now(),
        nullable=False
    )
    
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scroll_percentage: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="reading_history")
    article: Mapped["Article"] = relationship("Article", back_populates="reading_history")
    
    __table_args__ = (
        Index("idx_reading_history_user_id", "user_id"),
        Index("idx_reading_history_article_id", "article_id"),
        Index("idx_reading_history_viewed_at", "viewed_at"),
        Index("idx_reading_history_user_viewed", "user_id", "viewed_at"),
    )
    
    def __repr__(self) -> str:
        return f"<ReadingHistory user={self.user_id} article={self.article_id}>"
```

**File**: `backend/app/repositories/reading_history_repository.py`

```python
"""Repository for reading history."""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.reading_history import ReadingHistory


class ReadingHistoryRepository:
    """Repository for reading history operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def record_view(
        self,
        user_id: UUID,
        article_id: UUID,
        duration_seconds: Optional[int] = None,
        scroll_percentage: Optional[float] = None,
    ) -> ReadingHistory:
        """Record an article view."""
        history = ReadingHistory(
            user_id=user_id,
            article_id=article_id,
            duration_seconds=duration_seconds,
            scroll_percentage=scroll_percentage,
        )
        self.db.add(history)
        await self.db.commit()
        await self.db.refresh(history)
        return history
    
    async def get_user_history(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 25,
    ) -> tuple[list[ReadingHistory], int]:
        """Get user's reading history."""
        query = (
            select(ReadingHistory)
            .where(ReadingHistory.user_id == user_id)
            .options(selectinload(ReadingHistory.article))
            .order_by(desc(ReadingHistory.viewed_at))
        )
        
        if start_date:
            query = query.where(ReadingHistory.viewed_at >= start_date)
        if end_date:
            query = query.where(ReadingHistory.viewed_at <= end_date)
        
        # Get total count
        count_query = select(func.count()).select_from(ReadingHistory).where(ReadingHistory.user_id == user_id)
        if start_date:
            count_query = count_query.where(ReadingHistory.viewed_at >= start_date)
        if end_date:
            count_query = count_query.where(ReadingHistory.viewed_at <= end_date)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        history = result.scalars().all()
        
        return list(history), total
    
    async def get_recently_read(
        self,
        user_id: UUID,
        days: int = 7,
        limit: int = 10,
    ) -> list[ReadingHistory]:
        """Get recently read articles."""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.db.execute(
            select(ReadingHistory)
            .where(
                and_(
                    ReadingHistory.user_id == user_id,
                    ReadingHistory.viewed_at >= since_date
                )
            )
            .options(selectinload(ReadingHistory.article))
            .order_by(desc(ReadingHistory.viewed_at))
            .limit(limit)
        )
        
        return list(result.scalars().all())
    
    async def count_views_by_user(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Count total views for user."""
        query = (
            select(func.count())
            .select_from(ReadingHistory)
            .where(ReadingHistory.user_id == user_id)
        )
        
        if start_date:
            query = query.where(ReadingHistory.viewed_at >= start_date)
        if end_date:
            query = query.where(ReadingHistory.viewed_at <= end_date)
        
        result = await self.db.execute(query)
        return result.scalar_one()
    
    async def get_total_reading_time(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Get total reading time in seconds."""
        query = (
            select(func.sum(ReadingHistory.duration_seconds))
            .where(
                and_(
                    ReadingHistory.user_id == user_id,
                    ReadingHistory.duration_seconds.isnot(None)
                )
            )
        )
        
        if start_date:
            query = query.where(ReadingHistory.viewed_at >= start_date)
        if end_date:
            query = query.where(ReadingHistory.viewed_at <= end_date)
        
        result = await self.db.execute(query)
        total = result.scalar_one()
        return total or 0
    
    async def clear_history(
        self,
        user_id: UUID,
        before_date: Optional[datetime] = None,
    ) -> int:
        """Clear user's reading history."""
        query = delete(ReadingHistory).where(ReadingHistory.user_id == user_id)
        
        if before_date:
            query = query.where(ReadingHistory.viewed_at < before_date)
        
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount
```

**File**: `backend/app/services/reading_history_service.py`

```python
"""Service for reading history business logic."""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from app.repositories.reading_history_repository import ReadingHistoryRepository
from app.repositories.article_repository import ArticleRepository
from app.models.reading_history import ReadingHistory
from app.core.exceptions import NotFoundError


class ReadingHistoryService:
    """Service for reading history operations."""
    
    def __init__(
        self,
        history_repo: ReadingHistoryRepository,
        article_repo: ArticleRepository,
    ):
        self.history_repo = history_repo
        self.article_repo = article_repo
    
    async def record_view(
        self,
        user_id: UUID,
        article_id: UUID,
        duration_seconds: Optional[int] = None,
        scroll_percentage: Optional[float] = None,
    ) -> ReadingHistory:
        """Record an article view."""
        # Verify article exists
        article = await self.article_repo.get_by_id(article_id)
        if not article:
            raise NotFoundError(f"Article {article_id} not found")
        
        return await self.history_repo.record_view(
            user_id=user_id,
            article_id=article_id,
            duration_seconds=duration_seconds,
            scroll_percentage=scroll_percentage,
        )
    
    async def get_history(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[ReadingHistory], int]:
        """Get user's reading history."""
        skip = (page - 1) * page_size
        return await self.history_repo.get_user_history(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=page_size,
        )
    
    async def get_recently_read(
        self,
        user_id: UUID,
        days: int = 7,
        limit: int = 10,
    ) -> list[ReadingHistory]:
        """Get recently read articles."""
        return await self.history_repo.get_recently_read(
            user_id=user_id,
            days=days,
            limit=limit,
        )
    
    async def get_reading_stats(
        self,
        user_id: UUID,
        days: int = 30,
    ) -> dict:
        """Get reading statistics for user."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        total_views = await self.history_repo.count_views_by_user(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        total_reading_time = await self.history_repo.get_total_reading_time(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        return {
            "total_views": total_views,
            "total_reading_time_seconds": total_reading_time,
            "period_days": days,
            "average_reading_time_seconds": total_reading_time // total_views if total_views > 0 else 0,
        }
    
    async def clear_history(
        self,
        user_id: UUID,
        before_date: Optional[datetime] = None,
    ) -> int:
        """Clear user's reading history."""
        return await self.history_repo.clear_history(
            user_id=user_id,
            before_date=before_date,
        )
```

---

#### **Step 3.3: API Endpoints + Schemas + Tests** (2 hours)

**File**: `backend/app/schemas/reading_history.py`

```python
"""Schemas for reading history."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.article import ArticleResponse


class ReadingHistoryCreate(BaseModel):
    """Schema for recording article view."""
    article_id: UUID
    duration_seconds: Optional[int] = Field(None, ge=0)
    scroll_percentage: Optional[float] = Field(None, ge=0, le=100)


class ReadingHistoryResponse(BaseModel):
    """Schema for reading history response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    article_id: UUID
    viewed_at: datetime
    duration_seconds: Optional[int] = None
    scroll_percentage: Optional[float] = None
    article: Optional[ArticleResponse] = None


class ReadingHistoryListResponse(BaseModel):
    """Schema for paginated history list."""
    items: list[ReadingHistoryResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class ReadingStatsResponse(BaseModel):
    """Schema for reading statistics."""
    total_views: int
    total_reading_time_seconds: int
    period_days: int
    average_reading_time_seconds: int
```

**File**: `backend/app/api/v1/endpoints/reading_history.py`

```python
"""Reading history endpoints."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.repositories.reading_history_repository import ReadingHistoryRepository
from app.repositories.article_repository import ArticleRepository
from app.services.reading_history_service import ReadingHistoryService
from app.schemas.reading_history import (
    ReadingHistoryCreate,
    ReadingHistoryResponse,
    ReadingHistoryListResponse,
    ReadingStatsResponse,
)

router = APIRouter()


def get_reading_history_service(db: AsyncSession = Depends(get_db)) -> ReadingHistoryService:
    """Dependency for reading history service."""
    history_repo = ReadingHistoryRepository(db)
    article_repo = ArticleRepository(db)
    return ReadingHistoryService(history_repo, article_repo)


@router.post(
    "/",
    response_model=ReadingHistoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record article view",
)
async def record_view(
    view_data: ReadingHistoryCreate,
    current_user: User = Depends(get_current_user),
    service: ReadingHistoryService = Depends(get_reading_history_service),
) -> ReadingHistoryResponse:
    """Record an article view."""
    history = await service.record_view(
        user_id=current_user.id,
        article_id=view_data.article_id,
        duration_seconds=view_data.duration_seconds,
        scroll_percentage=view_data.scroll_percentage,
    )
    return ReadingHistoryResponse.model_validate(history)


@router.get(
    "/",
    response_model=ReadingHistoryListResponse,
    summary="Get reading history",
)
async def get_history(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: ReadingHistoryService = Depends(get_reading_history_service),
) -> ReadingHistoryListResponse:
    """Get user's reading history."""
    history, total = await service.get_history(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    
    return ReadingHistoryListResponse(
        items=[ReadingHistoryResponse.model_validate(h) for h in history],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get(
    "/recent",
    response_model=list[ReadingHistoryResponse],
    summary="Get recently read articles",
)
async def get_recently_read(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    service: ReadingHistoryService = Depends(get_reading_history_service),
) -> list[ReadingHistoryResponse]:
    """Get recently read articles."""
    history = await service.get_recently_read(
        user_id=current_user.id,
        days=days,
        limit=limit,
    )
    return [ReadingHistoryResponse.model_validate(h) for h in history]


@router.get(
    "/stats",
    response_model=ReadingStatsResponse,
    summary="Get reading statistics",
)
async def get_reading_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    service: ReadingHistoryService = Depends(get_reading_history_service),
) -> ReadingStatsResponse:
    """Get reading statistics."""
    stats = await service.get_reading_stats(
        user_id=current_user.id,
        days=days,
    )
    return ReadingStatsResponse(**stats)


@router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear reading history",
)
async def clear_history(
    before_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    service: ReadingHistoryService = Depends(get_reading_history_service),
) -> None:
    """Clear reading history."""
    await service.clear_history(
        user_id=current_user.id,
        before_date=before_date,
    )
```

Register router in `backend/app/api/v1/api.py`:
```python
from app.api.v1.endpoints import reading_history

api_router.include_router(
    reading_history.router,
    prefix="/history",
    tags=["reading-history"]
)
```

---

**Continue in next message with Day 4-6...**

Would you like me to continue with the remaining days (User Preferences and User Stats), or would you prefer to start implementing the bookmarks feature first?