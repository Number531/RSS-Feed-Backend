#!/usr/bin/env python3
"""Examine detailed fact-check results for an article."""

import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

async def main():
    engine = create_async_engine(str(settings.DATABASE_URL), echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # Find the Marriage Act article
        result = await session.execute(text("""
            SELECT 
                a.id,
                a.title,
                a.url,
                a.fact_check_score,
                a.fact_check_verdict,
                fc.summary,
                fc.validation_results,
                fc.credibility_score,
                fc.verdict,
                fc.fact_checked_at
            FROM articles a
            LEFT JOIN article_fact_checks fc ON a.id = fc.article_id
            WHERE a.title LIKE '%Marriage%'
            ORDER BY a.created_at DESC
            LIMIT 1
        """))
        
        row = result.fetchone()
        
        if not row:
            print("Article not found!")
            return
        
        article_id, title, url, a_score, a_verdict, summary, validation_results, fc_score, fc_verdict, checked_at = row
        
        print(f"\n{'='*80}")
        print(f"FACT-CHECK ANALYSIS: Respect for Marriage Act")
        print(f"{'='*80}\n")
        
        print(f"Article Title: {title}")
        print(f"URL: {url}")
        print(f"Article ID: {article_id}\n")
        
        print(f"{'─'*80}")
        print(f"SCORES & VERDICTS")
        print(f"{'─'*80}")
        print(f"Article Score: {a_score}")
        print(f"Article Verdict: {a_verdict}")
        print(f"Fact-Check Score: {fc_score}")
        print(f"Fact-Check Verdict: {fc_verdict}")
        print(f"Checked At: {checked_at}\n")
        
        print(f"{'─'*80}")
        print(f"SUMMARY")
        print(f"{'─'*80}")
        print(f"{summary}\n")
        
        print(f"{'─'*80}")
        print(f"VALIDATION RESULTS (Raw JSON)")
        print(f"{'─'*80}")
        
        if validation_results:
            # Pretty print JSON
            formatted_json = json.dumps(validation_results, indent=2)
            print(formatted_json)
            
            # Extract claims if available
            if isinstance(validation_results, dict):
                print(f"\n{'─'*80}")
                print(f"EXTRACTED CLAIMS ANALYSIS")
                print(f"{'─'*80}\n")
                
                # Look for claims in various possible keys
                claims = None
                if 'claims' in validation_results:
                    claims = validation_results['claims']
                elif 'extracted_claims' in validation_results:
                    claims = validation_results['extracted_claims']
                elif 'claim_validations' in validation_results:
                    claims = validation_results['claim_validations']
                
                if claims:
                    if isinstance(claims, list):
                        for i, claim in enumerate(claims, 1):
                            print(f"\nClaim #{i}:")
                            print(f"{'─'*40}")
                            if isinstance(claim, dict):
                                for key, value in claim.items():
                                    print(f"{key}: {value}")
                            else:
                                print(claim)
                    else:
                        print(json.dumps(claims, indent=2))
                else:
                    print("No claims found in standard format.")
                    print("\nAvailable keys in validation_results:")
                    for key in validation_results.keys():
                        print(f"  - {key}")
        else:
            print("No validation results found.")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
