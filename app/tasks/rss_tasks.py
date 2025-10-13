"""
Celery tasks for RSS feed fetching and processing.
"""
import asyncio
import logging
from typing import List
from celery import group

from app.core.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.services.rss_feed_service import RSSFeedService, parse_feed_entry
from app.services.article_processing_service import ArticleProcessingService
from app.core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.rss_tasks.fetch_all_feeds", bind=True, max_retries=0)
def fetch_all_feeds(self):
    """
    Fetch all active RSS feeds.
    
    This task is scheduled to run every 15 minutes via Celery Beat.
    It spawns individual tasks for each feed to enable parallel processing.
    """
    logger.info("Starting RSS feed fetch cycle")
    
    # Run async code in event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        source_ids = loop.run_until_complete(_get_active_source_ids())
    finally:
        loop.close()
    
    if not source_ids:
        logger.warning("No active RSS sources found")
        return {"status": "no_sources", "count": 0}
    
    logger.info(f"Found {len(source_ids)} active RSS sources")
    
    # Create parallel tasks for each source (max concurrent controlled by Celery)
    job = group(
        fetch_single_feed.s(str(source_id))
        for source_id in source_ids[:settings.RSS_MAX_CONCURRENT_FETCHES]
    )
    
    # Execute first batch
    result = job.apply_async()
    
    # Queue remaining sources
    if len(source_ids) > settings.RSS_MAX_CONCURRENT_FETCHES:
        remaining_job = group(
            fetch_single_feed.s(str(source_id))
            for source_id in source_ids[settings.RSS_MAX_CONCURRENT_FETCHES:]
        )
        remaining_job.apply_async(countdown=60)  # Start after 1 minute
    
    return {
        "status": "dispatched",
        "total_sources": len(source_ids),
        "immediate": min(len(source_ids), settings.RSS_MAX_CONCURRENT_FETCHES)
    }


@celery_app.task(name="app.tasks.rss_tasks.fetch_single_feed", bind=True, max_retries=3)
def fetch_single_feed(self, source_id: str):
    """
    Fetch and process a single RSS feed.
    
    Args:
        source_id: UUID of RSS source
        
    Returns:
        Result dict with status and article count
    """
    logger.info(f"Fetching feed for source: {source_id}")
    
    try:
        # Run async code in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_fetch_and_process_feed(source_id))
            return result
        finally:
            loop.close()
        
    except Exception as e:
        logger.error(f"Error in fetch_single_feed for {source_id}: {str(e)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            # Backoff: 1s, 2s, 4s
            countdown = 2 ** self.request.retries
            raise self.retry(exc=e, countdown=countdown)
        
        return {
            "status": "error",
            "source_id": source_id,
            "error": str(e),
            "articles_created": 0
        }


async def _get_active_source_ids() -> List[str]:
    """Get list of active RSS source IDs."""
    async with AsyncSessionLocal() as db:
        feed_service = RSSFeedService(db)
        sources = await feed_service.get_active_sources()
        return [str(source.id) for source in sources]


async def _fetch_and_process_feed(source_id: str) -> dict:
    """
    Fetch RSS feed and process all articles.
    
    Args:
        source_id: UUID of RSS source
        
    Returns:
        Result dict with status and article count
    """
    async with AsyncSessionLocal() as db:
        # Initialize services
        feed_service = RSSFeedService(db)
        article_service = ArticleProcessingService(db)
        
        # Get source
        source = await feed_service.get_source_by_id(source_id)
        if not source:
            logger.error(f"Source not found: {source_id}")
            return {
                "status": "error",
                "source_id": source_id,
                "error": "Source not found",
                "articles_created": 0
            }
        
        # Fetch feed
        feed = await feed_service.fetch_feed(source)
        if not feed:
            return {
                "status": "not_modified",
                "source_id": source_id,
                "source_name": source.name,
                "articles_created": 0
            }
        
        # Process each entry
        articles_created = 0
        articles_skipped = 0
        
        for entry in feed.entries:
            try:
                # Parse entry
                article_data = parse_feed_entry(entry)
                
                # Process and store article
                article = await article_service.process_article(article_data, source)
                
                if article:
                    articles_created += 1
                else:
                    articles_skipped += 1
                    
            except Exception as e:
                logger.error(f"Error processing entry from {source.name}: {str(e)}")
                articles_skipped += 1
                continue
        
        logger.info(
            f"Completed {source.name}: {articles_created} created, "
            f"{articles_skipped} skipped"
        )
        
        return {
            "status": "success",
            "source_id": source_id,
            "source_name": source.name,
            "articles_created": articles_created,
            "articles_skipped": articles_skipped,
            "total_entries": len(feed.entries)
        }
