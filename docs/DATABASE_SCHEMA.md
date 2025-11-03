# RSS Feed Backend - Supabase Database Schema

## 📋 Table of Contents

1. [Overview](#overview)
2. [Entity Relationship Diagram](#entity-relationship-diagram)
3. [Core Tables](#core-tables)
4. [Supporting Tables](#supporting-tables)
5. [Analytics Tables](#analytics-tables)
6. [Data Flow](#data-flow)
7. [Relationships](#relationships)
8. [Indexes & Performance](#indexes--performance)

---

## Overview

**Database:** PostgreSQL (via Supabase)  
**ORM:** SQLAlchemy (Async)  
**Total Tables:** 14 (11 core + 3 materialized views)  
**Architecture:** Layered (API → Service → Repository → Database)

### Design Principles
- **UUID Primary Keys** - For distributed systems and security
- **Soft Deletes** - Where appropriate (comments, notifications)
- **Denormalized Metrics** - For performance (vote counts, comment counts)
- **Cascading Deletes** - Data integrity with ON DELETE CASCADE
- **Timestamped Records** - All tables have created_at/updated_at
- **Indexed Foreign Keys** - All relationships are indexed

---

## Entity Relationship Diagram

```
┌──────────────┐
│    User      │
│ (users)      │
└──────┬───────┘
       │
       ├───────────────┬────────────────┬─────────────────┬──────────────┐
       │               │                │                 │              │
       ▼               ▼                ▼                 ▼              ▼
  ┌─────────┐    ┌─────────┐     ┌──────────┐    ┌──────────┐   ┌──────────┐
  │  Vote   │    │ Comment │     │ Bookmark │    │ Reading  │   │Notification│
  │ (votes) │    │(comments)│     │(bookmarks)│    │ History  │   │           │
  └────┬────┘    └────┬────┘     └────┬─────┘    └────┬─────┘   └──────────┘
       │              │               │              │
       └──────┬───────┴───────┬───────┴──────────────┘
              │               │
              ▼               ▼
        ┌──────────┐    ┌──────────┐
        │ Article  │    │ Comment  │
        │(articles)│    │(recursive)│
        └────┬─────┘    └──────────┘
             │
             ├───────────────┬──────────────────┐
             │               │                  │
             ▼               ▼                  ▼
      ┌───────────┐   ┌──────────────┐   ┌──────────┐
      │RSS Source │   │ArticleFact   │   │  Vote    │
      │(rss_sources)│  │    Check     │   │ (votes)  │
      └─────┬─────┘   │(article_fact_│   └──────────┘
            │         │   checks)    │
            ▼         └──────────────┘
      ┌───────────┐
      │  Source   │
      │Credibility│
      │  Score    │
      └───────────┘
```

---

## Core Tables

### 1. **users** 👤

**Purpose:** User authentication, profiles, and OAuth integration

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, Index | Primary key |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, Index | User email (login) |
| `username` | VARCHAR(50) | UNIQUE, NOT NULL, Index | Unique username |
| `hashed_password` | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| `full_name` | VARCHAR(255) | NULL | User's full name |
| `avatar_url` | VARCHAR(500) | NULL | Profile picture URL |
| `is_active` | BOOLEAN | NOT NULL, Default: true | Account status |
| `is_superuser` | BOOLEAN | NOT NULL, Default: false | Admin privileges |
| `is_verified` | BOOLEAN | NOT NULL, Default: false | Email verification |
| `oauth_provider` | VARCHAR(50) | NULL | OAuth provider name |
| `oauth_id` | VARCHAR(255) | NULL | OAuth provider user ID |
| `created_at` | TIMESTAMP | NOT NULL | Account creation time |
| `updated_at` | TIMESTAMP | NOT NULL | Last update time |
| `last_login_at` | TIMESTAMP | NULL | Last login timestamp |

**Relationships:**
- 1:N → `votes`
- 1:N → `comments`
- 1:N → `bookmarks`
- 1:N → `reading_history`
- 1:1 → `user_reading_preferences`
- 1:N → `notifications`
- 1:1 → `user_notification_preferences`
- 1:N → `user_feed_subscriptions`

**Indexes:**
- `idx_users_email` - Fast login lookups
- `idx_users_username` - Username uniqueness
- `idx_users_id` - Primary key index

---

### 2. **rss_sources** 📡

**Purpose:** RSS feed source configuration and health monitoring

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Primary key |
| `name` | VARCHAR(255) | NOT NULL | Feed display name |
| `url` | TEXT | UNIQUE, NOT NULL, Index | Feed URL |
| `source_name` | VARCHAR(100) | NOT NULL, Index | Publisher name (e.g., "CNN") |
| `category` | VARCHAR(50) | NOT NULL, Index | Content category |
| `is_active` | BOOLEAN | NOT NULL, Default: true, Index | Feed active status |
| `last_fetched` | TIMESTAMP | NULL | Last fetch attempt |
| `last_successful_fetch` | TIMESTAMP | NULL | Last successful fetch |
| `fetch_success_count` | INTEGER | NOT NULL, Default: 0 | Success counter |
| `fetch_failure_count` | INTEGER | NOT NULL, Default: 0 | Failure counter |
| `consecutive_failures` | INTEGER | NOT NULL, Default: 0 | Consecutive failures |
| `etag` | VARCHAR(255) | NULL | HTTP ETag for caching |
| `last_modified` | TIMESTAMP | NULL | HTTP Last-Modified header |
| `created_at` | TIMESTAMP | NOT NULL | Source added date |
| `updated_at` | TIMESTAMP | NOT NULL | Last update time |

**Relationships:**
- 1:N → `articles`
- 1:N → `source_credibility_scores`
- 1:N → `user_feed_subscriptions`

**Computed Properties:**
- `success_rate` - Percentage of successful fetches
- `is_healthy` - Success rate > 80% AND consecutive failures < 5

**Indexes:**
- `idx_rss_sources_url` - Feed URL uniqueness
- `idx_rss_sources_source_name` - Publisher filtering
- `idx_rss_sources_category` - Category filtering
- `idx_rss_sources_is_active` - Active feed queries

---

### 3. **articles** 📰

**Purpose:** Aggregated news articles from RSS feeds

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Primary key |
| `rss_source_id` | UUID | FK → rss_sources, NOT NULL, Index | Source reference |
| `title` | TEXT | NOT NULL | Article title |
| `url` | TEXT | NOT NULL | Original article URL |
| `url_hash` | VARCHAR(64) | UNIQUE, NOT NULL, Index | SHA-256 hash for deduplication |
| `description` | TEXT | NULL | Article summary |
| `content` | TEXT | NULL | Full article content |
| `author` | VARCHAR(255) | NULL | Author name |
| `published_date` | TIMESTAMP | NULL, Index | Original publish date |
| `thumbnail_url` | TEXT | NULL | Article image URL |
| `category` | VARCHAR(50) | NOT NULL, Index | Content category |
| `tags` | ARRAY(STRING) | NULL | Article tags |
| `vote_score` | INTEGER | NOT NULL, Default: 0, Index | Sum of vote values |
| `vote_count` | INTEGER | NOT NULL, Default: 0 | Total votes |
| `comment_count` | INTEGER | NOT NULL, Default: 0 | Total comments |
| `trending_score` | DECIMAL(10,4) | NOT NULL, Default: 0, Index | Trending algorithm score |
| `fact_check_score` | INTEGER | NULL, Index | Cached credibility score |
| `fact_check_verdict` | VARCHAR(50) | NULL, Index | Cached verdict |
| `fact_checked_at` | TIMESTAMP | NULL, Index | Fact-check timestamp |
| `search_vector` | TSVECTOR | NULL | Full-text search vector |
| `created_at` | TIMESTAMP | NOT NULL, Index | Article added date |
| `updated_at` | TIMESTAMP | NOT NULL | Last update time |

**Relationships:**
- N:1 → `rss_sources`
- 1:N → `votes`
- 1:N → `comments`
- 1:N → `bookmarks`
- 1:N → `reading_history`
- 1:1 → `article_fact_checks`

**Indexes:**
- `idx_articles_rss_source_id` - Source filtering
- `idx_articles_url_hash` - Deduplication
- `idx_articles_published_date` - Date sorting
- `idx_articles_category` - Category filtering
- `idx_articles_vote_score` - Popular sorting
- `idx_articles_trending_score` - Trending algorithm
- `idx_articles_fact_check_score` - Credibility filtering
- `idx_articles_fact_check_verdict` - Verdict filtering
- `idx_articles_fact_checked_at` - Recent fact-checks
- `idx_articles_created_at` - Date range queries ⭐ **NEW**
- `idx_articles_source_created` - Source + date composite ⭐ **NEW**
- `idx_articles_category_created` - Category + date composite ⭐ **NEW**

---

### 4. **article_fact_checks** ✅

**Purpose:** Detailed fact-check results from AI validation

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Primary key |
| `article_id` | UUID | FK → articles, UNIQUE, NOT NULL, Index | Article reference (1:1) |
| `verdict` | VARCHAR(50) | NOT NULL, Index | Overall verdict |
| `credibility_score` | INTEGER | NOT NULL, Index | Score 0-100 |
| `confidence` | DECIMAL(3,2) | NULL | AI confidence level |
| `summary` | TEXT | NOT NULL | Human-readable summary |
| `claims_analyzed` | INTEGER | NULL | Total claims found |
| `claims_validated` | INTEGER | NULL | Claims verified |
| `claims_true` | INTEGER | NULL | True claims count |
| `claims_false` | INTEGER | NULL | False claims count |
| `claims_misleading` | INTEGER | NULL | Misleading claims count |
| `claims_unverified` | INTEGER | NULL | Unverified claims count |
| `validation_results` | JSONB | NOT NULL | Full API response |
| `num_sources` | INTEGER | NULL | Evidence sources used |
| `source_consensus` | VARCHAR(20) | NULL | Source agreement level |
| `job_id` | VARCHAR(255) | UNIQUE, NOT NULL, Index | Async job ID |
| `validation_mode` | VARCHAR(20) | NULL | Validation mode used |
| `processing_time_seconds` | INTEGER | NULL | Processing duration |
| `api_costs` | JSONB | NULL | API usage costs |
| `fact_checked_at` | TIMESTAMP | NOT NULL, Index | Fact-check completion time |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |
| `updated_at` | TIMESTAMP | NOT NULL | Last update |

**Relationships:**
- 1:1 → `articles`

**Verdict Values:**
- `TRUE` - Factually accurate
- `FALSE` - Factually false
- `MOSTLY_TRUE` - Largely accurate
- `MOSTLY_FALSE` - Largely false
- `MIXED` - Contains both true and false
- `MISLEADING` - Technically true but misleading
- `UNVERIFIED` - Cannot be verified

**Indexes:**
- `idx_article_fact_checks_article_id` - Article lookup ⭐ **NEW**
- `idx_article_fact_checks_verdict` - Verdict filtering ⭐ **NEW**
- `idx_article_fact_checks_confidence` - Confidence queries ⭐ **NEW**
- `idx_article_fact_checks_job_id` - Job status lookup
- `idx_article_fact_checks_fact_checked_at` - Date sorting

---

### 5. **comments** 💬

**Purpose:** Threaded user comments on articles

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Primary key |
| `user_id` | UUID | FK → users, NOT NULL, Index | Comment author |
| `article_id` | UUID | FK → articles, NOT NULL, Index | Article reference |
| `parent_comment_id` | UUID | FK → comments, NULL, Index | Parent comment (threading) |
| `content` | TEXT | NOT NULL | Comment text |
| `is_edited` | BOOLEAN | NOT NULL, Default: false | Edit flag |
| `is_deleted` | BOOLEAN | NOT NULL, Default: false | Soft delete flag |
| `deleted_at` | TIMESTAMP | NULL | Soft delete timestamp |
| `vote_score` | INTEGER | NOT NULL, Default: 0 | Sum of vote values |
| `vote_count` | INTEGER | NOT NULL, Default: 0, Index | Total votes |
| `reply_count` | INTEGER | NOT NULL, Default: 0 | Direct replies |
| `depth` | INTEGER | NOT NULL, Default: 0 | Thread depth level |
| `created_at` | TIMESTAMP | NOT NULL | Comment creation |
| `updated_at` | TIMESTAMP | NOT NULL | Last update |

**Relationships:**
- N:1 → `users`
- N:1 → `articles`
- N:1 → `comments` (parent - self-referential)
- 1:N → `comments` (replies - self-referential)
- 1:N → `votes`

**Indexes:**
- `idx_comments_user_id` - User's comments
- `idx_comments_article_id` - Article's comments
- `idx_comments_parent_comment_id` - Thread traversal
- `idx_comments_vote_count` - Popular comments

---

### 6. **votes** 👍👎

**Purpose:** Reddit-style upvote/downvote system

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Primary key |
| `user_id` | UUID | FK → users, NOT NULL, Index | Voter |
| `article_id` | UUID | FK → articles, NULL, Index | Article vote (XOR with comment_id) |
| `comment_id` | UUID | FK → comments, NULL, Index | Comment vote (XOR with article_id) |
| `vote_value` | SMALLINT | NOT NULL | 1 (upvote) or -1 (downvote) |
| `created_at` | TIMESTAMP | NOT NULL | Vote timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update |

**Relationships:**
- N:1 → `users`
- N:1 → `articles` (polymorphic)
- N:1 → `comments` (polymorphic)

**Constraints:**
- `vote_target_check` - Either article_id OR comment_id must be set
- `unique_user_article_vote` - One vote per user per article
- `unique_user_comment_vote` - One vote per user per comment

**Indexes:**
- `idx_votes_user_id` - User's votes
- `idx_votes_article_id` - Article votes
- `idx_votes_comment_id` - Comment votes

---

## Supporting Tables

### 7. **bookmarks** 🔖

**Purpose:** User-saved articles with optional collections

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Primary key |
| `user_id` | UUID | FK → users, NOT NULL | Bookmark owner |
| `article_id` | UUID | FK → articles, NOT NULL | Bookmarked article |
| `collection` | VARCHAR(100) | NULL | Collection name |
| `notes` | TEXT | NULL | User notes |
| `created_at` | TIMESTAMP | NOT NULL | Bookmark timestamp |

**Relationships:**
- N:1 → `users`
- N:1 → `articles`

**Constraints:**
- `uq_user_article_bookmark` - Unique user+article combination

**Indexes:**
- `idx_bookmarks_user_id` - User's bookmarks
- `idx_bookmarks_article_id` - Article bookmarks
- `idx_bookmarks_created_at` - Date sorting
- `idx_bookmarks_collection` - Collection filtering (partial index)

---

### 8. **reading_history** 📖

**Purpose:** Track article views and engagement metrics

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Primary key |
| `user_id` | UUID | FK → users, NOT NULL | Reader |
| `article_id` | UUID | FK → articles, NOT NULL | Article viewed |
| `viewed_at` | TIMESTAMP | NOT NULL | View timestamp |
| `duration_seconds` | INTEGER | NULL | Time spent reading |
| `scroll_percentage` | DECIMAL(5,2) | NULL | Scroll depth (0-100) |

**Relationships:**
- N:1 → `users`
- N:1 → `articles`

**Indexes:**
- `idx_reading_history_user_id` - User's history
- `idx_reading_history_article_id` - Article views
- `idx_reading_history_viewed_at` - Date sorting
- `idx_reading_history_user_viewed` - User + date composite

---

### 9. **user_reading_preferences** ⚙️

**Purpose:** User privacy and tracking preferences

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Primary key |
| `user_id` | UUID | FK → users, UNIQUE, NOT NULL, Index | User reference (1:1) |
| `tracking_enabled` | BOOLEAN | NOT NULL, Default: true | Reading history tracking |
| `analytics_opt_in` | BOOLEAN | NOT NULL, Default: true | Analytics participation |
| `auto_cleanup_enabled` | BOOLEAN | NOT NULL, Default: false | Auto-delete old history |
| `retention_days` | INTEGER | NOT NULL, Default: 365 | History retention period |
| `exclude_categories` | ARRAY(STRING) | NOT NULL, Default: [] | Categories to exclude |
| `created_at` | TIMESTAMP | NOT NULL | Preference creation |
| `updated_at` | TIMESTAMP | NOT NULL | Last update |

**Relationships:**
- 1:1 → `users`

---

### 10. **notifications** 🔔

**Purpose:** User notifications for interactions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Primary key |
| `user_id` | UUID | FK → users, NOT NULL, Index | Notification recipient |
| `type` | VARCHAR(50) | NOT NULL, Index | Notification type |
| `title` | VARCHAR(255) | NOT NULL | Notification title |
| `message` | TEXT | NOT NULL | Notification message |
| `related_entity_type` | VARCHAR(50) | NULL | Entity type (article/comment) |
| `related_entity_id` | UUID | NULL | Entity ID |
| `actor_id` | UUID | FK → users, NULL, Index | User who triggered |
| `is_read` | BOOLEAN | NOT NULL, Default: false, Index | Read status |
| `read_at` | TIMESTAMP | NULL | Read timestamp |
| `created_at` | TIMESTAMP | NOT NULL, Index | Notification creation |

**Notification Types:**
- `vote` - Someone voted on user's content
- `reply` - Someone replied to user's comment
- `mention` - User was mentioned

**Relationships:**
- N:1 → `users` (recipient)
- N:1 → `users` (actor)

**Indexes:**
- `idx_notifications_user_id` - User's notifications
- `idx_notifications_type` - Type filtering
- `idx_notifications_actor_id` - Actor filtering
- `idx_notifications_is_read` - Unread notifications
- `idx_notifications_created_at` - Date sorting

---

### 11. **user_notification_preferences** 🔕

**Purpose:** User notification settings

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Primary key |
| `user_id` | UUID | FK → users, UNIQUE, NOT NULL, Index | User reference (1:1) |
| `vote_notifications` | BOOLEAN | NOT NULL, Default: true | Vote notifications |
| `reply_notifications` | BOOLEAN | NOT NULL, Default: true | Reply notifications |
| `mention_notifications` | BOOLEAN | NOT NULL, Default: true | Mention notifications |
| `email_notifications` | BOOLEAN | NOT NULL, Default: false | Email notifications |
| `created_at` | TIMESTAMP | NOT NULL | Preference creation |
| `updated_at` | TIMESTAMP | NOT NULL | Last update |

**Relationships:**
- 1:1 → `users`

---

### 12. **user_feed_subscriptions** 📬

**Purpose:** User subscriptions to specific RSS feeds

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Primary key |
| `user_id` | UUID | FK → users, NOT NULL, Index | Subscriber |
| `feed_id` | UUID | FK → rss_sources, NOT NULL, Index | Subscribed feed |
| `is_active` | BOOLEAN | NOT NULL, Default: true | Subscription status |
| `notifications_enabled` | BOOLEAN | NOT NULL, Default: true | New article notifications |
| `subscribed_at` | TIMESTAMP | NOT NULL | Subscription timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update |

**Relationships:**
- N:1 → `users`
- N:1 → `rss_sources`

**Constraints:**
- `unique_user_feed_subscription` - One subscription per user per feed

---

### 13. **source_credibility_scores** 📊

**Purpose:** Aggregated source credibility over time

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Primary key |
| `rss_source_id` | UUID | FK → rss_sources, NOT NULL, Index | Source reference |
| `average_score` | DECIMAL(5,2) | NOT NULL, Index | Average credibility |
| `total_articles_checked` | INTEGER | NOT NULL, Default: 0 | Articles fact-checked |
| `true_count` | INTEGER | NOT NULL, Default: 0 | True verdicts |
| `false_count` | INTEGER | NOT NULL, Default: 0 | False verdicts |
| `misleading_count` | INTEGER | NOT NULL, Default: 0 | Misleading verdicts |
| `unverified_count` | INTEGER | NOT NULL, Default: 0 | Unverified verdicts |
| `period_start` | TIMESTAMP | NOT NULL | Period start date |
| `period_end` | TIMESTAMP | NOT NULL, Index | Period end date |
| `period_type` | VARCHAR(20) | NOT NULL, Index | Period type |
| `trend_data` | JSONB | NULL | Historical trend data |
| `created_at` | TIMESTAMP | NOT NULL | Record creation |
| `updated_at` | TIMESTAMP | NOT NULL | Last update |

**Period Types:**
- `daily` - Daily aggregation
- `weekly` - Weekly aggregation
- `monthly` - Monthly aggregation
- `all_time` - All-time aggregation

**Relationships:**
- N:1 → `rss_sources`

**Indexes:**
- `idx_source_credibility_scores_rss_source_id` - Source lookup
- `idx_source_credibility_scores_average_score` - Score sorting
- `idx_source_credibility_scores_period_end` - Date filtering
- `idx_source_credibility_scores_period_type` - Period filtering

---

## Analytics Tables

### 14. **Materialized Views** (Analytics Optimization)

#### **analytics_daily_summary** 📅

Pre-aggregated daily statistics for fast dashboard loading.

```sql
CREATE MATERIALIZED VIEW analytics_daily_summary AS
SELECT 
    DATE(a.created_at) as summary_date,
    COUNT(DISTINCT a.id) as articles_count,
    COUNT(DISTINCT a.rss_source_id) as sources_count,
    AVG(afc.credibility_score) as avg_credibility,
    AVG(afc.confidence) as avg_confidence,
    COUNT(CASE WHEN afc.verdict = 'TRUE' THEN 1 END) as true_count,
    COUNT(CASE WHEN afc.verdict = 'FALSE' THEN 1 END) as false_count,
    COUNT(CASE WHEN afc.verdict = 'MISLEADING' THEN 1 END) as misleading_count,
    SUM(afc.claims_analyzed) as total_claims
FROM articles a
JOIN article_fact_checks afc ON a.id = afc.article_id
WHERE a.created_at >= CURRENT_DATE - INTERVAL '365 days'
GROUP BY DATE(a.created_at);
```

**Refresh:** Every 15 minutes via Celery  
**Index:** `idx_analytics_daily_summary_date (summary_date DESC)`

---

#### **analytics_source_reliability** 📰

Per-source credibility aggregations for the last 90 days.

```sql
CREATE MATERIALIZED VIEW analytics_source_reliability AS
SELECT 
    rs.id as source_id,
    rs.name as source_name,
    rs.category,
    COUNT(DISTINCT a.id) as articles_count,
    AVG(afc.credibility_score) as avg_credibility,
    AVG(afc.confidence) as avg_confidence,
    COUNT(CASE WHEN afc.verdict = 'TRUE' THEN 1 END) as true_verdicts,
    COUNT(CASE WHEN afc.verdict = 'FALSE' THEN 1 END) as false_verdicts,
    COUNT(CASE WHEN afc.verdict = 'MISLEADING' THEN 1 END) as misleading_verdicts,
    SUM(afc.claims_analyzed) as total_claims,
    MAX(a.created_at) as last_article_date
FROM rss_sources rs
JOIN articles a ON rs.id = a.rss_source_id
JOIN article_fact_checks afc ON a.id = afc.article_id
WHERE a.created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY rs.id, rs.name, rs.category
HAVING COUNT(DISTINCT a.id) >= 5;
```

**Refresh:** Every 15 minutes via Celery  
**Indexes:**
- `idx_analytics_source_reliability_id (source_id)` - Unique
- `idx_analytics_source_reliability_credibility (avg_credibility DESC)`

---

#### **analytics_category_summary** 📂

Category-level analytics with risk assessment.

```sql
CREATE MATERIALIZED VIEW analytics_category_summary AS
SELECT 
    a.category,
    COUNT(DISTINCT a.id) as articles_count,
    AVG(afc.credibility_score) as avg_credibility,
    COUNT(CASE WHEN afc.verdict IN ('FALSE', 'MISLEADING') THEN 1 END) as risk_count,
    COUNT(CASE WHEN afc.verdict IN ('FALSE', 'MISLEADING') THEN 1 END)::FLOAT 
        / NULLIF(COUNT(a.id), 0) * 100 as false_rate,
    ARRAY(
        SELECT DISTINCT name 
        FROM unnest(ARRAY_AGG(DISTINCT rs.name)) AS name 
        ORDER BY name 
        LIMIT 5
    ) as top_sources
FROM articles a
JOIN article_fact_checks afc ON a.id = afc.article_id
JOIN rss_sources rs ON a.rss_source_id = rs.id
WHERE a.created_at >= CURRENT_DATE - INTERVAL '90 days'
  AND a.category IS NOT NULL
GROUP BY a.category
HAVING COUNT(DISTINCT a.id) >= 5;
```

**Refresh:** Every 15 minutes via Celery  
**Index:** `idx_analytics_category_summary_category (category)` - Unique

---

## Data Flow

### 1. **RSS Feed Ingestion Flow** 📥

```
┌──────────────────┐
│  Celery Beat     │ (Every 15 minutes)
│  Scheduler       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ fetch_all_feeds  │ (Celery Task)
│    Task          │
└────────┬─────────┘
         │
         ├─────────────────────────────────────┐
         │                                     │
         ▼                                     ▼
┌──────────────────┐                  ┌──────────────────┐
│  RSS Feed        │                  │  RSS Feed        │
│  Parser          │                  │  Parser          │
│  (feedparser)    │                  │  (feedparser)    │
└────────┬─────────┘                  └────────┬─────────┘
         │                                     │
         ▼                                     ▼
┌──────────────────┐                  ┌──────────────────┐
│ Validate &       │                  │ Validate &       │
│ Hash URL         │                  │ Hash URL         │
└────────┬─────────┘                  └────────┬─────────┘
         │                                     │
         └─────────────────┬───────────────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Check Duplicate  │ (url_hash lookup)
                 │ via url_hash     │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │  Create Article  │
                 │  in Database     │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Trigger Fact     │ (Optional/Async)
                 │ Check Job        │
                 └──────────────────┘
```

---

### 2. **Fact-Check Flow** ✅

```
┌──────────────────┐
│   Article        │
│   Created        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Fact-Check API   │ (External Service)
│    Request       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  AI Validation   │ (GPT-4, Claude, etc.)
│  Processing      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Parse Results   │
│  Extract Claims  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Create/Update    │
│ ArticleFactCheck │
│   Record         │
└────────┬─────────┘
         │
         ├─────────────────────────────────────┐
         │                                     │
         ▼                                     ▼
┌──────────────────┐                  ┌──────────────────┐
│ Update Article   │                  │ Update Source    │
│ Denormalized     │                  │ Credibility      │
│ Fields           │                  │ Scores           │
│ (fact_check_*)   │                  │                  │
└────────┬─────────┘                  └────────┬─────────┘
         │                                     │
         └─────────────────┬───────────────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Refresh Mat.     │
                 │ Views (Next      │
                 │ 15-min cycle)    │
                 └──────────────────┘
```

---

### 3. **User Interaction Flow** 👥

```
┌──────────────────┐
│   User Action    │
│ (Vote/Comment/   │
│  Bookmark)       │
└────────┬─────────┘
         │
         ├────────────────┬────────────────┬────────────────┐
         │                │                │                │
         ▼                ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Create Vote │  │Create Comment│  │Create        │  │Track Reading │
│  Record      │  │  Record      │  │Bookmark      │  │ History      │
└────┬─────────┘  └────┬─────────┘  └────┬─────────┘  └────┬─────────┘
     │                 │                 │                 │
     ▼                 ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│Update Article│  │Update Article│  │Update User   │  │Update User   │
│vote_score &  │  │comment_count │  │Collections   │  │Reading Stats │
│vote_count    │  │              │  │              │  │              │
└────┬─────────┘  └────┬─────────┘  └────┬─────────┘  └──────────────┘
     │                 │                 │
     ▼                 ▼                 │
┌──────────────────────────────┐       │
│  Create Notification         │       │
│  (if applicable)             │       │
│  - Vote on user's content    │       │
│  - Reply to comment          │       │
│  - Mention in comment        │       │
└────┬─────────────────────────┘       │
     │                                 │
     └─────────────────┬───────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Update Trending  │
              │ Algorithm Score  │
              └──────────────────┘
```

---

### 4. **Analytics Query Flow** 📊

```
┌──────────────────┐
│  API Request     │ (GET /api/v1/analytics/*)
│  (Analytics      │
│   Endpoint)      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Check Redis      │ (5-minute TTL)
│ Cache            │
└────────┬─────────┘
         │
         ├─────────────────────────────┐
         │ CACHE HIT                   │ CACHE MISS
         ▼                             ▼
┌──────────────────┐         ┌──────────────────┐
│ Return Cached    │         │ Query Database   │
│ Result           │         │ (Materialized    │
│                  │         │  Views or        │
│                  │         │  Direct Tables)  │
└──────────────────┘         └────────┬─────────┘
                                      │
                                      ▼
                             ┌──────────────────┐
                             │ Process &        │
                             │ Format Results   │
                             └────────┬─────────┘
                                      │
                                      ▼
                             ┌──────────────────┐
                             │ Store in Redis   │
                             │ Cache (5 min)    │
                             └────────┬─────────┘
                                      │
                                      ▼
                             ┌──────────────────┐
                             │ Return Result    │
                             └──────────────────┘
```

---

## Relationships

### Cascade Delete Behavior

**User Deletion** → Cascades to:
- votes
- comments
- bookmarks
- reading_history
- user_reading_preferences
- notifications
- user_notification_preferences
- user_feed_subscriptions

**Article Deletion** → Cascades to:
- votes
- comments
- bookmarks
- reading_history
- article_fact_checks

**RSS Source Deletion** → Cascades to:
- articles (and all article cascades)
- source_credibility_scores
- user_feed_subscriptions

**Comment Deletion** → Cascades to:
- votes on that comment
- child comments (recursive)

---

## Indexes & Performance

### Critical Indexes for Analytics (⭐ Optimized)

1. **Date Range Queries**
   - `idx_articles_created_at` - 10x faster date filtering
   - `idx_articles_source_created` - 7x faster source analytics
   - `idx_articles_category_created` - 8x faster category analytics

2. **Fact-Check Queries**
   - `idx_article_fact_checks_article_id` - Fast JOIN operations
   - `idx_article_fact_checks_verdict` - Verdict filtering
   - `idx_article_fact_checks_confidence` - Confidence-based queries

3. **Engagement Metrics**
   - `idx_articles_vote_score` - Popular articles
   - `idx_articles_trending_score` - Trending algorithm
   - `idx_comments_vote_count` - Popular comments

### Performance Optimization Strategies

1. **Materialized Views** - 45-70x faster for complex aggregations
2. **Redis Caching** - 5-minute TTL for analytics endpoints
3. **Denormalized Counters** - vote_count, comment_count on articles
4. **Composite Indexes** - (source_id, created_at), (category, created_at)
5. **Partial Indexes** - Collection bookmarks, unread notifications
6. **TSVECTOR** - Full-text search on articles

---

## Database Maintenance

### Automated Tasks (Celery Beat)

| Task | Frequency | Purpose |
|------|-----------|---------|
| `fetch_all_feeds` | 15 min | RSS feed ingestion |
| `refresh_materialized_views` | 15 min | Update analytics views |
| `warm_analytics_cache` | 16 min | Pre-populate Redis cache |
| `clear_analytics_cache` | 15 min | Invalidate stale cache |

### Manual Maintenance

```sql
-- Vacuum and analyze
VACUUM ANALYZE articles;
VACUUM ANALYZE article_fact_checks;
VACUUM ANALYZE votes;
VACUUM ANALYZE comments;

-- Reindex
REINDEX TABLE articles;
REINDEX TABLE article_fact_checks;

-- Check table sizes
SELECT 
    tablename, 
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Migration Management

**Tool:** Alembic  
**Location:** `alembic/versions/`  
**Current Version:** See `alembic_version` table

### Key Migrations

1. **Initial Schema** - Base tables and relationships
2. **Fact-Check Integration** - ArticleFactCheck table
3. **Analytics Indexes** - Performance optimization indexes
4. **Materialized Views** - Pre-aggregated analytics
5. **Query Monitoring** - pg_stat_statements extension

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Check current version
alembic current
```

---

## Related Documentation

- [DATABASE_OPTIMIZATION.md](./DATABASE_OPTIMIZATION.md) - Performance optimization guide
- [DATABASE_OPTIMIZATION_COMPLETE.md](./DATABASE_OPTIMIZATION_COMPLETE.md) - Implementation summary
- [ANALYTICS_API.md](./ANALYTICS_API.md) - Analytics API documentation
- [WARP.md](./WARP.md) - Development guide

---

**Last Updated:** November 2, 2025  
**Database Version:** PostgreSQL 15+ (Supabase)  
**Total Tables:** 14 (11 core + 3 materialized views)
