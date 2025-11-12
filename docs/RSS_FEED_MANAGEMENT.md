# RSS Feed Management API - Frontend Guide

**Updated**: November 12, 2025  
**Base URL**: `http://localhost:8000/api/v1/feeds`

## Quick Start

The RSS feed endpoints are now **PUBLIC** - no authentication required for viewing feeds. Users can browse all available RSS feeds before signing up or logging in.

---

## Public Endpoints (No Authentication Required)

### 1. List All RSS Feeds

**Endpoint**: `GET /api/v1/feeds`

**Purpose**: Get all available RSS feeds with pagination.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-indexed) |
| `page_size` | integer | 50 | Items per page (max 100) |
| `category` | string | null | Filter by category (e.g., "technology", "politics") |
| `is_active` | boolean | true* | Filter by active status |

*Note: Defaults to `true` for unauthenticated users to show only active feeds.

**Example Request**:
```javascript
// Get all active feeds
const response = await fetch('http://localhost:8000/api/v1/feeds');
const data = await response.json();

// Filter by category
const techFeeds = await fetch('http://localhost:8000/api/v1/feeds?category=technology');

// Pagination
const page2 = await fetch('http://localhost:8000/api/v1/feeds?page=2&page_size=20');
```

**Response Structure**:
```typescript
interface FeedListResponse {
  sources: RSSFeed[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface RSSFeed {
  id: string;                        // UUID
  name: string;                      // Display name
  url: string;                       // RSS feed URL
  source_name: string;               // Source organization (e.g., "CNN")
  category: string;                  // Category (e.g., "technology")
  is_active: boolean;                // Whether feed is active
  last_fetched: string | null;      // ISO timestamp
  last_successful_fetch: string | null;
  fetch_success_count: number;
  fetch_failure_count: number;
  consecutive_failures: number;
  success_rate: number;              // 0-100
  is_healthy: boolean;               // Health status
  created_at: string;                // ISO timestamp
  updated_at: string;                // ISO timestamp
}
```

**Example Response**:
```json
{
  "sources": [
    {
      "id": "1a9000cd-da7f-42b9-b201-2a44749d9ece",
      "name": "Fox News - Politics",
      "url": "http://feeds.foxnews.com/foxnews/politics",
      "source_name": "Fox News",
      "category": "politics",
      "is_active": true,
      "last_fetched": null,
      "last_successful_fetch": null,
      "fetch_success_count": 0,
      "fetch_failure_count": 0,
      "consecutive_failures": 0,
      "success_rate": 0,
      "is_healthy": false,
      "created_at": "2025-11-10T21:20:31.634917Z",
      "updated_at": "2025-11-10T21:20:31.634920Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 50,
  "total_pages": 1
}
```

---

### 2. Get Feed Categories

**Endpoint**: `GET /api/v1/feeds/categories`

**Purpose**: Get all available feed categories with statistics.

**Example Request**:
```javascript
const response = await fetch('http://localhost:8000/api/v1/feeds/categories');
const categories = await response.json();
```

**Response Structure**:
```typescript
interface FeedCategory {
  category: string;      // Category name
  count: number;        // Total feeds in category
  active_count: number; // Active feeds in category
}
```

**Example Response**:
```json
[
  {
    "category": "politics",
    "count": 1,
    "active_count": 1
  },
  {
    "category": "technology",
    "count": 5,
    "active_count": 4
  }
]
```

**UI Suggestion**: Use this to create category filter buttons or dropdown menus.

---

### 3. Get Specific Feed Details

**Endpoint**: `GET /api/v1/feeds/{feed_id}`

**Purpose**: Get detailed information about a specific RSS feed.

**Example Request**:
```javascript
const feedId = '1a9000cd-da7f-42b9-b201-2a44749d9ece';
const response = await fetch(`http://localhost:8000/api/v1/feeds/${feedId}`);
const feed = await response.json();
```

**Response**: Same structure as single `RSSFeed` object from list endpoint.

---

## User Subscription Endpoints (Authentication Required)

Once users are logged in, they can subscribe to feeds to customize their homepage.

### 4. Subscribe to Feed

**Endpoint**: `POST /api/v1/feeds/{feed_id}/subscribe`

**Authentication**: Required

**Example Request**:
```javascript
const feedId = '1a9000cd-da7f-42b9-b201-2a44749d9ece';

const response = await fetch(
  `http://localhost:8000/api/v1/feeds/${feedId}/subscribe`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      notifications_enabled: true  // Optional, default: true
    })
  }
);

const subscription = await response.json();
```

**Response Structure**:
```typescript
interface Subscription {
  id: string;
  user_id: string;
  feed_id: string;
  is_active: boolean;
  notifications_enabled: boolean;
  created_at: string;
  updated_at: string;
  feed: RSSFeed;  // Full feed details
}
```

---

### 5. Unsubscribe from Feed

**Endpoint**: `DELETE /api/v1/feeds/{feed_id}/unsubscribe`

**Authentication**: Required

**Example Request**:
```javascript
const feedId = '1a9000cd-da7f-42b9-b201-2a44749d9ece';

await fetch(
  `http://localhost:8000/api/v1/feeds/${feedId}/unsubscribe`,
  {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  }
);
```

**Response**:
```json
{
  "message": "Successfully unsubscribed from feed"
}
```

---

### 6. Get My Subscriptions

**Endpoint**: `GET /api/v1/feeds/subscriptions`

**Authentication**: Required

**Purpose**: Get all feeds the current user is subscribed to.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `page_size` | integer | 50 | Items per page (max 100) |
| `is_active` | boolean | null | Filter by active status |

**Example Request**:
```javascript
const response = await fetch(
  'http://localhost:8000/api/v1/feeds/subscriptions',
  {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  }
);

const myFeeds = await response.json();
```

**Response Structure**:
```typescript
interface SubscriptionListResponse {
  subscriptions: Subscription[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
```

---

### 7. Get Subscribed Feed IDs (Quick Check)

**Endpoint**: `GET /api/v1/feeds/subscribed`

**Authentication**: Required

**Purpose**: Get array of feed IDs user is subscribed to (for quick UI state updates).

**Example Request**:
```javascript
const response = await fetch(
  'http://localhost:8000/api/v1/feeds/subscribed',
  {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  }
);

const subscribedIds = await response.json();
// Returns: ["feed-uuid-1", "feed-uuid-2", ...]
```

**Use Case**: Check if user is subscribed to show "Subscribe" vs "Unsubscribe" button.

```javascript
const isSubscribed = subscribedIds.includes(feedId);
```

---

### 8. Update Subscription Preferences

**Endpoint**: `PUT /api/v1/feeds/{feed_id}/subscription`

**Authentication**: Required

**Purpose**: Update notification settings for a subscribed feed.

**Example Request**:
```javascript
const feedId = '1a9000cd-da7f-42b9-b201-2a44749d9ece';

const response = await fetch(
  `http://localhost:8000/api/v1/feeds/${feedId}/subscription`,
  {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      is_active: true,              // Optional
      notifications_enabled: false  // Optional: turn off notifications
    })
  }
);

const updatedSubscription = await response.json();
```

---

## Admin Endpoints (Admin Authentication Required)

### 9. Create New Feed

**Endpoint**: `POST /api/v1/feeds`

**Authentication**: Admin required

**Example Request**:
```javascript
const response = await fetch(
  'http://localhost:8000/api/v1/feeds',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${adminToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: "TechCrunch",
      url: "https://techcrunch.com/feed/",
      source_name: "TechCrunch",
      category: "technology",
      is_active: true
    })
  }
);

const newFeed = await response.json();
```

---

### 10. Update Feed

**Endpoint**: `PUT /api/v1/feeds/{feed_id}`

**Authentication**: Admin required

**Example Request**:
```javascript
const feedId = '1a9000cd-da7f-42b9-b201-2a44749d9ece';

const response = await fetch(
  `http://localhost:8000/api/v1/feeds/${feedId}`,
  {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${adminToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      is_active: false  // Deactivate feed
    })
  }
);

const updatedFeed = await response.json();
```

---

### 11. Delete Feed

**Endpoint**: `DELETE /api/v1/feeds/{feed_id}`

**Authentication**: Admin required

**Warning**: This will delete all articles associated with the feed.

**Example Request**:
```javascript
const feedId = '1a9000cd-da7f-42b9-b201-2a44749d9ece';

await fetch(
  `http://localhost:8000/api/v1/feeds/${feedId}`,
  {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${adminToken}`
    }
  }
);
```

---

## Frontend Implementation Examples

### Feed Browser Component (Public)

```jsx
function FeedBrowser() {
  const [feeds, setFeeds] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  
  useEffect(() => {
    // Load categories for filter
    fetch('http://localhost:8000/api/v1/feeds/categories')
      .then(res => res.json())
      .then(setCategories);
    
    // Load feeds
    const url = selectedCategory
      ? `http://localhost:8000/api/v1/feeds?category=${selectedCategory}`
      : 'http://localhost:8000/api/v1/feeds';
    
    fetch(url)
      .then(res => res.json())
      .then(data => setFeeds(data.sources));
  }, [selectedCategory]);
  
  return (
    <div>
      <CategoryFilter 
        categories={categories} 
        onSelect={setSelectedCategory} 
      />
      <FeedList feeds={feeds} />
    </div>
  );
}
```

### Subscription Toggle Component (Authenticated)

```jsx
function SubscriptionButton({ feedId, accessToken }) {
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    // Check if user is subscribed
    fetch('http://localhost:8000/api/v1/feeds/subscribed', {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    })
      .then(res => res.json())
      .then(ids => setIsSubscribed(ids.includes(feedId)));
  }, [feedId, accessToken]);
  
  const toggleSubscription = async () => {
    setLoading(true);
    
    const endpoint = isSubscribed ? 'unsubscribe' : 'subscribe';
    const method = isSubscribed ? 'DELETE' : 'POST';
    
    await fetch(
      `http://localhost:8000/api/v1/feeds/${feedId}/${endpoint}`,
      {
        method,
        headers: { 'Authorization': `Bearer ${accessToken}` }
      }
    );
    
    setIsSubscribed(!isSubscribed);
    setLoading(false);
  };
  
  return (
    <button onClick={toggleSubscription} disabled={loading}>
      {isSubscribed ? 'Unsubscribe' : 'Subscribe'}
    </button>
  );
}
```

### My Feeds Component (Authenticated)

```jsx
function MyFeeds({ accessToken }) {
  const [subscriptions, setSubscriptions] = useState([]);
  
  useEffect(() => {
    fetch('http://localhost:8000/api/v1/feeds/subscriptions', {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    })
      .then(res => res.json())
      .then(data => setSubscriptions(data.subscriptions));
  }, [accessToken]);
  
  return (
    <div>
      <h2>My Subscribed Feeds ({subscriptions.length})</h2>
      {subscriptions.map(sub => (
        <FeedCard 
          key={sub.id} 
          feed={sub.feed}
          subscription={sub}
        />
      ))}
    </div>
  );
}
```

---

## Testing

### Test Public Access
```bash
# List feeds (no auth)
curl http://localhost:8000/api/v1/feeds

# Get categories (no auth)
curl http://localhost:8000/api/v1/feeds/categories

# Filter by category (no auth)
curl 'http://localhost:8000/api/v1/feeds?category=technology'
```

### Test Authenticated Access
```bash
# Login first
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.access_token')

# Get my subscriptions
curl http://localhost:8000/api/v1/feeds/subscriptions \
  -H "Authorization: Bearer $TOKEN"

# Subscribe to feed
curl -X POST http://localhost:8000/api/v1/feeds/FEED_ID/subscribe \
  -H "Authorization: Bearer $TOKEN"
```

---

## Common Issues

### Issue: "Not authenticated" error
**Solution**: The listing endpoints are now public. Make sure you're using the latest code (commit `41ab90c`).

### Issue: Can't see any feeds
**Solution**: Check if feeds exist in database. Use the admin endpoints to create feeds if needed.

### Issue: Subscription not working
**Solution**: Ensure user is logged in and access token is valid. Subscriptions require authentication.

---

## Summary

**Public Endpoints** (No auth needed):
- ✅ `GET /api/v1/feeds` - List all feeds
- ✅ `GET /api/v1/feeds/categories` - List categories
- ✅ `GET /api/v1/feeds/{feed_id}` - Get feed details

**User Endpoints** (Auth required):
- 🔐 `GET /api/v1/feeds/subscriptions` - My subscriptions
- 🔐 `GET /api/v1/feeds/subscribed` - My subscribed feed IDs
- 🔐 `POST /api/v1/feeds/{feed_id}/subscribe` - Subscribe
- 🔐 `DELETE /api/v1/feeds/{feed_id}/unsubscribe` - Unsubscribe
- 🔐 `PUT /api/v1/feeds/{feed_id}/subscription` - Update preferences

**Admin Endpoints** (Admin auth required):
- 👑 `POST /api/v1/feeds` - Create feed
- 👑 `PUT /api/v1/feeds/{feed_id}` - Update feed
- 👑 `DELETE /api/v1/feeds/{feed_id}` - Delete feed

---

**Server**: Running on `http://localhost:8000`  
**API Docs**: `http://localhost:8000/docs`  
**Commit**: `41ab90c`
