#!/usr/bin/env python3
"""Review fact-check outputs with available data."""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db.session import AsyncSessionLocal
from app.repositories.fact_check_repository import FactCheckRepository
from sqlalchemy import select
from app.models import Article


async def review_all():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Article)
            .where(Article.fact_check_verdict.isnot(None))
            .order_by(Article.created_at.desc())
            .limit(10)
        )
        articles = result.scalars().all()
        
        print('\n' + '='*90)
        print(f'FACT-CHECK REVIEW: {len(articles)} Articles (Iterative Mode)')
        print('='*90 + '\n')
        
        for idx, article in enumerate(articles, 1):
            print(f'\n{"─"*90}')
            print(f'[{idx}] {article.title[:75]}...')
            print(f'{"─"*90}')
            print(f'URL: {article.url}')
            print(f'ID: {article.id}')
            
            # Article-level fact-check summary
            print(f'\n📊 SUMMARY:')
            print(f'   Verdict: {article.fact_check_verdict}')
            print(f'   Score: {article.fact_check_score}/100')
            print(f'   Checked: {article.fact_checked_at}')
            
            # Get detailed fact-check
            fact_check = await FactCheckRepository(session).get_by_article_id(article.id)
            
            if fact_check:
                print(f'\n📋 DETAILS:')
                print(f'   Job ID: {fact_check.job_id}')
                print(f'   Mode: {fact_check.validation_mode}')
                print(f'   Processing Time: {fact_check.processing_time_seconds}s')
                print(f'   Claims Analyzed: {fact_check.claims_analyzed}')
                print(f'   Claims Validated: {fact_check.claims_validated}')
                
                # Breakdown
                print(f'\n   Breakdown:')
                print(f'     ✓ True: {fact_check.claims_true or 0}')
                print(f'     ✗ False: {fact_check.claims_false or 0}')
                print(f'     ⚠ Misleading: {fact_check.claims_misleading or 0}')
                print(f'     ? Unverified: {fact_check.claims_unverified or 0}')
                
                # Evidence quality
                print(f'\n   Evidence Quality:')
                print(f'     Sources Used: {fact_check.num_sources or 0}')
                
                # Costs
                if fact_check.api_costs:
                    costs = fact_check.api_costs
                    print(f'\n   API Costs:')
                    print(f'     Total: ${costs.get("total", 0):.4f}')
                    breakdown = costs.get('breakdown', {})
                    if breakdown:
                        print(f'     - Extraction: ${breakdown.get("claim_extraction", 0):.4f}')
                        print(f'     - Search: ${breakdown.get("evidence_search", 0):.4f}')
                        print(f'     - Validation: ${breakdown.get("validation", 0):.4f}')
                
                # Show top 3 claims
                if fact_check.validation_results:
                    print(f'\n   🔍 CLAIMS ({len(fact_check.validation_results)} total):')
                    for i, val_result in enumerate(fact_check.validation_results[:3], 1):
                        claim = val_result.get('claim', '')
                        verdict = val_result.get('verdict', 'N/A')
                        confidence = val_result.get('confidence', 0)
                        
                        # Truncate claim
                        if len(claim) > 70:
                            claim = claim[:70] + '...'
                        
                        print(f'\n     {i}. {claim}')
                        print(f'        Verdict: {verdict}')
                        print(f'        Confidence: {confidence:.2f}')


if __name__ == "__main__":
    asyncio.run(review_all())
