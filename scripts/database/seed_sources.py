#!/usr/bin/env python
"""Seed RSS sources into the database"""

import asyncio
import sys
import os
from dotenv import load_dotenv
from sqlalchemy import select

# Load environment variables
load_dotenv()

from app.db.session import AsyncSessionLocal
from app.models.rss_source import RSSSource

# 37 RSS News Sources
RSS_SOURCES = [
    # CNN Feeds
    {"name": "CNN - Top Stories", "url": "http://rss.cnn.com/rss/cnn_topstories.rss", "source_name": "CNN", "category": "general"},
    {"name": "CNN - World", "url": "http://rss.cnn.com/rss/cnn_world.rss", "source_name": "CNN", "category": "world"},
    {"name": "CNN - US", "url": "http://rss.cnn.com/rss/cnn_us.rss", "source_name": "CNN", "category": "us"},
    {"name": "CNN - Politics", "url": "http://rss.cnn.com/rss/cnn_allpolitics.rss", "source_name": "CNN", "category": "politics"},
    
    # Fox News Feeds
    {"name": "Fox News - Latest", "url": "http://feeds.foxnews.com/foxnews/latest", "source_name": "Fox News", "category": "general"},
    {"name": "Fox News - Politics", "url": "http://feeds.foxnews.com/foxnews/politics", "source_name": "Fox News", "category": "politics"},
    {"name": "Fox News - World", "url": "http://feeds.foxnews.com/foxnews/world", "source_name": "Fox News", "category": "world"},
    {"name": "Fox News - US", "url": "http://feeds.foxnews.com/foxnews/national", "source_name": "Fox News", "category": "us"},
    
    # BBC Feeds
    {"name": "BBC - Top Stories", "url": "http://feeds.bbci.co.uk/news/rss.xml", "source_name": "BBC", "category": "general"},
    {"name": "BBC - World", "url": "http://feeds.bbci.co.uk/news/world/rss.xml", "source_name": "BBC", "category": "world"},
    {"name": "BBC - US & Canada", "url": "http://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml", "source_name": "BBC", "category": "us"},
    {"name": "BBC - Politics", "url": "http://feeds.bbci.co.uk/news/politics/rss.xml", "source_name": "BBC", "category": "politics"},
    {"name": "BBC - Technology", "url": "http://feeds.bbci.co.uk/news/technology/rss.xml", "source_name": "BBC", "category": "science"},
    
    # Reuters
    {"name": "Reuters - World News", "url": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best", "source_name": "Reuters", "category": "world"},
    {"name": "Reuters - US News", "url": "https://www.reutersagency.com/feed/?best-regions=united-states", "source_name": "Reuters", "category": "us"},
    
    # NPR
    {"name": "NPR - News", "url": "https://feeds.npr.org/1001/rss.xml", "source_name": "NPR", "category": "general"},
    {"name": "NPR - Politics", "url": "https://feeds.npr.org/1014/rss.xml", "source_name": "NPR", "category": "politics"},
    {"name": "NPR - World", "url": "https://feeds.npr.org/1004/rss.xml", "source_name": "NPR", "category": "world"},
    {"name": "NPR - US", "url": "https://feeds.npr.org/1003/rss.xml", "source_name": "NPR", "category": "us"},
    
    # The Guardian
    {"name": "The Guardian - World", "url": "https://www.theguardian.com/world/rss", "source_name": "The Guardian", "category": "world"},
    {"name": "The Guardian - US", "url": "https://www.theguardian.com/us-news/rss", "source_name": "The Guardian", "category": "us"},
    {"name": "The Guardian - Politics", "url": "https://www.theguardian.com/politics/rss", "source_name": "The Guardian", "category": "politics"},
    {"name": "The Guardian - Science", "url": "https://www.theguardian.com/science/rss", "source_name": "The Guardian", "category": "science"},
    
    # Al Jazeera
    {"name": "Al Jazeera - News", "url": "https://www.aljazeera.com/xml/rss/all.xml", "source_name": "Al Jazeera", "category": "world"},
    
    # Associated Press
    {"name": "AP - Top News", "url": "https://rsshub.app/apnews/topics/apf-topnews", "source_name": "AP", "category": "general"},
    
    # Politico
    {"name": "Politico - Politics", "url": "https://www.politico.com/rss/politics08.xml", "source_name": "Politico", "category": "politics"},
    {"name": "Politico - Congress", "url": "https://www.politico.com/rss/congress.xml", "source_name": "Politico", "category": "politics"},
    
    # The Hill
    {"name": "The Hill - News", "url": "https://thehill.com/feed/", "source_name": "The Hill", "category": "politics"},
    
    # Axios
    {"name": "Axios - Politics", "url": "https://api.axios.com/feed/politics", "source_name": "Axios", "category": "politics"},
    
    # Washington Post
    {"name": "Washington Post - Politics", "url": "https://feeds.washingtonpost.com/rss/politics", "source_name": "Washington Post", "category": "politics"},
    {"name": "Washington Post - World", "url": "https://feeds.washingtonpost.com/rss/world", "source_name": "Washington Post", "category": "world"},
    
    # New York Times
    {"name": "NYT - World", "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "source_name": "New York Times", "category": "world"},
    {"name": "NYT - US", "url": "https://rss.nytimes.com/services/xml/rss/nyt/US.xml", "source_name": "New York Times", "category": "us"},
    {"name": "NYT - Politics", "url": "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml", "source_name": "New York Times", "category": "politics"},
    
    # USA Today
    {"name": "USA Today - News", "url": "http://rssfeeds.usatoday.com/usatoday-NewsTopStories", "source_name": "USA Today", "category": "general"},
    
    # CBS News
    {"name": "CBS News - Latest", "url": "https://www.cbsnews.com/latest/rss/main", "source_name": "CBS News", "category": "general"},
]

async def seed_sources():
    """Seed RSS sources into database"""
    print("🌱 Seeding RSS sources...")
    print("=" * 70)
    print(f"📊 Total sources to add: {len(RSS_SOURCES)}")
    print("")
    
    async with AsyncSessionLocal() as session:
        try:
            added = 0
            skipped = 0
            
            for source_data in RSS_SOURCES:
                # Check if source already exists
                result = await session.execute(
                    select(RSSSource).where(RSSSource.url == source_data["url"])
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    print(f"⏭️  Skipping (exists): {source_data['name']}")
                    skipped += 1
                    continue
                
                # Create new source
                source = RSSSource(**source_data)
                session.add(source)
                print(f"✅ Added: {source_data['name']:<40} ({source_data['source_name']}, {source_data['category']})")
                added += 1
            
            await session.commit()
            
            print("")
            print("=" * 70)
            print("🎉 Seeding complete!")
            print("")
            print(f"   ✅ Added: {added}")
            print(f"   ⏭️  Skipped: {skipped}")
            print(f"   📊 Total: {len(RSS_SOURCES)}")
            print("")
            
            # Show breakdown by category
            from sqlalchemy import func
            result = await session.execute(
                select(RSSSource.category, func.count(RSSSource.id))
                .group_by(RSSSource.category)
                .order_by(func.count(RSSSource.id).desc())
            )
            
            categories = result.fetchall()
            
            print("📋 Sources by category:")
            for category, count in categories:
                print(f"   {category:<15} {count} sources")
            
            print("")
            print("📦 Next steps:")
            print("   1. Test feed fetching: python test_feed_fetch.py")
            print("   2. Start backend: uvicorn app.main:app --reload")
            print("   3. Visit API docs: http://localhost:8000/docs")
            
            return True
            
        except Exception as e:
            await session.rollback()
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
    
    success = asyncio.run(seed_sources())
    sys.exit(0 if success else 1)
