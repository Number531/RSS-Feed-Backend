# Iterative Mode: Concrete Scoring Criteria Analysis

## Executive Summary

**Yes, iterative mode DOES use the same concrete scoring criteria prompts as thorough/summary modes** for the initial article analysis. The iterative pipeline starts with the standard summary generation process, then adds multi-pass refinement on top of it.

---

## How Iterative Mode Works

### Pipeline Architecture

```
Iterative Mode Pipeline:
┌──────────────────────────────────────────────────┐
│ PASS 0: Initial Summary (SAME AS STANDARD)      │
│ ├─ Uses: get_summary_prompt() or                │
│ │         get_thorough_summary_prompt()          │
│ └─ Result: Structured summary with scoring      │
├──────────────────────────────────────────────────┤
│ PASS 1: Claim Validation (ITERATIVE-SPECIFIC)   │
│ ├─ Extract top-k key claims from summary        │
│ ├─ Parallel validation with evidence search     │
│ └─ Result: Claim verdicts + confidence scores   │
├──────────────────────────────────────────────────┤
│ PASS 1.5: Summary Refinement (IF ISSUES FOUND)  │
│ ├─ Refine summary based on validation results   │
│ └─ Result: Updated summary with caveats         │
├──────────────────────────────────────────────────┤
│ PASS 2: Temporal Reconciliation (OPTIONAL)      │
│ ├─ Adjust temporal language for article age     │
│ └─ Result: Temporally-aware summary             │
├──────────────────────────────────────────────────┤
│ PASS 3: Article Accuracy Score (NEW)            │
│ └─ Calculate overall article reliability        │
└──────────────────────────────────────────────────┘
```

---

## Pass 0: Initial Summary Generation

### Code Evidence

From `src/services/summary_generator.py`:

```python
async def generate_summary_iterative(self,
                                    content: Dict[str, Any],
                                    mode: str = "standard",
                                    cost_tracker: Optional[CostTracker] = None):
    """
    Generate article summary with iterative refinement.
    """
    # PASS 0: Generate initial summary using existing method
    self.logger.debug("Pass 0: Generating initial summary")
    summary = await self.generate_summary(content, mode, cost_tracker)  # ← SAME METHOD
    
    # Extract top-k key claims for validation
    key_claims = summary.get('key_factual_claims', [])[:iter_config['top_k_claims']]
    
    # ... then continues with iterative refinement ...
```

**Key Observation**: Line 296 calls `self.generate_summary()` — **the same method used by standard and thorough modes**.

---

### The Standard Summary Prompt

From `src/prompts/summary_generation_prompt.py`:

```python
def get_summary_prompt(content: Dict[str, Any], 
                      summary_length: str = "2-3 sentences",
                      max_input_chars: int = 10000) -> str:
    """
    Get prompt for generating article summary for fact-checking.
    """
    return f"""
    You are an expert fact-checker tasked with summarizing an article's 
    main narrative for validation.
    
    CHAIN-OF-THOUGHT REASONING FOR KEY CLAIMS SELECTION:
    
    STEP 1: Identify all factual assertions in the article
    → List claims with specific numbers, dates, names, or events
    
    STEP 2: Determine centrality to main narrative
    → Which claims are essential to the article's core message?
    
    STEP 3: Assess verifiability
    → Can this claim be checked against external sources?
    → Does it have specific, concrete details?
    
    STEP 4: Prioritize by impact and specificity
    → Claims with numbers/dates → Higher priority
    → Claims from named sources → Higher priority
    
    STEP 5: Select top 3-5 claims from intersection of:
    → Most central + Most specific + Most verifiable
    
    FEW-SHOT EXAMPLES:
    [Detailed examples with ✅ GOOD and ❌ BAD demonstrations]
    
    Return a JSON object with:
    - summary_statement
    - key_factual_claims (scored)
    - main_actors
    - temporal_context
    - narrative_classification
    - quantitative_claims (scored)
    - causal_claims
    - source_attribution (scored)
    - potential_bias_indicators
    - fact_check_priority (risk_level scoring)
    - metadata (extraction_confidence, completeness scores)
    - validation_hints
    """
```

---

## Concrete Scoring Criteria Used

### 1. Fact Check Priority (Risk Scoring)

```json
"fact_check_priority": {
    "risk_level": "HIGH|MEDIUM|LOW",
    "priority_reason": "Why this narrative should be fact-checked",
    "potential_impact": "Who might be affected"
}
```

**Concrete Criteria**:
- HIGH: Claims with numbers/dates/named sources
- MEDIUM: Verifiable but less specific claims
- LOW: Opinion-based or vague statements

---

### 2. Source Attribution Quality

```json
"source_attribution": {
    "primary_sources": ["Main sources cited"],
    "source_diversity": "single_source|limited_sources|diverse_sources",
    "attribution_quality": "well_attributed|partially_attributed|poorly_attributed"
}
```

**Concrete Scoring**:
- **well_attributed**: All major claims cite specific sources
- **partially_attributed**: Some claims sourced, others not
- **poorly_attributed**: Most claims lack attribution

---

### 3. Extraction Quality Metrics

```json
"metadata": {
    "extraction_confidence": 0.0-1.0,
    "summary_completeness": 0.0-1.0,
    "content_type": "domain",
    "word_count": 1234,
    "contains_data_viz": true/false,
    "prompt_version": "2.0.0"
}
```

**Concrete Scoring**:
- **extraction_confidence**: 
  - 0.9-1.0: Clear, unambiguous claims
  - 0.7-0.9: Mostly clear with minor ambiguity
  - 0.5-0.7: Significant interpretation required
  - <0.5: Highly ambiguous or vague

- **summary_completeness**:
  - 0.9-1.0: All key elements captured
  - 0.7-0.9: Most key elements present
  - 0.5-0.7: Missing important context
  - <0.5: Incomplete summary

---

### 4. Narrative Classification

```json
"narrative_classification": {
    "primary_type": "news|opinion|analysis|investigation|feature",
    "narrative_stance": "supportive|critical|neutral|mixed",
    "rhetorical_approach": "factual|emotional|analytical|persuasive"
}
```

**Concrete Categories** with clear definitions applied consistently.

---

## Pass 1: Claim Validation (Iterative-Specific)

After generating the initial summary with scoring, iterative mode **validates the extracted claims**:

```python
# From summary_generator.py, line 319-328
if self.exa_client and self.validation_client and key_claims:
    self.logger.info(f"Pass 1: Validating {len(key_claims)} key claims")
    
    validation_results = await self._validate_claims_with_evidence(
        key_claims,
        iter_config
    )
    
    iterative_metadata['claim_verdicts'] = validation_results
    iterative_metadata['claims_validated'] = len(validation_results)
```

### Validation Uses Thorough Prompt

From `src/services/summary_generator.py`, line 622-627:

```python
# Validate claim with evidence using Gemini
validation_result = await self.validation_client.validate_claim_with_evidence(
    claim=claim_text,
    evidence=evidence,
    risk_level=risk_level,  # ← Uses risk_level from initial scoring
    category="summary_claim"
)
```

This calls the **thorough validation prompt** (`thorough_validation_prompt.py`) which includes:

1. **Epistemological Analysis** with Evidence Quality Assessment (HIGH/MEDIUM/LOW)
2. **Source Credibility Matrix** with numerical scores (0-10)
3. **Confidence Assessment** with breakdown:
   ```
   - Core claim accuracy: [1-5]
   - Evidence quality: [1-5]
   - Source reliability: [1-5]
   - Logical consistency: [1-5]
   ```
4. **Misinformation Risk Assessment** with 4 concrete indicators
5. **Final Verdict** with confidence scoring

---

## Comparison: Summary vs Iterative

### What's the SAME

| Feature | Summary Mode | Iterative Mode |
|---------|--------------|----------------|
| **Initial Analysis Prompt** | `get_summary_prompt()` | `get_summary_prompt()` ✅ |
| **Scoring Criteria** | Risk level, attribution, confidence | Same scoring ✅ |
| **Few-Shot Examples** | Yes | Same examples ✅ |
| **Chain-of-Thought** | Yes | Same CoT reasoning ✅ |
| **JSON Schema** | Structured output | Same structure ✅ |
| **Concrete Metrics** | Extraction confidence, completeness | Same metrics ✅ |

### What's DIFFERENT

| Feature | Summary Mode | Iterative Mode |
|---------|--------------|----------------|
| **Claim Validation** | ❌ Not done | ✅ Parallel validation |
| **Multi-Pass Refinement** | ❌ Single pass | ✅ 2-5 iterations |
| **Temporal Reconciliation** | ❌ Not applied | ✅ Adjusts for article age |
| **Article Accuracy Score** | ❌ Not calculated | ✅ Overall reliability score |
| **Metadata** | Basic generation info | ✅ Iterative execution details |

---

## Pass 1.5: Summary Refinement

If validation finds issues (false/misleading/unverified claims), iterative mode **refines the summary**:

```python
# From summary_generator.py, line 336-346
if issues_found > 0:
    self.logger.debug(f"Pass 1.5: Refining summary based on {issues_found} issues")
    summary = await self._refine_summary_with_validation(
        summary,
        validation_results,
        content,
        mode,
        cost_tracker
    )
    iterative_metadata['refinement_applied'] = True
    iterative_metadata['iterations_completed'] += 1
```

The refinement prompt **updates the initial scored summary** to:
- Add caveats for false claims
- Mark unverified claims with uncertainty
- Preserve accurate elements
- Adjust confidence scores based on validation

---

## Pass 3: Article Accuracy Score (NEW)

Iterative mode calculates an **overall article reliability score**:

```python
# From summary_generator.py, line 387-392
article_score = self._calculate_article_accuracy(
    iterative_metadata.get('claim_verdicts', []),
    summary
)
iterative_metadata['article_accuracy'] = article_score
```

This produces:

```json
"article_accuracy": {
    "reliability_score": 0.87,  // 0.0-1.0
    "verdict": "MOSTLY RELIABLE|MIXED|MOSTLY UNRELIABLE|UNRELIABLE",
    "breakdown": {
        "claims_true": 3,
        "claims_false": 0,
        "claims_misleading": 0,
        "claims_unverified": 0
    }
}
```

---

## Example: Full Iterative Output

```json
{
  "summary_statement": "Article discusses Trump administration warning...",
  
  "key_factual_claims": [
    "The Trump administration warned 42 million Americans could lose food stamps",
    "Government shutdown caused SNAP funding concerns",
    "USDA issued warnings about benefit disruptions"
  ],
  
  "fact_check_priority": {
    "risk_level": "HIGH",  // ← SCORED IN PASS 0
    "priority_reason": "Claims affect 42M people",
    "potential_impact": "Low-income families"
  },
  
  "source_attribution": {
    "primary_sources": ["USDA", "Trump administration"],
    "source_diversity": "limited_sources",  // ← SCORED IN PASS 0
    "attribution_quality": "well_attributed"  // ← SCORED IN PASS 0
  },
  
  "metadata": {
    "extraction_confidence": 0.92,  // ← SCORED IN PASS 0
    "summary_completeness": 0.88,   // ← SCORED IN PASS 0
    "prompt_version": "2.0.0"
  },
  
  "iterative_metadata": {  // ← ADDED BY ITERATIVE MODE
    "iterations_completed": 2,
    "claims_validated": 3,
    "issues_found": 0,
    "claim_verdicts": [
      {
        "claim": "The Trump administration warned...",
        "verdict": "SUPPORTED",
        "confidence": 0.89,  // ← FROM THOROUGH VALIDATION
        "evidence_count": 12
      }
    ],
    "article_accuracy": {
      "reliability_score": 0.89,
      "verdict": "MOSTLY RELIABLE"
    },
    "refinement_applied": true,
    "temporal_reconciliation_applied": false,
    "early_stopped": true,
    "total_time_seconds": 53.47
  }
}
```

---

## Key Takeaways

### ✅ Yes, Iterative Mode Uses Concrete Scoring

1. **Initial Analysis**: Uses the SAME prompts with concrete scoring criteria
2. **Risk Scoring**: HIGH/MEDIUM/LOW based on specificity and verifiability
3. **Quality Metrics**: Extraction confidence (0.0-1.0), completeness (0.0-1.0)
4. **Attribution Scoring**: well_attributed/partially_attributed/poorly_attributed
5. **Chain-of-Thought**: 5-step reasoning for claim prioritization
6. **Few-Shot Examples**: Concrete examples of good vs bad summaries

### ✅ Additional Iterative Scoring

After the initial scored analysis, iterative mode adds:

1. **Claim Validation Scores**: Confidence per claim (0.0-1.0)
2. **Evidence Quality**: HIGH/MEDIUM/LOW per source
3. **Source Credibility**: Numerical scores (0-10 scale)
4. **Article Accuracy**: Overall reliability score (0.0-1.0)
5. **Iteration Tracking**: Refinement history with confidence adjustments

---

## Comparison to Thorough Mode

### Thorough Mode Prompt

From `get_thorough_summary_prompt()`:

```python
thorough_additions = """
ADDITIONAL THOROUGH ANALYSIS REQUIREMENTS:
- Identify any contradictions or inconsistencies within the article
- Note any significant claims that lack attribution or sources
- Highlight rhetorical techniques that may influence interpretation
- Identify what context or counterarguments are missing
- Extract implied claims that aren't explicitly stated
- Note any temporal inconsistencies or vague timeframes
"""
```

**Key Difference**:
- **Thorough Mode**: Deeper initial analysis, more claims extracted
- **Iterative Mode**: Standard initial analysis + multi-pass refinement

Both use the same **concrete scoring framework**.

---

## Configuration Control

Users can control which scoring framework to use:

```python
# In worker.py or fact_check_cli.py
if mode == "thorough":
    # Uses get_thorough_summary_prompt() → More detailed scoring
    summary = await summary_generator.generate_summary(content, mode="thorough")
    
elif mode == "iterative":
    # Uses get_summary_prompt() → Standard scoring + refinement
    summary = await summary_generator.generate_summary_iterative(content, mode="standard")
    
else:  # mode == "summary" or "standard"
    # Uses get_summary_prompt() → Standard scoring
    summary = await summary_generator.generate_summary(content, mode="standard")
```

---

## Conclusion

**Iterative mode absolutely uses concrete scoring criteria** — it's built on top of the standard summary generation process that includes:

- **Risk level scoring** (HIGH/MEDIUM/LOW)
- **Attribution quality** (well/partially/poorly attributed)
- **Confidence scores** (0.0-1.0)
- **Completeness metrics** (0.0-1.0)
- **Chain-of-thought reasoning** with 5-step prioritization
- **Few-shot examples** demonstrating scoring standards

The difference is that **iterative mode doesn't stop there**. It:
1. Validates the scored claims with evidence
2. Refines the summary if issues are found
3. Applies temporal reconciliation
4. Calculates an overall article accuracy score
5. Tracks all iterations with metadata

**In short**: Iterative mode uses the same concrete scoring for the initial article analysis, then adds layers of validation and refinement on top of it.

---

*Last Updated: October 29, 2025*  
*Based on code analysis of fact-check v2.1.1*
