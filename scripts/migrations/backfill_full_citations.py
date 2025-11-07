#!/usr/bin/env python3
"""
Backfill full citation data for existing fact-checks.

This script fetches the complete validation results from the Railway API
(including references and key_evidence) and updates the database records
that currently only have summary data.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.fact_check_client import FactCheckAPIClient
from app.db.session import AsyncSessionLocal
from app.models.fact_check import ArticleFactCheck
from app.models.article import Article


async def fetch_full_validation_results(job_id: str) -> Optional[dict]:
    """
    Fetch complete validation results from Railway API and extract citations.
    
    Args:
        job_id: Railway API job ID
        
    Returns:
        Enhanced validation_results with references and key_evidence, or None if failed
    """
    try:
        async with FactCheckAPIClient() as client:
            result = await client.get_job_result(job_id)
            
            # Extract validation_results and article_data from the response
            validation_results = result.get("validation_results", [])
            article_data = result.get("article_data", {})
            
            if not validation_results:
                print(f"  ⚠️  No validation_results in API response for job {job_id}")
                return None
            
            # Extract references and key_evidence from article_data
            references = article_data.get("references", [])
            key_evidence = article_data.get("key_evidence", {})
            
            if not key_evidence:
                # Try alternate locations
                verdict_summary = article_data.get("verdict_summary", {})
                key_evidence = verdict_summary.get("key_supporting_evidence", {})
            
            if not key_evidence:
                sidebar = article_data.get("sidebar_elements", {})
                claims_panel = sidebar.get("high_risk_claims_panel", {})
                key_evidence = claims_panel.get("key_evidence", {})
            
            # Inject into validation_results
            enhanced_results = []
            for vr in validation_results:
                enhanced_vr = vr.copy()
                val_result = enhanced_vr.get("validation_result", {})
                
                if references:
                    val_result["references"] = references
                if key_evidence:
                    val_result["key_evidence"] = key_evidence
                
                enhanced_vr["validation_result"] = val_result
                enhanced_results.append(enhanced_vr)
            
            # Check if we got the data
            if references or key_evidence:
                print(f"  ✅ Extracted: references={len(references)}, key_evidence_keys={len(key_evidence) if isinstance(key_evidence, dict) else 'list'}")
                return enhanced_results
            else:
                print(f"  ⚠️  No references or key_evidence found in article_data")
                return None
            
    except Exception as e:
        print(f"  ❌ Error fetching from Railway API: {e}")
        return None


async def check_article_content(session: AsyncSession, article_id: str) -> tuple[bool, Optional[str]]:
    """
    Check if article has full content stored.
    
    Returns:
        (has_content: bool, content: Optional[str])
    """
    result = await session.execute(
        select(Article).where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()
    
    if not article:
        return False, None
    
    has_content = article.content and len(article.content) > 100
    return has_content, article.content


async def backfill_citations():
    """Main backfill function."""
    
    print("\n" + "="*80)
    print("BACKFILLING FULL CITATION DATA FROM RAILWAY API")
    print("="*80 + "\n")
    
    async with AsyncSessionLocal() as session:
        # Get all completed fact-checks
        result = await session.execute(
            select(ArticleFactCheck)
            .where(ArticleFactCheck.verdict != "PENDING")
            .where(ArticleFactCheck.verdict != "ERROR")
            .where(ArticleFactCheck.verdict != "TIMEOUT")
            .where(ArticleFactCheck.verdict != "CANCELLED")
        )
        fact_checks = result.scalars().all()
        
        if not fact_checks:
            print("❌ No completed fact-checks found in database")
            return
        
        print(f"📋 Found {len(fact_checks)} completed fact-checks\n")
        
        updated_count = 0
        failed_count = 0
        already_complete_count = 0
        missing_content_count = 0
        
        for idx, fact_check in enumerate(fact_checks, 1):
            print(f"\n[{idx}/{len(fact_checks)}] Processing fact-check {fact_check.id}")
            print(f"  Job ID: {fact_check.job_id}")
            print(f"  Article ID: {fact_check.article_id}")
            print(f"  Verdict: {fact_check.verdict}")
            
            # Check current validation_results structure
            current_results = fact_check.validation_results
            
            if isinstance(current_results, list) and current_results:
                first_result = current_results[0]
                val_result = first_result.get("validation_result", {})
                
                # Check if already has full data
                if "references" in val_result or "key_evidence" in val_result:
                    print(f"  ✅ Already has full citation data - skipping")
                    already_complete_count += 1
                    continue
            
            # Check article content
            has_content, content = await check_article_content(session, fact_check.article_id)
            if not has_content:
                print(f"  ⚠️  Article missing full content (length: {len(content or '')})")
                missing_content_count += 1
            else:
                print(f"  ✅ Article has content (length: {len(content)})")
            
            # Fetch full data from Railway API
            print(f"  🔄 Fetching full data from Railway API...")
            full_results = await fetch_full_validation_results(fact_check.job_id)
            
            if full_results:
                # Update the database record
                try:
                    await session.execute(
                        update(ArticleFactCheck)
                        .where(ArticleFactCheck.id == fact_check.id)
                        .values(validation_results=full_results)
                    )
                    await session.commit()
                    print(f"  ✅ Updated with full citation data")
                    updated_count += 1
                except Exception as e:
                    print(f"  ❌ Failed to update database: {e}")
                    await session.rollback()
                    failed_count += 1
            else:
                print(f"  ❌ Could not fetch full data from Railway API")
                failed_count += 1
        
        print("\n" + "="*80)
        print("BACKFILL SUMMARY")
        print("="*80)
        print(f"✅ Successfully updated: {updated_count}")
        print(f"📋 Already complete: {already_complete_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"⚠️  Articles missing content: {missing_content_count}")
        print(f"📊 Total processed: {len(fact_checks)}")
        print()


async def main():
    """Entry point."""
    try:
        await backfill_citations()
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
