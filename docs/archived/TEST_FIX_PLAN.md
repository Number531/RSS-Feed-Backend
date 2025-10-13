# Integration Test Fixes - Step-by-Step Plan

## Problem Analysis

### Issue 1: Missing `url_hash` Field (16 Errors)
**Location**: `tests/integration/test_comment_voting_api.py`  
**Root Cause**: The `test_article` fixture creates Article objects without the required `url_hash` field  
**Error**: `null value in column "url_hash" of relation "articles" violates not-null constraint`

**Affected Tests**: 16 tests in `test_comment_voting_api.py`

### Issue 2: Incorrect `create_access_token` Call (1 Error)
**Location**: `tests/integration/test_comment_voting_api.py:76`  
**Root Cause**: Using `data=` parameter instead of positional argument  
**Error**: `TypeError: create_access_token() got an unexpected keyword argument 'data'`

**Affected Tests**: 1 test (`test_vote_on_nonexistent_comment`)

### Issue 3: Other Test Failures (15 Failed)
**Locations**: Various test files  
**Root Causes**: 
- Missing authentication in some tests
- Comment tree building issues
- RSS feed parsing issues

## Step-by-Step Fix Plan

### Phase 1: Fix Comment Voting API Tests (Priority 1)
**Impact**: Fixes 16 errors  
**Risk**: Low - isolated to test fixtures  
**Time**: 15 minutes

#### Step 1.1: Add URL Hash Utility Function
**File**: `tests/conftest.py` or create `tests/utils.py`  
**Action**: Create a helper function to generate URL hashes

```python
import hashlib

def generate_url_hash(url: str) -> str:
    """Generate SHA-256 hash of URL for deduplication."""
    return hashlib.sha256(url.encode('utf-8')).hexdigest()
```

#### Step 1.2: Fix `test_article` Fixture
**File**: `tests/integration/test_comment_voting_api.py`  
**Current Code** (lines 42-53):
```python
@pytest.fixture
async def test_article(db_session: AsyncSession, test_user: User):
    """Create a test article."""
    article = Article(
        id=uuid4(),
        title="Test Article",
        url="https://example.com/article",
        rss_source_id=uuid4()  # ❌ Missing url_hash and category
    )
    db_session.add(article)
    await db_session.commit()
    await db_session.refresh(article)
    return article
```

**Fixed Code**:
```python
@pytest.fixture
async def test_article(db_session: AsyncSession, test_user: User):
    """Create a test article."""
    from app.models.rss_source import RSSSource
    from tests.utils import generate_url_hash
    
    # Create RSS source first (foreign key requirement)
    rss_source = RSSSource(
        id=uuid4(),
        name="Test Source",
        url="https://example.com/feed",
        url_hash=generate_url_hash("https://example.com/feed"),
        category="Technology"
    )
    db_session.add(rss_source)
    await db_session.flush()
    
    # Create article with all required fields
    article_url = "https://example.com/article"
    article = Article(
        id=uuid4(),
        title="Test Article",
        url=article_url,
        url_hash=generate_url_hash(article_url),
        rss_source_id=rss_source.id,
        category="Technology"  # Required field
    )
    db_session.add(article)
    await db_session.commit()
    await db_session.refresh(article)
    return article
```

#### Step 1.3: Fix `auth_headers` Fixture
**File**: `tests/integration/test_comment_voting_api.py`  
**Current Code** (lines 73-77):
```python
@pytest.fixture
def auth_headers(test_user: User):
    """Create authentication headers with JWT token."""
    token = create_access_token(data={"sub": str(test_user.id)})  # ❌ Wrong parameter
    return {"Authorization": f"Bearer {token}"}
```

**Fixed Code**:
```python
@pytest.fixture
def auth_headers(test_user: User):
    """Create authentication headers with JWT token."""
    token = create_access_token({"sub": str(test_user.id)})  # ✅ Correct - positional arg
    return {"Authorization": f"Bearer {token}"}
```

### Phase 2: Fix Other Test Files (Priority 2)
**Impact**: Fixes remaining failures  
**Risk**: Medium - may affect multiple test files  
**Time**: 30 minutes

#### Step 2.1: Search for All Article Fixtures
**Action**: Find all places where Article objects are created in tests

```bash
grep -r "Article(" tests/ --include="*.py"
```

#### Step 2.2: Create Centralized Test Fixtures
**File**: `tests/conftest.py`  
**Action**: Add reusable fixtures for common test objects

```python
@pytest.fixture
async def rss_source(db_session: AsyncSession):
    """Create a test RSS source."""
    from app.models.rss_source import RSSSource
    from tests.utils import generate_url_hash
    
    source = RSSSource(
        id=uuid4(),
        name="Test Source",
        url="https://example.com/feed",
        url_hash=generate_url_hash("https://example.com/feed"),
        category="Technology"
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)
    return source

@pytest.fixture
async def test_article(db_session: AsyncSession, rss_source):
    """Create a test article with all required fields."""
    from app.models.article import Article
    from tests.utils import generate_url_hash
    
    article_url = f"https://example.com/article-{uuid4().hex[:8]}"
    article = Article(
        id=uuid4(),
        title=f"Test Article {uuid4().hex[:8]}",
        url=article_url,
        url_hash=generate_url_hash(article_url),
        rss_source_id=rss_source.id,
        category="Technology"
    )
    db_session.add(article)
    await db_session.commit()
    await db_session.refresh(article)
    return article
```

#### Step 2.3: Fix Comment Tree Tests
**Files**: `tests/integration/test_comments.py`  
**Issues**: 
- `test_get_comment_tree` - Check tree building logic
- `test_comment_tree_max_depth` - Check depth limiting

**Action**: Review and fix tree building tests

#### Step 2.4: Fix Authentication Tests
**Files**: Various  
**Issues**: Tests expecting 401 but getting different status codes

**Action**: Check authentication middleware and test expectations

### Phase 3: Verification and Documentation (Priority 3)
**Impact**: Ensures all fixes work  
**Risk**: Low  
**Time**: 15 minutes

#### Step 3.1: Run All Integration Tests
```bash
pytest tests/integration/ -v --tb=short
```

#### Step 3.2: Fix Any Remaining Issues
**Action**: Address any new failures that appear

#### Step 3.3: Update Documentation
**Files**: 
- `TESTING_STATUS.md`
- `TEST_FIX_PLAN.md` (this file)

## Implementation Order

### Step 1: Create Utility Function (5 min)
1. Create `tests/utils.py`
2. Add `generate_url_hash()` function
3. Test the function works

### Step 2: Fix Comment Voting API Tests (10 min)
1. Update `test_comment_voting_api.py` fixtures
2. Run tests: `pytest tests/integration/test_comment_voting_api.py -v`
3. Verify all 16 tests pass

### Step 3: Centralize Fixtures (10 min)
1. Move fixed fixtures to `tests/conftest.py`
2. Update imports in test files
3. Verify no regressions

### Step 4: Fix Other Test Files (20 min)
1. Search for all Article creation without `url_hash`
2. Update each occurrence
3. Run full test suite

### Step 5: Final Verification (10 min)
1. Run complete integration test suite
2. Document results
3. Update testing status

## Risk Mitigation

### Backup Strategy
```bash
# Before starting, create a backup
git add .
git commit -m "Checkpoint before test fixes"
git branch backup-before-test-fixes
```

### Incremental Testing
- Fix one test file at a time
- Run tests after each fix
- Commit working changes incrementally

### Rollback Plan
If issues arise:
```bash
git reset --hard backup-before-test-fixes
```

## Success Criteria

- ✅ All 16 comment voting API errors resolved
- ✅ All 15 failed tests passing
- ✅ No new test failures introduced
- ✅ All fixtures use proper `url_hash` values
- ✅ Centralized fixtures in `conftest.py`
- ✅ Documentation updated

## Estimated Time

- **Phase 1**: 15 minutes
- **Phase 2**: 30 minutes
- **Phase 3**: 15 minutes
- **Total**: ~60 minutes

## Notes

- The `url_hash` field is required by the Article model for deduplication
- It must be a SHA-256 hash of the URL
- The `category` field is also required
- Foreign key `rss_source_id` must reference an actual RSS source
- Always use `generate_url_hash()` utility for consistency
