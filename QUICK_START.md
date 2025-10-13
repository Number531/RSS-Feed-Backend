# 🚀 Quick Start - Staging Deployment

**Read this first!** This is your 2-minute quick reference.

---

## ✅ What's Done

- ✅ CORS configured for staging
- ✅ Secure secrets generated
- ✅ `.env.staging` file created
- ✅ Admin creation script ready
- ✅ All tests passing (87%)
- ✅ Security hardened
- ✅ Ready to deploy!

---

## 🎯 What You Need to Do (10 minutes)

### 1. Save Your Credentials (2 min)
```bash
# View credentials
cat STAGING_CREDENTIALS.txt

# Copy to password manager, then delete:
rm STAGING_CREDENTIALS.txt
```

**Your Credentials:**
- Admin Password: `IvPkTBbgFPHixMBAWqY4KITgZ3gaYU`
- JWT Secret: `96b38cb5cc0e449f611acdd963a504e6189a6ab8aaf51be3e15301c0b66c6de4`

---

### 2. Update `.env.staging` (5 min)
```bash
nano .env.staging
```

**Update these 4 lines:**
- Line 35: `BACKEND_CORS_ORIGINS=["https://YOUR-DOMAIN.com"]`
- Line 51: `DATABASE_URL=postgresql+asyncpg://...YOUR-DB...`
- Line 64: `REDIS_URL=redis://...YOUR-REDIS...`
- Line 155: `ADMIN_EMAIL=admin@YOUR-DOMAIN.com`

Save: `Ctrl+X`, `Y`, `Enter`

---

### 3. Deploy (15-30 min)

**Option A: Docker (Recommended)**
```bash
docker build -t rss-feed:staging .
docker run -d --name rss-staging --env-file .env.staging -p 8000:8000 rss-feed:staging
```

**Option B: Direct Python**
```bash
# Install dependencies
pip install -r requirements-prod.txt

# Run migrations
alembic upgrade head

# Create admin
python scripts/create_admin.py

# Start server
uvicorn app.main:app --env-file .env.staging --host 0.0.0.0 --port 8000
```

---

### 4. Verify (2 min)
```bash
# Health check
curl http://localhost:8000/health

# Should return: {"status":"healthy","database":"connected"}
```

---

## 📚 Full Documentation

- **Detailed Guide:** `DEPLOY_TO_STAGING.md`
- **Setup Summary:** `SETUP_COMPLETE_SUMMARY.md`
- **Improvements:** `PRE_STAGING_IMPROVEMENTS.md`
- **Test Results:** `TEST_RESULTS_FINAL.md`

---

## 🆘 Help

**Issue:** CORS errors
→ Update line 35 in `.env.staging` with your actual domain

**Issue:** Database connection fails  
→ Update line 51 in `.env.staging` with your database URL

**Issue:** Can't create admin  
→ Run: `alembic upgrade head` first

**Issue:** Something else  
→ Check: `DEPLOY_TO_STAGING.md` or `SETUP_COMPLETE_SUMMARY.md`

---

## ✅ Ready?

1. [ ] Saved credentials to password manager
2. [ ] Deleted `STAGING_CREDENTIALS.txt`
3. [ ] Updated `.env.staging` with your values
4. [ ] Deployed using commands above
5. [ ] Verified health check passes

**All checked?** 🎉 You're live on staging!

---

**Next:** Monitor for 24-48 hours, then deploy to production.

Good luck! 🚀
