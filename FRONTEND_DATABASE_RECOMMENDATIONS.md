# Frontend Database Migration Recommendations

**Date**: November 19, 2025  
**Purpose**: Optimize database for frontend synthesis mode display  
**Status**: Recommendations for Phase 2  
**Priority**: Medium (current schema works, these are optimizations)

---

## Executive Summary

After analyzing the synthesis mode implementation and test results, the **current database schema is sufficient for MVP frontend integration**. However, several **optional optimizations** would significantly improve frontend performance and developer experience.

### Current State: ✅ Ready for Frontend

**What Works Now**:
- ✅ `synthesis_article` TEXT column stores full markdown article (10-17KB)
- ✅ `article_data` JSONB stores structured metadata (references, timelines, etc.)
- ✅ Existing indexes support basic queries
- ✅ All 10 test articles have complete data

**What Could Be Better**:
- 🔄 No computed columns for quick UI checks
- 🔄 JSONB accessors require frontend parsing
- 🔄 Large text fields transferred even when not needed
- 🔄 No caching hints for CDN/frontend

---

## Recommended Migrations (Priority Order)

### 🔥 HIGH PRIORITY - Immediate Frontend Value

#### 1. Add Computed Columns for Quick UI Checks

**Problem**: Frontend has to check `LENGTH(synthesis_article)` or parse JSON to know what's available

**Solution**: Add boolean/integer helper columns

```sql
-- Migration: Add frontend helper columns
ALTER TABLE articles 
  ADD COLUMN has_synthesis BOOLEAN 
    GENERATED ALWAYS AS (synthesis_article IS NOT NULL) STORED,
  ADD COLUMN synthesis_word_count INTEGER 
    GENERATED ALWAYS AS (
      CASE 
        WHEN synthesis_article IS NOT NULL 
        THEN ARRAY_LENGTH(STRING_TO_ARRAY(synthesis_article, ' '), 1)
        ELSE NULL 
      END
    ) STORED,
  ADD COLUMN has_context_emphasis BOOLEAN
    GENERATED ALWAYS AS (article_data ? 'context_and_emphasis') STORED,
  ADD COLUMN has_timeline BOOLEAN
    GENERATED ALWAYS AS (article_data ? 'event_timeline') STORED;

-- Add indexes for filtering
CREATE INDEX idx_articles_has_synthesis 
  ON articles (has_synthesis) 
  WHERE has_synthesis = true;

CREATE INDEX idx_articles_synthesis_ready 
  ON articles (has_synthesis, fact_check_score, fact_check_verdict)
  WHERE has_synthesis = true;
```

**Frontend Benefit**:
```typescript
// Before: Requires full article fetch or complex query
const hasSynthesis = article.synthesis_article?.length > 0;

// After: Simple boolean flag
const hasSynthesis = article.has_synthesis;
const wordCount = article.synthesis_word_count; // No parsing needed
```

**Impact**: 
- Eliminates frontend parsing
- Enables efficient filtering (show only articles with synthesis)
- No storage overhead (computed columns)

---

#### 2. Add Summary/Preview Column

**Problem**: Frontend loads entire 10-17KB synthesis article just to show preview

**Solution**: Store first 500 characters as preview

```sql
-- Migration: Add synthesis preview
ALTER TABLE articles
  ADD COLUMN synthesis_preview TEXT
    GENERATED ALWAYS AS (
      CASE 
        WHEN synthesis_article IS NOT NULL 
        THEN LEFT(synthesis_article, 500) 
        ELSE NULL 
      END
    ) STORED;

-- Index for full-text search on previews
CREATE INDEX idx_articles_synthesis_preview_fts
  ON articles USING GIN (to_tsvector('english', synthesis_preview))
  WHERE synthesis_preview IS NOT NULL;
```

**Frontend Benefit**:
```typescript
// Article list view - only load preview (500 chars vs 10-17KB)
GET /api/v1/articles?fields=id,title,synthesis_preview,fact_check_score

// Full article view - load complete synthesis
GET /api/v1/articles/123?fields=synthesis_article,article_data
```

**Impact**:
- 95% smaller payload for list views
- Faster initial page loads
- Preview for "Read Full Analysis" teasers

---

### ⚙️ MEDIUM PRIORITY - Performance Optimizations

#### 3. Extract Key JSON Fields to Dedicated Columns

**Problem**: Accessing nested JSONB requires parsing and is slower than native columns

**Solution**: Extract commonly accessed fields

```sql
-- Migration: Extract key JSON fields
ALTER TABLE articles
  ADD COLUMN timeline_event_count INTEGER
    GENERATED ALWAYS AS (
      CASE 
        WHEN article_data ? 'event_timeline'
        THEN jsonb_array_length(article_data->'event_timeline')
        ELSE NULL
      END
    ) STORED,
  ADD COLUMN reference_count INTEGER
    GENERATED ALWAYS AS (
      CASE 
        WHEN article_data ? 'references'
        THEN jsonb_array_length(article_data->'references')
        ELSE NULL
      END
    ) STORED,
  ADD COLUMN margin_note_count INTEGER
    GENERATED ALWAYS AS (
      CASE 
        WHEN article_data ? 'margin_notes'
        THEN jsonb_array_length(article_data->'margin_notes')
        ELSE NULL
      END
    ) STORED;

-- Index for queries
CREATE INDEX idx_articles_synthesis_metrics
  ON articles (timeline_event_count, reference_count)
  WHERE has_synthesis = true;
```

**Frontend Benefit**:
```typescript
// Quick stats without JSON parsing
<ArticleCard 
  timelineEvents={article.timeline_event_count}
  citations={article.reference_count}
  marginNotes={article.margin_note_count}
/>
```

**Impact**:
- Instant stat display
- Filter by article richness (e.g., "Articles with 5+ citations")
- No JSON parsing overhead

---

#### 4. Add Processing Metadata Columns

**Problem**: Frontend can't easily show "when was this fact-checked" or "which mode was used"

**Solution**: Extract processing metadata

```sql
-- Migration: Add processing metadata
ALTER TABLE articles
  ADD COLUMN fact_check_mode VARCHAR(20),
  ADD COLUMN fact_check_processing_time INTEGER, -- seconds
  ADD COLUMN synthesis_generated_at TIMESTAMP WITH TIME ZONE;

-- Update trigger to set synthesis_generated_at
CREATE OR REPLACE FUNCTION update_synthesis_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.synthesis_article IS NOT NULL AND OLD.synthesis_article IS NULL THEN
    NEW.synthesis_generated_at = NOW();
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_synthesis_timestamp
  BEFORE UPDATE ON articles
  FOR EACH ROW
  EXECUTE FUNCTION update_synthesis_timestamp();
```

**Frontend Benefit**:
```typescript
// Display freshness
<Badge>
  Synthesis analysis from {formatDate(article.synthesis_generated_at)}
  Processing time: {article.fact_check_processing_time}s
  Mode: {article.fact_check_mode}
</Badge>
```

**Impact**:
- User trust (show recency)
- Debugging aid (track slow analyses)
- Mode comparison (synthesis vs iterative)

---

### 🔹 LOW PRIORITY - Nice-to-Have Features

#### 5. Add Read-Time Estimate

**Problem**: Users don't know how long synthesis articles will take to read

**Solution**: Calculate based on average 200 WPM reading speed

```sql
-- Migration: Add read time estimate
ALTER TABLE articles
  ADD COLUMN synthesis_read_minutes INTEGER
    GENERATED ALWAYS AS (
      CASE 
        WHEN synthesis_word_count IS NOT NULL 
        THEN GREATEST(1, ROUND(synthesis_word_count::NUMERIC / 200.0))
        ELSE NULL
      END
    ) STORED;
```

**Frontend Benefit**:
```typescript
<ArticleHeader>
  {article.synthesis_read_minutes} min read
</ArticleHeader>
```

**Impact**:
- Better UX (set expectations)
- Users can decide to read now or save for later

---

#### 6. Add Verdict Display Color Hint

**Problem**: Frontend needs to map verdicts to colors repeatedly

**Solution**: Store computed color class

```sql
-- Migration: Add verdict color hint
ALTER TABLE articles
  ADD COLUMN verdict_color VARCHAR(20)
    GENERATED ALWAYS AS (
      CASE fact_check_verdict
        WHEN 'TRUE' THEN 'green'
        WHEN 'MOSTLY TRUE' THEN 'light-green'
        WHEN 'MOSTLY FALSE' THEN 'orange'
        WHEN 'FALSE' THEN 'red'
        WHEN 'UNVERIFIED - INSUFFICIENT EVIDENCE' THEN 'gray'
        ELSE 'neutral'
      END
    ) STORED;
```

**Frontend Benefit**:
```typescript
// Direct styling without mapping logic
<Badge className={`bg-${article.verdict_color}`}>
  {article.fact_check_verdict}
</Badge>
```

**Impact**:
- Consistent coloring across frontend
- No repeated mapping logic
- Easy to update globally (change DB, not code)

---

## Performance Analysis

### Current Query Performance

Based on test data (10 synthesis articles):

```sql
-- List view with preview (RECOMMENDED)
SELECT id, title, fact_check_score, fact_check_verdict, synthesis_preview
FROM articles 
WHERE has_synthesis = true
ORDER BY published_date DESC
LIMIT 20;
-- Estimated: <10ms, ~5KB payload

-- Full article view
SELECT synthesis_article, article_data
FROM articles
WHERE id = '123...';
-- Estimated: <5ms, ~15KB payload

-- Stats dashboard
SELECT 
  COUNT(*) FILTER (WHERE has_synthesis) as total_synthesis,
  AVG(synthesis_word_count) as avg_words,
  AVG(timeline_event_count) as avg_events
FROM articles
WHERE fact_checked_at > NOW() - INTERVAL '7 days';
-- Estimated: <15ms
```

### With Recommended Migrations

**Before** (current schema):
- List query: Transfer 10-17KB per article × 20 = 200-340KB
- Parse JSON in frontend for every card
- No efficient filtering by synthesis availability

**After** (with optimizations):
- List query: Transfer 0.5KB per article × 20 = 10KB (97% reduction!)
- Zero JSON parsing (use computed columns)
- Instant filtering with indexed boolean columns

---

## Storage Impact

### Estimated Storage Per Article

**Current**:
- `synthesis_article`: 10-17KB (avg 13.9KB)
- `article_data`: 2-5KB (avg 3KB)
- **Total**: ~17KB per synthesis article

**With All Recommended Migrations**:
- `synthesis_preview`: 500 bytes (computed, stored)
- `has_synthesis`: 1 byte (computed, stored)
- `synthesis_word_count`: 4 bytes (computed, stored)
- `timeline_event_count`: 4 bytes (computed, stored)
- `reference_count`: 4 bytes (computed, stored)
- `margin_note_count`: 4 bytes (computed, stored)
- `synthesis_read_minutes`: 4 bytes (computed, stored)
- `verdict_color`: ~10 bytes (computed, stored)
- **Additional Storage**: ~0.53KB per article (~3% overhead)

**For 100,000 articles**:
- Current: 1.7GB
- With optimizations: 1.75GB (+50MB, +3%)

**Verdict**: Negligible storage cost for significant performance gain

---

## Migration Priority & Timeline

### Phase 1 (Immediate - MVP Frontend Launch)
✅ **Already Complete**:
- `synthesis_article` column
- `article_data` JSONB
- Basic indexes

**Frontend can launch NOW with current schema**

### Phase 2 (Week 1 - After Frontend Launch)
🔥 **High Priority Optimizations**:
1. Add `has_synthesis` boolean + indexes (30 min)
2. Add `synthesis_preview` column (30 min)
3. Add `synthesis_word_count` (15 min)

**Impact**: 95% faster list views, instant filtering

### Phase 3 (Week 2-3 - Performance Tuning)
⚙️ **Medium Priority**:
4. Extract JSON field counts (45 min)
5. Add processing metadata columns (45 min)

**Impact**: Richer UI, better analytics

### Phase 4 (Month 2 - Polish)
🔹 **Low Priority Nice-to-Haves**:
6. Add read-time estimate (15 min)
7. Add verdict color hint (15 min)

**Impact**: Better UX, cleaner frontend code

---

## Frontend API Recommendations

### Suggested Endpoint Structure

```typescript
// List view - minimal data
GET /api/v1/articles?has_synthesis=true&fields=id,title,synthesis_preview,fact_check_score,verdict_color

Response: {
  articles: [{
    id: "123...",
    title: "Article Title",
    synthesis_preview: "First 500 characters...",
    fact_check_score: 67,
    verdict_color: "green",
    has_synthesis: true,
    synthesis_word_count: 1954,
    synthesis_read_minutes: 10
  }]
}

// Full article view - complete data
GET /api/v1/articles/123?fields=synthesis_article,article_data,timeline_event_count

Response: {
  id: "123...",
  synthesis_article: "Full markdown content...",
  article_data: {
    references: [...],
    event_timeline: [...],
    margin_notes: [...],
    context_and_emphasis: {...}
  },
  timeline_event_count: 5,
  reference_count: 12
}

// Stats dashboard
GET /api/v1/articles/stats?synthesis=true

Response: {
  total_synthesis: 150,
  avg_word_count: 1956,
  avg_credibility_score: 53.4,
  verdict_distribution: {
    "TRUE": 30,
    "MOSTLY TRUE": 15,
    "MOSTLY FALSE": 30,
    "FALSE": 15,
    "UNVERIFIED": 60
  }
}
```

---

## Rollback Plan

All recommended migrations are **non-breaking**:

1. **Computed columns**: Can be dropped without affecting existing queries
2. **Indexes**: Can be dropped without data loss
3. **No data changes**: Only adding derived/computed fields

**Rollback Strategy**:
```sql
-- Drop all Phase 2-4 additions
ALTER TABLE articles
  DROP COLUMN IF EXISTS has_synthesis,
  DROP COLUMN IF EXISTS synthesis_preview,
  DROP COLUMN IF EXISTS synthesis_word_count,
  DROP COLUMN IF EXISTS has_context_emphasis,
  DROP COLUMN IF EXISTS has_timeline,
  DROP COLUMN IF EXISTS timeline_event_count,
  DROP COLUMN IF EXISTS reference_count,
  DROP COLUMN IF EXISTS margin_note_count,
  DROP COLUMN IF EXISTS synthesis_read_minutes,
  DROP COLUMN IF EXISTS verdict_color,
  DROP COLUMN IF EXISTS fact_check_mode,
  DROP COLUMN IF EXISTS fact_check_processing_time,
  DROP COLUMN IF EXISTS synthesis_generated_at;

-- Drop indexes
DROP INDEX IF EXISTS idx_articles_has_synthesis;
DROP INDEX IF EXISTS idx_articles_synthesis_ready;
DROP INDEX IF EXISTS idx_articles_synthesis_preview_fts;
DROP INDEX IF EXISTS idx_articles_synthesis_metrics;
```

**No data loss, no breaking changes**

---

## Conclusion

### Recommendation: Phased Approach

**For MVP Launch**:
- ✅ **Current schema is sufficient**
- Frontend can launch immediately
- All data is accessible via existing columns

**For Optimal Performance**:
- 🔥 **Implement Phase 2 within Week 1**
- `has_synthesis`, `synthesis_preview`, `synthesis_word_count`
- 95% performance improvement for list views
- ~2 hours of migration work

**For Long-Term**:
- ⚙️ **Implement Phase 3 as needed**
- Based on frontend team feedback
- Additional metadata as requirements emerge

### Key Takeaway

**The current database schema is production-ready for frontend integration.** The recommended migrations are **optimizations, not requirements**. Prioritize based on:
1. Frontend team bandwidth
2. User feedback post-launch
3. Performance monitoring data

---

**Status**: ✅ Current Schema Ready, Optimizations Optional  
**Next Review**: After 1,000 synthesis articles in production  
**Last Updated**: November 19, 2025
