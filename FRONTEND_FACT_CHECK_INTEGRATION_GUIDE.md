# Frontend Fact-Check Integration Guide

**Complete guide for integrating fact-check data into your React/Next.js frontend application**

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Data Structure](#data-structure)
4. [Backend API Endpoints](#backend-api-endpoints)
5. [External Fact-Check API](#external-fact-check-api)
6. [Real API Response Examples](#real-api-response-examples)
7. [TypeScript Interfaces](#typescript-interfaces)
8. [Frontend Integration Examples](#frontend-integration-examples)
9. [UI Component Recommendations](#ui-component-recommendations)
10. [Best Practices](#best-practices)

---

## Overview

The fact-check system uses a **microservice architecture** where:

- **External API** (Railway) performs AI-powered fact-checking
- **Your Backend** stores results in database for fast queries
- **Frontend** can access data from either source

### Key Features

✅ **Automatic Fact-Checking** - All new articles are fact-checked automatically  
✅ **Credibility Scores** - 0-100 score based on validation results  
✅ **Detailed Verdicts** - TRUE, FALSE, MISLEADING, UNVERIFIED, etc.  
✅ **Multi-Source Verification** - Claims verified against multiple sources  
✅ **Real-time Status** - Track fact-check progress via API or WebSocket  

---

## Architecture

```
┌─────────────────┐
│   Frontend      │
│   (React/Next)  │
└────────┬────────┘
         │
         ├─────────────────┬─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌────────────────┐  ┌──────────────┐  ┌──────────────┐
│ Your Backend   │  │ Railway API  │  │ WebSocket    │
│ (Cached Data)  │  │ (Real-time)  │  │ (Live Status)│
└────────────────┘  └──────────────┘  └──────────────┘
         │                 │
         ▼                 │
┌────────────────┐         │
│  Supabase      │◀────────┘
│  PostgreSQL    │
└────────────────┘
```

### Data Flow

1. **New Article Created** → Background task triggered
2. **Backend Submits** to Railway API → Gets `job_id`
3. **Backend Polls** Railway API every 5s → Gets progress updates
4. **Results Stored** in Supabase → Article updated with credibility score
5. **Frontend Queries** backend → Gets cached fact-check data

---

## Data Structure

### Database Schema: `article_fact_checks`

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `article_id` | UUID | Foreign key to articles (1:1, cascade delete) |
| `job_id` | String | Railway API job identifier |
| `verdict` | String | PRIMARY_VERDICT (TRUE, FALSE, MISLEADING, etc.) |
| `credibility_score` | Integer | 0-100 calculated score |
| `confidence` | Decimal | 0.00-1.00 AI confidence level |
| `summary` | Text | Brief fact-check summary |
| `claims_analyzed` | Integer | Total claims extracted |
| `claims_true` | Integer | Claims verified as true |
| `claims_false` | Integer | Claims verified as false |
| `claims_misleading` | Integer | Claims marked misleading |
| `claims_unverified` | Integer | Claims without verification |
| `num_sources` | Integer | Sources consulted |
| `source_consensus` | String | STRONG_AGREEMENT, MIXED, etc. |
| `validation_results` | JSONB | Full API response |
| `processing_time_seconds` | Integer | Time to complete |
| `fact_checked_at` | Timestamp | When fact-check completed |

### Denormalized Fields on `articles` Table

| Field | Type | Description |
|-------|------|-------------|
| `fact_check_score` | Integer | Credibility score (indexed) |
| `fact_check_verdict` | String | Verdict (indexed) |
| `fact_checked_at` | Timestamp | Completion time (indexed) |

---

## Backend API Endpoints

### Your Backend (Cached Data)

#### 1. Get All Articles (with Fact-Check Data)

```http
GET /api/v1/articles
```

**Query Parameters:**
- `category` - Filter by category (general, politics, us, world, science)
- `sort_by` - Sort order (hot, new, top)
- `time_range` - Time filter (hour, day, week, month, year, all)
- `page` - Page number (default: 1)
- `page_size` - Items per page (1-100, default: 25)

**Response:**
```json
{
  "articles": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Article Title",
      "url": "https://example.com/article",
      "description": "Article description...",
      "author": "John Doe",
      "thumbnail_url": "https://example.com/image.jpg",
      "category": "politics",
      "published_date": "2025-10-18T12:00:00Z",
      "created_at": "2025-10-18T12:05:00Z",
      "vote_score": 245,
      "vote_count": 312,
      "comment_count": 48,
      "tags": ["politics", "international"],
      
      // Fact-check fields (denormalized for performance)
      "fact_check_score": 87,           // ← Credibility score
      "fact_check_verdict": "TRUE",     // ← Verdict
      "fact_checked_at": "2025-10-18T12:07:00Z",  // ← Timestamp
      
      "user_vote": 1  // User's vote (-1, 0, 1) - if authenticated
    }
  ],
  "pagination": {
    "current_page": 1,
    "page_size": 25,
    "total_items": 523,
    "total_pages": 21,
    "has_next": true,
    "has_previous": false
  }
}
```

#### 2. Get Single Article (with Fact-Check Data)

```http
GET /api/v1/articles/{article_id}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "rss_source_id": "...",
  "title": "Article Title",
  "url": "https://example.com/article",
  "description": "Full description...",
  "author": "Author Name",
  "thumbnail_url": "https://...",
  "category": "politics",
  "published_date": "2025-10-18T12:00:00Z",
  "created_at": "2025-10-18T12:05:00Z",
  "vote_score": 245,
  "vote_count": 312,
  "comment_count": 48,
  "tags": ["tag1", "tag2"],
  "fact_check_score": 87,
  "fact_check_verdict": "TRUE",
  "fact_checked_at": "2025-10-18T12:07:00Z",
  "user_vote": null
}
```

#### 3. Filter Articles by Credibility Score

```http
GET /api/v1/articles?sort_by=top&time_range=day
```

Then filter client-side:
```javascript
const highCredibility = articles.filter(a => a.fact_check_score >= 80);
const lowCredibility = articles.filter(a => a.fact_check_score < 50);
const pending = articles.filter(a => !a.fact_checked_at);
```

---

## External Fact-Check API

### Railway API (Real-time Status)

**Base URL:** `https://fact-check-production.up.railway.app`

#### 1. Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-19T14:20:21.885928",
  "services": {
    "redis": "healthy",
    "queue": "healthy"
  },
  "metrics": {
    "queue_length": 0
  }
}
```

#### 2. Submit Fact-Check Job

```http
POST /fact-check/submit
Content-Type: application/json

{
  "url": "https://www.example.com/article",
  "mode": "summary",
  "generate_image": false,
  "generate_article": true
}
```

**Response:**
```json
{
  "success": true,
  "job_id": "9aa51885-c336-4de0-aa17-88a1944379c7",
  "message": "Fact-check job submitted successfully",
  "status_url": "/fact-check/9aa51885-c336-4de0-aa17-88a1944379c7/status",
  "result_url": "/fact-check/9aa51885-c336-4de0-aa17-88a1944379c7/result",
  "websocket_url": "/ws/9aa51885-c336-4de0-aa17-88a1944379c7",
  "estimated_time_seconds": 60,
  "queue_position": null
}
```

#### 3. Check Job Status

```http
GET /fact-check/{job_id}/status
```

**Response (In Progress):**
```json
{
  "job_id": "9aa51885-c336-4de0-aa17-88a1944379c7",
  "status": "started",
  "phase": "extraction",
  "progress": 45,
  "elapsed_time_seconds": 25.8,
  "estimated_remaining_seconds": 35,
  "article_ready": false,
  "error_message": null,
  "queue_position": null
}
```

**Response (Complete):**
```json
{
  "job_id": "9aa51885-c336-4de0-aa17-88a1944379c7",
  "status": "finished",
  "phase": "complete",
  "progress": 100,
  "elapsed_time_seconds": 154.08,
  "estimated_remaining_seconds": 0,
  "article_ready": true,
  "error_message": null,
  "queue_position": null
}
```

#### 4. Get Job Result

```http
GET /fact-check/{job_id}/result
```

**Response:** See [Real API Response Example](#real-api-response-examples) below

---

## Real API Response Examples

### Complete Fact-Check Result (Actual API Response)

Here's a **real response** from the Railway API for the BBC article about UK-Mauritius Chagos Islands deal:

```json
{
  "job_id": "9aa51885-c336-4de0-aa17-88a1944379c7",
  "source_url": "https://www.bbc.com/news/articles/c98ynejg4l5o",
  "validation_mode": "summary",
  "processing_time_seconds": 137.68,
  "timestamp": "2025-10-19T14:22:54.919896Z",
  
  // HIGH-LEVEL SUMMARY
  "summary": "Analyzed 1 claims: 1 UNKNOWN",
  "claims_analyzed": 1,
  "claims_validated": 1,
  
  // EXTRACTED CLAIMS
  "claims": [
    {
      "claim": "The UK announced on 3 October 2024, its decision to hand over sovereignty of the Chagos Islands to Mauritius...",
      "risk_level": "HIGH",
      "category": "Narrative Summary",
      "context": [],
      "actors": [
        {
          "name": "Keir Starmer",
          "role": "UK Prime Minister"
        },
        {
          "name": "Pravind Jugnauth",
          "role": "Mauritius Prime Minister"
        }
        // ... more actors
      ]
    }
  ],
  
  // VALIDATION RESULTS
  "validation_results": [
    {
      "claim": "The UK announced on 3 October 2024...",
      "risk_level": "HIGH",
      "category": "Narrative Summary",
      "validation_output": {
        "verdict": "TRUE",               // ← PRIMARY VERDICT
        "confidence": 0.9,                // ← AI CONFIDENCE
        "summary": "The UK did announce its decision to cede sovereignty...",
        
        // EVIDENCE
        "key_evidence": {
          "supporting": [
            "The UK agreed to cede sovereignty of the Chagos Islands to Mauritius on 3 October 2024...",
            "The deal, referred to as the United Kingdom–Mauritius Joint Statement (UKMJS)...",
            "Mauritius agreed to lease Diego Garcia to Britain for a renewable 99 years..."
          ],
          "contradicting": [],
          "context": [
            "Negotiations for the handover began in 2022..."
          ]
        },
        
        // SOURCE ANALYSIS
        "source_analysis": {
          "most_credible_sources": [1, 2, 3],
          "source_consensus": "STRONG_AGREEMENT",
          "evidence_quality": "HIGH"
        },
        
        // REFERENCES (8 sources)
        "references": [
          {
            "citation_id": 1,
            "title": "The Devil Will Be in the Details...",
            "url": "https://www.rand.org/pubs/commentary/2025/01/...",
            "source": "RAND Corporation",
            "author": "Benjamin J. Sacks",
            "date": "2025-01-21",
            "type": "general",
            "relevance": "Confirms the date of the agreement...",
            "credibility": "HIGH"
          }
          // ... 7 more references
        ],
        
        "timestamp": "2025-10-19T14:22:16.614032",
        "model": "gemini-2.5-flash",
        "validation_mode": "standard",
        "cost": 0.039895,
        "token_usage": {
          "prompt_tokens": 113300,
          "candidates_tokens": 2362,
          "total_tokens": 121728
        }
      },
      
      "verdict": "TRUE",
      "confidence": 0.9,
      "summary": "The UK did announce its decision to cede sovereignty of the Chagos Islands to Mauritius on 3 October 2024...",
      "evidence_found": true,
      "num_sources": 25,
      "search_breakdown": {
        "news": 5,
        "research": 10,
        "general": 5,
        "historical": 5
      },
      "search_timestamp": "2025-10-19T14:21:21.286929",
      "validation_timestamp": "2025-10-19T14:22:16.614032"
    }
  ],
  
  // GENERATED ARTICLE DATA
  "article_data": {
    "article_metadata": {
      "headline": "Fact Check: UK-Mauritius Chagos Islands Sovereignty Deal Verified",
      "subheadline": "Examining claims about the historic agreement...",
      "lead_paragraph": "This fact-checking article investigates claims...",
      "author": "Fact Check Team",
      "publication_date": "2024-10-04",
      "fact_check_type": "claim_verification",
      "category": "Politics",
      "urgency_level": "HIGH",
      "public_impact_score": 9,
      "word_count": 1350,
      "reading_time_minutes": 7
    },
    
    "executive_summary": {
      "claims_checked": 1,
      "verdicts_summary": {
        "true": 1,
        "false": 0,
        "misinformation": 0,
        "misleading": 0,
        "unverified": 0
      },
      "key_findings": [
        "The UK formally announced its decision to transfer sovereignty of the Chagos Islands to Mauritius on October 3, 2024.",
        "The initial agreement ensures the US-UK military base on Diego Garcia remains operational for an initial 99-year period.",
        "Mauritius gains the right to resettle former inhabitants on other Chagos Islands, excluding Diego Garcia."
      ],
      "bottom_line": "Claims about the UK-Mauritius Chagos Islands deal... are confirmed as true..."
    },
    
    "claim_analysis_sections": [
      {
        "claim_id": "chagos_sovereignty_deal_2024",
        "claim_text": "The UK announced on 3 October 2024...",
        "verdict": "TRUE",
        "verdict_icon": "✓",
        "confidence_level": 0.9,
        "importance": "HIGH",
        "evidence_for": [...],
        "evidence_against": [],
        "context_needed": [...],
        "expert_analysis": {...},
        "public_impact": {...}
      }
    ],
    
    "references": [
      {
        "citation_number": 1,
        "full_citation": "Joint Statement by UK Prime Minister Keir Starmer...",
        "url": "https://www.gov.uk/...",
        "access_date": "2024-10-04",
        "source_type": "government",
        "credibility_rating": "HIGH",
        "relevance_note": "Primary source confirming the agreement..."
      }
    ]
  },
  
  // ARTICLE TEXT (Markdown)
  "article_text": "# Fact Check: UK-Mauritius Chagos Islands Sovereignty Deal Verified\n\n## Examining claims...\n\n...",
  
  "image_url": null,
  
  "metadata": {
    "mode": "summary",
    "generate_image": false,
    "generate_article": true,
    "is_summary_mode": true
  },
  
  "costs": {
    "claim_extraction": 0.001,
    "evidence_search": 0.002,
    "validation": 0.002,
    "article_generation": 0.003,
    "image_generation": 0,
    "total": 0.008
  }
}
```

### Key Fields for Frontend UI

| Field Path | Description | Example Value |
|------------|-------------|---------------|
| `validation_results[0].verdict` | Primary verdict | `"TRUE"` |
| `validation_results[0].confidence` | AI confidence | `0.9` |
| `validation_results[0].summary` | Short summary | `"The UK did announce..."` |
| `validation_results[0].key_evidence.supporting` | Evidence array | `[...]` |
| `validation_results[0].source_analysis.source_consensus` | Source agreement | `"STRONG_AGREEMENT"` |
| `validation_results[0].num_sources` | Sources count | `25` |
| `article_data.executive_summary.bottom_line` | Bottom line | `"Claims are confirmed..."` |
| `processing_time_seconds` | Time taken | `137.68` |

---

## TypeScript Interfaces

```typescript
// types/factcheck.ts

export type Verdict = 
  | 'TRUE' 
  | 'FALSE' 
  | 'MISLEADING' 
  | 'UNVERIFIED' 
  | 'MISINFORMATION'
  | 'PENDING'
  | 'ERROR';

export type SourceConsensus = 
  | 'STRONG_AGREEMENT' 
  | 'MODERATE_AGREEMENT' 
  | 'MIXED' 
  | 'WEAK_AGREEMENT';

// Denormalized fields on Article
export interface Article {
  id: string;
  title: string;
  url: string;
  description: string;
  author: string | null;
  thumbnail_url: string | null;
  category: string;
  published_date: string;
  created_at: string;
  vote_score: number;
  vote_count: number;
  comment_count: number;
  tags: string[];
  
  // Fact-check fields (from database)
  fact_check_score: number | null;      // 0-100
  fact_check_verdict: Verdict | null;
  fact_checked_at: string | null;
  
  user_vote: number | null;  // -1, 0, 1
}

// Full fact-check details (from Railway API or database)
export interface FactCheckResult {
  job_id: string;
  source_url: string;
  validation_mode: string;
  processing_time_seconds: number;
  timestamp: string;
  
  summary: string;
  claims_analyzed: number;
  claims_validated: number;
  
  validation_results: ValidationResult[];
  article_data: ArticleData;
  article_text: string;
  
  metadata: {
    mode: string;
    generate_image: boolean;
    generate_article: boolean;
  };
  
  costs: {
    total: number;
  };
}

export interface ValidationResult {
  claim: string;
  verdict: Verdict;
  confidence: number;
  summary: string;
  evidence_found: boolean;
  num_sources: number;
  
  validation_output: {
    key_evidence: {
      supporting: string[];
      contradicting: string[];
      context: string[];
    };
    source_analysis: {
      most_credible_sources: number[];
      source_consensus: SourceConsensus;
      evidence_quality: 'HIGH' | 'MEDIUM' | 'LOW';
    };
    references: Reference[];
  };
}

export interface Reference {
  citation_id: number;
  title: string;
  url: string;
  source: string;
  author: string | null;
  date: string;
  type: string;
  relevance: string;
  credibility: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface ArticleData {
  article_metadata: {
    headline: string;
    subheadline: string;
    lead_paragraph: string;
    author: string;
    publication_date: string;
    category: string;
    urgency_level: string;
    public_impact_score: number;
    word_count: number;
    reading_time_minutes: number;
  };
  
  executive_summary: {
    claims_checked: number;
    verdicts_summary: Record<string, number>;
    key_findings: string[];
    bottom_line: string;
  };
  
  references: Reference[];
}
```

---

## Frontend Integration Examples

### 1. Article Card with Credibility Badge

```typescript
// components/ArticleCard.tsx

import { Article } from '@/types/factcheck';

interface ArticleCardProps {
  article: Article;
}

export function ArticleCard({ article }: ArticleCardProps) {
  const getCredibilityColor = (score: number | null) => {
    if (score === null) return 'gray';
    if (score >= 80) return 'green';
    if (score >= 60) return 'yellow';
    if (score >= 40) return 'orange';
    return 'red';
  };
  
  const getVerdictIcon = (verdict: string | null) => {
    switch (verdict) {
      case 'TRUE': return '✓';
      case 'FALSE': return '✗';
      case 'MISLEADING': return '⚠';
      case 'UNVERIFIED': return '?';
      default: return '⏳';
    }
  };
  
  return (
    <div className="article-card">
      <div className="article-header">
        <h2>{article.title}</h2>
        
        {/* Credibility Badge */}
        {article.fact_check_score !== null && (
          <div 
            className={`credibility-badge ${getCredibilityColor(article.fact_check_score)}`}
            title={`Credibility Score: ${article.fact_check_score}/100`}
          >
            <span className="icon">{getVerdictIcon(article.fact_check_verdict)}</span>
            <span className="score">{article.fact_check_score}</span>
          </div>
        )}
        
        {/* Pending Fact-Check */}
        {article.fact_check_score === null && (
          <div className="credibility-badge pending">
            <span>⏳ Checking...</span>
          </div>
        )}
      </div>
      
      <p className="description">{article.description}</p>
      
      <div className="article-meta">
        <span>👍 {article.vote_score}</span>
        <span>💬 {article.comment_count}</span>
        {article.fact_checked_at && (
          <span title="Fact-checked">
            ✓ Verified {new Date(article.fact_checked_at).toLocaleDateString()}
          </span>
        )}
      </div>
    </div>
  );
}
```

### 2. Filter Articles by Credibility

```typescript
// hooks/useFactCheckFilters.ts

import { useState, useMemo } from 'react';
import { Article } from '@/types/factcheck';

export function useFactCheckFilters(articles: Article[]) {
  const [credibilityFilter, setCredibilityFilter] = useState<'all' | 'high' | 'medium' | 'low' | 'pending'>('all');
  const [verdictFilter, setVerdictFilter] = useState<string | null>(null);
  
  const filteredArticles = useMemo(() => {
    let filtered = [...articles];
    
    // Filter by credibility score
    if (credibilityFilter !== 'all') {
      filtered = filtered.filter(article => {
        const score = article.fact_check_score;
        
        switch (credibilityFilter) {
          case 'high':
            return score !== null && score >= 80;
          case 'medium':
            return score !== null && score >= 60 && score < 80;
          case 'low':
            return score !== null && score < 60;
          case 'pending':
            return score === null;
          default:
            return true;
        }
      });
    }
    
    // Filter by verdict
    if (verdictFilter) {
      filtered = filtered.filter(article => 
        article.fact_check_verdict === verdictFilter
      );
    }
    
    return filtered;
  }, [articles, credibilityFilter, verdictFilter]);
  
  return {
    filteredArticles,
    credibilityFilter,
    setCredibilityFilter,
    verdictFilter,
    setVerdictFilter
  };
}
```

### 3. Fetch Fact-Check Details

```typescript
// services/factCheckApi.ts

const RAILWAY_API = 'https://fact-check-production.up.railway.app';

export class FactCheckAPI {
  async getJobStatus(jobId: string) {
    const response = await fetch(`${RAILWAY_API}/fact-check/${jobId}/status`);
    if (!response.ok) throw new Error('Failed to fetch status');
    return response.json();
  }
  
  async getJobResult(jobId: string): Promise<FactCheckResult> {
    const response = await fetch(`${RAILWAY_API}/fact-check/${jobId}/result`);
    if (!response.ok) throw new Error('Failed to fetch result');
    return response.json();
  }
  
  async submitFactCheck(url: string): Promise<{ job_id: string }> {
    const response = await fetch(`${RAILWAY_API}/fact-check/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url,
        mode: 'summary',
        generate_image: false,
        generate_article: true
      })
    });
    
    if (!response.ok) throw new Error('Failed to submit');
    return response.json();
  }
}
```

### 4. Display Fact-Check Details Modal

```typescript
// components/FactCheckModal.tsx

import { FactCheckResult } from '@/types/factcheck';

interface FactCheckModalProps {
  result: FactCheckResult;
  onClose: () => void;
}

export function FactCheckModal({ result, onClose }: FactCheckModalProps) {
  const validation = result.validation_results[0];
  
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <h2>Fact-Check Report</h2>
        
        {/* Verdict */}
        <div className="verdict-section">
          <span className={`verdict-badge ${validation.verdict.toLowerCase()}`}>
            {validation.verdict}
          </span>
          <span className="confidence">
            Confidence: {(validation.confidence * 100).toFixed(0)}%
          </span>
        </div>
        
        {/* Summary */}
        <div className="summary">
          <h3>Summary</h3>
          <p>{validation.summary}</p>
        </div>
        
        {/* Evidence */}
        <div className="evidence">
          <h3>Supporting Evidence</h3>
          <ul>
            {validation.validation_output.key_evidence.supporting.map((evidence, i) => (
              <li key={i}>{evidence}</li>
            ))}
          </ul>
        </div>
        
        {/* Sources */}
        <div className="sources">
          <h3>Sources Consulted ({validation.num_sources})</h3>
          <div className="source-metrics">
            <span>Consensus: {validation.validation_output.source_analysis.source_consensus}</span>
            <span>Quality: {validation.validation_output.source_analysis.evidence_quality}</span>
          </div>
          
          <ul className="references">
            {validation.validation_output.references.slice(0, 5).map(ref => (
              <li key={ref.citation_id}>
                <a href={ref.url} target="_blank" rel="noopener noreferrer">
                  [{ref.citation_id}] {ref.title}
                </a>
                <span className="source-meta">
                  {ref.source} • {ref.credibility}
                </span>
              </li>
            ))}
          </ul>
        </div>
        
        <button onClick={onClose}>Close</button>
      </div>
    </div>
  );
}
```

---

## UI Component Recommendations

### 1. Credibility Badge

**Where:** Article cards, article detail page  
**Display:**
- Score 80-100: Green checkmark ✓
- Score 60-79: Yellow warning ⚠
- Score 40-59: Orange caution ⚠
- Score 0-39: Red cross ✗
- Pending: Gray clock ⏳

### 2. Filter Controls

```typescript
<select onChange={e => setCredibilityFilter(e.target.value)}>
  <option value="all">All Articles</option>
  <option value="high">High Credibility (80+)</option>
  <option value="medium">Medium Credibility (60-79)</option>
  <option value="low">Low Credibility (&lt;60)</option>
  <option value="pending">Pending Fact-Check</option>
</select>

<select onChange={e => setVerdictFilter(e.target.value)}>
  <option value="">All Verdicts</option>
  <option value="TRUE">✓ True</option>
  <option value="FALSE">✗ False</option>
  <option value="MISLEADING">⚠ Misleading</option>
  <option value="UNVERIFIED">? Unverified</option>
</select>
```

### 3. Article Detail Sidebar

```html
<aside class="fact-check-sidebar">
  <h3>Fact-Check Report</h3>
  
  <div class="score-display">
    <div class="score-circle">87</div>
    <span class="verdict">TRUE</span>
  </div>
  
  <div class="metrics">
    <div>Confidence: 90%</div>
    <div>Sources: 25</div>
    <div>Consensus: Strong Agreement</div>
  </div>
  
  <button onclick="showFullReport()">
    View Full Report
  </button>
</aside>
```

### 4. Real-time Status Component

```typescript
// components/FactCheckStatus.tsx

export function FactCheckStatus({ jobId }: { jobId: string }) {
  const [status, setStatus] = useState(null);
  
  useEffect(() => {
    const interval = setInterval(async () => {
      const api = new FactCheckAPI();
      const data = await api.getJobStatus(jobId);
      setStatus(data);
      
      if (data.status === 'finished') {
        clearInterval(interval);
      }
    }, 2000);  // Poll every 2 seconds
    
    return () => clearInterval(interval);
  }, [jobId]);
  
  if (!status) return <div>Loading...</div>;
  
  return (
    <div className="fact-check-status">
      <div className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ width: `${status.progress}%` }}
        />
      </div>
      <span>{status.phase} - {status.progress}%</span>
      <span className="time">
        {Math.floor(status.elapsed_time_seconds)}s elapsed
      </span>
    </div>
  );
}
```

---

## Best Practices

### Performance Optimization

1. **Use Denormalized Fields** - Query `fact_check_score` directly from articles table
2. **Index Filters** - Backend has indexes on score, verdict, and timestamp
3. **Cache Results** - Fact-check results rarely change, cache aggressively
4. **Lazy Load Details** - Only fetch full fact-check data when user clicks "View Details"

### User Experience

1. **Show Pending State** - Display "⏳ Fact-checking..." for new articles
2. **Progressive Disclosure** - Show score first, full report on demand
3. **Color Coding** - Use consistent colors (green=high, red=low)
4. **Trust Signals** - Show source count and consensus level

### Error Handling

```typescript
// Handle missing fact-check data gracefully
function getCredibilityDisplay(article: Article) {
  if (article.fact_check_score === null) {
    return {
      text: 'Pending',
      color: 'gray',
      icon: '⏳'
    };
  }
  
  if (article.fact_check_verdict === 'ERROR') {
    return {
      text: 'Unable to verify',
      color: 'gray',
      icon: '⚠'
    };
  }
  
  return {
    text: `${article.fact_check_score}/100`,
    color: getCredibilityColor(article.fact_check_score),
    icon: getVerdictIcon(article.fact_check_verdict)
  };
}
```

### Accessibility

```typescript
// Always include ARIA labels for screen readers
<div 
  className="credibility-badge"
  role="status"
  aria-label={`Credibility score: ${score} out of 100. Verdict: ${verdict}`}
>
  <span aria-hidden="true">{icon}</span>
  <span>{score}</span>
</div>
```

---

## Summary

### Quick Integration Checklist

✅ **Backend API** - Use `/api/v1/articles` endpoints for cached data  
✅ **Denormalized Fields** - `fact_check_score`, `fact_check_verdict`, `fact_checked_at`  
✅ **Railway API** - Use for real-time status and full detailed reports  
✅ **TypeScript Types** - Import interfaces for type safety  
✅ **UI Components** - Badge, modal, filters, status indicator  
✅ **Error Handling** - Handle pending, error, and null states  
✅ **Performance** - Cache results, lazy load details, use indexed queries  

### Key Metrics to Display

| Metric | Location | Example |
|--------|----------|---------|
| Credibility Score | Article cards | `87/100` |
| Verdict | Article cards, detail | `TRUE` ✓ |
| Confidence | Detail modal | `90%` |
| Sources Count | Detail modal | `25 sources` |
| Consensus | Detail modal | `STRONG_AGREEMENT` |
| Evidence Quality | Detail modal | `HIGH` |

### For More Information

- **Integration Guide**: `/Fact-Check-Integration-Guide.md`
- **API Schema**: `/Fact-Check-Output-Guide.md`
- **Database Architecture**: `/FACT_CHECK_DATABASE_ARCHITECTURE.md`
- **Railway API Docs**: `https://fact-check-production.up.railway.app/docs`

---

**Need help?** Contact the backend team or refer to the comprehensive documentation in this repository.
