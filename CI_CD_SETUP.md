# CI/CD Setup Documentation

**RSS Feed Backend - Reading History Enhancement v1.0.0**

---

## 📋 Table of Contents

- [Overview](#overview)
- [Pipeline Architecture](#pipeline-architecture)
- [Setup Instructions](#setup-instructions)
- [GitHub Secrets Configuration](#github-secrets-configuration)
- [Pipeline Jobs](#pipeline-jobs)
- [Deployment Workflow](#deployment-workflow)
- [Monitoring & Alerts](#monitoring--alerts)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This CI/CD pipeline automates the entire software delivery process for the RSS Feed Backend, including:

- **Code Quality**: Linting, formatting, and type checking
- **Security**: Dependency vulnerability scanning and code security analysis
- **Testing**: Automated unit and integration tests with coverage reporting
- **Build**: Docker image creation and registry publishing
- **Deployment**: Automated deployment to staging and production environments
- **Monitoring**: Post-deployment health checks and integration tests

### Key Features

✅ **Zero-Downtime Deployments** - Blue-green deployment strategy  
✅ **Automated Testing** - 28 unit tests run on every commit  
✅ **Security Scanning** - Bandit, Safety, and pip-audit checks  
✅ **Code Quality Gates** - Black, flake8, pylint, mypy validation  
✅ **Rollback Capability** - Automated rollback on deployment failures  
✅ **Multi-Environment** - Separate staging and production pipelines  

---

## 🏗️ Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         TRIGGER                                  │
│  - Push to main/develop/staging                                 │
│  - Pull Request                                                  │
│  - Manual Workflow Dispatch                                     │
└────────────────────┬─────────────────────────────────────────────┘
                     │
      ┌──────────────┴──────────────┬──────────────┐
      │                             │              │
┌─────▼─────┐              ┌────────▼────────┐  ┌─▼────────┐
│   LINT    │              │    SECURITY     │  │   TEST   │
│           │              │                 │  │          │
│ - Black   │              │ - Bandit        │  │ - Pytest │
│ - isort   │              │ - Safety        │  │ - Coverage│
│ - flake8  │              │ - pip-audit     │  │ - Reports│
│ - pylint  │              │                 │  │          │
│ - mypy    │              │                 │  │          │
└─────┬─────┘              └────────┬────────┘  └─┬────────┘
      │                             │              │
      └──────────────┬──────────────┴──────────────┘
                     │
              ┌──────▼──────┐
              │    BUILD    │
              │             │
              │ - Docker    │
              │ - Push Hub  │
              └──────┬──────┘
                     │
        ┌────────────┴────────────┐
        │                         │
  ┌─────▼─────┐           ┌──────▼──────┐
  │  STAGING  │           │ PRODUCTION  │
  │  DEPLOY   │           │   DEPLOY    │
  │           │           │             │
  │ - Migrate │           │ - Backup    │
  │ - Deploy  │           │ - Migrate   │
  │ - Smoke   │           │ - Deploy    │
  └─────┬─────┘           │ - Smoke     │
        │                 │ - Notify    │
  ┌─────▼─────┐           └─────────────┘
  │INTEGRATION│
  │   TESTS   │
  └───────────┘
```

---

## 🔧 Setup Instructions

### 1. GitHub Repository Setup

```bash
# Navigate to your repository
cd /path/to/RSS-Feed/backend

# Create GitHub Actions workflow directory
mkdir -p .github/workflows

# The CI/CD workflow is already created at:
# .github/workflows/ci-cd.yml
```

### 2. Docker Hub Setup

1. Create a Docker Hub account at https://hub.docker.com
2. Create a repository named `rss-feed-backend`
3. Generate an access token:
   - Account Settings → Security → New Access Token
   - Name: `GitHub Actions CI/CD`
   - Permissions: Read, Write, Delete
   - Save the token securely

### 3. Server Preparation

#### Staging Server
```bash
# SSH into staging server
ssh user@staging-server

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# Create application directory
sudo mkdir -p /opt/rss-feed-backend
sudo chown $USER:$USER /opt/rss-feed-backend
cd /opt/rss-feed-backend

# Create backups directory
mkdir -p backups

# Copy deployment files
# - docker-compose.prod.yml
# - .env.prod (from .env.prod.template)
```

#### Production Server
Same as staging, but ensure:
- Production database URL is configured
- SSL certificates are in place
- Firewall rules are configured
- Monitoring is set up

---

## 🔐 GitHub Secrets Configuration

Go to **Repository Settings → Secrets and variables → Actions**

### Required Secrets

#### Docker Hub
```
DOCKER_USERNAME      # Your Docker Hub username
DOCKER_PASSWORD      # Docker Hub access token
```

#### Staging Environment
```
STAGING_HOST         # staging-api.example.com
STAGING_USER         # deployment user on staging server
STAGING_SSH_KEY      # Private SSH key for deployment
```

#### Production Environment
```
PRODUCTION_HOST      # api.example.com
PRODUCTION_USER      # deployment user on production server
PRODUCTION_SSH_KEY   # Private SSH key for deployment
PROD_DB_URL          # Production database URL
```

#### Optional (Notifications)
```
SLACK_WEBHOOK_URL    # Slack webhook for deployment notifications
```

#### Optional (Monitoring)
```
CODECOV_TOKEN        # Codecov.io token for coverage reports
SENTRY_DSN           # Sentry DSN for error tracking
```

### Generating SSH Keys for Deployment

```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions

# Copy public key to server
ssh-copy-id -i ~/.ssh/github_actions.pub user@server

# Copy private key content to GitHub Secret
cat ~/.ssh/github_actions
```

---

## ⚙️ Pipeline Jobs

### 1. Lint & Format Check

**Purpose**: Ensure code quality and consistency

**Tools**:
- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Style guide enforcement
- **pylint**: Code analysis
- **mypy**: Type checking

**Triggers**: All pushes and pull requests

**Duration**: ~2 minutes

### 2. Security Scanning

**Purpose**: Identify security vulnerabilities

**Tools**:
- **Bandit**: Python security issues
- **Safety**: Known security vulnerabilities in dependencies
- **pip-audit**: CVE scanning

**Triggers**: All pushes and pull requests

**Duration**: ~3 minutes

**Reports**: Uploaded as artifacts (30-day retention)

### 3. Unit Tests

**Purpose**: Verify functionality and track coverage

**Environment**:
- PostgreSQL 14 test database
- Python 3.10
- All application dependencies

**Metrics**:
- **28 tests** covering repositories and services
- **Target Coverage**: >80%
- **Test Duration**: ~45 seconds

**Triggers**: All pushes and pull requests

**Reports**:
- Coverage report (XML, HTML)
- JUnit test results
- Uploaded to Codecov

### 4. Build Docker Image

**Purpose**: Create deployable Docker images

**Process**:
1. Build image from `Dockerfile`
2. Tag with branch name and commit SHA
3. Push to Docker Hub
4. Use build cache for faster builds

**Triggers**: Push to main/develop/staging or manual dispatch

**Duration**: ~5 minutes (with cache)

**Tags Created**:
```
youruser/rss-feed-backend:main
youruser/rss-feed-backend:main-abc1234
youruser/rss-feed-backend:latest
```

### 5. Deploy to Staging

**Purpose**: Deploy to staging environment for testing

**Triggers**:
- Push to `staging` branch
- Manual workflow dispatch (environment: staging)

**Process**:
1. Pull latest Docker image
2. Run database migrations
3. Deploy with zero downtime
4. Run smoke tests
5. Notify team

**Duration**: ~3 minutes

**Health Checks**:
- Application health endpoint
- Database connection
- API availability

### 6. Deploy to Production

**Purpose**: Deploy to production environment

**Triggers**:
- Push to `main` branch
- Manual workflow dispatch (environment: production)

**Process**:
1. Create database backup
2. Pull latest Docker image
3. Run database migrations
4. Deploy with blue-green strategy
5. Run smoke tests
6. Notify team (Slack)
7. Rollback on failure

**Duration**: ~5 minutes

**Safety Features**:
- Automatic database backup before deployment
- Zero-downtime deployment
- Automated health checks
- Automatic rollback on failure

### 7. Integration Tests (Post-Deploy)

**Purpose**: Verify staging deployment

**Triggers**: After successful staging deployment

**Tests**:
- API endpoint validation
- Reading history functionality
- Database connectivity
- Performance benchmarks

**Duration**: ~2 minutes

---

## 🚀 Deployment Workflow

### Automatic Deployments

#### To Staging
```bash
# Commit and push to staging branch
git checkout staging
git merge develop
git push origin staging

# CI/CD pipeline will:
# 1. Run all tests
# 2. Build Docker image
# 3. Deploy to staging
# 4. Run integration tests
```

#### To Production
```bash
# Commit and push to main branch
git checkout main
git merge staging  # After staging validation
git push origin main

# CI/CD pipeline will:
# 1. Run all tests
# 2. Build Docker image
# 3. Create database backup
# 4. Deploy to production
# 5. Send Slack notification
```

### Manual Deployments

1. Go to **Actions** tab in GitHub repository
2. Select **RSS Feed Backend CI/CD** workflow
3. Click **Run workflow**
4. Select:
   - Branch: `main` or `staging`
   - Environment: `staging` or `production`
5. Click **Run workflow**

### Branch Strategy

```
main (production)
  ↑
staging (staging environment)
  ↑
develop (development)
  ↑
feature/* (feature branches)
```

**Workflow**:
1. Create feature branch from `develop`
2. Make changes and push (triggers CI tests)
3. Create PR to `develop` (triggers full CI)
4. Merge to `develop`
5. Merge `develop` to `staging` (auto-deploys to staging)
6. Test in staging environment
7. Merge `staging` to `main` (auto-deploys to production)

---

## 📊 Monitoring & Alerts

### CI/CD Monitoring

**GitHub Actions Dashboard**:
- Workflow run history
- Job durations and trends
- Failure rates

**Codecov**:
- Coverage trends
- PR coverage reports
- Coverage goals tracking

**Docker Hub**:
- Image sizes
- Pull statistics
- Vulnerability scanning

### Application Monitoring

Post-deployment, monitor:

**Health Endpoints**:
```bash
# Application health
curl https://api.example.com/health

# Database health
curl https://api.example.com/api/v1/health/db
```

**Docker Logs**:
```bash
# On server
docker-compose -f docker-compose.prod.yml logs -f backend
```

**Database Metrics**:
```bash
# Connection count
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Slow queries
psql $DATABASE_URL -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

### Notifications

**Slack Notifications** (Production):
- ✅ Successful deployments
- ❌ Failed deployments
- 🔄 Rollbacks
- ⚠️ Security vulnerabilities

**Email Notifications** (GitHub):
- Workflow failures
- Build errors
- Test failures

---

## 🔍 Troubleshooting

### Common Issues

#### 1. Tests Failing in CI but Passing Locally

**Problem**: Database or environment differences

**Solution**:
```bash
# Ensure test database schema is up to date
python scripts/create_tables.py
python run_preferences_migration.py

# Check environment variables
echo $DATABASE_URL
```

#### 2. Docker Build Failing

**Problem**: Missing dependencies or Dockerfile errors

**Solution**:
```bash
# Build locally to debug
docker build -t rss-feed-backend:test .

# Check build logs
docker build --no-cache -t rss-feed-backend:test . 2>&1 | tee build.log
```

#### 3. Deployment Failing

**Problem**: Server connection, permissions, or resource issues

**Solution**:
```bash
# Test SSH connection
ssh -i ~/.ssh/github_actions user@server

# Check server resources
ssh user@server "df -h && free -h && docker ps"

# Check application logs
ssh user@server "cd /opt/rss-feed-backend && docker-compose -f docker-compose.prod.yml logs --tail=100 backend"
```

#### 4. Rollback Not Working

**Problem**: Backup missing or corrupted

**Solution**:
```bash
# List available backups
ls -lh /backups/*.sql

# Manually restore backup
psql $DATABASE_URL < /backups/pre_deploy_20251011_120000.sql

# Restart application
docker-compose -f docker-compose.prod.yml restart backend
```

### Debug Commands

**Check Pipeline Status**:
```bash
# Using GitHub CLI
gh run list --workflow=ci-cd.yml
gh run view <run-id>
```

**View Job Logs**:
```bash
gh run view <run-id> --log
gh run view <run-id> --job=<job-id> --log
```

**Re-run Failed Jobs**:
```bash
gh run rerun <run-id>
gh run rerun <run-id> --failed
```

---

## 📚 Additional Resources

### Documentation
- [Staging Deployment Guide](./STAGING_DEPLOYMENT_GUIDE.md)
- [Production Deployment Checklist](./PRODUCTION_DEPLOYMENT_CHECKLIST.md)
- [Test Report](./FINAL_TEST_REPORT.md)
- [Reading History Implementation](./READING_HISTORY_IMPLEMENTATION.md)

### Scripts
- Health Check: `scripts/deployment/health_check.sh`
- Rollback: `scripts/deployment/rollback.sh`
- Migration: `run_preferences_migration.py`

### External Links
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Hub](https://hub.docker.com)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [PostgreSQL Backup & Recovery](https://www.postgresql.org/docs/current/backup.html)

---

## ✅ Success Metrics

### Pipeline Performance
- **Build Time**: < 10 minutes (typical: 7 minutes)
- **Test Success Rate**: > 95%
- **Deployment Time**: < 5 minutes
- **Rollback Time**: < 3 minutes

### Quality Metrics
- **Test Coverage**: > 80% (current: 85%+)
- **Security Vulnerabilities**: 0 high/critical
- **Code Quality**: A+ (pylint score > 9.0)

### Deployment Metrics
- **Deployment Frequency**: Daily (staging), Weekly (production)
- **Change Failure Rate**: < 5%
- **Mean Time to Recovery**: < 30 minutes
- **Lead Time**: < 2 hours (commit to production)

---

**Document Version**: 1.0  
**Last Updated**: October 11, 2025  
**Status**: Production Ready ✅
