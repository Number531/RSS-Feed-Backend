# QUICK FIX GUIDE: 0 Sources Issue in Production

## 🎯 The Problem

**Symptom**: All articles in production (Railway) return:
- 0 sources found
- UNVERIFIED verdicts
- Low confidence (0.00-0.10)

**Root Cause**: `EXA_API_KEY` environment variable is missing in Railway deployment

**Impact**: Iterative mode fact-checking is completely non-functional in production

---

## ✅ The Fix (5 minutes)

### Option 1: Railway Dashboard (Recommended)

1. Go to Railway project: https://railway.app/project/your-project-id
2. Click on your service (fact-check or backend)
3. Navigate to **"Variables"** tab
4. Click **"New Variable"**
5. Add:
   - Key: `EXA_API_KEY`
   - Value: `<your_actual_exa_api_key>`
6. Click **"Add"**
7. Railway will automatically redeploy ✅

### Option 2: Railway CLI

```bash
# Login to Railway
railway login

# Link to your project
railway link

# Set the environment variable
railway variables set EXA_API_KEY=<your_actual_exa_api_key>

# Redeploy
railway up
```

### Option 3: Via Git (if using .env.production)

```bash
# Add to .env.production file
echo "EXA_API_KEY=<your_actual_exa_api_key>" >> .env.production

# Commit and push
git add .env.production
git commit -m "fix: Add missing EXA_API_KEY for production"
git push

# Railway will auto-deploy
```

---

## 🧪 Verification

### Before Fix

Look for this warning in Railway logs:

```
WARNING - No Exa API key provided. Using mock client.
```

### After Fix

Railway logs should show:

```
INFO - Exa client initialized with 4 search types
INFO - Comprehensive search for claim: ...
INFO - Comprehensive search completed: 35 total results
```

### Test with API

```bash
curl -X POST "https://your-production-url.up.railway.app/fact-check/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article",
    "mode": "iterative"
  }'

# Check response for:
# - sources_used > 0 (should be 20-40)
# - confidence > 0.60 (should be 0.60-0.95)
# - verdict: not "UNVERIFIED" (should be TRUE/FALSE/MISLEADING/etc)
```

---

## 📊 Expected Results After Fix

| Metric | Before Fix | After Fix |
|--------|------------|-----------|
| Sources Found | **0** | **20-40** |
| Verdict | **UNVERIFIED** | **TRUE/FALSE/MISLEADING** |
| Confidence | **0.00-0.10** | **0.60-0.95** |
| API Cost | **$0.006** | **$0.012-0.016** |

---

## 🧪 Local Testing (Already Working)

You can test locally to confirm expected behavior:

```bash
cd /Users/ej/Downloads/RSS-Feed/fact-check

# Test iterative mode locally
python fact_check_cli.py \
  --url "https://www.cnn.com/politics/article" \
  --iterative \
  --top-k 3

# Should see:
# INFO - Exa client initialized with 4 search types
# ✅ Iterative validation completed
# - Total sources: 25-40 (not 0!)
```

**Local status**: ✅ **WORKING** (EXA_API_KEY is set in `.env`)

---

## 🔍 How to Get Your Exa API Key

If you don't have your Exa API key:

1. Go to https://exa.ai/
2. Sign in to your account
3. Navigate to Dashboard → API Keys
4. Copy your API key
5. Add it to Railway as shown above

---

## 📝 Checklist

Before deploying to Railway, always verify:

- [ ] `EXA_API_KEY` is set in Railway environment
- [ ] `GEMINI_API_KEY` is set in Railway environment
- [ ] `OPENAI_API_KEY` is set (if using image generation)
- [ ] Railway logs show "Exa client initialized" (not "Using mock client")
- [ ] Test with a single article to verify sources > 0

---

## 🚨 If Still Not Working

If you've added the API key but still seeing 0 sources:

1. **Check Railway logs** for the "Exa client initialized" message
2. **Verify the API key is valid** by testing locally:
   ```bash
   cd /Users/ej/Downloads/RSS-Feed/fact-check
   export EXA_API_KEY=your_key_here
   python fact_check_cli.py --url <url> --iterative
   ```
3. **Check Railway deployment logs** for errors during startup
4. **Verify the service redeployed** after adding the variable
5. **Contact Exa support** if the API key is expired or invalid

---

## 📞 Support

- Review full analysis: `docs/CRITICAL_BUG_ZERO_SOURCES_ISSUE.md`
- Check Railway logs: `railway logs`
- Test locally: `python fact_check_cli.py --help`

---

**Priority**: 🔴 CRITICAL  
**Estimated Fix Time**: 5 minutes  
**Downtime**: None (Railway redeploys automatically)  
**Risk**: Low (only adds missing environment variable)

---

*Last Updated: October 29, 2025*
