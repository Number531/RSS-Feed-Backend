"""
Fact-Check Service Module

Orchestrates fact-checking operations including API communication,
polling, result storage, and error handling.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.clients.fact_check_client import FactCheckAPIClient
from app.core.config import settings
from app.core.exceptions import (
    AlreadyFactCheckedError,
    ArticleNotFoundError,
    FactCheckAPIError,
    FactCheckTimeoutError,
)
from app.models.fact_check import ArticleFactCheck
from app.repositories.article_repository import ArticleRepository
from app.repositories.fact_check_repository import FactCheckRepository
from app.services.base_service import BaseService
from app.utils.fact_check_transform import transform_api_result_to_db

logger = logging.getLogger(__name__)


class FactCheckService(BaseService):
    """
    Service for fact-check related business logic.

    Handles:
    - Submitting fact-check jobs to external API
    - Polling job status until completion
    - Storing fact-check results in database
    - Updating article credibility scores
    - Error handling and retry logic
    """

    def __init__(self, fact_check_repo: FactCheckRepository, article_repo: ArticleRepository):
        """
        Initialize fact-check service.

        Args:
            fact_check_repo: FactCheckRepository instance
            article_repo: ArticleRepository instance
        """
        super().__init__()
        self.fact_check_repo = fact_check_repo
        self.article_repo = article_repo

    async def submit_fact_check(self, article_id: UUID, mode: str = "summary") -> ArticleFactCheck:
        """
        Submit a fact-check job for an article.

        Args:
            article_id: UUID of the article to fact-check
            mode: Validation mode ("summary" or "detailed")

        Returns:
            ArticleFactCheck: Initial fact-check record with PENDING status

        Raises:
            ArticleNotFoundError: If article doesn't exist
            AlreadyFactCheckedError: If article already has fact-check
            FactCheckAPIError: If API submission fails
        """
        self.log_operation("submit_fact_check", article_id=str(article_id), mode=mode)

        # 1. Validate article exists
        article = await self.article_repo.get_article_by_id(article_id)
        if not article:
            raise ArticleNotFoundError(str(article_id))

        # 2. Check if already fact-checked
        existing = await self.fact_check_repo.exists_for_article(article_id)
        if existing:
            logger.warning(f"Article {article_id} already fact-checked")
            raise AlreadyFactCheckedError()

        # 3. Submit job to API
        try:
            async with FactCheckAPIClient() as client:
                result = await client.submit_fact_check(
                    url=article.url,
                    mode=mode,
                    generate_image=False,  # Never generate images
                    generate_article=True,
                )

                job_id = result.get("job_id")

                logger.info(f"Fact-check job submitted: {job_id} for article {article_id}")

                # 4. Create initial database record
                fact_check_data = {
                    "article_id": article_id,
                    "job_id": job_id,
                    "verdict": "PENDING",
                    "credibility_score": -1,  # Placeholder
                    "summary": "Fact-check in progress...",
                    "validation_results": {"status": "pending"},
                    "validation_mode": mode,
                    "fact_checked_at": datetime.now(timezone.utc),
                }

                fact_check = await self.fact_check_repo.create(fact_check_data)

                return fact_check

        except Exception as e:
            self.log_error("submit_fact_check", e, article_id=str(article_id))
            raise FactCheckAPIError(f"Failed to submit fact-check: {str(e)}")

    async def poll_and_complete_job(
        self, job_id: str, max_attempts: int = None, poll_interval: int = None
    ) -> ArticleFactCheck:
        """
        Poll job status until completion and store result.

        Args:
            job_id: External API job ID
            max_attempts: Max polling attempts (default from settings)
            poll_interval: Seconds between polls (default from settings)

        Returns:
            ArticleFactCheck: Completed fact-check record

        Raises:
            FactCheckTimeoutError: If job exceeds timeout
            FactCheckAPIError: If API returns error
        """
        max_attempts = max_attempts or settings.FACT_CHECK_MAX_POLL_ATTEMPTS
        poll_interval = poll_interval or settings.FACT_CHECK_POLL_INTERVAL

        self.log_operation("poll_and_complete_job", job_id=job_id)

        # Get fact-check record
        fact_check = await self.fact_check_repo.get_by_job_id(job_id)
        if not fact_check:
            raise FactCheckAPIError(f"Fact-check record not found for job {job_id}")

        attempt = 0

        try:
            async with FactCheckAPIClient() as client:
                while attempt < max_attempts:
                    # Check job status
                    status = await client.get_job_status(job_id)
                    current_status = status.get("status")
                    progress = status.get("progress", 0)

                    logger.debug(f"Job {job_id} status: {current_status} ({progress}%)")

                    # Handle completion
                    if current_status == "finished":
                        logger.info(f"Job {job_id} completed successfully")

                        # Fetch result
                        result = await client.get_job_result(job_id)

                        # Transform and store
                        db_data = transform_api_result_to_db(result, fact_check.article_id)

                        # Update fact-check record
                        updated_fact_check = await self.fact_check_repo.update(
                            fact_check.id, db_data
                        )

                        # Update article credibility score and crawled content
                        await self._update_article_credibility(
                            fact_check.article_id, db_data["credibility_score"]
                        )
                        
                        # Update article with crawled content from Railway API
                        await self._update_article_content(fact_check.article_id, result)

                        return updated_fact_check

                    # Handle failure
                    elif current_status == "failed":
                        error_msg = status.get("error", "Unknown error")
                        logger.error(f"Job {job_id} failed: {error_msg}")

                        # Store failure state
                        await self.fact_check_repo.update(
                            fact_check.id,
                            {
                                "verdict": "ERROR",
                                "credibility_score": -1,
                                "summary": f"Fact-check failed: {error_msg}",
                                "validation_results": {"error": error_msg},
                            },
                        )

                        raise FactCheckAPIError(f"Job failed: {error_msg}")

                    # Still processing, wait and retry
                    await asyncio.sleep(poll_interval)
                    attempt += 1

                # Timeout reached
                logger.warning(f"Job {job_id} timed out after {max_attempts} attempts")

                # Store timeout state
                await self.fact_check_repo.update(
                    fact_check.id,
                    {
                        "verdict": "TIMEOUT",
                        "credibility_score": -1,
                        "summary": f"Fact-check timed out after {max_attempts * poll_interval}s",
                        "validation_results": {"error": "timeout"},
                    },
                )

                raise FactCheckTimeoutError(
                    f"Job exceeded timeout ({max_attempts * poll_interval}s)"
                )

        except (FactCheckAPIError, FactCheckTimeoutError):
            raise
        except Exception as e:
            self.log_error("poll_and_complete_job", e, job_id=job_id)
            raise FactCheckAPIError(f"Polling failed: {str(e)}")

    async def get_fact_check_by_article(self, article_id: UUID) -> Optional[ArticleFactCheck]:
        """
        Get fact-check result for an article.

        Args:
            article_id: Article UUID

        Returns:
            ArticleFactCheck or None if not fact-checked
        """
        self.log_operation("get_fact_check_by_article", article_id=str(article_id))

        try:
            fact_check = await self.fact_check_repo.get_by_article_id(article_id)
            return fact_check
        except Exception as e:
            self.log_error("get_fact_check_by_article", e, article_id=str(article_id))
            raise

    async def get_detailed_fact_check_results(self, job_id: str) -> dict:
        """
        Fetch complete fact-check results with ALL details from Railway API.
        
        This method retrieves the full validation_results from the Railway API,
        including:
        - Individual source references (URLs, titles, credibility ratings)
        - Evidence quotes (supporting, contradicting, context)
        - Citation IDs for traceability
        - Source names and relevance scores
        
        Args:
            job_id: Railway API job ID
            
        Returns:
            dict: Complete validation results with all evidence and sources
            
        Raises:
            FactCheckAPIError: If API call fails or job not found
        """
        self.log_operation("get_detailed_fact_check_results", job_id=job_id)
        
        try:
            async with FactCheckAPIClient() as client:
                # Fetch full result from Railway API
                result = await client.get_job_result(job_id)
                
                # Railway API returns complete validation_results with:
                # - claims[].validation_result.references (list of sources)
                # - claims[].validation_result.key_evidence (categorized quotes)
                # - claims[].validation_result.source_analysis
                return result
                
        except Exception as e:
            self.log_error("get_detailed_fact_check_results", e, job_id=job_id)
            raise FactCheckAPIError(f"Failed to fetch detailed results: {str(e)}")

    async def get_fact_check_status(self, job_id: str) -> dict:
        """
        Get current status of a fact-check job.

        Args:
            job_id: External API job ID

        Returns:
            dict: Status information
        """
        self.log_operation("get_fact_check_status", job_id=job_id)

        try:
            async with FactCheckAPIClient() as client:
                status = await client.get_job_status(job_id)
                return status
        except Exception as e:
            self.log_error("get_fact_check_status", e, job_id=job_id)
            raise FactCheckAPIError(f"Failed to get status: {str(e)}")

    async def cancel_fact_check(self, job_id: str) -> bool:
        """
        Cancel a pending fact-check job.

        Args:
            job_id: External API job ID

        Returns:
            bool: True if cancelled successfully
        """
        self.log_operation("cancel_fact_check", job_id=job_id)

        try:
            async with FactCheckAPIClient() as client:
                result = await client.cancel_job(job_id)

                # Update database record
                fact_check = await self.fact_check_repo.get_by_job_id(job_id)
                if fact_check:
                    await self.fact_check_repo.update(
                        fact_check.id,
                        {
                            "verdict": "CANCELLED",
                            "credibility_score": -1,
                            "summary": "Fact-check cancelled by user",
                            "validation_results": {"status": "cancelled"},
                        },
                    )

                logger.info(f"Job {job_id} cancelled successfully")
                return True

        except Exception as e:
            self.log_error("cancel_fact_check", e, job_id=job_id)
            raise FactCheckAPIError(f"Failed to cancel: {str(e)}")

    async def _update_article_credibility(self, article_id: UUID, credibility_score: int):
        """
        Update article's fact-check fields.

        Args:
            article_id: Article UUID
            credibility_score: Score to set (0-100)
        """
        try:
            article = await self.article_repo.get_article_by_id(article_id)
            if article:
                # Get fact-check record for additional fields
                fact_check = await self.fact_check_repo.get_by_article_id(article_id)

                if fact_check:
                    # Update denormalized fact-check fields in article
                    article.fact_check_score = credibility_score
                    article.fact_check_verdict = fact_check.verdict
                    article.fact_checked_at = fact_check.fact_checked_at

                    logger.info(
                        f"Updated article {article_id} fact-check fields: "
                        f"score={credibility_score}, verdict={fact_check.verdict}"
                    )
        except Exception as e:
            logger.error(f"Failed to update article fact-check fields: {e}")
            # Non-critical error, don't raise
    
    async def _update_article_content(self, article_id: UUID, api_result: dict):
        """
        Update article's content fields with text from Railway API.
        
        Args:
            article_id: Article UUID
            api_result: Complete API response from Railway
        """
        try:
            crawled_content = api_result.get("crawled_content", "")
            article_text = api_result.get("article_text", "")
            
            if crawled_content or article_text:
                article = await self.article_repo.get_article_by_id(article_id)
                if article:
                    # Update article with both raw and clean content from Railway API
                    if crawled_content:
                        article.crawled_content = crawled_content
                    if article_text:
                        article.article_text = article_text
                    
                    # Commit the changes to database
                    await self.article_repo.db.commit()
                    
                    logger.info(
                        f"Updated article {article_id} with content: "
                        f"crawled={len(crawled_content)} chars, article_text={len(article_text)} chars"
                    )
            else:
                logger.debug(f"No content available for article {article_id}")
                
        except Exception as e:
            logger.error(f"Failed to update article content: {e}")
            # Non-critical error, don't raise
