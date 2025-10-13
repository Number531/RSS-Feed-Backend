"""FastAPI endpoints for reading history management."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.reading_history_service import ReadingHistoryService
from app.schemas.reading_history import (
    ReadingHistoryCreate,
    ReadingHistoryResponse,
    ReadingHistoryList,
    ReadingHistoryWithArticle,
    ReadingStatsResponse,
    ClearHistoryRequest,
    ClearHistoryResponse,
)
from app.schemas.reading_preferences import (
    ReadingPreferencesResponse,
    ReadingPreferencesUpdate,
)


router = APIRouter()


@router.post(
    "/",
    response_model=ReadingHistoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record article view",
    description="Record that the current user viewed an article, with optional engagement metrics."
)
async def record_view(
    data: ReadingHistoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Record a new article view."""
    service = ReadingHistoryService(db)
    history = await service.record_view(
        user_id=current_user.id,
        article_id=data.article_id,
        duration_seconds=data.duration_seconds,
        scroll_percentage=data.scroll_percentage
    )
    return ReadingHistoryResponse(
        id=str(history.id),
        user_id=str(history.user_id),
        article_id=str(history.article_id),
        viewed_at=history.viewed_at,
        duration_seconds=history.duration_seconds,
        scroll_percentage=history.scroll_percentage
    )


@router.get(
    "/",
    response_model=ReadingHistoryList,
    summary="Get reading history",
    description="Get paginated reading history for the current user with optional date filtering."
)
async def get_history(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    start_date: Optional[datetime] = Query(None, description="Filter views after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter views before this date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's reading history."""
    service = ReadingHistoryService(db)
    history_list, total = await service.get_user_history(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date
    )
    
    # Convert to response schema with article details
    items = [ReadingHistoryWithArticle.from_orm_with_article(h) for h in history_list]
    
    return ReadingHistoryList(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/recent",
    response_model=list[ReadingHistoryWithArticle],
    summary="Get recently read articles",
    description="Get list of recently read articles for the current user."
)
async def get_recent(
    days: int = Query(7, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of articles"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get recently read articles."""
    service = ReadingHistoryService(db)
    recent = await service.get_recently_read(
        user_id=current_user.id,
        days=days,
        limit=limit
    )
    
    return [ReadingHistoryWithArticle.from_orm_with_article(h) for h in recent]


@router.get(
    "/stats",
    response_model=ReadingStatsResponse,
    summary="Get reading statistics",
    description="Get reading statistics for the current user with optional date filtering."
)
async def get_stats(
    start_date: Optional[datetime] = Query(None, description="Statistics period start"),
    end_date: Optional[datetime] = Query(None, description="Statistics period end"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's reading statistics."""
    service = ReadingHistoryService(db)
    stats = await service.get_reading_stats(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    return ReadingStatsResponse(**stats)


@router.delete(
    "/",
    response_model=ClearHistoryResponse,
    summary="Clear reading history",
    description="Clear reading history for the current user. Optionally specify a date to only clear history before that date."
)
async def clear_history(
    data: ClearHistoryRequest = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clear user's reading history."""
    service = ReadingHistoryService(db)
    
    before_date = data.before_date if data else None
    deleted_count = await service.clear_history(
        user_id=current_user.id,
        before_date=before_date
    )
    
    message = f"Successfully cleared {deleted_count} history record(s)"
    if before_date:
        message += f" before {before_date.isoformat()}"
    
    return ClearHistoryResponse(
        deleted_count=deleted_count,
        message=message
    )


@router.get(
    "/export",
    summary="Export reading history",
    description="Export reading history in JSON or CSV format for data portability."
)
async def export_history(
    format: str = Query("json", pattern="^(json|csv)$", description="Export format: json or csv"),
    start_date: Optional[datetime] = Query(None, description="Export history after this date"),
    end_date: Optional[datetime] = Query(None, description="Export history before this date"),
    include_articles: bool = Query(True, description="Include full article details in export"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export user's reading history in JSON or CSV format."""
    service = ReadingHistoryService(db)
    
    content, filename = await service.export_history(
        user_id=current_user.id,
        format=format,
        start_date=start_date,
        end_date=end_date,
        include_articles=include_articles
    )
    
    # Set appropriate media type
    media_type = "application/json" if format == "json" else "text/csv"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get(
    "/preferences",
    response_model=ReadingPreferencesResponse,
    summary="Get reading preferences",
    description="Get reading tracking preferences for the current user."
)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's reading preferences."""
    service = ReadingHistoryService(db)
    prefs = await service.get_user_preferences(current_user.id)
    return ReadingPreferencesResponse.from_orm(prefs)


@router.put(
    "/preferences",
    response_model=ReadingPreferencesResponse,
    summary="Update reading preferences",
    description="Update reading tracking preferences for the current user."
)
async def update_preferences(
    data: ReadingPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user's reading preferences."""
    service = ReadingHistoryService(db)
    prefs = await service.update_user_preferences(
        user_id=current_user.id,
        **data.dict(exclude_unset=True)
    )
    return ReadingPreferencesResponse.from_orm(prefs)
