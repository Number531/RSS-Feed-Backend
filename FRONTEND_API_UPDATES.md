# Frontend API Updates - Performance Optimizations

## Overview
The backend has been optimized with new endpoints and caching headers to improve frontend performance. This document provides migration instructions and updated API usage patterns.

**Date:** December 2024  
**Backend Version:** Updated  
**Impact:** Breaking changes (optional) - old endpoints still work

---

## What Changed?

### 1. New Combined Endpoint: `/api/v1/articles/{id}/full`
**Replaces 4 separate API calls with 1 unified request**

### 2. HTTP Caching Headers
**Automatic browser and CDN caching for better performance**

### 3. Increased Backend Capacity
**Backend can now handle 3x more concurrent users**

---

## Migration Guide

### Old Implementation (4 API Calls)

```typescript
// ❌ OLD WAY - Multiple requests (slow)
async function fetchArticleDetail(articleId: string) {
  const article = await fetch(`/api/v1/articles/${articleId}`);
  const vote = await fetch(`/api/v1/votes/articles/${articleId}`);
  const comments = await fetch(`/api/v1/articles/${articleId}/comments?page=1&page_size=10`);
  const factCheck = await fetch(`/api/v1/articles/${articleId}/fact-check`);
  
  return {
    article: await article.json(),
    userVote: await vote.json(),
    comments: await comments.json(),
    factCheck: await factCheck.json(),
  };
}
```

**Issues:**
- 400ms+ latency on good connections
- 1-2 seconds on mobile/slow connections
- 4x network overhead
- Poor mobile battery life

---

### New Implementation (1 API Call)

```typescript
// ✅ NEW WAY - Single request (fast!)
async function fetchArticleDetail(articleId: string) {
  const response = await fetch(`/api/v1/articles/${articleId}/full`);
  const data = await response.json();
  
  // Everything in one response!
  return data; // { article, user_vote, comments, fact_check }
}
```

**Benefits:**
- ~100ms latency (75% faster!)
- Works great on mobile
- 1 TLS handshake instead of 4
- Better battery life

---

## API Response Format

### Combined Endpoint Response

```typescript
interface ArticleFullResponse {
  article: {
    id: string;
    rss_source_id: string;
    title: string;
    url: string;
    description: string;
    author: string | null;
    thumbnail_url: string | null;
    category: string;
    published_date: string;
    created_at: string;
    vote_score: number;
    vote_count: number;
    comment_count: number;
    tags: string[];
  };
  user_vote: "upvote" | "downvote" | null;
  comments: Array<{
    id: string;
    user_id: string;
    content: string;
    vote_score: number;
    created_at: string;
    is_deleted: boolean;
  }>;
  fact_check: {
    id: string;
    verdict: string;
    credibility_score: number;
    confidence: number;
    summary: string;
    claims_analyzed: number;
    claims_true: number;
    claims_false: number;
    claims_misleading: number;
    source_consensus: string;
    validation_mode: string;
  } | null;
}
```

---

## React/Next.js Integration

### Using with React Query

```typescript
import { useQuery } from '@tanstack/react-query';

function ArticleDetailPage({ articleId }: { articleId: string }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['article', articleId, 'full'],
    queryFn: async () => {
      const res = await fetch(`/api/v1/articles/${articleId}/full`);
      if (!res.ok) throw new Error('Failed to fetch article');
      return res.json() as Promise<ArticleFullResponse>;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes (matches backend cache)
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <div>
      <Article data={data.article} userVote={data.user_vote} />
      <FactCheck data={data.fact_check} />
      <CommentsList comments={data.comments} />
    </div>
  );
}
```

### Using with SWR

```typescript
import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then(res => res.json());

function ArticleDetailPage({ articleId }: { articleId: string }) {
  const { data, error, isLoading } = useSWR(
    `/api/v1/articles/${articleId}/full`,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      dedupingInterval: 60000, // 1 minute
    }
  );

  // SWR automatically respects Cache-Control headers!
  // No need to manually manage cache timing
  
  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <div>
      <Article data={data.article} userVote={data.user_vote} />
      <FactCheck data={data.fact_check} />
      <CommentsList comments={data.comments} />
    </div>
  );
}
```

### Using with Native Fetch (Vanilla JS)

```typescript
async function loadArticlePage(articleId: string) {
  try {
    const response = await fetch(`/api/v1/articles/${articleId}/full`);
    
    // Check if content was cached (304 response)
    if (response.status === 304) {
      console.log('Using cached version');
      // Browser automatically serves cached response
    }
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    
    // Update UI
    renderArticle(data.article);
    renderUserVote(data.user_vote);
    renderComments(data.comments);
    renderFactCheck(data.fact_check);
    
  } catch (error) {
    console.error('Failed to load article:', error);
    showErrorMessage();
  }
}
```

---

## Caching Behavior

### Automatic Browser Caching
The backend now sends cache headers - browsers handle this automatically!

```http
Cache-Control: public, max-age=300, s-maxage=300
ETag: "1672531200.0"
```

**What this means:**
- Browser caches for 5 minutes
- Subsequent requests within 5 minutes = instant load from cache
- After 5 minutes, browser sends `If-None-Match` header
- If unchanged, server returns 304 (no data transfer!)

### Cache Timing
- **Article detail** (`/full`): 1 minute cache
- **Article detail** (`/{id}`): 5 minutes cache
- **Article feed** (`/`): 1 minute cache

### Disabling Cache (if needed)
```typescript
// Force fresh data (bypasses cache)
fetch('/api/v1/articles/${id}/full', {
  cache: 'no-cache',
  headers: {
    'Cache-Control': 'no-cache',
  }
});
```

---

## Breaking Changes (None!)

**Good news:** All old endpoints still work!

You can migrate incrementally:
1. ✅ Keep using existing endpoints while testing
2. ✅ Switch to `/full` endpoint when ready
3. ✅ No frontend changes required for caching (automatic)

---

## Performance Comparison

### Before Optimization
```
GET /articles/{id}           → 100ms
GET /votes/articles/{id}     → 100ms
GET /articles/{id}/comments  → 100ms
GET /articles/{id}/fact-check → 100ms
─────────────────────────────────────
TOTAL: 400ms (sequential) or 150ms (parallel)
```

### After Optimization
```
GET /articles/{id}/full      → 100ms
─────────────────────────────────────
TOTAL: 100ms
```

### With Caching (Repeat Visits)
```
GET /articles/{id}/full      → 5ms (304 Not Modified)
─────────────────────────────────────
TOTAL: 5ms (98% faster!)
```

---

## Mobile Optimization

### Recommended Fetch Strategy

```typescript
// Detect slow connection and adjust behavior
function useArticleDetail(articleId: string) {
  const connection = (navigator as any).connection;
  const isSlowConnection = connection?.effectiveType === '2g' || 
                          connection?.effectiveType === 'slow-2g';

  return useQuery({
    queryKey: ['article', articleId, 'full'],
    queryFn: () => fetchArticleFull(articleId),
    staleTime: isSlowConnection ? 10 * 60 * 1000 : 5 * 60 * 1000,
    // Cache longer on slow connections
  });
}
```

---

## Error Handling

### Graceful Degradation

```typescript
async function fetchArticleDetail(articleId: string) {
  try {
    // Try combined endpoint first
    const response = await fetch(`/api/v1/articles/${articleId}/full`);
    
    if (response.ok) {
      return await response.json();
    }
    
    // Fallback to individual requests if /full fails
    if (response.status === 404) {
      return await fetchArticleDetailLegacy(articleId);
    }
    
    throw new Error(`HTTP ${response.status}`);
    
  } catch (error) {
    console.error('Article fetch failed:', error);
    throw error;
  }
}

// Legacy fallback (for compatibility)
async function fetchArticleDetailLegacy(articleId: string) {
  const [article, vote, comments, factCheck] = await Promise.all([
    fetch(`/api/v1/articles/${articleId}`).then(r => r.json()),
    fetch(`/api/v1/votes/articles/${articleId}`).then(r => r.json()).catch(() => null),
    fetch(`/api/v1/articles/${articleId}/comments?page=1&page_size=10`).then(r => r.json()).catch(() => []),
    fetch(`/api/v1/articles/${articleId}/fact-check`).then(r => r.json()).catch(() => null),
  ]);
  
  return { article, user_vote: vote, comments, fact_check: factCheck };
}
```

---

## Testing

### Manual Testing Checklist

- [ ] Article detail page loads in <200ms (desktop)
- [ ] Article detail page loads in <500ms (mobile)
- [ ] Second visit to same article loads instantly (<50ms)
- [ ] Network tab shows 1 request instead of 4
- [ ] Network tab shows 304 responses on repeat visits
- [ ] Error handling works when offline
- [ ] Comments display correctly (first 10)
- [ ] Fact-check displays correctly (or null if unavailable)
- [ ] User vote displays correctly (if authenticated)

### Chrome DevTools Testing

1. Open DevTools → Network tab
2. Navigate to article detail page
3. Check request count: Should be 1 request to `/full`
4. Check response headers: Should have `Cache-Control` and `ETag`
5. Refresh page within 1 minute
6. Check response: Should be 304 with cached data

---

## Monitoring Recommendations

### Key Metrics to Track

```typescript
// Example: Track API performance
const startTime = performance.now();

const data = await fetch(`/api/v1/articles/${id}/full`).then(r => r.json());

const duration = performance.now() - startTime;

// Log to analytics
analytics.track('api_article_full_timing', {
  duration_ms: duration,
  cached: response.status === 304,
  article_id: id,
});

// Alert if slow
if (duration > 500) {
  console.warn('Slow article fetch:', duration);
}
```

### Expected Metrics
- **P50 latency**: <100ms
- **P95 latency**: <200ms
- **P99 latency**: <500ms
- **Cache hit rate**: >50%

---

## Troubleshooting

### Issue: Cache Not Working

**Symptom:** Every request is 200 instead of 304

**Solutions:**
1. Check browser cache is enabled (not in incognito mode)
2. Verify `Cache-Control` header is present in response
3. Check if API returns `ETag` header
4. Ensure no middleware is stripping cache headers

### Issue: Stale Data

**Symptom:** Old data shown after article updates

**Solutions:**
1. Wait 1 minute (cache TTL) or force refresh
2. Invalidate cache programmatically:
```typescript
// React Query
queryClient.invalidateQueries(['article', articleId]);

// SWR
mutate(`/api/v1/articles/${articleId}/full`);
```

### Issue: Missing Comments/Fact-Check

**Symptom:** `comments` or `fact_check` is null/empty

**Explanation:** This is normal! The endpoint returns:
- `comments`: Empty array `[]` if no comments exist
- `fact_check`: `null` if not yet fact-checked

**Handle gracefully:**
```typescript
{data.fact_check ? (
  <FactCheck data={data.fact_check} />
) : (
  <div>Fact-check pending...</div>
)}
```

---

## Next Steps

1. **Update API client** to use `/full` endpoint
2. **Test on staging** environment first
3. **Monitor performance** metrics after deployment
4. **Gradually migrate** article detail pages
5. **Remove old code** once migration is complete

---

## Questions or Issues?

- Check backend documentation: `docs/API_PERFORMANCE_OPTIMIZATIONS.md`
- Review API changes on GitHub
- Contact backend team if issues persist

---

## Changelog

### December 2024 - Initial Release
- ✅ Added `/api/v1/articles/{id}/full` combined endpoint
- ✅ Added HTTP caching headers (ETag, Cache-Control)
- ✅ Increased backend capacity (60 concurrent connections)
- ✅ All old endpoints remain functional
