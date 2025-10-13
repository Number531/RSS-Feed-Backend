# Reading History API - Quick Reference

## 🚀 Base URL
```
http://localhost:8000/api/v1/reading-history
```

## 🔐 Authentication
All endpoints require Bearer token authentication:
```
Authorization: Bearer <your_access_token>
```

## 📍 Endpoints

### 1. Record Article View
Track when a user views an article with optional engagement metrics.

```bash
POST /api/v1/reading-history/

# Request Body (JSON)
{
  "article_id": "uuid",           # Required
  "duration_seconds": 120,        # Optional: reading time
  "scroll_percentage": 85.5       # Optional: 0-100
}

# Response: 201 Created
{
  "id": "uuid",
  "user_id": "uuid",
  "article_id": "uuid",
  "viewed_at": "2025-10-10T20:00:00",
  "duration_seconds": 120,
  "scroll_percentage": 85.5
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/reading-history/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": "123e4567-e89b-12d3-a456-426614174000",
    "duration_seconds": 120,
    "scroll_percentage": 85.5
  }'
```

---

### 2. Get Reading History
Retrieve paginated reading history with optional date filtering.

```bash
GET /api/v1/reading-history/?skip=0&limit=20&start_date=<iso>&end_date=<iso>

# Query Parameters
skip            # Number of records to skip (default: 0)
limit           # Max records to return (1-100, default: 20)
start_date      # Filter: views after this date (ISO 8601)
end_date        # Filter: views before this date (ISO 8601)

# Response: 200 OK
{
  "items": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "article_id": "uuid",
      "viewed_at": "2025-10-10T20:00:00",
      "duration_seconds": 120,
      "scroll_percentage": 85.5,
      "article_title": "Article Title",
      "article_url": "https://example.com/article",
      "article_published_at": "2025-10-10T10:00:00"
    }
  ],
  "total": 42,
  "skip": 0,
  "limit": 20
}
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/reading-history/?skip=0&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 3. Get Recently Read Articles
Get articles read within a specified number of days.

```bash
GET /api/v1/reading-history/recent?days=7&limit=10

# Query Parameters
days      # Days to look back (1-365, default: 7)
limit     # Max articles to return (1-50, default: 10)

# Response: 200 OK
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "article_id": "uuid",
    "viewed_at": "2025-10-10T20:00:00",
    "duration_seconds": 120,
    "scroll_percentage": 85.5,
    "article_title": "Recent Article",
    "article_url": "https://...",
    "article_published_at": "2025-10-10T10:00:00"
  }
]
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/reading-history/recent?days=7&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 4. Get Reading Statistics
Get reading statistics with optional date range.

```bash
GET /api/v1/reading-history/stats?start_date=<iso>&end_date=<iso>

# Query Parameters
start_date    # Optional: stats period start (ISO 8601)
end_date      # Optional: stats period end (ISO 8601)

# Response: 200 OK
{
  "total_views": 42,
  "total_reading_time_seconds": 5400,
  "average_reading_time_seconds": 128.57,
  "period_start": "2025-10-01T00:00:00",
  "period_end": "2025-10-10T23:59:59"
}
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/reading-history/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 5. Clear Reading History
Delete reading history (all or before a specific date).

```bash
DELETE /api/v1/reading-history/

# Request Body (JSON) - Optional
{
  "before_date": "2025-10-01T00:00:00"  # Optional: only clear before this date
}

# Response: 200 OK
{
  "deleted_count": 25,
  "message": "Successfully cleared 25 history record(s) before 2025-10-01T00:00:00"
}
```

**cURL Example (Clear All):**
```bash
curl -X DELETE http://localhost:8000/api/v1/reading-history/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**cURL Example (Clear Before Date):**
```bash
curl -X DELETE http://localhost:8000/api/v1/reading-history/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"before_date": "2025-10-01T00:00:00"}'
```

---

## ⚠️ Error Codes

| Code | Description |
|------|-------------|
| 400  | Bad Request - Invalid parameters or validation failed |
| 401  | Unauthorized - Missing or invalid auth token |
| 404  | Not Found - Article doesn't exist |
| 422  | Unprocessable Entity - Schema validation failed |
| 500  | Internal Server Error |

### Common Error Responses

**Invalid Scroll Percentage:**
```json
{
  "detail": "Scroll percentage must be between 0 and 100"
}
```

**Invalid Pagination:**
```json
{
  "detail": "Limit must be between 1 and 100"
}
```

**Article Not Found:**
```json
{
  "detail": "Article with ID xxx not found"
}
```

---

## 📊 Python Client Example

```python
import httpx
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "your_access_token"

headers = {"Authorization": f"Bearer {TOKEN}"}

async with httpx.AsyncClient() as client:
    # Record a view
    response = await client.post(
        f"{BASE_URL}/reading-history/",
        headers=headers,
        json={
            "article_id": "article-uuid",
            "duration_seconds": 180,
            "scroll_percentage": 92.5
        }
    )
    print(response.json())
    
    # Get history
    response = await client.get(
        f"{BASE_URL}/reading-history/",
        headers=headers,
        params={"skip": 0, "limit": 20}
    )
    history = response.json()
    print(f"Total views: {history['total']}")
    
    # Get stats
    response = await client.get(
        f"{BASE_URL}/reading-history/stats",
        headers=headers
    )
    stats = response.json()
    print(f"Average reading time: {stats['average_reading_time_seconds']}s")
```

---

## 🧪 Testing

### Run Repository Tests
```bash
python test_reading_history_repository.py
```

### Run API Integration Tests
```bash
# Start server first
uvicorn app.main:app --reload

# In another terminal
python test_reading_history_api.py
```

---

## 💡 Tips

1. **Tracking Reading Progress**: Record views with `duration_seconds` when user leaves article page
2. **Engagement Metrics**: Use `scroll_percentage` to understand content engagement
3. **Privacy**: Allow users to clear history regularly
4. **Analytics**: Use stats endpoint for user dashboard
5. **Performance**: Use pagination for large history lists
6. **Date Filtering**: Combine with date ranges for time-based analysis

---

## 📚 Related Documentation
- [Full Implementation Guide](./READING_HISTORY_IMPLEMENTATION.md)
- [API Swagger Docs](http://localhost:8000/docs)
- [API ReDoc](http://localhost:8000/redoc)
