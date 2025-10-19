# Fact-Check API Integration Guide

Complete guide for integrating the Fact-Check API as a microservice into your frontend and backend applications.

**Production API Base URL**: `https://fact-check-production.up.railway.app`

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [API Overview](#api-overview)
3. [Frontend Integration](#frontend-integration)
4. [Backend Integration](#backend-integration)
5. [WebSocket Real-Time Updates](#websocket-real-time-updates)
6. [Complete Use Cases](#complete-use-cases)
7. [Error Handling](#error-handling)
8. [Production Best Practices](#production-best-practices)

---

## Quick Start

### Test the API

```bash
# Health check
curl https://fact-check-production.up.railway.app/health

# Submit a fact-check job
curl -X POST https://fact-check-production.up.railway.app/fact-check/submit \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.foxnews.com/politics/article",
    "mode": "standard",
    "generate_image": false,
    "generate_article": true
  }'
```

### Response:
```json
{
  "success": true,
  "job_id": "abc123def456",
  "message": "Fact-check job submitted successfully",
  "status_url": "/fact-check/abc123def456/status",
  "result_url": "/fact-check/abc123def456/result",
  "websocket_url": "/ws/abc123def456",
  "estimated_time_seconds": 60,
  "queue_position": 1
}
```

---

## API Overview

### Base Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | API health check |
| `POST` | `/fact-check/submit` | Submit URL for fact-checking |
| `GET` | `/fact-check/{job_id}/status` | Poll job status |
| `GET` | `/fact-check/{job_id}/result` | Get final results |
| `DELETE` | `/fact-check/{job_id}/cancel` | Cancel a job |
| `GET` | `/queue/stats` | Queue statistics |
| `WS` | `/ws/{job_id}` | Real-time progress updates |

### Validation Modes

1. **`standard`** (Default) - Fast validation (~60s)
2. **`thorough`** - Detailed analysis (~70s)
3. **`summary`** - Validate overall narrative

### Options

- **`generate_image`** (boolean) - Generate editorial cartoon (+10s)
- **`generate_article`** (boolean) - Generate comprehensive article (default: true)

---

## Frontend Integration

### TypeScript Interfaces

```typescript
// types/factcheck.ts

export type ValidationMode = 'standard' | 'thorough' | 'summary';
export type JobStatus = 'queued' | 'started' | 'finished' | 'failed';

export interface FactCheckRequest {
  url: string;
  mode?: ValidationMode;
  generate_image?: boolean;
  generate_article?: boolean;
}

export interface FactCheckSubmitResponse {
  success: boolean;
  job_id: string;
  message: string;
  status_url: string;
  result_url: string;
  websocket_url: string;
  estimated_time_seconds: number;
  queue_position?: number;
}

export interface FactCheckStatus {
  job_id: string;
  status: JobStatus;
  phase?: string;
  progress: number;
  elapsed_time_seconds: number;
  estimated_remaining_seconds?: number;
  article_ready: boolean;
  error_message?: string;
  queue_position?: number;
}

export interface ValidationResult {
  claim: string;
  verdict: string;
  confidence: string;
  evidence_for: string[];
  evidence_against: string[];
}

export interface FactCheckResult {
  job_id: string;
  source_url: string;
  validation_mode: string;
  processing_time_seconds: number;
  summary: string;
  claims_analyzed: number;
  claims_validated: number;
  claims: any[];
  validation_results: ValidationResult[];
  article_data?: any;
  article_text?: string;
  image_url?: string;
  metadata: Record<string, any>;
  costs: Record<string, number>;
}
```

---

### React/Next.js Integration

#### API Client Service

```typescript
// services/factCheckApi.ts

const API_BASE_URL = 'https://fact-check-production.up.railway.app';

export class FactCheckApiClient {
  async submitFactCheck(request: FactCheckRequest): Promise<FactCheckSubmitResponse> {
    const response = await fetch(`${API_BASE_URL}/fact-check/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  async getJobStatus(jobId: string): Promise<FactCheckStatus> {
    const response = await fetch(`${API_BASE_URL}/fact-check/${jobId}/status`);

    if (!response.ok) {
      throw new Error(`Failed to fetch job status: ${response.statusText}`);
    }

    return response.json();
  }

  async getJobResult(jobId: string): Promise<FactCheckResult> {
    const response = await fetch(`${API_BASE_URL}/fact-check/${jobId}/result`);

    if (!response.ok) {
      throw new Error(`Failed to fetch job result: ${response.statusText}`);
    }

    return response.json();
  }

  async cancelJob(jobId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/fact-check/${jobId}/cancel`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Failed to cancel job: ${response.statusText}`);
    }
  }

  // Polling helper with exponential backoff
  async pollJobUntilComplete(
    jobId: string,
    onProgress?: (status: FactCheckStatus) => void,
    maxAttempts = 120,
    initialDelay = 1000
  ): Promise<FactCheckResult> {
    let attempts = 0;
    let delay = initialDelay;

    while (attempts < maxAttempts) {
      const status = await this.getJobStatus(jobId);

      if (onProgress) {
        onProgress(status);
      }

      if (status.status === 'finished') {
        return await this.getJobResult(jobId);
      }

      if (status.status === 'failed') {
        throw new Error(status.error_message || 'Job failed');
      }

      await new Promise(resolve => setTimeout(resolve, delay));

      // Exponential backoff: increase delay up to 5 seconds
      delay = Math.min(delay * 1.2, 5000);
      attempts++;
    }

    throw new Error('Job polling timeout');
  }
}

export const factCheckApi = new FactCheckApiClient();
```

---

#### React Hook - REST Polling Pattern

```typescript
// hooks/useFactCheck.ts

import { useState, useCallback } from 'react';
import { factCheckApi } from '@/services/factCheckApi';

export function useFactCheck() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<FactCheckStatus | null>(null);
  const [result, setResult] = useState<FactCheckResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitAndPoll = useCallback(async (request: FactCheckRequest) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Submit job
      const submission = await factCheckApi.submitFactCheck(request);
      setJobId(submission.job_id);

      // Poll until complete
      const finalResult = await factCheckApi.pollJobUntilComplete(
        submission.job_id,
        (progressStatus) => {
          setStatus(progressStatus);
        }
      );

      setResult(finalResult);
      return finalResult;

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const cancel = useCallback(async () => {
    if (jobId) {
      await factCheckApi.cancelJob(jobId);
      setLoading(false);
      setStatus(null);
    }
  }, [jobId]);

  return {
    jobId,
    status,
    result,
    loading,
    error,
    submitAndPoll,
    cancel,
  };
}
```

---

#### React Component Example

```typescript
// components/FactCheckForm.tsx

import React, { useState } from 'react';
import { useFactCheck } from '@/hooks/useFactCheck';

export function FactCheckForm() {
  const [url, setUrl] = useState('');
  const [mode, setMode] = useState<ValidationMode>('standard');
  const [generateImage, setGenerateImage] = useState(false);

  const { status, result, loading, error, submitAndPoll, cancel } = useFactCheck();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    await submitAndPoll({
      url,
      mode,
      generate_image: generateImage,
      generate_article: true,
    });
  };

  return (
    <div className="fact-check-form">
      <form onSubmit={handleSubmit}>
        <div>
          <label>Article URL:</label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/article"
            required
            disabled={loading}
          />
        </div>

        <div>
          <label>Validation Mode:</label>
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value as ValidationMode)}
            disabled={loading}
          >
            <option value="standard">Standard (Fast)</option>
            <option value="thorough">Thorough (Detailed)</option>
            <option value="summary">Summary (Narrative)</option>
          </select>
        </div>

        <div>
          <label>
            <input
              type="checkbox"
              checked={generateImage}
              onChange={(e) => setGenerateImage(e.target.checked)}
              disabled={loading}
            />
            Generate Editorial Cartoon (+10s)
          </label>
        </div>

        <button type="submit" disabled={loading || !url}>
          {loading ? 'Processing...' : 'Submit Fact-Check'}
        </button>

        {loading && (
          <button type="button" onClick={cancel}>
            Cancel
          </button>
        )}
      </form>

      {/* Progress Display */}
      {status && (
        <div className="progress">
          <h3>Status: {status.status}</h3>
          <p>Phase: {status.phase}</p>
          <progress value={status.progress} max={100} />
          <span>{status.progress}%</span>

          {status.estimated_remaining_seconds && (
            <p>Est. remaining: {status.estimated_remaining_seconds}s</p>
          )}

          {status.article_ready && (
            <p className="success">✓ Article ready!</p>
          )}
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error">
          <h3>Error</h3>
          <p>{error}</p>
        </div>
      )}

      {/* Results Display */}
      {result && (
        <div className="results">
          <h2>Fact-Check Results</h2>
          <p><strong>Summary:</strong> {result.summary}</p>
          <p>Claims Analyzed: {result.claims_analyzed}</p>
          <p>Claims Validated: {result.claims_validated}</p>
          <p>Processing Time: {result.processing_time_seconds}s</p>

          {/* Validation Results */}
          <div className="validation-results">
            <h3>Validation Results</h3>
            {result.validation_results.map((validation, idx) => (
              <div key={idx} className={`claim ${validation.verdict.toLowerCase()}`}>
                <h4>{validation.verdict}</h4>
                <p><strong>Claim:</strong> {validation.claim}</p>
                <p><strong>Confidence:</strong> {validation.confidence}</p>

                {validation.evidence_for.length > 0 && (
                  <div>
                    <strong>Evidence For:</strong>
                    <ul>
                      {validation.evidence_for.map((ev, i) => (
                        <li key={i}>{ev}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {validation.evidence_against.length > 0 && (
                  <div>
                    <strong>Evidence Against:</strong>
                    <ul>
                      {validation.evidence_against.map((ev, i) => (
                        <li key={i}>{ev}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Generated Article */}
          {result.article_text && (
            <div className="article">
              <h3>Generated Article</h3>
              <pre>{result.article_text}</pre>
            </div>
          )}

          {/* Generated Image */}
          {result.image_url && (
            <div className="image">
              <h3>Editorial Cartoon</h3>
              <img src={result.image_url} alt="Fact-check editorial cartoon" />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

---

### Vue.js Integration

```typescript
// composables/useFactCheck.ts

import { ref, computed } from 'vue';
import { factCheckApi } from '@/services/factCheckApi';

export function useFactCheck() {
  const jobId = ref<string | null>(null);
  const status = ref<FactCheckStatus | null>(null);
  const result = ref<FactCheckResult | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const progress = computed(() => status.value?.progress ?? 0);
  const phase = computed(() => status.value?.phase ?? 'pending');

  const submitAndPoll = async (request: FactCheckRequest) => {
    loading.value = true;
    error.value = null;
    result.value = null;

    try {
      const submission = await factCheckApi.submitFactCheck(request);
      jobId.value = submission.job_id;

      const finalResult = await factCheckApi.pollJobUntilComplete(
        submission.job_id,
        (progressStatus) => {
          status.value = progressStatus;
        }
      );

      result.value = finalResult;
      return finalResult;

    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error';
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const cancel = async () => {
    if (jobId.value) {
      await factCheckApi.cancelJob(jobId.value);
      loading.value = false;
      status.value = null;
    }
  };

  return {
    jobId,
    status,
    result,
    loading,
    error,
    progress,
    phase,
    submitAndPoll,
    cancel,
  };
}
```

---

## Backend Integration

### Node.js/Express Proxy

```typescript
// routes/factcheck.ts

import express from 'express';
import axios from 'axios';

const router = express.Router();
const FACT_CHECK_API = 'https://fact-check-production.up.railway.app';

// Submit fact-check (with request logging)
router.post('/submit', async (req, res) => {
  try {
    const { url, mode, generate_image, generate_article } = req.body;

    // Log request for analytics
    console.log(`Fact-check submitted: ${url} (mode: ${mode})`);

    const response = await axios.post(`${FACT_CHECK_API}/fact-check/submit`, {
      url,
      mode: mode || 'standard',
      generate_image: generate_image || false,
      generate_article: generate_article !== false,
    });

    // Store job ID in database for tracking
    await db.factCheckJobs.create({
      jobId: response.data.job_id,
      userId: req.user.id,
      sourceUrl: url,
      mode,
      createdAt: new Date(),
    });

    res.json(response.data);
  } catch (error) {
    console.error('Error submitting fact-check:', error);
    res.status(500).json({ error: 'Failed to submit fact-check' });
  }
});

// Get job status (with caching)
router.get('/status/:jobId', async (req, res) => {
  try {
    const { jobId } = req.params;

    const response = await axios.get(`${FACT_CHECK_API}/fact-check/${jobId}/status`);

    // Cache completed jobs
    if (response.data.status === 'finished') {
      await cache.set(`job:${jobId}:status`, response.data, { ttl: 3600 });
    }

    res.json(response.data);
  } catch (error) {
    console.error('Error fetching status:', error);
    res.status(404).json({ error: 'Job not found' });
  }
});

// Get job result (with database storage)
router.get('/result/:jobId', async (req, res) => {
  try {
    const { jobId } = req.params;

    // Check cache first
    const cached = await cache.get(`job:${jobId}:result`);
    if (cached) {
      return res.json(cached);
    }

    const response = await axios.get(`${FACT_CHECK_API}/fact-check/${jobId}/result`);

    // Store result in database
    await db.factCheckResults.upsert({
      jobId,
      result: response.data,
      completedAt: new Date(),
    });

    // Cache for 1 hour
    await cache.set(`job:${jobId}:result`, response.data, { ttl: 3600 });

    res.json(response.data);
  } catch (error) {
    console.error('Error fetching result:', error);
    res.status(404).json({ error: 'Result not found' });
  }
});

// Webhook handler (for event-driven architecture)
router.post('/webhook/:jobId', async (req, res) => {
  try {
    const { jobId } = req.params;
    const { status, result } = req.body;

    // Update database
    await db.factCheckJobs.update(
      { jobId },
      { status, result, completedAt: new Date() }
    );

    // Notify user via WebSocket/Push notification
    await notifyUser(jobId, { status, result });

    res.json({ success: true });
  } catch (error) {
    console.error('Webhook error:', error);
    res.status(500).json({ error: 'Webhook processing failed' });
  }
});

export default router;
```

---

### Python/FastAPI Integration

```python
# app/services/factcheck.py

import httpx
from typing import Optional, Dict, Any
from app.models import FactCheckRequest, FactCheckResult

FACT_CHECK_API = "https://fact-check-production.up.railway.app"

class FactCheckService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=120.0)

    async def submit_fact_check(
        self,
        url: str,
        mode: str = "standard",
        generate_image: bool = False,
        generate_article: bool = True
    ) -> Dict[str, Any]:
        """Submit a URL for fact-checking."""
        response = await self.client.post(
            f"{FACT_CHECK_API}/fact-check/submit",
            json={
                "url": url,
                "mode": mode,
                "generate_image": generate_image,
                "generate_article": generate_article,
            }
        )
        response.raise_for_status()
        return response.json()

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status."""
        response = await self.client.get(
            f"{FACT_CHECK_API}/fact-check/{job_id}/status"
        )
        response.raise_for_status()
        return response.json()

    async def get_job_result(self, job_id: str) -> Dict[str, Any]:
        """Get job result."""
        response = await self.client.get(
            f"{FACT_CHECK_API}/fact-check/{job_id}/result"
        )
        response.raise_for_status()
        return response.json()

    async def poll_until_complete(
        self,
        job_id: str,
        max_attempts: int = 120,
        delay: float = 1.0
    ) -> Dict[str, Any]:
        """Poll job until complete."""
        import asyncio

        for attempt in range(max_attempts):
            status = await self.get_job_status(job_id)

            if status["status"] == "finished":
                return await self.get_job_result(job_id)

            if status["status"] == "failed":
                raise Exception(f"Job failed: {status.get('error_message')}")

            await asyncio.sleep(delay)

        raise TimeoutError("Job polling timeout")

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

# Usage in FastAPI endpoint
from fastapi import APIRouter, HTTPException

router = APIRouter()
factcheck_service = FactCheckService()

@router.post("/factcheck/submit")
async def submit_factcheck(request: FactCheckRequest):
    try:
        submission = await factcheck_service.submit_fact_check(
            url=str(request.url),
            mode=request.mode,
            generate_image=request.generate_image,
            generate_article=request.generate_article,
        )
        return submission
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/factcheck/{job_id}")
async def get_factcheck_result(job_id: str):
    try:
        result = await factcheck_service.poll_until_complete(job_id)
        return result
    except TimeoutError:
        raise HTTPException(status_code=408, detail="Job timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## WebSocket Real-Time Updates

### JavaScript WebSocket Client

```typescript
// services/factCheckWebSocket.ts

export class FactCheckWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect(
    jobId: string,
    onMessage: (data: FactCheckStatus) => void,
    onError?: (error: Event) => void,
    onClose?: () => void
  ): void {
    const wsUrl = `wss://fact-check-production.up.railway.app/ws/${jobId}`;

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log(`WebSocket connected for job ${jobId}`);
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as FactCheckStatus;
      onMessage(data);

      // Auto-close when job is complete
      if (data.status === 'finished' || data.status === 'failed') {
        this.close();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (onError) onError(error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket closed');
      if (onClose) onClose();

      // Auto-reconnect logic
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);

        setTimeout(() => {
          console.log(`Reconnecting (attempt ${this.reconnectAttempts})...`);
          this.connect(jobId, onMessage, onError, onClose);
        }, delay);
      }
    };
  }

  close(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

---

### React Hook with WebSocket

```typescript
// hooks/useFactCheckWebSocket.ts

import { useState, useEffect, useCallback, useRef } from 'react';
import { FactCheckWebSocket } from '@/services/factCheckWebSocket';

export function useFactCheckWebSocket(jobId: string | null) {
  const [status, setStatus] = useState<FactCheckStatus | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<FactCheckWebSocket | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const ws = new FactCheckWebSocket();
    wsRef.current = ws;

    ws.connect(
      jobId,
      (data) => {
        setStatus(data);
        setConnected(true);
      },
      (error) => {
        setError('WebSocket connection error');
        setConnected(false);
      },
      () => {
        setConnected(false);
      }
    );

    return () => {
      ws.close();
    };
  }, [jobId]);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
  }, []);

  return {
    status,
    connected,
    error,
    disconnect,
  };
}
```

---

## Complete Use Cases

### Use Case 1: Standard Fact-Check with Polling

```bash
# Step 1: Submit job
curl -X POST https://fact-check-production.up.railway.app/fact-check/submit \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.example.com/article",
    "mode": "standard",
    "generate_image": false,
    "generate_article": true
  }'

# Response: { "job_id": "abc123", ... }

# Step 2: Poll status (repeat every 2 seconds)
curl https://fact-check-production.up.railway.app/fact-check/abc123/status

# Step 3: Get result when status=finished
curl https://fact-check-production.up.railway.app/fact-check/abc123/result
```

---

### Use Case 2: Thorough Mode with Image Generation

```typescript
const result = await factCheckApi.submitFactCheck({
  url: 'https://www.foxnews.com/politics/article',
  mode: 'thorough',
  generate_image: true,
  generate_article: true,
});

// Poll until complete
const finalResult = await factCheckApi.pollJobUntilComplete(
  result.job_id,
  (status) => {
    console.log(`Progress: ${status.progress}% - Phase: ${status.phase}`);

    if (status.article_ready) {
      console.log('Article is ready! Image generation in progress...');
    }
  }
);

console.log('Image URL:', finalResult.image_url);
console.log('Article:', finalResult.article_text);
```

---

### Use Case 3: Summary Mode (Validate Overall Narrative)

```typescript
// Validate if the article's overall story is accurate
const result = await factCheckApi.submitFactCheck({
  url: 'https://www.cnn.com/politics/article',
  mode: 'summary',
  generate_image: false,
  generate_article: true,
});

const finalResult = await factCheckApi.pollJobUntilComplete(result.job_id);

// Summary mode validates the overall narrative, not individual claims
console.log('Narrative Summary:', finalResult.summary);
console.log('Overall Verdict:', finalResult.validation_results[0].verdict);
```

---

### Use Case 4: Batch Processing Multiple URLs

```typescript
// Process multiple articles concurrently
const urls = [
  'https://example.com/article1',
  'https://example.com/article2',
  'https://example.com/article3',
];

const submissions = await Promise.all(
  urls.map(url =>
    factCheckApi.submitFactCheck({
      url,
      mode: 'standard',
      generate_image: false,
      generate_article: true,
    })
  )
);

// Poll all jobs
const results = await Promise.all(
  submissions.map(sub =>
    factCheckApi.pollJobUntilComplete(sub.job_id)
  )
);

console.log('All results:', results);
```

---

## Error Handling

### Retry Strategy

```typescript
class FactCheckApiWithRetry extends FactCheckApiClient {
  async submitWithRetry(
    request: FactCheckRequest,
    maxRetries = 3
  ): Promise<FactCheckSubmitResponse> {
    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await this.submitFactCheck(request);
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');

        if (attempt < maxRetries) {
          const delay = 1000 * Math.pow(2, attempt);
          console.log(`Retry attempt ${attempt} after ${delay}ms`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }

    throw new Error(`Failed after ${maxRetries} attempts: ${lastError?.message}`);
  }
}
```

---

### Error Types and Handling

```typescript
interface ApiError {
  success: false;
  error: string;
  error_type: string;
  timestamp: string;
  job_id?: string;
}

function handleFactCheckError(error: any) {
  if (error.response) {
    // API error response
    const apiError = error.response.data as ApiError;

    switch (apiError.error_type) {
      case 'http_error':
        return `HTTP Error: ${apiError.error}`;

      case 'validation_error':
        return `Validation failed: ${apiError.error}`;

      case 'timeout_error':
        return 'Job took too long to complete. Please try again.';

      case 'server_error':
        return 'Server error. Please try again later.';

      default:
        return `Error: ${apiError.error}`;
    }
  }

  if (error.request) {
    // Network error
    return 'Network error. Please check your connection.';
  }

  return 'Unknown error occurred.';
}
```

---

## Production Best Practices

### 1. Rate Limiting

```typescript
class RateLimitedFactCheckApi extends FactCheckApiClient {
  private requestQueue: Promise<any>[] = [];
  private maxConcurrent = 3;

  async submitFactCheck(request: FactCheckRequest): Promise<FactCheckSubmitResponse> {
    // Wait if queue is full
    while (this.requestQueue.length >= this.maxConcurrent) {
      await Promise.race(this.requestQueue);
    }

    const promise = super.submitFactCheck(request);
    this.requestQueue.push(promise);

    promise.finally(() => {
      const index = this.requestQueue.indexOf(promise);
      if (index > -1) {
        this.requestQueue.splice(index, 1);
      }
    });

    return promise;
  }
}
```

---

### 2. Caching Strategy

```typescript
class CachedFactCheckApi extends FactCheckApiClient {
  private cache = new Map<string, any>();
  private cacheTtl = 3600000; // 1 hour

  async getJobResult(jobId: string): Promise<FactCheckResult> {
    const cacheKey = `result:${jobId}`;
    const cached = this.cache.get(cacheKey);

    if (cached && Date.now() - cached.timestamp < this.cacheTtl) {
      return cached.data;
    }

    const result = await super.getJobResult(jobId);

    this.cache.set(cacheKey, {
      data: result,
      timestamp: Date.now(),
    });

    return result;
  }
}
```

---

### 3. Monitoring & Logging

```typescript
class MonitoredFactCheckApi extends FactCheckApiClient {
  async submitFactCheck(request: FactCheckRequest): Promise<FactCheckSubmitResponse> {
    const startTime = Date.now();

    try {
      const result = await super.submitFactCheck(request);

      // Log success metric
      analytics.track('factcheck_submitted', {
        mode: request.mode,
        generate_image: request.generate_image,
        duration: Date.now() - startTime,
      });

      return result;

    } catch (error) {
      // Log error metric
      analytics.track('factcheck_error', {
        mode: request.mode,
        error: error instanceof Error ? error.message : 'Unknown',
        duration: Date.now() - startTime,
      });

      throw error;
    }
  }
}
```

---

### 4. CORS Configuration

If you're hosting a backend proxy, configure CORS properly:

```typescript
// Express.js
import cors from 'cors';

app.use(cors({
  origin: [
    'https://yourdomain.com',
    'https://app.yourdomain.com',
  ],
  credentials: true,
  methods: ['GET', 'POST', 'DELETE'],
}));
```

---

### 5. Environment Variables

```bash
# .env

# API Configuration
FACT_CHECK_API_URL=https://fact-check-production.up.railway.app
FACT_CHECK_TIMEOUT=120000

# Caching
CACHE_TTL=3600000

# Rate Limiting
MAX_CONCURRENT_REQUESTS=3
RATE_LIMIT_PER_MINUTE=10

# Monitoring
ANALYTICS_ENABLED=true
LOG_LEVEL=info
```

---

## Testing & Development

### Postman Collection

Import this into Postman for quick testing:

```json
{
  "info": {
    "name": "Fact-Check API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Submit Standard Fact-Check",
      "request": {
        "method": "POST",
        "header": [{ "key": "Content-Type", "value": "application/json" }],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"url\": \"https://www.example.com/article\",\n  \"mode\": \"standard\",\n  \"generate_image\": false,\n  \"generate_article\": true\n}"
        },
        "url": {
          "raw": "https://fact-check-production.up.railway.app/fact-check/submit",
          "protocol": "https",
          "host": ["fact-check-production", "up", "railway", "app"],
          "path": ["fact-check", "submit"]
        }
      }
    }
  ]
}
```

---

### Mock Data for Testing

```typescript
export const mockFactCheckResult: FactCheckResult = {
  job_id: 'mock-123',
  source_url: 'https://example.com/article',
  validation_mode: 'standard',
  processing_time_seconds: 62.5,
  timestamp: new Date(),
  summary: 'Analyzed 1 claims: 1 VERIFIED',
  claims_analyzed: 1,
  claims_validated: 1,
  claims: [],
  validation_results: [
    {
      claim: 'The unemployment rate is at a record low.',
      verdict: 'VERIFIED',
      confidence: 'high',
      evidence_for: [
        'Bureau of Labor Statistics confirms record low unemployment',
        'Historical data supports this claim'
      ],
      evidence_against: []
    }
  ],
  article_data: {},
  article_text: 'Fact-check article text...',
  image_url: 'https://example.com/image.png',
  metadata: {},
  costs: {
    total: 0.05,
    claim_extraction: 0.001,
    evidence_search: 0.002,
    validation: 0.002,
    article_generation: 0.003,
    image_generation: 0.04
  }
};
```

---

## Additional Resources

- **API Documentation**: https://fact-check-production.up.railway.app/docs
- **Health Check**: https://fact-check-production.up.railway.app/health
- **Queue Stats**: https://fact-check-production.up.railway.app/queue/stats

---

## Support

For questions or issues:
- Check the API health endpoint
- Review error messages for specific error types
- Contact the backend team for API access issues

---

**Last Updated**: January 2025  
**API Version**: 1.0.0
