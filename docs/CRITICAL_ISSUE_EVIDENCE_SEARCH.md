# CRITICAL ISSUE: Fact-Check API Evidence Search Failing

**Date:** October 29, 2025  
**Status:** 🔴 **CRITICAL - REQUIRES IMMEDIATE ATTENTION**

---

## Issue Summary

**All 10 articles processed return "UNVERIFIED - INSUFFICIENT EVIDENCE" with 0 sources found.**

This is NOT a backend parsing issue - our backend is correctly reading the API responses. The problem is that **the fact-check API's evidence search is failing completely**.

---

## Symptoms

### What We Observe:
- ✅ Claims are correctly extracted (3 per article)
- ✅ API responds successfully (no errors or timeouts)
- ✅ Verdicts are returned as "UNVERIFIED - INSUFFICIENT EVIDENCE"
- ❌ **Evidence count: 0 for ALL claims** (100% failure rate)
- ❌ **No sources found for ANY article** (10/10 affected)
- ❌ Confidence scores extremely low: 0.0 - 0.1

### Sample Results:
```
Article: Pentagon scales back troops from NATO eastern flank
Claims Analyzed: 3
Evidence Found: 0 sources

Claim 1: "U.S. is scaling back military presence in Romania"
  Verdict: UNVERIFIED - INSUFFICIENT EVIDENCE
  Evidence Count: 0
  Confidence: 0.1
  Summary: "cannot be verified due to a complete absence of supporting or contradicting evidence"

Claim 2: "2nd Infantry Brigade Combat Team of 101st Airborne will redeploy"
  Verdict: UNVERIFIED - INSUFFICIENT EVIDENCE
  Evidence Count: 0
  Confidence: 0.1

Claim 3: "U.S. Army Europe announced redeployment on Wednesday"
  Verdict: UNVERIFIED - INSUFFICIENT EVIDENCE
  Evidence Count: 0
  Confidence: 0.1
```

---

## Impact Assessment

### **Production Impact: CRITICAL** 🔴

**User-Facing:**
- All fact-checks show as "UNVERIFIED"
- No credibility scoring (all scores 50/100)
- No source citations
- No evidence summaries
- **Feature is essentially non-functional**

**Business Impact:**
- Fact-check feature provides zero value to users
- Cannot distinguish between true and false claims
- Credibility scoring meaningless
- Platform differentiation lost

### **Data Quality: ZERO** 🔴

- 10/10 articles (100%) show UNVERIFIED
- 0 sources found across 30 claims
- Evidence search failure rate: 100%

---

## Root Cause Analysis

### **Backend: ✅ WORKING CORRECTLY**

Our backend successfully:
- ✅ Parses API responses
- ✅ Stores verdicts correctly
- ✅ Extracts confidence scores
- ✅ Saves evidence counts (which are 0)
- ✅ Handles nested response structure

**Backend is NOT the problem.**

### **Fact-Check API: ❌ EVIDENCE SEARCH FAILING**

The microservice is:
- ✅ Receiving requests
- ✅ Extracting claims (working)
- ❌ **Finding evidence (FAILING)**
- ✅ Returning responses (but with no evidence)

---

## Possible Causes

### 1. **Evidence Search API Issues**

The fact-check service uses external APIs (Exa/Perplexity) for evidence search:

**Potential Issues:**
- API keys invalid or expired
- Rate limits exceeded
- API service downtime
- Network connectivity issues
- Authentication failures

**How to Check:**
```bash
# Check Railway logs
railway logs -p fact-check-production

# Look for errors like:
- "API key invalid"
- "Rate limit exceeded"
- "Connection timeout"
- "Authentication failed"
```

### 2. **Configuration Issues**

**Potential Issues:**
- Environment variables not set correctly
- Search configuration disabled
- API endpoints changed
- Feature flags turned off

**How to Check:**
```bash
# Verify environment variables on Railway
railway variables -p fact-check-production

# Check for:
- EXA_API_KEY
- PERPLEXITY_API_KEY
- ENABLE_EVIDENCE_SEARCH=true
```

### 3. **Search Query Generation Failing**

**Potential Issues:**
- Query generation logic broken
- Queries too restrictive (no results)
- Search index issues
- Language processing errors

**How to Check:**
- Review search query logs
- Check if queries are being generated
- Verify query formatting

### 4. **Iterative Mode Specific Issue**

**Potential Issues:**
- Iterative mode's evidence search broken
- Parallel validation failing silently
- New iterative code has bugs

**How to Check:**
```bash
# Try with standard mode instead of iterative
curl -X POST "https://fact-check-production.up.railway.app/fact-check/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.foxnews.com/politics/...",
    "mode": "summary"  # Try summary instead of iterative
  }'
```

---

## Test Cases

### These Claims SHOULD Be Verifiable:

1. **"Pentagon scales back troops from NATO"**
   - This would be major news
   - Pentagon announcements are public
   - Should have DoD press releases
   - Should have news coverage

2. **"Trump administration nets 1,700 arrests in Memphis"**
   - Specific statistics
   - Law enforcement data
   - Should have local news coverage
   - DOJ/DHS press releases

3. **"Republicans praise Fetterman"**
   - Congressional statements
   - Social media posts
   - News quotes
   - Should be easily verifiable

**All returning 0 sources suggests systemic failure, not content issues.**

---

## Immediate Actions Required

### **Priority 1: Check Fact-Check API Logs**

```bash
# On Railway dashboard
1. Navigate to fact-check-production project
2. View deployment logs
3. Filter for "error", "exception", "failed"
4. Look for evidence search errors
```

**Look for:**
- Exa API errors
- Perplexity API errors
- Rate limit messages
- Timeout errors
- Authentication failures

### **Priority 2: Verify API Keys**

```bash
# Check environment variables
railway variables -p fact-check-production

# Verify these exist and are valid:
- EXA_API_KEY
- PERPLEXITY_API_KEY
- OPENAI_API_KEY (if used)
```

### **Priority 3: Test Evidence Search Directly**

```bash
# Submit a test job with a known verifiable claim
curl -X POST "https://fact-check-production.up.railway.app/fact-check/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.example.com/test",
    "mode": "summary"
  }'

# Check if evidence_count > 0
```

### **Priority 4: Contact Microservice Team**

**Questions to ask:**
1. Are Exa/Perplexity API keys configured correctly?
2. Has evidence search been working recently?
3. Were there any recent changes to search logic?
4. Are there known issues with iterative mode evidence search?
5. Can they see evidence search errors in their logs?

---

## Temporary Workarounds

### **Option 1: Disable Fact-Checking**

Until fixed, consider:
- Disabling automatic fact-check jobs
- Removing fact-check UI elements
- Showing "Feature temporarily unavailable" message

### **Option 2: Use Summary Mode**

Test if summary mode works better:
```python
# In fact_check_service.py
mode="summary"  # Instead of "iterative"
```

### **Option 3: Mock Data (DEV ONLY)**

For development/testing only:
```python
# Return mock data until API fixed
if settings.ENV == "development":
    return mock_fact_check_result()
```

---

## Testing Plan Once Fixed

### **Step 1: Test Single Article**

```bash
# Submit one article
python -c "
import asyncio
from app.services.fact_check_service import FactCheckService
# Test with single known-verifiable article
"
```

### **Step 2: Verify Evidence Found**

```sql
-- Check for non-zero evidence counts
SELECT 
    id,
    verdict,
    num_sources,
    claims_validated
FROM article_fact_checks
WHERE num_sources > 0;
```

### **Step 3: Full Reprocess**

```bash
# Clear bad data
DELETE FROM article_fact_checks;

# Reprocess
python scripts/testing/complete_fox_politics_test.py

# Verify results
SELECT 
    verdict,
    COUNT(*) 
FROM article_fact_checks 
GROUP BY verdict;
```

**Expected after fix:**
- Mix of TRUE, FALSE, MISLEADING, UNVERIFIED
- num_sources > 0 for most articles
- Confidence scores > 0.5 for verified claims

---

## Success Criteria

### Evidence Search is Fixed When:

1. ✅ At least 50% of claims find evidence (num_sources > 0)
2. ✅ Verdicts show variety (not all UNVERIFIED)
3. ✅ Confidence scores > 0.5 for verified claims
4. ✅ Source citations available
5. ✅ Evidence summaries contain actual source info

---

## Related Documents

- `/Users/ej/Downloads/RSS-Feed/backend/docs/ITERATIVE_MODE_ANALYSIS.md`
- `/Users/ej/Downloads/RSS-Feed/backend/docs/ITERATIVE_MODE_FIX_REQUIRED.md`
- `/Users/ej/Downloads/RSS-Feed/backend/docs/OPTION_A_COMPLETION_REPORT.md`
- `/Users/ej/Downloads/RSS-Feed/backend/docs/raw_api_response_sample.json`

---

## Timeline

- **October 29, 2025 17:00 UTC:** Backend parsing fixed ✅
- **October 29, 2025 21:15 UTC:** Reprocessing completed ✅
- **October 29, 2025 21:20 UTC:** Issue identified - 0 evidence found 🔴
- **Status:** Waiting for fact-check API team investigation

---

## Conclusion

**Our backend is working correctly.** The problem is with the fact-check microservice's evidence search functionality. 

**All claims return 0 sources, which is statistically impossible for real news articles.** This indicates a systemic failure in the evidence gathering component of the fact-check API.

**Next Step:** Fact-check API team needs to investigate why evidence search is returning 0 results for all claims.

---

**Priority:** 🔥 **HIGHEST**  
**Owner:** Fact-Check API Team  
**Backend Status:** ✅ Ready (waiting for API fix)  
**Blocker:** Evidence search must be fixed before fact-check feature is production-ready
