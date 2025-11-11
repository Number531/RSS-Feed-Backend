"""
Analytics API Endpoints

Provides REST API endpoints for fact-check analytics including source reliability,
temporal trends, and claims statistics.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.db.session import get_db
from app.repositories.analytics_repository import AnalyticsRepository
from app.services.analytics_service import AnalyticsService
from app.services.article_analytics_service import ArticleAnalyticsService
from app.services.content_quality_service import ContentQualityService
from app.schemas.analytics import (
    AggregateStatsResponse,
    CategoryAnalyticsResponse,
    VerdictAnalyticsResponse,
    HighRiskArticlesResponse,
    SourceBreakdownResponse,
    SourceQualityResponse,
    RiskCorrelationResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/sources",
    summary="Get source reliability rankings",
    description="""
    Retrieve reliability rankings for news sources based on fact-check data.
    
    **Rankings Include:**
    - Average credibility scores (0-100)
    - Verdict distributions
    - Claims accuracy rates
    - Article counts
    
    **Use Cases:**
    - Source comparison dashboards
    - Content moderation
    - User trust indicators
    
    **Filters:**
    - `days`: Time period to analyze (1-365 days)
    - `min_articles`: Minimum articles required for inclusion (1-100)
    """,
    responses={
        200: {"description": "Source reliability data retrieved successfully"},
        400: {"description": "Invalid parameters (validation error)"},
        500: {"description": "Internal server error"},
    },
    tags=["analytics"],
)
async def get_source_reliability(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    min_articles: int = Query(
        5, ge=1, le=100, description="Minimum articles required for inclusion"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Get source reliability rankings.

    Args:
        days: Number of days to look back (1-365)
        min_articles: Minimum article threshold (1-100)
        db: Database session

    Returns:
        Source reliability statistics

    Raises:
        HTTPException: 400 if parameters are invalid
        HTTPException: 500 if server error occurs
    """
    try:
        analytics_repo = AnalyticsRepository(db)
        analytics_service = AnalyticsService(analytics_repo)

        stats = await analytics_service.get_source_reliability_stats(
            days=days, min_articles=min_articles
        )

        # Format response
        return {
            "sources": stats,
            "period": {"days": days},
            "total_sources": len(stats),
            "criteria": {"min_articles": min_articles},
        }

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve source reliability: {str(e)}"
        )


@router.get(
    "/trends",
    summary="Get fact-check trends over time",
    description="""
    Retrieve temporal trends in fact-check credibility scores.
    
    **Features:**
    - Time series data (hourly/daily/weekly)
    - Filtering by source or category
    - Verdict distributions over time
    - Accuracy rate trends
    
    **Use Cases:**
    - Trend visualization charts
    - Quality monitoring dashboards
    - Historical analysis
    
    **Parameters:**
    - `days`: Time period (1-365)
    - `granularity`: Time bucket size (hourly/daily/weekly)
    - `source_id`: Optional filter by specific source UUID
    - `category`: Optional filter by content category
    """,
    responses={
        200: {"description": "Trends data retrieved successfully"},
        400: {"description": "Invalid parameters (validation error)"},
        500: {"description": "Internal server error"},
    },
    tags=["analytics"],
)
async def get_fact_check_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    granularity: str = Query(
        "daily", regex="^(hourly|daily|weekly)$", description="Time granularity"
    ),
    source_id: Optional[str] = Query(
        None, description="Filter by specific source UUID"
    ),
    category: Optional[str] = Query(None, description="Filter by article category"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get temporal fact-check trends.

    Args:
        days: Number of days (1-365)
        granularity: Time bucket size
        source_id: Optional source filter
        category: Optional category filter
        db: Database session

    Returns:
        Time series trend data

    Raises:
        HTTPException: 400 if parameters are invalid
        HTTPException: 500 if server error occurs
    """
    try:
        analytics_repo = AnalyticsRepository(db)
        analytics_service = AnalyticsService(analytics_repo)

        trends = await analytics_service.get_temporal_trends(
            source_id=source_id, category=category, days=days, granularity=granularity
        )

        # Calculate overall average
        overall_avg = 0.0
        if trends:
            total_score = sum(float(t.get("avg_score", 0)) for t in trends)
            overall_avg = round(total_score / len(trends), 1)

        # Format time series for response
        time_series = []
        for trend in trends:
            period = trend.get("period")
            if hasattr(period, "isoformat"):
                period_str = period.isoformat()
            else:
                period_str = str(period)

            # Handle None values for confidence
            avg_conf = trend.get("avg_confidence")
            avg_conf_rounded = (
                round(float(avg_conf), 2) if avg_conf is not None else 0.0
            )

            time_series.append(
                {
                    "period": period_str,
                    "articles_count": trend.get("articles_count", 0),
                    "avg_credibility_score": round(float(trend.get("avg_score", 0)), 1),
                    "avg_confidence": avg_conf_rounded,
                    "true_count": trend.get("true_count", 0),
                    "false_count": trend.get("false_count", 0),
                }
            )

        return {
            "time_series": time_series,
            "granularity": granularity,
            "filters": {"source_id": source_id, "category": category, "days": days},
            "summary": {
                "total_periods": len(time_series),
                "overall_avg_score": overall_avg,
            },
        }

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve trends: {str(e)}"
        )


@router.get(
    "/claims",
    summary="Get claims accuracy analytics",
    description="""
    Retrieve aggregate statistics on fact-checked claims.
    
    **Includes:**
    - Total claims analyzed
    - Breakdown by truth/false/misleading/unverified
    - Accuracy rates
    - Verdict distributions
    - Quality metrics
    
    **Use Cases:**
    - Overall system quality metrics
    - Claims accuracy reporting
    - API performance monitoring
    
    **Parameters:**
    - `days`: Time period (1-365)
    - `verdict`: Optional filter by specific verdict type
    """,
    responses={
        200: {"description": "Claims analytics retrieved successfully"},
        400: {"description": "Invalid parameters (validation error)"},
        500: {"description": "Internal server error"},
    },
    tags=["analytics"],
)
async def get_claims_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    verdict: Optional[str] = Query(None, description="Filter by specific verdict type"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get claims accuracy analytics.

    Args:
        days: Number of days (1-365)
        verdict: Optional verdict filter
        db: Database session

    Returns:
        Claims statistics

    Raises:
        HTTPException: 400 if parameters are invalid
        HTTPException: 500 if server error occurs
    """
    try:
        analytics_repo = AnalyticsRepository(db)
        analytics_service = AnalyticsService(analytics_repo)

        # Get claims statistics
        claims_stats = await analytics_service.get_claims_statistics(
            verdict=verdict, days=days
        )

        # Get verdict distribution
        verdict_dist = await analytics_service.get_verdict_distribution(days=days)

        # Calculate accuracy rate
        total_claims = claims_stats.get("total_claims", 0)
        claims_true = claims_stats.get("claims_true", 0)
        accuracy_rate = 0.0
        if total_claims > 0:
            accuracy_rate = round((claims_true / total_claims) * 100, 1)

        # Format verdict distribution
        formatted_verdicts = []
        for v in verdict_dist:
            formatted_verdicts.append(
                {
                    "verdict": v.get("verdict"),
                    "count": v.get("count"),
                    "avg_score": round(float(v.get("avg_score", 0)), 1),
                }
            )

        return {
            "period_days": days,
            "total_fact_checks": claims_stats.get("total_fact_checks", 0),
            "claims_summary": {
                "total_claims": total_claims,
                "claims_true": claims_true,
                "claims_false": claims_stats.get("claims_false", 0),
                "claims_misleading": claims_stats.get("claims_misleading", 0),
                "claims_unverified": claims_stats.get("claims_unverified", 0),
                "accuracy_rate": accuracy_rate,
            },
            "verdict_distribution": formatted_verdicts,
            "quality_metrics": {
                "avg_credibility_score": round(
                    float(claims_stats.get("avg_credibility") or 0), 1
                ),
                "avg_confidence": round(
                    float(claims_stats.get("avg_confidence") or 0), 2
                ),
            },
        }

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve claims analytics: {str(e)}"
        )


# === Phase 2A Endpoints ===


@router.get(
    "/stats",
    response_model=AggregateStatsResponse,
    summary="Get aggregate statistics",
    description="High-level statistics across all fact-check data including lifetime totals and monthly trends.",
)
async def get_aggregate_statistics(
    include_lifetime: bool = Query(True, description="Include lifetime statistics"),
    include_trends: bool = Query(True, description="Include month-over-month trends"),
    db: AsyncSession = Depends(get_db),
) -> AggregateStatsResponse:
    """Get aggregate statistics."""
    try:
        analytics_repo = AnalyticsRepository(db)
        analytics_service = AnalyticsService(analytics_repo)

        result = await analytics_service.get_aggregate_stats(
            include_lifetime=include_lifetime, include_trends=include_trends
        )
        return result

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving aggregate statistics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve aggregate statistics"
        )


@router.get(
    "/categories",
    response_model=CategoryAnalyticsResponse,
    summary="Get category analytics",
    description="Statistics aggregated by article category with risk levels and top sources.",
)
async def get_category_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    min_articles: int = Query(
        5, ge=1, le=100, description="Minimum articles per category"
    ),
    sort_by: str = Query("credibility", pattern="^(credibility|volume|false_rate)$"),
    db: AsyncSession = Depends(get_db),
) -> CategoryAnalyticsResponse:
    """Get category analytics."""
    try:
        analytics_repo = AnalyticsRepository(db)
        analytics_service = AnalyticsService(analytics_repo)

        result = await analytics_service.get_category_analytics(
            days=days, min_articles=min_articles, sort_by=sort_by
        )
        return result

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving category analytics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve category analytics"
        )


@router.get(
    "/verdict-details",
    response_model=VerdictAnalyticsResponse,
    summary="Get comprehensive verdict analytics",
    description="""
    Retrieve detailed verdict analytics including distribution, confidence correlations,
    temporal trends, and risk indicators.
    
    **Features:**
    - Verdict distribution with percentages and credibility scores
    - Confidence levels by verdict type (min/max/avg)
    - Daily temporal trends showing verdict patterns over time
    - Risk analysis highlighting false/misleading content
    - Overall risk level assessment
    
    **Use Cases:**
    - Content quality monitoring dashboards
    - Trend analysis and pattern detection
    - Risk assessment and alerting
    - Performance metrics for fact-checking accuracy
    
    **Parameters:**
    - `days`: Time period to analyze (1-365 days, default 30)
    
    **Response Includes:**
    - Distribution breakdown with percentages
    - Confidence statistics per verdict
    - Day-by-day verdict trends
    - False/misleading content indicators
    - Summary statistics and risk level
    """,
    responses={
        200: {"description": "Verdict analytics retrieved successfully"},
        400: {"description": "Invalid parameters (validation error)"},
        500: {"description": "Internal server error"},
    },
    tags=["analytics"],
)
async def get_verdict_details(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
) -> VerdictAnalyticsResponse:
    """Get comprehensive verdict analytics."""
    try:
        analytics_repo = AnalyticsRepository(db)
        analytics_service = AnalyticsService(analytics_repo)

        result = await analytics_service.get_verdict_analytics(days=days)
        return result

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving verdict analytics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve verdict analytics"
        )


# === New Source & Risk Endpoints ===


@router.get(
    "/high-risk-articles",
    response_model=HighRiskArticlesResponse,
    summary="Get articles with high-risk claims",
    description="""
    Retrieve articles containing high-risk claims, sorted by risk level.
    
    **Use Cases:**
    - Content moderation queues
    - Editorial review prioritization
    - Risk monitoring dashboards
    - Alerting systems
    
    **Response Includes:**
    - Article metadata (ID, title, author, URL)
    - Fact-check verdicts and scores
    - High-risk claim counts
    - Source information
    - Publication dates
    
    **Parameters:**
    - `days`: Time period (1-365 days, default 30)
    - `limit`: Max results (1-1000, default 100)
    - `offset`: Pagination offset (default 0)
    """,
    responses={
        200: {"description": "High-risk articles retrieved successfully"},
        400: {"description": "Invalid parameters"},
        500: {"description": "Internal server error"},
    },
    tags=["analytics"],
)
async def get_high_risk_articles(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
) -> HighRiskArticlesResponse:
    """Get articles with high-risk claims."""
    try:
        analytics_repo = AnalyticsRepository(db)
        analytics_service = AnalyticsService(analytics_repo)

        result = await analytics_service.get_high_risk_articles(
            days=days, limit=limit, offset=offset
        )
        return result

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving high-risk articles: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve high-risk articles"
        )


@router.get(
    "/articles/{article_id}/source-breakdown",
    response_model=SourceBreakdownResponse,
    summary="Get article source breakdown",
    description="""
    Retrieve detailed source analysis for a specific article.
    
    **Response Includes:**
    - Complete source breakdown by type (news, government, academic, social media, etc.)
    - Primary source type
    - Source diversity score (0.0-1.0 Shannon entropy)
    - Source consensus level (STRONG/MODERATE/MIXED)
    - Total unique sources count
    - Article metadata
    
    **Use Cases:**
    - Source transparency displays
    - Credibility verification
    - Editorial review
    - User trust indicators
    
    **Parameters:**
    - `article_id`: UUID of the article
    """,
    responses={
        200: {"description": "Source breakdown retrieved successfully"},
        404: {"description": "Article not found or no fact-check available"},
        500: {"description": "Internal server error"},
    },
    tags=["analytics"],
)
async def get_article_source_breakdown(
    article_id: str,
    db: AsyncSession = Depends(get_db),
) -> SourceBreakdownResponse:
    """Get source breakdown for a specific article."""
    try:
        analytics_repo = AnalyticsRepository(db)
        analytics_service = AnalyticsService(analytics_repo)

        result = await analytics_service.get_source_breakdown(article_id=article_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Article {article_id} not found or has no fact-check data",
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving source breakdown for {article_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve source breakdown"
        )


@router.get(
    "/source-quality",
    response_model=SourceQualityResponse,
    summary="Get source quality metrics",
    description="""
    Retrieve aggregate quality metrics grouped by source type.
    
    **Metrics Include:**
    - Average credibility scores by source type
    - Average number of sources per article
    - Source diversity scores
    - Article counts per source type
    - Overall weighted averages
    
    **Source Types:**
    - news
    - government
    - academic
    - social_media
    - fact_checking
    - expert
    - press_release
    - other
    
    **Use Cases:**
    - Source type comparison dashboards
    - Quality benchmarking
    - Editorial guidelines
    - Content strategy
    
    **Parameters:**
    - `days`: Time period (1-365 days, default 30)
    """,
    responses={
        200: {"description": "Source quality metrics retrieved successfully"},
        400: {"description": "Invalid parameters"},
        500: {"description": "Internal server error"},
    },
    tags=["analytics"],
)
async def get_source_quality(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
) -> SourceQualityResponse:
    """Get source quality metrics by type."""
    try:
        analytics_repo = AnalyticsRepository(db)
        analytics_service = AnalyticsService(analytics_repo)

        result = await analytics_service.get_source_quality(days=days)
        return result

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving source quality metrics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve source quality metrics"
        )


@router.get(
    "/risk-correlation",
    response_model=RiskCorrelationResponse,
    summary="Get risk vs credibility correlation",
    description="""
    Analyze the relationship between high-risk claims and article credibility.
    
    **Analysis Includes:**
    - Statistics by risk level (low/medium/high)
    - Average credibility scores per risk category
    - False verdict rates by risk level
    - Article counts per category
    - Correlation insights
    
    **Insights:**
    - Whether high-risk claims indicate lower credibility
    - False information patterns
    - Risk-based content moderation thresholds
    
    **Use Cases:**
    - Risk modeling
    - Content moderation rule development
    - Quality assurance
    - Editorial policy
    
    **Parameters:**
    - `days`: Time period (1-365 days, default 30)
    """,
    responses={
        200: {"description": "Risk correlation analysis retrieved successfully"},
        400: {"description": "Invalid parameters"},
        500: {"description": "Internal server error"},
    },
    tags=["analytics"],
)
async def get_risk_correlation(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
) -> RiskCorrelationResponse:
    """Get risk vs credibility correlation analysis."""
    try:
        analytics_repo = AnalyticsRepository(db)
        analytics_service = AnalyticsService(analytics_repo)

        result = await analytics_service.get_risk_correlation(days=days)
        return result

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving risk correlation: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve risk correlation"
        )


# === Article Performance Analytics ===


@router.get(
    "/articles/{article_id}/performance",
    summary="Get article performance metrics",
    description="""
    Get comprehensive performance analytics for a specific article.
    
    **Metrics Included:**
    - View counts (total, unique, by source)
    - Engagement metrics (read time, scroll depth, completion rate)
    - Social metrics (votes, comments, bookmarks, shares)
    - Trending score and performance percentile
    
    **Authentication**: Optional (public stats available)
    
    **Cache**: Results cached for 5 minutes
    """,
    responses={
        200: {"description": "Article analytics retrieved successfully"},
        404: {"description": "Article not found"},
        500: {"description": "Internal server error"},
    },
    tags=["analytics"],
)
async def get_article_performance(
    article_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get article performance analytics."""
    try:
        service = ArticleAnalyticsService(db)
        from uuid import UUID
        analytics = await service.get_article_analytics(UUID(article_id))
        return analytics
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving article analytics for {article_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve analytics: {str(e)}",
        )


# === Content Quality Analytics ===


@router.get(
    "/content-quality",
    summary="Get content quality report",
    description="""
    Generate a comprehensive content quality analysis across articles.
    
    **Metrics Included:**
    - Quality scores (0-100) based on engagement and sentiment
    - Vote ratios and controversy scores
    - Comment and bookmark metrics
    - Aggregate statistics (averages, medians, distributions)
    - Top performing articles
    - Actionable recommendations
    
    **Quality Score Calculation:**
    - Vote Ratio (35%): Positive sentiment indicator
    - Comments (25%): Discussion engagement quality
    - Bookmarks (20%): Long-term value assessment
    - Total Votes (15%): Overall engagement
    - Controversy Penalty (5%): Polarization reduction
    
    **Use Cases:**
    - Content strategy planning
    - Editorial quality monitoring
    - Source evaluation and optimization
    - Performance benchmarking
    
    **Parameters:**
    - `days`: Analysis period (1-365 days, default 7)
    - `category`: Optional category filter
    - `min_engagement`: Minimum total engagement (votes+comments+bookmarks, default 5)
    
    **Response Includes:**
    - Quality metrics (avg/median scores, distributions)
    - Top 10 performing articles
    - Category-specific insights
    - Engagement pattern analysis
    - Strategic recommendations
    """,
    responses={
        200: {"description": "Quality report generated successfully"},
        400: {"description": "Invalid parameters"},
        500: {"description": "Internal server error"},
    },
    tags=["analytics"],
)
async def get_content_quality_report(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    category: Optional[str] = Query(None, description="Filter by article category"),
    min_engagement: int = Query(5, ge=1, le=100, description="Minimum engagement threshold"),
    db: AsyncSession = Depends(get_db),
):
    """Get content quality report."""
    try:
        service = ContentQualityService(db)
        report = await service.get_quality_report(
            days=days,
            category=category,
            min_engagement=min_engagement
        )
        return report
    except Exception as e:
        logger.error(f"Error generating content quality report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate quality report: {str(e)}",
        )
