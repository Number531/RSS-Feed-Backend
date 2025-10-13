# Quick Start Guide - Staging Deployment

**Target Audience:** DevOps Engineers, Backend Developers, SREs  
**Estimated Time:** 30-60 minutes  
**Prerequisites:** Access to staging server, staging database credentials

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [5-Minute Setup](#5-minute-setup)
3. [Full Deployment](#full-deployment)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Access
- [ ] SSH access to staging server
- [ ] Staging database credentials (PostgreSQL)
- [ ] Staging Redis credentials (optional)
- [ ] Sentry DSN for staging environment
- [ ] GitHub repository access

### Required Software (on staging server)
```bash
# Check versions
python3 --version  # Should be 3.11+
git --version
postgresql-client --version  # For testing DB connection
```

### Required Credentials Checklist
```bash
# You'll need these environment variables:
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379/0  # Optional
SECRET_KEY=your-secret-key-here
SENTRY_DSN=https://your-sentry-dsn
```

---

## 5-Minute Setup

**For quick local testing or development**

```bash
# 1. Clone repository
git clone <your-repo-url>
cd backend

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements-prod.txt

# 4. Copy environment template
cp .env.example .env

# 5. Edit .env with your local settings
# Minimum required:
# - DATABASE_URL
# - SECRET_KEY (generate with: openssl rand -hex 32)

# 6. Run migrations
alembic upgrade head

# 7. Start server
uvicorn app.main:app --reload --port 8000

# 8. Test health endpoint
curl http://localhost:8000/health
```

**Expected Output:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-18T..."
}
```

---

## Full Deployment

### Step 1: Prepare Staging Server

```bash
# SSH into staging server
ssh user@staging-server.example.com

# Create application directory
sudo mkdir -p /opt/rss-feed-backend
sudo chown $USER:$USER /opt/rss-feed-backend
cd /opt/rss-feed-backend

# Create necessary directories
mkdir -p logs
mkdir -p backups
```

### Step 2: Deploy Code

```bash
# Clone repository
git clone <repository-url> .

# Or update existing deployment
git fetch origin
git checkout main
git pull origin main

# Verify you're on the correct branch/tag
git log -1 --oneline
```

### Step 3: Setup Python Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install production dependencies
pip install -r requirements-prod.txt

# Verify installation
pip list | grep -E "fastapi|sqlalchemy|alembic|uvicorn"
```

### Step 4: Configure Environment

```bash
# Copy environment template
cp .env.example .env.staging

# Edit environment file
nano .env.staging

# Required configurations:
cat > .env.staging << 'EOF'
# Application
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=info

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@staging-db:5432/rss_feed

# Redis (optional)
REDIS_URL=redis://staging-redis:6379/0

# Security
SECRET_KEY=<generate-with-openssl-rand-hex-32>
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:3000", "https://staging-frontend.example.com"]

# Monitoring
SENTRY_DSN=https://your-sentry-dsn-here
METRICS_ENABLED=true

# External APIs
RSS_FEED_TIMEOUT=30
MAX_CONCURRENT_FEEDS=10
EOF

# Set proper permissions
chmod 600 .env.staging
```

### Step 5: Database Setup

```bash
# Source environment
set -a
source .env.staging
set +a

# Test database connection
python << 'PYTHON'
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import os

async def test_connection():
    engine = create_async_engine(os.getenv("DATABASE_URL"))
    async with engine.begin() as conn:
        result = await conn.execute("SELECT version()")
        print(f"Database connected: {result.scalar()}")
    await engine.dispose()

asyncio.run(test_connection())
PYTHON

# Run database migrations
alembic upgrade head

# Verify migrations
alembic current
alembic history --verbose
```

### Step 6: Run Security Verification

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run security verification
./scripts/verify_security_upgrades.sh --verbose

# Expected output should show:
# ✅ All critical packages verified
# ✅ No dependency conflicts
# ✅ Documentation complete
# ✅ CI/CD workflows valid
```

### Step 7: Start Application (Test Mode)

```bash
# Start application in foreground for testing
uvicorn app.main:app --host 0.0.0.0 --port 8000

# In another terminal, run health checks
curl http://localhost:8000/health
curl http://localhost:8000/health/db
curl http://localhost:8000/health/redis

# Check metrics endpoint
curl http://localhost:8000/metrics | head -20

# Stop application with Ctrl+C
```

### Step 8: Create Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/rss-feed-backend.service

# Add the following content:
```

```ini
[Unit]
Description=RSS Feed Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/rss-feed-backend
Environment="PATH=/opt/rss-feed-backend/venv/bin"
EnvironmentFile=/opt/rss-feed-backend/.env.staging
ExecStart=/opt/rss-feed-backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Restart policy
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/var/log/rss-feed-backend/app.log
StandardError=append:/var/log/rss-feed-backend/error.log

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

```bash
# Create log directory
sudo mkdir -p /var/log/rss-feed-backend
sudo chown www-data:www-data /var/log/rss-feed-backend

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable rss-feed-backend

# Start service
sudo systemctl start rss-feed-backend

# Check status
sudo systemctl status rss-feed-backend
```

### Step 9: Configure Nginx Reverse Proxy (Optional)

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/rss-feed-backend

# Add configuration:
```

```nginx
server {
    listen 80;
    server_name staging-api.example.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/rss-feed-backend-access.log;
    error_log /var/log/nginx/rss-feed-backend-error.log;

    # Proxy to FastAPI application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (no auth required)
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }

    # Metrics endpoint (restrict access)
    location /metrics {
        proxy_pass http://127.0.0.1:8000/metrics;
        allow 10.0.0.0/8;  # Adjust to your monitoring network
        deny all;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/rss-feed-backend /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## Verification

### Automated Verification Script

```bash
#!/bin/bash
# save as: verify_deployment.sh

set -e

echo "🔍 Starting deployment verification..."

# 1. Check service status
echo "1️⃣ Checking service status..."
systemctl is-active --quiet rss-feed-backend && echo "✅ Service is running" || echo "❌ Service is not running"

# 2. Check health endpoints
echo "2️⃣ Checking health endpoints..."
curl -f http://localhost:8000/health > /dev/null 2>&1 && echo "✅ Health endpoint OK" || echo "❌ Health endpoint failed"
curl -f http://localhost:8000/health/db > /dev/null 2>&1 && echo "✅ Database health OK" || echo "❌ Database health failed"

# 3. Check logs for errors
echo "3️⃣ Checking logs for recent errors..."
ERROR_COUNT=$(sudo journalctl -u rss-feed-backend --since "5 minutes ago" | grep -c "ERROR" || true)
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo "✅ No errors in recent logs"
else
    echo "⚠️ Found $ERROR_COUNT errors in logs"
fi

# 4. Check database connection
echo "4️⃣ Checking database migrations..."
cd /opt/rss-feed-backend
source venv/bin/activate
CURRENT_REV=$(alembic current 2>&1 | grep -oP '[a-f0-9]{12}' | head -1)
if [ -n "$CURRENT_REV" ]; then
    echo "✅ Database migrations current: $CURRENT_REV"
else
    echo "❌ Database migrations not current"
fi

# 5. Check process resources
echo "5️⃣ Checking process resources..."
PID=$(systemctl show --property MainPID --value rss-feed-backend)
if [ "$PID" != "0" ]; then
    CPU=$(ps -p $PID -o %cpu= | xargs)
    MEM=$(ps -p $PID -o %mem= | xargs)
    echo "✅ Process resources: CPU=${CPU}% MEM=${MEM}%"
else
    echo "❌ Could not find process"
fi

echo "✅ Verification complete!"
```

### Manual Verification Checklist

```bash
# Service status
sudo systemctl status rss-feed-backend

# View logs (last 50 lines)
sudo journalctl -u rss-feed-backend -n 50

# Follow logs in real-time
sudo journalctl -u rss-feed-backend -f

# Health checks
curl http://localhost:8000/health | jq '.'
curl http://localhost:8000/health/db | jq '.'
curl http://localhost:8000/metrics | head -20

# Check listening ports
sudo netstat -tlnp | grep 8000

# Check process
ps aux | grep uvicorn
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Service Won't Start

```bash
# Check service status
sudo systemctl status rss-feed-backend

# View detailed logs
sudo journalctl -u rss-feed-backend -n 100 --no-pager

# Common causes:
# - Environment variables not loaded
# - Database connection failed
# - Port already in use

# Test manually
cd /opt/rss-feed-backend
source venv/bin/activate
source .env.staging
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Issue 2: Database Connection Failed

```bash
# Test database connection
psql "$DATABASE_URL"

# Check if database exists
psql -h <host> -U <user> -l

# Verify migrations
alembic current
alembic history

# Re-run migrations if needed
alembic upgrade head
```

#### Issue 3: Import Errors

```bash
# Verify all dependencies installed
pip list
pip check

# Reinstall requirements
pip install -r requirements-prod.txt --force-reinstall

# Verify Python path
python -c "import sys; print('\n'.join(sys.path))"
```

#### Issue 4: High Memory Usage

```bash
# Check worker count (should match CPU cores)
# Edit service file to reduce workers
sudo nano /etc/systemd/system/rss-feed-backend.service
# Change: --workers 4 to --workers 2

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart rss-feed-backend
```

#### Issue 5: 502 Bad Gateway (Nginx)

```bash
# Check if application is running
curl http://localhost:8000/health

# Check Nginx error log
sudo tail -f /var/log/nginx/error.log

# Verify Nginx configuration
sudo nginx -t

# Common causes:
# - Application not listening on correct port
# - Firewall blocking connection
# - Application crashed
```

### Useful Commands

```bash
# Restart service
sudo systemctl restart rss-feed-backend

# Stop service
sudo systemctl stop rss-feed-backend

# Start service
sudo systemctl start rss-feed-backend

# View real-time logs
sudo journalctl -u rss-feed-backend -f

# Check last 100 log lines
sudo journalctl -u rss-feed-backend -n 100

# Check logs since specific time
sudo journalctl -u rss-feed-backend --since "10 minutes ago"

# Reload environment (if .env.staging changed)
sudo systemctl restart rss-feed-backend
```

---

## Next Steps

After successful staging deployment:

1. **Run Integration Tests**
   ```bash
   cd /opt/rss-feed-backend
   source venv/bin/activate
   pip install -r requirements-dev.txt
   pytest tests/integration/ -v
   ```

2. **Setup Monitoring**
   - Configure Prometheus scraping
   - Verify Sentry error capture
   - Setup uptime monitoring

3. **Performance Testing**
   - Run load tests
   - Monitor resource usage
   - Tune worker count if needed

4. **Security Review**
   - Run security audit: `./scripts/security_audit.sh`
   - Review CORS settings
   - Verify authentication works

5. **Documentation**
   - Update `STAGING_DEPLOYMENT_READINESS.md` with actual results
   - Document any issues encountered
   - Update runbook with environment-specific details

---

## Support Contacts

- **Backend Team:** [Slack/Email]
- **DevOps Team:** [Slack/Email]
- **On-Call Rotation:** [PagerDuty/OpsGenie]

---

## Appendix: Useful Snippets

### Generate Secure Keys

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate JWT_SECRET_KEY
openssl rand -hex 32

# Generate random password
openssl rand -base64 24
```

### Database Backup

```bash
# Create backup
pg_dump "$DATABASE_URL" > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
psql "$DATABASE_URL" < backup_20250118_120000.sql
```

### Log Rotation Setup

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/rss-feed-backend

# Add:
/var/log/rss-feed-backend/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload rss-feed-backend > /dev/null
    endscript
}
```

### Quick Performance Check

```bash
# API response time
time curl -o /dev/null -s http://localhost:8000/health

# Process memory usage
ps aux | grep uvicorn | awk '{print $11, $6/1024 " MB"}'

# Open files
lsof -p $(pgrep -f "uvicorn app.main:app") | wc -l

# Network connections
netstat -an | grep :8000 | grep ESTABLISHED | wc -l
```

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-18  
**Tested On:** Ubuntu 22.04, Python 3.11
