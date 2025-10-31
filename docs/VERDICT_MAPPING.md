# Fact-Check Verdict Mapping

## Overview

This document defines the verdict categories returned by the fact-checking API and how they are mapped for outlet credibility aggregation in the RSS Feed application.

---

## Current Verdict Categories (As of 2025-10-23)

Based on live testing with Fox News Politics articles, the fact-check API returns the following verdict categories:

| Verdict | Description | Sample Count | Avg Score |
|---------|-------------|--------------|-----------|
| **TRUE** | Verified accurate claims | 3 articles | ~72 |
| **FALSE** | Demonstrably false claims | 2 articles | ~30 |
| **MOSTLY FALSE** | Primarily false with minor accurate elements | 1 article | ~30 |
| **MISLEADING** | Technically accurate but presented deceptively | 1 article | ~50 |
| **MIXED** | Contains both true and false claims | 1 article | ~55 |
| **UNVERIFIED - INSUFFICIENT EVIDENCE** | Unable to verify due to lack of sources | 1 article | ~45 |

---

## Test Results Summary

**Last Updated:** 2025-10-23  
**Test Dataset:** Fox News Politics (10 articles)  
**Success Rate:** 9/10 articles fact-checked successfully  
**Average Credibility Score:** 61.4/100  
**Processing Time:** ~7.2 minutes

### Verdict Distribution
```
TRUE                               3 articles (33%)
FALSE                              2 articles (22%)
MOSTLY FALSE                       1 article  (11%)
MISLEADING                         1 article  (11%)
MIXED                              1 article  (11%)
UNVERIFIED - INSUFFICIENT EVIDENCE 1 article  (11%)
```

---

## Aggregation Strategy for Outlet Credibility

For the outlet credibility scoring system, verdicts are grouped into **4 primary categories** to simplify frontend display and provide clear credibility metrics:

### 4-Category Grouping

```python
VERDICT_CATEGORIES = {
    'TRUE': 'true_count',
    'FALSE': 'false_count',
    'MOSTLY FALSE': 'false_count',          # Group with FALSE
    'MISLEADING': 'misleading_count',
    'MIXED': 'misleading_count',            # Group with MISLEADING  
    'UNVERIFIED - INSUFFICIENT EVIDENCE': 'unverified_count',
    'UNVERIFIED - INSUFFICIENT_EVIDENCE': 'unverified_count',  # Handle underscore variant
}
```

### Category Definitions

#### 1. ✅ TRUE (true_count)
- **Verdicts:** `TRUE`
- **Meaning:** Claims are verified as accurate by credible sources
- **Color Code:** Green
- **Score Range:** 70-100

#### 2. ❌ FALSE (false_count)  
- **Verdicts:** `FALSE`, `MOSTLY FALSE`
- **Meaning:** Claims are demonstrably incorrect or primarily false
- **Color Code:** Red
- **Score Range:** 0-40

#### 3. ⚠️ MISLEADING (misleading_count)
- **Verdicts:** `MISLEADING`, `MIXED`
- **Meaning:** Claims are technically accurate but deceptively presented, or contain both true and false elements
- **Color Code:** Orange/Yellow
- **Score Range:** 40-70

#### 4. ❓ UNVERIFIED (unverified_count)
- **Verdicts:** `UNVERIFIED - INSUFFICIENT EVIDENCE`, `UNVERIFIED - INSUFFICIENT_EVIDENCE`
- **Meaning:** Unable to verify due to lack of reliable sources or evidence
- **Color Code:** Gray
- **Score Range:** 30-60

---

## Database Schema

### Articles Table (Denormalized Cache)
```sql
articles.fact_check_score      -- Integer (0-100)
articles.fact_check_verdict    -- String (exact verdict from API)
articles.fact_checked_at       -- Timestamp
```

### Source Credibility Scores Table (Aggregated)
```sql
source_credibility_scores.average_score          -- DECIMAL(5,2)
source_credibility_scores.total_articles_checked -- Integer
source_credibility_scores.true_count             -- Integer
source_credibility_scores.false_count            -- Integer (FALSE + MOSTLY FALSE)
source_credibility_scores.misleading_count       -- Integer (MISLEADING + MIXED)
source_credibility_scores.unverified_count       -- Integer (all UNVERIFIED variants)
source_credibility_scores.period_type            -- 'daily', 'weekly', 'monthly', 'all_time'
source_credibility_scores.period_start           -- Timestamp
source_credibility_scores.period_end             -- Timestamp
source_credibility_scores.trend_data             -- JSONB (historical trends)
```

---

## Aggregation Query Logic

### SQL Query for Calculating Outlet Scores

```sql
SELECT 
  rs.source_name,
  AVG(a.fact_check_score) as average_score,
  COUNT(*) as total_articles_checked,
  
  -- TRUE count
  COUNT(*) FILTER (WHERE a.fact_check_verdict = 'TRUE') as true_count,
  
  -- FALSE count (includes MOSTLY FALSE)
  COUNT(*) FILTER (WHERE a.fact_check_verdict IN ('FALSE', 'MOSTLY FALSE')) as false_count,
  
  -- MISLEADING count (includes MIXED)
  COUNT(*) FILTER (WHERE a.fact_check_verdict IN ('MISLEADING', 'MIXED')) as misleading_count,
  
  -- UNVERIFIED count (both variants)
  COUNT(*) FILTER (WHERE 
    a.fact_check_verdict = 'UNVERIFIED - INSUFFICIENT EVIDENCE' OR
    a.fact_check_verdict = 'UNVERIFIED - INSUFFICIENT_EVIDENCE'
  ) as unverified_count

FROM articles a
JOIN rss_sources rs ON a.rss_source_id = rs.id
WHERE a.fact_check_score IS NOT NULL
  AND a.fact_checked_at >= :period_start
  AND a.fact_checked_at <= :period_end
GROUP BY rs.id, rs.source_name;
```

---

## Frontend Display Recommendations

### Outlet Credibility Card
```json
{
  "outlet_name": "Fox News",
  "category": "politics",
  "overall_score": 61.4,
  "total_articles": 10,
  "verdicts": {
    "true": 3,
    "false": 3,
    "misleading": 2,
    "unverified": 1
  },
  "percentages": {
    "true": 33.3,
    "false": 33.3,
    "misleading": 22.2,
    "unverified": 11.1
  },
  "trend": "stable",
  "last_updated": "2025-10-23T16:25:00Z"
}
```

### Visual Representation
```
Fox News - Politics                        Overall Score: 61/100

████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  61%

TRUE:       ███████████ 33% (3 articles)
FALSE:      ███████████ 33% (3 articles)  
MISLEADING: ███████░░░░ 22% (2 articles)
UNVERIFIED: ████░░░░░░░ 11% (1 article)

Total Articles: 10
```

---

## Future-Proofing

### Handling New Verdict Types

If the fact-check API introduces new verdict categories:

1. **Log unknown verdicts** to monitoring system
2. **Store exact API verdict** in `articles.fact_check_verdict`
3. **Default categorization:** Map unknown verdicts to `unverified_count`
4. **Update mapping** in next deployment

### Example New Verdicts
- `PARTLY TRUE` → Map to `misleading_count`
- `PANTS ON FIRE` → Map to `false_count`
- `HALF TRUE` → Map to `misleading_count`
- `OUTDATED` → Map to `misleading_count`

---

## API Endpoints

### Get Outlet Credibility Scores
```
GET /api/v1/outlets/credibility
GET /api/v1/outlets/{source_name}/credibility
GET /api/v1/outlets/{source_name}/credibility?period=weekly
```

### Response Format
```json
{
  "source_name": "Fox News",
  "category": "politics",
  "scores": [
    {
      "period_type": "all_time",
      "average_score": 61.4,
      "total_articles": 150,
      "true_count": 45,
      "false_count": 50,
      "misleading_count": 35,
      "unverified_count": 20,
      "period_start": "2025-01-01T00:00:00Z",
      "period_end": "2025-10-23T16:25:00Z"
    },
    {
      "period_type": "weekly",
      "average_score": 58.0,
      "total_articles": 10,
      "true_count": 3,
      "false_count": 3,
      "misleading_count": 2,
      "unverified_count": 1,
      "period_start": "2025-10-17T00:00:00Z",
      "period_end": "2025-10-23T23:59:59Z"
    }
  ]
}
```

---

## Testing

### Test Scripts
- `scripts/testing/complete_fox_politics_test.py` - Full integration test with fact-checking
- `scripts/utilities/show_verdict_mapping.py` - Display current verdict distribution (TODO)

### Sample Test Output
```
================================================================================
FACT-CHECK INTEGRATION TEST - FOX NEWS POLITICS
================================================================================

Database Setup: ✓
RSS Feed Fetch: ✓ (10 articles)
Fact-Check Jobs: ✓ (9/10 completed)

VERDICT DISTRIBUTION:
  TRUE:       3 articles (avg score: 72)
  FALSE:      2 articles (avg score: 30)
  MOSTLY FALSE: 1 article  (avg score: 30)
  MISLEADING: 1 article  (avg score: 50)
  MIXED:      1 article  (avg score: 55)
  UNVERIFIED: 1 article  (avg score: 45)

Overall Average: 61.4/100
Total Duration: 433.6 seconds
```

---

## Change Log

### 2025-10-23
- Initial documentation created
- Identified 6 verdict categories from updated API
- Defined 4-category grouping strategy
- Documented database schema and aggregation logic

### Future Updates
- Track verdict category changes from API updates
- Document new verdict types as they appear
- Update grouping strategy based on user feedback
