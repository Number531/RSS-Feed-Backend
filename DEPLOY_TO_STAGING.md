# 🚀 Deploy to Staging - Quick Start Guide

**Time Required:** 15-30 minutes  
**Difficulty:** Easy

---

## ✅ Pre-Flight Checklist (5 minutes)

Run these checks to ensure everything is ready:

```bash
# 1. Verify tests pass
pytest tests/integration/ -v
# Expected: 92/92 passing ✅

# 2. Check for security issues
./scripts/security_audit.sh
# Expected: No critical issues ✅

# 3. Verify dependencies are correct
pip list | grep bcrypt
# Expected: bcrypt 4.x.x (not 5.x)

# 4. Test database migrations
alembic check
# Expected: No issues ✅
```

**All checks passing?** ✅ Proceed to deployment!

---

## 🎯 Step-by-Step Deployment

### Step 1: Prepare Environment File (5 minutes)

Create staging environment configuration:

```bash
# Copy template
cp .env.example .env.staging

# Edit with your staging values
nano .env.staging
```

**Critical Variables to Update:**

```bash
# Application
ENVIRONMENT=staging
DEBUG=False
SECRET_KEY=<generate-32-char-secret>  # Use: openssl rand -hex 32

# Database (your staging database)
DATABASE_URL=postgresql+asyncpg://user:password@your-db-host:5432/rss_feed_staging

# Redis (your staging Redis)
REDIS_URL=redis://your-redis-host:6379/0

# CORS - UPDATE THIS! 🔴
BACKEND_CORS_ORIGINS=["https://staging-app.yourdomain.com","https://staging.yourdomain.com"]

# Admin (create strong password!)
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<generate-strong-password>  # Use: openssl rand -base64 24

# Optional: Sentry (highly recommended)
SENTRY_DSN=https://your-key@sentry.io/your-project
SENTRY_ENVIRONMENT=staging
```

---

### Step 2: Deploy Code (Method A: Docker - Recommended)

Using Docker (easiest):

```bash
# 1. Build image
docker build -t rss-feed-backend:staging .

# 2. Run with staging env
docker run -d \
  --name rss-feed-staging \
  --env-file .env.staging \
  -p 8000:8000 \
  rss-feed-backend:staging

# 3. Check health
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-10-13T03:00:00Z"
}
```

---

### Step 2: Deploy Code (Method B: Direct Python)

Without Docker:

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install production dependencies
pip install -r requirements-prod.txt

# 3. Set environment
export ENV_FILE=.env.staging

# 4. Run migrations
alembic upgrade head

# 5. Start server
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --env-file .env.staging
```

---

### Step 3: Initialize Database (5 minutes)

```bash
# Run migrations
alembic upgrade head

# Create admin user
python scripts/create_admin.py

# Verify admin created
psql $DATABASE_URL -c "SELECT username, email, is_superuser FROM users WHERE is_superuser = true;"
```

---

### Step 4: Start Background Workers (5 minutes)

Start Celery workers for RSS feed processing:

```bash
# Terminal 1: Celery worker
celery -A app.celery_app worker \
  --loglevel=info \
  --concurrency=4

# Terminal 2: Celery beat (scheduler)
celery -A app.celery_app beat \
  --loglevel=info

# Or use Docker Compose:
docker-compose -f docker-compose.prod.yml up -d worker beat
```

---

### Step 5: Smoke Tests (5 minutes)

Verify everything works:

```bash
# 1. Health check
curl https://staging-api.yourdomain.com/health

# 2. API root
curl https://staging-api.yourdomain.com/api/v1/

# 3. Get articles (should be empty initially)
curl https://staging-api.yourdomain.com/api/v1/articles

# 4. Register a test user
curl -X POST https://staging-api.yourdomain.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "TestPass123!"
  }'

# 5. Login
curl -X POST https://staging-api.yourdomain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'
```

**Or use the automated test script:**
```bash
./scripts/test_api_endpoints.sh https://staging-api.yourdomain.com
```

---

### Step 6: Monitoring Setup (Optional, 10 minutes)

**Option 1: Sentry (Recommended)**
```bash
# Already configured if SENTRY_DSN is set
# Visit sentry.io to see errors and performance
```

**Option 2: Prometheus + Grafana**
```bash
# Metrics already exposed at /metrics
curl https://staging-api.yourdomain.com/metrics

# Set up Prometheus scraper (example config):
# prometheus.yml
scrape_configs:
  - job_name: 'rss-feed'
    static_configs:
      - targets: ['staging-api.yourdomain.com']
```

---

## 🎉 Deployment Complete!

Your staging environment is now live at:
- **API:** https://staging-api.yourdomain.com
- **Docs:** https://staging-api.yourdomain.com/docs
- **Health:** https://staging-api.yourdomain.com/health
- **Metrics:** https://staging-api.yourdomain.com/metrics

---

## 🔍 Post-Deployment Checklist

Within first 24 hours:

- [ ] Monitor logs for errors
- [ ] Check Sentry for exceptions
- [ ] Verify RSS feeds are being fetched (Celery logs)
- [ ] Test user registration flow
- [ ] Test article voting
- [ ] Test comment system
- [ ] Test notifications
- [ ] Verify email notifications (if configured)
- [ ] Check database backup schedule
- [ ] Monitor API response times

---

## 📊 Monitoring Commands

```bash
# View application logs
docker logs -f rss-feed-staging

# Or with Docker Compose
docker-compose -f docker-compose.prod.yml logs -f api

# Check Celery tasks
celery -A app.celery_app inspect active

# Database connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity WHERE datname='rss_feed_staging';"

# Redis info
redis-cli -h your-redis-host info stats
```

---

## 🆘 Troubleshooting

### Issue: Database connection fails
```bash
# Check connection string
echo $DATABASE_URL

# Test connection manually
psql $DATABASE_URL -c "SELECT 1;"

# Check firewall/security groups
```

### Issue: CORS errors in frontend
```bash
# Verify CORS origins in .env.staging
grep BACKEND_CORS_ORIGINS .env.staging

# Should include your frontend domain
# e.g., ["https://staging-app.yourdomain.com"]
```

### Issue: 500 Internal Server Error
```bash
# Check application logs
docker logs rss-feed-staging --tail 100

# Check Sentry for stack trace
# Visit sentry.io dashboard
```

### Issue: Celery tasks not running
```bash
# Check worker is running
celery -A app.celery_app inspect ping

# Check Redis connection
redis-cli -h your-redis-host ping

# Restart workers
docker-compose -f docker-compose.prod.yml restart worker beat
```

---

## 🔄 Rollback Procedure (if needed)

If something goes wrong:

```bash
# 1. Stop the new version
docker stop rss-feed-staging

# 2. Rollback database (if migrations were applied)
alembic downgrade -1

# 3. Start previous version
docker start rss-feed-previous

# 4. Investigate issue
docker logs rss-feed-staging > error_log.txt
```

---

## 📝 Next Steps

After staging is stable (3-7 days):

1. **Week 1:**
   - Monitor for issues
   - Collect user feedback
   - Fix any bugs found

2. **Week 2:**
   - Performance optimization
   - Fix remaining unit tests
   - Add enhanced monitoring

3. **Week 3:**
   - Load testing
   - Security audit
   - Prepare for production

4. **Week 4:**
   - Production deployment
   - Marketing/launch prep
   - User onboarding

---

## 🎯 Success Metrics

Track these KPIs in staging:

- **Uptime:** Target 99.5%+
- **API Response Time:** <200ms p95
- **Error Rate:** <0.1%
- **RSS Fetch Success Rate:** >95%
- **Database Connections:** <50% of pool
- **Memory Usage:** <1GB
- **CPU Usage:** <50% average

---

## 📚 Useful Resources

- **API Documentation:** https://staging-api.yourdomain.com/docs
- **Health Check:** https://staging-api.yourdomain.com/health
- **Metrics:** https://staging-api.yourdomain.com/metrics
- **Sentry:** https://sentry.io (if configured)
- **GitHub Issues:** [Your repo URL]

---

## ✅ Deployment Verified

**Checklist:**
- [ ] Application is running
- [ ] Health check returns 200
- [ ] Database is connected
- [ ] Redis is connected
- [ ] Celery workers are running
- [ ] Admin user can login
- [ ] Test user can register
- [ ] Articles endpoint returns data
- [ ] CORS is configured correctly
- [ ] Monitoring is active

**All checked?** 🎉 **Deployment successful!**

---

**Questions or issues?** Check logs or create a GitHub issue.

**Ready for production?** Follow the same process with `.env.production` 🚀
