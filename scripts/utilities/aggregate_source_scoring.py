#!/usr/bin/env python3
"""
Aggregate Source Scoring Analysis
==================================
Demonstrates aggregate scoring capabilities for news sources.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(str(settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')))
SessionLocal = sessionmaker(bind=engine)


def analyze_aggregates():
    db = SessionLocal()
    
    try:
        print("\n" + "="*100)
        print("AGGREGATE NEWS SOURCE SCORING ANALYSIS")
        print("="*100 + "\n")
        
        # 1. Overall Source Performance
        print("📊 OVERALL SOURCE PERFORMANCE")
        print("-"*100)
        result = db.execute(text("""
            SELECT 
                rs.source_name,
                rs.category,
                COUNT(a.id) as total_articles,
                COUNT(afc.id) as fact_checked_articles,
                ROUND(AVG(afc.credibility_score), 1) as avg_credibility_score,
                ROUND(AVG(afc.confidence), 2) as avg_confidence,
                ROUND(AVG(afc.processing_time_seconds), 0) as avg_processing_time,
                COUNT(CASE WHEN afc.verdict = 'TRUE' THEN 1 END) as true_count,
                COUNT(CASE WHEN afc.verdict LIKE 'MOSTLY TRUE%' THEN 1 END) as mostly_true_count,
                COUNT(CASE WHEN afc.verdict = 'MIXED' THEN 1 END) as mixed_count,
                COUNT(CASE WHEN afc.verdict = 'MISLEADING' THEN 1 END) as misleading_count,
                COUNT(CASE WHEN afc.verdict LIKE 'MOSTLY FALSE%' THEN 1 END) as mostly_false_count,
                COUNT(CASE WHEN afc.verdict = 'FALSE' THEN 1 END) as false_count,
                COUNT(CASE WHEN afc.verdict LIKE 'UNVERIFIED%' THEN 1 END) as unverified_count
            FROM rss_sources rs
            LEFT JOIN articles a ON a.rss_source_id = rs.id
            LEFT JOIN article_fact_checks afc ON afc.article_id = a.id
            GROUP BY rs.id, rs.source_name, rs.category
            ORDER BY avg_credibility_score DESC NULLS LAST
        """))
        
        for row in result:
            print(f"\nSource: {row.source_name} ({row.category})")
            print(f"  Articles: {row.total_articles} total, {row.fact_checked_articles} fact-checked")
            if row.avg_credibility_score:
                print(f"  Avg Credibility Score: {row.avg_credibility_score}/100")
                print(f"  Avg Confidence: {row.avg_confidence}")
                print(f"  Avg Processing Time: {row.avg_processing_time}s")
                print(f"  Verdict Breakdown:")
                print(f"    ✓ TRUE: {row.true_count}")
                print(f"    ≈ MOSTLY TRUE: {row.mostly_true_count}")
                print(f"    ◐ MIXED: {row.mixed_count}")
                print(f"    ⚠ MISLEADING: {row.misleading_count}")
                print(f"    ≈ MOSTLY FALSE: {row.mostly_false_count}")
                print(f"    ✗ FALSE: {row.false_count}")
                print(f"    ? UNVERIFIED: {row.unverified_count}")
        
        # 2. Verdict Distribution Analysis
        print("\n\n" + "="*100)
        print("📋 VERDICT DISTRIBUTION ANALYSIS")
        print("-"*100)
        result = db.execute(text("""
            SELECT 
                verdict,
                COUNT(*) as count,
                ROUND(AVG(credibility_score), 1) as avg_score,
                ROUND(MIN(credibility_score), 0) as min_score,
                ROUND(MAX(credibility_score), 0) as max_score,
                ROUND(AVG(confidence), 2) as avg_confidence
            FROM article_fact_checks
            GROUP BY verdict
            ORDER BY count DESC
        """))
        
        for row in result:
            print(f"\n{row.verdict}:")
            print(f"  Count: {row.count}")
            print(f"  Avg Score: {row.avg_score}/100 (range: {row.min_score}-{row.max_score})")
            print(f"  Avg Confidence: {row.avg_confidence}")
        
        # 3. Claims Analysis
        print("\n\n" + "="*100)
        print("🔍 CLAIMS ANALYSIS")
        print("-"*100)
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total_articles,
                SUM(claims_analyzed) as total_claims,
                SUM(claims_validated) as total_validated,
                SUM(claims_true) as total_true,
                SUM(claims_false) as total_false,
                SUM(claims_misleading) as total_misleading,
                SUM(claims_unverified) as total_unverified,
                ROUND(AVG(claims_analyzed), 1) as avg_claims_per_article,
                ROUND(100.0 * SUM(claims_true) / NULLIF(SUM(claims_validated), 0), 1) as pct_true,
                ROUND(100.0 * SUM(claims_false) / NULLIF(SUM(claims_validated), 0), 1) as pct_false,
                ROUND(100.0 * SUM(claims_misleading) / NULLIF(SUM(claims_validated), 0), 1) as pct_misleading,
                ROUND(100.0 * SUM(claims_unverified) / NULLIF(SUM(claims_validated), 0), 1) as pct_unverified
            FROM article_fact_checks
        """))
        
        row = result.fetchone()
        print(f"Total Articles Analyzed: {row.total_articles}")
        print(f"Total Claims: {row.total_claims} ({row.avg_claims_per_article} avg per article)")
        print(f"Total Validated: {row.total_validated}")
        print(f"\nClaim Outcomes:")
        print(f"  ✓ True: {row.total_true} ({row.pct_true}%)")
        print(f"  ✗ False: {row.total_false} ({row.pct_false}%)")
        print(f"  ⚠ Misleading: {row.total_misleading} ({row.pct_misleading}%)")
        print(f"  ? Unverified: {row.total_unverified} ({row.pct_unverified}%)")
        
        # 4. Temporal Analysis
        print("\n\n" + "="*100)
        print("📅 TEMPORAL ANALYSIS (Last 7 Days)")
        print("-"*100)
        result = db.execute(text("""
            SELECT 
                DATE(fact_checked_at) as check_date,
                COUNT(*) as articles_checked,
                ROUND(AVG(credibility_score), 1) as avg_score,
                COUNT(CASE WHEN verdict = 'TRUE' THEN 1 END) as true_count,
                COUNT(CASE WHEN verdict = 'FALSE' THEN 1 END) as false_count,
                COUNT(CASE WHEN verdict LIKE '%UNVERIFIED%' THEN 1 END) as unverified_count
            FROM article_fact_checks
            WHERE fact_checked_at >= NOW() - INTERVAL '7 days'
            GROUP BY DATE(fact_checked_at)
            ORDER BY check_date DESC
        """))
        
        for row in result:
            print(f"\n{row.check_date}:")
            print(f"  Articles: {row.articles_checked}")
            print(f"  Avg Score: {row.avg_score}/100")
            print(f"  TRUE: {row.true_count} | FALSE: {row.false_count} | UNVERIFIED: {row.unverified_count}")
        
        # 5. Source Quality Metrics
        print("\n\n" + "="*100)
        print("⭐ SOURCE QUALITY METRICS")
        print("-"*100)
        result = db.execute(text("""
            SELECT 
                AVG(num_sources) as avg_sources_used,
                AVG(processing_time_seconds) as avg_processing_time,
                COUNT(DISTINCT validation_mode) as validation_modes_used,
                string_agg(DISTINCT validation_mode, ', ') as modes
            FROM article_fact_checks
        """))
        
        row = result.fetchone()
        print(f"Avg Sources Used per Validation: {row.avg_sources_used:.1f}")
        print(f"Avg Processing Time: {row.avg_processing_time:.1f}s")
        print(f"Validation Modes Used: {row.modes}")
        
        # 6. Cost Analysis
        print("\n\n" + "="*100)
        print("💰 COST ANALYSIS")
        print("-"*100)
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total_validations,
                SUM((api_costs->>'extraction')::numeric) as total_extraction_cost,
                SUM((api_costs->>'search')::numeric) as total_search_cost,
                SUM((api_costs->>'validation')::numeric) as total_validation_cost,
                SUM((api_costs->>'extraction')::numeric + 
                    (api_costs->>'search')::numeric + 
                    (api_costs->>'validation')::numeric) as total_cost,
                AVG((api_costs->>'extraction')::numeric + 
                    (api_costs->>'search')::numeric + 
                    (api_costs->>'validation')::numeric) as avg_cost_per_article
            FROM article_fact_checks
            WHERE api_costs IS NOT NULL
        """))
        
        row = result.fetchone()
        if row.total_cost:
            print(f"Total Validations: {row.total_validations}")
            print(f"Total Cost: ${row.total_cost:.4f}")
            print(f"Avg Cost per Article: ${row.avg_cost_per_article:.4f}")
            print(f"\nCost Breakdown:")
            print(f"  Extraction: ${row.total_extraction_cost:.4f}")
            print(f"  Search: ${row.total_search_cost:.4f}")
            print(f"  Validation: ${row.total_validation_cost:.4f}")
        else:
            print("No cost data available")
        
        # 7. Accuracy by Category
        print("\n\n" + "="*100)
        print("📂 ACCURACY BY CATEGORY")
        print("-"*100)
        result = db.execute(text("""
            SELECT 
                a.category,
                COUNT(afc.id) as fact_checked_count,
                ROUND(AVG(afc.credibility_score), 1) as avg_score,
                ROUND(100.0 * COUNT(CASE WHEN afc.verdict = 'TRUE' THEN 1 END) / COUNT(afc.id), 1) as pct_true,
                ROUND(100.0 * COUNT(CASE WHEN afc.verdict = 'FALSE' THEN 1 END) / COUNT(afc.id), 1) as pct_false
            FROM articles a
            JOIN article_fact_checks afc ON afc.article_id = a.id
            GROUP BY a.category
            ORDER BY avg_score DESC
        """))
        
        for row in result:
            print(f"\n{row.category or 'Uncategorized'}:")
            print(f"  Articles: {row.fact_checked_count}")
            print(f"  Avg Score: {row.avg_score}/100")
            print(f"  TRUE: {row.pct_true}% | FALSE: {row.pct_false}%")
        
        # 8. Reliability Score (Custom Metric)
        print("\n\n" + "="*100)
        print("🎯 COMPOSITE RELIABILITY SCORE")
        print("-"*100)
        print("Formula: (Avg Score * 0.4) + (% True * 0.3) + (% Non-False * 0.2) + (Confidence * 10)")
        print()
        result = db.execute(text("""
            SELECT 
                rs.source_name,
                COUNT(afc.id) as articles,
                ROUND(AVG(afc.credibility_score), 1) as avg_score,
                ROUND(100.0 * COUNT(CASE WHEN afc.verdict = 'TRUE' THEN 1 END) / COUNT(afc.id), 1) as pct_true,
                ROUND(100.0 * COUNT(CASE WHEN afc.verdict NOT IN ('FALSE', 'MOSTLY FALSE') THEN 1 END) / COUNT(afc.id), 1) as pct_non_false,
                ROUND(AVG(afc.confidence), 2) as avg_confidence,
                ROUND(
                    (AVG(afc.credibility_score) * 0.4) + 
                    (100.0 * COUNT(CASE WHEN afc.verdict = 'TRUE' THEN 1 END) / COUNT(afc.id) * 0.3) +
                    (100.0 * COUNT(CASE WHEN afc.verdict NOT IN ('FALSE', 'MOSTLY FALSE') THEN 1 END) / COUNT(afc.id) * 0.2) +
                    (AVG(afc.confidence) * 10 * 0.1)
                , 1) as reliability_score
            FROM rss_sources rs
            JOIN articles a ON a.rss_source_id = rs.id
            JOIN article_fact_checks afc ON afc.article_id = a.id
            GROUP BY rs.id, rs.source_name
            HAVING COUNT(afc.id) >= 3
            ORDER BY reliability_score DESC
        """))
        
        for row in result:
            print(f"{row.source_name}:")
            print(f"  Reliability Score: {row.reliability_score}/100")
            print(f"  Based on: {row.articles} articles, {row.avg_score} avg score, {row.pct_true}% true, {row.avg_confidence} confidence")
        
        print("\n" + "="*100)
        print("✅ Analysis Complete")
        print("="*100 + "\n")
        
    finally:
        db.close()


if __name__ == '__main__':
    analyze_aggregates()
