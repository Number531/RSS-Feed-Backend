# Quick Start Guide - Deployment & CI/CD

**Reading History Enhancement v1.0.0**

---

## 🚀 Quick Deployment

### Local Testing
```bash
# Run unit tests
pytest tests/ -v

# Health check
./scripts/deployment/health_check.sh http://localhost:8000
```

### Deploy to Staging
```bash
git checkout staging
git merge develop
git push origin staging
# Watch: https://github.com/your-org/RSS-Feed/actions
```

### Deploy to Production
```bash
git checkout main
git merge staging
git push origin main
# Watch: https://github.com/your-org/RSS-Feed/actions
```

---

## ⚙️ GitHub Secrets Setup

**Required for CI/CD**:

```bash
# Go to: Repository Settings → Secrets → Actions

# Docker Hub
DOCKER_USERNAME=your_username
DOCKER_PASSWORD=your_token

# Staging
STAGING_HOST=staging-api.example.com
STAGING_USER=deploy
STAGING_SSH_KEY=<private_key>

# Production
PRODUCTION_HOST=api.example.com
PRODUCTION_USER=deploy
PRODUCTION_SSH_KEY=<private_key>
PROD_DB_URL=postgresql://...
```

---

## 🔧 Server Setup

```bash
# On each server (staging & production)

# 1. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# 2. Create directories
sudo mkdir -p /opt/rss-feed-backend
sudo chown $USER:$USER /opt/rss-feed-backend
cd /opt/rss-feed-backend
mkdir -p backups

# 3. Copy files
# - docker-compose.prod.yml
# - .env.prod

# 4. Start services
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🏥 Health Checks

```bash
# Local
curl http://localhost:8000/health

# Staging
curl https://staging-api.example.com/health

# Production
curl https://api.example.com/health

# Using script
./scripts/deployment/health_check.sh https://api.example.com
```

---

## 🔄 Rollback

```bash
# Interactive
./scripts/deployment/rollback.sh

# With specific backup
./scripts/deployment/rollback.sh /backups/pre_deploy_20251011.sql
```

---

## 📊 Monitoring

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Check database
psql $DATABASE_URL -c "SELECT COUNT(*) FROM reading_history;"

# GitHub Actions
# https://github.com/your-org/RSS-Feed/actions
```

---

## 📚 Full Documentation

- **CI/CD Setup**: [CI_CD_SETUP.md](./CI_CD_SETUP.md)
- **Staging Guide**: [STAGING_DEPLOYMENT_GUIDE.md](./STAGING_DEPLOYMENT_GUIDE.md)
- **Production Checklist**: [PRODUCTION_DEPLOYMENT_CHECKLIST.md](./PRODUCTION_DEPLOYMENT_CHECKLIST.md)
- **Complete Summary**: [DI_CICD_COMPLETE.md](./DI_CICD_COMPLETE.md)

---

## 🆘 Quick Troubleshooting

### Tests Failing
```bash
python scripts/create_tables.py
python run_preferences_migration.py
pytest tests/ -v
```

### Docker Build Failing
```bash
docker build --no-cache -t test . 2>&1 | tee build.log
```

### Deployment Failing
```bash
# Check SSH
ssh -i ~/.ssh/github_actions user@server

# Check logs
docker-compose -f docker-compose.prod.yml logs --tail=100
```

### Need Help?
Check [CI_CD_SETUP.md](./CI_CD_SETUP.md) for detailed troubleshooting.

---

**Status**: ✅ Production Ready  
**Version**: 1.0.0
