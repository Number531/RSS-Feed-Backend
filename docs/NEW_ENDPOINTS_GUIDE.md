# New API Endpoints Guide - Article Analytics

## Overview

This guide documents the newly implemented Article Performance Analytics endpoint that provides comprehensive performance metrics for articles.

**Implemented**: November 11, 2025  
**Version**: 1.0.0  
**Status**: ✅ Production Ready

---

## Table of Contents

1. [Article Performance Analytics](#article-performance-analytics)
2. [Database Schema](#database-schema)
3. [Usage Examples](#usage-examples)
4. [Response Format](#response-format)
5. [Integration Guide](#integration-guide)

---

## Article Performance Analytics

### Endpoint

```
GET /api/v1/analytics/articles/{article_id}/performance
```

### Description

Retrieves comprehensive performance metrics for a specific article including view counts, engagement metrics, social interactions, and trending scores.

### Authentication

**Optional** - Public statistics available without authentication

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `article_id` | UUID (path) | Yes | The unique identifier of the article |

### Response Status Codes

| Code | Description |
|------|-------------|
| 200 | Analytics retrieved successfully |
| 404 | Article not found |
| 500 | Internal server error |

---

## Database Schema

### New Table: `article_analytics`

The endpoint is backed by a new PostgreSQL table with the following structure:

```sql
CREATE TABLE article_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE UNIQUE,
    
    -- View Metrics
    total_views INTEGER DEFAULT 0,
    unique_views INTEGER DEFAULT 0,
    direct_views INTEGER DEFAULT 0,
    rss_views INTEGER DEFAULT 0,
    search_views INTEGER DEFAULT 0,
    
    -- Engagement Metrics
    avg_read_time_seconds INTEGER DEFAULT 0,
    avg_scroll_percentage DECIMAL(5,2) DEFAULT 0,
    completion_rate DECIMAL(5,4) DEFAULT 0,
    
    -- Social Metrics
    bookmark_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    
    -- Performance Scores
    trending_score DECIMAL(5,2) DEFAULT 0,
    performance_percentile INTEGER DEFAULT 0,
    
    -- Timestamps
    last_calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Indexes:**
- `idx_article_analytics_article_id` - Fast lookup by article
- `idx_article_analytics_trending_score` - Trending score queries
- `idx_article_analytics_performance` - Performance percentile queries

---

## Usage Examples

### Example 1: Get Article Performance Metrics

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/articles/3b04d5c7-4a1d-44fb-afee-928fc763187a/performance" \
  -H "Accept: application/json"
```

**Response:**
```json
{
  "article_id": "3b04d5c7-4a1d-44fb-afee-928fc763187a",
  "views": {
    "total": 0,
    "unique": 0,
    "by_source": {
      "direct": 0,
      "rss": 0,
      "search": 0
    }
  },
  "engagement": {
    "avg_read_time_seconds": 0,
    "avg_scroll_percentage": 0.0,
    "completion_rate": 0.0
  },
  "social": {
    "shares": 0,
    "bookmarks": 0,
    "votes": {
      "upvotes": 0,
      "downvotes": 0
    },
    "comments": 0
  },
  "trending_score": 0.0,
  "performance_percentile": 0,
  "last_updated": "2025-11-11T20:46:55.929122+00:00"
}
```

### Example 2: Using with JavaScript/TypeScript

```typescript
async function getArticlePerformance(articleId: string) {
  const response = await fetch(
    `https://api.example.com/api/v1/analytics/articles/${articleId}/performance`,
    {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    }
  );

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Article not found');
    }
    throw new Error('Failed to fetch analytics');
  }

  const analytics = await response.json();
  return analytics;
}

// Usage
try {
  const analytics = await getArticlePerformance('3b04d5c7-4a1d-44fb-afee-928fc763187a');
  console.log(`Article has ${analytics.views.total} total views`);
  console.log(`Trending score: ${analytics.trending_score}`);
} catch (error) {
  console.error('Error:', error);
}
```

### Example 3: Using with Python

```python
import requests
from uuid import UUID

def get_article_performance(article_id: UUID) -> dict:
    """Get performance analytics for an article."""
    url = f"https://api.example.com/api/v1/analytics/articles/{article_id}/performance"
    
    response = requests.get(url)
    response.raise_for_status()
    
    return response.json()

# Usage
try:
    article_id = "3b04d5c7-4a1d-44fb-afee-928fc763187a"
    analytics = get_article_performance(article_id)
    
    print(f"Total views: {analytics['views']['total']}")
    print(f"Engagement rate: {analytics['engagement']['completion_rate']}")
    print(f"Trending score: {analytics['trending_score']}")
except requests.HTTPError as e:
    if e.response.status_code == 404:
        print("Article not found")
    else:
        print(f"Error: {e}")
```

---

## Response Format

### Response Schema

```typescript
interface ArticlePerformanceResponse {
  article_id: string;  // UUID
  views: {
    total: number;
    unique: number;
    by_source: {
      direct: number;
      rss: number;
      search: number;
    };
  };
  engagement: {
    avg_read_time_seconds: number;
    avg_scroll_percentage: number;  // 0-100
    completion_rate: number;  // 0.0-1.0
  };
  social: {
    shares: number;
    bookmarks: number;
    votes: {
      upvotes: number;
      downvotes: number;
    };
    comments: number;
  };
  trending_score: number;  // Calculated using Reddit hot algorithm
  performance_percentile: number;  // 0-100
  last_updated: string;  // ISO 8601 timestamp
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `article_id` | UUID | Unique identifier of the article |
| `views.total` | integer | Total number of views (all sources) |
| `views.unique` | integer | Number of unique viewers |
| `views.by_source.direct` | integer | Views from direct traffic |
| `views.by_source.rss` | integer | Views from RSS feeds |
| `views.by_source.search` | integer | Views from search results |
| `engagement.avg_read_time_seconds` | integer | Average time spent reading (seconds) |
| `engagement.avg_scroll_percentage` | float | Average scroll depth (0-100%) |
| `engagement.completion_rate` | float | Percentage of article completed (0.0-1.0) |
| `social.shares` | integer | Number of times shared |
| `social.bookmarks` | integer | Number of bookmarks |
| `social.votes.upvotes` | integer | Number of upvotes |
| `social.votes.downvotes` | integer | Number of downvotes |
| `social.comments` | integer | Number of comments |
| `trending_score` | float | Trending algorithm score (Reddit-style) |
| `performance_percentile` | integer | Performance relative to other articles (0-100) |
| `last_updated` | string | Last time analytics were calculated |

---

## Integration Guide

### Frontend Integration

#### React Component Example

```tsx
import React, { useEffect, useState } from 'react';

interface ArticleAnalytics {
  views: { total: number };
  engagement: { completion_rate: number };
  social: { comments: number; votes: { upvotes: number } };
  trending_score: number;
}

function ArticleStats({ articleId }: { articleId: string }) {
  const [analytics, setAnalytics] = useState<ArticleAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchAnalytics() {
      try {
        const response = await fetch(
          `/api/v1/analytics/articles/${articleId}/performance`
        );
        
        if (!response.ok) {
          throw new Error('Failed to fetch analytics');
        }
        
        const data = await response.json();
        setAnalytics(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchAnalytics();
  }, [articleId]);

  if (loading) return <div>Loading analytics...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!analytics) return null;

  return (
    <div className="article-stats">
      <div className="stat">
        <span className="label">Views</span>
        <span className="value">{analytics.views.total.toLocaleString()}</span>
      </div>
      <div className="stat">
        <span className="label">Comments</span>
        <span className="value">{analytics.social.comments}</span>
      </div>
      <div className="stat">
        <span className="label">Upvotes</span>
        <span className="value">{analytics.social.votes.upvotes}</span>
      </div>
      <div className="stat">
        <span className="label">Trending Score</span>
        <span className="value">{analytics.trending_score.toFixed(1)}</span>
      </div>
    </div>
  );
}
```

### Backend Integration

#### Periodic Analytics Calculation

The analytics data is stored in the database and should be recalculated periodically. Future implementation will include Celery tasks for this:

```python
# Future: Celery task for daily analytics calculation
@shared_task(name="calculate_article_analytics")
async def calculate_article_analytics_task(article_id: str):
    """Calculate analytics for a single article."""
    async with AsyncSessionLocal() as db:
        service = ArticleAnalyticsService(db)
        await service.recalculate_analytics(UUID(article_id))
```

### Caching Strategy

**Recommended**: Cache responses for 5 minutes

```nginx
# Nginx caching example
location /api/v1/analytics/ {
    proxy_pass http://backend;
    proxy_cache my_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_key "$scheme$request_method$host$request_uri";
}
```

---

## Performance Considerations

### Query Performance

The endpoint is optimized with:
- Database indexes on frequently queried fields
- Single query per request (no N+1 problems)
- Denormalized data for fast reads

### Scalability

- **Read-heavy workload**: Optimized for high read volume
- **Write frequency**: Analytics updated periodically (not real-time)
- **Caching**: Recommended 5-minute cache TTL

### Rate Limiting

**Recommended limits**:
- Public endpoints: 100 requests/minute/IP
- Authenticated users: 1000 requests/minute/user

---

## Migration History

### Migration: `bf07c7c9a81b`

**Revision**: bf07c7c9a81b  
**Created**: 2025-11-11 15:35:23  
**Parent**: 6134904aa8f0

**Changes**:
- Created `article_analytics` table
- Added unique constraint on `article_id`
- Created performance indexes
- Added foreign key relationship to `articles`

**Apply migration**:
```bash
alembic upgrade head
```

**Rollback**:
```bash
alembic downgrade -1
```

---

## Architecture Components

### Layers Implemented

1. **Database Layer**
   - `alembic/versions/...add_article_analytics_table.py`
   - Migration with table definition and indexes

2. **Model Layer**
   - `app/models/article_analytics.py`
   - SQLAlchemy ORM model

3. **Repository Layer**
   - `app/repositories/article_analytics_repository.py`
   - Data access methods (get, create, update, calculate percentile)

4. **Service Layer**
   - `app/services/article_analytics_service.py`
   - Business logic (analytics calculation, trending score algorithm)

5. **API Layer**
   - `app/api/v1/endpoints/analytics.py` (updated)
   - REST endpoint with FastAPI

---

## Testing

### Manual Testing

```bash
# 1. Apply migration
alembic upgrade head

# 2. Start server
uvicorn app.main:app --reload --port 8000

# 3. Test endpoint
curl "http://localhost:8000/api/v1/analytics/articles/{article_id}/performance"
```

### Unit Tests

```python
# tests/unit/test_article_analytics_service.py
import pytest
from datetime import datetime, timezone

from app.services.article_analytics_service import ArticleAnalyticsService


@pytest.mark.asyncio
async def test_calculate_trending_score(test_db):
    """Test trending score calculation."""
    service = ArticleAnalyticsService(test_db)
    
    score = service._calculate_trending_score(
        vote_score=50,
        created_at=datetime.now(timezone.utc),
        comment_count=10
    )
    
    assert score > 0
    assert isinstance(score, float)
```

### Integration Tests

```python
# tests/integration/test_analytics_endpoints.py
@pytest.mark.integration
async def test_get_article_performance(test_client, sample_article):
    """Test GET /api/v1/analytics/articles/{id}/performance"""
    response = await test_client.get(
        f"/api/v1/analytics/articles/{sample_article.id}/performance"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "views" in data
    assert "engagement" in data
    assert "social" in data
    assert "trending_score" in data
```

---

## Troubleshooting

### Common Issues

**Issue**: 404 Article Not Found  
**Solution**: Verify the article UUID exists in the database

**Issue**: 500 Internal Server Error  
**Solution**: Check server logs for database connection issues

**Issue**: Empty/Zero metrics  
**Solution**: Analytics are created on first request with default values. They will be populated as data is tracked.

### Debug Mode

Enable detailed logging:

```python
import logging
logging.getLogger("app.services.article_analytics_service").setLevel(logging.DEBUG)
```

---

## Roadmap

### Phase 2 (Planned)

- [ ] Content Quality Score endpoint
- [ ] Celery tasks for periodic analytics calculation
- [ ] Real-time view tracking integration
- [ ] Analytics dashboard aggregations
- [ ] CSV export functionality

### Phase 3 (Future)

- [ ] Historical trends API
- [ ] Comparative analytics (article vs article)
- [ ] Predictive trending scores
- [ ] Machine learning recommendations

---

## Support & Feedback

**Documentation**: `/docs` directory  
**API Docs**: `http://localhost:8000/docs` (Swagger UI)  
**Issues**: GitHub Issues  
**Version**: 1.0.0

**Last Updated**: 2025-11-11  
**Status**: ✅ Production Ready
