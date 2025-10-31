#!/usr/bin/env python3
"""Show full validation details for all fact-checked articles."""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(str(settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')))
SessionLocal = sessionmaker(bind=engine)

def main():
    db = SessionLocal()
    
    try:
        # Get all fact-checked articles with their validation details
        result = db.execute(text("""
            SELECT 
                a.id,
                a.title,
                a.url,
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
                afc.source_consensus,
                afc.job_id,
                afc.validation_mode
            FROM articles a
            LEFT JOIN article_fact_checks afc ON a.id = afc.article_id
            WHERE a.fact_check_verdict IS NOT NULL
            ORDER BY a.created_at DESC
        """))
        
        articles = result.fetchall()
        
        print("\n" + "="*120)
        print(f"FULL VALIDATION REVIEW - ALL {len(articles)} FACT-CHECKED ARTICLES")
        print("="*120 + "\n")
        
        for i, article in enumerate(articles, 1):
            print(f"\n{'='*120}")
            print(f"ARTICLE {i}/{len(articles)}")
            print("="*120)
            print(f"\nTitle: {article.title}")
            print(f"URL: {article.url}")
            print(f"\nVerdict: {article.fact_check_verdict}")
            print(f"Credibility Score: {article.fact_check_score}/100")
            print(f"Validation Mode: {article.validation_mode}")
            print(f"Job ID: {article.job_id}")
            
            print(f"\n{'-'*120}")
            print("CLAIMS BREAKDOWN")
            print("-"*120)
            print(f"Total claims analyzed: {article.claims_analyzed}")
            print(f"Claims validated: {article.claims_validated}")
            print(f"  • True: {article.claims_true}")
            print(f"  • False: {article.claims_false}")
            print(f"  • Misleading: {article.claims_misleading}")
            print(f"  • Unverified: {article.claims_unverified}")
            print(f"\nSources checked: {article.num_sources}")
            if article.source_consensus:
                print(f"Source consensus: {article.source_consensus}")
            
            print(f"\n{'-'*120}")
            print("SUMMARY")
            print("-"*120)
            print(article.summary if article.summary else "No summary available")
            
            if article.validation_results:
                print(f"\n{'-'*120}")
                print("DETAILED VALIDATION RESULTS")
                print("-"*120)
                
                try:
                    # validation_results might already be a list or need JSON parsing
                    if isinstance(article.validation_results, list):
                        validation_data = article.validation_results
                    else:
                        validation_data = json.loads(article.validation_results)
                    
                    for j, claim_validation in enumerate(validation_data, 1):
                        claim = claim_validation.get('claim', {})
                        result = claim_validation.get('validation_result', {})
                        
                        print(f"\nCLAIM {j}:")
                        print(f"  Text: {claim.get('claim', 'N/A')}")
                        print(f"  Category: {claim.get('category', 'N/A')}")
                        print(f"  Risk Level: {claim.get('risk_level', 'N/A')}")
                        
                        print(f"\n  VALIDATION:")
                        print(f"    Verdict: {result.get('verdict', 'N/A')}")
                        print(f"    Confidence: {result.get('confidence', 0)*100:.0f}%")
                        print(f"    Evidence Count: {result.get('evidence_count', 0)}")
                        
                        breakdown = result.get('evidence_breakdown', {})
                        if breakdown:
                            print(f"    Evidence Sources:")
                            print(f"      - News: {breakdown.get('news', 0)}")
                            print(f"      - General: {breakdown.get('general', 0)}")
                            print(f"      - Research: {breakdown.get('research', 0)}")
                            print(f"      - Historical: {breakdown.get('historical', 0)}")
                        
                        print(f"\n    Summary: {result.get('summary', 'No summary')}")
                        
                        # Show supporting evidence if available
                        if result.get('supporting_evidence'):
                            print(f"\n    Supporting Evidence:")
                            for k, evidence in enumerate(result['supporting_evidence'][:3], 1):
                                print(f"      {k}. {evidence.get('title', 'N/A')}")
                                print(f"         Source: {evidence.get('source', 'N/A')}")
                                print(f"         Relevance: {evidence.get('relevance_score', 0)*100:.0f}%")
                        
                        print()
                
                except json.JSONDecodeError:
                    print("Could not parse validation results JSON")
            
            print(f"\nAPI Analysis: https://fact-check-production.up.railway.app/fact-check/{article.job_id}/result")
            print("\n" + "="*120 + "\n")
    
    finally:
        db.close()

if __name__ == '__main__':
    main()
