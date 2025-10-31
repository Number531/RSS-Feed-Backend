#!/usr/bin/env python3
"""
Reprocess existing fact-check data with fixed transformation logic.

This script re-applies the transformation logic to existing fact-check records
to correctly calculate verdicts and scores from the validation_results.
"""
import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.article import Article
from app.models.fact_check import ArticleFactCheck
from app.utils.fact_check_transform import (
    calculate_credibility_score,
    calculate_verdict_counts,
    extract_primary_verdict
)

async def reprocess_fact_checks():
    """Reprocess all existing fact-check records."""
    print("=" * 70)
    print("REPROCESSING FACT-CHECK DATA")
    print("=" * 70)
    print()
    
    async with AsyncSessionLocal() as session:
        # Get all fact-check records with validation_results
        result = await session.execute(
            select(ArticleFactCheck).where(
                ArticleFactCheck.validation_results != None
            )
        )
        fact_checks = result.scalars().all()
        
        print(f"Found {len(fact_checks)} fact-check records to reprocess\n")
        
        updated_count = 0
        
        for fc in fact_checks:
            try:
                validation_results = fc.validation_results
                
                if not validation_results or not isinstance(validation_results, list):
                    print(f"⚠️  Skipping {fc.id} - invalid validation_results")
                    continue
                
                # Recalculate verdict and scores using fixed logic
                new_verdict = extract_primary_verdict(validation_results)
                new_score = calculate_credibility_score(validation_results)
                verdict_counts = calculate_verdict_counts(validation_results)
                
                # Get primary result for summary
                primary_result = validation_results[0]
                validation_output = primary_result.get("validation_result", primary_result.get("validation_output", {}))
                new_summary = validation_output.get("summary", fc.summary)
                new_confidence = validation_output.get("confidence", fc.confidence)
                
                # Update fact-check record
                old_verdict = fc.verdict
                old_score = fc.credibility_score
                
                fc.verdict = new_verdict
                fc.credibility_score = new_score
                fc.summary = new_summary
                fc.confidence = new_confidence
                fc.claims_true = verdict_counts["TRUE"]
                fc.claims_false = verdict_counts["FALSE"]
                fc.claims_misleading = verdict_counts["MISLEADING"]
                fc.claims_unverified = verdict_counts["UNVERIFIED"]
                
                # Update associated article
                article = await session.get(Article, fc.article_id)
                if article:
                    article.fact_check_score = new_score
                    article.fact_check_verdict = new_verdict
                    article.fact_checked_at = fc.fact_checked_at
                
                updated_count += 1
                
                print(f"✓ Updated {fc.article_id}")
                print(f"  Old: {old_verdict} (score: {old_score})")
                print(f"  New: {new_verdict} (score: {new_score})")
                print(f"  Claims: {verdict_counts['TRUE']} true, {verdict_counts['FALSE']} false, "
                      f"{verdict_counts['MISLEADING']} misleading, {verdict_counts['UNVERIFIED']} unverified")
                print()
                
            except Exception as e:
                print(f"❌ Error processing {fc.id}: {e}")
                continue
        
        # Commit all changes
        await session.commit()
        
        print("=" * 70)
        print(f"✅ Successfully updated {updated_count}/{len(fact_checks)} records")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(reprocess_fact_checks())
