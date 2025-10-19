# FactCheckService Implementation Plan

> **Goal:** Build a production-ready fact-checking system that automatically validates all RSS feed articles using an external fact-check API, with async processing, error handling, and performance optimization.

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Breakdown](#component-breakdown)
3. [Implementation Phases](#implementation-phases)
4. [API Integration Details](#api-integration-details)
5. [Data Flow](#data-flow)
6. [Error Handling Strategy](#error-handling-strategy)
7. [Testing Strategy](#testing-strategy)
8. [Performance Considerations](#performance-considerations)
9. [Security & Rate Limiting](#security--rate-limiting)
10. [Deployment Checklist](#deployment-checklist)

---

## 🏗️ Architecture Overview

### High-Level Flow

```
RSS Feed Update
    ↓
Article Created (RSSFeedService)
    ↓
Submit Fact-Check Job (FactCheckService)
    ↓
Queue Background Task (Celery)
    ↓
Poll API Every 5s (60-90s total)
    ↓
Store Result in DB (FactCheckService)
    ↓
Update Article Cache (FactCheckService)
    ↓
Frontend Displays Result
```

### System Components

```
┌─────────────────────────────────────────────────────┐
│                 RSS Feed Service                     │
│  • Fetches RSS feeds                                │
│  • Creates Article records                          │
│  • Triggers fact-check submission                   │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│              FactCheckService                        │
│  • Submit job to external API                       │
│  • Transform API response → DB format               │
│  • Store results in article_fact_checks             │
│  • Update articles cache columns                    │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│            Celery Background Task                    │
│  • Poll API for job status                          │
│  • Exponential backoff (5s → 10s → 20s)            │
│  • Retry on transient failures                      │
│  • Timeout after 2 minutes                          │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│         External Fact-Check API                      │
│  • Receives article URL                             │
│  • Performs fact-checking (60-90s)                  │
│  • Returns validation results                       │
└─────────────────────────────────────────────────────┘
```

---

## 🧩 Component Breakdown

### 1. FactCheckService (`app/services/fact_check_service.py`)

**Purpose:** Core business logic for fact-checking operations

**Responsibilities:**
- Submit fact-check jobs to external API
- Poll job status
- Retrieve completed results
- Transform API data to database format
- Store results in database
- Update article cache columns
- Calculate credibility scores
- Handle API errors

**Key Methods:**
```python
class FactCheckService:
    # API Integration
    async def submit_fact_check(url: str) -> str
    async def get_job_status(job_id: str) -> dict
    async def retrieve_result(job_id: str) -> dict
    
    # Data Transformation
    def transform_api_result(api_result: dict) -> dict
    def calculate_credibility_score(validation_results: list) -> int
    def calculate_verdict_counts(validation_results: list) -> dict
    
    # Database Operations
    async def store_fact_check(article_id: UUID, data: dict) -> ArticleFactCheck
    async def update_article_cache(article_id: UUID, score: int, verdict: str)
    async def get_fact_check_by_article(article_id: UUID) -> ArticleFactCheck
    async def get_fact_check_by_job(job_id: str) -> ArticleFactCheck
    
    # Error Handling
    async def handle_api_error(error: Exception, job_id: str)
    async def mark_fact_check_failed(article_id: UUID, reason: str)
```

**Dependencies:**
- `httpx.AsyncClient` for HTTP requests
- `ArticleFactCheckRepository` for database access
- `ArticleRepository` for updating cache
- Config settings for API credentials

---

### 2. ArticleFactCheckRepository (`app/repositories/fact_check_repository.py`)

**Purpose:** Data access layer for fact-check tables

**Responsibilities:**
- CRUD operations for `article_fact_checks`
- CRUD operations for `source_credibility_scores`
- Complex queries (filtering, aggregation)
- Transaction management

**Key Methods:**
```python
class ArticleFactCheckRepository:
    # ArticleFactCheck operations
    async def create(data: dict) -> ArticleFactCheck
    async def get_by_id(id: UUID) -> ArticleFactCheck
    async def get_by_article_id(article_id: UUID) -> ArticleFactCheck
    async def get_by_job_id(job_id: str) -> ArticleFactCheck
    async def update(id: UUID, data: dict) -> ArticleFactCheck
    async def delete(id: UUID) -> bool
    
    # Queries
    async def get_recent_fact_checks(limit: int) -> list[ArticleFactCheck]
    async def get_by_verdict(verdict: str, limit: int) -> list[ArticleFactCheck]
    async def get_by_score_range(min_score: int, max_score: int) -> list[ArticleFactCheck]
    
    # Source credibility
    async def create_credibility_score(data: dict) -> SourceCredibilityScore
    async def get_source_scores(source_id: UUID, period: str) -> list[SourceCredibilityScore]
    async def update_credibility_aggregate(source_id: UUID, period: str)
```

---

### 3. Celery Background Task (`app/tasks/fact_check_tasks.py`)

**Purpose:** Async processing of fact-check jobs

**Responsibilities:**
- Poll API until job completes
- Exponential backoff for polling
- Retry on failures (max 3 retries)
- Timeout after 2 minutes
- Error reporting

**Key Task:**
```python
@celery_app.task(bind=True, max_retries=3)
def process_article_fact_check(
    self,
    article_id: str,
    article_url: str,
    job_id: str
):
    """
    Background task to poll fact-check API and store results.
    
    Flow:
    1. Poll API every 5 seconds
    2. Check job status (queued/started/finished/failed)
    3. If finished: retrieve result, transform, store
    4. If failed: log error, update article
    5. If timeout: retry task
    
    Args:
        article_id: UUID of article
        article_url: Article URL for logging
        job_id: Fact-check API job ID
    
    Raises:
        Retry: If API temporarily unavailable
        MaxRetriesExceeded: After 3 failed attempts
    """
```

**Polling Logic:**
```python
# Exponential backoff
intervals = [5, 10, 20]  # seconds
max_wait = 120  # 2 minutes total

for i, interval in enumerate(intervals):
    status = await api.get_status(job_id)
    
    if status == "finished":
        result = await api.get_result(job_id)
        await service.store_fact_check(article_id, result)
        return
    
    if status == "failed":
        await service.mark_failed(article_id, error)
        return
    
    await asyncio.sleep(interval)
```

---

### 4. API Client (`app/clients/fact_check_client.py`)

**Purpose:** HTTP client for external fact-check API

**Responsibilities:**
- Make HTTP requests to API
- Handle authentication
- Parse responses
- Retry on network errors
- Rate limiting

**Key Methods:**
```python
class FactCheckAPIClient:
    def __init__(self, api_url: str, api_key: str):
        self.client = httpx.AsyncClient(
            base_url=api_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0
        )
    
    async def submit_job(self, url: str, mode: str = "summary") -> dict:
        """Submit fact-check job."""
        response = await self.client.post("/fact-check", json={
            "url": url,
            "mode": mode,
            "generate_image": False,
            "generate_article": True
        })
        response.raise_for_status()
        return response.json()
    
    async def get_status(self, job_id: str) -> dict:
        """Get job status."""
        response = await self.client.get(f"/fact-check/status/{job_id}")
        response.raise_for_status()
        return response.json()
    
    async def get_result(self, job_id: str) -> dict:
        """Get completed fact-check result."""
        response = await self.client.get(f"/fact-check/result/{job_id}")
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
```

---

### 5. API Endpoints (`app/api/v1/endpoints/fact_checks.py`)

**Purpose:** REST API for fact-check operations

**Endpoints:**
```python
# Get fact-check for article
GET /api/v1/fact-checks/{article_id}
Response: {
    "article_id": "uuid",
    "verdict": "TRUE",
    "credibility_score": 95,
    "summary": "...",
    "validation_results": {...},
    "fact_checked_at": "2025-10-17T..."
}

# Manual fact-check trigger (admin only)
POST /api/v1/fact-checks/trigger/{article_id}
Response: {
    "job_id": "abc123",
    "status": "queued",
    "message": "Fact-check initiated"
}

# Get job status
GET /api/v1/fact-checks/status/{job_id}
Response: {
    "job_id": "abc123",
    "status": "finished",
    "progress": 100
}

# Source credibility leaderboard
GET /api/v1/sources/credibility-scores?period=monthly&limit=10
Response: {
    "scores": [
        {
            "source_name": "Reuters",
            "average_score": 92.5,
            "total_articles": 150,
            "period": "monthly"
        }
    ]
}
```

---

### 6. Pydantic Schemas (`app/schemas/fact_check.py`)

**Purpose:** Request/response validation

**Schemas:**
```python
class FactCheckResponse(BaseModel):
    """Fact-check result for article."""
    article_id: UUID
    verdict: str
    credibility_score: int
    confidence: Optional[float]
    summary: str
    claims_analyzed: Optional[int]
    validation_results: dict
    num_sources: Optional[int]
    fact_checked_at: datetime

class FactCheckTriggerResponse(BaseModel):
    """Response after triggering manual fact-check."""
    job_id: str
    status: str
    message: str

class SourceCredibilityScoreResponse(BaseModel):
    """Source credibility score."""
    source_name: str
    average_score: float
    total_articles_checked: int
    period_type: str
    period_start: datetime
    period_end: datetime
```

---

## 📅 Implementation Phases

### Phase 1: Core Service (Day 1)
**Estimated Time:** 4-5 hours

**Components:**
1. `FactCheckAPIClient` - HTTP client
2. `FactCheckService` - Core business logic
3. Data transformation methods
4. Credibility score calculation

**Deliverables:**
- ✅ API client with submit/status/result methods
- ✅ Service can submit jobs
- ✅ Transform API response to DB format
- ✅ Calculate credibility scores
- ✅ Unit tests for transformations

**Acceptance Criteria:**
- Submit job returns job_id
- Transform produces valid DB dict
- Score calculation matches spec (TRUE=100, FALSE=10, etc.)

---

### Phase 2: Repository & Database (Day 1-2)
**Estimated Time:** 2-3 hours

**Components:**
1. `ArticleFactCheckRepository` - Data access
2. Database operations in service
3. Update article cache columns

**Deliverables:**
- ✅ Repository with CRUD methods
- ✅ Service stores fact-checks in DB
- ✅ Article cache columns updated
- ✅ Integration tests

**Acceptance Criteria:**
- Create fact-check record succeeds
- Retrieve by article_id works
- Article cache columns updated
- Integration test passes

---

### Phase 3: Background Tasks (Day 2)
**Estimated Time:** 3-4 hours

**Components:**
1. `process_article_fact_check` Celery task
2. Polling logic with exponential backoff
3. Retry and timeout handling
4. Error logging

**Deliverables:**
- ✅ Celery task polls API
- ✅ Stores result when complete
- ✅ Retries on failures
- ✅ Logs errors properly

**Acceptance Criteria:**
- Task completes for successful job
- Retries on API errors (max 3)
- Times out after 2 minutes
- Stores result correctly

---

### Phase 4: RSS Feed Integration (Day 2-3)
**Estimated Time:** 2 hours

**Components:**
1. Update `RSSFeedService.create_article`
2. Auto-trigger fact-check on article creation
3. Handle fact-check failures gracefully

**Deliverables:**
- ✅ RSS feed service triggers fact-checks
- ✅ Articles created with pending status
- ✅ Background task processes async

**Acceptance Criteria:**
- New articles auto-trigger fact-check
- Article accessible immediately (without fact-check)
- Fact-check appears 60-90s later

---

### Phase 5: API Endpoints (Day 3)
**Estimated Time:** 2-3 hours

**Components:**
1. GET `/fact-checks/{article_id}`
2. POST `/fact-checks/trigger/{article_id}`
3. GET `/fact-checks/status/{job_id}`
4. GET `/sources/credibility-scores`

**Deliverables:**
- ✅ All endpoints functional
- ✅ Proper authentication
- ✅ Error handling
- ✅ API tests

**Acceptance Criteria:**
- Endpoints return correct data
- 404 for missing fact-checks
- Admin-only for trigger endpoint
- Credibility leaderboard works

---

### Phase 6: Testing & Optimization (Day 3-4)
**Estimated Time:** 3-4 hours

**Components:**
1. Comprehensive integration tests
2. Performance optimization
3. Error scenario testing
4. Load testing

**Deliverables:**
- ✅ Integration test suite (>90% coverage)
- ✅ Performance benchmarks met
- ✅ Error handling validated
- ✅ Load test results

**Acceptance Criteria:**
- Test coverage >90%
- Query time <50ms for cached columns
- Handles 100 concurrent fact-checks
- API errors handled gracefully

---

## 🔌 API Integration Details

### External Fact-Check API Specification

**Base URL:** `https://fact-check-api.com/v1` (from config)

**Authentication:** Bearer token in header

**Endpoints:**

#### 1. Submit Job
```http
POST /fact-check
Content-Type: application/json
Authorization: Bearer {API_KEY}

{
  "url": "https://article-url.com",
  "mode": "summary",
  "generate_image": false,
  "generate_article": true
}

Response (202 Accepted):
{
  "job_id": "abc123def456",
  "status": "queued",
  "message": "Job submitted successfully"
}
```

#### 2. Get Status
```http
GET /fact-check/status/{job_id}
Authorization: Bearer {API_KEY}

Response (200 OK):
{
  "job_id": "abc123def456",
  "status": "started",  // queued|started|finished|failed
  "progress": 45,       // 0-100
  "estimated_time_remaining": 30  // seconds
}
```

#### 3. Get Result
```http
GET /fact-check/result/{job_id}
Authorization: Bearer {API_KEY}

Response (200 OK):
{
  "status": "SUCCESS",
  "timestamp": "2025-10-17T16:19:33Z",
  "elapsed_time": 62.5,
  "statistics": {
    "total_claims": 1,
    "validated_claims": 1,
    "total_validation_cost": 0.0107
  },
  "validation_results": [...]
}
```

**Rate Limits:**
- 100 requests/minute for submit
- 1000 requests/minute for status
- Cost: ~$0.01 per fact-check

---

## 🔄 Data Flow

### Sequence Diagram

```
User          RSS Service      FactCheckService    Celery Task        API
 │                 │                   │                 │             │
 │    RSS Update   │                   │                 │             │
 │────────────────>│                   │                 │             │
 │                 │                   │                 │             │
 │                 │  Create Article   │                 │             │
 │                 │──────────────────>│                 │             │
 │                 │                   │                 │             │
 │                 │   Submit Job      │                 │             │
 │                 │────────────────────────────────────────────────>│
 │                 │                   │<────────────────────────────│
 │                 │                   │   job_id: "abc123"          │
 │                 │                   │                 │             │
 │                 │   Queue Task      │                 │             │
 │                 │───────────────────────────────────>│             │
 │                 │                   │                 │             │
 │                 │  Return article   │                 │             │
 │                 │<──────────────────│                 │             │
 │<────────────────│                   │                 │             │
 │  Article        │                   │                 │             │
 │  (pending)      │                   │                 │             │
 │                 │                   │                 │             │
 │                 │                   │    Poll Status  │             │
 │                 │                   │                 │────────────>│
 │                 │                   │                 │<────────────│
 │                 │                   │                 │  "started"  │
 │                 │                   │                 │             │
 │                 │                   │    Wait 5s      │             │
 │                 │                   │                 │─────────┐   │
 │                 │                   │                 │         │   │
 │                 │                   │                 │<────────┘   │
 │                 │                   │                 │             │
 │                 │                   │    Poll Status  │             │
 │                 │                   │                 │────────────>│
 │                 │                   │                 │<────────────│
 │                 │                   │                 │  "finished" │
 │                 │                   │                 │             │
 │                 │                   │   Get Result    │             │
 │                 │                   │                 │────────────>│
 │                 │                   │                 │<────────────│
 │                 │                   │                 │   Result    │
 │                 │                   │                 │             │
 │                 │   Store Result    │                 │             │
 │                 │                   │<────────────────│             │
 │                 │                   │                 │             │
 │                 │   Update Cache    │                 │             │
 │                 │                   │─────────────┐   │             │
 │                 │                   │             │   │             │
 │                 │                   │<────────────┘   │             │
 │                 │                   │                 │             │
 │    Fetch Article│                   │                 │             │
 │────────────────>│                   │                 │             │
 │<────────────────│                   │                 │             │
 │  Article +      │                   │                 │             │
 │  Fact-Check     │                   │                 │             │
```

---

## ⚠️ Error Handling Strategy

### Error Categories

#### 1. API Errors
**Transient (Retry):**
- Network timeouts
- 429 Rate Limited
- 500 Server Error
- 503 Service Unavailable

**Permanent (Fail):**
- 400 Bad Request (invalid URL)
- 401 Unauthorized (invalid API key)
- 404 Not Found
- 413 Payload Too Large

**Handling:**
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
)
async def submit_with_retry(url: str):
    try:
        return await client.submit_job(url)
    except httpx.HTTPStatusError as e:
        if e.response.status_code in [400, 401, 404]:
            raise  # Don't retry
        if e.response.status_code == 429:
            await asyncio.sleep(60)  # Wait 1 minute
            raise  # Retry
        raise
```

#### 2. Database Errors
- Connection failures → Retry
- Integrity errors → Log and fail
- Deadlocks → Retry with backoff

#### 3. Validation Errors
- Invalid article URL → Mark as failed
- Missing required fields → Log error
- Malformed API response → Retry once, then fail

### Error States in Database

```python
# Store failed fact-check
{
    "verdict": "ERROR",
    "credibility_score": -1,  # Indicates error
    "summary": "Fact-check failed: {reason}",
    "validation_results": {"error": error_details},
    "job_id": job_id,
    "fact_checked_at": now()
}
```

Frontend can check:
```python
if article.fact_check_score == -1:
    display("Fact-check unavailable")
elif article.fact_check_score is None:
    display("Fact-check pending...")
else:
    display(fact_check_badge)
```

---

## 🧪 Testing Strategy

### Unit Tests

**Test Files:**
- `tests/unit/test_fact_check_service.py`
- `tests/unit/test_fact_check_transformations.py`
- `tests/unit/test_credibility_score_calculation.py`

**Key Tests:**
```python
def test_calculate_credibility_score_true_verdict():
    """Test score calculation for TRUE verdict."""
    validation_results = [{"validation_output": {"verdict": "TRUE", "confidence": 0.95}}]
    score = calculate_credibility_score(validation_results)
    assert score == 95  # 100 * 0.95

def test_transform_api_result():
    """Test API result transformation."""
    api_result = {...}  # Mock API response
    db_data = transform_api_result(api_result)
    assert "verdict" in db_data
    assert "credibility_score" in db_data
    assert db_data["validation_results"] == api_result["validation_results"]

def test_handle_api_timeout():
    """Test timeout handling."""
    with pytest.raises(TimeoutError):
        await service.submit_fact_check("https://slow-url.com", timeout=1)
```

### Integration Tests

**Test Files:**
- `tests/integration/test_fact_check_end_to_end.py`
- `tests/integration/test_fact_check_api.py`

**Key Tests:**
```python
@pytest.mark.integration
async def test_fact_check_workflow(test_db, mock_api):
    """Test complete fact-check workflow."""
    # 1. Create article
    article = await create_test_article()
    
    # 2. Submit fact-check
    job_id = await fact_check_service.submit_fact_check(article.url)
    assert job_id is not None
    
    # 3. Simulate polling (mock API)
    mock_api.set_status(job_id, "finished")
    mock_api.set_result(job_id, mock_result)
    
    # 4. Process task
    await process_article_fact_check(str(article.id), article.url, job_id)
    
    # 5. Verify stored
    fact_check = await repo.get_by_article_id(article.id)
    assert fact_check.verdict == "TRUE"
    assert fact_check.credibility_score == 95
    
    # 6. Verify cache updated
    updated_article = await article_repo.get_by_id(article.id)
    assert updated_article.fact_check_score == 95
```

### Mock API Client

```python
class MockFactCheckAPIClient:
    """Mock API client for testing."""
    def __init__(self):
        self.jobs = {}
    
    async def submit_job(self, url: str, mode: str) -> dict:
        job_id = f"test-job-{uuid4().hex[:8]}"
        self.jobs[job_id] = {"status": "queued", "url": url}
        return {"job_id": job_id, "status": "queued"}
    
    async def get_status(self, job_id: str) -> dict:
        return self.jobs.get(job_id, {"status": "failed"})
    
    async def get_result(self, job_id: str) -> dict:
        return {
            "status": "SUCCESS",
            "validation_results": [...]
        }
```

---

## ⚡ Performance Considerations

### Caching Strategy

1. **Article Cache Columns**
   - Store score, verdict, timestamp in `articles` table
   - No JOIN needed for list views
   - Target: <10ms query time

2. **Redis Cache** (Optional)
   - Cache frequent fact-check queries
   - TTL: 1 hour
   - Key: `fact_check:{article_id}`

### Database Optimization

1. **Indexes** (already created in migration)
   - `ix_articles_fact_check_score`
   - `ix_articles_fact_check_verdict`
   - `ix_article_fact_checks_article_id`
   - `ix_article_fact_checks_validation_results_gin`

2. **Query Patterns**
   ```python
   # Fast: Uses cached columns
   articles = await db.query(Article).filter(
       Article.fact_check_score > 70
   ).limit(20).all()
   
   # Slower: Requires JOIN for full details
   article_with_details = await db.query(Article).options(
       selectinload(Article.fact_check)
   ).filter(Article.id == article_id).first()
   ```

3. **Pagination**
   - Limit results to 50 per page
   - Use cursor-based pagination for large datasets

### Background Task Optimization

1. **Batch Processing**
   - Process multiple articles in parallel
   - Max 10 concurrent API requests
   - Rate limit: 100/minute

2. **Priority Queue**
   - High priority: Manual fact-checks
   - Normal: Automatic fact-checks
   - Low: Re-checks

---

## 🔒 Security & Rate Limiting

### API Key Management

```python
# app/core/config.py
class Settings(BaseSettings):
    FACT_CHECK_API_URL: str
    FACT_CHECK_API_KEY: SecretStr  # Never logged
    
    @validator("FACT_CHECK_API_KEY")
    def validate_api_key(cls, v):
        if not v or len(v.get_secret_value()) < 20:
            raise ValueError("Invalid FACT_CHECK_API_KEY")
        return v
```

### Rate Limiting

1. **External API Limits**
   - 100 submissions/minute
   - Track in Redis
   - Queue overflow requests

2. **Internal API Limits**
   - `/fact-checks/*`: 100 requests/minute per user
   - `/fact-checks/trigger`: 10 requests/hour (admin only)

### Input Validation

```python
from pydantic import HttpUrl, validator

class FactCheckRequest(BaseModel):
    url: HttpUrl  # Validates URL format
    
    @validator("url")
    def validate_article_url(cls, v):
        # Only allow fact-checking of known domains
        allowed_domains = ["example.com", "news.com"]
        if v.host not in allowed_domains:
            raise ValueError("URL not from allowed source")
        return v
```

---

## 📦 Deployment Checklist

### Environment Variables

```bash
# .env
FACT_CHECK_API_URL=https://fact-check-api.com/v1
FACT_CHECK_API_KEY=your_secret_key_here
FACT_CHECK_ENABLED=true
FACT_CHECK_MODE=summary
FACT_CHECK_POLL_INTERVAL=5
FACT_CHECK_MAX_WAIT=120
FACT_CHECK_RETRY_ATTEMPTS=3
```

### Celery Configuration

```python
# app/core/celery_app.py
celery_app.conf.update(
    task_routes={
        'app.tasks.fact_check_tasks.process_article_fact_check': {
            'queue': 'fact_checks',
            'priority': 5
        }
    },
    task_time_limit=180,  # 3 minutes
    task_soft_time_limit=150  # 2.5 minutes
)
```

### Monitoring

1. **Metrics to Track**
   - Fact-check success rate
   - Average processing time
   - API error rate
   - Queue depth
   - Cost per fact-check

2. **Alerts**
   - API error rate >5%
   - Processing time >120s
   - Queue depth >100
   - Failed tasks >10/hour

3. **Logging**
   ```python
   logger.info("Fact-check submitted", extra={
       "article_id": article_id,
       "job_id": job_id,
       "url": article_url
   })
   
   logger.error("Fact-check failed", extra={
       "article_id": article_id,
       "job_id": job_id,
       "error": str(e)
   })
   ```

### Health Checks

```python
@router.get("/health/fact-check")
async def fact_check_health():
    """Check fact-check service health."""
    try:
        # Test API connectivity
        status = await fact_check_client.get_status("health-check")
        
        # Test database
        count = await repo.count()
        
        return {
            "status": "healthy",
            "api_accessible": True,
            "database_accessible": True,
            "total_fact_checks": count
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

---

## 📊 Success Metrics

### Functional Metrics
- ✅ All articles automatically fact-checked
- ✅ Results available within 90 seconds
- ✅ <1% failure rate
- ✅ Citations properly stored and retrievable

### Performance Metrics
- ✅ Article list query <10ms (cached columns)
- ✅ Full fact-check query <50ms (with JOIN)
- ✅ API response time <100ms
- ✅ Background task completion <120s

### Quality Metrics
- ✅ Test coverage >90%
- ✅ Zero data loss
- ✅ Proper error handling for all scenarios
- ✅ Admin can manually trigger re-checks

---

## 🚀 Estimated Timeline

| Phase | Component | Time | Status |
|-------|-----------|------|--------|
| 1 | API Client + Core Service | 4-5h | ⏳ Pending |
| 2 | Repository + Database Ops | 2-3h | ⏳ Pending |
| 3 | Celery Background Task | 3-4h | ⏳ Pending |
| 4 | RSS Feed Integration | 2h | ⏳ Pending |
| 5 | API Endpoints | 2-3h | ⏳ Pending |
| 6 | Testing & Optimization | 3-4h | ⏳ Pending |
| **Total** | **All Components** | **16-21h** | ⏳ Pending |

**Breakdown by Day:**
- **Day 1:** Phases 1-2 (Core service + Repository)
- **Day 2:** Phases 3-4 (Background tasks + RSS integration)
- **Day 3:** Phases 5-6 (API endpoints + Testing)

---

## ✅ Pre-Implementation Checklist

Before starting implementation:

- [x] Database migration 006 applied
- [x] Migration tested and verified
- [x] Models created and working
- [x] Integration test passes
- [ ] External API credentials obtained
- [ ] API documentation reviewed
- [ ] Celery configured and running
- [ ] Redis configured (for Celery broker)
- [ ] Environment variables set
- [ ] Test environment ready

---

## 📝 Next Steps

**Ready to implement?**

1. Review this plan
2. Confirm external API access
3. Start with Phase 1 (API Client + Core Service)
4. Implement incrementally with tests
5. Deploy to staging
6. Monitor and optimize
7. Deploy to production

**Questions to answer before starting:**
1. Do you have external fact-check API credentials?
2. Is Celery already configured in the project?
3. What should happen if fact-check fails? (show error or hide article?)
4. Should there be manual re-check ability for admins?
5. What's the budget for fact-checking API costs?

---

**Document Version:** 1.0  
**Last Updated:** October 18, 2025  
**Status:** Ready for Implementation
