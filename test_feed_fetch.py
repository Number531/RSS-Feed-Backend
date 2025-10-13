#!/usr/bin/env python
"""Test fetching and processing RSS feeds"""

import asyncio
import sys
import os
from dotenv import load_dotenv
from sqlalchemy import select, func

# Load environment variables
load_dotenv()

from app.db.session import AsyncSessionLocal
from app.models.rss_source import RSSSource
from app.models.article import Article
from app.services.rss_feed_service import RSSFeedService
from app.services.article_processing_service import ArticleProcessingService

async def test_feed_fetch():
    """Test fetching RSS feeds and processing articles"""
    print("📡 Testing RSS Feed Fetching & Processing")
    print("=" * 70)
    
    async with AsyncSessionLocal() as session:
        try:
            # Get active RSS sources
            result = await session.execute(
                select(RSSSource)
                .where(RSSSource.is_active == True)
                .limit(5)  # Test with first 5 sources
            )
            sources = result.scalars().all()
            
            if not sources:
                print("❌ No active RSS sources found!")
                print("   Run: python seed_sources.py")
                return False
            
            print(f"📊 Testing with {len(sources)} sources:")
            for source in sources:
                print(f"   • {source.name} ({source.source_name})")
            print("")
            
            # Initialize services
            rss_service = RSSFeedService(session)
            article_service = ArticleProcessingService(session)
            
            total_articles = 0
            successful_sources = 0
            failed_sources = []
            
            for source in sources:
                print(f"\n📰 Fetching: {source.name}")
                print(f"   URL: {source.url}")
                
                try:
                    # Fetch feed
                    feed = await rss_service.fetch_feed(source)
                    
                    if not feed or not feed.entries:
                        print(f"   ⚠️  No entries found")
                        failed_sources.append((source.name, "No entries"))
                        continue
                    
                    print(f"   ✅ Fetched {len(feed.entries)} articles")
                    
                    # Process first 3 articles from this feed
                    processed_count = 0
                    for entry in feed.entries[:3]:
                        try:
                            # Parse feed entry into article data format
                            from app.services.rss_feed_service import parse_feed_entry
                            article_data = parse_feed_entry(entry)
                            
                            article = await article_service.process_article(article_data, source)
                            if article:
                                print(f"      ✓ Processed: {article.title[:60]}...")
                                processed_count += 1
                            else:
                                print(f"      ⊗ Skipped (duplicate or invalid)")
                        except Exception as e:
                            print(f"      ✗ Error processing entry: {str(e)[:80]}")
                    
                    if processed_count > 0:
                        successful_sources += 1
                        total_articles += processed_count
                        print(f"   💾 Saved {processed_count} new articles")
                    
                except Exception as e:
                    print(f"   ❌ Error: {str(e)[:100]}")
                    failed_sources.append((source.name, str(e)[:50]))
            
            # Show summary
            print("")
            print("=" * 70)
            print("📊 Summary:")
            print(f"   ✅ Successful sources: {successful_sources}/{len(sources)}")
            print(f"   📰 Total articles processed: {total_articles}")
            
            if failed_sources:
                print(f"\n   ⚠️  Failed sources:")
                for name, error in failed_sources:
                    print(f"      • {name}: {error}")
            
            # Check database
            result = await session.execute(
                select(func.count(Article.id))
            )
            total_in_db = result.scalar()
            print(f"\n   📚 Total articles in database: {total_in_db}")
            
            # Show sample articles
            if total_in_db > 0:
                result = await session.execute(
                    select(Article)
                    .order_by(Article.created_at.desc())
                    .limit(5)
                )
                recent_articles = result.scalars().all()
                
                print(f"\n   📄 Recent articles:")
                for article in recent_articles:
                    print(f"      • {article.title[:60]}...")
                    print(f"        Category: {article.category} | {article.created_at.strftime('%H:%M:%S')}")
            
            print("")
            print("=" * 70)
            print("🎉 Feed fetching test complete!")
            print("")
            print("📦 Next steps:")
            print("   1. Set up Celery for automatic fetching every 15 minutes")
            print("   2. Start the backend API: uvicorn app.main:app --reload")
            print("   3. Visit API documentation: http://localhost:8000/docs")
            print("   4. Connect the React Native frontend")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    # Unset any shell DATABASE_URL that might override .env
    if 'DATABASE_URL' in os.environ and not os.environ['DATABASE_URL'].startswith('postgresql+asyncpg://postgres.rtmcxjlagusjhsrslvab'):
        print('⚠️  Warning: DATABASE_URL found in shell environment')
        print('   Temporarily unsetting to use .env value...')
        print('')
        del os.environ['DATABASE_URL']
        load_dotenv(override=True)
    
    success = asyncio.run(test_feed_fetch())
    sys.exit(0 if success else 1)
