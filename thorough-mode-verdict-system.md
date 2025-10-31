# Thorough Mode Overall Verdict & Credibility System

## Overview

Yes, thorough mode DOES provide an overall credibility rating and verdict assessment for the entire article being fact-checked, similar to summary mode's scoring system but with much richer detail and context.

## Comparison: Summary vs Thorough Mode Verdicts

### Summary Mode
- **Simple Categorical Verdict**: `TRUE`, `FALSE`, `MISLEADING`, `MISINFORMATION`, `UNVERIFIED`
- **Confidence Score**: 0-100 numeric value
- **Brief Summary**: Short text explanation
- **Single Overall Assessment**: One verdict for the entire article

### Thorough Mode
- **Multiple Verdict Layers**: Individual claim verdicts PLUS overall article assessment
- **Rich Credibility Framework**: Multiple dimensions of trustworthiness
- **Detailed Rating System**: Qualitative ratings with extensive explanations
- **Public Impact Metrics**: How false/misleading information affects readers

---

## Thorough Mode Overall Verdict Structure

### 1. Executive Summary Level

Located in: `article_content.executive_summary.article_accuracy_assessment`

```json
{
  "executive_summary": {
    "claims_checked": 5,
    "verdicts_summary": {
      "true": 2,
      "false": 1,
      "misinformation": 0,
      "misleading": 2,
      "unverified": 0
    },
    "key_findings": [
      "Major finding 1",
      "Major finding 2",
      "Major finding 3"
    ],
    "bottom_line": "Clear 1-2 sentence summary",
    
    // ⭐ OVERALL CREDIBILITY ASSESSMENT HERE
    "article_accuracy_assessment": {
      "overall_rating": "HIGH|MODERATE|LOW|MIXED",
      "rating_explanation": "3-5 sentences explaining the overall accuracy of the SOURCE ARTICLE being fact-checked. Considers proportion of verified vs false/misleading claims, severity of inaccuracies, whether article made claims or reported them, editorial framing, and public impact.",
      "trust_recommendation": "RELIABLE|USE_CAUTION|UNRELIABLE",
      "source_context_notes": "2-3 sentences about the source publication, observable bias, news vs opinion/commentary distinction, and context readers need when evaluating this source"
    }
  }
}
```

**Example**:
```json
{
  "article_accuracy_assessment": {
    "overall_rating": "MODERATE",
    "rating_explanation": "This article contains a mix of accurate reporting and misleading framing. While 2 of 5 claims are fully supported by evidence, 2 claims are presented with misleading context that could misinform readers. The article reports on legitimate events but uses selective framing that amplifies unverified aspects. The severity is moderate because core facts are present but interpretation guidance is problematic.",
    "trust_recommendation": "USE_CAUTION",
    "source_context_notes": "The source is a partisan news outlet known for editorial slant. This piece mixes news reporting with opinion framing. Readers should cross-reference claims with non-partisan sources and distinguish reported facts from editorial interpretation."
  }
}
```

### 2. Sidebar Overall Risk Assessment

Located in: `article_content.sidebar_elements.overall_risk_assessment`

```json
{
  "sidebar_elements": {
    "overall_risk_assessment": {
      "article_risk_level": "HIGH|MEDIUM|LOW",
      "reason": "Why this risk level was assigned",
      "high_risk_claim_count": 3,
      "reader_alert": "Warning or guidance for readers"
    }
  }
}
```

**Example**:
```json
{
  "overall_risk_assessment": {
    "article_risk_level": "HIGH",
    "reason": "Contains multiple false and misleading claims about public health that could influence critical decisions",
    "high_risk_claim_count": 3,
    "reader_alert": "⚠️ This article contains claims that contradict established medical consensus. Readers making health decisions should consult official health authorities."
  }
}
```

---

## How Overall Ratings Are Determined

### Overall Rating Categories

**HIGH Accuracy (Similar to TRUE in summary mode)**
- Most/all claims are verified true
- Minor inaccuracies if present don't affect core message
- Editorial framing is fair and balanced
- Sources are credible and properly cited
- **Trust Recommendation**: `RELIABLE`

**MODERATE Accuracy (Similar to PARTIALLY_TRUE)**
- Mix of true and misleading/false claims
- Some factual basis but significant context issues
- Editorial framing may amplify unverified aspects
- Mix of credible and questionable sources
- **Trust Recommendation**: `USE_CAUTION`

**LOW Accuracy (Similar to FALSE/MISLEADING)**
- Majority of key claims are false or misleading
- Significant factual errors that mislead readers
- Editorial framing distorts reality
- Sources lack credibility or are misrepresented
- **Trust Recommendation**: `UNRELIABLE`

**MIXED Accuracy**
- Roughly equal true and false claims
- Factually accurate on some points, problematic on others
- Difficult to categorize as primarily true or false
- **Trust Recommendation**: Varies, typically `USE_CAUTION`

### Trust Recommendation Levels

**RELIABLE**
- Readers can generally trust the information
- Minor fact-checking or verification may still be wise
- Source demonstrates journalistic standards

**USE_CAUTION**
- Readers should verify claims independently
- Mix of accurate and problematic content
- Editorial bias or framing issues present
- Not entirely unreliable but requires critical reading

**UNRELIABLE**
- Readers should not trust information without verification
- Significant factual errors or misinformation
- Source lacks credibility or demonstrates pattern of inaccuracy
- Alternative, more credible sources should be sought

---

## Rating Factors Considered

The AI fact-checker evaluates multiple dimensions when assigning overall ratings:

### 1. **Claim Verification Proportion**
```
True Claims vs. False/Misleading Claims Ratio
```
- What percentage of claims are verified?
- What percentage are false or misleading?
- Are core claims or peripheral details problematic?

### 2. **Severity of Inaccuracies**
- Are errors minor factual mistakes?
- Or major falsehoods that fundamentally change meaning?
- Do errors affect reader understanding or decisions?

### 3. **Attribution vs. Assertion**
- Did the article make the claims directly?
- Or did it report claims made by others?
- Was proper attribution provided?
- Were opposing views included?

### 4. **Editorial Framing**
- Is presentation balanced and fair?
- Does framing amplify unverified aspects?
- Are limitations or uncertainties acknowledged?
- Does headline match article content?

### 5. **Source Credibility & Bias**
- Is the publication generally reliable?
- Known editorial slant or bias?
- Track record of accuracy?
- Peer/expert review process?

### 6. **Public Impact**
- Could false information cause harm?
- Does it affect important decisions?
- Potential to mislead on critical topics?
- Viral spread on social media?

---

## Comparison Table: Summary vs. Thorough

| Aspect | Summary Mode | Thorough Mode |
|--------|--------------|---------------|
| **Overall Verdict** | Single categorical verdict | Multi-layered rating system |
| **Confidence** | 0-100 numeric score | Qualitative rating + explanation |
| **Granularity** | Article-level only | Per-claim + article-level |
| **Explanation** | Brief summary | 3-5 sentence detailed explanation |
| **Trust Guidance** | Implicit in verdict | Explicit recommendation (RELIABLE/USE_CAUTION/UNRELIABLE) |
| **Context** | Minimal | Rich source context notes |
| **Risk Assessment** | None | High/Medium/Low risk level |
| **Public Impact** | Not addressed | Scored 1-10 with affected groups |
| **Reader Guidance** | None | Explicit alerts and warnings |

---

## Where to Find Overall Verdict in Output

### In JSON Structure

```json
{
  "article_content": {
    "article_metadata": {
      "urgency_level": "HIGH|MEDIUM|LOW",
      "public_impact_score": 8
    },
    "executive_summary": {
      "article_accuracy_assessment": {
        "overall_rating": "MODERATE",           // ← HERE
        "rating_explanation": "...",            // ← HERE
        "trust_recommendation": "USE_CAUTION",  // ← HERE
        "source_context_notes": "..."           // ← HERE
      }
    },
    "sidebar_elements": {
      "overall_risk_assessment": {
        "article_risk_level": "HIGH",  // ← HERE
        "reason": "...",
        "reader_alert": "..."          // ← HERE
      }
    }
  }
}
```

### In Database

Saved to Supabase in:
- `fact_check_submissions.article_content` (JSONB column)
- Navigate: `article_content -> executive_summary -> article_accuracy_assessment`
- Navigate: `article_content -> sidebar_elements -> overall_risk_assessment`

### In API Response

```json
{
  "status": "completed",
  "validation_results": { /* per-claim verdicts */ },
  "article_content": {
    "executive_summary": {
      "article_accuracy_assessment": {
        "overall_rating": "MODERATE",
        "trust_recommendation": "USE_CAUTION"
      }
    }
  }
}
```

---

## Frontend Display Recommendations

### Primary Display: Trust Badge

```tsx
// Example React component
function TrustBadge({ rating, recommendation }) {
  const badgeConfig = {
    'RELIABLE': { color: 'green', icon: '✓', text: 'Reliable' },
    'USE_CAUTION': { color: 'yellow', icon: '⚠', text: 'Use Caution' },
    'UNRELIABLE': { color: 'red', icon: '✗', text: 'Unreliable' }
  };
  
  const config = badgeConfig[recommendation];
  
  return (
    <div className={`trust-badge trust-${config.color}`}>
      <span className="badge-icon">{config.icon}</span>
      <span className="badge-rating">{rating} Accuracy</span>
      <span className="badge-recommendation">{config.text}</span>
    </div>
  );
}
```

### Expandable Details Panel

```tsx
function AccuracyDetails({ assessment }) {
  return (
    <div className="accuracy-panel">
      <h3>Overall Accuracy Assessment</h3>
      <div className="rating-badge">{assessment.overall_rating}</div>
      <p className="explanation">{assessment.rating_explanation}</p>
      <div className="source-context">
        <h4>About This Source</h4>
        <p>{assessment.source_context_notes}</p>
      </div>
    </div>
  );
}
```

### Risk Alert Banner (if HIGH risk)

```tsx
function RiskAlert({ riskAssessment }) {
  if (riskAssessment.article_risk_level !== 'HIGH') return null;
  
  return (
    <div className="risk-alert-banner high-risk">
      <span className="alert-icon">⚠️</span>
      <div>
        <strong>High-Risk Content Detected</strong>
        <p>{riskAssessment.reader_alert}</p>
      </div>
    </div>
  );
}
```

---

## Summary

**Yes, thorough mode provides an overall credibility rating similar to summary mode's verdict system, but with significantly more depth:**

✅ **Overall Rating**: HIGH / MODERATE / LOW / MIXED accuracy  
✅ **Trust Recommendation**: RELIABLE / USE_CAUTION / UNRELIABLE  
✅ **Detailed Explanation**: 3-5 sentence rating justification  
✅ **Source Context**: Publication bias and credibility notes  
✅ **Risk Assessment**: HIGH / MEDIUM / LOW risk level  
✅ **Reader Alerts**: Explicit warnings for high-risk content  
✅ **Public Impact Score**: 1-10 rating of potential harm  

The thorough mode verdict system is **more comprehensive than summary mode** because it:
1. Provides both article-level and claim-level verdicts
2. Includes explicit trust recommendations for readers
3. Assesses source credibility and bias
4. Evaluates public impact and potential harm
5. Offers detailed explanations of rating decisions

This makes thorough mode ideal for **high-stakes fact-checking** where readers need detailed guidance on source trustworthiness and claim reliability.
