# Seed Synthesis Endpoints - Complete Guide

**Date:** November 21, 2025  
**Status:** ✅ FULLY OPERATIONAL  
**Version:** 1.0

---

## 🎉 Executive Summary

All synthesis endpoints are now **fully functional**, including the new **seed endpoints** for rapid testing! You can now:

1. ✅ **GET** synthesis articles from the feed
2. ✅ **GET** individual synthesis article details  
3. ✅ **GET** synthesis statistics
4. ✅ **POST** to quickly seed test data (NEW!)
5. ✅ **DELETE** to clear test data (NEW!)

**Current Status:** 10 articles with full synthesis data ready for testing.

---

## 📋 Table of Contents

1. [Quick Start - 30 Seconds](#quick-start)
2. [Main Synthesis Endpoints](#main-synthesis-endpoints)
3. [Seed Endpoints (Development)](#seed-endpoints)
4. [Complete API Reference](#complete-api-reference)
5. [Sample Data Structure](#sample-data-structure)
6. [Testing Workflow](#testing-workflow)
7. [Troubleshooting](#troubleshooting)

---

## ⚡ Quick Start

### Test All Endpoints (30 seconds)

```bash
# 1. Get synthesis feed (should return 10 articles)
curl http://localhost:8000/api/v1/articles/synthesis

# 2. Get synthesis stats
curl http://localhost:8000/api/v1/articles/synthesis/stats

# 3. Seed 5 more articles (development)
curl -X POST 'http://localhost:8000/api/v1/dev/seed-synthesis?count=5'

# 4. Clear all synthesis data (careful!)
curl -X DELETE http://localhost:8000/api/v1/dev/seed-synthesis
```

---

## 🚀 Main Synthesis Endpoints

### 1. GET Synthesis Feed

**Endpoint:** `GET /api/v1/articles/synthesis`

Returns paginated list of articles with synthesis data.

**Query Parameters:**
- `page` (int, default: 1) - Page number
- `limit` (int, default: 20, max: 100) - Items per page
- `verdict` (string, optional) - Filter by verdict: `TRUE`, `MOSTLY TRUE`, `MIXED`, `MOSTLY FALSE`, `FALSE`, `UNVERIFIED`

**Example Request:**
```bash
curl 'http://localhost:8000/api/v1/articles/synthesis?page=1&limit=10'
```

**Example Response:**
```json
{
  "items": [
    {
      "id": "ba4dcab9-2fb9-4884-8849-bd29f8c6ca67",
      "title": "Eric Swalwell announces run for California governor",
      "url": "https://example.com/article",
      "source_name": "Fox News - Politics",
      "published_at": "2025-01-20T15:30:00Z",
      "has_synthesis": true,
      "synthesis_preview": "# Eric Swalwell announces run for California governor...",
      "fact_check_verdict": "TRUE",
      "verdict_color": "#10b981",
      "fact_check_score": 90,
      "synthesis_word_count": 450,
      "synthesis_read_minutes": 3,
      "has_timeline": true,
      "has_context_emphasis": true,
      "timeline_event_count": 3,
      "reference_count": 4,
      "margin_note_count": 5
    }
  ],
  "total": 10,
  "page": 1,
  "limit": 10,
  "pages": 1
}
```

### 2. GET Single Synthesis Article

**Endpoint:** `GET /api/v1/articles/{article_id}/synthesis`

Returns complete synthesis content for a specific article.

**Example Request:**
```bash
curl http://localhost:8000/api/v1/articles/ba4dcab9-2fb9-4884-8849-bd29f8c6ca67/synthesis
```

**Example Response:**
```json
{
  "article_id": "ba4dcab9-2fb9-4884-8849-bd29f8c6ca67",
  "synthesis_article": "# Eric Swalwell announces run for California governor\n\n## Executive Summary...",
  "fact_check_verdict": "TRUE",
  "verdict_color": "#10b981",
  "fact_check_score": 90,
  "word_count": 450,
  "read_minutes": 3,
  "article_data": {
    "references": [
      {
        "id": 1,
        "text": "Official government documentation",
        "url": "https://example.com/doc1",
        "credibility": "high"
      }
    ],
    "event_timeline": [
      {
        "date": "2025-01-15",
        "event": "Initial Report",
        "description": "The story first emerged from credible sources"
      }
    ],
    "margin_notes": [
      {
        "id": 1,
        "position": 150,
        "type": "context",
        "content": "Additional context about this claim"
      }
    ]
  },
  "has_timeline": true,
  "timeline_event_count": 3,
  "reference_count": 4,
  "margin_note_count": 5
}
```

### 3. GET Synthesis Statistics

**Endpoint:** `GET /api/v1/articles/synthesis/stats`

Returns aggregated statistics about synthesis articles.

**Example Request:**
```bash
curl http://localhost:8000/api/v1/articles/synthesis/stats
```

**Example Response:**
```json
{
  "total_synthesis_articles": 10,
  "average_credibility_score": 60.0,
  "verdict_distribution": {
    "TRUE": 2,
    "MOSTLY TRUE": 2,
    "MIXED": 2,
    "MOSTLY FALSE": 2,
    "FALSE": 2
  },
  "average_word_count": 450,
  "average_read_minutes": 3,
  "articles_with_timeline": 10,
  "articles_with_context": 10
}
```

---

## 🛠️ Seed Endpoints (Development)

### NEW! POST Seed Synthesis Data

**Endpoint:** `POST /api/v1/dev/seed-synthesis`

Quickly populate existing articles with sample synthesis data for frontend testing.

**Query Parameters:**
- `count` (int, default: 5, max: 20) - Number of articles to seed

**Example Request:**
```bash
curl -X POST 'http://localhost:8000/api/v1/dev/seed-synthesis?count=10'
```

**Example Response:**
```json
{
  "message": "Successfully seeded 7 articles with synthesis data",
  "count": 7,
  "article_ids": [
    "3de45d4c-df62-41b7-9868-aa31b91b42c9",
    "ef6779d2-a2db-4b36-ac24-8a2bfaa2d102",
    "f16e1658-975a-470f-9dc8-44b9bd5cba8d",
    "54ad68bd-6777-4ea1-81ed-d8e2e5df703d",
    "52a4f179-8b92-4ce1-8861-9f0ac301b3e8",
    "269291cb-433d-4b56-8fd6-c82fd425cdb2",
    "fa4a376e-05f1-4bb3-ac42-8ce0199e11a3"
  ]
}
```

**What Gets Created:**
- ✅ Full markdown synthesis article (450+ words)
- ✅ Fact-check verdict (TRUE, MOSTLY TRUE, MIXED, MOSTLY FALSE, FALSE)
- ✅ Credibility scores (30-90 range)
- ✅ Verdict colors (green to red)
- ✅ Timeline events (3-7 events)
- ✅ References (4-7 references)
- ✅ Margin notes (5-10 notes)
- ✅ Word count and read time estimates

**Error Responses:**

404 - No articles available without synthesis:
```json
{
  "detail": "No articles found without synthesis data"
}
```

### NEW! DELETE Clear Synthesis Data

**Endpoint:** `DELETE /api/v1/dev/seed-synthesis`

Remove all synthesis data from articles (useful for resetting test environment).

**Example Request:**
```bash
curl -X DELETE http://localhost:8000/api/v1/dev/seed-synthesis
```

**Example Response:**
```json
{
  "message": "Successfully cleared all synthesis data from articles"
}
```

⚠️ **Warning:** This clears ALL synthesis data from ALL articles. Use with caution!

---

## 📖 Complete API Reference

### Base URL
```
http://localhost:8000/api/v1
```

### Endpoints Summary

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| GET | `/articles/synthesis` | List synthesis articles | ✅ Working |
| GET | `/articles/{id}/synthesis` | Get single synthesis | ✅ Working |
| GET | `/articles/synthesis/stats` | Get statistics | ✅ Working |
| POST | `/dev/seed-synthesis` | Seed test data | ✅ Working |
| DELETE | `/dev/seed-synthesis` | Clear test data | ✅ Working |

### Verdict Types

| Verdict | Color | Score Range | Meaning |
|---------|-------|-------------|---------|
| TRUE | #10b981 (green) | 90 | Fully accurate |
| MOSTLY TRUE | #84cc16 (lime) | 75 | Mostly accurate |
| MIXED | #fbbf24 (yellow) | 60 | Mixed accuracy |
| MOSTLY FALSE | #fb923c (orange) | 45 | Mostly inaccurate |
| FALSE | #ef4444 (red) | 30 | Fully inaccurate |
| UNVERIFIED | #6b7280 (gray) | 50 | Cannot verify |

---

## 📊 Sample Data Structure

### Synthesis Article Fields

```typescript
interface SynthesisArticle {
  // Basic Article Info
  id: string;
  title: string;
  url: string;
  source_name: string;
  published_at: string;
  
  // Synthesis Flags
  has_synthesis: boolean;
  fact_check_mode: string; // "synthesis"
  
  // Synthesis Content
  synthesis_article: string; // Full markdown content
  synthesis_preview: string; // First 280 chars
  synthesis_word_count: number;
  synthesis_read_minutes: number;
  
  // Verdict Info
  fact_check_verdict: "TRUE" | "MOSTLY TRUE" | "MIXED" | "MOSTLY FALSE" | "FALSE" | "UNVERIFIED";
  verdict_color: string; // Hex color code
  fact_check_score: number; // 0-100
  
  // Feature Flags
  has_timeline: boolean;
  has_context_emphasis: boolean;
  
  // Counts
  timeline_event_count: number;
  reference_count: number;
  margin_note_count: number;
  
  // Structured Data (JSONB)
  article_data: {
    references: Reference[];
    event_timeline: TimelineEvent[];
    margin_notes: MarginNote[];
  };
}

interface Reference {
  id: number;
  text: string;
  url: string;
  credibility: "high" | "medium" | "low";
}

interface TimelineEvent {
  date: string; // ISO date
  event: string;
  description: string;
}

interface MarginNote {
  id: number;
  position: number; // Character position in text
  type: "context" | "correction" | "clarification" | "source";
  content: string;
}
```

---

## 🧪 Testing Workflow

### Recommended Testing Flow

1. **Start Fresh**
   ```bash
   # Clear existing data
   curl -X DELETE http://localhost:8000/api/v1/dev/seed-synthesis
   ```

2. **Seed Test Data**
   ```bash
   # Create 10 test articles
   curl -X POST 'http://localhost:8000/api/v1/dev/seed-synthesis?count=10'
   ```

3. **Test Feed Endpoint**
   ```bash
   # Get first page
   curl 'http://localhost:8000/api/v1/articles/synthesis?page=1&limit=5'
   
   # Filter by verdict
   curl 'http://localhost:8000/api/v1/articles/synthesis?verdict=TRUE'
   ```

4. **Test Detail View**
   ```bash
   # Use an article_id from the feed response
   curl http://localhost:8000/api/v1/articles/{article_id}/synthesis
   ```

5. **Test Statistics**
   ```bash
   curl http://localhost:8000/api/v1/articles/synthesis/stats
   ```

### Frontend Integration Checklist

- [ ] Display synthesis feed with pagination
- [ ] Show verdict badges with correct colors
- [ ] Render markdown synthesis content
- [ ] Display timeline events
- [ ] Show references with credibility indicators
- [ ] Render margin notes
- [ ] Show read time estimates
- [ ] Filter by verdict type
- [ ] Handle loading states
- [ ] Handle error states (404, 500)

---

## 🔧 Troubleshooting

### Issue: Endpoint returns 404

**Solution:** Ensure you're using the correct URL with `/api/v1` prefix:
```bash
# ❌ Wrong
curl http://localhost:8000/dev/seed-synthesis

# ✅ Correct
curl http://localhost:8000/api/v1/dev/seed-synthesis
```

### Issue: Seed endpoint says "No articles found"

**Solution:** The database needs articles without synthesis data. Either:
1. Clear existing synthesis data first: `DELETE /dev/seed-synthesis`
2. Add more articles to the database
3. Use the RSS feed endpoints to fetch new articles

### Issue: Synthesis feed returns empty array

**Solution:** Seed data first:
```bash
curl -X POST 'http://localhost:8000/api/v1/dev/seed-synthesis?count=10'
```

### Issue: Article doesn't have synthesis data

**Symptoms:**
- `has_synthesis` is `false` or `null`
- `synthesis_article` is empty

**Solution:** The article hasn't been processed yet. Use the seed endpoint to add test data, or wait for the fact-check service to process it.

---

## 📝 Testing Notes

### Current Test Data (as of Nov 21, 2025)

- **Total Articles:** 10 with full synthesis
- **Verdict Distribution:** 2 each of TRUE, MOSTLY TRUE, MIXED, MOSTLY FALSE, FALSE
- **Average Word Count:** ~450 words
- **Average Read Time:** ~3 minutes
- **All articles include:**
  - Full markdown content
  - Timeline events (3-7 per article)
  - References (4-7 per article)
  - Margin notes (5-10 per article)

### Sample Markdown Structure

```markdown
# {Article Title}

## Executive Summary

Brief overview with fact-check verdict.

**Fact-Check Verdict:** TRUE

## Background Context

Context about the story.

### Key Timeline Events

1. **Initial Report** - Description
2. **Verification Process** - Description
3. **Expert Analysis** - Description

## Detailed Analysis

### Claim 1: Primary Assertion
**Assessment:** Verification details

**Supporting Evidence:**
- Primary source documents
- Expert verification

### Claim 2: Secondary Context
**Assessment:** Additional context

## Expert Perspectives

> "Quote from expert" - Dr. Expert Source

## References and Citations

1. [Reference 1] - Description
2. [Reference 2] - Description

## Conclusion

Final verdict and key takeaways.

### Key Takeaways
- ✓ Main claims substantiated
- ⚠️ Context important
- ℹ️ Ongoing developments

### Credibility Assessment
Overall assessment of article quality.
```

---

## 🎯 Next Steps for Frontend Team

1. **Test All Endpoints** - Use the quick start commands above
2. **Implement Feed View** - Display synthesis articles with pagination
3. **Build Detail View** - Render full markdown content with timeline
4. **Add Filtering** - Filter by verdict type
5. **Style Verdict Badges** - Use the provided color codes
6. **Test Edge Cases** - Empty states, loading states, errors

---

## 📞 Support

**Questions?** Contact the backend team or file an issue in the GitHub repo.

**API Documentation:** http://localhost:8000/docs (Swagger UI)

**OpenAPI Spec:** http://localhost:8000/api/v1/openapi.json

---

## ✅ Status Updates

### November 21, 2025 - ALL SYSTEMS GO! 🚀

- ✅ Main synthesis endpoints operational
- ✅ Seed endpoints fully functional
- ✅ 10 test articles available
- ✅ All data structures complete
- ✅ Documentation updated

**Ready for frontend integration!**
