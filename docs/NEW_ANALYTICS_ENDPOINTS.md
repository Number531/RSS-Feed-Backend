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

**Last Updated**: November 7, 2025
**Version**: 1.2.0

---

## 5. Get Detailed Fact-Check (with ALL Sources & Evidence)

**NEW in v1.2.0**: Retrieve the **complete** fact-check details including ALL individual source references, evidence quotes, and citation metadata that were used during the fact-checking process.

### Endpoint

```http
GET /api/v1/articles/{article_id}/fact-check/detailed
```

### Path Parameters

| Parameter    | Type   | Required | Description                  |
|--------------|--------|----------|------------------------------|
| `article_id` | string | Yes      | UUID of the article          |

### What's Different from the Summary Endpoint?

The standard `/fact-check` endpoint returns **summarized** data with evidence counts and breakdowns. This **detailed** endpoint fetches **complete granular data** from the Railway API:

| Standard Endpoint                | Detailed Endpoint                                    |
|----------------------------------|------------------------------------------------------|
| ✅ Overall verdict + score       | ✅ Overall verdict + score                            |
| ✅ Evidence *counts*             | ✅ Evidence *counts* + **full evidence quotes**        |
| ✅ Source *breakdown* by type    | ✅ Source *breakdown* + **individual source references** |
| ❌ Individual sources             | ✅ **All source URLs, titles, credibility ratings**   |
| ❌ Evidence quotes               | ✅ **Supporting, contradicting, and context quotes**  |
| ❌ Citation IDs                  | ✅ **Traceable citation IDs**                         |

### Request Example

```http
GET /api/v1/articles/fadb7b72-de4f-407a-91b9-bcbce8a7ae87/fact-check/detailed
```

### Response

**Status Code:** `200 OK`

```json
{
  "id": "8b2e1d3c-4f5a-6b7c-8d9e-0f1a2b3c4d5e",
  "article_id": "fadb7b72-de4f-407a-91b9-bcbce8a7ae87",
  "job_id": "2c23d1cd-d571-47be-bc0b-7465f007fec9",
  "verdict": "MOSTLY TRUE",
  "credibility_score": 82,
  "confidence": 0.87,
  "summary": "Article contains mostly accurate information with minor issues",
  "claims_analyzed": 4,
  "claims_validated": 4,
  "claims_true": 2,
  "claims_false": 0,
  "claims_misleading": 2,
  "claims_unverified": 0,
  "claims": [
    {
      "claim_text": "U.S. District Judge ordered Trump admin to fund SNAP by Friday",
      "claim_index": 0,
      "category": "Iterative Claim",
      "risk_level": "HIGH",
      "verdict": "MOSTLY TRUE",
      "confidence": 0.9,
      "summary": "The claim is largely accurate. Judge John McConnell...",
      "key_evidence": {
        "supporting": [
          "Court order dated November 6, 2025 explicitly requires full SNAP funding by November 7",
          "Judge John McConnell's ruling cited administration's failure to comply with federal law"
        ],
        "contradicting": [],
        "context": [
          "SNAP provides food assistance to over 40 million Americans",
          "Previous administration had attempted to reduce SNAP funding through regulatory changes"
        ]
      },
      "references": [
        {
          "citation_id": 1,
          "title": "Judge orders Trump admin to restore SNAP funding by Friday",
          "url": "https://apnews.com/article/snap-funding-court-order-2025",
          "source": "AP News",
          "credibility": "HIGH",
          "relevance_score": 0.95,
          "published_date": "2025-11-06"
        },
        {
          "citation_id": 2,
          "title": "Federal court mandates immediate SNAP restoration",
          "url": "https://reuters.com/legal/snap-court-ruling",
          "source": "Reuters",
          "credibility": "HIGH",
          "relevance_score": 0.93
        },
        {
          "citation_id": 3,
          "title": "Rhode Island court rules on SNAP funding",
          "url": "https://providence-journal.com/snap-ruling",
          "source": "Providence Journal",
          "credibility": "MEDIUM",
          "relevance_score": 0.88
        }
      ],
      "evidence_count": 35,
      "evidence_breakdown": {
        "news": 10,
        "general": 10,
        "research": 10,
        "historical": 5
      },
      "validation_mode": "thorough"
    }
  ],
  "total_sources": 140,
  "source_consensus": "STRONG_AGREEMENT",
  "validation_mode": "iterative",
  "processing_time_seconds": 301,
  "api_costs": {
    "total": 0.012,
    "validation": 0.008,
    "research": 0.004
  },
  "fact_checked_at": "2025-11-07T05:34:59Z"
}
```

### Response Fields

| Field                          | Type                | Description                                           |
|--------------------------------|---------------------|-------------------------------------------------------|
| `id`                           | string (UUID)       | Fact-check record ID                                  |
| `article_id`                   | string (UUID)       | Article identifier                                    |
| `job_id`                       | string              | Railway API job ID (for traceability)                 |
| `verdict`                      | string              | Overall verdict                                       |
| `credibility_score`            | integer             | Overall credibility (0-100)                           |
| `confidence`                   | decimal             | AI confidence (0.0-1.0)                               |
| `summary`                      | string              | Overall analysis summary                              |
| `claims_analyzed`              | integer             | Total claims analyzed                                 |
| `claims_validated`             | integer             | Claims successfully validated                         |
| `claims_true`                  | integer             | Count of TRUE verdicts                                |
| `claims_false`                 | integer             | Count of FALSE verdicts                               |
| `claims_misleading`            | integer             | Count of MISLEADING verdicts                          |
| `claims_unverified`            | integer             | Count of UNVERIFIED claims                            |
| **`claims`**                   | **array**           | **Detailed claim analysis (KEY NEW DATA)**            |
| `claims[].claim_text`          | string              | Original claim statement                              |
| `claims[].claim_index`         | integer             | Zero-based claim index                                |
| `claims[].category`            | string              | Claim category                                        |
| `claims[].risk_level`          | string              | Risk level (HIGH, MEDIUM, LOW)                        |
| `claims[].verdict`             | string              | Claim verdict                                         |
| `claims[].confidence`          | decimal             | Confidence for this claim                             |
| `claims[].summary`             | string              | Detailed claim analysis                               |
| **`claims[].key_evidence`**    | **object**          | **Categorized evidence quotes (NEW)**                 |
| `claims[].key_evidence.supporting` | array (string)  | Evidence supporting the claim                         |
| `claims[].key_evidence.contradicting` | array (string) | Evidence contradicting the claim                      |
| `claims[].key_evidence.context` | array (string)     | Background context information                        |
| **`claims[].references`**      | **array**           | **Individual source citations (NEW)**                 |
| `claims[].references[].citation_id` | integer        | Unique citation identifier                            |
| `claims[].references[].title`  | string              | Source article/document title                         |
| `claims[].references[].url`    | string              | Direct URL to source                                  |
| `claims[].references[].source` | string              | Source name (e.g., "Reuters", "AP News")              |
| `claims[].references[].credibility` | string         | Source credibility rating (HIGH, MEDIUM, LOW)         |
| `claims[].references[].relevance_score` | decimal    | Relevance to claim (0.0-1.0)                          |
| `claims[].references[].published_date` | string      | Source publication date                               |
| `claims[].evidence_count`      | integer             | Total evidence items for this claim                   |
| `claims[].evidence_breakdown`  | object              | Evidence by type (news, research, etc.)               |
| `claims[].validation_mode`     | string              | Validation mode used                                  |
| `total_sources`                | integer             | Total unique sources across all claims                |
| `source_consensus`             | string              | Overall source agreement level                        |
| `validation_mode`              | string              | Overall validation mode                               |
| `processing_time_seconds`      | integer             | Time taken for fact-check                             |
| `api_costs`                    | object              | Breakdown of API costs                                |
| `fact_checked_at`              | string (ISO 8601)   | Timestamp of fact-check completion                    |

### Performance Notes

**Important:** This endpoint fetches data **on-demand** from the Railway API, which may take 1-2 seconds. The standard `/fact-check` endpoint is faster because it reads from the database.

**Use cases:**
- Displaying full source list for transparency
- Citation tracking and verification  
- Academic analysis requiring source metadata
- Detailed evidence inspection
- Building trust indicators with source details

**Optimization:**
- Cache results client-side when possible
- Use the lightweight `/claims` endpoint for navigation
- Reserve this endpoint for user-initiated "View Details" actions

### Error Responses

**404 Not Found** - Article has no fact-check
```json
{
  "detail": "No fact-check found for this article"
}
```

**503 Service Unavailable** - Railway API unavailable or job expired
```json
{
  "detail": "Failed to fetch detailed results from Railway API: Job expired or API unavailable"
}
```

---

## 6. List Article Claims (Lightweight)

Retrieve a **lightweight list** of all claims in an article WITHOUT fetching full evidence and sources. Useful for navigation and overview UIs.

### Endpoint

```http
GET /api/v1/articles/{article_id}/fact-check/claims
```

### Path Parameters

| Parameter    | Type   | Required | Description                  |
|--------------|--------|----------|------------------------------|
| `article_id` | string | Yes      | UUID of the article          |

### Request Example

```http
GET /api/v1/articles/fadb7b72-de4f-407a-91b9-bcbce8a7ae87/fact-check/claims
```

### Response

**Status Code:** `200 OK`

```json
{
  "article_id": "fadb7b72-de4f-407a-91b9-bcbce8a7ae87",
  "total_claims": 4,
  "claims": [
    {
      "claim_index": 0,
      "claim_text": "U.S. District Judge ordered Trump admin to fund SNAP by Friday",
      "category": "Iterative Claim",
      "risk_level": "HIGH",
      "verdict": "MOSTLY TRUE",
      "confidence": 0.9,
      "evidence_count": 35
    },
    {
      "claim_index": 1,
      "claim_text": "SNAP provides food assistance to over 40 million Americans",
      "category": "Iterative Claim",
      "risk_level": "MEDIUM",
      "verdict": "TRUE",
      "confidence": 0.95,
      "evidence_count": 30
    },
    {
      "claim_index": 2,
      "claim_text": "Previous administration attempted to reduce SNAP funding",
      "category": "Iterative Claim",
      "risk_level": "MEDIUM",
      "verdict": "MOSTLY TRUE",
      "confidence": 0.85,
      "evidence_count": 40
    },
    {
      "claim_index": 3,
      "claim_text": "Rhode Island federal court issued the ruling",
      "category": "Iterative Claim",
      "risk_level": "LOW",
      "verdict": "TRUE",
      "confidence": 0.98,
      "evidence_count": 35
    }
  ]
}
```

### Response Fields

| Field                       | Type          | Description                                           |
|-----------------------------|---------------|-------------------------------------------------------|
| `article_id`                | string (UUID) | Article identifier                                    |
| `total_claims`              | integer       | Total number of claims                                |
| `claims`                    | array         | List of claim summaries                               |
| `claims[].claim_index`      | integer       | Zero-based claim index                                |
| `claims[].claim_text`       | string        | Original claim statement                              |
| `claims[].category`         | string        | Claim category                                        |
| `claims[].risk_level`       | string        | Risk level (HIGH, MEDIUM, LOW)                        |
| `claims[].verdict`          | string        | Claim verdict                                         |
| `claims[].confidence`       | decimal       | AI confidence (0.0-1.0)                               |
| `claims[].evidence_count`   | integer       | Total evidence items                                  |

**Note:** This endpoint does **NOT** include:
- Individual source references
- Evidence quotes
- Citation details

Use the detailed endpoint (`/fact-check/detailed`) to get full information.

### Use Cases

- **Navigation UI**: Display claim list for user to select
- **Quick Overview**: Show claim count and verdicts
- **Search Results**: Include claim summaries in search
- **Mobile Apps**: Lightweight payload for mobile devices

### Error Responses

**404 Not Found** - Article has no fact-check
```json
{
  "detail": "No fact-check found for this article"
}
```

---

## Endpoint Comparison Summary

| Endpoint                                         | Speed  | Data Included                                      | Use Case                              |
|--------------------------------------------------|--------|-----------------------------------------------------|---------------------------------------|
| `GET /articles/{id}/fact-check`                  | Fast   | Overall verdict, claim summaries, evidence counts   | General fact-check display            |
| `GET /articles/{id}/fact-check/claims`           | Fast   | Lightweight claim list (no sources)                 | Navigation, claim overview            |
| `GET /articles/{id}/fact-check/detailed`         | Slower | **EVERYTHING**: sources, evidence quotes, citations | Detailed inspection, source transparency |

---

## Integration Example: React Component

```tsx
import React, { useState, useEffect } from 'react';

interface ClaimReference {
  citation_id: number;
  title: string;
  url: string;
  source: string;
  credibility: string;
  relevance_score?: number;
}

interface DetailedClaim {
  claim_text: string;
  claim_index: number;
  verdict: string;
  confidence: number;
  summary: string;
  key_evidence: {
    supporting: string[];
    contradicting: string[];
    context: string[];
  };
  references: ClaimReference[];
  evidence_count: number;
}

interface DetailedFactCheck {
  verdict: string;
  credibility_score: number;
  claims: DetailedClaim[];
  total_sources: number;
}

export const FactCheckDetailView: React.FC<{ articleId: string }> = ({ articleId }) => {
  const [factCheck, setFactCheck] = useState<DetailedFactCheck | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedClaim, setSelectedClaim] = useState<number>(0);

  useEffect(() => {
    async function loadDetails() {
      try {
        const response = await fetch(
          `/api/v1/articles/${articleId}/fact-check/detailed`
        );
        const data = await response.json();
        setFactCheck(data);
      } catch (error) {
        console.error('Failed to load detailed fact-check:', error);
      } finally {
        setLoading(false);
      }
    }
    loadDetails();
  }, [articleId]);

  if (loading) return <div>Loading detailed analysis...</div>;
  if (!factCheck) return <div>No fact-check available</div>;

  const claim = factCheck.claims[selectedClaim];

  return (
    <div className="fact-check-detail">
      <div className="overall-verdict">
        <h2>Verdict: {factCheck.verdict}</h2>
        <div className="credibility-score">
          Credibility Score: {factCheck.credibility_score}/100
        </div>
        <div className="source-count">
          {factCheck.total_sources} unique sources consulted
        </div>
      </div>

      <div className="claim-navigator">
        <h3>Claims ({factCheck.claims.length})</h3>
        {factCheck.claims.map((c, idx) => (
          <button
            key={idx}
            onClick={() => setSelectedClaim(idx)}
            className={selectedClaim === idx ? 'active' : ''}
          >
            Claim {idx + 1}: {c.verdict}
          </button>
        ))}
      </div>

      <div className="claim-detail">
        <h3>Claim {selectedClaim + 1}</h3>
        <p className="claim-text">{claim.claim_text}</p>
        <div className="verdict">
          <span className={`badge ${claim.verdict.toLowerCase()}`}>
            {claim.verdict}
          </span>
          <span className="confidence">
            {(claim.confidence * 100).toFixed(0)}% confidence
          </span>
        </div>

        <div className="summary">
          <h4>Analysis</h4>
          <p>{claim.summary}</p>
        </div>

        <div className="evidence">
          <h4>Evidence ({claim.evidence_count} items)</h4>
          
          {claim.key_evidence.supporting.length > 0 && (
            <div className="supporting">
              <h5>✅ Supporting Evidence</h5>
              <ul>
                {claim.key_evidence.supporting.map((ev, idx) => (
                  <li key={idx}>{ev}</li>
                ))}
              </ul>
            </div>
          )}

          {claim.key_evidence.contradicting.length > 0 && (
            <div className="contradicting">
              <h5>❌ Contradicting Evidence</h5>
              <ul>
                {claim.key_evidence.contradicting.map((ev, idx) => (
                  <li key={idx}>{ev}</li>
                ))}
              </ul>
            </div>
          )}

          {claim.key_evidence.context.length > 0 && (
            <div className="context">
              <h5>📚 Context</h5>
              <ul>
                {claim.key_evidence.context.map((ev, idx) => (
                  <li key={idx}>{ev}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="sources">
          <h4>Sources ({claim.references.length})</h4>
          <div className="source-list">
            {claim.references.map((ref) => (
              <div key={ref.citation_id} className="source-card">
                <div className="source-header">
                  <span className="source-name">{ref.source}</span>
                  <span className={`credibility ${ref.credibility.toLowerCase()}`}>
                    {ref.credibility}
                  </span>
                </div>
                <h5>
                  <a href={ref.url} target="_blank" rel="noopener noreferrer">
                    {ref.title}
                  </a>
                </h5>
                {ref.relevance_score && (
                  <div className="relevance">
                    Relevance: {(ref.relevance_score * 100).toFixed(0)}%
                  </div>
                )}
                <div className="citation-id">Citation ID: {ref.citation_id}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
```

---
