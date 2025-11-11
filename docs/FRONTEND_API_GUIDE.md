# Frontend API Integration Guide

**Version**: 1.0  
**Last Updated**: November 11, 2025  
**Base URL**: `http://localhost:8000/api/v1` (Development)  
**Production URL**: `https://your-domain.com/api/v1`

This guide covers all newly implemented API endpoints for frontend integration. For authentication and existing CRUD endpoints, see the main API documentation at `/docs`.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Analytics Endpoints](#analytics-endpoints)
3. [Reputation & Gamification](#reputation--gamification)
4. [Health & Monitoring](#health--monitoring)
5. [Cache Management](#cache-management)
6. [Social Features](#social-features)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)

---

## Authentication

Most endpoints support optional authentication. Include JWT token in header when available:

```javascript
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${accessToken}` // Optional for most endpoints
};
```

**Getting an Access Token**:
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password"
}

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

## Analytics Endpoints

### 1. Article Performance Metrics

**Endpoint**: `GET /api/v1/analytics/articles/{article_id}/performance`

**Purpose**: Get comprehensive performance analytics for a specific article.

**Authentication**: Optional

**Parameters**:
- `article_id` (path parameter, required): UUID of the article

**Frontend Usage**:
```javascript
async function getArticlePerformance(articleId) {
  const response = await fetch(
    `${BASE_URL}/analytics/articles/${articleId}/performance`,
    { method: 'GET' }
  );
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  
  return await response.json();
}
```

**Response Structure**:
```typescript
interface ArticlePerformance {
  article_id: string;
  views: {
    total_views: number;
    unique_views: number;
    direct_views: number;
    rss_views: number;
    search_views: number;
  };
  engagement: {
    avg_read_time_seconds: number;
    avg_scroll_percentage: number;  // 0-100
    completion_rate: number;         // 0-1
  };
  social: {
    bookmark_count: number;
    share_count: number;
    vote_score: number;
    comment_count: number;
  };
  trending_score: number;            // Reddit hot algorithm score
  performance_percentile: number;    // 0-100, higher = better
  last_calculated_at: string;        // ISO 8601 timestamp
}
```

**Example Response**:
```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "views": {
    "total_views": 1250,
    "unique_views": 980,
    "direct_views": 650,
    "rss_views": 200,
    "search_views": 400
  },
  "engagement": {
    "avg_read_time_seconds": 180,
    "avg_scroll_percentage": 75.5,
    "completion_rate": 0.68
  },
  "social": {
    "bookmark_count": 45,
    "share_count": 12,
    "vote_score": 156,
    "comment_count": 23
  },
  "trending_score": 87.23,
  "performance_percentile": 92,
  "last_calculated_at": "2025-11-11T20:30:00Z"
}
```

**UI Display Suggestions**:
- Show trending score as a badge ("Hot", "Trending")
- Display engagement metrics in a progress bar
- Use performance percentile for ranking indicators
- Show social counts as action buttons (bookmark, comment, vote)

---

### 2. Content Quality Score

**Endpoint**: `GET /api/v1/analytics/content-quality`

**Purpose**: Get content quality analysis across articles with recommendations.

**Authentication**: Optional

**Query Parameters**:
| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `days` | integer | 7 | 1-365 | Number of days to analyze |
| `category` | string | null | - | Filter by article category |
| `min_engagement` | integer | 5 | 1-100 | Minimum engagement threshold |

**Frontend Usage**:
```javascript
async function getContentQuality(options = {}) {
  const params = new URLSearchParams({
    days: options.days || 7,
    min_engagement: options.minEngagement || 5
  });
  
  if (options.category) {
    params.append('category', options.category);
  }
  
  const response = await fetch(
    `${BASE_URL}/analytics/content-quality?${params}`,
    { method: 'GET' }
  );
  
  return await response.json();
}
```

**Response Structure**:
```typescript
interface ContentQualityReport {
  period_days: number;
  category: string | null;
  total_articles: number;
  articles_analyzed: number;
  min_engagement_threshold: number;
  quality_metrics: {
    avg_quality_score: number;        // 0-100
    median_quality_score: number;     // 0-100
    avg_vote_ratio: number;           // 0-1
    avg_comments_per_article: number;
    total_engagement: number;
    quality_distribution: {
      "excellent (80+)": number;
      "good (60-79)": number;
      "average (40-59)": number;
      "poor (<40)": number;
    };
  };
  top_performers: Article[];
  recommendations: Recommendation[];
  generated_at: string;
}

interface Article {
  article_id: string;
  title: string;
  url: string;
  published_at: string | null;
  category: string;
  metrics: {
    votes_count: number;
    upvotes: number;
    downvotes: number;
    vote_ratio: number;
    comments_count: number;
    bookmarks_count: number;
    controversy_score: number;
  };
  quality_score: number;
  total_engagement: number;
}

interface Recommendation {
  type: "quality_improvement" | "category_optimization" | "engagement_insight" | "sentiment_alert";
  priority: "high" | "medium" | "info";
  message: string;
  action: string;
}
```

**Example Response**:
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
      "title": "AI Breakthrough in Medical Research",
      "url": "https://example.com/article",
      "published_at": "2025-11-05T10:30:00Z",
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
  "generated_at": "2025-11-11T16:00:00Z"
}
```

**UI Display Suggestions**:
- Display quality distribution as a pie/donut chart
- Show top performers in a ranked list
- Display recommendations as actionable cards with priority badges
- Use quality scores for visual indicators (colors, badges)

---

## Reputation & Gamification

### 3. User Leaderboard

**Endpoint**: `GET /api/v1/reputation/leaderboard`

**Purpose**: Get top users ranked by reputation score.

**Authentication**: Optional

**Query Parameters**:
| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `limit` | integer | 50 | 1-100 | Number of users to return |

**Frontend Usage**:
```javascript
async function getLeaderboard(limit = 50) {
  const response = await fetch(
    `${BASE_URL}/reputation/leaderboard?limit=${limit}`,
    { method: 'GET' }
  );
  
  return await response.json();
}
```

**Response Structure**:
```typescript
interface LeaderboardResponse {
  leaderboard: LeaderboardUser[];
  total_users: number;
  limit: number;
}

interface LeaderboardUser {
  rank: number;
  user_id: string;
  username: string;
  full_name: string | null;
  avatar_url: string | null;
  reputation_score: number;
  stats: {
    votes_received: number;
    comments_posted: number;
    bookmarks_received: number;
  };
  member_since: string | null;
}
```

**Example Response**:
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "user_id": "770e8400-e29b-41d4-a716-446655440002",
      "username": "johndoe",
      "full_name": "John Doe",
      "avatar_url": "https://example.com/avatar.jpg",
      "reputation_score": 1250,
      "stats": {
        "votes_received": 100,
        "comments_posted": 50,
        "bookmarks_received": 10
      },
      "member_since": "2025-01-15T10:00:00Z"
    }
  ],
  "total_users": 50,
  "limit": 50
}
```

**Reputation Formula**:
```
Reputation Score = (Votes × 10) + (Comments × 5) + (Bookmarks × 15)
```

**UI Display Suggestions**:
- Display as ranked table with position badges (🥇🥈🥉)
- Show avatar thumbnails
- Display reputation score with progress bar
- Add "View Profile" action for each user
- Highlight current user if in leaderboard

**React Component Example**:
```jsx
function Leaderboard() {
  const [users, setUsers] = useState([]);
  
  useEffect(() => {
    getLeaderboard(10).then(data => setUsers(data.leaderboard));
  }, []);
  
  return (
    <div className="leaderboard">
      {users.map(user => (
        <div key={user.user_id} className="leaderboard-item">
          <span className="rank">#{user.rank}</span>
          <img src={user.avatar_url} alt={user.username} />
          <span className="username">{user.username}</span>
          <span className="score">{user.reputation_score} pts</span>
        </div>
      ))}
    </div>
  );
}
```

---

### 4. User Reputation Details

**Endpoint**: `GET /api/v1/reputation/users/{user_id}`

**Purpose**: Get detailed reputation for a specific user.

**Authentication**: Optional

**Parameters**:
- `user_id` (path parameter, required): UUID of the user

**Frontend Usage**:
```javascript
async function getUserReputation(userId) {
  const response = await fetch(
    `${BASE_URL}/reputation/users/${userId}`,
    { method: 'GET' }
  );
  
  if (response.status === 404) {
    throw new Error('User not found');
  }
  
  return await response.json();
}
```

**Response Structure**:
```typescript
interface UserReputation {
  user_id: string;
  username: string;
  reputation_score: number;
  rank: number | null;
  stats: {
    votes_received: number;
    comments_posted: number;
    bookmarks_received: number;
  };
  badges: string[];
}
```

**Example Response**:
```json
{
  "user_id": "770e8400-e29b-41d4-a716-446655440002",
  "username": "johndoe",
  "reputation_score": 1250,
  "rank": 5,
  "stats": {
    "votes_received": 100,
    "comments_posted": 50,
    "bookmarks_received": 10
  },
  "badges": ["expert", "commentator", "voter"]
}
```

**Badge Levels**:
| Badge | Requirement | Icon Suggestion |
|-------|------------|-----------------|
| `expert` | 1000+ reputation | ⭐ Gold star |
| `veteran` | 500+ reputation | 🎖️ Medal |
| `contributor` | 100+ reputation | ✅ Checkmark |
| `commentator` | 100+ comments | 💬 Speech bubble |
| `voter` | 50+ votes | 👍 Thumbs up |

**UI Display Suggestions**:
- Display badges as icons or colored pills
- Show reputation with progress bar to next level
- Display global rank prominently
- Show contribution breakdown as stats cards

---

## Health & Monitoring

### 5. Enhanced Health Check

**Endpoint**: `GET /api/v1/health/detailed`

**Purpose**: Get comprehensive system health status.

**Authentication**: None (public endpoint)

**Frontend Usage**:
```javascript
async function getSystemHealth() {
  const response = await fetch(
    `${BASE_URL}/health/detailed`,
    { method: 'GET' }
  );
  
  return await response.json();
}
```

**Response Structure**:
```typescript
interface HealthStatus {
  status: "healthy" | "degraded";
  timestamp: number;
  components: {
    database: ComponentHealth;
    redis: ComponentHealth;
    api: ComponentHealth;
  };
}

interface ComponentHealth {
  status: "healthy" | "unhealthy" | "unknown";
  response_time_ms?: number;
  pool_size?: number;
  pool_overflow?: number;
  used_memory_mb?: number;
  connected_clients?: number;
  message: string;
  error?: string;
}
```

**Example Response**:
```json
{
  "status": "healthy",
  "timestamp": 1762898452.040868,
  "components": {
    "database": {
      "status": "healthy",
      "response_time_ms": 257.75,
      "pool_size": 3,
      "pool_overflow": -2,
      "message": "Database connection OK"
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 1.23,
      "used_memory_mb": 12.45,
      "connected_clients": 5,
      "message": "Redis connection OK"
    },
    "api": {
      "status": "healthy",
      "message": "API server responding"
    }
  }
}
```

**UI Display Suggestions**:
- Display as status dashboard with color indicators
- Green = healthy, Yellow = degraded, Red = unhealthy
- Show response times with performance indicators
- Use for system status page or admin dashboard
- Poll every 30-60 seconds for real-time monitoring

---

## Cache Management

### 6. Clear Cache

**Endpoint**: `POST /api/v1/cache/clear`

**Purpose**: Manually clear the application cache.

**Authentication**: Admin recommended (production)

**Frontend Usage**:
```javascript
async function clearCache(token) {
  const response = await fetch(
    `${BASE_URL}/cache/clear`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  return await response.json();
}
```

**Response Structure**:
```typescript
interface CacheClearResponse {
  status: "success";
  message: string;
  keys_cleared: number;
}
```

**Example Response**:
```json
{
  "status": "success",
  "message": "Cache cleared successfully",
  "keys_cleared": 1250
}
```

**UI Display Suggestions**:
- Show as admin action button
- Display confirmation dialog before clearing
- Show success toast notification
- Display number of keys cleared

---

### 7. Cache Statistics

**Endpoint**: `GET /api/v1/cache/stats`

**Purpose**: Get Redis cache statistics.

**Authentication**: Optional

**Frontend Usage**:
```javascript
async function getCacheStats() {
  const response = await fetch(
    `${BASE_URL}/cache/stats`,
    { method: 'GET' }
  );
  
  return await response.json();
}
```

**Response Structure**:
```typescript
interface CacheStats {
  status: "healthy" | "unavailable";
  message?: string;
  stats: {
    memory_used_mb: number;
    total_keys: number;
    hit_rate: number;           // 0-1
    evicted_keys?: number;
    connections?: number;
  };
}
```

**Example Response**:
```json
{
  "status": "healthy",
  "stats": {
    "memory_used_mb": 45.2,
    "total_keys": 1250,
    "hit_rate": 0.87,
    "evicted_keys": 15,
    "connections": 8
  }
}
```

**UI Display Suggestions**:
- Display memory usage as progress bar
- Show hit rate as percentage
- Use for admin monitoring dashboard

---

## Social Features

### 8. Comment Mentions

**Feature**: Automatic @username mention detection in comments.

**How It Works**:
When a user posts a comment with `@username`, the system:
1. Automatically parses the mention
2. Creates a mention record in the database
3. Sends a notification to the mentioned user

**Frontend Implementation**:

**Creating a Comment with Mentions**:
```javascript
async function createComment(articleId, content, token) {
  // Content can include @username mentions
  const response = await fetch(
    `${BASE_URL}/comments`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        article_id: articleId,
        content: content,  // e.g., "Hey @alice, check this out!"
        parent_comment_id: null
      })
    }
  );
  
  return await response.json();
}
```

**Mention Syntax**:
- Valid: `@username` (3-30 characters)
- Must start with letter or number
- Can contain letters, numbers, underscores, hyphens
- Examples: `@john`, `@jane_doe`, `@bob-smith`, `@user123`

**UI Implementation Suggestions**:

**1. Mention Autocomplete**:
```jsx
function CommentInput() {
  const [content, setContent] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  
  const handleInput = (text) => {
    setContent(text);
    
    // Detect @ symbol and show user suggestions
    const lastAtPosition = text.lastIndexOf('@');
    if (lastAtPosition !== -1) {
      const searchTerm = text.substring(lastAtPosition + 1);
      if (searchTerm.length > 0) {
        fetchUserSuggestions(searchTerm).then(setSuggestions);
      }
    }
  };
  
  return (
    <div>
      <textarea value={content} onChange={(e) => handleInput(e.target.value)} />
      {suggestions.length > 0 && (
        <UserSuggestionDropdown users={suggestions} />
      )}
    </div>
  );
}
```

**2. Mention Highlighting**:
```jsx
function CommentContent({ content }) {
  // Highlight mentions in displayed comments
  const highlightMentions = (text) => {
    return text.replace(
      /@([a-zA-Z0-9][a-zA-Z0-9_-]{2,29})/g,
      '<span class="mention">@$1</span>'
    );
  };
  
  return (
    <div 
      dangerouslySetInnerHTML={{ 
        __html: highlightMentions(content) 
      }} 
    />
  );
}
```

**3. Mention Notifications**:
Users will receive notifications when mentioned. Fetch notifications via:
```javascript
async function getUserNotifications(token) {
  const response = await fetch(
    `${BASE_URL}/notifications`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  
  return await response.json();
}
```

---

## Error Handling

### Standard Error Response

All endpoints return consistent error responses:

```typescript
interface ErrorResponse {
  detail: string | object;
}
```

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response data |
| 400 | Bad Request | Show validation error to user |
| 401 | Unauthorized | Redirect to login |
| 403 | Forbidden | Show "Access Denied" message |
| 404 | Not Found | Show "Not Found" message |
| 422 | Validation Error | Show field-specific errors |
| 429 | Rate Limited | Show "Too Many Requests" |
| 500 | Server Error | Show generic error message |

### Frontend Error Handling Example

```javascript
async function apiRequest(url, options = {}) {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const error = await response.json();
      
      switch (response.status) {
        case 401:
          // Redirect to login
          window.location.href = '/login';
          break;
        case 404:
          throw new Error('Resource not found');
        case 429:
          throw new Error('Too many requests. Please try again later.');
        case 500:
          throw new Error('Server error. Please try again.');
        default:
          throw new Error(error.detail || 'An error occurred');
      }
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}
```

---

## Rate Limiting

**Current Limits**: Not enforced in development

**Production Recommendations**:
- Anonymous users: 100 requests/minute
- Authenticated users: 1000 requests/minute
- Admin users: 5000 requests/minute

**Handling Rate Limits**:
```javascript
async function apiRequestWithRetry(url, options = {}, retries = 3) {
  try {
    return await apiRequest(url, options);
  } catch (error) {
    if (error.message.includes('Too many requests') && retries > 0) {
      // Wait 1 second and retry
      await new Promise(resolve => setTimeout(resolve, 1000));
      return apiRequestWithRetry(url, options, retries - 1);
    }
    throw error;
  }
}
```

---

## Best Practices

### 1. Caching Strategies

**Client-Side Caching**:
```javascript
// Cache leaderboard for 5 minutes
const CACHE_DURATION = 5 * 60 * 1000;
let leaderboardCache = null;
let cacheTime = 0;

async function getLeaderboardCached() {
  const now = Date.now();
  
  if (leaderboardCache && (now - cacheTime) < CACHE_DURATION) {
    return leaderboardCache;
  }
  
  leaderboardCache = await getLeaderboard();
  cacheTime = now;
  
  return leaderboardCache;
}
```

### 2. Loading States

```jsx
function DataComponent() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    getData()
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);
  
  if (loading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;
  if (!data) return <EmptyState />;
  
  return <DataDisplay data={data} />;
}
```

### 3. Polling for Real-Time Data

```javascript
function useRealtimeHealth(interval = 30000) {
  const [health, setHealth] = useState(null);
  
  useEffect(() => {
    const fetchHealth = () => {
      getSystemHealth().then(setHealth).catch(console.error);
    };
    
    fetchHealth(); // Initial fetch
    const timer = setInterval(fetchHealth, interval);
    
    return () => clearInterval(timer);
  }, [interval]);
  
  return health;
}
```

### 4. TypeScript Integration

```typescript
// types/api.ts
export interface ApiResponse<T> {
  data: T;
  error?: string;
}

export async function apiGet<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`);
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  
  return await response.json();
}

// Usage
const leaderboard = await apiGet<LeaderboardResponse>('/reputation/leaderboard');
```

---

## Testing

### Example Test Cases

```javascript
describe('Analytics API', () => {
  test('should fetch article performance', async () => {
    const articleId = '550e8400-e29b-41d4-a716-446655440000';
    const data = await getArticlePerformance(articleId);
    
    expect(data).toHaveProperty('article_id');
    expect(data).toHaveProperty('views');
    expect(data).toHaveProperty('engagement');
    expect(data.trending_score).toBeGreaterThanOrEqual(0);
  });
  
  test('should fetch content quality report', async () => {
    const data = await getContentQuality({ days: 7 });
    
    expect(data).toHaveProperty('quality_metrics');
    expect(data).toHaveProperty('top_performers');
    expect(data.quality_metrics.avg_quality_score).toBeGreaterThanOrEqual(0);
    expect(data.quality_metrics.avg_quality_score).toBeLessThanOrEqual(100);
  });
});
```

---

## Quick Reference

### All New Endpoints

```
# Analytics
GET    /api/v1/analytics/articles/{id}/performance
GET    /api/v1/analytics/content-quality

# Reputation
GET    /api/v1/reputation/leaderboard
GET    /api/v1/reputation/users/{user_id}

# Health & Cache
GET    /api/v1/health/detailed
POST   /api/v1/cache/clear
GET    /api/v1/cache/stats

# Social (integrated into existing endpoints)
POST   /api/v1/comments  (with @mention support)
```

### Response Time Expectations

| Endpoint | Typical | Max |
|----------|---------|-----|
| Article Performance | 50ms | 150ms |
| Content Quality | 500ms | 1000ms |
| Leaderboard | 150ms | 300ms |
| User Reputation | 100ms | 200ms |
| Health Check | 250ms | 500ms |
| Cache Operations | 10ms | 50ms |

---

## Support

**Documentation**: `http://localhost:8000/docs` (Interactive API docs)

**Common Issues**:
1. **CORS errors**: Ensure backend CORS is configured for your frontend domain
2. **401 Unauthorized**: Token expired, refresh the access token
3. **404 Not Found**: Check article/user ID format (must be valid UUID)
4. **Empty responses**: Database may not have data yet in development

**Contact**: Backend team for API issues or questions

---

## Changelog

**Version 1.0** (November 11, 2025):
- Initial release
- 8 new endpoints documented
- Complete TypeScript interfaces
- React examples provided
- Error handling guidelines
