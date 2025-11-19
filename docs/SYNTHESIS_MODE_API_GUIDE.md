# Synthesis Mode API Integration Guide

**Version**: 1.0  
**Date**: November 19, 2025  
**Status**: ✅ Production Ready  
**API Endpoint**: `https://fact-check-production.up.railway.app`

---

## Table of Contents

1. [Overview](#overview)
2. [What is Synthesis Mode?](#what-is-synthesis-mode)
3. [Context & Emphasis Feature](#context--emphasis-feature)
4. [API Usage](#api-usage)
5. [Request Format](#request-format)
6. [Response Format](#response-format)
7. [Integration Examples](#integration-examples)
8. [Error Handling](#error-handling)
9. [Performance Guidelines](#performance-guidelines)
10. [Testing Checklist](#testing-checklist)

---

## Overview

Synthesis mode is a production-ready fact-checking mode that combines:
- **Iterative validation** with multi-pass refinement
- **Narrative synthesis** generating comprehensive journalistic articles
- **Context & Emphasis analysis** comparing original article framing to validated evidence
- **Timeline generation** with chronological event tracking
- **Margin notes** for technical terms and concepts

**Key Difference from Other Modes:**
- `standard`: Fast claim validation (~60s)
- `thorough`: Detailed validation (~5-10min)
- `iterative`: Multi-pass validation (~2-3min)
- **`synthesis`**: Iterative validation + narrative article + Context & Emphasis (~4-7min)

---

## What is Synthesis Mode?

Synthesis mode produces a **complete fact-check article** rather than just validation results.

### Output Includes:

1. **Narrative Article** (1,400-2,500 words)
   - Journalistic prose integrating all claim validations
   - Natural flow with embedded citations
   - Professional fact-check journalism format

2. **Context & Emphasis Section**
   - Compares original article's framing to validated evidence
   - Identifies emphasis gaps (what was overplayed/underplayed)
   - Lists omitted context from original article
   - Compares original sources vs. validated multi-source evidence

3. **Event Timeline**
   - Chronological sequence of key events
   - With dates, actors, significance ratings

4. **Margin Notes**
   - Definitions for technical terms
   - Background on organizations
   - Context for complex concepts

---

## Context & Emphasis Feature

### What It Does

Analyzes **how the original article frames the story** compared to **what validated evidence reveals**.

### Components

#### 1. Original Article Metadata
```json
{
  "original_article": {
    "outlet": "Fox News",
    "headline": "Marjorie Greene says Trump's 'traitor' label could put her life in danger",
    "published_date": "2025-11-16",
    "url": "https://www.foxnews.com/..."
  }
}
```

#### 2. Headline Analysis
```json
{
  "headline_analysis": {
    "original_emphasis": "Personal danger from Trump's label",
    "evidence_reality": "Political rhetoric in public feud between two officials",
    "alignment_assessment": "DIVERGENT",
    "explanation": "Headline emphasizes physical danger without evidence supporting that interpretation [1][2]"
  }
}
```

**Assessment Values:**
- `ALIGNED`: Original framing matches validated evidence
- `DIVERGENT`: Original framing differs significantly from evidence
- `MISLEADING`: Original framing misrepresents validated facts

#### 3. Emphasis Gaps
```json
{
  "emphasis_gaps": [
    {
      "aspect": "Trump's criticism of Greene's policy positions",
      "evidence_reveals": "Multiple policy disagreements documented over 6 months",
      "gap_type": "UNDERPLAYED",
      "citations": ["[15]", "[16]", "[17]"]
    }
  ]
}
```

**Gap Types:**
- `OMISSION`: Important fact completely absent from original
- `UNDERPLAYED`: Fact mentioned but not given appropriate weight
- `OVERPLAYED`: Fact given disproportionate emphasis

#### 4. Omitted Context
```json
{
  "omitted_context": [
    {
      "omitted_fact": "Greene previously criticized Trump on immigration policy",
      "significance": "HIGH",
      "evidence_citation": "[23]"
    }
  ]
}
```

**Significance Levels:**
- `HIGH`: Critical context that significantly changes interpretation
- `MEDIUM`: Important but not essential context
- `LOW`: Supplementary background information

#### 5. Source Attribution Comparison
```json
{
  "source_attribution": {
    "original_sources": ["Anonymous congressional aide"],
    "validated_sources": [
      "Reuters official statement",
      "C-SPAN video footage",
      "Congressional record",
      "Associated Press wire report"
    ],
    "comparison": "Single anonymous source vs. 4 independent verifiable sources"
  }
}
```

#### 6. Impact Statement
```json
{
  "impact_statement": {
    "without_context": "Reader might believe Greene faces imminent physical danger",
    "with_evidence": "Political rhetoric in ongoing policy disagreement between two officials"
  }
}
```

#### 7. Overall Assessment
```json
{
  "overall_assessment": "Original article's framing emphasizes personal danger narrative not supported by validated evidence. Key policy disagreements and broader political context omitted."
}
```

---

## API Usage

### Base URL
```
https://fact-check-production.up.railway.app
```

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/fact-check/submit` | POST | Submit synthesis job |
| `/fact-check/{job_id}/status` | GET | Check job progress |
| `/fact-check/{job_id}/result` | GET | Retrieve results |
| `/docs` | GET | Interactive API documentation |

---

## Request Format

### Submit Synthesis Job

**Endpoint:** `POST /fact-check/submit`

**Headers:**
```http
Content-Type: application/json
```

**Request Body:**
```json
{
  "url": "https://www.example.com/article",
  "mode": "synthesis",
  "generate_image": false,
  "generate_article": true
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string (URL) | ✅ Yes | Article URL to fact-check |
| `mode` | string | ✅ Yes | Must be `"synthesis"` |
| `generate_image` | boolean | ❌ No | Generate editorial image (default: false) |
| `generate_article` | boolean | ❌ No | Must be true for synthesis (default: true) |

**Example cURL:**
```bash
curl -X POST "https://fact-check-production.up.railway.app/fact-check/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.foxnews.com/media/marjorie-greene-says-trumps-traitor-label-could-put-her-life-danger",
    "mode": "synthesis",
    "generate_image": false,
    "generate_article": true
  }'
```

**Success Response (202 Accepted):**
```json
{
  "success": true,
  "job_id": "90c4358e-d7c8-4728-8d33-3024b6c71464",
  "message": "Fact-check job submitted successfully",
  "status_url": "/fact-check/90c4358e-d7c8-4728-8d33-3024b6c71464/status",
  "result_url": "/fact-check/90c4358e-d7c8-4728-8d33-3024b6c71464/result",
  "websocket_url": "/ws/90c4358e-d7c8-4728-8d33-3024b6c71464",
  "estimated_time_seconds": 60,
  "queue_position": null
}
```

**Save the `job_id` to poll for results!**

---

## Response Format

### Status Endpoint

**Endpoint:** `GET /fact-check/{job_id}/status`

**Response:**
```json
{
  "job_id": "90c4358e-d7c8-4728-8d33-3024b6c71464",
  "status": "started",
  "phase": "validation",
  "progress": 65,
  "elapsed_time_seconds": 145.3,
  "estimated_remaining_seconds": 80,
  "article_ready": false,
  "error_message": null,
  "queue_position": null
}
```

**Status Values:**
- `queued`: Job waiting to start
- `started`: Job processing
- `finished`: Job completed successfully
- `failed`: Job encountered error

**Phase Values (in order):**
- `extraction`: Extracting claims from article
- `search`: Searching for evidence
- `validation`: Validating claims
- `article`: Generating narrative article
- `complete`: Finished

### Result Endpoint

**Endpoint:** `GET /fact-check/{job_id}/result`

**Response Structure:**
```json
{
  "job_id": "90c4358e-d7c8-4728-8d33-3024b6c71464",
  "source_url": "https://www.foxnews.com/...",
  "validation_mode": "synthesis",
  "processing_time_seconds": 268.8,
  "timestamp": "2025-11-19T04:05:12.123456",
  
  "summary": "Executive summary of findings",
  "claims_analyzed": 4,
  "claims_validated": 4,
  "num_sources": 64,
  "source_consensus": "STRONG",
  
  "article_accuracy": {
    "verdict": "MIXED",
    "reliability_score": 0.67,
    "confidence": 0.9,
    "claim_breakdown": {
      "true": 2,
      "false": 1,
      "misleading": 1,
      "unverified": 0
    }
  },
  
  "quick_stats": {
    "overall_verdict": "MIXED",
    "reliability_score": 0.67,
    "claims_total": 4,
    "claims_true": 2,
    "claims_false": 1,
    "claims_misleading": 1,
    "claims_unverified": 0
  },
  
  "article_data": {
    "article_metadata": {
      "headline": "Trump-Greene Feud Escalates: 'Traitor' Label Sparks Fierce Reaction",
      "subheadline": "Fact-check analysis reveals complex political dynamics",
      "lead_paragraph": "...",
      "author": "Fact-Check Synthesis Team",
      "publication_date": "2025-11-19",
      "category": "Politics",
      "word_count": 1450,
      "reading_time_minutes": 6
    },
    
    "article_sections": [
      {
        "section_id": "intro",
        "section_type": "introduction",
        "title": "The Claims",
        "content": "Full narrative prose with embedded citations...",
        "key_points": ["Point 1", "Point 2"],
        "word_count": 250
      }
    ],
    
    "context_and_emphasis": {
      "original_article": { ... },
      "headline_analysis": { ... },
      "emphasis_gaps": [ ... ],
      "omitted_context": [ ... ],
      "source_attribution": { ... },
      "impact_statement": { ... },
      "overall_assessment": "..."
    },
    
    "event_timeline": {
      "timeline_type": "chronological",
      "timeline_entries": [
        {
          "date": "2025-11-15",
          "event_title": "Trump criticizes Greene",
          "event_description": "...",
          "significance": "high",
          "actors": ["Donald Trump", "Marjorie Taylor Greene"],
          "source_citation": "[1]"
        }
      ],
      "timeline_summary": "..."
    },
    
    "margin_notes": [
      {
        "note_id": "note-001",
        "target_text": "MAGA",
        "note_type": "definition",
        "content": {
          "title": "Make America Great Again",
          "text": "Political slogan..."
        }
      }
    ],
    
    "references": [
      {
        "citation_number": 1,
        "apa_citation": "Reuters. (2025, November 15)...",
        "url": "https://...",
        "source_type": "news",
        "credibility": "HIGH"
      }
    ]
  },
  
  "article_text": "# Trump-Greene Feud Escalates...\n\n## The Claims\n\n...\n\n## Context & Emphasis\n\n...",
  
  "claims": [...],
  "validation_results": [...],
  "metadata": {...},
  "costs": {...}
}
```

---

## Integration Examples

### JavaScript/TypeScript (Frontend)

```typescript
// Submit synthesis job
async function submitSynthesisJob(url: string) {
  const response = await fetch(
    'https://fact-check-production.up.railway.app/fact-check/submit',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url,
        mode: 'synthesis',
        generate_image: false,
        generate_article: true
      })
    }
  );
  
  const data = await response.json();
  return data.job_id;
}

// Poll for status
async function pollJobStatus(jobId: string) {
  const response = await fetch(
    `https://fact-check-production.up.railway.app/fact-check/${jobId}/status`
  );
  
  const status = await response.json();
  
  console.log(`Status: ${status.status}`);
  console.log(`Progress: ${status.progress}%`);
  console.log(`Phase: ${status.phase}`);
  
  return status;
}

// Get results when finished
async function getResults(jobId: string) {
  const response = await fetch(
    `https://fact-check-production.up.railway.app/fact-check/${jobId}/result`
  );
  
  const results = await response.json();
  
  // Access Context & Emphasis
  const contextEmphasis = results.article_data?.context_and_emphasis;
  
  if (contextEmphasis) {
    console.log('Original outlet:', contextEmphasis.original_article.outlet);
    console.log('Headline assessment:', contextEmphasis.headline_analysis.alignment_assessment);
    console.log('Emphasis gaps:', contextEmphasis.emphasis_gaps.length);
  }
  
  return results;
}

// Complete workflow
async function factCheckArticle(url: string) {
  // 1. Submit job
  const jobId = await submitSynthesisJob(url);
  console.log('Job submitted:', jobId);
  
  // 2. Poll until complete
  let status;
  do {
    await new Promise(resolve => setTimeout(resolve, 10000)); // Wait 10s
    status = await pollJobStatus(jobId);
  } while (status.status === 'queued' || status.status === 'started');
  
  // 3. Get results if successful
  if (status.status === 'finished') {
    const results = await getResults(jobId);
    return results;
  } else {
    throw new Error(`Job failed: ${status.error_message}`);
  }
}

// Usage
factCheckArticle('https://www.foxnews.com/article')
  .then(results => {
    console.log('Article headline:', results.article_data.article_metadata.headline);
    console.log('Verdict:', results.article_accuracy.verdict);
  })
  .catch(error => console.error('Error:', error));
```

### Python (Backend)

```python
import requests
import time
from typing import Dict, Any

API_BASE = "https://fact-check-production.up.railway.app"

def submit_synthesis_job(url: str) -> str:
    """Submit synthesis mode fact-check job."""
    response = requests.post(
        f"{API_BASE}/fact-check/submit",
        json={
            "url": url,
            "mode": "synthesis",
            "generate_image": False,
            "generate_article": True
        }
    )
    response.raise_for_status()
    data = response.json()
    return data["job_id"]

def get_job_status(job_id: str) -> Dict[str, Any]:
    """Get job status."""
    response = requests.get(f"{API_BASE}/fact-check/{job_id}/status")
    response.raise_for_status()
    return response.json()

def get_job_results(job_id: str) -> Dict[str, Any]:
    """Get job results."""
    response = requests.get(f"{API_BASE}/fact-check/{job_id}/result")
    response.raise_for_status()
    return response.json()

def wait_for_completion(job_id: str, timeout: int = 600) -> Dict[str, Any]:
    """Poll job until complete or timeout."""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        status = get_job_status(job_id)
        
        print(f"Status: {status['status']} | "
              f"Phase: {status.get('phase', 'N/A')} | "
              f"Progress: {status.get('progress', 0)}%")
        
        if status["status"] == "finished":
            return get_job_results(job_id)
        elif status["status"] == "failed":
            raise Exception(f"Job failed: {status.get('error_message')}")
        
        time.sleep(10)  # Wait 10 seconds
    
    raise TimeoutError("Job did not complete within timeout")

# Complete workflow
def fact_check_article(url: str) -> Dict[str, Any]:
    """Submit job and wait for results."""
    job_id = submit_synthesis_job(url)
    print(f"Job submitted: {job_id}")
    
    results = wait_for_completion(job_id)
    
    # Extract Context & Emphasis
    context_emphasis = results["article_data"]["context_and_emphasis"]
    
    print(f"\nResults:")
    print(f"Verdict: {results['article_accuracy']['verdict']}")
    print(f"Original outlet: {context_emphasis['original_article']['outlet']}")
    print(f"Headline assessment: {context_emphasis['headline_analysis']['alignment_assessment']}")
    print(f"Emphasis gaps: {len(context_emphasis['emphasis_gaps'])}")
    print(f"Omitted context: {len(context_emphasis['omitted_context'])}")
    
    return results

# Usage
if __name__ == "__main__":
    url = "https://www.foxnews.com/media/marjorie-greene-says-trumps-traitor-label-could-put-her-life-danger"
    results = fact_check_article(url)
```

### React Component Example

```tsx
import { useState, useEffect } from 'react';

interface ContextEmphasis {
  original_article: {
    outlet: string;
    headline: string;
    published_date: string;
  };
  headline_analysis: {
    alignment_assessment: 'ALIGNED' | 'DIVERGENT' | 'MISLEADING';
    explanation: string;
  };
  emphasis_gaps: Array<{
    aspect: string;
    evidence_reveals: string;
    gap_type: 'OMISSION' | 'UNDERPLAYED' | 'OVERPLAYED';
  }>;
  omitted_context: Array<{
    omitted_fact: string;
    significance: 'HIGH' | 'MEDIUM' | 'LOW';
  }>;
  overall_assessment: string;
}

function ContextEmphasisDisplay({ jobId }: { jobId: string }) {
  const [data, setData] = useState<ContextEmphasis | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchResults() {
      const response = await fetch(
        `https://fact-check-production.up.railway.app/fact-check/${jobId}/result`
      );
      const results = await response.json();
      setData(results.article_data.context_and_emphasis);
      setLoading(false);
    }
    fetchResults();
  }, [jobId]);

  if (loading) return <div>Loading...</div>;
  if (!data) return <div>No data</div>;

  return (
    <div className="context-emphasis">
      <h2>Context & Emphasis Analysis</h2>
      
      {/* Original Article Info */}
      <div className="original-article">
        <h3>Original Article</h3>
        <p><strong>Source:</strong> {data.original_article.outlet}</p>
        <p><strong>Headline:</strong> {data.original_article.headline}</p>
        <p><strong>Published:</strong> {data.original_article.published_date}</p>
      </div>

      {/* Headline Analysis */}
      <div className="headline-analysis">
        <h3>Headline Assessment</h3>
        <div className={`assessment ${data.headline_analysis.alignment_assessment.toLowerCase()}`}>
          {data.headline_analysis.alignment_assessment}
        </div>
        <p>{data.headline_analysis.explanation}</p>
      </div>

      {/* Emphasis Gaps */}
      <div className="emphasis-gaps">
        <h3>Emphasis Gaps ({data.emphasis_gaps.length})</h3>
        {data.emphasis_gaps.map((gap, index) => (
          <div key={index} className={`gap ${gap.gap_type.toLowerCase()}`}>
            <span className="badge">{gap.gap_type}</span>
            <p><strong>{gap.aspect}</strong></p>
            <p>Evidence reveals: {gap.evidence_reveals}</p>
          </div>
        ))}
      </div>

      {/* Omitted Context */}
      <div className="omitted-context">
        <h3>Omitted Context ({data.omitted_context.length})</h3>
        {data.omitted_context.map((item, index) => (
          <div key={index} className={`context ${item.significance.toLowerCase()}`}>
            <span className="significance">{item.significance}</span>
            <p>{item.omitted_fact}</p>
          </div>
        ))}
      </div>

      {/* Overall Assessment */}
      <div className="overall-assessment">
        <h3>Overall Assessment</h3>
        <p>{data.overall_assessment}</p>
      </div>
    </div>
  );
}
```

---

## Error Handling

### Common Errors

#### 1. Invalid Mode
```json
{
  "detail": [
    {
      "type": "literal_error",
      "loc": ["body", "mode"],
      "msg": "Input should be 'standard', 'thorough', 'summary', 'iterative' or 'synthesis'",
      "input": "syntesis"
    }
  ]
}
```
**Solution:** Use exact string `"synthesis"`

#### 2. Invalid URL
```json
{
  "detail": [
    {
      "type": "url_parsing",
      "loc": ["body", "url"],
      "msg": "Input should be a valid URL"
    }
  ]
}
```
**Solution:** Provide valid HTTP/HTTPS URL

#### 3. Job Failed
```json
{
  "job_id": "...",
  "status": "failed",
  "error_message": "No content extracted from URL"
}
```
**Common Causes:**
- URL is behind paywall
- URL requires JavaScript to render
- Site blocks automated access
- URL is invalid/dead link

**Solution:** Validate URL accessibility before submission

#### 4. Synthesis Mode Disabled
```json
{
  "job_id": "...",
  "status": "failed",
  "error_message": "Synthesis mode is disabled by configuration"
}
```
**Solution:** Contact backend team (this should not occur in production)

### Retry Strategy

```python
def submit_with_retry(url: str, max_retries: int = 3) -> str:
    """Submit job with retry logic."""
    for attempt in range(max_retries):
        try:
            job_id = submit_synthesis_job(url)
            return job_id
        except requests.HTTPError as e:
            if e.response.status_code == 429:  # Rate limit
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
            else:
                raise
    raise Exception("Max retries exceeded")
```

---

## Performance Guidelines

### Expected Processing Times

| Mode | Average Time | Range |
|------|-------------|-------|
| Standard | 60s | 30-90s |
| Thorough | 7min | 5-10min |
| Iterative | 2.5min | 2-3min |
| **Synthesis** | **5min** | **4-7min** |

### Factors Affecting Time

1. **Number of claims**: More claims = longer processing
2. **Evidence complexity**: Complex topics require more evidence search
3. **Article length**: Longer articles take more time to extract
4. **API rate limits**: Gemini/Exa rate limits can slow processing

### Best Practices

#### 1. Set Realistic Timeouts
```typescript
const SYNTHESIS_TIMEOUT = 600000; // 10 minutes
```

#### 2. Show Progress to Users
```typescript
function displayProgress(status) {
  const phaseMessages = {
    'extraction': 'Extracting claims from article...',
    'search': 'Searching for evidence...',
    'validation': 'Validating claims...',
    'article': 'Generating narrative article...',
    'complete': 'Complete!'
  };
  
  return `${phaseMessages[status.phase]} (${status.progress}%)`;
}
```

#### 3. Cache Results
```python
# Cache results for 24 hours
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def get_cached_results(url: str) -> Dict[str, Any]:
    """Cache synthesis results by URL."""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    # Check cache...
    # If miss, submit new job
    return results
```

#### 4. Poll Efficiently
```typescript
// Adaptive polling: fast initially, slower later
function getPollingInterval(elapsedSeconds: number): number {
  if (elapsedSeconds < 60) return 5000;   // 5s for first minute
  if (elapsedSeconds < 180) return 10000; // 10s for next 2 minutes
  return 15000;                            // 15s thereafter
}
```

---

## Testing Checklist

### Pre-Integration Testing

- [ ] Test submission with valid URL
- [ ] Test submission with invalid URL (expect validation error)
- [ ] Test submission with invalid mode (expect validation error)
- [ ] Poll status endpoint until `finished`
- [ ] Verify `article_data.context_and_emphasis` exists
- [ ] Verify all Context & Emphasis fields are populated:
  - [ ] `original_article`
  - [ ] `headline_analysis`
  - [ ] `emphasis_gaps` (array)
  - [ ] `omitted_context` (array)
  - [ ] `source_attribution`
  - [ ] `impact_statement`
  - [ ] `overall_assessment`
- [ ] Verify `article_text` contains "## Context & Emphasis"
- [ ] Test error handling for failed jobs
- [ ] Verify timeout handling

### Test URLs

**Recommended for testing:**
```
https://www.foxnews.com/media/marjorie-greene-says-trumps-traitor-label-could-put-her-life-danger
```
- **Claims**: 4
- **Processing Time**: ~5 min
- **Context & Emphasis**: ✅ Yes

### Integration Validation

```python
def validate_synthesis_response(results: Dict[str, Any]) -> bool:
    """Validate synthesis response has required fields."""
    required_fields = [
        'job_id',
        'validation_mode',
        'article_data',
        'article_text',
        'article_accuracy',
        'claims_analyzed',
        'claims_validated'
    ]
    
    # Check top-level fields
    for field in required_fields:
        if field not in results:
            print(f"Missing field: {field}")
            return False
    
    # Check mode is synthesis
    if results['validation_mode'] != 'synthesis':
        print(f"Wrong mode: {results['validation_mode']}")
        return False
    
    # Check Context & Emphasis exists
    context = results['article_data'].get('context_and_emphasis')
    if not context:
        print("Missing context_and_emphasis")
        return False
    
    # Check Context & Emphasis has required fields
    context_fields = [
        'original_article',
        'headline_analysis',
        'emphasis_gaps',
        'omitted_context',
        'overall_assessment'
    ]
    
    for field in context_fields:
        if field not in context:
            print(f"Missing context field: {field}")
            return False
    
    print("✅ All validations passed")
    return True
```

---

## Appendix: JSON Schema

### Context & Emphasis Schema

```typescript
interface ContextAndEmphasis {
  original_article: {
    outlet: string;
    headline: string;
    published_date: string;
    url: string;
  };
  
  headline_analysis: {
    original_emphasis: string;
    evidence_reality: string;
    alignment_assessment: 'ALIGNED' | 'DIVERGENT' | 'MISLEADING';
    explanation: string;
  };
  
  emphasis_gaps: Array<{
    aspect: string;
    evidence_reveals: string;
    gap_type: 'OMISSION' | 'UNDERPLAYED' | 'OVERPLAYED';
    citations: string[];
  }>;
  
  omitted_context: Array<{
    omitted_fact: string;
    significance: 'HIGH' | 'MEDIUM' | 'LOW';
    evidence_citation: string;
  }>;
  
  source_attribution: {
    original_sources: string[];
    validated_sources: string[];
    comparison: string;
  };
  
  impact_statement: {
    without_context: string;
    with_evidence: string;
  };
  
  overall_assessment: string;
}
```

---

## Support & Questions

**Technical Issues:**
- Check Railway deployment logs
- Verify API endpoint is accessible
- Ensure synthesis mode is enabled in config

**Questions:**
- Contact backend engineering team
- Reference this document
- Test with provided example URLs

---

**Document Version**: 1.0  
**Last Updated**: November 19, 2025  
**API Status**: ✅ Production Ready
