"""Service for analyzing content quality metrics."""

from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.comment import Comment
from app.models.vote import Vote
from app.models.bookmark import Bookmark
from app.models.reading_history import ReadingHistory


class ContentQualityService:
    """Service for calculating and analyzing content quality metrics."""

    def __init__(self, db: AsyncSession):
        """Initialize the content quality service."""
        self.db = db

    async def get_quality_report(
        self,
        days: int = 7,
        category: str | None = None,
        min_engagement: int = 5
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive content quality report.
        
        Args:
            days: Number of days to analyze (default: 7)
            category: Optional category filter
            min_engagement: Minimum engagement threshold (votes + comments + bookmarks)
            
        Returns:
            Dict containing quality metrics, top performers, and recommendations
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        # Build base query
        query = select(Article).where(Article.created_at >= since)
        if category:
            query = query.where(Article.category == category)
            
        articles = (await self.db.execute(query)).scalars().all()
        
        if not articles:
            return {
                "period_days": days,
                "category": category,
                "total_articles": 0,
                "quality_metrics": {},
                "top_performers": [],
                "recommendations": []
            }
        
        # Calculate metrics for each article
        article_metrics = []
        for article in articles:
            metrics = await self._calculate_article_metrics(article)
            
            # Filter by engagement threshold
            total_engagement = (
                metrics["votes_count"] + 
                metrics["comments_count"] + 
                metrics["bookmarks_count"]
            )
            
            if total_engagement >= min_engagement:
                article_metrics.append({
                    "article_id": str(article.id),
                    "title": article.title,
                    "url": article.url,
                    "published_at": article.published_at.isoformat() if article.published_at else None,
                    "category": article.category,
                    "metrics": metrics,
                    "quality_score": self._calculate_quality_score(metrics),
                    "total_engagement": total_engagement
                })
        
        # Sort by quality score
        article_metrics.sort(key=lambda x: x["quality_score"], reverse=True)
        
        # Calculate aggregate metrics
        quality_metrics = self._calculate_aggregate_metrics(article_metrics)
        
        # Get top performers
        top_performers = article_metrics[:10]
        
        # Generate recommendations
        recommendations = self._generate_recommendations(article_metrics, quality_metrics)
        
        return {
            "period_days": days,
            "category": category,
            "total_articles": len(articles),
            "articles_analyzed": len(article_metrics),
            "min_engagement_threshold": min_engagement,
            "quality_metrics": quality_metrics,
            "top_performers": top_performers,
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }

    async def _calculate_article_metrics(self, article: Article) -> Dict[str, Any]:
        """Calculate detailed metrics for a single article."""
        
        # Count votes
        votes_query = select(func.count(Vote.id)).where(Vote.article_id == article.id)
        votes_count = (await self.db.execute(votes_query)).scalar_one()
        
        # Count upvotes and downvotes
        upvotes_query = select(func.count(Vote.id)).where(
            and_(Vote.article_id == article.id, Vote.vote_value == 1)
        )
        upvotes = (await self.db.execute(upvotes_query)).scalar_one()
        
        downvotes_query = select(func.count(Vote.id)).where(
            and_(Vote.article_id == article.id, Vote.vote_value == -1)
        )
        downvotes = (await self.db.execute(downvotes_query)).scalar_one()
        
        # Count comments
        comments_query = select(func.count(Comment.id)).where(Comment.article_id == article.id)
        comments_count = (await self.db.execute(comments_query)).scalar_one()
        
        # Count bookmarks
        bookmarks_query = select(func.count(Bookmark.id)).where(Bookmark.article_id == article.id)
        bookmarks_count = (await self.db.execute(bookmarks_query)).scalar_one()
        
        # Calculate engagement rate (interactions per view)
        # Note: Would need article_analytics for actual view counts
        
        # Calculate vote ratio
        vote_ratio = upvotes / votes_count if votes_count > 0 else 0
        
        # Calculate controversy score (high votes + balanced ratio = controversial)
        if votes_count > 0:
            controversy = 1 - abs(upvotes - downvotes) / votes_count
        else:
            controversy = 0
        
        return {
            "votes_count": votes_count,
            "upvotes": upvotes,
            "downvotes": downvotes,
            "vote_ratio": round(vote_ratio, 3),
            "comments_count": comments_count,
            "bookmarks_count": bookmarks_count,
            "controversy_score": round(controversy, 3)
        }

    def _calculate_quality_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate overall quality score (0-100).
        
        Weighted formula:
        - Vote ratio (35%): Positive sentiment
        - Comments (25%): Discussion quality
        - Bookmarks (20%): Long-term value
        - Total votes (15%): Overall engagement
        - Low controversy bonus (5%): Reduces polarization penalty
        """
        # Normalize metrics to 0-100 scale
        vote_ratio_score = metrics["vote_ratio"] * 100
        
        # Logarithmic scaling for counts (diminishing returns)
        import math
        comments_score = min(math.log1p(metrics["comments_count"]) * 15, 100)
        bookmarks_score = min(math.log1p(metrics["bookmarks_count"]) * 20, 100)
        votes_score = min(math.log1p(metrics["votes_count"]) * 10, 100)
        
        # Controversy penalty (highly controversial = lower quality)
        controversy_penalty = metrics["controversy_score"] * 5
        
        quality_score = (
            vote_ratio_score * 0.35 +
            comments_score * 0.25 +
            bookmarks_score * 0.20 +
            votes_score * 0.15 +
            (100 - controversy_penalty) * 0.05
        )
        
        return round(quality_score, 2)

    def _calculate_aggregate_metrics(self, article_metrics: list) -> Dict[str, Any]:
        """Calculate aggregate metrics across all articles."""
        if not article_metrics:
            return {}
        
        quality_scores = [a["quality_score"] for a in article_metrics]
        vote_ratios = [a["metrics"]["vote_ratio"] for a in article_metrics]
        comments_counts = [a["metrics"]["comments_count"] for a in article_metrics]
        
        return {
            "avg_quality_score": round(sum(quality_scores) / len(quality_scores), 2),
            "median_quality_score": round(sorted(quality_scores)[len(quality_scores) // 2], 2),
            "avg_vote_ratio": round(sum(vote_ratios) / len(vote_ratios), 3),
            "avg_comments_per_article": round(sum(comments_counts) / len(comments_counts), 2),
            "total_engagement": sum(a["total_engagement"] for a in article_metrics),
            "quality_distribution": {
                "excellent (80+)": len([s for s in quality_scores if s >= 80]),
                "good (60-79)": len([s for s in quality_scores if 60 <= s < 80]),
                "average (40-59)": len([s for s in quality_scores if 40 <= s < 60]),
                "poor (<40)": len([s for s in quality_scores if s < 40])
            }
        }

    def _generate_recommendations(
        self, 
        article_metrics: list, 
        aggregate_metrics: Dict[str, Any]
    ) -> list:
        """Generate actionable recommendations based on quality analysis."""
        recommendations = []
        
        if not article_metrics:
            return recommendations
        
        avg_quality = aggregate_metrics.get("avg_quality_score", 0)
        
        # Recommendation 1: Quality threshold
        if avg_quality < 50:
            recommendations.append({
                "type": "quality_improvement",
                "priority": "high",
                "message": f"Average quality score ({avg_quality}) is below target. Focus on sources with higher engagement.",
                "action": "Review RSS sources and prioritize quality over quantity"
            })
        
        # Recommendation 2: Category performance
        category_performance = {}
        for article in article_metrics:
            cat = article["category"] or "uncategorized"
            if cat not in category_performance:
                category_performance[cat] = []
            category_performance[cat].append(article["quality_score"])
        
        if category_performance:
            best_category = max(category_performance, key=lambda k: sum(category_performance[k]) / len(category_performance[k]))
            worst_category = min(category_performance, key=lambda k: sum(category_performance[k]) / len(category_performance[k]))
            
            recommendations.append({
                "type": "category_optimization",
                "priority": "medium",
                "message": f"'{best_category}' category performs best. Consider expanding similar sources.",
                "action": f"Increase content from '{best_category}' category, review '{worst_category}' sources"
            })
        
        # Recommendation 3: Engagement patterns
        high_engagement = [a for a in article_metrics if a["total_engagement"] > 50]
        if high_engagement:
            avg_quality_high_engagement = sum(a["quality_score"] for a in high_engagement) / len(high_engagement)
            recommendations.append({
                "type": "engagement_insight",
                "priority": "info",
                "message": f"High-engagement articles (50+ interactions) have {avg_quality_high_engagement:.1f} avg quality score",
                "action": "Analyze common attributes of top performers for content strategy"
            })
        
        # Recommendation 4: Vote ratio insights
        avg_vote_ratio = aggregate_metrics.get("avg_vote_ratio", 0)
        if avg_vote_ratio < 0.7:
            recommendations.append({
                "type": "sentiment_alert",
                "priority": "medium",
                "message": f"Vote ratio ({avg_vote_ratio:.2f}) indicates mixed sentiment. Review content sources.",
                "action": "Focus on authoritative, well-researched sources"
            })
        
        return recommendations
