"""
Unit tests for FactCheckService.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.fact_check_service import FactCheckService
from app.models.fact_check import ArticleFactCheck
from app.models.article import Article
from app.core.exceptions import (
    AlreadyFactCheckedError,
    ArticleNotFoundError,
    FactCheckAPIError,
    FactCheckTimeoutError
)


@pytest.fixture
def mock_fact_check_repo():
    """Mock FactCheckRepository."""
    return AsyncMock()


@pytest.fixture
def mock_article_repo():
    """Mock ArticleRepository."""
    return AsyncMock()


@pytest.fixture
def fact_check_service(mock_fact_check_repo, mock_article_repo):
    """FactCheckService with mocked repositories."""
    return FactCheckService(mock_fact_check_repo, mock_article_repo)


@pytest.fixture
def sample_article():
    """Sample Article model."""
    article = Article()
    article.id = uuid4()
    article.url = "https://example.com/article"
    article.title = "Test Article"
    return article


@pytest.fixture
def sample_fact_check():
    """Sample ArticleFactCheck model."""
    fact_check = ArticleFactCheck()
    fact_check.id = uuid4()
    fact_check.article_id = uuid4()
    fact_check.job_id = "test-job-123"
    fact_check.verdict = "PENDING"
    fact_check.credibility_score = -1
    fact_check.summary = "Fact-check in progress..."
    fact_check.validation_results = {"status": "pending"}
    return fact_check


class TestSubmitFactCheck:
    """Test submit_fact_check method."""
    
    @pytest.mark.asyncio
    async def test_submit_success(
        self,
        fact_check_service,
        mock_fact_check_repo,
        mock_article_repo,
        sample_article
    ):
        """Test successful fact-check submission."""
        # Setup
        article_id = sample_article.id
        mock_article_repo.get_article_by_id = AsyncMock(return_value=sample_article)
        mock_fact_check_repo.exists_for_article = AsyncMock(return_value=False)
        mock_fact_check_repo.create = AsyncMock(return_value=sample_article)
        
        # Mock API client
        with patch('app.services.fact_check_service.FactCheckAPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.submit_fact_check = AsyncMock(return_value={"job_id": "test-job-123"})
            mock_client_class.return_value = mock_client
            
            # Execute
            result = await fact_check_service.submit_fact_check(article_id)
            
            # Verify
            mock_article_repo.get_article_by_id.assert_called_once_with(article_id)
            mock_fact_check_repo.exists_for_article.assert_called_once_with(article_id)
            mock_client.submit_fact_check.assert_called_once()
            mock_fact_check_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_submit_article_not_found(
        self,
        fact_check_service,
        mock_article_repo
    ):
        """Test submission when article doesn't exist."""
        # Setup
        article_id = uuid4()
        mock_article_repo.get_article_by_id = AsyncMock(return_value=None)
        
        # Execute & Verify
        with pytest.raises(ArticleNotFoundError):
            await fact_check_service.submit_fact_check(article_id)
    
    @pytest.mark.asyncio
    async def test_submit_already_fact_checked(
        self,
        fact_check_service,
        mock_fact_check_repo,
        mock_article_repo,
        sample_article
    ):
        """Test submission when article already fact-checked."""
        # Setup
        article_id = sample_article.id
        mock_article_repo.get_article_by_id = AsyncMock(return_value=sample_article)
        mock_fact_check_repo.exists_for_article = AsyncMock(return_value=True)
        
        # Execute & Verify
        with pytest.raises(AlreadyFactCheckedError):
            await fact_check_service.submit_fact_check(article_id)


class TestPollAndCompleteJob:
    """Test poll_and_complete_job method."""
    
    @pytest.mark.asyncio
    async def test_poll_success(
        self,
        fact_check_service,
        mock_fact_check_repo,
        mock_article_repo,
        sample_fact_check,
        sample_article
    ):
        """Test successful polling and completion."""
        # Setup
        job_id = "test-job-123"
        mock_fact_check_repo.get_by_job_id = AsyncMock(return_value=sample_fact_check)
        mock_fact_check_repo.update = AsyncMock(return_value=sample_fact_check)
        mock_article_repo.get_article_by_id = AsyncMock(return_value=sample_article)
        
        # Mock API client with immediate success
        with patch('app.services.fact_check_service.FactCheckAPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get_job_status = AsyncMock(return_value={
                "status": "finished",
                "progress": 100
            })
            mock_client.get_job_result = AsyncMock(return_value={
                "job_id": job_id,
                "validation_mode": "summary",
                "processing_time_seconds": 60,
                "claims_analyzed": 1,
                "validation_results": [{
                    "claim": "Test claim",
                    "validation_output": {
                        "verdict": "TRUE",
                        "confidence": 0.95,
                        "summary": "Test summary",
                        "source_analysis": {},
                        "references": []
                    },
                    "num_sources": 25
                }]
            })
            mock_client_class.return_value = mock_client
            
            # Execute
            result = await fact_check_service.poll_and_complete_job(job_id, max_attempts=5)
            
            # Verify
            mock_fact_check_repo.get_by_job_id.assert_called_once_with(job_id)
            mock_client.get_job_status.assert_called()
            mock_client.get_job_result.assert_called_once_with(job_id)
            mock_fact_check_repo.update.assert_called()
    
    @pytest.mark.asyncio
    async def test_poll_job_failed(
        self,
        fact_check_service,
        mock_fact_check_repo,
        sample_fact_check
    ):
        """Test polling when job fails."""
        # Setup
        job_id = "test-job-123"
        mock_fact_check_repo.get_by_job_id = AsyncMock(return_value=sample_fact_check)
        mock_fact_check_repo.update = AsyncMock(return_value=sample_fact_check)
        
        # Mock API client with failure
        with patch('app.services.fact_check_service.FactCheckAPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get_job_status = AsyncMock(return_value={
                "status": "failed",
                "error": "Test error"
            })
            mock_client_class.return_value = mock_client
            
            # Execute & Verify
            with pytest.raises(FactCheckAPIError):
                await fact_check_service.poll_and_complete_job(job_id, max_attempts=5)
            
            # Verify error state was stored
            mock_fact_check_repo.update.assert_called()
            update_call = mock_fact_check_repo.update.call_args
            assert update_call[0][1]["verdict"] == "ERROR"
    
    @pytest.mark.asyncio
    async def test_poll_timeout(
        self,
        fact_check_service,
        mock_fact_check_repo,
        sample_fact_check
    ):
        """Test polling timeout."""
        # Setup
        job_id = "test-job-123"
        mock_fact_check_repo.get_by_job_id = AsyncMock(return_value=sample_fact_check)
        mock_fact_check_repo.update = AsyncMock(return_value=sample_fact_check)
        
        # Mock API client that never finishes
        with patch('app.services.fact_check_service.FactCheckAPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get_job_status = AsyncMock(return_value={
                "status": "started",
                "progress": 50
            })
            mock_client_class.return_value = mock_client
            
            # Execute & Verify
            with pytest.raises(FactCheckTimeoutError):
                await fact_check_service.poll_and_complete_job(
                    job_id,
                    max_attempts=2,
                    poll_interval=0  # No delay for test
                )
            
            # Verify timeout state was stored
            mock_fact_check_repo.update.assert_called()
            update_call = mock_fact_check_repo.update.call_args
            assert update_call[0][1]["verdict"] == "TIMEOUT"


class TestGetFactCheckByArticle:
    """Test get_fact_check_by_article method."""
    
    @pytest.mark.asyncio
    async def test_get_fact_check_found(
        self,
        fact_check_service,
        mock_fact_check_repo,
        sample_fact_check
    ):
        """Test getting fact-check when it exists."""
        # Setup
        article_id = uuid4()
        mock_fact_check_repo.get_by_article_id = AsyncMock(return_value=sample_fact_check)
        
        # Execute
        result = await fact_check_service.get_fact_check_by_article(article_id)
        
        # Verify
        assert result == sample_fact_check
        mock_fact_check_repo.get_by_article_id.assert_called_once_with(article_id)
    
    @pytest.mark.asyncio
    async def test_get_fact_check_not_found(
        self,
        fact_check_service,
        mock_fact_check_repo
    ):
        """Test getting fact-check when it doesn't exist."""
        # Setup
        article_id = uuid4()
        mock_fact_check_repo.get_by_article_id = AsyncMock(return_value=None)
        
        # Execute
        result = await fact_check_service.get_fact_check_by_article(article_id)
        
        # Verify
        assert result is None


class TestGetFactCheckStatus:
    """Test get_fact_check_status method."""
    
    @pytest.mark.asyncio
    async def test_get_status(
        self,
        fact_check_service
    ):
        """Test getting job status."""
        # Setup
        job_id = "test-job-123"
        expected_status = {"status": "started", "progress": 50}
        
        # Mock API client
        with patch('app.services.fact_check_service.FactCheckAPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get_job_status = AsyncMock(return_value=expected_status)
            mock_client_class.return_value = mock_client
            
            # Execute
            result = await fact_check_service.get_fact_check_status(job_id)
            
            # Verify
            assert result == expected_status
            mock_client.get_job_status.assert_called_once_with(job_id)


class TestCancelFactCheck:
    """Test cancel_fact_check method."""
    
    @pytest.mark.asyncio
    async def test_cancel_success(
        self,
        fact_check_service,
        mock_fact_check_repo,
        sample_fact_check
    ):
        """Test successful cancellation."""
        # Setup
        job_id = "test-job-123"
        mock_fact_check_repo.get_by_job_id = AsyncMock(return_value=sample_fact_check)
        mock_fact_check_repo.update = AsyncMock(return_value=sample_fact_check)
        
        # Mock API client
        with patch('app.services.fact_check_service.FactCheckAPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.cancel_job = AsyncMock(return_value={"cancelled": True})
            mock_client_class.return_value = mock_client
            
            # Execute
            result = await fact_check_service.cancel_fact_check(job_id)
            
            # Verify
            assert result is True
            mock_client.cancel_job.assert_called_once_with(job_id)
            mock_fact_check_repo.update.assert_called_once()
            update_call = mock_fact_check_repo.update.call_args
            assert update_call[0][1]["verdict"] == "CANCELLED"
