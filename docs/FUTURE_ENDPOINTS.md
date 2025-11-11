# Future API Endpoints - Exploration and Recommendations

## Overview

This document explores additional API endpoints to consider for the RSS News Aggregator backend. These recommendations are based on the current architecture (9 core services, layered design) and aim to enhance functionality, user experience, and data accessibility.

**Current Endpoint Count**: ~50 endpoints across 14 modules
**Status**: Active exploration for v2.0 roadmap

---

## Table of Contents

1. [Analytics & Insights Endpoints](#1-analytics--insights-endpoints)
2. [Social Features Endpoints](#2-social-features-endpoints)
3. [Content Discovery Endpoints](#3-content-discovery-endpoints)
4. [Moderation & Admin Endpoints](#4-moderation--admin-endpoints)
5. [External Integration Endpoints](#5-external-integration-endpoints)
6. [Accessibility & Personalization Endpoints](#6-accessibility--personalization-endpoints)
7. [Performance & Developer Endpoints](#7-performance--developer-endpoints)
8. [Webhook & Event Streaming Endpoints](#8-webhook--event-streaming-endpoints)
9. [Implementation Priority Matrix](#9-implementation-priority-matrix)
10. [Technical Considerations](#10-technical-considerations)

---

## 1. Analytics & Insights Endpoints

### 1.1 Trending Topics Endpoint
**Endpoint**: `GET /api/v1/analytics/trending-topics`

**Purpose**: Surface trending topics across articles to help users discover hot discussions.

**Query Parameters**:
- `time_range`: hour, day, week, month (default: day)
- `category`: Filter by article category
- `min_article_count`: Minimum articles to be considered trending (default: 3)
- `limit`: Number of topics to return (default: 10, max: 50)

**Response Example**:
```json
{
  "topics": [
    {
      "topic": "artificial intelligence",
      "article_count": 47,
      "total_votes": 1253,
      "total_comments": 387,
      "growth_rate": 2.3,
      "trending_score": 89.5,
      "sample_articles": [
        {"id": "uuid", "title": "AI Breakthrough..."},
        {"id": "uuid", "title": "OpenAI Announces..."}
      ]
    }
  ],
  "generated_at": "2025-11-11T18:00:00Z"
}
```

**Implementation Notes**:
- Use PostgreSQL full-text search with `ts_rank` for relevance
- Cache results for 15 minutes
- Consider using Redis for real-time trending calculation
- Tag extraction from article titles/descriptions

---

### 1.2 User Engagement Heatmap
**Endpoint**: `GET /api/v1/analytics/engagement-heatmap`

**Purpose**: Provide temporal engagement patterns for optimal posting times.

**Query Parameters**:
- `date_range`: Last 7/30/90 days
- `timezone`: User's timezone for localization

**Response Example**:
```json
{
  "heatmap": [
    {
      "day_of_week": "Monday",
      "hourly_data": [
        {"hour": 0, "article_views": 234, "comments": 45, "votes": 123},
        {"hour": 1, "article_views": 189, "comments": 32, "votes": 98}
      ]
    }
  ],
  "peak_engagement_time": "Tuesday 8:00 PM",
  "timezone": "America/New_York"
}
```

**Use Cases**:
- Content publishers optimize posting times
- Admins understand traffic patterns
- RSS feed scheduling optimization

---

### 1.3 Article Performance Metrics
**Endpoint**: `GET /api/v1/articles/{article_id}/analytics`

**Purpose**: Detailed performance metrics for individual articles.

**Response Example**:
```json
{
  "article_id": "uuid",
  "views": {
    "total": 5432,
    "unique": 4123,
    "by_source": {"direct": 2341, "rss": 1891, "search": 1200}
  },
  "engagement": {
    "avg_read_time_seconds": 147,
    "avg_scroll_percentage": 68.3,
    "completion_rate": 0.42
  },
  "social": {
    "shares": 234,
    "bookmarks": 189,
    "votes": {"upvotes": 456, "downvotes": 23},
    "comments": 67
  },
  "trending_score": 87.5,
  "performance_percentile": 92
}
```

**Authentication**: Optional (public stats vs detailed stats for authenticated users)

---

### 1.4 Content Quality Score
**Endpoint**: `GET /api/v1/analytics/content-quality`

**Purpose**: Aggregate quality metrics across sources and categories.

**Query Parameters**:
- `source_id`: Filter by RSS source
- `category`: Filter by category
- `time_range`: Analysis period

**Response Example**:
```json
{
  "overall_quality_score": 78.4,
  "metrics": {
    "fact_check_pass_rate": 0.87,
    "avg_credibility_score": 82.1,
    "misinformation_rate": 0.03,
    "source_consensus_rate": 0.91
  },
  "by_source": [
    {
      "source_name": "AP News",
      "quality_score": 94.2,
      "article_count": 234,
      "fact_check_pass_rate": 0.98
    }
  ],
  "recommendations": [
    "Consider removing sources with quality_score < 60",
    "5 sources have declining quality trends"
  ]
}
```

---

## 2. Social Features Endpoints

### 2.1 User Following System
**Endpoints**:
- `POST /api/v1/users/{user_id}/follow` - Follow a user
- `DELETE /api/v1/users/{user_id}/follow` - Unfollow a user
- `GET /api/v1/users/{user_id}/followers` - Get followers list
- `GET /api/v1/users/{user_id}/following` - Get following list
- `GET /api/v1/users/me/feed` - Personalized feed from followed users

**Use Case**: Build community by enabling users to follow power commenters/contributors.

**Response Example** (`GET /api/v1/users/me/feed`):
```json
{
  "activities": [
    {
      "id": "uuid",
      "user": {"username": "john_doe", "avatar_url": "..."},
      "activity_type": "comment",
      "article": {"id": "uuid", "title": "..."},
      "comment": {"content": "Great analysis...", "vote_score": 45},
      "timestamp": "2025-11-11T17:30:00Z"
    },
    {
      "activity_type": "vote",
      "user": {...},
      "article": {...},
      "timestamp": "2025-11-11T16:45:00Z"
    }
  ],
  "page": 1,
  "total": 147
}
```

**Database Impact**:
- New table: `user_follows` (follower_id, followed_id, created_at)
- Index on both foreign keys for performance

---

### 2.2 Comment Mentions
**Endpoints**:
- `GET /api/v1/users/me/mentions` - Get all mentions
- `POST /api/v1/comments` (enhanced) - Parse @username mentions

**Purpose**: Enable user-to-user communication via @mentions in comments.

**Implementation**:
- Parse comment content for `@username` patterns
- Create notification when user is mentioned
- Link mention to notification system

**Response Example**:
```json
{
  "mentions": [
    {
      "id": "uuid",
      "mentioned_in": {
        "comment_id": "uuid",
        "comment_content": "Hey @john_doe, what do you think?",
        "article_id": "uuid",
        "article_title": "..."
      },
      "mentioned_by": {
        "user_id": "uuid",
        "username": "jane_smith",
        "avatar_url": "..."
      },
      "created_at": "2025-11-11T16:00:00Z",
      "is_read": false
    }
  ],
  "unread_count": 7
}
```

---

### 2.3 Thread Subscriptions
**Endpoints**:
- `POST /api/v1/comments/{comment_id}/subscribe` - Subscribe to thread updates
- `DELETE /api/v1/comments/{comment_id}/subscribe` - Unsubscribe
- `GET /api/v1/users/me/subscriptions` - Get all subscribed threads

**Purpose**: Allow users to follow specific discussion threads.

**Notifications**:
- New reply in subscribed thread
- Mentioned in subscribed thread
- Highly upvoted reply in thread

---

### 2.4 User Reputation System
**Endpoints**:
- `GET /api/v1/users/{user_id}/reputation` - Get reputation breakdown
- `GET /api/v1/leaderboard` - Top contributors

**Response Example**:
```json
{
  "user_id": "uuid",
  "username": "power_commenter",
  "reputation_score": 4523,
  "breakdown": {
    "comment_upvotes": 3892,
    "helpful_flags": 234,
    "article_submissions": 45,
    "fact_check_contributions": 12,
    "badges": ["fact_checker", "super_commenter", "early_adopter"]
  },
  "rank": 47,
  "percentile": 98.2
}
```

**Reputation Calculation**:
- Comment upvotes: +1 point each
- Downvotes: -1 point each
- Accepted answer: +15 points
- Article upvote: +2 points
- Fact-check contribution: +50 points

---

## 3. Content Discovery Endpoints

### 3.1 Similar Articles Recommendation
**Endpoint**: `GET /api/v1/articles/{article_id}/similar`

**Purpose**: Content-based recommendation using article similarity.

**Query Parameters**:
- `limit`: Number of results (default: 5, max: 20)
- `algorithm`: cosine_similarity, tf_idf, collaborative (default: tf_idf)

**Response Example**:
```json
{
  "article_id": "uuid",
  "similar_articles": [
    {
      "id": "uuid",
      "title": "Related Article...",
      "similarity_score": 0.87,
      "matching_tags": ["AI", "technology"],
      "published_date": "2025-11-10T12:00:00Z"
    }
  ],
  "algorithm_used": "tf_idf"
}
```

**Implementation**:
- Use PostgreSQL `pg_trgm` extension for trigram similarity
- Pre-compute article embeddings nightly
- Cache results for 1 hour

---

### 3.2 Personalized Recommendations
**Endpoint**: `GET /api/v1/recommendations/for-you`

**Purpose**: ML-powered personalized article recommendations.

**Query Parameters**:
- `page`: Page number
- `page_size`: Items per page
- `exclude_read`: Skip articles user already read (default: true)

**Response Example**:
```json
{
  "recommendations": [
    {
      "article": {...},
      "recommendation_score": 0.92,
      "reasons": [
        "Similar to articles you upvoted",
        "Popular in your reading history category",
        "Trending in your network"
      ],
      "model_version": "v2.1"
    }
  ],
  "model_type": "collaborative_filtering",
  "generated_at": "2025-11-11T18:00:00Z"
}
```

**ML Model Requirements**:
- Collaborative filtering based on user-article interactions
- Cold start handling for new users
- A/B testing framework for model versions

---

### 3.3 Topic Clustering
**Endpoint**: `GET /api/v1/topics/clusters`

**Purpose**: Discover topic clusters and related articles.

**Response Example**:
```json
{
  "clusters": [
    {
      "cluster_id": 1,
      "primary_topic": "Climate Change",
      "subtopics": ["renewable energy", "carbon emissions", "policy"],
      "article_count": 234,
      "avg_engagement_score": 78.3,
      "sample_articles": [...]
    }
  ],
  "total_clusters": 15,
  "clustering_algorithm": "k_means"
}
```

---

### 3.4 Saved Searches
**Endpoints**:
- `POST /api/v1/search/save` - Save a search query
- `GET /api/v1/search/saved` - List saved searches
- `GET /api/v1/search/saved/{search_id}/results` - Get new results for saved search
- `DELETE /api/v1/search/saved/{search_id}` - Delete saved search

**Purpose**: Allow users to monitor specific topics via saved searches.

**Response Example**:
```json
{
  "saved_searches": [
    {
      "id": "uuid",
      "query": "artificial intelligence ethics",
      "created_at": "2025-11-01T00:00:00Z",
      "new_results_count": 12,
      "notification_enabled": true,
      "last_checked": "2025-11-11T17:00:00Z"
    }
  ]
}
```

---

## 4. Moderation & Admin Endpoints

### 4.1 Content Flagging System
**Endpoints**:
- `POST /api/v1/flags` - Report content (article, comment)
- `GET /api/v1/admin/flags` - List all reported content
- `PATCH /api/v1/admin/flags/{flag_id}` - Resolve flag
- `GET /api/v1/admin/flags/stats` - Moderation statistics

**Request Example** (`POST /api/v1/flags`):
```json
{
  "entity_type": "comment",
  "entity_id": "uuid",
  "reason": "spam",
  "details": "Commercial link with no relevance"
}
```

**Response Example** (`GET /api/v1/admin/flags`):
```json
{
  "flags": [
    {
      "id": "uuid",
      "entity_type": "comment",
      "entity_id": "uuid",
      "reason": "misinformation",
      "reporter_id": "uuid",
      "status": "pending",
      "priority": "high",
      "created_at": "2025-11-11T16:00:00Z",
      "moderator_notes": null
    }
  ],
  "pending_count": 47,
  "avg_resolution_time_minutes": 45
}
```

---

### 4.2 Automated Content Filters
**Endpoints**:
- `GET /api/v1/admin/filters` - List active filters
- `POST /api/v1/admin/filters` - Create filter rule
- `DELETE /api/v1/admin/filters/{filter_id}` - Remove filter

**Filter Types**:
- Spam detection (ML-based)
- Profanity filtering
- Suspicious link detection
- Bot account detection

**Response Example**:
```json
{
  "filters": [
    {
      "id": "uuid",
      "filter_type": "spam_detection",
      "enabled": true,
      "confidence_threshold": 0.85,
      "actions": ["flag", "auto_hide"],
      "hit_count_24h": 23
    }
  ]
}
```

---

### 4.3 User Moderation Actions
**Endpoints**:
- `POST /api/v1/admin/users/{user_id}/ban` - Ban user
- `POST /api/v1/admin/users/{user_id}/unban` - Unban user
- `POST /api/v1/admin/users/{user_id}/mute` - Temporary mute
- `GET /api/v1/admin/users/{user_id}/history` - Moderation history

**Request Example** (`POST /api/v1/admin/users/{user_id}/ban`):
```json
{
  "reason": "repeated spam violations",
  "duration_hours": 168,
  "ban_type": "temporary",
  "notify_user": true
}
```

---

### 4.4 Content Approval Queue
**Endpoint**: `GET /api/v1/admin/approval-queue`

**Purpose**: Review articles/comments before public visibility (optional workflow).

**Query Parameters**:
- `content_type`: article, comment
- `status`: pending, approved, rejected
- `source_id`: Filter by RSS source

**Response Example**:
```json
{
  "queue": [
    {
      "id": "uuid",
      "content_type": "article",
      "title": "...",
      "source": "New Source Name",
      "submitted_at": "2025-11-11T15:00:00Z",
      "risk_score": 0.35,
      "auto_flags": ["suspicious_link", "new_source"],
      "status": "pending"
    }
  ],
  "stats": {
    "pending": 12,
    "avg_review_time_minutes": 8
  }
}
```

---

## 5. External Integration Endpoints

### 5.1 RSS Feed Management (Enhanced)
**Endpoints**:
- `POST /api/v1/rss-feeds/{feed_id}/validate` - Test RSS feed health
- `GET /api/v1/rss-feeds/{feed_id}/preview` - Preview articles from new feed
- `POST /api/v1/rss-feeds/bulk-import` - Bulk import from OPML file
- `GET /api/v1/rss-feeds/export` - Export subscriptions as OPML

**Response Example** (`GET /api/v1/rss-feeds/{feed_id}/preview`):
```json
{
  "feed_id": "uuid",
  "feed_url": "https://example.com/feed",
  "preview_articles": [
    {
      "title": "Sample Article",
      "url": "https://example.com/article",
      "published_date": "2025-11-11T12:00:00Z",
      "estimated_category": "technology"
    }
  ],
  "feed_health": {
    "status": "healthy",
    "last_updated": "2025-11-11T17:30:00Z",
    "avg_article_quality_score": 82.3
  }
}
```

---

### 5.2 Third-Party API Integrations
**Endpoints**:
- `POST /api/v1/integrations/pocket/save` - Save to Pocket
- `POST /api/v1/integrations/twitter/share` - Share on Twitter/X
- `GET /api/v1/integrations/instapaper/export` - Export to Instapaper
- `POST /api/v1/integrations/evernote/clip` - Clip to Evernote

**Purpose**: Enable read-it-later and social sharing integrations.

**Authentication**: OAuth 2.0 flow for each third-party service.

---

### 5.3 Webhook Configuration
**Endpoints**:
- `POST /api/v1/webhooks` - Create webhook
- `GET /api/v1/webhooks` - List user's webhooks
- `DELETE /api/v1/webhooks/{webhook_id}` - Delete webhook
- `POST /api/v1/webhooks/{webhook_id}/test` - Send test payload

**Request Example** (`POST /api/v1/webhooks`):
```json
{
  "url": "https://example.com/webhook",
  "events": ["article.created", "fact_check.completed"],
  "secret": "webhook_secret_for_signature",
  "enabled": true
}
```

**Webhook Events**:
- `article.created`
- `fact_check.completed`
- `comment.created`
- `article.trending`
- `user.mentioned`

---

### 5.4 API Usage & Rate Limits
**Endpoints**:
- `GET /api/v1/account/api-keys` - List API keys
- `POST /api/v1/account/api-keys` - Generate new API key
- `GET /api/v1/account/usage` - Get API usage stats
- `GET /api/v1/account/rate-limits` - Get current rate limit status

**Response Example** (`GET /api/v1/account/usage`):
```json
{
  "current_period": {
    "start": "2025-11-01T00:00:00Z",
    "end": "2025-12-01T00:00:00Z",
    "requests_made": 12453,
    "requests_limit": 100000,
    "usage_percentage": 12.45
  },
  "by_endpoint": [
    {
      "endpoint": "/api/v1/articles",
      "method": "GET",
      "request_count": 5432
    }
  ]
}
```

---

## 6. Accessibility & Personalization Endpoints

### 6.1 Reading Preferences
**Endpoints**:
- `GET /api/v1/users/me/reading-preferences` - Get preferences
- `PUT /api/v1/users/me/reading-preferences` - Update preferences

**Preference Options**:
```json
{
  "font_size": "medium",
  "theme": "dark",
  "line_spacing": 1.5,
  "dyslexia_friendly_font": true,
  "auto_read_aloud": false,
  "summarization_length": "medium",
  "translation_language": "es"
}
```

---

### 6.2 Content Summarization
**Endpoint**: `GET /api/v1/articles/{article_id}/summary`

**Purpose**: AI-generated article summaries for quick consumption.

**Query Parameters**:
- `length`: short (50 words), medium (150 words), long (300 words)
- `format`: bullet_points, paragraph

**Response Example**:
```json
{
  "article_id": "uuid",
  "summary": {
    "short": "Three-sentence summary...",
    "key_points": [
      "Main point 1",
      "Main point 2",
      "Main point 3"
    ]
  },
  "reading_time_saved_seconds": 180,
  "model_used": "gpt-4-turbo"
}
```

---

### 6.3 Translation Service
**Endpoint**: `GET /api/v1/articles/{article_id}/translate`

**Query Parameters**:
- `target_language`: ISO 639-1 code (es, fr, de, etc.)
- `translate_comments`: Include comment translations (default: false)

**Response Example**:
```json
{
  "article_id": "uuid",
  "original_language": "en",
  "target_language": "es",
  "translated_content": {
    "title": "Título traducido",
    "description": "Descripción traducida",
    "crawled_content": "Contenido completo traducido..."
  },
  "translation_provider": "google_translate_api"
}
```

---

### 6.4 Accessibility Score
**Endpoint**: `GET /api/v1/articles/{article_id}/accessibility`

**Purpose**: Evaluate article accessibility (readability, alt text, etc.).

**Response Example**:
```json
{
  "article_id": "uuid",
  "accessibility_score": 78,
  "metrics": {
    "flesch_reading_ease": 65.2,
    "gunning_fog_index": 10.3,
    "has_alt_text": true,
    "color_contrast_pass": true,
    "screen_reader_friendly": true
  },
  "recommendations": [
    "Simplify complex sentences",
    "Add more paragraph breaks"
  ]
}
```

---

## 7. Performance & Developer Endpoints

### 7.1 Cache Management
**Endpoints**:
- `DELETE /api/v1/cache/articles/{article_id}` - Invalidate article cache
- `DELETE /api/v1/cache/feed` - Clear feed cache
- `POST /api/v1/cache/warm` - Pre-warm cache for popular content

**Purpose**: Admin control over cache invalidation.

---

### 7.2 Health & Status Endpoints (Enhanced)
**Endpoints**:
- `GET /api/v1/status/detailed` - Detailed system status
- `GET /api/v1/status/dependencies` - External service health
- `GET /api/v1/status/metrics` - Real-time metrics

**Response Example** (`GET /api/v1/status/detailed`):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 345623,
  "services": {
    "database": {
      "status": "healthy",
      "response_time_ms": 12,
      "connections": {"active": 8, "idle": 15, "max": 20}
    },
    "redis": {
      "status": "healthy",
      "memory_used_mb": 234,
      "hit_rate": 0.87
    },
    "celery": {
      "status": "healthy",
      "workers": 4,
      "queued_tasks": 23,
      "processed_tasks_1h": 1523
    },
    "railway_api": {
      "status": "healthy",
      "last_request_time_ms": 2341
    }
  },
  "timestamp": "2025-11-11T18:00:00Z"
}
```

---

### 7.3 API Documentation Endpoints
**Endpoints**:
- `GET /api/v1/docs/openapi.json` - OpenAPI 3.0 spec
- `GET /api/v1/docs/changelog` - API changelog
- `GET /api/v1/docs/rate-limits` - Rate limit documentation

---

### 7.4 Feature Flags
**Endpoints**:
- `GET /api/v1/features` - List available features for user
- `GET /api/v1/admin/features` - Manage feature flags

**Response Example**:
```json
{
  "features": {
    "article_summarization": true,
    "ai_recommendations": true,
    "beta_ui_v2": false,
    "advanced_search": true
  },
  "user_segment": "premium",
  "flags_updated_at": "2025-11-11T12:00:00Z"
}
```

**Use Cases**:
- A/B testing new features
- Gradual rollout
- Premium feature gating

---

## 8. Webhook & Event Streaming Endpoints

### 8.1 Server-Sent Events (SSE)
**Endpoint**: `GET /api/v1/stream/notifications` (SSE)

**Purpose**: Real-time notification streaming without WebSocket complexity.

**Response Stream**:
```
event: notification
data: {"id": "uuid", "type": "reply", "message": "..."}

event: notification
data: {"id": "uuid", "type": "mention", "message": "..."}
```

---

### 8.2 WebSocket Endpoints
**Endpoint**: `WS /api/v1/ws/feed` (WebSocket)

**Purpose**: Real-time feed updates for live discussions.

**Message Types**:
- `article.published`
- `comment.added`
- `vote.cast`
- `user.online`

---

## 9. Implementation Priority Matrix

### High Priority (v2.0)
| Endpoint | Complexity | Value | Dependencies |
|----------|-----------|-------|--------------|
| Similar Articles | Medium | High | PostgreSQL extensions |
| Trending Topics | Medium | High | Redis, background tasks |
| Content Flagging | Low | High | Admin panel |
| Saved Searches | Low | Medium | Existing search |
| User Following | Medium | High | Social features |

### Medium Priority (v2.1)
| Endpoint | Complexity | Value | Dependencies |
|----------|-----------|-------|--------------|
| Personalized Recommendations | High | High | ML model, training pipeline |
| Article Summaries | Medium | Medium | OpenAI API |
| Webhooks | Medium | Medium | Queue system |
| Reading Preferences | Low | Medium | None |
| API Keys | Low | Medium | Auth system |

### Low Priority (v3.0)
| Endpoint | Complexity | Value | Dependencies |
|----------|-----------|-------|--------------|
| Translation Service | Medium | Low | Translation API |
| Accessibility Score | Medium | Low | NLP libraries |
| Topic Clustering | High | Medium | ML model |
| Third-Party Integrations | High | Low | OAuth flows |
| WebSocket Streaming | High | Medium | WebSocket infra |

---

## 10. Technical Considerations

### 10.1 Database Schema Changes

**New Tables Required**:
```sql
-- User following
CREATE TABLE user_follows (
    follower_id UUID REFERENCES users(id),
    followed_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (follower_id, followed_id)
);

-- Content flags
CREATE TABLE content_flags (
    id UUID PRIMARY KEY,
    entity_type VARCHAR(20),
    entity_id UUID,
    reporter_id UUID REFERENCES users(id),
    reason VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Saved searches
CREATE TABLE saved_searches (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    query TEXT,
    notification_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- API keys
CREATE TABLE api_keys (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    key_hash VARCHAR(255),
    name VARCHAR(100),
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);
```

### 10.2 Performance Optimization

**Caching Strategy**:
- Trending topics: Redis, 15-minute TTL
- Similar articles: PostgreSQL materialized views, daily refresh
- User feed: Redis sorted sets
- Analytics: Pre-aggregate daily via Celery

**Rate Limiting**:
- Public endpoints: 100 req/min/IP
- Authenticated: 1000 req/min/user
- Admin endpoints: 5000 req/min
- Webhook delivery: 10 req/sec/endpoint

### 10.3 Security Considerations

**Authentication**:
- JWT for user endpoints
- API keys for programmatic access
- OAuth 2.0 for third-party integrations
- Admin endpoints require `is_admin` flag

**Authorization**:
- RBAC for moderation actions
- Content ownership validation
- Rate limit by user tier (free/premium/enterprise)

**Data Privacy**:
- GDPR compliance for user data export
- Right to deletion implementation
- Data retention policies
- Audit logs for sensitive actions

### 10.4 Infrastructure Requirements

**Redis**:
- Trending calculations
- Real-time feeds
- Rate limiting
- Session storage

**Celery Workers**:
- Background fact-checking
- Email notifications
- Analytics aggregation
- ML model inference

**External Services**:
- Railway API (fact-checking)
- OpenAI API (summarization)
- Translation API (optional)
- Email service (notifications)

**Monitoring**:
- Sentry (error tracking)
- Prometheus (metrics)
- Grafana (dashboards)
- ELK stack (logging)

---

## Conclusion

This document outlines **40+ additional API endpoints** across 8 major categories. The recommendations prioritize:

1. **User Value**: Features that enhance discovery, engagement, and personalization
2. **Implementation Feasibility**: Leveraging existing architecture and services
3. **Scalability**: Design patterns that support growth
4. **Maintainability**: Clean API design following REST principles

### Next Steps

1. **Stakeholder Review**: Validate priorities with product team
2. **Technical Spike**: Proof-of-concept for high-priority endpoints
3. **API Design Workshop**: Finalize request/response schemas
4. **Migration Plan**: Database schema updates and migrations
5. **Documentation**: OpenAPI specs and developer guides
6. **Phased Rollout**: v2.0 → v2.1 → v3.0 release timeline

### Feedback

For questions or suggestions on these endpoints, contact:
- Backend Team Lead: [contact]
- API Design Review: [email]
- GitHub Discussions: [link]

**Last Updated**: 2025-11-11  
**Version**: 1.0  
**Status**: Draft for Review
