# Backend API Endpoints Audit
## Complete Review of Existing Analytics & Stats Capabilities

**Date:** 2025-10-31  
**Purpose:** Identify existing stats/analytics endpoints before implementing new aggregate scoring features

---

## 📊 EXISTING STATS ENDPOINTS

### 1. **Admin Stats** - `/api/v1/admin/stats/overview`
**Status:** ✅ **EXISTS**  
**Auth:** Admin only  
**Returns:**
```json
{
  "users": {"total": 150},
  "articles": {"total": 2500},
  "rss_sources": {
    "total": 15,
    "active": 12,
    "inactive": 3
  }
}
```
**Limitations:**
- ❌ No fact-check metrics
- ❌ No credibility scores
- ❌ No source reliability ratings
- ❌ No temporal trends
- ✅ Basic counts only

---

### 2. **Feed Health** - `/api/v1/admin/feeds/health`
**Status:** ✅ **EXISTS**  
**Auth:** Admin only  
**Returns:**
```json
{
  "total_sources": 15,
  "healthy": 12,
  "unhealthy": 2,
  "inactive": 1,
  "health_rate": 0.8,
  "unhealthy_feeds": [
    {
      "id": "uuid",
      "name": "Source Name",
      "success_rate": 0.65,
      "consecutive_failures": 3,
      "last_fetched": "2025-10-31T00:00:00Z"
    }
  ]
}
```
**Limitations:**
- ✅ RSS feed health monitoring
- ❌ No content quality metrics
- ❌ No fact-check statistics per source
- ✅ Technical health only

---

### 3. **User Stats** - `/api/v1/users/me/stats`
**Status:** ⚠️ **NOT IMPLEMENTED** (501 error)  
**Auth:** User  
**Planned Returns:** Votes, comments, karma  
**Note:** Placeholder endpoint, not functional

---

### 4. **Reading History Stats** - `/api/v1/reading-history/stats`
**Status:** ✅ **EXISTS**  
**Auth:** User  
**Returns:**
```json
{
  "total_articles_read": 45,
  "total_time_spent_minutes": 320,
  "average_session_duration_minutes": 7.1,
  "articles_per_day": 1.5,
  "top_categories": ["politics", "tech"],
  "reading_streak_days": 12
}
```
**Limitations:**
- ✅ Personal reading metrics only
- ❌ No source credibility data
- ❌ No fact-check engagement
- ✅ User-specific only (not aggregate)

---

### 5. **Notification Stats** - `/api/v1/notifications/stats`
**Status:** ✅ **EXISTS**  
**Auth:** User  
**Returns:** Unread counts, notification types breakdown  
**Limitations:**
- ✅ Personal notification metrics
- ❌ No content or source analytics

---

### 6. **Trending Articles** - `/api/v1/search/trending`
**Status:** ✅ **EXISTS**  
**Auth:** Public  
**Returns:**
```json
{
  "articles": [
    {
      "id": "uuid",
      "title": "Article title",
      "vote_velocity": 12.5,
      "comment_velocity": 3.2,
      "engagement_score": 34.6,
      "published_at": "2025-10-31T00:00:00Z"
    }
  ],
  "period": "24h",
  "total": 20
}
```
**Metrics:**
- ✅ Engagement velocity
- ✅ Vote/comment tracking
- ❌ No fact-check credibility
- ❌ No source reliability

---

### 7. **Popular Articles** - `/api/v1/search/popular`
**Status:** ✅ **EXISTS**  
**Auth:** Public  
**Returns:** Most upvoted articles by time period  
**Limitations:**
- ✅ Vote-based popularity
- ❌ No quality/credibility metrics

---

## ❌ MISSING ANALYTICS ENDPOINTS

### **NOT FOUND - Fact-Check Analytics:**
1. ❌ `/api/v1/analytics/sources` - Source credibility aggregates
2. ❌ `/api/v1/analytics/trends` - Temporal fact-check trends
3. ❌ `/api/v1/analytics/claims` - Claims accuracy statistics
4. ❌ `/api/v1/analytics/reliability` - Source reliability scores
5. ❌ `/api/v1/fact-check/stats` - Overall fact-check metrics
6. ❌ `/api/v1/sources/{source_id}/stats` - Per-source analytics

---

## 📋 COMPLETE ENDPOINT INVENTORY

### **Authentication** (3 endpoints)
```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
```

### **Articles** (3 endpoints)
```
GET    /api/v1/articles/                      # Feed with pagination
GET    /api/v1/articles/search                # Search articles
GET    /api/v1/articles/{article_id}          # Single article
```

### **Fact-Check** (1 endpoint) ⚠️ **LIMITED**
```
GET    /api/v1/articles/{article_id}/fact-check  # Individual article only
```
**Missing:**
- No aggregate fact-check stats
- No source-level credibility
- No temporal trends

### **Search & Discovery** (3 endpoints)
```
GET    /api/v1/search                         # Full-text search
GET    /api/v1/search/trending                # Engagement velocity
GET    /api/v1/search/popular                 # Vote-based ranking
```

### **Admin** (10 endpoints)
```
GET    /api/v1/admin/celery/status
POST   /api/v1/admin/celery/fetch-now
POST   /api/v1/admin/celery/fetch-feed/{feed_id}
GET    /api/v1/admin/celery/task/{task_id}
GET    /api/v1/admin/celery/active-tasks
POST   /api/v1/admin/feeds
PUT    /api/v1/admin/feeds/{feed_id}
DELETE /api/v1/admin/feeds/{feed_id}
GET    /api/v1/admin/feeds/health            # RSS health only
GET    /api/v1/admin/stats/overview          # Basic counts only
```

### **User Management** (4 endpoints)
```
GET    /api/v1/users/me
PATCH  /api/v1/users/me
DELETE /api/v1/users/me
GET    /api/v1/users/me/stats                # 501 NOT IMPLEMENTED
```

### **Reading History** (7 endpoints)
```
POST   /api/v1/reading-history/
GET    /api/v1/reading-history/
GET    /api/v1/reading-history/recent
GET    /api/v1/reading-history/stats         # Personal stats only
DELETE /api/v1/reading-history/
GET    /api/v1/reading-history/export
GET    /api/v1/reading-history/preferences
PUT    /api/v1/reading-history/preferences
```

### **Bookmarks** (8 endpoints)
```
POST   /api/v1/bookmarks/
GET    /api/v1/bookmarks/
GET    /api/v1/bookmarks/collections
GET    /api/v1/bookmarks/check/{article_id}
GET    /api/v1/bookmarks/{bookmark_id}
PATCH  /api/v1/bookmarks/{bookmark_id}
DELETE /api/v1/bookmarks/{bookmark_id}
DELETE /api/v1/bookmarks/article/{article_id}
```

### **Comments** (10 endpoints)
```
POST   /api/v1/comments/
GET    /api/v1/comments/article/{article_id}
GET    /api/v1/comments/article/{article_id}/tree
GET    /api/v1/comments/{comment_id}
GET    /api/v1/comments/{comment_id}/replies
PUT    /api/v1/comments/{comment_id}
DELETE /api/v1/comments/{comment_id}
POST   /api/v1/comments/{comment_id}/vote
DELETE /api/v1/comments/{comment_id}/vote
GET    /api/v1/comments/{comment_id}/vote
GET    /api/v1/comments/{comment_id}/vote/summary
```

### **Votes** (3 endpoints)
```
POST   /api/v1/votes/
DELETE /api/v1/votes/{article_id}
GET    /api/v1/votes/article/{article_id}
```

### **Notifications** (9 endpoints)
```
GET    /api/v1/notifications/
GET    /api/v1/notifications/stats           # Personal stats only
GET    /api/v1/notifications/unread-count
GET    /api/v1/notifications/preferences
PUT    /api/v1/notifications/preferences
GET    /api/v1/notifications/{notification_id}
POST   /api/v1/notifications/mark-read
POST   /api/v1/notifications/mark-all-read
DELETE /api/v1/notifications/{notification_id}
```

### **RSS Feeds** (11 endpoints)
```
GET    /api/v1/rss-feeds/
GET    /api/v1/rss-feeds/categories
GET    /api/v1/rss-feeds/subscriptions
GET    /api/v1/rss-feeds/subscribed
GET    /api/v1/rss-feeds/{feed_id}
POST   /api/v1/rss-feeds/
PUT    /api/v1/rss-feeds/{feed_id}
DELETE /api/v1/rss-feeds/{feed_id}
POST   /api/v1/rss-feeds/{feed_id}/subscribe
DELETE /api/v1/rss-feeds/{feed_id}/unsubscribe
PUT    /api/v1/rss-feeds/{feed_id}/subscription
```

---

## 🎯 VERDICT: NO AGGREGATE FACT-CHECK ANALYTICS EXIST

### **Confirmed Missing:**
1. ❌ Source-level credibility aggregation
2. ❌ Temporal fact-check trends
3. ❌ Claims accuracy statistics
4. ❌ Reliability scoring across sources
5. ❌ Verdict distribution analytics
6. ❌ Rolling averages over time
7. ❌ Comparative source analysis

### **Existing Stats Are:**
- ✅ Basic system counts (users, articles, sources)
- ✅ RSS feed technical health
- ✅ Personal user metrics only
- ✅ Engagement metrics (votes, comments)
- ❌ **NO fact-check quality metrics**

---

## 📝 RECOMMENDATION: IMPLEMENT NEW `/api/v1/analytics` ENDPOINTS

### **Priority 1: Core Analytics**
```
GET /api/v1/analytics/sources        # Source credibility aggregates
GET /api/v1/analytics/trends         # Temporal fact-check trends  
GET /api/v1/analytics/claims         # Claims accuracy stats
```

### **Priority 2: Enhanced Stats**
```
GET /api/v1/admin/stats/fact-checks  # Add to existing admin stats
GET /api/v1/sources/{id}/reliability # Per-source deep dive
GET /api/v1/analytics/compare        # Source comparison
```

### **Data Already Available:**
✅ All necessary data exists in `article_fact_checks` table  
✅ Aggregate queries tested and working  
✅ Logic prototyped in `scripts/utilities/aggregate_source_scoring.py`  
✅ Just needs FastAPI endpoint wrappers

---

## 🚀 IMPLEMENTATION EFFORT: 2-3 Days

**Day 1:** Create `/api/v1/analytics/sources` endpoint  
**Day 2:** Create `/api/v1/analytics/trends` and `/claims` endpoints  
**Day 3:** Add tests, documentation, materialized views  

**Blocker:** None - all prerequisites met ✅

