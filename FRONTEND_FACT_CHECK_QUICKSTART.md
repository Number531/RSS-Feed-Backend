# Fact-Check Frontend Quick Start

**TL;DR for frontend developers - Get started in 5 minutes**

---

## What You Need to Know

Your RSS Feed backend now includes **AI-powered fact-checking** for all articles. Every article is automatically fact-checked using a microservice that:

✅ Verifies claims against **25+ sources**  
✅ Detects **misinformation and fabricated quotes**  
✅ Assigns **credibility scores (0-100)**  
✅ Provides **detailed evidence and references**  
✅ Takes **~60-120 seconds** per article  

---

## Real Example: Detecting Misinformation

### Source Article
**URL**: `https://www.foxnews.com/media/kamala-harris-says-its-f-up-what-rfk-jrs-hhs-doing-america`

**Claim**: Article reports Kamala Harris condemned HHS under RFK Jr. as "f----- up" and "criminal" in a podcast interview.

### Fact-Check Result

```json
{
  "verdict": "FALSE - MISINFORMATION",
  "confidence": 1.0,  // 100% confidence
  "credibility_score": 0,  // 0/100 - Complete misinformation
  "num_sources": 25,
  "processing_time_seconds": 128
}
```

### Key Findings

❌ **FABRICATED** - No evidence Harris made these statements  
❌ **FALSE ATTRIBUTION** - Quotes are invented  
⚠️ **HIGH SPREAD RISK** - Designed to mislead voters  

### Evidence

**Contradicting Evidence (9 sources)**:
- Extensive search of public records found no such interview
- No major news outlet reported these remarks
- Specific quotes ('f----- up', 'criminal') not found anywhere
- Context and event details are fabricated

**Source Analysis**:
- **Consensus**: STRONG_DISAGREEMENT (all sources contradict claim)
- **Evidence Quality**: HIGH
- **Most Credible Sources**: AP News, BMJ, Reuters, CFR

### What Frontend Shows

```tsx
<ArticleCard>
  <CredibilityBadge 
    score={0}           // 0/100
    verdict="FALSE - MISINFORMATION"
    color="red"
    icon="✗"
  />
  <Warning severity="high">
    ⚠️ MISINFORMATION DETECTED
  </Warning>
</ArticleCard>
```

---

## Quick Integration (3 Steps)

### 1. Articles Already Include Fact-Check Data

```typescript
// GET /api/v1/articles
{
  "articles": [
    {
      "id": "...",
      "title": "Article Title",
      "url": "...",
      
      // NEW: Fact-check fields (denormalized for performance)
      "fact_check_score": 87,        // ← 0-100 credibility score
      "fact_check_verdict": "TRUE",  // ← Verdict
      "fact_checked_at": "2025-10-18T12:07:00Z"
    }
  ]
}
```

**No changes needed to your API calls** - fact-check fields are already included!

### 2. Display Credibility Badge

```tsx
export function ArticleCard({ article }) {
  const getCredibilityDisplay = (score) => {
    if (score === null) return { color: 'gray', icon: '⏳', text: 'Checking...' };
    if (score >= 80) return { color: 'green', icon: '✓', text: 'High Credibility' };
    if (score >= 60) return { color: 'yellow', icon: '⚠', text: 'Medium' };
    if (score >= 40) return { color: 'orange', icon: '⚠', text: 'Low' };
    return { color: 'red', icon: '✗', text: 'Very Low/Misinformation' };
  };
  
  const display = getCredibilityDisplay(article.fact_check_score);
  
  return (
    <div className="article-card">
      <h2>{article.title}</h2>
      
      {/* Credibility Badge */}
      <div className={`badge ${display.color}`}>
        <span>{display.icon}</span>
        <span>{article.fact_check_score ?? '?'}/100</span>
        <span>{display.text}</span>
      </div>
      
      {/* High-Risk Warning */}
      {article.fact_check_score < 40 && (
        <div className="warning">
          ⚠️ {article.fact_check_verdict}
        </div>
      )}
    </div>
  );
}
```

### 3. Add Filters

```tsx
// Filter by credibility
const highCredibility = articles.filter(a => a.fact_check_score >= 80);
const suspicious = articles.filter(a => a.fact_check_score < 40);
const misinformation = articles.filter(a => 
  a.fact_check_verdict?.includes('MISINFORMATION')
);
```

---

## Complete Fact-Check Response Structure

### Summary Data (Always Available)

```typescript
{
  "job_id": "ed66d9a2-a34c-40ea-9e97-f784195e2da2",
  "source_url": "https://...",
  "processing_time_seconds": 128.28,
  
  // Quick summary
  "summary": "Analyzed 1 claims: 1 UNKNOWN",
  "claims_analyzed": 1,
  "claims_validated": 1
}
```

### Validation Results (Detailed)

```typescript
"validation_results": [
  {
    "claim": "Full claim text...",
    "verdict": "FALSE - MISINFORMATION",
    "confidence": 1.0,
    "summary": "The claim is false because...",
    
    // Evidence
    "key_evidence": {
      "supporting": [],  // Empty for false claims
      "contradicting": [
        "Extensive review found no evidence...",
        "No major news outlet reported...",
        "Specific quotes not found anywhere..."
      ],
      "context": [...]
    },
    
    // Source analysis
    "source_analysis": {
      "source_consensus": "STRONG_DISAGREEMENT",
      "evidence_quality": "HIGH",
      "most_credible_sources": [1, 2, 3]
    },
    
    // References (25 sources)
    "references": [
      {
        "citation_id": 1,
        "title": "Hillary Clinton slams RFK Jr...",
        "url": "https://apnews.com/...",
        "source": "AP News",
        "date": "2025-09-24",
        "credibility": "HIGH"
      }
      // ... 24 more
    ],
    
    // Metrics
    "num_sources": 25,
    "search_breakdown": {
      "news": 5,
      "research": 10,
      "general": 5,
      "historical": 5
    },
    
    // Misinformation indicators
    "metadata": {
      "misinformation_indicators": [
        "FABRICATED",
        "FALSE_ATTRIBUTION",
        "OUT_OF_CONTEXT"
      ],
      "spread_risk": "HIGH"
    }
  }
]
```

### Generated Article (For Detailed View)

```typescript
"article_data": {
  "article_metadata": {
    "headline": "Fact Check: Harris's Alleged Condemnation...",
    "urgency_level": "HIGH",
    "public_impact_score": 8,
    "reading_time_minutes": 6
  },
  
  "executive_summary": {
    "claims_checked": 1,
    "verdicts_summary": {
      "misinformation": 1,
      "true": 0,
      "false": 0
    },
    "key_findings": [
      "Former VP did not make alleged statements",
      "Specific quotes are fabricated",
      "No evidence links Harris to remarks"
    ],
    "bottom_line": "Claims are false and constitute misinformation"
  },
  
  "references": [...]  // Full citation list
}
```

---

## UI Component Examples

### 1. Credibility Badge (Compact)

```tsx
<span className={`badge badge-${getColorClass(score)}`}>
  {getVerdictIcon(verdict)} {score}/100
</span>
```

**Color Classes**:
- `badge-green` - 80-100 (High credibility)
- `badge-yellow` - 60-79 (Medium)
- `badge-orange` - 40-59 (Low)
- `badge-red` - 0-39 (Very low/misinformation)
- `badge-gray` - null (Pending)

### 2. Warning Banner (For Low Scores)

```tsx
{article.fact_check_score < 40 && (
  <div className="alert alert-danger">
    <strong>⚠️ MISINFORMATION DETECTED</strong>
    <p>{article.fact_check_verdict}</p>
    <button onClick={() => showFullReport(article.id)}>
      View Fact-Check Report
    </button>
  </div>
)}
```

### 3. Filter Dropdown

```tsx
<select onChange={(e) => setCredibilityFilter(e.target.value)}>
  <option value="all">All Articles</option>
  <option value="high">✓ High Credibility (80+)</option>
  <option value="medium">⚠ Medium Credibility (60-79)</option>
  <option value="low">⚠ Low Credibility (40-59)</option>
  <option value="misinformation">✗ Misinformation (<40)</option>
  <option value="pending">⏳ Pending Fact-Check</option>
</select>
```

### 4. Detailed Fact-Check Modal

```tsx
function FactCheckModal({ result }) {
  const validation = result.validation_results[0];
  
  return (
    <Modal>
      <ModalHeader>
        <h2>Fact-Check Report</h2>
        <Badge 
          variant={validation.verdict.includes('MISINFORMATION') ? 'danger' : 'warning'}
        >
          {validation.verdict}
        </Badge>
      </ModalHeader>
      
      <ModalBody>
        {/* Summary */}
        <section>
          <h3>Summary</h3>
          <p>{validation.summary}</p>
          <div className="metrics">
            <Metric label="Confidence" value={`${(validation.confidence * 100)}%`} />
            <Metric label="Sources" value={validation.num_sources} />
            <Metric label="Consensus" value={validation.source_analysis.source_consensus} />
          </div>
        </section>
        
        {/* Evidence */}
        <section>
          <h3>Contradicting Evidence</h3>
          <ul>
            {validation.key_evidence.contradicting.map((evidence, i) => (
              <li key={i}>{evidence}</li>
            ))}
          </ul>
        </section>
        
        {/* Misinformation Indicators */}
        {validation.metadata.misinformation_indicators && (
          <section className="alert alert-warning">
            <h3>⚠️ Misinformation Indicators</h3>
            <ul>
              {validation.metadata.misinformation_indicators.map(indicator => (
                <li key={indicator}>
                  <strong>{indicator.replace('_', ' ')}</strong>
                </li>
              ))}
            </ul>
            <p>Spread Risk: <strong>{validation.metadata.spread_risk}</strong></p>
          </section>
        )}
        
        {/* Sources */}
        <section>
          <h3>References ({validation.num_sources} sources)</h3>
          <ul className="references">
            {validation.references.slice(0, 5).map(ref => (
              <li key={ref.citation_id}>
                <a href={ref.url} target="_blank" rel="noopener">
                  [{ref.citation_id}] {ref.title}
                </a>
                <div className="source-meta">
                  {ref.source} • {ref.date} • {ref.credibility}
                </div>
              </li>
            ))}
          </ul>
        </section>
      </ModalBody>
    </Modal>
  );
}
```

---

## TypeScript Interfaces

```typescript
// Article with fact-check fields
export interface Article {
  id: string;
  title: string;
  url: string;
  description: string;
  
  // Fact-check fields (denormalized)
  fact_check_score: number | null;      // 0-100
  fact_check_verdict: string | null;    // "TRUE", "FALSE - MISINFORMATION", etc.
  fact_checked_at: string | null;
}

// Full fact-check result (from Railway API)
export interface FactCheckResult {
  job_id: string;
  source_url: string;
  processing_time_seconds: number;
  
  summary: string;
  claims_analyzed: number;
  
  validation_results: ValidationResult[];
  article_data: ArticleData;
}

export interface ValidationResult {
  claim: string;
  verdict: string;
  confidence: number;
  summary: string;
  num_sources: number;
  
  key_evidence: {
    supporting: string[];
    contradicting: string[];
    context: string[];
  };
  
  source_analysis: {
    source_consensus: string;
    evidence_quality: 'HIGH' | 'MEDIUM' | 'LOW';
  };
  
  references: Reference[];
  
  metadata?: {
    misinformation_indicators?: string[];
    spread_risk?: 'HIGH' | 'MEDIUM' | 'LOW';
  };
}

export interface Reference {
  citation_id: number;
  title: string;
  url: string;
  source: string;
  date: string;
  credibility: 'HIGH' | 'MEDIUM' | 'LOW';
}
```

---

## Testing Your Integration

### 1. Check Backend Health

```bash
curl https://fact-check-production.up.railway.app/health
```

Expected:
```json
{
  "status": "healthy",
  "services": { "redis": "healthy", "queue": "healthy" }
}
```

### 2. Get Articles with Fact-Check Data

```bash
curl http://localhost:8000/api/v1/articles?page=1&page_size=10
```

Look for:
```json
{
  "articles": [
    {
      "fact_check_score": 87,
      "fact_check_verdict": "TRUE",
      "fact_checked_at": "2025-10-18T12:07:00Z"
    }
  ]
}
```

### 3. Manual Fact-Check (Optional)

```bash
curl -X POST https://fact-check-production.up.railway.app/fact-check/submit \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.bbc.com/news/article",
    "mode": "summary",
    "generate_image": false,
    "generate_article": true
  }'
```

Returns `job_id` → Check status → Get result

---

## Credibility Score Breakdown

| Score Range | Color | Icon | Meaning | Action |
|-------------|-------|------|---------|--------|
| **80-100** | 🟢 Green | ✓ | High credibility, well-verified | Show normally |
| **60-79** | 🟡 Yellow | ⚠ | Medium credibility, some concerns | Show with note |
| **40-59** | 🟠 Orange | ⚠ | Low credibility, significant issues | Show warning |
| **0-39** | 🔴 Red | ✗ | Very low/misinformation | Strong warning |
| **null** | ⚪ Gray | ⏳ | Pending fact-check | "Checking..." |

---

## Verdict Types

| Verdict | Description | UI Treatment |
|---------|-------------|--------------|
| `TRUE` | Claims verified as accurate | Green badge, checkmark |
| `MOSTLY_TRUE` | Mostly accurate with minor issues | Green/yellow |
| `PARTIALLY_TRUE` | Mix of true and false | Yellow |
| `MISLEADING` | Technically true but misleading context | Orange warning |
| `FALSE` | Claims are incorrect | Red badge |
| `FALSE - MISINFORMATION` | Deliberately false, designed to deceive | **Red alert banner** |
| `UNVERIFIED` | Cannot verify claims | Gray, neutral |

---

## Best Practices

### 1. **Always Handle Null Values**

```typescript
// ✅ Good
const display = article.fact_check_score !== null 
  ? `${article.fact_check_score}/100`
  : 'Pending fact-check';

// ❌ Bad
const display = `${article.fact_check_score}/100`;  // Throws error if null
```

### 2. **Progressive Disclosure**

```tsx
// Show score on card
<Badge score={article.fact_check_score} />

// Full report on click
<button onClick={() => showModal(article.id)}>
  View Full Fact-Check
</button>
```

### 3. **Cache Aggressively**

```typescript
// Fact-check results rarely change
const cacheTime = 24 * 60 * 60 * 1000;  // 24 hours
```

### 4. **Highlight Misinformation**

```tsx
// Red alert for misinformation
{article.fact_check_verdict?.includes('MISINFORMATION') && (
  <Alert severity="error">
    ⚠️ This article contains misinformation
  </Alert>
)}
```

### 5. **Show Source Count as Trust Signal**

```tsx
<span className="source-count">
  Verified against {validation.num_sources} sources
</span>
```

---

## FAQs

**Q: Do I need to change my API calls?**  
A: No! Fact-check fields are already included in all article responses.

**Q: What if an article isn't fact-checked yet?**  
A: Fields will be `null`. Show "⏳ Checking..." badge. Most articles are checked within 2 minutes.

**Q: How do I get full fact-check details?**  
A: Call Railway API: `GET https://fact-check-production.up.railway.app/fact-check/{job_id}/result`  
Or query your backend for the `article_fact_checks` table data.

**Q: Can users report fact-check errors?**  
A: Yes! Add a "Report Issue" button that sends feedback to your backend.

**Q: How often are articles re-checked?**  
A: Currently once per article. Re-checking can be triggered manually via API.

**Q: What about performance?**  
A: Credibility scores are **denormalized** on articles table for instant queries. Full details are loaded on-demand.

---

## Complete Documentation

📚 **Full Integration Guide**: [`FRONTEND_FACT_CHECK_INTEGRATION_GUIDE.md`](./FRONTEND_FACT_CHECK_INTEGRATION_GUIDE.md)

Includes:
- Complete TypeScript interfaces
- 4 React component examples  
- Real API response samples
- WebSocket integration
- Accessibility guidelines
- Performance optimization tips

📊 **Database Schema**: [`FACT_CHECK_DATABASE_ARCHITECTURE.md`](./FACT_CHECK_DATABASE_ARCHITECTURE.md)

🔗 **Railway API Docs**: `https://fact-check-production.up.railway.app/docs`

---

## Next Steps

1. ✅ Test backend API to see fact-check fields
2. ✅ Add credibility badge to article cards
3. ✅ Implement filter controls
4. ✅ Create fact-check detail modal
5. ✅ Add misinformation warnings
6. 📚 Read full guide for advanced features

---

## Summary

Your backend now automatically fact-checks **every article** with:
- ✓ AI-powered verification against 25+ sources
- ✓ Credibility scores (0-100) 
- ✓ Misinformation detection
- ✓ Detailed evidence and references
- ✓ ~2 minute processing time

**Frontend gets fact-check data automatically** in article responses - no API changes needed!

**Happy coding!** 🚀
