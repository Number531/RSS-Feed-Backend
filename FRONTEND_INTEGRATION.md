# Frontend Integration Guide

## 🚀 Quick Start

### Backend Setup
```bash
# Start backend services
cd backend
docker-compose -f docker/docker-compose.dev.yml up -d

# Or run backend directly
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### Access Points
- **Backend API**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8000/redoc` (ReDoc)
- **Health Check**: `http://localhost:8000/health`

---

## 🔐 Authentication Flow

### 1. User Registration
**POST** `/api/v1/auth/register`

```json
// Request
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!"
}

// Response (201 Created)
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  "email": "john@example.com",
  "is_active": true,
  "created_at": "2025-10-15T12:00:00Z"
}
```

### 2. Login
**POST** `/api/v1/auth/login`

```json
// Request
{
  "email": "john@example.com",
  "password": "SecurePass123!"
}

// Response (200 OK)
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400  // 24 hours in seconds
}
```

### 3. Refresh Token
**POST** `/api/v1/auth/refresh`

```json
// Request
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

// Response (200 OK)
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 4. Using Authentication
Include the access token in the `Authorization` header for all protected endpoints:

```javascript
headers: {
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json'
}
```

---

## 📰 Core API Endpoints

### Articles

#### Get Article Feed
**GET** `/api/v1/articles`

Query Parameters:
- `page` (int, default: 1) - Page number
- `page_size` (int, default: 20, max: 100) - Items per page
- `category` (string, optional) - Filter by category: `general`, `politics`, `technology`, `business`, `entertainment`, `sports`, `health`, `science`
- `source` (string, optional) - Filter by source name
- `sort_by` (string, default: `hot`) - Sort by: `hot`, `new`, `top`
- `time_range` (string, default: `day`) - For `top` sort: `hour`, `day`, `week`, `month`, `year`, `all`

```json
// Response (200 OK)
{
  "articles": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Breaking News: Major Tech Announcement",
      "url": "https://example.com/article",
      "description": "Brief description...",
      "content": "Full article content...",
      "author": "John Smith",
      "published_date": "2025-10-15T10:00:00Z",
      "category": "technology",
      "image_url": "https://example.com/image.jpg",
      "source_name": "TechNews",
      "vote_score": 245,
      "vote_count": 312,
      "comment_count": 48,
      "user_vote": 1,  // 1 = upvote, -1 = downvote, null = no vote
      "is_bookmarked": false,
      "created_at": "2025-10-15T10:05:00Z"
    }
  ],
  "total": 1523,
  "page": 1,
  "page_size": 20,
  "total_pages": 77
}
```

#### Get Single Article
**GET** `/api/v1/articles/{article_id}`

```json
// Response (200 OK)
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Article Title",
  "url": "https://example.com/article",
  "description": "Description...",
  "content": "Full content...",
  "author": "Author Name",
  "published_date": "2025-10-15T10:00:00Z",
  "category": "technology",
  "image_url": "https://example.com/image.jpg",
  "source_name": "TechNews",
  "vote_score": 245,
  "vote_count": 312,
  "comment_count": 48,
  "user_vote": 1,
  "is_bookmarked": false,
  "created_at": "2025-10-15T10:05:00Z"
}
```

---

### Voting

#### Cast Vote on Article
**POST** `/api/v1/votes/{article_id}`

```json
// Request
{
  "value": 1  // 1 = upvote, -1 = downvote, 0 = remove vote
}

// Response (200 OK)
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "440e8400-e29b-41d4-a716-446655440000",
  "value": 1,
  "created_at": "2025-10-15T12:00:00Z"
}
```

#### Get User's Vote
**GET** `/api/v1/votes/{article_id}`

```json
// Response (200 OK) - If vote exists
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "value": 1,
  "created_at": "2025-10-15T12:00:00Z"
}

// Response (404) - If no vote exists
```

#### Remove Vote
**DELETE** `/api/v1/votes/{article_id}`

```json
// Response (204 No Content)
```

---

### Comments

#### Get Article Comments
**GET** `/api/v1/comments/article/{article_id}`

Query Parameters:
- `page` (int, default: 1)
- `page_size` (int, default: 50)
- `sort_by` (string, default: `best`) - Options: `best`, `new`, `top`, `controversial`

```json
// Response (200 OK)
{
  "comments": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "article_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_id": "440e8400-e29b-41d4-a716-446655440000",
      "username": "johndoe",
      "content": "Great article! Very informative.",
      "parent_id": null,
      "depth": 0,
      "vote_score": 12,
      "vote_count": 15,
      "user_vote": 1,
      "reply_count": 3,
      "is_deleted": false,
      "is_edited": false,
      "created_at": "2025-10-15T11:00:00Z",
      "updated_at": "2025-10-15T11:00:00Z"
    }
  ],
  "total": 48,
  "page": 1,
  "page_size": 50
}
```

#### Create Comment
**POST** `/api/v1/comments`

```json
// Request - Top-level comment
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "This is my comment on the article"
}

// Request - Reply to comment
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "parent_id": "660e8400-e29b-41d4-a716-446655440000",
  "content": "This is a reply to another comment"
}

// Response (201 Created)
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "440e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  "content": "This is my comment",
  "parent_id": null,
  "depth": 0,
  "vote_score": 0,
  "vote_count": 0,
  "user_vote": null,
  "reply_count": 0,
  "is_deleted": false,
  "is_edited": false,
  "created_at": "2025-10-15T12:00:00Z",
  "updated_at": "2025-10-15T12:00:00Z"
}
```

#### Update Comment
**PUT** `/api/v1/comments/{comment_id}`

```json
// Request
{
  "content": "Updated comment content"
}

// Response (200 OK)
// Same structure as create response with updated fields
```

#### Delete Comment
**DELETE** `/api/v1/comments/{comment_id}`

```json
// Response (204 No Content)
// Note: Comment content is replaced with "[deleted]" but structure remains for thread integrity
```

#### Vote on Comment
**POST** `/api/v1/comments/{comment_id}/vote`

```json
// Request
{
  "value": 1  // 1 = upvote, -1 = downvote
}

// Response (200 OK)
{
  "comment_id": "660e8400-e29b-41d4-a716-446655440000",
  "value": 1,
  "created_at": "2025-10-15T12:00:00Z"
}
```

---

### Bookmarks

#### Get User Bookmarks
**GET** `/api/v1/bookmarks`

Query Parameters:
- `page` (int, default: 1)
- `page_size` (int, default: 20)

```json
// Response (200 OK)
{
  "bookmarks": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440000",
      "article": {
        // Full article object
      },
      "created_at": "2025-10-15T09:00:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 20
}
```

#### Add Bookmark
**POST** `/api/v1/bookmarks/{article_id}`

```json
// Response (201 Created)
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "440e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-10-15T12:00:00Z"
}
```

#### Remove Bookmark
**DELETE** `/api/v1/bookmarks/{article_id}`

```json
// Response (204 No Content)
```

---

### Notifications

#### Get Notifications
**GET** `/api/v1/notifications`

Query Parameters:
- `page` (int, default: 1)
- `page_size` (int, default: 20)
- `unread_only` (bool, default: false)
- `type` (string, optional) - Filter by type: `comment_reply`, `vote`, `mention`

```json
// Response (200 OK)
{
  "notifications": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440000",
      "type": "comment_reply",
      "title": "New reply to your comment",
      "message": "johndoe replied to your comment",
      "is_read": false,
      "link": "/articles/550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2025-10-15T11:30:00Z"
    }
  ],
  "total": 8,
  "unread_count": 3,
  "page": 1,
  "page_size": 20
}
```

#### Mark Notification as Read
**PUT** `/api/v1/notifications/{notification_id}/read`

```json
// Response (200 OK)
{
  "id": "990e8400-e29b-41d4-a716-446655440000",
  "is_read": true,
  "updated_at": "2025-10-15T12:00:00Z"
}
```

#### Mark All as Read
**PUT** `/api/v1/notifications/read-all`

```json
// Response (200 OK)
{
  "marked_read": 3
}
```

---

### User Profile

#### Get Current User Profile
**GET** `/api/v1/users/me`

```json
// Response (200 OK)
{
  "id": "440e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "avatar_url": "https://example.com/avatar.jpg",
  "is_active": true,
  "is_verified": false,
  "created_at": "2025-10-01T10:00:00Z",
  "last_login_at": "2025-10-15T08:00:00Z"
}
```

#### Update Profile
**PUT** `/api/v1/users/me`

```json
// Request
{
  "full_name": "John A. Doe",
  "avatar_url": "https://example.com/new-avatar.jpg"
}

// Response (200 OK)
// Same structure as GET profile
```

---

### RSS Sources

#### List RSS Sources
**GET** `/api/v1/sources`

Query Parameters:
- `page` (int, default: 1)
- `page_size` (int, default: 50)
- `category` (string, optional)
- `is_active` (bool, optional)

```json
// Response (200 OK)
{
  "sources": [
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440000",
      "name": "TechCrunch",
      "url": "https://techcrunch.com/feed/",
      "source_name": "TechCrunch",
      "category": "technology",
      "is_active": true,
      "last_fetched": "2025-10-15T11:45:00Z",
      "success_rate": 98.5,
      "is_healthy": true,
      "created_at": "2025-10-01T00:00:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "page_size": 50
}
```

#### Get Categories
**GET** `/api/v1/sources/categories`

```json
// Response (200 OK)
{
  "categories": [
    {
      "category": "technology",
      "count": 8,
      "active_count": 8
    },
    {
      "category": "politics",
      "count": 6,
      "active_count": 5
    }
  ]
}
```

---

## 🎯 Response Status Codes

### Success Codes
- **200 OK** - Request succeeded
- **201 Created** - Resource created successfully
- **204 No Content** - Request succeeded with no response body

### Client Error Codes
- **400 Bad Request** - Invalid request data
- **401 Unauthorized** - Missing or invalid authentication
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Resource not found
- **409 Conflict** - Resource conflict (e.g., duplicate email)
- **422 Unprocessable Entity** - Validation error

### Server Error Codes
- **500 Internal Server Error** - Server error
- **503 Service Unavailable** - Service temporarily unavailable

---

## 🔧 Error Response Format

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}

// Or for validation errors (422):
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## 🌐 CORS Configuration

The backend is configured to accept requests from:
- `http://localhost:3000` (React/Next.js default)
- `http://localhost:8081` (Mobile dev server)
- `http://localhost:19006` (Expo default)

To add your frontend URL, update `BACKEND_CORS_ORIGINS` in `.env`:

```env
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:3001,https://yourdomain.com
```

---

## 📊 Pagination Pattern

All paginated endpoints follow this pattern:

**Request:**
- `page`: Page number (1-indexed)
- `page_size`: Items per page (typically max 100)

**Response:**
```json
{
  "items": [...],  // Array of items (name varies by endpoint)
  "total": 150,    // Total number of items
  "page": 1,       // Current page
  "page_size": 20, // Items per page
  "total_pages": 8 // Total pages
}
```

---

## 🔄 Real-time Updates

The backend uses polling for real-time features. Recommended intervals:

- **Notifications**: Poll every 30-60 seconds
- **Article feed**: Poll every 5 minutes (or on user action)
- **Comment updates**: Poll every 30 seconds when viewing article

Example polling implementation:

```javascript
// Poll for new notifications
setInterval(async () => {
  const response = await fetch('/api/v1/notifications?unread_only=true', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const data = await response.json();
  updateNotificationBadge(data.unread_count);
}, 30000); // 30 seconds
```

---

## 🧪 Testing the API

### Using cURL

```bash
# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"pass123"}'

# Login
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123"}' \
  | jq -r '.access_token')

# Get articles
curl http://localhost:8000/api/v1/articles \
  -H "Authorization: Bearer $TOKEN"
```

### Using Postman/Insomnia

1. Import the OpenAPI spec from: `http://localhost:8000/api/v1/openapi.json`
2. Set up environment variable for `access_token`
3. Add Authorization header: `Bearer {{access_token}}`

---

## 🐛 Troubleshooting

### CORS Issues
**Problem:** Browser blocks requests with CORS error  
**Solution:** Ensure your frontend URL is in `BACKEND_CORS_ORIGINS` in backend `.env`

### 401 Unauthorized
**Problem:** All requests return 401  
**Solution:** Check that:
1. Access token is included in Authorization header
2. Token hasn't expired (24 hour lifetime)
3. Use refresh token endpoint to get new access token

### 422 Validation Error
**Problem:** Request validation fails  
**Solution:** Check the `detail` array in response for specific field errors

### Connection Refused
**Problem:** Can't connect to backend  
**Solution:** Verify backend is running on port 8000:
```bash
curl http://localhost:8000/health
```

---

## 📝 Rate Limiting

- **Authenticated users**: 100 requests per minute
- **Unauthenticated users**: 20 requests per minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Requests allowed per window
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

---

## 🚀 Production Considerations

### Base URL
Update your base URL for production:
```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

### Token Storage
- **Web**: Store tokens in HttpOnly cookies or secure localStorage
- **Mobile**: Use secure storage (Keychain/Keystore)
- Always use HTTPS in production

### Error Handling
Implement global error handler for:
- Network errors
- 401 (trigger re-login)
- 5xx errors (show user-friendly message)

---

## 📞 Support

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **GitHub**: https://github.com/Number531/RSS-Feed-Backend

---

**Last Updated:** October 15, 2025  
**API Version:** 1.0.0  
**Backend Version:** 1.0.0
