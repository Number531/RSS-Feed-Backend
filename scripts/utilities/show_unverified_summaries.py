#!/usr/bin/env python3
"""
Display full summaries of UNVERIFIED articles.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal


async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("""
            SELECT 
                a.title,
                a.fact_check_verdict,
                a.fact_check_score,
                afc.summary
            FROM articles a
            LEFT JOIN article_fact_checks afc ON a.id = afc.article_id
            WHERE a.fact_check_verdict LIKE '%UNVERIFIED%'
            ORDER BY a.fact_check_score DESC
        """))
        
        articles = result.fetchall()
        
        if not articles:
            print("\nNo UNVERIFIED articles found.\n")
            return
        
        print("\n" + "="*100)
        print("FULL SUMMARIES OF UNVERIFIED ARTICLES")
        print("="*100 + "\n")
        
        for i, (title, verdict, score, summary) in enumerate(articles, 1):
            print(f"{i}. {title}")
            print(f"   Verdict: {verdict} | Score: {score}/100")
            print(f"\n   {'-'*96}")
            print(f"   FULL SUMMARY:")
            print(f"   {'-'*96}\n")
            
            if summary:
                # Print full summary with proper formatting
                lines = summary.split('\n')
                for line in lines:
                    print(f"   {line}")
                print()
            else:
                print("   (No summary available)\n")
            
            print(f"   {'='*96}\n")
        
        print(f"Total UNVERIFIED articles: {len(articles)}\n")


if __name__ == "__main__":
    asyncio.run(main())
