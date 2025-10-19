#!/usr/bin/env python3
"""
End-to-end test for fact-check database operations.

Tests:
1. Creating articles with fact-checks
2. Querying articles by fact-check score
3. JSONB storage and retrieval of citations
4. Cascade deletes
5. Unique constraints enforcement
6. Source credibility score aggregation
"""
import sys
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.models import Article, ArticleFactCheck, RSSSource, SourceCredibilityScore


def test_create_article_with_fact_check(session):
    """Test creating an article with a complete fact-check."""
    print("🧪 Test 1: Creating article with fact-check...")
    
    # Create RSS source
    source = RSSSource(
        id=uuid4(),
        name="Test News Source",
        url="https://test-news.com/feed.xml",
        source_name="TestNews",
        category="general",
        is_active=True
    )
    session.add(source)
    session.flush()
    
    # Create article
    article = Article(
        id=uuid4(),
        rss_source_id=source.id,
        title="Breaking: Major Economic Policy Announced",
        url="https://test-news.com/economics/policy",
        url_hash="e2e_test_hash_1",
        description="Government announces new economic policy",
        category="general"
    )
    session.add(article)
    session.flush()
    
    # Create comprehensive fact-check with citations
    validation_data = {
        "validation_results": [{
            "claim": "The government announced a 3.2% GDP growth target",
            "risk_level": "HIGH",
            "category": "Economic Claim",
            "validation_output": {
                "verdict": "TRUE",
                "confidence": 0.95,
                "summary": "The claim is accurate based on official government documents.",
                "key_evidence": {
                    "supporting": [
                        "Official government press release confirms 3.2% target",
                        "Treasury Department budget projections align with this figure"
                    ],
                    "contradicting": [],
                    "context": [
                        "This represents a 0.5% increase from previous year's target"
                    ]
                },
                "source_analysis": {
                    "most_credible_sources": [1, 3, 5],
                    "source_consensus": "GENERAL_AGREEMENT",
                    "evidence_quality": "HIGH"
                },
                "metadata": {
                    "misinformation_indicators": [],
                    "spread_risk": "LOW",
                    "confidence_factors": {
                        "source_agreement": 0.92,
                        "evidence_quality": 0.98,
                        "temporal_consistency": 0.95
                    }
                },
                "references": [
                    {
                        "citation_id": 1,
                        "title": "Economic Policy Statement 2025",
                        "url": "https://treasury.gov/policy-2025",
                        "source": "U.S. Department of Treasury",
                        "author": "Secretary of Treasury",
                        "date": "2025-10-15",
                        "type": "research",
                        "relevance": "Primary source document",
                        "credibility": "HIGH"
                    },
                    {
                        "citation_id": 3,
                        "title": "GDP Growth Analysis Q4 2024",
                        "url": "https://bea.gov/q4-2024",
                        "source": "Bureau of Economic Analysis",
                        "author": None,
                        "date": "2025-01-10",
                        "type": "research",
                        "relevance": "Historical context",
                        "credibility": "HIGH"
                    }
                ],
                "model": "gemini-2.5-flash",
                "validation_mode": "summary",
                "cost": 0.0107,
                "token_usage": {
                    "prompt_tokens": 1500,
                    "candidates_tokens": 800,
                    "total_tokens": 2300
                }
            },
            "evidence_found": True,
            "num_sources": 25,
            "search_breakdown": {
                "news": 8,
                "research": 12,
                "general": 3,
                "historical": 2
            },
            "search_timestamp": "2025-10-17T16:18:45Z",
            "validation_timestamp": "2025-10-17T16:19:30Z"
        }]
    }
    
    fact_check = ArticleFactCheck(
        id=uuid4(),
        article_id=article.id,
        verdict="TRUE",
        credibility_score=95,
        confidence=0.95,
        summary="The claim is accurate based on official government documents.",
        claims_analyzed=1,
        claims_validated=1,
        claims_true=1,
        claims_false=0,
        claims_misleading=0,
        claims_unverified=0,
        validation_results=validation_data,
        num_sources=25,
        source_consensus="GENERAL_AGREEMENT",
        job_id="e2e-test-job-001",
        validation_mode="summary",
        processing_time_seconds=45,
        api_costs={"total": 0.0107, "breakdown": {"search": 0.002, "validation": 0.0087}},
        fact_checked_at=datetime.now(timezone.utc)
    )
    session.add(fact_check)
    session.flush()
    
    # Update article cache
    article.fact_check_score = fact_check.credibility_score
    article.fact_check_verdict = fact_check.verdict
    article.fact_checked_at = fact_check.fact_checked_at
    session.commit()
    
    print(f"  ✅ Created article: {article.title}")
    print(f"  ✅ Created fact-check with verdict: {fact_check.verdict} (score: {fact_check.credibility_score})")
    print(f"  ✅ Stored {len(validation_data['validation_results'][0]['validation_output']['references'])} citations")
    
    return article, fact_check, source


def test_query_by_fact_check_score(session):
    """Test querying articles by fact-check score (fast query using cached columns)."""
    print("\n🧪 Test 2: Querying articles by fact-check score...")
    
    # Create multiple articles with different scores
    source = session.query(RSSSource).filter_by(source_name="TestNews").first()
    
    test_articles = [
        ("Article with high score", "TRUE", 95),
        ("Article with medium score", "MOSTLY_TRUE", 75),
        ("Article with low score", "FALSE", 15),
    ]
    
    for title, verdict, score in test_articles:
        article = Article(
            id=uuid4(),
            rss_source_id=source.id,
            title=title,
            url=f"https://test-news.com/{uuid4().hex[:8]}",
            url_hash=f"hash_{uuid4().hex[:8]}",
            category="general",
            fact_check_score=score,
            fact_check_verdict=verdict,
            fact_checked_at=datetime.now(timezone.utc)
        )
        session.add(article)
    session.commit()
    
    # Query: Get articles with score > 70
    high_score_articles = session.query(Article).filter(
        Article.fact_check_score > 70
    ).order_by(Article.fact_check_score.desc()).all()
    
    print(f"  ✅ Found {len(high_score_articles)} articles with score > 70")
    for art in high_score_articles:
        print(f"     - {art.title}: {art.fact_check_score}")
    
    # Query: Get FALSE articles
    false_articles = session.query(Article).filter(
        Article.fact_check_verdict == "FALSE"
    ).all()
    
    print(f"  ✅ Found {len(false_articles)} articles with FALSE verdict")
    
    return len(high_score_articles), len(false_articles)


def test_jsonb_citation_retrieval(session):
    """Test retrieving citations from JSONB field."""
    print("\n🧪 Test 3: Retrieving citations from JSONB...")
    
    # Get the first fact-check with citations
    fact_check = session.query(ArticleFactCheck).filter(
        ArticleFactCheck.job_id == "e2e-test-job-001"
    ).first()
    
    if not fact_check:
        print("  ❌ Fact-check not found")
        return False
    
    validation_results = fact_check.validation_results
    first_result = validation_results["validation_results"][0]
    references = first_result["validation_output"]["references"]
    
    print(f"  ✅ Retrieved {len(references)} citations from JSONB")
    for ref in references:
        print(f"     - [{ref['citation_id']}] {ref['title']}")
        print(f"       Source: {ref['source']}")
        print(f"       Credibility: {ref['credibility']}")
    
    # Test accessing nested evidence
    key_evidence = first_result["validation_output"]["key_evidence"]
    print(f"  ✅ Supporting evidence: {len(key_evidence['supporting'])} items")
    print(f"  ✅ Contradicting evidence: {len(key_evidence['contradicting'])} items")
    
    return True


def test_relationship_access(session):
    """Test ORM relationships between Article and ArticleFactCheck."""
    print("\n🧪 Test 4: Testing ORM relationships...")
    
    # Get article via relationship from fact-check
    fact_check = session.query(ArticleFactCheck).filter(
        ArticleFactCheck.job_id == "e2e-test-job-001"
    ).first()
    
    article_from_relationship = fact_check.article
    print(f"  ✅ Accessed article via fact_check.article: {article_from_relationship.title}")
    
    # Get fact-check via relationship from article
    article = session.query(Article).filter(
        Article.id == article_from_relationship.id
    ).first()
    
    fact_check_from_relationship = article.fact_check
    print(f"  ✅ Accessed fact-check via article.fact_check: verdict={fact_check_from_relationship.verdict}")
    
    return True


def test_unique_constraints(session):
    """Test unique constraints on article_id and job_id."""
    print("\n🧪 Test 5: Testing unique constraints...")
    
    # Get existing article
    article = session.query(Article).filter(
        Article.url_hash == "e2e_test_hash_1"
    ).first()
    
    # Try to create duplicate fact-check for same article
    try:
        duplicate_fact_check = ArticleFactCheck(
            id=uuid4(),
            article_id=article.id,  # Same article_id
            verdict="FALSE",
            credibility_score=10,
            summary="Duplicate test",
            validation_results={},
            job_id="e2e-test-job-duplicate",
            fact_checked_at=datetime.now(timezone.utc)
        )
        session.add(duplicate_fact_check)
        session.commit()
        print("  ❌ Unique constraint on article_id NOT enforced!")
        return False
    except IntegrityError:
        session.rollback()
        print("  ✅ Unique constraint on article_id enforced")
    
    # Try to create fact-check with duplicate job_id
    new_article = Article(
        id=uuid4(),
        rss_source_id=article.rss_source_id,
        title="New Article",
        url="https://test-news.com/new-article",
        url_hash="new_article_hash",
        category="general"
    )
    session.add(new_article)
    session.flush()
    
    try:
        duplicate_job_fact_check = ArticleFactCheck(
            id=uuid4(),
            article_id=new_article.id,
            verdict="TRUE",
            credibility_score=90,
            summary="Test",
            validation_results={},
            job_id="e2e-test-job-001",  # Duplicate job_id
            fact_checked_at=datetime.now(timezone.utc)
        )
        session.add(duplicate_job_fact_check)
        session.commit()
        print("  ❌ Unique constraint on job_id NOT enforced!")
        return False
    except IntegrityError:
        session.rollback()
        print("  ✅ Unique constraint on job_id enforced")
    
    return True


def test_cascade_delete(session):
    """Test CASCADE delete when article is deleted."""
    print("\n🧪 Test 6: Testing CASCADE delete...")
    
    # Create article with fact-check
    source = session.query(RSSSource).first()
    article = Article(
        id=uuid4(),
        rss_source_id=source.id,
        title="Article to delete",
        url="https://test-news.com/delete-test",
        url_hash="delete_test_hash",
        category="general"
    )
    session.add(article)
    session.flush()
    
    fact_check = ArticleFactCheck(
        id=uuid4(),
        article_id=article.id,
        verdict="TRUE",
        credibility_score=85,
        summary="Test fact-check",
        validation_results={},
        job_id="delete-test-job",
        fact_checked_at=datetime.now(timezone.utc)
    )
    session.add(fact_check)
    session.commit()
    
    fact_check_id = fact_check.id
    article_id = article.id
    
    # Delete article
    session.delete(article)
    session.commit()
    
    # Check that fact-check was also deleted
    deleted_fact_check = session.query(ArticleFactCheck).filter_by(id=fact_check_id).first()
    
    if deleted_fact_check is None:
        print("  ✅ Fact-check cascaded on article delete")
        return True
    else:
        print("  ❌ Fact-check NOT deleted (CASCADE not working)")
        return False


def test_source_credibility_score(session):
    """Test creating and querying source credibility scores."""
    print("\n🧪 Test 7: Testing source credibility scores...")
    
    source = session.query(RSSSource).filter_by(source_name="TestNews").first()
    
    # Create credibility score for monthly period
    now = datetime.now(timezone.utc)
    score = SourceCredibilityScore(
        id=uuid4(),
        rss_source_id=source.id,
        average_score=87.5,
        total_articles_checked=10,
        true_count=8,
        false_count=1,
        misleading_count=1,
        unverified_count=0,
        period_start=now,
        period_end=now,
        period_type="monthly",
        trend_data={
            "trend": [85.0, 86.2, 87.5],
            "dates": ["2025-08", "2025-09", "2025-10"]
        }
    )
    session.add(score)
    session.commit()
    
    print(f"  ✅ Created credibility score: {score.average_score} for {source.source_name}")
    
    # Query scores
    monthly_scores = session.query(SourceCredibilityScore).filter_by(
        period_type="monthly"
    ).all()
    
    print(f"  ✅ Found {len(monthly_scores)} monthly credibility scores")
    
    # Test relationship
    source_with_scores = session.query(RSSSource).filter_by(id=source.id).first()
    print(f"  ✅ Source has {len(source_with_scores.credibility_scores)} credibility scores")
    
    return True


def cleanup(session):
    """Clean up test data."""
    print("\n🧹 Cleaning up test data...")
    
    # Delete all test articles (will cascade to fact-checks)
    session.query(Article).filter(Article.url.like("%test-news.com%")).delete(synchronize_session=False)
    
    # Delete test RSS source
    session.query(RSSSource).filter_by(source_name="TestNews").delete()
    
    session.commit()
    print("  ✅ Test data cleaned up")


def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 FACT-CHECK END-TO-END INTEGRATION TEST")
    print("=" * 60)
    
    # Setup database connection
    engine = create_engine(str(settings.DATABASE_URL).replace('+asyncpg', ''))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Run tests
        article, fact_check, source = test_create_article_with_fact_check(session)
        high_count, false_count = test_query_by_fact_check_score(session)
        citations_ok = test_jsonb_citation_retrieval(session)
        relationships_ok = test_relationship_access(session)
        constraints_ok = test_unique_constraints(session)
        cascade_ok = test_cascade_delete(session)
        credibility_ok = test_source_credibility_score(session)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        all_passed = all([
            high_count >= 2,
            false_count >= 1,
            citations_ok,
            relationships_ok,
            constraints_ok,
            cascade_ok,
            credibility_ok
        ])
        
        if all_passed:
            print("✅ ALL TESTS PASSED!")
            print("\nThe fact-check database is fully functional and ready for:")
            print("  • Creating articles with comprehensive fact-checks")
            print("  • Fast queries using cached columns")
            print("  • JSONB citation storage and retrieval")
            print("  • ORM relationships")
            print("  • Data integrity via unique constraints")
            print("  • CASCADE deletes")
            print("  • Source credibility tracking")
            result = 0
        else:
            print("❌ SOME TESTS FAILED")
            result = 1
        
        # Cleanup
        cleanup(session)
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
