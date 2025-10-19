"""
Article Processing Service for deduplication, categorization, and storage.
"""
import logging
from typing import Dict, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.article import Article
from app.models.rss_source import RSSSource
from app.utils.url_utils import generate_url_hash
from app.utils.categorization import categorize_article, extract_tags
from app.utils.content_utils import sanitize_html, clean_description, extract_first_image
from app.core.config import settings

logger = logging.getLogger(__name__)


class ArticleProcessingService:
    """Service for processing and storing articles."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize article processing service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def process_article(
        self,
        article_data: Dict,
        source: RSSSource
    ) -> Optional[Article]:
        """
        Process article: deduplicate, categorize, sanitize, and store.
        
        Args:
            article_data: Parsed article data from RSS feed
            source: RSS source this article came from
            
        Returns:
            Created/existing Article or None if skipped
        """
        url = article_data.get('url')
        if not url:
            logger.warning("Article missing URL, skipping")
            return None
        
        title = article_data.get('title', '')
        if not title:
            logger.warning(f"Article missing title: {url}")
            return None
        
        # Generate URL hash for deduplication
        url_hash = generate_url_hash(url)
        
        # Check if article already exists
        existing = await self._get_article_by_url_hash(url_hash)
        if existing:
            logger.debug(f"Article already exists: {title[:50]}...")
            return existing
        
        # Extract and clean content
        description = article_data.get('description', '')
        content = article_data.get('content', '')
        
        if description:
            description = clean_description(description)
        
        if content:
            content = sanitize_html(content)
        
        # Categorize article
        category = categorize_article(title, description or '', source.category)
        
        # Extract tags
        tags = extract_tags(title, description or '')
        
        # Extract thumbnail
        thumbnail_url = article_data.get('thumbnail_url')
        if not thumbnail_url and content:
            thumbnail_url = extract_first_image(content)
        
        # Create article
        try:
            article = Article(
                rss_source_id=source.id,
                title=title,
                url=url,
                url_hash=url_hash,
                description=description,
                content=content,
                author=article_data.get('author'),
                published_date=article_data.get('published_date'),
                thumbnail_url=thumbnail_url,
                category=category,
                tags=tags,
            )
            
            self.db.add(article)
            await self.db.commit()
            await self.db.refresh(article)
            
            logger.info(f"Created new article: {title[:50]}... (category: {category})")
            
            # Trigger fact-check asynchronously
            self._trigger_fact_check(article.id)
            
            return article
            
        except IntegrityError as e:
            # Duplicate detected (race condition)
            await self.db.rollback()
            logger.debug(f"Duplicate article detected (race condition): {title[:50]}...")
            existing = await self._get_article_by_url_hash(url_hash)
            return existing
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating article {title[:50]}...: {str(e)}")
            return None
    
    async def _get_article_by_url_hash(self, url_hash: str) -> Optional[Article]:
        """
        Get article by URL hash.
        
        Args:
            url_hash: SHA-256 hash of normalized URL
            
        Returns:
            Article or None
        """
        result = await self.db.execute(
            select(Article).where(Article.url_hash == url_hash)
        )
        return result.scalar_one_or_none()
    
    async def get_article_count_by_source(self, source_id: str) -> int:
        """
        Get count of articles from a specific source.
        
        Args:
            source_id: RSS source ID
            
        Returns:
            Article count
        """
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count(Article.id)).where(Article.rss_source_id == source_id)
        )
        return result.scalar() or 0
    
    async def get_total_article_count(self) -> int:
        """
        Get total count of articles in database.
        
        Returns:
            Total article count
        """
        from sqlalchemy import func
        result = await self.db.execute(select(func.count(Article.id)))
        return result.scalar() or 0
    
    def _trigger_fact_check(self, article_id: UUID):
        """
        Trigger asynchronous fact-check for an article.
        
        Args:
            article_id: UUID of article to fact-check
        """
        if not settings.FACT_CHECK_ENABLED:
            logger.debug(f"Fact-check disabled, skipping article {article_id}")
            return
        
        try:
            # Import here to avoid circular dependency
            from app.tasks.fact_check_tasks import process_fact_check_job_async
            
            # Trigger Celery task
            process_fact_check_job_async.delay(str(article_id))
            logger.info(f"Triggered fact-check task for article {article_id}")
            
        except Exception as e:
            # Non-critical error, log and continue
            logger.error(f"Failed to trigger fact-check for article {article_id}: {e}")
