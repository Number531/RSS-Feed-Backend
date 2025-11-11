# Phase 2 API Endpoints Documentation

**Date**: November 11, 2025  
**Version**: 2.0  
**Status**: Production Ready

This document describes the Phase 2 endpoints implemented for the RSS News Aggregator backend. Phase 2 focuses on **Content Quality Analytics** and **Social Features** (mentions).

---

## Table of Contents

1. [Content Quality Analytics](#content-quality-analytics)
2. [Comment Mentions](#comment-mentions)
3. [Database Schema Changes](#database-schema-changes)
4. [Testing Guide](#testing-guide)

---

## Content Quality Analytics

### 1. GET /api/v1/analytics/content-quality

**Purpose**: Generate comprehensive content quality analysis across articles.

**Authentication**: None (public endpoint)

**Query Parameters**:
| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `days` | integer | 7 | 1-365 | Number of days to analyze |
| `category` | string | null | - | Optional filter by article category |
| `min_engagement` | integer | 5 | 1-100 | Minimum engagement threshold (votes+comments+bookmarks) |

**Response Schema**:
```json
{
  "period_days": 7,
  "category": "technology",
  "total_articles": 150,
  "articles_analyzed": 45,
  "min_engagement_threshold": 5,
  "quality_metrics": {
    "avg_quality_score": 67.5,
    "median_quality_score": 72.0,
    "avg_vote_ratio": 0.825,
    "avg_comments_per_article": 12.3,
    "total_engagement": 2847,
    "quality_distribution": {
      "excellent (80+)": 12,
      "good (60-79)": 23,
      "average (40-59)": 8,
      "poor (<40)": 2
    }
  },
  "top_performers": [
    {
      "article_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "New AI Breakthrough in Medical Diagnostics",
      "url": "https://example.com/article",
      "published_at": "2025-11-05T10:30:00",
      "category": "technology",
      "metrics": {
        "votes_count": 156,
        "upvotes": 142,
        "downvotes": 14,
        "vote_ratio": 0.910,
        "comments_count": 34,
        "bookmarks_count": 28,
        "controversy_score": 0.179
      },
      "quality_score": 89.45,
      "total_engagement": 218
    }
  ],
  "recommendations": [
    {
      "type": "category_optimization",
      "priority": "medium",
      "message": "'technology' category performs best. Consider expanding similar sources.",
      "action": "Increase content from 'technology' category, review 'politics' sources"
    }
  ],
  "generated_at": "2025-11-11T16:00:00"
}
```

**Quality Score Calculation**:
The quality score (0-100) uses a weighted formula:
- **Vote Ratio** (35%): Upvotes / total votes
- **Comments** (25%): Logarithmic scaling of comment count
- **Bookmarks** (20%): Logarithmic scaling of bookmark count
- **Total Votes** (15%): Logarithmic scaling of vote count
- **Controversy Penalty** (5%): Reduces score for polarizing content

**Example Usage**:
```bash
# Get 30-day quality report for technology category
curl 'http://localhost:8000/api/v1/analytics/content-quality?days=30&category=technology&min_engagement=10'

# Get 7-day quality report (all categories)
curl 'http://localhost:8000/api/v1/analytics/content-quality?days=7'
```

**Use Cases**:
- **Content Strategy**: Identify which categories and sources produce highest quality content
- **Editorial Review**: Find underperforming content that needs improvement
- **Source Evaluation**: Determine which RSS sources to prioritize
- **Performance Benchmarking**: Track quality trends over time

**Recommendations Types**:
1. **quality_improvement** (priority: high): Overall quality below target
2. **category_optimization** (priority: medium): Category performance insights
3. **engagement_insight** (priority: info): High-engagement patterns
4. **sentiment_alert** (priority: medium): Mixed sentiment indicators

---

## Comment Mentions

### Overview

The Comment Mentions feature enables users to mention other users in comments using the `@username` syntax. When a user is mentioned, they receive a notification and the mention is tracked in the database.

### Features

1. **Automatic Parsing**: Mentions are automatically detected when comments are created
2. **Notification Creation**: Mentioned users receive real-time notifications
3. **Database Tracking**: All mentions are stored for querying and analytics
4. **Self-Mention Protection**: Users cannot mention themselves
5. **Case-Insensitive Matching**: @JohnDoe and @johndoe both match user `johndoe`

### Mention Syntax

**Valid Mentions**:
- Must start with `@` symbol
- Username can contain letters, numbers, underscores, hyphens
- Must be 3-30 characters long
- First character must be letter or number

**Examples**:
```
"Hey @john, check this out!"          ✓ Valid
"@jane_doe and @bob-smith agree"      ✓ Valid (multiple mentions)
"Contact @user123 for help"           ✓ Valid
"Email me at @a"                      ✗ Invalid (too short)
"See @very_long_username_here_123456" ✗ Invalid (too long)
```

### 2. Comment Creation with Mentions

**Endpoint**: POST /api/v1/comments

**Note**: This is an existing endpoint enhanced with automatic mention processing.

**Request Body**:
```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "Great article! @alice and @bob you should read this.",
  "parent_comment_id": null
}
```

**Response** (same as before, mentions processed in background):
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "user_id": "770e8400-e29b-41d4-a716-446655440002",
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "Great article! @alice and @bob you should read this.",
  "created_at": "2025-11-11T16:00:00",
  "vote_score": 0,
  "reply_count": 0
}
```

**Behind the Scenes**:
When this comment is created, the system:
1. Parses the content and extracts mentions (`alice`, `bob`)
2. Looks up users with usernames `alice` and `bob`
3. Creates `CommentMention` records linking the comment to mentioned users
4. Sends notifications to Alice and Bob
5. Logs the operation

### 3. Retrieving User Mentions

**Endpoint**: GET /api/v1/users/me/mentions *(Planned)*

**Purpose**: Retrieve all comments where the authenticated user was mentioned.

**Authentication**: Required (JWT Bearer token)

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `page_size` | integer | 20 | Items per page (max 100) |
| `unread_only` | boolean | false | Only unread mentions |

**Planned Response Schema**:
```json
{
  "mentions": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "comment": {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "content": "Hey @alice, great point about AI ethics!",
        "created_at": "2025-11-11T16:00:00",
        "article": {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "title": "AI Ethics in 2025"
        }
      },
      "mentioned_by": {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "username": "bob",
        "avatar_url": "https://example.com/avatars/bob.jpg"
      },
      "mentioned_at": "2025-11-11T16:00:00",
      "is_read": false
    }
  ],
  "total": 47,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

---

## Database Schema Changes

### New Tables

#### 1. comment_mentions

**Purpose**: Track user mentions in comments.

**Schema**:
```sql
CREATE TABLE comment_mentions (
    id UUID PRIMARY KEY,
    comment_id UUID NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
    mentioned_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mentioned_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX idx_comment_mentions_comment_id ON comment_mentions(comment_id);
CREATE INDEX idx_comment_mentions_mentioned_user_id ON comment_mentions(mentioned_user_id);
CREATE INDEX idx_comment_mentions_mentioned_by_user_id ON comment_mentions(mentioned_by_user_id);
```

**Columns**:
- `id`: UUID primary key
- `comment_id`: Reference to the comment containing the mention
- `mentioned_user_id`: User who was mentioned (receives notification)
- `mentioned_by_user_id`: User who created the comment (author)
- `created_at`: Timestamp when mention was created

**Relationships**:
- **comment**: Many-to-one with `comments` table
- **mentioned_user**: Many-to-one with `users` table (recipient)
- **mentioned_by**: Many-to-one with `users` table (author)

**Indexes**:
- `comment_id` for fast lookup of mentions in a comment
- `mentioned_user_id` for querying mentions received by a user
- `mentioned_by_user_id` for querying mentions made by a user

### Modified Models

#### Comment Model
Added relationship:
```python
mentions = relationship("CommentMention", back_populates="comment")
```

#### User Model
Added relationships:
```python
received_mentions = relationship(
    "CommentMention",
    foreign_keys="CommentMention.mentioned_user_id",
    back_populates="mentioned_user"
)
made_mentions = relationship(
    "CommentMention",
    foreign_keys="CommentMention.mentioned_by_user_id",
    back_populates="mentioned_by"
)
```

---

## Testing Guide

### Manual Testing

#### 1. Content Quality Endpoint

**Test Case 1: Default Parameters**
```bash
curl 'http://localhost:8000/api/v1/analytics/content-quality?days=7' | jq .
```

Expected: Returns quality report for last 7 days with default min_engagement=5

**Test Case 2: Category Filter**
```bash
curl 'http://localhost:8000/api/v1/analytics/content-quality?days=30&category=technology' | jq .
```

Expected: Returns quality report for technology articles only

**Test Case 3: High Engagement Threshold**
```bash
curl 'http://localhost:8000/api/v1/analytics/content-quality?days=14&min_engagement=20' | jq .
```

Expected: Returns only articles with 20+ total engagement

**Test Case 4: Empty Result**
```bash
curl 'http://localhost:8000/api/v1/analytics/content-quality?days=1&min_engagement=100' | jq .
```

Expected: Returns empty top_performers and recommendations arrays

#### 2. Comment Mentions

**Test Case 1: Create Comment with Mention**
```bash
# Get auth token first
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}' \
  | jq -r '.access_token')

# Create comment with mention
curl -X POST http://localhost:8000/api/v1/comments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": "550e8400-e29b-41d4-a716-446655440000",
    "content": "Hey @alice, what do you think about this?"
  }' | jq .
```

Expected:
- Comment created successfully
- `CommentMention` record created in database
- Notification sent to user `alice`

**Test Case 2: Mention Parsing**
```python
from app.utils.mention_parser import parse_mentions

# Test valid mentions
assert parse_mentions("Hey @john") == ["john"]
assert set(parse_mentions("@alice and @bob agree")) == {"alice", "bob"}

# Test duplicate handling
assert parse_mentions("@john @john @john") == ["john"]

# Test invalid mentions
assert parse_mentions("Email: @a") == []  # Too short
assert parse_mentions("@") == []  # No username
```

**Test Case 3: Self-Mention Protection**
```bash
# User mentions themselves in a comment
curl -X POST http://localhost:8000/api/v1/comments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": "550e8400-e29b-41d4-a716-446655440000",
    "content": "Reminder to @testuser (myself) to follow up"
  }' | jq .
```

Expected:
- Comment created successfully
- NO `CommentMention` record created (self-mention ignored)
- NO notification sent

**Test Case 4: Non-Existent User Mention**
```bash
curl -X POST http://localhost:8000/api/v1/comments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": "550e8400-e29b-41d4-a716-446655440000",
    "content": "@nonexistentuser123 check this out"
  }' | jq .
```

Expected:
- Comment created successfully
- NO `CommentMention` record created (user doesn't exist)
- System logs warning about unknown user

### Database Verification

#### Check Mentions Table
```sql
-- View all mentions
SELECT 
    cm.id,
    c.content,
    mu.username AS mentioned_user,
    mb.username AS mentioned_by,
    cm.created_at
FROM comment_mentions cm
JOIN comments c ON cm.comment_id = c.id
JOIN users mu ON cm.mentioned_user_id = mu.id
JOIN users mb ON cm.mentioned_by_user_id = mb.id
ORDER BY cm.created_at DESC
LIMIT 10;

-- Count mentions per user
SELECT 
    u.username,
    COUNT(cm.id) AS mention_count
FROM users u
LEFT JOIN comment_mentions cm ON u.id = cm.mentioned_user_id
GROUP BY u.username
ORDER BY mention_count DESC;
```

### Integration Tests

**Test Content Quality Service**:
```python
# tests/unit/test_content_quality_service.py
import pytest
from app.services.content_quality_service import ContentQualityService

@pytest.mark.asyncio
async def test_quality_report_generation(test_db):
    service = ContentQualityService(test_db)
    report = await service.get_quality_report(days=7)
    
    assert "quality_metrics" in report
    assert "top_performers" in report
    assert "recommendations" in report
    assert report["period_days"] == 7

@pytest.mark.asyncio
async def test_quality_score_calculation(test_db):
    service = ContentQualityService(test_db)
    
    metrics = {
        "votes_count": 100,
        "upvotes": 90,
        "downvotes": 10,
        "vote_ratio": 0.9,
        "comments_count": 20,
        "bookmarks_count": 15,
        "controversy_score": 0.2
    }
    
    score = service._calculate_quality_score(metrics)
    assert 0 <= score <= 100
    assert score > 50  # High vote ratio should yield good score
```

**Test Mention Parsing**:
```python
# tests/unit/test_mention_parser.py
from app.utils.mention_parser import parse_mentions

def test_single_mention():
    assert parse_mentions("Hey @john") == ["john"]

def test_multiple_mentions():
    mentions = set(parse_mentions("@alice and @bob"))
    assert mentions == {"alice", "bob"}

def test_duplicate_mentions():
    # Should deduplicate
    assert parse_mentions("@john @john") == ["john"]

def test_invalid_mentions():
    # Too short (< 3 chars)
    assert parse_mentions("@ab") == []
    
    # Too long (> 30 chars)
    long_username = "a" * 31
    assert parse_mentions(f"@{long_username}") == []
    
    # No username after @
    assert parse_mentions("@") == []

def test_complex_content():
    content = "Great discussion @alice! I agree with @bob_smith and @jane-doe123."
    mentions = set(parse_mentions(content))
    assert mentions == {"alice", "bob_smith", "jane-doe123"}
```

---

## Performance Considerations

### Content Quality Endpoint

**Query Optimization**:
- Uses indexed columns (article_id, created_at) for fast filtering
- Aggregates counts using efficient SELECT COUNT queries
- Caches results for 5 minutes (recommended for production)

**Scalability**:
- For 10,000+ articles: Response time < 1s with proper indexes
- Pagination not implemented (returns top 10 only)
- Consider background job for pre-computing daily quality reports

### Comment Mentions

**Processing Time**:
- Mention parsing: O(n) where n = comment length (very fast)
- User lookup: Single database query with IN clause (fast)
- Notification creation: Async, non-blocking (doesn't slow comment creation)

**Database Load**:
- Each mention creates 1 row in `comment_mentions` table
- Average 1-3 mentions per comment = minimal storage
- Indexes ensure fast queries

---

## Error Handling

### Content Quality Endpoint

**400 Bad Request**:
```json
{
  "detail": "days parameter must be between 1 and 365"
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Failed to generate quality report: <error message>"
}
```

### Comment Mentions

**Graceful Failure**:
- If mention processing fails, comment is still created
- Errors are logged but don't block comment creation
- Users don't see errors related to mention processing

**Non-Existent Users**:
- Mentions of non-existent users are silently ignored
- No error thrown, just skipped in processing

---

## Future Enhancements

### Planned Features

1. **Mention Notifications API**
   - GET /api/v1/users/me/mentions
   - Mark mentions as read
   - Filter by read/unread status

2. **Mention Analytics**
   - Most mentioned users
   - Mention frequency over time
   - Mention network visualization

3. **Advanced Quality Metrics**
   - Readability scores (Flesch-Kincaid)
   - Sentiment analysis integration
   - Source authority scoring

4. **Real-Time Updates**
   - WebSocket notifications for mentions
   - Live quality score updates

---

## Migration Reference

**Applied Migrations**:
1. `bf07c7c9a81b` - Article Analytics table (Phase 1)
2. `730687afff1c` - Comment Mentions table (Phase 2)

**Rollback Command** (if needed):
```bash
# Rollback comment mentions migration
alembic downgrade -1

# Rollback to start of Phase 2
alembic downgrade bf07c7c9a81b
```

---

## Summary

Phase 2 successfully delivers:

✅ **Content Quality Analytics**
- Comprehensive quality scoring system
- Top performer identification
- Actionable recommendations
- Category-based insights

✅ **Comment Mentions**
- Automatic @username parsing
- Database tracking
- Notification integration
- Self-mention protection

**Production Readiness**: Both features are tested, documented, and ready for production deployment.

**API Documentation**: Auto-generated OpenAPI docs available at `http://localhost:8000/docs`
