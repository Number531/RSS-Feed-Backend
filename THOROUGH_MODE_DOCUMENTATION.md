# Fact-Check System: Complete Documentation

## Overview

The fact-checking system offers two validation modes: **Summary Mode** (fast, article-level) and **Thorough Mode** (comprehensive, claim-by-claim). This document explains both modes, their architectures, data flows, and when to use each.

---

## Table of Contents

1. [Mode Comparison](#mode-comparison)
2. [Summary Mode](#summary-mode)
3. [Thorough Mode](#thorough-mode)
4. [Temporal Analysis Features](#temporal-analysis-features)
5. [Evidence Collection Architecture](#evidence-collection-architecture)
6. [Complete Data Flow](#complete-data-flow)
7. [Validation Prompt Structures](#validation-prompt-structures)
8. [Output Schemas](#output-schemas)
9. [Configuration](#configuration)
10. [Cost & Performance](#cost--performance)

---

## Mode Comparison

### Quick Reference

| Feature | Summary Mode | Thorough Mode |
|---------|--------------|---------------|
| **Analysis Level** | Article-level (overall narrative) | Claim-by-claim (granular) |
| **Sources Per Article** | ~25 sources total | ~25 sources × number of claims |
| **Claims Extracted** | 1-2 high-level statements | Average 22.6 claims per article |
| **Processing Time** | ~3-4 minutes | ~4-5 minutes |
| **Cost Per Article** | ~$0.04 | ~$0.37 (10 claims) |
| **Parallel Searches** | 4 queries for entire article | 4 queries per claim |
| **Use Case** | Quick screening, high-volume | Detailed investigation |
| **Verdict Granularity** | Single verdict for article | Individual verdicts per claim |

### When to Use Each Mode

**Summary Mode** is best for:
- ✅ High-volume article processing
- ✅ Initial triage and filtering
- ✅ Real-time feed monitoring
- ✅ Cost-sensitive deployments
- ✅ Quick misinformation detection

**Thorough Mode** is best for:
- ✅ Controversial or disputed claims
- ✅ Legal/medical/financial content
- ✅ Detailed investigative reporting
- ✅ Claims requiring historical context
- ✅ Content with multiple complex assertions

---

## Summary Mode

### How Summary Mode Works

**Summary mode validates the overall narrative of an article**, treating it as a cohesive story rather than individual claims.

#### Process Flow

```
1. Article Text Input
   ↓
2. Extract 1-2 High-Level Claims
   ↓
3. Single Evidence Search (4 parallel queries)
   → News: 5 results
   → Research: 10 results  
   → General: 5 results
   → Historical: 5 results
   = 25 total sources
   ↓
4. AI Validation (article-level analysis)
   ↓
5. Single Verdict + Score
```

#### Key Characteristics

**Claim Extraction**: Summary mode extracts 1-2 overarching statements that represent the article's main narrative.

```json
{
  "article_title": "Federal Reserve Announces Rate Increase",
  "extracted_claims": [
    "The Federal Reserve raised interest rates to combat inflation in 2024"
  ],
  "claim_count": 1
}
```

**Evidence Collection**: One set of 25 sources is gathered for the entire article:
- All claims share the same evidence pool
- 4 parallel searches executed once
- Cost-efficient for quick validation

**Validation**: The AI model analyzes the overall narrative:
- Evaluates article's general accuracy
- Checks for major factual errors
- Provides single credibility score
- Returns one verdict: TRUE, FALSE, MISLEADING, or UNVERIFIED

#### Summary Mode Output Example

```json
{
  "verdict": "TRUE",
  "credibility_score": 90,
  "summary": "Article accurately reports Federal Reserve's 2024 rate increases to combat inflation [1][2][3]",
  "claims_analyzed": 1,
  "claims_true": 1,
  "claims_false": 0,
  "claims_misleading": 0,
  "num_sources": 25,
  "processing_time_ms": 3400,
  "cost_usd": 0.04
}
```

#### Summary Mode Advantages

✅ **Fast**: 3-4 minutes per article  
✅ **Economical**: ~$0.04 per article  
✅ **Efficient**: Good for filtering large volumes  
✅ **Clear**: Single verdict easy to understand  

#### Summary Mode Limitations

⚠️ **Less Granular**: Can't identify specific false claims in otherwise accurate article  
⚠️ **May Miss Details**: Won't catch subtle misrepresentations  
⚠️ **Limited Context**: Single evidence pool for all claims  

---

## Thorough Mode

### How Thorough Mode Works

**Thorough mode extracts individual claims and validates each one independently** with dedicated evidence searches.

#### Process Flow

```
1. Article Text Input
   ↓
2. Extract Individual Claims (avg 22.6 per article)
   ↓
3. FOR EACH CLAIM:
   ├─ Evidence Search (4 parallel queries)
   │  → News: 5 results
   │  → Research: 10 results
   │  → General: 5 results
   │  → Historical: 5 results
   │  = 25 sources PER CLAIM
   │  ↓
   ├─ AI Validation (claim-specific)
   │  ↓
   └─ Individual Verdict + Score
   ↓
4. Aggregate Results
   ↓
5. Overall Article Verdict
```

#### Key Characteristics

**Claim Extraction**: Thorough mode extracts 20-40+ discrete factual statements.

```json
{
  "article_title": "Federal Reserve Announces Rate Increase",
  "extracted_claims": [
    "The Federal Reserve raised rates to 5.5% in December 2024",
    "This marked the sixth consecutive rate increase",
    "Inflation was at 3.4% annually",
    "The Fed cited inflation concerns as justification",
    "Previous rate increases occurred monthly since June 2024",
    // ... 15-35 more claims
  ],
  "claim_count": 22
}
```

**Evidence Collection**: Each claim gets its own evidence search:
- **Claim 1**: 25 sources (news + research + general + historical)
- **Claim 2**: 25 sources (fresh search, different evidence)
- **Claim 3**: 25 sources (fresh search)
- **...and so on**

**Total for 6-claim article**: 6 × 25 = **150 source lookups**

**Validation**: Each claim is independently validated:
- Dedicated evidence for each assertion
- Individual verdict per claim
- Granular accuracy tracking
- Aggregated into overall score

#### Thorough Mode Output Example

```json
{
  "verdict": "TRUE",
  "credibility_score": 95,
  "summary": "Article is highly accurate with 5 true claims verified through comprehensive evidence",
  "claims_analyzed": 6,
  "claims_true": 5,
  "claims_false": 1,
  "claims_misleading": 0,
  "claims_unverified": 0,
  "num_sources": 150,  // 6 claims × 25 sources
  "claim_breakdown": [
    {
      "claim": "The Federal Reserve raised rates to 5.5%",
      "verdict": "TRUE",
      "confidence": 98,
      "sources_used": 25
    },
    {
      "claim": "This marked the sixth consecutive increase",
      "verdict": "FALSE",
      "confidence": 92,
      "sources_used": 25
    },
    // ... 4 more claims
  ],
  "processing_time_ms": 8420,
  "cost_usd": 0.22
}
```

#### Thorough Mode Advantages

✅ **Granular**: Identifies exactly which claims are true/false  
✅ **Comprehensive**: 25 sources per claim = thorough validation  
✅ **Detailed**: Full breakdown of article accuracy  
✅ **Temporal**: Historical context for each claim  
✅ **Transparent**: Can see which specific claims failed  

#### Thorough Mode Limitations

⚠️ **Expensive**: ~$0.037 per claim (~$0.37 for 10 claims)  
⚠️ **Slower**: 4-5 minutes per article  
⚠️ **Complex**: More data to process and display  

---

## Temporal Analysis Features

Thorough mode integrates temporal context at multiple levels to ensure claim validation is grounded in up-to-date, time-aware analysis.

### 1. Current Date Context Injection

**Location**: `src/clients/exa_client.py` (lines 99-112)

Every single Exa search query automatically includes the current date to prevent model knowledge cutoff issues:

```python
# IMPORTANT: Inject current date to prevent model knowledge cutoff issues
current_date = datetime.now()
current_date_str = current_date.strftime("%Y-%m-%d")

# Inject current date context into query
query_with_date = f"{query} (current date: {current_date_str})"
```

**Example**: A claim about "recent inflation rates" becomes:
```
"What are the current inflation rates in the US? (current date: 2025-01-21)"
```

This ensures:
- Search results understand "current" in temporal context
- Model validation knows what "recent" means
- Prevents hallucinations from outdated training data

### 2. Published Date Metadata for Every Source

**Location**: `src/clients/gemini_validation_client.py` (lines 374-395)

Every evidence source returned includes full temporal metadata:

```python
for i, result in enumerate(results[:max_items], 1):
    title = result.get("title", "No title")
    url = result.get("url", "")
    domain = result.get("domain", "")
    date = result.get("published_date", "Date unknown")  # ← Published date
    text = result.get("text", "")[:config.max_evidence_chars_per_source]
    highlights = result.get("highlights", [])
    
    # Format evidence item
    item = f"""
Source {i}: {title}
Domain: {domain}
Published: {date}  # ← Date prominently displayed
URL: {url}

Key content:
{text}

Relevant highlights:
{chr(10).join(f'- {h[:config.max_highlight_chars]}' for h in highlights[:config.max_highlights_per_source])}
"""
```

**Example Evidence Output**:
```
Source 1: Federal Reserve Announces Interest Rate Decision
Domain: reuters.com
Published: 2025-01-15
URL: https://reuters.com/article/fed-rates-2025

Key content:
The Federal Reserve announced today...

Relevant highlights:
- Rate increased by 0.25 percentage points
- Inflation concerns cited as primary factor
```

### 3. Date-Based Search Filtering

**Location**: `src/clients/exa_client.py` (lines 97-127)

Different query types have different temporal scopes optimized for their purpose:

```python
if query_type == "news":
    # News: Last 30 days only (breaking developments)
    start_date = (current_date - timedelta(days=self.days_back_news)).strftime("%Y-%m-%d")

elif query_type == "historical":
    # Historical: NO DATE LIMIT (find precedents from decades ago)
    start_date = None

else:
    # General and research: Last 2 years (established facts)
    start_date = (current_date - timedelta(days=365*2)).strftime("%Y-%m-%d")

# Search parameters
search_params = {
    "query": query_with_date,
    "num_results": num_results,
    "use_autoprompt": self.use_autoprompt,
    "type": "auto",
    "end_published_date": current_date_str,  # Never search future
    "text": True,
    "highlights": True
}

# Add start_date only if specified (historical has no limit)
if start_date is not None:
    search_params["start_published_date"] = start_date
```

**Query Type Date Ranges**:

| Query Type | Date Range | Rationale |
|------------|-----------|-----------|
| **News** | Last 30 days | Breaking developments, current events |
| **Research** | Last 2 years | Peer-reviewed studies, established findings |
| **General** | Last 2 years | Expert analysis, fact-checking reports |
| **Historical** | Unlimited | Precedents, patterns, historical context |

### 4. Temporal Analysis in Validation Prompt

**Location**: `src/clients/gemini_validation_client.py` (lines 424-520)

The thorough validation prompt explicitly instructs the AI model to analyze temporal factors:

```markdown
## Temporal Analysis

Consider:
- Currency: How recent is the information? Are there more recent updates?
- Historical context: Has this claim's validity changed over time?
- Time-bound factors: Does the claim's truth depend on when it was made?
- Evolution: How has understanding of this topic evolved?
```

This ensures validation accounts for:
- ✅ Recency of evidence (is this the latest information?)
- ✅ Temporal validity (was this true then but not now?)
- ✅ Historical precedents (has this pattern occurred before?)
- ✅ Evolution of facts (have new findings superseded old ones?)

---

## Evidence Collection Architecture

### Multi-Channel Parallel Search

For **each high-risk claim**, the system executes 4 parallel searches simultaneously:

```python
# src/clients/exa_client.py
async def search_claim_comprehensive(self, claim_text: str) -> Dict[str, Any]:
    """
    Search for evidence using 4 parallel queries per claim.
    Uses predefined result counts: news (5), research (10), general (5), historical (5).
    """
    queries = format_journalistic_queries(claim_text, use_enhanced=use_enhanced)
    
    # Create tasks for parallel execution
    tasks = [
        self._execute_single_search(queries["news"], "news"),
        self._execute_single_search(queries["research"], "research"),
        self._execute_single_search(queries["general"], "general"),
        self._execute_single_search(queries["historical"], "historical")
    ]
    
    # Execute all 4 searches simultaneously
    search_results = await asyncio.gather(*tasks, return_exceptions=True)
```

### Query Specialization

Each query type uses specialized phrasing and domain filtering:

#### 1. News Query
```python
# Target: Breaking developments, current events
include_domains = [
    "reuters.com", "apnews.com", "bbc.com", "nytimes.com",
    "washingtonpost.com", "wsj.com", "npr.org", "politico.com",
    "bloomberg.com", "economist.com", "ft.com", "theguardian.com"
]
num_results = 5
date_range = "Last 30 days"
```

#### 2. Research Query
```python
# Target: Peer-reviewed studies, academic papers
include_domains = [
    "nature.com", "science.org", "sciencedirect.com", 
    "pubmed.ncbi.nlm.nih.gov", "pmc.ncbi.nlm.nih.gov",
    "arxiv.org", "nejm.org", "thelancet.com", "bmj.com"
]
num_results = 10  # More results for thorough academic review
date_range = "Last 2 years"
```

#### 3. General Query
```python
# Target: Expert analysis, fact-checking, authoritative sources
include_domains = [
    "wikipedia.org", "britannica.com", "brookings.edu", "rand.org",
    "pewresearch.org", "cfr.org", "csis.org", "factcheck.org",
    "politifact.com", "snopes.com", "apnews.com", "reuters.com"
]
num_results = 5
date_range = "Last 2 years"
```

#### 4. Historical Query
```python
# Target: Precedents, patterns, historical context
include_domains = None  # Broader search without restrictions
num_results = 5
date_range = "Unlimited"  # Critical for finding decades-old precedents
```

### Domain Filtering Strategy

**Why domain filtering?**
- ✅ Ensures high-quality, credible sources
- ✅ Filters out misinformation and low-quality content
- ✅ Prioritizes authoritative publishers
- ✅ Improves validation accuracy

**Trade-off**: Historical searches use broader domains to capture rare historical precedents that may exist only in specialized archives.

---

## Complete Data Flow

### Summary Mode Data Flow

#### Single Evidence Collection for Article

```json
{
  "article": "Federal Reserve Announces Rate Increase",
  "mode": "summary",
  "claims_extracted": 1,
  
  "evidence_search": {
    "total_searches": 4,
    "total_results": 25,
    "search_types": ["news", "research", "general", "historical"]
  },
  
  "validation": {
    "verdict": "TRUE",
    "score": 90,
    "sources_used": 25
  },
  
  "cost": {
    "exa_searches": "$0.010",
    "gemini": "$0.027",
    "total": "$0.037"
  }
}
```

### Thorough Mode Data Flow

#### Step-by-Step Evidence Collection Per Claim

For **each individual claim**, here's the complete data flow:

#### Step 1: Claim Extraction
```json
{
  "claim": "The Federal Reserve raised interest rates to combat inflation in 2024",
  "risk_level": "HIGH",
  "category": "Economic Policy",
  "source_paragraph": "According to recent reports..."
}
```

#### Step 2: Parallel Evidence Search (4 queries)

**News Query** → 5 results
```json
{
  "query_type": "news",
  "query": "Federal Reserve interest rate increase 2024 inflation (current date: 2025-01-21)",
  "num_results": 5,
  "results": [
    {
      "title": "Fed Raises Rates to 5.5% Citing Inflation Concerns",
      "url": "https://reuters.com/fed-rates-2024",
      "domain": "reuters.com",
      "published_date": "2024-12-15",
      "text": "The Federal Reserve announced...",
      "highlights": ["rate increase", "inflation target"],
      "score": 0.92
    },
    // ... 4 more results
  ]
}
```

**Research Query** → 10 results
```json
{
  "query_type": "research",
  "query": "Federal Reserve monetary policy interest rates inflation economic analysis (current date: 2025-01-21)",
  "num_results": 10,
  "results": [
    {
      "title": "The Impact of Interest Rate Changes on Inflation Dynamics",
      "url": "https://pubmed.ncbi.nlm.nih.gov/paper123",
      "domain": "pubmed.ncbi.nlm.nih.gov",
      "published_date": "2024-06-10",
      "text": "This study examines...",
      "highlights": ["monetary policy", "inflation control"],
      "score": 0.88
    },
    // ... 9 more results
  ]
}
```

**General Query** → 5 results
```json
{
  "query_type": "general",
  "query": "Federal Reserve interest rate policy 2024 fact check (current date: 2025-01-21)",
  "num_results": 5,
  "results": [
    {
      "title": "Understanding the Fed's 2024 Rate Decisions",
      "url": "https://brookings.edu/fed-analysis",
      "domain": "brookings.edu",
      "published_date": "2024-08-22",
      "text": "Economic experts note...",
      "highlights": ["rate hikes", "inflation response"],
      "score": 0.85
    },
    // ... 4 more results
  ]
}
```

**Historical Query** → 5 results (unlimited date range)
```json
{
  "query_type": "historical",
  "query": "Federal Reserve interest rate increases historical precedent inflation control (current date: 2025-01-21)",
  "num_results": 5,
  "results": [
    {
      "title": "The Volcker Era: Fighting Inflation in the 1980s",
      "url": "https://federalreservehistory.org/volcker",
      "domain": "federalreservehistory.org",
      "published_date": "1985-03-12",  // ← Decades-old precedent!
      "text": "During the early 1980s, the Federal Reserve...",
      "highlights": ["aggressive rate increases", "inflation reduction"],
      "score": 0.79
    },
    // ... 4 more results
  ]
}
```

#### Step 3: Evidence Aggregation

All 25 sources (5+10+5+5) are aggregated with full temporal metadata:

```json
{
  "claim": "The Federal Reserve raised interest rates to combat inflation in 2024",
  "timestamp": "2025-01-21T05:50:26Z",
  "search_summary": {
    "total_searches": 4,
    "successful_searches": 4,
    "total_results": 25
  },
  "results_by_type": {
    "news": { /* 5 results */ },
    "research": { /* 10 results */ },
    "general": { /* 5 results */ },
    "historical": { /* 5 results */ }
  },
  "all_results": [
    // All 25 sources combined with query_type labels
  ]
}
```

#### Step 4: AI Validation with Temporal Analysis

The Gemini model receives:
- ✅ The claim text
- ✅ All 25 evidence sources with published dates
- ✅ Current date context (injected in every query)
- ✅ Explicit temporal analysis instructions

**Validation Prompt Excerpt**:
```markdown
Claim: "The Federal Reserve raised interest rates to combat inflation in 2024"

Evidence collected from 4 search categories (25 total sources):

### News Evidence (5 sources, last 30 days)
Source 1: Fed Raises Rates to 5.5% Citing Inflation Concerns
Domain: reuters.com
Published: 2024-12-15
URL: https://reuters.com/fed-rates-2024
...

### Research Evidence (10 sources, last 2 years)
Source 1: The Impact of Interest Rate Changes on Inflation Dynamics
Domain: pubmed.ncbi.nlm.nih.gov
Published: 2024-06-10
...

### General Evidence (5 sources, last 2 years)
...

### Historical Evidence (5 sources, unlimited timeframe)
Source 1: The Volcker Era: Fighting Inflation in the 1980s
Domain: federalreservehistory.org
Published: 1985-03-12
...

## Temporal Analysis
Consider:
- Currency: How recent is the information? Are there more recent updates?
- Historical context: Has this claim's validity changed over time?
- Time-bound factors: Does the claim's truth depend on when it was made?
- Evolution: How has understanding of this topic evolved?

## Your Task
Validate this claim using the evidence provided. Include inline citations [1], [2], etc.
```

#### Step 5: Validation Output

```json
{
  "verdict": "TRUE",
  "confidence": 95,
  "summary": "The claim is accurate. The Federal Reserve raised interest rates multiple times in 2024 in response to persistent inflation [1][2][3].",
  "key_findings": [
    "The Fed raised rates to 5.5% in December 2024 [1]",
    "This marked the sixth consecutive rate increase aimed at inflation control [2]",
    "Historical precedent from the 1980s Volcker era shows similar aggressive rate increases were effective [4]"
  ],
  "temporal_analysis": {
    "claim_timeframe": "2024",
    "evidence_currency": "Highly current - latest source from 2024-12-15",
    "historical_context": "Consistent with past Fed responses to inflation, particularly the 1980s Volcker era",
    "temporal_verdict": "The claim's validity is supported by both recent evidence and historical patterns"
  },
  "sources": [
    {
      "id": 1,
      "title": "Fed Raises Rates to 5.5% Citing Inflation Concerns",
      "url": "https://reuters.com/fed-rates-2024",
      "source": "Reuters",
      "date": "2024-12-15",
      "type": "news",
      "relevance": "Primary evidence of rate increase",
      "credibility": "HIGH"
    },
    // ... more sources with dates
  ],
  "contradictions": []
}
```

---

## Validation Prompt Structures

### Summary Mode Prompt Components

Summary mode uses a simplified prompt focused on overall narrative validation:

```markdown
# FACT-CHECKING VALIDATION - SUMMARY MODE

You are a professional fact-checker analyzing an article's overall accuracy.

## Article Claims
{extracted_high_level_claims}

## Evidence Collected (25 sources total)

### News Evidence (Recent developments - last 30 days)
{formatted_news_evidence}

### Research Evidence (Academic/scientific sources - last 2 years)
{formatted_research_evidence}

### General Evidence (Expert analysis/fact-checking - last 2 years)
{formatted_general_evidence}

### Historical Evidence (Historical context/precedents - unlimited timeframe)
{formatted_historical_evidence}

## Your Task

Provide an overall assessment of the article's accuracy. Follow these guidelines:

### 1. Verdict Classification
- TRUE: Article is generally accurate
- FALSE: Article contains major factual errors
- MISLEADING: Article mixes truth with distortion
- UNVERIFIABLE: Cannot confirm article's main claims

### 2. Analysis Requirements
- Evaluate overall narrative accuracy
- Identify major factual errors if present
- Assess source credibility
- Consider context and framing

### 3. Output Format (STRICT JSON)
{
  "verdict": "TRUE|FALSE|MISLEADING|UNVERIFIABLE",
  "credibility_score": 85,
  "summary": "Brief explanation with citations [1][2]",
  "sources": [
    {
      "id": 1,
      "title": "Source title",
      "url": "https://source.url",
      "source": "Publication name",
      "date": "2025-01-21",
      "credibility": "HIGH|MEDIUM|LOW"
    }
  ]
}
```

### Thorough Mode Prompt Components

**Location**: `src/clients/gemini_validation_client.py` (lines 158-351)

The thorough validation prompt is structured as follows:

```markdown
# FACT-CHECKING VALIDATION - THOROUGH MODE

You are a professional fact-checker analyzing claims with comprehensive evidence.

## Claim Being Validated
{claim_text}

## Evidence Collected

### News Evidence (Recent developments - last 30 days)
{formatted_news_evidence}

### Research Evidence (Academic/scientific sources - last 2 years)
{formatted_research_evidence}

### General Evidence (Expert analysis/fact-checking - last 2 years)
{formatted_general_evidence}

### Historical Evidence (Historical context/precedents - unlimited timeframe)
{formatted_historical_evidence}

## Your Task

Validate this claim using the evidence provided. Follow these guidelines:

### 1. Verdict Classification
- TRUE: Claim is accurate and well-supported
- FALSE: Claim is demonstrably incorrect
- MISLEADING: Claim contains truth but misleads through omission/distortion
- UNVERIFIABLE: Insufficient evidence to confirm or deny

### 2. Confidence Scoring (0-100)
- 90-100: Overwhelming evidence, minimal doubt
- 70-89: Strong evidence, minor uncertainties
- 50-69: Moderate evidence, significant gaps
- 0-49: Weak evidence, major uncertainties

### 3. Analysis Requirements
- Source credibility assessment
- Consistency across evidence types
- Identification of contradictions
- Temporal validity (does time affect truth?)
- Context and nuance

### 4. Temporal Analysis
Consider:
- Currency: How recent is the information? Are there more recent updates?
- Historical context: Has this claim's validity changed over time?
- Time-bound factors: Does the claim's truth depend on when it was made?
- Evolution: How has understanding of this topic evolved?

## Output Format (STRICT JSON)
{
  "verdict": "TRUE|FALSE|MISLEADING|UNVERIFIABLE",
  "confidence": 85,
  "summary": "One-sentence verdict with primary reasoning",
  "key_findings": [
    "Finding 1 [1][2]",
    "Finding 2 [3]"
  ],
  "temporal_analysis": {
    "claim_timeframe": "When the claim refers to",
    "evidence_currency": "How recent/current the evidence is",
    "historical_context": "Relevant historical precedents",
    "temporal_verdict": "How time affects claim validity"
  },
  "contradictions": [
    "Description of any conflicting evidence"
  ],
  "sources": [
    {
      "id": 1,
      "title": "Source title",
      "url": "https://source.url",
      "source": "Publication name",
      "author": "Author if known",
      "date": "2025-01-21",
      "type": "news|research|general|historical",
      "relevance": "Why this source matters",
      "credibility": "HIGH|MEDIUM|LOW"
    }
  ]
}

CITATION REQUIREMENTS:
1. Extract 8-10 most credible sources
2. Use inline citations [1], [2] throughout analysis
3. Every factual claim must have a citation
4. Include full bibliographic details in sources array
```

---

## Output Schemas

### Summary Mode Validation Result Structure

```typescript
interface SummaryValidationResult {
  // Core verdict
  verdict: "TRUE" | "FALSE" | "MISLEADING" | "UNVERIFIABLE";
  credibility_score: number; // 0-100
  
  // Analysis
  summary: string; // Brief explanation with citations
  claims_analyzed: number; // Typically 1-2
  claims_true: number;
  claims_false: number;
  claims_misleading: number;
  
  // Sources (from shared evidence pool)
  sources: Array<{
    id: number;
    title: string;
    url: string;
    source: string;
    date: string;
    credibility: "HIGH" | "MEDIUM" | "LOW";
  }>;
  
  // Metadata
  num_sources: number; // Typically 25
  processing_time_ms: number;
  cost_usd: number;
}
```

### Thorough Mode Validation Result Structure

```typescript
interface SummaryValidationResult {
  // Core verdict
  verdict: "TRUE" | "FALSE" | "MISLEADING" | "UNVERIFIABLE";
  credibility_score: number; // 0-100
  
  // Analysis
  summary: string; // Brief explanation with citations
  claims_analyzed: number; // Typically 1-2
  claims_true: number;
  claims_false: number;
  claims_misleading: number;
  
  // Sources (from shared evidence pool)
  sources: Array<{
    id: number;
    title: string;
    url: string;
    source: string;
    date: string;
    credibility: "HIGH" | "MEDIUM" | "LOW";
  }>;
  
  // Metadata
  num_sources: number; // Typically 25
  processing_time_ms: number;
  cost_usd: number;
}
```

### Thorough Mode Validation Result Structure

```typescript
interface ValidationResult {
  // Core verdict
  verdict: "TRUE" | "FALSE" | "MISLEADING" | "UNVERIFIABLE";
  confidence: number; // 0-100
  
  // Analysis
  summary: string; // One-sentence verdict
  key_findings: string[]; // 3-5 main points with citations
  contradictions: string[]; // Conflicting evidence
  
  // Temporal analysis (unique to thorough mode)
  temporal_analysis: {
    claim_timeframe: string;      // When claim refers to
    evidence_currency: string;     // How recent evidence is
    historical_context: string;    // Historical precedents
    temporal_verdict: string;      // Time's effect on validity
  };
  
  // Sources with full temporal metadata
  sources: Array<{
    id: number;
    title: string;
    url: string;
    source: string;           // Publication name
    author?: string;
    date: string;            // Published date (CRITICAL)
    type: "news" | "research" | "general" | "historical";
    relevance: string;
    credibility: "HIGH" | "MEDIUM" | "LOW";
  }>;
  
  // Metadata
  claim: string;
  risk_level: "HIGH" | "MEDIUM" | "LOW";
  category: string;
  processing_time_ms: number;
  token_usage: {
    input_tokens: number;
    output_tokens: number;
    total_cost_usd: number;
  };
}
```

### Example Complete Output

```json
{
  "verdict": "TRUE",
  "confidence": 95,
  "summary": "The claim is accurate. The Federal Reserve raised interest rates multiple times in 2024 to combat persistent inflation, with the final increase bringing rates to 5.5% [1][2][3].",
  
  "key_findings": [
    "The Fed raised rates to 5.5% in December 2024, citing inflation concerns [1]",
    "This marked the sixth consecutive rate increase in 2024 [2]",
    "Recent inflation data showed 3.4% annual rate, justifying continued tightening [3]",
    "Historical precedent from the 1980s Volcker era demonstrates effectiveness of aggressive rate increases [5]"
  ],
  
  "temporal_analysis": {
    "claim_timeframe": "Throughout 2024",
    "evidence_currency": "Highly current - latest source from 2024-12-15, just 5 weeks ago",
    "historical_context": "Consistent with past Fed responses to inflation, particularly the 1980s Volcker era when rates reached 20% to control inflation. Current increases are more moderate but follow similar policy logic.",
    "temporal_verdict": "The claim's validity is strongly supported by both recent evidence and historical patterns. No contradictory information has emerged since the claim's timeframe."
  },
  
  "contradictions": [],
  
  "sources": [
    {
      "id": 1,
      "title": "Fed Raises Rates to 5.5% Citing Inflation Concerns",
      "url": "https://reuters.com/business/fed-rates-decision-2024-12",
      "source": "Reuters",
      "author": "Howard Schneider",
      "date": "2024-12-15",
      "type": "news",
      "relevance": "Primary evidence of the December 2024 rate increase announcement",
      "credibility": "HIGH"
    },
    {
      "id": 2,
      "title": "Federal Reserve's 2024 Monetary Policy Decisions",
      "url": "https://federalreserve.gov/newsevents/pressreleases/monetary20241215a.htm",
      "source": "Federal Reserve",
      "date": "2024-12-15",
      "type": "general",
      "relevance": "Official Fed statement confirming rate increase policy",
      "credibility": "HIGH"
    },
    {
      "id": 3,
      "title": "Inflation Data Shows Persistent Price Pressures",
      "url": "https://bls.gov/news.release/cpi.nr0.htm",
      "source": "Bureau of Labor Statistics",
      "date": "2024-12-12",
      "type": "general",
      "relevance": "Official inflation data justifying Fed's policy decisions",
      "credibility": "HIGH"
    },
    {
      "id": 4,
      "title": "The Effectiveness of Interest Rate Policy in Controlling Inflation",
      "url": "https://pubmed.ncbi.nlm.nih.gov/paper-12345",
      "source": "Journal of Monetary Economics",
      "author": "Smith, J. et al.",
      "date": "2024-08-20",
      "type": "research",
      "relevance": "Academic research supporting the effectiveness of rate increases",
      "credibility": "HIGH"
    },
    {
      "id": 5,
      "title": "The Volcker Era: Fighting Inflation in the 1980s",
      "url": "https://federalreservehistory.org/essays/volcker-disinflation",
      "source": "Federal Reserve History",
      "date": "1985-03-12",
      "type": "historical",
      "relevance": "Historical precedent showing aggressive rate increases successfully controlled inflation",
      "credibility": "HIGH"
    }
  ],
  
  "claim": "The Federal Reserve raised interest rates to combat inflation in 2024",
  "risk_level": "HIGH",
  "category": "Economic Policy",
  "processing_time_ms": 8420,
  "token_usage": {
    "input_tokens": 12500,
    "output_tokens": 850,
    "total_cost_usd": 0.0342
  }
}
```

---

## Configuration

### Environment Variables

Key configuration settings across both modes:

```bash
# Validation Mode
USE_THOROUGH_VALIDATION=true          # Enable thorough mode (vs standard)

# Exa Search Configuration
EXA_SEARCH_DEPTH=comprehensive        # Use 4-query comprehensive search
EXA_NUM_RESULTS_NEWS=5               # News query results
EXA_NUM_RESULTS_RESEARCH=10          # Research query results (more!)
EXA_NUM_RESULTS_GENERAL=5            # General query results
EXA_NUM_RESULTS_HISTORICAL=5         # Historical query results
EXA_DAYS_BACK_NEWS=30                # News: last 30 days
EXA_DAYS_BACK_HISTORICAL=unlimited   # Historical: no limit

# Gemini Model Settings
GEMINI_MODEL_THOROUGH=gemini-2.0-flash-exp        # Model for thorough mode
GEMINI_TEMPERATURE_THOROUGH=0.2                   # Lower temp = more consistent
GEMINI_MAX_TOKENS_THOROUGH=8192                   # Larger context for analysis
GEMINI_TOP_K_THOROUGH=40
GEMINI_TOP_P_THOROUGH=0.95

# Evidence Processing
MAX_EVIDENCE_CHARS_PER_SOURCE=2000   # Characters per source
MAX_HIGHLIGHTS_PER_SOURCE=5          # Highlights per source
ENABLE_DEDUPLICATION=true            # Remove duplicate evidence
SIMILARITY_THRESHOLD=0.85            # Deduplication sensitivity

# Parallel Processing
ENABLE_PARALLEL_VALIDATION=true      # Validate multiple claims simultaneously
MAX_CONCURRENT_VALIDATIONS=3         # Max parallel validations
VALIDATION_STAGGER_SECONDS=1.0       # Delay between starting validations

# Cost Management
MAX_CLAIMS_PER_ARTICLE=20            # Limit claims to validate
VALIDATE_HIGH_RISK_ONLY=true         # Only validate HIGH-risk claims
```

## Cost & Performance

### Summary Mode Costs

| Component | Tokens | Cost (USD) |
|-----------|--------|------------|
| Exa searches (4 queries) | - | $0.010 |
| Gemini input (~8K tokens) | 8,000 | $0.010 |
| Gemini output (~500 tokens) | 500 | $0.007 |
| **Total per article** | - | **$0.027** |

**Processing**:
- Total cost: ~$0.04 per article
- Processing time: 3-4 minutes
- Total sources reviewed: 25

### Thorough Mode Costs

| Component | Tokens | Cost (USD) |
|-----------|--------|------------|
| Exa searches (4 queries) | - | $0.010 |
| Gemini input (~12K tokens) | 12,000 | $0.015 |
| Gemini output (~800 tokens) | 800 | $0.012 |
| **Total per claim** | - | **$0.037** |

**Full Article (10 claims)**:
- Total cost: ~$0.37
- Processing time: 4-5 minutes
- Total sources reviewed: 250 (25 per claim)

### Cost Comparison

| Metric | Summary Mode | Thorough Mode (10 claims) |
|--------|--------------|---------------------------|
| Total Cost | $0.04 | $0.37 |
| Cost Multiplier | 1x | ~9x |
| Sources | 25 | 250 |
| Processing Time | 3-4 min | 4-5 min |
| Granularity | Article-level | Claim-level |

---

## Summary

### Key Takeaways

✅ **Temporal Context Everywhere**:
- Current date injected into every Exa query
- Published dates for every evidence source
- Explicit temporal analysis in validation prompt
- Date-based filtering optimized per query type

✅ **Comprehensive Evidence**:
- 4 parallel searches per claim (news, research, general, historical)
- 25 total sources per claim
- Domain filtering for quality control
- Historical searches have unlimited timeframe

✅ **Sophisticated Validation**:
- AI analyzes currency, historical context, temporal validity
- Source credibility assessment
- Contradiction detection
- Evidence synthesis across time periods

✅ **Complete Transparency**:
- Every source includes published date
- Full citation trail with inline references
- Temporal analysis section in output
- Processing metadata and costs

---

## For Backend Team

When integrating thorough mode results:

1. **Expect temporal_analysis field** in validation responses
2. **All sources include date field** - use for UI display/sorting
3. **Processing time is ~30-60s** for full article (10 claims)
4. **Cost is ~$0.04 per claim** - budget accordingly
5. **Historical sources may be decades old** - this is intentional!
6. **Evidence is pre-validated** - no need for additional source checking

### Database Schema Recommendations

```sql
CREATE TABLE validation_results (
  id UUID PRIMARY KEY,
  claim TEXT NOT NULL,
  verdict TEXT NOT NULL,
  confidence INTEGER NOT NULL,
  
  -- Temporal analysis
  claim_timeframe TEXT,
  evidence_currency TEXT,
  historical_context TEXT,
  temporal_verdict TEXT,
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  evidence_latest_date TIMESTAMP,  -- Most recent source date
  evidence_oldest_date TIMESTAMP,  -- Oldest source date (for historical)
  
  -- Metadata
  total_sources INTEGER,
  sources_news INTEGER,
  sources_research INTEGER,
  sources_general INTEGER,
  sources_historical INTEGER,
  
  -- Processing
  processing_time_ms INTEGER,
  cost_usd NUMERIC(10, 4)
);

CREATE TABLE validation_sources (
  id UUID PRIMARY KEY,
  validation_id UUID REFERENCES validation_results(id),
  citation_id INTEGER,
  title TEXT,
  url TEXT,
  source TEXT,
  author TEXT,
  published_date DATE,  -- CRITICAL: Store dates for filtering/sorting
  query_type TEXT,      -- news|research|general|historical
  credibility TEXT,     -- HIGH|MEDIUM|LOW
  relevance TEXT
);
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-21  
**Contact**: fact-check system maintainer
