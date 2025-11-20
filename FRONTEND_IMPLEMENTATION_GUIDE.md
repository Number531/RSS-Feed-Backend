# Frontend Implementation Guide - RSS Feed Backend

**Complete integration guide for React/Next.js frontend developers**  
**Version 2.0 - Updated with Synthesis Mode Endpoints**

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [API Endpoints](#api-endpoints)
   - [Authentication](#authentication)
   - [Articles](#articles)
   - [Synthesis Mode (NEW)](#synthesis-mode-new)
   - [Fact-Check](#fact-check)
   - [RSS Feeds](#rss-feeds)
   - [Bookmarks](#bookmarks)
4. [TypeScript Types](#typescript-types)
5. [Integration Examples](#integration-examples)
6. [Best Practices](#best-practices)

---

## Overview

This backend provides a **Reddit-style RSS feed aggregator** with advanced features:

- ✅ **Reddit-style voting** for articles and comments
- ✅ **Fact-checking** with AI-powered credibility scores
- ✅ **Synthesis mode** with enriched article content (NEW)
- ✅ **RSS feed management** with auto-refresh
- ✅ **Bookmarks** and collections
- ✅ **Threaded comments**
- ✅ **User authentication** with JWT

### Base URLs

- **Development**: `http://localhost:8000`
- **Swagger UI**: `http://localhost:8000/docs`
- **API Base**: `/api/v1`

---

## Quick Start

### 1. Environment Setup

```bash
# Frontend .env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_VERSION=v1
```

### 2. Install Dependencies

```typescript
// Copy TypeScript types from this guide
// Install axios or use fetch API
npm install axios
```

### 3. Create API Client

```typescript
// lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || 'v1';

export const api = {
  baseURL: `${API_BASE}/api/${API_VERSION}`,
  
  headers(token?: string) {
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  },
  
  async get(endpoint: string, token?: string) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      headers: this.headers(token)
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  },
  
  async post(endpoint: string, data: any, token?: string) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers: this.headers(token),
      body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }
};
```

---

## API Endpoints

### Authentication

#### Register
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "john_doe",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 900
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:** Same as register

#### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### Articles

#### List Articles
```http
GET /articles?category=politics&sort_by=hot&page=1&page_size=25
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
      "fact_check_score": 87,
      "fact_check_verdict": "TRUE",
      "fact_checked_at": "2025-10-18T12:07:00Z",
      "user_vote": 1
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

#### Get Single Article
```http
GET /articles/{article_id}
```

**Response:** Single article object (same structure as list item)

---

### Synthesis Mode (NEW)

**Synthesis mode** provides enriched articles with:
- 📝 Full synthesis markdown content
- 📚 Inline references and citations
- ⏱️ Event timeline
- 📌 Margin notes
- 🎯 Context and emphasis
- ✅ Fact-check integration

#### 1. List Synthesis Articles

```http
GET /articles/synthesis?page=1&page_size=10&verdict=TRUE&sort_by=newest
```

**Query Parameters:**
- `page` - Page number (min: 1, default: 1)
- `page_size` - Items per page (min: 1, max: 100, default: 20)
- `verdict` - Filter by verdict (TRUE, FALSE, MISLEADING, UNVERIFIED, MISINFORMATION)
- `sort_by` - Sort order (newest, oldest, credibility)

**Response:**
```json
{
  "articles": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Article Title",
      "url": "https://example.com/article",
      "author": "Author Name",
      "source_name": "BBC News",
      "published_date": "2025-11-20T12:00:00Z",
      "thumbnail_url": "https://example.com/thumb.jpg",
      "category": "politics",
      "fact_check_verdict": "TRUE",
      "fact_check_score": 87,
      "fact_checked_at": "2025-11-20T12:15:00Z",
      "synthesis_preview": "A 200-word preview of the synthesis article...",
      "synthesis_word_count": 1547,
      "synthesis_read_minutes": 6,
      "has_timeline": true,
      "has_context_emphasis": true,
      "timeline_event_count": 8,
      "reference_count": 25,
      "margin_note_count": 12,
      "verdict_color": "#22c55e"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 45,
    "has_next": true
  }
}
```

**Key Features:**
- **95% payload reduction** vs full article details
- **Preview only** - no full content or JSONB arrays
- **Optimized for lists** - fast loading for article grids
- **Pagination** - efficient navigation through large datasets

#### 2. Get Synthesis Article Details

```http
GET /articles/{article_id}/synthesis
```

**Path Parameters:**
- `article_id` - UUID of the article (e.g., `550e8400-e29b-41d4-a716-446655440000`)

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Full Article Title",
  "url": "https://example.com/article",
  "author": "Author Name",
  "source_name": "BBC News",
  "published_date": "2025-11-20T12:00:00Z",
  "thumbnail_url": "https://example.com/thumb.jpg",
  "category": "politics",
  "content": "Original article content...",
  "synthesis_article": "# Synthesis Article\n\n## Executive Summary\n\nFull markdown synthesis...",
  "fact_check_verdict": "TRUE",
  "fact_check_score": 87,
  "fact_checked_at": "2025-11-20T12:15:00Z",
  "synthesis_generated_at": "2025-11-20T12:20:00Z",
  "synthesis_word_count": 1547,
  "synthesis_read_minutes": 6,
  "fact_check_processing_time": 45.2,
  "verdict_color": "#22c55e",
  "has_timeline": true,
  "has_context_emphasis": true,
  "timeline_event_count": 8,
  "reference_count": 25,
  "margin_note_count": 12,
  "fact_check_mode": "comprehensive",
  "references": [
    {
      "id": 1,
      "title": "UK Government Announcement",
      "url": "https://example.com/source1",
      "source": "gov.uk",
      "credibility": "HIGH",
      "date": "2025-11-20",
      "relevance": "Primary source confirming the agreement"
    }
  ],
  "event_timeline": [
    {
      "date": "2025-11-15",
      "event": "Initial announcement",
      "significance": "HIGH",
      "description": "UK Prime Minister announces decision"
    }
  ],
  "margin_notes": [
    {
      "paragraph_number": 3,
      "note": "This claim is supported by 8 independent sources",
      "type": "evidence"
    }
  ],
  "context_and_emphasis": [
    {
      "text": "Historic sovereignty agreement",
      "type": "key_claim",
      "reasoning": "Central to the article's main assertion"
    }
  ]
}
```

**Key Features:**
- **Full synthesis markdown** in `synthesis_article` field
- **JSONB arrays** extracted: references, event_timeline, margin_notes, context_and_emphasis
- **Complete metadata** - word count, read time, fact-check details
- **Fact-check integration** - verdict, score, processing time
- **Enrichment data** - timeline events, reference count, margin notes

**Error Responses:**
- `404 Not Found` - Article doesn't exist or doesn't have synthesis
- `422 Unprocessable Entity` - Invalid UUID format

#### 3. Get Synthesis Statistics

```http
GET /articles/synthesis/stats
```

**Response:**
```json
{
  "total_synthesis_articles": 156,
  "average_credibility_score": 78.5,
  "total_references": 3890,
  "total_timeline_events": 1248,
  "total_margin_notes": 1872,
  "articles_with_timeline": 142,
  "articles_with_context_emphasis": 148,
  "verdict_distribution": {
    "TRUE": 98,
    "FALSE": 12,
    "MISLEADING": 24,
    "UNVERIFIED": 18,
    "MISINFORMATION": 4
  }
}
```

**Use Cases:**
- Dashboard analytics
- Content quality metrics
- User onboarding (show total verified articles)
- Admin monitoring

---

### Fact-Check

#### Get Fact-Check Details
```http
GET /articles/{article_id}/fact-check
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "article_id": "650e8400-e29b-41d4-a716-446655440001",
  "job_id": "9aa51885-c336-4de0-aa17-88a1944379c7",
  "verdict": "TRUE",
  "credibility_score": 87,
  "confidence": 0.9,
  "summary": "The UK did announce its decision to cede sovereignty...",
  "claims_analyzed": 1,
  "claims_true": 1,
  "claims_false": 0,
  "claims_misleading": 0,
  "claims_unverified": 0,
  "validation_results": {
    "claim": "The UK announced on 3 October 2024...",
    "verdict": "TRUE",
    "confidence": 0.9,
    "key_evidence": {
      "supporting": [
        "Official UK government announcement",
        "Confirmed by multiple news agencies"
      ],
      "contradicting": [],
      "context": ["Historic sovereignty dispute"]
    },
    "references": [
      {
        "citation_id": 1,
        "title": "UK Government Statement",
        "url": "https://example.com/source1",
        "source": "gov.uk",
        "credibility": "HIGH"
      }
    ]
  },
  "num_sources": 25,
  "source_consensus": "STRONG_AGREEMENT",
  "processing_time_seconds": 137,
  "fact_checked_at": "2025-10-19T14:22:54Z"
}
```

---

### RSS Feeds

#### List Feeds
```http
GET /feeds
Authorization: Bearer {access_token}
```

#### Add Feed
```http
POST /feeds
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "url": "https://example.com/feed.xml",
  "title": "Custom Title (optional)"
}
```

#### Delete Feed
```http
DELETE /feeds/{feed_id}
Authorization: Bearer {access_token}
```

---

### Bookmarks

#### List Bookmarks
```http
GET /bookmarks
Authorization: Bearer {access_token}
```

#### Add Bookmark
```http
POST /bookmarks
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "article_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Remove Bookmark
```http
DELETE /bookmarks/{bookmark_id}
Authorization: Bearer {access_token}
```

---

## TypeScript Types

```typescript
// types/api.ts

// ==================== SYNTHESIS TYPES (NEW) ====================

export interface SynthesisListItem {
  id: string;
  title: string;
  url: string;
  author: string | null;
  source_name: string;
  published_date: string | null;
  thumbnail_url: string | null;
  category: string;
  fact_check_verdict: Verdict;
  fact_check_score: number;
  fact_checked_at: string;
  synthesis_preview: string;
  synthesis_word_count: number;
  synthesis_read_minutes: number;
  has_timeline: boolean;
  has_context_emphasis: boolean;
  timeline_event_count: number;
  reference_count: number;
  margin_note_count: number;
  verdict_color: string;
}

export interface SynthesisListResponse {
  articles: SynthesisListItem[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    has_next: boolean;
  };
}

export interface Reference {
  id: number;
  title: string;
  url: string;
  source: string;
  credibility: 'HIGH' | 'MEDIUM' | 'LOW';
  date: string | null;
  relevance: string | null;
}

export interface TimelineEvent {
  date: string;
  event: string;
  significance: 'HIGH' | 'MEDIUM' | 'LOW';
  description: string | null;
}

export interface MarginNote {
  paragraph_number: number;
  note: string;
  type: 'evidence' | 'context' | 'clarification';
}

export interface ContextEmphasis {
  text: string;
  type: 'key_claim' | 'disputed_fact' | 'expert_opinion' | 'historical_context';
  reasoning: string;
}

export interface SynthesisDetailArticle {
  id: string;
  title: string;
  url: string;
  author: string | null;
  source_name: string;
  published_date: string | null;
  thumbnail_url: string | null;
  category: string;
  content: string | null;
  synthesis_article: string;
  fact_check_verdict: Verdict;
  fact_check_score: number;
  fact_checked_at: string;
  synthesis_generated_at: string;
  synthesis_word_count: number;
  synthesis_read_minutes: number;
  fact_check_processing_time: number | null;
  verdict_color: string;
  has_timeline: boolean;
  has_context_emphasis: boolean;
  timeline_event_count: number;
  reference_count: number;
  margin_note_count: number;
  fact_check_mode: string | null;
  references: Reference[];
  event_timeline: TimelineEvent[];
  margin_notes: MarginNote[];
  context_and_emphasis: ContextEmphasis[];
}

export interface SynthesisStatsResponse {
  total_synthesis_articles: number;
  average_credibility_score: number;
  total_references: number;
  total_timeline_events: number;
  total_margin_notes: number;
  articles_with_timeline: number;
  articles_with_context_emphasis: number;
  verdict_distribution: Record<string, number>;
}

// ==================== ARTICLE TYPES ====================

export type Verdict = 
  | 'TRUE' 
  | 'FALSE' 
  | 'MISLEADING' 
  | 'UNVERIFIED' 
  | 'MISINFORMATION'
  | 'PENDING'
  | 'ERROR';

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
  fact_check_score: number | null;
  fact_check_verdict: Verdict | null;
  fact_checked_at: string | null;
  user_vote: number | null;  // -1, 0, 1
}

export interface ArticlesResponse {
  articles: Article[];
  pagination: {
    current_page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  };
}

// ==================== FACT-CHECK TYPES ====================

export interface FactCheckDetail {
  id: string;
  article_id: string;
  job_id: string;
  verdict: Verdict;
  credibility_score: number;
  confidence: number | null;
  summary: string;
  claims_analyzed: number | null;
  claims_true: number | null;
  claims_false: number | null;
  claims_misleading: number | null;
  claims_unverified: number | null;
  validation_results: {
    claim: string;
    verdict: Verdict;
    confidence: number;
    key_evidence: {
      supporting: string[];
      contradicting: string[];
      context: string[];
    };
    references: Array<{
      citation_id: number;
      title: string;
      url: string;
      source: string;
      credibility: 'HIGH' | 'MEDIUM' | 'LOW';
    }>;
  };
  num_sources: number | null;
  source_consensus: 'STRONG_AGREEMENT' | 'MODERATE_AGREEMENT' | 'MIXED' | 'WEAK_AGREEMENT' | null;
  processing_time_seconds: number | null;
  fact_checked_at: string;
  created_at: string;
  updated_at: string;
}

// ==================== AUTH TYPES ====================

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// ==================== FEED TYPES ====================

export interface RSSFeed {
  id: string;
  url: string;
  title: string;
  created_at: string;
  last_fetched_at: string | null;
}

// ==================== BOOKMARK TYPES ====================

export interface Bookmark {
  id: string;
  article_id: string;
  article: Article;
  created_at: string;
}
```

---

## Integration Examples

### 1. Synthesis Mode Article List

```typescript
// pages/synthesis/index.tsx

import { useState, useEffect } from 'react';
import { SynthesisListResponse, SynthesisListItem } from '@/types/api';

export default function SynthesisPage() {
  const [data, setData] = useState<SynthesisListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [verdict, setVerdict] = useState<string | null>(null);

  useEffect(() => {
    async function fetchSynthesisArticles() {
      setLoading(true);
      try {
        const params = new URLSearchParams({
          page: page.toString(),
          page_size: '10',
          sort_by: 'newest',
          ...(verdict && { verdict })
        });
        
        const response = await fetch(
          `http://localhost:8000/api/v1/articles/synthesis?${params}`
        );
        const data = await response.json();
        setData(data);
      } catch (error) {
        console.error('Failed to fetch synthesis articles:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchSynthesisArticles();
  }, [page, verdict]);

  if (loading) return <div>Loading synthesis articles...</div>;
  if (!data) return <div>No data</div>;

  return (
    <div className="synthesis-page">
      <h1>Synthesis Mode Articles</h1>
      
      {/* Filters */}
      <div className="filters">
        <select onChange={(e) => setVerdict(e.target.value || null)}>
          <option value="">All Verdicts</option>
          <option value="TRUE">✓ True</option>
          <option value="FALSE">✗ False</option>
          <option value="MISLEADING">⚠ Misleading</option>
          <option value="UNVERIFIED">? Unverified</option>
        </select>
      </div>

      {/* Article Grid */}
      <div className="article-grid">
        {data.articles.map((article) => (
          <SynthesisCard key={article.id} article={article} />
        ))}
      </div>

      {/* Pagination */}
      <div className="pagination">
        <button 
          onClick={() => setPage(p => p - 1)} 
          disabled={page === 1}
        >
          Previous
        </button>
        <span>Page {page}</span>
        <button 
          onClick={() => setPage(p => p + 1)} 
          disabled={!data.pagination.has_next}
        >
          Next
        </button>
      </div>
    </div>
  );
}

function SynthesisCard({ article }: { article: SynthesisListItem }) {
  const verdictColors = {
    TRUE: 'bg-green-500',
    FALSE: 'bg-red-500',
    MISLEADING: 'bg-yellow-500',
    UNVERIFIED: 'bg-gray-500',
    MISINFORMATION: 'bg-red-700'
  };

  return (
    <div className="synthesis-card">
      {article.thumbnail_url && (
        <img src={article.thumbnail_url} alt={article.title} />
      )}
      
      <div className="card-content">
        <div className="card-header">
          <h2>{article.title}</h2>
          <div 
            className={`verdict-badge ${verdictColors[article.fact_check_verdict]}`}
            style={{ backgroundColor: article.verdict_color }}
          >
            {article.fact_check_verdict} • {article.fact_check_score}/100
          </div>
        </div>
        
        <p className="preview">{article.synthesis_preview}</p>
        
        <div className="metadata">
          <span>{article.source_name}</span>
          <span>{article.synthesis_read_minutes} min read</span>
          <span>{article.reference_count} sources</span>
          {article.has_timeline && <span>📅 Timeline</span>}
        </div>
        
        <a href={`/synthesis/${article.id}`}>
          Read Full Synthesis →
        </a>
      </div>
    </div>
  );
}
```

### 2. Synthesis Article Detail Page

```typescript
// pages/synthesis/[id].tsx

import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import ReactMarkdown from 'react-markdown';
import { SynthesisDetailArticle } from '@/types/api';

export default function SynthesisDetailPage() {
  const router = useRouter();
  const { id } = router.query;
  const [article, setArticle] = useState<SynthesisDetailArticle | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'synthesis' | 'references' | 'timeline'>('synthesis');

  useEffect(() => {
    if (!id) return;

    async function fetchArticle() {
      try {
        const response = await fetch(
          `http://localhost:8000/api/v1/articles/${id}/synthesis`
        );
        if (response.ok) {
          const data = await response.json();
          setArticle(data);
        } else if (response.status === 404) {
          router.push('/404');
        }
      } catch (error) {
        console.error('Failed to fetch article:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchArticle();
  }, [id]);

  if (loading) return <div>Loading article...</div>;
  if (!article) return <div>Article not found</div>;

  return (
    <div className="synthesis-detail">
      {/* Header */}
      <header className="article-header">
        <h1>{article.title}</h1>
        <div className="metadata">
          <span className="author">{article.author || 'Unknown'}</span>
          <span className="source">{article.source_name}</span>
          <span className="date">
            {new Date(article.published_date || '').toLocaleDateString()}
          </span>
          <span className="reading-time">
            {article.synthesis_read_minutes} min read
          </span>
        </div>
        
        {/* Fact-Check Badge */}
        <div 
          className="fact-check-badge"
          style={{ backgroundColor: article.verdict_color }}
        >
          <span className="verdict">{article.fact_check_verdict}</span>
          <span className="score">{article.fact_check_score}/100</span>
          <span className="sources">{article.reference_count} sources</span>
        </div>
      </header>

      {/* Tabs */}
      <div className="tabs">
        <button 
          className={activeTab === 'synthesis' ? 'active' : ''}
          onClick={() => setActiveTab('synthesis')}
        >
          Synthesis Article
        </button>
        <button 
          className={activeTab === 'references' ? 'active' : ''}
          onClick={() => setActiveTab('references')}
        >
          References ({article.reference_count})
        </button>
        {article.has_timeline && (
          <button 
            className={activeTab === 'timeline' ? 'active' : ''}
            onClick={() => setActiveTab('timeline')}
          >
            Timeline ({article.timeline_event_count})
          </button>
        )}
      </div>

      {/* Content */}
      <div className="content">
        {activeTab === 'synthesis' && (
          <div className="synthesis-content">
            <ReactMarkdown>{article.synthesis_article}</ReactMarkdown>
            
            {/* Margin Notes */}
            {article.margin_notes.length > 0 && (
              <aside className="margin-notes">
                <h3>Notes</h3>
                {article.margin_notes.map((note, i) => (
                  <div key={i} className={`note ${note.type}`}>
                    <strong>¶{note.paragraph_number}</strong>
                    <p>{note.note}</p>
                  </div>
                ))}
              </aside>
            )}
          </div>
        )}

        {activeTab === 'references' && (
          <div className="references">
            <h2>Sources & References</h2>
            {article.references.map((ref) => (
              <div key={ref.id} className="reference">
                <div className="ref-header">
                  <span className="ref-number">[{ref.id}]</span>
                  <span className={`credibility ${ref.credibility.toLowerCase()}`}>
                    {ref.credibility}
                  </span>
                </div>
                <h3>{ref.title}</h3>
                <p className="source">{ref.source}</p>
                {ref.date && <p className="date">{ref.date}</p>}
                {ref.relevance && <p className="relevance">{ref.relevance}</p>}
                <a href={ref.url} target="_blank" rel="noopener noreferrer">
                  View Source →
                </a>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'timeline' && article.has_timeline && (
          <div className="timeline">
            <h2>Event Timeline</h2>
            {article.event_timeline.map((event, i) => (
              <div key={i} className={`timeline-event ${event.significance.toLowerCase()}`}>
                <div className="event-date">{event.date}</div>
                <div className="event-content">
                  <h3>{event.event}</h3>
                  {event.description && <p>{event.description}</p>}
                  <span className="significance">{event.significance}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="article-footer">
        <div className="processing-info">
          <span>
            Fact-checked in {article.fact_check_processing_time?.toFixed(1)}s
          </span>
          <span>•</span>
          <span>
            Synthesis generated {new Date(article.synthesis_generated_at).toLocaleDateString()}
          </span>
          <span>•</span>
          <span>
            Mode: {article.fact_check_mode || 'standard'}
          </span>
        </div>
        
        <a href={article.url} target="_blank" rel="noopener noreferrer">
          Read Original Article →
        </a>
      </footer>
    </div>
  );
}
```

### 3. Synthesis Stats Dashboard

```typescript
// components/SynthesisStats.tsx

import { useState, useEffect } from 'react';
import { SynthesisStatsResponse } from '@/types/api';

export function SynthesisStats() {
  const [stats, setStats] = useState<SynthesisStatsResponse | null>(null);

  useEffect(() => {
    async function fetchStats() {
      try {
        const response = await fetch(
          'http://localhost:8000/api/v1/articles/synthesis/stats'
        );
        const data = await response.json();
        setStats(data);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      }
    }

    fetchStats();
  }, []);

  if (!stats) return <div>Loading stats...</div>;

  return (
    <div className="synthesis-stats">
      <h2>Synthesis Mode Statistics</h2>
      
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{stats.total_synthesis_articles}</div>
          <div className="stat-label">Synthesis Articles</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-value">{stats.average_credibility_score.toFixed(1)}</div>
          <div className="stat-label">Average Credibility</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-value">{stats.total_references}</div>
          <div className="stat-label">Total References</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-value">{stats.articles_with_timeline}</div>
          <div className="stat-label">Articles with Timeline</div>
        </div>
      </div>

      <div className="verdict-distribution">
        <h3>Verdict Distribution</h3>
        <div className="distribution-chart">
          {Object.entries(stats.verdict_distribution).map(([verdict, count]) => (
            <div key={verdict} className="verdict-bar">
              <span className="verdict-label">{verdict}</span>
              <div className="bar" style={{ width: `${(count / stats.total_synthesis_articles) * 100}%` }}>
                <span>{count}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

### 4. Article Card with Fact-Check Badge

```typescript
// components/ArticleCard.tsx

import { Article } from '@/types/api';

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
      {article.thumbnail_url && (
        <img src={article.thumbnail_url} alt={article.title} />
      )}
      
      <div className="card-content">
        <div className="card-header">
          <h2>{article.title}</h2>
          
          {article.fact_check_score !== null ? (
            <div 
              className={`credibility-badge ${getCredibilityColor(article.fact_check_score)}`}
              title={`Credibility Score: ${article.fact_check_score}/100`}
            >
              <span className="icon">{getVerdictIcon(article.fact_check_verdict)}</span>
              <span className="score">{article.fact_check_score}</span>
            </div>
          ) : (
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
    </div>
  );
}
```

---

## Best Practices

### Performance Optimization

1. **Use Denormalized Fields**
   - List endpoints return `fact_check_score` and `fact_check_verdict` directly
   - No need for additional queries for basic fact-check info
   - Use detail endpoints only when showing full reports

2. **Pagination**
   - Default `page_size=20` for synthesis endpoints
   - Increase to 50-100 for infinite scroll
   - Always check `has_next` before loading more

3. **Caching**
   - Cache synthesis articles aggressively (rarely change)
   - Cache fact-check details for 24 hours
   - Cache stats for 1 hour

4. **Lazy Loading**
   - Load synthesis preview in lists
   - Fetch full `synthesis_article` markdown only on detail page
   - Lazy load JSONB arrays (references, timeline, etc.)

### Error Handling

```typescript
async function fetchWithErrorHandling(url: string) {
  try {
    const response = await fetch(url);
    
    if (response.status === 404) {
      // Handle not found
      return null;
    }
    
    if (response.status === 422) {
      // Invalid UUID
      throw new Error('Invalid article ID format');
    }
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}
```

### Authentication

```typescript
// Store tokens securely
function storeTokens(accessToken: string, refreshToken: string) {
  // Use httpOnly cookies in production
  localStorage.setItem('access_token', accessToken);
  localStorage.setItem('refresh_token', refreshToken);
}

// Auto-refresh expired tokens
async function fetchWithAuth(url: string, options: RequestInit = {}) {
  let token = localStorage.getItem('access_token');
  
  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  });
  
  // If 401, try refreshing token
  if (response.status === 401) {
    const refreshToken = localStorage.getItem('refresh_token');
    const refreshResponse = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken })
    });
    
    if (refreshResponse.ok) {
      const { access_token } = await refreshResponse.json();
      storeTokens(access_token, refreshToken!);
      
      // Retry original request
      response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${access_token}`
        }
      });
    } else {
      // Redirect to login
      window.location.href = '/login';
    }
  }
  
  return response;
}
```

### UI/UX Guidelines

1. **Credibility Badges**
   - Green (80-100): ✓ High credibility
   - Yellow (60-79): ⚠ Medium credibility
   - Orange (40-59): ⚠ Low credibility
   - Red (0-39): ✗ Very low credibility
   - Gray: ⏳ Pending fact-check

2. **Verdict Colors** (from backend)
   - TRUE: `#22c55e` (green)
   - FALSE: `#ef4444` (red)
   - MISLEADING: `#f59e0b` (orange)
   - UNVERIFIED: `#6b7280` (gray)

3. **Progressive Disclosure**
   - Show preview and score in list view
   - Load full synthesis on detail page
   - Expand references/timeline on demand

4. **Loading States**
   ```typescript
   {loading ? (
     <div>Loading synthesis articles...</div>
   ) : error ? (
     <div>Error: {error.message}</div>
   ) : articles.length === 0 ? (
     <div>No articles found</div>
   ) : (
     <ArticleList articles={articles} />
   )}
   ```

### Accessibility

```typescript
// Always include ARIA labels
<div 
  className="credibility-badge"
  role="status"
  aria-label={`Credibility score: ${score} out of 100. Verdict: ${verdict}`}
>
  <span aria-hidden="true">{icon}</span>
  <span>{score}</span>
</div>

// Semantic HTML
<article>
  <header>
    <h1>{article.title}</h1>
  </header>
  <main>
    {article.synthesis_article}
  </main>
  <footer>
    <time dateTime={article.published_date}>
      {formatDate(article.published_date)}
    </time>
  </footer>
</article>
```

---

## Summary

### Quick Reference

| Feature | Endpoint | Use Case |
|---------|----------|----------|
| **Articles List** | `GET /articles` | Homepage feed with fact-check scores |
| **Synthesis List** | `GET /articles/synthesis` | Optimized list for synthesis mode |
| **Synthesis Detail** | `GET /articles/{id}/synthesis` | Full article with enrichments |
| **Synthesis Stats** | `GET /articles/synthesis/stats` | Dashboard analytics |
| **Fact-Check Detail** | `GET /articles/{id}/fact-check` | Detailed fact-check report |
| **Authentication** | `POST /auth/login` | User login |
| **RSS Feeds** | `GET /feeds` | User's feed list |
| **Bookmarks** | `GET /bookmarks` | Saved articles |

### Key Differences: Articles vs Synthesis

| Feature | `/articles` | `/articles/synthesis` |
|---------|-------------|----------------------|
| **Payload Size** | Normal | 95% smaller (list) |
| **Content** | Original article | Synthesis markdown |
| **Enrichments** | No | Yes (references, timeline, notes) |
| **Fact-Check** | Denormalized fields | Full integration |
| **Use Case** | General browsing | Enhanced reading experience |

### Implementation Priority

1. ✅ **Phase 1**: Authentication + Basic article list
2. ✅ **Phase 2**: Fact-check badges on article cards
3. ✅ **Phase 3**: Synthesis list endpoint
4. ✅ **Phase 4**: Synthesis detail page with markdown rendering
5. ✅ **Phase 5**: References, timeline, and margin notes
6. ✅ **Phase 6**: Stats dashboard

### Resources

- **Swagger UI**: http://localhost:8000/docs
- **Repository**: /Users/ej/Downloads/RSS-Feed/backend
- **Branch**: `feature/synthesis-endpoints`
- **Documentation**:
  - `SYNTHESIS_ENDPOINTS_COMPLETE.md` - Implementation details
  - `FRONTEND_FACT_CHECK_INTEGRATION_GUIDE.md` - Fact-check integration
  - `FRONTEND_DEVELOPER_GUIDE.md` - API reference

---

**Questions or issues?** Contact the backend team or open an issue on GitHub.
