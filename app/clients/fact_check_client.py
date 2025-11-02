"""
HTTP client for internal fact-check API.

Handles communication with the fact-check microservice.
No authentication required (internal service).
"""

import logging
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class FactCheckAPIClient:
    """Client for internal fact-check API."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        """
        Initialize fact-check API client.

        Args:
            base_url: API base URL (defaults to settings)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or settings.FACT_CHECK_API_URL
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            base_url=self.base_url, timeout=httpx.Timeout(timeout), follow_redirects=True
        )

    async def submit_fact_check(
        self,
        url: str,
        mode: str = "summary",
        generate_image: bool = False,
        generate_article: bool = True,
    ) -> Dict[str, Any]:
        """
        Submit a fact-check job.

        Args:
            url: Article URL to fact-check
            mode: Validation mode (standard, thorough, summary)
            generate_image: Whether to generate editorial image
            generate_article: Whether to generate comprehensive article

        Returns:
            dict: {
                "success": bool,
                "job_id": str,
                "message": str,
                "status_url": str,
                "result_url": str,
                "estimated_time_seconds": int
            }

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If network error occurs
        """
        payload = {
            "url": url,
            "mode": mode,
            "generate_image": generate_image,
            "generate_article": generate_article,
        }

        logger.info(f"Submitting fact-check job", extra={"url": url, "mode": mode})

        try:
            response = await self.client.post("/fact-check/submit", json=payload)
            response.raise_for_status()

            result = response.json()

            logger.info(
                f"Fact-check job submitted successfully",
                extra={"job_id": result.get("job_id"), "url": url},
            )

            return result

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error submitting fact-check",
                extra={"status_code": e.response.status_code, "url": url, "error": str(e)},
            )
            raise
        except httpx.RequestError as e:
            logger.error(
                f"Network error submitting fact-check", extra={"url": url, "error": str(e)}
            )
            raise

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get status of a fact-check job.

        Args:
            job_id: Job identifier

        Returns:
            dict: {
                "job_id": str,
                "status": str,  # queued, started, finished, failed
                "phase": str,
                "progress": int,  # 0-100
                "elapsed_time_seconds": int,
                "estimated_remaining_seconds": int,
                "article_ready": bool
            }

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If network error occurs
        """
        try:
            response = await self.client.get(f"/fact-check/{job_id}/status")
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Job not found: {job_id}")
            else:
                logger.error(
                    f"Error fetching job status", extra={"job_id": job_id, "error": str(e)}
                )
            raise
        except httpx.RequestError as e:
            logger.error(
                f"Network error fetching job status", extra={"job_id": job_id, "error": str(e)}
            )
            raise

    async def get_job_result(self, job_id: str) -> Dict[str, Any]:
        """
        Get completed fact-check result.

        Args:
            job_id: Job identifier

        Returns:
            dict: Complete fact-check result with validation_results

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If network error occurs
        """
        try:
            response = await self.client.get(f"/fact-check/{job_id}/result")
            response.raise_for_status()

            result = response.json()

            logger.info(
                f"Retrieved fact-check result",
                extra={
                    "job_id": job_id,
                    "status": result.get("status"),
                    "claims_analyzed": result.get("claims_analyzed", 0),
                },
            )

            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Result not found for job: {job_id}")
            else:
                logger.error(
                    f"Error fetching job result", extra={"job_id": job_id, "error": str(e)}
                )
            raise
        except httpx.RequestError as e:
            logger.error(
                f"Network error fetching job result", extra={"job_id": job_id, "error": str(e)}
            )
            raise

    async def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel a running fact-check job.

        Args:
            job_id: Job identifier

        Returns:
            dict: Cancellation confirmation

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If network error occurs
        """
        try:
            response = await self.client.delete(f"/fact-check/{job_id}/cancel")
            response.raise_for_status()

            logger.info(f"Job cancelled: {job_id}")

            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"Error cancelling job", extra={"job_id": job_id, "error": str(e)})
            raise
        except httpx.RequestError as e:
            logger.error(f"Network error cancelling job", extra={"job_id": job_id, "error": str(e)})
            raise

    async def health_check(self) -> Dict[str, Any]:
        """
        Check API health.

        Returns:
            dict: Health status

        Raises:
            httpx.RequestError: If API is unreachable
        """
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
