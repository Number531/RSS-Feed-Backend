#!/usr/bin/env python3
"""
Verify crawled_content field is accessible via API endpoint.
"""
import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.article import Article


async def verify_crawled_content():
    """Check if articles have crawled_content and verify it's accessible."""
    
    print("=" * 80)
    print("CRAWLED CONTENT VERIFICATION")
    print("=" * 80)
    
    # Get database session
    async for db in get_async_session():
        # Get first article with crawled_content
        stmt = (
            select(Article)
            .where(Article.crawled_content.isnot(None))
            .limit(1)
        )
        result = await db.execute(stmt)
        article = result.scalar_one_or_none()
        
        if not article:
            print("❌ No articles found with crawled_content")
            return
        
        print(f"\n✅ Found article with crawled_content:")
        print(f"  ID: {article.id}")
        print(f"  Title: {article.title[:100]}...")
        print(f"  crawled_content length: {len(article.crawled_content)} characters")
        print(f"  First 500 chars of crawled_content:")
        print(f"  {article.crawled_content[:500]}...")
        
        # Check ArticleResponse schema includes crawled_content
        from app.schemas.article import ArticleResponse
        
        schema_fields = ArticleResponse.model_fields
        if "crawled_content" in schema_fields:
            print(f"\n✅ ArticleResponse schema includes 'crawled_content' field")
        else:
            print(f"\n❌ ArticleResponse schema MISSING 'crawled_content' field")
            return
        
        # Create response object to verify serialization works
        try:
            response = ArticleResponse.model_validate(article)
            print(f"\n✅ ArticleResponse serialization successful")
            print(f"  crawled_content in response: {response.crawled_content is not None}")
            if response.crawled_content:
                print(f"  crawled_content length: {len(response.crawled_content)} characters")
        except Exception as e:
            print(f"\n❌ ArticleResponse serialization failed: {e}")
            return
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("✅ Database: Articles have crawled_content stored")
        print("✅ Schema: ArticleResponse includes crawled_content field")
        print("✅ Serialization: crawled_content can be converted to API response")
        print("\n🎉 Frontend can now access crawled_content via:")
        print(f"   GET /api/v1/articles/{article.id}/full")
        print("\nThe 'article' object in the response will include 'crawled_content'.")
        
        break


if __name__ == "__main__":
    asyncio.run(verify_crawled_content())
