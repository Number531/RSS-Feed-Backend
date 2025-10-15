# Celery Workers & Admin Dashboard Guide

**Complete guide for setting up and using Celery background workers with the Admin Dashboard**

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Celery Setup](#celery-setup)
3. [Admin Dashboard API](#admin-dashboard-api)
4. [How It Works](#how-it-works)
5. [Monitoring & Troubleshooting](#monitoring--troubleshooting)

---

## 🚀 Quick Start

### Prerequisites

1. **Redis running** (required for Celery)
2. **API server running** (for Admin Dashboard)
3. **Admin user created** (for accessing admin endpoints)

### Start Everything

```bash
# Terminal 1: Start Redis (if not running)
docker-compose -f docker/docker-compose.dev.yml up -d redis
# OR
brew services start redis  # macOS with Homebrew

# Terminal 2: Start API server
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 3: Start Celery workers
./scripts/start_celery.sh

# ✅ Done! RSS feeds will now be fetched every 15 minutes automatically
```

---

## 🔧 Celery Setup

### What is Celery?

Celery is a distributed task queue that handles background jobs. In this project, it:
- **Fetches RSS feeds every 15 minutes** (scheduled task)
- **Processes articles** in parallel for faster updates
- **Retries failed fetches** automatically
- **Runs independently** from the API server

### Starting Celery

#### Option 1: Background Mode (Production-like)

```bash
./scripts/start_celery.sh
```

This starts:
- **Celery Worker** - Processes tasks in background
- **Celery Beat** - Schedules periodic tasks

Check status:
```bash
# View logs
tail -f logs/celery_worker.log
tail -f logs/celery_beat.log

# Check if running
ps aux | grep celery
```

Stop:
```bash
./scripts/stop_celery.sh
```

#### Option 2: Foreground Mode (Development/Debugging)

```bash
./scripts/start_celery.sh --foreground
```

This starts both worker and beat in one terminal window. Useful for:
- Debugging
- Seeing real-time log output
- Development

Press `Ctrl+C` to stop.

### Celery Configuration

Located in `app/core/celery_app.py`:

```python
# Schedule - Fetch feeds every 15 minutes
celery_app.conf.beat_schedule = {
    "fetch-all-rss-feeds": {
        "task": "app.tasks.rss_tasks.fetch_all_feeds",
        "schedule": 900,  # seconds
    },
}
```

To change frequency, edit `CELERY_BEAT_SCHEDULE_INTERVAL` in `.env`:
```env
CELERY_BEAT_SCHEDULE_INTERVAL=900  # 15 minutes
# Or:
CELERY_BEAT_SCHEDULE_INTERVAL=300  # 5 minutes
CELERY_BEAT_SCHEDULE_INTERVAL=1800  # 30 minutes
```

---

## 🎛️ Admin Dashboard API

### Authentication

All admin endpoints require:
1. Valid JWT token
2. User with `is_superuser=True`

```bash
# Create admin user (if not exists)
python scripts/create_admin.py

# Login to get token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"your_password"}'

# Use the returned access_token in subsequent requests
export TOKEN="your_access_token_here"
```

### Admin Endpoints

#### 1. Check Celery Status

```bash
GET /api/v1/admin/celery/status
```

Response:
```json
{
  "celery_available": true,
  "active_workers": ["celery@hostname"],
  "worker_count": 1,
  "registered_tasks": [
    "app.tasks.rss_tasks.fetch_all_feeds",
    "app.tasks.rss_tasks.fetch_single_feed"
  ],
  "worker_stats": {...}
}
```

#### 2. Manually Trigger Feed Fetch (All Feeds)

```bash
POST /api/v1/admin/celery/fetch-now
Authorization: Bearer {TOKEN}
```

Response:
```json
{
  "status": "dispatched",
  "task_id": "abc123...",
  "message": "RSS feed fetch initiated",
  "check_status_url": "/api/v1/admin/celery/task/abc123..."
}
```

**Use Case:** Force immediate fetch without waiting for schedule

#### 3. Fetch Single Feed

```bash
POST /api/v1/admin/celery/fetch-feed/{feed_id}
Authorization: Bearer {TOKEN}
```

**Use Case:** Test or refresh a specific feed

#### 4. Check Task Status

```bash
GET /api/v1/admin/celery/task/{task_id}
Authorization: Bearer {TOKEN}
```

Response:
```json
{
  "task_id": "abc123...",
  "status": "SUCCESS",
  "ready": true,
  "successful": true,
  "result": {
    "status": "success",
    "source_name": "TechCrunch",
    "articles_created": 12,
    "articles_skipped": 3
  }
}
```

**Use Case:** Monitor progress of manual fetch

#### 5. View Active Tasks

```bash
GET /api/v1/admin/celery/active-tasks
Authorization: Bearer {TOKEN}
```

**Use Case:** See what's currently being processed

#### 6. RSS Feed Health Dashboard

```bash
GET /api/v1/admin/feeds/health
Authorization: Bearer {TOKEN}
```

Response:
```json
{
  "total_sources": 44,
  "healthy": 42,
  "unhealthy": 2,
  "inactive": 0,
  "health_rate": 0.954,
  "unhealthy_feeds": [
    {
      "id": "uuid",
      "name": "Broken Feed",
      "url": "https://...",
      "success_rate": 0.45,
      "last_fetch_status": "error",
      "last_fetched_at": "2025-01-15T10:00:00Z"
    }
  ]
}
```

**Use Case:** Monitor which feeds are failing

#### 7. System Overview

```bash
GET /api/v1/admin/stats/overview
Authorization: Bearer {TOKEN}
```

Response:
```json
{
  "users": {"total": 150},
  "articles": {"total": 5420},
  "rss_sources": {
    "total": 44,
    "active": 44,
    "inactive": 0
  }
}
```

#### 8. Create RSS Source

```bash
POST /api/v1/admin/feeds
Authorization: Bearer {TOKEN}
Content-Type: application/json

{
  "name": "New Tech Blog",
  "url": "https://example.com/feed.xml",
  "source_name": "Example Blog",
  "category": "technology",
  "description": "Latest tech news",
  "is_active": true
}
```

#### 9. Update RSS Source

```bash
PUT /api/v1/admin/feeds/{feed_id}
Authorization: Bearer {TOKEN}
Content-Type: application/json

{
  "is_active": false,
  "description": "Updated description"
}
```

#### 10. Delete RSS Source

```bash
DELETE /api/v1/admin/feeds/{feed_id}
Authorization: Bearer {TOKEN}
```

Note: This is a soft delete (sets `is_active=false`)

---

## 🔄 How It Works

### Automatic RSS Fetching Flow

```
1. Celery Beat (scheduler)
   ↓
2. Triggers "fetch_all_feeds" task every 15 minutes
   ↓
3. Gets list of all active RSS sources (44 feeds)
   ↓
4. Creates parallel tasks for each feed
   ↓
5. Each "fetch_single_feed" task:
   - Fetches RSS feed XML
   - Parses entries
   - Creates Article records
   - Updates feed health metrics
   ↓
6. Returns results (articles created/skipped)
```

### Manual Fetch via Admin API

```
1. Admin calls POST /api/v1/admin/celery/fetch-now
   ↓
2. API immediately dispatches Celery task
   ↓
3. Returns task_id to admin
   ↓
4. Admin polls GET /api/v1/admin/celery/task/{task_id}
   ↓
5. Gets real-time status and results
```

### Parallel Processing

Celery processes multiple feeds simultaneously:
- **Default concurrency**: 4 workers
- **Max concurrent fetches**: Controlled by `RSS_MAX_CONCURRENT_FETCHES` setting
- **Task retry**: 3 attempts with exponential backoff

---

## 🔍 Monitoring & Troubleshooting

### Check if Celery is Running

```bash
# Check processes
ps aux | grep celery

# Check logs
tail -f logs/celery_worker.log
tail -f logs/celery_beat.log

# Check via API
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/admin/celery/status
```

### Common Issues

#### 1. "Redis connection refused"

```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# If not running:
# Docker:
docker-compose -f docker/docker-compose.dev.yml up -d redis

# macOS:
brew services start redis

# Linux:
sudo systemctl start redis
```

#### 2. "No active workers"

```bash
# Check if Celery worker is running
ps aux | grep "celery.*worker"

# Restart Celery
./scripts/stop_celery.sh
./scripts/start_celery.sh
```

#### 3. "Tasks not executing"

```bash
# Check Beat scheduler is running
ps aux | grep "celery.*beat"

# Check beat schedule file
ls -la celerybeat-schedule.db

# View logs
tail -f logs/celery_beat.log
```

#### 4. Feed fetch failures

```bash
# Check feed health
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/admin/feeds/health

# Manually test a failing feed
curl -H "Authorization: Bearer $TOKEN" \
  -X POST http://localhost:8000/api/v1/admin/celery/fetch-feed/{feed_id}

# Check task result
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/admin/celery/task/{task_id}
```

### Performance Tuning

#### Increase Workers

Edit `scripts/start_celery.sh`:
```bash
--concurrency=8  # Increase from 4 to 8
```

#### Adjust Fetch Frequency

Edit `.env`:
```env
# Fetch more frequently
CELERY_BEAT_SCHEDULE_INTERVAL=300  # 5 minutes

# Fetch less frequently
CELERY_BEAT_SCHEDULE_INTERVAL=3600  # 1 hour
```

#### Limit Concurrent Fetches

Edit `.env`:
```env
# Process fewer feeds at once (reduces load)
RSS_MAX_CONCURRENT_FETCHES=10
```

### Logs

```bash
# Worker logs (task execution)
tail -f logs/celery_worker.log

# Beat logs (scheduling)
tail -f logs/celery_beat.log

# API logs (admin dashboard requests)
# Depends on your FastAPI logging setup

# Filter for specific feed
tail -f logs/celery_worker.log | grep "TechCrunch"

# Watch for errors
tail -f logs/celery_worker.log | grep ERROR
```

---

## 🎯 Common Admin Use Cases

### 1. Adding a New RSS Source

```bash
# Option A: Via Admin API
curl -X POST http://localhost:8000/api/v1/admin/feeds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Hacker News",
    "url": "https://news.ycombinator.com/rss",
    "source_name": "Hacker News",
    "category": "technology",
    "is_active": true
  }'

# Option B: Via database script
python scripts/database/add_youtube_channels.py  # For YouTube
# OR modify scripts/database/seed_database.py for other feeds
```

### 2. Pausing a Feed

```bash
curl -X PUT http://localhost:8000/api/v1/admin/feeds/{feed_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

### 3. Testing a New Feed

```bash
# 1. Add the feed (inactive)
curl -X POST http://localhost:8000/api/v1/admin/feeds \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"Test","url":"...","is_active":false,...}'

# 2. Manually fetch to test
curl -X POST http://localhost:8000/api/v1/admin/celery/fetch-feed/{feed_id} \
  -H "Authorization: Bearer $TOKEN"

# 3. Check results
curl http://localhost:8000/api/v1/admin/celery/task/{task_id} \
  -H "Authorization: Bearer $TOKEN"

# 4. If successful, activate
curl -X PUT http://localhost:8000/api/v1/admin/feeds/{feed_id} \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"is_active": true}'
```

### 4. Monitoring Feed Health

```bash
# Check overall health
curl http://localhost:8000/api/v1/admin/feeds/health \
  -H "Authorization: Bearer $TOKEN"

# Get list of unhealthy feeds
curl http://localhost:8000/api/v1/admin/feeds/health \
  -H "Authorization: Bearer $TOKEN" | jq '.unhealthy_feeds'

# Fix unhealthy feed (update URL or deactivate)
curl -X PUT http://localhost:8000/api/v1/admin/feeds/{feed_id} \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url": "https://corrected-url.com/feed"}'
```

---

## 📊 Summary

✅ **Celery handles background RSS fetching automatically**  
✅ **Admin Dashboard provides full control over feeds and workers**  
✅ **Monitor health, trigger manual fetches, manage sources**  
✅ **Scales to hundreds of feeds with parallel processing**

For questions or issues, check the logs first:
```bash
tail -f logs/celery_worker.log
```

---

**Updated:** January 15, 2025
