"""
Article Service Module

Handles business logic for article operations including feed retrieval,
search, and pagination. Coordinates between repositories and applies
business rules.
"""

from typing import List, Optional, Tuple
from uuid import UUID

from app.services.base_service import BaseService
from app.repositories.article_repository import ArticleRepository
from app.models.article import Article
from app.core.exceptions import ValidationError, NotFoundError


class ArticleService(BaseService):
    """
    Service for article-related business logic.
    
    Handles:
    - Article feed retrieval with sorting and filtering
    - Article search functionality
    - Pagination and metadata generation
    - Category and time-range filtering
    """
    
    def __init__(self, article_repository: ArticleRepository):
        """
        Initialize article service.
        
        Args:
            article_repository: Article repository instance
        """
        super().__init__()
        self.article_repo = article_repository
    
    async def get_articles_feed(
        self,
        category: Optional[str] = None,
        sort_by: str = "hot",
        time_range: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
        user_id: Optional[UUID] = None
    ) -> Tuple[List[Article], dict]:
        """
        Get paginated articles feed with filtering and sorting.
        
        Args:
            category: Filter by category (general, politics, us, world, science)
            sort_by: Sorting method (hot, new, top)
            time_range: Time filter (hour, day, week, month, year, all)
            page: Page number (1-indexed)
            page_size: Items per page
            user_id: Optional user ID for personalization
            
        Returns:
            Tuple of (articles list, pagination metadata)
            
        Raises:
            ValidationError: If parameters are invalid
        """
        # Validate pagination
        skip = (page - 1) * page_size
        self.validate_pagination(skip, page_size)
        
        # Validate sort_by
        valid_sorts = ["hot", "new", "top"]
        if sort_by not in valid_sorts:
            raise ValidationError(
                f"Invalid sort_by value. Must be one of: {', '.join(valid_sorts)}"
            )
        
        # Validate category
        if category and category not in ["general", "politics", "us", "world", "science"]:
            raise ValidationError(
                "Invalid category. Must be one of: general, politics, us, world, science"
            )
        
        # Validate time_range
        if time_range and time_range not in ["hour", "day", "week", "month", "year", "all"]:
            raise ValidationError(
                "Invalid time_range. Must be one of: hour, day, week, month, year, all"
            )
        
        # Log operation
        self.log_operation(
            "get_articles_feed",
            user_id=user_id,
            category=category,
            sort_by=sort_by,
            time_range=time_range,
            page=page,
            page_size=page_size
        )
        
        try:
            # Get articles from repository
            articles, total = await self.article_repo.get_articles_feed(
                category=category,
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                time_range=time_range,
                user_id=user_id
            )
            
            # Create pagination metadata
            metadata = self.create_pagination_metadata(
                total=total,
                skip=skip,
                limit=page_size,
                returned_count=len(articles)
            )
            
            # Add additional feed-specific metadata
            metadata.update({
                "category": category or "all",
                "sort_by": sort_by,
                "time_range": time_range or "all"
            })
            
            return articles, metadata
            
        except Exception as e:
            self.log_error("get_articles_feed", e, user_id=user_id)
            raise
    
    async def get_article_by_id(
        self,
        article_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Article:
        """
        Get a single article by ID.
        
        Args:
            article_id: Article UUID
            user_id: Optional user ID for vote information
            
        Returns:
            Article instance
            
        Raises:
            NotFoundError: If article doesn't exist
        """
        self.log_operation(
            "get_article_by_id",
            user_id=user_id,
            article_id=str(article_id)
        )
        
        try:
            article = await self.article_repo.get_article_by_id(
                article_id=article_id,
                user_id=user_id
            )
            
            if not article:
                raise NotFoundError(f"Article with ID {article_id} not found")
            
            return article
            
        except NotFoundError:
            raise
        except Exception as e:
            self.log_error("get_article_by_id", e, user_id=user_id)
            raise
    
    async def search_articles(
        self,
        query: str,
        page: int = 1,
        page_size: int = 25
    ) -> Tuple[List[Article], dict]:
        """
        Search articles using full-text search.
        
        Args:
            query: Search query string
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            Tuple of (articles list, pagination metadata)
            
        Raises:
            ValidationError: If parameters are invalid
        """
        # Validate search query
        if not query or len(query.strip()) == 0:
            raise ValidationError("Search query cannot be empty")
        
        if len(query) > 200:
            raise ValidationError("Search query too long (max 200 characters)")
        
        # Validate pagination
        skip = (page - 1) * page_size
        self.validate_pagination(skip, page_size)
        
        # Log operation
        self.log_operation(
            "search_articles",
            query=query,
            page=page,
            page_size=page_size
        )
        
        try:
            # Search articles
            articles, total = await self.article_repo.search_articles(
                query=query,
                page=page,
                page_size=page_size
            )
            
            # Create pagination metadata
            metadata = self.create_pagination_metadata(
                total=total,
                skip=skip,
                limit=page_size,
                returned_count=len(articles)
            )
            
            # Add search-specific metadata
            metadata.update({
                "query": query
            })
            
            return articles, metadata
            
        except Exception as e:
            self.log_error("search_articles", e, query=query)
            raise
    
    def validate_article_id(self, article_id: UUID) -> None:
        """
        Validate article ID format.
        
        Args:
            article_id: Article UUID to validate
            
        Raises:
            ValidationError: If article ID is invalid
        """
        if not article_id:
            raise ValidationError("Article ID is required")
        
        # UUID validation is handled by type system, but we can add
        # additional business logic validation here if needed
