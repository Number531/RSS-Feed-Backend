#!/usr/bin/env python3
"""Test script to debug search endpoint."""
import asyncio
import sys
sys.path.insert(0, '/Users/ej/Downloads/RSS-Feed/backend')

from app.core.database import get_session
from app.repositories.article_repository import ArticleRepository
from app.services.article_service import ArticleService

async def test_search():
    """Test article search."""
    async for session in get_session():
        try:
            # Create repository and service
            article_repo = ArticleRepository(session)
            article_service = ArticleService(article_repo)
            
            # Test search
            print("Testing search for 'trump'...")
            articles, metadata = await article_service.search_articles(
                query="trump",
                page=1,
                page_size=3
            )
            
            print(f"Found {len(articles)} articles")
            print(f"Metadata: {metadata}")
            
            for article in articles:
                print(f"- {article.title}")
                
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(test_search())
