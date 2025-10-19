#!/usr/bin/env python3
"""
Test full fact-check workflow:
1. Create test article
2. Submit fact-check via service
3. Poll until complete
4. Verify database write
"""
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db.session import AsyncSessionLocal
from app.models.article import Article
from app.models.rss_source import RSSSource
from app.services.fact_check_service import FactCheckService
from app.repositories.fact_check_repository import FactCheckRepository
from app.repositories.article_repository import ArticleRepository


async def test_full_workflow():
    """Test complete fact-check workflow with database write."""
    print("=" * 60)
    print("🧪 FULL FACT-CHECK WORKFLOW TEST")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        # Step 1: Create test RSS source
        print("\n📝 Step 1: Creating test RSS source...")
        rss_source = RSSSource(
            name="Test Source for Fact-Check",
            url="https://example.com/test-feed",
            source_name="Test Source",
            category="general",
            is_active=True
        )
        db.add(rss_source)
        await db.flush()
        print(f"   ✅ RSS source created: {rss_source.id}")
        
        # Step 2: Create test article
        print("\n📝 Step 2: Creating test article...")
        test_url = "https://www.foxnews.com/media/kamala-harris-says-its-f-up-what-rfk-jrs-hhs-doing-america"
        article = Article(
            rss_source_id=rss_source.id,
            title="Test Article for Fact-Check",
            url=test_url,
            url_hash=f"test-hash-{uuid4()}",
            category="general",
            description="Test article to verify fact-check workflow"
        )
        db.add(article)
        await db.commit()
        await db.refresh(article)
        print(f"   ✅ Article created: {article.id}")
        print(f"   📰 URL: {article.url}")
        
        # Step 3: Initialize services
        print("\n📝 Step 3: Initializing fact-check service...")
        fact_check_repo = FactCheckRepository(db)
        article_repo = ArticleRepository(db)
        fact_check_service = FactCheckService(fact_check_repo, article_repo)
        print("   ✅ Services initialized")
        
        # Step 4: Submit fact-check
        print(f"\n📝 Step 4: Submitting fact-check for article {article.id}...")
        try:
            fact_check = await fact_check_service.submit_fact_check(article.id)
            print(f"   ✅ Fact-check submitted!")
            print(f"   🆔 Job ID: {fact_check.job_id}")
            print(f"   📊 Initial verdict: {fact_check.verdict}")
            
            job_id = fact_check.job_id
            
        except Exception as e:
            print(f"   ❌ Submission failed: {e}")
            return 1
        
        # Step 5: Poll until complete
        print(f"\n📝 Step 5: Polling job {job_id} until complete...")
        try:
            completed_fact_check = await fact_check_service.poll_and_complete_job(
                job_id,
                max_attempts=30,  # 2.5 minutes
                poll_interval=5
            )
            
            await db.commit()
            
            print(f"   ✅ Job completed!")
            print(f"   🎯 Verdict: {completed_fact_check.verdict}")
            print(f"   📊 Credibility Score: {completed_fact_check.credibility_score}")
            print(f"   💯 Confidence: {completed_fact_check.confidence}")
            print(f"   📝 Summary: {completed_fact_check.summary[:100]}...")
            
        except Exception as e:
            print(f"   ❌ Polling/completion failed: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        # Step 6: Verify database persistence
        print(f"\n📝 Step 6: Verifying database persistence...")
        
        # Check fact-check record
        db_fact_check = await fact_check_repo.get_by_article_id(article.id)
        if db_fact_check:
            print(f"   ✅ Fact-check record found in database!")
            print(f"      Verdict: {db_fact_check.verdict}")
            print(f"      Score: {db_fact_check.credibility_score}")
        else:
            print(f"   ❌ Fact-check record NOT found in database")
            return 1
        
        # Check article update
        await db.refresh(article)
        if article.fact_check_score is not None:
            print(f"   ✅ Article updated with fact-check data!")
            print(f"      fact_check_score: {article.fact_check_score}")
            print(f"      fact_check_verdict: {article.fact_check_verdict}")
            print(f"      fact_checked_at: {article.fact_checked_at}")
        else:
            print(f"   ⚠️  Article NOT updated (denormalized fields empty)")
        
        # Cleanup
        print(f"\n📝 Step 7: Cleaning up test data...")
        await db.delete(article)
        await db.delete(rss_source)
        await db.commit()
        print(f"   ✅ Test data cleaned up")
        
        print("\n" + "=" * 60)
        print("✅ FULL WORKFLOW TEST PASSED!")
        print("=" * 60)
        print("\n📊 Summary:")
        print(f"   • Article created: {article.id}")
        print(f"   • Fact-check submitted: {job_id}")
        print(f"   • Result stored in database: YES")
        print(f"   • Article updated: {article.fact_check_score is not None}")
        
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(test_full_workflow())
    sys.exit(exit_code)
