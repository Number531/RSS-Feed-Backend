#!/usr/bin/env python3
"""
Review fact-check outputs for all processed articles.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db.session import AsyncSessionLocal
from app.repositories.fact_check_repository import FactCheckRepository
from app.repositories.article_repository import ArticleRepository
from sqlalchemy import select
from app.models import Article


async def review_all_articles():
    async with AsyncSessionLocal() as session:
        fact_check_repo = FactCheckRepository(session)
        article_repo = ArticleRepository(session)
        
        # Get all articles with fact-checks
        result = await session.execute(
            select(Article)
            .where(Article.fact_check_verdict.isnot(None))
            .order_by(Article.created_at.desc())
            .limit(10)
        )
        articles = result.scalars().all()
        
        print('\n' + '='*80)
        print(f'FACT-CHECK REVIEW: {len(articles)} Articles (Iterative Mode)')
        print('='*80 + '\n')
        
        for idx, article in enumerate(articles, 1):
            print(f'\n--- Article {idx} ---')
            print(f'Title: {article.title[:80]}...')
            print(f'URL: {article.url}')
            print(f'Article ID: {article.id}')
            print('\nFact-Check Summary:')
            print(f'  Verdict: {article.fact_check_verdict}')
            print(f'  Score: {article.fact_check_score}')
            print(f'  Checked At: {article.fact_checked_at}')
            
            # Get full fact-check details
            latest = await fact_check_repo.get_by_article_id(article.id)
            
            if latest:
                print('\nFact-Check Details:')
                print(f'  Job ID: {latest.job_id}')
                print(f'  Mode: {latest.validation_mode}')
                print(f'  Processing Time: {latest.processing_time_seconds}s')
                
                if latest.validation_results:
                    result_data = latest.validation_results
                    print('\nValidation Results:')
                    print(f'  Claims Analyzed: {result_data.get("claims_analyzed", "N/A")}')
                    print(f'  Claims Validated: {result_data.get("claims_validated", "N/A")}')
                    
                    # Check for iterative metadata
                    metadata = result_data.get('metadata', {})
                    if metadata.get('is_iterative_mode'):
                        iter_meta = metadata.get('iterative_metadata', {})
                        print('\nIterative Mode Metadata:')
                        print(f'  Iterations: {iter_meta.get("iterations_completed", "N/A")}')
                        print(f'  Issues Found: {iter_meta.get("issues_found", "N/A")}')
                        print(f'  Total Time: {iter_meta.get("total_time_seconds", "N/A")}s')
                        print(f'  Early Stopped: {iter_meta.get("early_stopped", "N/A")}')
                        
                        # Article accuracy
                        accuracy = iter_meta.get('article_accuracy', {})
                        if accuracy:
                            print('\nArticle Accuracy:')
                            print(f'  Reliability Score: {accuracy.get("reliability_score", "N/A")}')
                            print(f'  Verdict: {accuracy.get("verdict", "N/A")}')
                            explanation = accuracy.get('explanation', 'N/A')
                            if len(explanation) > 100:
                                explanation = explanation[:100] + '...'
                            print(f'  Explanation: {explanation}')
                    
                    # Show validation results
                    validation_results = result_data.get('validation_results', [])
                    if validation_results:
                        print('\nClaim Verdicts:')
                        for i, val_result in enumerate(validation_results[:3], 1):
                            claim = val_result.get('claim', '')
                            if len(claim) > 60:
                                claim = claim[:60] + '...'
                            vr = val_result.get('validation_result', {})
                            verdict = vr.get('verdict', 'N/A')
                            confidence = vr.get('confidence', 'N/A')
                            print(f'  {i}. [{verdict}] (conf: {confidence}) {claim}')
            
            print('\n' + '─'*80)


if __name__ == "__main__":
    asyncio.run(review_all_articles())
