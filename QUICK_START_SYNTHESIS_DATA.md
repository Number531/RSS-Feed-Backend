# 🚀 Quick Start: Populate Synthesis Data in 10 Seconds

**For Frontend Team** - Get synthesis data instantly without waiting for fact-checking!

---

## ⚡ Super Quick Method (10 seconds)

### Step 1: Seed Test Data

```bash
curl -X POST 'http://localhost:8000/api/v1/dev/seed-synthesis?count=10'
```

**That's it!** Your synthesis endpoints now have data.

### Step 2: Verify It Worked

```bash
curl 'http://localhost:8000/api/v1/articles/synthesis?page=1&page_size=10' | jq '.total'
# Should return: 10
```

### Step 3: View in Frontend

Refresh your frontend - you should now see 10 synthesis articles with:
- ✅ Full markdown content (1,400+ words)
- ✅ Fact-check verdicts (TRUE, MOSTLY TRUE, MIXED, etc.)
- ✅ Credibility scores
- ✅ Timelines and references
- ✅ All metadata fields

---

## 🎯 What Just Happened?

The seed endpoint:
1. Found 10 existing articles in your database
2. Added realistic synthesis content to each
3. Set all the required fields (verdicts, scores, metadata)
4. Populated JSONB arrays (references, timelines, notes)

**Result:** Instant test data without 40-60 minute fact-check wait!

---

## 📊 Detailed Usage

### Seed Different Amounts

```bash
# Seed 5 articles (default)
curl -X POST 'http://localhost:8000/api/v1/dev/seed-synthesis'

# Seed 20 articles (maximum)
curl -X POST 'http://localhost:8000/api/v1/dev/seed-synthesis?count=20'
```

### Clear All Synthesis Data

```bash
# Reset everything (useful for retesting)
curl -X DELETE 'http://localhost:8000/api/v1/dev/seed-synthesis'
```

### Check What You Have

```bash
# List all synthesis articles
curl 'http://localhost:8000/api/v1/articles/synthesis?page=1&page_size=100' | jq '{total: .total, verdicts: [.items[].fact_check_verdict]}'

# Get stats
curl 'http://localhost:8000/api/v1/articles/synthesis/stats' | jq '.'

# View a single article
ARTICLE_ID="paste-an-id-from-list"
curl "http://localhost:8000/api/v1/articles/${ARTICLE_ID}/synthesis" | jq '.'
```

---

## 🎨 What the Data Looks Like

### Sample Synthesis Article Structure

Each seeded article includes:

**Metadata:**
- `has_synthesis = true`
- `fact_check_verdict` = Rotates through TRUE, MOSTLY TRUE, MIXED, MOSTLY FALSE, FALSE
- `verdict_color` = Matching colors (#10b981 green → #ef4444 red)
- `fact_check_score` = 90, 75, 60, 45, 30 (based on verdict)
- `synthesis_word_count` = ~350 words
- `synthesis_read_minutes` = ~2 minutes

**Content:**
- Full markdown synthesis article with:
  - Executive Summary
  - Background Context
  - Detailed Analysis (3 claims)
  - Expert Perspectives  
  - References & Citations
  - Conclusion & Key Takeaways

**JSONB Arrays:**
```json
{
  "references": [
    {"id": 1, "text": "Official documentation", "url": "...", "credibility": "high"}
  ],
  "event_timeline": [
    {"date": "2025-01-15", "event": "Initial Report", "description": "..."}
  ],
  "margin_notes": [
    {"location": "paragraph_2", "note": "Important context..."}
  ],
  "context_and_emphasis": [
    {"type": "context", "text": "Historical precedent..."}
  ]
}
```

---

## 🔄 Workflow for Frontend Development

### First Time Setup
```bash
# 1. Seed data
curl -X POST 'http://localhost:8000/api/v1/dev/seed-synthesis?count=10'

# 2. Verify
curl 'http://localhost:8000/api/v1/articles/synthesis' | jq '.total'

# 3. Start building your UI
# Frontend will now have real data to work with
```

### Reset and Reseed
```bash
# 1. Clear old data
curl -X DELETE 'http://localhost:8000/api/v1/dev/seed-synthesis'

# 2. Seed new data
curl -X POST 'http://localhost:8000/api/v1/dev/seed-synthesis?count=10'
```

### Test Different Scenarios
```bash
# Just TRUE and MOSTLY TRUE (seed 2)
curl -X POST 'http://localhost:8000/api/v1/dev/seed-synthesis?count=2'

# Full variety (seed 10+)
curl -X POST 'http://localhost:8000/api/v1/dev/seed-synthesis?count=15'

# Maximum test data (seed 20)
curl -X POST 'http://localhost:8000/api/v1/dev/seed-synthesis?count=20'
```

---

## ⚠️ Important Notes

### This is Development Only

- ✅ Perfect for frontend development and testing
- ✅ Fast way to populate test data
- ❌ NOT for production use
- ❌ NOT real fact-checked content (it's synthetic/sample data)

### Required Articles

You need existing articles in the database first. If you get:
```json
{"detail": "No articles found without synthesis data"}
```

Then either:
1. Your articles already have synthesis (check with `/articles/synthesis`)
2. You have no articles at all (check with `/articles`)

### Endpoint Location

```
POST   /api/v1/dev/seed-synthesis?count=10
DELETE /api/v1/dev/seed-synthesis
```

Available at: http://localhost:8000/docs (look for "development" tag)

---

## 🎉 Benefits

### Before (The Slow Way)
```
1. Fetch articles from RSS      →  30 seconds
2. Trigger fact-check           →  5 seconds  
3. Wait for processing          →  40-70 minutes ⏰
4. Test frontend                →  Finally!
```

### After (The Fast Way)
```
1. curl -X POST .../seed-synthesis  →  10 seconds ⚡
2. Test frontend                    →  Done!
```

**Time Saved:** 40-70 minutes → 10 seconds

---

## 🔍 Troubleshooting

### "Connection refused"
```bash
# Make sure backend is running
curl http://localhost:8000/health
```

### "No articles found"
```bash
# Check if you have any articles
curl 'http://localhost:8000/api/v1/articles/?page=1&page_size=5' | jq '.articles | length'

# If 0, you need to fetch some articles first
# Or wait for RSS background processing
```

### "Nothing shows in frontend"
```bash
# Verify data exists in API
curl 'http://localhost:8000/api/v1/articles/synthesis' | jq '.total'

# If > 0, check your frontend is calling the right endpoint
# Should be: GET /api/v1/articles/synthesis
```

---

## 📚 Related Documentation

- `SYNTHESIS_ENDPOINTS_WORKING_GUIDE.md` - Complete endpoint docs
- `SYNTHESIS_COLUMN_STATUS.md` - Why columns were empty
- `SYNTHESIS_ENDPOINTS_TEST_RESULTS.md` - API test results

---

## 🎯 Summary

**One command to rule them all:**
```bash
curl -X POST 'http://localhost:8000/api/v1/dev/seed-synthesis?count=10'
```

Now go build your amazing synthesis UI! 🚀
