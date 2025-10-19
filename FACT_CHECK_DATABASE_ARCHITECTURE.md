# Fact-Check Database Architecture Analysis

> **Use Case:** Always display fact-check summary + citations when user opens article  
> **Phase 1:** Summary mode only (no image generation)  
> **Scaling Requirement:** Aggressive scaling to millions of articles  
> **Performance Target:** Sub-100ms article fetch with fact-check data

---

## 🎯 Requirements Analysis

### Must-Have Features:
1. ✅ **Always available** - Fact-check displayed 100% of the time when article opened
2. ✅ **Summary + Citations** - Verdict, summary, evidence, sources
3. ✅ **No images** (Phase 1) - Reduces API cost and processing time
4. ✅ **Fast reads** - Article + fact-check in single query
5. ✅ **Source scoring** - Daily/weekly/monthly outlet ratings

### Current Article Table Structure:
```sql
articles (
    id UUID PRIMARY,
    rss_source_id UUID FK,
    title TEXT,
    url TEXT,
    url_hash VARCHAR(64) UNIQUE,  -- Deduplication
    description TEXT,
    content TEXT,
    author VARCHAR(255),
    published_date TIMESTAMP,
    thumbnail_url TEXT,
    category VARCHAR(50),
    tags VARCHAR[],
    
    -- Engagement (denormalized)
    vote_score INTEGER,
    vote_count INTEGER,
    comment_count INTEGER,
    trending_score DECIMAL(10,4),
    
    -- Search
    search_vector TSVECTOR,
    
    -- Timestamps
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

---

## 📊 Architecture Options Comparison

### Option 1: Add Columns to Articles Table ❌ **NOT RECOMMENDED**

```sql
ALTER TABLE articles ADD COLUMN fact_check_summary TEXT;
ALTER TABLE articles ADD COLUMN fact_check_verdict VARCHAR(50);
ALTER TABLE articles ADD COLUMN credibility_score INTEGER;
ALTER TABLE articles ADD COLUMN fact_check_citations JSONB;
ALTER TABLE articles ADD COLUMN fact_checked_at TIMESTAMP;
```

**Pros:**
- ✅ Single query to fetch article + fact-check
- ✅ No joins required
- ✅ Simple implementation

**Cons:**
- ❌ **Table bloat** - Articles table becomes massive (50+ columns)
- ❌ **No versioning** - Can't track fact-check history
- ❌ **No re-checking** - Can't re-fact-check articles with updated info
- ❌ **Limited metadata** - Can't store processing details, costs, etc.
- ❌ **Poor separation of concerns** - Mixing article content with fact-check data
- ❌ **Difficult to query** - "Show all FALSE articles" requires scanning entire table
- ❌ **Migration nightmare** - Large table alterations are slow and risky
- ❌ **Cache invalidation issues** - Updating fact-check invalidates article cache

**Scaling Impact:** 🔴 Poor - Table becomes unmanageable at scale

---

### Option 2: Separate Fact-Check Table (1:1) ✅ **RECOMMENDED**

```sql
article_fact_checks (
    id UUID PRIMARY,
    article_id UUID FK UNIQUE,  -- 1:1 relationship
    
    -- Core results (frequently accessed)
    verdict VARCHAR(50) NOT NULL,
    credibility_score INTEGER NOT NULL,  -- 0-100
    summary TEXT NOT NULL,
    confidence DECIMAL(3,2),
    
    -- Citations (JSONB for flexibility)
    validation_results JSONB NOT NULL,  -- Array of claims with evidence
    
    -- Processing metadata
    job_id VARCHAR(255) UNIQUE,
    status VARCHAR(20) DEFAULT 'completed',
    processing_time_seconds INTEGER,
    
    -- Timestamps
    fact_checked_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
)

CREATE INDEX idx_article_fact_checks_article_id ON article_fact_checks(article_id);
CREATE INDEX idx_article_fact_checks_verdict ON article_fact_checks(verdict);
CREATE INDEX idx_article_fact_checks_score ON article_fact_checks(credibility_score);
```

**Pros:**
- ✅ **Clean separation** - Article content separate from fact-check data
- ✅ **Fast joins** - 1:1 relationship with unique index
- ✅ **Query optimization** - Can index fact-check specific fields
- ✅ **Versioning ready** - Easy to add fact-check history later
- ✅ **Flexible JSONB** - Store complex validation data without schema changes
- ✅ **Independent caching** - Cache article and fact-check separately
- ✅ **Easier migrations** - Smaller table, faster alterations
- ✅ **Better analytics** - Dedicated fact-check queries don't impact articles table

**Cons:**
- ⚠️ **Requires join** - Need LEFT JOIN to fetch article + fact-check
- ⚠️ **Two tables to maintain** - Slightly more complex

**Scaling Impact:** 🟢 Excellent - Clean, maintainable, performant at scale

---

### Option 3: Hybrid Approach ⚡ **OPTIMAL FOR AGGRESSIVE SCALING**

**Articles Table (minimal denormalization):**
```sql
ALTER TABLE articles ADD COLUMN fact_check_score INTEGER;  -- Cache for sorting
ALTER TABLE articles ADD COLUMN fact_check_verdict VARCHAR(50);  -- Cache for filtering
ALTER TABLE articles ADD COLUMN fact_checked_at TIMESTAMP;  -- Cache for staleness check

CREATE INDEX idx_articles_fact_check_score ON articles(fact_check_score DESC);
CREATE INDEX idx_articles_fact_check_verdict ON articles(fact_check_verdict);
```

**Fact-Check Table (full data):**
```sql
article_fact_checks (
    id UUID PRIMARY,
    article_id UUID FK UNIQUE,
    
    -- Full fact-check data
    verdict VARCHAR(50) NOT NULL,
    credibility_score INTEGER NOT NULL,
    summary TEXT NOT NULL,
    confidence DECIMAL(3,2),
    validation_results JSONB NOT NULL,
    
    -- Processing
    job_id VARCHAR(255) UNIQUE,
    status VARCHAR(20),
    processing_time_seconds INTEGER,
    api_costs JSONB,
    
    -- Timestamps
    fact_checked_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
)
```

**Pros:**
- ✅ **Best read performance** - Filter/sort on articles table without join
- ✅ **Full data available** - Complete fact-check in separate table
- ✅ **Flexible queries** - Can query with or without join
- ✅ **Cache-friendly** - Denormalized fields rarely change
- ✅ **Analytics ready** - Rich querying capabilities
- ✅ **Version friendly** - Easy to extend with history table later

**Cons:**
- ⚠️ **Sync required** - Must update articles table when fact-check completes
- ⚠️ **Slight redundancy** - Score/verdict stored in two places

**Scaling Impact:** 🟢🟢 Best - Optimized for both reads and analytics

---

## 🏗️ Recommended Schema (Hybrid Approach)

### 1. Update Articles Table (Minimal Denormalization)

```sql
-- Migration: Add fact-check cache columns
ALTER TABLE articles 
    ADD COLUMN fact_check_score INTEGER,
    ADD COLUMN fact_check_verdict VARCHAR(50),
    ADD COLUMN fact_checked_at TIMESTAMP;

-- Indexes for filtering/sorting
CREATE INDEX idx_articles_fact_check_score ON articles(fact_check_score DESC) 
    WHERE fact_check_score IS NOT NULL;
CREATE INDEX idx_articles_fact_check_verdict ON articles(fact_check_verdict) 
    WHERE fact_check_verdict IS NOT NULL;
CREATE INDEX idx_articles_fact_checked_at ON articles(fact_checked_at DESC) 
    WHERE fact_checked_at IS NOT NULL;
```

### 2. Create Fact-Check Table (Full Data)

```sql
CREATE TABLE article_fact_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID NOT NULL UNIQUE REFERENCES articles(id) ON DELETE CASCADE,
    
    -- Core results (always needed for display)
    verdict VARCHAR(50) NOT NULL,  -- TRUE, FALSE, MISLEADING, etc.
    credibility_score INTEGER NOT NULL CHECK (credibility_score >= 0 AND credibility_score <= 100),
    confidence DECIMAL(3,2) CHECK (confidence >= 0 AND confidence <= 1),
    summary TEXT NOT NULL,
    
    -- Claims breakdown
    claims_analyzed INTEGER DEFAULT 0,
    claims_validated INTEGER DEFAULT 0,
    claims_true INTEGER DEFAULT 0,
    claims_false INTEGER DEFAULT 0,
    claims_misleading INTEGER DEFAULT 0,
    claims_unverified INTEGER DEFAULT 0,
    
    -- Validation results (JSONB for flexibility)
    validation_results JSONB NOT NULL,  -- Full claims with evidence
    
    -- Evidence quality
    num_sources INTEGER DEFAULT 0,
    source_consensus VARCHAR(20),  -- GENERAL_AGREEMENT, MIXED, DISPUTED
    
    -- Processing metadata
    job_id VARCHAR(255) UNIQUE NOT NULL,
    validation_mode VARCHAR(20) DEFAULT 'summary',
    processing_time_seconds INTEGER,
    api_costs JSONB,
    
    -- Timestamps
    fact_checked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE UNIQUE INDEX idx_article_fact_checks_article_id ON article_fact_checks(article_id);
CREATE INDEX idx_article_fact_checks_verdict ON article_fact_checks(verdict);
CREATE INDEX idx_article_fact_checks_score ON article_fact_checks(credibility_score DESC);
CREATE INDEX idx_article_fact_checks_job_id ON article_fact_checks(job_id);
CREATE INDEX idx_article_fact_checks_checked_at ON article_fact_checks(fact_checked_at DESC);

-- GIN index for JSONB queries
CREATE INDEX idx_article_fact_checks_validation_results ON article_fact_checks USING GIN (validation_results);
```

### 3. Source Credibility Scores (Separate Table)

```sql
CREATE TABLE source_credibility_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rss_source_id UUID NOT NULL REFERENCES rss_sources(id) ON DELETE CASCADE,
    
    -- Time period
    period_type VARCHAR(20) NOT NULL,  -- daily, weekly, monthly, all_time
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Aggregated metrics
    articles_fact_checked INTEGER DEFAULT 0,
    articles_verified INTEGER DEFAULT 0,
    articles_false INTEGER DEFAULT 0,
    articles_misleading INTEGER DEFAULT 0,
    articles_unverified INTEGER DEFAULT 0,
    
    -- Score (0-100)
    accuracy_score DECIMAL(5,2) NOT NULL,
    credibility_rating VARCHAR(20) NOT NULL,  -- EXCELLENT, GOOD, FAIR, POOR, FAILING
    
    -- Breakdown percentages
    true_claims_pct DECIMAL(5,2),
    false_claims_pct DECIMAL(5,2),
    misleading_claims_pct DECIMAL(5,2),
    
    -- Trends
    score_change DECIMAL(5,2),
    trend VARCHAR(20),  -- IMPROVING, DECLINING, STABLE
    
    -- Rankings
    rank_in_category INTEGER,
    rank_overall INTEGER,
    
    -- Metadata
    last_calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_source_period UNIQUE(rss_source_id, period_type, period_start)
);

-- Indexes
CREATE INDEX idx_source_credibility_source ON source_credibility_scores(rss_source_id);
CREATE INDEX idx_source_credibility_period ON source_credibility_scores(period_type, period_start DESC);
CREATE INDEX idx_source_credibility_score ON source_credibility_scores(accuracy_score DESC);
CREATE INDEX idx_source_credibility_rating ON source_credibility_scores(credibility_rating);
```

---

## 📈 Query Patterns & Performance

### Pattern 1: Fetch Article with Fact-Check (Most Common)

```sql
-- Option A: With JOIN (100% accurate, slightly slower)
SELECT 
    a.*,
    fc.verdict,
    fc.credibility_score,
    fc.summary,
    fc.validation_results,
    fc.fact_checked_at
FROM articles a
LEFT JOIN article_fact_checks fc ON a.id = fc.article_id
WHERE a.id = $1;

-- Performance: ~5-10ms with proper indexes
```

```sql
-- Option B: Without JOIN (using cached fields, faster)
SELECT * FROM articles WHERE id = $1;
-- Then fetch fact-check only if needed:
SELECT * FROM article_fact_checks WHERE article_id = $1;

-- Performance: ~2-3ms for article, ~2-3ms for fact-check if needed
```

### Pattern 2: List Articles with Fact-Check Scores (Feed)

```sql
-- Fast filtering using denormalized columns
SELECT 
    a.id,
    a.title,
    a.url,
    a.category,
    a.fact_check_score,
    a.fact_check_verdict,
    a.vote_score,
    a.comment_count
FROM articles a
WHERE 
    a.category = $1
    AND a.fact_check_score >= 70  -- Show only verified/mostly accurate
ORDER BY a.trending_score DESC
LIMIT 20 OFFSET $2;

-- Performance: ~5ms (no join required)
```

### Pattern 3: Verified Articles Feed

```sql
-- Using cached verdict field
SELECT 
    a.*,
    fc.summary,
    fc.credibility_score,
    fc.validation_results
FROM articles a
INNER JOIN article_fact_checks fc ON a.id = fc.article_id
WHERE 
    a.fact_check_verdict IN ('TRUE', 'MOSTLY_TRUE')
    AND a.published_date > NOW() - INTERVAL '7 days'
ORDER BY a.fact_check_score DESC, a.vote_score DESC
LIMIT 50;

-- Performance: ~10-15ms with proper indexes
```

### Pattern 4: Source Credibility Leaderboard

```sql
-- No join to articles table needed
SELECT 
    rs.name AS source_name,
    scs.accuracy_score,
    scs.credibility_rating,
    scs.articles_fact_checked,
    scs.true_claims_pct,
    scs.false_claims_pct,
    scs.trend,
    scs.rank_overall
FROM source_credibility_scores scs
JOIN rss_sources rs ON scs.rss_source_id = rs.id
WHERE 
    scs.period_type = 'weekly'
    AND scs.period_start = (
        SELECT MAX(period_start) 
        FROM source_credibility_scores 
        WHERE period_type = 'weekly'
    )
ORDER BY scs.accuracy_score DESC
LIMIT 20;

-- Performance: ~5ms
```

---

## 🚀 Scaling Strategy

### Storage Estimates

**Assumptions:**
- 1M articles per month
- 100% fact-check coverage
- Average validation_results JSONB: 5KB

**Articles Table:**
- Current: ~500 bytes per row
- With fact-check columns: +150 bytes = 650 bytes
- 10M articles = 6.5GB (manageable)

**Fact-Check Table:**
- Per row: ~5.5KB (mostly JSONB)
- 10M articles = 55GB
- With indexes: ~70GB total

**Source Credibility:**
- Minimal (500 sources × 365 days × 4 periods = ~730K rows)
- ~100MB total

**Total Storage (10M articles):**
- Articles: 6.5GB
- Fact-checks: 70GB
- Sources: 0.1GB
- **Total: ~77GB** (easily scalable to 100M+ articles)

### Read Performance Optimization

1. **Connection Pooling**
```python
# PostgreSQL connection pool
POOL_SIZE = 20
MAX_OVERFLOW = 40
```

2. **Query Caching**
```python
# Redis cache for hot articles
cache_key = f"article:{article_id}:full"
ttl = 3600  # 1 hour
```

3. **Prepared Statements**
```python
# Pre-compile frequent queries
FETCH_ARTICLE_WITH_FACT_CHECK = """
    SELECT a.*, fc.* FROM articles a 
    LEFT JOIN article_fact_checks fc ON a.id = fc.article_id 
    WHERE a.id = $1
"""
```

4. **Partial Indexes**
```sql
-- Index only fact-checked articles
CREATE INDEX idx_articles_fact_checked 
ON articles(created_at DESC) 
WHERE fact_check_score IS NOT NULL;
```

### Write Performance Optimization

1. **Async Fact-Check Updates**
```python
# Update articles table asynchronously after fact-check completes
@celery.task
def update_article_fact_check_cache(article_id, fact_check_data):
    db.execute("""
        UPDATE articles 
        SET 
            fact_check_score = :score,
            fact_check_verdict = :verdict,
            fact_checked_at = :checked_at
        WHERE id = :id
    """, fact_check_data)
```

2. **Batch Source Score Updates**
```python
# Calculate source scores once daily, not per article
@celery.task(schedule=crontab(hour=2, minute=0))
def update_source_credibility_scores():
    # Bulk calculate for all sources
    pass
```

---

## 🎯 Implementation Priority

### Phase 1: Core Infrastructure (4 hours)
1. ✅ Create migration for articles table columns
2. ✅ Create article_fact_checks table
3. ✅ Create source_credibility_scores table
4. ✅ Update Article model relationships
5. ✅ Add indexes

### Phase 2: Fact-Check Integration (3 hours)
1. ✅ Implement FactCheckService
2. ✅ Submit article to fact-check API (summary mode)
3. ✅ Poll and store results
4. ✅ Update articles table cache columns
5. ✅ Background job for pending fact-checks

### Phase 3: Source Scoring (2 hours)
1. ✅ Implement credibility calculation service
2. ✅ Daily aggregation job
3. ✅ API endpoints for source scores

### Phase 4: API & Frontend (3 hours)
1. ✅ Fact-check endpoints
2. ✅ Update article response schema
3. ✅ Source credibility endpoints
4. ✅ Verified articles feed

**Total: 12 hours**

---

## 📋 Migration Script

```python
# alembic/versions/xxx_add_fact_check_support.py

def upgrade():
    # 1. Add columns to articles
    op.add_column('articles', sa.Column('fact_check_score', sa.Integer(), nullable=True))
    op.add_column('articles', sa.Column('fact_check_verdict', sa.String(50), nullable=True))
    op.add_column('articles', sa.Column('fact_checked_at', sa.DateTime(timezone=True), nullable=True))
    
    # Indexes for articles
    op.create_index('idx_articles_fact_check_score', 'articles', ['fact_check_score'], 
                    postgresql_where=sa.text('fact_check_score IS NOT NULL'))
    op.create_index('idx_articles_fact_check_verdict', 'articles', ['fact_check_verdict'],
                    postgresql_where=sa.text('fact_check_verdict IS NOT NULL'))
    
    # 2. Create article_fact_checks table
    op.create_table('article_fact_checks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('article_id', UUID(as_uuid=True), sa.ForeignKey('articles.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('verdict', sa.String(50), nullable=False),
        sa.Column('credibility_score', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.DECIMAL(3,2), nullable=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('claims_analyzed', sa.Integer(), default=0),
        sa.Column('claims_validated', sa.Integer(), default=0),
        sa.Column('claims_true', sa.Integer(), default=0),
        sa.Column('claims_false', sa.Integer(), default=0),
        sa.Column('claims_misleading', sa.Integer(), default=0),
        sa.Column('claims_unverified', sa.Integer(), default=0),
        sa.Column('validation_results', JSONB(), nullable=False),
        sa.Column('num_sources', sa.Integer(), default=0),
        sa.Column('source_consensus', sa.String(20), nullable=True),
        sa.Column('job_id', sa.String(255), unique=True, nullable=False),
        sa.Column('validation_mode', sa.String(20), default='summary'),
        sa.Column('processing_time_seconds', sa.Integer(), nullable=True),
        sa.Column('api_costs', JSONB(), nullable=True),
        sa.Column('fact_checked_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(timezone=True), default=datetime.utcnow),
    )
    
    # Indexes for article_fact_checks
    op.create_index('idx_article_fact_checks_article_id', 'article_fact_checks', ['article_id'], unique=True)
    op.create_index('idx_article_fact_checks_verdict', 'article_fact_checks', ['verdict'])
    op.create_index('idx_article_fact_checks_score', 'article_fact_checks', ['credibility_score'])
    op.create_index('idx_article_fact_checks_job_id', 'article_fact_checks', ['job_id'])
    op.create_index('idx_article_fact_checks_validation_results', 'article_fact_checks', ['validation_results'],
                    postgresql_using='gin')
    
    # 3. Create source_credibility_scores table
    op.create_table('source_credibility_scores',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('rss_source_id', UUID(as_uuid=True), sa.ForeignKey('rss_sources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('articles_fact_checked', sa.Integer(), default=0),
        sa.Column('articles_verified', sa.Integer(), default=0),
        sa.Column('articles_false', sa.Integer(), default=0),
        sa.Column('articles_misleading', sa.Integer(), default=0),
        sa.Column('articles_unverified', sa.Integer(), default=0),
        sa.Column('accuracy_score', sa.DECIMAL(5,2), nullable=False),
        sa.Column('credibility_rating', sa.String(20), nullable=False),
        sa.Column('true_claims_pct', sa.DECIMAL(5,2), nullable=True),
        sa.Column('false_claims_pct', sa.DECIMAL(5,2), nullable=True),
        sa.Column('misleading_claims_pct', sa.DECIMAL(5,2), nullable=True),
        sa.Column('score_change', sa.DECIMAL(5,2), nullable=True),
        sa.Column('trend', sa.String(20), nullable=True),
        sa.Column('rank_in_category', sa.Integer(), nullable=True),
        sa.Column('rank_overall', sa.Integer(), nullable=True),
        sa.Column('last_calculated_at', sa.DateTime(timezone=True), default=datetime.utcnow),
        sa.Column('created_at', sa.DateTime(timezone=True), default=datetime.utcnow),
        sa.UniqueConstraint('rss_source_id', 'period_type', 'period_start', name='unique_source_period')
    )
    
    # Indexes for source_credibility_scores
    op.create_index('idx_source_credibility_source', 'source_credibility_scores', ['rss_source_id'])
    op.create_index('idx_source_credibility_period', 'source_credibility_scores', ['period_type', 'period_start'])
    op.create_index('idx_source_credibility_score', 'source_credibility_scores', ['accuracy_score'])
    op.create_index('idx_source_credibility_rating', 'source_credibility_scores', ['credibility_rating'])


def downgrade():
    op.drop_table('source_credibility_scores')
    op.drop_table('article_fact_checks')
    op.drop_column('articles', 'fact_checked_at')
    op.drop_column('articles', 'fact_check_verdict')
    op.drop_column('articles', 'fact_check_score')
```

---

## ✅ Final Recommendation

**Use Hybrid Approach (Option 3)** with:

1. **Minimal denormalization** in articles table (3 columns)
   - Fast filtering/sorting without joins
   - Cache invalidation rarely needed
   
2. **Full data** in article_fact_checks table
   - Clean separation of concerns
   - Easy to extend with history tracking
   - Optimal for analytics

3. **Separate source_credibility_scores** table
   - Independent scoring system
   - Efficient aggregations
   - No impact on article queries

**This architecture scales to 100M+ articles with sub-100ms query times.**

---

## 🎯 Next Steps

1. Review and approve schema
2. Create Alembic migration
3. Implement models and relationships
4. Build fact-check service
5. Create API endpoints
6. Frontend integration

**Estimated Total Implementation: 12 hours**
