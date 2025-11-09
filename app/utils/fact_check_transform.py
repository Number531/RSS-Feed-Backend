"""
Data transformation utilities for fact-check API results.

Transforms external API responses into database-compatible format.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import UUID

logger = logging.getLogger(__name__)


def calculate_credibility_score(validation_results: List[Dict[str, Any]]) -> int:
    """
    Calculate 0-100 credibility score from validation results.

    Scoring:
    - TRUE: 100 points
    - MOSTLY_TRUE / MOSTLY TRUE: 85 points
    - PARTIALLY_TRUE / PARTIALLY TRUE: 70 points
    - UNVERIFIED: 50 points
    - MISLEADING: 30 points
    - FALSE: 10 points
    - MISINFORMATION / FALSE - MISINFORMATION: 0 points

    Args:
        validation_results: List of validation result dictionaries

    Returns:
        int: Credibility score 0-100
    """
    if not validation_results:
        return 50  # Default for no results

    verdict_scores = {
        "TRUE": 100,
        "MOSTLY_TRUE": 85,
        "MOSTLY TRUE": 85,
        "PARTIALLY_TRUE": 70,
        "PARTIALLY TRUE": 70,
        "UNVERIFIED": 50,
        "MISLEADING": 30,
        "FALSE": 10,
        "MISINFORMATION": 0,
        "FALSE - MISINFORMATION": 0,
        "FALSE_MISINFORMATION": 0,
    }

    total_score = 0.0
    total_weight = 0.0

    for result in validation_results:
        # API uses 'validation_result' not 'validation_output'
        validation_output = result.get("validation_result", result.get("validation_output", {}))
        verdict = validation_output.get("verdict", "UNVERIFIED")
        confidence = validation_output.get("confidence", 0.5)

        # Normalize verdict (uppercase, replace spaces/dashes with underscores)
        normalized_verdict = verdict.upper().replace(" - ", "_").replace(" ", "_")

        # Get base score for verdict
        base_score = verdict_scores.get(normalized_verdict, 50)

        # Weight by confidence
        weighted_score = base_score * confidence

        total_score += weighted_score
        total_weight += confidence

    # For single result, return weighted score directly
    # For multiple results, return weighted average
    if total_weight > 0:
        if len(validation_results) == 1:
            # Single result: return confidence-weighted score
            final_score = int(total_score)
        else:
            # Multiple results: return weighted average
            final_score = int(total_score / total_weight)
        return max(0, min(100, final_score))  # Clamp to 0-100

    return 50  # Default if no valid data


def calculate_verdict_counts(validation_results: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count verdicts by type.

    Args:
        validation_results: List of validation result dictionaries

    Returns:
        dict: {
            "TRUE": count,
            "FALSE": count,
            "MISLEADING": count,
            "UNVERIFIED": count
        }
    """
    counts = {"TRUE": 0, "FALSE": 0, "MISLEADING": 0, "UNVERIFIED": 0}

    for result in validation_results:
        # API uses 'validation_result' not 'validation_output'
        validation_output = result.get("validation_result", result.get("validation_output", {}))
        verdict = validation_output.get("verdict", "UNVERIFIED")

        # Normalize verdict
        verdict_upper = verdict.upper()

        # Categorize
        if "TRUE" in verdict_upper and "FALSE" not in verdict_upper:
            if "MOSTLY" in verdict_upper or "PARTIALLY" in verdict_upper:
                counts["TRUE"] += 1  # Consider partial truths as TRUE category
            else:
                counts["TRUE"] += 1
        elif "FALSE" in verdict_upper or "MISINFORMATION" in verdict_upper:
            counts["FALSE"] += 1
        elif "MISLEADING" in verdict_upper:
            counts["MISLEADING"] += 1
        else:
            counts["UNVERIFIED"] += 1

    return counts


def extract_references_and_evidence(api_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract references, key_evidence, and crawled_content from Railway API response.
    
    The Railway API stores:
    - Full citation data in article_data.references and article_data.key_evidence
    - Full article text in crawled_content (top-level field)
    
    Args:
        api_result: Complete API response from Railway
        
    Returns:
        dict: {
            "references": List of citation dicts,
            "key_evidence": Dict with supporting/contradicting/context arrays,
            "crawled_content": Full article text (string)
        }
    """
    article_data = api_result.get("article_data", {})
    
    # Extract references from article_data
    references = article_data.get("references", [])
    
    # Extract key_evidence from multiple possible locations
    key_evidence = article_data.get("key_evidence", {})
    
    if not key_evidence:
        # Try alternate location: verdict_summary.key_supporting_evidence
        verdict_summary = article_data.get("verdict_summary", {})
        key_evidence = verdict_summary.get("key_supporting_evidence", {})
    
    if not key_evidence:
        # Try alternate location: sidebar_elements.high_risk_claims_panel
        sidebar = article_data.get("sidebar_elements", {})
        claims_panel = sidebar.get("high_risk_claims_panel", {})
        key_evidence = claims_panel.get("key_evidence", {})
    
    # Extract crawled_content from top-level API response
    crawled_content = api_result.get("crawled_content", "")
    
    return {
        "references": references,
        "key_evidence": key_evidence,
        "crawled_content": crawled_content
    }


def transform_api_result_to_db(api_result: Dict[str, Any], article_id: UUID) -> Dict[str, Any]:
    """
    Transform fact-check API result to database record format.

    Args:
        api_result: Complete API response
        article_id: UUID of the article

    Returns:
        dict: Database-compatible record with all required fields
    """
    validation_results = api_result.get("validation_results", [])

    if not validation_results:
        logger.warning(f"No validation results for article {article_id}")
        # Return error state
        return {
            "article_id": article_id,
            "verdict": "ERROR",
            "credibility_score": -1,
            "confidence": None,
            "summary": "No validation results available",
            "claims_analyzed": 0,
            "claims_validated": 0,
            "claims_true": 0,
            "claims_false": 0,
            "claims_misleading": 0,
            "claims_unverified": 0,
            "validation_results": {"error": "No validation results"},
            "num_sources": 0,
            "source_consensus": None,
            "source_breakdown": {},
            "primary_source_type": None,
            "source_diversity_score": None,
            "high_risk_claims_count": 0,
            "job_id": api_result.get("job_id", "unknown"),
            "validation_mode": api_result.get("validation_mode", "summary"),
            "processing_time_seconds": int(api_result.get("processing_time_seconds", 0)),
            "api_costs": {"total": 0},
            "fact_checked_at": datetime.now(timezone.utc),
        }

    # Get primary result (first validation result for summary mode)
    primary_result = validation_results[0]
    # API uses 'validation_result' not 'validation_output'
    validation_output = primary_result.get(
        "validation_result", primary_result.get("validation_output", {})
    )

    # Extract verdict
    verdict = validation_output.get("verdict", "UNVERIFIED")

    # Calculate scores
    credibility_score = calculate_credibility_score(validation_results)
    verdict_counts = calculate_verdict_counts(validation_results)

    # Extract confidence
    confidence = validation_output.get("confidence")

    # Extract summary
    summary = validation_output.get("summary", "No summary available")

    # Get claim counts
    claims_analyzed = api_result.get("claims_analyzed", len(validation_results))
    claims_validated = api_result.get("claims_validated", len(validation_results))

    # Get source info and risk assessment - aggregate from all validation results
    num_sources = 0
    source_breakdown = {"news": 0, "general": 0, "research": 0, "historical": 0}
    high_risk_claims_count = 0

    for result in validation_results:
        result_validation = result.get("validation_result", result.get("validation_output", {}))

        # Get evidence count from this claim
        evidence_count = result_validation.get("evidence_count", 0)
        num_sources += evidence_count

        # Aggregate evidence breakdown
        evidence_breakdown = result_validation.get("evidence_breakdown", {})
        for source_type, count in evidence_breakdown.items():
            if source_type in source_breakdown:
                source_breakdown[source_type] += count

        # Count high-risk claims
        claim_data = result.get("claim", {})
        risk_level = claim_data.get("risk_level", "")
        if risk_level and risk_level.upper() == "HIGH":
            high_risk_claims_count += 1

    # Calculate source consensus and materialized fields based on breakdown
    if num_sources > 0:
        # Consensus is the dominant source type
        max_type = max(source_breakdown, key=source_breakdown.get)
        max_count = source_breakdown[max_type]
        consensus_percentage = (max_count / num_sources) * 100

        if consensus_percentage >= 60:
            source_consensus = f"STRONG_{max_type.upper()}"  # e.g., "STRONG_NEWS"
        elif consensus_percentage >= 40:
            source_consensus = f"MODERATE_{max_type.upper()}"  # e.g., "MODERATE_NEWS"
        else:
            source_consensus = "MIXED"  # No dominant type

        # Materialized fields for fast queries
        primary_source_type = max_type  # "news", "research", etc.

        # Calculate diversity score (0.0 = single type, 1.0 = perfectly balanced)
        # Using Shannon entropy normalized to 0-1 range
        total_types = sum(1 for count in source_breakdown.values() if count > 0)
        if total_types > 1:
            from math import log

            entropy = 0.0
            for count in source_breakdown.values():
                if count > 0:
                    proportion = count / num_sources
                    entropy -= proportion * log(proportion, total_types)
            source_diversity_score = round(entropy, 2)  # 0.0 to 1.0
        else:
            source_diversity_score = 0.0  # Single source type
    else:
        source_consensus = None
        primary_source_type = None
        source_diversity_score = None

    # Get processing metadata
    job_id = api_result.get("job_id", "unknown")
    validation_mode = api_result.get("validation_mode", "summary")
    processing_time = int(api_result.get("processing_time_seconds", 0))

    # Get costs
    costs = api_result.get("costs", {})
    api_costs = {"total": costs.get("total", 0), "breakdown": costs}

    # Timestamp
    timestamp_str = api_result.get("timestamp")
    if timestamp_str:
        try:
            fact_checked_at = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except:
            fact_checked_at = datetime.now(timezone.utc)
    else:
        fact_checked_at = datetime.now(timezone.utc)
    
    # Extract references and key_evidence from article_data
    extracted_data = extract_references_and_evidence(api_result)
    references = extracted_data["references"]
    key_evidence = extracted_data["key_evidence"]
    
    # Inject into validation_results for storage
    enhanced_validation_results = []
    for result in validation_results:
        enhanced_result = result.copy()
        val_result = enhanced_result.get("validation_result", {})
        
        # Add references and key_evidence to validation_result
        if references:
            val_result["references"] = references
        if key_evidence:
            val_result["key_evidence"] = key_evidence
        
        enhanced_result["validation_result"] = val_result
        enhanced_validation_results.append(enhanced_result)
    
    # Log extraction success
    if references or key_evidence:
        logger.info(
            f"Extracted citation data for article {article_id}: "
            f"references={len(references)}, key_evidence_categories={len(key_evidence)}"
        )

    return {
        "article_id": article_id,
        "verdict": verdict,
        "credibility_score": credibility_score,
        "confidence": confidence,
        "summary": summary,
        "claims_analyzed": claims_analyzed,
        "claims_validated": claims_validated,
        "claims_true": verdict_counts["TRUE"],
        "claims_false": verdict_counts["FALSE"],
        "claims_misleading": verdict_counts["MISLEADING"],
        "claims_unverified": verdict_counts["UNVERIFIED"],
        "validation_results": enhanced_validation_results,  # Store enhanced array with citations
        "num_sources": num_sources,
        "source_consensus": source_consensus,
        "source_breakdown": source_breakdown,  # NEW: JSONB breakdown by type
        "primary_source_type": primary_source_type,  # NEW: Materialized dominant type
        "source_diversity_score": source_diversity_score,  # NEW: Diversity metric
        "high_risk_claims_count": high_risk_claims_count,  # NEW: Count of HIGH risk claims
        "job_id": job_id,
        "validation_mode": validation_mode,
        "processing_time_seconds": processing_time,
        "api_costs": api_costs,
        "fact_checked_at": fact_checked_at,
    }


def extract_primary_verdict(validation_results: List[Dict[str, Any]]) -> str:
    """
    Extract primary verdict from validation results.

    For summary mode, returns verdict of first result.
    For detailed mode, returns most frequent verdict.

    Args:
        validation_results: List of validation results

    Returns:
        str: Primary verdict
    """
    if not validation_results:
        return "UNVERIFIED"

    if len(validation_results) == 1:
        # Summary mode - single result
        # API uses 'validation_result' not 'validation_output'
        validation_output = validation_results[0].get(
            "validation_result", validation_results[0].get("validation_output", {})
        )
        return validation_output.get("verdict", "UNVERIFIED")

    # Detailed mode - count verdicts
    verdict_counts = calculate_verdict_counts(validation_results)

    # Return most frequent
    max_count = 0
    primary_verdict = "UNVERIFIED"

    for verdict, count in verdict_counts.items():
        if count > max_count:
            max_count = count
            primary_verdict = verdict

    return primary_verdict
