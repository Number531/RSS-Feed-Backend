#!/usr/bin/env python3
"""
Fetch completed fact-check results and save them to the database.
"""

import asyncio
from datetime import datetime
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.article import Article
from app.models.fact_check import ArticleFactCheck
from app.clients.fact_check_client import FactCheckAPIClient
from app.utils.fact_check_transform import transform_api_result_to_db


# Job IDs from the completed fact-checks
COMPLETED_JOBS = [
    {
        'job_id': 'e8463762-6805-4c43-b765-9fadba556ff5',
        'url': 'https://www.foxnews.com/world/brazen-louvre-robbery-crew-may-have-been-hired-collector-prosecutor-says'
    },
    {
        'job_id': 'e4bd54e2-1cf2-4543-b423-1370bcfaa5ae',
        'url': 'https://www.foxnews.com/media/karine-jean-pierre-insists-skeptical-cbs-anchors-biden-treated-unfairly-always-seemed-sharp'
    },
    {
        'job_id': '38f45b0d-26b1-41e9-85ee-175dd0af2ea7',
        'url': 'https://www.foxnews.com/sports/details-emerge-death-ex-nfl-star-doug-martin'
    },
]


async def fetch_and_save_fact_checks():
    """Fetch completed fact-check results and save to database."""
    print("\n" + "=" * 70)
    print("🔄 FETCHING COMPLETED FACT-CHECKS")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    async with AsyncSessionLocal() as session:
        async with FactCheckAPIClient() as client:
            
            for i, job_info in enumerate(COMPLETED_JOBS, 1):
                job_id = job_info['job_id']
                url = job_info['url']
                
                print(f"[{i}/{len(COMPLETED_JOBS)}] Processing job: {job_id[:20]}...")
                print(f"   URL: {url[:80]}...")
                
                try:
                    # Find the article by URL
                    result = await session.execute(
                        select(Article).where(Article.url == url)
                    )
                    article = result.scalar_one_or_none()
                    
                    if not article:
                        print(f"   ❌ Article not found in database")
                        continue
                    
                    print(f"   ✅ Found article: {article.title[:50]}...")
                    
                    # Check if fact-check already exists
                    existing_fc = await session.execute(
                        select(ArticleFactCheck).where(
                            ArticleFactCheck.article_id == article.id
                        )
                    )
                    if existing_fc.scalar_one_or_none():
                        print(f"   ⏭️  Fact-check already exists, skipping")
                        continue
                    
                    # Fetch the completed result from API
                    print(f"   📥 Fetching fact-check result...")
                    api_result = await client.get_job_result(job_id)
                    
                    # Transform API result to database format
                    db_data = transform_api_result_to_db(api_result, article.id)
                    db_data['job_id'] = job_id
                    db_data['validation_mode'] = 'summary'
                    
                    # Create fact-check record
                    fact_check = ArticleFactCheck(**db_data)
                    session.add(fact_check)
                    
                    # Update article's denormalized fact-check fields
                    article.fact_check_score = db_data['credibility_score']
                    article.fact_check_verdict = db_data['verdict']
                    article.fact_checked_at = db_data['fact_checked_at']
                    
                    await session.flush()
                    
                    print(f"   ✅ SAVED!")
                    print(f"      Verdict: {db_data['verdict']}")
                    print(f"      Score: {db_data['credibility_score']}/100")
                    print(f"      Claims Analyzed: {db_data.get('claims_analyzed', 0)}")
                    print()
                    
                except Exception as e:
                    print(f"   ❌ Error: {str(e)}")
                    print()
                    continue
            
            # Commit all changes
            await session.commit()
            print("=" * 70)
            print("✅ ALL FACT-CHECKS SAVED TO DATABASE")
            print("=" * 70)


async def show_saved_fact_checks():
    """Display all saved fact-checks."""
    print("\n" + "=" * 70)
    print("📊 FACT-CHECKS IN DATABASE")
    print("=" * 70)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ArticleFactCheck)
            .join(Article)
            .order_by(ArticleFactCheck.credibility_score.desc())
        )
        fact_checks = result.scalars().all()
        
        if not fact_checks:
            print("No fact-checks found.")
            return
        
        print(f"\nTotal: {len(fact_checks)} fact-check(s)\n")
        
        for fc in fact_checks:
            article_result = await session.execute(
                select(Article).where(Article.id == fc.article_id)
            )
            article = article_result.scalar_one_or_none()
            
            # Verdict emoji
            verdict_emoji = {
                'MOSTLY_TRUE': '✅',
                'MIXED': '⚠️',
                'MOSTLY_FALSE': '❌',
                'FALSE': '🚫',
                'TRUE': '✅',
            }.get(fc.verdict, '📊')
            
            print(f"{verdict_emoji} {fc.verdict:15} | Score: {fc.credibility_score:3}/100")
            print(f"   Article: {article.title[:60] if article else 'Unknown'}...")
            print(f"   Summary: {fc.summary[:100] if fc.summary else 'N/A'}...")
            print(f"   Claims: {fc.claims_analyzed} analyzed, {fc.claims_true} true, {fc.claims_false} false")
            print(f"   Sources: {fc.num_sources} used")
            print()


async def main():
    """Main function."""
    print("\n🚀 Fetch Completed Fact-Checks\n")
    
    await fetch_and_save_fact_checks()
    await show_saved_fact_checks()
    
    print("\n" + "=" * 70)
    print("✨ Complete!")
    print("=" * 70)
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    print("\n📋 Next Steps:")
    print("   1. Start backend: uvicorn app.main:app --reload --port 8000")
    print("   2. Test API: curl http://localhost:8000/api/v1/articles")
    print("   3. Frontend can now display fact-check scores!")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
