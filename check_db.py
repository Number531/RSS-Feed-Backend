#!/usr/bin/env python3
"""Check database content for RSS feeds and articles."""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://postgres.rtmcxjlagusjhsrslvab:%40136Breezylane%21@aws-1-us-east-2.pooler.supabase.com:5432/postgres"

async def check_database():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("=" * 80)
        print("DATABASE CONTENT CHECK")
        print("=" * 80)
        
        # Count RSS sources
        result = await session.execute(text("SELECT COUNT(*) FROM rss_sources"))
        feeds_count = result.scalar()
        print(f"\n📡 RSS Sources: {feeds_count}")
        
        result = await session.execute(text("SELECT COUNT(*) FROM rss_sources WHERE is_active = true"))
        active_count = result.scalar()
        print(f"   Active: {active_count}")
        
        # Count articles
        result = await session.execute(text("SELECT COUNT(*) FROM articles"))
        articles_count = result.scalar()
        print(f"\n📰 Articles: {articles_count}")
        
        # Check for thumbnails
        result = await session.execute(text("SELECT COUNT(*) FROM articles WHERE thumbnail_url IS NOT NULL"))
        thumbs_count = result.scalar()
        print(f"   With thumbnails: {thumbs_count} ({round(thumbs_count/articles_count*100 if articles_count > 0 else 0, 1)}%)")
        
        # Sample RSS sources
        if feeds_count > 0:
            print(f"\n📋 Sample RSS Feeds (first 5):")
            result = await session.execute(text("""
                SELECT name, source_name, category, url, last_fetched, last_successful_fetch 
                FROM rss_sources 
                ORDER BY created_at 
                LIMIT 5
            """))
            for row in result:
                print(f"   • {row.name} ({row.source_name}) - {row.category}")
                print(f"     URL: {row.url[:70]}...")
                print(f"     Last fetched: {row.last_fetched or 'Never'}")
                print()
        
        # Sample articles with thumbnails
        if thumbs_count > 0:
            print(f"\n🖼️  Sample Articles WITH Thumbnails (first 3):")
            result = await session.execute(text("""
                SELECT title, source, thumbnail_url, published_at 
                FROM articles 
                WHERE thumbnail_url IS NOT NULL 
                ORDER BY published_at DESC 
                LIMIT 3
            """))
            for row in result:
                print(f"   • {row.title[:70]}...")
                print(f"     Source: {row.source}")
                print(f"     Thumbnail: {row.thumbnail_url[:80]}...")
                print(f"     Published: {row.published_at}")
                print()
        
        # Sample articles without thumbnails
        result = await session.execute(text("""
            SELECT COUNT(*) FROM articles WHERE thumbnail_url IS NULL
        """))
        no_thumbs = result.scalar()
        
        if no_thumbs > 0:
            print(f"\n❌ Articles WITHOUT Thumbnails: {no_thumbs}")
            result = await session.execute(text("""
                SELECT title, source, published_at 
                FROM articles 
                WHERE thumbnail_url IS NULL 
                ORDER BY published_at DESC 
                LIMIT 3
            """))
            for row in result:
                print(f"   • {row.title[:70]}...")
                print(f"     Source: {row.source}")
                print()
        
        print("=" * 80)
        
        # Summary
        print("\n✅ SUMMARY:")
        if articles_count == 0:
            print("   ⚠️  Database is EMPTY - No articles found")
            print("   ℹ️  Run: python scripts/database/seed_database.py")
            print("   OR fetch real RSS feeds to populate content")
        elif thumbs_count == 0:
            print(f"   ⚠️  {articles_count} articles but NO THUMBNAILS")
            print("   ℹ️  Test articles don't have thumbnail URLs")
            print("   ✅ Fetch from real RSS feeds to get images")
        else:
            print(f"   ✅ {thumbs_count}/{articles_count} articles have thumbnails!")
            print("   ✅ Image support is working!")
        
        print("\n" + "=" * 80)
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_database())
