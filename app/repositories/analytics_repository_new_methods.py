"""
New analytics repository methods to append to analytics_repository.py

These methods support:
- GET /articles/high-risk
- GET /articles/{id}/source-breakdown  
- GET /analytics/source-quality
- GET /analytics/risk-correlation
"""

# Append these methods to the AnalyticsRepository class:

    async def get_high_risk_articles(
        self,
        min_risk_count: int = 1,
        sort: str = "risk_desc",
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get articles with high-risk claims.

        Args:
            min_risk_count: Minimum high-risk claims count
            sort: Sort order (risk_desc, credibility_asc, recent)
            limit: Max results
            offset: Pagination offset

        Returns:
            Tuple of (articles list, total count)
        """
        from uuid import UUID
        
        # Build base query
        query = (
            select(
                Article.id,
                Article.title,
                Article.created_at,
                ArticleFactCheck.high_risk_claims_count,
                ArticleFactCheck.credibility_score,
                ArticleFactCheck.verdict,
                RSSSource.source_name,
            )
            .select_from(Article)
            .join(ArticleFactCheck, ArticleFactCheck.article_id == Article.id)
            .join(RSSSource, RSSSource.id == Article.rss_source_id)
            .where(ArticleFactCheck.high_risk_claims_count >= min_risk_count)
        )

        # Apply sorting
        if sort == "risk_desc":
            query = query.order_by(desc(ArticleFactCheck.high_risk_claims_count))
        elif sort == "credibility_asc":
            query = query.order_by(ArticleFactCheck.credibility_score.asc())
        elif sort == "recent":
            query = query.order_by(desc(Article.created_at))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        rows = result.mappings().all()

        return [dict(row) for row in rows], total

    async def get_source_breakdown(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        Get source breakdown for a specific article.

        Args:
            article_id: Article UUID

        Returns:
            Dict with source breakdown or None
        """
        from uuid import UUID
        
        query = (
            select(
                ArticleFactCheck.num_sources,
                ArticleFactCheck.source_breakdown,
                ArticleFactCheck.primary_source_type,
                ArticleFactCheck.source_diversity_score,
                ArticleFactCheck.source_consensus,
            )
            .select_from(ArticleFactCheck)
            .where(ArticleFactCheck.article_id == UUID(article_id))
        )

        result = await self.db.execute(query)
        row = result.mappings().first()

        return dict(row) if row else None

    async def get_source_quality_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get source quality metrics grouped by primary source type.

        Args:
            days: Number of days to look back

        Returns:
            List of source type quality metrics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                ArticleFactCheck.primary_source_type.label("type"),
                func.count(ArticleFactCheck.id).label("article_count"),
                func.avg(ArticleFactCheck.source_diversity_score).label("avg_diversity"),
                func.avg(ArticleFactCheck.credibility_score).label("avg_credibility"),
                func.avg(ArticleFactCheck.num_sources).label("avg_sources"),
            )
            .select_from(ArticleFactCheck)
            .join(Article, Article.id == ArticleFactCheck.article_id)
            .where(
                and_(
                    Article.created_at >= cutoff_date,
                    ArticleFactCheck.primary_source_type.isnot(None),
                )
            )
            .group_by(ArticleFactCheck.primary_source_type)
            .order_by(desc("article_count"))
        )

        result = await self.db.execute(query)
        rows = result.mappings().all()

        return [dict(row) for row in rows]

    async def get_risk_correlation_stats(
        self, days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get correlation between risk level and credibility.

        Args:
            days: Number of days to look back

        Returns:
            List of risk category statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Categorize by risk level
        risk_category = case(
            (ArticleFactCheck.high_risk_claims_count == 0, "low_risk"),
            (ArticleFactCheck.high_risk_claims_count <= 2, "medium_risk"),
            else_="high_risk",
        ).label("risk_category")

        query = (
            select(
                risk_category,
                func.count(ArticleFactCheck.id).label("article_count"),
                func.avg(ArticleFactCheck.credibility_score).label("avg_credibility"),
                # Verdict distribution as aggregated counts
                func.count(case((ArticleFactCheck.verdict == "TRUE", 1))).label(
                    "true_count"
                ),
                func.count(case((ArticleFactCheck.verdict == "FALSE", 1))).label(
                    "false_count"
                ),
                func.count(case((ArticleFactCheck.verdict.like("%MOSTLY%"), 1))).label(
                    "mostly_count"
                ),
                func.count(case((ArticleFactCheck.verdict.like("%MIXED%"), 1))).label(
                    "mixed_count"
                ),
                func.count(
                    case((ArticleFactCheck.verdict.like("%UNVERIFIED%"), 1))
                ).label("unverified_count"),
            )
            .select_from(ArticleFactCheck)
            .join(Article, Article.id == ArticleFactCheck.article_id)
            .where(Article.created_at >= cutoff_date)
            .group_by(risk_category)
            .order_by(desc("avg_credibility"))
        )

        result = await self.db.execute(query)
        rows = result.mappings().all()

        return [dict(row) for row in rows]
