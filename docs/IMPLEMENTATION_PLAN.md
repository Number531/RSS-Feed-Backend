# Implementation Plan - Priority Endpoints

## Overview

This document provides a detailed, step-by-step implementation plan for the priority endpoints selected from the Future Endpoints exploration document. Each endpoint includes database changes, service layer updates, API implementation, and testing requirements.

**Selected Endpoints** (8 total):
1. Article Performance Metrics
2. Content Quality Score
3. Comment Mentions (@username)
4. Thread Subscriptions
5. User Reputation & Leaderboard
6. Enhanced RSS Feed Management
7. Cache Management
8. Enhanced Health Checks

**Estimated Timeline**: 4-6 weeks (2 sprints)
**Team Size**: 2 backend developers
**Dependencies**: PostgreSQL, Redis, existing services

---

## Table of Contents

1. [Phase 1: Analytics Endpoints](#phase-1-analytics-endpoints-week-1-2)
2. [Phase 2: Social Features](#phase-2-social-features-week-2-3)
3. [Phase 3: Infrastructure Enhancements](#phase-3-infrastructure-enhancements-week-3-4)
4. [Phase 4: Testing & Documentation](#phase-4-testing--documentation-week-4)
5. [Deployment Strategy](#deployment-strategy)
6. [Rollback Plan](#rollback-plan)

---

## Phase 1: Analytics Endpoints (Week 1-2)

### Endpoint 1: Article Performance Metrics
**Endpoint**: `GET /api/v1/articles/{article_id}/analytics`

#### Step 1.1: Database Schema Updates
**Estimated Time**: 2 hours

**New Table**: `article_analytics`
```sql
CREATE TABLE article_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    
    -- View metrics
    total_views INTEGER DEFAULT 0,
    unique_views INTEGER DEFAULT 0,
    direct_views INTEGER DEFAULT 0,
    rss_views INTEGER DEFAULT 0,
    search_views INTEGER DEFAULT 0,
    
    -- Engagement metrics
    avg_read_time_seconds INTEGER DEFAULT 0,
    avg_scroll_percentage DECIMAL(5,2) DEFAULT 0,
    completion_rate DECIMAL(5,4) DEFAULT 0,
    
    -- Social metrics (denormalized for performance)
    bookmark_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    
    -- Performance scores
    trending_score DECIMAL(5,2) DEFAULT 0,
    performance_percentile INTEGER DEFAULT 0,
    
    -- Timestamps
    last_calculated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(article_id)
);

-- Indexes for performance
CREATE INDEX idx_article_analytics_article_id ON article_analytics(article_id);
CREATE INDEX idx_article_analytics_trending_score ON article_analytics(trending_score DESC);
CREATE INDEX idx_article_analytics_performance ON article_analytics(performance_percentile DESC);
```

**Migration File**: `alembic/versions/YYYY_MM_DD_HHMM-<hash>_add_article_analytics.py`

```python
"""Add article analytics table

Revision ID: <hash>
Revises: <previous_hash>
Create Date: 2025-11-11 20:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '<hash>'
down_revision = '<previous_hash>'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'article_analytics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('article_id', UUID(as_uuid=True), sa.ForeignKey('articles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('total_views', sa.Integer(), default=0),
        sa.Column('unique_views', sa.Integer(), default=0),
        sa.Column('direct_views', sa.Integer(), default=0),
        sa.Column('rss_views', sa.Integer(), default=0),
        sa.Column('search_views', sa.Integer(), default=0),
        sa.Column('avg_read_time_seconds', sa.Integer(), default=0),
        sa.Column('avg_scroll_percentage', sa.DECIMAL(5, 2), default=0),
        sa.Column('completion_rate', sa.DECIMAL(5, 4), default=0),
        sa.Column('bookmark_count', sa.Integer(), default=0),
        sa.Column('share_count', sa.Integer(), default=0),
        sa.Column('trending_score', sa.DECIMAL(5, 2), default=0),
        sa.Column('performance_percentile', sa.Integer(), default=0),
        sa.Column('last_calculated_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
    )
    
    op.create_unique_constraint('uq_article_analytics_article_id', 'article_analytics', ['article_id'])
    op.create_index('idx_article_analytics_article_id', 'article_analytics', ['article_id'])
    op.create_index('idx_article_analytics_trending_score', 'article_analytics', ['trending_score'], postgresql_ops={'trending_score': 'DESC'})
    op.create_index('idx_article_analytics_performance', 'article_analytics', ['performance_percentile'], postgresql_ops={'performance_percentile': 'DESC'})

def downgrade():
    op.drop_index('idx_article_analytics_performance', table_name='article_analytics')
    op.drop_index('idx_article_analytics_trending_score', table_name='article_analytics')
    op.drop_index('idx_article_analytics_article_id', table_name='article_analytics')
    op.drop_table('article_analytics')
```

#### Step 1.2: Create SQLAlchemy Model
**Estimated Time**: 1 hour

**File**: `app/models/article_analytics.py`

```python
"""Article Analytics Model"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DECIMAL, Column, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class ArticleAnalytics(Base):
    """Analytics data for articles."""
    
    __tablename__ = "article_analytics"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    article_id = Column(
        PG_UUID(as_uuid=True), 
        ForeignKey("articles.id", ondelete="CASCADE"), 
        unique=True, 
        nullable=False
    )
    
    # View metrics
    total_views = Column(Integer, default=0, nullable=False)
    unique_views = Column(Integer, default=0, nullable=False)
    direct_views = Column(Integer, default=0, nullable=False)
    rss_views = Column(Integer, default=0, nullable=False)
    search_views = Column(Integer, default=0, nullable=False)
    
    # Engagement metrics
    avg_read_time_seconds = Column(Integer, default=0, nullable=False)
    avg_scroll_percentage = Column(DECIMAL(5, 2), default=Decimal("0.00"), nullable=False)
    completion_rate = Column(DECIMAL(5, 4), default=Decimal("0.0000"), nullable=False)
    
    # Social metrics
    bookmark_count = Column(Integer, default=0, nullable=False)
    share_count = Column(Integer, default=0, nullable=False)
    
    # Performance scores
    trending_score = Column(DECIMAL(5, 2), default=Decimal("0.00"), nullable=False)
    performance_percentile = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    last_calculated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    article = relationship("Article", back_populates="analytics")
```

**Update**: `app/models/article.py` - Add relationship
```python
# Add to Article model:
analytics = relationship("ArticleAnalytics", back_populates="article", uselist=False, cascade="all, delete-orphan")
```

#### Step 1.3: Create Repository Layer
**Estimated Time**: 2 hours

**File**: `app/repositories/article_analytics_repository.py`

```python
"""Repository for article analytics operations."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article_analytics import ArticleAnalytics


class ArticleAnalyticsRepository:
    """Handle database operations for article analytics."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_article_id(self, article_id: UUID) -> Optional[ArticleAnalytics]:
        """Get analytics for a specific article."""
        result = await self.db.execute(
            select(ArticleAnalytics).where(ArticleAnalytics.article_id == article_id)
        )
        return result.scalar_one_or_none()
    
    async def create_or_update(
        self,
        article_id: UUID,
        total_views: int = 0,
        unique_views: int = 0,
        direct_views: int = 0,
        rss_views: int = 0,
        search_views: int = 0,
        avg_read_time_seconds: int = 0,
        avg_scroll_percentage: float = 0.0,
        completion_rate: float = 0.0,
        bookmark_count: int = 0,
        share_count: int = 0,
        trending_score: float = 0.0,
        performance_percentile: int = 0,
    ) -> ArticleAnalytics:
        """Create or update analytics record."""
        existing = await self.get_by_article_id(article_id)
        
        if existing:
            # Update existing record
            existing.total_views = total_views
            existing.unique_views = unique_views
            existing.direct_views = direct_views
            existing.rss_views = rss_views
            existing.search_views = search_views
            existing.avg_read_time_seconds = avg_read_time_seconds
            existing.avg_scroll_percentage = avg_scroll_percentage
            existing.completion_rate = completion_rate
            existing.bookmark_count = bookmark_count
            existing.share_count = share_count
            existing.trending_score = trending_score
            existing.performance_percentile = performance_percentile
            existing.last_calculated_at = datetime.now(timezone.utc)
            
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            # Create new record
            analytics = ArticleAnalytics(
                article_id=article_id,
                total_views=total_views,
                unique_views=unique_views,
                direct_views=direct_views,
                rss_views=rss_views,
                search_views=search_views,
                avg_read_time_seconds=avg_read_time_seconds,
                avg_scroll_percentage=avg_scroll_percentage,
                completion_rate=completion_rate,
                bookmark_count=bookmark_count,
                share_count=share_count,
                trending_score=trending_score,
                performance_percentile=performance_percentile,
            )
            
            self.db.add(analytics)
            await self.db.commit()
            await self.db.refresh(analytics)
            return analytics
    
    async def calculate_performance_percentile(self, article_id: UUID) -> int:
        """Calculate performance percentile for an article."""
        # Get article's trending score
        analytics = await self.get_by_article_id(article_id)
        if not analytics:
            return 0
        
        # Count articles with lower trending score
        result = await self.db.execute(
            select(func.count(ArticleAnalytics.id))
            .where(ArticleAnalytics.trending_score < analytics.trending_score)
        )
        lower_count = result.scalar() or 0
        
        # Get total articles
        result = await self.db.execute(select(func.count(ArticleAnalytics.id)))
        total_count = result.scalar() or 1
        
        # Calculate percentile
        percentile = int((lower_count / total_count) * 100)
        return percentile
```

#### Step 1.4: Create Service Layer
**Estimated Time**: 3 hours

**File**: `app/services/article_analytics_service.py`

```python
"""Service for article analytics operations."""

from typing import Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.article_analytics_repository import ArticleAnalyticsRepository
from app.repositories.article_repository import ArticleRepository
from app.repositories.bookmark_repository import BookmarkRepository
from app.repositories.reading_history_repository import ReadingHistoryRepository


class ArticleAnalyticsService:
    """Handle business logic for article analytics."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics_repo = ArticleAnalyticsRepository(db)
        self.article_repo = ArticleRepository(db)
        self.bookmark_repo = BookmarkRepository(db)
        self.reading_history_repo = ReadingHistoryRepository(db)
    
    async def get_article_analytics(self, article_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive analytics for an article.
        
        Returns both stored analytics and real-time calculated metrics.
        """
        # Get stored analytics
        analytics = await self.analytics_repo.get_by_article_id(article_id)
        
        if not analytics:
            # If no analytics exist, calculate from scratch
            await self.recalculate_analytics(article_id)
            analytics = await self.analytics_repo.get_by_article_id(article_id)
        
        # Get article for vote/comment counts
        article = await self.article_repo.get_by_id(article_id)
        if not article:
            raise ValueError("Article not found")
        
        return {
            "article_id": str(article_id),
            "views": {
                "total": analytics.total_views,
                "unique": analytics.unique_views,
                "by_source": {
                    "direct": analytics.direct_views,
                    "rss": analytics.rss_views,
                    "search": analytics.search_views,
                }
            },
            "engagement": {
                "avg_read_time_seconds": analytics.avg_read_time_seconds,
                "avg_scroll_percentage": float(analytics.avg_scroll_percentage),
                "completion_rate": float(analytics.completion_rate),
            },
            "social": {
                "shares": analytics.share_count,
                "bookmarks": analytics.bookmark_count,
                "votes": {
                    "upvotes": max(0, (article.vote_score + article.vote_count) // 2),
                    "downvotes": max(0, (article.vote_count - article.vote_score) // 2),
                },
                "comments": article.comment_count,
            },
            "trending_score": float(analytics.trending_score),
            "performance_percentile": analytics.performance_percentile,
            "last_updated": analytics.last_calculated_at.isoformat(),
        }
    
    async def recalculate_analytics(self, article_id: UUID) -> None:
        """
        Recalculate all analytics for an article from raw data.
        This should be called periodically via Celery task.
        """
        # Get article
        article = await self.article_repo.get_by_id(article_id)
        if not article:
            return
        
        # Calculate view metrics from reading_history
        view_stats = await self.reading_history_repo.get_article_view_stats(article_id)
        
        # Calculate bookmark count
        bookmark_count = await self.bookmark_repo.count_by_article(article_id)
        
        # Calculate trending score (using Reddit hot algorithm)
        trending_score = self._calculate_trending_score(
            article.vote_score,
            article.created_at,
            article.comment_count
        )
        
        # Calculate performance percentile
        performance_percentile = await self.analytics_repo.calculate_performance_percentile(article_id)
        
        # Update analytics
        await self.analytics_repo.create_or_update(
            article_id=article_id,
            total_views=view_stats.get("total_views", 0),
            unique_views=view_stats.get("unique_views", 0),
            direct_views=view_stats.get("direct_views", 0),
            rss_views=view_stats.get("rss_views", 0),
            search_views=view_stats.get("search_views", 0),
            avg_read_time_seconds=view_stats.get("avg_read_time_seconds", 0),
            avg_scroll_percentage=view_stats.get("avg_scroll_percentage", 0.0),
            completion_rate=view_stats.get("completion_rate", 0.0),
            bookmark_count=bookmark_count,
            share_count=0,  # Placeholder - implement share tracking separately
            trending_score=trending_score,
            performance_percentile=performance_percentile,
        )
    
    def _calculate_trending_score(
        self, vote_score: int, created_at, comment_count: int
    ) -> float:
        """
        Calculate trending score using modified Reddit hot algorithm.
        
        Score = log10(max(votes, 1)) + (comments * 0.5) + (age_penalty)
        """
        from datetime import datetime, timezone
        from math import log10
        
        # Vote component (logarithmic)
        vote_component = log10(max(abs(vote_score), 1))
        if vote_score < 0:
            vote_component *= -1
        
        # Comment component (linear with weight)
        comment_component = comment_count * 0.5
        
        # Age penalty (newer = higher score)
        age_hours = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600
        age_penalty = age_hours / 24  # Decay over days
        
        trending_score = vote_component + comment_component - age_penalty
        return round(max(0, trending_score), 2)
```

#### Step 1.5: Create API Endpoint
**Estimated Time**: 2 hours

**File**: `app/api/v1/endpoints/analytics.py`

```python
"""Analytics API Endpoints"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.article_analytics_service import ArticleAnalyticsService

router = APIRouter()


@router.get(
    "/articles/{article_id}/analytics",
    status_code=status.HTTP_200_OK,
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
)
async def get_article_analytics(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get article performance analytics."""
    service = ArticleAnalyticsService(db)
    
    try:
        analytics = await service.get_article_analytics(article_id)
        return analytics
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analytics: {str(e)}"
        )
```

#### Step 1.6: Register Router
**File**: `app/api/v1/api.py`

```python
# Add import
from app.api.v1.endpoints import analytics

# Add to api_router
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
```

#### Step 1.7: Create Celery Task for Analytics Calculation
**Estimated Time**: 2 hours

**File**: `app/tasks/analytics_tasks.py`

```python
"""Celery tasks for analytics calculation."""

from celery import shared_task
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.article import Article
from app.services.article_analytics_service import ArticleAnalyticsService


@shared_task(name="calculate_article_analytics")
async def calculate_article_analytics_task(article_id: str):
    """Calculate analytics for a single article."""
    async with AsyncSessionLocal() as db:
        service = ArticleAnalyticsService(db)
        await service.recalculate_analytics(UUID(article_id))


@shared_task(name="calculate_all_analytics")
async def calculate_all_analytics_task():
    """
    Calculate analytics for all articles.
    Run this daily via Celery Beat.
    """
    async with AsyncSessionLocal() as db:
        # Get all article IDs
        result = await db.execute(select(Article.id))
        article_ids = [str(row[0]) for row in result.fetchall()]
        
        # Queue individual calculation tasks
        for article_id in article_ids:
            calculate_article_analytics_task.delay(article_id)
```

**File**: `app/core/celery_app.py` - Add beat schedule

```python
# Add to beat_schedule
beat_schedule = {
    # ... existing schedules
    "calculate-all-analytics-daily": {
        "task": "calculate_all_analytics",
        "schedule": crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
}
```

#### Step 1.8: Add Tests
**Estimated Time**: 3 hours

**File**: `tests/unit/test_article_analytics_service.py`

```python
"""Tests for article analytics service."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.services.article_analytics_service import ArticleAnalyticsService


@pytest.mark.asyncio
async def test_calculate_trending_score(test_db):
    """Test trending score calculation."""
    service = ArticleAnalyticsService(test_db)
    
    # Recent article with good engagement
    score = service._calculate_trending_score(
        vote_score=50,
        created_at=datetime.now(timezone.utc),
        comment_count=10
    )
    
    assert score > 0
    assert isinstance(score, float)


@pytest.mark.asyncio
async def test_get_article_analytics(test_db, sample_article):
    """Test retrieving article analytics."""
    service = ArticleAnalyticsService(test_db)
    
    analytics = await service.get_article_analytics(sample_article.id)
    
    assert analytics["article_id"] == str(sample_article.id)
    assert "views" in analytics
    assert "engagement" in analytics
    assert "social" in analytics
```

**File**: `tests/integration/test_analytics_endpoints.py`

```python
"""Integration tests for analytics endpoints."""

import pytest


@pytest.mark.integration
async def test_get_article_analytics_endpoint(test_client, sample_article):
    """Test GET /api/v1/analytics/articles/{id}/analytics"""
    response = await test_client.get(f"/api/v1/analytics/articles/{sample_article.id}/analytics")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["article_id"] == str(sample_article.id)
    assert "views" in data
    assert "engagement" in data
    assert "social" in data
    assert "trending_score" in data


@pytest.mark.integration
async def test_get_analytics_nonexistent_article(test_client):
    """Test analytics for non-existent article returns 404"""
    fake_id = str(uuid4())
    response = await test_client.get(f"/api/v1/analytics/articles/{fake_id}/analytics")
    
    assert response.status_code == 404
```

---

### Endpoint 2: Content Quality Score
**Endpoint**: `GET /api/v1/analytics/content-quality`

#### Step 2.1: Database Schema Updates
**Estimated Time**: 1 hour

**No new tables needed** - Uses existing data from:
- `articles` table
- `article_fact_checks` table
- `rss_sources` table

#### Step 2.2: Create Service Layer
**Estimated Time**: 3 hours

**File**: `app/services/content_quality_service.py`

```python
"""Service for content quality analysis."""

from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.article_fact_check import ArticleFactCheck
from app.models.rss_source import RSSSource


class ContentQualityService:
    """Analyze content quality across sources and categories."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_quality_report(
        self,
        source_id: Optional[UUID] = None,
        category: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Generate content quality report.
        
        Args:
            source_id: Filter by RSS source
            category: Filter by article category
            days: Time range for analysis (default: 30 days)
        
        Returns:
            Quality metrics and recommendations
        """
        # Build base query
        query = select(Article).join(
            ArticleFactCheck, Article.id == ArticleFactCheck.article_id, isouter=True
        )
        
        # Apply filters
        if source_id:
            query = query.where(Article.rss_source_id == source_id)
        if category:
            query = query.where(Article.category == category)
        
        # Get articles
        result = await self.db.execute(query)
        articles = result.scalars().all()
        
        if not articles:
            return self._empty_report()
        
        # Calculate overall metrics
        overall_metrics = await self._calculate_overall_metrics(articles)
        
        # Calculate per-source breakdown
        by_source = await self._calculate_by_source_metrics()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(overall_metrics, by_source)
        
        return {
            "overall_quality_score": overall_metrics["quality_score"],
            "metrics": {
                "fact_check_pass_rate": overall_metrics["fact_check_pass_rate"],
                "avg_credibility_score": overall_metrics["avg_credibility_score"],
                "misinformation_rate": overall_metrics["misinformation_rate"],
                "source_consensus_rate": overall_metrics["source_consensus_rate"],
            },
            "by_source": by_source,
            "recommendations": recommendations,
            "time_range_days": days,
            "total_articles_analyzed": len(articles),
        }
    
    async def _calculate_overall_metrics(self, articles: List[Article]) -> Dict[str, float]:
        """Calculate overall quality metrics."""
        total_articles = len(articles)
        
        # Get fact-check data
        article_ids = [a.id for a in articles]
        fact_checks_query = select(ArticleFactCheck).where(
            ArticleFactCheck.article_id.in_(article_ids)
        )
        result = await self.db.execute(fact_checks_query)
        fact_checks = result.scalars().all()
        
        # Calculate metrics
        fact_checked_count = len(fact_checks)
        passed_fact_checks = sum(1 for fc in fact_checks if fc.verdict in ["TRUE", "MOSTLY_TRUE"])
        
        avg_credibility = (
            sum(fc.credibility_score for fc in fact_checks) / fact_checked_count
            if fact_checked_count > 0 else 0
        )
        
        misinformation_count = sum(
            1 for fc in fact_checks if fc.verdict in ["FALSE", "MOSTLY_FALSE"]
        )
        
        strong_consensus_count = sum(
            1 for fc in fact_checks if fc.source_consensus == "STRONG_AGREEMENT"
        )
        
        # Calculate rates
        fact_check_pass_rate = passed_fact_checks / fact_checked_count if fact_checked_count > 0 else 0
        misinformation_rate = misinformation_count / total_articles if total_articles > 0 else 0
        source_consensus_rate = strong_consensus_count / fact_checked_count if fact_checked_count > 0 else 0
        
        # Calculate overall quality score (weighted average)
        quality_score = (
            (fact_check_pass_rate * 40) +
            (avg_credibility * 0.30) +  # Scale to 30 points
            ((1 - misinformation_rate) * 20) +
            (source_consensus_rate * 10)
        )
        
        return {
            "quality_score": round(quality_score, 2),
            "fact_check_pass_rate": round(fact_check_pass_rate, 3),
            "avg_credibility_score": round(avg_credibility, 1),
            "misinformation_rate": round(misinformation_rate, 3),
            "source_consensus_rate": round(source_consensus_rate, 3),
        }
    
    async def _calculate_by_source_metrics(self) -> List[Dict[str, Any]]:
        """Calculate quality metrics grouped by RSS source."""
        # Complex aggregation query
        query = (
            select(
                RSSSource.id,
                RSSSource.name,
                func.count(Article.id).label("article_count"),
                func.avg(ArticleFactCheck.credibility_score).label("avg_credibility"),
                func.count(ArticleFactCheck.id).label("fact_checked_count"),
            )
            .join(Article, RSSSource.id == Article.rss_source_id)
            .join(ArticleFactCheck, Article.id == ArticleFactCheck.article_id, isouter=True)
            .group_by(RSSSource.id, RSSSource.name)
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        by_source = []
        for row in rows:
            # Calculate pass rate for this source
            pass_rate = await self._get_source_pass_rate(row.id)
            
            quality_score = (
                (pass_rate * 50) +
                ((row.avg_credibility or 0) * 0.5)  # Scale to 50 points
            )
            
            by_source.append({
                "source_id": str(row.id),
                "source_name": row.name,
                "quality_score": round(quality_score, 1),
                "article_count": row.article_count,
                "fact_check_pass_rate": round(pass_rate, 3),
                "avg_credibility_score": round(row.avg_credibility or 0, 1),
            })
        
        # Sort by quality score descending
        by_source.sort(key=lambda x: x["quality_score"], reverse=True)
        return by_source
    
    async def _get_source_pass_rate(self, source_id: UUID) -> float:
        """Get fact-check pass rate for a specific source."""
        # Get articles for this source
        articles_query = select(Article.id).where(Article.rss_source_id == source_id)
        result = await self.db.execute(articles_query)
        article_ids = [row[0] for row in result.fetchall()]
        
        if not article_ids:
            return 0.0
        
        # Get fact-checks
        fact_checks_query = select(ArticleFactCheck).where(
            ArticleFactCheck.article_id.in_(article_ids)
        )
        result = await self.db.execute(fact_checks_query)
        fact_checks = result.scalars().all()
        
        if not fact_checks:
            return 0.0
        
        passed = sum(1 for fc in fact_checks if fc.verdict in ["TRUE", "MOSTLY_TRUE"])
        return passed / len(fact_checks)
    
    def _generate_recommendations(
        self, overall_metrics: Dict, by_source: List[Dict]
    ) -> List[str]:
        """Generate actionable recommendations based on quality metrics."""
        recommendations = []
        
        # Check overall quality
        if overall_metrics["quality_score"] < 60:
            recommendations.append(
                "⚠️ Overall content quality is below acceptable threshold (60). Consider reviewing RSS sources."
            )
        
        # Check misinformation rate
        if overall_metrics["misinformation_rate"] > 0.05:
            recommendations.append(
                f"⚠️ Misinformation rate is {overall_metrics['misinformation_rate']:.1%}. Review moderation policies."
            )
        
        # Check low-quality sources
        low_quality_sources = [s for s in by_source if s["quality_score"] < 60]
        if low_quality_sources:
            recommendations.append(
                f"Consider removing or reviewing {len(low_quality_sources)} sources with quality score < 60"
            )
        
        # Check declining sources (would need time-series data)
        # Placeholder for now
        recommendations.append(
            "💡 Tip: Regularly monitor source quality trends to maintain high standards"
        )
        
        return recommendations
    
    def _empty_report(self) -> Dict[str, Any]:
        """Return empty report structure."""
        return {
            "overall_quality_score": 0.0,
            "metrics": {
                "fact_check_pass_rate": 0.0,
                "avg_credibility_score": 0.0,
                "misinformation_rate": 0.0,
                "source_consensus_rate": 0.0,
            },
            "by_source": [],
            "recommendations": ["No data available for analysis"],
            "time_range_days": 0,
            "total_articles_analyzed": 0,
        }
```

#### Step 2.3: Create API Endpoint
**Estimated Time**: 1 hour

**Update File**: `app/api/v1/endpoints/analytics.py`

```python
from typing import Optional
from fastapi import Query

from app.services.content_quality_service import ContentQualityService


@router.get(
    "/content-quality",
    status_code=status.HTTP_200_OK,
    summary="Get content quality analysis",
    description="""
    Analyze content quality across RSS sources and categories.
    
    **Quality Metrics:**
    - Fact-check pass rate
    - Average credibility score
    - Misinformation rate
    - Source consensus rate
    
    **Returns:**
    - Overall quality score (0-100)
    - Per-source breakdown
    - Actionable recommendations
    
    **Authentication**: Optional (admin recommended)
    """,
)
async def get_content_quality(
    source_id: Optional[UUID] = Query(None, description="Filter by RSS source"),
    category: Optional[str] = Query(None, description="Filter by category"),
    days: int = Query(30, ge=1, le=365, description="Analysis time range"),
    db: AsyncSession = Depends(get_db),
):
    """Get content quality analysis."""
    service = ContentQualityService(db)
    
    try:
        quality_report = await service.get_quality_report(
            source_id=source_id,
            category=category,
            days=days,
        )
        return quality_report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quality report: {str(e)}"
        )
```

---

## Phase 2: Social Features (Week 2-3)

### Endpoint 3: Comment Mentions (@username)
**Endpoints**: 
- `GET /api/v1/users/me/mentions`
- Enhanced `POST /api/v1/comments` to parse mentions

#### Step 3.1: Database Schema Updates
**Estimated Time**: 1 hour

**New Table**: `comment_mentions`

```sql
CREATE TABLE comment_mentions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    comment_id UUID REFERENCES comments(id) ON DELETE CASCADE,
    mentioned_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    mentioned_by_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(comment_id, mentioned_user_id)
);

CREATE INDEX idx_comment_mentions_mentioned_user ON comment_mentions(mentioned_user_id);
CREATE INDEX idx_comment_mentions_comment ON comment_mentions(comment_id);
```

#### Step 3.2: Update Comment Service
**Estimated Time**: 3 hours

**File**: `app/services/comment_service.py` - Add mention parsing

```python
import re
from typing import List, Set
from uuid import UUID

async def _parse_mentions(self, content: str) -> Set[str]:
    """
    Extract @username mentions from comment content.
    
    Returns set of unique usernames mentioned.
    """
    # Pattern: @username (alphanumeric + underscore, 3-50 chars)
    pattern = r'@([a-zA-Z0-9_]{3,50})'
    mentions = re.findall(pattern, content)
    return set(mentions)

async def create_comment(
    self,
    user_id: UUID,
    article_id: UUID,
    content: str,
    parent_comment_id: Optional[UUID] = None,
) -> Comment:
    """Create a new comment with mention parsing."""
    
    # ... existing validation code ...
    
    # Create comment
    comment = Comment(
        id=uuid4(),
        user_id=user_id,
        article_id=article_id,
        content=content,
        parent_comment_id=parent_comment_id,
    )
    
    self.db.add(comment)
    await self.db.commit()
    await self.db.refresh(comment)
    
    # Parse and process mentions
    mentioned_usernames = await self._parse_mentions(content)
    if mentioned_usernames:
        await self._process_mentions(
            comment_id=comment.id,
            mentioned_by_user_id=user_id,
            mentioned_usernames=mentioned_usernames,
            article_id=article_id,
        )
    
    return comment

async def _process_mentions(
    self,
    comment_id: UUID,
    mentioned_by_user_id: UUID,
    mentioned_usernames: Set[str],
    article_id: UUID,
):
    """
    Process mentions: create mention records and send notifications.
    """
    from app.models.user import User
    from app.models.comment_mention import CommentMention
    from app.services.notification_service import NotificationService
    
    # Get user IDs for mentioned usernames
    result = await self.db.execute(
        select(User.id, User.username).where(User.username.in_(mentioned_usernames))
    )
    users = result.all()
    
    notification_service = NotificationService(self.db)
    
    for user_id, username in users:
        # Don't notify if user mentions themselves
        if user_id == mentioned_by_user_id:
            continue
        
        # Create mention record
        mention = CommentMention(
            id=uuid4(),
            comment_id=comment_id,
            mentioned_user_id=user_id,
            mentioned_by_user_id=mentioned_by_user_id,
        )
        self.db.add(mention)
        
        # Create notification
        await notification_service.create_mention_notification(
            user_id=user_id,
            actor_id=mentioned_by_user_id,
            comment_id=comment_id,
            article_id=article_id,
        )
    
    await self.db.commit()
```

#### Step 3.3: Create Mentions Endpoint
**Estimated Time**: 2 hours

**File**: `app/api/v1/endpoints/users.py` - Add mentions endpoint

```python
@router.get("/me/mentions", status_code=status.HTTP_200_OK)
async def get_user_mentions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all @mentions for the current user.
    
    Returns comments where the user was mentioned with @username.
    """
    from app.models.comment_mention import CommentMention
    from app.models.comment import Comment
    from app.models.article import Article
    from app.models.user import User as UserModel
    
    skip = (page - 1) * page_size
    
    # Build query
    query = (
        select(CommentMention)
        .join(Comment, CommentMention.comment_id == Comment.id)
        .where(CommentMention.mentioned_user_id == current_user.id)
        .order_by(CommentMention.created_at.desc())
        .offset(skip)
        .limit(page_size)
    )
    
    result = await db.execute(query)
    mentions = result.scalars().all()
    
    # Build response
    mention_data = []
    for mention in mentions:
        # Get full comment data
        comment = await db.get(Comment, mention.comment_id)
        article = await db.get(Article, comment.article_id)
        mentioned_by = await db.get(UserModel, mention.mentioned_by_user_id)
        
        mention_data.append({
            "id": str(mention.id),
            "mentioned_in": {
                "comment_id": str(comment.id),
                "comment_content": comment.content,
                "article_id": str(article.id),
                "article_title": article.title,
            },
            "mentioned_by": {
                "user_id": str(mentioned_by.id),
                "username": mentioned_by.username,
                "avatar_url": mentioned_by.avatar_url,
            },
            "created_at": mention.created_at.isoformat(),
        })
    
    # Get total count
    count_query = select(func.count(CommentMention.id)).where(
        CommentMention.mentioned_user_id == current_user.id
    )
    result = await db.execute(count_query)
    total = result.scalar()
    
    return {
        "mentions": mention_data,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
```

---

### Endpoint 4: Thread Subscriptions
**Endpoints**:
- `POST /api/v1/comments/{comment_id}/subscribe`
- `DELETE /api/v1/comments/{comment_id}/subscribe`
- `GET /api/v1/users/me/subscriptions`

#### Step 4.1: Database Schema
**Estimated Time**: 1 hour

```sql
CREATE TABLE thread_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    comment_id UUID REFERENCES comments(id) ON DELETE CASCADE,
    subscribed_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, comment_id)
);

CREATE INDEX idx_thread_subscriptions_user ON thread_subscriptions(user_id);
CREATE INDEX idx_thread_subscriptions_comment ON thread_subscriptions(comment_id);
```

#### Step 4.2-4.5: Implementation
**Estimated Time**: 6 hours total

(Similar pattern to mentions - create model, repository, service, endpoints)

---

### Endpoint 5: User Reputation & Leaderboard
**Endpoints**:
- `GET /api/v1/users/{user_id}/reputation`
- `GET /api/v1/leaderboard`

#### Step 5.1: Database Schema
**Estimated Time**: 2 hours

```sql
CREATE TABLE user_reputation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    reputation_score INTEGER DEFAULT 0,
    
    -- Breakdown
    comment_upvotes INTEGER DEFAULT 0,
    helpful_flags INTEGER DEFAULT 0,
    article_submissions INTEGER DEFAULT 0,
    fact_check_contributions INTEGER DEFAULT 0,
    
    -- Badges (JSONB array)
    badges JSONB DEFAULT '[]'::jsonb,
    
    -- Rankings
    rank INTEGER,
    percentile DECIMAL(5,2),
    
    last_calculated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id)
);

CREATE INDEX idx_user_reputation_score ON user_reputation(reputation_score DESC);
CREATE INDEX idx_user_reputation_rank ON user_reputation(rank);
```

#### Step 5.2-5.5: Implementation
**Estimated Time**: 8 hours total

---

## Phase 3: Infrastructure Enhancements (Week 3-4)

### Endpoint 6: Enhanced RSS Feed Management
**Endpoints**:
- `POST /api/v1/rss-feeds/{feed_id}/validate`
- `GET /api/v1/rss-feeds/{feed_id}/preview`

*(Implementation details similar to above pattern)*

### Endpoint 7: Cache Management
**Endpoints**:
- `DELETE /api/v1/cache/articles/{article_id}`
- `DELETE /api/v1/cache/feed`
- `POST /api/v1/cache/warm`

### Endpoint 8: Enhanced Health Checks
**Endpoint**: `GET /api/v1/status/detailed`

---

## Phase 4: Testing & Documentation (Week 4)

### Testing Checklist
- [ ] Unit tests for all service methods
- [ ] Integration tests for all endpoints
- [ ] Load testing for analytics endpoints
- [ ] Database migration tests
- [ ] Rollback procedure tests

### Documentation Tasks
- [ ] Update OpenAPI/Swagger docs
- [ ] Create API usage examples
- [ ] Update README with new endpoints
- [ ] Create admin guide for analytics
- [ ] Update CHANGELOG.md

---

## Deployment Strategy

### Pre-Deployment
1. Code review (2 reviewers minimum)
2. Run full test suite
3. Performance testing in staging
4. Database backup

### Deployment Steps
1. Apply database migrations
2. Deploy backend code
3. Warm caches
4. Monitor error rates
5. Verify analytics calculation

### Post-Deployment
1. Monitor for 24 hours
2. Check analytics accuracy
3. Verify notification delivery
4. Review performance metrics

---

## Rollback Plan

### Database Rollback
```bash
# Rollback migrations
alembic downgrade -1

# Restore from backup if needed
pg_restore -d database_name backup_file.sql
```

### Code Rollback
```bash
# Revert to previous commit
git revert <commit-hash>
git push origin main

# Or full rollback
git reset --hard <previous-commit>
git push --force origin main
```

---

## Success Metrics

### Technical Metrics
- API response time < 200ms for analytics endpoints
- Cache hit rate > 80%
- Zero data loss during migration
- Test coverage > 90%

### Product Metrics
- Analytics endpoint usage > 1000 requests/day
- Mention feature adoption > 30% of active users
- Quality score correlation with user engagement

---

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1: Analytics | Week 1-2 | Performance metrics, Quality score |
| Phase 2: Social | Week 2-3 | Mentions, Subscriptions, Reputation |
| Phase 3: Infrastructure | Week 3-4 | RSS management, Cache, Health checks |
| Phase 4: Testing | Week 4 | Full test coverage, Documentation |

**Total Duration**: 4 weeks  
**Buffer Time**: +2 weeks for unexpected issues  
**Go-Live Date**: Week 6

---

## Contact & Support

**Technical Lead**: [Name]  
**Product Owner**: [Name]  
**Slack Channel**: #backend-implementation  
**Documentation**: `/docs` directory

**Last Updated**: 2025-11-11  
**Version**: 1.0  
**Status**: Ready for Review
