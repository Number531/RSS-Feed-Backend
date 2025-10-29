# Fact-Check API Integration Guide for Backend Team

## Overview

This guide shows how to integrate with the fact-check service API from the backend application. The fact-check service now supports iterative mode with parallel validation for enhanced accuracy.

---

## API Endpoint

**Production URL:** `https://fact-check-production.up.railway.app`

---

## Key Differences: Standard vs Iterative Mode

### Standard Mode (Original)
- Validates individual claims sequentially
- Faster but less thorough
- Good for quick fact-checks

### Iterative Mode (New - Recommended)
- Multi-pass refinement with parallel validation
- Validates top-K claims concurrently
- Early stopping when no issues found
- Provides detailed metadata including iterations, issues found, article accuracy score
- ~50% faster claim validation due to parallelization
- More accurate results

---

## API Call Examples

### 1. Basic Summary Mode (Uses Iterative if Enabled)

```bash
curl -X POST "https://fact-check-production.up.railway.app/fact-check/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.foxnews.com/politics/article-url",
    "mode": "summary"
  }'
```

**Response:**
```json
{
  "success": true,
  "job_id": "uuid-here",
  "status_url": "/fact-check/{job_id}/status",
  "result_url": "/fact-check/{job_id}/result",
  "estimated_time_seconds": 60
}
```

### 2. Explicit Iterative Mode (Recommended)

```bash
curl -X POST "https://fact-check-production.up.railway.app/fact-check/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.foxnews.com/politics/article-url",
    "mode": "iterative"
  }'
```

**Key Difference:** Use `"mode": "iterative"` instead of `"mode": "summary"`

### 3. With Article Generation

```bash
curl -X POST "https://fact-check-production.up.railway.app/fact-check/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.foxnews.com/politics/article-url",
    "mode": "iterative",
    "generate_article": true
  }'
```

### 4. Full Options

```bash
curl -X POST "https://fact-check-production.up.railway.app/fact-check/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.foxnews.com/politics/article-url",
    "mode": "iterative",
    "generate_article": true,
    "generate_image": false
  }'
```

---

## Checking Job Status

```bash
# Replace {job_id} with the ID from submit response
curl "https://fact-check-production.up.railway.app/fact-check/{job_id}/status"
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "finished",  // or "started", "failed"
  "phase": "complete",   // or "extraction", "validation", "article"
  "progress": 100,
  "elapsed_time_seconds": 307.89,
  "article_ready": true,
  "error_message": null
}
```

---

## Retrieving Results

```bash
curl "https://fact-check-production.up.railway.app/fact-check/{job_id}/result"
```

### Standard Mode Response

```json
{
  "source_url": "https://...",
  "validation_mode": "summary",
  "claims_analyzed": 1,
  "claims_validated": 1,
  "claims": [
    {
      "claim": "Claim text",
      "risk_level": "HIGH",
      "category": "Political",
      "context": "...",
      "actors": []
    }
  ],
  "validation_results": [
    {
      "claim": "Claim text",
      "validation_result": {
        "verdict": "TRUE",
        "confidence": 0.85,
        "evidence_summary": "..."
      }
    }
  ],
  "article_text": "Generated article...",
  "metadata": {
    "mode": "summary",
    "is_iterative_mode": false
  }
}
```

### Iterative Mode Response (Enhanced)

```json
{
  "source_url": "https://...",
  "validation_mode": "iterative",
  "claims_analyzed": 3,
  "claims_validated": 3,
  "claims": [
    {
      "claim": "The Trump administration is warning...",
      "risk_level": "HIGH",
      "category": "Factual Claim",
      "context": "Extracted from article (claim 1)",
      "actors": []
    },
    {
      "claim": "The U.S. Department of Agriculture states...",
      "risk_level": "HIGH",
      "category": "Factual Claim",
      "context": "Extracted from article (claim 2)",
      "actors": []
    }
  ],
  "validation_results": [
    {
      "claim": "...",
      "validation_result": {
        "verdict": "TRUE",
        "confidence": 0.90,
        "evidence_summary": "..."
      }
    }
  ],
  "article_text": "Generated article...",
  "metadata": {
    "mode": "iterative",
    "is_iterative_mode": true,
    "iterative_metadata": {
      "iterations_completed": 2,
      "claims_validated": 3,
      "issues_found": 0,
      "total_time_seconds": 53.47,
      "early_stopped": true,
      "extracted_claims": [...],
      "claim_verdicts": [...],
      "refinement_history": [...],
      "temporal_reconciliation_applied": false,
      "article_accuracy": {
        "reliability_score": 0.85,
        "verdict": "MOSTLY TRUE",
        "explanation": "..."
      }
    }
  },
  "costs": {
    "claim_extraction": 0.001,
    "evidence_search": 0.006,
    "validation": 0.006,
    "article_generation": 0.003,
    "total": 0.016
  }
}
```

---

## Node.js Integration Example

```javascript
// Submit fact-check job
async function submitFactCheck(url) {
  const response = await fetch('https://fact-check-production.up.railway.app/fact-check/submit', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      url: url,
      mode: 'iterative',  // Use iterative mode for better results
      generate_article: true
    })
  });
  
  const data = await response.json();
  return data.job_id;
}

// Poll for results
async function getFactCheckResult(jobId) {
  let status = 'started';
  
  while (status !== 'finished' && status !== 'failed') {
    const statusResponse = await fetch(
      `https://fact-check-production.up.railway.app/fact-check/${jobId}/status`
    );
    const statusData = await statusResponse.json();
    status = statusData.status;
    
    if (status === 'finished') {
      const resultResponse = await fetch(
        `https://fact-check-production.up.railway.app/fact-check/${jobId}/result`
      );
      return await resultResponse.json();
    }
    
    if (status === 'failed') {
      throw new Error(statusData.error_message || 'Fact-check job failed');
    }
    
    // Wait 5 seconds before polling again
    await new Promise(resolve => setTimeout(resolve, 5000));
  }
}

// Usage
const jobId = await submitFactCheck('https://example.com/article');
const result = await getFactCheckResult(jobId);

// Access iterative metadata if available
if (result.metadata.is_iterative_mode) {
  console.log('Iterations:', result.metadata.iterative_metadata.iterations_completed);
  console.log('Issues found:', result.metadata.iterative_metadata.issues_found);
  console.log('Article score:', result.metadata.iterative_metadata.article_accuracy);
}
```

---

## Python Integration Example

```python
import requests
import time

def submit_fact_check(url: str) -> str:
    """Submit a fact-check job and return job ID."""
    response = requests.post(
        'https://fact-check-production.up.railway.app/fact-check/submit',
        json={
            'url': url,
            'mode': 'iterative',  # Use iterative mode
            'generate_article': True
        }
    )
    data = response.json()
    return data['job_id']

def get_fact_check_result(job_id: str) -> dict:
    """Poll for fact-check results until complete."""
    while True:
        # Check status
        status_response = requests.get(
            f'https://fact-check-production.up.railway.app/fact-check/{job_id}/status'
        )
        status_data = status_response.json()
        
        if status_data['status'] == 'finished':
            # Get results
            result_response = requests.get(
                f'https://fact-check-production.up.railway.app/fact-check/{job_id}/result'
            )
            return result_response.json()
        
        if status_data['status'] == 'failed':
            raise Exception(status_data.get('error_message', 'Job failed'))
        
        # Wait 5 seconds before polling again
        time.sleep(5)

# Usage
job_id = submit_fact_check('https://example.com/article')
result = get_fact_check_result(job_id)

# Access iterative metadata
if result['metadata']['is_iterative_mode']:
    iter_meta = result['metadata']['iterative_metadata']
    print(f"Iterations: {iter_meta['iterations_completed']}")
    print(f"Claims validated: {iter_meta['claims_validated']}")
    print(f"Issues found: {iter_meta['issues_found']}")
    print(f"Article accuracy: {iter_meta.get('article_accuracy', {})}")
```

---

## Key Fields to Extract

### For Display in Frontend

```javascript
{
  validation_mode: result.validation_mode,              // "iterative"
  claimsAnalyzed: result.claims_analyzed,              // 3
  claimsValidated: result.claims_validated,            // 3
  
  // List of claims with their verdicts
  claims: result.validation_results.map(v => ({
    claim: v.claim,
    verdict: v.validation_result.verdict,              // "TRUE", "FALSE", etc.
    confidence: v.validation_result.confidence,        // 0.0-1.0
    summary: v.validation_result.evidence_summary
  })),
  
  // Iterative mode specific data
  iterations: result.metadata.iterative_metadata?.iterations_completed,
  issuesFound: result.metadata.iterative_metadata?.issues_found,
  processingTime: result.metadata.iterative_metadata?.total_time_seconds,
  articleScore: result.metadata.iterative_metadata?.article_accuracy,
  
  // Generated content
  article: result.article_text,
  imageUrl: result.image_url
}
```

---

## Performance Characteristics

### Standard Mode
- Processing time: ~120-180 seconds
- Best for: Quick checks, low-stakes validation

### Iterative Mode
- Processing time: ~250-350 seconds total
  - Extraction: ~20 seconds
  - Iterative validation: ~50-70 seconds
  - Article generation: ~50-100 seconds
- Best for: High-quality fact-checking, detailed analysis

---

## Error Handling

```javascript
try {
  const jobId = await submitFactCheck(url);
  const result = await getFactCheckResult(jobId);
  
  if (result.error) {
    // Handle API error
    console.error('Fact-check error:', result.error);
    return;
  }
  
  // Process successful result
  processFactCheckResult(result);
  
} catch (error) {
  console.error('Failed to fact-check:', error);
  // Show user-friendly error message
}
```

### Common Error Cases

1. **Invalid URL**: URL cannot be accessed or scraped
2. **No content extracted**: Article paywall or blocked
3. **Timeout**: Article too long or complex
4. **API rate limit**: Too many concurrent requests

---

## Migration from Old API

### Old Call (Standard Mode)
```json
{
  "url": "...",
  "mode": "standard"
}
```

### New Call (Iterative Mode)
```json
{
  "url": "...",
  "mode": "iterative"
}
```

**That's it!** Just change `"mode": "standard"` to `"mode": "iterative"`.

The response structure remains compatible, with additional fields in `metadata.iterative_metadata` that can be optionally displayed.

---

## Testing the API

### Quick Test (curl)

```bash
# Submit job
JOB_ID=$(curl -s -X POST "https://fact-check-production.up.railway.app/fact-check/submit" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.foxnews.com/politics/trump-admin-warns-42-million-americans-could-lose-food-stamps-shutdown-drags", "mode": "iterative"}' \
  | jq -r '.job_id')

echo "Job ID: $JOB_ID"

# Wait for completion
sleep 300

# Get results
curl -s "https://fact-check-production.up.railway.app/fact-check/$JOB_ID/result" | jq '.'
```

---

## Environment Variables (Backend Configuration)

If you need to configure the fact-check service behavior, these environment variables are available:

```bash
# Enable/disable iterative mode globally
USE_ITERATIVE_SUMMARY=true

# Enable parallel validation (recommended)
ENABLE_PARALLEL_VALIDATION=true

# Tuning parameters
ITER_SUMMARY_TOP_K=5                  # Claims to validate
ITER_SUMMARY_MAX_ITERATIONS=3         # Max refinement passes
ITER_SUMMARY_TIMEOUT=120              # Timeout in seconds
```

---

## Support & Questions

For issues or questions about the fact-check API:
1. Check the service health: `https://fact-check-production.up.railway.app/health`
2. Review logs on Railway dashboard
3. Reference: `docs/exa-summary-migration.md`

---

*Last Updated: October 29, 2025*  
*API Version: 2.1.1*  
*Status: Production Ready ✅*
