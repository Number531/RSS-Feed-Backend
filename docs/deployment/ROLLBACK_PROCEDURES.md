# Rollback Procedures - Security Upgrades

**Date**: 2025-06-08  
**Version**: 1.0  
**Purpose**: Emergency rollback procedures in case security upgrades cause production issues

---

## 🚨 When to Rollback

Execute rollback procedures if any of the following occur after deployment:

### Critical (Immediate Rollback)
- ❌ Application fails to start
- ❌ Database connectivity lost
- ❌ Authentication system fails
- ❌ Critical endpoints return 500 errors
- ❌ Memory/CPU usage exceeds 90%
- ❌ Cascading failures across services

### High (Rollback within 1 hour)
- ⚠️ Response times > 2x baseline
- ⚠️ Error rate > 5%
- ⚠️ Intermittent authentication failures
- ⚠️ Monitoring dashboards show red

### Medium (Consider Rollback)
- 🟡 Non-critical endpoints failing
- 🟡 Increased latency (< 2x baseline)
- 🟡 Minor functionality degradation
- 🟡 Error rate 1-5%

---

## ⚡ Quick Rollback (5 minutes)

Use this for emergency situations requiring immediate action.

### Step 1: Stop Application (30 seconds)

```bash
# If using systemd
sudo systemctl stop rss-feed-backend

# If using Docker
docker-compose down

# If using screen/tmux
# Find and kill the process
ps aux | grep uvicorn
kill <PID>
```

### Step 2: Activate Environment (30 seconds)

```bash
cd /Users/ej/Downloads/RSS-Feed/backend
source venv/bin/activate  # or your venv path
```

### Step 3: Rollback Dependencies (2-3 minutes)

```bash
# Install old requirements from backup
pip install -r requirements.txt.backup --force-reinstall

# Verify rollback
pip list | grep -E "fastapi|uvicorn|httpx|authlib"

# Expected: Old versions restored
# fastapi 0.104.1
# uvicorn 0.24.0
# httpx 0.25.1
# authlib 1.2.1
```

### Step 4: Restart Application (1 minute)

```bash
# If using systemd
sudo systemctl start rss-feed-backend
sudo systemctl status rss-feed-backend

# If using Docker
docker-compose up -d

# If manual start
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```

### Step 5: Verify (30 seconds)

```bash
# Check health endpoint
curl http://localhost:8000/health

# Check logs
tail -n 50 /var/log/rss-feed/app.log
```

**Total Time**: ~5 minutes

---

## 🔄 Full Rollback (15 minutes)

Use this for planned rollback with full verification.

### Phase 1: Pre-Rollback

#### 1.1 Document Current State

```bash
# Save current package versions
pip freeze > rollback-snapshot-$(date +%Y%m%d_%H%M%S).txt

# Save current logs
cp /var/log/rss-feed/app.log /var/log/rss-feed/app-before-rollback-$(date +%Y%m%d_%H%M%S).log

# Save current metrics
curl -s http://localhost:8000/metrics > metrics-before-rollback-$(date +%Y%m%d_%H%M%S).txt
```

#### 1.2 Notify Team

```bash
# Send notification (adjust for your system)
echo "ROLLBACK IN PROGRESS: Security upgrades being rolled back" | \
  # Your notification system here
```

#### 1.3 Enable Maintenance Mode (if available)

```bash
# Touch maintenance file
touch /var/www/maintenance.html

# Or update load balancer
# This depends on your infrastructure
```

### Phase 2: Execute Rollback

#### 2.1 Stop All Services

```bash
# Stop application
sudo systemctl stop rss-feed-backend

# Stop Celery workers (if running)
sudo systemctl stop celery-worker
sudo systemctl stop celery-beat

# Verify stopped
systemctl status rss-feed-backend
systemctl status celery-worker
systemctl status celery-beat
```

#### 2.2 Rollback Code (if needed)

```bash
# If you deployed code changes along with dependencies
cd /Users/ej/Downloads/RSS-Feed/backend

# Stash any uncommitted changes
git stash

# Rollback to previous commit
git log --oneline | head -5  # Find commit before security updates
git reset --hard <COMMIT_HASH>

# Or checkout previous branch
git checkout <PREVIOUS_BRANCH>
```

#### 2.3 Rollback Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Clear cache
pip cache purge

# Install old requirements
pip install -r requirements.txt.backup --force-reinstall

# Verify critical packages
pip list | grep -E "fastapi|uvicorn|httpx|authlib|h11|h2|certifi|idna|urllib3|starlette"
```

#### 2.4 Verify Environment

```bash
# Run quick import test
python -c "from app import main; print('✅ Imports OK')"

# Check for broken dependencies
pip check
```

### Phase 3: Restart Services

#### 3.1 Start Application

```bash
# Start main application
sudo systemctl start rss-feed-backend

# Wait for startup
sleep 10

# Check status
systemctl status rss-feed-backend
```

#### 3.2 Start Celery (if using)

```bash
sudo systemctl start celery-worker
sudo systemctl start celery-beat

systemctl status celery-worker
systemctl status celery-beat
```

#### 3.3 Verify Services

```bash
# Check all services are running
systemctl list-units | grep rss-feed
systemctl list-units | grep celery
```

### Phase 4: Verification

#### 4.1 Health Checks

```bash
# Test health endpoint
curl -f http://localhost:8000/health || echo "❌ Health check failed"

# Test metrics endpoint
curl -f http://localhost:8000/metrics | head -5 || echo "❌ Metrics failed"

# Test API endpoints
curl -f http://localhost:8000/api/v1/feeds || echo "❌ API failed"
```

#### 4.2 Monitor Logs

```bash
# Watch application logs
tail -f /var/log/rss-feed/app.log

# Watch for errors
tail -f /var/log/rss-feed/app.log | grep -i error
```

#### 4.3 Check Metrics

```bash
# CPU usage
top -b -n 1 | grep uvicorn

# Memory usage
ps aux | grep uvicorn | awk '{print $4}'

# Open connections
netstat -an | grep :8000 | wc -l
```

### Phase 5: Post-Rollback

#### 5.1 Disable Maintenance Mode

```bash
# Remove maintenance file
rm /var/www/maintenance.html

# Update load balancer
# Depends on your infrastructure
```

#### 5.2 Notify Team

```bash
echo "ROLLBACK COMPLETE: Services restored to previous version" | \
  # Your notification system here
```

#### 5.3 Document Issues

```bash
# Create incident report
cat > rollback-incident-$(date +%Y%m%d_%H%M%S).md << 'EOF'
# Rollback Incident Report

**Date**: $(date)
**Reason**: [Why rollback was necessary]
**Duration**: [Time from deployment to rollback]
**Impact**: [What was affected]

## Issues Encountered
1. [Issue 1]
2. [Issue 2]
3. [Issue 3]

## Root Cause
[Analysis of what went wrong]

## Prevention Measures
1. [What we'll do differently next time]
2. [Additional testing needed]
3. [Process improvements]

## Follow-up Actions
- [ ] Fix identified issues
- [ ] Re-test in staging
- [ ] Schedule re-deployment
EOF
```

---

## 🔍 Verification Checklist

After rollback, verify the following:

### Critical Services
- [ ] Application starts successfully
- [ ] Health endpoint returns 200 OK
- [ ] Database connectivity confirmed
- [ ] Redis connectivity confirmed
- [ ] Authentication working
- [ ] API endpoints responding

### Performance
- [ ] Response times within normal range (< 500ms)
- [ ] CPU usage < 50%
- [ ] Memory usage < 70%
- [ ] No memory leaks detected
- [ ] Error rate < 1%

### Functionality
- [ ] Users can log in
- [ ] Feeds can be fetched
- [ ] Articles can be read
- [ ] Comments can be posted
- [ ] Search working
- [ ] All critical features functional

### Monitoring
- [ ] Logs show no errors
- [ ] Metrics dashboard green
- [ ] Sentry shows no new errors
- [ ] Prometheus metrics normal
- [ ] Alert systems normal

---

## 📝 Rollback Decision Matrix

| Scenario | Action | Timeline |
|----------|--------|----------|
| App won't start | Quick Rollback | Immediate |
| Auth failures | Quick Rollback | Immediate |
| Database errors | Quick Rollback | Immediate |
| High error rate (>10%) | Quick Rollback | 15 min |
| Slow responses (>2x) | Full Rollback | 30 min |
| Minor issues | Monitor | 1-2 hours |
| Feature degradation | Evaluate | 2-4 hours |

---

## 🚀 Re-Deployment Plan

After successful rollback:

### 1. Root Cause Analysis (1-2 days)
- [ ] Identify what went wrong
- [ ] Document lessons learned
- [ ] Update testing procedures
- [ ] Create fix/mitigation plan

### 2. Fix and Re-Test (2-3 days)
- [ ] Apply fixes to security upgrades
- [ ] Test in development
- [ ] Test in staging for 48 hours
- [ ] Run full deployment test plan
- [ ] Get approval from team

### 3. Staged Re-Deployment (1 day)
- [ ] Deploy to canary (10% traffic)
- [ ] Monitor for 2 hours
- [ ] Deploy to 50% traffic
- [ ] Monitor for 4 hours
- [ ] Deploy to 100% traffic
- [ ] Monitor for 24 hours

---

## 📞 Emergency Contacts

**During Rollback**:
- DevOps Lead: _______________
- Backend Lead: _______________
- Security Team: _______________
- On-Call Engineer: _______________

**Escalation Path**:
1. On-Call Engineer (immediate)
2. Backend Lead (15 min)
3. CTO/VP Engineering (30 min)

---

## 🔐 Security Considerations

### After Rollback

**Important**: Rolling back means returning to vulnerable versions!

#### Immediate Actions (Within 1 hour)
- [ ] Re-enable WAF rules to compensate for vulnerabilities
- [ ] Increase logging and monitoring
- [ ] Set up alerts for exploitation attempts
- [ ] Restrict external access if possible
- [ ] Document vulnerable state

#### Short-term (Within 24 hours)
- [ ] Review access logs for exploitation attempts
- [ ] Apply temporary mitigations
- [ ] Schedule fix deployment
- [ ] Communicate risk to stakeholders

#### Medium-term (Within 1 week)
- [ ] Fix issues that caused rollback
- [ ] Complete full security re-testing
- [ ] Re-deploy with fixes
- [ ] Conduct post-mortem

**Risk Level After Rollback**: 🔴 HIGH
- 89 known vulnerabilities re-introduced
- Critical auth vulnerabilities active
- Request smuggling vectors re-opened
- Monitoring reduced during rollback

---

## 📚 Related Documentation

- `DEPLOYMENT_TESTING_PLAN.md` - Pre-deployment testing
- `SECURITY_AUDIT_REPORT.md` - Vulnerabilities addressed
- `SECURITY_REVIEW_CHECKLIST.md` - Review procedures
- `VULNERABILITY_ANALYSIS.md` - Dependency analysis

---

## 🔄 Version History

| Date | Version | Changes |
|------|---------|---------|
| 2025-06-08 | 1.0 | Initial rollback procedures |

---

**Document Version**: 1.0  
**Last Updated**: 2025-06-08  
**Next Review**: After any rollback event
