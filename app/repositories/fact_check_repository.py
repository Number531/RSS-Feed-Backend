"""
Fact-check repository for database operations.
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fact_check import ArticleFactCheck


class FactCheckRepository:
    """Repository for fact-check database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, fact_check_data: dict) -> ArticleFactCheck:
        """
        Create a new fact-check record.

        Args:
            fact_check_data: Dictionary with fact-check data

        Returns:
            ArticleFactCheck: Created fact-check record
        """
        fact_check = ArticleFactCheck(**fact_check_data)
        self.db.add(fact_check)
        await self.db.flush()
        await self.db.refresh(fact_check)
        return fact_check

    async def get_by_id(self, fact_check_id: UUID) -> Optional[ArticleFactCheck]:
        """
        Get fact-check by ID.

        Args:
            fact_check_id: Fact-check UUID

        Returns:
            ArticleFactCheck or None
        """
        query = select(ArticleFactCheck).where(ArticleFactCheck.id == fact_check_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_article_id(self, article_id: UUID) -> Optional[ArticleFactCheck]:
        """
        Get fact-check by article ID.

        Args:
            article_id: Article UUID

        Returns:
            ArticleFactCheck or None
        """
        query = select(ArticleFactCheck).where(ArticleFactCheck.article_id == article_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_job_id(self, job_id: str) -> Optional[ArticleFactCheck]:
        """
        Get fact-check by external job ID.

        Args:
            job_id: External API job ID

        Returns:
            ArticleFactCheck or None
        """
        query = select(ArticleFactCheck).where(ArticleFactCheck.job_id == job_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update(self, fact_check_id: UUID, update_data: dict) -> Optional[ArticleFactCheck]:
        """
        Update fact-check record.

        Args:
            fact_check_id: Fact-check UUID
            update_data: Dictionary with fields to update

        Returns:
            Updated ArticleFactCheck or None
        """
        fact_check = await self.get_by_id(fact_check_id)

        if not fact_check:
            return None

        # Update fields
        for key, value in update_data.items():
            if hasattr(fact_check, key):
                setattr(fact_check, key, value)

        # Update timestamp
        fact_check.updated_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self.db.refresh(fact_check)
        return fact_check

    async def delete(self, fact_check_id: UUID) -> bool:
        """
        Delete fact-check record.

        Args:
            fact_check_id: Fact-check UUID

        Returns:
            bool: True if deleted, False if not found
        """
        fact_check = await self.get_by_id(fact_check_id)

        if not fact_check:
            return False

        await self.db.delete(fact_check)
        await self.db.flush()
        return True

    async def get_recent_fact_checks(self, limit: int = 20) -> List[ArticleFactCheck]:
        """
        Get most recent fact-checks.

        Args:
            limit: Maximum number of records

        Returns:
            List of ArticleFactCheck
        """
        query = (
            select(ArticleFactCheck).order_by(ArticleFactCheck.fact_checked_at.desc()).limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_verdict(self, verdict: str, limit: int = 20) -> List[ArticleFactCheck]:
        """
        Get fact-checks by verdict type.

        Args:
            verdict: Verdict string (e.g., "TRUE", "FALSE", "MISLEADING")
            limit: Maximum number of records

        Returns:
            List of ArticleFactCheck
        """
        query = (
            select(ArticleFactCheck)
            .where(ArticleFactCheck.verdict == verdict)
            .order_by(ArticleFactCheck.fact_checked_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_high_credibility(
        self, threshold: int = 70, limit: int = 20
    ) -> List[ArticleFactCheck]:
        """
        Get fact-checks above credibility threshold.

        Args:
            threshold: Minimum credibility score (0-100)
            limit: Maximum number of records

        Returns:
            List of ArticleFactCheck
        """
        query = (
            select(ArticleFactCheck)
            .where(ArticleFactCheck.credibility_score >= threshold)
            .order_by(ArticleFactCheck.credibility_score.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def exists_for_article(self, article_id: UUID) -> bool:
        """
        Check if article already has a fact-check.

        Args:
            article_id: Article UUID

        Returns:
            bool: True if fact-check exists
        """
        fact_check = await self.get_by_article_id(article_id)
        return fact_check is not None
