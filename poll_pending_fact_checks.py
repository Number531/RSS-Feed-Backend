#!/usr/bin/env python3
"""
Poll and complete pending fact-check jobs.

This script finds all PENDING fact-checks in the database and polls
the fact-check API to fetch completed results.
"""

import asyncio
import sys
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import select

# Load environment variables
load_dotenv()

from app.db.session import AsyncSessionLocal
from app.models.fact_check import ArticleFactCheck
from app.models.article import Article
from app.services.fact_check_service import FactCheckService
from app.repositories.fact_check_repository import FactCheckRepository
from app.repositories.article_repository import ArticleRepository


async def poll_pending_fact_checks():
    """Poll all pending fact-checks and update with results."""
    print("\n" + "=" * 70)
    print("🔄 POLLING PENDING FACT-CHECKS")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    async with AsyncSessionLocal() as session:
        # Find all pending fact-checks
        result = await session.execute(
            select(ArticleFactCheck)
            .where(ArticleFactCheck.verdict == "PENDING")
            .join(Article)
        )
        pending = result.scalars().all()
        
        if not pending:
            print("✅ No pending fact-checks found!")
            return
        
        print(f"📝 Found {len(pending)} pending fact-check(s)\n")
        
        # Initialize services
        fact_check_repo = FactCheckRepository(session)
        article_repo = ArticleRepository(session)
        fact_check_service = FactCheckService(fact_check_repo, article_repo)
        
        completed = 0
        still_pending = 0
        failed = 0
        
        for i, fc in enumerate(pending, 1):
            # Get article for display
            article_result = await session.execute(
                select(Article).where(Article.id == fc.article_id)
            )
            article = article_result.scalar_one_or_none()
            
            print(f"[{i}/{len(pending)}] Polling: {article.title[:60] if article else 'Unknown'}...")
            print(f"   Job ID: {fc.job_id}")
            
            try:
                # Poll job status
                updated_fc = await fact_check_service.poll_and_complete_job(
                    fc.job_id,
                    max_attempts=1  # Only check once
                )
                
                if updated_fc.verdict != "PENDING":
                    print(f"   ✅ COMPLETED!")
                    print(f"      Verdict: {updated_fc.verdict}")
                    print(f"      Score: {updated_fc.credibility_score}/100")
                    completed += 1
                else:
                    print(f"   ⏳ Still processing...")
                    still_pending += 1
                    
            except Exception as e:
                error_msg = str(e)
                if "still processing" in error_msg.lower() or "in progress" in error_msg.lower():
                    print(f"   ⏳ Still processing...")
                    still_pending += 1
                else:
                    print(f"   ❌ Error: {error_msg}")
                    failed += 1
            
            print()
        
        print("=" * 70)
        print("📊 POLLING RESULTS")
        print("=" * 70)
        print(f"✅ Completed: {completed}")
        print(f"⏳ Still Pending: {still_pending}")
        print(f"❌ Failed: {failed}")
        
        if still_pending > 0:
            print(f"\n💡 TIP: Wait a few more minutes and run this script again.")
            print(f"   Fact-checks typically take 2-3 minutes per article.")


async def show_all_fact_checks():
    """Display all fact-checks in the database."""
    print("\n" + "=" * 70)
    print("📊 ALL FACT-CHECKS IN DATABASE")
    print("=" * 70)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ArticleFactCheck)
            .join(Article)
            .order_by(ArticleFactCheck.fact_checked_at.desc())
        )
        all_fcs = result.scalars().all()
        
        if not all_fcs:
            print("No fact-checks found in database.")
            return
        
        print(f"\nTotal: {len(all_fcs)} fact-check(s)\n")
        
        for fc in all_fcs:
            article_result = await session.execute(
                select(Article).where(Article.id == fc.article_id)
            )
            article = article_result.scalar_one_or_none()
            
            status_icon = "✅" if fc.verdict != "PENDING" else "⏳"
            print(f"{status_icon} {fc.verdict:15} | Score: {fc.credibility_score:3}/100")
            print(f"   Article: {article.title[:60] if article else 'Unknown'}...")
            print(f"   Checked: {fc.fact_checked_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print()


async def main():
    """Main function."""
    print("\n🚀 Fact-Check Polling Script")
    
    # Poll pending fact-checks
    await poll_pending_fact_checks()
    
    # Show all fact-checks
    await show_all_fact_checks()
    
    print("\n" + "=" * 70)
    print("✨ Polling Complete!")
    print("=" * 70)
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
