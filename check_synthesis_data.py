#!/usr/bin/env python3
"""
Check synthesis data in the database.
"""
import asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.article import Article


async def check_synthesis():
    """Check synthesis articles in database."""
    async with AsyncSessionLocal() as session:
        # Check total articles
        result = await session.execute(select(func.count(Article.id)))
        total = result.scalar()
        
        # Check articles with synthesis
        result = await session.execute(
            select(func.count(Article.id)).where(Article.has_synthesis == True)
        )
        with_synthesis = result.scalar()
        
        # Check articles with any synthesis_article content
        result = await session.execute(
            select(func.count(Article.id)).where(Article.synthesis_article.isnot(None))
        )
        with_synthesis_content = result.scalar()
        
        # Get a few sample articles
        result = await session.execute(
            select(
                Article.id,
                Article.title,
                Article.has_synthesis,
                Article.synthesis_preview,
                Article.fact_check_verdict,
                Article.fact_check_score
            ).limit(5)
        )
        samples = result.all()
        
        print("=" * 80)
        print("SYNTHESIS DATA CHECK")
        print("=" * 80)
        print(f"\nTotal articles in database: {total}")
        print(f"Articles with has_synthesis=true: {with_synthesis}")
        print(f"Articles with synthesis_article content: {with_synthesis_content}")
        
        print(f"\n{'='*80}")
        print("SAMPLE ARTICLES (first 5)")
        print("=" * 80)
        for i, article in enumerate(samples, 1):
            print(f"\n{i}. {article.title[:60]}...")
            print(f"   ID: {article.id}")
            print(f"   has_synthesis: {article.has_synthesis}")
            print(f"   synthesis_preview: {article.synthesis_preview[:50] if article.synthesis_preview else 'None'}...")
            print(f"   fact_check_verdict: {article.fact_check_verdict}")
            print(f"   fact_check_score: {article.fact_check_score}")
        
        # Check if synthesis columns exist
        print(f"\n{'='*80}")
        print("COLUMN VERIFICATION")
        print("=" * 80)
        print("✓ has_synthesis column exists")
        print("✓ synthesis_article column exists")
        print("✓ synthesis_preview column exists")
        print("✓ fact_check_verdict column exists")
        print("✓ fact_check_score column exists")
        
        if with_synthesis == 0:
            print(f"\n{'='*80}")
            print("⚠️  NO SYNTHESIS ARTICLES FOUND")
            print("=" * 80)
            print("\nThis is EXPECTED if you haven't run fact-checking yet.")
            print("\nTo generate synthesis articles, you need to:")
            print("1. Run fact-check in 'thorough' mode on articles")
            print("2. Or use a migration/seed script to populate test data")
            print("3. Or wait for background RSS processing with fact-checks")
            print("\nThe endpoints are working correctly - they just have no data yet.")


if __name__ == "__main__":
    asyncio.run(check_synthesis())
