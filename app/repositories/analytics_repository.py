"""
Analytics repository for aggregate fact-check queries.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.fact_check import ArticleFactCheck
from app.models.rss_source import RSSSource


class AnalyticsRepository:
    """Repository for fact-check analytics queries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_source_reliability_stats(
        self, days: int = 30, min_articles: int = 5
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
                RSSSource.id.label("source_id"),
                RSSSource.source_name,
                RSSSource.category,
                func.count(Article.id).label("articles_count"),
                func.avg(ArticleFactCheck.credibility_score).label("avg_score"),
                func.avg(ArticleFactCheck.confidence).label("avg_confidence"),
                func.count(case((ArticleFactCheck.verdict == "TRUE", 1))).label("true_count"),
                func.count(case((ArticleFactCheck.verdict == "FALSE", 1))).label("false_count"),
                func.count(case((ArticleFactCheck.verdict == "MIXED", 1))).label("mixed_count"),
                func.count(case((ArticleFactCheck.verdict == "MOSTLY_TRUE", 1))).label(
                    "mostly_true_count"
                ),
                func.count(case((ArticleFactCheck.verdict == "MOSTLY_FALSE", 1))).label(
                    "mostly_false_count"
                ),
                func.count(case((ArticleFactCheck.verdict.like("%MISLEADING%"), 1))).label(
                    "misleading_count"
                ),
                func.count(case((ArticleFactCheck.verdict.like("%UNVERIFIED%"), 1))).label(
                    "unverified_count"
                ),
                func.sum(ArticleFactCheck.claims_analyzed).label("total_claims"),
                func.sum(ArticleFactCheck.claims_true).label("total_claims_true"),
                func.sum(ArticleFactCheck.claims_false).label("total_claims_false"),
            )
            .select_from(RSSSource)
            .join(Article, Article.rss_source_id == RSSSource.id)
            .join(ArticleFactCheck, ArticleFactCheck.article_id == Article.id)
            .where(Article.created_at >= cutoff_date)
            .group_by(RSSSource.id, RSSSource.source_name, RSSSource.category)
            .having(func.count(Article.id) >= min_articles)
            .order_by(desc("avg_score"))
        )

        result = await self.db.execute(query)
        rows = result.mappings().all()

        return [dict(row) for row in rows]

    async def get_temporal_trends(
        self,
        source_id: Optional[str] = None,
        category: Optional[str] = None,
        days: int = 30,
        granularity: str = "daily",
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
        if granularity == "hourly":
            date_trunc = func.date_trunc("hour", Article.created_at)
        elif granularity == "weekly":
            date_trunc = func.date_trunc("week", Article.created_at)
        else:  # daily
            date_trunc = func.date_trunc("day", Article.created_at)

        query = (
            select(
                date_trunc.label("period"),
                func.count(Article.id).label("articles_count"),
                func.avg(ArticleFactCheck.credibility_score).label("avg_score"),
                func.avg(ArticleFactCheck.confidence).label("avg_confidence"),
                func.count(case((ArticleFactCheck.verdict == "TRUE", 1))).label("true_count"),
                func.count(case((ArticleFactCheck.verdict == "FALSE", 1))).label("false_count"),
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

        query = query.group_by("period").order_by("period")

        result = await self.db.execute(query)
        rows = result.mappings().all()

        return [dict(row) for row in rows]

    async def get_claims_statistics(
        self, verdict: Optional[str] = None, days: int = 30
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
                func.count(ArticleFactCheck.id).label("total_fact_checks"),
                func.sum(ArticleFactCheck.claims_analyzed).label("total_claims"),
                func.sum(ArticleFactCheck.claims_true).label("claims_true"),
                func.sum(ArticleFactCheck.claims_false).label("claims_false"),
                func.sum(ArticleFactCheck.claims_misleading).label("claims_misleading"),
                func.sum(ArticleFactCheck.claims_unverified).label("claims_unverified"),
                func.avg(ArticleFactCheck.credibility_score).label("avg_credibility"),
                func.avg(ArticleFactCheck.confidence).label("avg_confidence"),
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

    async def get_verdict_distribution(self, days: int = 30) -> List[Dict[str, Any]]:
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
                func.count(ArticleFactCheck.id).label("count"),
                func.avg(ArticleFactCheck.credibility_score).label("avg_score"),
            )
            .select_from(ArticleFactCheck)
            .join(Article, Article.id == ArticleFactCheck.article_id)
            .where(Article.created_at >= cutoff_date)
            .group_by(ArticleFactCheck.verdict)
            .order_by(desc("count"))
        )

        result = await self.db.execute(query)
        rows = result.mappings().all()

        return [dict(row) for row in rows]

    # === Phase 2A Methods ===

    async def get_aggregate_statistics(self) -> Dict[str, Any]:
        """
        Get high-level aggregate statistics across all data.

        Returns:
            Dict with lifetime and current month statistics
        """
        # Lifetime stats
        lifetime_query = (
            select(
                func.count(ArticleFactCheck.id).label("total_fact_checks"),
                func.count(func.distinct(Article.rss_source_id)).label("sources_monitored"),
                func.sum(ArticleFactCheck.claims_analyzed).label("total_claims"),
                func.avg(ArticleFactCheck.credibility_score).label("avg_credibility"),
            )
            .select_from(ArticleFactCheck)
            .join(Article, Article.id == ArticleFactCheck.article_id)
        )

        lifetime_result = await self.db.execute(lifetime_query)
        lifetime_row = lifetime_result.mappings().first()

        # Current month stats
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_query = (
            select(
                func.count(ArticleFactCheck.id).label("articles_this_month"),
                func.avg(ArticleFactCheck.credibility_score).label("avg_credibility_this_month"),
            )
            .select_from(ArticleFactCheck)
            .join(Article, Article.id == ArticleFactCheck.article_id)
            .where(Article.created_at >= month_start)
        )

        month_result = await self.db.execute(month_query)
        month_row = month_result.mappings().first()

        # Previous month for comparison
        prev_month_start = (month_start - timedelta(days=1)).replace(day=1)
        prev_month_query = (
            select(
                func.count(ArticleFactCheck.id).label("articles_last_month"),
                func.avg(ArticleFactCheck.credibility_score).label("avg_credibility_last_month"),
            )
            .select_from(ArticleFactCheck)
            .join(Article, Article.id == ArticleFactCheck.article_id)
            .where(and_(Article.created_at >= prev_month_start, Article.created_at < month_start))
        )

        prev_month_result = await self.db.execute(prev_month_query)
        prev_month_row = prev_month_result.mappings().first()

        return {
            "lifetime": dict(lifetime_row) if lifetime_row else {},
            "current_month": dict(month_row) if month_row else {},
            "previous_month": dict(prev_month_row) if prev_month_row else {},
        }

    async def get_category_statistics(
        self, days: int = 30, min_articles: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get statistics aggregated by article category.

        Args:
            days: Number of days to look back
            min_articles: Minimum articles required for inclusion

        Returns:
            List of category statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                Article.category,
                func.count(Article.id).label("articles_count"),
                func.avg(ArticleFactCheck.credibility_score).label("avg_credibility"),
                func.count(case((ArticleFactCheck.verdict == "FALSE", 1))).label("false_count"),
                func.count(case((ArticleFactCheck.verdict.like("%MISLEADING%"), 1))).label(
                    "misleading_count"
                ),
                func.array_agg(func.distinct(RSSSource.source_name)).label("sources"),
            )
            .select_from(Article)
            .join(ArticleFactCheck, ArticleFactCheck.article_id == Article.id)
            .join(RSSSource, RSSSource.id == Article.rss_source_id)
            .where(Article.created_at >= cutoff_date)
            .group_by(Article.category)
            .having(func.count(Article.id) >= min_articles)
            .order_by(desc("avg_credibility"))
        )

        result = await self.db.execute(query)
        rows = result.mappings().all()

        return [dict(row) for row in rows]

    async def get_verdict_confidence_correlation(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get confidence levels grouped by verdict type.

        Args:
            days: Number of days to look back

        Returns:
            List of verdict types with confidence statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                ArticleFactCheck.verdict,
                func.avg(ArticleFactCheck.confidence).label("avg_confidence"),
                func.min(ArticleFactCheck.confidence).label("min_confidence"),
                func.max(ArticleFactCheck.confidence).label("max_confidence"),
                func.count(ArticleFactCheck.id).label("count"),
            )
            .select_from(ArticleFactCheck)
            .join(Article, Article.id == ArticleFactCheck.article_id)
            .where(Article.created_at >= cutoff_date)
            .group_by(ArticleFactCheck.verdict)
            .order_by(desc("count"))
        )

        result = await self.db.execute(query)
        rows = result.mappings().all()

        return [dict(row) for row in rows]

    async def get_verdict_temporal_trends(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get verdict distribution trends over time (daily granularity).

        Args:
            days: Number of days to look back

        Returns:
            List of daily verdict counts
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        date_trunc = func.date_trunc("day", Article.created_at)

        query = (
            select(
                date_trunc.label("date"),
                ArticleFactCheck.verdict,
                func.count(ArticleFactCheck.id).label("count"),
            )
            .select_from(ArticleFactCheck)
            .join(Article, Article.id == ArticleFactCheck.article_id)
            .where(Article.created_at >= cutoff_date)
            .group_by("date", ArticleFactCheck.verdict)
            .order_by("date")
        )

        result = await self.db.execute(query)
        rows = result.mappings().all()

        return [dict(row) for row in rows]

    async def get_high_risk_verdicts(
        self, days: int = 30, min_count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get verdicts with high false/misleading rates.

        Args:
            days: Number of days to look back
            min_count: Minimum occurrences to include

        Returns:
            List of verdict statistics with risk indicators
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Calculate false/misleading counts and percentages
        query = (
            select(
                ArticleFactCheck.verdict,
                func.count(ArticleFactCheck.id).label("count"),
                func.avg(ArticleFactCheck.credibility_score).label("avg_credibility"),
                func.avg(ArticleFactCheck.confidence).label("avg_confidence"),
            )
            .select_from(ArticleFactCheck)
            .join(Article, Article.id == ArticleFactCheck.article_id)
            .where(
                and_(
                    Article.created_at >= cutoff_date,
                    ArticleFactCheck.verdict.in_(["FALSE", "MOSTLY_FALSE", "MISLEADING"]),
                )
            )
            .group_by(ArticleFactCheck.verdict)
            .having(func.count(ArticleFactCheck.id) >= min_count)
            .order_by(desc("count"))
        )

        result = await self.db.execute(query)
        rows = result.mappings().all()

        return [dict(row) for row in rows]

    async def get_high_risk_articles(
        self,
        days: int = 30,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get articles with high-risk claims.

        Args:
            days: Number of days to look back
            limit: Max results
            offset: Pagination offset

        Returns:
            Tuple of (articles list, total count)
        """
        from uuid import UUID

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Build base query - need more fields to match service expectations
        query = (
            select(
                Article.id.label("article_id"),
                Article.title,
                Article.author,
                Article.url,
                Article.created_at.label("published_at"),
                ArticleFactCheck.id.label("fact_check_id"),
                ArticleFactCheck.high_risk_claims_count,
                ArticleFactCheck.credibility_score,
                ArticleFactCheck.confidence.label("confidence_score"),
                ArticleFactCheck.verdict,
                ArticleFactCheck.num_sources,
                RSSSource.source_name,
            )
            .select_from(Article)
            .join(ArticleFactCheck, ArticleFactCheck.article_id == Article.id)
            .join(RSSSource, RSSSource.id == Article.rss_source_id)
            .where(
                and_(
                    ArticleFactCheck.high_risk_claims_count > 0,
                    Article.created_at >= cutoff_date,
                )
            )
            .order_by(desc(ArticleFactCheck.high_risk_claims_count))
        )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        rows = result.mappings().all()

        return [dict(row) for row in rows], total

    async def get_source_breakdown(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        Get source breakdown for a specific article.

        Args:
            article_id: Article UUID

        Returns:
            Dict with source breakdown or None
        """
        from uuid import UUID

        query = (
            select(
                Article.id.label("article_id"),
                Article.title,
                ArticleFactCheck.num_sources,
                ArticleFactCheck.source_breakdown,
                ArticleFactCheck.primary_source_type,
                ArticleFactCheck.source_diversity_score,
                ArticleFactCheck.source_consensus,
            )
            .select_from(ArticleFactCheck)
            .join(Article, Article.id == ArticleFactCheck.article_id)
            .where(ArticleFactCheck.article_id == UUID(article_id))
        )

        result = await self.db.execute(query)
        row = result.mappings().first()

        return dict(row) if row else None

    async def get_source_quality_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get source quality metrics grouped by primary source type.

        Args:
            days: Number of days to look back

        Returns:
            List of source type quality metrics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                ArticleFactCheck.primary_source_type,
                func.count(ArticleFactCheck.id).label("article_count"),
                func.avg(ArticleFactCheck.source_diversity_score).label("avg_diversity_score"),
                func.avg(ArticleFactCheck.credibility_score).label("avg_credibility_score"),
                func.avg(ArticleFactCheck.num_sources).label("avg_num_sources"),
            )
            .select_from(ArticleFactCheck)
            .join(Article, Article.id == ArticleFactCheck.article_id)
            .where(
                and_(
                    Article.created_at >= cutoff_date,
                    ArticleFactCheck.primary_source_type.isnot(None),
                )
            )
            .group_by(ArticleFactCheck.primary_source_type)
            .order_by(desc("article_count"))
        )

        result = await self.db.execute(query)
        rows = result.mappings().all()

        return [dict(row) for row in rows]

    async def get_risk_correlation_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get correlation between risk level and credibility.

        Args:
            days: Number of days to look back

        Returns:
            List of risk category statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Categorize by risk level
        risk_category = case(
            (ArticleFactCheck.high_risk_claims_count == 0, "low"),
            (ArticleFactCheck.high_risk_claims_count <= 2, "medium"),
            else_="high",
        ).label("risk_category")

        query = (
            select(
                risk_category,
                func.count(ArticleFactCheck.id).label("article_count"),
                func.avg(ArticleFactCheck.credibility_score).label("avg_credibility_score"),
                # Count FALSE and MOSTLY_FALSE verdicts
                func.sum(
                    case(
                        (
                            ArticleFactCheck.verdict.in_(["FALSE", "MOSTLY_FALSE"]),
                            1,
                        ),
                        else_=0,
                    )
                ).label("false_verdict_count"),
            )
            .select_from(ArticleFactCheck)
            .join(Article, Article.id == ArticleFactCheck.article_id)
            .where(Article.created_at >= cutoff_date)
            .group_by(risk_category)
            .order_by(desc("avg_credibility_score"))
        )

        result = await self.db.execute(query)
        rows = result.mappings().all()

        # Calculate false_verdict_rate for each row
        results = []
        for row in rows:
            row_dict = dict(row)
            article_count = row_dict["article_count"]
            false_count = row_dict["false_verdict_count"] or 0
            row_dict["false_verdict_rate"] = (
                float(false_count) / article_count if article_count > 0 else 0.0
            )
            results.append(row_dict)

        return results
