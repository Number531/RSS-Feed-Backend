# Backend Pending Requirements for Frontend Production Deployment

**Document Version:** 2.0  
**Date:** January 26, 2025  
**Priority:** HIGH - Required for Full Production Readiness  
**Frontend Version:** 1.0.0 (Next.js 15.1.8)  
**Backend Version:** FastAPI (Python)

---

## Executive Summary

The RSS News Feed frontend is **95% production-ready**. The remaining 5% requires backend API implementation for user profile management features. This document explicitly outlines:

1. **5 Missing API Endpoints** - User profile operations currently stubbed
2. **Type Alignment Issues** - Minor field mismatches between frontend/backend
3. **CORS Configuration** - Production URL allowlist requirements
4. **Deployment Coordination** - Environment setup and validation

**Critical Path:** Items 1-2 are required before the frontend can go to production with full functionality.

---

## Table of Contents

1. [Missing API Endpoints (Critical)](#1-missing-api-endpoints-critical)
2. [Type Alignment Issues (High Priority)](#2-type-alignment-issues-high-priority)
3. [CORS Configuration (High Priority)](#3-cors-configuration-high-priority)
4. [Optional Enhancements](#4-optional-enhancements)
5. [Testing Requirements](#5-testing-requirements)
6. [Deployment Checklist](#6-deployment-checklist)

---

## 1. Missing API Endpoints (Critical)

### Priority: 🔴 CRITICAL - Required for production deployment

The frontend has these user profile features **fully implemented in the UI** but currently stubbed in the API layer. All 5 hooks throw `throw new Error('Not implemented')`:

**File:** `frontend/lib/hooks/use-users.ts` (lines 1-100)

### 1.1 Get Current User Profile

**Frontend Hook:** `useUser()`  
**Status:** ❌ Stubbed  
**UI Impact:** Profile page, user menu, settings page

#### API Specification

**Endpoint:** `GET /api/v1/users/me`  
**Authentication:** Required (JWT Bearer token)  
**Request Headers:**
```http
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": 123,
  "email": "user@example.com",
  "username": "john_doe",
  "display_name": "John Doe",
  "avatar_url": "https://cdn.example.com/avatars/123.jpg",
  "bio": "Software engineer and news enthusiast",
  "karma": 150,
  "created_at": "2025-01-15T10:30:00Z",
  "is_verified": true,
  "is_active": true,
  "role": "user"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid/expired token
- `404 Not Found` - User account deleted
- `500 Internal Server Error` - Database error

**Frontend Type:** `User` interface in `types/api.ts`

#### Implementation Notes
- Must match existing `User` type in frontend
- Token validation required
- Should include aggregated user statistics if available
- Consider caching (5-10 minute TTL)

---

### 1.2 Update User Profile

**Frontend Hook:** `useUpdateProfile()`  
**Status:** ❌ Stubbed  
**UI Impact:** Profile settings page, avatar upload, bio editor

#### API Specification

**Endpoint:** `PATCH /api/v1/users/me`  
**Authentication:** Required (JWT Bearer token)  
**Request Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "display_name": "John Smith",
  "avatar_url": "https://cdn.example.com/avatars/new-avatar.jpg",
  "bio": "Updated bio text (max 500 characters)"
}
```

**Field Constraints:**
- `display_name`: 2-50 characters, alphanumeric + spaces only
- `avatar_url`: Valid URL, HTTPS only, max 500 characters
- `bio`: Optional, max 500 characters

**Response (200 OK):**
```json
{
  "id": 123,
  "email": "user@example.com",
  "username": "john_doe",
  "display_name": "John Smith",
  "avatar_url": "https://cdn.example.com/avatars/new-avatar.jpg",
  "bio": "Updated bio text",
  "karma": 150,
  "created_at": "2025-01-15T10:30:00Z",
  "is_verified": true,
  "is_active": true,
  "role": "user"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid field values (with validation errors)
- `401 Unauthorized` - Invalid/expired token
- `422 Unprocessable Entity` - Validation failed
- `500 Internal Server Error` - Database error

**Validation Rules:**
1. Display name cannot be empty or only whitespace
2. Avatar URL must be valid HTTPS URL
3. Bio must not contain HTML/scripts (sanitize)
4. Cannot update email or username via this endpoint
5. Rate limit: 5 updates per hour per user

#### Frontend Type
```typescript
interface UserUpdate {
  display_name?: string;
  avatar_url?: string | null;
  bio?: string | null;
}
```

---

### 1.3 Get User Statistics

**Frontend Hook:** `useUserStats()`  
**Status:** ❌ Stubbed  
**UI Impact:** Profile page statistics cards, dashboard widgets

#### API Specification

**Endpoint:** `GET /api/v1/users/me/stats`  
**Authentication:** Required (JWT Bearer token)  
**Request Headers:**
```http
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "total_articles_read": 342,
  "total_comments": 87,
  "total_votes": 215,
  "total_bookmarks": 45,
  "karma": 150,
  "account_age_days": 120,
  "reading_streak_days": 7,
  "top_categories": [
    {
      "category": "politics",
      "article_count": 120
    },
    {
      "category": "science",
      "article_count": 85
    },
    {
      "category": "technology",
      "article_count": 67
    }
  ],
  "recent_activity": {
    "last_login": "2025-01-26T14:30:00Z",
    "last_comment": "2025-01-25T18:45:00Z",
    "last_vote": "2025-01-26T12:15:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid/expired token
- `500 Internal Server Error` - Database error

**Frontend Type:** `UserStats` interface in `types/api.ts`

#### Implementation Notes
- Aggregate data from multiple tables:
  - Articles read from reading_history
  - Comments from comments table
  - Votes from article_votes/comment_votes
  - Bookmarks from bookmarks table
- Consider caching (1 hour TTL)
- Expensive query - optimize with materialized view or daily batch job

---

### 1.4 Change Password

**Frontend Hook:** `useChangePassword()`  
**Status:** ❌ Stubbed  
**UI Impact:** Settings page - Security section

#### API Specification

**Endpoint:** `POST /api/v1/users/me/change-password`  
**Authentication:** Required (JWT Bearer token)  
**Request Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewSecurePassword456!",
  "confirm_password": "NewSecurePassword456!"
}
```

**Password Requirements:**
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character (!@#$%^&*)
- Cannot be the same as current password
- Cannot be commonly used password (check against list)

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Password validation failed (with specific errors)
- `401 Unauthorized` - Current password incorrect or token invalid
- `422 Unprocessable Entity` - Passwords don't match
- `429 Too Many Requests` - Rate limit exceeded (3 attempts per hour)
- `500 Internal Server Error` - Database error

**Validation Rules:**
1. Current password must be verified against database hash
2. New password must meet all requirements
3. New password != current password
4. Rate limit: 3 attempts per hour per user
5. Log password change events for security audit

#### Security Considerations
- **CRITICAL:** Always verify current password before changing
- Hash new password with BCrypt (cost factor 12+)
- Invalidate all existing refresh tokens after password change
- Send email notification to user about password change
- Log event with IP address and user agent

---

### 1.5 Delete User Account

**Frontend Hook:** `useDeleteAccount()`  
**Status:** ❌ Stubbed  
**UI Impact:** Settings page - Danger zone, account deletion flow

#### API Specification

**Endpoint:** `DELETE /api/v1/users/me`  
**Authentication:** Required (JWT Bearer token)  
**Request Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "password": "UserPassword123!",
  "confirmation": "DELETE MY ACCOUNT",
  "reason": "No longer needed" 
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Account scheduled for deletion in 30 days",
  "deletion_date": "2025-02-25T14:30:00Z",
  "cancellation_url": "https://yourapp.com/account/cancel-deletion?token=abc123"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid confirmation text
- `401 Unauthorized` - Password incorrect or token invalid
- `422 Unprocessable Entity` - Validation failed
- `429 Too Many Requests` - Rate limit (1 attempt per day)
- `500 Internal Server Error` - Database error

**Deletion Policy:**
1. **Soft delete:** Mark account as `pending_deletion` with 30-day grace period
2. **Data retention:** Keep anonymized content (comments, votes) for community integrity
3. **Personal data removal:**
   - Email: Hash or delete after 30 days
   - Display name: Replace with "Deleted User"
   - Avatar: Remove immediately
   - Reading history: Delete immediately
   - Bookmarks: Delete immediately
4. **Cancellation:** User can cancel deletion within 30 days via email link
5. **Hard delete:** After 30 days, permanently remove all personal data

#### Implementation Notes
- **CRITICAL:** Verify password before deletion
- Send confirmation email with cancellation link
- Log deletion request with reason for analytics
- Rate limit: 1 deletion attempt per 24 hours
- Consider GDPR "right to be forgotten" - provide data export first

**GDPR Compliance:**
- Must provide data export before deletion
- Must permanently delete all personal data after 30 days
- Must anonymize retained content (comments/votes)
- Must send deletion confirmation email

---

## 2. Type Alignment Issues (High Priority)

### Priority: 🟡 HIGH - Required for production, quick fix

The frontend TypeScript types don't perfectly match backend API responses, causing 4 compilation errors that block production builds.

### 2.1 Article Type - Missing Fields

**File:** `frontend/types/api.ts` - `Article` interface  
**Issue:** Missing `has_synthesis` field  
**Impact:** TypeScript build fails, synthesis button logic broken

#### Required Change

**Frontend Type (Current):**
```typescript
export interface Article {
  id: string;
  title: string;
  content: string;
  summary: string;
  url: string;
  source: string;
  author: string | null;
  published_at: string;
  category: string;
  image_url: string | null;
  upvotes: number;
  downvotes: number;
  user_vote: number | null;
  comments_count: number;
  is_bookmarked: boolean;
  credibility_score: number | null;
  created_at: string;
  // MISSING: has_synthesis field
}
```

**Required Addition:**
```typescript
export interface Article {
  // ... all existing fields ...
  has_synthesis?: boolean | null;  // NEW: Indicates if synthesis is available
}
```

#### Backend Requirements

**Ensure API Response Includes:**
```json
{
  "id": "article-uuid",
  "title": "Article Title",
  // ... all existing fields ...
  "has_synthesis": true  // ← Must be included in GET /api/v1/articles response
}
```

**Database Query:**
```sql
SELECT 
  a.*,
  EXISTS(SELECT 1 FROM syntheses s WHERE s.article_id = a.id) AS has_synthesis
FROM articles a;
```

**Logic:**
- `has_synthesis = true` if the article has at least one synthesis record
- `has_synthesis = false` if no synthesis exists
- Can be `null` if synthesis system not initialized

---

### 2.2 SynthesisStatsResponse - Field Name Mismatch

**File:** `frontend/types/api.ts` - `SynthesisStatsResponse` interface  
**Issue:** Property name mismatch causing 2 TypeScript errors  
**Impact:** Synthesis statistics page broken

#### Required Change

**Frontend Type (Expected):**
```typescript
export interface SynthesisStatsResponse {
  total_syntheses: number;
  total_fact_checks: number;
  average_credibility_score: number;  // ← Frontend expects this name
  average_read_minutes: number | null; // ← Frontend expects this field
  synthesis_by_category: Array<{
    category: string;
    count: number;
  }>;
  recent_syntheses: Array<{
    id: string;
    article_id: string;
    created_at: string;
  }>;
}
```

#### Backend Requirements

**API Response Must Match:**
```json
{
  "total_syntheses": 42,
  "total_fact_checks": 127,
  "average_credibility_score": 73.5,  // NOT "average_credibility"
  "average_read_minutes": 8.3,         // NEW: Must include this field
  "synthesis_by_category": [
    {
      "category": "politics",
      "count": 15
    }
  ],
  "recent_syntheses": [
    {
      "id": "synthesis-uuid",
      "article_id": "article-uuid",
      "created_at": "2025-01-26T12:00:00Z"
    }
  ]
}
```

**Changes Required:**
1. Rename `average_credibility` → `average_credibility_score` in API response
2. Add `average_read_minutes` calculation (average reading time across all articles with syntheses)

**SQL Query:**
```sql
SELECT 
  COUNT(*) as total_syntheses,
  AVG(credibility_score) as average_credibility_score,  -- ← Correct name
  AVG(read_minutes) as average_read_minutes             -- ← New field
FROM syntheses
WHERE created_at >= NOW() - INTERVAL '30 days';
```

---

## 3. CORS Configuration (High Priority)

### Priority: 🟡 HIGH - Required for production deployment

### 3.1 Production URL Allowlist

**Current CORS:** Likely allows `http://localhost:3000` only  
**Required:** Add production frontend URLs

#### Configuration Required

```python
# backend/app/main.py or backend/app/config.py

ALLOWED_ORIGINS = [
    "http://localhost:3000",           # Development
    "https://yourdomain.com",          # Production
    "https://www.yourdomain.com",      # Production (www)
    "https://preview-*.yourdomain.com" # Preview deployments (Vercel)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Total-Count", "Retry-After"],
    max_age=3600  # Cache preflight requests for 1 hour
)
```

#### Testing
1. Deploy frontend to staging (e.g., `https://staging.yourdomain.com`)
2. Verify API calls work from staging URL
3. Check browser console for CORS errors
4. Test with and without authentication

---

### 3.2 Rate Limiting Headers

**Required:** Backend should return rate limit headers

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1706281200
Retry-After: 3600  # Seconds to wait before retry (if rate limited)
```

Frontend already captures these headers in `lib/api/client.ts` but backend must send them.

---

## 4. Optional Enhancements

### Priority: 🟢 LOW - Nice to have, not blocking

### 4.1 User Avatar Upload Endpoint

**Current:** Users must provide avatar URL  
**Enhancement:** Direct upload to backend

**Endpoint:** `POST /api/v1/users/me/avatar`  
**Request:** Multipart form data with image file  
**Response:** Returns uploaded avatar URL

```json
{
  "avatar_url": "https://cdn.yourdomain.com/avatars/123-abc.jpg"
}
```

**Requirements:**
- Image validation (JPEG, PNG, WebP only)
- Max file size: 5MB
- Resize to 400x400px
- Store in CDN or S3
- Return publicly accessible URL

---

### 4.2 Email Change Endpoint

**Frontend has UI but no implementation**

**Endpoint:** `POST /api/v1/users/me/change-email`  
**Request:**
```json
{
  "new_email": "newemail@example.com",
  "password": "UserPassword123!"
}
```

**Flow:**
1. Verify password
2. Send verification email to new address
3. User clicks link to confirm
4. Update email in database
5. Invalidate old sessions

---

### 4.3 Two-Factor Authentication (2FA)

**Not implemented in frontend yet, but future consideration**

**Endpoints:**
- `POST /api/v1/users/me/2fa/enable`
- `POST /api/v1/users/me/2fa/disable`
- `POST /api/v1/users/me/2fa/verify`

---

## 5. Testing Requirements

### 5.1 Backend Unit Tests Required

For each endpoint, create tests covering:

**GET /api/v1/users/me**
- [ ] Returns user data for valid token
- [ ] Returns 401 for invalid token
- [ ] Returns 401 for expired token
- [ ] Returns 404 for deleted user

**PATCH /api/v1/users/me**
- [ ] Updates display name successfully
- [ ] Updates avatar URL successfully
- [ ] Updates bio successfully
- [ ] Returns 400 for invalid display name
- [ ] Returns 400 for invalid URL
- [ ] Returns 422 for bio > 500 characters
- [ ] Rate limits to 5 updates/hour

**GET /api/v1/users/me/stats**
- [ ] Returns correct aggregated statistics
- [ ] Returns 0 for new users
- [ ] Handles large datasets efficiently
- [ ] Returns 401 for invalid token

**POST /api/v1/users/me/change-password**
- [ ] Changes password successfully
- [ ] Returns 401 for incorrect current password
- [ ] Returns 400 for weak new password
- [ ] Returns 422 for mismatched passwords
- [ ] Rate limits to 3 attempts/hour
- [ ] Invalidates all refresh tokens
- [ ] Sends email notification

**DELETE /api/v1/users/me**
- [ ] Marks account for deletion
- [ ] Returns 401 for incorrect password
- [ ] Sends confirmation email
- [ ] Allows cancellation within 30 days
- [ ] Hard deletes after 30 days
- [ ] Anonymizes retained content

### 5.2 Integration Testing

**Test Scenarios:**
1. Complete user lifecycle: register → verify → update profile → change password → delete account
2. Rate limiting behavior for password changes
3. Account deletion cancellation flow
4. Token invalidation after password change
5. CORS preflight requests from production URL

### 5.3 API Documentation

**Required:** Update Swagger/OpenAPI docs at `/docs`

Ensure all 5 new endpoints appear in:
- `/api/v1/docs` (Swagger UI)
- `/api/v1/redoc` (ReDoc)
- `/api/v1/openapi.json` (OpenAPI spec)

---

## 6. Deployment Checklist

### 6.1 Pre-Deployment (Backend)

- [ ] All 5 user profile endpoints implemented
- [ ] Type alignment fixes applied (has_synthesis, average_credibility_score, average_read_minutes)
- [ ] CORS configuration updated with production URLs
- [ ] Rate limiting configured for sensitive endpoints
- [ ] Database migrations applied (if schema changes needed)
- [ ] Unit tests passing (>80% coverage on new endpoints)
- [ ] Integration tests passing
- [ ] API documentation updated (Swagger/OpenAPI)
- [ ] Error handling standardized (consistent error response format)
- [ ] Logging configured (log all password changes, deletions)
- [ ] Security audit passed (no SQL injection, XSS vulnerabilities)

### 6.2 Deployment Day (Backend)

- [ ] Deploy to staging first
- [ ] Run smoke tests on staging
- [ ] Verify CORS from frontend staging URL
- [ ] Test each endpoint with Postman/curl
- [ ] Monitor error logs for 30 minutes
- [ ] If staging clean, deploy to production
- [ ] Verify production CORS from frontend production URL
- [ ] Monitor error rates (< 1% expected)
- [ ] Check database query performance
- [ ] Notify frontend team of deployment completion

### 6.3 Post-Deployment Validation (Coordinated)

**Backend Team:**
- [ ] Monitor API error rates
- [ ] Check database connection pool
- [ ] Review slow query logs
- [ ] Verify rate limiting working

**Frontend Team:**
- [ ] Test all 5 profile features in production
- [ ] Verify no CORS errors
- [ ] Check authentication flow
- [ ] Monitor Sentry for frontend errors

**Coordinated:**
- [ ] End-to-end test: Register → Update Profile → Change Password → Delete Account
- [ ] Performance test: Profile page load time < 2s
- [ ] Security test: Token refresh works correctly

---

## 7. Timeline & Effort Estimate

### Development Effort

| Task | Priority | Estimated Hours | Dependencies |
|------|----------|----------------|--------------|
| Implement GET /users/me | Critical | 2-3h | Database query optimization |
| Implement PATCH /users/me | Critical | 3-4h | Field validation, rate limiting |
| Implement GET /users/me/stats | High | 4-6h | Complex aggregation queries |
| Implement POST /change-password | Critical | 3-4h | Token invalidation logic |
| Implement DELETE /users/me | Critical | 4-6h | Soft delete logic, GDPR compliance |
| Fix type alignment issues | High | 1h | None |
| Update CORS configuration | High | 1h | Production URL known |
| Write unit tests | High | 4-6h | Endpoints complete |
| Write integration tests | Medium | 2-3h | Endpoints complete |
| Update API documentation | Medium | 1-2h | Endpoints complete |
| **Total** | | **25-35 hours** | **~5-7 business days** |

### Recommended Schedule

**Week 1 (Backend Focus):**
- **Day 1-2:** Implement GET /users/me, PATCH /users/me
- **Day 3:** Implement GET /users/me/stats
- **Day 4:** Implement POST /change-password
- **Day 5:** Implement DELETE /users/me

**Week 2 (Testing & Deployment):**
- **Day 1:** Fix type alignment, update CORS
- **Day 2:** Write unit tests, fix bugs
- **Day 3:** Write integration tests, update docs
- **Day 4:** Deploy to staging, coordinate with frontend team
- **Day 5:** Deploy to production, monitor

---

## 8. Communication & Coordination

### Backend Team Responsibilities

1. **Notify frontend team** when each endpoint is ready for testing
2. **Provide staging environment** for integration testing
3. **Document any breaking changes** in API response format
4. **Share database schema changes** if any migrations needed
5. **Coordinate deployment window** with frontend team

### Frontend Team Responsibilities

1. **Test each endpoint** as it becomes available on staging
2. **Report bugs** with detailed reproduction steps
3. **Verify type definitions** match actual API responses
4. **Provide production URL** for CORS allowlist
5. **Coordinate deployment timing** for simultaneous release

### Collaboration Channels

- **Slack/Discord:** #backend-frontend-coordination
- **GitHub Issues:** Tag with `backend-coordination` label
- **Shared Docs:** This document + BACKEND_API_REQUIREMENTS.md
- **Weekly Sync:** 30-minute meeting to review progress

---

## 9. API Response Format Standards

### Success Response Format

All successful responses should follow this structure:

```json
{
  "success": true,
  "data": { /* actual response data */ },
  "meta": {
    "timestamp": "2025-01-26T14:30:00Z",
    "version": "1.0.0"
  }
}
```

### Error Response Format

All error responses should follow this structure:

```json
{
  "success": false,
  "error": {
    "code": "INVALID_PASSWORD",
    "message": "Password must be at least 8 characters",
    "details": {
      "field": "new_password",
      "constraint": "min_length"
    }
  },
  "meta": {
    "timestamp": "2025-01-26T14:30:00Z",
    "request_id": "req_abc123"
  }
}
```

**Standard Error Codes:**
- `INVALID_TOKEN` - JWT token invalid/expired
- `INVALID_PASSWORD` - Password validation failed
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `INVALID_INPUT` - Request validation failed
- `NOT_FOUND` - Resource not found
- `INTERNAL_ERROR` - Server error

---

## 10. Security Checklist

### Authentication & Authorization

- [ ] All endpoints require valid JWT token
- [ ] Token expiry properly enforced (15 minutes access token)
- [ ] Refresh token rotation implemented
- [ ] Password hashing uses BCrypt (cost factor 12+)
- [ ] No passwords logged in plain text

### Input Validation

- [ ] All user inputs sanitized (prevent XSS)
- [ ] SQL injection prevented (use parameterized queries)
- [ ] File uploads validated (type, size, content)
- [ ] URL validation prevents SSRF attacks
- [ ] HTML/script tags stripped from bio/display name

### Rate Limiting

- [ ] Password changes: 3/hour per user
- [ ] Profile updates: 5/hour per user
- [ ] Account deletions: 1/day per user
- [ ] Login attempts: 5/15min per IP

### Logging & Monitoring

- [ ] All password changes logged (user_id, timestamp, IP)
- [ ] All account deletions logged (user_id, reason, timestamp)
- [ ] Failed authentication attempts logged
- [ ] Sensitive data (passwords) never logged
- [ ] Error logs include request_id for tracing

---

## 11. Database Schema Requirements

### Users Table Updates (if needed)

Ensure the `users` table has these fields:

```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  username VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  display_name VARCHAR(100),
  avatar_url VARCHAR(500),
  bio TEXT,
  karma INTEGER DEFAULT 0,
  is_verified BOOLEAN DEFAULT FALSE,
  is_active BOOLEAN DEFAULT TRUE,
  role VARCHAR(20) DEFAULT 'user',
  pending_deletion BOOLEAN DEFAULT FALSE,
  deletion_scheduled_at TIMESTAMP NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_pending_deletion ON users(pending_deletion);
```

### New Tables (if needed)

**User Statistics Cache (Optional - for performance)**
```sql
CREATE TABLE user_stats_cache (
  user_id INTEGER PRIMARY KEY REFERENCES users(id),
  total_articles_read INTEGER DEFAULT 0,
  total_comments INTEGER DEFAULT 0,
  total_votes INTEGER DEFAULT 0,
  total_bookmarks INTEGER DEFAULT 0,
  reading_streak_days INTEGER DEFAULT 0,
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Password Change Log (for security audit)**
```sql
CREATE TABLE password_changes (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ip_address INET,
  user_agent TEXT
);
```

---

## 12. Success Criteria

### Must-Have (Go/No-Go)

- ✅ All 5 user profile endpoints implemented and tested
- ✅ Type alignment issues fixed (has_synthesis, field names)
- ✅ CORS configuration allows production frontend URL
- ✅ Unit test coverage > 80% on new endpoints
- ✅ API documentation updated (Swagger/OpenAPI)
- ✅ Security audit passed (no critical vulnerabilities)
- ✅ Integration tests passing on staging
- ✅ Performance acceptable (< 500ms response time for profile endpoints)

### Should-Have

- ✅ Rate limiting configured for sensitive endpoints
- ✅ Error logging configured for all endpoints
- ✅ Database query optimization (< 100ms for stats endpoint)
- ✅ Email notifications for password changes and deletions
- ✅ Monitoring dashboards configured

### Nice-to-Have

- ⚪ Avatar upload endpoint implemented
- ⚪ Email change endpoint implemented
- ⚪ User stats cache table for performance
- ⚪ Automated integration tests in CI/CD

---

## 13. Contact & Questions

### Backend Team Lead
- **Name:** [To be filled]
- **Email:** [To be filled]
- **Slack:** [To be filled]

### Frontend Team Lead
- **Name:** EJ (User)
- **GitHub:** Number531/RSS-Frontend

### Documentation
- **Frontend Types:** `frontend/types/api.ts`
- **Frontend Hooks:** `frontend/lib/hooks/use-users.ts`
- **Frontend API Client:** `frontend/lib/api/client.ts`
- **Previous Requirements:** `BACKEND_API_REQUIREMENTS.md` (1,242 lines)

---

## Appendix A: Postman Collection

Import this collection to test all endpoints:

```json
{
  "info": {
    "name": "RSS News Feed - User Profile API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Get Current User",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}"
          }
        ],
        "url": {
          "raw": "{{base_url}}/users/me",
          "host": ["{{base_url}}"],
          "path": ["users", "me"]
        }
      }
    },
    {
      "name": "Update Profile",
      "request": {
        "method": "PATCH",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}"
          },
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"display_name\": \"John Smith\",\n  \"bio\": \"Updated bio\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/users/me",
          "host": ["{{base_url}}"],
          "path": ["users", "me"]
        }
      }
    },
    {
      "name": "Get User Stats",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}"
          }
        ],
        "url": {
          "raw": "{{base_url}}/users/me/stats",
          "host": ["{{base_url}}"],
          "path": ["users", "me", "stats"]
        }
      }
    },
    {
      "name": "Change Password",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}"
          },
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"current_password\": \"OldPassword123!\",\n  \"new_password\": \"NewPassword456!\",\n  \"confirm_password\": \"NewPassword456!\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/users/me/change-password",
          "host": ["{{base_url}}"],
          "path": ["users", "me", "change-password"]
        }
      }
    },
    {
      "name": "Delete Account",
      "request": {
        "method": "DELETE",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}"
          },
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"password\": \"UserPassword123!\",\n  \"confirmation\": \"DELETE MY ACCOUNT\",\n  \"reason\": \"Testing\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/users/me",
          "host": ["{{base_url}}"],
          "path": ["users", "me"]
        }
      }
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000/api/v1"
    },
    {
      "key": "access_token",
      "value": "your_jwt_token_here"
    }
  ]
}
```

---

**Document End**

**Next Actions:**
1. Backend team reviews and confirms timeline
2. Frontend team provides production URL for CORS
3. Weekly sync meetings scheduled
4. Backend implementation begins
5. Frontend monitors #backend-coordination Slack channel

**Questions?** Contact frontend team lead or create GitHub issue with `backend-coordination` label.
