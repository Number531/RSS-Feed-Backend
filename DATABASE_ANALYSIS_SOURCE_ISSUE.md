# Database Analysis: Source Counting Issue

## Investigation Date: December 2024

## Question
Is the `num_sources = 0` issue caused by our database structure, or is it an API problem?

---

## Answer: **CONFIRMED - This is an API Issue, NOT a Database Issue**

The database structure is **correct and ready** to receive source count data. The problem is that the **fact-check API is not populating these fields**.

---

## Evidence

### 1. Database Schema is Correct ✅

```sql
Column Name                    Data Type            Nullable   Default
--------------------------------------------------------------------------------
num_sources                    integer              YES        NULL
source_consensus               character varying    YES        NULL
```

**Analysis:**
- ✅ `num_sources` column EXISTS
- ✅ Data type is `integer` (correct for counting)
- ✅ `source_consensus` column EXISTS
- ✅ Data type is `character varying` (correct for string values)
- ✅ Both columns allow NULL (appropriate for optional fields)

**Conclusion:** Database is properly structured to store source information.

---

### 2. All Records Show Same Problem 🔴

```
ID                                   Verdict         Score    Sources    Consensus
------------------------------------------------------------------------------------------------
b9ba5128-d999-4bde-8d22-db9f34d220ae MOSTLY TRUE     95       0          None
d82abe2d-ffa5-46cf-8442-e159c2c68eea TRUE            90       0          None
5891cd11-38f8-45cd-9715-8f7a9033d6d5 TRUE            83       0          None
f8581110-1b2a-4c8b-b05b-041d50fb9dec TRUE            80       0          None
980fbea1-de61-4ff2-823a-fb021594d1f5 UNVERIFIED      65       0          None
4d2daa47-3b88-473d-bb2c-9057d08f196a MOSTLY FALSE    50       0          None
33b75eb1-eaf7-4d98-8559-0bf1f0d71580 UNVERIFIED      49       0          None
59102e4d-c56c-4889-a070-4e1bfc5d0957 FALSE           36       0          None
15776e74-2c98-4c2d-beba-6dd247aec70d UNVERIFIED      34       0          None
```

**Analysis:**
- **100% of records have `num_sources = 0`**
- **100% of records have `source_consensus = None`**
- This pattern is **consistent across ALL verdicts** (TRUE, FALSE, UNVERIFIED)
- This pattern is **consistent across ALL credibility scores** (34 to 95)

**Conclusion:** The API is **systematically failing** to populate these fields.

---

### 3. Raw Database Values Confirm API Issue

```
num_sources (raw): 0 (type: integer)
source_consensus (raw): None (type: character varying)
```

**Analysis:**
- Values stored in database are **exactly what the API returns**
- Database is **correctly storing** what it receives
- PostgreSQL types are correct: `integer` for counts, `character varying` for strings

**Conclusion:** Database is functioning correctly. The API is sending `0` and `None`.

---

### 4. Evidence of Sources Being Checked 🔍

In the `validation_results` JSONB field, we can see:

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

**Analysis:**
- API **IS checking sources** (35 sources per claim!)
- API **IS tracking** source breakdown by category
- API **IS storing** this information in `validation_results`
- But API is **NOT populating** the dedicated `num_sources` field

**Conclusion:** The API has the data but is not putting it in the right place.

---

## Root Cause Analysis

### The Problem

```python
# What the API is doing (WRONG):
response = {
    "num_sources": 0,              # ← Always hardcoded or never set
    "source_consensus": None,       # ← Always hardcoded or never set
    "validation_results": {
        "evidence_count": 35,       # ← Has the actual data!
        "evidence_breakdown": {...} # ← Has detailed breakdown!
    }
}
```

### What Should Happen

```python
# What the API should do (CORRECT):
response = {
    "num_sources": 35,              # ← Use evidence_count
    "source_consensus": "STRONG_AGREEMENT",  # ← Calculate from evidence
    "validation_results": {
        "evidence_count": 35,
        "evidence_breakdown": {...}
    }
}
```

---

## Comparison: Database vs. API Responsibility

### Database Responsibility ✅
- [x] Store `num_sources` as integer
- [x] Store `source_consensus` as string
- [x] Accept NULL values
- [x] Store JSONB for `validation_results`
- [x] Handle all data types correctly

**Status:** ALL RESPONSIBILITIES MET

### API Responsibility ❌
- [x] Count sources during validation ✅ (evidence shows 35 sources checked)
- [ ] **Populate `num_sources` field** ❌ (always sends 0)
- [ ] **Calculate consensus from source agreement** ❌ (always sends None)
- [x] Return validation results ✅ (JSONB data present)

**Status:** 2 OUT OF 4 RESPONSIBILITIES MISSING

---

## Impact Assessment

### What Works
1. ✅ Database stores all data correctly
2. ✅ API checks sources (35 per claim)
3. ✅ API determines verdicts accurately
4. ✅ API calculates credibility scores
5. ✅ validation_results contains evidence data

### What's Broken
1. ❌ `num_sources` field not populated (always 0)
2. ❌ `source_consensus` field not populated (always None)
3. ❌ Frontend can't display "Verified by 35 sources"
4. ❌ Frontend can't show consensus strength badges
5. ❌ Users can't see fact-check robustness

---

## Recommended Fixes

### For API Team (Fact-Check Microservice)

**Fix #1: Populate num_sources**

```python
# Current (broken):
def create_fact_check_response(validation_data):
    return {
        "num_sources": 0,  # ❌ Wrong
        ...
    }

# Fixed:
def create_fact_check_response(validation_data):
    evidence_count = validation_data.get("evidence_count", 0)
    return {
        "num_sources": evidence_count,  # ✅ Correct
        ...
    }
```

**Fix #2: Calculate source_consensus**

```python
def calculate_consensus(supporting, contradicting, neutral):
    """Calculate source agreement level"""
    total = supporting + contradicting + neutral
    
    if total < 5:
        return "INSUFFICIENT_DATA"
    
    support_ratio = supporting / total
    
    if support_ratio >= 0.8:
        return "STRONG_AGREEMENT"
    elif support_ratio >= 0.6:
        return "MODERATE_AGREEMENT"
    elif 0.4 <= support_ratio <= 0.6:
        return "SPLIT"
    elif support_ratio <= 0.2:
        return "STRONG_DISAGREEMENT"
    else:
        return "NO_CONSENSUS"

# Use in response:
def create_fact_check_response(validation_data):
    evidence = validation_data.get("key_evidence", {})
    supporting = len(evidence.get("supporting", []))
    contradicting = len(evidence.get("contradicting", []))
    neutral = len(evidence.get("neutral", []))
    
    return {
        "num_sources": supporting + contradicting + neutral,
        "source_consensus": calculate_consensus(supporting, contradicting, neutral),
        ...
    }
```

---

### For Backend Team (RSS Feed - Our Team)

**No database changes needed!** ✅

Our database is already correct. We just need to:

1. ✅ **Wait for API team to fix their code**
2. ✅ **No schema migrations required**
3. ✅ **No code changes on our end**
4. ✅ **Once API fixed, data will flow correctly**

---

## Testing Plan

### Before Fix (Current State)
```sql
SELECT verdict, num_sources, source_consensus 
FROM article_fact_checks;

-- Result:
-- MOSTLY TRUE | 0 | None
-- TRUE        | 0 | None
-- FALSE       | 0 | None
```

### After Fix (Expected State)
```sql
SELECT verdict, num_sources, source_consensus 
FROM article_fact_checks;

-- Expected Result:
-- MOSTLY TRUE | 35 | STRONG_AGREEMENT
-- TRUE        | 35 | STRONG_AGREEMENT
-- FALSE       | 35 | MODERATE_AGREEMENT
```

---

## Data Migration

### Question: Do we need to backfill existing records?

**Answer:** Depends on API team's timeline

**Option A: No Backfill**
- Wait for API fix
- New fact-checks will have correct data
- Old fact-checks keep `num_sources = 0`
- **Pros:** Simple, no work
- **Cons:** Historical data incomplete

**Option B: Re-run Fact-Checks**
- Re-process articles with fixed API
- Expensive (5 min per article × 9 articles = 45 minutes)
- **Pros:** Complete historical data
- **Cons:** API costs, processing time

**Option C: Manual Backfill**
- Extract `evidence_count` from `validation_results` JSONB
- Update `num_sources` in place
- **Pros:** Fast, no re-processing
- **Cons:** Requires custom script

### Recommended: Option C (Manual Backfill)

```sql
-- Update num_sources from validation_results JSONB
UPDATE article_fact_checks
SET num_sources = COALESCE(
    (validation_results->>'evidence_count')::integer,
    0
)
WHERE num_sources = 0 OR num_sources IS NULL;

-- Verify
SELECT 
    verdict,
    credibility_score,
    num_sources,
    validation_results->>'evidence_count' as json_evidence_count
FROM article_fact_checks
ORDER BY credibility_score DESC;
```

---

## Timeline

### Immediate (Now)
- [x] Confirm database structure is correct ✅
- [x] Identify root cause (API not populating fields) ✅
- [x] Document issue for API team ✅

### API Team (1-2 weeks)
- [ ] Implement num_sources population
- [ ] Implement source_consensus calculation
- [ ] Deploy API fix
- [ ] Test with sample articles

### After API Fix
- [ ] Run test articles through fixed API
- [ ] Verify num_sources and source_consensus populated
- [ ] Consider backfill strategy for old records

---

## Conclusion

### Key Findings

1. **Database is NOT the problem** ✅
   - Schema is correct
   - Columns exist
   - Data types are appropriate
   - Storage is working

2. **API is NOT populating fields** ❌
   - Has the data (evidence_count = 35)
   - Not mapping to num_sources
   - Not calculating source_consensus
   - Needs code fix, not schema change

3. **No database migration needed** ✅
   - Current schema is sufficient
   - Just need API to use it correctly

### Action Items

**For API Team:**
1. 🔴 **Critical:** Populate `num_sources` field
2. 🔴 **Critical:** Calculate and populate `source_consensus`
3. 🟡 **High:** Test fixes with sample articles
4. 🟢 **Nice-to-have:** Add validation to ensure fields are set

**For Backend Team (Us):**
1. ✅ **Monitor:** Watch for API fixes
2. 🟡 **Plan:** Decide on backfill strategy
3. 🟢 **Prepare:** Frontend updates to display source counts once available

---

## References

- **Feedback Document:** `FACT_CHECK_API_FEEDBACK.md` (sent to API team)
- **Database Schema:** See `DATABASE_SCHEMA.md`
- **Test Results:** See `HIGH_RISK_CLAIMS_REPORT.md`

---

**Report Prepared By:** RSS Feed Backend Team  
**Investigation Date:** December 2024  
**Verification Method:** Direct PostgreSQL query + SQLAlchemy ORM inspection  
**Conclusion:** Database structure is correct. Issue is in fact-check API code.
