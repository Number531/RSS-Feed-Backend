# Frontend Integration Guide - Synthesis Mode & Fact-Checking

**Last Updated**: November 20, 2025  
**Backend Version**: Phase 4 Complete (Migration 2317b7aeeb89)  
**Target Audience**: Frontend Development Team

---

## Table of Contents

1. [Overview](#overview)
2. [Database Schema Changes](#database-schema-changes)
3. [Fact-Check Process Flow](#fact-check-process-flow)
4. [API Endpoint Recommendations](#api-endpoint-recommendations)
5. [Data Structures](#data-structures)
6. [Query Examples](#query-examples)
7. [UI/UX Guidelines](#uiux-guidelines)
8. [Performance Optimization](#performance-optimization)

---

## Overview

### What Changed?

We've added **synthesis mode fact-checking** to the RSS Feed platform. This creates **full journalistic articles** (1,400-2,500 words) with embedded fact-checking, replacing the simple bullet-point reports.

### Key Features:
- ✅ **Full narrative articles** instead of bullet points
- ✅ **Embedded citations** throughout the text
- ✅ **Margin notes** for additional context
- ✅ **Event timelines** when applicable
- ✅ **Context & emphasis** sections
- ✅ **95% smaller payloads** for list views
- ✅ **Sub-millisecond query performance**

---

## Database Schema Changes

### New Columns (13 total)

#### **Phase 2: Frontend Helper Columns** (Optimized for list views)

| Column | Type | Nullable | Description | Example |
|--------|------|----------|-------------|---------|
| `has_synthesis` | BOOLEAN | Yes | Quick filter: has synthesis article? | `true` |
| `synthesis_preview` | TEXT | Yes | First 500 characters of article | "# Trump Receives..." |
| `synthesis_word_count` | INTEGER | Yes | Total word count | `2027` |
| `has_context_emphasis` | BOOLEAN | Yes | Has context/emphasis section? | `true` |
| `has_timeline` | BOOLEAN | Yes | Has event timeline? | `true` |

#### **Phase 3: Metadata Enrichment** (Enhanced UX data)

| Column | Type | Nullable | Description | Example |
|--------|------|----------|-------------|---------|
| `timeline_event_count` | INTEGER | Yes | Number of timeline events | `5` |
| `reference_count` | INTEGER | Yes | Number of source references | `12` |
| `margin_note_count` | INTEGER | Yes | Number of margin notes | `8` |
| `fact_check_mode` | VARCHAR(20) | Yes | Mode: 'synthesis' or 'standard' | `'synthesis'` |
| `fact_check_processing_time` | INTEGER | Yes | Processing time (seconds) | `180` |
| `synthesis_generated_at` | TIMESTAMP | Yes | When synthesis was created | `2025-11-19 17:30:00` |

#### **Phase 4: UX Enhancements** (Display helpers)

| Column | Type | Nullable | Description | Example |
|--------|------|----------|-------------|---------|
| `synthesis_read_minutes` | INTEGER | Yes | Estimated read time (200 WPM) | `10` |
| `verdict_color` | VARCHAR(20) | Yes | UI color hint | `'green'` |

### Existing Columns (Still used)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `synthesis_article` | TEXT | Full markdown article (1,400-2,500 words) | "# Article Title\n\n..." |
| `article_data` | JSONB | Structured data (references, timeline, etc.) | `{ "references": [...] }` |
| `fact_check_score` | INTEGER | Credibility score (0-100) | `73` |
| `fact_check_verdict` | VARCHAR(50) | Final verdict | `'MOSTLY TRUE'` |
| `fact_checked_at` | TIMESTAMP | When fact-checked | `2025-11-19 17:30:00` |

---

## Fact-Check Process Flow

### Old Process (Standard Mode)
```
Article → Fact-Check API → Bullet Points Report → Display
                             (~5KB)
```

### New Process (Synthesis Mode)
```
Article → Fact-Check API (synthesis=true) → Full Article (10-17KB) → Display
                                                                  ↓
                                          article_data JSONB (2-5KB)
                                          + 13 computed columns
```

### Processing Steps:

1. **Initiation**: 
   ```python
   POST /api/v1/fact-check
   {
     "article_id": "uuid",
     "mode": "synthesis"  # NEW parameter
   }
   ```

2. **Background Processing** (180-900 seconds):
   - Article analysis & source verification
   - Narrative synthesis (1,400-2,500 words)
   - Citation embedding
   - Timeline construction (if applicable)
   - Margin note generation

3. **Database Storage**:
   - `synthesis_article` ← Full markdown text
   - `article_data` ← Structured JSON
   - All 13 helper columns auto-populated

4. **Polling**:
   ```python
   GET /api/v1/fact-check/{job_id}/status
   ```
   Poll every 5 seconds, max 180 attempts (15 minutes)

5. **Completion**:
   ```python
   GET /api/v1/articles/{article_id}
   # synthesis_article and helper columns now populated
   ```

---

## API Endpoint Recommendations

### ✅ **Recommended: New Endpoints**

Yes, create **new optimized endpoints** for synthesis mode to take advantage of the 95% payload reduction.

#### **1. List Synthesis Articles** (NEW - Recommended)
```http
GET /api/v1/articles/synthesis
```

**Purpose**: Fetch optimized list view data (95% smaller payloads)

**Query Parameters**:
```
?limit=20                    # Default: 20
&offset=0                    # Pagination
&verdict_color=green         # Filter by verdict: green, red, gray, orange, lime
&min_word_count=1500         # Minimum article length
&has_timeline=true           # Only articles with timelines
&sort=newest                 # newest, oldest, longest, shortest
```

**Response** (12KB for 20 articles vs 340KB before):
```json
{
  "articles": [
    {
      "id": "uuid",
      "title": "Article Title",
      "published_date": "2025-11-19T17:30:00Z",
      "synthesis_preview": "First 500 characters of article...",
      "synthesis_word_count": 2027,
      "synthesis_read_minutes": 10,
      "verdict_color": "green",
      "fact_check_verdict": "MOSTLY TRUE",
      "fact_check_score": 73,
      "has_context_emphasis": true,
      "has_timeline": true,
      "timeline_event_count": 5,
      "reference_count": 12,
      "margin_note_count": 8,
      "thumbnail_url": "https://...",
      "synthesis_generated_at": "2025-11-19T17:30:00Z"
    }
  ],
  "pagination": {
    "total": 100,
    "limit": 20,
    "offset": 0,
    "has_next": true
  }
}
```

**Implementation**:
```python
# app/api/v1/endpoints/articles.py

@router.get("/synthesis")
async def list_synthesis_articles(
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    verdict_color: Optional[str] = Query(None, regex="^(green|lime|yellow|orange|red|gray)$"),
    min_word_count: Optional[int] = Query(None, ge=0),
    has_timeline: Optional[bool] = None,
    sort: str = Query("newest", regex="^(newest|oldest|longest|shortest)$"),
    db: Session = Depends(get_db)
):
    """
    Get optimized list of synthesis articles.
    Uses helper columns for 95% payload reduction.
    """
    query = db.query(Article).filter(Article.has_synthesis == True)
    
    if verdict_color:
        query = query.filter(Article.verdict_color == verdict_color)
    if min_word_count:
        query = query.filter(Article.synthesis_word_count >= min_word_count)
    if has_timeline is not None:
        query = query.filter(Article.has_timeline == has_timeline)
    
    # Sorting
    if sort == "newest":
        query = query.order_by(Article.synthesis_generated_at.desc())
    elif sort == "oldest":
        query = query.order_by(Article.synthesis_generated_at.asc())
    elif sort == "longest":
        query = query.order_by(Article.synthesis_word_count.desc())
    elif sort == "shortest":
        query = query.order_by(Article.synthesis_word_count.asc())
    
    total = query.count()
    articles = query.offset(offset).limit(limit).all()
    
    return {
        "articles": [
            {
                "id": str(a.id),
                "title": a.title,
                "published_date": a.published_date,
                "synthesis_preview": a.synthesis_preview,
                "synthesis_word_count": a.synthesis_word_count,
                "synthesis_read_minutes": a.synthesis_read_minutes,
                "verdict_color": a.verdict_color,
                "fact_check_verdict": a.fact_check_verdict,
                "fact_check_score": a.fact_check_score,
                "has_context_emphasis": a.has_context_emphasis,
                "has_timeline": a.has_timeline,
                "timeline_event_count": a.timeline_event_count,
                "reference_count": a.reference_count,
                "margin_note_count": a.margin_note_count,
                "thumbnail_url": a.thumbnail_url,
                "synthesis_generated_at": a.synthesis_generated_at
            }
            for a in articles
        ],
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total
        }
    }
```

---

#### **2. Get Full Synthesis Article** (NEW - Recommended)
```http
GET /api/v1/articles/{article_id}/synthesis
```

**Purpose**: Fetch complete synthesis article with all data

**Response** (10-17KB for full article):
```json
{
  "article": {
    "id": "uuid",
    "title": "Article Title",
    "published_date": "2025-11-19T17:30:00Z",
    
    // Full Content
    "synthesis_article": "# Full markdown article (1,400-2,500 words)...",
    
    // Metadata
    "synthesis_word_count": 2027,
    "synthesis_read_minutes": 10,
    "fact_check_verdict": "MOSTLY TRUE",
    "fact_check_score": 73,
    "verdict_color": "green",
    "synthesis_generated_at": "2025-11-19T17:30:00Z",
    
    // Structured Data
    "references": [
      {
        "id": 1,
        "title": "Source title",
        "url": "https://...",
        "publication": "CNN",
        "date": "2025-11-19",
        "credibility_score": 85
      }
    ],
    "margin_notes": [
      {
        "id": 1,
        "paragraph_index": 3,
        "text": "Additional context about this claim",
        "type": "context"
      }
    ],
    "event_timeline": [
      {
        "date": "2025-11-15",
        "time": "14:30",
        "event": "Event description",
        "source_id": 1
      }
    ],
    "context_and_emphasis": {
      "key_context": "Important background information",
      "why_this_matters": "Significance of this story"
    },
    
    // Counts
    "reference_count": 12,
    "margin_note_count": 8,
    "timeline_event_count": 5
  }
}
```

**Implementation**:
```python
@router.get("/{article_id}/synthesis")
async def get_synthesis_article(
    article_id: str,
    db: Session = Depends(get_db)
):
    """
    Get full synthesis article with all structured data.
    """
    article = db.query(Article).filter(Article.id == article_id).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if not article.has_synthesis:
        raise HTTPException(
            status_code=404, 
            detail="Synthesis article not available for this article"
        )
    
    # Extract structured data from article_data JSONB
    article_data = article.article_data or {}
    
    return {
        "article": {
            "id": str(article.id),
            "title": article.title,
            "published_date": article.published_date,
            "synthesis_article": article.synthesis_article,
            "synthesis_word_count": article.synthesis_word_count,
            "synthesis_read_minutes": article.synthesis_read_minutes,
            "fact_check_verdict": article.fact_check_verdict,
            "fact_check_score": article.fact_check_score,
            "verdict_color": article.verdict_color,
            "synthesis_generated_at": article.synthesis_generated_at,
            "references": article_data.get("references", []),
            "margin_notes": article_data.get("margin_notes", []),
            "event_timeline": article_data.get("event_timeline", []),
            "context_and_emphasis": article_data.get("context_and_emphasis", {}),
            "reference_count": article.reference_count,
            "margin_note_count": article.margin_note_count,
            "timeline_event_count": article.timeline_event_count
        }
    }
```

---

#### **3. Get Synthesis Stats** (NEW - Optional)
```http
GET /api/v1/articles/synthesis/stats
```

**Purpose**: Dashboard statistics

**Response**:
```json
{
  "total_synthesis_articles": 150,
  "verdicts": {
    "green": 45,
    "lime": 30,
    "yellow": 20,
    "orange": 25,
    "red": 15,
    "gray": 15
  },
  "average_word_count": 2027,
  "average_read_minutes": 10,
  "average_credibility_score": 68,
  "articles_with_timelines": 75,
  "articles_with_context": 140
}
```

---

#### **4. Initiate Fact-Check (UPDATED)**
```http
POST /api/v1/fact-check
```

**Request**:
```json
{
  "article_id": "uuid",
  "mode": "synthesis"  // NEW: "synthesis" or "standard" (default)
}
```

**Response**:
```json
{
  "job_id": "fact-check-uuid",
  "status": "processing",
  "mode": "synthesis",
  "estimated_time_seconds": 600,
  "poll_interval_seconds": 5
}
```

---

#### **5. Check Fact-Check Status (EXISTING - No changes needed)**
```http
GET /api/v1/fact-check/{job_id}/status
```

**Response**:
```json
{
  "job_id": "fact-check-uuid",
  "status": "completed",  // processing, completed, failed
  "mode": "synthesis",
  "article_id": "uuid",
  "progress_percentage": 100,
  "result": {
    "verdict": "MOSTLY TRUE",
    "score": 73,
    "synthesis_word_count": 2027
  }
}
```

---

### ❌ **Not Recommended: Modifying Existing Endpoints**

**Why?**  
Existing endpoints return full `Article` objects (17KB each). Adding synthesis data would make them even larger. Keep them for backward compatibility.

**Existing endpoints to keep as-is**:
- `GET /api/v1/articles` - Standard article list
- `GET /api/v1/articles/{id}` - Full article details

---

## Data Structures

### Verdict Color Mapping

| Verdict | Color | Hex Code | Usage |
|---------|-------|----------|-------|
| `TRUE` | `green` | `#10b981` | High credibility, verified claims |
| `MOSTLY TRUE` | `lime` | `#84cc16` | Largely accurate, minor issues |
| `MIXED` | `yellow` | `#eab308` | Some true, some false |
| `MOSTLY FALSE` | `orange` | `#f97316` | Largely inaccurate |
| `FALSE` | `red` | `#ef4444` | Debunked, fabricated |
| `UNVERIFIED` | `gray` | `#6b7280` | Insufficient evidence |

### article_data JSONB Structure

```typescript
interface ArticleData {
  references: Reference[];
  margin_notes: MarginNote[];
  event_timeline?: TimelineEvent[];
  context_and_emphasis?: {
    key_context: string;
    why_this_matters: string;
  };
  article_sections?: Section[];
  generation_metadata: {
    generated_at: string;
    processing_time_seconds: number;
    model: string;
    version: string;
  };
}

interface Reference {
  id: number;
  title: string;
  url: string;
  publication: string;
  date: string;
  credibility_score: number;
  quote?: string;
}

interface MarginNote {
  id: number;
  paragraph_index: number;
  text: string;
  type: "context" | "clarification" | "source" | "warning";
}

interface TimelineEvent {
  date: string;
  time?: string;
  event: string;
  source_id: number;
}

interface Section {
  title: string;
  content: string;
  level: number;  // H1, H2, H3
}
```

---

## Query Examples

### Frontend Use Cases

#### **1. Homepage Feed (Latest Synthesis Articles)**
```sql
SELECT 
    id, title, published_date, synthesis_preview,
    synthesis_read_minutes, verdict_color, 
    fact_check_score, thumbnail_url
FROM articles
WHERE has_synthesis = true
ORDER BY synthesis_generated_at DESC
LIMIT 20;
```

**API Call**:
```javascript
const response = await fetch('/api/v1/articles/synthesis?limit=20&sort=newest');
```

---

#### **2. Filter by Verdict (Show only verified articles)**
```sql
SELECT ...
FROM articles
WHERE has_synthesis = true
  AND verdict_color IN ('green', 'lime')
ORDER BY fact_check_score DESC
LIMIT 20;
```

**API Call**:
```javascript
const response = await fetch('/api/v1/articles/synthesis?verdict_color=green&limit=20');
```

---

#### **3. Long-Read Articles (> 2000 words)**
```sql
SELECT ...
FROM articles
WHERE has_synthesis = true
  AND synthesis_word_count >= 2000
ORDER BY synthesis_word_count DESC;
```

**API Call**:
```javascript
const response = await fetch('/api/v1/articles/synthesis?min_word_count=2000&sort=longest');
```

---

#### **4. Articles with Timelines**
```sql
SELECT ...
FROM articles
WHERE has_synthesis = true
  AND has_timeline = true
ORDER BY timeline_event_count DESC;
```

**API Call**:
```javascript
const response = await fetch('/api/v1/articles/synthesis?has_timeline=true');
```

---

#### **5. Search Preview Text**
```sql
SELECT ...
FROM articles
WHERE has_synthesis = true
  AND synthesis_preview ILIKE '%keyword%'
ORDER BY fact_check_score DESC;
```

**Note**: Uses `idx_articles_synthesis_preview_fts` (GIN index with pg_trgm) for fast fuzzy search.

---

## UI/UX Guidelines

### List View Display

```jsx
<ArticleCard>
  <Badge color={article.verdict_color}>
    {article.fact_check_verdict}
  </Badge>
  
  <Title>{article.title}</Title>
  
  <Preview>{article.synthesis_preview}</Preview>
  
  <Metadata>
    <ReadTime>{article.synthesis_read_minutes} min read</ReadTime>
    <Score>{article.fact_check_score}/100</Score>
    
    {article.has_timeline && <Badge>Timeline</Badge>}
    {article.has_context_emphasis && <Badge>Context</Badge>}
    
    <Sources>{article.reference_count} sources</Sources>
  </Metadata>
</ArticleCard>
```

---

### Detail View Display

```jsx
<ArticleDetail>
  {/* Header */}
  <Header>
    <Title>{article.title}</Title>
    <VerdictBadge 
      color={article.verdict_color}
      score={article.fact_check_score}
    >
      {article.fact_check_verdict}
    </VerdictBadge>
  </Header>
  
  {/* Metadata */}
  <Metadata>
    <PublishDate>{article.published_date}</PublishDate>
    <ReadTime>{article.synthesis_read_minutes} min read</ReadTime>
    <WordCount>{article.synthesis_word_count} words</WordCount>
  </Metadata>
  
  {/* Main Content */}
  <MarkdownRenderer content={article.synthesis_article} />
  
  {/* Sidebar */}
  <Sidebar>
    {/* References */}
    <Section title="Sources">
      {article.references.map(ref => (
        <Reference key={ref.id}>
          <Link href={ref.url}>{ref.title}</Link>
          <Publisher>{ref.publication}</Publisher>
          <Credibility score={ref.credibility_score} />
        </Reference>
      ))}
    </Section>
    
    {/* Timeline (if available) */}
    {article.has_timeline && (
      <Section title="Timeline">
        {article.event_timeline.map(event => (
          <TimelineEvent key={event.date}>
            <Date>{event.date}</Date>
            <Description>{event.event}</Description>
          </TimelineEvent>
        ))}
      </Section>
    )}
    
    {/* Context */}
    {article.has_context_emphasis && (
      <Section title="Why This Matters">
        <p>{article.context_and_emphasis.why_this_matters}</p>
      </Section>
    )}
  </Sidebar>
  
  {/* Margin Notes (inline with paragraphs) */}
  {article.margin_notes.map(note => (
    <MarginNote 
      key={note.id}
      paragraphIndex={note.paragraph_index}
      type={note.type}
    >
      {note.text}
    </MarginNote>
  ))}
</ArticleDetail>
```

---

## Performance Optimization

### Best Practices

#### **1. Use List Endpoint for All List Views**
✅ **DO**: 
```javascript
fetch('/api/v1/articles/synthesis?limit=20')  // 12KB
```

❌ **DON'T**: 
```javascript
fetch('/api/v1/articles?limit=20')  // 340KB
```

**Savings**: 95% reduction (340KB → 12KB)

---

#### **2. Paginate Large Lists**
```javascript
// Load 20 at a time
const [offset, setOffset] = useState(0);
const limit = 20;

fetch(`/api/v1/articles/synthesis?limit=${limit}&offset=${offset}`)
```

---

#### **3. Cache Article Details**
```javascript
// Use React Query or SWR
const { data } = useQuery(['article', id], () =>
  fetch(`/api/v1/articles/${id}/synthesis`).then(r => r.json()),
  { staleTime: 5 * 60 * 1000 }  // Cache for 5 minutes
);
```

---

#### **4. Lazy Load Sidebar Content**
```javascript
// Load references/timeline only when user scrolls to sidebar
const { data: references } = useQuery(
  ['references', articleId],
  () => fetch(`/api/v1/articles/${articleId}/references`).then(r => r.json()),
  { enabled: sidebarVisible }
);
```

---

#### **5. Use Filters Efficiently**
```javascript
// Filter on backend (uses indexes)
fetch('/api/v1/articles/synthesis?verdict_color=green')  // ✅ Fast

// Don't filter on frontend
fetch('/api/v1/articles/synthesis')
  .then(articles => articles.filter(a => a.verdict_color === 'green'))  // ❌ Slow
```

---

## Migration Checklist for Frontend

### Phase 1: Read-Only Integration (Week 1)
- [ ] Create new API endpoints (list, detail, stats)
- [ ] Build synthesis article list component
- [ ] Build synthesis article detail component
- [ ] Implement verdict color badges
- [ ] Add read time display
- [ ] Test with existing 10 synthesis articles

### Phase 2: Filtering & Search (Week 2)
- [ ] Add verdict filters (green/red/gray/etc.)
- [ ] Add word count filters
- [ ] Add timeline filter
- [ ] Implement preview text search
- [ ] Add sorting options (newest, longest, etc.)

### Phase 3: Enhanced UX (Week 3)
- [ ] Display margin notes inline
- [ ] Render event timelines
- [ ] Show reference citations
- [ ] Add context/emphasis sections
- [ ] Implement source credibility scores

### Phase 4: Fact-Check Initiation (Week 4)
- [ ] Build fact-check request UI
- [ ] Implement polling for job status
- [ ] Show progress indicators
- [ ] Handle errors gracefully
- [ ] Add "Re-fact-check" button

---

## Testing Endpoints

### Development URLs
```bash
# List synthesis articles
curl http://localhost:8000/api/v1/articles/synthesis?limit=5

# Get full article
curl http://localhost:8000/api/v1/articles/{article_id}/synthesis

# Initiate fact-check
curl -X POST http://localhost:8000/api/v1/fact-check \
  -H "Content-Type: application/json" \
  -d '{"article_id": "uuid", "mode": "synthesis"}'

# Check status
curl http://localhost:8000/api/v1/fact-check/{job_id}/status
```

---

## FAQ

### Q: Should we use synthesis mode for all articles?
**A**: No. Synthesis mode takes 3-15 minutes and costs more. Use it for:
- Featured/important articles
- User-requested fact-checks
- Articles flagged for deep analysis

Use standard mode (bullet points) for:
- Quick fact-checks
- Automated fact-checks on all new articles
- Lower-priority content

### Q: Can users switch between standard and synthesis modes?
**A**: Yes! An article can have both:
- `fact_check_mode = 'standard'` → Bullet points (fast, cheap)
- `fact_check_mode = 'synthesis'` → Full article (slow, expensive)

Show a "Get detailed analysis" button to generate synthesis version on demand.

### Q: How do we handle fact-check failures?
**A**: Check `status` field in polling response:
- `processing` → Show loading spinner
- `completed` → Redirect to article
- `failed` → Show error message, offer retry

### Q: Can we cache synthesis articles?
**A**: Yes! Cache aggressively:
- List view: Cache for 5-10 minutes
- Detail view: Cache for 1 hour
- Update cache when fact-check completes

### Q: What if synthesis_article is NULL?
**A**: Check `has_synthesis` column first:
```javascript
if (article.has_synthesis) {
  // Show synthesis UI
} else {
  // Show "Fact-check not available" or "Generate fact-check" button
}
```

---

## Support

### Backend Team Contacts
- **Architecture questions**: [Backend Lead]
- **API issues**: [API Team]
- **Database queries**: [DBA Team]

### Documentation
- API Spec: `/docs` (Swagger UI)
- Database Schema: `PHASE2_3_4_MIGRATION_COMPLETE.md`
- Fact-Check Guide: `SYNTHESIS_MODE_API_GUIDE.md`

### Sample Data
- 10 synthesis articles available in database
- Test with article IDs in `SYNTHESIS_MODE_TEST_RESULTS.md`

---

## Appendix: Complete TypeScript Interfaces

```typescript
// List View Response
interface SynthesisListResponse {
  articles: SynthesisListItem[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
    has_next: boolean;
  };
}

interface SynthesisListItem {
  id: string;
  title: string;
  published_date: string;
  synthesis_preview: string;
  synthesis_word_count: number;
  synthesis_read_minutes: number;
  verdict_color: 'green' | 'lime' | 'yellow' | 'orange' | 'red' | 'gray';
  fact_check_verdict: string;
  fact_check_score: number;
  has_context_emphasis: boolean;
  has_timeline: boolean;
  timeline_event_count: number;
  reference_count: number;
  margin_note_count: number;
  thumbnail_url: string | null;
  synthesis_generated_at: string;
}

// Detail View Response
interface SynthesisDetailResponse {
  article: {
    id: string;
    title: string;
    published_date: string;
    synthesis_article: string;  // Markdown
    synthesis_word_count: number;
    synthesis_read_minutes: number;
    fact_check_verdict: string;
    fact_check_score: number;
    verdict_color: string;
    synthesis_generated_at: string;
    references: Reference[];
    margin_notes: MarginNote[];
    event_timeline: TimelineEvent[];
    context_and_emphasis: {
      key_context: string;
      why_this_matters: string;
    };
    reference_count: number;
    margin_note_count: number;
    timeline_event_count: number;
  };
}

interface Reference {
  id: number;
  title: string;
  url: string;
  publication: string;
  date: string;
  credibility_score: number;
  quote?: string;
}

interface MarginNote {
  id: number;
  paragraph_index: number;
  text: string;
  type: 'context' | 'clarification' | 'source' | 'warning';
}

interface TimelineEvent {
  date: string;
  time?: string;
  event: string;
  source_id: number;
}

// Fact-Check Request
interface FactCheckRequest {
  article_id: string;
  mode: 'synthesis' | 'standard';
}

interface FactCheckResponse {
  job_id: string;
  status: 'processing' | 'completed' | 'failed';
  mode: string;
  estimated_time_seconds: number;
  poll_interval_seconds: number;
}

interface FactCheckStatusResponse {
  job_id: string;
  status: 'processing' | 'completed' | 'failed';
  mode: string;
  article_id: string;
  progress_percentage: number;
  result?: {
    verdict: string;
    score: number;
    synthesis_word_count: number;
  };
  error?: string;
}
```

---

**End of Frontend Integration Guide**

For questions or clarifications, please contact the backend team or refer to the linked documentation files.
