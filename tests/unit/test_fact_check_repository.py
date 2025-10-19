"""
Unit tests for FactCheckRepository.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.repositories.fact_check_repository import FactCheckRepository
from app.models.fact_check import ArticleFactCheck


@pytest.fixture
def mock_db_session():
    """Mock AsyncSession."""
    return AsyncMock()


@pytest.fixture
def fact_check_repo(mock_db_session):
    """FactCheckRepository with mocked session."""
    return FactCheckRepository(mock_db_session)


@pytest.fixture
def sample_fact_check_data():
    """Sample fact-check data."""
    return {
        "article_id": uuid4(),
        "verdict": "TRUE",
        "credibility_score": 95,
        "confidence": 0.95,
        "summary": "Test summary",
        "claims_analyzed": 1,
        "claims_validated": 1,
        "claims_true": 1,
        "claims_false": 0,
        "claims_misleading": 0,
        "claims_unverified": 0,
        "validation_results": {"test": "data"},
        "num_sources": 25,
        "source_consensus": "GENERAL_AGREEMENT",
        "job_id": "test-job-123",
        "validation_mode": "summary",
        "processing_time_seconds": 60,
        "api_costs": {"total": 0.01},
        "fact_checked_at": datetime.now(timezone.utc)
    }


@pytest.fixture
def sample_fact_check(sample_fact_check_data):
    """Sample ArticleFactCheck model."""
    return ArticleFactCheck(**sample_fact_check_data)


class TestFactCheckRepositoryCreate:
    """Test create operations."""
    
    @pytest.mark.asyncio
    async def test_create_fact_check(
        self,
        fact_check_repo,
        mock_db_session,
        sample_fact_check_data
    ):
        """Test creating a fact-check record."""
        # Setup
        expected_fact_check = ArticleFactCheck(**sample_fact_check_data)
        mock_db_session.flush = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
        # Execute
        result = await fact_check_repo.create(sample_fact_check_data)
        
        # Verify
        assert mock_db_session.add.called
        assert mock_db_session.flush.called
        assert mock_db_session.refresh.called
        assert isinstance(result, ArticleFactCheck)
        assert result.verdict == "TRUE"
        assert result.credibility_score == 95


class TestFactCheckRepositoryRead:
    """Test read operations."""
    
    @pytest.mark.asyncio
    async def test_get_by_id_found(
        self,
        fact_check_repo,
        mock_db_session,
        sample_fact_check
    ):
        """Test getting fact-check by ID when found."""
        # Setup
        fact_check_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_fact_check
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await fact_check_repo.get_by_id(fact_check_id)
        
        # Verify
        assert result is not None
        assert result == sample_fact_check
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(
        self,
        fact_check_repo,
        mock_db_session
    ):
        """Test getting fact-check by ID when not found."""
        # Setup
        fact_check_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await fact_check_repo.get_by_id(fact_check_id)
        
        # Verify
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_by_article_id(
        self,
        fact_check_repo,
        mock_db_session,
        sample_fact_check
    ):
        """Test getting fact-check by article ID."""
        # Setup
        article_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_fact_check
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await fact_check_repo.get_by_article_id(article_id)
        
        # Verify
        assert result is not None
        assert result == sample_fact_check
    
    @pytest.mark.asyncio
    async def test_get_by_job_id(
        self,
        fact_check_repo,
        mock_db_session,
        sample_fact_check
    ):
        """Test getting fact-check by job ID."""
        # Setup
        job_id = "test-job-123"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_fact_check
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await fact_check_repo.get_by_job_id(job_id)
        
        # Verify
        assert result is not None
        assert result.job_id == "test-job-123"
    
    @pytest.mark.asyncio
    async def test_exists_for_article_true(
        self,
        fact_check_repo,
        mock_db_session,
        sample_fact_check
    ):
        """Test checking if article has fact-check (exists)."""
        # Setup
        article_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_fact_check
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        exists = await fact_check_repo.exists_for_article(article_id)
        
        # Verify
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_exists_for_article_false(
        self,
        fact_check_repo,
        mock_db_session
    ):
        """Test checking if article has fact-check (does not exist)."""
        # Setup
        article_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        exists = await fact_check_repo.exists_for_article(article_id)
        
        # Verify
        assert exists is False


class TestFactCheckRepositoryUpdate:
    """Test update operations."""
    
    @pytest.mark.asyncio
    async def test_update_fact_check(
        self,
        fact_check_repo,
        mock_db_session,
        sample_fact_check
    ):
        """Test updating fact-check record."""
        # Setup
        fact_check_id = uuid4()
        update_data = {"summary": "Updated summary"}
        
        # Mock get_by_id to return fact-check
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_fact_check
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.flush = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
        # Execute
        result = await fact_check_repo.update(fact_check_id, update_data)
        
        # Verify
        assert result is not None
        assert result.summary == "Updated summary"
        assert mock_db_session.flush.called
        assert mock_db_session.refresh.called
    
    @pytest.mark.asyncio
    async def test_update_fact_check_not_found(
        self,
        fact_check_repo,
        mock_db_session
    ):
        """Test updating non-existent fact-check."""
        # Setup
        fact_check_id = uuid4()
        update_data = {"summary": "Updated summary"}
        
        # Mock get_by_id to return None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await fact_check_repo.update(fact_check_id, update_data)
        
        # Verify
        assert result is None


class TestFactCheckRepositoryDelete:
    """Test delete operations."""
    
    @pytest.mark.asyncio
    async def test_delete_fact_check(
        self,
        fact_check_repo,
        mock_db_session,
        sample_fact_check
    ):
        """Test deleting fact-check record."""
        # Setup
        fact_check_id = uuid4()
        
        # Mock get_by_id to return fact-check
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_fact_check
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.delete = AsyncMock()
        mock_db_session.flush = AsyncMock()
        
        # Execute
        result = await fact_check_repo.delete(fact_check_id)
        
        # Verify
        assert result is True
        assert mock_db_session.delete.called
        assert mock_db_session.flush.called
    
    @pytest.mark.asyncio
    async def test_delete_fact_check_not_found(
        self,
        fact_check_repo,
        mock_db_session
    ):
        """Test deleting non-existent fact-check."""
        # Setup
        fact_check_id = uuid4()
        
        # Mock get_by_id to return None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await fact_check_repo.delete(fact_check_id)
        
        # Verify
        assert result is False


class TestFactCheckRepositoryQueries:
    """Test query operations."""
    
    @pytest.mark.asyncio
    async def test_get_recent_fact_checks(
        self,
        fact_check_repo,
        mock_db_session,
        sample_fact_check
    ):
        """Test getting recent fact-checks."""
        # Setup
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_fact_check, sample_fact_check]
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        results = await fact_check_repo.get_recent_fact_checks(limit=10)
        
        # Verify
        assert len(results) == 2
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_by_verdict(
        self,
        fact_check_repo,
        mock_db_session,
        sample_fact_check
    ):
        """Test getting fact-checks by verdict."""
        # Setup
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_fact_check]
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        results = await fact_check_repo.get_by_verdict("TRUE", limit=10)
        
        # Verify
        assert len(results) == 1
        assert results[0].verdict == "TRUE"
    
    @pytest.mark.asyncio
    async def test_get_high_credibility(
        self,
        fact_check_repo,
        mock_db_session,
        sample_fact_check
    ):
        """Test getting high credibility fact-checks."""
        # Setup
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_fact_check]
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        results = await fact_check_repo.get_high_credibility(threshold=80, limit=10)
        
        # Verify
        assert len(results) == 1
        assert results[0].credibility_score >= 80
