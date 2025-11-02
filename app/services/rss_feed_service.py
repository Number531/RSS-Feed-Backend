"""
RSS Feed Service for fetching and parsing RSS feeds.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

import feedparser
import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.rss_source import RSSSource

logger = logging.getLogger(__name__)


class RSSFeedService:
    """Service for fetching and parsing RSS feeds."""

    def __init__(self, db: AsyncSession):
        """
        Initialize RSS feed service.

        Args:
            db: Database session
        """
        self.db = db
        self.timeout = settings.RSS_FETCH_TIMEOUT
        self.user_agent = settings.RSS_USER_AGENT

    async def fetch_feed(self, source: RSSSource) -> Optional[feedparser.FeedParserDict]:
        """
        Fetch RSS feed from source with timeout and error handling.

        Args:
            source: RSS source configuration

        Returns:
            Parsed feed dict or None on error
        """
        headers = {
            "User-Agent": self.user_agent,
        }

        # Add conditional GET headers if available
        if source.etag:
            headers["If-None-Match"] = source.etag
        if source.last_modified:
            headers["If-Modified-Since"] = source.last_modified.strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Fetching feed: {source.name} ({source.url})")
                response = await client.get(source.url, headers=headers, follow_redirects=True)

                # Handle 304 Not Modified
                if response.status_code == 304:
                    logger.info(f"Feed not modified: {source.name}")
                    await self._update_fetch_success(source, None, None)
                    return None

                # Check for errors
                response.raise_for_status()

                # Parse feed
                feed = feedparser.parse(response.content)

                # Update caching headers
                etag = response.headers.get("ETag")
                last_modified = response.headers.get("Last-Modified")

                await self._update_fetch_success(source, etag, last_modified)

                logger.info(f"Successfully fetched {len(feed.entries)} entries from {source.name}")
                return feed

        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching feed: {source.name}")
            await self._update_fetch_failure(source, "Timeout")
            return None

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching feed {source.name}: {e.response.status_code}")
            await self._update_fetch_failure(source, f"HTTP {e.response.status_code}")
            return None

        except Exception as e:
            logger.error(f"Error fetching feed {source.name}: {str(e)}")
            await self._update_fetch_failure(source, str(e))
            return None

    async def _update_fetch_success(
        self, source: RSSSource, etag: Optional[str], last_modified: Optional[str]
    ):
        """Update source after successful fetch."""
        now = datetime.now(timezone.utc)

        source.last_fetched = now
        source.last_successful_fetch = now
        source.fetch_success_count += 1
        source.consecutive_failures = 0

        if etag:
            source.etag = etag
        if last_modified:
            try:
                source.last_modified = datetime.strptime(last_modified, "%a, %d %b %Y %H:%M:%S GMT")
            except ValueError:
                pass  # Invalid date format, skip

        await self.db.commit()

    async def _update_fetch_failure(self, source: RSSSource, error: str):
        """Update source after failed fetch."""
        source.last_fetched = datetime.now(timezone.utc)
        source.fetch_failure_count += 1
        source.consecutive_failures += 1

        # Deactivate source after 10 consecutive failures
        if source.consecutive_failures >= 10:
            source.is_active = False
            logger.warning(
                f"Deactivating source {source.name} after {source.consecutive_failures} "
                f"consecutive failures"
            )

        await self.db.commit()

    async def get_active_sources(self) -> List[RSSSource]:
        """
        Get all active RSS sources.

        Returns:
            List of active RSS sources
        """
        result = await self.db.execute(select(RSSSource).where(RSSSource.is_active.is_(True)))
        return list(result.scalars().all())

    async def get_source_by_id(self, source_id: str) -> Optional[RSSSource]:
        """
        Get RSS source by ID.

        Args:
            source_id: Source UUID

        Returns:
            RSS source or None
        """
        result = await self.db.execute(select(RSSSource).where(RSSSource.id == source_id))
        return result.scalar_one_or_none()


def parse_feed_entry(entry: Dict) -> Dict:
    """
    Parse feed entry into standardized format.

    Handles both dict-style and object-style feed entries.

    Args:
        entry: feedparser entry dict or object

    Returns:
        Standardized article dict
    """

    # Helper function to get value from dict or object attribute
    def get_value(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    # Extract published date
    published_date = None
    published_parsed = get_value(entry, "published_parsed")
    if published_parsed:
        try:
            published_date = datetime(*published_parsed[:6])
        except (TypeError, ValueError):
            pass

    # Extract author
    author = get_value(entry, "author")
    if not author:
        authors = get_value(entry, "authors", [])
        if authors:
            if isinstance(authors[0], dict):
                author = authors[0].get("name", "")
            else:
                author = str(authors[0])

    # Extract content - prefer content field over summary
    content = None
    content_list = get_value(entry, "content")
    if content_list:
        if isinstance(content_list, list) and len(content_list) > 0:
            content_item = content_list[0]
            if isinstance(content_item, dict):
                content = content_item.get("value", "")
            else:
                content = getattr(content_item, "value", None)

    if not content:
        content = get_value(entry, "summary")

    # Extract description - prefer summary field
    description = get_value(entry, "summary")
    if not description:
        description = get_value(entry, "description")

    # Extract thumbnail
    thumbnail_url = None
    media_thumbnail = get_value(entry, "media_thumbnail")
    if media_thumbnail:
        thumbnail_url = media_thumbnail[0].get("url") if isinstance(media_thumbnail, list) else None

    if not thumbnail_url:
        media_content = get_value(entry, "media_content")
        if media_content:
            thumbnail_url = media_content[0].get("url") if isinstance(media_content, list) else None

    return {
        "title": get_value(entry, "title", ""),
        "url": get_value(entry, "link", ""),
        "description": description,
        "content": content,
        "author": author,
        "published_date": published_date,
        "thumbnail_url": thumbnail_url,
    }


def extract_feed_metadata(feed: feedparser.FeedParserDict) -> dict:
    """
    Extract metadata from an RSS feed (stub implementation).

    Args:
        feed: Parsed feedparser feed object

    Returns:
        Dictionary with feed metadata
    """
    # TODO: Implement full feed metadata extraction
    return {
        "title": feed.feed.get("title", ""),
        "link": feed.feed.get("link", ""),
        "description": feed.feed.get("description", ""),
        "language": feed.feed.get("language", "en"),
    }
