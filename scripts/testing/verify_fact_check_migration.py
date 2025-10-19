#!/usr/bin/env python3
"""
Simple script to verify fact-check migration 006 was applied correctly.

Run with: python scripts/testing/verify_fact_check_migration.py
"""
import sys
from sqlalchemy import create_engine, inspect, text
from app.core.config import settings


def main():
    """Verify migration 006 applied correctly."""
    print("🔍 Verifying Fact-Check Migration 006...\n")
    
    # Connect to database
    engine = create_engine(str(settings.DATABASE_URL).replace('+asyncpg', ''))
    inspector = inspect(engine)
    
    errors = []
    warnings = []
    
    # Test 1: Articles table has new columns
    print("✓ Testing articles table...")
    articles_columns = {col['name']: col for col in inspector.get_columns('articles')}
    
    required_article_columns = ['fact_check_score', 'fact_check_verdict', 'fact_checked_at']
    for col in required_article_columns:
        if col not in articles_columns:
            errors.append(f"  ❌ Column 'articles.{col}' not found")
        else:
            print(f"  ✅ Column 'articles.{col}' exists")
    
    # Test 2: Articles indexes
    print("\n✓ Testing articles indexes...")
    articles_indexes = {idx['name']: idx for idx in inspector.get_indexes('articles')}
    
    required_article_indexes = [
        'ix_articles_fact_check_score',
        'ix_articles_fact_check_verdict',
        'ix_articles_fact_checked_at'
    ]
    for idx in required_article_indexes:
        if idx not in articles_indexes:
            errors.append(f"  ❌ Index '{idx}' not found")
        else:
            print(f"  ✅ Index '{idx}' exists")
    
    # Test 3: article_fact_checks table exists
    print("\n✓ Testing article_fact_checks table...")
    tables = inspector.get_table_names()
    
    if 'article_fact_checks' not in tables:
        errors.append("  ❌ Table 'article_fact_checks' not found")
    else:
        print("  ✅ Table 'article_fact_checks' exists")
        
        fact_check_columns = {col['name']: col for col in inspector.get_columns('article_fact_checks')}
        required_columns = [
            'id', 'article_id', 'verdict', 'credibility_score', 'confidence',
            'summary', 'claims_analyzed', 'claims_validated', 'claims_true',
            'claims_false', 'claims_misleading', 'claims_unverified',
            'validation_results', 'num_sources', 'source_consensus',
            'job_id', 'validation_mode', 'processing_time_seconds',
            'api_costs', 'fact_checked_at', 'created_at', 'updated_at'
        ]
        
        for col in required_columns:
            if col not in fact_check_columns:
                errors.append(f"  ❌ Column 'article_fact_checks.{col}' not found")
        
        if not errors:
            print(f"  ✅ All {len(required_columns)} columns present")
    
    # Test 4: article_fact_checks indexes
    print("\n✓ Testing article_fact_checks indexes...")
    if 'article_fact_checks' in tables:
        fact_check_indexes = {idx['name']: idx for idx in inspector.get_indexes('article_fact_checks')}
        
        required_indexes = [
            'ix_article_fact_checks_article_id',
            'ix_article_fact_checks_verdict',
            'ix_article_fact_checks_credibility_score',
            'ix_article_fact_checks_job_id',
            'ix_article_fact_checks_fact_checked_at',
            'ix_article_fact_checks_validation_results_gin'
        ]
        
        for idx in required_indexes:
            if idx not in fact_check_indexes:
                errors.append(f"  ❌ Index '{idx}' not found")
            else:
                print(f"  ✅ Index '{idx}' exists")
    
    # Test 5: Foreign keys
    print("\n✓ Testing foreign key constraints...")
    if 'article_fact_checks' in tables:
        fks = inspector.get_foreign_keys('article_fact_checks')
        article_fk = next((fk for fk in fks if 'article_id' in fk['constrained_columns']), None)
        
        if article_fk is None:
            errors.append("  ❌ Foreign key on 'article_id' not found")
        elif article_fk['referred_table'] != 'articles':
            errors.append(f"  ❌ Foreign key refers to '{article_fk['referred_table']}' instead of 'articles'")
        elif article_fk['options'].get('ondelete') != 'CASCADE':
            warnings.append(f"  ⚠️  Foreign key ondelete is '{article_fk['options'].get('ondelete')}' (expected 'CASCADE')")
        else:
            print("  ✅ Foreign key 'article_fact_checks.article_id → articles.id' (CASCADE)")
    
    # Test 6: source_credibility_scores table
    print("\n✓ Testing source_credibility_scores table...")
    if 'source_credibility_scores' not in tables:
        errors.append("  ❌ Table 'source_credibility_scores' not found")
    else:
        print("  ✅ Table 'source_credibility_scores' exists")
        
        credibility_columns = {col['name']: col for col in inspector.get_columns('source_credibility_scores')}
        required_credibility_columns = [
            'id', 'rss_source_id', 'average_score', 'total_articles_checked',
            'true_count', 'false_count', 'misleading_count', 'unverified_count',
            'period_start', 'period_end', 'period_type', 'trend_data',
            'created_at', 'updated_at'
        ]
        
        for col in required_credibility_columns:
            if col not in credibility_columns:
                errors.append(f"  ❌ Column 'source_credibility_scores.{col}' not found")
        
        if not errors:
            print(f"  ✅ All {len(required_credibility_columns)} columns present")
    
    # Test 7: Unique constraints
    print("\n✓ Testing unique constraints...")
    if 'article_fact_checks' in tables:
        unique_constraints = inspector.get_unique_constraints('article_fact_checks')
        unique_columns = []
        for constraint in unique_constraints:
            unique_columns.extend(constraint['column_names'])
        
        if 'article_id' in unique_columns:
            print("  ✅ Unique constraint on 'article_fact_checks.article_id'")
        else:
            errors.append("  ❌ Unique constraint on 'article_id' not found")
        
        if 'job_id' in unique_columns:
            print("  ✅ Unique constraint on 'article_fact_checks.job_id'")
        else:
            errors.append("  ❌ Unique constraint on 'job_id' not found")
    
    if 'source_credibility_scores' in tables:
        source_constraints = inspector.get_unique_constraints('source_credibility_scores')
        constraint_names = [c['name'] for c in source_constraints]
        
        if 'unique_source_period_score' in constraint_names:
            print("  ✅ Unique constraint 'unique_source_period_score' on source_credibility_scores")
        else:
            warnings.append("  ⚠️  Named unique constraint 'unique_source_period_score' not found")
    
    # Test 8: JSONB GIN index
    print("\n✓ Testing JSONB GIN index...")
    if 'article_fact_checks' in tables:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'article_fact_checks' 
                  AND indexdef LIKE '%gin%'
            """))
            gin_indexes = result.fetchall()
            
            if gin_indexes:
                print(f"  ✅ GIN index found: {gin_indexes[0][0]}")
            else:
                warnings.append("  ⚠️  GIN index not found (validation_results may be slower to query)")
    
    # Print summary
    print("\n" + "="*60)
    print("📊 VERIFICATION SUMMARY")
    print("="*60)
    
    if not errors and not warnings:
        print("✅ All tests passed! Migration 006 applied successfully.")
        print("\nYour fact-check database schema is ready to use.")
        return 0
    
    if warnings:
        print(f"\n⚠️  {len(warnings)} Warning(s):")
        for warning in warnings:
            print(warning)
    
    if errors:
        print(f"\n❌ {len(errors)} Error(s):")
        for error in errors:
            print(error)
        print("\n⚠️  Migration 006 may not have applied correctly.")
        print("Run: alembic downgrade -1 && alembic upgrade head")
        return 1
    
    print("\n✅ Migration applied with minor warnings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
