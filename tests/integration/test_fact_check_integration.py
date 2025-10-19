"""
Integration tests for fact-check workflow.

Tests the complete flow:
1. Article creation
2. Fact-check submission
3. Polling and completion
4. Database persistence
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from sqlalchemy import select

from app.models.article import Article
from app.models.rss_source import RSSSource
from app.models.fact_check import ArticleFactCheck
from app.services.fact_check_service import FactCheckService
from app.repositories.fact_check_repository import FactCheckRepository
from app.repositories.article_repository import ArticleRepository
from app.core.exceptions import AlreadyFactCheckedError


@pytest.mark.integration
class TestFactCheckIntegration:
    """Integration tests for fact-check workflow."""
    
    async def test_complete_fact_check_workflow(self, test_db):
        """Test complete fact-check workflow from submission to completion."""
        # Step 1: Create test RSS source and article
        rss_source = RSSSource(
            name="Test Source",
            url="https://example.com/feed",
            source_name="Test Source",
            category="general",
            is_active=True
        )
        test_db.add(rss_source)
        await test_db.flush()
        
        article = Article(
            rss_source_id=rss_source.id,
            title="Test Article for Fact-Check",
            url="https://example.com/test-article",
            url_hash="test-hash-123",
            category="general"
        )
        test_db.add(article)
        await test_db.commit()
        await test_db.refresh(article)
        
        # Step 2: Initialize repositories and service
        fact_check_repo = FactCheckRepository(test_db)
        article_repo = ArticleRepository(test_db)
        fact_check_service = FactCheckService(fact_check_repo, article_repo)
        
        # Step 3: Mock API client for controlled testing
        with patch('app.services.fact_check_service.FactCheckAPIClient') as mock_client_class:
            # Setup mock client
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            
            # Mock submission
            job_id = f"test-job-{uuid4()}"
            mock_client.submit_fact_check = AsyncMock(return_value={"job_id": job_id})
            
            # Mock immediate completion
            mock_client.get_job_status = AsyncMock(return_value={
                "status": "finished",
                "progress": 100
            })
            
            # Mock result
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
                        "source_analysis": {
                            "source_consensus": "GENERAL_AGREEMENT"
                        },
                        "references": []
                    },
                    "num_sources": 25
                }]
            })
            
            mock_client_class.return_value = mock_client
            
            # Step 4: Submit fact-check
            fact_check = await fact_check_service.submit_fact_check(article.id)
            
            # Verify initial fact-check record
            assert fact_check is not None
            assert fact_check.article_id == article.id
            assert fact_check.verdict == "PENDING"
            assert fact_check.job_id == job_id
            
            # Step 5: Poll and complete
            completed_fact_check = await fact_check_service.poll_and_complete_job(job_id)
            
            # Commit transaction
            await test_db.commit()
            
            # Step 6: Verify completed fact-check
            assert completed_fact_check is not None
            assert completed_fact_check.verdict == "TRUE"
            assert completed_fact_check.credibility_score == 95
            assert float(completed_fact_check.confidence) == 0.95
            assert completed_fact_check.summary == "Test summary"
            assert completed_fact_check.num_sources == 25
            
            # Step 7: Verify database persistence
            db_fact_check = await fact_check_repo.get_by_article_id(article.id)
            assert db_fact_check is not None
            assert db_fact_check.verdict == "TRUE"
            assert db_fact_check.credibility_score == 95
            
            # Step 8: Verify article was updated
            await test_db.refresh(article)
            assert article.fact_check_score == 95
            assert article.fact_check_verdict == "TRUE"
            assert article.fact_checked_at is not None
    
    async def test_duplicate_fact_check_prevention(self, test_db):
        """Test that duplicate fact-checks are prevented."""
        # Create test article
        rss_source = RSSSource(
            name="Test Source",
            url="https://example.com/feed",
            source_name="Test Source",
            category="general",
            is_active=True
        )
        test_db.add(rss_source)
        await test_db.flush()
        
        article = Article(
            rss_source_id=rss_source.id,
            title="Test Article",
            url="https://example.com/test-article-2",
            url_hash="test-hash-456",
            category="general"
        )
        test_db.add(article)
        await test_db.commit()
        await test_db.refresh(article)
        
        # Create fact-check manually
        fact_check_repo = FactCheckRepository(test_db)
        article_repo = ArticleRepository(test_db)
        
        fact_check_data = {
            "article_id": article.id,
            "job_id": "existing-job",
            "verdict": "TRUE",
            "credibility_score": 90,
            "summary": "Existing fact-check",
            "validation_results": {},
            "fact_checked_at": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        }
        await fact_check_repo.create(fact_check_data)
        await test_db.commit()
        
        # Try to submit duplicate fact-check
        fact_check_service = FactCheckService(fact_check_repo, article_repo)
        
        with pytest.raises(AlreadyFactCheckedError):
            await fact_check_service.submit_fact_check(article.id)
    
    async def test_fact_check_cascade_delete(self, test_db):
        """Test that fact-check is deleted when article is deleted (cascade)."""
        # Create test article with fact-check
        rss_source = RSSSource(
            name="Test Source",
            url="https://example.com/feed",
            source_name="Test Source",
            category="general",
            is_active=True
        )
        test_db.add(rss_source)
        await test_db.flush()
        
        article = Article(
            rss_source_id=rss_source.id,
            title="Test Article",
            url="https://example.com/test-article-3",
            url_hash="test-hash-789",
            category="general"
        )
        test_db.add(article)
        await test_db.commit()
        await test_db.refresh(article)
        
        # Create fact-check
        fact_check_repo = FactCheckRepository(test_db)
        fact_check_data = {
            "article_id": article.id,
            "job_id": "cascade-test-job",
            "verdict": "TRUE",
            "credibility_score": 85,
            "summary": "Test fact-check",
            "validation_results": {},
            "fact_checked_at": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        }
        fact_check = await fact_check_repo.create(fact_check_data)
        await test_db.commit()
        
        fact_check_id = fact_check.id
        
        # Delete article
        await test_db.delete(article)
        await test_db.commit()
        
        # Verify fact-check was cascaded deleted
        deleted_fact_check = await fact_check_repo.get_by_id(fact_check_id)
        assert deleted_fact_check is None
    
    async def test_query_operations(self, test_db):
        """Test fact-check query operations."""
        # Create multiple test articles with fact-checks
        rss_source = RSSSource(
            name="Test Source",
            url="https://example.com/feed",
            source_name="Test Source",
            category="general",
            is_active=True
        )
        test_db.add(rss_source)
        await test_db.flush()
        
        # Create articles with different verdicts and scores
        test_data = [
            {"verdict": "TRUE", "score": 95, "hash": "hash1"},
            {"verdict": "FALSE", "score": 20, "hash": "hash2"},
            {"verdict": "MISLEADING", "score": 50, "hash": "hash3"},
            {"verdict": "TRUE", "score": 88, "hash": "hash4"},
        ]
        
        fact_check_repo = FactCheckRepository(test_db)
        
        for idx, data in enumerate(test_data):
            article = Article(
                rss_source_id=rss_source.id,
                title=f"Test Article {idx}",
                url=f"https://example.com/article-{idx}",
                url_hash=data["hash"],
                category="general"
            )
            test_db.add(article)
            await test_db.flush()
            
            fact_check_data = {
                "article_id": article.id,
                "job_id": f"job-{idx}",
                "verdict": data["verdict"],
                "credibility_score": data["score"],
                "summary": f"Summary {idx}",
                "validation_results": {},
                "fact_checked_at": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            }
            await fact_check_repo.create(fact_check_data)
        
        await test_db.commit()
        
        # Test query by verdict
        true_checks = await fact_check_repo.get_by_verdict("TRUE", limit=10)
        assert len(true_checks) == 2
        assert all(fc.verdict == "TRUE" for fc in true_checks)
        
        # Test query by high credibility
        high_cred = await fact_check_repo.get_high_credibility(threshold=80, limit=10)
        assert len(high_cred) >= 2
        assert all(fc.credibility_score >= 80 for fc in high_cred)
        
        # Test recent fact-checks
        recent = await fact_check_repo.get_recent_fact_checks(limit=10)
        assert len(recent) == 4
