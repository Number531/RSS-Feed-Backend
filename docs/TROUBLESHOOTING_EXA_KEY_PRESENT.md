# Troubleshooting: EXA_API_KEY Present But Still 0 Sources

## 🔍 Situation

- ✅ `EXA_API_KEY` **IS** present in Railway environment variables
- ❌ Still getting **0 sources** for all articles
- ❌ All claims marked **UNVERIFIED**

This means the issue is **NOT** a missing API key, but something else.

---

## 🚨 Possible Causes

### 1. API Key is Invalid or Expired

**Check**:
```bash
# Test locally with the same key from Railway
export EXA_API_KEY=<copy_key_from_railway>
cd /Users/ej/Downloads/RSS-Feed/fact-check
python -c "
from exa_py import Exa
exa = Exa(api_key='<your_railway_key>')
try:
    result = exa.search('test query', num_results=1)
    print(f'✅ API key valid: {len(result.results)} results')
except Exception as e:
    print(f'❌ API key invalid: {e}')
"
```

**If invalid**: Get a new API key from https://exa.ai/ and update Railway

---

### 2. Wrong Service Has the API Key

Railway projects can have multiple services. The API key needs to be set on the **fact-check service**.

**Check**:
- In Railway dashboard, verify which service has the `EXA_API_KEY`
- It should be on the service that runs the fact-check worker/API
- If it's on the wrong service, add it to the correct one

---

### 3. Environment Variable Not Loaded

The code might not be reading from the environment correctly.

**Check Railway logs for**:
```
WARNING - No Exa API key provided. Using mock client.
```

If this warning appears even though the key is set, the code isn't reading it properly.

**Possible reasons**:
- The service isn't restarting after adding the variable
- The variable name has a typo (should be exactly `EXA_API_KEY`)
- The code is checking a different config source first

---

### 4. Code is Using Wrong Configuration Path

Check which configuration the deployed code is using:

**In `src/clients/exa_client.py` (line 25-37)**:
```python
def __init__(self, api_key: Optional[str] = None):
    self.api_key = api_key or config.exa_api_key  # Check config first
    if not self.api_key:
        self.api_key = os.getenv('EXA_API_KEY')  # Then env var
```

**Priority order**:
1. Passed `api_key` parameter
2. `config.exa_api_key` (from config.py)
3. `os.getenv('EXA_API_KEY')`

**Check `src/config.py`** to see what `config.exa_api_key` defaults to:

```bash
cd /Users/ej/Downloads/RSS-Feed/fact-check
grep -A 5 "exa_api_key" src/config.py
```

---

### 5. API Rate Limiting or Service Issues

Even with a valid key, Exa's API might be:
- Rate limited
- Experiencing downtime
- Blocking requests from Railway's IP range

**Check Railway logs for**:
```
ERROR - Exa API error: <rate limit/timeout/etc>
```

---

## 🔧 Diagnostic Steps

### Step 1: Check Railway Logs

```bash
railway logs --tail 100
```

Look for:
- ✅ `INFO - Exa client initialized with 4 search types` (GOOD)
- ❌ `WARNING - No Exa API key provided` (API key not loaded)
- ❌ `ERROR - Failed to initialize Exa client` (Invalid key or connection issue)
- ❌ `Exception` or `Traceback` related to Exa

### Step 2: Verify API Key Value

1. In Railway dashboard, click on `EXA_API_KEY` variable
2. Copy the value
3. Test it locally:
   ```bash
   cd /Users/ej/Downloads/RSS-Feed/fact-check
   export EXA_API_KEY="<paste_key_here>"
   python fact_check_cli.py --url "https://www.cnn.com/article" --iterative --top-k 1
   ```
4. Check if you get sources > 0

### Step 3: Check Service Configuration

In Railway dashboard:
1. Verify the correct service is running
2. Check "Deployments" tab - ensure latest deployment succeeded
3. Check "Settings" → "Environment" - verify `EXA_API_KEY` is listed
4. Click "Restart" to force a fresh deployment

### Step 4: Check for Code Issues

Look for any recent code changes that might affect ExaClient initialization:

```bash
cd /Users/ej/Downloads/RSS-Feed/fact-check
git log --oneline -10 src/clients/exa_client.py
git log --oneline -10 src/config.py
```

---

## 🐛 Common Issues & Solutions

### Issue: API Key Has Extra Whitespace

**Symptom**: Key looks correct but doesn't work

**Fix**: In Railway, edit the `EXA_API_KEY` variable and ensure no spaces before/after the key

```
❌ EXA_API_KEY=" abc123def456 "
✅ EXA_API_KEY="abc123def456"
```

### Issue: Using Staging Key in Production

**Symptom**: Different keys for staging vs production

**Fix**: Verify you're using the production Exa API key, not a development/staging key

### Issue: Config Override

**Symptom**: Code uses config.py default instead of environment variable

**Fix**: Check `src/config.py` and ensure `exa_api_key` reads from environment:

```python
# Should be:
exa_api_key: str = os.getenv('EXA_API_KEY', '')

# NOT:
exa_api_key: str = 'hardcoded_key'
```

### Issue: Import Error

**Symptom**: `exa_py` package not installed in production

**Check Railway logs for**:
```
ModuleNotFoundError: No module named 'exa_py'
ImportError: exa_py package not installed
```

**Fix**: Ensure `exa_py` is in `requirements.txt`:
```bash
cd /Users/ej/Downloads/RSS-Feed/fact-check
grep exa_py requirements.txt
# Should show: exa_py==x.x.x
```

---

## 🧪 Advanced Debugging

### Add Explicit Logging

Temporarily add debug logging to see what's happening:

**File**: `src/clients/exa_client.py` (after line 37)

```python
# After self.api_key = os.getenv('EXA_API_KEY')
print(f"DEBUG: API key present: {self.api_key is not None}")
print(f"DEBUG: API key length: {len(self.api_key) if self.api_key else 0}")
print(f"DEBUG: API key starts with: {self.api_key[:8] if self.api_key else 'None'}...")
```

Commit, push, and check Railway logs for the debug output.

### Test Exa Client Directly in Production

Add a health check endpoint to test Exa:

```python
# In your API file (e.g., api/fact_check_queue_api.py)

@app.get("/health/exa")
async def exa_health():
    from src.clients.exa_client import ExaClient
    import os
    
    exa = ExaClient()
    
    return {
        "exa_api_key_present": os.getenv('EXA_API_KEY') is not None,
        "exa_api_key_length": len(os.getenv('EXA_API_KEY', '')),
        "client_initialized": exa.client is not None,
        "using_mock": exa.client is None,
        "search_types": exa.search_types if exa.client else []
    }
```

Then test:
```bash
curl https://your-railway-url.up.railway.app/health/exa
```

---

## 📊 Expected Railway Logs (Working)

After fixing, you should see this pattern in logs:

```
2025-10-29 18:00:00 | INFO - Starting fact-check service...
2025-10-29 18:00:01 | INFO - Exa client initialized with 4 search types
2025-10-29 18:00:05 | INFO - Processing article: <url>
2025-10-29 18:00:10 | INFO - Comprehensive search for claim: ...
2025-10-29 18:00:15 | INFO - Comprehensive search completed: 35 total results
2025-10-29 18:00:20 | INFO - Validation completed: TRUE (confidence: 0.85)
```

**NOT**:
```
2025-10-29 18:00:00 | WARNING - No Exa API key provided. Using mock client.
```

---

## 🎯 Action Items

Based on Railway having the API key present:

1. **Check Railway logs** - Look for the exact error message
2. **Verify API key validity** - Test the key locally
3. **Check which service has the key** - Ensure it's on the fact-check service
4. **Force restart** - Redeploy the service in Railway
5. **Add health check** - Create `/health/exa` endpoint to verify
6. **Review recent changes** - Check git log for recent ExaClient changes

---

## 📞 Next Steps

Please provide:
1. **Railway logs** from a recent deployment (run: `railway logs --tail 50`)
2. **First 8 characters** of the EXA_API_KEY from Railway (to verify it's not empty)
3. **Service name** that has the EXA_API_KEY variable
4. **Deployment status** - Is the latest deployment successful?

With this information, we can pinpoint the exact issue.

---

*Last Updated: October 29, 2025 18:02 PST*
