#!/usr/bin/env python3
"""
Check reasons for UNVERIFIED verdicts in fact-checked articles.
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
        print("\n" + "="*100)
        print("UNVERIFIED ARTICLES - DETAILED ANALYSIS")
        print("="*100 + "\n")
        
        # Get UNVERIFIED articles with details
        result = await db.execute(text("""
            SELECT 
                a.title,
                a.fact_check_verdict,
                a.fact_check_score,
                afc.summary,
                afc.claims_analyzed,
                afc.claims_validated,
                afc.claims_unverified,
                afc.num_sources
            FROM articles a
            LEFT JOIN article_fact_checks afc ON a.id = afc.article_id
            WHERE a.fact_check_verdict LIKE '%UNVERIFIED%'
            ORDER BY a.created_at DESC
        """))
        
        rows = result.fetchall()
        
        if not rows:
            print("No UNVERIFIED articles found in database.\n")
            
            # Show what verdicts we do have
            result = await db.execute(text("""
                SELECT fact_check_verdict, COUNT(*) as count
                FROM articles 
                WHERE fact_check_verdict IS NOT NULL 
                GROUP BY fact_check_verdict
                ORDER BY count DESC
            """))
            verdicts = result.fetchall()
            
            print("Available verdicts in database:")
            for verdict, count in verdicts:
                print(f"  • {verdict}: {count}")
            print()
            return
        
        print(f"Found {len(rows)} UNVERIFIED articles:\n")
        
        for i, (title, verdict, score, summary, claims_analyzed, claims_validated, 
                claims_unverified, num_sources) in enumerate(rows, 1):
            
            print(f"{i}. {title}")
            print(f"   {'─'*94}")
            print(f"   Verdict: {verdict}")
            print(f"   Credibility Score: {score}/100")
            
            if claims_analyzed:
                print(f"\n   Claims Analysis:")
                print(f"     • Total claims analyzed: {claims_analyzed}")
                print(f"     • Claims validated: {claims_validated}")
                print(f"     • Claims unverified: {claims_unverified}")
            
            if num_sources:
                print(f"   • Number of sources checked: {num_sources}")
            
            print(f"\n   Reason for UNVERIFIED status:")
            print(f"   {'─'*94}")
            
            if summary:
                # Format summary nicely
                lines = summary.split('\n')
                for line in lines:
                    if line.strip():
                        print(f"   {line}")
            else:
                print("   (No detailed summary available)")
            
            print(f"\n   {'='*94}\n")
        
        # Summary statistics
        avg_score = sum(row[2] for row in rows) / len(rows) if rows else 0
        print(f"Summary Statistics:")
        print(f"  • Total UNVERIFIED articles: {len(rows)}")
        print(f"  • Average credibility score: {avg_score:.1f}/100")
        print()


if __name__ == "__main__":
    asyncio.run(main())
