# Frontend Quick Start - Essential Files

## ⭐ Top 3 Must-Read Files

### 1. **All API Endpoints**
📄 `docs/api-reference/01-API-QUICK-REFERENCE.md`
- Every endpoint with examples
- Request/response formats
- Authentication requirements

### 2. **TypeScript Types** (Copy into your frontend)
📄 `docs/api-reference/02-TYPESCRIPT-TYPES.md`
- All type definitions ready to use
- Copy into `frontend/src/types/api.ts`

### 3. **Getting Started Guide**
📄 `docs/api-reference/README.md`
- Authentication flow
- Base URLs
- Best practices

---

## 🚀 Quick Setup (5 Minutes)

### 1. Start Backend Server
```bash
cd /Users/ej/Downloads/RSS-Feed/backend
make run
# Server runs on http://localhost:8000
```

### 2. View Interactive API Docs
```bash
open http://localhost:8000/docs
# Swagger UI with all endpoints
```

### 3. Copy TypeScript Types
```bash
# Copy types from:
cat docs/api-reference/02-TYPESCRIPT-TYPES.md

# Into your frontend:
# frontend/src/types/api.ts
```

### 4. Set Frontend Environment
```bash
# Create frontend/.env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > frontend/.env.local
```

---

## 🔐 Authentication Quick Start

### Login Flow
```typescript
// 1. Login
const response = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    email: 'user@example.com', 
    password: 'password123' 
  })
});

const { access_token, refresh_token } = await response.json();

// 2. Store tokens
localStorage.setItem('access_token', access_token);
localStorage.setItem('refresh_token', refresh_token);

// 3. Use in requests
fetch('http://localhost:8000/feeds', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
```

---

## 📚 All API Endpoints

### Authentication
```
POST   /auth/register          - Register new user
POST   /auth/login             - Login (get JWT)
POST   /auth/refresh           - Refresh access token
POST   /auth/logout            - Logout
POST   /auth/forgot-password   - Request password reset
POST   /auth/reset-password    - Complete password reset
```

### User Profile
```
GET    /users/me               - Get current user
PUT    /users/me               - Update profile
DELETE /users/me               - Delete account
```

### RSS Feeds
```
GET    /feeds                  - List all feeds
POST   /feeds                  - Add new feed
GET    /feeds/{id}             - Get specific feed
PUT    /feeds/{id}             - Update feed
DELETE /feeds/{id}             - Delete feed
POST   /feeds/{id}/refresh     - Refresh feed now
```

### Articles
```
GET    /articles               - List articles (paginated)
GET    /articles/{id}          - Get article details
PUT    /articles/{id}          - Update article
DELETE /articles/{id}          - Delete article
GET    /articles/unread        - Get unread articles
POST   /articles/{id}/mark-read   - Mark as read
```

### Bookmarks
```
GET    /bookmarks              - List bookmarks
POST   /bookmarks              - Add bookmark
DELETE /bookmarks/{id}         - Remove bookmark
```

### Search
```
GET    /search/articles?q=...  - Search articles
GET    /search/feeds?q=...     - Search feeds
```

---

## 📊 Common Query Parameters

### Pagination
```
?page=1&limit=20
```

### Filtering Articles
```
?feed_id=123               - From specific feed
?is_read=false             - Unread only
?start_date=2025-01-01     - After date
&end_date=2025-01-31       - Before date
```

### Sorting
```
?sort=published_at         - Sort by field
&order=desc                - Sort direction (asc/desc)
```

---

## 🛡️ Error Handling

### Status Codes
```
200 - Success
201 - Created
400 - Bad Request (validation error)
401 - Unauthorized (need to login)
403 - Forbidden (no permission)
404 - Not Found
429 - Too Many Requests (rate limited)
500 - Server Error
```

### Error Response Format
```typescript
{
  "detail": "Error message",
  "status_code": 400
}
```

---

## 🎯 Implementation Order

### Day 1: Authentication
- [ ] Login page
- [ ] Registration page
- [ ] Token storage
- [ ] Protected routes

### Day 2: Core Features
- [ ] Feed list page
- [ ] Add feed form
- [ ] Article list page
- [ ] Article detail page

### Day 3: Additional Features
- [ ] Bookmark functionality
- [ ] User profile page
- [ ] Search
- [ ] Mark read/unread

### Day 4+: Polish
- [ ] Error handling
- [ ] Loading states
- [ ] Refresh functionality
- [ ] Notifications

---

## 💡 Pro Tips

### 1. Use the Swagger UI
```
http://localhost:8000/docs
```
- Test all endpoints
- See request/response examples
- Try authentication flow

### 2. Check Test Files for Examples
```
tests/test_api/test_auth.py      - Auth examples
tests/test_api/test_feeds.py     - Feed examples
tests/test_api/test_articles.py  - Article examples
```

### 3. CORS Configuration
Backend already configured for:
- `http://localhost:3000` (Next.js)
- `http://localhost:5173` (Vite)

If using different port, update `app/core/config.py`:
```python
BACKEND_CORS_ORIGINS = [
    "http://localhost:YOUR_PORT",
]
```

---

## 📁 File Reference Summary

| Purpose | File | Priority |
|---------|------|----------|
| All endpoints | `docs/api-reference/01-API-QUICK-REFERENCE.md` | ⭐⭐⭐ |
| Type definitions | `docs/api-reference/02-TYPESCRIPT-TYPES.md` | ⭐⭐⭐ |
| Getting started | `docs/api-reference/README.md` | ⭐⭐⭐ |
| OpenAPI spec | `docs/api-reference/03-OPENAPI-SPEC.md` | ⭐⭐ |
| Auth validation | `app/schemas/auth.py` | ⭐⭐ |
| Auth endpoints | `app/api/v1/endpoints/auth.py` | ⭐ |
| Feed endpoints | `app/api/v1/endpoints/feeds.py` | ⭐ |
| Article endpoints | `app/api/v1/endpoints/articles.py` | ⭐ |
| Auth examples | `tests/test_api/test_auth.py` | ⭐ |
| Environment config | `.env.example` | ⭐ |

⭐⭐⭐ = Must read  
⭐⭐ = Highly recommended  
⭐ = Optional reference

---

## 🚦 Quick Test

### 1. Test Backend is Running
```bash
curl http://localhost:8000/api/v1/health
```

### 2. Test Registration
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "username": "testuser"
  }'
```

### 3. Test Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

---

## 📞 Need More Details?

**Full guide**: `FRONTEND_DEVELOPER_GUIDE.md`  
**Complete docs**: `docs/api-reference/`  
**Swagger UI**: http://localhost:8000/docs  
**GitHub Repo**: https://github.com/Number531/RSS-Feed-Backend

---

## ✅ Checklist Before Starting Frontend

- [ ] Backend server running (`make run`)
- [ ] Can access http://localhost:8000/docs
- [ ] TypeScript types copied to frontend
- [ ] Frontend `.env` configured with API_URL
- [ ] Read `docs/api-reference/01-API-QUICK-REFERENCE.md`
- [ ] Tested login with curl or Postman

---

**You're ready to build! 🚀**

All endpoints are documented, tested, and ready for integration.
