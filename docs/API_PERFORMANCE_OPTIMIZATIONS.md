# API Performance Optimizations

## Overview
This document describes the performance optimizations implemented to improve frontend experience, reduce latency, and handle higher loads.

## Implementation Date
December 2024

---

## 1. HTTP Caching with ETag and Cache-Control Headers

### Problem
- Every request was fetching fresh data from the database
- High latency for users with slow connections
- Increased database load for unchanged content
- CDN couldn't cache responses effectively

### Solution
Added HTTP caching headers to key GET endpoints:

#### Article Detail Endpoint (`GET /api/v1/articles/{article_id}`)
```http
Cache-Control: public, max-age=300, s-maxage=300
ETag: "1672531200.0"
```

- **Cache-Control**: 
  - `public`: Response can be cached by browsers and CDNs
  - `max-age=300`: Browser caches for 5 minutes
  - `s-maxage=300`: CDN caches for 5 minutes
  
- **ETag**: 
  - Generated from article's `updated_at` timestamp
  - Enables 304 Not Modified responses if content unchanged
  - Client sends `If-None-Match` header on subsequent requests

#### Article Feed Endpoint (`GET /api/v1/articles/`)
```http
Cache-Control: public, max-age=60, s-maxage=60
```

- Shorter cache time (1 minute) for frequently changing feed content
- Balances freshness with performance

### Benefits
- **Reduced bandwidth**: 304 responses have no body
- **Lower latency**: Browser serves from cache instantly
- **Decreased database load**: Fewer queries for unchanged content
- **CDN efficiency**: CDN can serve cached responses

### Usage Example
```javascript
// First request
fetch('/api/v1/articles/550e8400-e29b-41d4-a716-446655440000')
// Response: 200 OK with full data + ETag header

// Second request (within 5 minutes)
fetch('/api/v1/articles/550e8400-e29b-41d4-a716-446655440000')
// Browser sends If-None-Match header automatically
// Response: 304 Not Modified (no body, uses cached data)
```

---

## 2. Increased Database Connection Pool Size

### Problem
- Default pool size of 20 connections
- Frontend makes multiple concurrent requests per page
- Connection exhaustion under moderate load
- Request queueing and timeout errors

### Solution
Increased connection pool configuration:

**Before:**
```python
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 0
```

**After:**
```python
DATABASE_POOL_SIZE = 50
DATABASE_MAX_OVERFLOW = 10
```

### Configuration
Updated in both:
1. `app/core/config.py` (default values)
2. `.env` file (environment override)

### Benefits
- **60 max connections** (50 pool + 10 overflow)
- Supports 60 concurrent requests without queueing
- Better performance under load
- Reduced connection wait times

### Recommendations for Production
- **Monitor connection usage** via database metrics
- **Adjust based on load**: Supabase Free Tier allows 60 connections
- **Consider connection pooling** at infrastructure level (e.g., PgBouncer)

---

## 3. Combined Full Article Endpoint

### Problem
Frontend article detail page required 4 separate API calls:
1. `GET /articles/{id}` - Article details
2. `GET /articles/{id}/vote` - User's vote status
3. `GET /articles/{id}/comments` - Top comments
4. `GET /articles/{id}/fact-check` - Fact-check data

**Issues:**
- High latency due to sequential requests (waterfall effect)
- Mobile users experience slow page loads
- 4x network overhead (headers, TLS handshakes, etc.)
- Increased battery consumption on mobile

### Solution
Created new combined endpoint: `GET /api/v1/articles/{article_id}/full`

Returns all data in a single request:
```json
{
  "article": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Article Title",
    "url": "https://example.com",
    "description": "Article description...",
    "vote_score": 42,
    "comment_count": 15,
    ...
  },
  "user_vote": "upvote",
  "comments": [
    {
      "id": "...",
      "content": "Great article!",
      "vote_score": 10,
      ...
    }
  ],
  "fact_check": {
    "verdict": "TRUE",
    "credibility_score": 87,
    "summary": "Fact-check summary...",
    ...
  }
}
```

### Implementation Details
- **Non-blocking**: Uses graceful error handling for optional data
- **Top 10 comments**: Only fetches first page (page_size=10)
- **Authenticated users**: Includes user_vote if logged in
- **Fact-check optional**: Returns null if not available
- **Caching**: Includes ETag and Cache-Control headers (1 minute)

### Code Location
- **Endpoint**: `app/api/v1/endpoints/articles.py::get_article_full()`
- **Dependencies**: Uses existing services (ArticleService, CommentService, VoteService, FactCheckService)
- **Position**: Placed BEFORE `/{article_id}` route to avoid conflicts

### Benefits
- **~75% latency reduction**: 1 request instead of 4
- **Better mobile experience**: Faster page loads
- **Reduced server load**: Single database transaction
- **Lower network overhead**: 1 TLS handshake vs 4

### Usage Example

**Before (4 requests):**
```javascript
const article = await fetch(`/api/v1/articles/${id}`);
const vote = await fetch(`/api/v1/articles/${id}/vote`);
const comments = await fetch(`/api/v1/articles/${id}/comments?page=1&page_size=10`);
const factCheck = await fetch(`/api/v1/articles/${id}/fact-check`);
// Total time: ~400ms (100ms per request on good connection)
```

**After (1 request):**
```javascript
const { article, user_vote, comments, fact_check } = await fetch(`/api/v1/articles/${id}/full`);
// Total time: ~100ms (single request)
```

---

## Performance Metrics

### Expected Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Article detail page load | 400ms | 100ms | 75% faster |
| Repeated page views | Full load | 304 cached | ~95% faster |
| Database queries/page | 4-6 | 1-2 | 50-75% reduction |
| Network requests/page | 4+ | 1 | 75% reduction |
| Concurrent user capacity | ~20 | ~60 | 3x increase |

### Cache Hit Rates (Expected)
- **Article detail**: ~60-80% (content changes infrequently)
- **Article feed**: ~30-50% (updates every minute)

---

## Testing

### Manual Testing
```bash
# Test ETag and Cache-Control headers
curl -I http://localhost:8000/api/v1/articles/550e8400-e29b-41d4-a716-446655440000

# Test 304 Not Modified response
ETAG=$(curl -sI http://localhost:8000/api/v1/articles/${ID} | grep -i etag | cut -d' ' -f2)
curl -H "If-None-Match: $ETAG" -I http://localhost:8000/api/v1/articles/${ID}

# Test combined endpoint
curl http://localhost:8000/api/v1/articles/550e8400-e29b-41d4-a716-446655440000/full
```

### Load Testing
```bash
# Test connection pool under load
ab -n 1000 -c 50 http://localhost:8000/api/v1/articles/

# Monitor connection usage
# In Supabase dashboard: Database > Connection Pooling
```

---

## Migration Guide for Frontend

### Switching to Combined Endpoint

**Current Implementation:**
```javascript
const fetchArticleDetails = async (articleId) => {
  const article = await api.get(`/articles/${articleId}`);
  const vote = await api.get(`/articles/${articleId}/vote`);
  const comments = await api.get(`/articles/${articleId}/comments?page=1&page_size=10`);
  const factCheck = await api.get(`/articles/${articleId}/fact-check`);
  
  return { article, vote, comments, factCheck };
};
```

**Optimized Implementation:**
```javascript
const fetchArticleDetails = async (articleId) => {
  const data = await api.get(`/articles/${articleId}/full`);
  
  // All data available in single response
  return data;
};
```

### Enabling Browser Caching
No changes needed! Modern browsers automatically handle:
- ETag-based conditional requests
- Cache-Control directives

For React/Next.js:
```javascript
// Use SWR or React Query for automatic caching
import useSWR from 'swr';

function Article({ id }) {
  const { data, error } = useSWR(`/api/v1/articles/${id}/full`, fetcher, {
    revalidateOnFocus: false,
    revalidateOnReconnect: false,
  });
  
  // SWR respects Cache-Control headers automatically
}
```

---

## Monitoring

### Key Metrics to Track

1. **Cache Hit Rate**
   - Monitor CDN analytics
   - Track 304 vs 200 response ratio
   - Target: >50% cache hits for detail pages

2. **Database Connection Usage**
   - Supabase Dashboard > Database > Connection Pooling
   - Alert if connections exceed 50 (approaching limit)

3. **API Latency**
   - P50, P95, P99 response times
   - Compare `/articles/{id}` vs `/articles/{id}/full`

4. **Error Rates**
   - Watch for connection timeout errors
   - Monitor 429 rate limit responses

### Supabase Monitoring
```sql
-- Check active connections
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE datname = 'postgres';

-- Check connection pool usage
SELECT * FROM pg_stat_database 
WHERE datname = 'postgres';
```

---

## Future Optimizations

### Short-term (Next Sprint)
- [ ] Add Redis caching layer for hot articles
- [ ] Implement GraphQL for flexible data fetching
- [ ] Add pagination to combined endpoint comments

### Medium-term (Next Quarter)
- [ ] Implement CDN (Cloudflare/Fastly)
- [ ] Add read replicas for heavy read operations
- [ ] Implement database query result caching

### Long-term (Future)
- [ ] Move to microservices architecture
- [ ] Implement edge caching with Vercel/Netlify
- [ ] Add service worker for offline support

---

## Related Documentation
- [Database Schema](./DATABASE_SCHEMA.md)
- [API Endpoints](../README.md#api-endpoints)
- [Deployment Guide](./DEPLOYMENT.md)

---

## Changelog

### 2024-12-XX - Initial Implementation
- ✅ Added ETag and Cache-Control headers to article endpoints
- ✅ Increased database connection pool from 20 to 50
- ✅ Created combined `/articles/{id}/full` endpoint
- ✅ Updated dependencies to support fact check service

### Future Updates
Track changes here as optimizations are refined based on production metrics.
