# Aggregate Scoring Capabilities for News Sources

## Executive Summary

**YES** - The current system **fully supports aggregate scoring** of news articles and sources with the following capabilities:

---

## ✅ Currently Available Metrics

### 1. **Source-Level Aggregation**
```sql
- Average credibility score per source
- Verdict distribution (TRUE, FALSE, MIXED, etc.)
- Total articles fact-checked
- Average confidence scores
- Processing time metrics
```

**Example Output:**
```
Fox News (politics):
  Avg Credibility Score: 57.6/100
  TRUE: 60% | FALSE: 20% | MISLEADING: 10% | MOSTLY FALSE: 10%
  Articles Analyzed: 10
```

### 2. **Claims-Level Analysis**
```sql
- Total claims analyzed across all articles
- Claims validated per article (avg 3.0)
- Outcome percentages:
  • True: 30.0%
  • False: 43.3%
  • Misleading: 3.3%
  • Unverified: 23.3%
```

### 3. **Temporal Trends**
```sql
- Daily/weekly credibility score trends
- Verdict distribution over time
- Processing time evolution
```

### 4. **Category-Based Scoring**
```sql
- Accuracy by article category (politics, technology, etc.)
- Category-specific verdict distributions
- Comparative category analysis
```

### 5. **Composite Reliability Score**
Custom formula combining multiple factors:
```
Reliability = (Avg Score × 0.4) + 
              (% True × 0.3) + 
              (% Non-False × 0.2) + 
              (Confidence × 10 × 0.1)
```

**Result: 55.9/100 for Fox News based on 10 articles**

### 6. **Cost Analysis**
```sql
- Total validation costs
- Cost per article breakdown
- Cost by operation (extraction, search, validation)
```

### 7. **Quality Metrics**
```sql
- Sources used per validation (avg: 35)
- Processing time statistics (avg: 276s)
- Confidence distributions by verdict type
```

---

## 📊 Available Database Fields for Aggregation

### article_fact_checks Table
| Field | Type | Aggregatable |
|-------|------|--------------|
| `credibility_score` | integer | ✅ AVG, MIN, MAX, STDDEV |
| `verdict` | varchar | ✅ COUNT, GROUP BY |
| `confidence` | numeric | ✅ AVG, MIN, MAX |
| `claims_analyzed` | integer | ✅ SUM, AVG |
| `claims_validated` | integer | ✅ SUM, AVG |
| `claims_true` | integer | ✅ SUM, AVG, % |
| `claims_false` | integer | ✅ SUM, AVG, % |
| `claims_misleading` | integer | ✅ SUM, AVG, % |
| `claims_unverified` | integer | ✅ SUM, AVG, % |
| `num_sources` | integer | ✅ AVG, MIN, MAX |
| `processing_time_seconds` | integer | ✅ AVG, SUM |
| `validation_mode` | varchar | ✅ COUNT, GROUP BY |
| `api_costs` | jsonb | ✅ SUM components |
| `fact_checked_at` | timestamp | ✅ DATE grouping, trends |

### articles Table
| Field | Type | Aggregatable |
|-------|------|--------------|
| `category` | varchar | ✅ GROUP BY |
| `published_date` | timestamp | ✅ DATE grouping |
| `fact_check_score` | integer | ✅ AVG, MIN, MAX |
| `fact_check_verdict` | varchar | ✅ COUNT, GROUP BY |

### rss_sources Table
| Field | Type | Aggregatable |
|-------|------|--------------|
| `source_name` | varchar | ✅ GROUP BY |
| `category` | varchar | ✅ GROUP BY |
| `fetch_success_count` | integer | ✅ SUM, AVG |

---

## 🎯 Use Cases Enabled

### 1. **Source Comparison Dashboard**
Compare multiple news sources side-by-side:
```
Source A: 75/100 avg (80% TRUE, 5% FALSE)
Source B: 62/100 avg (55% TRUE, 15% FALSE)
Source C: 48/100 avg (30% TRUE, 35% FALSE)
```

### 2. **Reliability Ranking**
Rank sources by composite reliability score:
```
1. Associated Press - 82.5/100
2. Reuters - 78.3/100
3. Fox News - 55.9/100
```

### 3. **Trend Analysis**
Track credibility over time:
```
Week 1: 64.5 avg score
Week 2: 57.6 avg score (⬇️ -6.9)
```

### 4. **Category Insights**
Identify which categories have better accuracy:
```
Technology: 78/100 avg
Politics: 57/100 avg
Entertainment: 82/100 avg
```

### 5. **Claims Accuracy Tracking**
Monitor claim-level accuracy:
```
30% claims TRUE
43% claims FALSE
24% claims UNVERIFIED
```

### 6. **Cost-Benefit Analysis**
Calculate ROI of fact-checking:
```
$0.013 per article
57.6 avg credibility score
60% TRUE verdict rate
```

---

## 📈 Example Aggregate Queries

### Query 1: Source Leaderboard
```sql
SELECT 
    source_name,
    ROUND(AVG(credibility_score), 1) as avg_score,
    COUNT(*) as articles,
    ROUND(100.0 * COUNT(CASE WHEN verdict = 'TRUE' THEN 1 END) / COUNT(*), 1) as pct_true
FROM rss_sources rs
JOIN articles a ON a.rss_source_id = rs.id
JOIN article_fact_checks afc ON afc.article_id = a.id
GROUP BY rs.id, source_name
HAVING COUNT(*) >= 10
ORDER BY avg_score DESC;
```

### Query 2: Weekly Trends
```sql
SELECT 
    DATE_TRUNC('week', fact_checked_at) as week,
    COUNT(*) as articles,
    ROUND(AVG(credibility_score), 1) as avg_score,
    ROUND(AVG(confidence), 2) as avg_confidence
FROM article_fact_checks
WHERE fact_checked_at >= NOW() - INTERVAL '12 weeks'
GROUP BY week
ORDER BY week DESC;
```

### Query 3: Verdict Distribution
```sql
SELECT 
    verdict,
    COUNT(*) as count,
    ROUND(AVG(credibility_score), 1) as avg_score,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) as percentage
FROM article_fact_checks
GROUP BY verdict
ORDER BY count DESC;
```

---

## 🚀 API Endpoints for Frontend

### Recommended Aggregation Endpoints

#### 1. `/api/v1/analytics/sources`
```json
{
  "sources": [
    {
      "source_name": "Fox News",
      "avg_credibility_score": 57.6,
      "total_articles": 10,
      "fact_checked": 10,
      "verdicts": {
        "TRUE": 6,
        "FALSE": 2,
        "MISLEADING": 1,
        "MOSTLY_FALSE": 1
      },
      "reliability_score": 55.9
    }
  ]
}
```

#### 2. `/api/v1/analytics/trends?period=7d`
```json
{
  "period": "7_days",
  "data_points": [
    {
      "date": "2025-10-31",
      "articles": 10,
      "avg_score": 57.6,
      "verdicts": {"TRUE": 6, "FALSE": 2}
    }
  ]
}
```

#### 3. `/api/v1/analytics/claims`
```json
{
  "total_claims": 30,
  "outcomes": {
    "true": {"count": 9, "percentage": 30.0},
    "false": {"count": 13, "percentage": 43.3},
    "misleading": {"count": 1, "percentage": 3.3},
    "unverified": {"count": 7, "percentage": 23.3}
  }
}
```

---

## ⚠️ Current Limitations

### 1. **No Historical Baseline**
- Cannot compare current scores to historical averages
- **Solution**: Add `source_historical_scores` table

### 2. **No Peer Comparison**
- Cannot compare source against category average
- **Solution**: Calculate category baselines in queries

### 3. **No Weighted Scoring**
- All articles weighted equally regardless of importance
- **Solution**: Add `article_importance_weight` field

### 4. **No Topic Tracking**
- Cannot aggregate by specific topics within categories
- **Solution**: Add `tags` or `topics` array field

### 5. **Limited Cost Data**
- Some articles missing `api_costs` field
- **Solution**: Ensure all validations populate costs

---

## ✨ Recommended Enhancements

### High Priority

1. **Add Historical Benchmarks Table**
```sql
CREATE TABLE source_benchmarks (
    source_id UUID,
    period_start DATE,
    period_end DATE,
    avg_credibility_score NUMERIC,
    verdict_distribution JSONB,
    articles_analyzed INTEGER
);
```

2. **Add Importance Weighting**
```sql
ALTER TABLE articles 
ADD COLUMN importance_weight INTEGER DEFAULT 1;
```

3. **Add Topic Tags**
```sql
-- Already exists: tags ARRAY field
-- Just need to populate it consistently
```

### Medium Priority

4. **Materialized Views for Performance**
```sql
CREATE MATERIALIZED VIEW source_aggregate_scores AS
SELECT 
    source_name,
    AVG(credibility_score) as avg_score,
    COUNT(*) as total_articles,
    -- ... other metrics
FROM rss_sources rs
JOIN articles a ON a.rss_source_id = rs.id
JOIN article_fact_checks afc ON afc.article_id = a.id
GROUP BY rs.id, source_name;
```

5. **Time-Decay Scoring**
Weight recent articles more heavily:
```sql
SELECT 
    source_name,
    SUM(credibility_score * EXP(-0.1 * EXTRACT(EPOCH FROM NOW() - fact_checked_at)/(86400*30))) / 
    SUM(EXP(-0.1 * EXTRACT(EPOCH FROM NOW() - fact_checked_at)/(86400*30))) as weighted_score
FROM ...
```

---

## 📝 Conclusion

### Summary

✅ **Aggregate scoring is FULLY SUPPORTED** with current schema

**Current Capabilities:**
- ✅ Source-level scoring (57.6/100 for Fox News)
- ✅ Verdict distributions (60% TRUE, 20% FALSE)
- ✅ Claims analysis (30% true, 43% false)
- ✅ Temporal trends (daily/weekly)
- ✅ Category breakdowns
- ✅ Composite reliability scores (55.9/100)
- ✅ Cost analysis
- ✅ Quality metrics

**What Works Well:**
1. All core metrics are calculable
2. Database schema supports complex aggregations
3. Historical data is preserved
4. Multiple dimensions for analysis (source, category, time, verdict)

**Quick Wins for Enhancement:**
1. Create aggregate API endpoints (2-3 days)
2. Add materialized views for performance (1 day)
3. Build frontend dashboard (1 week)
4. Add importance weighting (1-2 days)
5. Implement time-decay scoring (1 day)

**Bottom Line:** The data structure is **excellent for aggregate scoring**. You can immediately build source comparison tools, reliability rankings, and trend analysis dashboards.
