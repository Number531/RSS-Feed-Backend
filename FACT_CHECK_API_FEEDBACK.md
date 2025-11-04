# Fact-Check API Improvement Recommendations

## To: Fact-Check Microservice API Team
## From: RSS Feed Backend Integration Team
## Date: December 2024
## Re: Performance Analysis and Enhancement Requests

---

## Executive Summary

After processing 10 Fox News Politics articles through the fact-check API, we've identified several areas for improvement. Overall success rate: **90%** (9/10 completed), with valuable insights for enhancing accuracy and reliability.

---

## Current Performance Metrics

### ✅ Strengths
- **High completion rate:** 9 out of 10 articles (90%)
- **Detailed claim analysis:** Each article analyzed 3 claims
- **Good confidence scoring:** 60-95% confidence on verdicts
- **Consistent processing time:** 300 seconds (5 minutes) per article
- **Evidence diversity:** Multiple source types checked

### ⚠️ Areas for Improvement
- **Source consensus always "None":** No consensus data being returned
- **0 sources reported:** `num_sources` field shows 0 for all articles
- **Inconsistent validation_results format:** Sometimes list, sometimes string
- **Processing failures:** 1 out of 10 failed with "Unknown error"
- **Context awareness:** Some claims lack temporal context

---

## Issue #1: Source Tracking Not Working ❌

### Problem
```json
{
  "num_sources": 0,
  "source_consensus": "None"
}
```

**Every article shows 0 sources checked, despite evidence being gathered.**

### Impact
- **User trust:** Users can't see how many sources validated the claim
- **Transparency:** No visibility into fact-check robustness
- **Credibility:** "0 sources" appears unprofessional

### Evidence from Our Data
```
Article #1 (95/100): num_sources = 0, consensus = None
Article #2 (90/100): num_sources = 0, consensus = None
...all 9 articles show same issue
```

### Root Cause Hypothesis
- Counter not incrementing during source checks
- Field not being populated before response
- Sources checked but metadata not recorded

### Recommended Fix
**Priority: HIGH**

```python
# Suggested implementation
def check_sources(claim):
    sources_checked = 0
    supporting = []
    contradicting = []
    
    for source in [news_sources, web_sources, research_sources]:
        result = validate_against_source(claim, source)
        sources_checked += 1
        if result.supports:
            supporting.append(source)
        elif result.contradicts:
            contradicting.append(source)
    
    consensus = calculate_consensus(supporting, contradicting)
    
    return {
        "num_sources": sources_checked,  # ← Actually populate this
        "source_consensus": consensus,    # ← Return actual consensus
        "supporting_sources": len(supporting),
        "contradicting_sources": len(contradicting)
    }
```

---

## Issue #2: Consensus Logic Missing 📊

### Problem
`source_consensus` always returns `"None"` instead of meaningful values.

### Expected Values
Based on your API docs, we expect:
- `"STRONG_AGREEMENT"` - Most sources agree
- `"MODERATE_AGREEMENT"` - Some disagreement
- `"SPLIT"` - Sources evenly divided
- `"NO_CONSENSUS"` - High disagreement
- `"INSUFFICIENT_DATA"` - Not enough sources

### Current Reality
**Always:** `"None"`

### Impact
- Can't show users source agreement level
- Missing key credibility indicator
- Frontend can't display consensus badges

### Recommended Fix
**Priority: HIGH**

```python
def calculate_consensus(supporting, contradicting, neutral):
    total = supporting + contradicting + neutral
    
    if total < 5:
        return "INSUFFICIENT_DATA"
    
    support_pct = supporting / total
    
    if support_pct >= 0.8:
        return "STRONG_AGREEMENT"
    elif support_pct >= 0.6:
        return "MODERATE_AGREEMENT"
    elif 0.4 <= support_pct <= 0.6:
        return "SPLIT"
    else:
        return "NO_CONSENSUS"
```

---

## Issue #3: Processing Failures Need Better Error Messages 💥

### Problem
Article #10 failed with:
```json
{
  "status": "failed",
  "error": "Unknown error"
}
```

### Impact
- **Can't debug:** No actionable information
- **Can't retry intelligently:** Don't know if transient or permanent
- **User experience:** Can't explain failure to users

### What We Need
Specific error codes and messages:

```python
class FactCheckError:
    NETWORK_TIMEOUT = {
        "code": "E001",
        "message": "Source unreachable after 3 retries",
        "retryable": True
    }
    
    RATE_LIMIT = {
        "code": "E002", 
        "message": "API rate limit exceeded, retry after 60s",
        "retryable": True,
        "retry_after": 60
    }
    
    CONTENT_TOO_SHORT = {
        "code": "E003",
        "message": "Article content less than 100 words",
        "retryable": False
    }
    
    PAYWALLED_CONTENT = {
        "code": "E004",
        "message": "Article behind paywall, cannot access",
        "retryable": False
    }
    
    PARSING_ERROR = {
        "code": "E005",
        "message": "Unable to extract meaningful text from URL",
        "retryable": False
    }
```

### Recommended Fix
**Priority: MEDIUM**

Return structured errors:
```json
{
  "status": "failed",
  "error": {
    "code": "E001",
    "message": "Source unreachable after 3 retries",
    "details": "Connection timeout to foxnews.com",
    "retryable": true,
    "retry_after": null
  }
}
```

---

## Issue #4: Temporal Context Missing ⏰

### Problem
Several articles received low scores due to lack of temporal awareness:

**Example: Article #6 (50/100 - MOSTLY FALSE)**
> "Pelosi spokesman sidesteps retirement rumors"

**Verdict:** MOSTLY FALSE  
**Reason:** "She announced re-election bid in 2023 and was re-elected in 2024"

**Issue:** Article headline might be from 2022, when rumors were active. Fact-checker didn't account for article publication date vs. current date.

### Impact
- **False negatives:** True articles marked false due to time lag
- **Context loss:** Don't know if claim was true when published
- **Historical accuracy:** Can't fact-check older articles fairly

### What We Need
Include article publication date in fact-check request:

```python
# Our request format
{
  "url": "https://foxnews.com/article",
  "published_date": "2022-11-15T10:30:00Z",  # ← Add this
  "current_date": "2025-11-03T18:00:00Z"      # ← And this
}
```

### Recommended Enhancement
**Priority: MEDIUM**

Adjust validation based on temporal context:
```python
def validate_claim_with_time(claim, article_published_date):
    """
    Validate claim as of article publication date,
    then note if status has changed since.
    """
    
    # Check claim at time of publication
    historical_verdict = check_claim_at_date(claim, article_published_date)
    
    # Check claim as of today
    current_verdict = check_claim_at_date(claim, datetime.now())
    
    if historical_verdict != current_verdict:
        return {
            "verdict": historical_verdict,
            "verdict_at_publication": historical_verdict,
            "current_verdict": current_verdict,
            "note": f"Claim was {historical_verdict} when published, "
                   f"but is now {current_verdict}"
        }
    
    return {"verdict": historical_verdict}
```

---

## Issue #5: Validation Results Format Inconsistent 📦

### Problem
`validation_results` field has inconsistent structure:

**Sometimes:** List of claim objects
```python
[
  {
    "claim": {...},
    "validation_result": {...}
  }
]
```

**Sometimes:** String (possibly JSON encoded)
```python
"[{\"claim\": ..., \"validation_result\": ...}]"
```

**Sometimes:** Simple dict
```python
{"status": "pending"}
```

### Impact
- **Parsing complexity:** Our code needs 3 different parsers
- **Error prone:** Type checking required everywhere
- **Frontend issues:** Can't reliably extract claims for display

### Recommended Fix
**Priority: HIGH**

**Standardize on single format:**
```json
{
  "validation_results": {
    "version": "2.0",
    "format": "structured",
    "claims": [
      {
        "claim_id": "claim_001",
        "claim_text": "Full text of claim",
        "category": "Iterative Claim",
        "risk_level": "HIGH",
        "verdict": "FALSE",
        "confidence": 0.9,
        "evidence": {
          "supporting": ["source1", "source2"],
          "contradicting": ["source3"],
          "neutral": ["source4"]
        },
        "summary": "Detailed explanation..."
      }
    ],
    "overall_verdict": "FALSE",
    "credibility_score": 36
  }
}
```

**Benefits:**
- Single parser for all responses
- Type-safe with JSON schema
- Extensible with version field
- Clear hierarchy

---

## Issue #6: High-Risk Claim Detection Works Well! ✅

### What's Working
The API successfully identifies HIGH RISK claims:

**Example from Article #8:**
```json
{
  "claim": {
    "claim": "Trump denied directing DOJ...",
    "risk_level": "HIGH"
  }
}
```

### Strengths
- ✅ Correctly identifies constitutional/legal claims as high-risk
- ✅ Flags false attributions to media outlets
- ✅ Marks specific factual assertions requiring verification
- ✅ Assigns appropriate confidence levels (80-95%)

### Enhancement Suggestion
**Add risk explanation:**
```json
{
  "claim": {
    "claim": "Trump denied directing DOJ...",
    "risk_level": "HIGH",
    "risk_factors": [
      "Constitutional significance",
      "False media attribution",
      "Political implications"
    ],
    "why_high_risk": "Claims about presidential DOJ actions have constitutional significance and false attribution to '60 Minutes' undermines media credibility."
  }
}
```

---

## Issue #7: Evidence Count Discrepancy 📊

### Problem
Validation results show:
```json
{
  "evidence_count": 35,
  "evidence_breakdown": {
    "news": 10,
    "general": 10,
    "research": 10,
    "historical": 5
  }
}
```

But `num_sources: 0` in the parent object.

### Questions
1. Is `evidence_count` different from `num_sources`?
2. Should they be the same?
3. Which one should we display to users?

### Recommended Clarification
**Priority: LOW**

Define these terms clearly in API docs:
- `num_sources`: Unique external sources consulted
- `evidence_count`: Total pieces of evidence gathered (may include multiple from same source)
- `source_breakdown`: How evidence distributed across source types

---

## Requested Features 🚀

### Feature Request #1: Batch Processing
**Current:** Process one article at a time  
**Desired:** Submit 10 articles, get 10 results

**Why:**
- Reduce API round trips
- Better resource utilization
- Faster overall processing

**Suggested Endpoint:**
```python
POST /api/fact-check/batch
{
  "jobs": [
    {"url": "...", "mode": "summary"},
    {"url": "...", "mode": "summary"},
    ...
  ]
}

# Returns
{
  "batch_id": "batch_123",
  "jobs": [
    {"job_id": "job_001", "status": "processing"},
    {"job_id": "job_002", "status": "processing"},
    ...
  ]
}
```

---

### Feature Request #2: Streaming Results
**Current:** Poll every 5 seconds for 5 minutes  
**Desired:** WebSocket or SSE for real-time updates

**Why:**
- More responsive UX
- Reduce polling overhead
- Can show progress (e.g., "Checking sources... 15/35")

**Suggested Implementation:**
```python
# WebSocket connection
ws://api/fact-check/job/{job_id}/stream

# Messages:
{"status": "processing", "progress": 0.1, "message": "Fetching article..."}
{"status": "processing", "progress": 0.3, "message": "Analyzing claims..."}
{"status": "processing", "progress": 0.6, "message": "Checking sources..."}
{"status": "completed", "progress": 1.0, "result": {...}}
```

---

### Feature Request #3: Confidence Breakdown
**Current:** Single confidence score  
**Desired:** Per-claim confidence + factors

**Example:**
```json
{
  "claim": "Trump denied...",
  "confidence": 0.9,
  "confidence_breakdown": {
    "source_reliability": 0.95,
    "source_agreement": 0.88,
    "claim_specificity": 0.92,
    "temporal_relevance": 0.85
  },
  "confidence_explanation": "High confidence due to strong source agreement and reliable sources. Slight uncertainty due to lack of direct transcript access."
}
```

---

### Feature Request #4: Source Citations
**Current:** No source URLs provided  
**Desired:** List of sources that validated/contradicted claim

**Why:**
- User transparency
- Allow users to verify themselves
- Build trust in fact-checks

**Example:**
```json
{
  "evidence": {
    "supporting": [
      {
        "title": "AP News Report on DOJ Actions",
        "url": "https://apnews.com/...",
        "date": "2025-10-15",
        "credibility_rating": "HIGH",
        "excerpt": "Trump publicly called for investigations..."
      }
    ],
    "contradicting": [],
    "neutral": [...]
  }
}
```

---

## Performance Recommendations 🔧

### Optimization #1: Reduce Processing Time
**Current:** 300 seconds (5 minutes) per article  
**Target:** 120 seconds (2 minutes) for summary mode

**Suggestions:**
- Cache source checks for common claims
- Parallel source validation
- Progressive disclosure (return basic verdict fast, detailed analysis slower)

---

### Optimization #2: Implement Caching
**Problem:** Same article fact-checked multiple times

**Solution:**
```python
# Before processing
cache_key = hash(article_url + validation_mode)
if cache_hit := redis.get(cache_key):
    return cache_hit

# After processing
redis.setex(cache_key, ttl=3600, value=result)
```

**Benefits:**
- Instant responses for repeated articles
- Lower API costs
- Better user experience

---

### Optimization #3: Smart Mode Selection
**Current:** We always use "summary" mode  
**Suggestion:** API recommends appropriate mode based on article

**Logic:**
```python
def recommend_mode(article):
    if article.word_count < 300:
        return "summary"  # Short article, quick check
    
    if article.is_breaking_news:
        return "summary"  # Speed matters
    
    if article.contains_high_risk_claims():
        return "thorough"  # Accuracy matters
    
    return "standard"  # Default
```

---

## Data Quality Issues Found 📋

### Issue: Inconsistent Verdict Names
Found in our data:
- `"TRUE"`
- `"MOSTLY TRUE"`
- `"UNVERIFIED"`
- `"UNVERIFIED - INSUFFICIENT EVIDENCE"` ← Inconsistent
- `"MOSTLY FALSE"`
- `"FALSE"`
- `"MIXED"` ← Not in documented list
- `"ERROR"` ← Edge case

**Request:** Standardize to documented values only

---

### Issue: Missing Fields
Some fact-check results missing optional fields:
- `tags` - Always empty array
- `related_articles` - Never populated
- `update_timestamp` - When fact-check last updated

**Request:** Populate these fields if data available

---

## Testing Recommendations 🧪

### Test Case #1: Paywall Detection
**Current:** Fails with "Unknown error"  
**Needed:** Detect paywalls and return specific error

**Test URLs:**
- NYT article (paywall)
- WSJ article (paywall)
- Medium article (metered paywall)

---

### Test Case #2: Multiple Claims Per Article
**Current:** Always 3 claims analyzed  
**Question:** Is this a hard limit?

**Test:** Submit article with 10 distinct claims, ensure all validated

---

### Test Case #3: Non-English Content
**Current:** Unknown behavior  
**Test:** Submit Spanish/French/German articles

---

### Test Case #4: Multimedia Articles
**Current:** Unknown behavior  
**Test:** 
- Video-only articles
- Podcast transcripts
- Image galleries with captions

---

## Summary of Priorities

### 🔴 Critical (Fix ASAP)
1. **Source counting:** `num_sources` always 0
2. **Consensus logic:** Always returns "None"
3. **Format consistency:** Standardize `validation_results` structure

### 🟡 High Priority (Next Sprint)
4. **Error messages:** Return specific error codes
5. **Temporal context:** Account for publication dates
6. **Source citations:** Return source URLs

### 🟢 Enhancement Requests
7. **Batch processing:** Submit multiple articles
8. **Streaming results:** WebSocket/SSE updates
9. **Confidence breakdown:** Explain confidence scores
10. **Performance:** Reduce processing time to 2 minutes

---

## Sample Output Analysis

### Best Performing Article
**Article #1: 95/100 - MOSTLY TRUE**
- Clean verdict
- Good summary
- All 3 claims validated correctly
- Appropriate confidence (90%)

**What worked:** Clear claims, good sources, no temporal issues

### Worst Performing Article
**Article #8: 36/100 - FALSE**
- Good claim detection (3 HIGH RISK claims)
- Excellent summary
- **Issue:** False attribution to "60 Minutes" caught correctly

**What worked:** High-risk claim detection, detailed evidence

### Failed Article
**Article #10: ERROR**
- No processing completed
- Generic "Unknown error"
- No recovery possible

**What failed:** Error handling, no actionable information

---

## Metrics We're Tracking

For your reference, we measure:

```python
{
  "total_articles": 10,
  "successful": 9,
  "failed": 1,
  "success_rate": 0.90,
  
  "avg_processing_time": 300,
  "min_processing_time": 300,
  "max_processing_time": 300,
  
  "verdict_distribution": {
    "TRUE": 3,
    "MOSTLY TRUE": 1,
    "UNVERIFIED": 3,
    "MOSTLY FALSE": 1,
    "FALSE": 1
  },
  
  "avg_credibility_score": 64.7,
  "avg_confidence": 0.87,
  
  "claims_analyzed_per_article": 3.0,
  "high_risk_claims": 9  # 3 claims × 3 articles
}
```

---

## Questions for API Team

1. **Source counting:**
   - Why is `num_sources` always 0?
   - Are sources being checked but not counted?
   - Is there a configuration flag we're missing?

2. **Processing time:**
   - Why exactly 300 seconds for all articles?
   - Is this a hard-coded timeout?
   - Can we reduce for simple articles?

3. **Validation modes:**
   - We use "summary" mode. What's different in "standard"/"thorough"?
   - Does mode affect processing time?
   - Which mode do you recommend for news articles?

4. **Error handling:**
   - What causes "Unknown error"?
   - Is there error logging we can access?
   - How can we help debug failures?

5. **Rate limits:**
   - What are our rate limits?
   - Can we request increase for batch processing?
   - Are there different tiers available?

---

## Contact & Feedback

**Integration Team:** RSS Feed Backend  
**Email:** backend-team@rssfeed.com  
**Slack:** #fact-check-integration  
**Environment:** Production

**This Report Based On:**
- 10 Fox News Politics articles
- Processing date: December 2024
- API version: Unknown (please add version to responses)
- Mode used: "summary"

---

## Conclusion

The fact-check API is **working well overall** (90% success rate), but has significant opportunities for improvement:

✅ **Strengths:**
- High-risk claim detection
- Detailed summaries
- Good confidence scoring
- Thorough evidence gathering (35 sources per claim)

❌ **Critical Issues:**
- Source counting broken
- Consensus logic missing
- Inconsistent data formats

🚀 **Enhancement Opportunities:**
- Batch processing
- Streaming results
- Better error messages
- Performance optimization

We appreciate the work your team is doing and look forward to collaborating on these improvements!
