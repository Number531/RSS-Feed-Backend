# Seed Endpoint Status

## Current Status

The seed endpoint (`POST /api/v1/dev/seed-synthesis`) **is implemented and will work**, but requires a **full server restart** to become active.

## Why It's Not Active Yet

1. ✅ Code is committed and pushed
2. ✅ Module imports successfully (`app.api.v1.endpoints.seed_synthesis`)
3. ✅ Router is registered in `api.py` (line 53)
4. ✅ Routes are defined (`/seed-synthesis` POST and DELETE)
5. ⚠️ **Server needs full restart** (not just reload)

## How to Activate

```bash
# Kill all Python/uvicorn processes
pkill -f uvicorn

# Start fresh
make run
# OR
uvicorn app.main:app --reload --port 8000
```

## Verification

After restart, test with:
```bash
curl -X POST 'http://localhost:8000/api/v1/dev/seed-synthesis?count=5'
```

Should return:
```json
{
  "message": "Successfully seeded 5 articles with synthesis data",
  "count": 5,
  "article_ids": [...]
}
```

## Why This Matters

The seed endpoint is **useful for development** because it:
- Populates synthesis data in 10 seconds (vs 40-60 minutes)
- Creates realistic test data with verdicts, scores, and content
- Can be cleared and reseeded easily

## Current Workaround

Since you already have 10 synthesis articles populated, the seed endpoint is **not critical right now**. The main synthesis endpoints are working:

✅ `GET /articles/synthesis` - Working  
✅ `GET /articles/{id}/synthesis` - Working  
✅ `GET /articles/synthesis/stats` - Working  

## When You'll Need It

The seed endpoint becomes useful when you want to:
- Test with different data sets
- Clear and repopulate synthesis articles
- Add more articles quickly for pagination testing
- Test with specific verdict distributions

## Next Full Restart

The seed endpoint will automatically become active when you:
- Deploy new code to staging/production
- Restart the backend server manually
- Rebuild Docker containers

No code changes needed - just a restart!
