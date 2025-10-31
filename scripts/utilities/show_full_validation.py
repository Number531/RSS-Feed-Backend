#!/usr/bin/env python3
"""
Display full validation results for a specific article.
"""
import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal


async def main():
    async with AsyncSessionLocal() as db:
        # Get the article with highest UNVERIFIED score
        result = await db.execute(text("""
            SELECT 
                a.title,
                a.fact_check_verdict,
                a.fact_check_score,
                afc.summary,
                afc.validation_results,
                afc.claims_analyzed,
                afc.claims_validated,
                afc.claims_true,
                afc.claims_false,
                afc.claims_misleading,
                afc.claims_unverified,
                afc.num_sources,
                afc.source_consensus
            FROM articles a
            LEFT JOIN article_fact_checks afc ON a.id = afc.article_id
            WHERE a.fact_check_verdict LIKE '%UNVERIFIED%'
            ORDER BY a.fact_check_score DESC
            LIMIT 1
        """))
        
        row = result.fetchone()
        
        if not row:
            print("\nNo UNVERIFIED articles found.\n")
            return
        
        (title, verdict, score, summary, validation_results, claims_analyzed,
         claims_validated, claims_true, claims_false, claims_misleading,
         claims_unverified, num_sources, source_consensus) = row
        
        print("\n" + "="*100)
        print("FULL VALIDATION RESULTS - HIGHEST SCORING UNVERIFIED ARTICLE")
        print("="*100 + "\n")
        
        print(f"Title: {title}")
        print(f"Verdict: {verdict}")
        print(f"Credibility Score: {score}/100")
        print()
        
        print("="*100)
        print("CLAIMS ANALYSIS")
        print("="*100)
        print(f"Total claims analyzed: {claims_analyzed}")
        print(f"Claims validated: {claims_validated}")
        print(f"  • True: {claims_true}")
        print(f"  • False: {claims_false}")
        print(f"  • Misleading: {claims_misleading}")
        print(f"  • Unverified: {claims_unverified}")
        print(f"\nSources checked: {num_sources}")
        print(f"Source consensus: {source_consensus}")
        print()
        
        print("="*100)
        print("SUMMARY")
        print("="*100)
        print(summary)
        print()
        
        print("="*100)
        print("FULL VALIDATION RESULTS (JSON)")
        print("="*100)
        
        if validation_results:
            # Pretty print the JSON
            formatted_json = json.dumps(validation_results, indent=2)
            print(formatted_json)
        else:
            print("(No validation results available)")
        
        print()


if __name__ == "__main__":
    asyncio.run(main())
