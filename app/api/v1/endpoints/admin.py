"""
Admin endpoints for system management and monitoring.

Requires superuser authentication.
"""

from typing import Any, Dict, List

from celery import group
from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery_app import celery_app
from app.core.security import get_current_admin_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.rss_source_repository import RSSSourceRepository
from app.schemas.rss_source import RSSSourceCreate, RSSSourceResponse, RSSSourceUpdate
from app.services.rss_source_service import RSSSourceService
from app.tasks.rss_tasks import fetch_all_feeds, fetch_single_feed

router = APIRouter()


# ============================================================================
# CELERY CONTROL & MONITORING
# ============================================================================


@router.get("/celery/status", response_model=Dict[str, Any])
async def get_celery_status(current_user: User = Depends(get_current_admin_user)):
    """
    Get Celery worker and scheduler status.

    **Admin only**
    """
    try:
        # Check if Celery workers are active
        inspect = celery_app.control.inspect()

        # Get active workers
        active_workers = inspect.active()
        registered_tasks = inspect.registered()
        stats = inspect.stats()

        # Get scheduled tasks (from beat scheduler)
        scheduled = inspect.scheduled()

        return {
            "celery_available": active_workers is not None,
            "active_workers": list(active_workers.keys()) if active_workers else [],
            "worker_count": len(active_workers) if active_workers else 0,
            "registered_tasks": list(registered_tasks.values())[0] if registered_tasks else [],
            "worker_stats": stats,
            "scheduled_tasks": scheduled,
        }
    except Exception as e:
        return {
            "celery_available": False,
            "error": str(e),
            "message": "Celery workers may not be running",
        }


@router.post("/celery/fetch-now", response_model=Dict[str, Any])
async def trigger_feed_fetch(current_user: User = Depends(get_current_admin_user)):
    """
    Manually trigger RSS feed fetching immediately.

    This bypasses the scheduled task and fetches all feeds now.

    **Admin only**
    """
    try:
        # Trigger the task
        result = fetch_all_feeds.delay()

        return {
            "status": "dispatched",
            "task_id": result.id,
            "message": "RSS feed fetch initiated",
            "check_status_url": f"/api/v1/admin/celery/task/{result.id}",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger feed fetch: {str(e)}",
        )


@router.post("/celery/fetch-feed/{feed_id}", response_model=Dict[str, Any])
async def trigger_single_feed_fetch(
    feed_id: str, current_user: User = Depends(get_current_admin_user)
):
    """
    Manually trigger fetching for a single RSS feed.

    **Admin only**

    Args:
        feed_id: UUID of the RSS source to fetch
    """
    try:
        # Trigger the task for specific feed
        result = fetch_single_feed.delay(feed_id)

        return {
            "status": "dispatched",
            "task_id": result.id,
            "feed_id": feed_id,
            "message": f"Feed fetch initiated for {feed_id}",
            "check_status_url": f"/api/v1/admin/celery/task/{result.id}",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger feed fetch: {str(e)}",
        )


@router.get("/celery/task/{task_id}", response_model=Dict[str, Any])
async def get_task_status(task_id: str, current_user: User = Depends(get_current_admin_user)):
    """
    Get status of a specific Celery task.

    **Admin only**

    Args:
        task_id: Celery task ID
    """
    try:
        result = AsyncResult(task_id, app=celery_app)

        response = {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
        }

        # Add result if task is complete
        if result.ready():
            if result.successful():
                response["result"] = result.result
            else:
                response["error"] = str(result.result)

        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}",
        )


@router.get("/celery/active-tasks", response_model=Dict[str, Any])
async def get_active_tasks(current_user: User = Depends(get_current_admin_user)):
    """
    Get list of currently running Celery tasks.

    **Admin only**
    """
    try:
        inspect = celery_app.control.inspect()
        active = inspect.active()
        reserved = inspect.reserved()

        return {
            "active_tasks": active or {},
            "reserved_tasks": reserved or {},
            "total_active": sum(len(tasks) for tasks in (active or {}).values()),
            "total_reserved": sum(len(tasks) for tasks in (reserved or {}).values()),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active tasks: {str(e)}",
        )


# ============================================================================
# RSS SOURCE MANAGEMENT (CRUD)
# ============================================================================


@router.post("/feeds", response_model=RSSSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_rss_source(
    source_data: RSSSourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Create a new RSS source.

    **Admin only**
    """
    repository = RSSSourceRepository(db)
    service = RSSSourceService(repository)
    return await service.create_source(source_data)


@router.put("/feeds/{feed_id}", response_model=RSSSourceResponse)
async def update_rss_source(
    feed_id: str,
    source_data: RSSSourceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Update an existing RSS source.

    **Admin only**
    """
    repository = RSSSourceRepository(db)
    service = RSSSourceService(repository)
    updated_source = await service.update_source(feed_id, source_data)

    if not updated_source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RSS source not found")

    return updated_source


@router.delete("/feeds/{feed_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rss_source(
    feed_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Delete an RSS source (soft delete).

    **Admin only**
    """
    repository = RSSSourceRepository(db)
    service = RSSSourceService(repository)
    deleted = await service.delete_source(feed_id)

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RSS source not found")

    return None


@router.get("/feeds/health", response_model=Dict[str, Any])
async def get_feeds_health(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_admin_user)
):
    """
    Get health status of all RSS feeds.

    Shows which feeds are failing, success rates, etc.

    **Admin only**
    """
    repository = RSSSourceRepository(db)
    sources, total = await repository.get_all(skip=0, limit=1000)  # Get all sources

    # Calculate health metrics
    healthy = [s for s in sources if s.is_healthy]
    unhealthy = [s for s in sources if not s.is_healthy and s.is_active]
    inactive = [s for s in sources if not s.is_active]

    return {
        "total_sources": len(sources),
        "healthy": len(healthy),
        "unhealthy": len(unhealthy),
        "inactive": len(inactive),
        "health_rate": len(healthy) / len(sources) if sources else 0,
        "unhealthy_feeds": [
            {
                "id": str(s.id),
                "name": s.name,
                "url": s.url,
                "success_rate": s.success_rate,
                "consecutive_failures": s.consecutive_failures,
                "last_fetched": s.last_fetched.isoformat() if s.last_fetched else None,
                "last_successful_fetch": (
                    s.last_successful_fetch.isoformat() if s.last_successful_fetch else None
                ),
            }
            for s in unhealthy
        ],
    }


# ============================================================================
# SYSTEM STATISTICS
# ============================================================================


@router.get("/stats/overview", response_model=Dict[str, Any])
async def get_system_overview(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_admin_user)
):
    """
    Get overview of system statistics.

    **Admin only**
    """
    from sqlalchemy import func, select

    from app.models.article import Article
    from app.models.rss_source import RSSSource
    from app.models.user import User as UserModel

    # Get counts
    total_users = await db.scalar(select(func.count()).select_from(UserModel))
    total_articles = await db.scalar(select(func.count()).select_from(Article))
    total_sources = await db.scalar(select(func.count()).select_from(RSSSource))
    active_sources = await db.scalar(
        select(func.count()).select_from(RSSSource).where(RSSSource.is_active == True)
    )

    return {
        "users": {
            "total": total_users,
        },
        "articles": {
            "total": total_articles,
        },
        "rss_sources": {
            "total": total_sources,
            "active": active_sources,
            "inactive": total_sources - active_sources,
        },
    }
