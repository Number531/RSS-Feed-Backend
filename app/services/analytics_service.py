"""
Analytics Service Module

Provides business logic for fact-check analytics including source reliability,
temporal trends, claims statistics, and verdict distribution.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.exceptions import ValidationError
from app.repositories.analytics_repository import AnalyticsRepository
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class AnalyticsService(BaseService):
    """
    Service for fact-check analytics operations.

    Handles:
    - Source reliability statistics
    - Temporal trend analysis
    - Claims statistics aggregation
    - Verdict distribution analysis
    - Input validation and error handling
    """

    def __init__(self, analytics_repo: AnalyticsRepository):
        """
        Initialize analytics service.

        Args:
            analytics_repo: AnalyticsRepository instance
        """
        super().__init__()
        self.analytics_repo = analytics_repo

    async def get_source_reliability_stats(
        self, days: int = 30, min_articles: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get reliability statistics for news sources.

        Args:
            days: Number of days to look back (1-365)
            min_articles: Minimum articles required for inclusion (1-100)

        Returns:
            List of source reliability statistics

        Raises:
            ValidationError: If parameters are invalid
        """
        self.log_operation("get_source_reliability_stats", days=days, min_articles=min_articles)

        # Validate parameters
        if days < 1 or days > 365:
            raise ValidationError("Days parameter must be between 1 and 365")

        if min_articles < 1 or min_articles > 100:
            raise ValidationError("min_articles parameter must be between 1 and 100")

        try:
            stats = await self.analytics_repo.get_source_reliability_stats(
                days=days, min_articles=min_articles
            )

            logger.info(f"Retrieved {len(stats)} source reliability stats for {days} days")
            return stats

        except Exception as e:
            self.log_error("get_source_reliability_stats", e)
            raise

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
            source_id: Optional filter by specific source UUID
            category: Optional filter by category
            days: Number of days to look back (1-365)
            granularity: Time granularity ('hourly', 'daily', 'weekly')

        Returns:
            List of temporal trend data points

        Raises:
            ValidationError: If parameters are invalid
        """
        self.log_operation(
            "get_temporal_trends",
            source_id=source_id,
            category=category,
            days=days,
            granularity=granularity,
        )

        # Validate parameters
        if days < 1 or days > 365:
            raise ValidationError("Days parameter must be between 1 and 365")

        valid_granularities = {"hourly", "daily", "weekly"}
        if granularity not in valid_granularities:
            raise ValidationError(f"Granularity must be one of: {', '.join(valid_granularities)}")

        # Validate granularity makes sense for time period
        if granularity == "hourly" and days > 7:
            raise ValidationError("Hourly granularity is only supported for up to 7 days")

        try:
            trends = await self.analytics_repo.get_temporal_trends(
                source_id=source_id, category=category, days=days, granularity=granularity
            )

            logger.info(
                f"Retrieved {len(trends)} temporal trends "
                f"(granularity={granularity}, days={days})"
            )
            return trends

        except Exception as e:
            self.log_error("get_temporal_trends", e)
            raise

    async def get_claims_statistics(
        self, verdict: Optional[str] = None, days: int = 30
    ) -> Dict[str, Any]:
        """
        Get aggregate claims statistics.

        Args:
            verdict: Optional filter by specific verdict
            days: Number of days to look back (1-365)

        Returns:
            Dictionary with claims statistics

        Raises:
            ValidationError: If parameters are invalid
        """
        self.log_operation("get_claims_statistics", verdict=verdict, days=days)

        # Validate parameters
        if days < 1 or days > 365:
            raise ValidationError("Days parameter must be between 1 and 365")

        if verdict:
            valid_verdicts = {
                "TRUE",
                "FALSE",
                "MIXED",
                "MOSTLY_TRUE",
                "MOSTLY_FALSE",
                "MISLEADING",
                "UNVERIFIED",
            }
            if verdict.upper() not in valid_verdicts:
                raise ValidationError(f"Verdict must be one of: {', '.join(valid_verdicts)}")
            verdict = verdict.upper()

        try:
            stats = await self.analytics_repo.get_claims_statistics(verdict=verdict, days=days)

            # Handle empty result
            if not stats:
                logger.info(f"No claims statistics found for {days} days")
                return {
                    "total_fact_checks": 0,
                    "total_claims": 0,
                    "claims_true": 0,
                    "claims_false": 0,
                    "claims_misleading": 0,
                    "claims_unverified": 0,
                    "avg_credibility": None,
                    "avg_confidence": None,
                }

            logger.info(
                f"Retrieved claims statistics: " f"{stats.get('total_fact_checks', 0)} fact-checks"
            )
            return stats

        except Exception as e:
            self.log_error("get_claims_statistics", e)
            raise

    async def get_verdict_distribution(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get distribution of verdicts.

        Args:
            days: Number of days to look back (1-365)

        Returns:
            List of verdict counts with average scores

        Raises:
            ValidationError: If parameters are invalid
        """
        self.log_operation("get_verdict_distribution", days=days)

        # Validate parameters
        if days < 1 or days > 365:
            raise ValidationError("Days parameter must be between 1 and 365")

        try:
            distribution = await self.analytics_repo.get_verdict_distribution(days=days)

            logger.info(
                f"Retrieved verdict distribution: "
                f"{len(distribution)} verdict types for {days} days"
            )
            return distribution

        except Exception as e:
            self.log_error("get_verdict_distribution", e)
            raise

    async def get_analytics_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive analytics summary including all metrics.

        This is a convenience method that fetches multiple analytics
        in a single call for dashboard views.

        Args:
            days: Number of days to look back (1-365)

        Returns:
            Dictionary containing all analytics data

        Raises:
            ValidationError: If parameters are invalid
        """
        self.log_operation("get_analytics_summary", days=days)

        # Validate parameters
        if days < 1 or days > 365:
            raise ValidationError("Days parameter must be between 1 and 365")

        try:
            # Fetch all analytics concurrently for better performance
            import asyncio

            source_stats_task = self.get_source_reliability_stats(days=days)
            claims_stats_task = self.get_claims_statistics(days=days)
            verdict_dist_task = self.get_verdict_distribution(days=days)

            source_stats, claims_stats, verdict_dist = await asyncio.gather(
                source_stats_task, claims_stats_task, verdict_dist_task, return_exceptions=False
            )

            summary = {
                "period_days": days,
                "generated_at": datetime.utcnow().isoformat(),
                "source_reliability": source_stats,
                "claims_statistics": claims_stats,
                "verdict_distribution": verdict_dist,
                "summary_metrics": {
                    "total_sources_analyzed": len(source_stats),
                    "total_fact_checks": claims_stats.get("total_fact_checks", 0),
                    "avg_credibility_score": claims_stats.get("avg_credibility"),
                    "avg_confidence": claims_stats.get("avg_confidence"),
                },
            }

            logger.info(f"Generated comprehensive analytics summary for {days} days")
            return summary

        except Exception as e:
            self.log_error("get_analytics_summary", e)
            raise

    # === Phase 2A Methods ===

    async def get_aggregate_stats(
        self, include_lifetime: bool = True, include_trends: bool = True
    ) -> Dict[str, Any]:
        """
        Get high-level aggregate statistics across all data.

        Args:
            include_lifetime: Include lifetime statistics
            include_trends: Include month-over-month trend data

        Returns:
            Dictionary with aggregate statistics
        """
        self.log_operation(
            "get_aggregate_stats", include_lifetime=include_lifetime, include_trends=include_trends
        )

        try:
            stats = await self.analytics_repo.get_aggregate_statistics()

            response: Dict[str, Any] = {}

            # Lifetime statistics
            if include_lifetime and stats.get("lifetime"):
                lifetime = stats["lifetime"]
                response["lifetime"] = {
                    "articles_fact_checked": int(lifetime.get("total_fact_checks", 0)),
                    "sources_monitored": int(lifetime.get("sources_monitored", 0)),
                    "claims_verified": int(lifetime.get("total_claims", 0) or 0),
                    "overall_credibility": float(lifetime.get("avg_credibility", 0) or 0),
                }

            # Current month statistics
            if stats.get("current_month"):
                current = stats["current_month"]
                response["this_month"] = {
                    "articles_fact_checked": int(current.get("articles_this_month", 0)),
                    "avg_credibility": float(current.get("avg_credibility_this_month", 0) or 0),
                }

                # Calculate trends if requested
                if include_trends:
                    # Initialize with null fallback values
                    response["this_month"]["volume_change"] = None
                    response["this_month"]["credibility_change"] = None
                    
                    # Calculate actual values if previous month data exists
                    if stats.get("previous_month"):
                        prev = stats["previous_month"]
                        prev_count = int(prev.get("articles_last_month", 0))
                        curr_count = int(current.get("articles_this_month", 0))

                        # Calculate volume change with division by zero protection
                        if prev_count > 0:
                            volume_change = ((curr_count - prev_count) / prev_count) * 100
                            response["this_month"]["volume_change"] = f"{volume_change:+.1f}%"

                        prev_cred = float(prev.get("avg_credibility_last_month", 0) or 0)
                        curr_cred = float(current.get("avg_credibility_this_month", 0) or 0)

                        # Calculate credibility change with division by zero protection
                        if prev_cred > 0:
                            cred_change = ((curr_cred - prev_cred) / prev_cred) * 100
                            response["this_month"]["credibility_change"] = f"{cred_change:+.1f}%"

            # Generate milestones
            if include_lifetime and stats.get("lifetime"):
                milestones = []
                lifetime = stats["lifetime"]

                fact_checks = int(lifetime.get("total_fact_checks", 0))
                if fact_checks >= 10000:
                    milestones.append("10,000+ articles fact-checked")
                elif fact_checks >= 5000:
                    milestones.append("5,000+ articles fact-checked")
                elif fact_checks >= 1000:
                    milestones.append("1,000+ articles fact-checked")

                sources = int(lifetime.get("sources_monitored", 0))
                if sources >= 50:
                    milestones.append("50+ sources monitored")
                elif sources >= 25:
                    milestones.append("25+ sources monitored")

                response["milestones"] = milestones

            logger.info("Retrieved aggregate statistics")
            return response

        except Exception as e:
            self.log_error("get_aggregate_stats", e)
            raise

    async def get_category_analytics(
        self, days: int = 30, min_articles: int = 5, sort_by: str = "credibility"
    ) -> Dict[str, Any]:
        """
        Get statistics aggregated by article category.

        Args:
            days: Number of days to look back (1-365)
            min_articles: Minimum articles required for inclusion (1-100)
            sort_by: Sort field ('credibility', 'volume', 'false_rate')

        Returns:
            Dictionary with category analytics

        Raises:
            ValidationError: If parameters are invalid
        """
        self.log_operation(
            "get_category_analytics", days=days, min_articles=min_articles, sort_by=sort_by
        )

        # Validate parameters
        if days < 1 or days > 365:
            raise ValidationError("Days parameter must be between 1 and 365")

        if min_articles < 1 or min_articles > 100:
            raise ValidationError("min_articles parameter must be between 1 and 100")

        valid_sort_fields = {"credibility", "volume", "false_rate"}
        if sort_by not in valid_sort_fields:
            raise ValidationError(f"sort_by must be one of: {', '.join(valid_sort_fields)}")

        try:
            categories = await self.analytics_repo.get_category_statistics(
                days=days, min_articles=min_articles
            )

            # Transform and enrich data
            enriched_categories = []
            for cat in categories:
                articles_count = int(cat.get("articles_count", 0))
                false_count = int(cat.get("false_count", 0))
                misleading_count = int(cat.get("misleading_count", 0))

                # Calculate false rate
                false_rate = 0.0
                if articles_count > 0:
                    false_rate = (false_count + misleading_count) / articles_count

                # Determine risk level
                risk_level = "low"
                if false_rate >= 0.5:
                    risk_level = "critical"
                elif false_rate >= 0.3:
                    risk_level = "high"
                elif false_rate >= 0.15:
                    risk_level = "medium"

                # Get top 3 sources
                sources = cat.get("sources", [])
                top_sources = sources[:3] if sources else []

                enriched_categories.append(
                    {
                        "category": cat.get("category"),
                        "articles_count": articles_count,
                        "avg_credibility": float(cat.get("avg_credibility", 0) or 0),
                        "false_rate": round(false_rate, 3),
                        "risk_level": risk_level,
                        "top_sources": top_sources,
                    }
                )

            # Apply sorting
            if sort_by == "volume":
                enriched_categories.sort(key=lambda x: x["articles_count"], reverse=True)
            elif sort_by == "false_rate":
                enriched_categories.sort(key=lambda x: x["false_rate"], reverse=True)
            # 'credibility' is already sorted by default from repository

            response = {
                "categories": enriched_categories,
                "total_categories": len(enriched_categories),
                "period": {
                    "days": days,
                    "start_date": (datetime.utcnow() - timedelta(days=days)).isoformat(),
                    "end_date": datetime.utcnow().isoformat(),
                },
                "criteria": {"min_articles": min_articles, "sort_by": sort_by},
            }

            logger.info(f"Retrieved {len(enriched_categories)} category analytics for {days} days")
            return response

        except Exception as e:
            self.log_error("get_category_analytics", e)
            raise

    async def get_verdict_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive verdict analytics including distribution, confidence,
        trends, and risk indicators.

        Args:
            days: Number of days to look back (1-365)

        Returns:
            Dictionary with verdict analytics data

        Raises:
            ValidationError: If parameters are invalid
        """
        self.log_operation("get_verdict_analytics", days=days)

        # Validate parameters
        if days < 1 or days > 365:
            raise ValidationError("Days parameter must be between 1 and 365")

        try:
            # Fetch all data sequentially (SQLAlchemy async sessions don't support concurrent operations)
            # Note: Cannot use asyncio.gather() here due to SQLAlchemy session limitation
            distribution = await self.analytics_repo.get_verdict_distribution(days=days)
            confidence_data = await self.analytics_repo.get_verdict_confidence_correlation(days=days)
            trends_data = await self.analytics_repo.get_verdict_temporal_trends(days=days)
            risk_verdicts = await self.analytics_repo.get_high_risk_verdicts(days=days)

            # Process verdict distribution with enriched data
            total_verdicts = sum(v.get("count", 0) for v in distribution)
            enriched_distribution = []

            for verdict in distribution:
                count = int(verdict.get("count", 0))
                percentage = (count / total_verdicts * 100) if total_verdicts > 0 else 0.0

                enriched_distribution.append(
                    {
                        "verdict": verdict.get("verdict"),
                        "count": count,
                        "percentage": round(percentage, 2),
                        "avg_credibility_score": round(float(verdict.get("avg_score", 0) or 0), 1),
                    }
                )

            # Process confidence correlation
            confidence_by_verdict = {}
            for conf in confidence_data:
                verdict = conf.get("verdict")
                confidence_by_verdict[verdict] = {
                    "avg_confidence": round(float(conf.get("avg_confidence", 0) or 0), 3),
                    "min_confidence": round(float(conf.get("min_confidence", 0) or 0), 3),
                    "max_confidence": round(float(conf.get("max_confidence", 0) or 0), 3),
                    "sample_size": int(conf.get("count", 0)),
                }

            # Process temporal trends - group by date
            trends_by_date = {}
            for trend in trends_data:
                date = trend.get("date")
                if hasattr(date, "isoformat"):
                    date_str = date.date().isoformat()
                else:
                    date_str = str(date).split()[0]  # Extract date part

                if date_str not in trends_by_date:
                    trends_by_date[date_str] = {}

                verdict = trend.get("verdict")
                count = int(trend.get("count", 0))
                trends_by_date[date_str][verdict] = count

            # Convert to list format sorted by date
            verdict_trends = [
                {"date": date, "verdicts": verdicts}
                for date, verdicts in sorted(trends_by_date.items())
            ]

            # Process risk indicators
            risk_indicators = []
            for risk in risk_verdicts:
                risk_indicators.append(
                    {
                        "verdict": risk.get("verdict"),
                        "count": int(risk.get("count", 0)),
                        "avg_credibility": round(float(risk.get("avg_credibility", 0) or 0), 1),
                        "avg_confidence": round(float(risk.get("avg_confidence", 0) or 0), 3),
                    }
                )

            # Calculate summary statistics
            total_false_misleading = sum(r.get("count", 0) for r in risk_indicators)
            risk_percentage = (
                (total_false_misleading / total_verdicts * 100) if total_verdicts > 0 else 0.0
            )

            # Determine overall risk level
            overall_risk = "low"
            if risk_percentage >= 40:
                overall_risk = "critical"
            elif risk_percentage >= 25:
                overall_risk = "high"
            elif risk_percentage >= 15:
                overall_risk = "medium"

            response = {
                "period": {
                    "days": days,
                    "start_date": (datetime.utcnow() - timedelta(days=days)).isoformat(),
                    "end_date": datetime.utcnow().isoformat(),
                },
                "verdict_distribution": enriched_distribution,
                "confidence_by_verdict": confidence_by_verdict,
                "temporal_trends": verdict_trends,
                "risk_indicators": {
                    "false_misleading_verdicts": risk_indicators,
                    "total_risk_count": total_false_misleading,
                    "risk_percentage": round(risk_percentage, 2),
                    "overall_risk_level": overall_risk,
                },
                "summary": {
                    "total_verdicts": total_verdicts,
                    "unique_verdict_types": len(distribution),
                    "most_common_verdict": distribution[0].get("verdict") if distribution else None,
                },
            }

            logger.info(
                f"Generated verdict analytics for {days} days: "
                f"{total_verdicts} total verdicts, risk level {overall_risk}"
            )
            return response

        except Exception as e:
            self.log_error("get_verdict_analytics", e)
            raise
