#!/usr/bin/env python3
"""
Test script: Populate database with Fox News articles and trigger fact-checking.

This script will:
1. Add Fox News RSS sources to database
2. Fetch articles from Fox News feeds
3. Automatically trigger fact-checking for articles
4. Display results with fact-check status
"""

import asyncio
import sys
import hashlib
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import select, func

# Load environment variables
load_dotenv()

from app.db.session import AsyncSessionLocal
from app.models.rss_source import RSSSource
from app.models.article import Article
from app.models.fact_check import ArticleFactCheck
from app.services.rss_feed_service import RSSFeedService, parse_feed_entry
from app.services.fact_check_service import FactCheckService
from app.repositories.fact_check_repository import FactCheckRepository
from app.repositories.article_repository import ArticleRepository

# Fox News RSS Sources
FOX_NEWS_SOURCES = [
    {"name": "Fox News - Latest", "url": "http://feeds.foxnews.com/foxnews/latest", "source_name": "Fox News", "category": "general"},
    {"name": "Fox News - Politics", "url": "http://feeds.foxnews.com/foxnews/politics", "source_name": "Fox News", "category": "politics"},
    {"name": "Fox News - World", "url": "http://feeds.foxnews.com/foxnews/world", "source_name": "Fox News", "category": "world"},
    {"name": "Fox News - US", "url": "http://feeds.foxnews.com/foxnews/national", "source_name": "Fox News", "category": "us"},
]


async def add_fox_news_sources(session):
    """Add Fox News RSS sources to database."""
    print("\n" + "=" * 70)
    print("STEP 1: Adding Fox News RSS Sources")
    print("=" * 70)
    
    added = 0
    
    for source_data in FOX_NEWS_SOURCES:
        # Check if source already exists
        result = await session.execute(
            select(RSSSource).where(RSSSource.url == source_data["url"])
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"⏭️  Already exists: {source_data['name']}")
            continue
        
        # Create new source
        source = RSSSource(**source_data, is_active=True)
        session.add(source)
        print(f"✅ Added: {source_data['name']}")
        added += 1
    
    await session.commit()
    
    print(f"\n📊 Added {added} new sources")
    return added > 0


async def fetch_articles(session):
    """Fetch articles from Fox News feeds."""
    print("\n" + "=" * 70)
    print("STEP 2: Fetching Articles from Fox News")
    print("=" * 70)
    
    # Get Fox News sources
    result = await session.execute(
        select(RSSSource).where(RSSSource.source_name == "Fox News", RSSSource.is_active == True)
    )
    sources = result.scalars().all()
    
    if not sources:
        print("❌ No Fox News sources found")
        return False
    
    print(f"\n📡 Found {len(sources)} Fox News feed(s)")
    
    # Initialize services
    rss_service = RSSFeedService(session)
    
    total_articles = 0
    
    for source in sources:
        print(f"\n📰 Fetching from: {source.name}")
        print(f"   URL: {source.url}")
        
        try:
            # Fetch RSS feed
            feed = await rss_service.fetch_feed(source)
            
            if not feed or not feed.entries:
                print(f"   ⚠️  No entries in feed")
                continue
            
            print(f"   📡 Found {len(feed.entries)} entries in feed")
            
            # Process each entry
            articles_added = 0
            for entry in feed.entries[:10]:  # Limit to 10 articles per feed
                try:
                    # Parse entry data
                    entry_data = parse_feed_entry(entry)
                    
                    # Check if article already exists by URL
                    existing = await session.execute(
                        select(Article).where(Article.url == entry_data['url'])
                    )
                    if existing.scalar_one_or_none():
                        continue  # Skip duplicates
                    # Create new article
                    # Generate URL hash for deduplication
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
                    if articles_added <= 3:
                        print(f"      {articles_added}. {article.title[:60]}...")
                        
                except Exception as e:
                    print(f"      ⚠️  Error: {str(e)}")
            
            # Commit articles for this source
            await session.commit()
            
            if articles_added > 0:
                print(f"   ✅ Added {articles_added} new articles")
                if articles_added > 3:
                    print(f"      ... and {articles_added - 3} more")
                total_articles += articles_added
            else:
                print(f"   ⚠️  No new articles (all may exist already)")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            await session.rollback()
    
    print(f"\n📊 Total new articles: {total_articles}")
    return total_articles > 0


async def trigger_fact_checks(session):
    """Trigger fact-checking for articles without fact-checks."""
    print("\n" + "=" * 70)
    print("STEP 3: Triggering Fact-Checks")
    print("=" * 70)
    
    # Get articles without fact-checks
    result = await session.execute(
        select(Article).where(Article.fact_check_score == None)
    )
    articles = result.scalars().all()
    
    if not articles:
        print("\n✅ All articles are already fact-checked")
        return True
    
    print(f"\n📝 Found {len(articles)} articles needing fact-checks")
    print(f"⏳ Processing 10 articles at a time (2-3 minutes per article)...\n")
    
    # Initialize repositories and fact-check service
    fact_check_repo = FactCheckRepository(session)
    article_repo = ArticleRepository(session)
    fact_check_service = FactCheckService(fact_check_repo, article_repo)
    
    # Process up to 10 articles at a time
    articles_to_process = articles[:10]
    
    if len(articles) > 10:
        print(f"ℹ️  Processing first 10 articles (out of {len(articles)})")
        print(f"   Run the script again to process more\n")
    
    successful = 0
    failed = 0
    
    for i, article in enumerate(articles_to_process, 1):
        print(f"[{i}/{len(articles_to_process)}] Fact-checking: {article.title[:50]}...")
        print(f"     URL: {article.url}")
        
        try:
            # Submit fact-check
            fact_check = await fact_check_service.submit_fact_check(article.id)
            
            if fact_check:
                print(f"     ✅ Verdict: {fact_check.verdict} | Score: {fact_check.credibility_score}/100")
                successful += 1
            else:
                print(f"     ⚠️  Fact-check submitted but pending")
                
        except Exception as e:
            print(f"     ❌ Error: {str(e)}")
            failed += 1
        
        print()
    
    print(f"📊 Fact-check results:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   ⏳ Pending: {len(articles_to_process) - successful - failed}")
    
    return successful > 0


async def display_results(session):
    """Display final results and statistics."""
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    
    # Count articles
    result = await session.execute(select(func.count(Article.id)))
    total_articles = result.scalar()
    
    # Count fact-checked articles
    result = await session.execute(
        select(func.count(Article.id)).where(Article.fact_check_score != None)
    )
    fact_checked = result.scalar()
    
    # Get fact-check summary
    result = await session.execute(
        select(
            Article.title,
            Article.url,
            Article.fact_check_score,
            Article.fact_check_verdict,
            Article.fact_checked_at
        )
        .where(Article.fact_check_score != None)
        .order_by(Article.fact_checked_at.desc())
        .limit(10)
    )
    fact_checked_articles = result.all()
    
    print(f"\n📊 Database Statistics:")
    print(f"   Total Articles: {total_articles}")
    print(f"   Fact-Checked: {fact_checked}")
    print(f"   Pending: {total_articles - fact_checked}")
    
    if fact_checked_articles:
        print(f"\n✓ Fact-Checked Articles:")
        print("-" * 70)
        
        for article in fact_checked_articles:
            title, url, score, verdict, checked_at = article
            print(f"\n📰 {title[:60]}")
            print(f"   Score: {score}/100 | Verdict: {verdict}")
            print(f"   URL: {url}")
            print(f"   Checked: {checked_at}")
        
        print("\n" + "-" * 70)
    
    # Test the new endpoint
    if fact_checked > 0:
        print("\n🧪 Testing New Fact-Check Endpoint:")
        print("-" * 70)
        
        # Get a fact-checked article
        result = await session.execute(
            select(Article.id, Article.title)
            .where(Article.fact_check_score != None)
            .limit(1)
        )
        article = result.first()
        
        if article:
            article_id, title = article
            
            print(f"\n📍 Sample API Call:")
            print(f"   GET /api/v1/articles/{article_id}/fact-check")
            print(f"\n   Article: {title[:50]}")
            
            # Get fact-check details
            result = await session.execute(
                select(ArticleFactCheck).where(ArticleFactCheck.article_id == article_id)
            )
            fact_check = result.scalar_one_or_none()
            
            if fact_check:
                print(f"\n   ✅ Fact-Check Available:")
                print(f"      Verdict: {fact_check.verdict}")
                print(f"      Score: {fact_check.credibility_score}/100")
                print(f"      Confidence: {fact_check.confidence}")
                print(f"      Sources: {fact_check.num_sources}")
                print(f"      Summary: {fact_check.summary[:100]}...")
    
    print("\n" + "=" * 70)
    print("✨ Test Complete!")
    print("=" * 70)
    
    print("\n📋 Next Steps for Frontend Testing:")
    print("   1. Start the backend server:")
    print("      cd /Users/ej/Downloads/RSS-Feed/backend")
    print("      uvicorn app.main:app --reload")
    print()
    print("   2. Test the API endpoints:")
    print("      GET http://localhost:8000/api/v1/articles")
    print("      GET http://localhost:8000/api/v1/articles/{id}/fact-check")
    print()
    print("   3. Frontend can now:")
    print("      - Display articles with fact-check scores")
    print("      - Show fact-check badges")
    print("      - Open detail modals with evidence")
    print()


async def main():
    """Main execution flow."""
    print("\n" + "=" * 70)
    print("🧪 FOX NEWS RSS + FACT-CHECK TEST")
    print("=" * 70)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    async with AsyncSessionLocal() as session:
        try:
            # Step 1: Add Fox News sources
            await add_fox_news_sources(session)
            
            # Step 2: Fetch articles
            has_articles = await fetch_articles(session)
            
            if not has_articles:
                print("\n⚠️  No articles fetched. This might be because:")
                print("   - Articles were already fetched before")
                print("   - RSS feeds are temporarily unavailable")
                print("   - Network connectivity issues")
                print("\nChecking existing articles...")
            
            # Step 3: Trigger fact-checks
            await trigger_fact_checks(session)
            
            # Step 4: Display results
            await display_results(session)
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    print("\n🚀 Starting Fox News RSS + Fact-Check Test...")
    print("⏱️  Estimated time: 5-10 minutes for 3 articles")
    print()
    
    success = asyncio.run(main())
    
    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    sys.exit(0 if success else 1)
