"""Service for RSS Source management (admin operations)."""
import logging
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status

from app.repositories.rss_source_repository import RSSSourceRepository
from app.schemas.rss_source import (
    RSSSourceCreate,
    RSSSourceUpdate,
    RSSSourceResponse,
    RSSSourceListResponse,
    RSSCategoryResponse
)
from app.models.rss_source import RSSSource

logger = logging.getLogger(__name__)


class RSSSourceService:
    """Service for managing RSS sources."""
    
    def __init__(self, repository: RSSSourceRepository):
        """
        Initialize service.
        
        Args:
            repository: RSS source repository
        """
        self.repository = repository
    
    async def get_all_sources(
        self,
        page: int = 1,
        page_size: int = 50,
        category: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> RSSSourceListResponse:
        """
        Get all RSS sources with pagination and filtering.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            category: Optional category filter
            is_active: Optional active status filter
            
        Returns:
            Paginated list of RSS sources
        """
        # Validate pagination
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page number must be >= 1"
            )
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100"
            )
        
        skip = (page - 1) * page_size
        sources, total = await self.repository.get_all(
            skip=skip,
            limit=page_size,
            category=category,
            is_active=is_active
        )
        
        total_pages = (total + page_size - 1) // page_size
        
        return RSSSourceListResponse(
            sources=[RSSSourceResponse.model_validate(s) for s in sources],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    async def get_source_by_id(self, source_id: UUID) -> RSSSourceResponse:
        """
        Get RSS source by ID.
        
        Args:
            source_id: Source UUID
            
        Returns:
            RSS source
            
        Raises:
            HTTPException: If source not found
        """
        source = await self.repository.get_by_id(source_id)
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RSS source with ID {source_id} not found"
            )
        
        return RSSSourceResponse.model_validate(source)
    
    async def create_source(self, source_data: RSSSourceCreate) -> RSSSourceResponse:
        """
        Create new RSS source (admin only).
        
        Args:
            source_data: Source creation data
            
        Returns:
            Created RSS source
            
        Raises:
            HTTPException: If URL already exists
        """
        # Check if URL already exists
        existing = await self.repository.get_by_url(str(source_data.url))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"RSS source with URL '{source_data.url}' already exists"
            )
        
        # Create source
        source_dict = source_data.model_dump()
        source_dict['url'] = str(source_data.url)  # Convert HttpUrl to string
        source = await self.repository.create(source_dict)
        
        logger.info(f"Created RSS source: {source.name} ({source.id})")
        return RSSSourceResponse.model_validate(source)
    
    async def update_source(
        self,
        source_id: UUID,
        update_data: RSSSourceUpdate
    ) -> RSSSourceResponse:
        """
        Update RSS source (admin only).
        
        Args:
            source_id: Source UUID
            update_data: Fields to update
            
        Returns:
            Updated RSS source
            
        Raises:
            HTTPException: If source not found or URL conflict
        """
        # Get existing source
        source = await self.repository.get_by_id(source_id)
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RSS source with ID {source_id} not found"
            )
        
        # Check URL uniqueness if URL is being updated
        if update_data.url:
            existing = await self.repository.get_by_url(str(update_data.url))
            if existing and existing.id != source_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"RSS source with URL '{update_data.url}' already exists"
                )
        
        # Update source
        update_dict = update_data.model_dump(exclude_unset=True)
        if 'url' in update_dict:
            update_dict['url'] = str(update_data.url)  # Convert HttpUrl to string
        
        updated_source = await self.repository.update(source, update_dict)
        
        logger.info(f"Updated RSS source: {source.name} ({source.id})")
        return RSSSourceResponse.model_validate(updated_source)
    
    async def delete_source(self, source_id: UUID) -> dict:
        """
        Delete RSS source (admin only).
        
        Args:
            source_id: Source UUID
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If source not found
        """
        source = await self.repository.get_by_id(source_id)
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RSS source with ID {source_id} not found"
            )
        
        await self.repository.delete(source)
        
        logger.info(f"Deleted RSS source: {source.name} ({source.id})")
        return {"message": f"RSS source '{source.name}' deleted successfully"}
    
    async def get_categories(self) -> List[RSSCategoryResponse]:
        """
        Get list of RSS categories with statistics.
        
        Returns:
            List of category statistics
        """
        categories = await self.repository.get_categories()
        return [RSSCategoryResponse(**cat) for cat in categories]
    
    async def get_active_sources(self) -> List[RSSSourceResponse]:
        """
        Get all active RSS sources.
        
        Returns:
            List of active sources
        """
        sources = await self.repository.get_active_sources()
        return [RSSSourceResponse.model_validate(s) for s in sources]
