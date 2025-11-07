"""
Integration tests for detailed fact-check API endpoints.

Tests cover:
- GET /articles/{id}/fact-check/detailed (full sources and evidence)
- GET /articles/{id}/fact-check/claims (lightweight list)
- Railway API integration
- Error handling for expired jobs
- Response schema validation for nested structures
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4
from unittest.mock import AsyncMock, patch


@pytest.mark.integration
class TestDetailedFactCheckEndpoint:
    """Test suite for detailed fact-check endpoint with Railway API integration."""

    @pytest.mark.asyncio
    async def test_get_detailed_fact_check_success(
        self,
        client: AsyncClient,
        test_article_with_fact_check: dict,
    ):
        """Test successful retrieval of detailed fact-check with all sources."""
        article_id = test_article_with_fact_check["id"]

        # Mock Railway API response with full details
        mock_railway_response = {
            "validation_results": {
                "claims": [
                    {
                        "claim": {
                            "claim": "Test claim text",
                            "category": "Iterative Claim",
                            "risk_level": "HIGH",
                        },
                        "validation_result": {
                            "verdict": "TRUE",
                            "confidence": 0.9,
                            "summary": "Claim is accurate",
                            "evidence_count": 35,
                            "evidence_breakdown": {"news": 15, "research": 20},
                            "validation_mode": "thorough",
                            "references": [
                                {
                                    "citation_id": 1,
                                    "title": "Source Title",
                                    "url": "https://example.com/source1",
                                    "source": "AP News",
                                    "credibility": "HIGH",
                                    "relevance_score": 0.95,
                                    "published_date": "2025-11-06",
                                }
                            ],
                            "key_evidence": {
                                "supporting": ["Supporting evidence 1", "Supporting evidence 2"],
                                "contradicting": [],
                                "context": ["Background context"],
                            },
                        },
                    }
                ]
            }
        }

        with patch(
            "app.clients.fact_check_client.FactCheckAPIClient.get_job_result",
            new_callable=AsyncMock,
        ) as mock_get_result:
            mock_get_result.return_value = mock_railway_response

            response = await client.get(f"/api/v1/articles/{article_id}/fact-check/detailed")

            assert response.status_code == 200
            data = response.json()

            # Verify required top-level fields
            assert "id" in data
            assert data["article_id"] == article_id
            assert "job_id" in data
            assert "verdict" in data
            assert "credibility_score" in data
            assert "claims" in data
            assert "total_sources" in data

            # Verify claims structure
            assert len(data["claims"]) > 0
            claim = data["claims"][0]

            # Verify claim has all detailed fields
            assert "claim_text" in claim
            assert "claim_index" in claim
            assert "verdict" in claim
            assert "confidence" in claim
            assert "summary" in claim
            assert "references" in claim
            assert "key_evidence" in claim
            assert "evidence_count" in claim
            assert "evidence_breakdown" in claim

            # Verify references structure (this is the KEY new data)
            assert len(claim["references"]) > 0
            ref = claim["references"][0]
            assert "citation_id" in ref
            assert "title" in ref
            assert "url" in ref
            assert "source" in ref
            assert "credibility" in ref

            # Verify key evidence structure (this is the KEY new data)
            evidence = claim["key_evidence"]
            assert "supporting" in evidence
            assert "contradicting" in evidence
            assert "context" in evidence
            assert isinstance(evidence["supporting"], list)

    @pytest.mark.asyncio
    async def test_get_detailed_fact_check_not_found(
        self,
        client: AsyncClient,
    ):
        """Test 404 when article has no fact-check."""
        non_existent_id = str(uuid4())

        response = await client.get(f"/api/v1/articles/{non_existent_id}/fact-check/detailed")

        assert response.status_code == 404
        assert "No fact-check found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_detailed_fact_check_railway_api_failure(
        self,
        client: AsyncClient,
        test_article_with_fact_check: dict,
    ):
        """Test 503 when Railway API is unavailable."""
        article_id = test_article_with_fact_check["id"]

        # Mock Railway API failure
        with patch(
            "app.clients.fact_check_client.FactCheckAPIClient.get_job_result",
            new_callable=AsyncMock,
        ) as mock_get_result:
            mock_get_result.side_effect = Exception("Railway API unavailable")

            response = await client.get(f"/api/v1/articles/{article_id}/fact-check/detailed")

            assert response.status_code == 503
            assert "Railway API" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_detailed_fact_check_expired_job(
        self,
        client: AsyncClient,
        test_article_with_fact_check: dict,
    ):
        """Test handling of expired Railway API job."""
        article_id = test_article_with_fact_check["id"]

        # Mock 404 from Railway API (job expired)
        with patch(
            "app.clients.fact_check_client.FactCheckAPIClient.get_job_result",
            new_callable=AsyncMock,
        ) as mock_get_result:
            import httpx

            mock_get_result.side_effect = httpx.HTTPStatusError(
                "Not Found", request=None, response=None
            )

            response = await client.get(f"/api/v1/articles/{article_id}/fact-check/detailed")

            # Should return 503 with helpful error message
            assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_get_detailed_fact_check_multiple_claims(
        self,
        client: AsyncClient,
        test_article_with_fact_check: dict,
    ):
        """Test detailed fact-check with multiple claims."""
        article_id = test_article_with_fact_check["id"]

        # Mock Railway API with multiple claims
        mock_railway_response = {
            "validation_results": {
                "claims": [
                    {
                        "claim": {
                            "claim": f"Claim {i}",
                            "category": "Iterative Claim",
                            "risk_level": "MEDIUM",
                        },
                        "validation_result": {
                            "verdict": "TRUE" if i % 2 == 0 else "FALSE",
                            "confidence": 0.8 + (i * 0.05),
                            "summary": f"Analysis {i}",
                            "evidence_count": 20 + i,
                            "evidence_breakdown": {"news": 10, "research": 10 + i},
                            "validation_mode": "thorough",
                            "references": [
                                {
                                    "citation_id": j,
                                    "title": f"Source {j}",
                                    "url": f"https://example.com/source{j}",
                                    "source": "Reuters",
                                    "credibility": "HIGH",
                                }
                                for j in range(3)
                            ],
                            "key_evidence": {
                                "supporting": [f"Evidence {i}"],
                                "contradicting": [],
                                "context": [f"Context {i}"],
                            },
                        },
                    }
                    for i in range(4)
                ]
            }
        }

        with patch(
            "app.clients.fact_check_client.FactCheckAPIClient.get_job_result",
            new_callable=AsyncMock,
        ) as mock_get_result:
            mock_get_result.return_value = mock_railway_response

            response = await client.get(f"/api/v1/articles/{article_id}/fact-check/detailed")

            assert response.status_code == 200
            data = response.json()

            # Verify all claims are present
            assert len(data["claims"]) == 4

            # Verify claim indices are correct
            for i, claim in enumerate(data["claims"]):
                assert claim["claim_index"] == i
                assert claim["claim_text"] == f"Claim {i}"

            # Verify total unique sources calculation
            # 4 claims × 3 sources each = 12 total (but may have duplicates)
            assert data["total_sources"] >= 3  # At least unique sources per claim

    @pytest.mark.asyncio
    async def test_get_detailed_fact_check_no_references(
        self,
        client: AsyncClient,
        test_article_with_fact_check: dict,
    ):
        """Test handling claim with no references (edge case)."""
        article_id = test_article_with_fact_check["id"]

        mock_railway_response = {
            "validation_results": {
                "claims": [
                    {
                        "claim": {
                            "claim": "Unverified claim",
                            "category": "Standard Claim",
                            "risk_level": "LOW",
                        },
                        "validation_result": {
                            "verdict": "UNVERIFIED",
                            "confidence": 0.3,
                            "summary": "Insufficient evidence",
                            "evidence_count": 0,
                            "evidence_breakdown": {},
                            "validation_mode": "summary",
                            "references": [],  # No references
                            "key_evidence": {
                                "supporting": [],
                                "contradicting": [],
                                "context": [],
                            },
                        },
                    }
                ]
            }
        }

        with patch(
            "app.clients.fact_check_client.FactCheckAPIClient.get_job_result",
            new_callable=AsyncMock,
        ) as mock_get_result:
            mock_get_result.return_value = mock_railway_response

            response = await client.get(f"/api/v1/articles/{article_id}/fact-check/detailed")

            assert response.status_code == 200
            data = response.json()

            # Should handle empty references gracefully
            claim = data["claims"][0]
            assert claim["references"] == []
            assert claim["evidence_count"] == 0
            assert data["total_sources"] == 0


@pytest.mark.integration
class TestClaimListEndpoint:
    """Test suite for lightweight claim list endpoint."""

    @pytest.mark.asyncio
    async def test_list_claims_success(
        self,
        client: AsyncClient,
        test_article_with_fact_check: dict,
    ):
        """Test successful retrieval of claim list."""
        article_id = test_article_with_fact_check["id"]

        response = await client.get(f"/api/v1/articles/{article_id}/fact-check/claims")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "article_id" in data
        assert data["article_id"] == article_id
        assert "total_claims" in data
        assert "claims" in data

        # Verify claims list structure (lightweight - no full evidence)
        if data["total_claims"] > 0:
            claim = data["claims"][0]
            assert "claim_index" in claim
            assert "claim_text" in claim
            assert "verdict" in claim
            assert "confidence" in claim
            assert "evidence_count" in claim

            # Should NOT include full references or key_evidence
            assert "references" not in claim
            assert "key_evidence" not in claim

    @pytest.mark.asyncio
    async def test_list_claims_not_found(
        self,
        client: AsyncClient,
    ):
        """Test 404 when article has no fact-check."""
        non_existent_id = str(uuid4())

        response = await client.get(f"/api/v1/articles/{non_existent_id}/fact-check/claims")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_claims_empty(
        self,
        client: AsyncClient,
        test_article_with_fact_check: dict,
    ):
        """Test claim list with zero claims (edge case)."""
        article_id = test_article_with_fact_check["id"]

        response = await client.get(f"/api/v1/articles/{article_id}/fact-check/claims")

        assert response.status_code == 200
        data = response.json()

        # Should handle zero claims gracefully
        assert data["total_claims"] >= 0
        assert isinstance(data["claims"], list)


@pytest.mark.integration
class TestBackwardCompatibility:
    """Test that existing endpoint still works after changes."""

    @pytest.mark.asyncio
    async def test_original_endpoint_unchanged(
        self,
        client: AsyncClient,
        test_article_with_fact_check: dict,
    ):
        """Test that original fact-check endpoint still works."""
        article_id = test_article_with_fact_check["id"]

        response = await client.get(f"/api/v1/articles/{article_id}/fact-check")

        # Original endpoint should work exactly as before
        assert response.status_code == 200
        data = response.json()

        # Verify it returns summary data (NOT detailed)
        assert "verdict" in data
        assert "credibility_score" in data
        assert "validation_results" in data

        # Should NOT have new detailed structure at top level
        # (detailed endpoint is separate)
        if "claims" in data:
            # If claims exist, they should be summary format
            claim = data["claims"][0] if data["claims"] else None
            if claim:
                # Summary format doesn't have full nested references
                assert "validation_result" in claim or "verdict" in claim

    @pytest.mark.asyncio
    async def test_all_three_endpoints_coexist(
        self,
        client: AsyncClient,
        test_article_with_fact_check: dict,
    ):
        """Test that all three endpoints work together."""
        article_id = test_article_with_fact_check["id"]

        # 1. Original endpoint
        response1 = await client.get(f"/api/v1/articles/{article_id}/fact-check")
        assert response1.status_code == 200

        # 2. Claims list endpoint
        response2 = await client.get(f"/api/v1/articles/{article_id}/fact-check/claims")
        assert response2.status_code == 200

        # 3. Detailed endpoint (with mocked Railway API)
        mock_railway_response = {
            "validation_results": {
                "claims": [
                    {
                        "claim": {
                            "claim": "Test",
                            "category": "Test",
                            "risk_level": "LOW",
                        },
                        "validation_result": {
                            "verdict": "TRUE",
                            "confidence": 0.9,
                            "summary": "Test",
                            "evidence_count": 10,
                            "evidence_breakdown": {},
                            "validation_mode": "test",
                            "references": [],
                            "key_evidence": {
                                "supporting": [],
                                "contradicting": [],
                                "context": [],
                            },
                        },
                    }
                ]
            }
        }

        with patch(
            "app.clients.fact_check_client.FactCheckAPIClient.get_job_result",
            new_callable=AsyncMock,
        ) as mock_get_result:
            mock_get_result.return_value = mock_railway_response

            response3 = await client.get(f"/api/v1/articles/{article_id}/fact-check/detailed")
            assert response3.status_code == 200

        # All three should return data for the same article
        assert response1.json()["article_id"] == article_id
        assert response2.json()["article_id"] == article_id
        assert response3.json()["article_id"] == article_id
