"""
Unit tests for fact-check endpoint.
"""
import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from app.api.v1.endpoints.fact_check import get_article_fact_check
from app.models.fact_check import ArticleFactCheck


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_article_fact_check_success():
    """Test successful retrieval of fact-check details."""
    # Arrange
    article_id = uuid4()
    fact_check = ArticleFactCheck(
        id=uuid4(),
        article_id=article_id,
        job_id="test-job-123",
        verdict="TRUE",
        credibility_score=85,
        confidence=0.9,
        summary="Test summary",
        claims_analyzed=1,
        claims_validated=1,
        claims_true=1,
        claims_false=0,
        claims_misleading=0,
        claims_unverified=0,
        validation_results={"test": "data"},
        num_sources=10,
        source_consensus="STRONG_AGREEMENT",
        validation_mode="summary",
        processing_time_seconds=100,
        api_costs={"total": 0.005},
        fact_checked_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Mock database session
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fact_check
    
    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result
    
    # Act
    result = await get_article_fact_check(article_id, mock_db)
    
    # Assert
    assert result == fact_check
    assert result.article_id == article_id
    assert result.verdict == "TRUE"
    assert result.credibility_score == 85
    mock_db.execute.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_article_fact_check_not_found():
    """Test 404 when fact-check doesn't exist."""
    # Arrange
    article_id = uuid4()
    
    # Mock database session returning None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    
    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_article_fact_check(article_id, mock_db)
    
    assert exc_info.value.status_code == 404
    assert "No fact-check found" in exc_info.value.detail
    mock_db.execute.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_article_fact_check_with_minimal_data():
    """Test fact-check with minimal optional fields."""
    # Arrange
    article_id = uuid4()
    fact_check = ArticleFactCheck(
        id=uuid4(),
        article_id=article_id,
        job_id="test-job-456",
        verdict="UNVERIFIED",
        credibility_score=50,
        confidence=None,  # Optional
        summary="Could not verify claims",
        claims_analyzed=None,  # Optional
        claims_validated=None,
        claims_true=None,
        claims_false=None,
        claims_misleading=None,
        claims_unverified=None,
        validation_results={},
        num_sources=None,  # Optional
        source_consensus=None,
        validation_mode=None,
        processing_time_seconds=None,
        api_costs=None,
        fact_checked_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Mock database session
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fact_check
    
    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result
    
    # Act
    result = await get_article_fact_check(article_id, mock_db)
    
    # Assert
    assert result == fact_check
    assert result.verdict == "UNVERIFIED"
    assert result.credibility_score == 50
    assert result.confidence is None
    assert result.num_sources is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_article_fact_check_database_error():
    """Test handling of database errors."""
    # Arrange
    article_id = uuid4()
    
    # Mock database session that raises an error
    mock_db = AsyncMock()
    mock_db.execute.side_effect = Exception("Database connection failed")
    
    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        await get_article_fact_check(article_id, mock_db)
    
    assert "Database connection failed" in str(exc_info.value)
