# article_data Field Structure

The `article_data` field contains structured JSON from the Railway API's fact-check process.

## Database Schema
- **Column**: `article_data`
- **Type**: JSONB (PostgreSQL)
- **Nullable**: Yes
- **Location**: `articles` table

## API Endpoint
Available at: `GET /api/v1/articles/{id}/full`

Response structure:
```json
{
  "article": {
    "id": "uuid",
    "title": "...",
    "article_data": { /* Structure below */ },
    "crawled_content": "raw text..."
  }
}
```

## article_data JSON Structure

From Railway API response at `api_result.get("article_data")`:

```json
{
  "article_metadata": {
    "title": "Article title",
    "author": "Author name",
    "publish_date": "ISO date",
    "source_url": "https://..."
  },
  
  "verdict_card": {
    "overall_verdict": "TRUE | MOSTLY TRUE | MIXED | MOSTLY FALSE | FALSE",
    "confidence_level": "HIGH | MEDIUM | LOW",
    "color_code": "#hex"
  },
  
  "verdict_summary": {
    "overall_verdict": "String verdict",
    "reliability_score": 85,
    "confidence": "HIGH",
    "verdict_explanation": "Detailed explanation...",
    "key_supporting_evidence": ["Evidence 1", "Evidence 2"]
  },
  
  "executive_summary": {
    "claims_checked": 4,
    "verdicts_summary": {
      "true": 2,
      "mostly_true": 1,
      "mixed": 0,
      "mostly_false": 1,
      "false": 0
    },
    "key_findings": ["Finding 1", "Finding 2"],
    "bottom_line": "Summary statement",
    "article_accuracy_assessment": "Overall assessment"
  },
  
  "what_readers_should_know": [
    {
      "key_point": "Important fact",
      "action": "What to do with this info",
      "icon": "ℹ️",
      "priority": "HIGH"
    }
  ],
  
  "claim_analysis_sections": [
    {
      "claim_id": 1,
      "claim_text": "The claim being checked",
      "claim_source": "Source of claim",
      "verdict": "TRUE",
      "verdict_icon": "✅",
      "verdict_explanation": "Why this verdict",
      "evidence": ["Evidence 1", "Evidence 2"],
      "sources": [
        {
          "citation_number": 1,
          "title": "Source title",
          "url": "https://...",
          "credibility_rating": "HIGH"
        }
      ]
    }
  ],
  
  "references": [
    {
      "citation_number": 1,
      "full_citation": "Full bibliographic citation",
      "url": "https://...",
      "access_date": "2024-01-01",
      "source_type": "news | academic | government",
      "credibility_rating": "HIGH | MEDIUM | LOW",
      "relevance_note": "Why this source matters"
    }
  ],
  
  "key_evidence": {
    "supporting": ["Quote 1", "Quote 2"],
    "contradicting": ["Quote 3"],
    "context": ["Background info"]
  },
  
  "methodology_transparency": {
    "verification_steps": ["Step 1", "Step 2"],
    "sources_consulted": 140,
    "experts_contacted": ["Expert 1"],
    "limitations": ["Limitation 1"],
    "conflicts_of_interest": "None disclosed"
  },
  
  "evidence_strength_summary": {
    "overall_strength": "STRONG",
    "source_diversity": "HIGH",
    "corroboration_level": "MULTIPLE_INDEPENDENT_SOURCES"
  },
  
  "missing_context": [
    {
      "context_item": "Important missing info",
      "impact": "How this affects understanding"
    }
  ],
  
  "how_we_verified": {
    "steps": ["Verification step 1", "Step 2"],
    "sources_used": ["Source type 1", "Source type 2"],
    "time_spent": "2 hours"
  },
  
  "visual_evidence": {
    "charts": [],
    "infographics": [],
    "timeline": []
  },
  
  "reader_guidance": {
    "key_takeaways": ["Takeaway 1", "Takeaway 2"],
    "red_flags": ["Warning 1"],
    "recommended_actions": ["Action 1"]
  },
  
  "corrections_and_updates": [],
  
  "sidebar_elements": {
    "related_articles": [],
    "expert_quotes": [],
    "high_risk_claims_panel": {
      "claims": [],
      "key_evidence": []
    }
  },
  
  "social_sharing_optimized": {
    "share_text": "Shareable summary",
    "hashtags": ["#factcheck"]
  },
  
  "generation_metadata": {
    "generated_at": "ISO timestamp",
    "model_version": "1.0",
    "processing_time_seconds": 45.2
  }
}
```

## Usage Examples

### Frontend: Display Verdict Card
```typescript
const { verdict_card, verdict_summary } = article.article_data;
<VerdictBadge 
  verdict={verdict_card.overall_verdict}
  score={verdict_summary.reliability_score}
  confidence={verdict_summary.confidence}
/>
```

### Frontend: Render Claims
```typescript
const { claim_analysis_sections } = article.article_data;
claim_analysis_sections.map(claim => (
  <ClaimCard
    key={claim.claim_id}
    text={claim.claim_text}
    verdict={claim.verdict}
    evidence={claim.evidence}
  />
))
```

### Frontend: Show References
```typescript
const { references } = article.article_data;
<ReferenceList>
  {references.map(ref => (
    <Citation
      key={ref.citation_number}
      citation={ref.full_citation}
      url={ref.url}
      credibility={ref.credibility_rating}
    />
  ))}
</ReferenceList>
```

## Notes

- **Populated When**: Article goes through fact-check process
- **Source**: Railway API's `/result` endpoint
- **Storage**: As JSON in PostgreSQL (efficient querying with JSONB operators)
- **Fallback**: If null, use `crawled_content` for plain text display
- **Size**: Typically 140+ references, 4 claims, ~15-20KB JSON

## Migration History
- `6134904aa8f0`: Replaced `article_text` (Text) with `article_data` (JSONB)
- Applied: 2025-11-10
