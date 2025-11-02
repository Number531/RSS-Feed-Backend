"""
Celery tasks for fact-checking articles.
"""

import asyncio
import logging
from uuid import UUID

from app.core.celery_app import celery_app
from app.core.exceptions import (
    AlreadyFactCheckedError,
    ArticleNotFoundError,
    FactCheckAPIError,
    FactCheckTimeoutError,
)
from app.db.session import AsyncSessionLocal
from app.repositories.article_repository import ArticleRepository
from app.repositories.fact_check_repository import FactCheckRepository
from app.services.fact_check_service import FactCheckService

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.fact_check_tasks.process_fact_check_job_async",
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
)
def process_fact_check_job_async(self, article_id: str):
    """
    Background task to process fact-check job.

    Workflow:
    1. Submit fact-check job to external API
    2. Poll job status until completion (up to 5 minutes)
    3. Store result in database
    4. Update article credibility score

    Args:
        article_id: UUID string of article to fact-check

    Returns:
        dict: Result with status and details
    """
    logger.info(f"Starting fact-check task for article {article_id}")

    try:
        # Run async code in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_process_fact_check(article_id))
            return result
        finally:
            loop.close()

    except AlreadyFactCheckedError:
        logger.warning(f"Article {article_id} already fact-checked, skipping")
        return {"status": "skipped", "article_id": article_id, "reason": "already_fact_checked"}

    except ArticleNotFoundError:
        logger.error(f"Article {article_id} not found")
        return {"status": "error", "article_id": article_id, "error": "article_not_found"}

    except (FactCheckTimeoutError, FactCheckAPIError) as e:
        logger.error(f"Fact-check failed for {article_id}: {str(e)}")

        # Retry with exponential backoff for transient errors
        if self.request.retries < self.max_retries:
            countdown = 60 * (2**self.request.retries)  # 1min, 2min, 4min
            logger.info(f"Retrying fact-check for {article_id} in {countdown}s")
            raise self.retry(exc=e, countdown=countdown)

        return {
            "status": "error",
            "article_id": article_id,
            "error": str(e),
            "retries": self.request.retries,
        }

    except Exception as e:
        logger.error(f"Unexpected error in fact-check task for {article_id}: {str(e)}")
        return {"status": "error", "article_id": article_id, "error": f"unexpected_error: {str(e)}"}


async def _process_fact_check(article_id: str) -> dict:
    """
    Internal async function to process fact-check.

    Args:
        article_id: UUID string of article

    Returns:
        dict: Result with status and details
    """
    async with AsyncSessionLocal() as db:
        # Initialize repositories and service
        fact_check_repo = FactCheckRepository(db)
        article_repo = ArticleRepository(db)
        fact_check_service = FactCheckService(fact_check_repo, article_repo)

        # Convert string to UUID
        article_uuid = UUID(article_id)

        # Step 1: Submit fact-check job
        logger.info(f"Submitting fact-check for article {article_id}")
        fact_check = await fact_check_service.submit_fact_check(
            article_id=article_uuid, mode="summary"
        )

        job_id = fact_check.job_id
        logger.info(f"Fact-check job submitted: {job_id}")

        # Step 2: Poll until completion
        logger.info(f"Polling job {job_id} until completion")
        completed_fact_check = await fact_check_service.poll_and_complete_job(job_id)

        # Commit transaction
        await db.commit()

        logger.info(
            f"Fact-check completed for article {article_id}: "
            f"verdict={completed_fact_check.verdict}, "
            f"score={completed_fact_check.credibility_score}"
        )

        return {
            "status": "success",
            "article_id": article_id,
            "job_id": job_id,
            "verdict": completed_fact_check.verdict,
            "credibility_score": completed_fact_check.credibility_score,
            "processing_time_seconds": completed_fact_check.processing_time_seconds,
        }
