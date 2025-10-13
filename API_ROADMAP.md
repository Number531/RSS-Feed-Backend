# RSS News Aggregator - API Roadmap & Recommendations

**Date**: October 10, 2025  
**Current Status**: MVP Complete with Core Features

---

## Current API Endpoints (Implemented) ✅

### 1. **Authentication** (3 endpoints) ✅
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token

### 2. **Articles** (3 endpoints) ✅
- `GET /api/v1/articles/` - Get articles feed (with filters, sorting, pagination)
- `GET /api/v1/articles/search` - Full-text search articles
- `GET /api/v1/articles/{article_id}` - Get single article details

### 3. **Comments** (5 endpoints) ✅
- `POST /api/v1/comments/` - Create comment
- `GET /api/v1/comments/article/{article_id}` - Get comments for article
- `GET /api/v1/comments/article/{article_id}/tree` - Get threaded comments
- `GET /api/v1/comments/{comment_id}` - Get single comment
- `GET /api/v1/comments/{comment_id}/replies` - Get comment replies

### 4. **Voting** (3 endpoints) ✅
- `POST /api/v1/votes/` - Cast vote on article
- `GET /api/v1/votes/article/{article_id}` - Get votes for article
- `DELETE /api/v1/votes/{article_id}` - Remove vote

### 5. **User Profile** (2 endpoints) ✅
- `GET /api/v1/users/me` - Get current user profile
- `PATCH /api/v1/users/me` - Update user profile
- `DELETE /api/v1/users/me` - Delete account
- `GET /api/v1/users/me/stats` - User statistics (501 - Not Implemented)

### 6. **System** (2 endpoints) ✅
- `GET /health` - Health check
- `GET /` - Root endpoint

**Total Endpoints**: 19 (17 functional, 1 placeholder)

---

## Recommended Additional Endpoints

### Priority 1: Essential Features (High Impact, Low Effort)

#### **A. User Activity & History** 🔥
**Value**: High engagement, personalization  
**Complexity**: Low-Medium

```
GET /api/v1/users/me/history
  - Get user's reading history (viewed articles)
  - Pagination support
  - Filter by date range
  
GET /api/v1/users/me/votes
  - Get all articles user has voted on
  - Filter by vote type (upvote/downvote)
  - Pagination support
  
GET /api/v1/users/me/comments
  - Get all user's comments
  - Include article context
  - Pagination support

DELETE /api/v1/users/me/history
  - Clear reading history
```

**Use Cases:**
- Users track their reading activity
- "Continue reading" feature
- Personalized recommendations
- Activity overview

---

#### **B. Bookmarks/Saved Articles** 🔥🔥
**Value**: Very High - Core feature for news apps  
**Complexity**: Low

```
POST /api/v1/bookmarks/
  - Save article for later
  - Optional: Add to collections/folders
  
GET /api/v1/bookmarks/
  - Get all saved articles
  - Filter by collection
  - Pagination support
  
DELETE /api/v1/bookmarks/{article_id}
  - Remove bookmark
  
GET /api/v1/articles/{article_id}/bookmarked
  - Check if article is bookmarked
```

**Database Addition:**
```sql
CREATE TABLE bookmarks (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  article_id UUID REFERENCES articles(id),
  collection VARCHAR(100),  -- Optional grouping
  created_at TIMESTAMP,
  UNIQUE(user_id, article_id)
);
```

---

#### **C. User Preferences/Settings** 🔥
**Value**: High - Better UX  
**Complexity**: Low

```
GET /api/v1/users/me/preferences
  - Get user preferences (theme, categories, notifications)
  
PATCH /api/v1/users/me/preferences
  - Update preferences
  
Available Preferences:
  - favorite_categories: ["politics", "science"]
  - theme: "light" | "dark" | "auto"
  - language: "en" | "es" | etc.
  - notifications_enabled: boolean
  - email_digest: "daily" | "weekly" | "never"
  - reading_speed: "slow" | "medium" | "fast"
```

**Database Addition:**
```sql
CREATE TABLE user_preferences (
  user_id UUID PRIMARY KEY REFERENCES users(id),
  favorite_categories JSONB,
  theme VARCHAR(20),
  language VARCHAR(10),
  notifications_enabled BOOLEAN,
  email_digest VARCHAR(20),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

---

#### **D. Article View Tracking** 🔥
**Value**: Medium-High - Analytics, recommendations  
**Complexity**: Low

```
POST /api/v1/articles/{article_id}/view
  - Record article view (anonymous or authenticated)
  - Track view duration, scroll depth (optional)
  
GET /api/v1/articles/trending
  - Get trending articles by views
  - Time-based (last hour, day, week)
```

---

### Priority 2: Enhanced Features (High Value, Medium Effort)

#### **E. RSS Source Management** 🔥🔥🔥
**Value**: Critical for admin/power users  
**Complexity**: Medium

```
# Public endpoints
GET /api/v1/sources/
  - List all active RSS sources
  - Filter by category
  - Pagination support

GET /api/v1/sources/{source_id}
  - Get source details
  - Include article count, last updated

GET /api/v1/sources/{source_id}/articles
  - Get articles from specific source
  - Pagination support

# User subscription endpoints
POST /api/v1/users/me/subscriptions/{source_id}
  - Follow/subscribe to RSS source

DELETE /api/v1/users/me/subscriptions/{source_id}
  - Unfollow RSS source

GET /api/v1/users/me/subscriptions
  - Get user's subscribed sources

# Admin endpoints (require admin role)
POST /api/v1/admin/sources/
  - Add new RSS source

PATCH /api/v1/admin/sources/{source_id}
  - Update RSS source

DELETE /api/v1/admin/sources/{source_id}
  - Remove RSS source

POST /api/v1/admin/sources/{source_id}/refresh
  - Manually trigger RSS feed refresh
```

---

#### **F. Notifications** 🔥
**Value**: High - User engagement  
**Complexity**: Medium

```
GET /api/v1/notifications/
  - Get user notifications
  - Filter by type, read/unread
  - Pagination support

PATCH /api/v1/notifications/{notification_id}/read
  - Mark notification as read

DELETE /api/v1/notifications/{notification_id}
  - Delete notification

PATCH /api/v1/notifications/read-all
  - Mark all as read

Notification Types:
  - Comment replies
  - Vote milestones (article reached X votes)
  - New articles in favorite categories
  - Mentions in comments
```

**Database Addition:**
```sql
CREATE TABLE notifications (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  type VARCHAR(50),
  title VARCHAR(255),
  message TEXT,
  link VARCHAR(500),
  is_read BOOLEAN DEFAULT false,
  created_at TIMESTAMP
);
```

---

#### **G. User Statistics (Complete Implementation)** 🔥
**Value**: Medium - User engagement  
**Complexity**: Low-Medium

```
GET /api/v1/users/me/stats
  - Complete the placeholder endpoint
  
Statistics to Include:
  - total_articles_read: integer
  - total_votes_cast: integer
  - total_comments: integer
  - karma_score: integer (votes received on comments)
  - account_age_days: integer
  - top_categories: array of categories
  - reading_streak: integer (days)
  - articles_read_this_week: integer
```

---

#### **H. Social Features** 🔥
**Value**: Medium-High - Community building  
**Complexity**: Medium-High

```
# User profiles (public view)
GET /api/v1/users/{username}
  - Get public user profile
  - Include public stats, recent comments
  
# Following system
POST /api/v1/users/{username}/follow
  - Follow a user

DELETE /api/v1/users/{username}/follow
  - Unfollow user

GET /api/v1/users/me/following
  - Get users you follow

GET /api/v1/users/me/followers
  - Get your followers

GET /api/v1/feed/following
  - Get feed from followed users' activity
```

---

### Priority 3: Advanced Features (Nice-to-Have)

#### **I. Article Collections/Lists** 
**Value**: Medium  
**Complexity**: Medium

```
POST /api/v1/collections/
  - Create article collection (e.g., "Articles to Read", "Research")

GET /api/v1/collections/
  - Get user's collections

POST /api/v1/collections/{collection_id}/articles/{article_id}
  - Add article to collection

DELETE /api/v1/collections/{collection_id}/articles/{article_id}
  - Remove from collection

PATCH /api/v1/collections/{collection_id}
  - Update collection (name, description, privacy)

GET /api/v1/collections/{collection_id}/articles
  - Get articles in collection
```

---

#### **J. Search Enhancements**
**Value**: Medium  
**Complexity**: Medium

```
GET /api/v1/search/
  - Unified search (articles, comments, users)
  - Advanced filters
  - Search history

GET /api/v1/articles/related/{article_id}
  - Get related articles (by tags, category, keywords)

GET /api/v1/articles/recommended
  - Personalized recommendations based on:
    - Reading history
    - Voting patterns
    - Favorite categories
```

---

#### **K. Comment Voting**
**Value**: Medium  
**Complexity**: Low

```
POST /api/v1/comments/{comment_id}/vote
  - Vote on comments (upvote/downvote)

DELETE /api/v1/comments/{comment_id}/vote
  - Remove vote from comment

GET /api/v1/comments/{comment_id}/votes
  - Get comment vote stats
```

---

#### **L. Report/Moderation**
**Value**: Medium (Important for community)  
**Complexity**: Medium

```
POST /api/v1/reports/
  - Report article, comment, or user
  - Specify reason

# Admin endpoints
GET /api/v1/admin/reports/
  - Get pending reports

PATCH /api/v1/admin/reports/{report_id}
  - Resolve report (approve/reject)

POST /api/v1/admin/users/{user_id}/ban
  - Ban user

DELETE /api/v1/admin/comments/{comment_id}
  - Delete comment (moderation)
```

---

#### **M. Email Verification & Password Reset**
**Value**: High (Security)  
**Complexity**: Medium

```
POST /api/v1/auth/verify-email
  - Send verification email

GET /api/v1/auth/verify/{token}
  - Verify email with token

POST /api/v1/auth/forgot-password
  - Request password reset

POST /api/v1/auth/reset-password
  - Reset password with token

POST /api/v1/auth/change-password
  - Change password (authenticated)
```

---

#### **N. Analytics & Insights**
**Value**: Medium  
**Complexity**: Medium-High

```
GET /api/v1/articles/top
  - Top articles by votes, comments, views
  - Time range filters

GET /api/v1/stats/global
  - Global platform statistics
  - Total articles, users, comments

GET /api/v1/users/me/insights
  - Personal reading insights
  - Reading patterns, favorite topics
  - Best times to read
```

---

## Implementation Priority Ranking

### **Phase 1: Must-Have for MVP+** (1-2 weeks)
1. ✅ ~~User Profile CRUD~~ (Complete!)
2. 🔥 **Bookmarks/Saved Articles** (Critical for news apps)
3. 🔥 **User Activity History** (Reading history, votes, comments)
4. 🔥 **User Preferences** (Theme, categories, settings)
5. 🔥 **Complete User Stats** (Finish the 501 endpoint)

### **Phase 2: Enhanced Experience** (2-3 weeks)
6. 🔥 **RSS Source Management** (Public + subscriptions)
7. 🔥 **Notifications System** (Comment replies, mentions)
8. 🔥 **Article View Tracking** (Trending, analytics)
9. **Email Verification** (Security)

### **Phase 3: Community & Engagement** (3-4 weeks)
10. **Social Features** (Follow users, public profiles)
11. **Comment Voting** (Upvote/downvote comments)
12. **Search Enhancements** (Related articles, recommendations)
13. **Collections/Lists** (Organize saved articles)

### **Phase 4: Moderation & Scale** (4+ weeks)
14. **Report System** (User reports, moderation)
15. **Admin Dashboard** (Moderation tools)
16. **Analytics & Insights** (Platform and personal analytics)

---

## Immediate Recommendations (Next Steps)

### **Option A: Complete Core Features** ✅ Recommended
Focus on completing the user experience loop:
1. **Bookmarks** (2-3 days) - Essential for any news reader
2. **User History** (2 days) - Reading activity tracking
3. **User Preferences** (1-2 days) - Settings and customization
4. **Complete Stats Endpoint** (1 day) - Finish what's started

**Total Time**: ~1 week  
**Value**: Very High - Makes app truly usable

### **Option B: Focus on Content Discovery** 
Improve how users find content:
1. **RSS Source Management** (3-4 days) - See available sources
2. **Article View Tracking** (2 days) - Trending articles
3. **Search Enhancements** (3 days) - Better discovery

**Total Time**: ~1.5 weeks  
**Value**: High - Better content discovery

### **Option C: Build Community Features**
Enhance social aspects:
1. **Notifications** (4-5 days) - Keep users engaged
2. **Social Features** (5-7 days) - Follow users
3. **Comment Voting** (2 days) - Better discussions

**Total Time**: ~2 weeks  
**Value**: Medium-High - Community building

---

## Technical Considerations

### **Database Schema Additions Needed**

For recommended Phase 1 features:

```sql
-- Bookmarks
CREATE TABLE bookmarks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
  collection VARCHAR(100),
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, article_id)
);
CREATE INDEX idx_bookmarks_user_id ON bookmarks(user_id);
CREATE INDEX idx_bookmarks_article_id ON bookmarks(article_id);

-- Reading History
CREATE TABLE reading_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
  viewed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  duration_seconds INTEGER,
  scroll_percentage DECIMAL(5,2),
  UNIQUE(user_id, article_id, viewed_at)
);
CREATE INDEX idx_history_user_id ON reading_history(user_id);
CREATE INDEX idx_history_viewed_at ON reading_history(viewed_at);

-- User Preferences
CREATE TABLE user_preferences (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  favorite_categories JSONB DEFAULT '[]'::jsonb,
  theme VARCHAR(20) DEFAULT 'auto',
  language VARCHAR(10) DEFAULT 'en',
  notifications_enabled BOOLEAN DEFAULT true,
  email_digest VARCHAR(20) DEFAULT 'daily',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## API Design Consistency

All new endpoints should follow existing patterns:

### **Response Format**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 25,
  "has_more": true
}
```

### **Error Format**
```json
{
  "error": "error_code",
  "message": "Human-readable message",
  "details": {...}
}
```

### **Authentication**
- Required: `Authorization: Bearer <token>`
- Optional: Use `get_current_user_optional`
- Admin: Check `is_superuser` flag

---

## Conclusion

**Current State**: ✅ Strong MVP with core features (Articles, Comments, Voting, User Profile)

**Recommended Next Step**: **Implement Bookmarks/Saved Articles + User Activity** (Phase 1)
- These are table-stakes features for any news aggregator
- Relatively quick to implement (~1 week)
- High user value and engagement

**Long-term**: Build out community features (notifications, social, moderation) to differentiate from basic RSS readers.

---

**Questions to Consider:**
1. Is this a personal project or targeting users?
2. What's the priority: more features or polish existing ones?
3. Mobile app planned? (affects notification requirements)
4. Open to the public or private use?

Your answers will help prioritize the roadmap! 🚀
