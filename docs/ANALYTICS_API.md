# Analytics API Documentation

## Overview

The Analytics API provides comprehensive insights into fact-checking activities, source credibility, and temporal trends. These endpoints aggregate data from article fact-checks to help understand patterns, reliability metrics, and claim verification statistics.

**Base Path:** `/api/v1/analytics`

**Version:** 1.0.0

---

## Table of Contents

1. [Authentication](#authentication)
2. [Endpoints](#endpoints)
   - [Get Aggregate Statistics](#1-get-aggregate-statistics) ⭐ **Phase 2A**
   - [Get Category Analytics](#2-get-category-analytics) ⭐ **Phase 2A**
   - [Get Verdict Details](#3-get-verdict-details) ⭐ **NEW**
   - [Get Source Reliability Statistics](#4-get-source-reliability-statistics)
   - [Get Fact-Check Trends](#5-get-fact-check-trends)
   - [Get Claims Analytics](#6-get-claims-analytics)
3. [Data Models](#data-models)
4. [Error Responses](#error-responses)
5. [Usage Examples](#usage-examples)
6. [Rate Limits](#rate-limits)

---

## Authentication

All analytics endpoints require authentication. Include a valid JWT token in the request header:

```http
Authorization: Bearer <your_jwt_token>
```

---

## Endpoints

### 1. Get Aggregate Statistics

⭐ **NEW - Phase 2A**: Comprehensive dashboard overview with lifetime metrics, monthly comparisons, and milestone tracking.

Retrieves high-level aggregate statistics across all fact-checking activities, providing a complete overview of the platform's health and performance.

#### Endpoint

```http
GET /api/v1/analytics/stats
```

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_lifetime` | boolean | No | `true` | Include lifetime statistics |
| `include_trends` | boolean | No | `true` | Calculate month-over-month trends |

#### Request Example

```http
GET /api/v1/analytics/stats?include_lifetime=true&include_trends=true
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response

**Status Code:** `200 OK`

```json
{
  "lifetime": {
    "articles_fact_checked": 1500,
    "sources_monitored": 25,
    "claims_verified": 4500,
    "average_credibility": 75.5
  },
  "this_month": {
    "articles_fact_checked": 150,
    "average_credibility": 78.2,
    "volume_change": 25.0,
    "credibility_change": 2.89
  },
  "milestones": [
    {
      "milestone": "1000_articles",
      "label": "1,000 Articles Fact-Checked",
      "achieved": true,
      "achieved_at": "2025-09-15T10:30:00Z"
    },
    {
      "milestone": "5000_claims",
      "label": "5,000 Claims Verified",
      "achieved": false,
      "progress": 90.0
    }
  ]
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `lifetime.articles_fact_checked` | integer | Total articles fact-checked (all-time) |
| `lifetime.sources_monitored` | integer | Total unique RSS sources monitored |
| `lifetime.claims_verified` | integer | Total individual claims verified |
| `lifetime.average_credibility` | decimal | Overall average credibility score (0-100) |
| `this_month.articles_fact_checked` | integer | Articles fact-checked this month |
| `this_month.average_credibility` | decimal | Average credibility this month (0-100) |
| `this_month.volume_change` | decimal | % change in volume vs last month |
| `this_month.credibility_change` | decimal | % change in credibility vs last month |
| `milestones` | array | Platform milestones and achievements |
| `milestones[].milestone` | string | Milestone identifier |
| `milestones[].label` | string | Human-readable milestone description |
| `milestones[].achieved` | boolean | Whether milestone is completed |
| `milestones[].achieved_at` | string (ISO 8601) | When milestone was achieved (if completed) |
| `milestones[].progress` | decimal | Progress towards milestone (0-100, if not achieved) |

#### Use Cases

- **Dashboard Overview**: Display key metrics on main analytics dashboard
- **Executive Summary**: Provide high-level platform health to stakeholders
- **Progress Tracking**: Monitor month-over-month growth and trends
- **Gamification**: Display milestones to engage users
- **Reporting**: Generate monthly/quarterly performance reports

---

### 2. Get Category Analytics

⭐ **NEW - Phase 2A**: Deep-dive into category-level performance with risk assessment, false rate tracking, and source attribution.

Retrieves comprehensive analytics grouped by article category, including credibility metrics, misinformation rates, risk levels, and top sources per category.

#### Endpoint

```http
GET /api/v1/analytics/categories
```

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `days` | integer | No | `30` | Time period for analysis (1-365 days) |
| `min_articles` | integer | No | `5` | Minimum articles to include category (1-100) |
| `sort_by` | string | No | `credibility` | Sort field: `credibility`, `volume`, `false_rate` |

#### Request Examples

**Basic Request:**
```http
GET /api/v1/analytics/categories?days=30
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**With Sorting:**
```http
GET /api/v1/analytics/categories?days=7&min_articles=10&sort_by=false_rate
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response

**Status Code:** `200 OK`

```json
{
  "categories": [
    {
      "category": "politics",
      "articles_count": 50,
      "avg_credibility": 72.5,
      "false_rate": 16.0,
      "misleading_rate": 10.0,
      "risk_level": "high",
      "top_sources": ["CNN", "Fox News", "BBC"]
    },
    {
      "category": "health",
      "articles_count": 25,
      "avg_credibility": 88.5,
      "false_rate": 4.0,
      "misleading_rate": 0.0,
      "risk_level": "low",
      "top_sources": ["WHO", "CDC", "WebMD"]
    }
  ],
  "total_categories": 2,
  "period": {
    "days": 30,
    "start_date": "2025-10-01T00:00:00Z",
    "end_date": "2025-10-31T00:00:00Z"
  },
  "criteria": {
    "min_articles": 5,
    "sort_by": "credibility"
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `categories` | array | List of category-level analytics |
| `categories[].category` | string | Category name (e.g., "politics", "health") |
| `categories[].articles_count` | integer | Number of articles in this category |
| `categories[].avg_credibility` | decimal | Average credibility score (0-100) |
| `categories[].false_rate` | decimal | Percentage of false articles (%) |
| `categories[].misleading_rate` | decimal | Percentage of misleading articles (%) |
| `categories[].risk_level` | string | Risk assessment: `low`, `medium`, `high`, `critical` |
| `categories[].top_sources` | array | Top 3 sources by volume in this category |
| `total_categories` | integer | Total number of categories |
| `period.days` | integer | Time period analyzed |
| `period.start_date` | string (ISO 8601) | Start of analysis period |
| `period.end_date` | string (ISO 8601) | End of analysis period |
| `criteria.min_articles` | integer | Minimum articles filter applied |
| `criteria.sort_by` | string | Sorting method used |

#### Risk Level Calculation

| Risk Level | Criteria |
|------------|----------|
| `low` | False rate < 10% AND Credibility > 80 |
| `medium` | False rate 10-20% OR Credibility 60-80 |
| `high` | False rate 20-30% OR Credibility 40-60 |
| `critical` | False rate > 30% OR Credibility < 40 |

#### Use Cases

- **Category Filtering**: Allow users to filter by category risk level
- **Content Moderation**: Identify high-risk categories needing attention
- **Source Prioritization**: Show which sources dominate each category
- **Topic Analysis**: Compare misinformation rates across topics
- **Alert Systems**: Trigger warnings for categories with high false rates
- **Editorial Planning**: Focus fact-checking resources on high-risk categories

---

### 3. Get Verdict Details

⭐ **NEW**: Comprehensive verdict analytics with distribution, confidence correlation, temporal trends, and risk indicators.

Retrieves in-depth analytics on fact-check verdicts, including distribution breakdowns, confidence levels by verdict type, daily temporal trends, and risk assessment for false/misleading content.

#### Endpoint

```http
GET /api/v1/analytics/verdict-details
```

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `days` | integer | No | `30` | Time period for analysis (1-365 days) |

#### Request Example

```http
GET /api/v1/analytics/verdict-details?days=30
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response

**Status Code:** `200 OK`

```json
{
  "period": {
    "days": 30,
    "start_date": "2025-10-01T00:00:00Z",
    "end_date": "2025-10-31T00:00:00Z"
  },
  "verdict_distribution": [
    {
      "verdict": "TRUE",
      "count": 45,
      "percentage": 45.0,
      "avg_credibility_score": 85.5
    },
    {
      "verdict": "FALSE",
      "count": 15,
      "percentage": 15.0,
      "avg_credibility_score": 25.3
    },
    {
      "verdict": "MISLEADING",
      "count": 10,
      "percentage": 10.0,
      "avg_credibility_score": 35.0
    }
  ],
  "confidence_by_verdict": {
    "TRUE": {
      "avg_confidence": 0.892,
      "min_confidence": 0.750,
      "max_confidence": 0.990,
      "sample_size": 45
    },
    "FALSE": {
      "avg_confidence": 0.812,
      "min_confidence": 0.700,
      "max_confidence": 0.950,
      "sample_size": 15
    }
  },
  "temporal_trends": [
    {
      "date": "2025-10-30",
      "verdicts": {
        "TRUE": 5,
        "FALSE": 2,
        "MISLEADING": 1
      }
    }
  ],
  "risk_indicators": {
    "false_misleading_verdicts": [
      {
        "verdict": "FALSE",
        "count": 15,
        "avg_credibility": 25.3,
        "avg_confidence": 0.812
      },
      {
        "verdict": "MISLEADING",
        "count": 10,
        "avg_credibility": 35.0,
        "avg_confidence": 0.785
      }
    ],
    "total_risk_count": 25,
    "risk_percentage": 25.0,
    "overall_risk_level": "high"
  },
  "summary": {
    "total_verdicts": 100,
    "unique_verdict_types": 5,
    "most_common_verdict": "TRUE"
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `period.days` | integer | Time period analyzed |
| `period.start_date` | string (ISO 8601) | Start of analysis period |
| `period.end_date` | string (ISO 8601) | End of analysis period |
| `verdict_distribution` | array | Breakdown of all verdicts with percentages |
| `verdict_distribution[].verdict` | string | Verdict type (TRUE, FALSE, MISLEADING, etc.) |
| `verdict_distribution[].count` | integer | Number of this verdict |
| `verdict_distribution[].percentage` | decimal | Percentage of total verdicts |
| `verdict_distribution[].avg_credibility_score` | decimal | Average credibility score for this verdict (0-100) |
| `confidence_by_verdict` | object | Confidence statistics grouped by verdict |
| `confidence_by_verdict.<verdict>.avg_confidence` | decimal | Average confidence level (0-1) |
| `confidence_by_verdict.<verdict>.min_confidence` | decimal | Minimum confidence observed |
| `confidence_by_verdict.<verdict>.max_confidence` | decimal | Maximum confidence observed |
| `confidence_by_verdict.<verdict>.sample_size` | integer | Number of fact-checks |
| `temporal_trends` | array | Daily verdict counts over time |
| `temporal_trends[].date` | string (ISO date) | Date of data point |
| `temporal_trends[].verdicts` | object | Verdict counts for this date |
| `risk_indicators` | object | Risk analysis for false/misleading content |
| `risk_indicators.false_misleading_verdicts` | array | Details of risky verdicts |
| `risk_indicators.total_risk_count` | integer | Total false/misleading verdicts |
| `risk_indicators.risk_percentage` | decimal | Percentage of risky content |
| `risk_indicators.overall_risk_level` | string | Overall risk: `low`, `medium`, `high`, `critical` |
| `summary.total_verdicts` | integer | Total number of verdicts analyzed |
| `summary.unique_verdict_types` | integer | Number of distinct verdict types |
| `summary.most_common_verdict` | string | Most frequently occurring verdict |

#### Risk Level Thresholds

| Risk Level | Criteria |
|------------|----------|
| `low` | False/misleading rate < 15% |
| `medium` | False/misleading rate 15-24% |
| `high` | False/misleading rate 25-39% |
| `critical` | False/misleading rate ≥ 40% |

#### Use Cases

- **Content Quality Monitoring**: Track overall verdict distribution and identify trends
- **Confidence Analysis**: Understand how confidence levels correlate with different verdicts
- **Trend Detection**: Spot patterns in verdicts over time for early warning
- **Risk Assessment**: Identify periods or patterns with high false/misleading content
- **Performance Metrics**: Measure fact-checking accuracy and coverage
- **Alert Systems**: Trigger warnings when risk levels exceed thresholds
- **Data Visualization**: Power charts and graphs showing verdict breakdowns

---

### 4. Get Source Reliability Statistics

Retrieves aggregated credibility metrics for RSS sources based on their fact-checked articles.

#### Endpoint

```http
GET /api/v1/analytics/sources
```

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `days` | integer | No | `30` | Time period for analysis (1-365 days) |
| `min_articles` | integer | No | `5` | Minimum articles required to include source (1-100) |

#### Request Example

```http
GET /api/v1/analytics/sources?days=30&min_articles=5
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response

**Status Code:** `200 OK`

```json
{
  "sources": [
    {
      "source_id": "550e8400-e29b-41d4-a716-446655440000",
      "source_name": "TechNews Daily",
      "category": "technology",
      "articles_count": 25,
      "avg_score": 82.5,
      "avg_confidence": 0.88
    },
    {
      "source_id": "660e8400-e29b-41d4-a716-446655440001",
      "source_name": "Health Monitor",
      "category": "health",
      "articles_count": 18,
      "avg_score": 75.3,
      "avg_confidence": 0.82
    }
  ],
  "total_sources": 2,
  "period": {
    "days": 30,
    "start_date": "2025-10-01T00:00:00Z",
    "end_date": "2025-10-31T00:00:00Z"
  },
  "criteria": {
    "min_articles": 5
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `sources` | array | List of source reliability statistics |
| `sources[].source_id` | string (UUID) | Unique identifier for the RSS source |
| `sources[].source_name` | string | Name of the news source |
| `sources[].category` | string | Content category (e.g., "technology", "health") |
| `sources[].articles_count` | integer | Number of fact-checked articles from this source |
| `sources[].avg_score` | decimal | Average credibility score (0-100) |
| `sources[].avg_confidence` | decimal | Average confidence level (0-1) |
| `total_sources` | integer | Total number of sources matching criteria |
| `period.days` | integer | Time period analyzed |
| `period.start_date` | string (ISO 8601) | Start of analysis period |
| `period.end_date` | string (ISO 8601) | End of analysis period |
| `criteria.min_articles` | integer | Minimum articles filter applied |

#### Use Cases

- **Source Ranking Dashboard**: Display most reliable news sources
- **Content Curation**: Prioritize articles from high-credibility sources
- **Trend Detection**: Identify sources with declining credibility
- **Category Analysis**: Compare source reliability across different topics

---

### 4. Get Fact-Check Trends

Retrieves temporal trends of fact-checking activity with configurable granularity.

#### Endpoint

```http
GET /api/v1/analytics/trends
```

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `days` | integer | No | `30` | Time period for analysis (1-365 days) |
| `granularity` | string | No | `daily` | Time bucket size: `hourly`, `daily`, `weekly` |
| `source_id` | string (UUID) | No | `null` | Filter by specific RSS source |
| `category` | string | No | `null` | Filter by article category |

#### Constraints

- **Hourly granularity** is only supported for up to 7 days
- **Daily granularity** supports 1-365 days
- **Weekly granularity** supports 7-365 days

#### Request Examples

**Basic Request:**
```http
GET /api/v1/analytics/trends?days=30&granularity=daily
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**With Filters:**
```http
GET /api/v1/analytics/trends?days=7&granularity=hourly&source_id=550e8400-e29b-41d4-a716-446655440000&category=technology
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response

**Status Code:** `200 OK`

```json
{
  "time_series": [
    {
      "period": "2025-10-29T00:00:00Z",
      "articles_count": 15,
      "avg_score": 78.5,
      "avg_confidence": 0.85,
      "true_count": 8,
      "false_count": 4,
      "misleading_count": 2,
      "unverified_count": 1
    },
    {
      "period": "2025-10-30T00:00:00Z",
      "articles_count": 22,
      "avg_score": 82.3,
      "avg_confidence": 0.88,
      "true_count": 12,
      "false_count": 5,
      "misleading_count": 3,
      "unverified_count": 2
    }
  ],
  "granularity": "daily",
  "filters": {
    "days": 30,
    "source_id": null,
    "category": null
  },
  "summary": {
    "total_periods": 2,
    "overall_avg_score": 80.4,
    "overall_avg_confidence": 0.865,
    "total_articles": 37
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `time_series` | array | Ordered list of time-bucketed statistics |
| `time_series[].period` | string (ISO 8601) | Start timestamp of the time bucket |
| `time_series[].articles_count` | integer | Number of articles fact-checked in this period |
| `time_series[].avg_score` | decimal | Average credibility score for this period |
| `time_series[].avg_confidence` | decimal | Average confidence level for this period |
| `time_series[].true_count` | integer | Articles verified as TRUE |
| `time_series[].false_count` | integer | Articles verified as FALSE |
| `time_series[].misleading_count` | integer | Articles marked as MISLEADING |
| `time_series[].unverified_count` | integer | Articles that couldn't be verified |
| `granularity` | string | Time bucket size used (`hourly`, `daily`, `weekly`) |
| `filters` | object | Applied filters |
| `summary.total_periods` | integer | Number of time buckets in result |
| `summary.overall_avg_score` | decimal | Average score across all periods |
| `summary.overall_avg_confidence` | decimal | Average confidence across all periods |
| `summary.total_articles` | integer | Total articles in all periods |

#### Use Cases

- **Activity Monitoring**: Track fact-checking volume over time
- **Quality Trends**: Identify periods with declining credibility scores
- **Real-time Dashboards**: Display hourly fact-checking activity
- **Pattern Detection**: Spot weekly patterns in misinformation spread
- **Source Performance**: Track specific source reliability over time

---

### 5. Get Claims Analytics

Retrieves comprehensive statistics about individual claims extracted from articles.

#### Endpoint

```http
GET /api/v1/analytics/claims
```

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `days` | integer | No | `30` | Time period for analysis (1-365 days) |
| `verdict` | string | No | `null` | Filter by specific verdict type |

#### Valid Verdict Values

- `TRUE` - Claim is factually accurate
- `FALSE` - Claim is factually false
- `MOSTLY_TRUE` - Claim is largely accurate with minor inaccuracies
- `MOSTLY_FALSE` - Claim is largely false with some truth
- `MIXED` - Claim contains both true and false elements
- `MISLEADING` - Claim is technically true but misleading
- `UNVERIFIED` - Claim cannot be verified

#### Request Examples

**All Claims:**
```http
GET /api/v1/analytics/claims?days=30
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Filtered by Verdict:**
```http
GET /api/v1/analytics/claims?days=30&verdict=FALSE
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response

**Status Code:** `200 OK`

```json
{
  "period_days": 30,
  "total_fact_checks": 150,
  "claims_summary": {
    "total_claims": 487,
    "claims_true": 210,
    "claims_false": 85,
    "claims_misleading": 120,
    "claims_unverified": 72,
    "accuracy_rate": 43.12
  },
  "verdict_distribution": [
    {
      "verdict": "TRUE",
      "count": 68,
      "percentage": 45.33,
      "avg_score": 88.5
    },
    {
      "verdict": "FALSE",
      "count": 32,
      "percentage": 21.33,
      "avg_score": 22.3
    },
    {
      "verdict": "MISLEADING",
      "count": 28,
      "percentage": 18.67,
      "avg_score": 45.8
    },
    {
      "verdict": "MOSTLY_TRUE",
      "count": 15,
      "percentage": 10.00,
      "avg_score": 72.1
    },
    {
      "verdict": "UNVERIFIED",
      "count": 7,
      "percentage": 4.67,
      "avg_score": 50.0
    }
  ],
  "quality_metrics": {
    "avg_credibility_score": 62.5,
    "avg_confidence": 0.84,
    "high_confidence_rate": 78.5
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `period_days` | integer | Time period analyzed |
| `total_fact_checks` | integer | Number of fact-checked articles |
| `claims_summary.total_claims` | integer | Total individual claims analyzed |
| `claims_summary.claims_true` | integer | Claims verified as true |
| `claims_summary.claims_false` | integer | Claims verified as false |
| `claims_summary.claims_misleading` | integer | Claims marked as misleading |
| `claims_summary.claims_unverified` | integer | Claims that couldn't be verified |
| `claims_summary.accuracy_rate` | decimal | Percentage of true claims (%) |
| `verdict_distribution` | array | Breakdown by article verdict |
| `verdict_distribution[].verdict` | string | Verdict category |
| `verdict_distribution[].count` | integer | Number of articles with this verdict |
| `verdict_distribution[].percentage` | decimal | Percentage of total articles (%) |
| `verdict_distribution[].avg_score` | decimal | Average credibility score for this verdict |
| `quality_metrics.avg_credibility_score` | decimal | Overall average credibility (0-100) |
| `quality_metrics.avg_confidence` | decimal | Overall average confidence (0-1) |
| `quality_metrics.high_confidence_rate` | decimal | Percentage of high-confidence verdicts (%) |

#### Use Cases

- **Misinformation Tracking**: Monitor false claims over time
- **Accuracy Reports**: Generate claim accuracy reports
- **Content Moderation**: Identify articles with high false claim rates
- **Research & Analysis**: Study patterns in misinformation
- **Public Dashboards**: Display fact-checking statistics to users

---

## Data Models

### Source Reliability

```typescript
interface SourceReliability {
  source_id: string;          // UUID
  source_name: string;
  category: string;
  articles_count: number;
  avg_score: number;          // 0-100
  avg_confidence: number;     // 0-1
}
```

### Temporal Trend Point

```typescript
interface TrendPoint {
  period: string;             // ISO 8601 timestamp
  articles_count: number;
  avg_score: number;          // 0-100
  avg_confidence: number;     // 0-1
  true_count: number;
  false_count: number;
  misleading_count: number;
  unverified_count: number;
}
```

### Verdict Distribution

```typescript
interface VerdictDistribution {
  verdict: string;            // 'TRUE', 'FALSE', etc.
  count: number;
  percentage: number;         // 0-100
  avg_score: number;          // 0-100
}
```

---

## Error Responses

### 400 Bad Request

Returned when request parameters are invalid.

```json
{
  "detail": "days must be between 1 and 365"
}
```

**Common Validation Errors:**
- `days must be between 1 and 365`
- `min_articles must be between 1 and 100`
- `Invalid granularity. Must be: hourly, daily, weekly`
- `Hourly granularity is only supported for up to 7 days`
- `Invalid verdict. Must be one of: TRUE, FALSE, MOSTLY_TRUE, MOSTLY_FALSE, MIXED, MISLEADING, UNVERIFIED`

### 401 Unauthorized

Returned when authentication token is missing or invalid.

```json
{
  "detail": "Not authenticated"
}
```

### 404 Not Found

Returned when a specified resource doesn't exist.

```json
{
  "detail": "Source not found"
}
```

### 500 Internal Server Error

Returned when an unexpected server error occurs.

```json
{
  "detail": "Failed to retrieve analytics data"
}
```

---

## Usage Examples

### Python (requests)

```python
import requests

# Configuration
API_BASE = "http://localhost:8000/api/v1/analytics"
TOKEN = "your_jwt_token_here"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

# Get aggregate statistics (Phase 2A)
response = requests.get(
    f"{API_BASE}/stats",
    headers=headers,
    params={"include_lifetime": True, "include_trends": True}
)
stats = response.json()

# Get category analytics (Phase 2A)
response = requests.get(
    f"{API_BASE}/categories",
    headers=headers,
    params={"days": 30, "min_articles": 5, "sort_by": "false_rate"}
)
categories = response.json()

# Get source reliability
response = requests.get(
    f"{API_BASE}/sources",
    headers=headers,
    params={"days": 30, "min_articles": 10}
)
sources = response.json()

# Get daily trends
response = requests.get(
    f"{API_BASE}/trends",
    headers=headers,
    params={
        "days": 7,
        "granularity": "daily",
        "category": "technology"
    }
)
trends = response.json()

# Get claims analytics
response = requests.get(
    f"{API_BASE}/claims",
    headers=headers,
    params={"days": 30, "verdict": "FALSE"}
)
claims = response.json()
```

### JavaScript (fetch)

```javascript
const API_BASE = 'http://localhost:8000/api/v1/analytics';
const TOKEN = 'your_jwt_token_here';

const headers = {
  'Authorization': `Bearer ${TOKEN}`,
  'Content-Type': 'application/json'
};

// Get aggregate statistics (Phase 2A)
const stats = await fetch(
  `${API_BASE}/stats?include_lifetime=true&include_trends=true`,
  { headers }
).then(res => res.json());

// Get category analytics (Phase 2A)
const categories = await fetch(
  `${API_BASE}/categories?days=30&sort_by=false_rate`,
  { headers }
).then(res => res.json());

// Get source reliability
const sources = await fetch(
  `${API_BASE}/sources?days=30&min_articles=5`,
  { headers }
).then(res => res.json());

// Get hourly trends
const trends = await fetch(
  `${API_BASE}/trends?days=7&granularity=hourly`,
  { headers }
).then(res => res.json());

// Get claims analytics
const claims = await fetch(
  `${API_BASE}/claims?days=30`,
  { headers }
).then(res => res.json());
```

### cURL

```bash
# Set your token
TOKEN="your_jwt_token_here"

# Get aggregate statistics (Phase 2A)
curl -X GET "http://localhost:8000/api/v1/analytics/stats?include_lifetime=true&include_trends=true" \
  -H "Authorization: Bearer $TOKEN"

# Get category analytics (Phase 2A)
curl -X GET "http://localhost:8000/api/v1/analytics/categories?days=30&min_articles=5&sort_by=false_rate" \
  -H "Authorization: Bearer $TOKEN"

# Get source reliability
curl -X GET "http://localhost:8000/api/v1/analytics/sources?days=30&min_articles=5" \
  -H "Authorization: Bearer $TOKEN"

# Get daily trends with filters
curl -X GET "http://localhost:8000/api/v1/analytics/trends?days=30&granularity=daily&category=technology" \
  -H "Authorization: Bearer $TOKEN"

# Get claims analytics
curl -X GET "http://localhost:8000/api/v1/analytics/claims?days=30&verdict=FALSE" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Rate Limits

Analytics endpoints have the following rate limits:

- **Authenticated requests:** 100 requests per minute per user
- **Burst limit:** 200 requests per minute (temporary spike)

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1698765432
```

---

## Performance Considerations

### Caching

- Analytics data is cached for **5 minutes**
- Subsequent identical requests within the cache window return cached results
- Cache keys include all query parameters

### Query Optimization

- **Use appropriate time ranges**: Shorter periods (7-30 days) are faster than longer ones
- **Apply filters**: Filter by `source_id` or `category` to reduce result set size
- **Choose granularity wisely**: Hourly queries are more expensive than daily/weekly

### Best Practices

1. **Paginate large datasets**: For long time periods, break requests into smaller chunks
2. **Use webhooks for real-time updates**: Instead of polling, subscribe to analytics events
3. **Cache responses client-side**: Store analytics data locally when appropriate
4. **Request only needed data**: Use filters to reduce payload size

---

## Changelog

### Version 1.1.0 (2025-10-31) - Phase 2A

**New Endpoints**

- ⭐ **Aggregate Statistics** (`/api/v1/analytics/stats`)
  - Lifetime metrics and monthly comparisons
  - Month-over-month trend calculations
  - Platform milestone tracking
  - Dashboard overview optimized

- ⭐ **Category Analytics** (`/api/v1/analytics/categories`) 
  - Category-level credibility metrics
  - False rate and misleading rate tracking
  - Risk level assessment (low/medium/high/critical)
  - Top sources per category
  - Flexible sorting (credibility, volume, false_rate)

**Testing**

- ✅ 16 integration tests for Phase 2A endpoints
- ✅ 100% test coverage maintained
- ✅ Validation testing for all parameters
- ✅ Error handling verification

### Version 1.0.0 (2025-10-31)

**Initial Release**

- ✅ Source reliability statistics endpoint
- ✅ Temporal trends with hourly/daily/weekly granularity
- ✅ Claims analytics with verdict distribution
- ✅ Comprehensive filtering and parameter validation
- ✅ 76 unit tests with 100% coverage

---

## Support

For questions, issues, or feature requests:

- **Documentation**: [README.md](../README.md)
- **API Issues**: Create an issue in the GitHub repository
- **Email**: support@example.com

---

## License

This API is part of the RSS-Feed Backend project. See [LICENSE](../LICENSE) for details.
