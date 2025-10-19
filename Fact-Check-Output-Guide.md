# Fact-Check Output Structure Guide

**For Frontend & Backend Integration Teams**

This document explains the complete output structure of the fact-check system, including all returned data fields, file formats, and integration examples.

---

## Table of Contents

1. [Overview](#overview)
2. [Output Modes](#output-modes)
3. [File Structure](#file-structure)
4. [API Response Format](#api-response-format)
5. [Data Field Reference](#data-field-reference)
6. [Integration Examples](#integration-examples)
7. [Example Output](#example-output)

---

## Overview

The fact-check system analyzes articles and returns comprehensive validation results including:
- ✅ Verdict classification (TRUE, FALSE, MISLEADING, etc.)
- 📊 Confidence scores
- 📚 Evidence from multiple sources
- 📰 AI-generated fact-check article
- 🎨 Editorial cartoon visualization (optional)
- 💾 Supabase database record

**Processing Time**: 60-90 seconds depending on mode and options

---

## Output Modes

### 1. **Standard Mode** (Default)
- Extracts individual claims from the article
- Validates HIGH-risk claims only
- Faster processing (~60s)

### 2. **Thorough Mode** (`--thorough`)
- Validates ALL claims regardless of risk level
- More comprehensive analysis
- Longer processing (~70s)

### 3. **Summary Mode** (`--summary`)
- Treats entire article as single narrative
- Validates overall story accuracy
- Ideal for opinion pieces or editorials
- Processing time: ~70-80s

---

## File Structure

When using CLI or when outputs are saved locally, results are stored in timestamped directories:

```
fact_check_outputs/
└── 2025-10-17_16-19-33_foxnews_com/
    ├── report.json          # Main validation results (12KB)
    ├── evidence.json        # Raw evidence data from searches (5.2MB)
    ├── claims.json          # Extracted claims with metadata (830B)
    ├── article.json         # Generated fact-check article (15KB)
    ├── article.txt          # Plain text version of article (5.6KB)
    ├── summary.txt          # Human-readable summary (2.5KB)
    ├── metadata.json        # Processing metadata (678B)
    └── image_url.txt        # Editorial cartoon URL (154B)
```

### File Descriptions

| File | Size | Purpose | Required For |
|------|------|---------|--------------|
| `report.json` | 12KB | **Primary output** - Validation results, verdicts, evidence | ✅ All integrations |
| `article.json` | 15KB | Generated fact-check article with structured data | 📰 Article display |
| `article.txt` | 5.6KB | Plain text version of fact-check article | 📄 Text-only display |
| `metadata.json` | 678B | Processing info, costs, config | 📊 Analytics |
| `image_url.txt` | 154B | Direct URL to editorial cartoon | 🎨 Image display |
| `claims.json` | 830B | Raw extracted claims before validation | 🔍 Claim analysis |
| `evidence.json` | 5.2MB | All evidence from Exa searches | 📚 Deep research |
| `summary.txt` | 2.5KB | Human-readable summary | 👁️ Quick preview |

---

## API Response Format

### Submit Job Response

```json
{
  "success": true,
  "job_id": "a75a91be-d5d9-4b8a-83cc-f85906ec714e",
  "message": "Fact-check job submitted successfully",
  "status_url": "/fact-check/a75a91be-d5d9-4b8a-83cc-f85906ec714e/status",
  "result_url": "/fact-check/a75a91be-d5d9-4b8a-83cc-f85906ec714e/result",
  "websocket_url": "/ws/a75a91be-d5d9-4b8a-83cc-f85906ec714e",
  "estimated_time_seconds": 70,
  "queue_position": 1
}
```

### Job Status Response

```json
{
  "job_id": "a75a91be-d5d9-4b8a-83cc-f85906ec714e",
  "status": "started",
  "phase": "validating_claims",
  "progress": 75,
  "elapsed_time_seconds": 45.2,
  "estimated_remaining_seconds": 15,
  "article_ready": true,
  "error_message": null,
  "queue_position": null
}
```

**Status Values**: `queued` → `started` → `finished` | `failed`

**Phase Values**: 
- `extracting_content`
- `generating_summary`
- `searching_evidence`
- `validating_claims`
- `generating_article`
- `generating_image`

---

## Data Field Reference

### Main Result Object (`report.json`)

```typescript
interface FactCheckResult {
  // Status
  status: "SUCCESS" | "FAILED";
  timestamp: string;  // ISO 8601
  elapsed_time: number;  // seconds
  
  // Statistics
  statistics: {
    total_claims: number;
    high_risk_claims: number;
    validated_claims: number;
    claims_with_evidence: number;
    average_sources_per_claim: number;
    total_validation_cost: number;  // USD
  };
  
  // Validation Results (array of claims)
  validation_results: ValidationResult[];
  
  // Optional: Generated image URL
  image_url?: string;
}
```

### Validation Result Object

```typescript
interface ValidationResult {
  // Claim Information
  claim: string;  // Full claim text
  risk_level: "HIGH" | "MEDIUM" | "LOW";
  category: string;  // e.g., "Narrative Summary", "Financial Claim"
  
  // Validation Output
  validation_output: {
    verdict: string;  // See Verdict Types below
    confidence: number;  // 0.0 to 1.0
    summary: string;  // Concise explanation
    
    // Evidence
    key_evidence: {
      supporting: string[];  // Array of supporting facts
      contradicting: string[];  // Array of contradicting facts
      context: string[];  // Additional context
    };
    
    // Source Analysis
    source_analysis: {
      most_credible_sources: number[];  // Citation IDs
      source_consensus: "GENERAL_AGREEMENT" | "MIXED" | "DISPUTED";
      evidence_quality: "HIGH" | "MEDIUM" | "LOW";
    };
    
    // Metadata
    metadata: {
      misinformation_indicators: string[];  // e.g., ["FABRICATED", "TEMPORAL_INCONSISTENCY"]
      spread_risk: "HIGH" | "MEDIUM" | "LOW";
      confidence_factors: {
        source_agreement: number;
        evidence_quality: number;
        temporal_consistency: number;
      };
    };
    
    // References
    references: Reference[];  // Full citation objects
    
    // Technical Details
    model: string;
    validation_mode: "standard" | "thorough";
    cost: number;
    token_usage: {
      prompt_tokens: number;
      candidates_tokens: number;
      total_tokens: number;
    };
  };
  
  // Search Details
  evidence_found: boolean;
  num_sources: number;
  search_breakdown: {
    news: number;
    research: number;
    general: number;
    historical: number;
  };
  
  // Timestamps
  search_timestamp: string;
  validation_timestamp: string;
}
```

### Verdict Types

| Verdict | Meaning | Confidence Range |
|---------|---------|------------------|
| `TRUE` | Claim is accurate | 80-100% |
| `MOSTLY TRUE` | Largely accurate with minor issues | 70-89% |
| `PARTIALLY TRUE` | Mixed accuracy | 50-69% |
| `MISLEADING` | Technically true but deceptive | 60-90% |
| `UNVERIFIED` | Insufficient evidence | 40-60% |
| `FALSE` | Claim is inaccurate | 70-100% |
| `FALSE - MISINFORMATION` | Intentionally false | 85-100% |

### Reference Object

```typescript
interface Reference {
  citation_id: number;
  title: string;
  url: string;
  source: string;  // e.g., "AP News", "Brookings"
  author: string | null;
  date: string;  // YYYY-MM-DD
  type: "news" | "research" | "general" | "historical";
  relevance: string;  // Description of relevance
  credibility: "HIGH" | "MEDIUM" | "LOW";
}
```

### Generated Article Object (`article.json`)

```typescript
interface GeneratedArticle {
  article_data: {
    headline: string;
    subheadline: string;
    summary: string;
    verdict_breakdown: {
      true_claims: number;
      false_claims: number;
      misleading_claims: number;
      unverified_claims: number;
    };
    key_findings: string[];
    bottom_line: string;
    article_body: string;  // Full formatted article
  };
  article_text: string;  // Plain text version
  timestamp: string;
}
```

### Metadata Object (`metadata.json`)

```typescript
interface Metadata {
  url: string;  // Source article URL
  timestamp: string;  // Processing timestamp
  mode: "standard" | "thorough" | "summary";
  duration_seconds: number;
  statistics: Statistics;  // Same as in report.json
  output_format: "standard" | "summary";
  submission_id: string;  // Supabase database ID
  total_validation_cost: number;
  config: {
    model: string;
    exa_results_per_query: number;
    max_claims: number;
  };
}
```

---

## Integration Examples

### React Component - Display Results

```typescript
import React from 'react';

interface Props {
  result: FactCheckResult;
}

export function FactCheckResultDisplay({ result }: Props) {
  return (
    <div className="fact-check-result">
      {/* Header */}
      <div className="header">
        <h2>Fact-Check Results</h2>
        <span className={`status ${result.status.toLowerCase()}`}>
          {result.status}
        </span>
      </div>

      {/* Statistics */}
      <div className="statistics">
        <div className="stat">
          <span className="label">Claims Analyzed:</span>
          <span className="value">{result.statistics.total_claims}</span>
        </div>
        <div className="stat">
          <span className="label">Validated:</span>
          <span className="value">{result.statistics.validated_claims}</span>
        </div>
        <div className="stat">
          <span className="label">Processing Time:</span>
          <span className="value">{result.elapsed_time.toFixed(1)}s</span>
        </div>
      </div>

      {/* Validation Results */}
      {result.validation_results.map((validation, idx) => (
        <div key={idx} className={`validation-item ${getVerdictClass(validation.validation_output.verdict)}`}>
          <div className="verdict-badge">
            {validation.validation_output.verdict}
          </div>
          
          <div className="confidence">
            Confidence: {(validation.validation_output.confidence * 100).toFixed(0)}%
          </div>

          <p className="claim">{validation.claim}</p>
          
          <p className="summary">{validation.validation_output.summary}</p>

          {/* Evidence */}
          {validation.validation_output.key_evidence.supporting.length > 0 && (
            <div className="evidence supporting">
              <h4>Supporting Evidence:</h4>
              <ul>
                {validation.validation_output.key_evidence.supporting.map((ev, i) => (
                  <li key={i}>{ev}</li>
                ))}
              </ul>
            </div>
          )}

          {validation.validation_output.key_evidence.contradicting.length > 0 && (
            <div className="evidence contradicting">
              <h4>Contradicting Evidence:</h4>
              <ul>
                {validation.validation_output.key_evidence.contradicting.map((ev, i) => (
                  <li key={i}>{ev}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Sources */}
          <div className="sources">
            <h4>Sources ({validation.num_sources}):</h4>
            <div className="source-breakdown">
              {Object.entries(validation.search_breakdown).map(([type, count]) => (
                <span key={type} className="source-badge">
                  {type}: {count}
                </span>
              ))}
            </div>
          </div>
        </div>
      ))}

      {/* Editorial Cartoon */}
      {result.image_url && (
        <div className="editorial-cartoon">
          <h3>Editorial Cartoon</h3>
          <img src={result.image_url} alt="Fact-check editorial cartoon" />
        </div>
      )}
    </div>
  );
}

function getVerdictClass(verdict: string): string {
  if (verdict.includes('TRUE')) return 'verdict-true';
  if (verdict.includes('FALSE') || verdict.includes('MISINFORMATION')) return 'verdict-false';
  if (verdict.includes('MISLEADING')) return 'verdict-misleading';
  return 'verdict-unverified';
}
```

### Backend - Save to Database

```typescript
// Node.js/Express
app.post('/api/factcheck/save', async (req, res) => {
  const { job_id } = req.body;

  try {
    // Get result from fact-check API
    const result = await fetch(
      `https://fact-check-production.up.railway.app/fact-check/${job_id}/result`
    ).then(r => r.json());

    // Save to your database
    const savedRecord = await db.factChecks.create({
      jobId: job_id,
      sourceUrl: result.metadata?.url,
      status: result.status,
      verdicts: result.validation_results.map(v => v.validation_output.verdict),
      confidence: result.validation_results.map(v => v.validation_output.confidence),
      processingTime: result.elapsed_time,
      totalCost: result.statistics.total_validation_cost,
      imageUrl: result.image_url,
      submissionId: result.metadata?.submission_id,
      fullResult: result,  // Store complete JSON
      createdAt: new Date(),
    });

    res.json({ success: true, id: savedRecord.id });
  } catch (error) {
    console.error('Error saving fact-check:', error);
    res.status(500).json({ error: 'Failed to save fact-check' });
  }
});
```

---

## Example Output

### Sample Execution

```bash
python fact_check_cli.py \
  --url "https://www.foxnews.com/politics/article" \
  --summary \
  --generate-image
```

### Console Output

```
🌐 Processing URL: https://www.foxnews.com/politics/article
🔧 Mode: Summary (narrative analysis)
------------------------------------------------------------

📄 Step 1: Extracting content from URL...
✅ Extracted article content (1428 words)

📝 Step 2: Generating article summary...
✅ Generated summary (97 words)
   - Risk level: HIGH
   - Type: investigation
   - Key claims: 5

🔧 Step 3: Initializing validation system...
✅ Validation system ready

🔍 Step 4: Validating article summary...
✅ Validation completed in 31.5 seconds

📝 Step 5: Generating journalistic article...
✅ Article generated successfully

🎨 Step 6: Generating editorial cartoon...
✅ Image generated successfully
   URL: https://jluwnohozbtsvzfiysnf.supabase.co/storage/v1/object/public/news-images/...

💾 Step 7: Saving to database...
✅ Saved to database with ID: 585fa0a8-5e4d-48f5-b5f5-2150439fbd28

📊 Results
============================================================
🔍 Fact Check Summary Report
========================

Source URL: https://www.foxnews.com/politics/article
Validation Mode: Narrative Summary
Claims analyzed: 1
Claims validated: 1
Total cost: $0.0107

NARRATIVE VALIDATION:
  Verdict: FALSE - MISINFORMATION
  Confidence: 90%

ANALYSIS:
The claim contains fabricated financial details and future dates that are 
inconsistent with the provided evidence. While the subject's affiliation 
is well-documented, the specific financial transactions are not supported 
by evidence.

============================================================
📰 FACT-CHECK ARTICLE PREVIEW
============================================================

Fact Check: Campaign Funding Claims Debunked

VERDICT SUMMARY:
  ✗⚠ Misinformation: 1

BOTTOM LINE: Claims are entirely fabricated, containing future dates and 
unverified financial figures, designed to spread misinformation.

💾 Results saved to: fact_check_outputs/2025-10-17_16-19-33_foxnews_com/
   Files: report.json, evidence.json, article.json, metadata.json, image_url.txt
   Database ID: 585fa0a8-5e4d-48f5-b5f5-2150439fbd28
```

### Key Result Fields

**From `report.json`:**

```json
{
  "status": "SUCCESS",
  "statistics": {
    "total_claims": 1,
    "validated_claims": 1,
    "total_validation_cost": 0.0107
  },
  "validation_results": [{
    "verdict": "FALSE - MISINFORMATION",
    "confidence": 0.9,
    "summary": "The claim contains fabricated financial details...",
    "num_sources": 25,
    "search_breakdown": {
      "news": 5,
      "research": 10,
      "general": 5,
      "historical": 5
    }
  }],
  "image_url": "https://jluwnohozbtsvzfiysnf.supabase.co/storage/v1/object/public/news-images/..."
}
```

**From `metadata.json`:**

```json
{
  "url": "https://www.foxnews.com/politics/article",
  "mode": "summary",
  "duration_seconds": 31.54,
  "submission_id": "585fa0a8-5e4d-48f5-b5f5-2150439fbd28",
  "config": {
    "model": "gemini-2.5-flash",
    "exa_results_per_query": 5
  }
}
```

---

## UI/UX Recommendations

### Color Coding for Verdicts

| Verdict | Color | Icon |
|---------|-------|------|
| TRUE | Green (#22c55e) | ✓ |
| MOSTLY TRUE | Light Green (#84cc16) | ✓ |
| PARTIALLY TRUE | Yellow (#facc15) | ⚠ |
| MISLEADING | Orange (#f97316) | ⚠ |
| UNVERIFIED | Gray (#9ca3af) | ? |
| FALSE | Red (#ef4444) | ✗ |
| MISINFORMATION | Dark Red (#dc2626) | ✗⚠ |

### Display Priority

1. **Verdict & Confidence** (most prominent)
2. **Summary** (concise explanation)
3. **Evidence** (expandable sections)
4. **Sources** (collapsible with badges)
5. **Technical Details** (optional, for power users)

### Progressive Disclosure

- Show summary by default
- Expand to see detailed evidence
- Click sources to view full citations
- Technical metadata in separate tab/panel

---

## Performance Considerations

### Response Sizes

| Field | Typical Size | Notes |
|-------|--------------|-------|
| `report.json` | 10-15KB | Main response |
| `article.json` | 12-20KB | If article generation enabled |
| `evidence.json` | 3-8MB | **Large** - usually not needed for display |
| Full API response | 15-35KB | Without evidence.json |

### Recommendations

1. **Don't load `evidence.json`** unless needed for deep research
2. **Cache results** by `submission_id` or `job_id`
3. **Paginate sources** if displaying all references
4. **Lazy load images** from Supabase storage
5. **WebSocket for real-time updates** during processing

---

## Database Integration

The fact-check system saves results to Supabase with this schema:

### Tables

1. **`fact_check_submissions`** - Main records
   - `id` (UUID) - Primary key
   - `url` (text) - Source article URL
   - `status` (text) - Processing status
   - `mode` (text) - Validation mode
   - `processing_time_seconds` (float)
   - `total_cost` (decimal)
   - `created_at` (timestamp)
   - Full metadata fields...

2. **`individual_claims`** - Claim details
   - `id` (UUID) - Primary key
   - `submission_id` (UUID) - Foreign key
   - `claim_text` (text)
   - `verdict` (text)
   - `confidence` (float)
   - `supporting_evidence` (jsonb)
   - `contradicting_evidence` (jsonb)

### Query Examples

```sql
-- Get recent fact-checks
SELECT id, url, status, verdict, processing_time_seconds
FROM fact_check_submissions
ORDER BY created_at DESC
LIMIT 10;

-- Get claims for a submission
SELECT claim_text, verdict, confidence
FROM individual_claims
WHERE submission_id = '585fa0a8-5e4d-48f5-b5f5-2150439fbd28';

-- Get misinformation alerts
SELECT url, verdict, confidence
FROM fact_check_submissions
WHERE verdict LIKE '%MISINFORMATION%'
  AND created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;
```

---

## Testing & Validation

### Sample Test Cases

```bash
# Standard mode - quick validation
curl -X POST https://fact-check-production.up.railway.app/fact-check/submit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.reuters.com/article", "mode": "standard"}'

# Summary mode with image
curl -X POST https://fact-check-production.up.railway.app/fact-check/submit \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.example.com/article",
    "mode": "summary",
    "generate_image": true,
    "generate_article": true
  }'

# Thorough mode - all claims
curl -X POST https://fact-check-production.up.railway.app/fact-check/submit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.example.com/article", "mode": "thorough"}'
```

---

## Error Handling

### Common Error Responses

```json
{
  "success": false,
  "error": "Failed to extract content from URL",
  "error_type": "http_error",
  "timestamp": "2025-10-17T16:20:00Z",
  "job_id": "abc123"
}
```

**Error Types**:
- `http_error` - Failed to fetch URL
- `validation_error` - Invalid input
- `timeout_error` - Processing took too long
- `server_error` - Internal error

---

## Additional Resources

- **API Documentation**: https://fact-check-production.up.railway.app/docs
- **Integration Guide**: [API_INTEGRATION_GUIDE.md](API_INTEGRATION_GUIDE.md)
- **Railway Deployment**: [RAILWAY_DEPLOYMENT_SUCCESS.md](RAILWAY_DEPLOYMENT_SUCCESS.md)

---

**Last Updated**: October 2025  
**API Version**: 1.0.0
