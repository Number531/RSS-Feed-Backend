# API Quick Reference Cheat Sheet

> **RSS Feed Backend API - Quick Reference**  
> Base URL: `/api/v1`  
> All timestamps in ISO 8601 UTC format

---

## 🔐 Authentication

**All authenticated endpoints require:**
```http
Authorization: Bearer <access_token>
```

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/register` | POST | ❌ | Create new user account |
| `/auth/login` | POST | ❌ | Login and get JWT tokens |
| `/auth/refresh` | POST | ❌ | Refresh access token |

**Token Lifecycle:**
- Access Token: 30 min
- Refresh Token: 7 days

---

## 👤 User Management

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/users/me` | GET | ✅ | Get current user profile |
| `/users/me` | PATCH | ✅ | Update user profile |
| `/users/me` | DELETE | ✅ | Delete user account (soft) |
| `/users/me/stats` | GET | ✅ | Get user statistics (501) |

---

## 📰 Articles

| Endpoint | Method | Auth | Description | Key Params |
|----------|--------|------|-------------|------------|
| `/articles` | GET | 🔓 | Get articles feed | `category`, `sort_by`, `time_range`, `page`, `page_size` |
| `/articles/search` | GET | 🔓 | Search articles | `q` (required), `page`, `page_size` |
| `/articles/{id}` | GET | 🔓 | Get single article | `article_id` (path) |

**Categories:** `general`, `politics`, `us`, `world`, `science`  
**Sort Options:** `hot` (default), `new`, `top`  
**Time Ranges:** `hour`, `day`, `week`, `month`, `year`, `all`

🔓 = Optional auth (adds `user_vote` to response)

---

## ⬆️⬇️ Votes

| Endpoint | Method | Auth | Description | Body/Params |
|----------|--------|------|-------------|-------------|
| `/votes` | POST | ✅ | Cast/update vote | `{ article_id, vote_value }` |
| `/votes/{article_id}` | DELETE | ✅ | Remove vote | - |
| `/votes/article/{article_id}` | GET | ✅ | Get user's vote | - |

**Vote Values:** `1` (upvote), `-1` (downvote), `0` (remove)

---

## 💬 Comments

### Comment CRUD

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/comments` | POST | ✅ | Create comment/reply |
| `/comments/article/{id}` | GET | ❌ | Get article comments (paginated) |
| `/comments/article/{id}/tree` | GET | ❌ | Get nested comment tree |
| `/comments/{id}` | GET | ❌ | Get single comment |
| `/comments/{id}/replies` | GET | ❌ | Get comment replies |
| `/comments/{id}` | PUT | ✅ | Update comment (author only) |
| `/comments/{id}` | DELETE | ✅ | Delete comment (author only) |

### Comment Voting

| Endpoint | Method | Auth | Description | Query Params |
|----------|--------|------|-------------|--------------|
| `/comments/{id}/vote` | POST | ✅ | Vote on comment | `vote_type=upvote|downvote` |
| `/comments/{id}/vote` | DELETE | ✅ | Remove vote | - |
| `/comments/{id}/vote` | GET | ✅ | Get user's vote | - |
| `/comments/{id}/vote/summary` | GET | ❌ | Get vote summary | - |

---

## 🔖 Bookmarks

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/bookmarks` | POST | ✅ | Create bookmark |
| `/bookmarks` | GET | ✅ | List bookmarks (paginated) |
| `/bookmarks/collections` | GET | ✅ | List collection names |
| `/bookmarks/check/{article_id}` | GET | ✅ | Check if bookmarked |
| `/bookmarks/{id}` | GET | ✅ | Get bookmark by ID |
| `/bookmarks/{id}` | PATCH | ✅ | Update bookmark |
| `/bookmarks/{id}` | DELETE | ✅ | Delete bookmark |
| `/bookmarks/article/{article_id}` | DELETE | ✅ | Delete by article ID |

**Collections:** Custom string labels (e.g., "Read Later", "Tech News")

---

## 📖 Reading History

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/reading-history` | POST | ✅ | Record article view |
| `/reading-history` | GET | ✅ | Get reading history |
| `/reading-history/recent` | GET | ✅ | Get recently read articles |
| `/reading-history/stats` | GET | ✅ | Get reading statistics |
| `/reading-history` | DELETE | ✅ | Clear history |
| `/reading-history/export` | GET | ✅ | Export history (JSON/CSV) |
| `/reading-history/preferences` | GET | ✅ | Get tracking preferences |
| `/reading-history/preferences` | PUT | ✅ | Update preferences |

**Tracking Metrics:** `duration_seconds`, `scroll_percentage`

---

## 🔔 Notifications

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/notifications` | GET | ✅ | List notifications |
| `/notifications/stats` | GET | ✅ | Get notification stats |
| `/notifications/unread-count` | GET | ✅ | Get unread count (lightweight) |
| `/notifications/preferences` | GET | ✅ | Get preferences |
| `/notifications/preferences` | PUT | ✅ | Update preferences |
| `/notifications/{id}` | GET | ✅ | Get single notification |
| `/notifications/mark-read` | POST | ✅ | Mark notifications as read |
| `/notifications/mark-all-read` | POST | ✅ | Mark all as read |
| `/notifications/{id}` | DELETE | ✅ | Delete notification |

**Notification Types:** `vote`, `reply`, `mention`

---

## 🚨 HTTP Status Codes

| Code | Meaning | Use Case |
|------|---------|----------|
| 200 | OK | Successful GET, PUT, PATCH, POST |
| 201 | Created | Resource created successfully |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing/invalid auth token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource (e.g., email) |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 501 | Not Implemented | Planned but not available |

---

## 🔄 Common Patterns

### Pagination

**Query Parameters:**
```typescript
page: number = 1          // Page number (1-indexed)
page_size: number = 25    // Items per page (max: 100)
```

**Response Format:**
```json
{
  "items": [...],
  "total": 500,
  "page": 1,
  "page_size": 25,
  "has_next": true,
  "has_prev": false
}
```

### Error Response

```json
{
  "detail": "Error message here"
}
```

### UUID Format

All IDs are UUIDs (v4):
```
550e8400-e29b-41d4-a716-446655440000
```

---

## 💡 Quick Tips

### Token Refresh Pattern
```typescript
// Check token expiry
if (tokenExpiresAt < Date.now() + 5*60*1000) {
  await refreshToken();
}
```

### Optional Authentication
Some endpoints work without auth but provide extra data when authenticated:
- Articles endpoints include `user_vote` field
- Comment voting available only when authenticated

### Soft Deletes
- User accounts: Marked inactive, data retained
- Comments: Content replaced with "[deleted]", structure preserved

### Rate Limiting
- Auth endpoints: 5 req/min per IP
- General: 100 req/min per IP
- Heavy (search/feed): 30 req/min per user

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1706367600
```

---

## 🎯 Common Request Examples

### Login
```bash
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

### Get Articles Feed
```bash
GET /api/v1/articles?category=politics&sort_by=hot&page=1&page_size=25
Authorization: Bearer <token>  # Optional
```

### Cast Vote
```bash
POST /api/v1/votes
Authorization: Bearer <token>
{
  "article_id": "550e8400-...",
  "vote_value": 1
}
```

### Create Comment
```bash
POST /api/v1/comments
Authorization: Bearer <token>
{
  "article_id": "550e8400-...",
  "content": "Great article!",
  "parent_comment_id": null  # Optional for replies
}
```

### Create Bookmark
```bash
POST /api/v1/bookmarks
Authorization: Bearer <token>
{
  "article_id": "550e8400-...",
  "collection": "Read Later",
  "notes": "Want to read this later"
}
```

### Check Unread Notifications
```bash
GET /api/v1/notifications/unread-count
Authorization: Bearer <token>
```

---

## 📚 Interactive Documentation

For detailed interactive API docs, visit:
- **Development:** http://localhost:8000/docs
- **Production:** https://your-domain.com/docs

---

**Version:** 1.0  
**Last Updated:** 2025-01-27
