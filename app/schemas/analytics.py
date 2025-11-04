"""
Analytics API Response Schemas

Pydantic models for analytics endpoint responses including source reliability,
temporal trends, claims statistics, and verdict distributions.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VerdictDistribution(BaseModel):
    """Verdict distribution counts."""

    TRUE: int = Field(default=0, description="Count of TRUE verdicts")
    FALSE: int = Field(default=0, description="Count of FALSE verdicts")
    MIXED: int = Field(default=0, description="Count of MIXED verdicts")
    MOSTLY_TRUE: int = Field(default=0, description="Count of MOSTLY_TRUE verdicts")
    MOSTLY_FALSE: int = Field(default=0, description="Count of MOSTLY_FALSE verdicts")
    MISLEADING: int = Field(default=0, description="Count of MISLEADING verdicts")
    UNVERIFIED: int = Field(default=0, description="Count of UNVERIFIED verdicts")


class SourceReliabilityItem(BaseModel):
    """Individual source reliability statistics."""

    source_id: str = Field(..., description="Source UUID")
    source_name: str = Field(..., description="Source display name")
    category: str = Field(..., description="Content category")
    articles_count: int = Field(..., description="Number of articles analyzed")
    avg_credibility_score: float = Field(..., description="Average credibility score (0-100)")
    avg_confidence: float = Field(..., description="Average confidence level (0-1)")
    verdict_distribution: Dict[str, int] = Field(..., description="Breakdown by verdict type")
    total_claims: Optional[int] = Field(None, description="Total claims analyzed")
    claims_accuracy: Optional[float] = Field(None, description="Claims accuracy percentage")


class SourceReliabilityResponse(BaseModel):
    """Response for GET /analytics/sources endpoint."""

    sources: List[SourceReliabilityItem] = Field(..., description="List of source statistics")
    period: Dict[str, Any] = Field(..., description="Time period analyzed")
    total_sources: int = Field(..., description="Total number of sources")
    criteria: Dict[str, int] = Field(..., description="Filtering criteria applied")

    class Config:
        json_schema_extra = {
            "example": {
                "sources": [
                    {
                        "source_id": "550e8400-e29b-41d4-a716-446655440000",
                        "source_name": "Example News",
                        "category": "politics",
                        "articles_count": 50,
                        "avg_credibility_score": 75.5,
                        "avg_confidence": 0.85,
                        "verdict_distribution": {
                            "TRUE": 30,
                            "FALSE": 5,
                            "MIXED": 10,
                            "MOSTLY_TRUE": 5,
                            "MOSTLY_FALSE": 0,
                            "MISLEADING": 0,
                            "UNVERIFIED": 0,
                        },
                        "total_claims": 150,
                        "claims_accuracy": 78.5,
                    }
                ],
                "period": {
                    "days": 30,
                    "start": "2025-10-01T00:00:00Z",
                    "end": "2025-10-31T00:00:00Z",
                },
                "total_sources": 5,
                "criteria": {"min_articles": 5},
            }
        }


class TimeSeriesDataPoint(BaseModel):
    """Single time series data point for trends."""

    period: str = Field(..., description="Time period (ISO 8601 format)")
    articles_count: int = Field(..., description="Number of articles in period")
    avg_credibility_score: float = Field(..., description="Average credibility score")
    avg_confidence: float = Field(..., description="Average confidence level")
    true_count: int = Field(..., description="TRUE verdicts count")
    false_count: int = Field(..., description="FALSE verdicts count")
    accuracy_rate: Optional[float] = Field(None, description="Accuracy rate percentage")


class TrendsResponse(BaseModel):
    """Response for GET /analytics/trends endpoint."""

    time_series: List[TimeSeriesDataPoint] = Field(..., description="Time series data points")
    granularity: str = Field(..., description="Time granularity (hourly/daily/weekly)")
    filters: Dict[str, Any] = Field(..., description="Applied filters")
    summary: Dict[str, Any] = Field(..., description="Summary statistics")

    class Config:
        json_schema_extra = {
            "example": {
                "time_series": [
                    {
                        "period": "2025-10-30T00:00:00Z",
                        "articles_count": 10,
                        "avg_credibility_score": 70.0,
                        "avg_confidence": 0.80,
                        "true_count": 6,
                        "false_count": 4,
                        "accuracy_rate": 60.0,
                    }
                ],
                "granularity": "daily",
                "filters": {"source_id": None, "category": None, "days": 7},
                "summary": {"total_periods": 7, "overall_avg_score": 72.5},
            }
        }


class ClaimsSummary(BaseModel):
    """Claims summary statistics."""

    total_claims: int = Field(..., description="Total claims analyzed")
    claims_true: int = Field(..., description="Claims verified as true")
    claims_false: int = Field(..., description="Claims verified as false")
    claims_misleading: int = Field(..., description="Claims marked as misleading")
    claims_unverified: int = Field(..., description="Claims that couldn't be verified")
    accuracy_rate: float = Field(..., description="Overall accuracy percentage")


class VerdictDistributionItem(BaseModel):
    """Verdict distribution item with statistics."""

    verdict: str = Field(..., description="Verdict type")
    count: int = Field(..., description="Number of occurrences")
    avg_score: float = Field(..., description="Average credibility score")


class QualityMetrics(BaseModel):
    """Quality metrics for fact-checks."""

    avg_credibility_score: float = Field(..., description="Average credibility score")
    avg_confidence: float = Field(..., description="Average confidence level")


class ClaimsAnalyticsResponse(BaseModel):
    """Response for GET /analytics/claims endpoint."""

    period_days: int = Field(..., description="Number of days analyzed")
    total_fact_checks: int = Field(..., description="Total fact-checks performed")
    claims_summary: ClaimsSummary = Field(..., description="Claims statistics")
    verdict_distribution: List[VerdictDistributionItem] = Field(
        ..., description="Verdict breakdown"
    )
    quality_metrics: QualityMetrics = Field(..., description="Quality indicators")

    class Config:
        json_schema_extra = {
            "example": {
                "period_days": 30,
                "total_fact_checks": 100,
                "claims_summary": {
                    "total_claims": 300,
                    "claims_true": 180,
                    "claims_false": 80,
                    "claims_misleading": 20,
                    "claims_unverified": 20,
                    "accuracy_rate": 60.0,
                },
                "verdict_distribution": [
                    {"verdict": "TRUE", "count": 60, "avg_score": 85.0},
                    {"verdict": "FALSE", "count": 20, "avg_score": 35.0},
                ],
                "quality_metrics": {"avg_credibility_score": 72.5, "avg_confidence": 0.85},
            }
        }


class AnalyticsSummaryResponse(BaseModel):
    """Response for comprehensive analytics summary."""

    period_days: int = Field(..., description="Number of days analyzed")
    generated_at: str = Field(..., description="Timestamp when summary was generated")
    source_reliability: List[SourceReliabilityItem] = Field(..., description="Source statistics")
    claims_statistics: Dict[str, Any] = Field(..., description="Claims data")
    verdict_distribution: List[VerdictDistributionItem] = Field(
        ..., description="Verdict breakdown"
    )
    summary_metrics: Dict[str, Any] = Field(..., description="Overall metrics")


# === Phase 2A Schemas ===


class LifetimeStats(BaseModel):
    """Lifetime aggregate statistics."""

    articles_fact_checked: int = Field(..., description="Total articles fact-checked")
    sources_monitored: int = Field(..., description="Number of sources monitored")
    claims_verified: int = Field(..., description="Total claims verified")
    overall_credibility: float = Field(..., description="Overall credibility score")


class CurrentPeriodStats(BaseModel):
    """Current period statistics with trends."""

    articles_fact_checked: int = Field(..., description="Articles this period")
    avg_credibility: float = Field(..., description="Average credibility")
    volume_change: Optional[str] = Field(None, description="Volume change percentage")
    credibility_change: Optional[str] = Field(None, description="Credibility change percentage")


class AggregateStatsResponse(BaseModel):
    """Response for aggregate statistics endpoint."""

    lifetime: Optional[LifetimeStats] = Field(None, description="Lifetime statistics")
    this_month: CurrentPeriodStats = Field(..., description="Current month stats")
    milestones: List[str] = Field(default_factory=list, description="Achievement milestones")


class CategoryAnalytics(BaseModel):
    """Analytics for a single category."""

    category: str = Field(..., description="Category name")
    articles_count: int = Field(..., description="Number of articles")
    avg_credibility: float = Field(..., description="Average credibility score")
    false_rate: float = Field(..., description="False content rate")
    risk_level: str = Field(..., description="Risk level (low/medium/high/critical)")
    top_sources: List[str] = Field(..., description="Top sources in category")


class CategoryAnalyticsResponse(BaseModel):
    """Response for category analytics endpoint."""

    categories: List[CategoryAnalytics] = Field(..., description="Category statistics")
    total_categories: int = Field(..., description="Number of categories")
    period: Dict[str, Any] = Field(..., description="Analysis period")
    criteria: Dict[str, Any] = Field(..., description="Filtering criteria")


# === Verdict Analytics Schemas ===


class VerdictDistributionDetail(BaseModel):
    """Detailed verdict distribution item."""

    verdict: str = Field(..., description="Verdict type")
    count: int = Field(..., description="Number of occurrences")
    percentage: float = Field(..., description="Percentage of total verdicts")
    avg_credibility_score: float = Field(..., description="Average credibility score")


class ConfidenceStatistics(BaseModel):
    """Confidence statistics for a verdict."""

    avg_confidence: float = Field(..., description="Average confidence level")
    min_confidence: float = Field(..., description="Minimum confidence level")
    max_confidence: float = Field(..., description="Maximum confidence level")
    sample_size: int = Field(..., description="Number of samples")


class VerdictTrendDataPoint(BaseModel):
    """Single data point in verdict temporal trends."""

    date: str = Field(..., description="Date in ISO format")
    verdicts: Dict[str, int] = Field(..., description="Verdict counts for this date")


class RiskVerdictItem(BaseModel):
    """High-risk verdict item."""

    verdict: str = Field(..., description="Verdict type")
    count: int = Field(..., description="Number of occurrences")
    avg_credibility: float = Field(..., description="Average credibility score")
    avg_confidence: float = Field(..., description="Average confidence level")


class RiskIndicators(BaseModel):
    """Risk indicators for false/misleading content."""

    false_misleading_verdicts: List[RiskVerdictItem] = Field(
        ..., description="False/misleading verdict details"
    )
    total_risk_count: int = Field(..., description="Total false/misleading verdicts")
    risk_percentage: float = Field(..., description="Percentage of risky verdicts")
    overall_risk_level: str = Field(..., description="Risk level (low/medium/high/critical)")


class VerdictAnalyticsSummary(BaseModel):
    """Summary statistics for verdict analytics."""

    total_verdicts: int = Field(..., description="Total number of verdicts")
    unique_verdict_types: int = Field(..., description="Number of unique verdict types")
    most_common_verdict: Optional[str] = Field(None, description="Most common verdict type")


class VerdictAnalyticsResponse(BaseModel):
    """Response for verdict analytics endpoint."""

    period: Dict[str, Any] = Field(..., description="Analysis time period")
    verdict_distribution: List[VerdictDistributionDetail] = Field(
        ..., description="Verdict distribution with percentages"
    )
    confidence_by_verdict: Dict[str, ConfidenceStatistics] = Field(
        ..., description="Confidence statistics by verdict"
    )
    temporal_trends: List[VerdictTrendDataPoint] = Field(..., description="Daily verdict trends")
    risk_indicators: RiskIndicators = Field(..., description="Risk analysis")
    summary: VerdictAnalyticsSummary = Field(..., description="Summary statistics")

    class Config:
        json_schema_extra = {
            "example": {
                "period": {
                    "days": 30,
                    "start_date": "2025-10-01T00:00:00",
                    "end_date": "2025-10-31T00:00:00",
                },
                "verdict_distribution": [
                    {
                        "verdict": "TRUE",
                        "count": 45,
                        "percentage": 45.0,
                        "avg_credibility_score": 85.5,
                    },
                    {
                        "verdict": "FALSE",
                        "count": 15,
                        "percentage": 15.0,
                        "avg_credibility_score": 25.3,
                    },
                ],
                "confidence_by_verdict": {
                    "TRUE": {
                        "avg_confidence": 0.892,
                        "min_confidence": 0.750,
                        "max_confidence": 0.990,
                        "sample_size": 45,
                    }
                },
                "temporal_trends": [
                    {"date": "2025-10-30", "verdicts": {"TRUE": 5, "FALSE": 2, "MISLEADING": 1}}
                ],
                "risk_indicators": {
                    "false_misleading_verdicts": [
                        {
                            "verdict": "FALSE",
                            "count": 15,
                            "avg_credibility": 25.3,
                            "avg_confidence": 0.812,
                        }
                    ],
                    "total_risk_count": 20,
                    "risk_percentage": 20.0,
                    "overall_risk_level": "medium",
                },
                "summary": {
                    "total_verdicts": 100,
                    "unique_verdict_types": 5,
                    "most_common_verdict": "TRUE",
                },
            }
        }


# === New Risk & Source Quality Endpoints ===


class HighRiskArticleItem(BaseModel):
    """Individual high-risk article summary."""

    id: str = Field(..., description="Article UUID")
    title: str = Field(..., description="Article title")
    high_risk_claims_count: int = Field(..., description="Number of HIGH risk claims")
    credibility_score: int = Field(..., description="Credibility score (0-100)")
    verdict: str = Field(..., description="Fact-check verdict")
    published_at: datetime = Field(..., description="Publication timestamp")
    source_name: Optional[str] = Field(None, description="RSS source name")


class HighRiskArticlesResponse(BaseModel):
    """Response for GET /articles/high-risk endpoint."""

    total: int = Field(..., description="Total high-risk articles")
    articles: List[HighRiskArticleItem] = Field(..., description="List of high-risk articles")
    filters: Dict[str, Any] = Field(..., description="Applied filters")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 8,
                "articles": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "title": "Breaking: Major political development",
                        "high_risk_claims_count": 3,
                        "credibility_score": 80,
                        "verdict": "TRUE",
                        "published_at": "2025-11-04T12:00:00Z",
                        "source_name": "Fox News Politics",
                    }
                ],
                "filters": {"min_risk_count": 1, "sort": "risk_desc"},
            }
        }


class SourceBreakdownResponse(BaseModel):
    """Response for GET /articles/{id}/source-breakdown endpoint."""

    article_id: str = Field(..., description="Article UUID")
    total_sources: int = Field(..., description="Total evidence sources used")
    breakdown: Dict[str, int] = Field(..., description="Sources by type")
    primary_source_type: Optional[str] = Field(None, description="Dominant source type")
    diversity_score: Optional[float] = Field(
        None, description="Source diversity score (0.0-1.0)"
    )
    source_consensus: Optional[str] = Field(
        None, description="Source consensus classification"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "article_id": "550e8400-e29b-41d4-a716-446655440000",
                "total_sources": 105,
                "breakdown": {"news": 30, "general": 30, "research": 30, "historical": 15},
                "primary_source_type": "news",
                "diversity_score": 0.98,
                "source_consensus": "MIXED",
            }
        }


class SourceTypeQuality(BaseModel):
    """Quality metrics for a source type."""

    type: str = Field(..., description="Source type (news/research/general/historical)")
    article_count: int = Field(..., description="Number of articles")
    avg_diversity: float = Field(..., description="Average diversity score")
    avg_credibility: float = Field(..., description="Average credibility score")
    avg_sources: float = Field(..., description="Average number of sources")


class SourceQualityResponse(BaseModel):
    """Response for GET /analytics/source-quality endpoint."""

    by_source_type: List[SourceTypeQuality] = Field(
        ..., description="Metrics by source type"
    )
    overall: Dict[str, Any] = Field(..., description="Overall statistics")
    period: Dict[str, Any] = Field(..., description="Analysis period")

    class Config:
        json_schema_extra = {
            "example": {
                "by_source_type": [
                    {
                        "type": "news",
                        "article_count": 8,
                        "avg_diversity": 0.98,
                        "avg_credibility": 80.8,
                        "avg_sources": 105.0,
                    }
                ],
                "overall": {
                    "avg_diversity": 0.98,
                    "most_common_type": "news",
                    "highly_diverse_articles": 8,
                },
                "period": {"days": 30},
            }
        }


class RiskCategory(BaseModel):
    """Risk category statistics."""

    category: str = Field(..., description="Risk category (low/medium/high)")
    article_count: int = Field(..., description="Number of articles")
    avg_credibility: float = Field(..., description="Average credibility score")
    verdict_distribution: Dict[str, int] = Field(
        ..., description="Verdict distribution"
    )


class RiskCorrelationResponse(BaseModel):
    """Response for GET /analytics/risk-correlation endpoint."""

    risk_categories: List[RiskCategory] = Field(..., description="Categories breakdown")
    insights: Dict[str, Any] = Field(..., description="Analysis insights")
    period: Dict[str, Any] = Field(..., description="Analysis period")

    class Config:
        json_schema_extra = {
            "example": {
                "risk_categories": [
                    {
                        "category": "high_risk",
                        "article_count": 8,
                        "avg_credibility": 80.8,
                        "verdict_distribution": {"TRUE": 7, "FALSE": 1},
                    },
                    {
                        "category": "low_risk",
                        "article_count": 2,
                        "avg_credibility": 0.0,
                        "verdict_distribution": {},
                    },
                ],
                "insights": {
                    "high_risk_can_be_true": True,
                    "correlation": "weak",
                    "notes": "High-risk claims don't necessarily indicate false information",
                },
                "period": {"days": 30},
            }
        }
