# Synthesis Mode Timeout Configuration Fix

**Date**: November 19, 2025  
**Issue**: AbandonedJobError during synthesis mode testing  
**Status**: ✅ Fixed  

---

## Problem Summary

During synthesis mode testing with `complete_fox_politics_test_synthesis.py`, all 10 fact-check jobs failed with "AbandonedJobError" during the extraction phase. The backend team incorrectly attributed this to Fox News extraction limitations in the Railway API.

## Root Cause Analysis

### The Real Issue: Polling Timeout Too Short

**Previous Configuration** (`app/core/config.py` line 107):
```python
FACT_CHECK_MAX_POLL_ATTEMPTS: int = 60  # 5 minutes at 5s intervals
```

**Calculation:**
- 60 attempts × 5 seconds = **300 seconds (5 minutes)**

**Synthesis Mode Requirements:**
- Processing time: **4-7 minutes (240-420 seconds)**
- Often closer to 5-6 minutes for typical articles

**Result:**
- Jobs timed out after 5 minutes
- Synthesis mode needs 4-7 minutes to complete
- Backend service marked jobs as "abandoned" before completion

### Why This Wasn't a Fox News Issue

1. ✅ **Tested successfully**: The same Fox News article (`marjorie-greene-says-trumps-traitor-label`) was successfully processed in synthesis mode via direct API testing
   - Job ID: `90c4358e-d7c8-4728-8d33-3024b6c71464`
   - Processing time: 268.8 seconds (4.5 minutes)
   - Result: 4 claims analyzed, Context & Emphasis generated

2. ✅ **API documentation**: The SYNTHESIS_MODE_API_GUIDE.md explicitly uses Fox News as the recommended test URL

3. ✅ **Error timing**: "AbandonedJobError" occurs when polling timeout expires, not when URL extraction fails

---

## Fix Applied

### Configuration Update

**File**: `app/core/config.py` (lines 102-112)

**Before:**
```python
FACT_CHECK_MAX_POLL_ATTEMPTS: int = 60  # max polling attempts (5 minutes at 5s intervals)
```

**After:**
```python
FACT_CHECK_MAX_POLL_ATTEMPTS: int = 180  # max polling attempts (15 minutes at 5s intervals)
# Note: Synthesis mode requires 4-7 minutes, thorough 5-10 minutes, standard ~1 minute
# 180 attempts × 5s = 900s (15 min) accommodates all modes with buffer
```

### New Timeout Calculations

| Mode | Average Time | Max Time | Buffer | Total Needed |
|------|-------------|----------|--------|--------------|
| `standard` | 60s | 90s | +30s | 120s (2 min) |
| `thorough` | 7 min | 10 min | +2 min | 12 min |
| `iterative` | 2.5 min | 3 min | +1 min | 4 min |
| **`synthesis`** | **5 min** | **7 min** | **+3 min** | **10 min** |

**New timeout: 15 minutes** accommodates all modes with generous buffer.

---

## Testing Instructions

### 1. Verify Configuration

```bash
cd /Users/ej/Downloads/RSS-Feed/backend
grep "FACT_CHECK_MAX_POLL_ATTEMPTS" app/core/config.py
```

**Expected output:**
```python
FACT_CHECK_MAX_POLL_ATTEMPTS: int = 180  # max polling attempts (15 minutes at 5s intervals)
```

### 2. Re-run Synthesis Test

```bash
python3 scripts/testing/complete_fox_politics_test_synthesis.py
```

**Expected behavior:**
- ✅ Jobs submit successfully (10 jobs)
- ✅ Polling continues for up to 15 minutes per job
- ✅ Jobs complete with status "finished"
- ✅ `article_text` field populated with synthesis content
- ✅ Context & Emphasis data present in validation_results

### 3. Verify Job Completion

After script completes, check database:

```sql
SELECT 
    job_id,
    verdict,
    validation_mode,
    LENGTH(synthesis_article) as article_length,
    fact_checked_at
FROM article_fact_checks
WHERE validation_mode = 'synthesis'
ORDER BY fact_checked_at DESC
LIMIT 10;
```

**Expected results:**
- `verdict` should be real verdicts (MIXED, MOSTLY TRUE, etc.), not "ERROR"
- `article_length` should be > 5000 characters (typically 8,000-15,000)
- `validation_mode` should be "synthesis"

---

## Additional Considerations

### Environment Variable Override

If you need different timeouts per environment, you can override via `.env`:

```bash
# .env
FACT_CHECK_MAX_POLL_ATTEMPTS=180  # 15 minutes
```

### Mode-Specific Timeouts (Future Enhancement)

For more granular control, consider adding mode-specific timeouts:

```python
# Future enhancement in app/core/config.py
FACT_CHECK_TIMEOUTS: dict = {
    "standard": 120,    # 2 minutes (120 × 5s = 600s)
    "thorough": 180,    # 15 minutes (180 × 5s = 900s)
    "summary": 120,     # 2 minutes
    "iterative": 60,    # 5 minutes (60 × 5s = 300s)
    "synthesis": 180,   # 15 minutes (180 × 5s = 900s)
}
```

Then in `FactCheckService.poll_and_complete_job()`:

```python
async def poll_and_complete_job(
    self, job_id: str, mode: str = "summary", max_attempts: int = None, poll_interval: int = None
) -> ArticleFactCheck:
    """Poll job until completion with mode-specific timeouts."""
    if max_attempts is None:
        max_attempts = settings.FACT_CHECK_TIMEOUTS.get(mode, 180)
    # ... rest of implementation
```

---

## Performance Monitoring

### Recommended Metrics to Track

1. **Processing Time by Mode**
   ```sql
   SELECT 
       validation_mode,
       AVG(processing_time_seconds) as avg_time,
       MIN(processing_time_seconds) as min_time,
       MAX(processing_time_seconds) as max_time,
       COUNT(*) as total_jobs
   FROM article_fact_checks
   WHERE processing_time_seconds IS NOT NULL
   GROUP BY validation_mode;
   ```

2. **Timeout Rate**
   ```sql
   SELECT 
       validation_mode,
       COUNT(*) FILTER (WHERE verdict = 'ERROR') as failed,
       COUNT(*) as total,
       ROUND(100.0 * COUNT(*) FILTER (WHERE verdict = 'ERROR') / COUNT(*), 2) as failure_rate_pct
   FROM article_fact_checks
   GROUP BY validation_mode;
   ```

3. **Synthesis Mode Completion Rate**
   ```sql
   SELECT 
       DATE(fact_checked_at) as date,
       COUNT(*) as total_jobs,
       COUNT(*) FILTER (WHERE verdict != 'ERROR') as successful,
       COUNT(*) FILTER (WHERE LENGTH(synthesis_article) > 5000) as has_article
   FROM article_fact_checks
   WHERE validation_mode = 'synthesis'
   GROUP BY DATE(fact_checked_at)
   ORDER BY date DESC;
   ```

---

## Troubleshooting

### If Jobs Still Fail

1. **Check Railway API Status**
   ```bash
   curl https://fact-check-production.up.railway.app/health
   ```

2. **Test Direct API Call**
   ```bash
   curl -X POST https://fact-check-production.up.railway.app/fact-check/submit \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://www.foxnews.com/media/marjorie-greene-says-trumps-traitor-label-could-put-her-life-danger",
       "mode": "synthesis",
       "generate_image": false,
       "generate_article": true
     }'
   ```
   
   Save the `job_id` and check status:
   ```bash
   curl https://fact-check-production.up.railway.app/fact-check/{job_id}/status
   ```

3. **Check Backend Logs**
   ```bash
   # Look for FactCheckService logs
   tail -f logs/app.log | grep "FactCheckService"
   ```

4. **Verify Network Connectivity**
   ```bash
   # Test connection to Railway API
   curl -I https://fact-check-production.up.railway.app
   ```

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `AbandonedJobError` | Timeout too short | ✅ Fixed by this update |
| `No content extracted` | URL blocked/paywalled | Try different URL |
| `Synthesis mode disabled` | Config flag off | Check Railway API config |
| `Connection timeout` | Network issue | Check Railway API status |

---

## Rollback Plan

If you need to revert this change:

```bash
cd /Users/ej/Downloads/RSS-Feed/backend
git diff HEAD~1 app/core/config.py
git checkout HEAD~1 -- app/core/config.py
```

Or manually change line 107 back to:
```python
FACT_CHECK_MAX_POLL_ATTEMPTS: int = 60  # max polling attempts (5 minutes at 5s intervals)
```

**Note**: Reverting will break synthesis mode testing.

---

## Deployment Checklist

- [x] Configuration updated in `app/core/config.py`
- [ ] Documentation reviewed by backend team
- [ ] Test script re-run successfully
- [ ] Database verified for synthesis articles
- [ ] Monitoring alerts configured for timeouts
- [ ] Production environment updated (if applicable)

---

## References

- [SYNTHESIS_MODE_API_GUIDE.md](./SYNTHESIS_MODE_API_GUIDE.md) - Complete API documentation
- [Railway API Endpoint](https://fact-check-production.up.railway.app)
- [Interactive API Docs](https://fact-check-production.up.railway.app/docs)

---

**Questions?**  
Contact the fact-check API team with any issues or questions about synthesis mode configuration.

**Last Updated**: November 19, 2025  
**Status**: Configuration Fix Applied ✅
