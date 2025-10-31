# Analytics API Documentation

## Overview

The Analytics API provides comprehensive insights into fact-checking activities, source credibility, and temporal trends. These endpoints aggregate data from article fact-checks to help understand patterns, reliability metrics, and claim verification statistics.

**Base Path:** `/api/v1/analytics`

**Version:** 1.0.0

---

## Table of Contents

1. [Authentication](#authentication)
2. [Endpoints](#endpoints)
   - [Get Source Reliability Statistics](#1-get-source-reliability-statistics)
   - [Get Fact-Check Trends](#2-get-fact-check-trends)
   - [Get Claims Analytics](#3-get-claims-analytics)
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

### 1. Get Source Reliability Statistics

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

### 2. Get Fact-Check Trends

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

### 3. Get Claims Analytics

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
