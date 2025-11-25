# Production Deployment Guide

**Version**: 1.0.0  
**Last Updated**: November 25, 2025  
**Status**: ✅ Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Environment Configuration](#environment-configuration)
4. [Security Validation](#security-validation)
5. [Health Check Verification](#health-check-verification)
6. [Deployment Procedures](#deployment-procedures)
7. [Post-Deployment Verification](#post-deployment-verification)
8. [Monitoring Setup](#monitoring-setup)
9. [Rollback Procedures](#rollback-procedures)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This guide provides step-by-step instructions for deploying the RSS Feed Backend to production. Follow each section in order to ensure a secure, reliable deployment.

### Prerequisites

- [ ] Access to production server/cloud environment
- [ ] Database credentials (PostgreSQL 14+)
- [ ] Redis instance (7.0+)
- [ ] SMTP or Microsoft Graph API credentials
- [ ] Sentry DSN (for error tracking)
- [ ] Domain name with SSL certificate
- [ ] Docker installed (if using containerized deployment)

### Architecture

```
┌─────────────────┐
│   Load Balancer │ (HTTPS)
└────────┬────────┘
         │
    ┌────┴────┐
    │ Backend │ (FastAPI - 3 replicas)
    └────┬────┘
         │
    ┌────┴────────────┬──────────┐
    │                 │          │
┌───▼────┐    ┌──────▼─────┐  ┌─▼─────┐
│ PostgreSQL│  │   Redis    │  │Celery │
└──────────┘    └────────────┘  └───────┘
```

---

## Pre-Deployment Checklist

### Critical Requirements

#### 1. Environment Variables

**Run this validation script:**
```bash
python -c "
import os
import sys

required = {
    'ENVIRONMENT': 'production',
    'DEBUG': 'False',
    'DATABASE_URL': None,
    'REDIS_URL': None,
    'SECRET_KEY': None,
    'ADMIN_EMAIL': None,
    'ADMIN_USERNAME': None,
    'ADMIN_PASSWORD': None,
}

missing = []
for key, expected in required.items():
    value = os.getenv(key)
    if not value:
        missing.append(key)
    elif expected and value != expected:
        print(f'⚠️  {key}={value} (expected: {expected})')

if missing:
    print(f'❌ Missing: {", ".join(missing)}')
    sys.exit(1)
else:
    print('✅ All required environment variables set')
"
```

#### 2. Configuration Validation

**Test production config validators:**
```bash
python -c "
from app.core.config import Settings

settings = Settings()
try:
    settings.validate_production_config()
    print('✅ Production config validation passed')
except ValueError as e:
    print(f'❌ Validation failed:\n{e}')
    exit(1)
"
```

**Expected Output:**
```
Production configuration warnings:
  ⚠️  SENTRY_DSN is not configured...
✅ Production config validation passed
```

⚠️ **Warnings are OK** - Errors will block startup.

#### 3. Dependencies

**Check for security vulnerabilities:**
```bash
# Install security scanners
pip install safety bandit

# Check dependencies
safety check

# Check code security
bandit -r app/ -ll
```

**Expected Result:** No HIGH or CRITICAL vulnerabilities.

#### 4. Database Migrations

**Verify migration status:**
```bash
# Check current migration
alembic current

# Check pending migrations
alembic heads

# Test migration (dry run if supported)
alembic upgrade head --sql > migration.sql
cat migration.sql  # Review changes
```

#### 5. Test Suite

**Run complete test suite:**
```bash
# Run all tests
pytest tests/ --cov=app --cov-report=term

# Minimum coverage required: 95%
# All tests must pass
```

---

## Environment Configuration

### Step 1: Create Production Environment File

Create `.env.production` (never commit this file):

```bash
# Application
ENVIRONMENT=production
DEBUG=False
APP_NAME=RSS News Aggregator
APP_VERSION=1.0.0

# API
API_V1_PREFIX=/api/v1
BACKEND_CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]

# Database (use your actual credentials)
DATABASE_URL=postgresql+asyncpg://prod_user:STRONG_PASSWORD@db-host:5432/rss_prod
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://redis-host:6379/0
REDIS_CACHE_TTL=900

# Celery
CELERY_BROKER_URL=redis://redis-host:6379/1
CELERY_RESULT_BACKEND=redis://redis-host:6379/2

# JWT - Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=YOUR_GENERATED_SECRET_HERE_32_CHARS_MIN
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30

# Admin User (change from defaults!)
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=STRONG_ADMIN_PASSWORD_HERE  # NOT changeme123!

# Email - Microsoft Graph API (recommended)
MICROSOFT_CLIENT_ID=your_azure_client_id
MICROSOFT_CLIENT_SECRET=your_azure_client_secret
MICROSOFT_TENANT_ID=your_azure_tenant_id
MICROSOFT_SENDER_EMAIL=noreply@yourdomain.com
USE_GRAPH_API=true

# Email - SMTP Fallback (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=noreply@yourdomain.com

# Email Verification
EMAIL_VERIFICATION_REQUIRED=true
FRONTEND_URL=https://yourdomain.com
VERIFICATION_TOKEN_EXPIRE_HOURS=1

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_UNAUTHENTICATED=20

# Request Size Limiting (optional - defaults to 10MB)
# MAX_REQUEST_SIZE=10485760

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Error Tracking (required for production)
SENTRY_DSN=https://YOUR_SENTRY_DSN@sentry.io/PROJECT_ID
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# RSS Feed Settings
RSS_FETCH_TIMEOUT=10
RSS_MAX_CONCURRENT_FETCHES=5

# Fact-Check API
FACT_CHECK_API_URL=https://fact-check-production.up.railway.app
FACT_CHECK_ENABLED=true
FACT_CHECK_MODE=summary
```

### Step 2: Generate Secure Secrets

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
```

**Generate ADMIN_PASSWORD:**
```bash
python -c "import secrets; import string; chars = string.ascii_letters + string.digits + '!@#$%^&*'; print('ADMIN_PASSWORD=' + ''.join(secrets.choice(chars) for _ in range(20)))"
```

### Step 3: Validate Configuration

**Test config loads correctly:**
```bash
export $(cat .env.production | xargs)
python -c "from app.core.config import settings; print(f'Environment: {settings.ENVIRONMENT}'); print(f'Debug: {settings.DEBUG}'); print(f'Frontend: {settings.FRONTEND_URL}')"
```

**Expected Output:**
```
Environment: production
Debug: False
Frontend: https://yourdomain.com
```

---

## Security Validation

### 1. Production Config Validators

The application automatically validates production config on startup. Test manually:

```bash
python -c "
from app.core.config import settings

print('Running production validators...')
settings.validate_production_config()
print('✅ All validations passed')
"
```

**Checks Performed:**
- ✅ DEBUG is False
- ✅ CORS origins don't contain localhost
- ✅ ADMIN_PASSWORD is not default value
- ✅ SECRET_KEY is not default value
- ✅ FRONTEND_URL uses https://
- ⚠️ EMAIL_VERIFICATION_REQUIRED (warning if false)
- ⚠️ SENTRY_DSN configured (warning if missing)
- ⚠️ DATABASE_POOL_SIZE < 80 (warning if high)

### 2. Security Headers

**Verify middleware registration:**
```bash
python -c "
from app.main import app
middleware_names = [mw.cls.__name__ for mw in app.user_middleware]
print('Middleware stack:')
for mw in middleware_names:
    print(f'  - {mw}')

required = ['SecurityHeadersMiddleware', 'RequestSizeLimitMiddleware']
missing = [m for m in required if m not in middleware_names]
if missing:
    print(f'❌ Missing: {missing}')
    exit(1)
print('✅ All security middleware registered')
"
```

**Test headers after deployment:**
```bash
# Test security headers are present
curl -I https://yourdomain.com/health | grep -E "(X-Content-Type-Options|X-Frame-Options|X-XSS-Protection|Strict-Transport-Security|Content-Security-Policy)"
```

**Expected Headers:**
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'; ...
```

### 3. Request Size Limits

**Test request size limit:**
```bash
# Create 11MB file (exceeds 10MB limit)
dd if=/dev/zero of=large_file.bin bs=1M count=11

# Should return 413 Payload Too Large
curl -X POST https://yourdomain.com/api/v1/articles \
  -F "file=@large_file.bin" \
  -w "\nHTTP Status: %{http_code}\n"
```

**Expected Response:**
```json
{
  "error": "payload_too_large",
  "message": "Request body too large. Maximum size: 10.0MB, received: 11.0MB",
  "max_size_bytes": 10485760,
  "actual_size_bytes": 11534336
}
HTTP Status: 413
```

### 4. Rate Limiting

**Test rate limiting:**
```bash
# Should succeed first 3 times, then get rate limited
for i in {1..5}; do
  echo "Request $i:"
  curl -X POST https://yourdomain.com/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email":"test'$i'@example.com","username":"test'$i'","password":"Test1234!"}' \
    -w "\nStatus: %{http_code}\n\n"
done
```

**Expected:** First 3 succeed (or fail validation), 4th and 5th return 429 Too Many Requests.

---

## Health Check Verification

### 1. Basic Health Check

```bash
curl https://yourdomain.com/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-25T20:54:00.123456Z",
  "environment": "production",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected"
}
```

### 2. Database Health

**Test database connectivity:**
```bash
curl https://yourdomain.com/health | jq -r '.database'
```

**Expected:** `"connected"`

**If unhealthy:**
```bash
# Check database connection
psql $DATABASE_URL -c "SELECT 1;"

# Check connection pool
# Look for errors in application logs
```

### 3. Redis Health

**Test Redis connectivity:**
```bash
curl https://yourdomain.com/health | jq -r '.redis'
```

**Expected:** `"connected"`

**If unhealthy:**
```bash
# Test Redis connection
redis-cli -h redis-host -p 6379 PING

# Should return: PONG
```

### 4. API Endpoints

**Test critical endpoints:**
```bash
# API root
curl https://yourdomain.com/api/v1/ | jq

# Docs available
curl -I https://yourdomain.com/docs

# Metrics (should require auth or return 200)
curl -I https://yourdomain.com/metrics
```

---

## Deployment Procedures

### Option 1: Docker Deployment (Recommended)

#### Step 1: Build Production Image

```bash
# Build image with production requirements
docker build -t rss-backend:production .

# Verify image uses requirements-prod.txt
docker run --rm rss-backend:production cat Dockerfile | grep requirements-prod.txt
```

#### Step 2: Deploy with Docker Compose

**Create `docker-compose.prod.yml`:**
```yaml
version: '3.8'

services:
  backend:
    image: rss-backend:production
    env_file: .env.production
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

  postgres:
    image: postgres:14-alpine
    env_file: .env.production
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  celery-worker:
    image: rss-backend:production
    env_file: .env.production
    command: celery -A app.core.celery_app worker -l info
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  celery-beat:
    image: rss-backend:production
    env_file: .env.production
    command: celery -A app.core.celery_app beat -l info
    depends_on:
      - redis
    restart: unless-stopped

volumes:
  postgres_data:
```

**Deploy:**
```bash
# Pull/build images
docker-compose -f docker-compose.prod.yml build

# Run migrations
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### Option 2: Direct Deployment

#### Step 1: Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install production dependencies
pip install -r requirements-prod.txt
```

#### Step 2: Run Migrations

```bash
# Set environment
export $(cat .env.production | xargs)

# Run migrations
alembic upgrade head

# Verify
alembic current
```

#### Step 3: Start Services

**Using systemd (recommended):**

Create `/etc/systemd/system/rss-backend.service`:
```ini
[Unit]
Description=RSS Feed Backend API
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/rss-backend
EnvironmentFile=/opt/rss-backend/.env.production
ExecStart=/opt/rss-backend/venv/bin/uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --timeout-keep-alive 5 \
    --access-log \
    --log-config logging.conf
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable rss-backend
sudo systemctl start rss-backend
sudo systemctl status rss-backend
```

**Using Uvicorn directly:**
```bash
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --timeout-keep-alive 5 \
  --access-log
```

---

## Post-Deployment Verification

### Immediate Checks (T+0)

Run these checks immediately after deployment:

#### 1. Application Started Successfully

```bash
# Check logs for startup messages
docker-compose logs backend | grep "Starting RSS News Aggregator"
# or
journalctl -u rss-backend | grep "Starting"

# Should see:
# 🚀 Starting RSS News Aggregator v1.0.0
# 📊 Environment: production
# 🔍 Debug mode: False
# ✅ Production configuration validated
# ✅ Database connection initialized
# ✅ Cache manager initialized
# ✅ Metrics endpoint exposed at /metrics
```

#### 2. Health Endpoints Return 200

```bash
# Basic health
curl -f https://yourdomain.com/health || echo "FAILED"

# Detailed health (with DB/Redis checks)
curl -f https://yourdomain.com/health || echo "FAILED"
```

#### 3. API Responds Correctly

```bash
# Test API root
curl https://yourdomain.com/api/v1/ | jq -r '.message'
# Expected: "RSS News Aggregator API v1"

# Test OpenAPI docs
curl -I https://yourdomain.com/docs
# Expected: 200 OK
```

#### 4. Security Headers Present

```bash
curl -I https://yourdomain.com/health | grep -c "X-Frame-Options"
# Expected: 1 (header present)
```

#### 5. Database Migrations Applied

```bash
docker-compose exec backend alembic current
# or
alembic current
# Should show: "head"
```

### Within 1 Hour (T+1h)

#### 1. Monitor Error Rates

**Check Sentry dashboard:**
- Error rate < 1%
- No critical errors
- No recurring patterns

**Check application logs:**
```bash
docker-compose logs backend --tail=100 | grep -i error
# or
journalctl -u rss-backend -n 100 | grep -i error
```

#### 2. Monitor Performance

**Response times:**
```bash
# Test multiple endpoints
for endpoint in / /health /api/v1/ ; do
  echo "Testing $endpoint:"
  curl -o /dev/null -s -w "Time: %{time_total}s\n" https://yourdomain.com$endpoint
done

# Expected: < 500ms for all
```

**Resource usage:**
```bash
# CPU and memory
docker stats backend

# Database connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity WHERE datname='rss_prod';"
```

#### 3. Test Key Features

**Registration:**
```bash
curl -X POST https://yourdomain.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "Test1234!"
  }'
```

**Email delivery (check logs for verification email):**
```bash
docker-compose logs backend | grep "verification email sent"
```

**Background tasks (Celery):**
```bash
docker-compose logs celery-worker | grep "Task"
```

### Within 24 Hours (T+24h)

#### 1. Review Metrics

**Prometheus metrics:**
```bash
curl https://yourdomain.com/metrics | grep -E "(request_count|request_duration)"
```

#### 2. Check Background Jobs

```bash
# Check Celery task execution
docker-compose logs celery-worker | grep "succeeded"
docker-compose logs celery-beat | grep "Scheduler"
```

#### 3. Verify Email Verification

- Register test account
- Verify email received
- Complete verification flow
- Test login with verified account

#### 4. Database Health

```bash
# Check for slow queries
psql $DATABASE_URL -c "SELECT query, calls, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Check connection pool usage
psql $DATABASE_URL -c "SELECT count(*), state FROM pg_stat_activity WHERE datname='rss_prod' GROUP BY state;"
```

---

## Monitoring Setup

### 1. Prometheus Metrics

**Metrics exposed at:** `/metrics`

**Key metrics to monitor:**
```
# Request metrics
http_requests_total
http_request_duration_seconds

# System metrics
process_cpu_seconds_total
process_resident_memory_bytes

# Application metrics
fastapi_inprogress
```

**Grafana Dashboard:**
- Import dashboard ID: 12974 (FastAPI monitoring)
- Configure data source: Prometheus
- Set up alerts for error rate > 1%

### 2. Sentry Alerts

**Configure alerts for:**
- Critical errors (immediate notification)
- Error rate > 1% (within 5 minutes)
- New error types (within 1 hour)

**Alert channels:**
- Email
- Slack
- PagerDuty (for critical)

### 3. Log Monitoring

**Centralized logging:**
```bash
# Ship logs to logging service
docker-compose logs -f backend | 
  grep -v "GET /health" |  # Filter health checks
  logstash ...
```

**Key log patterns to alert on:**
```
ERROR
CRITICAL
"Database connection failed"
"Redis connection failed"
"Email delivery failed"
```

### 4. Uptime Monitoring

**Configure external monitors:**
- Health endpoint: https://yourdomain.com/health
- Check interval: 1 minute
- Alert after: 2 consecutive failures

**Services:**
- UptimeRobot
- Pingdom
- StatusCake

---

## Rollback Procedures

### When to Rollback

Rollback immediately if:
- Error rate > 5% for 5+ minutes
- Critical feature completely broken
- Database corruption detected
- Security vulnerability introduced

### Quick Rollback (< 2 minutes)

#### Docker Deployment

```bash
# Stop current deployment
docker-compose -f docker-compose.prod.yml down

# Deploy previous version
docker-compose -f docker-compose.prod.yml up -d --force-recreate

# Verify health
curl https://yourdomain.com/health
```

#### Direct Deployment

```bash
# Stop current service
sudo systemctl stop rss-backend

# Restore previous code
git checkout previous-stable-tag
# or
cd /opt/rss-backend && git reset --hard HEAD~1

# Restart service
sudo systemctl start rss-backend

# Verify
curl https://yourdomain.com/health
```

### Database Rollback (if needed)

**Only if database changes are incompatible:**

```bash
# Check current migration
alembic current

# Rollback to previous migration
alembic downgrade -1

# Verify
alembic current
```

**Restore from backup (last resort):**

```bash
# Stop application
docker-compose stop backend

# Restore database
pg_restore -d $DATABASE_URL /backups/pre_deploy_20251125.sql

# Restart application
docker-compose start backend
```

### Post-Rollback

1. **Verify rollback successful:**
   ```bash
   curl https://yourdomain.com/health
   ```

2. **Monitor for 30 minutes:**
   - Check error rates returned to normal
   - Verify key features working
   - Review logs for issues

3. **Document incident:**
   - What triggered rollback
   - Impact duration
   - Root cause (if known)
   - Prevention measures

4. **Schedule post-mortem:**
   - Within 24 hours
   - Identify root cause
   - Plan fixes
   - Update deployment procedures

---

## Troubleshooting

### Application Won't Start

**Symptoms:** Container/service fails to start

**Check:**
```bash
# View startup logs
docker-compose logs backend --tail=50
# or
journalctl -u rss-backend -n 50

# Common issues:
# - Config validation failed
# - Database connection failed
# - Port already in use
```

**Solutions:**

1. **Config validation failed:**
   ```bash
   # Run validation manually
   python -c "from app.core.config import settings; settings.validate_production_config()"
   # Fix issues in .env.production
   ```

2. **Database connection failed:**
   ```bash
   # Test database connection
   psql $DATABASE_URL -c "SELECT 1;"
   # Check DATABASE_URL in .env.production
   ```

3. **Port already in use:**
   ```bash
   # Find process using port 8000
   lsof -i :8000
   # Kill process or change port
   ```

### High Error Rate

**Symptoms:** Sentry showing many errors, logs full of errors

**Check:**
```bash
# Recent errors
docker-compose logs backend --tail=100 | grep ERROR

# Error patterns
docker-compose logs backend | grep ERROR | cut -d' ' -f5- | sort | uniq -c | sort -rn
```

**Common causes:**

1. **Database connection pool exhausted:**
   ```bash
   # Check active connections
   psql $DATABASE_URL -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"
   # If too many, increase DATABASE_POOL_SIZE
   ```

2. **Redis connection failed:**
   ```bash
   # Test Redis
   redis-cli -h redis-host PING
   # Check REDIS_URL in config
   ```

3. **External API failures:**
   ```bash
   # Check Fact-Check API
   curl $FACT_CHECK_API_URL/health
   # Check Graph API token
   ```

### Slow Performance

**Symptoms:** Response times > 1 second

**Check:**
```bash
# Response time distribution
curl -o /dev/null -s -w "Total: %{time_total}s\n" https://yourdomain.com/api/v1/

# Slow query log
psql $DATABASE_URL -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 5;"
```

**Solutions:**

1. **Slow database queries:**
   - Add indexes
   - Optimize queries
   - Review N+1 query patterns

2. **High CPU usage:**
   - Scale horizontally (add replicas)
   - Optimize hot code paths
   - Check for infinite loops

3. **Memory pressure:**
   - Increase container memory limits
   - Check for memory leaks
   - Scale vertically

### Email Delivery Failures

**Symptoms:** Users not receiving verification emails

**Check:**
```bash
# Email service logs
docker-compose logs backend | grep "email"

# Test Graph API token
python -c "from app.core.graph_auth import graph_auth_manager; print(graph_auth_manager.get_access_token())"
```

**Solutions:**

1. **Graph API token expired:**
   - Token refresh happens automatically
   - Check MICROSOFT_CLIENT_SECRET is correct
   - Verify Graph API permissions

2. **SMTP fallback issues:**
   - Check SMTP credentials
   - Test SMTP connection manually
   - Verify SMTP port not blocked

### Rate Limiting Too Aggressive

**Symptoms:** Legitimate users getting 429 errors

**Check:**
```bash
# Redis rate limit keys
redis-cli --scan --pattern "slowapi:*" | head -20
```

**Solutions:**

1. **Adjust rate limits:**
   ```bash
   # In .env.production
   RATE_LIMIT_PER_MINUTE=200  # Increase from 100
   RATE_LIMIT_UNAUTHENTICATED=50  # Increase from 20
   ```

2. **Whitelist IPs:**
   - Add IP whitelist to rate limiter
   - Configure load balancer to pass X-Forwarded-For

---

## Additional Resources

### Documentation

- [README.md](./README.md) - Project overview and features
- [PRODUCTION_READINESS_REVIEW.md](./PRODUCTION_READINESS_REVIEW.md) - Detailed security audit
- [SECURITY.md](./SECURITY.md) - Security policy and vulnerability reporting
- [CHANGELOG.md](./CHANGELOG.md) - Version history
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture

### Support

- **Issues**: [GitHub Issues](https://github.com/Number531/RSS-Feed-Backend/issues)
- **Documentation**: [Documentation Index](./DOCUMENTATION_INDEX.md)
- **Security**: security@example.com

---

## Deployment History Template

Keep a log of deployments in your team's wiki or runbook:

```markdown
## Deployment - [DATE]

**Version**: 1.0.0
**Deployed By**: [NAME]
**Environment**: Production

### Pre-Deployment Checklist
- [x] Config validation passed
- [x] Tests passed (659/659)
- [x] Security scan clean
- [x] Database backup created
- [x] Rollback plan documented

### Deployment Steps
1. Built Docker image: `rss-backend:production-v1.0.0`
2. Ran migrations: `alembic upgrade head`
3. Deployed services: `docker-compose up -d`
4. Verified health checks: All passing

### Post-Deployment
- **Status**: ✅ Successful
- **Error Rate**: 0.1% (normal)
- **Response Time**: p95 < 200ms
- **Incidents**: None

### Notes
- All production readiness enhancements active
- Security headers verified
- Rate limiting working as expected
```

---

**End of Production Deployment Guide**

For questions or issues during deployment, refer to the troubleshooting section or contact the development team.
