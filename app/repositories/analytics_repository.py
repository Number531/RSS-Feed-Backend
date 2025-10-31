"""
Analytics repository for aggregate fact-check queries.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, case, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.fact_check import ArticleFactCheck
from app.models.rss_source import RSSSource


class AnalyticsRepository:
    """Repository for fact-check analytics queries."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_source_reliability_stats(
        self,
        days: int = 30,
        min_articles: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get reliability statistics grouped by source.
        
        Args:
            days: Number of days to look back
            min_articles: Minimum articles required for inclusion
            
        Returns:
            List of dicts with source statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = (
            select(
                RSSSource.id.label('source_id'),
                RSSSource.source_name,
                RSSSource.category,
                func.count(Article.id).label('articles_count'),
                func.avg(ArticleFactCheck.credibility_score).label('avg_score'),
                func.avg(ArticleFactCheck.confidence).label('avg_confidence'),
                func.count(case((ArticleFactCheck.verdict == 'TRUE', 1))).label('true_count'),
                func.count(case((ArticleFactCheck.verdict == 'FALSE', 1))).label('false_count'),
                func.count(case((ArticleFactCheck.verdict == 'MIXED', 1))).label('mixed_count'),
                func.count(case((ArticleFactCheck.verdict == 'MOSTLY_TRUE', 1))).label('mostly_true_count'),
                func.count(case((ArticleFactCheck.verdict == 'MOSTLY_FALSE', 1))).label('mostly_false_count'),
                func.count(case((ArticleFactCheck.verdict.like('%MISLEADING%'), 1))).label('misleading_count'),
                func.count(case((ArticleFactCheck.verdict.like('%UNVERIFIED%'), 1))).label('unverified_count'),
                func.sum(ArticleFactCheck.claims_analyzed).label('total_claims'),
                func.sum(ArticleFactCheck.claims_true).label('total_claims_true'),
                func.sum(ArticleFactCheck.claims_false).label('total_claims_false')
            )
            .select_from(RSSSource)
            .join(Article, Article.rss_source_id == RSSSource.id)
            .join(ArticleFactCheck, ArticleFactCheck.article_id == Article.id)
            .where(Article.created_at >= cutoff_date)
            .group_by(RSSSource.id, RSSSource.source_name, RSSSource.category)
            .having(func.count(Article.id) >= min_articles)
            .order_by(desc('avg_score'))
        )
        
        result = await self.db.execute(query)
        rows = result.mappings().all()
        
        return [dict(row) for row in rows]
    
    async def get_temporal_trends(
        self,
        source_id: Optional[str] = None,
        category: Optional[str] = None,
        days: int = 30,
        granularity: str = 'daily'
    ) -> List[Dict[str, Any]]:
        """
        Get fact-check trends over time.
        
        Args:
            source_id: Filter by specific source
            category: Filter by category
            days: Number of days to look back
            granularity: 'hourly', 'daily', or 'weekly'
            
        Returns:
            List of dicts with temporal data
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Choose date truncation based on granularity
        if granularity == 'hourly':
            date_trunc = func.date_trunc('hour', Article.created_at)
        elif granularity == 'weekly':
            date_trunc = func.date_trunc('week', Article.created_at)
        else:  # daily
            date_trunc = func.date_trunc('day', Article.created_at)
        
        query = (
            select(
                date_trunc.label('period'),
                func.count(Article.id).label('articles_count'),
                func.avg(ArticleFactCheck.credibility_score).label('avg_score'),
                func.avg(ArticleFactCheck.confidence).label('avg_confidence'),
                func.count(case((ArticleFactCheck.verdict == 'TRUE', 1))).label('true_count'),
                func.count(case((ArticleFactCheck.verdict == 'FALSE', 1))).label('false_count')
            )
            .select_from(Article)
            .join(ArticleFactCheck, ArticleFactCheck.article_id == Article.id)
            .where(Article.created_at >= cutoff_date)
        )
        
        # Apply filters
        if source_id:
            query = query.where(Article.rss_source_id == source_id)
        if category:
            query = query.where(Article.category == category)
        
        query = query.group_by('period').order_by('period')
        
        result = await self.db.execute(query)
        rows = result.mappings().all()
        
        return [dict(row) for row in rows]
    
    async def get_claims_statistics(
        self,
        verdict: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get aggregate claims statistics.
        
        Args:
            verdict: Filter by specific verdict
            days: Number of days to look back
            
        Returns:
            Dict with claims statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = (
            select(
                func.count(ArticleFactCheck.id).label('total_fact_checks'),
                func.sum(ArticleFactCheck.claims_analyzed).label('total_claims'),
                func.sum(ArticleFactCheck.claims_true).label('claims_true'),
                func.sum(ArticleFactCheck.claims_false).label('claims_false'),
                func.sum(ArticleFactCheck.claims_misleading).label('claims_misleading'),
                func.sum(ArticleFactCheck.claims_unverified).label('claims_unverified'),
                func.avg(ArticleFactCheck.credibility_score).label('avg_credibility'),
                func.avg(ArticleFactCheck.confidence).label('avg_confidence')
            )
            .select_from(ArticleFactCheck)
            .join(Article, Article.id == ArticleFactCheck.article_id)
            .where(Article.created_at >= cutoff_date)
        )
        
        if verdict:
            query = query.where(ArticleFactCheck.verdict == verdict)
        
        result = await self.db.execute(query)
        row = result.mappings().first()
        
        return dict(row) if row else {}
    
    async def get_verdict_distribution(
        self,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get distribution of verdicts.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of verdict counts
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = (
            select(
                ArticleFactCheck.verdict,
                func.count(ArticleFactCheck.id).label('count'),
                func.avg(ArticleFactCheck.credibility_score).label('avg_score')
            )
            .select_from(ArticleFactCheck)
            .join(Article, Article.id == ArticleFactCheck.article_id)
            .where(Article.created_at >= cutoff_date)
            .group_by(ArticleFactCheck.verdict)
            .order_by(desc('count'))
        )
        
        result = await self.db.execute(query)
        rows = result.mappings().all()
        
        return [dict(row) for row in rows]
