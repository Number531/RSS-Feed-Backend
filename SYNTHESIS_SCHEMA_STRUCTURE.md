# Synthesis Endpoints Schema Structure

## Database Schema (Actual)

### Article Model Fields
```python
# Primary Key
id: UUID  # Not integer!

# Core Fields  
title: Text
url: Text
published_date: DateTime  # Not published_at!
author: String(255)
source_name: N/A  # Comes from rss_source relationship
category: String(50)

# Synthesis Content
synthesis_article: Text  # Full markdown (1,400-2,500 words)
article_data: JSONB  # Structured data with references, timeline, etc.

# Fact Check Fields (existing)
fact_check_score: Integer  # Not confidence_score!
fact_check_verdict: String(50)  # Not verdict!
fact_checked_at: DateTime

# Phase 2: Helper Columns
has_synthesis: Boolean
synthesis_preview: Text
synthesis_word_count: Integer
has_context_emphasis: Boolean
has_timeline: Boolean

# Phase 3: Metadata Enrichment
timeline_event_count: Integer
reference_count: Integer
margin_note_count: Integer
fact_check_mode: String(20)  # 'synthesis', 'standard', or NULL
fact_check_processing_time: Integer  # seconds
synthesis_generated_at: DateTime

# Phase 4: UX Enhancements
synthesis_read_minutes: Integer
verdict_color: String(20)  # 'green', 'lime', 'yellow', 'orange', 'red', 'gray'
```

### JSONB Structure (article_data)
```json
{
  "references": [
    {
      "citation_number": 1,
      "full_citation": "...",
      "url": "...",
      "credibility_rating": "HIGH|MEDIUM|LOW"
    }
  ],
  "event_timeline": [
    {
      "date": "2025-01-01",
      "event": "..."
    }
  ],
  "margin_notes": [
    {
      "note_text": "...",
      "position": "..."
    }
  ],
  "context_and_emphasis": [
    {
      "context_item": "...",
      "impact": "..."
    }
  ],
  "generation_metadata": {
    "generated_at": "ISO timestamp",
    "processing_time_seconds": 45.2
  }
}
```

## Endpoint Requirements

### GET /api/v1/articles/synthesis

**Query Parameters:**
- `page`: int (default: 1)
- `page_size`: int (default: 20, max: 100)
- `verdict`: Optional[str] (filter by fact_check_verdict)
- `sort_by`: str (default: "newest")

**Response:**
```json
{
  "items": [
    {
      "id": "uuid-string",
      "title": "...",
      "synthesis_preview": "...",
      "fact_check_verdict": "TRUE|MOSTLY TRUE|MIXED|...",
      "verdict_color": "green|lime|yellow|...",
      "fact_check_score": 85,
      "synthesis_read_minutes": 2,
      "published_date": "ISO datetime",
      "source_name": "from rss_source.name",
      "category": "...",
      "has_timeline": true,
      "has_context_emphasis": false
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "has_next": true
}
```

### GET /api/v1/articles/{article_id}/synthesis

**Response:**
```json
{
  "article": {
    "id": "uuid-string",
    "title": "...",
    "content": "original article content",
    "synthesis_article": "full markdown synthesis",
    "fact_check_verdict": "...",
    "verdict_color": "...",
    "fact_check_score": 85,
    "synthesis_word_count": 2000,
    "synthesis_read_minutes": 10,
    "published_date": "ISO datetime",
    "author": "...",
    "source_name": "from rss_source.name",
    "category": "...",
    "url": "...",
    "has_timeline": true,
    "has_context_emphasis": true,
    "timeline_event_count": 5,
    "reference_count": 10,
    "margin_note_count": 3,
    "fact_check_mode": "synthesis",
    "fact_check_processing_time": 45,
    "synthesis_generated_at": "ISO datetime",
    "references": [...],  // from article_data JSONB
    "event_timeline": [...],  // from article_data JSONB
    "margin_notes": [...],  // from article_data JSONB
    "context_and_emphasis": [...]  // from article_data JSONB
  }
}
```

### GET /api/v1/articles/synthesis/stats

**Response:**
```json
{
  "total_synthesis_articles": 150,
  "articles_with_timeline": 80,
  "articles_with_context": 45,
  "average_credibility": 0.78,
  "verdict_distribution": {
    "TRUE": 30,
    "MOSTLY TRUE": 60,
    "MIXED": 40,
    "MOSTLY FALSE": 20,
    "FALSE": 10
  },
  "average_word_count": 245,
  "average_read_minutes": 2
}
```

## Key Changes Needed

1. **ID Type**: Change from `int` to `str` (UUID)
2. **Field Names**:
   - `verdict` → `fact_check_verdict`
   - `verdict_color` → keep as is
   - `confidence_score` → `fact_check_score`
   - `published_at` → `published_date`
   - `synthesis_text` → `synthesis_article`
3. **Add JSONB Arrays**:
   - Extract `references`, `event_timeline`, `margin_notes`, `context_and_emphasis` from `article_data`
4. **Source Name**: Join with `rss_source` table to get `name`
5. **Response Structure**: Match existing API patterns
