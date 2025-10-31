# Analytics Phase 2 - Implementation Plan

**Date:** October 31, 2025  
**Status:** Planning Phase  
**Estimated Duration:** 12-16 hours  

---

## 🎯 Overview

Implementation plan for 7 additional analytics endpoints building upon the existing analytics foundation (Phase 1). Each endpoint follows the established architecture pattern: Repository → Service → API.

---

## 📋 Endpoints to Implement

1. **Source Comparison** - Compare multiple sources side-by-side
2. **Category Analytics** - Statistics by content category
3. **Real-time Dashboard** - Single endpoint for dashboard KPIs
4. **Historical Trends** - Long-term performance tracking
5. **Leaderboard** - Ranked sources by various metrics
6. **Misinformation Hotspots** - Identify problematic areas
7. **Aggregate Statistics** - High-level overview stats

---

## 🏗️ Architecture

### Existing Foundation (Phase 1)
```
✅ AnalyticsRepository (app/repositories/analytics_repository.py)
✅ AnalyticsService (app/services/analytics_service.py)
✅ Analytics API Router (app/api/v1/endpoints/analytics.py)
✅ Analytics Schemas (app/schemas/analytics.py)
```

### Phase 2 Additions
```
📝 Extend AnalyticsRepository with 7 new query methods
📝 Extend AnalyticsService with 7 new business logic methods
📝 Add 7 new API endpoints to existing router
📝 Add 7 new response schemas
📝 Write ~150 new unit tests
📝 Write ~35 new integration tests
```

---

## 📊 Detailed Implementation Plan

### **Endpoint 1: Source Comparison**

#### API Endpoint
```python
GET /api/v1/analytics/sources/compare
```

#### Parameters
- `source_ids`: string (comma-separated UUIDs, required, max 10)
- `days`: int (1-365, default: 30)
- `metric`: enum (`all`, `credibility`, `volume`, `accuracy`)

#### Repository Method
```python
async def compare_sources(
    self,
    source_ids: List[UUID],
    days: int
) -> List[Dict[str, Any]]:
    """
    Compare multiple sources across key metrics.
    
    SQL: Join article_fact_checks with articles and rss_sources
    Aggregate: AVG(credibility_score), COUNT(*), 
               SUM(CASE verdict TRUE), SUM(CASE verdict FALSE)
    Group by: source_id
    Filter: source_id IN (...) AND fact_checked_at >= cutoff
    """
```

#### Service Method
```python
async def compare_sources(
    self,
    source_ids: List[UUID],
    days: int = 30,
    metric: str = "all"
) -> Dict[str, Any]:
    """
    Validate inputs:
    - 2 <= len(source_ids) <= 10
    - 1 <= days <= 365
    - metric in allowed list
    
    Call repository, transform data, add:
    - Percentage comparisons
    - Winner by each metric
    - Statistical significance
    """
```

#### Response Schema
```python
class SourceComparisonResponse(BaseModel):
    sources: List[SourceComparisonItem]
    comparison_period: PeriodInfo
    winners: Dict[str, str]  # metric -> source_name
    
class SourceComparisonItem(BaseModel):
    source_id: UUID
    source_name: str
    avg_score: Decimal
    articles_count: int
    true_rate: Decimal
    false_rate: Decimal
    rank_by_credibility: int
```

#### Tests
- **Unit (Repository):** 3 tests
  - Valid comparison query
  - Handle missing sources
  - Date filtering
  
- **Unit (Service):** 8 tests
  - Valid comparison (2-10 sources)
  - Invalid: 1 source (ValidationError)
  - Invalid: >10 sources (ValidationError)
  - Invalid days
  - Invalid metric
  - Empty results handling
  - Winner calculation
  - Tie handling

- **Integration (API):** 5 tests
  - Successful comparison
  - 400: Invalid source_ids format
  - 400: Too many sources
  - 404: No data for sources
  - Response structure validation

**Estimated Time:** 2.5 hours

---

### **Endpoint 2: Category Analytics**

#### API Endpoint
```python
GET /api/v1/analytics/categories
```

#### Parameters
- `days`: int (1-365, default: 30)
- `min_articles`: int (1-100, default: 5)
- `sort_by`: enum (`credibility`, `volume`, `false_rate`)

#### Repository Method
```python
async def get_category_statistics(
    self,
    days: int,
    min_articles: int
) -> List[Dict[str, Any]]:
    """
    Aggregate statistics by article category.
    
    SQL: Join articles with article_fact_checks
    Aggregate: AVG(credibility_score), COUNT(*),
               verdict counts, list of top sources
    Group by: category
    Having: COUNT(*) >= min_articles
    Order by: AVG(credibility_score) DESC
    """
```

#### Service Method
```python
async def get_category_analytics(
    self,
    days: int = 30,
    min_articles: int = 5,
    sort_by: str = "credibility"
) -> Dict[str, Any]:
    """
    Validate and call repository.
    Add calculated fields:
    - False rate percentage
    - Risk level (low/medium/high)
    - Category health score
    """
```

#### Response Schema
```python
class CategoryAnalyticsResponse(BaseModel):
    categories: List[CategoryAnalytics]
    total_categories: int
    period: PeriodInfo
    
class CategoryAnalytics(BaseModel):
    category: str
    articles_count: int
    avg_credibility: Decimal
    false_rate: Decimal
    risk_level: str
    top_sources: List[str]
```

#### Tests
- **Unit (Repository):** 3 tests
- **Unit (Service):** 7 tests
- **Integration (API):** 4 tests

**Estimated Time:** 2 hours

---

### **Endpoint 3: Real-time Dashboard**

#### API Endpoint
```python
GET /api/v1/analytics/dashboard
```

#### Parameters
- `period`: enum (`today`, `week`, `month`, default: `today`)

#### Repository Methods (Multiple)
```python
async def get_dashboard_summary(
    self,
    period_start: datetime,
    period_end: datetime
) -> Dict[str, Any]:
    """
    Single optimized query for dashboard KPIs.
    
    Returns:
    - Total articles fact-checked
    - Average credibility
    - Verdict distribution
    - Top categories
    - Alert conditions
    """

async def get_trending_sources(
    self,
    days: int
) -> List[Dict[str, Any]]:
    """Most active sources by article count."""

async def get_declining_sources(
    self,
    days: int,
    threshold: float = 0.15
) -> List[Dict[str, Any]]:
    """Sources with significant credibility drop."""
```

#### Service Method
```python
async def get_dashboard_summary(
    self,
    period: str = "today"
) -> Dict[str, Any]:
    """
    Orchestrate multiple repository calls:
    - Dashboard summary
    - Trending sources
    - Alerts for declining quality
    
    Return unified dashboard response.
    """
```

#### Response Schema
```python
class DashboardResponse(BaseModel):
    period: str
    summary: DashboardSummary
    trending_sources: List[str]
    alerts: List[DashboardAlert]
    quick_stats: QuickStats
    
class DashboardAlert(BaseModel):
    type: str
    severity: str
    source_id: Optional[UUID]
    message: str
```

#### Tests
- **Unit (Repository):** 5 tests
- **Unit (Service):** 8 tests
- **Integration (API):** 5 tests

**Estimated Time:** 3 hours

---

### **Endpoint 4: Historical Trends**

#### API Endpoint
```python
GET /api/v1/analytics/sources/{source_id}/history
```

#### Parameters
- `source_id`: UUID (path parameter)
- `period`: enum (`month`, `quarter`, `year`, `all_time`)
- `metric`: enum (`credibility`, `volume`, `accuracy`)

#### Repository Method
```python
async def get_source_historical_trends(
    self,
    source_id: UUID,
    period_type: str
) -> List[Dict[str, Any]]:
    """
    Historical performance data for a source.
    
    SQL: Time-bucketed aggregation
    Bucket by: month, quarter, or year based on period_type
    Calculate: trend direction (up/down/stable)
    """
```

#### Service Method
```python
async def get_source_history(
    self,
    source_id: UUID,
    period: str = "month",
    metric: str = "credibility"
) -> Dict[str, Any]:
    """
    Validate source exists.
    Calculate overall trend.
    Identify best/worst periods.
    """
```

#### Response Schema
```python
class HistoricalTrendsResponse(BaseModel):
    source_id: UUID
    source_name: str
    period_type: str
    historical_data: List[TrendDataPoint]
    overall_trend: str
    best_period: str
    worst_period: str
    
class TrendDataPoint(BaseModel):
    period: str
    avg_score: Decimal
    articles_count: int
    trend: str  # up/down/stable
```

#### Tests
- **Unit (Repository):** 4 tests
- **Unit (Service):** 9 tests
- **Integration (API):** 6 tests

**Estimated Time:** 2.5 hours

---

### **Endpoint 5: Leaderboard**

#### API Endpoint
```python
GET /api/v1/analytics/leaderboard
```

#### Parameters
- `metric`: enum (`credibility`, `accuracy`, `volume`, `consistency`)
- `limit`: int (5-50, default: 10)
- `direction`: enum (`top`, `bottom`, default: `top`)
- `days`: int (1-365, default: 30)
- `category`: string (optional filter)

#### Repository Method
```python
async def get_source_leaderboard(
    self,
    metric: str,
    days: int,
    limit: int,
    direction: str,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Ranked list of sources by metric.
    
    SQL: Order sources by specified metric
    Include: rank, score, rank change from previous period
    """
```

#### Service Method
```python
async def get_leaderboard(
    self,
    metric: str = "credibility",
    limit: int = 10,
    direction: str = "top",
    days: int = 30,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate parameters.
    Add badges (🥇🥈🥉) for top 3.
    Calculate rank changes.
    """
```

#### Response Schema
```python
class LeaderboardResponse(BaseModel):
    metric: str
    period_days: int
    direction: str
    leaderboard: List[LeaderboardEntry]
    
class LeaderboardEntry(BaseModel):
    rank: int
    source_id: UUID
    source_name: str
    category: str
    score: Decimal
    change: str  # "+2", "-1", "new"
    badge: Optional[str]  # emoji
```

#### Tests
- **Unit (Repository):** 4 tests
- **Unit (Service):** 10 tests
- **Integration (API):** 6 tests

**Estimated Time:** 2.5 hours

---

### **Endpoint 6: Misinformation Hotspots**

#### API Endpoint
```python
GET /api/v1/analytics/hotspots
```

#### Parameters
- `days`: int (1-365, default: 30)
- `threshold`: float (0.1-1.0, default: 0.3)
- `type`: enum (`all`, `category`, `source`)

#### Repository Method
```python
async def get_misinformation_hotspots(
    self,
    days: int,
    threshold: float,
    hotspot_type: str
) -> List[Dict[str, Any]]:
    """
    Identify areas with high false/misleading rates.
    
    SQL: Calculate false_rate for categories and sources
    Filter: false_rate >= threshold
    Order by: false_rate DESC, articles_count DESC
    """
```

#### Service Method
```python
async def identify_hotspots(
    self,
    days: int = 30,
    threshold: float = 0.3,
    hotspot_type: str = "all"
) -> Dict[str, Any]:
    """
    Validate inputs.
    Assign severity levels (low/medium/high/critical).
    Generate recommendations.
    """
```

#### Response Schema
```python
class HotspotsResponse(BaseModel):
    hotspots: List[Hotspot]
    threshold: float
    period_days: int
    recommendations: List[str]
    
class Hotspot(BaseModel):
    type: str  # category or source
    name: str
    false_rate: Decimal
    articles_count: int
    severity: str
    details: Optional[Dict[str, Any]]
```

#### Tests
- **Unit (Repository):** 3 tests
- **Unit (Service):** 8 tests
- **Integration (API):** 5 tests

**Estimated Time:** 2 hours

---

### **Endpoint 7: Aggregate Statistics**

#### API Endpoint
```python
GET /api/v1/analytics/stats
```

#### Parameters
- `include_lifetime`: bool (default: true)
- `include_trends`: bool (default: true)

#### Repository Method
```python
async def get_aggregate_statistics(
    self,
    include_lifetime: bool = True
) -> Dict[str, Any]:
    """
    High-level statistics across all data.
    
    Queries:
    - Total articles fact-checked (all time)
    - Total claims verified
    - Current month stats
    - Comparison with previous month
    """
```

#### Service Method
```python
async def get_aggregate_stats(
    self,
    include_lifetime: bool = True,
    include_trends: bool = True
) -> Dict[str, Any]:
    """
    Calculate:
    - Month-over-month changes
    - Milestone achievements
    - Overall accuracy rate
    """
```

#### Response Schema
```python
class AggregateStatsResponse(BaseModel):
    lifetime: Optional[LifetimeStats]
    this_month: CurrentPeriodStats
    trends: Optional[TrendComparison]
    milestones: List[str]
    
class LifetimeStats(BaseModel):
    articles_fact_checked: int
    sources_monitored: int
    claims_verified: int
    accuracy_rate: Decimal
```

#### Tests
- **Unit (Repository):** 3 tests
- **Unit (Service):** 6 tests
- **Integration (API):** 4 tests

**Estimated Time:** 1.5 hours

---

## 📁 File Structure

### Files to Modify
```
app/repositories/analytics_repository.py
  - Add ~200 lines (7 new methods)

app/services/analytics_service.py
  - Add ~350 lines (7 new methods)

app/api/v1/endpoints/analytics.py
  - Add ~400 lines (7 new endpoints)

app/schemas/analytics.py
  - Add ~300 lines (14 new schemas)
```

### Test Files to Create/Modify
```
tests/unit/test_analytics_repository.py
  - Add ~25 new tests (~500 lines)

tests/unit/test_analytics_service.py
  - Add ~56 new tests (~1100 lines)

tests/integration/test_analytics_endpoints.py (NEW)
  - Add ~35 new integration tests (~700 lines)
```

---

## 🧪 Testing Strategy

### Unit Tests (Repository Layer)
- **Total:** 25 new tests
- **Focus:**
  - SQL query correctness
  - Parameter handling
  - Edge cases (empty results, null values)
  - Date range filtering

### Unit Tests (Service Layer)
- **Total:** 56 new tests
- **Focus:**
  - Parameter validation
  - Business logic correctness
  - Error handling
  - Data transformation
  - Calculated fields
  - Concurrent operations

### Integration Tests (API Layer)
- **Total:** 35 new tests
- **Focus:**
  - HTTP status codes
  - Request validation
  - Response structure
  - Error messages
  - Authentication
  - Rate limiting

### Test Coverage Goal
- **Target:** 95%+ coverage for all new code
- **Strategy:** Test-driven development (TDD)

---

## 🔄 Implementation Order

### Phase 2A (Days 1-2): Foundation
1. ✅ **Aggregate Statistics** (easiest, sets patterns)
2. ✅ **Category Analytics** (reuses patterns)

### Phase 2B (Days 3-4): Core Features
3. ✅ **Source Comparison** (high user value)
4. ✅ **Leaderboard** (engaging, reuses queries)

### Phase 2C (Days 5-6): Advanced Features
5. ✅ **Historical Trends** (complex time-bucketing)
6. ✅ **Real-time Dashboard** (orchestrates multiple queries)

### Phase 2D (Day 7): Analysis Features
7. ✅ **Misinformation Hotspots** (advanced analytics)

---

## 📊 Estimated Effort

| Task | Estimated Hours |
|------|----------------|
| Repository methods | 3.5 hours |
| Service methods | 4.5 hours |
| API endpoints | 3.0 hours |
| Response schemas | 1.5 hours |
| Unit tests (repository) | 1.5 hours |
| Unit tests (service) | 3.0 hours |
| Integration tests | 2.0 hours |
| Documentation updates | 1.0 hours |
| **TOTAL** | **20 hours** |

**With buffer:** 24 hours (~3 days)

---

## 🎯 Success Criteria

### Code Quality
- ✅ All tests passing (116 new tests)
- ✅ Code coverage ≥95%
- ✅ No linting errors
- ✅ Type hints on all functions
- ✅ Comprehensive docstrings

### Functionality
- ✅ All 7 endpoints working
- ✅ Parameter validation comprehensive
- ✅ Error messages clear and actionable
- ✅ Response times <500ms (with caching)

### Documentation
- ✅ API documentation updated
- ✅ Usage examples provided
- ✅ Frontend integration guide
- ✅ Postman collection updated

---

## 🔒 Dependencies & Prerequisites

### Required
- ✅ Phase 1 analytics endpoints deployed
- ✅ Database with fact-check data
- ✅ Existing test infrastructure

### Optional
- ⚠️ Redis for caching (recommended)
- ⚠️ Rate limiting middleware
- ⚠️ Monitoring/observability setup

---

## 🚀 Deployment Checklist

### Pre-deployment
- [ ] All tests passing locally
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Performance testing done
- [ ] Security review passed

### Deployment
- [ ] Merge to main branch
- [ ] Run migrations (if any)
- [ ] Deploy to staging
- [ ] Smoke test on staging
- [ ] Deploy to production
- [ ] Monitor error rates

### Post-deployment
- [ ] Verify all endpoints responding
- [ ] Check performance metrics
- [ ] Update API documentation site
- [ ] Notify frontend team
- [ ] Create announcement

---

## 📚 Documentation Updates Needed

### API Documentation (ANALYTICS_API.md)
- Add 7 new endpoint specifications
- Add request/response examples
- Add error scenarios
- Add rate limit info

### Frontend Integration Guide
- Add TypeScript interfaces
- Add React hook examples
- Add usage patterns
- Add dashboard examples

### Changelog
- Version bump to 1.1.0
- List all new features
- Migration guide (if needed)

---

## 🎓 Lessons from Phase 1

### What Worked Well
- ✅ Layered architecture (easy to extend)
- ✅ Comprehensive testing approach
- ✅ Clear parameter validation
- ✅ Detailed documentation

### Improvements for Phase 2
- 🔄 Add caching layer (Redis)
- 🔄 Create integration test suite
- 🔄 Add performance benchmarks
- 🔄 Implement request logging

---

## 💡 Future Considerations (Phase 3)

### Potential Enhancements
1. **Export endpoint** (CSV/Excel downloads)
2. **Forecast endpoint** (ML-based predictions)
3. **Quality metrics** (fact-check process quality)
4. **Custom reports** (user-defined analytics)
5. **Real-time streaming** (WebSocket support)

### Infrastructure
- CDN for static analytics data
- Read replicas for analytics queries
- Elasticsearch for advanced search
- GraphQL API layer

---

## 📞 Support & Questions

**Implementation Lead:** Analytics Development Team  
**Review Required:** Senior Backend Engineer  
**Stakeholders:** Product, Frontend, QA Teams

---

**Document Status:** ✅ Ready for Implementation  
**Next Step:** Begin Phase 2A (Aggregate Statistics + Category Analytics)
