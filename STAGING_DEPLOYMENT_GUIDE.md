# Reading History Enhancement - Staging Deployment Guide

**Feature:** Reading History Enhancement  
**Version:** 1.0.0  
**Target Environment:** Staging  
**Date:** October 11, 2025

---

## 🎯 Deployment Overview

This guide covers deploying the Reading History Enhancement feature to the staging environment for user acceptance testing and final validation before production.

---

## ✅ Pre-Deployment Checklist

### 1. Code Verification
- [x] All tests passing (28/28 - 100%)
- [x] Code reviewed and approved
- [x] Documentation complete
- [x] No critical security issues
- [x] Dependencies up to date

### 2. Environment Verification
- [ ] Staging database accessible
- [ ] Environment variables configured
- [ ] Backup systems operational
- [ ] Monitoring tools ready
- [ ] Access credentials validated

### 3. Database Readiness
- [ ] Staging database backed up
- [ ] Migration scripts tested locally
- [ ] Rollback plan documented
- [ ] Database connection string verified
- [ ] Admin access confirmed

---

## 📦 Files to Deploy

### New Files
```
app/
├── models/
│   ├── reading_history.py                    (NEW)
│   └── user_reading_preferences.py           (NEW)
├── repositories/
│   └── reading_preferences_repository.py     (NEW)
├── schemas/
│   └── reading_history.py                    (NEW)
└── services/
    └── reading_history_service.py            (MODIFIED - enhanced)

migrations/
├── run_preferences_migration.py              (NEW)
└── run_reading_history_migration.py          (NEW - if needed)

tests/
├── unit/
│   ├── conftest.py                           (NEW)
│   ├── test_reading_preferences_repository.py (NEW)
│   └── test_reading_history_service_extended.py (NEW)
└── conftest.py                               (MODIFIED - unique URLs)
```

### Modified Files
- `app/services/reading_history_service.py` - Added preference management
- `tests/conftest.py` - Fixed test_article fixture

---

## 🗄️ Database Migration Steps

### Step 1: Backup Current Database
```bash
# Connect to staging database
export STAGING_DB_URL="your-staging-database-url"

# Create backup
pg_dump $STAGING_DB_URL > backup_before_reading_history_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh backup_*.sql
```

### Step 2: Verify Base Tables Exist
```bash
# Check if base tables exist
psql $STAGING_DB_URL -c "\dt"

# Expected tables:
# - users
# - articles
# - rss_sources
# - votes
# - comments
# - bookmarks
```

### Step 3: Run Preferences Migration
```bash
# Navigate to backend directory
cd /path/to/RSS-Feed/backend

# Set database URL
export DATABASE_URL=$STAGING_DB_URL

# Run preferences migration
python run_preferences_migration.py

# Expected output:
# ✅ Table created
# ✅ Index created
# ✅ Constraint added
# ✅ Function created
# ✅ Trigger created
# ✅ Migration completed successfully!
```

### Step 4: Verify Migration
```bash
# Check if user_reading_preferences table exists
psql $STAGING_DB_URL -c "\d user_reading_preferences"

# Expected output:
# Column names: id, user_id, tracking_enabled, analytics_opt_in, 
#               auto_cleanup_enabled, retention_days, exclude_categories,
#               created_at, updated_at

# Check indexes
psql $STAGING_DB_URL -c "\d+ user_reading_preferences"

# Expected indexes:
# - idx_user_reading_preferences_user_id
# - user_reading_preferences_pkey
# - user_reading_preferences_user_id_key
```

### Step 5: Verify reading_history Table
```bash
# Check if reading_history table exists
psql $STAGING_DB_URL -c "\d reading_history"

# If it doesn't exist, it should have been created by create_tables.py
# Verify indexes
psql $STAGING_DB_URL -c "\d+ reading_history"

# Expected indexes:
# - idx_reading_history_user_id
# - idx_reading_history_viewed_at
# - idx_reading_history_user_viewed
# - idx_reading_history_article_id
```

---

## 🚀 Application Deployment

### Step 1: Stop Staging Application
```bash
# Stop the staging server
# (Method depends on your deployment setup)
# Examples:
# Docker: docker-compose -f docker-compose.staging.yml down
# Systemd: sudo systemctl stop rss-feed-backend
# PM2: pm2 stop rss-feed-backend
```

### Step 2: Deploy New Code
```bash
# Pull latest code
git fetch origin
git checkout main
git pull origin main

# Or if using a specific branch
git checkout feature/reading-history
git pull origin feature/reading-history

# Verify new files exist
ls -la app/models/reading_history.py
ls -la app/models/user_reading_preferences.py
ls -la app/repositories/reading_preferences_repository.py
```

### Step 3: Install Dependencies
```bash
# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Verify SQLAlchemy version
pip show sqlalchemy | grep Version
```

### Step 4: Set Environment Variables
```bash
# Staging environment variables
export ENVIRONMENT=staging
export DATABASE_URL=$STAGING_DB_URL
export LOG_LEVEL=DEBUG  # More verbose for staging

# Optional: Export-specific settings
export MAX_EXPORT_RECORDS=1000
export EXPORT_TIMEOUT_SECONDS=60
```

### Step 5: Start Application
```bash
# Start staging server
# Examples:
# Docker: docker-compose -f docker-compose.staging.yml up -d
# Systemd: sudo systemctl start rss-feed-backend
# PM2: pm2 start rss-feed-backend
# Direct: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 6: Verify Application Started
```bash
# Check application logs
tail -f logs/app.log

# Or with Docker
docker-compose -f docker-compose.staging.yml logs -f

# Expected output:
# - Application started successfully
# - Database connection established
# - All models loaded
# - No error messages
```

---

## 🧪 Smoke Tests

### Test 1: Health Check
```bash
# Basic health check
curl http://staging-api.yourdomain.com/health

# Expected: {"status": "healthy"}
```

### Test 2: Database Connection
```bash
# Test database connectivity
curl http://staging-api.yourdomain.com/api/v1/health/db

# Expected: {"database": "connected"}
```

### Test 3: Create Test User (via API or database)
```bash
# Create a test user directly in database
psql $STAGING_DB_URL << EOF
INSERT INTO users (id, email, username, hashed_password, is_active, is_superuser, is_verified)
VALUES (
  gen_random_uuid(),
  'staging-test@example.com',
  'staging-test-user',
  'hashed-password-here',
  true,
  false,
  true
) ON CONFLICT (email) DO NOTHING
RETURNING id, username;
EOF
```

### Test 4: Verify Preferences Auto-Creation
```bash
# Get the test user ID from previous step
TEST_USER_ID="user-id-from-previous-step"

# Check if preferences were created (they shouldn't exist yet)
psql $STAGING_DB_URL -c "SELECT * FROM user_reading_preferences WHERE user_id = '$TEST_USER_ID';"

# Expected: No rows (preferences created on-demand)
```

### Test 5: Test Export Functionality
```python
# Create a simple Python script to test export
cat > test_export.py << 'EOF'
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.services.reading_history_service import ReadingHistoryService
import os

async def test_export():
    engine = create_async_engine(os.getenv('DATABASE_URL'))
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        service = ReadingHistoryService(session)
        
        # Test with empty history
        content, filename = await service.export_history(
            user_id="test-user-id",
            format="json"
        )
        print(f"✅ Export test passed: {filename}")
        print(f"Content length: {len(content)} bytes")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_export())
EOF

# Run the test
python test_export.py

# Expected output:
# ✅ Export test passed: reading_history_20251011_HHMMSS.json
# Content length: XXX bytes
```

---

## 📊 Validation Checklist

### Database Validation
- [ ] All tables exist with correct schema
- [ ] All indexes created successfully
- [ ] All constraints enforced
- [ ] Foreign keys working (CASCADE deletes)
- [ ] Default values applied correctly
- [ ] Triggers functioning (if any)

### Application Validation
- [ ] Application starts without errors
- [ ] Database connection successful
- [ ] All endpoints responding
- [ ] Logging working correctly
- [ ] No import errors
- [ ] Dependencies loaded

### Functionality Validation
- [ ] Can create reading history records
- [ ] Can retrieve user preferences
- [ ] Can update user preferences
- [ ] Can export to JSON
- [ ] Can export to CSV
- [ ] Date range filtering works
- [ ] Category exclusion works

---

## 🔍 Monitoring Setup

### Step 1: Enable Database Query Logging
```sql
-- Enable slow query logging
ALTER SYSTEM SET log_min_duration_statement = 1000; -- Log queries > 1s
ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';
SELECT pg_reload_conf();
```

### Step 2: Monitor Key Metrics
```bash
# Monitor table sizes
psql $STAGING_DB_URL -c "
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename IN ('reading_history', 'user_reading_preferences')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# Monitor query performance
psql $STAGING_DB_URL -c "
SELECT 
  query,
  calls,
  total_time,
  mean_time,
  max_time
FROM pg_stat_statements 
WHERE query LIKE '%reading%' 
ORDER BY mean_time DESC 
LIMIT 10;
"
```

### Step 3: Application Monitoring
```bash
# Monitor application logs for errors
tail -f logs/app.log | grep -i error

# Monitor export operations
tail -f logs/app.log | grep -i export

# Monitor preference updates
tail -f logs/app.log | grep -i preference
```

---

## 🚨 Rollback Procedure

### If Issues Are Discovered

#### Step 1: Stop Application
```bash
# Stop the staging application
# (Use same method as deployment)
```

#### Step 2: Rollback Database
```bash
# Restore from backup
psql $STAGING_DB_URL < backup_before_reading_history_YYYYMMDD_HHMMSS.sql

# Verify restoration
psql $STAGING_DB_URL -c "\dt"
```

#### Step 3: Rollback Code
```bash
# Checkout previous version
git checkout <previous-commit-hash>

# Or checkout main branch
git checkout main
```

#### Step 4: Restart Application
```bash
# Restart with previous version
# (Use same method as deployment)
```

#### Step 5: Verify Rollback
```bash
# Test health endpoints
curl http://staging-api.yourdomain.com/health

# Check logs for errors
tail -100 logs/app.log
```

---

## 📝 Post-Deployment Tasks

### Immediate (Within 1 Hour)
- [ ] Verify all smoke tests pass
- [ ] Check error logs for any issues
- [ ] Verify database connections stable
- [ ] Test basic user workflows
- [ ] Notify QA team deployment complete

### Within 24 Hours
- [ ] Monitor query performance
- [ ] Check database growth rate
- [ ] Review application logs
- [ ] Test export functionality with real data
- [ ] Gather initial user feedback

### Within 1 Week
- [ ] Conduct user acceptance testing
- [ ] Performance testing with load
- [ ] Review and optimize slow queries
- [ ] Document any issues found
- [ ] Plan production deployment

---

## 🔐 Security Checklist

- [ ] No secrets in code or config files
- [ ] Environment variables properly secured
- [ ] Database credentials rotated
- [ ] SSL/TLS enabled for database connections
- [ ] API rate limiting enabled
- [ ] User input validation working
- [ ] SQL injection protection verified
- [ ] CORS properly configured

---

## 📞 Support & Escalation

### Issue Severity Levels

**P0 - Critical (Immediate Response)**
- Database connection failures
- Application won't start
- Data loss or corruption
- Security vulnerabilities

**P1 - High (Response within 2 hours)**
- Export functionality broken
- Preferences not saving
- Performance degradation >50%
- User-facing errors

**P2 - Medium (Response within 24 hours)**
- Minor UI issues
- Non-critical bugs
- Performance degradation <50%
- Enhancement requests

**P3 - Low (Response within 1 week)**
- Documentation updates
- Code cleanup
- Nice-to-have features
- General questions

### Contact Information
- **DevOps:** [contact info]
- **Database Admin:** [contact info]
- **Backend Lead:** [contact info]
- **Product Owner:** [contact info]

---

## ✅ Sign-Off

### Deployment Completed By
- **Name:** _______________
- **Date:** _______________
- **Time:** _______________

### Verified By
- **QA Lead:** _______________
- **Date:** _______________

### Issues Found
- None ☐
- Minor (documented below) ☐
- Major (deployment rolled back) ☐

### Notes
```
_____________________________________________
_____________________________________________
_____________________________________________
```

---

## 📚 Additional Resources

- **Test Report:** `FINAL_TEST_REPORT.md`
- **Technical Docs:** `READING_HISTORY_IMPLEMENTATION.md`
- **API Docs:** `app/schemas/reading_history.py`
- **Quickstart Guide:** `READING_HISTORY_QUICKSTART.md`
- **Database Schema:** Run `\d+ reading_history` and `\d+ user_reading_preferences`

---

**Document Version:** 1.0  
**Last Updated:** October 11, 2025  
**Status:** Ready for Use 🚀
