"""
Celery tasks for analytics operations.
"""

import logging
from datetime import datetime

from celery import shared_task
from sqlalchemy import text

from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


@shared_task(name="refresh_analytics_materialized_views")
def refresh_materialized_views():
    """
    Refresh all analytics materialized views.
    
    Runs every 15 minutes to keep analytics data up-to-date.
    Uses CONCURRENTLY to avoid locking tables during refresh.
    
    Returns:
        dict: Status and timestamp of refresh operation
    """
    try:
        db = SessionLocal()
        
        # Refresh all materialized views concurrently (no table locks)
        views = [
            "analytics_daily_summary",
            "analytics_source_reliability",
            "analytics_category_summary"
        ]
        
        for view_name in views:
            logger.info(f"Refreshing materialized view: {view_name}")
            db.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}"))
        
        db.commit()
        db.close()
        
        logger.info("✅ All analytics materialized views refreshed successfully")
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "views_refreshed": views
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to refresh materialized views: {e}")
        if db:
            db.rollback()
            db.close()
        raise


@shared_task(name="warm_analytics_cache")
def warm_analytics_cache():
    """
    Pre-populate Redis cache with common analytics queries.
    
    Runs after materialized view refresh to ensure cache
    contains fresh data for frequently accessed endpoints.
    
    Returns:
        dict: Status and number of cache entries warmed
    """
    try:
        from app.services.analytics_service import AnalyticsService
        from app.repositories.analytics_repository import AnalyticsRepository
        
        db = SessionLocal()
        repo = AnalyticsRepository(db)
        service = AnalyticsService(repo)
        
        # Common query patterns to pre-cache
        cache_keys_warmed = 0
        
        # Warm aggregate stats
        logger.info("Warming cache: aggregate statistics")
        service.get_aggregate_statistics()
        cache_keys_warmed += 1
        
        # Warm category analytics for common periods
        for days in [7, 30]:
            logger.info(f"Warming cache: category analytics ({days} days)")
            service.get_category_analytics(days=days, min_articles=5, sort_by="credibility")
            cache_keys_warmed += 1
        
        # Warm verdict details
        logger.info("Warming cache: verdict details")
        service.get_verdict_details(days=30)
        cache_keys_warmed += 1
        
        db.close()
        
        logger.info(f"✅ Cache warmed with {cache_keys_warmed} entries")
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "cache_keys_warmed": cache_keys_warmed
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to warm analytics cache: {e}")
        if db:
            db.close()
        # Don't raise - cache warming is non-critical
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
