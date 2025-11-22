"""
Synthesis service for business logic.
Handles queries for synthesis mode articles with optimized joins.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.article import Article
from app.models.rss_source import RSSSource


class SynthesisService:
    """Service for synthesis article operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_synthesis_articles(
        self,
        page: int = 1,
        page_size: int = 20,
        verdict: Optional[str] = None,
        sort_by: str = "newest"
    ) -> Dict[str, Any]:
        """
        List synthesis articles with pagination and filtering.
        
        Args:
            page: Page number (1-indexed)
            page_size: Items per page (max 100)
            verdict: Optional filter by fact_check_verdict
            sort_by: Sort order (newest, oldest, credibility)
        
        Returns:
            Dict with items, total, page, page_size, has_next
        """
        # Ensure valid pagination
        page = max(1, page)
        page_size = min(100, max(1, page_size))
        offset = (page - 1) * page_size
        
        # Build query with join
        query = (
            select(
                Article.id,
                Article.title,
                Article.synthesis_preview,
                Article.fact_check_verdict,
                Article.verdict_color,
                Article.fact_check_score,
                Article.synthesis_read_minutes,
                Article.published_date,
                RSSSource.name.label("source_name"),
                Article.category,
                Article.has_timeline,
                Article.has_context_emphasis
            )
            .join(RSSSource, Article.rss_source_id == RSSSource.id)
            .where(Article.has_synthesis == True)
        )
        
        # Apply verdict filter
        if verdict:
            query = query.where(Article.fact_check_verdict == verdict)
        
        # Apply sorting
        if sort_by == "oldest":
            query = query.order_by(Article.published_date.asc())
        elif sort_by == "credibility":
            query = query.order_by(Article.fact_check_score.desc().nullslast())
        else:  # newest (default)
            query = query.order_by(Article.published_date.desc().nullslast())
        
        # Get total count (before pagination)
        count_query = (
            select(func.count())
            .select_from(Article)
            .where(Article.has_synthesis == True)
        )
        if verdict:
            count_query = count_query.where(Article.fact_check_verdict == verdict)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        query = query.limit(page_size).offset(offset)
        
        # Execute query
        result = await self.db.execute(query)
        rows = result.all()
        
        # Convert to dicts
        items = []
        for row in rows:
            items.append({
                "id": str(row.id),  # Convert UUID to string
                "title": row.title,
                "synthesis_preview": row.synthesis_preview,
                "fact_check_verdict": row.fact_check_verdict,
                "verdict_color": row.verdict_color,
                "fact_check_score": row.fact_check_score,
                "synthesis_read_minutes": row.synthesis_read_minutes,
                "published_date": row.published_date,
                "source_name": row.source_name,
                "category": row.category,
                "has_timeline": row.has_timeline or False,
                "has_context_emphasis": row.has_context_emphasis or False
            })
        
        # Calculate has_next
        has_next = (offset + len(items)) < total
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_next": has_next
        }
    
    async def get_synthesis_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single synthesis article with full details and JSONB arrays.
        
        Args:
            article_id: Article UUID as string
        
        Returns:
            Dict with article details or None if not found
        """
        try:
            # Convert string to UUID
            article_uuid = UUID(article_id)
        except ValueError:
            return None
        
        # Query with join - fetch the full article object including article_data
        query = (
            select(
                Article.id,
                Article.title,
                Article.content,
                Article.synthesis_article,
                Article.fact_check_verdict,
                Article.verdict_color,
                Article.fact_check_score,
                Article.synthesis_word_count,
                Article.synthesis_read_minutes,
                Article.published_date,
                Article.author,
                RSSSource.name.label("source_name"),
                Article.category,
                Article.url,
                Article.has_timeline,
                Article.has_context_emphasis,
                Article.timeline_event_count,
                Article.reference_count,
                Article.margin_note_count,
                Article.fact_check_mode,
                Article.fact_check_processing_time,
                Article.synthesis_generated_at,
                Article.article_data  # Fetch the whole JSONB object
            )
            .join(RSSSource, Article.rss_source_id == RSSSource.id)
            .where(Article.id == article_uuid)
            .where(Article.has_synthesis == True)
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        # Extract JSONB arrays from article_data (in Python)
        article_data = row.article_data or {}
        references = article_data.get("references", [])
        event_timeline = article_data.get("event_timeline", [])
        margin_notes = article_data.get("margin_notes", [])
        context_and_emphasis = article_data.get("context_and_emphasis", [])
        
        # Convert to dict with JSONB arrays
        return {
            "id": str(row.id),
            "title": row.title,
            "content": row.content,
            "synthesis_article": row.synthesis_article,
            "fact_check_verdict": row.fact_check_verdict,
            "verdict_color": row.verdict_color,
            "fact_check_score": row.fact_check_score,
            "synthesis_word_count": row.synthesis_word_count,
            "synthesis_read_minutes": row.synthesis_read_minutes,
            "published_date": row.published_date,
            "author": row.author,
            "source_name": row.source_name,
            "category": row.category,
            "url": row.url,
            "has_timeline": row.has_timeline or False,
            "has_context_emphasis": row.has_context_emphasis or False,
            "timeline_event_count": row.timeline_event_count,
            "reference_count": row.reference_count,
            "margin_note_count": row.margin_note_count,
            "fact_check_mode": row.fact_check_mode,
            "fact_check_processing_time": row.fact_check_processing_time,
            "synthesis_generated_at": row.synthesis_generated_at,
            # JSONB arrays extracted from article_data
            "references": references if references else [],
            "event_timeline": event_timeline if event_timeline else [],
            "margin_notes": margin_notes if margin_notes else [],
            "context_and_emphasis": context_and_emphasis if context_and_emphasis else []
        }
    
    async def get_synthesis_stats(self) -> Dict[str, Any]:
        """
        Get aggregate statistics for synthesis articles.
        
        Returns:
            Dict with aggregate metrics
        """
        # Main stats query
        # Use CASE WHEN for Boolean to Integer conversion (PostgreSQL compatible)
        stats_query = select(
            func.count(Article.id).label("total"),
            func.sum(case((Article.has_timeline == True, 1), else_=0)).label("with_timeline"),
            func.sum(case((Article.has_context_emphasis == True, 1), else_=0)).label("with_context"),
            func.avg(Article.fact_check_score).label("avg_score"),
            func.avg(Article.synthesis_word_count).label("avg_words"),
            func.avg(Article.synthesis_read_minutes).label("avg_minutes")
        ).where(Article.has_synthesis == True)
        
        stats_result = await self.db.execute(stats_query)
        stats = stats_result.first()
        
        # Verdict distribution query
        verdict_query = (
            select(
                Article.fact_check_verdict,
                func.count().label("count")
            )
            .where(Article.has_synthesis == True)
            .where(Article.fact_check_verdict.isnot(None))
            .group_by(Article.fact_check_verdict)
        )
        
        verdict_result = await self.db.execute(verdict_query)
        verdict_rows = verdict_result.all()
        
        # Build verdict distribution dict
        verdict_distribution = {row.fact_check_verdict: row.count for row in verdict_rows}
        
        # Calculate averages with defaults (handle None gracefully)
        total = int(stats.total) if stats.total is not None else 0
        with_timeline = int(stats.with_timeline) if stats.with_timeline is not None else 0
        with_context = int(stats.with_context) if stats.with_context is not None else 0
        avg_score = float(stats.avg_score) if stats.avg_score is not None else 0.0
        avg_words = int(stats.avg_words) if stats.avg_words is not None else 0
        avg_minutes = int(stats.avg_minutes) if stats.avg_minutes is not None else 0
        
        # Convert score to 0-1 range for average_credibility (fact_check_score is 0-100)
        average_credibility = avg_score / 100.0 if avg_score > 0 else 0.0
        
        return {
            "total_synthesis_articles": total,
            "articles_with_timeline": with_timeline,
            "articles_with_context": with_context,
            "average_credibility": average_credibility,
            "verdict_distribution": verdict_distribution,
            "average_word_count": avg_words,
            "average_read_minutes": avg_minutes
        }
