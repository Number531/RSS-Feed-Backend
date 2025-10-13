# Next Phase Implementation Plan

**Project:** RSS News Aggregator Backend  
**Phase:** Service Layer, DI, API Endpoints & Testing  
**Date:** October 10, 2025  
**Status:** 📋 READY TO IMPLEMENT

---

## 🎯 **Overview**

This plan covers the implementation of:
1. **Service Layer** - Business logic and orchestration
2. **Dependency Injection** - Factory functions for repositories and services
3. **API Endpoints** - Votes and Comments endpoints
4. **Testing Suite** - Unit and integration tests

**Estimated Time:** 8-10 hours  
**Complexity:** Medium  
**Priority:** High

---

## 📊 **Phase Breakdown**

| Phase | Components | Time | Priority |
|-------|-----------|------|----------|
| 1. Service Layer | 3 services + base | 3 hours | HIGH |
| 2. Dependency Injection | DI setup + factories | 1 hour | HIGH |
| 3. API Endpoints | Votes + Comments | 2 hours | HIGH |
| 4. Init Files | Package exports | 30 min | MEDIUM |
| 5. Testing | Unit + Integration | 3 hours | MEDIUM |

---

# PHASE 1: SERVICE LAYER IMPLEMENTATION

**Goal:** Create business logic layer that orchestrates repository operations

## 🏗️ **Architecture Overview**

```
Service Layer Architecture:
┌─────────────────────────────────────────────────┐
│                  API Layer                       │
│          (FastAPI Routers/Endpoints)            │
└────────────────┬────────────────────────────────┘
                 │ Depends on
┌────────────────▼────────────────────────────────┐
│              Service Layer                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Article  │  │   Vote   │  │ Comment  │     │
│  │ Service  │  │ Service  │  │ Service  │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
└───────┼─────────────┼─────────────┼────────────┘
        │ Uses        │ Uses        │ Uses
┌───────▼─────────────▼─────────────▼────────────┐
│            Repository Layer                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Article  │  │   Vote   │  │ Comment  │     │
│  │   Repo   │  │   Repo   │  │   Repo   │     │
│  └──────────┘  └──────────┘  └──────────┘     │
└─────────────────────────────────────────────────┘
```

## 📋 **1.1: Base Service Class**

**Purpose:** Abstract base class with common functionality

**File:** `backend/app/services/base_service.py`

**Key Features:**
- Generic database session handling
- Common error handling patterns
- Logging integration
- Transaction management helpers

**Implementation:**

```python
"""Base service class for common functionality."""
from typing import Generic, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger

T = TypeVar('T')


class BaseService(Generic[T]):
    """Base service class with common functionality."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize base service.
        
        Args:
            db: Async database session
        """
        self.db = db
        self.logger = logger
    
    async def _handle_error(self, error: Exception, context: str) -> None:
        """
        Handle service errors with logging.
        
        Args:
            error: The exception that occurred
            context: Context description for logging
        """
        self.logger.error(f"Service error in {context}: {str(error)}", exc_info=True)
        raise
    
    def _validate_pagination(self, page: int, page_size: int) -> tuple[int, int]:
        """
        Validate and normalize pagination parameters.
        
        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            Validated (page, page_size) tuple
        """
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        return page, page_size
```

**Lines of Code:** ~40  
**Complexity:** Low  
**Testing:** Basic unit tests

---

## 📋 **1.2: Article Service**

**Purpose:** Business logic for article operations

**File:** `backend/app/services/article_service.py`

**Responsibilities:**
- Orchestrate article feed retrieval
- Handle search operations
- Manage article details with user context
- Calculate pagination metadata

**Key Methods:**

```python
class ArticleService(BaseService):
    """Service for article business logic."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.article_repo = ArticleRepository(db)
    
    async def get_feed(
        self,
        params: ArticleFeed,
        current_user: Optional[User] = None
    ) -> ArticleList:
        """
        Get paginated article feed.
        
        Business Logic:
        1. Validate pagination parameters
        2. Get user_id if authenticated
        3. Fetch articles from repository
        4. Calculate total pages
        5. Return structured response
        """
        # Implementation
    
    async def get_article_detail(
        self,
        article_id: UUID,
        current_user: Optional[User] = None
    ) -> ArticleResponse:
        """
        Get article by ID with user context.
        
        Business Logic:
        1. Fetch article from repository
        2. Raise 404 if not found
        3. Load user vote if authenticated
        4. Return article response
        """
        # Implementation
    
    async def search(
        self,
        query: str,
        page: int,
        page_size: int
    ) -> ArticleList:
        """
        Full-text search for articles.
        
        Business Logic:
        1. Sanitize search query
        2. Validate pagination
        3. Execute search via repository
        4. Return paginated results
        """
        # Implementation
```

**Full Implementation:**

```python
"""Article service for business logic."""
from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.article_repository import ArticleRepository
from app.schemas.article import ArticleFeed, ArticleList, ArticleResponse
from app.services.base_service import BaseService


class ArticleService(BaseService):
    """Service for article business logic."""
    
    def __init__(self, db: AsyncSession):
        """Initialize article service."""
        super().__init__(db)
        self.article_repo = ArticleRepository(db)
    
    async def get_feed(
        self,
        params: ArticleFeed,
        current_user: Optional[User] = None
    ) -> ArticleList:
        """
        Get paginated article feed.
        
        Args:
            params: Feed query parameters
            current_user: Optional authenticated user
            
        Returns:
            Paginated article list with metadata
        """
        try:
            # Validate pagination
            page, page_size = self._validate_pagination(params.page, params.page_size)
            
            # Get user_id if authenticated
            user_id = current_user.id if current_user else None
            
            # Fetch articles
            articles, total = await self.article_repo.get_articles_feed(
                category=params.category,
                page=page,
                page_size=page_size,
                sort_by=params.sort_by,
                time_range=params.time_range,
                user_id=user_id
            )
            
            # Calculate total pages
            total_pages = (total + page_size - 1) // page_size if total > 0 else 0
            
            return ArticleList(
                items=articles,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
        except Exception as e:
            await self._handle_error(e, "get_feed")
    
    async def get_article_detail(
        self,
        article_id: UUID,
        current_user: Optional[User] = None
    ) -> ArticleResponse:
        """
        Get article by ID with user context.
        
        Args:
            article_id: Article UUID
            current_user: Optional authenticated user
            
        Returns:
            Article details
            
        Raises:
            HTTPException: 404 if article not found
        """
        try:
            user_id = current_user.id if current_user else None
            
            article = await self.article_repo.get_article_by_id(
                article_id=article_id,
                user_id=user_id
            )
            
            if not article:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Article with id {article_id} not found"
                )
            
            return ArticleResponse.model_validate(article)
        except HTTPException:
            raise
        except Exception as e:
            await self._handle_error(e, "get_article_detail")
    
    async def search(
        self,
        query: str,
        page: int,
        page_size: int
    ) -> ArticleList:
        """
        Full-text search for articles.
        
        Args:
            query: Search query string
            page: Page number
            page_size: Items per page
            
        Returns:
            Paginated search results
        """
        try:
            # Validate pagination
            page, page_size = self._validate_pagination(page, page_size)
            
            # Sanitize query (basic)
            query = query.strip()
            
            if not query:
                return ArticleList(
                    items=[],
                    total=0,
                    page=page,
                    page_size=page_size,
                    total_pages=0
                )
            
            # Execute search
            articles, total = await self.article_repo.search_articles(
                query=query,
                page=page,
                page_size=page_size
            )
            
            # Calculate total pages
            total_pages = (total + page_size - 1) // page_size if total > 0 else 0
            
            return ArticleList(
                items=articles,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
        except Exception as e:
            await self._handle_error(e, "search")
```

**Lines of Code:** ~150  
**Complexity:** Medium  
**Testing:** Unit + Integration tests

---

## 📋 **1.3: Vote Service**

**Purpose:** Business logic for voting operations

**File:** `backend/app/services/vote_service.py`

**Responsibilities:**
- Validate vote values (-1 or +1)
- Handle vote creation/update/deletion
- Enforce one-vote-per-user constraint
- Manage article vote metrics

**Key Methods:**

```python
class VoteService(BaseService):
    """Service for vote business logic."""
    
    async def cast_vote(
        self,
        user: User,
        article_id: UUID,
        vote_value: int
    ) -> VoteResponse:
        """
        Cast or update a vote.
        
        Business Logic:
        1. Validate vote_value (-1 or +1)
        2. Check if user already voted
        3. If exists and same value: no-op (idempotent)
        4. If exists and different: update vote
        5. If not exists: create new vote
        6. Return vote response
        """
    
    async def remove_vote(
        self,
        user: User,
        article_id: UUID
    ) -> dict:
        """
        Remove user's vote from article.
        
        Business Logic:
        1. Find user's existing vote
        2. If not found: return success (idempotent)
        3. Delete vote
        4. Return success message
        """
    
    async def get_user_vote(
        self,
        user: User,
        article_id: UUID
    ) -> Optional[int]:
        """Get user's vote on an article."""
```

**Full Implementation:**

```python
"""Vote service for business logic."""
from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.vote_repository import VoteRepository
from app.schemas.vote import VoteResponse, VoteCreate
from app.services.base_service import BaseService


class VoteService(BaseService):
    """Service for vote business logic."""
    
    def __init__(self, db: AsyncSession):
        """Initialize vote service."""
        super().__init__(db)
        self.vote_repo = VoteRepository(db)
    
    def _validate_vote_value(self, vote_value: int) -> None:
        """
        Validate vote value.
        
        Args:
            vote_value: Vote value to validate
            
        Raises:
            HTTPException: If vote value is invalid
        """
        if vote_value not in (-1, 1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vote value must be -1 (downvote) or 1 (upvote)"
            )
    
    async def cast_vote(
        self,
        user: User,
        article_id: UUID,
        vote_value: int
    ) -> VoteResponse:
        """
        Cast or update a vote.
        
        Args:
            user: Authenticated user
            article_id: Article to vote on
            vote_value: Vote value (-1 or 1)
            
        Returns:
            Vote response
            
        Raises:
            HTTPException: If vote value is invalid
        """
        try:
            # Validate vote value
            self._validate_vote_value(vote_value)
            
            # Check for existing vote
            existing_vote = await self.vote_repo.get_user_vote(
                user_id=user.id,
                article_id=article_id
            )
            
            if existing_vote:
                # If same vote value, idempotent (no-op)
                if existing_vote.vote_value == vote_value:
                    self.logger.info(
                        f"User {user.id} already voted {vote_value} on article {article_id}"
                    )
                    return VoteResponse.model_validate(existing_vote)
                
                # Different vote value, update
                self.logger.info(
                    f"Updating vote for user {user.id} on article {article_id}: "
                    f"{existing_vote.vote_value} -> {vote_value}"
                )
                updated_vote = await self.vote_repo.update_vote(
                    vote=existing_vote,
                    new_value=vote_value
                )
                return VoteResponse.model_validate(updated_vote)
            
            # No existing vote, create new
            self.logger.info(
                f"Creating new vote for user {user.id} on article {article_id}: {vote_value}"
            )
            new_vote = await self.vote_repo.create_vote(
                user_id=user.id,
                article_id=article_id,
                vote_value=vote_value
            )
            return VoteResponse.model_validate(new_vote)
            
        except HTTPException:
            raise
        except Exception as e:
            await self._handle_error(e, "cast_vote")
    
    async def remove_vote(
        self,
        user: User,
        article_id: UUID
    ) -> dict:
        """
        Remove user's vote from article.
        
        Args:
            user: Authenticated user
            article_id: Article to remove vote from
            
        Returns:
            Success message
        """
        try:
            existing_vote = await self.vote_repo.get_user_vote(
                user_id=user.id,
                article_id=article_id
            )
            
            if not existing_vote:
                # Idempotent - return success even if no vote exists
                self.logger.info(
                    f"No vote found for user {user.id} on article {article_id}"
                )
                return {"message": "Vote removed successfully"}
            
            # Delete vote
            self.logger.info(
                f"Removing vote for user {user.id} on article {article_id}"
            )
            await self.vote_repo.delete_vote(existing_vote)
            
            return {"message": "Vote removed successfully"}
            
        except Exception as e:
            await self._handle_error(e, "remove_vote")
    
    async def get_user_vote(
        self,
        user: User,
        article_id: UUID
    ) -> Optional[int]:
        """
        Get user's vote value on an article.
        
        Args:
            user: Authenticated user
            article_id: Article ID
            
        Returns:
            Vote value (-1, 1) or None if no vote
        """
        try:
            vote = await self.vote_repo.get_user_vote(
                user_id=user.id,
                article_id=article_id
            )
            return vote.vote_value if vote else None
            
        except Exception as e:
            await self._handle_error(e, "get_user_vote")
```

**Lines of Code:** ~180  
**Complexity:** Medium  
**Testing:** Unit + Integration tests

---

## 📋 **1.4: Comment Service**

**Purpose:** Business logic for comment operations

**File:** `backend/app/services/comment_service.py`

**Responsibilities:**
- Create comments with validation
- Build threaded comment trees
- Handle comment updates and soft deletes
- Enforce ownership for updates/deletes

**Key Methods:**

```python
class CommentService(BaseService):
    """Service for comment business logic."""
    
    async def create_comment(
        self,
        user: User,
        data: CommentCreate
    ) -> CommentResponse:
        """
        Create a new comment.
        
        Business Logic:
        1. Validate article exists (optional)
        2. Validate parent comment exists (if replying)
        3. Create comment via repository
        4. Return comment response
        """
    
    async def get_article_comments(
        self,
        article_id: UUID,
        page: int,
        page_size: int,
        current_user: Optional[User] = None
    ) -> CommentList:
        """Get paginated top-level comments for an article."""
    
    async def get_comment_tree(
        self,
        article_id: UUID,
        current_user: Optional[User] = None
    ) -> List[CommentTree]:
        """
        Get threaded comment tree.
        
        Business Logic:
        1. Fetch all comments for article
        2. Build nested tree structure recursively
        3. Include user votes if authenticated
        4. Return comment tree
        """
    
    async def update_comment(
        self,
        user: User,
        comment_id: UUID,
        data: CommentUpdate
    ) -> CommentResponse:
        """
        Update comment content.
        
        Business Logic:
        1. Fetch comment
        2. Verify ownership
        3. Update content
        4. Mark as edited
        5. Return updated comment
        """
    
    async def delete_comment(
        self,
        user: User,
        comment_id: UUID
    ) -> dict:
        """
        Soft delete a comment.
        
        Business Logic:
        1. Fetch comment
        2. Verify ownership
        3. Soft delete (mark as deleted)
        4. Return success
        """
```

**Full Implementation:**

```python
"""Comment service for business logic."""
from typing import Optional, List
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.comment_repository import CommentRepository
from app.schemas.comment import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentTree,
    CommentList
)
from app.services.base_service import BaseService


class CommentService(BaseService):
    """Service for comment business logic."""
    
    def __init__(self, db: AsyncSession):
        """Initialize comment service."""
        super().__init__(db)
        self.comment_repo = CommentRepository(db)
    
    async def create_comment(
        self,
        user: User,
        data: CommentCreate
    ) -> CommentResponse:
        """
        Create a new comment.
        
        Args:
            user: Authenticated user
            data: Comment creation data
            
        Returns:
            Created comment
        """
        try:
            # Optional: Validate article exists (skip for now, FK handles it)
            
            # Optional: Validate parent comment exists if replying
            if data.parent_comment_id:
                parent = await self.comment_repo.get_comment_by_id(
                    data.parent_comment_id
                )
                if not parent:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Parent comment {data.parent_comment_id} not found"
                    )
                if parent.is_deleted:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot reply to deleted comment"
                    )
            
            # Create comment
            self.logger.info(
                f"Creating comment by user {user.id} on article {data.article_id}"
            )
            comment = await self.comment_repo.create_comment(
                user_id=user.id,
                article_id=data.article_id,
                content=data.content,
                parent_comment_id=data.parent_comment_id
            )
            
            return CommentResponse.model_validate(comment)
            
        except HTTPException:
            raise
        except Exception as e:
            await self._handle_error(e, "create_comment")
    
    async def get_article_comments(
        self,
        article_id: UUID,
        page: int,
        page_size: int,
        current_user: Optional[User] = None
    ) -> CommentList:
        """
        Get paginated top-level comments.
        
        Args:
            article_id: Article ID
            page: Page number
            page_size: Items per page
            current_user: Optional authenticated user
            
        Returns:
            Paginated comment list
        """
        try:
            # Validate pagination
            page, page_size = self._validate_pagination(page, page_size)
            
            # Fetch comments
            comments = await self.comment_repo.get_article_comments(
                article_id=article_id,
                page=page,
                page_size=page_size
            )
            
            # For simplicity, don't count total (would need separate query)
            # Frontend can detect end of pagination when items < page_size
            
            return CommentList(
                items=comments,
                total=len(comments),  # Simplified
                page=page,
                page_size=page_size
            )
            
        except Exception as e:
            await self._handle_error(e, "get_article_comments")
    
    async def get_comment_tree(
        self,
        article_id: UUID,
        current_user: Optional[User] = None
    ) -> List[CommentTree]:
        """
        Get threaded comment tree for an article.
        
        Args:
            article_id: Article ID
            current_user: Optional authenticated user
            
        Returns:
            List of top-level comments with nested replies
        """
        try:
            # Fetch top-level comments (no pagination for tree view)
            top_comments = await self.comment_repo.get_article_comments(
                article_id=article_id,
                page=1,
                page_size=1000  # Large limit for tree view
            )
            
            # Build tree recursively
            tree = []
            for comment in top_comments:
                tree_node = await self._build_comment_tree(comment)
                tree.append(tree_node)
            
            return tree
            
        except Exception as e:
            await self._handle_error(e, "get_comment_tree")
    
    async def _build_comment_tree(self, comment) -> CommentTree:
        """
        Recursively build comment tree.
        
        Args:
            comment: Comment model instance
            
        Returns:
            CommentTree with nested replies
        """
        # Get replies
        replies = await self.comment_repo.get_comment_replies(comment.id)
        
        # Recursively build reply trees
        reply_trees = []
        for reply in replies:
            reply_tree = await self._build_comment_tree(reply)
            reply_trees.append(reply_tree)
        
        # Create tree node
        tree_node = CommentTree.model_validate(comment)
        tree_node.replies = reply_trees
        
        return tree_node
    
    async def update_comment(
        self,
        user: User,
        comment_id: UUID,
        data: CommentUpdate
    ) -> CommentResponse:
        """
        Update comment content.
        
        Args:
            user: Authenticated user
            comment_id: Comment ID to update
            data: Update data
            
        Returns:
            Updated comment
            
        Raises:
            HTTPException: If comment not found or user not owner
        """
        try:
            # Fetch comment
            comment = await self.comment_repo.get_comment_by_id(comment_id)
            if not comment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Comment {comment_id} not found"
                )
            
            # Verify ownership
            if comment.user_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only edit your own comments"
                )
            
            # Check if deleted
            if comment.is_deleted:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot edit deleted comment"
                )
            
            # Update comment
            self.logger.info(f"Updating comment {comment_id} by user {user.id}")
            updated_comment = await self.comment_repo.update_comment(
                comment=comment,
                content=data.content
            )
            
            return CommentResponse.model_validate(updated_comment)
            
        except HTTPException:
            raise
        except Exception as e:
            await self._handle_error(e, "update_comment")
    
    async def delete_comment(
        self,
        user: User,
        comment_id: UUID
    ) -> dict:
        """
        Soft delete a comment.
        
        Args:
            user: Authenticated user
            comment_id: Comment ID to delete
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If comment not found or user not owner
        """
        try:
            # Fetch comment
            comment = await self.comment_repo.get_comment_by_id(comment_id)
            if not comment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Comment {comment_id} not found"
                )
            
            # Verify ownership
            if comment.user_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only delete your own comments"
                )
            
            # Check if already deleted (idempotent)
            if comment.is_deleted:
                self.logger.info(f"Comment {comment_id} already deleted")
                return {"message": "Comment deleted successfully"}
            
            # Soft delete
            self.logger.info(f"Deleting comment {comment_id} by user {user.id}")
            await self.comment_repo.soft_delete_comment(comment)
            
            return {"message": "Comment deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            await self._handle_error(e, "delete_comment")
```

**Lines of Code:** ~300  
**Complexity:** High (recursive tree building)  
**Testing:** Unit + Integration tests

---

## 📋 **Service Layer Summary**

| File | Lines | Complexity | Key Features |
|------|-------|------------|--------------|
| `base_service.py` | 40 | Low | Error handling, pagination validation |
| `article_service.py` | 150 | Medium | Feed, search, detail retrieval |
| `vote_service.py` | 180 | Medium | Vote CRUD, validation, idempotency |
| `comment_service.py` | 300 | High | Comment CRUD, tree building, ownership |

**Total:** ~670 lines of service code

---

# PHASE 2: DEPENDENCY INJECTION SETUP

**Goal:** Configure FastAPI dependency injection for repositories and services

## 🏗️ **2.1: Dependencies Module**

**File:** `backend/app/api/dependencies.py`

**Current State:** May have basic auth dependencies

**Updates Needed:**
1. Database session factory (should exist)
2. Repository factories
3. Service factories

**Implementation:**

```python
"""Dependency injection for FastAPI."""
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user, get_current_user_optional
from app.models.user import User

# Repository imports
from app.repositories.article_repository import ArticleRepository
from app.repositories.vote_repository import VoteRepository
from app.repositories.comment_repository import CommentRepository

# Service imports
from app.services.article_service import ArticleService
from app.services.vote_service import VoteService
from app.services.comment_service import CommentService


# ==================== Repository Factories ====================

async def get_article_repository(
    db: AsyncSession = Depends(get_db)
) -> ArticleRepository:
    """Get article repository instance."""
    return ArticleRepository(db)


async def get_vote_repository(
    db: AsyncSession = Depends(get_db)
) -> VoteRepository:
    """Get vote repository instance."""
    return VoteRepository(db)


async def get_comment_repository(
    db: AsyncSession = Depends(get_db)
) -> CommentRepository:
    """Get comment repository instance."""
    return CommentRepository(db)


# ==================== Service Factories ====================

async def get_article_service(
    db: AsyncSession = Depends(get_db)
) -> ArticleService:
    """Get article service instance."""
    return ArticleService(db)


async def get_vote_service(
    db: AsyncSession = Depends(get_db)
) -> VoteService:
    """Get vote service instance."""
    return VoteService(db)


async def get_comment_service(
    db: AsyncSession = Depends(get_db)
) -> CommentService:
    """Get comment service instance."""
    return CommentService(db)


# ==================== Auth Dependencies (existing) ====================

# These should already exist from Phase 3:
# - get_current_user: Returns authenticated user or raises 401
# - get_current_user_optional: Returns authenticated user or None
```

**Lines of Code:** ~60  
**Complexity:** Low  
**Testing:** Integration tests only

---

# PHASE 3: API ENDPOINTS IMPLEMENTATION

## 📋 **3.1: Vote Schemas**

**File:** `backend/app/schemas/vote.py`

```python
"""Vote schemas for API validation."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class VoteCreate(BaseModel):
    """Schema for creating/updating a vote."""
    article_id: UUID
    vote_value: int = Field(..., ge=-1, le=1, description="Vote value: -1 (downvote) or 1 (upvote)")


class VoteResponse(BaseModel):
    """Schema for vote response."""
    id: UUID
    user_id: UUID
    article_id: UUID
    vote_value: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
```

---

## 📋 **3.2: Votes API Endpoints**

**File:** `backend/app/api/v1/endpoints/votes.py`

**Endpoints:**
1. `POST /votes` - Cast or update vote
2. `DELETE /votes/{article_id}` - Remove vote
3. `GET /votes/{article_id}` - Get user's vote (optional endpoint)

**Implementation:**

```python
"""Votes API endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_vote_service
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.vote import VoteCreate, VoteResponse
from app.services.vote_service import VoteService

router = APIRouter()


@router.post("/", response_model=VoteResponse, status_code=status.HTTP_200_OK)
async def cast_vote(
    vote_data: VoteCreate,
    vote_service: VoteService = Depends(get_vote_service),
    current_user: User = Depends(get_current_user)
):
    """
    Cast or update a vote on an article.
    
    - **article_id**: UUID of the article to vote on
    - **vote_value**: -1 for downvote, 1 for upvote
    
    **Behavior:**
    - If user hasn't voted: Creates new vote
    - If user already voted same value: No-op (idempotent)
    - If user voted different value: Updates vote
    
    **Authentication:** Required
    """
    return await vote_service.cast_vote(
        user=current_user,
        article_id=vote_data.article_id,
        vote_value=vote_data.vote_value
    )


@router.delete("/{article_id}", status_code=status.HTTP_200_OK)
async def remove_vote(
    article_id: UUID,
    vote_service: VoteService = Depends(get_vote_service),
    current_user: User = Depends(get_current_user)
):
    """
    Remove vote from an article.
    
    - **article_id**: UUID of the article
    
    **Behavior:**
    - Removes user's vote if exists
    - Idempotent: Returns success even if no vote exists
    
    **Authentication:** Required
    """
    return await vote_service.remove_vote(
        user=current_user,
        article_id=article_id
    )


@router.get("/{article_id}", response_model=dict)
async def get_user_vote(
    article_id: UUID,
    vote_service: VoteService = Depends(get_vote_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's current vote on an article.
    
    - **article_id**: UUID of the article
    
    **Returns:**
    - `{"vote_value": -1}` for downvote
    - `{"vote_value": 1}` for upvote
    - `{"vote_value": null}` for no vote
    
    **Authentication:** Required
    """
    vote_value = await vote_service.get_user_vote(
        user=current_user,
        article_id=article_id
    )
    return {"vote_value": vote_value}
```

**Lines of Code:** ~80  
**Endpoints:** 3  
**Testing:** Integration tests

---

## 📋 **3.3: Comments API Endpoints**

**File:** `backend/app/api/v1/endpoints/comments.py`

**Endpoints:**
1. `POST /comments` - Create comment
2. `GET /comments/article/{article_id}` - Get comments (paginated or tree)
3. `PATCH /comments/{comment_id}` - Update comment
4. `DELETE /comments/{comment_id}` - Delete comment

**Implementation:**

```python
"""Comments API endpoints."""
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_comment_service
from app.core.security import get_current_user, get_current_user_optional
from app.models.user import User
from app.schemas.comment import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentTree,
    CommentList
)
from app.services.comment_service import CommentService

router = APIRouter()


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreate,
    comment_service: CommentService = Depends(get_comment_service),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new comment.
    
    - **article_id**: UUID of the article
    - **content**: Comment text (1-10000 characters)
    - **parent_comment_id**: Optional UUID of parent comment for replies
    
    **Authentication:** Required
    """
    return await comment_service.create_comment(
        user=current_user,
        data=comment_data
    )


@router.get("/article/{article_id}", response_model=CommentList)
async def get_article_comments(
    article_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    comment_service: CommentService = Depends(get_comment_service),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get paginated top-level comments for an article.
    
    - **article_id**: UUID of the article
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 50, max: 100)
    
    **Returns:** Top-level comments only (no nested replies)
    Use `/comments/article/{article_id}/tree` for threaded view
    
    **Authentication:** Optional
    """
    return await comment_service.get_article_comments(
        article_id=article_id,
        page=page,
        page_size=page_size,
        current_user=current_user
    )


@router.get("/article/{article_id}/tree", response_model=List[CommentTree])
async def get_comment_tree(
    article_id: UUID,
    comment_service: CommentService = Depends(get_comment_service),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get threaded comment tree for an article.
    
    - **article_id**: UUID of the article
    
    **Returns:** Nested comment tree with all replies
    
    **Note:** This endpoint loads all comments (no pagination)
    Use for articles with moderate comment counts (< 1000)
    
    **Authentication:** Optional
    """
    return await comment_service.get_comment_tree(
        article_id=article_id,
        current_user=current_user
    )


@router.patch("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: UUID,
    comment_data: CommentUpdate,
    comment_service: CommentService = Depends(get_comment_service),
    current_user: User = Depends(get_current_user)
):
    """
    Update comment content.
    
    - **comment_id**: UUID of the comment to update
    - **content**: New comment text
    
    **Authorization:** User must be comment owner
    **Authentication:** Required
    """
    return await comment_service.update_comment(
        user=current_user,
        comment_id=comment_id,
        data=comment_data
    )


@router.delete("/{comment_id}", status_code=status.HTTP_200_OK)
async def delete_comment(
    comment_id: UUID,
    comment_service: CommentService = Depends(get_comment_service),
    current_user: User = Depends(get_current_user)
):
    """
    Soft delete a comment.
    
    - **comment_id**: UUID of the comment to delete
    
    **Behavior:**
    - Comment is soft-deleted (marked as deleted)
    - Content replaced with "[deleted]"
    - Replies remain visible
    
    **Authorization:** User must be comment owner
    **Authentication:** Required
    """
    return await comment_service.delete_comment(
        user=current_user,
        comment_id=comment_id
    )
```

**Lines of Code:** ~150  
**Endpoints:** 5  
**Testing:** Integration tests

---

## 📋 **3.4: Router Registration**

**File:** `backend/app/api/v1/router.py`

**Update to include new routers:**

```python
"""API v1 router aggregation."""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, articles, votes, comments

api_router = APIRouter()

# Register all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(articles.router, prefix="/articles", tags=["articles"])
api_router.include_router(votes.router, prefix="/votes", tags=["votes"])
api_router.include_router(comments.router, prefix="/comments", tags=["comments"])
```

---

# PHASE 4: INIT FILES & PACKAGE EXPORTS

## 📋 **4.1: Repository Init**

**File:** `backend/app/repositories/__init__.py`

```python
"""Repository layer exports."""
from app.repositories.article_repository import ArticleRepository
from app.repositories.vote_repository import VoteRepository
from app.repositories.comment_repository import CommentRepository

__all__ = [
    "ArticleRepository",
    "VoteRepository",
    "CommentRepository",
]
```

---

## 📋 **4.2: Service Init**

**File:** `backend/app/services/__init__.py`

```python
"""Service layer exports."""
from app.services.base_service import BaseService
from app.services.article_service import ArticleService
from app.services.vote_service import VoteService
from app.services.comment_service import CommentService

__all__ = [
    "BaseService",
    "ArticleService",
    "VoteService",
    "CommentService",
]
```

---

# PHASE 5: TESTING SUITE

## 🧪 **Testing Strategy**

### **Test Pyramid:**
```
        ┌─────────────┐
        │  E2E Tests  │  (Few)
        │   (Manual)  │
        └─────────────┘
       ┌───────────────┐
       │ Integration   │  (Some)
       │     Tests     │
       └───────────────┘
      ┌─────────────────┐
      │   Unit Tests    │  (Many)
      └─────────────────┘
```

### **Coverage Goals:**
- **Unit Tests:** 80%+ coverage
- **Integration Tests:** All endpoints
- **E2E Tests:** Critical user flows (manual for now)

---

## 📋 **5.1: Test Configuration**

**File:** `backend/tests/conftest.py`

```python
"""Pytest configuration and fixtures."""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.session import get_db, Base
from app.core.config import settings

# Test database URL (use separate test DB)
TEST_DATABASE_URL = settings.DATABASE_URL.replace("/rss_feed", "/rss_feed_test")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session):
    """Create test user."""
    from app.models.user import User
    
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password_here"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture
async def auth_headers(test_user):
    """Create authentication headers."""
    from app.core.security import create_access_token
    
    token = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {token}"}
```

---

## 📋 **5.2: Service Unit Tests**

**File:** `backend/tests/unit/test_vote_service.py`

```python
"""Unit tests for vote service."""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.services.vote_service import VoteService
from app.models.vote import Vote


@pytest.fixture
def mock_vote_repo():
    """Create mock vote repository."""
    return AsyncMock()


@pytest.fixture
def vote_service(db_session, mock_vote_repo):
    """Create vote service with mocked repository."""
    service = VoteService(db_session)
    service.vote_repo = mock_vote_repo
    return service


@pytest.mark.asyncio
async def test_cast_vote_creates_new_vote(vote_service, mock_vote_repo, test_user):
    """Test casting a vote creates new vote when none exists."""
    article_id = uuid4()
    
    # Mock repository responses
    mock_vote_repo.get_user_vote.return_value = None  # No existing vote
    
    new_vote = Vote(
        id=uuid4(),
        user_id=test_user.id,
        article_id=article_id,
        vote_value=1
    )
    mock_vote_repo.create_vote.return_value = new_vote
    
    # Execute
    result = await vote_service.cast_vote(
        user=test_user,
        article_id=article_id,
        vote_value=1
    )
    
    # Assertions
    mock_vote_repo.get_user_vote.assert_called_once()
    mock_vote_repo.create_vote.assert_called_once()
    assert result.vote_value == 1


@pytest.mark.asyncio
async def test_cast_vote_updates_existing_different_value(
    vote_service, mock_vote_repo, test_user
):
    """Test casting a vote updates when different value exists."""
    article_id = uuid4()
    
    # Mock existing vote
    existing_vote = Vote(
        id=uuid4(),
        user_id=test_user.id,
        article_id=article_id,
        vote_value=-1  # Existing downvote
    )
    mock_vote_repo.get_user_vote.return_value = existing_vote
    
    updated_vote = Vote(**existing_vote.__dict__)
    updated_vote.vote_value = 1  # Updated to upvote
    mock_vote_repo.update_vote.return_value = updated_vote
    
    # Execute
    result = await vote_service.cast_vote(
        user=test_user,
        article_id=article_id,
        vote_value=1
    )
    
    # Assertions
    mock_vote_repo.update_vote.assert_called_once()
    assert result.vote_value == 1


@pytest.mark.asyncio
async def test_cast_vote_idempotent_same_value(
    vote_service, mock_vote_repo, test_user
):
    """Test casting same vote is idempotent."""
    article_id = uuid4()
    
    # Mock existing vote with same value
    existing_vote = Vote(
        id=uuid4(),
        user_id=test_user.id,
        article_id=article_id,
        vote_value=1
    )
    mock_vote_repo.get_user_vote.return_value = existing_vote
    
    # Execute
    result = await vote_service.cast_vote(
        user=test_user,
        article_id=article_id,
        vote_value=1
    )
    
    # Assertions
    mock_vote_repo.update_vote.assert_not_called()
    mock_vote_repo.create_vote.assert_not_called()
    assert result.vote_value == 1


@pytest.mark.asyncio
async def test_cast_vote_validates_value(vote_service, test_user):
    """Test vote value validation."""
    from fastapi import HTTPException
    
    article_id = uuid4()
    
    # Test invalid value
    with pytest.raises(HTTPException) as exc_info:
        await vote_service.cast_vote(
            user=test_user,
            article_id=article_id,
            vote_value=2  # Invalid
        )
    
    assert exc_info.value.status_code == 400
    assert "must be -1" in str(exc_info.value.detail)
```

---

## 📋 **5.3: API Integration Tests**

**File:** `backend/tests/integration/test_votes_api.py`

```python
"""Integration tests for votes API."""
import pytest
from uuid import uuid4


@pytest.mark.asyncio
async def test_cast_vote_unauthorized(client):
    """Test casting vote without authentication returns 401."""
    response = await client.post(
        "/api/v1/votes/",
        json={
            "article_id": str(uuid4()),
            "vote_value": 1
        }
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_cast_vote_success(client, auth_headers, test_article):
    """Test casting vote successfully."""
    response = await client.post(
        "/api/v1/votes/",
        headers=auth_headers,
        json={
            "article_id": str(test_article.id),
            "vote_value": 1
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["vote_value"] == 1
    assert data["article_id"] == str(test_article.id)


@pytest.mark.asyncio
async def test_cast_vote_update(client, auth_headers, test_article):
    """Test updating vote value."""
    # First vote
    await client.post(
        "/api/v1/votes/",
        headers=auth_headers,
        json={
            "article_id": str(test_article.id),
            "vote_value": 1
        }
    )
    
    # Update vote
    response = await client.post(
        "/api/v1/votes/",
        headers=auth_headers,
        json={
            "article_id": str(test_article.id),
            "vote_value": -1
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["vote_value"] == -1


@pytest.mark.asyncio
async def test_remove_vote(client, auth_headers, test_article):
    """Test removing vote."""
    # Cast vote first
    await client.post(
        "/api/v1/votes/",
        headers=auth_headers,
        json={
            "article_id": str(test_article.id),
            "vote_value": 1
        }
    )
    
    # Remove vote
    response = await client.delete(
        f"/api/v1/votes/{test_article.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "success" in data["message"].lower()


@pytest.mark.asyncio
async def test_remove_vote_idempotent(client, auth_headers, test_article):
    """Test removing non-existent vote is idempotent."""
    response = await client.delete(
        f"/api/v1/votes/{test_article.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
```

---

## 📋 **Testing Summary**

### **Test Files to Create:**

**Unit Tests:**
1. `tests/unit/test_article_service.py` - Article service logic
2. `tests/unit/test_vote_service.py` - Vote service logic
3. `tests/unit/test_comment_service.py` - Comment service logic

**Integration Tests:**
1. `tests/integration/test_articles_api.py` - Articles endpoints
2. `tests/integration/test_votes_api.py` - Votes endpoints
3. `tests/integration/test_comments_api.py` - Comments endpoints

**Estimated Test Count:**
- Unit tests: ~30-40 tests
- Integration tests: ~20-30 tests
- **Total: ~50-70 tests**

---

# 📊 IMPLEMENTATION TIMELINE

## **Day 1: Service Layer (3-4 hours)**
- ✅ Create `base_service.py`
- ✅ Create `article_service.py`
- ✅ Create `vote_service.py`
- ✅ Create `comment_service.py`
- ✅ Create service init file

## **Day 2: DI & API Endpoints (3-4 hours)**
- ✅ Update `dependencies.py`
- ✅ Create vote schema
- ✅ Create `votes.py` endpoints
- ✅ Create `comments.py` endpoints
- ✅ Update router registration
- ✅ Create repository init file

## **Day 3: Testing (3-4 hours)**
- ✅ Setup test configuration
- ✅ Write unit tests (services)
- ✅ Write integration tests (APIs)
- ✅ Run test suite and verify coverage

---

# ✅ IMPLEMENTATION CHECKLIST

## **Service Layer:**
- [ ] Create `base_service.py` with error handling
- [ ] Create `article_service.py` with feed/search/detail
- [ ] Create `vote_service.py` with cast/remove/get
- [ ] Create `comment_service.py` with CRUD and tree building
- [ ] Create `services/__init__.py`

## **Dependency Injection:**
- [ ] Update `api/dependencies.py` with repository factories
- [ ] Add service factories to dependencies
- [ ] Verify dependency chain works

## **Schemas:**
- [ ] Create `schemas/vote.py` with VoteCreate/Response
- [ ] Verify existing comment schemas are complete

## **API Endpoints:**
- [ ] Create `api/v1/endpoints/votes.py` (3 endpoints)
- [ ] Create `api/v1/endpoints/comments.py` (5 endpoints)
- [ ] Update `api/v1/router.py` to register new routers
- [ ] Test all endpoints with Swagger UI

## **Init Files:**
- [ ] Create `repositories/__init__.py`
- [ ] Update `services/__init__.py`
- [ ] Verify imports work

## **Testing:**
- [ ] Create `tests/conftest.py` with fixtures
- [ ] Write unit tests for services (3 files)
- [ ] Write integration tests for APIs (3 files)
- [ ] Run pytest and verify coverage >80%
- [ ] Fix any failing tests

## **Documentation:**
- [ ] Update API documentation in Swagger
- [ ] Add docstrings to all new functions
- [ ] Update README with new endpoints

---

# 🎯 SUCCESS CRITERIA

## **Functional Requirements:**
✅ All service methods work correctly  
✅ All API endpoints return expected responses  
✅ Authentication/authorization enforced properly  
✅ Vote operations are idempotent  
✅ Comment threading works correctly  
✅ Error handling provides useful messages  

## **Code Quality:**
✅ 80%+ test coverage  
✅ All tests passing  
✅ Type hints on all functions  
✅ Docstrings on all public methods  
✅ No linting errors  
✅ Follows established patterns  

## **Integration:**
✅ Services integrate with repositories correctly  
✅ DI system works smoothly  
✅ API endpoints integrate with services correctly  
✅ Authentication flow works end-to-end  
✅ Database transactions handled properly  

---

# 🚀 DEPLOYMENT PREPARATION

After implementation completion:

1. **Manual Testing:**
   - Test all endpoints via Swagger UI
   - Test authentication flows
   - Test error scenarios
   - Verify vote/comment operations

2. **Performance Testing:**
   - Test with multiple concurrent users
   - Check query performance
   - Verify no N+1 queries

3. **Documentation:**
   - Update API documentation
   - Document new endpoints
   - Update deployment guide

4. **Migration:**
   - Ensure database migrations are current
   - Test migrations on staging

---

# 📚 BEST PRACTICES IMPLEMENTED

✅ **Separation of Concerns:** Repositories → Services → APIs  
✅ **Dependency Injection:** Clean, testable code  
✅ **Error Handling:** Consistent HTTP exceptions  
✅ **Validation:** Pydantic schemas at boundaries  
✅ **Type Safety:** Full type hints throughout  
✅ **Idempotency:** Safe retry behavior  
✅ **Logging:** Structured logging in services  
✅ **Testing:** Comprehensive test coverage  
✅ **Documentation:** Clear docstrings and API docs  
✅ **Security:** Authentication/authorization enforced  

---

**Plan Created by:** Implementation Planning Agent  
**Date:** October 10, 2025  
**Status:** ✅ Ready for Implementation  
**Estimated Completion:** 3 days (8-10 hours)
