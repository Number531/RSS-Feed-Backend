"""
Unit tests for fact-check transformation utilities.
"""
import pytest
from uuid import uuid4
from app.utils.fact_check_transform import (
    calculate_credibility_score,
    calculate_verdict_counts,
    transform_api_result_to_db,
    extract_primary_verdict
)


class TestCredibilityScoreCalculation:
    """Test credibility score calculation."""
    
    def test_true_verdict_high_confidence(self):
        """Test score for TRUE verdict with high confidence."""
        validation_results = [{
            "validation_output": {
                "verdict": "TRUE",
                "confidence": 0.95
            }
        }]
        
        score = calculate_credibility_score(validation_results)
        assert score == 95  # 100 * 0.95
    
    def test_false_verdict(self):
        """Test score for FALSE verdict."""
        validation_results = [{
            "validation_output": {
                "verdict": "FALSE",
                "confidence": 0.90
            }
        }]
        
        score = calculate_credibility_score(validation_results)
        assert score == 9  # 10 * 0.90
    
    def test_misinformation_verdict(self):
        """Test score for MISINFORMATION (0 points)."""
        validation_results = [{
            "validation_output": {
                "verdict": "FALSE - MISINFORMATION",
                "confidence": 0.95
            }
        }]
        
        score = calculate_credibility_score(validation_results)
        assert score == 0
    
    def test_mostly_true(self):
        """Test score for MOSTLY TRUE."""
        validation_results = [{
            "validation_output": {
                "verdict": "MOSTLY TRUE",
                "confidence": 1.0
            }
        }]
        
        score = calculate_credibility_score(validation_results)
        assert score == 85
    
    def test_unverified_default(self):
        """Test score for UNVERIFIED."""
        validation_results = [{
            "validation_output": {
                "verdict": "UNVERIFIED",
                "confidence": 0.5
            }
        }]
        
        score = calculate_credibility_score(validation_results)
        assert score == 25  # 50 * 0.5
    
    def test_empty_results(self):
        """Test score for empty validation results."""
        score = calculate_credibility_score([])
        assert score == 50  # Default
    
    def test_multiple_mixed_verdicts(self):
        """Test score for multiple validation results."""
        validation_results = [
            {"validation_output": {"verdict": "TRUE", "confidence": 0.9}},
            {"validation_output": {"verdict": "FALSE", "confidence": 0.8}},
            {"validation_output": {"verdict": "MOSTLY TRUE", "confidence": 0.85}}
        ]
        
        score = calculate_credibility_score(validation_results)
        # (100*0.9 + 10*0.8 + 85*0.85) / (0.9 + 0.8 + 0.85)
        # = (90 + 8 + 72.25) / 2.55 = 170.25 / 2.55 ≈ 67
        assert 65 <= score <= 69


class TestVerdictCounts:
    """Test verdict counting."""
    
    def test_single_true(self):
        """Test counting single TRUE verdict."""
        validation_results = [{
            "validation_output": {"verdict": "TRUE"}
        }]
        
        counts = calculate_verdict_counts(validation_results)
        assert counts["TRUE"] == 1
        assert counts["FALSE"] == 0
        assert counts["MISLEADING"] == 0
        assert counts["UNVERIFIED"] == 0
    
    def test_single_false(self):
        """Test counting single FALSE verdict."""
        validation_results = [{
            "validation_output": {"verdict": "FALSE"}
        }]
        
        counts = calculate_verdict_counts(validation_results)
        assert counts["FALSE"] == 1
        assert counts["TRUE"] == 0
    
    def test_misinformation_counted_as_false(self):
        """Test MISINFORMATION counted as FALSE."""
        validation_results = [{
            "validation_output": {"verdict": "MISINFORMATION"}
        }]
        
        counts = calculate_verdict_counts(validation_results)
        assert counts["FALSE"] == 1
    
    def test_misleading(self):
        """Test counting MISLEADING verdict."""
        validation_results = [{
            "validation_output": {"verdict": "MISLEADING"}
        }]
        
        counts = calculate_verdict_counts(validation_results)
        assert counts["MISLEADING"] == 1
    
    def test_mixed_verdicts(self):
        """Test counting mixed verdicts."""
        validation_results = [
            {"validation_output": {"verdict": "TRUE"}},
            {"validation_output": {"verdict": "MOSTLY TRUE"}},
            {"validation_output": {"verdict": "FALSE"}},
            {"validation_output": {"verdict": "MISLEADING"}},
            {"validation_output": {"verdict": "UNVERIFIED"}}
        ]
        
        counts = calculate_verdict_counts(validation_results)
        assert counts["TRUE"] == 2  # TRUE + MOSTLY TRUE
        assert counts["FALSE"] == 1
        assert counts["MISLEADING"] == 1
        assert counts["UNVERIFIED"] == 1


class TestTransformAPIResult:
    """Test API result transformation."""
    
    def test_transform_summary_mode_result(self):
        """Test transformation of summary mode result."""
        api_result = {
            "job_id": "test-job-123",
            "validation_mode": "summary",
            "processing_time_seconds": 62.5,
            "claims_analyzed": 1,
            "claims_validated": 1,
            "timestamp": "2025-10-17T16:19:33Z",
            "costs": {"total": 0.0107, "search": 0.002, "validation": 0.0087},
            "validation_results": [{
                "claim": "Test claim",
                "validation_output": {
                    "verdict": "TRUE",
                    "confidence": 0.95,
                    "summary": "This claim is accurate",
                    "source_analysis": {
                        "source_consensus": "GENERAL_AGREEMENT"
                    },
                    "references": []
                },
                "num_sources": 25
            }]
        }
        
        article_id = uuid4()
        db_data = transform_api_result_to_db(api_result, article_id)
        
        assert db_data["article_id"] == article_id
        assert db_data["verdict"] == "TRUE"
        assert db_data["credibility_score"] == 95
        assert db_data["confidence"] == 0.95
        assert db_data["summary"] == "This claim is accurate"
        assert db_data["claims_analyzed"] == 1
        assert db_data["claims_true"] == 1
        assert db_data["claims_false"] == 0
        assert db_data["num_sources"] == 25
        assert db_data["source_consensus"] == "GENERAL_AGREEMENT"
        assert db_data["job_id"] == "test-job-123"
        assert db_data["validation_mode"] == "summary"
        assert db_data["processing_time_seconds"] == 62
        assert db_data["api_costs"]["total"] == 0.0107
    
    def test_transform_empty_results(self):
        """Test transformation with no validation results (error state)."""
        api_result = {
            "job_id": "test-job-456",
            "validation_mode": "summary",
            "processing_time_seconds": 5,
            "validation_results": []
        }
        
        article_id = uuid4()
        db_data = transform_api_result_to_db(api_result, article_id)
        
        assert db_data["verdict"] == "ERROR"
        assert db_data["credibility_score"] == -1
        assert db_data["summary"] == "No validation results available"
    
    def test_transform_false_misinformation(self):
        """Test transformation of FALSE - MISINFORMATION verdict."""
        api_result = {
            "job_id": "test-job-789",
            "validation_mode": "summary",
            "processing_time_seconds": 60,
            "claims_analyzed": 1,
            "validation_results": [{
                "claim": "False claim",
                "validation_output": {
                    "verdict": "FALSE - MISINFORMATION",
                    "confidence": 0.9,
                    "summary": "This is misinformation",
                    "source_analysis": {}
                },
                "num_sources": 20
            }]
        }
        
        article_id = uuid4()
        db_data = transform_api_result_to_db(api_result, article_id)
        
        assert db_data["verdict"] == "FALSE - MISINFORMATION"
        assert db_data["credibility_score"] == 0  # MISINFORMATION = 0 points
        assert db_data["claims_false"] == 1


class TestExtractPrimaryVerdict:
    """Test primary verdict extraction."""
    
    def test_single_result_summary_mode(self):
        """Test extract verdict from single result (summary mode)."""
        validation_results = [{
            "validation_output": {"verdict": "TRUE"}
        }]
        
        verdict = extract_primary_verdict(validation_results)
        assert verdict == "TRUE"
    
    def test_multiple_results_most_frequent(self):
        """Test extract most frequent verdict from multiple results."""
        validation_results = [
            {"validation_output": {"verdict": "TRUE"}},
            {"validation_output": {"verdict": "TRUE"}},
            {"validation_output": {"verdict": "FALSE"}},
        ]
        
        verdict = extract_primary_verdict(validation_results)
        assert verdict == "TRUE"  # Most frequent
    
    def test_empty_results(self):
        """Test extract verdict from empty results."""
        verdict = extract_primary_verdict([])
        assert verdict == "UNVERIFIED"
