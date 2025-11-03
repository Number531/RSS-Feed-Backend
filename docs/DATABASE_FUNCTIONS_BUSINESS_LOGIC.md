# RSS Feed Backend - Database Functions & Business Logic

## 📋 Table of Contents

1. [Overview](#overview)
2. [Service Layer Architecture](#service-layer-architecture)
3. [Core Services](#core-services)
4. [Business Rules](#business-rules)
5. [Background Jobs](#background-jobs)
6. [Cache Strategy](#cache-strategy)
7. [API Flow Examples](#api-flow-examples)

---

## Overview

**Architecture:** Layered Service-Oriented Architecture  
**Pattern:** Repository Pattern + Service Layer  
**Database Access:** Async SQLAlchemy + Supabase PostgreSQL

### Architectural Layers

```
┌─────────────────────────────────────┐
│         API Endpoints               │  FastAPI Routes
│  (app/api/v1/endpoints/)           │
└──────────────┬──────────────────────┘
               │ HTTP Requests
               ▼
┌─────────────────────────────────────┐
│       Service Layer                 │  Business Logic
│  (app/services/)                   │  Validation, Orchestration
└──────────────┬──────────────────────┘
               │ Domain Operations
               ▼
┌─────────────────────────────────────┐
│     Repository Layer                │  Data Access
│  (app/repositories/)               │  SQL Queries, ORM
└──────────────┬──────────────────────┘
               │ SQL/ORM
               ▼
┌─────────────────────────────────────┐
│    Database (Supabase/PostgreSQL)  │  Data Storage
└─────────────────────────────────────┘
```

---

## Service Layer Architecture

### Base Service (`BaseService`)

All services inherit from `BaseService` which provides:

```python
class BaseService:
    """Base service with common functionality."""
    
    # Logging
    def log_operation(self, operation: str, **kwargs)
    def log_error(self, operation: str, error: Exception, **kwargs)
    
    # Validation
    def validate_pagination(self, skip: int, limit: int, max_limit: int = 100)
    def validate_uuid(self, uuid_str: str) -> UUID
    
    # Pagination
    def create_pagination_metadata(
        self, total: int, skip: int, limit: int, returned_count: int
    ) -> dict
```

### Service Responsibilities

| Layer | Responsibility | Examples |
|-------|---------------|----------|
| **Service** | Business logic, validation, orchestration | Vote rules, comment threading, notification triggers |
| **Repository** | Data access, queries, transactions | CRUD operations, complex JOINs, aggregations |
| **Model** | Data structure, relationships | SQLAlchemy models, constraints |

---

## Core Services

### 1. **ArticleService** 📰

**File:** `app/services/article_service.py`

**Purpose:** Article feed retrieval, search, and filtering

#### Key Methods

##### `get_articles_feed()`
```python
async def get_articles_feed(
    category: Optional[str] = None,
    sort_by: str = "hot",
    time_range: Optional[str] = None,
    page: int = 1,
    page_size: int = 25,
    user_id: Optional[UUID] = None
) -> Tuple[List[Article], dict]
```

**Business Logic:**
1. **Validate Parameters**
   - `sort_by`: Must be "hot", "new", or "top"
   - `category`: Must be valid category (general, politics, us, world, science)
   - `time_range`: Must be hour, day, week, month, year, or all
   - `page_size`: Max 100 items

2. **Sort Algorithms**
   - **Hot:** Combines vote_score + recency (trending_score)
   - **New:** Most recent first (created_at DESC)
   - **Top:** Highest vote_score (all-time or time-range)

3. **Return Data**
   - Articles list with pagination
   - Includes user's vote status if user_id provided
   - Metadata: total count, page info, filters applied

**Example Flow:**
```
GET /api/v1/articles?sort_by=hot&time_range=day&page=1
    ↓
ArticleService.get_articles_feed()
    ↓
Validate: sort_by, time_range, pagination
    ↓
ArticleRepository.get_articles_feed()
    ↓
SQL: SELECT with WHERE, ORDER BY, LIMIT/OFFSET
    ↓
Return: (articles, pagination_metadata)
```

---

### 2. **VoteService** 👍👎

**File:** `app/services/vote_service.py`

**Purpose:** Reddit-style voting system with upvotes/downvotes

#### Key Methods

##### `cast_vote()`
```python
async def cast_vote(
    user_id: UUID,
    article_id: UUID,
    vote_value: int  # -1, 0, or 1
) -> Optional[Vote]
```

**Business Rules:**

1. **Vote Values**
   - `1` = Upvote
   - `-1` = Downvote
   - `0` = Remove vote

2. **Vote States & Transitions**
   ```
   No Vote → Upvote   [+1]
   No Vote → Downvote [-1]
   Upvote → Downvote  [-2 delta]
   Downvote → Upvote  [+2 delta]
   Upvote → No Vote   [-1]
   Downvote → No Vote [+1]
   ```

3. **Database Updates (Atomic)**
   - **Create Vote:** INSERT vote, UPDATE article.vote_score (+1 or -1), vote_count (+1)
   - **Change Vote:** UPDATE vote.vote_value, UPDATE article.vote_score (delta), no change to vote_count
   - **Remove Vote:** DELETE vote, UPDATE article.vote_score (-1 or +1), vote_count (-1)

4. **Constraints Enforced**
   - One vote per user per article (unique constraint)
   - Either article_id OR comment_id (check constraint)
   - Article/comment must exist (foreign key + validation)

**Example Flow:**
```
POST /api/v1/votes {"article_id": "...", "vote_value": 1}
    ↓
VoteService.cast_vote(user_id, article_id, 1)
    ↓
Check existing vote for user+article
    ↓
IF no existing vote:
    - Create vote record (vote_value=1)
    - Update article: vote_score += 1, vote_count += 1
    - Trigger notification (future: notify article author)
    ↓
ELSE IF existing vote:
    - Calculate delta (new_value - old_value)
    - Update vote record
    - Update article: vote_score += delta
    ↓
Return: Vote object
```

---

### 3. **CommentService** 💬

**File:** `app/services/comment_service.py`

**Purpose:** Threaded comments with soft deletes

#### Key Methods

##### `create_comment()`
```python
async def create_comment(
    user_id: UUID,
    article_id: UUID,
    content: str,
    parent_comment_id: Optional[UUID] = None
) -> Comment
```

**Business Rules:**

1. **Content Validation**
   - Must not be empty
   - Max length: 10,000 characters
   - No HTML sanitization (done at API layer)

2. **Threading Rules**
   - Top-level comments: `parent_comment_id = NULL`, `depth = 0`
   - Replies: `parent_comment_id = parent.id`, `depth = parent.depth + 1`
   - Max depth: Unlimited (but UI typically limits to 10)

3. **Forbidden Actions**
   - Cannot reply to deleted comments
   - Parent comment must belong to same article

4. **Automatic Updates**
   - Article: `comment_count += 1`
   - Parent comment (if reply): `reply_count += 1`
   - Trigger notification: If replying to another user's comment

**Threading Example:**
```
Article "Breaking News"
├─ Comment A (id: aaa, depth: 0, parent: NULL)
│  ├─ Comment B (id: bbb, depth: 1, parent: aaa)
│  │  └─ Comment C (id: ccc, depth: 2, parent: bbb)
│  └─ Comment D (id: ddd, depth: 1, parent: aaa)
└─ Comment E (id: eee, depth: 0, parent: NULL)
```

##### `delete_comment()` (Soft Delete)
```python
async def delete_comment(
    comment_id: UUID,
    user_id: UUID
) -> Comment
```

**Soft Delete Behavior:**
- Sets `is_deleted = True`, `deleted_at = NOW()`
- Content replaced with "[deleted]"
- Preserves thread structure (replies still visible)
- User can only delete own comments
- Admins can delete any comment

**Example Flow:**
```
POST /api/v1/comments {"article_id": "...", "content": "Great article!", "parent_comment_id": null}
    ↓
CommentService.create_comment(...)
    ↓
Validate: content length, article exists
    ↓
IF parent_comment_id:
    - Verify parent exists & not deleted
    - Calculate depth = parent.depth + 1
    ↓
ELSE:
    - depth = 0
    ↓
Create comment record
Update article.comment_count += 1
IF parent: Update parent.reply_count += 1
    ↓
IF parent AND parent.user_id != user_id:
    - NotificationService.create_reply_notification()
    ↓
Return: Comment object
```

---

### 4. **BookmarkService** 🔖

**File:** `app/services/bookmark_service.py`

**Purpose:** Save articles with optional collections

#### Key Methods

##### `create_bookmark()`
```python
async def create_bookmark(
    user_id: UUID,
    article_id: UUID,
    collection: Optional[str] = None,
    notes: Optional[str] = None
) -> Bookmark
```

**Business Rules:**

1. **Uniqueness:** One bookmark per user per article
   - Attempting to re-bookmark returns existing bookmark
   - Can update collection/notes

2. **Collections**
   - Optional grouping mechanism
   - Examples: "Read Later", "Favorites", "Research"
   - User-defined, no predefined list
   - Can be NULL (uncategorized)

3. **Notes**
   - Optional personal notes on article
   - Max 5,000 characters
   - Private to user

**Example Flow:**
```
POST /api/v1/bookmarks {"article_id": "...", "collection": "Read Later"}
    ↓
BookmarkService.create_bookmark(...)
    ↓
Check if bookmark already exists (user + article)
    ↓
IF exists:
    - Return existing bookmark
    ↓
ELSE:
    - Validate article exists
    - Create bookmark record
    - Return new bookmark
```

---

### 5. **NotificationService** 🔔

**File:** `app/services/notification_service.py`

**Purpose:** User interaction notifications

#### Key Methods

##### `create_reply_notification()`
```python
@staticmethod
async def create_reply_notification(
    db: AsyncSession,
    recipient_id: UUID,
    actor_id: UUID,
    comment_id: UUID,
    article_id: UUID
)
```

**Notification Types:**

| Type | Trigger | Example |
|------|---------|---------|
| `reply` | Someone replies to user's comment | "Alice replied to your comment on 'Breaking News'" |
| `vote` | Someone votes on user's content | "Bob upvoted your comment" *(future)* |
| `mention` | User mentioned in comment | "@charlie what do you think?" *(future)* |

**Business Rules:**

1. **Suppression Rules**
   - Don't notify if actor = recipient (user's own action)
   - Check user's notification preferences
   - Don't notify if recipient has disabled that notification type

2. **Notification Delivery**
   - Created in database immediately
   - Mark as unread (`is_read = false`)
   - Real-time push: WebSocket/SSE *(future)*
   - Email digest: Batch notifications *(future)*

3. **Notification Lifecycle**
   ```
   Created (is_read=false) → Read (is_read=true) → Deleted (after 30 days)
   ```

**Example Flow:**
```
User A replies to User B's comment
    ↓
CommentService.create_comment(...)
    ↓
IF parent_comment.user_id != current_user_id:
    ↓
    NotificationService.create_reply_notification(
        recipient_id = parent_comment.user_id,
        actor_id = current_user_id,
        comment_id = new_comment.id,
        article_id = article.id
    )
    ↓
    Check recipient's notification preferences
        ↓
        IF reply_notifications = true:
            - Create notification record
            - (Future: Send WebSocket event)
            - (Future: Queue email if enabled)
```

---

### 6. **AnalyticsService** 📊

**File:** `app/services/analytics_service.py`

**Purpose:** Fact-check analytics with caching

#### Key Methods

##### `get_aggregate_statistics()`
```python
@cache_result(ttl=300)  # 5 minutes
async def get_aggregate_statistics(
    include_lifetime: bool = True,
    include_trends: bool = True
) -> dict
```

**Business Logic:**

1. **Lifetime Metrics**
   - Total articles fact-checked (all-time)
   - Total sources monitored
   - Total claims verified
   - Average credibility score

2. **Monthly Trends**
   - This month vs. last month comparison
   - Volume change percentage
   - Credibility score change

3. **Milestones**
   ```python
   milestones = [
       "1000_articles": achieved if total >= 1000,
       "5000_claims": achieved if claims >= 5000,
       "50_sources": achieved if sources >= 50
   ]
   ```

**Caching Strategy:**
- Cache key: `analytics:stats:{include_lifetime}:{include_trends}`
- TTL: 5 minutes (300 seconds)
- Cached in Redis
- Auto-invalidated every 15 minutes by Celery task

---

### 7. **FactCheckService** ✅

**File:** `app/services/fact_check_service.py`

**Purpose:** AI-powered article fact-checking

#### Key Methods

##### `submit_fact_check_job()`
```python
async def submit_fact_check_job(
    article_id: UUID,
    mode: str = "summary"
) -> dict
```

**Validation Modes:**

| Mode | Description | Speed | Cost |
|------|-------------|-------|------|
| `summary` | Quick validation | Fast (10-30s) | Low |
| `standard` | Balanced approach | Medium (30-60s) | Medium |
| `thorough` | Deep verification | Slow (60-120s) | High |

**Business Flow:**

1. **Job Submission**
   ```
   POST /api/v1/fact-check {"article_id": "...", "mode": "summary"}
       ↓
   Check if already fact-checked
       ↓
   IF exists AND recent (< 24h):
       - Return cached results
       ↓
   ELSE:
       - Submit job to external Fact-Check API
       - Generate unique job_id
       - Store job_id in database
       - Return job status URL
   ```

2. **Job Polling**
   ```
   GET /api/v1/fact-check/{job_id}
       ↓
   Poll external API every 5 seconds
   Max attempts: 60 (5 minutes total)
       ↓
   IF completed:
       - Parse results
       - Create ArticleFactCheck record
       - Update article denormalized fields
       - Update source credibility scores
       - Return results
       ↓
   IF still processing:
       - Return status: "processing"
       ↓
   IF timeout:
       - Return status: "timeout"
   ```

3. **Result Storage**
   ```python
   ArticleFactCheck:
       verdict: "TRUE" | "FALSE" | "MISLEADING" | ...
       credibility_score: 0-100
       confidence: 0.00-1.00
       claims_analyzed: integer
       validation_results: JSONB (full API response)
       processing_time_seconds: integer
   ```

4. **Denormalized Updates**
   ```
   Article table updates:
       fact_check_score = credibility_score
       fact_check_verdict = verdict
       fact_checked_at = NOW()
   
   SourceCredibilityScore updates:
       average_score = recalculated avg
       verdict counts updated
   ```

---

## Business Rules

### Vote Rules

#### Constraints
- ✅ User can only vote once per article/comment
- ✅ Can change vote (upvote ↔ downvote)
- ✅ Can remove vote (set to 0)
- ❌ Cannot vote on own content *(not enforced yet)*
- ❌ Cannot vote on deleted content *(enforced for comments)*

#### Score Calculation
```python
# Article/Comment vote_score
vote_score = SUM(vote_value) for all votes
  # Sum of all +1 and -1 values

# Example:
# 10 upvotes (+10), 3 downvotes (-3) = vote_score: 7
# vote_count = 13 (total votes regardless of direction)
```

#### Trending Algorithm
```python
# Simplified trending score
trending_score = (vote_score / hours_since_creation) * decay_factor
  # Higher score = more trending
  # Recent articles favored (decay over time)
```

---

### Comment Rules

#### Threading
- **Max Depth:** Unlimited (UI typically caps at 10 levels)
- **Depth Calculation:** `parent.depth + 1`
- **Sorting:** Top-level by vote_score, replies by created_at

#### Soft Delete
```python
# When deleted:
is_deleted = True
deleted_at = NOW()
content = "[deleted]"  # Content replaced, not removed

# Child comments still visible:
"[deleted comment]"
└─ "This is a reply to the deleted comment" (still visible)
```

#### Edit Rules
- ❌ **Not implemented yet** (planned for future)
- Will set `is_edited = True` when content changes
- Edit history not tracked (single version)

---

### Bookmark Rules

#### Uniqueness
- **Constraint:** `UNIQUE(user_id, article_id)`
- **Behavior:** Attempting to re-bookmark returns existing

#### Collections
```python
# User-defined collections
collection: Optional[str]
  - "Read Later"
  - "Favorites"
  - "Research - Climate"
  - NULL (no collection)

# Fetching by collection
GET /api/v1/bookmarks?collection=Favorites
```

---

### Notification Rules

#### Triggering Conditions

| Event | Condition | Notification Created |
|-------|-----------|----------------------|
| Reply to comment | `parent.user_id != current_user_id` | ✅ Reply notification |
| Vote on article | *(future)* | Vote notification |
| Vote on comment | *(future)* | Vote notification |
| Mention in comment | *(future)* `@username` detected | Mention notification |

#### User Preferences
```python
# Notification preferences table
vote_notifications: bool = True
reply_notifications: bool = True
mention_notifications: bool = True
email_notifications: bool = False  # Future
```

**Suppression Logic:**
```python
if not recipient.notification_preferences.reply_notifications:
    return  # Don't create notification

if actor_id == recipient_id:
    return  # Don't notify user about own actions
```

---

### Reading History Rules

#### Privacy Controls
```python
# User reading preferences
tracking_enabled: bool = True  # Master switch
analytics_opt_in: bool = True  # Share for analytics
auto_cleanup_enabled: bool = False  # Auto-delete old entries
retention_days: int = 365  # Keep for 1 year
exclude_categories: List[str] = []  # Don't track certain categories
```

#### Tracking Behavior
```python
# When user views article
IF user.reading_preferences.tracking_enabled:
    IF article.category NOT IN user.reading_preferences.exclude_categories:
        - Create ReadingHistory record
        - Log: viewed_at, duration_seconds, scroll_percentage
```

---

## Background Jobs

### Celery Tasks

**File:** `app/tasks/`

#### 1. **RSS Feed Fetching** (`rss_tasks.py`)

##### `fetch_all_feeds` (Every 15 minutes)
```python
@celery_app.task(name="app.tasks.rss_tasks.fetch_all_feeds")
def fetch_all_feeds():
    """
    Master task that spawns individual feed fetch tasks.
    """
    1. Get all active RSS sources (is_active=True)
    2. Create parallel tasks (max 5 concurrent)
    3. Queue remaining sources with 1-minute delay
    4. Return dispatch status
```

**Flow:**
```
Celery Beat (every 15 min)
    ↓
fetch_all_feeds()
    ↓
Get active sources (N sources)
    ↓
Spawn group of tasks:
    - fetch_single_feed(source_1) ┐
    - fetch_single_feed(source_2) ├─ Parallel (max 5)
    - fetch_single_feed(source_3) ┘
    ↓
Process feed entries:
    - Parse RSS XML
    - Extract article data
    - Hash URL (SHA-256)
    - Check for duplicates (url_hash)
    - Create new articles
    - Skip duplicates
    ↓
Update source metrics:
    - last_fetched = NOW()
    - last_successful_fetch = NOW()
    - fetch_success_count += 1
    - consecutive_failures = 0
```

##### `fetch_single_feed` (Per-source task)
```python
@celery_app.task(name="app.tasks.rss_tasks.fetch_single_feed", max_retries=3)
def fetch_single_feed(source_id: str):
    """
    Fetch and process a single RSS feed.
    """
    1. Get source from database
    2. Fetch RSS feed (with HTTP caching)
    3. Parse entries with feedparser
    4. For each entry:
        a. Parse and validate
        b. Hash URL for deduplication
        c. Check if exists (url_hash lookup)
        d. Create article if new
        e. Skip if duplicate
    5. Update source health metrics
    6. Return results (created, skipped counts)
```

**Error Handling:**
- **Retry Logic:** Exponential backoff (1s, 2s, 4s)
- **Max Retries:** 3 attempts
- **Failure Tracking:** `consecutive_failures` counter
- **Health Status:** Source marked unhealthy after 5 consecutive failures

---

#### 2. **Analytics Cache Refresh** (`analytics_tasks.py`)

##### `refresh_materialized_views` (Every 15 minutes)
```python
@shared_task(name="refresh_analytics_materialized_views")
def refresh_materialized_views():
    """
    Refresh all materialized views for analytics.
    """
    views = [
        "analytics_daily_summary",
        "analytics_source_reliability",
        "analytics_category_summary"
    ]
    
    for view_name in views:
        db.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}")
    
    db.commit()
```

**Why CONCURRENTLY?**
- Doesn't lock the view for reads
- Users can still query while refreshing
- Takes longer but non-blocking

##### `warm_analytics_cache` (Every 16 minutes, after view refresh)
```python
@shared_task(name="warm_analytics_cache")
def warm_analytics_cache():
    """
    Pre-populate Redis cache with common queries.
    """
    # Warm aggregate stats
    service.get_aggregate_statistics()
    
    # Warm category analytics
    for days in [7, 30]:
        service.get_category_analytics(days=days)
    
    # Warm verdict details
    service.get_verdict_details(days=30)
```

**Purpose:** Ensure first user request after cache expiry is fast

---

#### 3. **Cache Invalidation** (`cache_tasks.py`)

##### `clear_analytics_cache` (Every 15 minutes)
```python
@shared_task(name="clear_analytics_cache")
def clear_analytics_cache():
    """
    Clear all analytics-related cache keys.
    """
    pattern = "analytics:*"
    keys = redis.keys(pattern)
    
    if keys:
        redis.delete(*keys)
        return {"cleared": len(keys)}
```

**Cache Lifecycle:**
```
T=0:00  → Cache empty
T=0:01  → User request → Cache MISS → Query DB → Cache SET (TTL: 5 min)
T=0:02  → User request → Cache HIT → Return cached data
T=5:00  → TTL expires → Cache empty
T=15:00 → warm_analytics_cache() → Pre-populate cache
```

---

## Cache Strategy

### Redis Caching

**File:** `app/utils/cache.py`

#### Cache Decorator
```python
@cache_result(ttl=300)  # 5 minutes
async def get_analytics_data(...):
    # Expensive database query
    return results
```

**How It Works:**
1. **Cache Key Generation:**
   ```python
   key = f"analytics:{function_name}:{hash(args)}"
   # Example: "analytics:get_category_analytics:30:5:credibility"
   ```

2. **Cache Lookup:**
   ```python
   cached = redis.get(key)
   if cached:
       return json.loads(cached)  # Cache HIT
   ```

3. **Cache Miss:**
   ```python
   result = await original_function(*args, **kwargs)
   redis.setex(key, ttl, json.dumps(result))
   return result
   ```

#### Cache Patterns

| Endpoint | Cache Key | TTL | Invalidation |
|----------|-----------|-----|--------------|
| Aggregate Stats | `analytics:stats:*` | 5 min | Every 15 min |
| Category Analytics | `analytics:categories:*` | 5 min | Every 15 min |
| Source Reliability | `analytics:sources:*` | 5 min | Every 15 min |
| Verdict Details | `analytics:verdicts:*` | 5 min | Every 15 min |

#### Cache Warming Strategy
```
15:00 → Clear old cache
15:01 → Refresh materialized views
15:02 → Warm cache with common queries
15:03 → User requests served from fresh cache
```

---

## API Flow Examples

### Example 1: Create Comment with Reply Notification

**Request:**
```http
POST /api/v1/comments
Authorization: Bearer <token>
Content-Type: application/json

{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "parent_comment_id": "660e8400-e29b-41d4-a716-446655440001",
  "content": "Great point! I totally agree."
}
```

**Flow:**
```
1. API Endpoint: POST /api/v1/comments
   ↓
2. Authentication Middleware
   - Decode JWT → user_id
   ↓
3. CommentService.create_comment(
     user_id="current-user-uuid",
     article_id="550e8400-...",
     parent_comment_id="660e8400-...",
     content="Great point! I totally agree."
   )
   ↓
4. Validations:
   - Content not empty ✓
   - Content length <= 10,000 ✓
   - Article exists ✓
   - Parent comment exists ✓
   - Parent belongs to same article ✓
   - Parent not deleted ✓
   ↓
5. Calculate depth:
   - parent.depth = 1
   - new comment depth = 2
   ↓
6. Create Comment Record:
   - INSERT INTO comments (id, user_id, article_id, parent_comment_id, content, depth, ...)
   ↓
7. Update Counters:
   - UPDATE articles SET comment_count = comment_count + 1 WHERE id = article_id
   - UPDATE comments SET reply_count = reply_count + 1 WHERE id = parent_comment_id
   ↓
8. Check Notification:
   - IF parent.user_id != current_user_id:
     ↓
     NotificationService.create_reply_notification(
       recipient_id=parent.user_id,
       actor_id=current_user_id,
       comment_id=new_comment.id,
       article_id=article_id
     )
     ↓
     Check user preferences:
     - user.notification_preferences.reply_notifications = True ✓
     ↓
     CREATE notification:
       - type: "reply"
       - title: "New reply to your comment"
       - message: "Alice replied: 'Great point! I totally agree.'"
       - is_read: False
   ↓
9. Commit Transaction
   ↓
10. Return Response:
    {
      "id": "new-comment-uuid",
      "user_id": "current-user-uuid",
      "article_id": "550e8400-...",
      "parent_comment_id": "660e8400-...",
      "content": "Great point! I totally agree.",
      "depth": 2,
      "vote_score": 0,
      "reply_count": 0,
      "created_at": "2025-11-03T04:30:00Z",
      ...
    }
```

---

### Example 2: Vote on Article with Score Update

**Request:**
```http
POST /api/v1/votes
Authorization: Bearer <token>
Content-Type: application/json

{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "vote_value": 1
}
```

**Flow:**
```
1. API Endpoint: POST /api/v1/votes
   ↓
2. Authentication → user_id
   ↓
3. VoteService.cast_vote(
     user_id="current-user-uuid",
     article_id="550e8400-...",
     vote_value=1
   )
   ↓
4. Validations:
   - vote_value in [-1, 0, 1] ✓
   - Article exists ✓
   ↓
5. Check Existing Vote:
   - SELECT * FROM votes WHERE user_id = ? AND article_id = ?
   - Result: existing_vote = None (no previous vote)
   ↓
6. Create New Vote:
   - INSERT INTO votes (id, user_id, article_id, vote_value, created_at)
     VALUES (new-uuid, user_id, article_id, 1, NOW())
   ↓
7. Update Article Counters (Atomic):
   - UPDATE articles 
     SET vote_score = vote_score + 1,
         vote_count = vote_count + 1
     WHERE id = article_id
   ↓
8. Update Trending Score:
   - Calculate new trending_score based on vote_score and recency
   - UPDATE articles SET trending_score = calculated_score WHERE id = article_id
   ↓
9. Commit Transaction
   ↓
10. Return Response:
    {
      "id": "vote-uuid",
      "user_id": "current-user-uuid",
      "article_id": "550e8400-...",
      "vote_value": 1,
      "created_at": "2025-11-03T04:35:00Z"
    }
```

**If User Changes Vote (Upvote → Downvote):**
```
5. Check Existing Vote:
   - existing_vote.vote_value = 1 (upvote)
   ↓
6. Calculate Delta:
   - new_value = -1
   - delta = -1 - 1 = -2
   ↓
7. Update Vote:
   - UPDATE votes SET vote_value = -1, updated_at = NOW() WHERE id = existing_vote.id
   ↓
8. Update Article (Delta Only):
   - UPDATE articles SET vote_score = vote_score + (-2) WHERE id = article_id
   - vote_count remains unchanged (13 votes total)
```

---

### Example 3: Fetch Articles Feed with Caching

**Request:**
```http
GET /api/v1/articles?sort_by=hot&time_range=day&page=1&page_size=25
Authorization: Bearer <token>
```

**Flow:**
```
1. API Endpoint: GET /api/v1/articles
   ↓
2. Parse Query Params:
   - sort_by = "hot"
   - time_range = "day"
   - page = 1
   - page_size = 25
   ↓
3. Authentication → user_id (optional for feed)
   ↓
4. ArticleService.get_articles_feed(
     category=None,
     sort_by="hot",
     time_range="day",
     page=1,
     page_size=25,
     user_id="current-user-uuid"
   )
   ↓
5. Validations:
   - sort_by in ["hot", "new", "top"] ✓
   - time_range in ["hour", "day", "week", ...] ✓
   - page_size <= 100 ✓
   ↓
6. ArticleRepository.get_articles_feed()
   ↓
7. Build SQL Query:
   SELECT a.*, 
          v.vote_value as user_vote,
          afc.credibility_score,
          afc.verdict
   FROM articles a
   LEFT JOIN votes v ON v.article_id = a.id AND v.user_id = 'user-uuid'
   LEFT JOIN article_fact_checks afc ON afc.article_id = a.id
   WHERE a.created_at >= NOW() - INTERVAL '1 day'
   ORDER BY a.trending_score DESC
   LIMIT 25 OFFSET 0
   ↓
8. Execute Query (using indexes):
   - idx_articles_created_at for date filter
   - idx_articles_trending_score for sorting
   ↓
9. Get Total Count:
   SELECT COUNT(*) FROM articles WHERE created_at >= NOW() - INTERVAL '1 day'
   ↓
10. Create Pagination Metadata:
    {
      "total": 250,
      "page": 1,
      "page_size": 25,
      "total_pages": 10,
      "has_next": true,
      "has_prev": false
    }
   ↓
11. Return Response:
    {
      "articles": [...], // 25 articles
      "metadata": {...},
      "filters": {
        "category": "all",
        "sort_by": "hot",
        "time_range": "day"
      }
    }
```

---

## Related Documentation

- [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) - Complete database structure
- [DATABASE_OPTIMIZATION.md](./DATABASE_OPTIMIZATION.md) - Performance optimization
- [ANALYTICS_API.md](./ANALYTICS_API.md) - Analytics API documentation
- [WARP.md](./WARP.md) - Development guide

---

**Last Updated:** November 3, 2025  
**Architecture:** Layered Service-Oriented Architecture  
**Services:** 9 core services + 3 background task modules
