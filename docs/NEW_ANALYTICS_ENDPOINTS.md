# New Analytics Endpoints - Source & Risk Analysis

## Overview

This document describes 4 new analytics endpoints added to enhance source transparency and risk assessment capabilities:

1. **GET /api/v1/analytics/high-risk-articles** - Identify articles containing high-risk claims
2. **GET /api/v1/analytics/articles/{article_id}/source-breakdown** - Detailed source analysis per article
3. **GET /api/v1/analytics/source-quality** - Aggregate source quality metrics by type
4. **GET /api/v1/analytics/risk-correlation** - Risk vs credibility correlation analysis

---

## 1. Get High-Risk Articles

Retrieve articles containing high-risk claims, sorted by risk level. Useful for content moderation, editorial review prioritization, and risk monitoring.

### Endpoint

```http
GET /api/v1/analytics/high-risk-articles
```

### Query Parameters

| Parameter | Type    | Required | Default | Description                                    |
|-----------|---------|----------|---------|------------------------------------------------|
| `days`    | integer | No       | `30`    | Time period to analyze (1-365 days)            |
| `limit`   | integer | No       | `100`   | Maximum results to return (1-1000)             |
| `offset`  | integer | No       | `0`     | Pagination offset                              |

### Request Example

```http
GET /api/v1/analytics/high-risk-articles?days=7&limit=50&offset=0
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Response

**Status Code:** `200 OK`

```json
{
  "articles": [
    {
      "article_id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Misleading Claims About Vaccine Effectiveness",
      "author": "John Smith",
      "url": "https://example.com/article/1234",
      "source_name": "NewsSource1",
      "published_at": "2025-10-29T14:30:00Z",
      "fact_check_id": "f8e2f567-1234-56d3-b789-123456789abc",
      "verdict": "FALSE",
      "credibility_score": 25,
      "confidence_score": 0.85,
      "num_sources": 105,
      "high_risk_claims_count": 5
    }
  ],
  "total": 127,
  "pagination": {
    "limit": 50,
    "offset": 0,
    "has_more": true
  }
}
```

### Response Fields

| Field                           | Type                | Description                                           |
|---------------------------------|---------------------|-------------------------------------------------------|
| `articles`                      | array               | List of high-risk articles                            |
| `articles[].article_id`         | string (UUID)       | Unique article identifier                             |
| `articles[].title`              | string              | Article title                                         |
| `articles[].author`             | string \| null      | Article author                                        |
| `articles[].url`                | string              | Article URL                                           |
| `articles[].source_name`        | string              | RSS source name                                       |
| `articles[].published_at`       | string (ISO 8601)   | Publication timestamp                                 |
| `articles[].fact_check_id`      | string (UUID)       | Associated fact-check ID                              |
| `articles[].verdict`            | string              | Fact-check verdict (TRUE, FALSE, MIXED, etc.)         |
| `articles[].credibility_score`  | integer             | Credibility score (0-100)                             |
| `articles[].confidence_score`   | decimal             | AI confidence level (0.0-1.0)                         |
| `articles[].num_sources`        | integer             | Total sources used in fact-check                      |
| `articles[].high_risk_claims_count` | integer        | Number of high-risk claims detected                   |
| `total`                         | integer             | Total count of matching articles                      |
| `pagination.limit`              | integer             | Requested page size                                   |
| `pagination.offset`             | integer             | Current offset                                        |
| `pagination.has_more`           | boolean             | Whether more results are available                    |

### Use Cases

- **Content Moderation**: Flag articles requiring immediate review
- **Editorial Workflow**: Prioritize fact-checking resources
- **Risk Dashboards**: Monitor high-risk content trends
- **Alerting Systems**: Trigger notifications for high-risk spikes

### Error Responses

**400 Bad Request** - Invalid parameters
```json
{
  "detail": "Days parameter must be between 1 and 365"
}
```

**500 Internal Server Error** - Server error
```json
{
  "detail": "Failed to retrieve high-risk articles"
}
```

---

## 2. Get Article Source Breakdown

Retrieve detailed source analysis for a specific article, including source type distribution, diversity metrics, and consensus levels.

### Endpoint

```http
GET /api/v1/analytics/articles/{article_id}/source-breakdown
```

### Path Parameters

| Parameter    | Type   | Required | Description                  |
|--------------|--------|----------|------------------------------|
| `article_id` | string | Yes      | UUID of the article          |

### Request Example

```http
GET /api/v1/analytics/articles/123e4567-e89b-12d3-a456-426614174000/source-breakdown
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Response

**Status Code:** `200 OK`

```json
{
  "article_id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Climate Change Impact Study Released",
  "source_breakdown": {
    "news": 45,
    "government": 20,
    "academic": 15,
    "social_media": 10,
    "fact_checking": 8,
    "expert": 2
  },
  "primary_source_type": "news",
  "source_diversity_score": 0.95,
  "num_sources": 100,
  "source_consensus": "MIXED"
}
```

### Response Fields

| Field                    | Type          | Description                                           |
|--------------------------|---------------|-------------------------------------------------------|
| `article_id`             | string (UUID) | Article identifier                                    |
| `title`                  | string        | Article title                                         |
| `source_breakdown`       | object        | Count of sources by type                              |
| `source_breakdown.news`  | integer       | News organization sources                             |
| `source_breakdown.government` | integer  | Government/official sources                           |
| `source_breakdown.academic` | integer     | Academic/research sources                             |
| `source_breakdown.social_media` | integer | Social media sources                                  |
| `source_breakdown.fact_checking` | integer | Fact-checking organization sources                   |
| `source_breakdown.expert` | integer      | Expert/individual sources                             |
| `source_breakdown.press_release` | integer | Press release sources                               |
| `source_breakdown.other` | integer       | Other source types                                    |
| `primary_source_type`    | string        | Most common source type                               |
| `source_diversity_score` | decimal       | Shannon entropy diversity (0.0-1.0, higher=more diverse) |
| `num_sources`            | integer       | Total unique sources                                  |
| `source_consensus`       | string        | STRONG, MODERATE, or MIXED                            |

### Source Consensus Levels

| Level      | Description                                            | Threshold       |
|------------|--------------------------------------------------------|-----------------|
| **STRONG** | High agreement among sources (≥60% from primary type)  | ≥60%            |
| **MODERATE** | Moderate agreement (40-59% from primary type)        | 40-59%          |
| **MIXED**  | Diverse sources, no clear consensus (<40% from primary) | <40%            |

### Use Cases

- **Source Transparency**: Display source composition to users
- **Credibility Verification**: Assess article reliability
- **Editorial Review**: Evaluate source quality before publication
- **Trust Indicators**: Show diversity scores as trust signals

### Error Responses

**404 Not Found** - Article not found or no fact-check data
```json
{
  "detail": "Article 123e4567-e89b-12d3-a456-426614174000 not found or has no fact-check data"
}
```

**500 Internal Server Error** - Server error
```json
{
  "detail": "Failed to retrieve source breakdown"
}
```

---

## 3. Get Source Quality Metrics

Retrieve aggregate quality metrics grouped by source type, showing average credibility, source counts, and diversity scores.

### Endpoint

```http
GET /api/v1/analytics/source-quality
```

### Query Parameters

| Parameter | Type    | Required | Default | Description                                |
|-----------|---------|----------|---------|--------------------------------------------|
| `days`    | integer | No       | `30`    | Time period to analyze (1-365 days)        |

### Request Example

```http
GET /api/v1/analytics/source-quality?days=30
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Response

**Status Code:** `200 OK`

```json
{
  "source_types": [
    {
      "source_type": "news",
      "article_count": 50,
      "avg_credibility_score": 75.50,
      "avg_num_sources": 98.20,
      "avg_diversity_score": 0.94
    },
    {
      "source_type": "government",
      "article_count": 20,
      "avg_credibility_score": 82.30,
      "avg_num_sources": 105.50,
      "avg_diversity_score": 0.88
    },
    {
      "source_type": "academic",
      "article_count": 15,
      "avg_credibility_score": 88.70,
      "avg_num_sources": 110.00,
      "avg_diversity_score": 0.92
    }
  ],
  "overall": {
    "total_articles": 85,
    "avg_credibility_score": 77.44,
    "avg_num_sources": 101.21,
    "avg_diversity_score": 0.92
  }
}
```

### Response Fields

| Field                                | Type    | Description                                       |
|--------------------------------------|---------|---------------------------------------------------|
| `source_types`                       | array   | Quality metrics by source type                    |
| `source_types[].source_type`         | string  | Source type (news, government, academic, etc.)    |
| `source_types[].article_count`       | integer | Number of articles using this primary source type |
| `source_types[].avg_credibility_score` | decimal | Average credibility (0-100)                     |
| `source_types[].avg_num_sources`     | decimal | Average source count per article                  |
| `source_types[].avg_diversity_score` | decimal | Average Shannon entropy (0.0-1.0)                 |
| `overall.total_articles`             | integer | Total articles analyzed                           |
| `overall.avg_credibility_score`      | decimal | Weighted average credibility (0-100)              |
| `overall.avg_num_sources`            | decimal | Weighted average source count                     |
| `overall.avg_diversity_score`        | decimal | Weighted average diversity (0.0-1.0)              |

### Source Types

| Type             | Description                                    |
|------------------|------------------------------------------------|
| `news`           | Traditional news organizations                 |
| `government`     | Government agencies and officials              |
| `academic`       | Universities and research institutions         |
| `social_media`   | Social media platforms                         |
| `fact_checking`  | Dedicated fact-checking organizations          |
| `expert`         | Individual expert sources                      |
| `press_release`  | Company/organization press releases            |
| `other`          | Other source types                             |

### Use Cases

- **Source Type Comparison**: Compare quality across different source types
- **Quality Benchmarking**: Set quality targets per source type
- **Editorial Guidelines**: Inform source selection policies
- **Content Strategy**: Identify high-performing source types

### Error Responses

**400 Bad Request** - Invalid parameters
```json
{
  "detail": "Days parameter must be between 1 and 365"
}
```

**500 Internal Server Error** - Server error
```json
{
  "detail": "Failed to retrieve source quality metrics"
}
```

---

## 4. Get Risk Correlation Analysis

Analyze the relationship between high-risk claims and article credibility, with insights on correlation patterns.

### Endpoint

```http
GET /api/v1/analytics/risk-correlation
```

### Query Parameters

| Parameter | Type    | Required | Default | Description                                |
|-----------|---------|----------|---------|--------------------------------------------|
| `days`    | integer | No       | `30`    | Time period to analyze (1-365 days)        |

### Request Example

```http
GET /api/v1/analytics/risk-correlation?days=30
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Response

**Status Code:** `200 OK`

```json
{
  "risk_levels": [
    {
      "risk_category": "low",
      "article_count": 30,
      "avg_credibility_score": 85.50,
      "false_verdict_count": 2,
      "false_verdict_rate": 0.07
    },
    {
      "risk_category": "medium",
      "article_count": 25,
      "avg_credibility_score": 65.30,
      "false_verdict_count": 8,
      "false_verdict_rate": 0.32
    },
    {
      "risk_category": "high",
      "article_count": 20,
      "avg_credibility_score": 35.20,
      "false_verdict_count": 15,
      "false_verdict_rate": 0.75
    }
  ],
  "insights": [
    "Strong correlation detected: High-risk claims have 75% false verdict rate vs 7% for low-risk.",
    "High-risk claims are strong indicators of false or misleading information."
  ]
}
```

### Response Fields

| Field                                | Type    | Description                                       |
|--------------------------------------|---------|---------------------------------------------------|
| `risk_levels`                        | array   | Statistics by risk category                       |
| `risk_levels[].risk_category`        | string  | Risk level: "low", "medium", or "high"            |
| `risk_levels[].article_count`        | integer | Number of articles in this risk category          |
| `risk_levels[].avg_credibility_score` | decimal | Average credibility score (0-100)                |
| `risk_levels[].false_verdict_count`  | integer | Count of FALSE verdicts                           |
| `risk_levels[].false_verdict_rate`   | decimal | Proportion of false verdicts (0.0-1.0)            |
| `insights`                           | array   | Generated correlation insights                    |

### Risk Categories

Articles are categorized based on `high_risk_claims_count`:

| Category   | High-Risk Claims Count | Description                           |
|------------|------------------------|---------------------------------------|
| **low**    | 0                      | No high-risk claims detected          |
| **medium** | 1-2                    | Small number of high-risk claims      |
| **high**   | 3+                     | Multiple high-risk claims detected    |

### Correlation Strength

The system generates insights based on false verdict rate differences:

| Strength     | Rate Difference | Interpretation                                      |
|--------------|-----------------|-----------------------------------------------------|
| **Strong**   | >30%            | High-risk claims strongly predict false information |
| **Moderate** | 15-30%          | High-risk claims moderately correlate with falsity  |
| **Weak**     | <15%            | High-risk classification alone isn't predictive     |

### Use Cases

- **Risk Modeling**: Build content moderation risk models
- **Rule Development**: Set risk-based moderation thresholds
- **Quality Assurance**: Monitor correlation patterns over time
- **Editorial Policy**: Inform risk assessment guidelines

### Error Responses

**400 Bad Request** - Invalid parameters
```json
{
  "detail": "Days parameter must be between 1 and 365"
}
```

**500 Internal Server Error** - Server error
```json
{
  "detail": "Failed to retrieve risk correlation"
}
```

---

## Implementation Notes

### Database Requirements

These endpoints require the following database enhancements (already applied):

1. `source_breakdown` - JSONB column with GIN index
2. `primary_source_type` - VARCHAR(20) for primary source classification
3. `source_diversity_score` - NUMERIC(3,2) for Shannon entropy
4. `high_risk_claims_count` - INTEGER with partial index
5. Multiple composite indexes for performance optimization

### Performance Considerations

- All endpoints use efficient database queries with proper indexing
- Responses are typically <200ms for 30-day time periods
- Pagination recommended for high-risk articles endpoint
- Consider caching for frequently accessed metrics

### Rate Limiting

Standard API rate limits apply:
- **Free tier**: 100 requests/hour
- **Pro tier**: 1,000 requests/hour
- **Enterprise**: Unlimited

---

## Complete Integration Example

### JavaScript/TypeScript Frontend

```typescript
interface HighRiskArticle {
  article_id: string;
  title: string;
  author: string | null;
  url: string;
  source_name: string;
  published_at: string;
  verdict: string;
  credibility_score: number;
  high_risk_claims_count: number;
}

interface HighRiskResponse {
  articles: HighRiskArticle[];
  total: number;
  pagination: {
    limit: number;
    offset: number;
    has_more: boolean;
  };
}

async function getHighRiskArticles(
  days: number = 30,
  limit: number = 100,
  offset: number = 0
): Promise<HighRiskResponse> {
  const response = await fetch(
    `/api/v1/analytics/high-risk-articles?days=${days}&limit=${limit}&offset=${offset}`,
    {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

async function getSourceBreakdown(articleId: string) {
  const response = await fetch(
    `/api/v1/analytics/articles/${articleId}/source-breakdown`,
    {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Article not found or no fact-check data');
    }
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}
```

### Python Backend Integration

```python
import httpx
from typing import Dict, List, Any

class AnalyticsClient:
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {auth_token}"}

    async def get_high_risk_articles(
        self,
        days: int = 30,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/analytics/high-risk-articles",
                params={"days": days, "limit": limit, "offset": offset},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_source_breakdown(self, article_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/analytics/articles/{article_id}/source-breakdown",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_source_quality(self, days: int = 30) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/analytics/source-quality",
                params={"days": days},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_risk_correlation(self, days: int = 30) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/analytics/risk-correlation",
                params={"days": days},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
```

---

## Migration Path

If upgrading from an older version of the backend:

1. **Database Migrations**: Run alembic migrations to add new columns and indexes
   ```bash
   alembic upgrade head
   ```

2. **Backfill Data**: Run backfill scripts to populate new fields for existing records
   ```bash
   python scripts/utilities/backfill_source_fields.py
   python scripts/utilities/backfill_high_risk_counts.py
   ```

3. **Update Frontend**: Integrate new endpoints as documented

4. **Monitor Performance**: Check query performance and adjust indexes if needed

---

## Support & Questions

For questions or issues with these endpoints:
- GitHub Issues: [RSS-Feed/backend/issues](https://github.com/your-org/RSS-Feed/issues)
- Documentation: `/docs/ANALYTICS_API.md`
- Email: backend-team@example.com

**Last Updated**: November 4, 2025
**Version**: 1.1.0
