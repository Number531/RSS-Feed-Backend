# Confidence Score Calculation Methodology

## Overview

The confidence score (0-100 or 0.0-1.0) is **NOT calculated using a fixed mathematical formula**. Instead, it is **subjectively determined by the AI fact-checker (Gemini)** based on qualitative assessment of multiple factors during the validation process.

## Key Finding

⚠️ **There is NO repeatable numeric rubric or algorithmic formula** ⚠️

The confidence score is an **AI-generated subjective rating** based on the model's analysis of:
- Evidence quality
- Source reliability
- Logical consistency
- Claim accuracy
- Uncertainty factors

## How It Works

### 1. AI Prompt Guidance

The AI is instructed to provide a confidence score, but **no specific calculation method is prescribed**. The prompts simply request:

```json
{
  "confidence": 0.0-1.0,
  "confidence_components": {
    "claim_accuracy": 0.0-1.0,
    "evidence_quality": 0.0-1.0,
    "source_reliability": 0.0-1.0,
    "logical_consistency": 0.0-1.0
  }
}
```

**Source**: `src/prompts/thorough_validation_prompt.py` lines 481-487

The AI determines these scores based on its training and the comprehensive evidence provided, without explicit formulas.

### 2. Confidence Assessment Structure (Thorough Mode)

In thorough mode, the AI provides a richer confidence breakdown:

```markdown
### Confidence Assessment
- **Overall Confidence Score**: [1-5]
- **Confidence Breakdown**:
  - Core claim accuracy: [1-5]
  - Evidence quality: [1-5]
  - Source reliability: [1-5]
  - Logical consistency: [1-5]

### Confidence Justification
[Detailed explanation of confidence scoring, including:
- Factors that increase confidence
- Factors that decrease confidence
- How different aspects were weighted]
```

**Source**: `src/prompts/thorough_validation_prompt.py` lines 275-287

Note: Despite the 1-5 scale in the markdown template, the JSON output typically uses 0.0-1.0 scale.

### 3. Factors Influencing Confidence (Implicit Guidelines)

While no rubric exists, the AI considers these factors based on the prompt structure:

#### Evidence Quality Factors
- **HIGH Confidence**:
  - Multiple independent credible sources
  - Direct evidence explicitly addressing claim
  - Recent, peer-reviewed research
  - Government or official records
  - Clear consensus across experts

- **MEDIUM Confidence**:
  - Some credible sources but gaps
  - Mix of direct and indirect evidence
  - Limited corroboration
  - Some source independence concerns
  - Mixed expert opinions

- **LOW Confidence**:
  - Few credible sources
  - Mostly indirect/tangential evidence
  - Outdated information
  - Conflicting evidence
  - No expert consensus

#### Source Reliability Factors
- **Credibility Ratings** assigned to each source:
  - HIGH: Peer-reviewed journals, government agencies, reputable news outlets
  - MEDIUM: Mainstream media, verified experts, established organizations
  - LOW: Unverified sources, partisan outlets, anonymous sources

**Source**: `src/prompts/thorough_validation_prompt.py` lines 154-170

#### Logical Consistency Factors
- **CONSISTENT**: No logical fallacies, coherent causal reasoning
- **PARTIALLY_CONSISTENT**: Some issues but not fundamental
- **INCONSISTENT**: Major logical flaws or contradictions

**Source**: `src/prompts/thorough_validation_prompt.py` lines 496-498

#### Uncertainty Quantification
The AI explicitly identifies:
- **Known Unknowns**: What evidence is missing
- **High Confidence Aspects**: Most certain findings
- **Medium Confidence Aspects**: Moderately certain findings
- **Low Confidence Aspects**: Highly uncertain areas

**Source**: `src/prompts/thorough_validation_prompt.py` lines 561-567

## Confidence Score Ranges & Interpretation

### Scale Conversion

The system uses two scales interchangeably:
- **0.0 to 1.0** (decimal, used in JSON output)
- **0 to 100** (percentage, displayed to users)

Conversion: `percentage = decimal × 100`

### Typical Confidence Ranges

**Based on observation of system outputs, NOT formal specification:**

| Confidence | Interpretation | Typical Scenario |
|------------|----------------|------------------|
| **0.90-1.00 (90-100%)** | Very High | Strong consensus, multiple direct sources, clear verdict |
| **0.75-0.89 (75-89%)** | High | Good evidence, minor gaps, credible sources |
| **0.60-0.74 (60-74%)** | Moderate-High | Solid evidence but some limitations |
| **0.50-0.59 (50-59%)** | Moderate | Mixed evidence, some uncertainty |
| **0.35-0.49 (35-49%)** | Moderate-Low | Limited evidence, significant gaps |
| **0.20-0.34 (20-34%)** | Low | Weak evidence, major uncertainties |
| **0.00-0.19 (0-19%)** | Very Low | Insufficient or contradictory evidence |

**Note**: These ranges are **observational estimates**, not hardcoded thresholds.

## Comparison: Summary Mode vs Thorough Mode

### Summary Mode Confidence

**Structure:**
```json
{
  "verdict": "TRUE|FALSE|MISLEADING|MISINFORMATION|UNVERIFIED",
  "confidence": 0.0-1.0,
  "confidence_justification": "Brief explanation"
}
```

**Characteristics:**
- Single overall confidence score
- Less granular breakdown
- Focused on narrative-level assessment
- Faster to compute

### Thorough Mode Confidence

**Structure:**
```json
{
  "confidence": 0.0-1.0,
  "confidence_components": {
    "claim_accuracy": 0.0-1.0,
    "evidence_quality": 0.0-1.0,
    "source_reliability": 0.0-1.0,
    "logical_consistency": 0.0-1.0
  },
  "uncertainty": {
    "known_unknowns": [...],
    "confidence_intervals": {
      "high_confidence": [...],
      "medium_confidence": [...],
      "low_confidence": [...]
    }
  }
}
```

**Characteristics:**
- Multi-dimensional confidence breakdown
- Explicit uncertainty quantification
- Detailed justification required
- More nuanced assessment

## Why No Fixed Formula?

### 1. **Complexity of Fact-Checking**
Fact-checking involves subjective judgment that can't be reduced to a simple formula:
- Context matters greatly
- Evidence strength varies by domain
- Source credibility is nuanced
- Logical consistency requires interpretation

### 2. **AI Expertise Leverage**
The system leverages Gemini's training on:
- Journalistic standards
- Scientific methodology
- Source evaluation
- Logical reasoning
- Epistemology

### 3. **Flexibility Across Domains**
Different claim types require different confidence assessments:
- **Scientific claims**: Heavy weight on peer-reviewed research
- **Political claims**: Focus on official records and corroboration
- **Statistical claims**: Emphasis on data source credibility
- **Historical claims**: Primary source documentation importance

### 4. **Human-Like Assessment**
Professional fact-checkers don't use formulas either—they make holistic judgments based on experience, training, and evidence evaluation.

## Confidence in Practice

### Example 1: High Confidence (0.95)

**Claim**: "The unemployment rate in the United States was 3.4% in January 2024."

**Why High Confidence**:
- Official government source (BLS)
- Directly addresses claim with exact number
- No contradicting evidence
- Recent, primary data source
- Clear, verifiable statistic

### Example 2: Moderate Confidence (0.60)

**Claim**: "Company X's new policy will save customers $500 per year."

**Why Moderate**:
- Company announcement (biased source)
- Projection, not confirmed data
- "Will save" is future prediction
- No independent verification yet
- Depends on assumptions about usage patterns

### Example 3: Low Confidence (0.30)

**Claim**: "Most experts believe Technology Y will replace Technology Z by 2030."

**Why Low**:
- "Most experts" is vague, unverified
- No specific expert citations
- Prediction 5+ years out
- "Believe" is opinion, not fact
- No consensus evidence found

## How to Interpret Confidence Scores

### For Frontend Display

**High Confidence (>75%)**
```tsx
<div className="confidence-badge high">
  <span className="score">85%</span>
  <span className="label">High Confidence</span>
  <p className="note">Strong evidence supports this verdict</p>
</div>
```

**Moderate Confidence (50-75%)**
```tsx
<div className="confidence-badge moderate">
  <span className="score">62%</span>
  <span className="label">Moderate Confidence</span>
  <p className="note">Evidence is solid but has some limitations</p>
</div>
```

**Low Confidence (<50%)**
```tsx
<div className="confidence-badge low">
  <span className="score">38%</span>
  <span className="label">Low Confidence</span>
  <p className="note">Insufficient evidence for strong conclusion</p>
</div>
```

### For API Consumers

**Always display confidence alongside verdict:**

```json
{
  "verdict": "MISLEADING",
  "confidence": 0.72,
  "confidence_explanation": "Moderate-high confidence based on multiple credible sources showing the claim is technically true but presented in misleading context."
}
```

### User Guidance

**What users should know:**

1. **Not a Truth Probability**: Confidence ≠ "72% chance the claim is true"
   - It's confidence in the **verdict assessment**, not the claim's truth

2. **Consider Context**: Low confidence doesn't mean claim is false
   - It means insufficient evidence to make strong determination
   - Verdict could be "UNVERIFIED" with low confidence = we're not confident we have enough to verify

3. **Evidence Quality Indicator**: 
   - High confidence = strong, clear evidence available
   - Low confidence = evidence gaps, ambiguity, or conflicting sources

## Limitations & Considerations

### 1. **Subjectivity**
- Different AI models might assign different scores
- Same evidence could yield different confidence ratings
- No "ground truth" for confidence validation

### 2. **Lack of Calibration**
- Scores are not statistically calibrated
- No formal validation that 80% confidence means 80% accuracy
- Cannot aggregate scores mathematically

### 3. **Context Dependency**
- Score meaning varies by claim type
- Domain expertise affects assessment
- Temporal factors influence confidence

### 4. **No Repeatability Guarantee**
- Running same claim twice may yield slightly different scores
- Temperature setting in AI affects variation
- Evidence corpus changes over time

## Best Practices

### For Development

**DO:**
- ✅ Display confidence alongside verdicts always
- ✅ Provide explanation/justification for confidence
- ✅ Use confidence to guide UI emphasis (bolder for high confidence)
- ✅ Show confidence components breakdown when available (thorough mode)
- ✅ Include uncertainty information from AI output

**DON'T:**
- ❌ Treat confidence as precise statistical probability
- ❌ Apply mathematical operations (averaging, weighted sums) to confidence scores
- ❌ Use confidence alone to filter/sort results without context
- ❌ Promise "calibrated" or "scientific" confidence to users
- ❌ Hide low-confidence results (they're still valuable)

### For Users

**Educate users that:**
- Confidence reflects evidence quality and clarity
- Low confidence ≠ claim is false or verdict is wrong
- High confidence verdicts are more defensible
- Always read the justification, not just the number

## Future Enhancements

### Potential Improvements

1. **Statistical Calibration**
   - Track verdict accuracy against confidence scores
   - Adjust AI prompts based on calibration data
   - Provide calibration curves to users

2. **Confidence Factors Transparency**
   - Explicit factor weighting shown to users
   - Interactive confidence breakdown
   - "Why this confidence?" explanations

3. **Confidence Comparison**
   - Compare confidence across similar claims
   - Domain-specific confidence benchmarks
   - Historical confidence trends

4. **User Feedback Integration**
   - Learn from user agreement/disagreement
   - Adjust confidence prompts based on feedback
   - Improve accuracy over time

## Summary

The confidence score is a **subjective AI-generated assessment** that reflects:
- Evidence quality and quantity
- Source credibility
- Logical consistency of the claim
- Clarity vs. ambiguity of findings

**It is NOT**:
- A mathematical formula
- A repeatable calculation
- A statistical probability
- A precise, calibrated measure

**It IS**:
- A holistic quality indicator
- Based on AI judgment trained on fact-checking standards
- Useful for prioritization and emphasis
- Best used with accompanying explanations

For implementation guidance, always pair confidence scores with qualitative explanations and treat them as **indicative, not definitive** measures of certainty.
