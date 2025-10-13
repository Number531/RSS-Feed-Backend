# 📋 Recommended Additional Endpoints

## Executive Summary

Based on your current architecture, here are **recommended endpoints** to complete your RSS Feed Aggregator MVP and make it production-ready. I've categorized them by priority.

---

## 🎯 Current Status

### ✅ **Implemented** (13 endpoints)
- **Authentication**: 3 endpoints (register, login, refresh)
- **Votes**: 3 endpoints (cast, remove, get)
- **Comments**: 7 endpoints (create, get, update, delete, tree, replies, list)

### 🚧 **Missing Critical Endpoints** 
- **Articles**: 0 endpoints ❌ **(CRITICAL - your main content!)**
- **Users**: 0 endpoints ❌ **(Important for user management)**
- **RSS Sources**: 0 endpoints ⚠️ **(Needed for feed management)**

---

## 🔥 Priority 1: CRITICAL - Must Have

### **1. Articles Endpoints** ⭐⭐⭐⭐⭐
**Why Critical**: Articles are your core content - users can't access them currently!

#### **A. Public Feed Endpoints** (3 endpoints)

##### `GET /api/v1/articles` - Get Article Feed
```python
Query Params:
- category: Optional[str] = None  # general, politics, us, world, science
- sort_by: str = "hot"  # hot, new, top
- time_range: Optional[str] = None  # hour, day, week, month, year, all
- page: int = 1
- page_size: int = 25

Response: ArticleFeed {
    articles: List[ArticleResponse]
    total: int
    page: int
    page_size: int
    category: str
    sort_by: str
}
```

**What it does**:
- Main feed endpoint (like Reddit/HackerNews front page)
- Supports sorting by hot (trending), new (recent), top (most voted)
- Category filtering
- Time-based filtering
- Pagination
- Returns articles with vote counts, comment counts
- If authenticated, includes user's vote status

##### `GET /api/v1/articles/{article_id}` - Get Single Article
```python
Path Params:
- article_id: UUID

Response: ArticleDetailResponse {
    ...all article fields...
    user_vote: Optional[int]  # -1, 0, 1 if authenticated
    comments_count: int
}
```

**What it does**:
- Get full article details
- Used when user clicks on an article
- Includes user's vote if authenticated
- Returns vote count, comment count

##### `GET /api/v1/articles/search` - Search Articles
```python
Query Params:
- q: str  # search query
- page: int = 1
- page_size: int = 25

Response: ArticleFeed
```

**What it does**:
- Full-text search through articles
- Searches title, description, content
- Uses PostgreSQL's full-text search (TSVECTOR)

---

### **2. User Profile Endpoints** ⭐⭐⭐⭐
**Why Important**: Users need to manage their profiles and see their activity

#### **B. User Management** (4 endpoints)

##### `GET /api/v1/users/me` - Get Current User Profile
```python
Headers: Authorization: Bearer {token}

Response: UserProfile {
    id: UUID
    username: str
    email: str
    created_at: datetime
    comment_count: int
    vote_count: int
}
```

##### `PUT /api/v1/users/me` - Update Profile
```python
Headers: Authorization: Bearer {token}

Body: {
    email: Optional[str]
    current_password: str  # required for security
    new_password: Optional[str]
}
```

##### `GET /api/v1/users/me/votes` - Get User's Votes
```python
Headers: Authorization: Bearer {token}
Query: page, page_size

Response: List[VoteWithArticle {
    vote: VoteResponse
    article: ArticleResponse
}]
```

##### `GET /api/v1/users/me/comments` - Get User's Comments
```python
Headers: Authorization: Bearer {token}
Query: page, page_size

Response: List[CommentWithArticle {
    comment: CommentResponse
    article: ArticleResponse
}]
```

---

## ⭐ Priority 2: HIGH - Strongly Recommended

### **3. RSS Source Management** ⭐⭐⭐
**Why Important**: Admin/power users need to manage RSS feeds

#### **C. RSS Sources** (5 endpoints)

##### `GET /api/v1/sources` - List RSS Sources
```python
Query Params:
- category: Optional[str]
- is_active: Optional[bool]
- page: int = 1
- page_size: int = 50

Response: List[RSSSourceResponse]
```

##### `GET /api/v1/sources/{source_id}` - Get Single Source
```python
Response: RSSSourceResponse with health stats
```

##### `POST /api/v1/sources` - Add RSS Source (Admin)
```python
Headers: Authorization: Bearer {admin_token}
Body: RSSSourceCreate
```

##### `PUT /api/v1/sources/{source_id}` - Update Source (Admin)
```python
Headers: Authorization: Bearer {admin_token}
Body: RSSSourceUpdate
```

##### `DELETE /api/v1/sources/{source_id}` - Remove Source (Admin)
```python
Headers: Authorization: Bearer {admin_token}
```

---

## 🌟 Priority 3: NICE TO HAVE - Enhancement

### **4. Advanced Features** ⭐⭐

#### **D. Trending & Discovery** (2 endpoints)

##### `GET /api/v1/articles/trending` - Trending Articles
```python
Query: time_range (hour, day, week), limit

Response: Top trending articles by engagement
```

##### `GET /api/v1/articles/popular` - Most Popular
```python
Query: time_range, limit

Response: Articles with most votes/comments
```

#### **E. User Preferences** (2 endpoints)

##### `GET /api/v1/users/me/preferences` - Get Preferences
```python
Response: {
    favorite_categories: List[str]
    default_sort: str
    email_notifications: bool
}
```

##### `PUT /api/v1/users/me/preferences` - Update Preferences
```python
Body: UserPreferences
```

#### **F. Statistics** (2 endpoints)

##### `GET /api/v1/stats/overview` - Platform Stats
```python
Response: {
    total_articles: int
    total_users: int
    total_comments: int
    articles_today: int
    active_sources: int
}
```

##### `GET /api/v1/stats/source/{source_id}` - Source Stats
```python
Response: {
    article_count: int
    success_rate: float
    avg_articles_per_day: float
    health_status: str
}
```

---

## 📊 Implementation Roadmap

### **Phase 1: MVP Completion** (2-3 hours)
**Goal**: Make the app usable for end users

✅ Already Done:
- [x] Authentication (3 endpoints)
- [x] Votes (3 endpoints)
- [x] Comments (7 endpoints)

🎯 **Need to Add** (Priority 1):
- [ ] **Articles Feed** (3 endpoints) - **CRITICAL**
- [ ] **User Profile** (4 endpoints) - **IMPORTANT**

**Total New Endpoints**: 7
**Estimated Time**: 2-3 hours

### **Phase 2: Admin Features** (1-2 hours)
**Goal**: Enable RSS source management

- [ ] **RSS Sources** (5 endpoints)

**Total New Endpoints**: 5
**Estimated Time**: 1-2 hours

### **Phase 3: Enhancements** (2-3 hours)
**Goal**: Add discovery and analytics

- [ ] **Trending/Discovery** (2 endpoints)
- [ ] **User Preferences** (2 endpoints)
- [ ] **Statistics** (2 endpoints)

**Total New Endpoints**: 6
**Estimated Time**: 2-3 hours

---

## 🎯 Recommended Implementation Order

### **Do This Next** (In Order):

1. **Articles Feed** (3 endpoints) - ⏱️ 1.5 hours
   - Without this, users can't see any articles!
   - Already have: ArticleService, ArticleRepository, ArticleResponse schemas
   - Just need to create the endpoint file

2. **User Profile** (4 endpoints) - ⏱️ 1 hour
   - Users need to manage their accounts
   - Already have: User model, authentication
   - Need to add user repository methods

3. **RSS Sources** (5 endpoints) - ⏱️ 1.5 hours
   - Admin feature to manage feeds
   - Already have: RSSSource model, schemas
   - Need repository and endpoints

---

## 💡 Why These Endpoints Matter

### **Articles Endpoints = 🔴 CRITICAL**
**Without them:**
- ❌ Users can't browse articles
- ❌ Can't see the RSS feed
- ❌ App is essentially unusable

**With them:**
- ✅ Full Reddit/HackerNews-like experience
- ✅ Users can browse, search, filter articles
- ✅ App becomes functional MVP

### **User Profile = 🟡 IMPORTANT**
**Benefits:**
- ✅ Users can manage their account
- ✅ View their voting/comment history
- ✅ Update email/password
- ✅ See their activity

### **RSS Sources = 🟢 USEFUL**
**Benefits:**
- ✅ Admin can add/remove RSS feeds
- ✅ Monitor feed health
- ✅ Enable/disable problematic sources
- ✅ Transparent source management

---

## 📝 Implementation Notes

### **What You Already Have** ✅

#### For Articles:
- ✅ `ArticleService` with `get_articles_feed()`, `get_article_by_id()`, `search_articles()`
- ✅ `ArticleRepository` with all necessary queries
- ✅ `ArticleResponse`, `ArticleFeed` schemas
- ✅ Article model with relationships

**What's Needed**:
- Just create `app/api/v1/endpoints/articles.py`
- Add dependency injection to `dependencies.py`
- Register router in `api.py`

#### For Users:
- ✅ User model
- ✅ Authentication system
- ✅ `UserResponse` schema (partially)

**What's Needed**:
- Create `UserRepository` with profile methods
- Create `UserService` with business logic
- Create `app/api/v1/endpoints/users.py`
- Add schemas for profile updates

#### For RSS Sources:
- ✅ RSSSource model
- ✅ `RSSSourceResponse`, `RSSSourceCreate`, `RSSSourceUpdate` schemas

**What's Needed**:
- Create `RSSSourceRepository`
- Create `RSSSourceService`
- Create `app/api/v1/endpoints/sources.py`
- Add admin role checking

---

## 🚀 Quick Start Guide

### **Option 1: Implement Articles First** (Recommended)

```bash
# 1. Create articles endpoints (uses existing service/repo)
touch app/api/v1/endpoints/articles.py

# 2. Add to dependencies.py (already exists!)
# - get_article_service() is already there

# 3. Register in api.py
# api_router.include_router(articles.router, prefix="/articles", tags=["articles"])

# 4. Test with existing data
curl http://localhost:8000/api/v1/articles?sort_by=hot&page=1
```

**Time**: 30-60 minutes (mostly endpoint boilerplate)

### **Option 2: Implement All Phase 1** (Complete MVP)

This would give you a fully functional RSS aggregator:
- ✅ Users can browse articles
- ✅ Users can vote and comment (already done)
- ✅ Users can manage their profile
- ✅ Full authentication flow

**Time**: 2-3 hours total

---

## 🎯 My Recommendation

### **START WITH ARTICLES IMMEDIATELY** 🔥

**Why**:
1. **Already 90% done** - Service and repository exist
2. **Just need endpoint wrappers** - Mostly boilerplate code
3. **Makes app immediately usable**
4. **Takes only 30-60 minutes**
5. **Can test with existing database data**

### **Then Add User Profiles**

This completes your MVP and makes the app production-ready.

### **RSS Sources Can Wait**

These are admin features and can be added later when you need content management.

---

## 📋 Decision Matrix

| Endpoints | Priority | Effort | Value | When? |
|-----------|----------|--------|-------|-------|
| **Articles** | 🔴 Critical | Low (30-60 min) | Very High | **NOW** |
| **User Profile** | 🟡 High | Medium (1 hr) | High | Phase 1 |
| **RSS Sources** | 🟢 Medium | Medium (1.5 hr) | Medium | Phase 2 |
| **Trending** | 🔵 Low | Low (30 min) | Medium | Phase 3 |
| **Stats** | 🔵 Low | Low (30 min) | Low | Phase 3 |

---

## ✅ Bottom Line

### **Minimum to Launch**: 
- ✅ Authentication (DONE)
- ✅ Votes (DONE)
- ✅ Comments (DONE)
- ❌ **Articles** - **CRITICAL - DO THIS NEXT!**

### **Recommended for MVP**:
All of the above PLUS:
- User profile management
- RSS source management (basic)

### **Total Time to Complete MVP**:
- Articles: 30-60 minutes
- User Profile: 1 hour
- RSS Sources: 1.5 hours
**Total: ~3 hours**

---

## 🚀 Next Steps

Would you like me to:

1. ✅ **Implement Articles endpoints right now** (30-60 min)
   - Uses existing service/repository
   - Makes app immediately functional
   
2. ✅ **Implement all Phase 1 endpoints** (2-3 hours)
   - Complete MVP functionality
   - Production-ready
   
3. ❓ **Just create the scaffolding**
   - I'll create empty endpoint files
   - You can fill them in later

**My Recommendation**: Let's implement the **Articles endpoints NOW** since you already have all the infrastructure. It's literally just creating wrapper functions around your existing `ArticleService`.

---

**Last Updated**: 2025-10-10  
**Status**: Ready for review and implementation
