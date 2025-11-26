# Synthesis Endpoints - Corrected Implementation Plan

## Issues Found in Original Implementation

### Critical Schema Mismatches
1. **ID Type**: Used `int` instead of `UUID` (string)
2. **Field Names**: Wrong names for multiple fields
   - Used `verdict` instead of `fact_check_verdict`
   - Used `confidence_score` instead of `fact_check_score`
   - Used `published_at` instead of `published_date`
   - Used `synthesis_text` instead of `synthesis_article`
3. **JSONB Structure**: Didn't extract arrays from `article_data`:
   - `references`
   - `event_timeline`
   - `margin_notes`
   - `context_and_emphasis`
4. **Missing Join**: Didn't join with `rss_source` to get `source_name`

### Test Failures Summary
- **36 failed** out of 38 tests
- **2 passed** (error handling tests)
- Schema validation errors across all Pydantic models
- Service layer method signature mismatches
- Article model missing synthesis fields (now fixed)

## Corrected Schema Design

### Pydantic Response Models

#### SynthesisListItem
```python
class SynthesisListItem(BaseModel):
    id: str  # UUID as string
    title: str
    synthesis_preview: Optional[str]
    fact_check_verdict: Optional[str]  # Not "verdict"!
    verdict_color: Optional[str]
    fact_check_score: Optional[int]  # Not "confidence_score"!
    synthesis_read_minutes: Optional[int]
    published_date: Optional[datetime]  # Not "published_at"!
    source_name: str  # From rss_source join
    category: str
    has_timeline: bool
    has_context_emphasis: bool
```

#### SynthesisDetailArticle
```python
class SynthesisDetailArticle(BaseModel):
    id: str
    title: str
    content: Optional[str]  # Original article
    synthesis_article: Optional[str]  # Not "synthesis_text"!
    fact_check_verdict: Optional[str]
    verdict_color: Optional[str]
    fact_check_score: Optional[int]
    synthesis_word_count: Optional[int]
    synthesis_read_minutes: Optional[int]
    published_date: Optional[datetime]
    author: Optional[str]
    source_name: str
    category: str
    url: str
    has_timeline: bool
    has_context_emphasis: bool
    timeline_event_count: Optional[int]
    reference_count: Optional[int]
    margin_note_count: Optional[int]
    fact_check_mode: Optional[str]
    fact_check_processing_time: Optional[int]
    synthesis_generated_at: Optional[datetime]
    
    # JSONB extracted arrays
    references: List[Dict[str, Any]] = []
    event_timeline: List[Dict[str, Any]] = []
    margin_notes: List[Dict[str, Any]] = []
    context_and_emphasis: List[Dict[str, Any]] = []
```

#### SynthesisStatsResponse
```python
class SynthesisStatsResponse(BaseModel):
    total_synthesis_articles: int
    articles_with_timeline: int
    articles_with_context: int
    average_credibility: float  # Average of fact_check_score / 100
    verdict_distribution: Dict[str, int]  # Keys: fact_check_verdict values
    average_word_count: int
    average_read_minutes: int
```

### Service Layer Methods

#### SynthesisService
```python
class SynthesisService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_synthesis_articles(
        self,
        page: int = 1,
        page_size: int = 20,
        verdict: Optional[str] = None,
        sort_by: str = "newest"
    ) -> Dict[str, Any]:
        # Query with rss_source join for source_name
        # Filter: has_synthesis = True
        # Order by published_date DESC (newest) or other
        # Paginate
        pass
    
    async def get_synthesis_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        # Query with rss_source join
        # Filter: id = article_id AND has_synthesis = True
        # Extract JSONB arrays from article_data:
        #   - article_data->'references'
        #   - article_data->'event_timeline'
        #   - article_data->'margin_notes'
        #   - article_data->'context_and_emphasis'
        pass
    
    async def get_synthesis_stats(self) -> Dict[str, Any]:
        # Aggregate queries:
        # - COUNT where has_synthesis = True
        # - COUNT where has_timeline = True
        # - COUNT where has_context_emphasis = True
        # - AVG(fact_check_score)
        # - GROUP BY fact_check_verdict, COUNT
        # - AVG(synthesis_word_count)
        # - AVG(synthesis_read_minutes)
        pass
```

### API Endpoints

#### GET /api/v1/articles/synthesis
```python
@router.get("/synthesis", response_model=SynthesisListResponse)
async def list_synthesis_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    verdict: Optional[str] = Query(None),
    sort_by: str = Query("newest", regex="^(newest|oldest|credibility)$"),
    db: AsyncSession = Depends(get_db)
):
    service = SynthesisService(db)
    return await service.list_synthesis_articles(page, page_size, verdict, sort_by)
```

#### GET /api/v1/articles/{article_id}/synthesis
```python
@router.get("/{article_id}/synthesis", response_model=SynthesisDetailResponse)
async def get_synthesis_article(
    article_id: str,  # UUID string
    db: AsyncSession = Depends(get_db)
):
    service = SynthesisService(db)
    article = await service.get_synthesis_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Synthesis article not found")
    return {"article": article}
```

#### GET /api/v1/articles/synthesis/stats
```python
@router.get("/synthesis/stats", response_model=SynthesisStatsResponse)
async def get_synthesis_stats(
    db: AsyncSession = Depends(get_db)
):
    service = SynthesisService(db)
    return await service.get_synthesis_stats()
```

## SQL Queries Needed

### List Query
```sql
SELECT 
    a.id,
    a.title,
    a.synthesis_preview,
    a.fact_check_verdict,
    a.verdict_color,
    a.fact_check_score,
    a.synthesis_read_minutes,
    a.published_date,
    rs.name as source_name,
    a.category,
    a.has_timeline,
    a.has_context_emphasis
FROM articles a
JOIN rss_sources rs ON a.rss_source_id = rs.id
WHERE a.has_synthesis = TRUE
  AND (verdict IS NULL OR a.fact_check_verdict = verdict)
ORDER BY a.published_date DESC
LIMIT page_size OFFSET (page - 1) * page_size
```

### Detail Query
```sql
SELECT 
    a.id,
    a.title,
    a.content,
    a.synthesis_article,
    a.fact_check_verdict,
    a.verdict_color,
    a.fact_check_score,
    a.synthesis_word_count,
    a.synthesis_read_minutes,
    a.published_date,
    a.author,
    rs.name as source_name,
    a.category,
    a.url,
    a.has_timeline,
    a.has_context_emphasis,
    a.timeline_event_count,
    a.reference_count,
    a.margin_note_count,
    a.fact_check_mode,
    a.fact_check_processing_time,
    a.synthesis_generated_at,
    a.article_data->'references' as references,
    a.article_data->'event_timeline' as event_timeline,
    a.article_data->'margin_notes' as margin_notes,
    a.article_data->'context_and_emphasis' as context_and_emphasis
FROM articles a
JOIN rss_sources rs ON a.rss_source_id = rs.id
WHERE a.id = article_id AND a.has_synthesis = TRUE
```

### Stats Query
```sql
SELECT 
    COUNT(*) as total_synthesis_articles,
    SUM(CASE WHEN has_timeline THEN 1 ELSE 0 END) as articles_with_timeline,
    SUM(CASE WHEN has_context_emphasis THEN 1 ELSE 0 END) as articles_with_context,
    AVG(fact_check_score) as average_credibility,
    AVG(synthesis_word_count) as average_word_count,
    AVG(synthesis_read_minutes) as average_read_minutes
FROM articles
WHERE has_synthesis = TRUE;

-- Verdict distribution (separate query)
SELECT 
    fact_check_verdict,
    COUNT(*) as count
FROM articles
WHERE has_synthesis = TRUE
  AND fact_check_verdict IS NOT NULL
GROUP BY fact_check_verdict;
```

## Corrected Test Strategy

### Unit Tests for Schemas
- Test UUID string validation
- Test field name mapping
- Test JSONB array deserialization
- Test optional field handling

### Unit Tests for Service
- Mock AsyncSession and Result objects
- Test query construction with joins
- Test JSONB extraction logic
- Test pagination math
- Test verdict filtering

### Integration Tests
- Use test database with real data
- Test full request/response cycle
- Test 404 handling
- Test pagination
- Test filtering

### Test Fixtures
- Create sample articles with UUIDs
- Include rss_source relationship
- Populate article_data JSONB with arrays
- Cover all synthesis column combinations

## Implementation Steps (Corrected)

1. **Create Schemas** (`app/schemas/synthesis.py`)
   - Use correct field names and types
   - Add JSONB array fields
   - UUID as string

2. **Create Service** (`app/services/synthesis_service.py`)
   - AsyncSession throughout
   - Join with rss_sources
   - Extract JSONB arrays
   - Proper pagination

3. **Create Endpoints** (`app/api/v1/endpoints/synthesis.py`)
   - UUID path parameters
   - Proper error handling
   - Response model validation

4. **Register Router** (`app/api/v1/api.py`)
   - Add synthesis import
   - Include router with /articles prefix

5. **Create Test Fixtures** (`tests/fixtures/synthesis_articles.py`)
   - Async fixtures with AsyncSession
   - Real UUIDs
   - Complete JSONB structures

6. **Write Tests**
   - Schema unit tests
   - Service unit tests  
   - Endpoint integration tests

7. **Manual Testing**
   - Start dev server
   - Test via Swagger UI
   - Verify responses match spec

8. **Documentation**
   - Update API docs
   - Add usage examples

## Current Status

- ✅ Article model updated with synthesis columns
- ✅ Migration applied (2317b7aeeb89)
- ✅ Schema structure documented
- ✅ Broken implementation removed
- ⏳ Awaiting approval to implement corrected version

## Estimated Time

- Schemas: 30 min
- Service: 1 hour  
- Endpoints: 30 min
- Test fixtures: 30 min
- Unit tests: 1 hour
- Integration tests: 1 hour
- Manual testing: 30 min
- Documentation: 30 min

**Total: ~5.5 hours**

## Next Steps

1. Get approval for corrected design
2. Implement schemas with correct structure
3. Implement service with proper joins
4. Implement endpoints
5. Write comprehensive tests
6. Manual verification
7. Commit and merge
