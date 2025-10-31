#!/usr/bin/env python3
"""
Populate database with Fox News Politics articles only.
"""

import asyncio
import hashlib
from datetime import datetime
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.rss_source import RSSSource
from app.models.article import Article
from app.services.rss_feed_service import RSSFeedService, parse_feed_entry


async def main():
    """Populate Fox News Politics articles."""
    print("\n" + "=" * 70)
    print("🦊 FOX NEWS POLITICS - ARTICLE POPULATION")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    async with AsyncSessionLocal() as session:
        # Step 1: Add Fox News Politics RSS source
        print("STEP 1: Adding RSS Source")
        print("-" * 70)
        
        source_data = {
            "name": "Fox News - Politics",
            "url": "http://feeds.foxnews.com/foxnews/politics",
            "source_name": "Fox News",
            "category": "politics",
            "is_active": True
        }
        
        # Check if already exists
        result = await session.execute(
            select(RSSSource).where(RSSSource.url == source_data["url"])
        )
        source = result.scalar_one_or_none()
        
        if source:
            print(f"✅ Source already exists: {source_data['name']}")
        else:
            source = RSSSource(**source_data)
            session.add(source)
            await session.commit()
            print(f"✅ Added source: {source_data['name']}")
        
        # Step 2: Fetch articles
        print("\nSTEP 2: Fetching Articles")
        print("-" * 70)
        print(f"Source: {source.name}")
        print(f"URL: {source.url}\n")
        
        rss_service = RSSFeedService(session)
        
        # Fetch RSS feed
        feed = await rss_service.fetch_feed(source)
        
        if not feed or not feed.entries:
            print("❌ No entries in feed")
            return
        
        print(f"📡 Found {len(feed.entries)} entries in feed")
        print(f"⏳ Processing articles...\n")
        
        articles_added = 0
        
        # Process entries (limit to 15 for politics)
        for entry in feed.entries[:15]:
            try:
                # Parse entry
                entry_data = parse_feed_entry(entry)
                
                # Check if exists
                existing = await session.execute(
                    select(Article).where(Article.url == entry_data['url'])
                )
                if existing.scalar_one_or_none():
                    continue
                
                # Create article
                url_hash = hashlib.sha256(entry_data['url'].encode()).hexdigest()
                
                article = Article(
                    title=entry_data['title'],
                    url=entry_data['url'],
                    url_hash=url_hash,
                    description=entry_data.get('description'),
                    content=entry_data.get('content'),
                    author=entry_data.get('author'),
                    published_date=entry_data.get('published_date'),
                    thumbnail_url=entry_data.get('thumbnail_url'),
                    rss_source_id=source.id,
                    category=source.category
                )
                session.add(article)
                await session.flush()
                
                articles_added += 1
                if articles_added <= 5:
                    print(f"   {articles_added}. {article.title[:65]}...")
                
            except Exception as e:
                print(f"   ⚠️ Error: {str(e)}")
        
        # Commit
        await session.commit()
        
        if articles_added > 5:
            print(f"   ... and {articles_added - 5} more")
        
        print(f"\n✅ Added {articles_added} articles")
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 SUMMARY")
        print("=" * 70)
        print(f"Source: Fox News Politics")
        print(f"Articles: {articles_added}")
        print(f"Category: politics")
        
        print("\n" + "=" * 70)
        print("✅ COMPLETE")
        print("=" * 70)
        print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print("\n📋 Next Steps:")
        print("   1. Fact-check articles (optional):")
        print("      python3 test_fox_news_with_factcheck.py")
        print("")
        print("   2. Start backend server:")
        print("      uvicorn app.main:app --reload --port 8000")
        print("")
        print("   3. Test API:")
        print("      curl http://localhost:8000/api/v1/articles?category=politics")
        print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
