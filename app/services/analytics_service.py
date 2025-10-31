"""
Analytics Service Module

Provides business logic for fact-check analytics including source reliability,
temporal trends, claims statistics, and verdict distribution.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.base_service import BaseService
from app.repositories.analytics_repository import AnalyticsRepository
from app.core.exceptions import ValidationError

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
        self,
        days: int = 30,
        min_articles: int = 5
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
        self.log_operation(
            "get_source_reliability_stats",
            days=days,
            min_articles=min_articles
        )
        
        # Validate parameters
        if days < 1 or days > 365:
            raise ValidationError("Days parameter must be between 1 and 365")
        
        if min_articles < 1 or min_articles > 100:
            raise ValidationError("min_articles parameter must be between 1 and 100")
        
        try:
            stats = await self.analytics_repo.get_source_reliability_stats(
                days=days,
                min_articles=min_articles
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
        granularity: str = 'daily'
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
            granularity=granularity
        )
        
        # Validate parameters
        if days < 1 or days > 365:
            raise ValidationError("Days parameter must be between 1 and 365")
        
        valid_granularities = {'hourly', 'daily', 'weekly'}
        if granularity not in valid_granularities:
            raise ValidationError(
                f"Granularity must be one of: {', '.join(valid_granularities)}"
            )
        
        # Validate granularity makes sense for time period
        if granularity == 'hourly' and days > 7:
            raise ValidationError("Hourly granularity is only supported for up to 7 days")
        
        try:
            trends = await self.analytics_repo.get_temporal_trends(
                source_id=source_id,
                category=category,
                days=days,
                granularity=granularity
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
        self,
        verdict: Optional[str] = None,
        days: int = 30
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
        self.log_operation(
            "get_claims_statistics",
            verdict=verdict,
            days=days
        )
        
        # Validate parameters
        if days < 1 or days > 365:
            raise ValidationError("Days parameter must be between 1 and 365")
        
        if verdict:
            valid_verdicts = {
                'TRUE', 'FALSE', 'MIXED', 
                'MOSTLY_TRUE', 'MOSTLY_FALSE',
                'MISLEADING', 'UNVERIFIED'
            }
            if verdict.upper() not in valid_verdicts:
                raise ValidationError(
                    f"Verdict must be one of: {', '.join(valid_verdicts)}"
                )
            verdict = verdict.upper()
        
        try:
            stats = await self.analytics_repo.get_claims_statistics(
                verdict=verdict,
                days=days
            )
            
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
                    "avg_confidence": None
                }
            
            logger.info(
                f"Retrieved claims statistics: "
                f"{stats.get('total_fact_checks', 0)} fact-checks"
            )
            return stats
            
        except Exception as e:
            self.log_error("get_claims_statistics", e)
            raise
    
    async def get_verdict_distribution(
        self,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get distribution of verdicts.
        
        Args:
            days: Number of days to look back (1-365)
            
        Returns:
            List of verdict counts with average scores
            
        Raises:
            ValidationError: If parameters are invalid
        """
        self.log_operation(
            "get_verdict_distribution",
            days=days
        )
        
        # Validate parameters
        if days < 1 or days > 365:
            raise ValidationError("Days parameter must be between 1 and 365")
        
        try:
            distribution = await self.analytics_repo.get_verdict_distribution(
                days=days
            )
            
            logger.info(
                f"Retrieved verdict distribution: "
                f"{len(distribution)} verdict types for {days} days"
            )
            return distribution
            
        except Exception as e:
            self.log_error("get_verdict_distribution", e)
            raise
    
    async def get_analytics_summary(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
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
                source_stats_task,
                claims_stats_task,
                verdict_dist_task,
                return_exceptions=False
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
                    "avg_confidence": claims_stats.get("avg_confidence")
                }
            }
            
            logger.info(f"Generated comprehensive analytics summary for {days} days")
            return summary
            
        except Exception as e:
            self.log_error("get_analytics_summary", e)
            raise
