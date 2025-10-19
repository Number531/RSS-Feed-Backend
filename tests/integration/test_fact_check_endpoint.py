"""
Integration tests for Fact-Check API endpoint.

Tests cover:
- Retrieving fact-check details for an article
- Handling non-existent articles
- Handling articles without fact-checks
- Response schema validation
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4


class TestFactCheckEndpoint:
    """Test suite for fact-check API endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_fact_check_success(
        self,
        client: AsyncClient,
        test_article_with_fact_check: dict
    ):
        """Test successful retrieval of fact-check details."""
        article_id = test_article_with_fact_check["id"]
        
        response = await client.get(
            f"/api/v1/articles/{article_id}/fact-check"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "id" in data
        assert data["article_id"] == article_id
        assert "job_id" in data
        assert "verdict" in data
        assert "credibility_score" in data
        assert "summary" in data
        assert "validation_results" in data
        assert "fact_checked_at" in data
        assert "created_at" in data
        assert "updated_at" in data
        
        # Verify credibility_score range
        assert 0 <= data["credibility_score"] <= 100
        
        # Verify verdict is a valid type
        valid_verdicts = ["TRUE", "FALSE", "MISLEADING", "UNVERIFIED", "MIXED", "SATIRE"]
        assert data["verdict"] in valid_verdicts
    
    @pytest.mark.asyncio
    async def test_get_fact_check_not_found(
        self,
        client: AsyncClient
    ):
        """Test 404 when article doesn't have a fact-check."""
        non_existent_id = str(uuid4())
        
        response = await client.get(
            f"/api/v1/articles/{non_existent_id}/fact-check"
        )
        
        assert response.status_code == 404
        assert "No fact-check found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_fact_check_invalid_uuid(
        self,
        client: AsyncClient
    ):
        """Test 422 when article_id is not a valid UUID."""
        response = await client.get(
            "/api/v1/articles/not-a-uuid/fact-check"
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_fact_check_with_all_fields(
        self,
        client: AsyncClient,
        test_article_with_complete_fact_check: dict
    ):
        """Test fact-check response includes all optional fields."""
        article_id = test_article_with_complete_fact_check["id"]
        
        response = await client.get(
            f"/api/v1/articles/{article_id}/fact-check"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify optional fields are present
        assert data["confidence"] is not None
        assert data["claims_analyzed"] is not None
        assert data["claims_validated"] is not None
        assert data["claims_true"] is not None
        assert data["claims_false"] is not None
        assert data["claims_misleading"] is not None
        assert data["claims_unverified"] is not None
        assert data["num_sources"] is not None
        assert data["source_consensus"] is not None
        assert data["validation_mode"] is not None
        assert data["processing_time_seconds"] is not None
        assert data["api_costs"] is not None
        
        # Verify confidence is in valid range
        assert 0.0 <= data["confidence"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_get_fact_check_validation_results_structure(
        self,
        client: AsyncClient,
        test_article_with_fact_check: dict
    ):
        """Test that validation_results field is properly structured."""
        article_id = test_article_with_fact_check["id"]
        
        response = await client.get(
            f"/api/v1/articles/{article_id}/fact-check"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify validation_results is a dict (JSON object)
        assert isinstance(data["validation_results"], dict)
        
        # If validation_results has data, check common fields
        if data["validation_results"]:
            validation = data["validation_results"]
            # These are expected fields from the fact-check API
            # but may vary based on validation_mode
            expected_keys = {"claim", "verdict", "key_evidence", "references"}
            # At least some expected keys should be present
            assert any(key in validation for key in expected_keys)
    
    @pytest.mark.asyncio
    async def test_get_fact_check_datetime_format(
        self,
        client: AsyncClient,
        test_article_with_fact_check: dict
    ):
        """Test that datetime fields are properly formatted."""
        article_id = test_article_with_fact_check["id"]
        
        response = await client.get(
            f"/api/v1/articles/{article_id}/fact-check"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify datetime fields are ISO 8601 formatted
        from datetime import datetime
        
        # Should be able to parse without errors
        datetime.fromisoformat(data["fact_checked_at"].replace("Z", "+00:00"))
        datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
    
    @pytest.mark.asyncio
    async def test_get_fact_check_no_auth_required(
        self,
        client: AsyncClient,
        test_article_with_fact_check: dict
    ):
        """Test that fact-check endpoint doesn't require authentication."""
        article_id = test_article_with_fact_check["id"]
        
        # Call without auth headers
        response = await client.get(
            f"/api/v1/articles/{article_id}/fact-check"
        )
        
        # Should succeed without authentication
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_fact_check_multiple_articles(
        self,
        client: AsyncClient,
        test_article_with_fact_check: dict,
        test_article_with_complete_fact_check: dict
    ):
        """Test retrieving fact-checks for multiple articles."""
        article1_id = test_article_with_fact_check["id"]
        article2_id = test_article_with_complete_fact_check["id"]
        
        # Get fact-check for first article
        response1 = await client.get(
            f"/api/v1/articles/{article1_id}/fact-check"
        )
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Get fact-check for second article
        response2 = await client.get(
            f"/api/v1/articles/{article2_id}/fact-check"
        )
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Verify they are different fact-checks
        assert data1["id"] != data2["id"]
        assert data1["article_id"] != data2["article_id"]
        assert data1["job_id"] != data2["job_id"]
