# Frontend Developer Guide - Essential Backend Files

## 📋 Quick Reference

This guide lists **all files you need to reference** when building the frontend to ensure proper API endpoint integration.

---

## 🎯 Critical Files (Must Read First)

### 1. **API Quick Reference** ⭐ START HERE
**File**: `docs/api-reference/01-API-QUICK-REFERENCE.md`

**What it contains:**
- All API endpoints at a glance
- Request/response formats
- Authentication requirements
- Status codes
- Example requests for every endpoint

**Use this for:**
- Understanding all available endpoints
- Quick lookup during development
- Knowing what data to send/receive

---

### 2. **TypeScript Type Definitions** ⭐ COPY THESE
**File**: `docs/api-reference/02-TYPESCRIPT-TYPES.md`

**What it contains:**
- Complete TypeScript interfaces for all API models
- Request/response types
- Authentication types
- Ready-to-use in your frontend

**Use this for:**
- Type safety in your frontend code
- Auto-completion in your IDE
- Catching errors at compile time

**How to use:**
```typescript
// Copy the types from the file into:
// frontend/src/types/api.ts
// Then import wherever needed:
import { User, Article, Feed, LoginRequest } from '@/types/api';
```

---

### 3. **OpenAPI Specification** 📐
**File**: `docs/api-reference/03-OPENAPI-SPEC.md`

**What it contains:**
- Complete OpenAPI 3.0 specification
- Can be imported into Swagger, Postman, or code generators

**Use this for:**
- Generating API client code automatically
- Importing into Postman for testing
- Comprehensive API documentation

**How to use:**
```bash
# Copy the YAML content to a file
# Then use with OpenAPI Generator:
npx @openapitools/openapi-generator-cli generate \
  -i openapi.yaml \
  -g typescript-axios \
  -o ./src/api
```

---

### 4. **API Reference Overview**
**File**: `docs/api-reference/README.md`

**What it contains:**
- Getting started guide
- Authentication flow explanation
- Base URLs for different environments
- Common patterns and best practices

**Use this for:**
- Understanding authentication flow
- Setting up API client configuration
- Learning common usage patterns

---

## 🔐 Authentication Files

### 5. **Authentication Implementation**
**File**: `app/api/v1/endpoints/auth.py`

**What it contains:**
- All authentication endpoints implementation
- Login, register, refresh, logout logic
- Password reset functionality

**Key endpoints to implement:**
```typescript
POST /auth/register     // User registration
POST /auth/login        // User login (get JWT tokens)
POST /auth/refresh      // Refresh access token
POST /auth/logout       // User logout
POST /auth/forgot-password  // Initiate password reset
POST /auth/reset-password   // Complete password reset
```

**View file to understand:**
- Request validation rules
- Response structures
- Error handling

---

### 6. **Authentication Schemas**
**File**: `app/schemas/auth.py`

**What it contains:**
- Pydantic schemas for authentication
- Validation rules (password length, email format, etc.)
- Request/response models

**Use this for:**
- Understanding validation requirements
- Knowing what fields are required vs optional
- Client-side validation rules

---

## 👤 User Management Files

### 7. **User Endpoints**
**File**: `app/api/v1/endpoints/users.py`

**Key endpoints:**
```typescript
GET    /users/me       // Get current user profile
PUT    /users/me       // Update current user
DELETE /users/me       // Delete account
```

---

### 8. **User Schemas**
**File**: `app/schemas/user.py`

**What it contains:**
- User model structure
- Profile update schemas
- User preferences structure

---

## 📡 RSS Feed Files

### 9. **Feed Endpoints**
**File**: `app/api/v1/endpoints/feeds.py`

**Key endpoints:**
```typescript
GET    /feeds              // List all user's feeds
POST   /feeds              // Add new RSS feed
GET    /feeds/{id}         // Get specific feed
PUT    /feeds/{id}         // Update feed
DELETE /feeds/{id}         // Delete feed
POST   /feeds/{id}/refresh // Manually refresh feed
GET    /feeds/{id}/articles // Get articles from specific feed
```

**View file to understand:**
- Pagination parameters
- Filtering options
- Refresh behavior

---

### 10. **Feed Schemas**
**File**: `app/schemas/feed.py`

**What it contains:**
- Feed creation requirements (URL, title, etc.)
- Feed update options
- Feed response structure

---

## 📰 Article Files

### 11. **Article Endpoints**
**File**: `app/api/v1/endpoints/articles.py`

**Key endpoints:**
```typescript
GET    /articles           // List articles (with filtering)
GET    /articles/{id}      // Get specific article
PUT    /articles/{id}      // Update article (mark read, etc.)
DELETE /articles/{id}      // Delete article
GET    /articles/unread    // Get unread articles
POST   /articles/{id}/mark-read    // Mark as read
POST   /articles/{id}/mark-unread  // Mark as unread
```

**View file to understand:**
- Pagination and filtering
- Search capabilities
- Sorting options

---

### 12. **Article Schemas**
**File**: `app/schemas/article.py`

**What it contains:**
- Article structure (title, content, author, etc.)
- Update options
- Read status management

---

## 🔖 Bookmark Files

### 13. **Bookmark Endpoints**
**File**: `app/api/v1/endpoints/bookmarks.py`

**Key endpoints:**
```typescript
GET    /bookmarks         // List all bookmarks
POST   /bookmarks         // Add bookmark
DELETE /bookmarks/{id}    // Remove bookmark
GET    /bookmarks/{id}    // Get specific bookmark
```

---

### 14. **Bookmark Schemas**
**File**: `app/schemas/bookmark.py`

**What it contains:**
- Bookmark creation requirements
- Bookmark structure
- Associated article data

---

## 🔍 Search Files

### 15. **Search Endpoints**
**File**: `app/api/v1/endpoints/search.py` (if exists, or check articles.py)

**Key endpoints:**
```typescript
GET /search/articles?q={query}  // Search articles
GET /search/feeds?q={query}     // Search feeds
```

**Parameters:**
- `q`: Search query string
- `page`: Page number
- `limit`: Results per page
- `sort`: Sort order

---

## 📧 Notification Files

### 16. **Notification Endpoints**
**File**: `app/api/v1/endpoints/notifications.py`

**Key endpoints:**
```typescript
GET /notifications/settings        // Get notification preferences
PUT /notifications/settings        // Update preferences
POST /notifications/test-email     // Send test email
```

---

## ⚙️ Configuration Files

### 17. **Environment Variables**
**File**: `.env.example`

**What it contains:**
- Required environment variables
- Configuration options
- API keys and secrets structure

**Use this for:**
- Setting up your frontend's backend URL
- Understanding what can be configured

**Frontend environment setup:**
```bash
# In your frontend .env file:
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_VERSION=v1
```

---

### 18. **CORS Configuration**
**File**: `app/core/config.py`

**What it contains:**
- Allowed origins
- CORS settings
- API configuration

**Important:** Make sure your frontend URL is in BACKEND_CORS_ORIGINS:
```python
BACKEND_CORS_ORIGINS = [
    "http://localhost:3000",  # Your frontend dev server
    "http://localhost:5173",  # Vite default
]
```

---

## 🛡️ Security & Error Handling

### 19. **Error Responses**
**File**: `app/core/exceptions.py`

**What it contains:**
- Custom exception classes
- Error response formats
- HTTP status codes

**Use this for:**
- Understanding error response structure
- Implementing proper error handling in frontend

**Standard error response format:**
```typescript
interface ErrorResponse {
  detail: string;
  status_code: number;
  error_code?: string;
}
```

---

### 20. **Rate Limiting**
**File**: `app/core/rate_limit.py`

**What it contains:**
- Rate limiting rules
- Endpoints and their limits

**Important for frontend:**
- Implement retry logic with exponential backoff
- Show user-friendly messages when rate limited (429 status)

---

## 📊 Models (Database Structure)

### 21. **Database Models**
**Files in**: `app/models/`

- `app/models/user.py` - User table structure
- `app/models/feed.py` - Feed table structure
- `app/models/article.py` - Article table structure
- `app/models/bookmark.py` - Bookmark table structure

**Use these for:**
- Understanding data relationships
- Knowing what fields exist in the database
- Understanding nullable vs required fields

---

## 🧪 Testing Files (For Reference)

### 22. **Test Examples**
**Files in**: `tests/test_api/`

**What they contain:**
- Example API requests
- Expected responses
- Edge cases and error scenarios

**Use these for:**
- Understanding how to use each endpoint
- Seeing example request bodies
- Learning error handling scenarios

**Key test files:**
- `tests/test_api/test_auth.py` - Auth flow examples
- `tests/test_api/test_feeds.py` - Feed management examples
- `tests/test_api/test_articles.py` - Article handling examples

---

## 📝 Quick Implementation Checklist

### Phase 1: Setup (Day 1)
- [ ] Read `docs/api-reference/README.md`
- [ ] Copy TypeScript types from `docs/api-reference/02-TYPESCRIPT-TYPES.md`
- [ ] Review authentication flow in `docs/api-reference/01-API-QUICK-REFERENCE.md`
- [ ] Set up environment variables from `.env.example`

### Phase 2: Authentication (Day 1-2)
- [ ] Implement login using `app/api/v1/endpoints/auth.py` reference
- [ ] Implement registration
- [ ] Set up JWT token storage
- [ ] Implement token refresh logic
- [ ] Add logout functionality

### Phase 3: Core Features (Day 3-7)
- [ ] Implement feed management using `app/api/v1/endpoints/feeds.py`
- [ ] Implement article listing using `app/api/v1/endpoints/articles.py`
- [ ] Add bookmark functionality using `app/api/v1/endpoints/bookmarks.py`
- [ ] Implement search using search endpoints
- [ ] Add user profile management

### Phase 4: Polish (Day 8+)
- [ ] Add error handling based on `app/core/exceptions.py`
- [ ] Implement rate limit handling
- [ ] Add loading states
- [ ] Add notifications/preferences

---

## 💡 Pro Tips

### 1. **Start with Authentication**
File order to read:
1. `docs/api-reference/README.md` (Auth flow section)
2. `docs/api-reference/02-TYPESCRIPT-TYPES.md` (Copy auth types)
3. `app/schemas/auth.py` (Understand validation rules)
4. `tests/test_api/test_auth.py` (See examples)

### 2. **Use TypeScript Types**
```typescript
// frontend/src/types/api.ts
// Copy all types from docs/api-reference/02-TYPESCRIPT-TYPES.md

// Then use throughout your app:
import { User, Article, Feed } from '@/types/api';
```

### 3. **Create API Client**
```typescript
// frontend/src/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private getHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  }

  async login(email: string, password: string) {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (!response.ok) throw new Error('Login failed');
    return response.json();
  }

  // ... more methods
}

export const api = new ApiClient();
```

### 4. **Handle Token Refresh**
Reference: `app/api/v1/endpoints/auth.py` (refresh endpoint)

```typescript
async function fetchWithAuth(url: string, options: RequestInit = {}) {
  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${getAccessToken()}`
    }
  });

  // If unauthorized, try refreshing token
  if (response.status === 401) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      // Retry original request
      response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${getAccessToken()}`
        }
      });
    }
  }

  return response;
}
```

### 5. **Error Handling**
Reference: `app/core/exceptions.py`

```typescript
async function handleApiError(response: Response) {
  const error = await response.json();
  
  switch (response.status) {
    case 400:
      throw new Error(error.detail || 'Invalid request');
    case 401:
      // Redirect to login
      window.location.href = '/login';
      break;
    case 403:
      throw new Error('Access forbidden');
    case 404:
      throw new Error('Resource not found');
    case 429:
      throw new Error('Too many requests. Please try again later.');
    case 500:
      throw new Error('Server error. Please try again later.');
    default:
      throw new Error(error.detail || 'An error occurred');
  }
}
```

---

## 🔗 File Path Summary

### Essential API Documentation
```
docs/api-reference/
├── README.md                    ⭐ Start here
├── 01-API-QUICK-REFERENCE.md   ⭐ All endpoints
├── 02-TYPESCRIPT-TYPES.md      ⭐ Copy these types
└── 03-OPENAPI-SPEC.md          📐 Complete spec
```

### Backend Implementation (For Reference)
```
app/
├── api/v1/endpoints/
│   ├── auth.py           🔐 Authentication
│   ├── users.py          👤 User management
│   ├── feeds.py          📡 RSS feeds
│   ├── articles.py       📰 Articles
│   ├── bookmarks.py      🔖 Bookmarks
│   └── notifications.py  📧 Notifications
│
├── schemas/
│   ├── auth.py           📋 Auth validation rules
│   ├── user.py           📋 User schemas
│   ├── feed.py           📋 Feed schemas
│   ├── article.py        📋 Article schemas
│   └── bookmark.py       📋 Bookmark schemas
│
└── core/
    ├── config.py         ⚙️ Configuration
    ├── exceptions.py     🛡️ Error handling
    └── rate_limit.py     🚦 Rate limiting
```

### Testing (For Examples)
```
tests/test_api/
├── test_auth.py          📝 Auth examples
├── test_feeds.py         📝 Feed examples
├── test_articles.py      📝 Article examples
└── test_bookmarks.py     📝 Bookmark examples
```

---

## 🚀 Quick Start Command

To view all API documentation:
```bash
# From backend directory
ls -la docs/api-reference/

# Open the main API reference
open docs/api-reference/README.md

# View TypeScript types
cat docs/api-reference/02-TYPESCRIPT-TYPES.md

# View all endpoints
cat docs/api-reference/01-API-QUICK-REFERENCE.md
```

---

## 📞 Need Help?

### During Development:
1. **First**: Check `docs/api-reference/01-API-QUICK-REFERENCE.md`
2. **For types**: Use `docs/api-reference/02-TYPESCRIPT-TYPES.md`
3. **For examples**: Look at `tests/test_api/` files
4. **For validation rules**: Check `app/schemas/` files

### Testing Endpoints:
```bash
# Start backend server
cd /Users/ej/Downloads/RSS-Feed/backend
make run

# Visit Swagger UI
open http://localhost:8000/docs

# Or use curl
curl http://localhost:8000/api/v1/health
```

---

## ✅ Summary

**Must-read files for frontend development:**

1. ⭐ `docs/api-reference/01-API-QUICK-REFERENCE.md` - All endpoints
2. ⭐ `docs/api-reference/02-TYPESCRIPT-TYPES.md` - Type definitions
3. ⭐ `docs/api-reference/README.md` - Getting started
4. 📋 `.env.example` - Configuration
5. 🔍 `tests/test_api/*.py` - Usage examples

**Everything else is optional** but helpful for understanding implementation details and edge cases.

---

**Start with the API reference docs, copy the TypeScript types, and you're ready to build!** 🚀
