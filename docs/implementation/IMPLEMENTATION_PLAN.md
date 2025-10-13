# 📋 Implementation Plan: Articles & User Profile Endpoints

**Date**: 2025-10-10  
**Goal**: Complete MVP by implementing critical Articles and User Profile endpoints  
**Estimated Time**: 2-3 hours  
**Status**: 🚧 In Progress

---

## 📊 Overview

### Phase 1: Articles Endpoints (3 endpoints)
- **Time**: 30-60 minutes
- **Priority**: 🔴 CRITICAL
- **Status**: Ready to implement

### Phase 2: User Profile Endpoints (4 endpoints)
- **Time**: 1-1.5 hours
- **Priority**: 🟡 HIGH
- **Status**: Need to create repository/service first

---

## 🏗️ Architecture Review

### **What We Have** ✅
1. **Articles Infrastructure**
   - ✅ `ArticleService` - Complete with all business logic
   - ✅ `ArticleRepository` - All database queries implemented
   - ✅ `ArticleResponse`, `ArticleFeed` schemas
   - ✅ Article model with relationships
   - ✅ `get_article_service()` in dependencies.py

2. **User Infrastructure**
   - ✅ User model with relationships
   - ✅ `UserResponse`, `UserUpdate`, `UserCreate` schemas
   - ✅ Authentication system working
   - ✅ Password hashing with bcrypt

### **What We Need to Create** 🚧
1. **For Articles**
   - 🚧 `app/api/v1/endpoints/articles.py` - Endpoint wrappers

2. **For User Profile**
   - 🚧 `UserRepository` - Database operations
   - 🚧 `UserService` - Business logic
   - 🚧 `app/api/v1/endpoints/users.py` - Endpoints
   - 🚧 Additional schemas for profile stats
   - 🚧 Dependency injection functions

---

## 📝 Detailed Implementation Steps

### **PHASE 1: Articles Endpoints** ⏱️ 30-60 min

#### **File**: `app/api/v1/endpoints/articles.py`

##### **Endpoint 1: GET /api/v1/articles** - Article Feed
```python
@router.get("/", response_model=dict)
async def get_articles_feed(
    category: Optional[str] = Query(None),
    sort_by: str = Query("hot", regex="^(hot|new|top)$"),
    time_range: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user_optional),
    article_service: ArticleService = Depends(get_article_service)
)
```

**What it does**:
- Calls `article_service.get_articles_feed()`
- Returns articles with pagination metadata
- Includes user's vote status if authenticated
- Supports filtering and sorting

**Response**:
```json
{
  "articles": [...],
  "total": 150,
  "page": 1,
  "page_size": 25,
  "total_pages": 6,
  "category": "general",
  "sort_by": "hot",
  "time_range": "all"
}
```

##### **Endpoint 2: GET /api/v1/articles/{article_id}** - Single Article
```python
@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    article_service: ArticleService = Depends(get_article_service)
)
```

**What it does**:
- Calls `article_service.get_article_by_id()`
- Returns article with user's vote if authenticated
- Raises 404 if not found

##### **Endpoint 3: GET /api/v1/articles/search** - Search Articles
```python
@router.get("/search", response_model=dict)
async def search_articles(
    q: str = Query(..., min_length=1, max_length=200),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    article_service: ArticleService = Depends(get_article_service)
)
```

**What it does**:
- Calls `article_service.search_articles()`
- Full-text search through title/description
- Returns paginated results

**Dependencies**:
- ✅ Already exists: `get_article_service()` in dependencies.py
- ✅ Already exists: `get_current_user_optional()` in security.py

**Router Registration**:
```python
# In app/api/v1/api.py
from app.api.v1.endpoints import auth, votes, comments, articles

api_router.include_router(articles.router, prefix="/articles", tags=["articles"])
```

---

### **PHASE 2: User Profile Endpoints** ⏱️ 1-1.5 hours

#### **Step 2.1: Create UserRepository** (20 min)

**File**: `app/repositories/user_repository.py`

```python
class UserRepository:
    """Repository for user database operations."""
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]
    async def get_by_email(self, email: str) -> Optional[User]
    async def get_by_username(self, username: str) -> Optional[User]
    async def update_user(self, user_id: UUID, updates: dict) -> User
    async def get_user_votes(self, user_id: UUID, page: int, page_size: int)
    async def get_user_comments(self, user_id: UUID, page: int, page_size: int)
    async def get_user_stats(self, user_id: UUID) -> dict
```

**Methods Needed**:
1. `get_by_id()` - Get user by UUID
2. `update_user()` - Update user fields (email, password, etc.)
3. `get_user_votes()` - Get paginated vote history with articles
4. `get_user_comments()` - Get paginated comment history with articles
5. `get_user_stats()` - Count votes and comments

#### **Step 2.2: Create UserService** (20 min)

**File**: `app/services/user_service.py`

```python
class UserService(BaseService):
    """Service for user profile operations."""
    
    async def get_profile(self, user_id: UUID) -> dict
    async def update_profile(self, user_id: UUID, updates: UserProfileUpdate) -> User
    async def change_password(self, user_id: UUID, current_pw: str, new_pw: str)
    async def get_user_activity(self, user_id: UUID, activity_type: str, page, size)
```

**Business Logic**:
- Profile validation
- Password verification before changes
- Activity aggregation
- Statistics calculation

#### **Step 2.3: Create Additional Schemas** (10 min)

**File**: Update `app/schemas/user.py`

```python
class UserProfile(BaseModel):
    """User profile with statistics."""
    id: UUID
    username: str
    email: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime
    
    # Statistics
    vote_count: int = 0
    comment_count: int = 0
    
class UserProfileUpdate(BaseModel):
    """Update profile fields."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    current_password: Optional[str] = None  # Required for password change
    new_password: Optional[str] = None

class UserVoteHistory(BaseModel):
    """Vote with article details."""
    vote: VoteResponse
    article: ArticleResponse

class UserCommentHistory(BaseModel):
    """Comment with article details."""
    comment: CommentResponse
    article: ArticleResponse
```

#### **Step 2.4: Create User Endpoints** (30 min)

**File**: `app/api/v1/endpoints/users.py`

##### **Endpoint 1: GET /api/v1/users/me** - Get Profile
```python
@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
)
```

##### **Endpoint 2: PUT /api/v1/users/me** - Update Profile
```python
@router.put("/me", response_model=UserProfile)
async def update_profile(
    updates: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
)
```

##### **Endpoint 3: GET /api/v1/users/me/votes** - Vote History
```python
@router.get("/me/votes", response_model=List[UserVoteHistory])
async def get_user_votes(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
)
```

##### **Endpoint 4: GET /api/v1/users/me/comments** - Comment History
```python
@router.get("/me/comments", response_model=List[UserCommentHistory])
async def get_user_comments(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
)
```

#### **Step 2.5: Update Dependencies** (5 min)

**File**: `app/api/dependencies.py`

Add:
```python
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService

def get_user_repository(
    db: AsyncSession = Depends(get_db)
) -> UserRepository:
    return UserRepository(db)

def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> UserService:
    return UserService(user_repo)
```

#### **Step 2.6: Register Router** (1 min)

**File**: `app/api/v1/api.py`

```python
from app.api.v1.endpoints import auth, votes, comments, articles, users

api_router.include_router(users.router, prefix="/users", tags=["users"])
```

---

## 🧪 Testing Strategy

### **Articles Endpoints Testing**

#### Test Cases:
1. **GET /articles**
   - ✅ Get articles without auth
   - ✅ Get articles with auth (includes user votes)
   - ✅ Filter by category
   - ✅ Sort by hot/new/top
   - ✅ Filter by time range
   - ✅ Pagination works
   - ✅ Empty results handled

2. **GET /articles/{id}**
   - ✅ Get existing article
   - ✅ Get with user vote
   - ✅ 404 for non-existent article

3. **GET /articles/search**
   - ✅ Search with results
   - ✅ Search with no results
   - ✅ Pagination works
   - ✅ Invalid query rejected

### **User Profile Endpoints Testing**

#### Test Cases:
1. **GET /users/me**
   - ✅ Get profile with stats
   - ✅ Requires authentication

2. **PUT /users/me**
   - ✅ Update email
   - ✅ Update username
   - ✅ Change password (with current password)
   - ✅ Update multiple fields
   - ✅ Validation errors

3. **GET /users/me/votes**
   - ✅ Get vote history
   - ✅ Includes article details
   - ✅ Pagination

4. **GET /users/me/comments**
   - ✅ Get comment history
   - ✅ Includes article details
   - ✅ Pagination

---

## 📂 File Structure

```
app/
├── api/
│   ├── dependencies.py          [UPDATE] Add user service DI
│   └── v1/
│       ├── api.py              [UPDATE] Register new routers
│       └── endpoints/
│           ├── articles.py     [CREATE] Articles endpoints
│           └── users.py        [CREATE] User profile endpoints
├── repositories/
│   └── user_repository.py      [CREATE] User data access
├── services/
│   └── user_service.py         [CREATE] User business logic
└── schemas/
    └── user.py                 [UPDATE] Add profile schemas

tests/
└── integration/
    ├── test_articles.py        [CREATE] Articles tests
    └── test_users.py           [CREATE] User profile tests
```

---

## ✅ Implementation Checklist

### Phase 1: Articles (30-60 min)
- [ ] Create `articles.py` endpoint file
- [ ] Implement GET feed endpoint
- [ ] Implement GET by ID endpoint
- [ ] Implement GET search endpoint
- [ ] Register router in `api.py`
- [ ] Test all endpoints

### Phase 2: User Profile (1-1.5 hours)
- [ ] Create `UserRepository`
- [ ] Create `UserService`
- [ ] Update user schemas
- [ ] Create `users.py` endpoint file
- [ ] Implement GET profile endpoint
- [ ] Implement PUT update endpoint
- [ ] Implement GET votes history
- [ ] Implement GET comments history
- [ ] Add DI functions to `dependencies.py`
- [ ] Register router in `api.py`
- [ ] Test all endpoints

### Testing & Documentation
- [ ] Create integration tests
- [ ] Run all tests
- [ ] Update API documentation
- [ ] Create usage examples

---

## 🎯 Success Criteria

### Articles Endpoints
- ✅ Users can browse article feed
- ✅ Feed supports sorting (hot/new/top)
- ✅ Feed supports filtering (category, time)
- ✅ Users can view single article
- ✅ Users can search articles
- ✅ Pagination works correctly
- ✅ User votes are included when authenticated

### User Profile Endpoints
- ✅ Users can view their profile
- ✅ Users can update email/username
- ✅ Users can change password
- ✅ Users can see voting history
- ✅ Users can see comment history
- ✅ All operations require authentication
- ✅ Proper error handling

---

## 📋 Implementation Order

1. **Articles Feed** (20 min)
   - Highest priority
   - Makes app usable
   - Straightforward implementation

2. **Articles Detail & Search** (20 min)
   - Complete articles functionality
   - Uses existing service methods

3. **UserRepository** (20 min)
   - Foundation for user features
   - Database access layer

4. **UserService** (20 min)
   - Business logic layer
   - Coordinates repository calls

5. **User Endpoints** (30 min)
   - API layer
   - Connects service to HTTP

6. **Testing** (30 min)
   - Verify all functionality
   - Integration tests

---

## 🚀 Getting Started

### Step 1: Create Articles Endpoints
```bash
touch app/api/v1/endpoints/articles.py
# Implement 3 endpoints using ArticleService
```

### Step 2: Test Articles
```bash
# Restart server
curl http://localhost:8000/api/v1/articles?sort_by=hot
```

### Step 3: Create User Infrastructure
```bash
touch app/repositories/user_repository.py
touch app/services/user_service.py
touch app/api/v1/endpoints/users.py
```

### Step 4: Test User Profile
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/users/me
```

---

## 📊 Time Breakdown

| Task | Estimated | Actual | Status |
|------|-----------|--------|--------|
| Articles endpoints | 30-60 min | TBD | 🚧 Pending |
| UserRepository | 20 min | TBD | 🚧 Pending |
| UserService | 20 min | TBD | 🚧 Pending |
| User endpoints | 30 min | TBD | 🚧 Pending |
| Testing | 30 min | TBD | 🚧 Pending |
| **TOTAL** | **2-3 hours** | **TBD** | 🚧 In Progress |

---

## 💡 Notes

### **Why This Order?**
1. **Articles first** - Makes app immediately usable
2. **User repository** - Foundation for user features
3. **User service** - Business logic layer
4. **User endpoints** - Complete user management

### **Key Patterns to Follow**
- Use existing patterns from votes/comments endpoints
- Proper error handling (404, 403, 422)
- Include docstrings for all functions
- Type hints everywhere
- Pagination for list endpoints
- Optional authentication where appropriate

### **Common Pitfalls to Avoid**
- ❌ Don't forget to register routers
- ❌ Don't skip authentication checks
- ❌ Don't forget pagination metadata
- ❌ Don't expose sensitive data (passwords)
- ❌ Don't skip input validation

---

**Status**: Ready to begin implementation  
**Next Step**: Create `app/api/v1/endpoints/articles.py`  
**Estimated Completion**: 2-3 hours from start
