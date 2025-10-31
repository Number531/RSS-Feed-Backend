"""
Analytics API Endpoints

Provides REST API endpoints for fact-check analytics including source reliability,
temporal trends, and claims statistics.
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.session import get_db
from app.repositories.analytics_repository import AnalyticsRepository
from app.services.analytics_service import AnalyticsService
from app.core.exceptions import ValidationError

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
        200: {
            "description": "Source reliability data retrieved successfully"
        },
        400: {
            "description": "Invalid parameters (validation error)"
        },
        500: {
            "description": "Internal server error"
        }
    },
    tags=["analytics"]
)
async def get_source_reliability(
    days: int = Query(
        30,
        ge=1,
        le=365,
        description="Number of days to analyze"
    ),
    min_articles: int = Query(
        5,
        ge=1,
        le=100,
        description="Minimum articles required for inclusion"
    ),
    db: AsyncSession = Depends(get_db)
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
            days=days,
            min_articles=min_articles
        )
        
        # Format response
        return {
            "sources": stats,
            "period": {
                "days": days
            },
            "total_sources": len(stats),
            "criteria": {
                "min_articles": min_articles
            }
        }
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve source reliability: {str(e)}"
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
        200: {
            "description": "Trends data retrieved successfully"
        },
        400: {
            "description": "Invalid parameters (validation error)"
        },
        500: {
            "description": "Internal server error"
        }
    },
    tags=["analytics"]
)
async def get_fact_check_trends(
    days: int = Query(
        30,
        ge=1,
        le=365,
        description="Number of days to analyze"
    ),
    granularity: str = Query(
        "daily",
        regex="^(hourly|daily|weekly)$",
        description="Time granularity"
    ),
    source_id: Optional[str] = Query(
        None,
        description="Filter by specific source UUID"
    ),
    category: Optional[str] = Query(
        None,
        description="Filter by article category"
    ),
    db: AsyncSession = Depends(get_db)
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
            source_id=source_id,
            category=category,
            days=days,
            granularity=granularity
        )
        
        # Calculate overall average
        overall_avg = 0.0
        if trends:
            total_score = sum(float(t.get('avg_score', 0)) for t in trends)
            overall_avg = round(total_score / len(trends), 1)
        
        # Format time series for response
        time_series = []
        for trend in trends:
            period = trend.get('period')
            if hasattr(period, 'isoformat'):
                period_str = period.isoformat()
            else:
                period_str = str(period)
            
            # Handle None values for confidence
            avg_conf = trend.get('avg_confidence')
            avg_conf_rounded = round(float(avg_conf), 2) if avg_conf is not None else 0.0
            
            time_series.append({
                "period": period_str,
                "articles_count": trend.get('articles_count', 0),
                "avg_credibility_score": round(float(trend.get('avg_score', 0)), 1),
                "avg_confidence": avg_conf_rounded,
                "true_count": trend.get('true_count', 0),
                "false_count": trend.get('false_count', 0)
            })
        
        return {
            "time_series": time_series,
            "granularity": granularity,
            "filters": {
                "source_id": source_id,
                "category": category,
                "days": days
            },
            "summary": {
                "total_periods": len(time_series),
                "overall_avg_score": overall_avg
            }
        }
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve trends: {str(e)}"
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
        200: {
            "description": "Claims analytics retrieved successfully"
        },
        400: {
            "description": "Invalid parameters (validation error)"
        },
        500: {
            "description": "Internal server error"
        }
    },
    tags=["analytics"]
)
async def get_claims_analytics(
    days: int = Query(
        30,
        ge=1,
        le=365,
        description="Number of days to analyze"
    ),
    verdict: Optional[str] = Query(
        None,
        description="Filter by specific verdict type"
    ),
    db: AsyncSession = Depends(get_db)
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
            verdict=verdict,
            days=days
        )
        
        # Get verdict distribution
        verdict_dist = await analytics_service.get_verdict_distribution(days=days)
        
        # Calculate accuracy rate
        total_claims = claims_stats.get('total_claims', 0)
        claims_true = claims_stats.get('claims_true', 0)
        accuracy_rate = 0.0
        if total_claims > 0:
            accuracy_rate = round((claims_true / total_claims) * 100, 1)
        
        # Format verdict distribution
        formatted_verdicts = []
        for v in verdict_dist:
            formatted_verdicts.append({
                "verdict": v.get('verdict'),
                "count": v.get('count'),
                "avg_score": round(float(v.get('avg_score', 0)), 1)
            })
        
        return {
            "period_days": days,
            "total_fact_checks": claims_stats.get('total_fact_checks', 0),
            "claims_summary": {
                "total_claims": total_claims,
                "claims_true": claims_true,
                "claims_false": claims_stats.get('claims_false', 0),
                "claims_misleading": claims_stats.get('claims_misleading', 0),
                "claims_unverified": claims_stats.get('claims_unverified', 0),
                "accuracy_rate": accuracy_rate
            },
            "verdict_distribution": formatted_verdicts,
            "quality_metrics": {
                "avg_credibility_score": round(float(claims_stats.get('avg_credibility') or 0), 1),
                "avg_confidence": round(float(claims_stats.get('avg_confidence') or 0), 2)
            }
        }
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve claims analytics: {str(e)}"
        )


# === Phase 2A Endpoints ===

@router.get(
    "/stats",
    response_model=Dict[str, Any],
    summary="Get aggregate statistics",
    description="High-level statistics across all fact-check data including lifetime totals and monthly trends."
)
async def get_aggregate_statistics(
    include_lifetime: bool = Query(True, description="Include lifetime statistics"),
    include_trends: bool = Query(True, description="Include month-over-month trends"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get aggregate statistics."""
    try:
        analytics_repo = AnalyticsRepository(db)
        analytics_service = AnalyticsService(analytics_repo)
        
        result = await analytics_service.get_aggregate_stats(
            include_lifetime=include_lifetime,
            include_trends=include_trends
        )
        return result
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving aggregate statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve aggregate statistics")


@router.get(
    "/categories",
    response_model=Dict[str, Any],
    summary="Get category analytics",
    description="Statistics aggregated by article category with risk levels and top sources."
)
async def get_category_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    min_articles: int = Query(5, ge=1, le=100, description="Minimum articles per category"),
    sort_by: str = Query("credibility", pattern="^(credibility|volume|false_rate)$"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get category analytics."""
    try:
        analytics_repo = AnalyticsRepository(db)
        analytics_service = AnalyticsService(analytics_repo)
        
        result = await analytics_service.get_category_analytics(
            days=days,
            min_articles=min_articles,
            sort_by=sort_by
        )
        return result
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving category analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve category analytics")
