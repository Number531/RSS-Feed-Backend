"""
Celery tasks for cache management.

Provides scheduled tasks for cache invalidation and warming.
"""

import logging
from datetime import datetime

from celery import shared_task

from app.utils.cache import cache_manager

logger = logging.getLogger(__name__)


@shared_task(name="clear_analytics_cache")
def clear_analytics_cache():
    """
    Clear all analytics cache entries.
    
    This task runs every 15 minutes (aligned with RSS feed refresh rate)
    to ensure analytics data stays fresh.
    
    Returns:
        dict: Status and statistics
    """
    try:
        logger.info("🧹 Starting analytics cache invalidation...")
        
        # Import asyncio to run async code in sync task
        import asyncio
        
        # Connect to cache if not already connected
        async def invalidate_cache():
            if not cache_manager._is_connected:
                await cache_manager.connect()
            
            # Clear all analytics cache keys
            deleted_count = await cache_manager.clear_analytics_cache()
            
            return deleted_count
        
        # Run async function
        deleted_count = asyncio.run(invalidate_cache())
        
        logger.info(
            f"✅ Analytics cache cleared successfully. "
            f"Deleted {deleted_count} keys at {datetime.utcnow().isoformat()}"
        )
        
        return {
            "status": "success",
            "keys_deleted": deleted_count,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to clear analytics cache: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@shared_task(name="warm_analytics_cache")
def warm_analytics_cache():
    """
    Warm analytics cache by pre-computing common queries.
    
    This task can be run after cache invalidation to ensure
    the first user request is fast.
    
    Note: Currently placeholder - implement if needed for better UX.
    
    Returns:
        dict: Status
    """
    logger.info("🔥 Cache warming task triggered (not yet implemented)")
    return {
        "status": "skipped",
        "message": "Cache warming will happen naturally on first request",
        "timestamp": datetime.utcnow().isoformat(),
    }
