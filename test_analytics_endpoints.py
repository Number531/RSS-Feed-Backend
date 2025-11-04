#!/usr/bin/env python3
"""
Test script to debug new analytics endpoints
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.repositories.analytics_repository import AnalyticsRepository
from app.services.analytics_service import AnalyticsService

engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=True,
    pool_pre_ping=True,
)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def test_high_risk_articles():
    """Test high-risk articles endpoint logic"""
    print("\n" + "=" * 60)
    print("Testing: High-Risk Articles")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        try:
            repo = AnalyticsRepository(session)
            service = AnalyticsService(repo)
            
            result = await service.get_high_risk_articles(days=30, limit=5, offset=0)
            
            print(f"\n✅ Success!")
            print(f"Total articles: {result['total']}")
            print(f"Returned: {len(result['articles'])}")
            print(f"\nFirst article: {result['articles'][0] if result['articles'] else 'None'}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


async def test_source_quality():
    """Test source quality endpoint logic"""
    print("\n" + "=" * 60)
    print("Testing: Source Quality")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        try:
            repo = AnalyticsRepository(session)
            service = AnalyticsService(repo)
            
            result = await service.get_source_quality(days=30)
            
            print(f"\n✅ Success!")
            print(f"Source types: {len(result['by_source_type'])}")
            print(f"Avg credibility: {result['overall']['avg_credibility']}")
            print(f"Avg sources: {result['overall'].get('avg_sources', 'N/A')}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


async def test_risk_correlation():
    """Test risk correlation endpoint logic"""
    print("\n" + "=" * 60)
    print("Testing: Risk Correlation")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        try:
            repo = AnalyticsRepository(session)
            service = AnalyticsService(repo)
            
            result = await service.get_risk_correlation(days=30)
            
            print(f"\n✅ Success!")
            print(f"Risk categories: {len(result['risk_categories'])}")
            for cat in result['risk_categories']:
                print(f"  {cat['category']}: {cat['article_count']} articles, avg score: {cat['avg_credibility']}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


async def test_source_breakdown():
    """Test source breakdown endpoint logic"""
    print("\n" + "=" * 60)
    print("Testing: Source Breakdown (requires article ID)")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        try:
            # Get a sample article ID
            from sqlalchemy import text
            result = await session.execute(
                text("SELECT id FROM articles WHERE fact_check_score IS NOT NULL LIMIT 1")
            )
            article_id = result.scalar()
            
            if not article_id:
                print("⚠️  No fact-checked articles found")
                return
            
            repo = AnalyticsRepository(session)
            service = AnalyticsService(repo)
            
            result = await service.get_source_breakdown(article_id=str(article_id))
            
            if result:
                print(f"\n✅ Success!")
                print(f"Article ID: {result['article_id']}")
                print(f"Primary source: {result['primary_source_type']}")
                print(f"Diversity score: {result['diversity_score']}")
                print(f"Consensus: {result['source_consensus']}")
            else:
                print("⚠️  No source breakdown found")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Analytics Endpoints Diagnostic Test")
    print("=" * 60)
    
    try:
        await test_high_risk_articles()
        await test_source_quality()
        await test_risk_correlation()
        await test_source_breakdown()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
