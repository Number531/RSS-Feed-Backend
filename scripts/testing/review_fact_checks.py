#!/usr/bin/env python3
"""Review all fact-checked articles in the database."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, selectinload

from app.core.config import settings
from app.models.article import Article
from app.models.fact_check import ArticleFactCheck

engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=False,
    pool_pre_ping=True,
)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def main():
    async with AsyncSessionLocal() as db:
        try:
            # Query all articles with their fact checks
            result = await db.execute(
                select(Article)
                .options(selectinload(Article.fact_check))
                .order_by(Article.created_at.desc())
            )
            articles = result.scalars().all()
        
        print('\n' + '='*120)
        print('ALL FACT-CHECKED ARTICLES - DETAILED REVIEW')
        print('='*120 + '\n')
        
        for i, article in enumerate(articles, 1):
            print(f'{i}. {article.title}')
            print(f'   URL: {article.url}')
            print(f'   Published: {article.published_at}')
            print(f'   Category: {article.category}')
            
            if article.fact_check:
                fc = article.fact_check
                print(f'\n   ✓ FACT-CHECK RESULTS:')
                print(f'     - Credibility Score: {fc.credibility_score}/100')
                print(f'     - Verdict: {fc.verdict}')
                print(f'     - Status: {fc.status}')
                print(f'     - Job ID: {fc.external_job_id}')
                
                if fc.summary:
                    print(f'\n     Summary:')
                    print(f'     {fc.summary}')
                
                if fc.key_findings:
                    print(f'\n     Key Findings:')
                    for finding in fc.key_findings[:3]:  # Show first 3
                        print(f'     • {finding}')
                
                print(f'\n     Analysis URL: https://fact-check-production.up.railway.app/fact-check/{fc.external_job_id}/result')
            else:
                print(f'\n   ✗ NO FACT-CHECK (Status: {article.status})')
            
            print('\n' + '-'*120 + '\n')
        
        # Summary stats
        total = len(articles)
        fact_checked = sum(1 for a in articles if a.fact_check)
        pending = total - fact_checked
        
        if fact_checked > 0:
            avg_score = sum(a.fact_check.credibility_score for a in articles if a.fact_check) / fact_checked
            verdicts = {}
            for a in articles:
                if a.fact_check:
                    verdict = a.fact_check.verdict
                    verdicts[verdict] = verdicts.get(verdict, 0) + 1
            
            print('='*120)
            print('SUMMARY STATISTICS')
            print('='*120)
            print(f'Total Articles: {total}')
            print(f'Fact-Checked: {fact_checked}')
            print(f'Pending: {pending}')
            print(f'Average Credibility Score: {avg_score:.1f}/100')
            print(f'\nVerdict Distribution:')
            for verdict, count in sorted(verdicts.items(), key=lambda x: -x[1]):
                print(f'  • {verdict}: {count}')
            print('='*120)
        
        except Exception as e:
            print(f"Error: {e}")
            raise


if __name__ == '__main__':
    asyncio.run(main())
