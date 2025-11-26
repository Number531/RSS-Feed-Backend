#!/usr/bin/env python3
"""
Fix has_synthesis flag for articles that have synthesis content.

If you manually populated synthesis_article without setting has_synthesis = true,
this script will fix it.
"""
import asyncio
from sqlalchemy import select, update, func
from app.db.session import AsyncSessionLocal
from app.models.article import Article


async def fix_synthesis_flags():
    """Update has_synthesis flag for articles with synthesis content."""
    async with AsyncSessionLocal() as session:
        # Count articles with synthesis_article but has_synthesis != true
        result = await session.execute(
            select(func.count(Article.id))
            .where(Article.synthesis_article.isnot(None))
            .where(Article.synthesis_article != '')
            .where((Article.has_synthesis.is_(None)) | (Article.has_synthesis == False))
        )
        count_to_fix = result.scalar() or 0
        
        print(f"\n{'='*60}")
        print(f"Fixing has_synthesis flags")
        print(f"{'='*60}")
        print(f"\nArticles to fix: {count_to_fix}")
        
        if count_to_fix == 0:
            print("\n✅ No articles need fixing!")
            print("All articles with synthesis_article already have has_synthesis = true")
            return
        
        # Update the articles
        result = await session.execute(
            update(Article)
            .where(Article.synthesis_article.isnot(None))
            .where(Article.synthesis_article != '')
            .where((Article.has_synthesis.is_(None)) | (Article.has_synthesis == False))
            .values(has_synthesis=True)
        )
        
        await session.commit()
        
        # Verify the fix
        result = await session.execute(
            select(func.count(Article.id))
            .where(Article.has_synthesis == True)
        )
        total_with_flag = result.scalar() or 0
        
        result = await session.execute(
            select(func.count(Article.id))
            .where(Article.synthesis_article.isnot(None))
        )
        total_with_content = result.scalar() or 0
        
        print(f"\n✅ Fixed {count_to_fix} articles!")
        print(f"\n{'='*60}")
        print(f"Verification")
        print(f"{'='*60}")
        print(f"Articles with has_synthesis = true: {total_with_flag}")
        print(f"Articles with synthesis_article content: {total_with_content}")
        
        if total_with_flag == total_with_content:
            print("\n✅ All articles with synthesis content now have has_synthesis = true")
        else:
            print(f"\n⚠️  Mismatch detected:")
            print(f"   {total_with_content - total_with_flag} articles have content but no flag")


if __name__ == "__main__":
    asyncio.run(fix_synthesis_flags())
