# Local Development Guide

> **Complete guide for local frontend + backend development**  
> No staging deployment required!

---

## ✅ **YES - Full Local Development Supported!**

Your backend API **fully supports local development** and works perfectly for building your frontend **before any staging/production deployment**.

---

## 🎯 **What Works Locally**

### All 51 API Endpoints Work! ✅

Your current setup already provides:

- ✅ **Authentication** (Register, Login, Token Refresh)
- ✅ **User Management** (Profile CRUD)
- ✅ **Articles Feed** (Browse, Search, Filter, Sort)
- ✅ **Voting System** (Upvote/Downvote articles)
- ✅ **Comments** (Create, Read, Update, Delete + Threading)
- ✅ **Comment Voting** (Upvote/Downvote comments)
- ✅ **Bookmarks** (Save articles with collections)
- ✅ **Reading History** (Track views with metrics)
- ✅ **Notifications** (User activity notifications)
- ✅ **Health Checks** (Monitor backend status)

### Current Configuration ✅

Your `.env` file is **already configured** for local development:
- ✅ **Database**: Supabase PostgreSQL (cloud-hosted, works from anywhere)
- ✅ **CORS**: Includes `localhost:3000` for React/Next.js
- ✅ **Debug Mode**: Enabled for development
- ✅ **JWT Authentication**: Working and secure

---

## 🚀 **Quick Start (3 Commands)**

### 1. Start the Backend
```bash
cd /Users/ej/Downloads/RSS-Feed/backend
uvicorn app.main:app --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
✅ Database connection initialized
✅ Metrics endpoint exposed at /metrics
```

### 2. Test It's Working
```bash
# In another terminal
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-27T19:30:00Z",
  "environment": "development",
  "version": "1.0.0",
  "database": "connected",
  "redis": "error: ..." // ← This is OK! Redis is optional
}
```

### 3. Open Interactive Docs
```bash
open http://localhost:8000/docs
```

**That's it!** Your backend is ready for frontend development.

---

## 📦 **What's Already Set Up**

### Current Stack

```
┌─────────────────────────────────────────┐
│         Your Local Computer             │
│                                         │
│  ┌─────────────┐      ┌──────────────┐ │
│  │  Frontend   │ ───► │   Backend    │ │
│  │  (Next.js)  │      │  (FastAPI)   │ │
│  │ localhost:  │      │ localhost:   │ │
│  │    3000     │      │    8000      │ │
│  └─────────────┘      └──────┬───────┘ │
│                              │          │
└──────────────────────────────┼──────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │  Supabase Cloud    │
                    │  PostgreSQL DB     │
                    │  (Remote, Always   │
                    │   Available)       │
                    └────────────────────┘
```

**Key Points:**
- ✅ Backend runs on `localhost:8000`
- ✅ Frontend runs on `localhost:3000` (or your choice)
- ✅ Database is cloud-hosted (Supabase) - no local PostgreSQL needed!
- ✅ Redis is **optional** - not required for core functionality

---

## 🔧 **Optional Services Status**

### Required (Already Working) ✅
- **Backend Server** - FastAPI on port 8000
- **Database** - Supabase PostgreSQL (cloud)

### Optional (Can Add Later) 🟡
- **Redis** - For caching (improves performance, not required)
- **Celery** - For background RSS fetching (can run manually instead)

---

## 💻 **Frontend Setup Example**

### Environment Variables

Create `.env.local` in your frontend:

```bash
# Next.js / React
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Vite / Vue
VITE_API_URL=http://localhost:8000/api/v1
```

### API Client Setup

```typescript
// src/api/client.ts
import axios from 'axios';

const API_BASE_URL = 
  process.env.NEXT_PUBLIC_API_URL || 
  'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Test Connection

```typescript
// src/pages/index.tsx (Next.js example)
import { useEffect, useState } from 'react';
import { apiClient } from '../api/client';

export default function Home() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchArticles() {
      try {
        const { data } = await apiClient.get('/articles');
        setArticles(data.articles);
      } catch (error) {
        console.error('Error fetching articles:', error);
      } finally {
        setLoading(false);
      }
    }
    
    fetchArticles();
  }, []);

  if (loading) return <div>Loading...</div>;
  
  return (
    <div>
      <h1>Articles</h1>
      {articles.map((article) => (
        <div key={article.id}>{article.title}</div>
      ))}
    </div>
  );
}
```

---

## 🧪 **Testing Your Setup**

### Test 1: Health Check
```bash
curl http://localhost:8000/health
```
**Expected:** `"status": "healthy"`

---

### Test 2: Register User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dev@example.com",
    "username": "devuser",
    "password": "DevPass123!",
    "full_name": "Dev User"
  }'
```
**Expected:** User object with `id`, `email`, etc.

---

### Test 3: Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dev@example.com",
    "password": "DevPass123!"
  }'
```
**Expected:** `access_token`, `refresh_token`

---

### Test 4: Get Articles (No Auth Required)
```bash
curl http://localhost:8000/api/v1/articles
```
**Expected:** Array of articles with pagination metadata

---

### Test 5: Get User Profile (Auth Required)
```bash
# Replace YOUR_TOKEN with the access_token from Test 3
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Expected:** User profile object

---

## 🌐 **CORS Configuration**

Your current CORS settings already support common frontend ports:

```bash
# Current in .env:
BACKEND_CORS_ORIGINS='["http://localhost:3000","http://localhost:8081","http://localhost:19006"]'
```

### Supported Frameworks:
- ✅ **Next.js** - `localhost:3000` (default)
- ✅ **React (CRA)** - `localhost:3000` (default)
- ✅ **Expo** - `localhost:19006` (default)
- ✅ **React Native Web** - `localhost:8081` (default)

### Add More Ports (Optional):
```bash
# If using Vite (port 5173) or other framework:
BACKEND_CORS_ORIGINS='["http://localhost:3000","http://localhost:5173","http://localhost:8080"]'
```

**After changing, restart backend:**
```bash
# Stop with Ctrl+C, then restart
uvicorn app.main:app --reload
```

---

## 📊 **Database Access**

Your database is **already set up** and accessible!

### Current Setup:
- **Host**: Supabase Cloud (AWS us-east-2)
- **Connection**: Already configured in `.env`
- **Tables**: All migrations applied ✅

### View Your Data:

**Option 1: Supabase Dashboard**
```bash
open https://supabase.com/dashboard/project/rtmcxjlagusjhsrslvab
```
- Navigate to "Table Editor" to see your data
- View SQL Editor to run queries

**Option 2: Command Line (via Python)**
```bash
cd /Users/ej/Downloads/RSS-Feed/backend
python -c "
import asyncio
from app.db.session import get_db
from sqlalchemy import select, text

async def check_tables():
    async for db in get_db():
        result = await db.execute(text('''
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        '''))
        print('Tables in database:')
        for row in result:
            print(f'  - {row[0]}')
        break

asyncio.run(check_tables())
"
```

---

## 🚫 **What You DON'T Need**

### ❌ Not Required for Local Development:

1. **Redis** - Optional caching (API works without it)
2. **Celery** - Optional background tasks (RSS fetching)
3. **Docker** - Can run directly with Python
4. **Nginx** - Not needed locally (FastAPI has built-in server)
5. **SSL/HTTPS** - Not needed for localhost
6. **Staging Server** - Develop everything locally first!
7. **Domain Name** - Use localhost
8. **Cloud Deployment** - Deploy when ready!

---

## 🐛 **Troubleshooting**

### Issue: "Connection Refused" on localhost:8000

**Solution:**
```bash
# Check if backend is running
lsof -i :8000

# If nothing, start backend:
cd /Users/ej/Downloads/RSS-Feed/backend
uvicorn app.main:app --reload
```

---

### Issue: CORS Error from Frontend

```
Access to fetch at 'http://localhost:8000/api/v1/...' from origin 
'http://localhost:3000' has been blocked by CORS policy
```

**Solution:**
1. Check `.env` has your frontend port:
   ```bash
   BACKEND_CORS_ORIGINS='["http://localhost:3000"]'
   ```
2. Restart backend after changing `.env`
3. Check browser console for exact origin being blocked
4. Add that origin to `BACKEND_CORS_ORIGINS`

---

### Issue: "Database Connection Error"

**Solution:**
Your database is cloud-hosted and should always be accessible. If you see this:

1. Check internet connection
2. Verify `DATABASE_URL` in `.env` is correct
3. Test connection:
   ```bash
   python -c "
   import asyncio
   from app.db.session import get_db
   async def test():
       async for db in get_db():
           print('✅ Database connected!')
           break
   asyncio.run(test())
   "
   ```

---

### Issue: "Redis Connection Error"

**This is OK!** Redis is optional. The error in health check is normal:
```json
{
  "status": "healthy",
  "redis": "error: ..."  // ← Ignore this
}
```

Core API functionality works without Redis. To add Redis later:
```bash
# macOS
brew install redis
brew services start redis

# Then restart backend
```

---

## 📝 **Development Workflow**

### Typical Development Session:

```bash
# 1. Start Backend (Terminal 1)
cd /Users/ej/Downloads/RSS-Feed/backend
uvicorn app.main:app --reload

# 2. Start Frontend (Terminal 2)
cd /path/to/your/frontend
npm run dev  # or yarn dev

# 3. Open Browser
open http://localhost:3000  # Frontend
open http://localhost:8000/docs  # API docs

# 4. Develop!
# - Backend auto-reloads on code changes (--reload flag)
# - Frontend hot-reloads automatically
# - Test API endpoints in Swagger UI
# - Use browser DevTools to debug API calls
```

---

## 🎯 **Feature Development Checklist**

When building a feature, follow this flow:

### Backend-First Approach:
- [ ] Endpoint already exists (check API reference)
- [ ] Test endpoint in Swagger UI (`/docs`)
- [ ] Verify response format matches TypeScript types
- [ ] Test authentication if required
- [ ] Implement in frontend

### Frontend-First Approach:
- [ ] Design UI component
- [ ] Implement with mock data
- [ ] Connect to real API endpoint
- [ ] Handle loading states
- [ ] Handle error states
- [ ] Test full flow

---

## 📚 **Key Resources for Local Development**

### Documentation:
1. **API Reference** - `/Users/ej/Downloads/RSS-Feed/backend/frontend-api-reference/`
2. **Interactive Docs** - http://localhost:8000/docs (when backend running)
3. **Quick Reference** - `frontend-api-reference/01-API-QUICK-REFERENCE.md`
4. **TypeScript Types** - `frontend-api-reference/02-TYPESCRIPT-TYPES.md`

### Testing Tools:
- **Swagger UI** - http://localhost:8000/docs
- **cURL** - Command line testing
- **Postman** - Import OpenAPI spec from docs
- **Browser DevTools** - Network tab for debugging

---

## 🚀 **When to Deploy to Staging**

You can develop **everything locally first**, then deploy when:

- ✅ Core features are implemented and tested
- ✅ Authentication flow works end-to-end
- ✅ Main user journeys are complete
- ✅ Ready for external testing/feedback
- ✅ Want to share with stakeholders

**There's NO rush to deploy!** Local development is:
- Faster (no deploy time)
- Easier to debug
- Free (no hosting costs during development)
- More flexible (easy to experiment)

---

## ✅ **Summary: You're All Set!**

### What You Have:
- ✅ **51 Working API Endpoints** (localhost:8000)
- ✅ **Cloud Database** (Supabase - always accessible)
- ✅ **CORS Configured** (supports localhost:3000)
- ✅ **Authentication** (JWT tokens working)
- ✅ **Interactive Docs** (Swagger UI)
- ✅ **Full Type Safety** (TypeScript definitions provided)

### What to Do:
```bash
# 1. Start backend
cd /Users/ej/Downloads/RSS-Feed/backend
uvicorn app.main:app --reload

# 2. Build your frontend pointing to:
API_URL=http://localhost:8000/api/v1

# 3. Develop all features locally

# 4. Deploy when ready (optional)
```

### No Deployment Needed!
- ✅ All endpoints work locally
- ✅ Real database (cloud-hosted)
- ✅ Full authentication
- ✅ Complete feature set
- ✅ Production-ready architecture

---

**Start building your frontend NOW!** 🚀

No staging deployment needed. Everything works locally.

---

**Last Updated:** 2025-01-27  
**Backend Status:** ✅ Ready for Local Development  
**Deployment Required:** ❌ No (Optional)
