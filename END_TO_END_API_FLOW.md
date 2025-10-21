# End-to-End API Flow: Complete Data Return Structure

## Overview

This document details the complete data flow from API call to final output, showing **exactly what data is returned at each stage** when fact-checking a URL using thorough mode.

---

## Table of Contents

1. [High-Level Flow Summary](#high-level-flow-summary)
2. [Stage 1: Content Extraction](#stage-1-content-extraction)
3. [Stage 2: Claim Extraction](#stage-2-claim-extraction)
4. [Stage 3: Evidence Search](#stage-3-evidence-search)
5. [Stage 4: Claim Validation](#stage-4-claim-validation)
6. [Stage 5: Article Generation](#stage-5-article-generation)
7. [Stage 6: Final Output](#stage-6-final-output)
8. [Complete Example Response](#complete-example-response)
9. [Database Storage Structure](#database-storage-structure)

---

## High-Level Flow Summary

```
User → API Call (URL) 
  ↓
1. Content Extraction (Exa API)
  ↓
2. Claim Extraction (Gemini)
  ↓
3. Evidence Search (Exa API: 4 parallel searches per claim)
  ↓
4. Claim Validation (Gemini: analyze each claim with evidence)
  ↓
5. Article Generation (Gemini: synthesize all validations into journalistic article)
  ↓
6. Final Output (JSON with reports, evidence, articles, metadata)
```

**Processing Time**: 30-60 seconds for typical article (10 claims)  
**Cost**: ~$0.40 total (~$0.04 per claim)

---

## Stage 1: Content Extraction

### Input
```json
{
  "url": "https://example.com/article"
}
```

### Process
- Uses Exa API `get_contents()` to extract article content
- Returns title, full text, highlights

### Output
```json
{
  "title": "Article Title Here",
  "text": "Full article content extracted...",
  "url": "https://example.com/article",
  "highlights": [
    "Key excerpt 1",
    "Key excerpt 2"
  ]
}
```

**Returned to next stage**: Content object for claim extraction

---

## Stage 2: Claim Extraction

### Input
```json
{
  "title": "Article Title",
  "text": "Full article content...",
  "url": "https://example.com/article"
}
```

### Process
- Gemini analyzes article text
- Extracts factual claims with risk levels
- Applies risk framework (HIGH/MEDIUM/LOW)
- Deduplicates similar claims

### Output
```json
{
  "claims": [
    {
      "claim": "The Federal Reserve raised interest rates to 5.5% in December 2024",
      "risk_level": "HIGH",
      "category": "Economic Policy",
      "context": "Article discusses monetary policy decisions amid inflation concerns",
      "risk_factors": [
        "Unsubstantiated Claims",
        "Could cause financial harm if incorrect"
      ],
      "speaker": "Article author",
      "source_url": "https://example.com/article",
      "extraction_timestamp": "2025-01-21T16:00:00Z"
    },
    {
      "claim": "Inflation reached 3.4% annually in 2024",
      "risk_level": "HIGH",
      "category": "Economic Policy",
      "context": "Supporting claim about economic conditions",
      "risk_factors": [
        "Specific numeric claim requiring verification"
      ],
      "speaker": "BLS data cited",
      "source_url": "https://example.com/article",
      "extraction_timestamp": "2025-01-21T16:00:00Z"
    }
    // ... more claims
  ],
  "extraction_metadata": {
    "prompt_tokens": 8500,
    "output_tokens": 450,
    "total_cost": 0.0085,
    "was_repaired": false
  }
}
```

**Returned to next stage**: List of HIGH-risk claims only (filtered)

---

## Stage 3: Evidence Search

### Input (per claim)
```json
{
  "claim": "The Federal Reserve raised interest rates to 5.5% in December 2024",
  "risk_level": "HIGH",
  "category": "Economic Policy"
}
```

### Process
For **each HIGH-risk claim**, execute 4 parallel Exa searches:
1. **News search** (last 30 days, 5 results)
2. **Research search** (last 2 years, 10 results)
3. **General search** (last 2 years, 5 results)
4. **Historical search** (unlimited timeframe, 5 results)

All queries include current date injection: `(current date: 2025-01-21)`

### Output (per claim)
```json
{
  "claim": "The Federal Reserve raised interest rates to 5.5% in December 2024",
  "timestamp": "2025-01-21T16:00:30Z",
  "risk_level": "HIGH",
  "category": "Economic Policy",
  
  "search_summary": {
    "total_searches": 4,
    "successful_searches": 4,
    "total_results": 25
  },
  
  "results_by_type": {
    "news": {
      "query_type": "news",
      "query": "Federal Reserve interest rate increase December 2024 (current date: 2025-01-21)",
      "num_results": 5,
      "results": [
        {
          "title": "Fed Raises Rates to 5.5% Amid Inflation Concerns",
          "url": "https://reuters.com/business/fed-rates-2024-12",
          "domain": "reuters.com",
          "published_date": "2024-12-15",
          "text": "The Federal Reserve announced today a 25 basis point increase...",
          "highlights": [
            "rates increased to 5.5%",
            "inflation remains above target",
            "policy continues aggressive tightening"
          ],
          "score": 0.92
        }
        // ... 4 more news results
      ]
    },
    
    "research": {
      "query_type": "research",
      "query": "Federal Reserve monetary policy interest rates inflation economic analysis (current date: 2025-01-21)",
      "num_results": 10,
      "results": [
        {
          "title": "The Effectiveness of Interest Rate Policy in Controlling Inflation",
          "url": "https://pubmed.ncbi.nlm.nih.gov/article-123",
          "domain": "pubmed.ncbi.nlm.nih.gov",
          "published_date": "2024-08-20",
          "text": "This study examines the relationship between interest rate adjustments...",
          "highlights": [
            "rate increases reduce inflation over 12-18 months",
            "historical effectiveness varies by economic context"
          ],
          "score": 0.88
        }
        // ... 9 more research results
      ]
    },
    
    "general": {
      "query_type": "general",
      "query": "Federal Reserve interest rate policy 2024 fact check (current date: 2025-01-21)",
      "num_results": 5,
      "results": [
        {
          "title": "Understanding the Fed's 2024 Rate Decisions",
          "url": "https://brookings.edu/fed-policy-2024",
          "domain": "brookings.edu",
          "published_date": "2024-12-16",
          "text": "Expert analysis of the Federal Reserve's latest policy moves...",
          "highlights": [
            "December increase marks sixth consecutive hike",
            "decision driven by persistent inflation"
          ],
          "score": 0.85
        }
        // ... 4 more general results
      ]
    },
    
    "historical": {
      "query_type": "historical",
      "query": "Federal Reserve interest rate increases historical precedent inflation control (current date: 2025-01-21)",
      "num_results": 5,
      "results": [
        {
          "title": "The Volcker Era: Fighting Inflation in the 1980s",
          "url": "https://federalreservehistory.org/volcker-disinflation",
          "domain": "federalreservehistory.org",
          "published_date": "1985-03-12",  // Historical precedent from decades ago
          "text": "During the early 1980s, Chairman Volcker raised rates aggressively...",
          "highlights": [
            "rates peaked at 20% in 1981",
            "successfully reduced inflation from 13% to 3%"
          ],
          "score": 0.79
        }
        // ... 4 more historical results
      ]
    }
  },
  
  "all_results": [
    // All 25 sources combined with query_type labels
  ]
}
```

**Returned to next stage**: Evidence package per claim (25 sources each)

---

## Stage 4: Claim Validation

### Input (per claim)
```json
{
  "claim": "The Federal Reserve raised interest rates to 5.5% in December 2024",
  "risk_level": "HIGH",
  "category": "Economic Policy",
  "evidence": {
    // Complete evidence package from Stage 3 (25 sources)
  }
}
```

### Process
- Gemini analyzes claim against all evidence
- Performs temporal analysis (currency, historical context)
- Generates verdict with confidence score
- Extracts 8-10 most credible sources as citations
- Identifies contradictions

### Output (per claim)
```json
{
  "claim": "The Federal Reserve raised interest rates to 5.5% in December 2024",
  "verdict": "TRUE",
  "confidence": 95,
  "risk_level": "HIGH",
  "category": "Economic Policy",
  
  "summary": "The claim is accurate. The Federal Reserve raised interest rates to 5.5% in December 2024 in response to persistent inflation, marking the sixth consecutive rate increase [1][2][3].",
  
  "key_findings": [
    "The Fed raised rates to 5.5% on December 15, 2024, citing inflation concerns [1]",
    "This marked the sixth consecutive rate increase aimed at inflation control [2]",
    "Recent inflation data showed 3.4% annual rate, justifying continued tightening [3]",
    "Historical precedent from the 1980s Volcker era demonstrates effectiveness of aggressive rate increases [5]"
  ],
  
  "temporal_analysis": {
    "claim_timeframe": "December 2024",
    "evidence_currency": "Highly current - latest source from 2024-12-15, just 5 weeks ago",
    "historical_context": "Consistent with past Fed responses to inflation, particularly the 1980s Volcker era when rates reached 20%. Current increases are more moderate but follow similar policy logic.",
    "temporal_verdict": "The claim's validity is strongly supported by both recent evidence and historical patterns. No contradictory information has emerged since the claim's timeframe."
  },
  
  "contradictions": [],
  
  "sources": [
    {
      "id": 1,
      "title": "Fed Raises Rates to 5.5% Amid Inflation Concerns",
      "url": "https://reuters.com/business/fed-rates-2024-12",
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
      "title": "The Effectiveness of Interest Rate Policy",
      "url": "https://pubmed.ncbi.nlm.nih.gov/paper-12345",
      "source": "Journal of Monetary Economics",
      "author": "Smith, J. et al.",
      "date": "2024-08-20",
      "type": "research",
      "relevance": "Academic research supporting effectiveness of rate increases",
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
    // ... up to 8-10 sources
  ],
  
  "processing_metadata": {
    "processing_time_ms": 8420,
    "token_usage": {
      "input_tokens": 12500,
      "output_tokens": 850,
      "total_cost_usd": 0.0342
    }
  },
  
  "raw_evidence_corpus": {
    // Full 25 sources with complete text (stored separately)
    // This is NOT included in the main report to keep it clean
  }
}
```

**Returned to next stage**: Validation result per claim

---

## Stage 5: Article Generation

### Input
```json
{
  "validation_results": [
    {
      // Validation result for claim 1
    },
    {
      // Validation result for claim 2
    }
    // ... all validated claims
  ]
}
```

### Process
- Gemini synthesizes all validation results
- Creates comprehensive journalistic article
- Aggregates and deduplicates references
- Structures with headline, sections, conclusion

### Output
```json
{
  "article_metadata": {
    "headline": "Fact Check: Federal Reserve Rate Policy in 2024",
    "subheadline": "Analysis of recent monetary policy claims and their accuracy",
    "lead_paragraph": "Recent claims about the Federal Reserve's interest rate decisions in 2024 have circulated widely. Our comprehensive fact-check examines these assertions against official data and expert analysis.",
    "author": "Fact Check Team",
    "publication_date": "2025-01-21",
    "reading_time_minutes": 8,
    "fact_check_verdict": "MOSTLY_TRUE",
    "claims_analyzed": 10,
    "claims_verified_true": 7,
    "claims_verified_false": 1,
    "claims_misleading": 2
  },
  
  "article_sections": [
    {
      "section_title": "The Claim",
      "section_type": "introduction",
      "content": "Multiple sources have reported that the Federal Reserve raised interest rates to 5.5% in December 2024 to combat inflation. We investigated this claim and related assertions.",
      "claims_addressed": [1, 2]
    },
    {
      "section_title": "What We Found",
      "section_type": "analysis",
      "content": "Our investigation confirms that the Federal Reserve did indeed raise rates to 5.5% on December 15, 2024 [1][2]. This marked the sixth consecutive rate increase of 2024, bringing the federal funds rate to its highest level since 2001...",
      "claims_addressed": [1, 2, 3],
      "verdict_summary": "TRUE"
    },
    {
      "section_title": "Historical Context",
      "section_type": "context",
      "content": "This rate increase follows a pattern similar to the Federal Reserve's actions during the 1980s Volcker era, when aggressive rate hikes successfully brought inflation under control [5]...",
      "claims_addressed": [1],
      "supporting_evidence": [5, 8]
    },
    {
      "section_title": "Expert Analysis",
      "section_type": "expert_opinion",
      "content": "Economic experts from the Brookings Institution note that the December increase was driven by persistent inflation data showing 3.4% annual rates [3][4]...",
      "claims_addressed": [2, 3],
      "supporting_evidence": [3, 4, 6]
    },
    {
      "section_title": "The Bottom Line",
      "section_type": "conclusion",
      "content": "The core claim is TRUE. The Federal Reserve raised interest rates to 5.5% in December 2024, as confirmed by official Fed statements and news reports. Supporting claims about inflation rates and policy rationale are also accurate.",
      "final_verdict": "TRUE",
      "confidence_level": 95
    }
  ],
  
  "references": [
    {
      "citation_id": 1,
      "title": "Fed Raises Rates to 5.5% Amid Inflation Concerns",
      "publication": "Reuters",
      "author": "Howard Schneider",
      "date": "2024-12-15",
      "url": "https://reuters.com/business/fed-rates-2024-12",
      "type": "news",
      "credibility": "HIGH"
    }
    // ... all deduplicated references (typically 15-25)
  ],
  
  "generation_metadata": {
    "generated_at": "2025-01-21T16:01:45Z",
    "model": "gemini-2.5-flash",
    "claims_synthesized": 10,
    "total_references": 23,
    "token_usage": {
      "input_tokens": 15000,
      "output_tokens": 2500,
      "total_cost_usd": 0.045
    }
  }
}
```

**Returned to next stage**: Complete article JSON

---

## Stage 6: Final Output

### Complete Response Structure

The API returns a comprehensive JSON object with THREE main sections:

```json
{
  "report": {
    // Clean validation report without raw evidence
  },
  "raw_evidence": {
    // Complete evidence corpus for each claim (stored separately)
  },
  "article": {
    // Generated journalistic article (if enabled)
  },
  "metadata": {
    // Processing statistics and costs
  }
}
```

### 6.1: Clean Report Section

The clean report contains the **analysis for each high-risk claim**, showing why it's correct or incorrect through evidence synthesis.

#### Overview Structure

```json
{
  "report": {
    "status": "SUCCESS",
    "timestamp": "2025-01-21T16:01:50Z",
    "elapsed_time": 45.2,
    
    "statistics": {
      "total_claims": 15,
      "high_risk_claims": 10,
      "validated_claims": 10,
      "claims_with_evidence": 10,
      "average_sources_per_claim": 25.0,
      "total_validation_cost": 0.342,
      
      "verdict_breakdown": {
        "true": 7,
        "false": 1,
        "misleading": 2,
        "unverified": 0
      }
    },
    
    "validation_results": [
      // Array of detailed claim analyses (see examples below)
    ]
  }
}
```

---

#### Example 1: TRUE Verdict - Complete Analysis

This shows how the system explains WHY a claim is correct:

```json
{
  "claim": "The Federal Reserve raised interest rates to 5.5% in December 2024",
  "verdict": "TRUE",
  "confidence": 95,
  "risk_level": "HIGH",
  "category": "Economic Policy",
  
  "summary": "The claim is accurate. The Federal Reserve raised interest rates to 5.5% in December 2024 in response to persistent inflation, marking the sixth consecutive rate increase [1][2][3].",
  
  "key_findings": [
    "The Fed raised rates to 5.5% on December 15, 2024, citing inflation concerns [1]",
    "This marked the sixth consecutive rate increase aimed at inflation control [2]",
    "Recent inflation data showed 3.4% annual rate, justifying continued tightening [3]",
    "Historical precedent from the 1980s Volcker era demonstrates effectiveness of aggressive rate increases [5]",
    "Multiple credible news sources and official Fed statements confirm this policy decision [1][2][4]"
  ],
  
  "temporal_analysis": {
    "claim_timeframe": "December 2024",
    "evidence_currency": "Highly current - latest source from 2024-12-15, just 5 weeks ago",
    "historical_context": "Consistent with past Fed responses to inflation, particularly the 1980s Volcker era when rates reached 20%. Current increases are more moderate but follow similar policy logic.",
    "temporal_verdict": "The claim's validity is strongly supported by both recent evidence and historical patterns. No contradictory information has emerged since the claim's timeframe."
  },
  
  "contradictions": [],
  
  "sources": [
    {
      "id": 1,
      "title": "Fed Raises Rates to 5.5% Amid Inflation Concerns",
      "url": "https://reuters.com/business/fed-rates-2024-12",
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
      "title": "Understanding the Fed's 2024 Rate Decisions",
      "url": "https://brookings.edu/fed-policy-2024",
      "source": "Brookings Institution",
      "date": "2024-12-16",
      "type": "general",
      "relevance": "Expert analysis confirming policy rationale",
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
  
  "processing_metadata": {
    "processing_time_ms": 8420,
    "token_usage": {
      "input_tokens": 12500,
      "output_tokens": 850,
      "total_cost_usd": 0.0342
    }
  }
}
```

---

#### Example 2: FALSE Verdict - Complete Analysis

This shows how the system explains WHY a claim is incorrect:

```json
{
  "claim": "The unemployment rate reached 15% in 2024",
  "verdict": "FALSE",
  "confidence": 98,
  "risk_level": "HIGH",
  "category": "Economic Policy",
  
  "summary": "This claim is false. Official Bureau of Labor Statistics data shows the unemployment rate remained between 3.7% and 4.1% throughout 2024, never approaching 15% [1][2].",
  
  "key_findings": [
    "BLS monthly employment reports consistently show unemployment between 3.7-4.1% throughout 2024 [1]",
    "The 15% figure has no basis in official government data or credible economic sources [2]",
    "Multiple independent fact-checking organizations have debunked this claim [3][4]",
    "The last time US unemployment reached 15% was during the Great Depression in the 1930s [5]",
    "Current unemployment rates are near historic lows, not highs [1][6]"
  ],
  
  "temporal_analysis": {
    "claim_timeframe": "Throughout 2024",
    "evidence_currency": "Highly current - BLS monthly reports through December 2024, published within days of claim",
    "historical_context": "Current unemployment rates (3.7-4.1%) are near historic lows. The 15% unemployment rate hasn't occurred in the US since the 1940s during World War II demobilization. Even during the 2008 financial crisis, unemployment peaked at 10%.",
    "temporal_verdict": "The claim is demonstrably false based on contemporaneous official government data. No credible economic source supports this figure. The claim appears to fabricate or severely misrepresent employment statistics."
  },
  
  "contradictions": [],
  
  "sources": [
    {
      "id": 1,
      "title": "Employment Situation Summary - December 2024",
      "url": "https://bls.gov/news.release/empsit.nr0.htm",
      "source": "Bureau of Labor Statistics",
      "date": "2024-12-06",
      "type": "general",
      "relevance": "Official government employment data showing actual unemployment rate of 3.9%",
      "credibility": "HIGH"
    },
    {
      "id": 2,
      "title": "2024 Employment Data: Year in Review",
      "url": "https://bls.gov/opub/mlr/2024/article/employment-review.htm",
      "source": "Bureau of Labor Statistics",
      "date": "2024-12-20",
      "type": "general",
      "relevance": "Comprehensive annual review confirming unemployment rates throughout 2024",
      "credibility": "HIGH"
    },
    {
      "id": 3,
      "title": "Fact Check: False Claim About 15% Unemployment",
      "url": "https://factcheck.org/2024/11/unemployment-claim-false/",
      "source": "FactCheck.org",
      "date": "2024-11-22",
      "type": "general",
      "relevance": "Independent fact-check debunking the 15% claim",
      "credibility": "HIGH"
    },
    {
      "id": 4,
      "title": "Debunking Viral Unemployment Misinformation",
      "url": "https://politifact.com/factchecks/2024/dec/unemployment-rate-false/",
      "source": "PolitiFact",
      "date": "2024-12-01",
      "type": "general",
      "relevance": "Additional independent verification that claim is false",
      "credibility": "HIGH"
    },
    {
      "id": 5,
      "title": "Historical Unemployment Rates in the United States",
      "url": "https://bls.gov/opub/mlr/2016/article/historical-unemployment.htm",
      "source": "Bureau of Labor Statistics",
      "date": "2016-06-15",
      "type": "historical",
      "relevance": "Historical data showing 15% unemployment last occurred in 1940s",
      "credibility": "HIGH"
    },
    {
      "id": 6,
      "title": "US Labor Market Remains Strong in 2024",
      "url": "https://brookings.edu/articles/labor-market-2024-analysis/",
      "source": "Brookings Institution",
      "author": "Janet Smith",
      "date": "2024-11-18",
      "type": "general",
      "relevance": "Expert analysis confirming low unemployment rates",
      "credibility": "HIGH"
    }
  ],
  
  "processing_metadata": {
    "processing_time_ms": 7850,
    "token_usage": {
      "input_tokens": 11200,
      "output_tokens": 920,
      "total_cost_usd": 0.0315
    }
  }
}
```

---

#### Example 3: MISLEADING Verdict - Complete Analysis

This shows how the system explains WHY a claim is misleading (contains truth but omits critical context):

```json
{
  "claim": "Crime rates are at an all-time high",
  "verdict": "MISLEADING",
  "confidence": 87,
  "risk_level": "HIGH",
  "category": "Public Safety",
  
  "summary": "This claim is misleading. While certain crime categories increased in specific cities, overall national crime rates remain near historic lows according to FBI data [1][2]. The claim cherry-picks data and omits crucial context about long-term trends.",
  
  "key_findings": [
    "FBI data shows violent crime decreased 3% nationally in 2024 compared to 2023 [1]",
    "Property crime also decreased 2.4% in the same period [1]",
    "Current crime rates are 40-50% lower than the peaks of the early 1990s [2][5]",
    "However, some cities did experience increases in specific categories like retail theft and auto theft [3]",
    "The claim selectively focuses on isolated increases while ignoring broader national downward trends [4]",
    "Major news coverage has disproportionately highlighted local crime spikes without national context [6]"
  ],
  
  "temporal_analysis": {
    "claim_timeframe": "Present day (2024)",
    "evidence_currency": "Very recent - FBI preliminary data from Q3 2024 released December 2024",
    "historical_context": "Crime peaked in the early 1990s with violent crime rates nearly double current levels. After steady declines through the 2000s and 2010s, rates briefly increased during 2020-2021 pandemic disruptions but have since resumed declining. Current rates are near 50-year lows, not highs.",
    "temporal_verdict": "The claim is misleading because it suggests unprecedented crime levels when the opposite is true historically. While recent years saw some localized increases, the long-term trend shows dramatic decreases. The claim conflates perception with reality."
  },
  
  "contradictions": [
    "Claim states 'all-time high' but FBI comprehensive data shows rates near historic lows",
    "National statistics directly contradict the blanket assertion about overall crime levels",
    "Historical comparison reveals current rates are 40-50% below 1990s peaks"
  ],
  
  "sources": [
    {
      "id": 1,
      "title": "Crime in the United States - 2024 Preliminary Report",
      "url": "https://fbi.gov/services/cjis/ucr/crime-us-2024-preliminary",
      "source": "FBI",
      "date": "2024-12-15",
      "type": "general",
      "relevance": "Official national crime statistics showing overall decreases",
      "credibility": "HIGH"
    },
    {
      "id": 2,
      "title": "Violent Crime Rates: 30-Year Trend Analysis",
      "url": "https://bjs.gov/content/pub/pdf/cv24.pdf",
      "source": "Bureau of Justice Statistics",
      "date": "2024-10-20",
      "type": "research",
      "relevance": "Long-term data showing current rates well below historical peaks",
      "credibility": "HIGH"
    },
    {
      "id": 3,
      "title": "Urban Crime Trends: A Mixed Picture in 2024",
      "url": "https://brennancenter.org/our-work/analysis-opinion/urban-crime-trends-2024",
      "source": "Brennan Center for Justice",
      "author": "Dr. Emma Rodriguez",
      "date": "2024-08-20",
      "type": "research",
      "relevance": "Nuanced analysis showing localized increases amid national decreases",
      "credibility": "HIGH"
    },
    {
      "id": 4,
      "title": "Fact Check: Crime Statistics Often Misrepresented",
      "url": "https://factcheck.org/2024/10/crime-statistics-context/",
      "source": "FactCheck.org",
      "date": "2024-10-15",
      "type": "general",
      "relevance": "Analysis of how crime data is frequently presented without context",
      "credibility": "HIGH"
    },
    {
      "id": 5,
      "title": "Historical Crime Rates: 1960-2024",
      "url": "https://ucr.fbi.gov/crime-in-the-u.s/2024/preliminary-report/tables/historical-data",
      "source": "FBI",
      "date": "2024-12-15",
      "type": "historical",
      "relevance": "Comprehensive historical data showing 1990s peaks and current lows",
      "credibility": "HIGH"
    },
    {
      "id": 6,
      "title": "Crime Perception vs. Reality: A 2024 Study",
      "url": "https://journals.sagepub.com/doi/10.1177/crime-perception-2024",
      "source": "Journal of Criminal Justice",
      "author": "Chen, M. et al.",
      "date": "2024-09-10",
      "type": "research",
      "relevance": "Research showing public perception of crime often diverges from statistics",
      "credibility": "HIGH"
    }
  ],
  
  "processing_metadata": {
    "processing_time_ms": 9200,
    "token_usage": {
      "input_tokens": 13800,
      "output_tokens": 1050,
      "total_cost_usd": 0.0385
    }
  }
}
```

---

### Key Components of Each Analysis

Every claim validation includes:

1. **Verdict** - TRUE, FALSE, MISLEADING, or UNVERIFIABLE
2. **Confidence** - 0-100 score of certainty
3. **Summary** - 1-2 sentence explanation with citations
4. **Key Findings** - 3-6 bullet points showing **WHY** the verdict was reached
5. **Temporal Analysis** - Time-based context and currency evaluation
6. **Contradictions** - Conflicting evidence (if any)
7. **Sources** - 5-10 most credible sources with full metadata
8. **Processing Metadata** - Cost and performance metrics

### 6.2: Raw Evidence Section

```json
{
  "raw_evidence": {
    "timestamp": "2025-01-21T16:01:50Z",
    
    "search_results": [
      {
        // Complete Exa search results for claim 1 (all 25 sources)
        "claim": "The Federal Reserve raised interest rates...",
        "search_summary": {
          "total_searches": 4,
          "total_results": 25
        },
        "results_by_type": {
          "news": { /* 5 full results */ },
          "research": { /* 10 full results */ },
          "general": { /* 5 full results */ },
          "historical": { /* 5 full results */ }
        },
        "all_results": [ /* All 25 sources */ ]
      }
      // ... evidence for 9 more claims
    ],
    
    "evidence_by_claim": [
      {
        "claim": "The Federal Reserve raised interest rates...",
        "raw_evidence_corpus": {
          // Complete unprocessed evidence with full text
          "news_evidence": "Full formatted text...",
          "research_evidence": "Full formatted text...",
          "general_evidence": "Full formatted text...",
          "historical_evidence": "Full formatted text..."
        }
      }
      // ... corpus for 9 more claims
    ]
  }
}
```

### 6.3: Article Section

```json
{
  "article": {
    "article_metadata": {
      "headline": "Fact Check: Federal Reserve Rate Policy in 2024",
      "subheadline": "Analysis of recent monetary policy claims",
      "lead_paragraph": "Recent claims about the Federal Reserve...",
      "author": "Fact Check Team",
      "publication_date": "2025-01-21",
      "reading_time_minutes": 8,
      "fact_check_verdict": "MOSTLY_TRUE",
      "claims_analyzed": 10,
      "claims_verified_true": 7,
      "claims_verified_false": 1,
      "claims_misleading": 2
    },
    
    "article_sections": [
      {
        "section_title": "The Claim",
        "section_type": "introduction",
        "content": "Multiple sources have reported...",
        "claims_addressed": [1, 2]
      },
      {
        "section_title": "What We Found",
        "section_type": "analysis",
        "content": "Our investigation confirms...",
        "claims_addressed": [1, 2, 3],
        "verdict_summary": "TRUE"
      }
      // ... more sections
    ],
    
    "references": [
      // All deduplicated references from all claims (15-25 total)
    ],
    
    "generation_metadata": {
      "generated_at": "2025-01-21T16:01:45Z",
      "model": "gemini-2.5-flash",
      "claims_synthesized": 10,
      "total_references": 23
    }
  }
}
```

### 6.4: Metadata Section

```json
{
  "metadata": {
    "submission": {
      "url": "https://example.com/article",
      "submitted_at": "2025-01-21T16:00:00Z",
      "processing_mode": "thorough",
      "user_id": "user_123"
    },
    
    "processing_config": {
      "use_thorough_validation": true,
      "use_comprehensive_search": true,
      "validate_high_risk_only": true,
      "enable_article_generation": true,
      "max_claims_per_article": 20
    },
    
    "cost_breakdown": {
      "content_extraction": 0.001,
      "claim_extraction": 0.0085,
      "evidence_searches": 0.100,  // 4 searches × 10 claims
      "claim_validations": 0.342,  // 10 claims × $0.0342
      "article_generation": 0.045,
      "total_cost": 0.4965
    },
    
    "processing_statistics": {
      "total_duration_seconds": 45.2,
      "content_extraction_seconds": 2.1,
      "claim_extraction_seconds": 3.8,
      "evidence_search_seconds": 12.5,
      "validation_seconds": 24.3,
      "article_generation_seconds": 2.5,
      
      "total_tokens": {
        "input_tokens": 135000,
        "output_tokens": 15500,
        "total": 150500
      },
      
      "api_calls": {
        "exa_searches": 40,  // 4 per claim × 10 claims
        "gemini_calls": 12   // claim extraction + 10 validations + article
      }
    },
    
    "json_repair_statistics": {
      "claims_extraction_repaired": false,
      "validation_repaired": false,
      "article_generation_repaired": false,
      "total_repairs": 0
    }
  }
}
```

---

## Complete Example Response

Here's a simplified complete response showing the structure:

```json
{
  "report": {
    "status": "SUCCESS",
    "timestamp": "2025-01-21T16:01:50Z",
    "elapsed_time": 45.2,
    "statistics": {
      "total_claims": 15,
      "high_risk_claims": 10,
      "validated_claims": 10,
      "claims_with_evidence": 10,
      "average_sources_per_claim": 25.0,
      "total_validation_cost": 0.342,
      "verdict_breakdown": {
        "true": 7,
        "false": 1,
        "misleading": 2,
        "unverified": 0
      }
    },
    "validation_results": [
      {
        "claim": "The Federal Reserve raised interest rates to 5.5% in December 2024",
        "verdict": "TRUE",
        "confidence": 95,
        "risk_level": "HIGH",
        "category": "Economic Policy",
        "summary": "The claim is accurate. The Federal Reserve raised interest rates to 5.5% in December 2024...",
        "key_findings": [
          "The Fed raised rates to 5.5% on December 15, 2024 [1]",
          "This marked the sixth consecutive rate increase [2]"
        ],
        "temporal_analysis": {
          "claim_timeframe": "December 2024",
          "evidence_currency": "Highly current - latest source from 2024-12-15",
          "historical_context": "Consistent with 1980s Volcker era policies",
          "temporal_verdict": "Strongly supported by recent and historical evidence"
        },
        "sources": [
          {
            "id": 1,
            "title": "Fed Raises Rates to 5.5%",
            "source": "Reuters",
            "date": "2024-12-15",
            "type": "news",
            "credibility": "HIGH"
          }
        ]
      }
    ]
  },
  
  "raw_evidence": {
    "timestamp": "2025-01-21T16:01:50Z",
    "search_results": [
      {
        "claim": "The Federal Reserve raised interest rates...",
        "search_summary": {
          "total_searches": 4,
          "total_results": 25
        },
        "results_by_type": {
          "news": { "num_results": 5, "results": [...] },
          "research": { "num_results": 10, "results": [...] },
          "general": { "num_results": 5, "results": [...] },
          "historical": { "num_results": 5, "results": [...] }
        }
      }
    ]
  },
  
  "article": {
    "article_metadata": {
      "headline": "Fact Check: Federal Reserve Rate Policy in 2024",
      "fact_check_verdict": "MOSTLY_TRUE",
      "claims_analyzed": 10,
      "reading_time_minutes": 8
    },
    "article_sections": [
      {
        "section_title": "The Claim",
        "content": "Multiple sources have reported..."
      },
      {
        "section_title": "What We Found",
        "content": "Our investigation confirms..."
      }
    ],
    "references": [...]
  },
  
  "metadata": {
    "submission": {
      "url": "https://example.com/article",
      "processing_mode": "thorough"
    },
    "cost_breakdown": {
      "total_cost": 0.4965
    },
    "processing_statistics": {
      "total_duration_seconds": 45.2
    }
  }
}
```

---

## Database Storage Structure

When saved to Supabase, the data is stored across multiple tables:

### Table: `submissions`
```sql
{
  id: uuid,
  url: text,
  submitted_at: timestamp,
  processing_mode: text,
  status: text,
  user_id: uuid,
  
  -- Processing config
  config_json: jsonb,
  
  -- Costs and statistics
  total_cost: numeric,
  processing_duration_seconds: numeric,
  total_claims: integer,
  high_risk_claims: integer,
  validated_claims: integer
}
```

### Table: `crawled_content`
```sql
{
  id: uuid,
  submission_id: uuid,  -- FK
  title: text,
  content_text: text,
  url: text,
  highlights: jsonb,
  extracted_at: timestamp
}
```

### Table: `extracted_claims`
```sql
{
  id: uuid,
  submission_id: uuid,  -- FK
  claim_text: text,
  risk_level: text,
  category: text,
  context: text,
  risk_factors: jsonb,
  speaker: text,
  extraction_timestamp: timestamp
}
```

### Table: `exa_search_responses`
```sql
{
  id: uuid,
  claim_id: uuid,  -- FK
  search_summary: jsonb,
  results_by_type: jsonb,  -- News, research, general, historical
  all_results: jsonb,
  search_timestamp: timestamp
}
```

### Table: `validation_results`
```sql
{
  id: uuid,
  claim_id: uuid,  -- FK
  verdict: text,
  confidence: integer,
  summary: text,
  key_findings: jsonb,
  
  -- Temporal analysis
  claim_timeframe: text,
  evidence_currency: text,
  historical_context: text,
  temporal_verdict: text,
  
  -- Sources (top 8-10 cited)
  sources: jsonb,
  contradictions: jsonb,
  
  -- Processing metadata
  processing_time_ms: integer,
  token_usage: jsonb,
  cost: numeric,
  
  validated_at: timestamp
}
```

### Table: `generated_articles`
```sql
{
  id: uuid,
  submission_id: uuid,  -- FK
  article_metadata: jsonb,
  article_sections: jsonb,
  references: jsonb,
  generation_metadata: jsonb,
  generated_at: timestamp
}
```

---

## Key Takeaways for Backend Integration

### 1. **Separate Data Streams**
The system returns THREE distinct data streams:
- **Clean Report**: For user display (no huge evidence dumps)
- **Raw Evidence**: For archival/debugging (full 25 sources per claim)
- **Article**: For publication (synthesized narrative)

### 2. **Temporal Metadata Everywhere**
Every source, every validation includes published dates and temporal analysis.

### 3. **Cost Tracking**
Complete cost breakdown at every stage for budget management.

### 4. **Processing Statistics**
Duration, token counts, API calls - full transparency.

### 5. **Verdict Categorization**
Clear verdicts: TRUE, FALSE, MISLEADING, UNVERIFIED with confidence scores.

### 6. **Citation Trail**
Every claim in validations and articles has inline citations [1][2][3] linking to sources.

### 7. **Scalable Structure**
Can handle 1-20 claims per article, each with 25 sources = up to 500 sources total.

### 8. **Status Tracking**
Monitor progress: content → claims → evidence → validation → article.

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-21  
**Recommended Next Steps**: 
1. Design database schema based on storage structure
2. Create API endpoints for each stage
3. Implement progress tracking for long-running operations
4. Build UI components for report, article, and evidence display
5. Add cost monitoring and budget alerts
