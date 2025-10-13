# 📖 Reading History Feature - Implementation Plan

**Feature**: Reading History / Article Views Tracking  
**Phase**: Phase 1 - Day 3  
**Estimated Time**: 2-3 hours  
**Status**: 🔄 Ready to Start

---

## 📋 Overview

Track when users view articles, including engagement metrics like reading duration and scroll depth. This feature enables:
- Recent reading history
- Reading statistics (time spent, articles read)
- Personalized recommendations (future)
- User analytics

---

## 🎯 Feature Requirements

### Core Features
1. **Record Article Views** - Track when user views an article
2. **List Reading History** - View past article views with pagination
3. **Recent Articles** - Get recently read articles (last N days)
4. **Reading Stats** - Aggregate statistics (total views, reading time)
5. **Clear History** - Delete reading history (privacy)

### Optional Engagement Metrics
- Reading duration (seconds spent on article)
- Scroll percentage (how much of article was read)

### Privacy & Storage
- No content duplication (just references to articles)
- User can clear their own history
- Automatic cleanup after N days (future enhancement)

---

## 🏗️ Architecture Overview

```
Database Layer (PostgreSQL)
    ↓
Model Layer (SQLAlchemy)
    ↓
Repository Layer (Data Access)
    ↓
Service Layer (Business Logic)
    ↓
Schema Layer (Pydantic Validation)
    ↓
API Layer (FastAPI Endpoints)
    ↓
Tests (Unit + Integration)
```

---

## 📅 Step-by-Step Implementation Plan

### **Phase 1: Database & Models** (30 minutes)

#### Step 1.1: Create Database Migration
**File**: `alembic/versions/2025_10_10_1950-002_add_reading_history_table.py`

**Schema Design**:
```sql
CREATE TABLE reading_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    viewed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    duration_seconds INTEGER,  -- Optional: time spent reading
    scroll_percentage DECIMAL(5,2),  -- Optional: % of article scrolled
    
    -- Indexes for performance
    INDEX idx_reading_history_user_id (user_id),
    INDEX idx_reading_history_article_id (article_id),
    INDEX idx_reading_history_viewed_at (viewed_at),
    INDEX idx_reading_history_user_viewed (user_id, viewed_at)
);
```

**Key Points**:
- No unique constraint (users can view same article multiple times)
- Cascade deletes if user or article is deleted
- Indexes for efficient querying by user and time
- Optional engagement metrics (nullable)

**Test**:
- [ ] Migration applies successfully
- [ ] Table created with correct columns
- [ ] All 4 indexes created
- [ ] Foreign keys working

---

#### Step 1.2: Create SQLAlchemy Model
**File**: `app/models/reading_history.py`

**Model Design**:
```python
class ReadingHistory(Base):
    __tablename__ = "reading_history"
    
    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID, ForeignKey("users.id", ondelete="CASCADE"))
    article_id: Mapped[UUID] = mapped_column(PGUUID, ForeignKey("articles.id", ondelete="CASCADE"))
    viewed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scroll_percentage: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="reading_history")
    article: Mapped["Article"] = relationship("Article", back_populates="reading_history")
```

**Updates Required**:
- `app/models/user.py` - Add `reading_history` relationship
- `app/models/article.py` - Add `reading_history` relationship
- `app/models/__init__.py` - Register model

**Test**:
- [ ] Model imports successfully
- [ ] Relationships work
- [ ] No circular import issues

---

### **Phase 2: Repository Layer** (45 minutes)

#### Step 2.1: Create Repository
**File**: `app/repositories/reading_history_repository.py`

**Methods to Implement**:
1. `record_view()` - Record an article view
2. `get_user_history()` - Get user's history with pagination and date filtering
3. `get_recently_read()` - Get recent articles (last N days)
4. `count_views_by_user()` - Count total views
5. `get_total_reading_time()` - Sum reading duration
6. `clear_history()` - Delete history (all or before date)

**Key Features**:
- Pagination support
- Date range filtering
- Aggregate statistics
- Efficient queries with indexes

**Test**:
- [ ] Create unit test file
- [ ] Test record_view()
- [ ] Test get_user_history() with pagination
- [ ] Test get_recently_read()
- [ ] Test count_views_by_user()
- [ ] Test get_total_reading_time()
- [ ] Test clear_history()
- [ ] Test date filtering

---

### **Phase 3: Service Layer** (30 minutes)

#### Step 3.1: Create Service
**File**: `app/services/reading_history_service.py`

**Business Logic**:
1. **record_view()** - Validate article exists, then record view
2. **get_history()** - Get paginated history for user
3. **get_recently_read()** - Get recent reads with configurable days
4. **get_reading_stats()** - Calculate statistics
5. **clear_history()** - Delete with optional date cutoff

**Validations**:
- Article must exist before recording view
- User can only access their own history
- Date ranges must be valid
- Statistics handle null values

**Test**:
- [ ] Article validation works
- [ ] Ownership checks work
- [ ] Statistics calculated correctly
- [ ] Null values handled

---

### **Phase 4: Schema Layer** (20 minutes)

#### Step 4.1: Create Pydantic Schemas
**File**: `app/schemas/reading_history.py`

**Schemas Needed**:
```python
1. ReadingHistoryCreate - Record a view
   - article_id: UUID
   - duration_seconds: Optional[int]
   - scroll_percentage: Optional[float]

2. ReadingHistoryResponse - Single history item
   - id: UUID
   - user_id: UUID
   - article_id: UUID
   - viewed_at: datetime
   - duration_seconds: Optional[int]
   - scroll_percentage: Optional[float]
   - article: Optional[ArticleResponse]

3. ReadingHistoryListResponse - Paginated list
   - items: List[ReadingHistoryResponse]
   - total: int
   - page: int
   - page_size: int
   - has_more: bool

4. ReadingStatsResponse - Statistics
   - total_views: int
   - total_reading_time_seconds: int
   - period_days: int
   - average_reading_time_seconds: int
```

**Test**:
- [ ] All schemas import successfully
- [ ] Validation rules work
- [ ] from_attributes works

---

### **Phase 5: API Endpoints** (45 minutes)

#### Step 5.1: Create API Routes
**File**: `app/api/v1/endpoints/reading_history.py`

**Endpoints**:
```
POST   /api/v1/history/                Record article view
GET    /api/v1/history/                List history (paginated)
GET    /api/v1/history/recent          Get recently read articles
GET    /api/v1/history/stats           Get reading statistics
DELETE /api/v1/history/                Clear history
```

**Details**:

1. **POST /api/v1/history/**
   - Body: `{ article_id, duration_seconds?, scroll_percentage? }`
   - Returns: 201 with ReadingHistoryResponse
   - Auth: Required

2. **GET /api/v1/history/**
   - Query: `?page=1&page_size=25&start_date=...&end_date=...`
   - Returns: 200 with ReadingHistoryListResponse
   - Auth: Required

3. **GET /api/v1/history/recent**
   - Query: `?days=7&limit=10`
   - Returns: 200 with List[ReadingHistoryResponse]
   - Auth: Required

4. **GET /api/v1/history/stats**
   - Query: `?days=30`
   - Returns: 200 with ReadingStatsResponse
   - Auth: Required

5. **DELETE /api/v1/history/**
   - Query: `?before_date=...` (optional)
   - Returns: 204 No Content
   - Auth: Required

**Test**:
- [ ] All endpoints registered
- [ ] Router added to api.py
- [ ] OpenAPI docs generated

---

### **Phase 6: Integration Tests** (30 minutes)

#### Step 6.1: Create Test Script
**File**: `test_reading_history_api.sh`

**Test Scenarios**:
1. ✅ User login
2. ✅ Get article ID
3. ✅ Record view (basic)
4. ✅ Record view with metrics
5. ✅ List history
6. ✅ Get recent articles
7. ✅ Get reading stats
8. ✅ Pagination
9. ✅ Date filtering
10. ✅ Clear partial history
11. ✅ Clear all history
12. ✅ Unauthorized access

**Expected Results**:
- All tests pass
- No internal server errors
- Proper HTTP status codes
- Data integrity maintained

---

## 🔄 Implementation Order

### Session 1: Database & Models (30 min)
1. Create migration script
2. Apply migration
3. Verify table structure
4. Create model
5. Update relationships
6. Test model imports

### Session 2: Repository Layer (45 min)
7. Create repository file
8. Implement all methods
9. Create unit tests
10. Run repository tests
11. Verify all pass

### Session 3: Service & Schemas (50 min)
12. Create schemas
13. Test schema imports
14. Create service
15. Implement business logic
16. Test service integration

### Session 4: API & Testing (45 min)
17. Create API endpoints
18. Register router
19. Create integration tests
20. Run full test suite
21. Verify all pass

---

## 🧪 Testing Strategy

### Repository Layer Tests
**File**: `test_reading_history_repository.py`
- Test each repository method
- Test edge cases
- Test date filtering
- Test aggregations

### API Integration Tests
**File**: `test_reading_history_api.sh`
- Test all endpoints
- Test happy paths
- Test error cases
- Test authentication
- Test pagination
- Test filtering

---

## 📊 Success Criteria

- [ ] Migration applied successfully
- [ ] Model created and relationships working
- [ ] Repository layer: 100% tests passing
- [ ] Service layer: business logic validated
- [ ] API: All 5 endpoints working
- [ ] Integration tests: 90%+ pass rate
- [ ] No breaking changes to existing features
- [ ] Performance: < 200ms response times
- [ ] OpenAPI docs updated

---

## 🔒 Security Considerations

1. **Authentication**: All endpoints require valid JWT token
2. **Authorization**: Users can only access their own history
3. **Privacy**: Users can clear their history
4. **Data Validation**: All inputs validated via Pydantic
5. **SQL Injection**: Protected by SQLAlchemy ORM

---

## 📈 Performance Optimizations

1. **Database Indexes**: 4 indexes for fast queries
2. **Pagination**: Prevent loading too much data
3. **Eager Loading**: Load article relationships efficiently
4. **Aggregations**: Use database functions for stats
5. **Date Filtering**: Use indexed timestamp columns

---

## 🎯 API Usage Examples

### Record a View
```bash
curl -X POST "http://localhost:8000/api/v1/history/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": "uuid-here",
    "duration_seconds": 120,
    "scroll_percentage": 85.5
  }'
```

### Get Reading History
```bash
curl "http://localhost:8000/api/v1/history/?page=1&page_size=25" \
  -H "Authorization: Bearer {token}"
```

### Get Recently Read
```bash
curl "http://localhost:8000/api/v1/history/recent?days=7&limit=10" \
  -H "Authorization: Bearer {token}"
```

### Get Stats
```bash
curl "http://localhost:8000/api/v1/history/stats?days=30" \
  -H "Authorization: Bearer {token}"
```

### Clear History
```bash
curl -X DELETE "http://localhost:8000/api/v1/history/" \
  -H "Authorization: Bearer {token}"
```

---

## 📁 Files to Create/Modify

### New Files (7)
1. ✅ `alembic/versions/2025_10_10_1950-002_add_reading_history_table.py`
2. ✅ `app/models/reading_history.py`
3. ✅ `app/repositories/reading_history_repository.py`
4. ✅ `app/services/reading_history_service.py`
5. ✅ `app/schemas/reading_history.py`
6. ✅ `app/api/v1/endpoints/reading_history.py`
7. ✅ `test_reading_history_repository.py`
8. ✅ `test_reading_history_api.sh`

### Modified Files (4)
1. ✅ `app/models/user.py` - Add relationship
2. ✅ `app/models/article.py` - Add relationship
3. ✅ `app/models/__init__.py` - Register model
4. ✅ `app/api/v1/api.py` - Register router

---

## 🚀 Execution Plan

### Pre-Implementation Checklist
- [x] Bookmarks feature complete and tested
- [x] Server running on port 8000
- [x] Database accessible
- [x] Implementation plan reviewed

### Phase 1: Foundation (30 min)
```bash
# Step 1: Create migration
# Step 2: Apply migration
# Step 3: Verify database
# Step 4: Create model
# Step 5: Test model
```

### Phase 2: Data Layer (45 min)
```bash
# Step 6: Create repository
# Step 7: Create repository tests
# Step 8: Run tests
# Step 9: Verify all pass
```

### Phase 3: Business Logic (50 min)
```bash
# Step 10: Create schemas
# Step 11: Create service
# Step 12: Test service
```

### Phase 4: API & Testing (45 min)
```bash
# Step 13: Create endpoints
# Step 14: Register router
# Step 15: Create integration tests
# Step 16: Run full test suite
# Step 17: Verify success
```

---

## ⚠️ Potential Challenges & Solutions

### Challenge 1: High Volume of History Data
**Solution**: 
- Pagination required
- Consider archiving old data (future)
- Add limit to date range queries

### Challenge 2: Multiple Views of Same Article
**Solution**:
- No unique constraint (allow duplicates)
- Aggregate stats account for multiple views

### Challenge 3: Null Engagement Metrics
**Solution**:
- Make duration and scroll nullable
- Stats calculations handle nulls with COALESCE

### Challenge 4: Performance with Large History
**Solution**:
- Proper indexes on user_id and viewed_at
- Pagination mandatory
- Date range filters encouraged

---

## 🎓 Learning from Bookmarks Implementation

### What Worked Well
✅ Step-by-step approach with testing at each phase  
✅ Clear separation of concerns (repository → service → API)  
✅ Comprehensive test scripts  
✅ Documentation at each step

### Improvements for Reading History
✅ Test model imports immediately after creation  
✅ Create test script earlier in process  
✅ Verify method names match between layers  
✅ Test server reload after changes

---

## 📝 Implementation Checklist

### Database Layer
- [ ] Migration script created
- [ ] Migration applied
- [ ] Table structure verified
- [ ] Indexes created
- [ ] Foreign keys working

### Model Layer
- [ ] ReadingHistory model created
- [ ] Relationships added to User model
- [ ] Relationships added to Article model
- [ ] Model registered in __init__.py
- [ ] Model imports successfully

### Repository Layer
- [ ] Repository file created
- [ ] All 6 methods implemented
- [ ] Unit test file created
- [ ] All repository tests pass

### Service Layer
- [ ] Service file created
- [ ] Business logic implemented
- [ ] Validations in place
- [ ] Error handling correct

### Schema Layer
- [ ] All 4 schemas created
- [ ] Validation rules defined
- [ ] Schemas import successfully

### API Layer
- [ ] Endpoint file created
- [ ] All 5 endpoints implemented
- [ ] Router registered in api.py
- [ ] Dependency injection working

### Testing
- [ ] Repository tests: 100% pass
- [ ] Integration test script created
- [ ] Integration tests: 90%+ pass
- [ ] Manual testing complete

### Documentation
- [ ] Implementation plan complete
- [ ] API examples documented
- [ ] Test results documented

---

## 🎯 Ready to Begin?

All prerequisites are in place:
- ✅ Implementation plan complete
- ✅ Architecture defined
- ✅ Test strategy planned
- ✅ Success criteria clear

**Next Step**: Begin Phase 1 - Database & Models

Would you like to proceed with implementation?

---

**Estimated Total Time**: 2.5 - 3 hours  
**Confidence Level**: High (following proven Bookmarks pattern)  
**Risk Level**: Low (well-defined requirements)  
**Production Readiness**: Expected after successful testing
