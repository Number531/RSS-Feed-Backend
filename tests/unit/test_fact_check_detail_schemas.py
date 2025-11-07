"""
Unit tests for detailed fact-check schemas.

Tests schema validation, field requirements, and edge cases.
"""

import pytest
from pydantic import ValidationError
from uuid import uuid4

from app.schemas.fact_check_detail import (
    SourceReference,
    KeyEvidence,
    ClaimAnalysis,
    DetailedFactCheckResponse,
    ClaimListResponse,
)


class TestSourceReference:
    """Test SourceReference schema validation."""

    def test_valid_source_reference(self):
        """Test creating valid source reference."""
        ref = SourceReference(
            citation_id=1,
            title="Test Article",
            url="https://example.com/article",
            source="AP News",
            credibility="HIGH",
            relevance_score=0.95,
            published_date="2025-11-06",
        )

        assert ref.citation_id == 1
        assert ref.title == "Test Article"
        assert ref.credibility == "HIGH"
        assert ref.relevance_score == 0.95

    def test_minimal_source_reference(self):
        """Test source reference with only required fields."""
        ref = SourceReference(
            citation_id=1,
            title="Test",
            url="https://example.com",
            source="Reuters",
            credibility="MEDIUM",
        )

        assert ref.relevance_score is None
        assert ref.published_date is None

    def test_invalid_relevance_score(self):
        """Test relevance score validation (must be 0.0-1.0)."""
        with pytest.raises(ValidationError):
            SourceReference(
                citation_id=1,
                title="Test",
                url="https://example.com",
                source="Reuters",
                credibility="HIGH",
                relevance_score=1.5,  # Invalid - exceeds 1.0
            )

    def test_missing_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            SourceReference(
                citation_id=1,
                title="Test",
                # Missing url, source, credibility
            )


class TestKeyEvidence:
    """Test KeyEvidence schema validation."""

    def test_valid_key_evidence(self):
        """Test creating valid key evidence."""
        evidence = KeyEvidence(
            supporting=["Evidence 1", "Evidence 2"],
            contradicting=["Counter evidence"],
            context=["Background info"],
        )

        assert len(evidence.supporting) == 2
        assert len(evidence.contradicting) == 1
        assert len(evidence.context) == 1

    def test_empty_key_evidence(self):
        """Test key evidence with no items (all defaults)."""
        evidence = KeyEvidence()

        assert evidence.supporting == []
        assert evidence.contradicting == []
        assert evidence.context == []

    def test_partial_key_evidence(self):
        """Test key evidence with only some categories."""
        evidence = KeyEvidence(
            supporting=["Evidence"],
            # contradicting and context default to []
        )

        assert len(evidence.supporting) == 1
        assert evidence.contradicting == []
        assert evidence.context == []


class TestClaimAnalysis:
    """Test ClaimAnalysis schema validation."""

    def test_valid_claim_analysis(self):
        """Test creating valid claim analysis."""
        references = [
            SourceReference(
                citation_id=1,
                title="Source 1",
                url="https://example.com/1",
                source="AP News",
                credibility="HIGH",
            )
        ]

        evidence = KeyEvidence(
            supporting=["Evidence"],
            contradicting=[],
            context=["Context"],
        )

        claim = ClaimAnalysis(
            claim_text="Test claim",
            claim_index=0,
            category="Iterative Claim",
            risk_level="HIGH",
            verdict="TRUE",
            confidence=0.9,
            summary="Analysis summary",
            key_evidence=evidence,
            references=references,
            evidence_count=35,
            evidence_breakdown={"news": 10, "research": 25},
            validation_mode="thorough",
        )

        assert claim.claim_text == "Test claim"
        assert claim.verdict == "TRUE"
        assert claim.confidence == 0.9
        assert len(claim.references) == 1
        assert claim.evidence_count == 35

    def test_claim_with_no_evidence(self):
        """Test claim analysis without evidence (optional fields)."""
        claim = ClaimAnalysis(
            claim_text="Test claim",
            claim_index=0,
            category="Standard Claim",
            risk_level="LOW",
            verdict="UNVERIFIED",
            confidence=0.5,
            summary="Insufficient evidence",
            key_evidence=None,  # Optional
            references=[],  # Empty list
            evidence_count=0,
            evidence_breakdown={},
            validation_mode="summary",
        )

        assert claim.key_evidence is None
        assert claim.references == []
        assert claim.evidence_count == 0

    def test_invalid_confidence_range(self):
        """Test confidence validation (must be 0.0-1.0)."""
        with pytest.raises(ValidationError):
            ClaimAnalysis(
                claim_text="Test",
                claim_index=0,
                category="Test",
                risk_level="LOW",
                verdict="TRUE",
                confidence=1.5,  # Invalid
                summary="Test",
                evidence_count=10,
                evidence_breakdown={},
                validation_mode="test",
            )

    def test_negative_claim_index(self):
        """Test claim_index must be non-negative."""
        with pytest.raises(ValidationError):
            ClaimAnalysis(
                claim_text="Test",
                claim_index=-1,  # Invalid - must be >= 0
                category="Test",
                risk_level="LOW",
                verdict="TRUE",
                confidence=0.5,
                summary="Test",
                evidence_count=10,
                evidence_breakdown={},
                validation_mode="test",
            )


class TestDetailedFactCheckResponse:
    """Test DetailedFactCheckResponse schema validation."""

    def test_valid_detailed_response(self):
        """Test creating valid detailed fact-check response."""
        article_id = uuid4()
        fact_check_id = uuid4()

        claim = ClaimAnalysis(
            claim_text="Test claim",
            claim_index=0,
            category="Test",
            risk_level="MEDIUM",
            verdict="TRUE",
            confidence=0.8,
            summary="Summary",
            evidence_count=20,
            evidence_breakdown={"news": 20},
            validation_mode="thorough",
        )

        response = DetailedFactCheckResponse(
            id=fact_check_id,
            article_id=article_id,
            job_id="test-job-123",
            verdict="TRUE",
            credibility_score=85,
            summary="Overall summary",
            claims=[claim],
            total_sources=15,
            fact_checked_at="2025-11-07T12:00:00Z",
        )

        assert response.verdict == "TRUE"
        assert response.credibility_score == 85
        assert len(response.claims) == 1
        assert response.total_sources == 15

    def test_invalid_credibility_score(self):
        """Test credibility score must be 0-100."""
        with pytest.raises(ValidationError):
            DetailedFactCheckResponse(
                id=uuid4(),
                article_id=uuid4(),
                job_id="test",
                verdict="TRUE",
                credibility_score=150,  # Invalid - exceeds 100
                summary="Test",
                claims=[],
                total_sources=0,
                fact_checked_at="2025-11-07T12:00:00Z",
            )

    def test_response_with_multiple_claims(self):
        """Test response with multiple claims."""
        claims = [
            ClaimAnalysis(
                claim_text=f"Claim {i}",
                claim_index=i,
                category="Test",
                risk_level="LOW",
                verdict="TRUE",
                confidence=0.9,
                summary=f"Summary {i}",
                evidence_count=10,
                evidence_breakdown={},
                validation_mode="test",
            )
            for i in range(3)
        ]

        response = DetailedFactCheckResponse(
            id=uuid4(),
            article_id=uuid4(),
            job_id="test",
            verdict="MOSTLY TRUE",
            credibility_score=78,
            summary="Test",
            claims=claims,
            total_sources=50,
            fact_checked_at="2025-11-07T12:00:00Z",
        )

        assert len(response.claims) == 3
        assert response.claims[0].claim_index == 0
        assert response.claims[2].claim_index == 2


class TestClaimListResponse:
    """Test ClaimListResponse schema validation."""

    def test_valid_claim_list(self):
        """Test creating valid claim list response."""
        article_id = uuid4()

        claims_data = [
            {
                "claim_index": 0,
                "claim_text": "Claim 1",
                "verdict": "TRUE",
                "confidence": 0.9,
                "evidence_count": 25,
            },
            {
                "claim_index": 1,
                "claim_text": "Claim 2",
                "verdict": "FALSE",
                "confidence": 0.85,
                "evidence_count": 30,
            },
        ]

        response = ClaimListResponse(
            article_id=article_id, total_claims=2, claims=claims_data
        )

        assert response.total_claims == 2
        assert len(response.claims) == 2
        assert response.claims[0]["verdict"] == "TRUE"
        assert response.claims[1]["verdict"] == "FALSE"

    def test_empty_claim_list(self):
        """Test claim list with no claims."""
        response = ClaimListResponse(
            article_id=uuid4(), total_claims=0, claims=[]
        )

        assert response.total_claims == 0
        assert response.claims == []


@pytest.mark.unit
class TestSchemaIntegration:
    """Test schema interactions and nesting."""

    def test_full_nested_structure(self):
        """Test complete nested structure with all components."""
        # Create source references
        references = [
            SourceReference(
                citation_id=i,
                title=f"Source {i}",
                url=f"https://example.com/{i}",
                source="AP News" if i % 2 == 0 else "Reuters",
                credibility="HIGH",
                relevance_score=0.9 - (i * 0.1),
            )
            for i in range(3)
        ]

        # Create key evidence
        evidence = KeyEvidence(
            supporting=["Supporting evidence 1", "Supporting evidence 2"],
            contradicting=["Contradicting evidence"],
            context=["Context 1", "Context 2", "Context 3"],
        )

        # Create claim analysis
        claim = ClaimAnalysis(
            claim_text="Complex claim requiring multiple sources",
            claim_index=0,
            category="Iterative Claim",
            risk_level="HIGH",
            verdict="MOSTLY TRUE",
            confidence=0.87,
            summary="Detailed analysis with nuance",
            key_evidence=evidence,
            references=references,
            evidence_count=42,
            evidence_breakdown={
                "news": 15,
                "research": 12,
                "historical": 10,
                "general": 5,
            },
            validation_mode="thorough",
        )

        # Create full response
        response = DetailedFactCheckResponse(
            id=uuid4(),
            article_id=uuid4(),
            job_id="complex-job-789",
            verdict="MOSTLY TRUE",
            credibility_score=82,
            confidence=0.87,
            summary="Article contains mostly accurate claims with minor issues",
            claims_analyzed=1,
            claims_validated=1,
            claims_true=0,
            claims_false=0,
            claims_misleading=1,
            claims_unverified=0,
            claims=[claim],
            total_sources=25,
            source_consensus="MODERATE_AGREEMENT",
            validation_mode="iterative",
            processing_time_seconds=287,
            api_costs={"total": 0.012, "validation": 0.008, "research": 0.004},
            fact_checked_at="2025-11-07T14:30:00Z",
        )

        # Verify complete structure
        assert len(response.claims) == 1
        assert len(response.claims[0].references) == 3
        assert len(response.claims[0].key_evidence.supporting) == 2
        assert len(response.claims[0].key_evidence.contradicting) == 1
        assert len(response.claims[0].key_evidence.context) == 3
        assert response.claims[0].evidence_count == 42
        assert response.total_sources == 25
        assert response.processing_time_seconds == 287

    def test_schema_json_serialization(self):
        """Test that schemas can be serialized to JSON."""
        ref = SourceReference(
            citation_id=1,
            title="Test",
            url="https://example.com",
            source="Reuters",
            credibility="HIGH",
        )

        # Should serialize without error
        json_data = ref.model_dump()

        assert json_data["citation_id"] == 1
        assert json_data["credibility"] == "HIGH"
        assert "relevance_score" in json_data  # Optional fields included as None
