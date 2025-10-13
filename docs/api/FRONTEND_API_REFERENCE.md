# Frontend API Reference

> **Complete API Documentation for RSS Feed Backend**  
> Version: 1.0  
> Last Updated: 2025-01-27

This document provides a comprehensive reference for all API endpoints available in the RSS Feed backend. Use this as your primary reference when building the frontend application.

---

## Table of Contents

1. [Base URL & Authentication](#base-url--authentication)
2. [Authentication Endpoints](#authentication-endpoints)
3. [User Management Endpoints](#user-management-endpoints)
4. [Articles Endpoints](#articles-endpoints)
5. [Votes Endpoints](#votes-endpoints)
6. [Comments Endpoints](#comments-endpoints)
7. [Bookmarks Endpoints](#bookmarks-endpoints)
8. [Reading History Endpoints](#reading-history-endpoints)
9. [Notifications Endpoints](#notifications-endpoints)
10. [Error Handling](#error-handling)
11. [Rate Limiting](#rate-limiting)

---

## Base URL & Authentication

### Base URL
```
Production: https://your-domain.com/api/v1
Development: http://localhost:8000/api/v1
```

### Authentication

Most endpoints require JWT authentication. Include the access token in the Authorization header:

```http
Authorization: Bearer <access_token>
```

### Token Lifecycle
- **Access Token**: Expires in 30 minutes (default)
- **Refresh Token**: Expires in 7 days (default)
- Use the `/auth/refresh` endpoint to obtain a new access token

---

## Authentication Endpoints

### Register User

**POST** `/auth/register`

Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "avatar_url": "https://example.com/avatar.jpg"  // Optional
}
```

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "avatar_url": "https://example.com/avatar.jpg",
  "is_active": true,
  "is_verified": false,
  "oauth_provider": null,
  "created_at": "2025-01-01T00:00:00Z",
  "last_login_at": null
}
```

**Errors:**
- `400 Bad Request`: Email or username already exists
- `422 Unprocessable Entity`: Validation error (weak password, invalid email, etc.)

---

### Login

**POST** `/auth/login`

Authenticate user and receive JWT tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors:**
- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: Account is inactive

**Frontend Usage:**
```typescript
// Store tokens securely
localStorage.setItem('access_token', response.access_token);
localStorage.setItem('refresh_token', response.refresh_token);

// Set token expiry
const expiresAt = Date.now() + response.expires_in * 1000;
localStorage.setItem('token_expires_at', expiresAt.toString());
```

---

### Refresh Token

**POST** `/auth/refresh`

Get new access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors:**
- `401 Unauthorized`: Invalid or expired refresh token

**Frontend Usage:**
```typescript
// Check if token is about to expire
const tokenExpiresAt = parseInt(localStorage.getItem('token_expires_at'));
const fiveMinutesFromNow = Date.now() + 5 * 60 * 1000;

if (tokenExpiresAt < fiveMinutesFromNow) {
  // Refresh token
  const refreshToken = localStorage.getItem('refresh_token');
  const response = await refreshAccessToken(refreshToken);
  // Update stored tokens
}
```

---

## User Management Endpoints

### Get Current User Profile

**GET** `/users/me`

Get authenticated user's profile.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "avatar_url": "https://example.com/avatar.jpg",
  "is_active": true,
  "is_verified": true,
  "oauth_provider": null,
  "created_at": "2025-01-01T00:00:00Z",
  "last_login_at": "2025-01-10T12:00:00Z"
}
```

---

### Update User Profile

**PATCH** `/users/me`

Update current user's profile. All fields are optional.

**Authentication:** Required

**Request Body:**
```json
{
  "email": "newemail@example.com",        // Optional
  "username": "newusername",              // Optional (3-50 chars)
  "full_name": "John Smith",              // Optional (max 255 chars)
  "avatar_url": "https://example.com/new-avatar.jpg",  // Optional
  "password": "NewSecurePass123!"         // Optional (min 8 chars)
}
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "newemail@example.com",
  "username": "newusername",
  "full_name": "John Smith",
  "avatar_url": "https://example.com/new-avatar.jpg",
  "is_active": true,
  "is_verified": true,
  "oauth_provider": null,
  "created_at": "2025-01-01T00:00:00Z",
  "last_login_at": "2025-01-10T12:00:00Z"
}
```

**Errors:**
- `409 Conflict`: Email or username already taken
- `422 Validation Error`: Invalid data format

**Notes:**
- Only provided fields will be updated
- Password is securely hashed before storage
- Email and username uniqueness is validated

---

### Delete User Account

**DELETE** `/users/me`

Soft delete current user's account.

**Authentication:** Required

**Response:** `204 No Content`

**Notes:**
- Account is marked as **inactive** (soft delete)
- User data is retained but account is inaccessible
- User votes and comments remain but are anonymized
- JWT tokens become invalid after deletion
- For permanent deletion, contact support

---

### Get User Statistics

**GET** `/users/me/stats`

Get current user's activity statistics.

**Authentication:** Required

**Response:** `501 Not Implemented`

**Note:** This endpoint is planned but not yet implemented. Will include:
- Total votes cast
- Total comments made
- Account age
- Karma score (upvotes received)

---

## Articles Endpoints

### Get Articles Feed

**GET** `/articles`

Get paginated articles feed with filtering and sorting.

**Authentication:** Optional (includes vote status if authenticated)

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `category` | string | No | null | Filter by category: `general`, `politics`, `us`, `world`, `science` |
| `sort_by` | string | No | `hot` | Sort order: `hot`, `new`, `top` |
| `time_range` | string | No | null | Time filter: `hour`, `day`, `week`, `month`, `year`, `all` |
| `page` | integer | No | 1 | Page number (min: 1) |
| `page_size` | integer | No | 25 | Items per page (min: 1, max: 100) |

**Sorting Algorithms:**
- **`hot`**: Trending algorithm based on votes and recency
- **`new`**: Most recent articles first
- **`top`**: Highest voted articles first (requires `time_range`)

**Example Request:**
```http
GET /api/v1/articles?category=politics&sort_by=hot&page=1&page_size=25
```

**Response:** `200 OK`
```json
{
  "articles": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "rss_source_id": "650e8400-e29b-41d4-a716-446655440001",
      "title": "Breaking News: Major Event Occurs",
      "url": "https://example.com/article",
      "description": "Article summary...",
      "author": "Jane Reporter",
      "thumbnail_url": "https://example.com/thumbnail.jpg",
      "category": "politics",
      "published_date": "2025-01-27T10:00:00Z",
      "created_at": "2025-01-27T10:05:00Z",
      "vote_score": 42,
      "vote_count": 50,
      "comment_count": 15,
      "tags": ["politics", "election"],
      "user_vote": 1  // Only if authenticated: 1 (upvote), -1 (downvote), null (no vote)
    }
  ],
  "total": 500,
  "page": 1,
  "page_size": 25,
  "has_next": true,
  "has_prev": false
}
```

**Frontend Usage:**
```typescript
// Build query string
const params = new URLSearchParams({
  category: selectedCategory,
  sort_by: sortBy,
  page: currentPage.toString(),
  page_size: '25'
});

const response = await fetch(`/api/v1/articles?${params}`, {
  headers: {
    // Include auth header if user is logged in
    ...(accessToken && { 'Authorization': `Bearer ${accessToken}` })
  }
});
```

---

### Search Articles

**GET** `/articles/search`

Search articles using full-text search.

**Authentication:** Optional

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | **Yes** | Search query (1-200 characters) |
| `page` | integer | No | Page number (default: 1, min: 1) |
| `page_size` | integer | No | Items per page (default: 25, min: 1, max: 100) |

**Search Algorithm:**
- Searches through article titles and descriptions
- Uses PostgreSQL full-text search (TSVECTOR)
- Results ordered by relevance and recency

**Example Request:**
```http
GET /api/v1/articles/search?q=artificial+intelligence&page=1
```

**Response:** `200 OK`
```json
{
  "articles": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "rss_source_id": "650e8400-e29b-41d4-a716-446655440001",
      "title": "AI Breakthrough in Natural Language",
      "url": "https://example.com/ai-article",
      "description": "Researchers announce...",
      "author": "Tech Reporter",
      "thumbnail_url": "https://example.com/thumb.jpg",
      "category": "science",
      "published_date": "2025-01-27T09:00:00Z",
      "created_at": "2025-01-27T09:05:00Z",
      "vote_score": 120,
      "vote_count": 130,
      "comment_count": 45,
      "tags": ["AI", "science"],
      "user_vote": null
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 25,
  "has_next": true,
  "has_prev": false
}
```

---

### Get Single Article

**GET** `/articles/{article_id}`

Get detailed information about a specific article.

**Authentication:** Optional (includes vote status if authenticated)

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `article_id` | UUID | Article identifier |

**Example Request:**
```http
GET /api/v1/articles/550e8400-e29b-41d4-a716-446655440000
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "rss_source_id": "650e8400-e29b-41d4-a716-446655440001",
  "title": "Article Title",
  "url": "https://example.com/article",
  "description": "Full article description...",
  "author": "Author Name",
  "thumbnail_url": "https://example.com/thumbnail.jpg",
  "category": "politics",
  "published_date": "2025-01-27T10:00:00Z",
  "created_at": "2025-01-27T10:05:00Z",
  "vote_score": 42,
  "vote_count": 50,
  "comment_count": 15,
  "tags": ["politics", "election"],
  "user_vote": 1  // Only if authenticated
}
```

**Errors:**
- `404 Not Found`: Article does not exist

---

## Votes Endpoints

### Cast Vote on Article

**POST** `/votes`

Cast, update, or remove a vote on an article.

**Authentication:** Required

**Request Body:**
```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "vote_value": 1  // 1 (upvote), -1 (downvote), 0 (remove vote)
}
```

**Response:** `201 Created`
```json
{
  "id": "750e8400-e29b-41d4-a716-446655440000",
  "user_id": "650e8400-e29b-41d4-a716-446655440001",
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "vote_value": 1,
  "created_at": "2025-01-27T12:00:00Z",
  "updated_at": "2025-01-27T12:00:00Z"
}
```

**Note:** Returns `null` if `vote_value` is 0 (vote removed)

**Behavior:**
- First vote: Creates new vote
- Same vote again: Updates vote
- vote_value = 0: Removes vote (returns null)

---

### Remove Vote from Article

**DELETE** `/votes/{article_id}`

Remove user's vote from an article.

**Authentication:** Required

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `article_id` | UUID | Article identifier |

**Response:** `204 No Content`

**Errors:**
- `404 Not Found`: No vote exists for this article

---

### Get User's Vote on Article

**GET** `/votes/article/{article_id}`

Get current user's vote on an article.

**Authentication:** Required

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `article_id` | UUID | Article identifier |

**Response:** `200 OK`
```json
{
  "id": "750e8400-e29b-41d4-a716-446655440000",
  "user_id": "650e8400-e29b-41d4-a716-446655440001",
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "vote_value": 1,
  "created_at": "2025-01-27T12:00:00Z",
  "updated_at": "2025-01-27T12:00:00Z"
}
```

**Note:** Returns `null` if user hasn't voted on this article

---

## Comments Endpoints

### Create Comment

**POST** `/comments`

Create a new comment on an article or reply to an existing comment.

**Authentication:** Required

**Request Body:**
```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "This is my comment...",
  "parent_comment_id": "850e8400-e29b-41d4-a716-446655440000"  // Optional, for replies
}
```

**Response:** `201 Created`
```json
{
  "id": "950e8400-e29b-41d4-a716-446655440000",
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "650e8400-e29b-41d4-a716-446655440001",
  "parent_comment_id": null,
  "content": "This is my comment...",
  "vote_score": 0,
  "vote_count": 0,
  "is_deleted": false,
  "created_at": "2025-01-27T12:30:00Z",
  "updated_at": "2025-01-27T12:30:00Z"
}
```

**Validation:**
- Content: 1-10,000 characters
- If `parent_comment_id` provided, it must exist and belong to the same article

---

### Get Article Comments

**GET** `/comments/article/{article_id}`

Get top-level comments for an article (paginated).

**Authentication:** Not required

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `article_id` | UUID | Article identifier |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (min: 1) |
| `page_size` | integer | 50 | Items per page (min: 1, max: 100) |

**Response:** `200 OK`
```json
[
  {
    "id": "950e8400-e29b-41d4-a716-446655440000",
    "article_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "650e8400-e29b-41d4-a716-446655440001",
    "parent_comment_id": null,
    "content": "Top-level comment",
    "vote_score": 5,
    "vote_count": 7,
    "is_deleted": false,
    "created_at": "2025-01-27T12:30:00Z",
    "updated_at": "2025-01-27T12:30:00Z"
  }
]
```

**Note:** Returns only top-level comments. Use comment tree endpoint or replies endpoint for nested comments.

---

### Get Comment Tree

**GET** `/comments/article/{article_id}/tree`

Get nested comment tree for an article (all comments with replies).

**Authentication:** Not required

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `article_id` | UUID | Article identifier |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_depth` | integer | 10 | Maximum nesting depth (min: 1, max: 20) |

**Response:** `200 OK`
```json
[
  {
    "id": "950e8400-e29b-41d4-a716-446655440000",
    "article_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "650e8400-e29b-41d4-a716-446655440001",
    "parent_comment_id": null,
    "content": "Top-level comment",
    "vote_score": 5,
    "vote_count": 7,
    "is_deleted": false,
    "created_at": "2025-01-27T12:30:00Z",
    "updated_at": "2025-01-27T12:30:00Z",
    "replies": [
      {
        "id": "960e8400-e29b-41d4-a716-446655440001",
        "article_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": "660e8400-e29b-41d4-a716-446655440002",
        "parent_comment_id": "950e8400-e29b-41d4-a716-446655440000",
        "content": "Reply to top-level",
        "vote_score": 2,
        "vote_count": 2,
        "is_deleted": false,
        "created_at": "2025-01-27T12:35:00Z",
        "updated_at": "2025-01-27T12:35:00Z",
        "replies": []
      }
    ]
  }
]
```

**Use Case:** Display threaded comment discussions with full nesting

---

### Get Single Comment

**GET** `/comments/{comment_id}`

Get a specific comment by ID.

**Authentication:** Not required

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `comment_id` | UUID | Comment identifier |

**Response:** `200 OK`
```json
{
  "id": "950e8400-e29b-41d4-a716-446655440000",
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "650e8400-e29b-41d4-a716-446655440001",
  "parent_comment_id": null,
  "content": "This is my comment...",
  "vote_score": 5,
  "vote_count": 7,
  "is_deleted": false,
  "created_at": "2025-01-27T12:30:00Z",
  "updated_at": "2025-01-27T12:30:00Z"
}
```

**Errors:**
- `404 Not Found`: Comment does not exist

---

### Get Comment Replies

**GET** `/comments/{comment_id}/replies`

Get direct replies to a comment (not nested).

**Authentication:** Not required

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `comment_id` | UUID | Parent comment identifier |

**Response:** `200 OK`
```json
[
  {
    "id": "960e8400-e29b-41d4-a716-446655440001",
    "article_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "660e8400-e29b-41d4-a716-446655440002",
    "parent_comment_id": "950e8400-e29b-41d4-a716-446655440000",
    "content": "Reply to comment",
    "vote_score": 2,
    "vote_count": 2,
    "is_deleted": false,
    "created_at": "2025-01-27T12:35:00Z",
    "updated_at": "2025-01-27T12:35:00Z"
  }
]
```

---

### Update Comment

**PUT** `/comments/{comment_id}`

Update a comment's content.

**Authentication:** Required (must be comment author)

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `comment_id` | UUID | Comment identifier |

**Request Body:**
```json
{
  "content": "Updated comment text..."
}
```

**Response:** `200 OK`
```json
{
  "id": "950e8400-e29b-41d4-a716-446655440000",
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "650e8400-e29b-41d4-a716-446655440001",
  "parent_comment_id": null,
  "content": "Updated comment text...",
  "vote_score": 5,
  "vote_count": 7,
  "is_deleted": false,
  "created_at": "2025-01-27T12:30:00Z",
  "updated_at": "2025-01-27T13:00:00Z"
}
```

**Errors:**
- `403 Forbidden`: User is not the comment author
- `404 Not Found`: Comment does not exist

---

### Delete Comment

**DELETE** `/comments/{comment_id}`

Soft delete a comment.

**Authentication:** Required (must be comment author)

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `comment_id` | UUID | Comment identifier |

**Response:** `204 No Content`

**Behavior:**
- Soft delete (marks as deleted)
- Content replaced with "[deleted]"
- Thread structure preserved

**Errors:**
- `403 Forbidden`: User is not the comment author
- `404 Not Found`: Comment does not exist

---

### Vote on Comment

**POST** `/comments/{comment_id}/vote?vote_type={upvote|downvote}`

Cast or toggle a vote on a comment.

**Authentication:** Required

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `comment_id` | UUID | Comment identifier |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `vote_type` | string | **Yes** | `upvote` or `downvote` |

**Behavior:**
- First vote: Creates the vote
- Same vote again: Removes the vote (toggle off)
- Different vote: Changes the vote type

**Response:** `200 OK`
```json
{
  "voted": true,
  "vote_type": "upvote",
  "vote_score": 6,
  "vote_count": 8
}
```

---

### Remove Comment Vote

**DELETE** `/comments/{comment_id}/vote`

Remove user's vote from a comment.

**Authentication:** Required

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `comment_id` | UUID | Comment identifier |

**Response:** `200 OK`
```json
{
  "removed": true,
  "vote_score": 5,
  "vote_count": 7
}
```

---

### Get User's Comment Vote

**GET** `/comments/{comment_id}/vote`

Get user's current vote on a comment.

**Authentication:** Required

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `comment_id` | UUID | Comment identifier |

**Response:** `200 OK`
```json
{
  "voted": true,
  "vote_type": "upvote",
  "vote_value": 1
}
```

**When no vote exists:**
```json
{
  "voted": false,
  "vote_type": null,
  "vote_value": 0
}
```

---

### Get Comment Vote Summary

**GET** `/comments/{comment_id}/vote/summary`

Get vote summary for a comment (public endpoint).

**Authentication:** Not required

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `comment_id` | UUID | Comment identifier |

**Response:** `200 OK`
```json
{
  "comment_id": "950e8400-e29b-41d4-a716-446655440000",
  "vote_score": 5,
  "vote_count": 7
}
```

---

## Bookmarks Endpoints

### Create Bookmark

**POST** `/bookmarks`

Save an article for later reading.

**Authentication:** Required

**Request Body:**
```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "collection": "Read Later",  // Optional, default collection name
  "notes": "Want to read this in detail"  // Optional
}
```

**Response:** `201 Created`
```json
{
  "id": "a50e8400-e29b-41d4-a716-446655440000",
  "user_id": "650e8400-e29b-41d4-a716-446655440001",
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "collection": "Read Later",
  "notes": "Want to read this in detail",
  "created_at": "2025-01-27T14:00:00Z",
  "updated_at": "2025-01-27T14:00:00Z"
}
```

---

### List Bookmarks

**GET** `/bookmarks`

Get all bookmarks for the current user with pagination.

**Authentication:** Required

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `collection` | string | null | Filter by collection name |
| `page` | integer | 1 | Page number (min: 1) |
| `page_size` | integer | 25 | Items per page (min: 1, max: 100) |

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "a50e8400-e29b-41d4-a716-446655440000",
      "user_id": "650e8400-e29b-41d4-a716-446655440001",
      "article_id": "550e8400-e29b-41d4-a716-446655440000",
      "collection": "Read Later",
      "notes": "Want to read this in detail",
      "created_at": "2025-01-27T14:00:00Z",
      "updated_at": "2025-01-27T14:00:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 25,
  "has_more": true
}
```

---

### List Collections

**GET** `/bookmarks/collections`

Get all bookmark collection names for the current user.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "collections": [
    "Read Later",
    "Tech News",
    "Research"
  ],
  "total": 3
}
```

---

### Check Bookmark Status

**GET** `/bookmarks/check/{article_id}`

Check if an article is bookmarked by the current user.

**Authentication:** Required

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `article_id` | UUID | Article identifier |

**Response:** `200 OK`
```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_bookmarked": true
}
```

---

### Get Bookmark

**GET** `/bookmarks/{bookmark_id}`

Get a specific bookmark by ID.

**Authentication:** Required

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `bookmark_id` | UUID | Bookmark identifier |

**Response:** `200 OK`
```json
{
  "id": "a50e8400-e29b-41d4-a716-446655440000",
  "user_id": "650e8400-e29b-41d4-a716-446655440001",
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "collection": "Read Later",
  "notes": "Want to read this in detail",
  "created_at": "2025-01-27T14:00:00Z",
  "updated_at": "2025-01-27T14:00:00Z"
}
```

**Errors:**
- `404 Not Found`: Bookmark not found or doesn't belong to user

---

### Update Bookmark

**PATCH** `/bookmarks/{bookmark_id}`

Update bookmark collection or notes.

**Authentication:** Required

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `bookmark_id` | UUID | Bookmark identifier |

**Request Body:**
```json
{
  "collection": "Important",  // Optional
  "notes": "Updated notes"    // Optional
}
```

**Response:** `200 OK`
```json
{
  "id": "a50e8400-e29b-41d4-a716-446655440000",
  "user_id": "650e8400-e29b-41d4-a716-446655440001",
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "collection": "Important",
  "notes": "Updated notes",
  "created_at": "2025-01-27T14:00:00Z",
  "updated_at": "2025-01-27T14:30:00Z"
}
```

**Errors:**
- `404 Not Found`: Bookmark not found or doesn't belong to user

---

### Delete Bookmark

**DELETE** `/bookmarks/{bookmark_id}`

Remove a bookmark by ID.

**Authentication:** Required

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `bookmark_id` | UUID | Bookmark identifier |

**Response:** `204 No Content`

**Errors:**
- `404 Not Found`: Bookmark not found or doesn't belong to user

---

### Delete Bookmark by Article

**DELETE** `/bookmarks/article/{article_id}`

Remove a bookmark by article ID (convenience endpoint).

**Authentication:** Required

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `article_id` | UUID | Article identifier |

**Response:** `204 No Content`

**Note:** Does nothing if article is not bookmarked (no error)

---

## Reading History Endpoints

### Record Article View

**POST** `/reading-history`

Record that the current user viewed an article with optional engagement metrics.

**Authentication:** Required

**Request Body:**
```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "duration_seconds": 120,    // Optional, time spent reading
  "scroll_percentage": 85     // Optional, how far user scrolled (0-100)
}
```

**Response:** `201 Created`
```json
{
  "id": "b50e8400-e29b-41d4-a716-446655440000",
  "user_id": "650e8400-e29b-41d4-a716-446655440001",
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "viewed_at": "2025-01-27T15:00:00Z",
  "duration_seconds": 120,
  "scroll_percentage": 85
}
```

**Frontend Usage:**
```typescript
// Track reading metrics
let startTime = Date.now();
let maxScroll = 0;

window.addEventListener('scroll', () => {
  const scrollPercentage = (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100;
  maxScroll = Math.max(maxScroll, scrollPercentage);
});

// When user leaves article
window.addEventListener('beforeunload', () => {
  const durationSeconds = Math.floor((Date.now() - startTime) / 1000);
  await recordArticleView(articleId, durationSeconds, maxScroll);
});
```

---

### Get Reading History

**GET** `/reading-history`

Get paginated reading history for the current user with optional date filtering.

**Authentication:** Required

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | integer | 0 | Number of records to skip |
| `limit` | integer | 20 | Maximum records to return (min: 1, max: 100) |
| `start_date` | datetime | null | Filter views after this date (ISO 8601) |
| `end_date` | datetime | null | Filter views before this date (ISO 8601) |

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "b50e8400-e29b-41d4-a716-446655440000",
      "user_id": "650e8400-e29b-41d4-a716-446655440001",
      "article_id": "550e8400-e29b-41d4-a716-446655440000",
      "viewed_at": "2025-01-27T15:00:00Z",
      "duration_seconds": 120,
      "scroll_percentage": 85,
      "article": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Article Title",
        "url": "https://example.com/article",
        "thumbnail_url": "https://example.com/thumb.jpg"
      }
    }
  ],
  "total": 156,
  "skip": 0,
  "limit": 20
}
```

---

### Get Recently Read Articles

**GET** `/reading-history/recent`

Get list of recently read articles for the current user.

**Authentication:** Required

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | integer | 7 | Number of days to look back (min: 1, max: 365) |
| `limit` | integer | 10 | Maximum articles to return (min: 1, max: 50) |

**Response:** `200 OK`
```json
[
  {
    "id": "b50e8400-e29b-41d4-a716-446655440000",
    "user_id": "650e8400-e29b-41d4-a716-446655440001",
    "article_id": "550e8400-e29b-41d4-a716-446655440000",
    "viewed_at": "2025-01-27T15:00:00Z",
    "duration_seconds": 120,
    "scroll_percentage": 85,
    "article": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Article Title",
      "url": "https://example.com/article",
      "thumbnail_url": "https://example.com/thumb.jpg"
    }
  }
]
```

---

### Get Reading Statistics

**GET** `/reading-history/stats`

Get reading statistics for the current user with optional date filtering.

**Authentication:** Required

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | datetime | null | Statistics period start (ISO 8601) |
| `end_date` | datetime | null | Statistics period end (ISO 8601) |

**Response:** `200 OK`
```json
{
  "total_articles_read": 156,
  "total_reading_time_seconds": 18720,
  "average_reading_time_seconds": 120,
  "average_scroll_percentage": 78.5,
  "articles_read_today": 5,
  "articles_read_this_week": 23,
  "articles_read_this_month": 87,
  "most_read_category": "science",
  "reading_streak_days": 12
}
```

---

### Clear Reading History

**DELETE** `/reading-history`

Clear reading history for the current user.

**Authentication:** Required

**Request Body (Optional):**
```json
{
  "before_date": "2025-01-01T00:00:00Z"  // Optional, only clear history before this date
}
```

**Response:** `200 OK`
```json
{
  "deleted_count": 50,
  "message": "Successfully cleared 50 history record(s)"
}
```

---

### Export Reading History

**GET** `/reading-history/export`

Export reading history in JSON or CSV format for data portability.

**Authentication:** Required

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format` | string | `json` | Export format: `json` or `csv` |
| `start_date` | datetime | null | Export history after this date (ISO 8601) |
| `end_date` | datetime | null | Export history before this date (ISO 8601) |
| `include_articles` | boolean | true | Include full article details in export |

**Response:** `200 OK`
- Content-Type: `application/json` or `text/csv`
- Content-Disposition: `attachment; filename=reading-history-2025-01-27.json`

**JSON Format Example:**
```json
[
  {
    "viewed_at": "2025-01-27T15:00:00Z",
    "duration_seconds": 120,
    "scroll_percentage": 85,
    "article": {
      "title": "Article Title",
      "url": "https://example.com/article",
      "category": "science"
    }
  }
]
```

---

### Get Reading Preferences

**GET** `/reading-history/preferences`

Get reading tracking preferences for the current user.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "id": "c50e8400-e29b-41d4-a716-446655440000",
  "user_id": "650e8400-e29b-41d4-a716-446655440001",
  "track_reading_history": true,
  "track_reading_time": true,
  "track_scroll_depth": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-27T10:00:00Z"
}
```

---

### Update Reading Preferences

**PUT** `/reading-history/preferences`

Update reading tracking preferences for the current user.

**Authentication:** Required

**Request Body:**
```json
{
  "track_reading_history": true,  // Optional
  "track_reading_time": false,    // Optional
  "track_scroll_depth": true      // Optional
}
```

**Response:** `200 OK`
```json
{
  "id": "c50e8400-e29b-41d4-a716-446655440000",
  "user_id": "650e8400-e29b-41d4-a716-446655440001",
  "track_reading_history": true,
  "track_reading_time": false,
  "track_scroll_depth": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-27T16:00:00Z"
}
```

---

## Notifications Endpoints

### Get Notifications

**GET** `/notifications`

Get paginated list of notifications for the current user.

**Authentication:** Required

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (min: 1) |
| `page_size` | integer | 20 | Items per page (min: 1, max: 100) |
| `unread_only` | boolean | false | Show only unread notifications |
| `notification_type` | string | null | Filter by type: `vote`, `reply`, `mention` |

**Response:** `200 OK`
```json
{
  "notifications": [
    {
      "id": "d50e8400-e29b-41d4-a716-446655440000",
      "user_id": "650e8400-e29b-41d4-a716-446655440001",
      "type": "reply",
      "title": "New reply to your comment",
      "message": "John replied to your comment on 'Article Title'",
      "related_entity_type": "comment",
      "related_entity_id": "960e8400-e29b-41d4-a716-446655440001",
      "actor_id": "660e8400-e29b-41d4-a716-446655440002",
      "actor_username": "johndoe",
      "is_read": false,
      "read_at": null,
      "created_at": "2025-01-27T16:30:00Z"
    }
  ],
  "total": 42,
  "unread_count": 5,
  "page": 1,
  "page_size": 20
}
```

**Notification Types:**
- `vote`: Someone voted on your content
- `reply`: Someone replied to your comment
- `mention`: Someone mentioned you in a comment

---

### Get Notification Statistics

**GET** `/notifications/stats`

Get notification statistics for the current user.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "total_count": 42,
  "unread_count": 5,
  "vote_count": 15,
  "reply_count": 20,
  "mention_count": 7
}
```

---

### Get Unread Count

**GET** `/notifications/unread-count`

Get count of unread notifications for the current user (lightweight endpoint for badges).

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "unread_count": 5
}
```

**Frontend Usage:**
```typescript
// Poll for unread count every 30 seconds
setInterval(async () => {
  const { unread_count } = await fetch('/api/v1/notifications/unread-count');
  updateNotificationBadge(unread_count);
}, 30000);
```

---

### Get Notification Preferences

**GET** `/notifications/preferences`

Get notification preferences for the current user.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "id": "e50e8400-e29b-41d4-a716-446655440000",
  "user_id": "650e8400-e29b-41d4-a716-446655440001",
  "vote_notifications": true,
  "reply_notifications": true,
  "mention_notifications": true,
  "email_notifications": false,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-27T10:00:00Z"
}
```

**Note:** Creates default preferences if none exist

---

### Update Notification Preferences

**PUT** `/notifications/preferences`

Update notification preferences for the current user.

**Authentication:** Required

**Request Body:**
```json
{
  "vote_notifications": true,      // Optional
  "reply_notifications": false,    // Optional
  "mention_notifications": true,   // Optional
  "email_notifications": false     // Optional (future feature)
}
```

**Response:** `200 OK`
```json
{
  "id": "e50e8400-e29b-41d4-a716-446655440000",
  "user_id": "650e8400-e29b-41d4-a716-446655440001",
  "vote_notifications": true,
  "reply_notifications": false,
  "mention_notifications": true,
  "email_notifications": false,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-27T17:00:00Z"
}
```

**Note:** Only provided fields are updated. Others remain unchanged.

---

### Get Single Notification

**GET** `/notifications/{notification_id}`

Get a specific notification by ID.

**Authentication:** Required

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `notification_id` | UUID | Notification identifier |

**Response:** `200 OK`
```json
{
  "id": "d50e8400-e29b-41d4-a716-446655440000",
  "user_id": "650e8400-e29b-41d4-a716-446655440001",
  "type": "reply",
  "title": "New reply to your comment",
  "message": "John replied to your comment on 'Article Title'",
  "related_entity_type": "comment",
  "related_entity_id": "960e8400-e29b-41d4-a716-446655440001",
  "actor_id": "660e8400-e29b-41d4-a716-446655440002",
  "actor_username": "johndoe",
  "is_read": false,
  "read_at": null,
  "created_at": "2025-01-27T16:30:00Z"
}
```

**Errors:**
- `404 Not Found`: Notification not found or doesn't belong to user

---

### Mark Notifications as Read

**POST** `/notifications/mark-read`

Mark one or more notifications as read.

**Authentication:** Required

**Request Body:**
```json
{
  "notification_ids": [
    "d50e8400-e29b-41d4-a716-446655440000",
    "d60e8400-e29b-41d4-a716-446655440001"
  ]
}
```

**Response:** `200 OK`
```json
{
  "marked_count": 2,
  "message": "Successfully marked 2 notification(s) as read"
}
```

---

### Mark All Notifications as Read

**POST** `/notifications/mark-all-read`

Mark all notifications as read for the current user.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "marked_count": 5,
  "message": "Successfully marked all 5 notifications as read"
}
```

---

### Delete Notification

**DELETE** `/notifications/{notification_id}`

Delete a notification.

**Authentication:** Required

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `notification_id` | UUID | Notification identifier |

**Response:** `204 No Content`

**Errors:**
- `404 Not Found`: Notification not found or doesn't belong to user

---

## Error Handling

### Standard Error Response Format

All errors return a consistent JSON structure:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Meaning | When It Occurs |
|------|---------|----------------|
| `200` | OK | Successful GET, PUT, PATCH, POST (non-creation) |
| `201` | Created | Successful resource creation |
| `204` | No Content | Successful DELETE or update with no response body |
| `400` | Bad Request | Invalid request data, validation errors |
| `401` | Unauthorized | Missing or invalid authentication token |
| `403` | Forbidden | User doesn't have permission for this action |
| `404` | Not Found | Resource doesn't exist |
| `409` | Conflict | Resource conflict (e.g., duplicate email) |
| `422` | Unprocessable Entity | Validation error in request body |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server-side error |
| `501` | Not Implemented | Endpoint not yet implemented |

### Frontend Error Handling Example

```typescript
async function apiRequest(url: string, options: RequestInit = {}) {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      
      switch (response.status) {
        case 401:
          // Token expired - try refresh
          await refreshToken();
          return apiRequest(url, options); // Retry
        
        case 403:
          // Permission denied
          showError('You don\'t have permission for this action');
          break;
        
        case 404:
          showError('Resource not found');
          break;
        
        case 422:
          // Validation error
          showValidationErrors(error.detail);
          break;
        
        case 429:
          // Rate limited
          showError('Too many requests. Please try again later.');
          break;
        
        default:
          showError(error.detail || 'An error occurred');
      }
      
      throw error;
    }

    return await response.json();
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}
```

---

## Rate Limiting

### Default Limits

The API implements rate limiting to prevent abuse:

- **Authentication endpoints**: 5 requests per minute per IP
- **General endpoints**: 100 requests per minute per IP
- **Heavy endpoints** (search, feed): 30 requests per minute per user

### Rate Limit Headers

Responses include rate limit information in headers:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1706367600
```

### Handling Rate Limits

When rate limited (429 status), wait for the time specified in `X-RateLimit-Reset` before retrying.

```typescript
if (response.status === 429) {
  const resetTime = parseInt(response.headers.get('X-RateLimit-Reset'));
  const waitTime = resetTime * 1000 - Date.now();
  
  // Wait and retry
  await new Promise(resolve => setTimeout(resolve, waitTime));
  return apiRequest(url, options);
}
```

---

## Additional Resources

### OpenAPI/Swagger Documentation

Interactive API documentation is available at:
```
http://localhost:8000/docs (Development)
https://your-domain.com/docs (Production)
```

### WebSocket Endpoints (Future)

Real-time updates for notifications and live comment threads are planned for future releases via WebSocket connections.

### GraphQL Support (Future)

GraphQL API is planned to provide more flexible data fetching capabilities.

---

## Support & Feedback

For questions or issues with the API:
- **GitHub Issues**: [Repository Issues](https://github.com/your-repo/issues)
- **Email**: support@yourdomain.com
- **Documentation**: See `docs/` folder for detailed guides

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-27  
**API Version**: v1
