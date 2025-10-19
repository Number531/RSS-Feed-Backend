"""
Integration tests for fact-check database migration (006).

Tests verify:
1. Tables exist with correct columns
2. Indexes are created
3. Foreign key relationships work
4. JSONB storage and querying works
5. Unique constraints enforced
"""
import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import text, inspect
from sqlalchemy.exc import IntegrityError

from app.models import Article, ArticleFactCheck, RSSSource, SourceCredibilityScore


@pytest.mark.integration
class TestFactCheckMigration:
    """Test suite for migration 006."""
    
    def test_articles_table_has_fact_check_columns(self, test_db):
        """Verify articles table has new fact-check cache columns."""
        inspector = inspect(test_db.bind)
        columns = {col['name']: col for col in inspector.get_columns('articles')}
        
        # Check columns exist
        assert 'fact_check_score' in columns
        assert 'fact_check_verdict' in columns
        assert 'fact_checked_at' in columns
        
        # Check types
        assert columns['fact_check_score']['type'].__class__.__name__ == 'INTEGER'
        assert columns['fact_check_verdict']['type'].__class__.__name__ == 'VARCHAR'
        assert columns['fact_checked_at']['type'].__class__.__name__ == 'TIMESTAMP'
        
        # Check nullable (all should be nullable for existing articles)
        assert columns['fact_check_score']['nullable'] is True
        assert columns['fact_check_verdict']['nullable'] is True
        assert columns['fact_checked_at']['nullable'] is True
    
    def test_articles_table_has_fact_check_indexes(self, test_db):
        """Verify indexes created on fact-check columns."""
        inspector = inspect(test_db.bind)
        indexes = {idx['name']: idx for idx in inspector.get_indexes('articles')}
        
        assert 'ix_articles_fact_check_score' in indexes
        assert 'ix_articles_fact_check_verdict' in indexes
        assert 'ix_articles_fact_checked_at' in indexes
    
    def test_article_fact_checks_table_exists(self, test_db):
        """Verify article_fact_checks table created with correct structure."""
        inspector = inspect(test_db.bind)
        tables = inspector.get_table_names()
        assert 'article_fact_checks' in tables
        
        columns = {col['name']: col for col in inspector.get_columns('article_fact_checks')}
        
        # Core columns
        required_columns = [
            'id', 'article_id', 'verdict', 'credibility_score', 'confidence',
            'summary', 'claims_analyzed', 'claims_validated', 'claims_true',
            'claims_false', 'claims_misleading', 'claims_unverified',
            'validation_results', 'num_sources', 'source_consensus',
            'job_id', 'validation_mode', 'processing_time_seconds',
            'api_costs', 'fact_checked_at', 'created_at', 'updated_at'
        ]
        
        for col in required_columns:
            assert col in columns, f"Column {col} missing from article_fact_checks"
    
    def test_article_fact_checks_indexes(self, test_db):
        """Verify indexes on article_fact_checks table."""
        inspector = inspect(test_db.bind)
        indexes = {idx['name']: idx for idx in inspector.get_indexes('article_fact_checks')}
        
        expected_indexes = [
            'ix_article_fact_checks_article_id',
            'ix_article_fact_checks_verdict',
            'ix_article_fact_checks_credibility_score',
            'ix_article_fact_checks_job_id',
            'ix_article_fact_checks_fact_checked_at',
            'ix_article_fact_checks_validation_results_gin'
        ]
        
        for idx_name in expected_indexes:
            assert idx_name in indexes, f"Index {idx_name} not found"
    
    def test_article_fact_checks_unique_constraints(self, test_db):
        """Verify unique constraints on article_id and job_id."""
        inspector = inspect(test_db.bind)
        unique_constraints = inspector.get_unique_constraints('article_fact_checks')
        
        # Get column names from unique constraints
        unique_columns = []
        for constraint in unique_constraints:
            unique_columns.extend(constraint['column_names'])
        
        assert 'article_id' in unique_columns
        assert 'job_id' in unique_columns
    
    def test_source_credibility_scores_table_exists(self, test_db):
        """Verify source_credibility_scores table created."""
        inspector = inspect(test_db.bind)
        tables = inspector.get_table_names()
        assert 'source_credibility_scores' in tables
        
        columns = {col['name']: col for col in inspector.get_columns('source_credibility_scores')}
        
        required_columns = [
            'id', 'rss_source_id', 'average_score', 'total_articles_checked',
            'true_count', 'false_count', 'misleading_count', 'unverified_count',
            'period_start', 'period_end', 'period_type', 'trend_data',
            'created_at', 'updated_at'
        ]
        
        for col in required_columns:
            assert col in columns, f"Column {col} missing from source_credibility_scores"
    
    def test_source_credibility_scores_unique_constraint(self, test_db):
        """Verify unique constraint on (rss_source_id, period_type, period_start)."""
        inspector = inspect(test_db.bind)
        unique_constraints = inspector.get_unique_constraints('source_credibility_scores')
        
        # Should have unique constraint named 'unique_source_period_score'
        constraint_names = [c['name'] for c in unique_constraints]
        assert 'unique_source_period_score' in constraint_names
    
    def test_foreign_key_relationships(self, test_db):
        """Verify foreign key constraints."""
        inspector = inspect(test_db.bind)
        
        # article_fact_checks -> articles
        fks = inspector.get_foreign_keys('article_fact_checks')
        article_fk = next((fk for fk in fks if 'article_id' in fk['constrained_columns']), None)
        assert article_fk is not None
        assert article_fk['referred_table'] == 'articles'
        assert article_fk['options']['ondelete'] == 'CASCADE'
        
        # source_credibility_scores -> rss_sources
        fks = inspector.get_foreign_keys('source_credibility_scores')
        source_fk = next((fk for fk in fks if 'rss_source_id' in fk['constrained_columns']), None)
        assert source_fk is not None
        assert source_fk['referred_table'] == 'rss_sources'
        assert source_fk['options']['ondelete'] == 'CASCADE'


@pytest.mark.integration
class TestFactCheckDataOperations:
    """Test CRUD operations on fact-check tables."""
    
    def test_create_article_with_fact_check(self, test_db, sample_rss_source):
        """Test creating article and associated fact-check."""
        # Create article
        article = Article(
            id=uuid.uuid4(),
            rss_source_id=sample_rss_source.id,
            title="Test Article",
            url="https://example.com/article",
            url_hash="abc123",
            description="Test description",
            category="general"
        )
        test_db.add(article)
        test_db.commit()
        
        # Create fact-check
        fact_check = ArticleFactCheck(
            id=uuid.uuid4(),
            article_id=article.id,
            verdict="TRUE",
            credibility_score=95,
            confidence=0.92,
            summary="This article is accurate and well-sourced.",
            claims_analyzed=3,
            claims_validated=3,
            claims_true=3,
            claims_false=0,
            claims_misleading=0,
            claims_unverified=0,
            validation_results={
                "validation_results": [{
                    "claim": "Test claim",
                    "validation_output": {
                        "verdict": "TRUE",
                        "confidence": 0.92,
                        "summary": "Accurate claim",
                        "references": []
                    }
                }]
            },
            num_sources=15,
            source_consensus="GENERAL_AGREEMENT",
            job_id="test-job-123",
            validation_mode="summary",
            processing_time_seconds=45,
            api_costs={"total": 0.01},
            fact_checked_at=datetime.now(timezone.utc)
        )
        test_db.add(fact_check)
        test_db.commit()
        
        # Update article cache
        article.fact_check_score = fact_check.credibility_score
        article.fact_check_verdict = fact_check.verdict
        article.fact_checked_at = fact_check.fact_checked_at
        test_db.commit()
        
        # Verify relationship
        test_db.refresh(article)
        assert article.fact_check is not None
        assert article.fact_check.verdict == "TRUE"
        assert article.fact_check_score == 95
    
    def test_article_fact_check_unique_constraint(self, test_db, sample_rss_source):
        """Test that article_id must be unique (1:1 relationship)."""
        article = Article(
            id=uuid.uuid4(),
            rss_source_id=sample_rss_source.id,
            title="Test Article",
            url="https://example.com/article2",
            url_hash="def456",
            category="general"
        )
        test_db.add(article)
        test_db.commit()
        
        # First fact-check
        fact_check1 = ArticleFactCheck(
            id=uuid.uuid4(),
            article_id=article.id,
            verdict="TRUE",
            credibility_score=95,
            summary="Test",
            validation_results={},
            job_id="job-1",
            fact_checked_at=datetime.now(timezone.utc)
        )
        test_db.add(fact_check1)
        test_db.commit()
        
        # Second fact-check with same article_id should fail
        fact_check2 = ArticleFactCheck(
            id=uuid.uuid4(),
            article_id=article.id,  # Same article_id
            verdict="FALSE",
            credibility_score=10,
            summary="Different test",
            validation_results={},
            job_id="job-2",
            fact_checked_at=datetime.now(timezone.utc)
        )
        test_db.add(fact_check2)
        
        with pytest.raises(IntegrityError):
            test_db.commit()
        test_db.rollback()
    
    def test_job_id_unique_constraint(self, test_db, sample_rss_source):
        """Test that job_id must be unique."""
        # Create two articles
        article1 = Article(
            id=uuid.uuid4(),
            rss_source_id=sample_rss_source.id,
            title="Article 1",
            url="https://example.com/article3",
            url_hash="ghi789",
            category="general"
        )
        article2 = Article(
            id=uuid.uuid4(),
            rss_source_id=sample_rss_source.id,
            title="Article 2",
            url="https://example.com/article4",
            url_hash="jkl012",
            category="general"
        )
        test_db.add_all([article1, article2])
        test_db.commit()
        
        # First fact-check
        fact_check1 = ArticleFactCheck(
            id=uuid.uuid4(),
            article_id=article1.id,
            verdict="TRUE",
            credibility_score=95,
            summary="Test",
            validation_results={},
            job_id="duplicate-job-id",
            fact_checked_at=datetime.now(timezone.utc)
        )
        test_db.add(fact_check1)
        test_db.commit()
        
        # Second fact-check with duplicate job_id should fail
        fact_check2 = ArticleFactCheck(
            id=uuid.uuid4(),
            article_id=article2.id,
            verdict="FALSE",
            credibility_score=10,
            summary="Different",
            validation_results={},
            job_id="duplicate-job-id",  # Duplicate!
            fact_checked_at=datetime.now(timezone.utc)
        )
        test_db.add(fact_check2)
        
        with pytest.raises(IntegrityError):
            test_db.commit()
        test_db.rollback()
    
    def test_jsonb_validation_results_storage(self, test_db, sample_rss_source):
        """Test storing and querying JSONB validation_results."""
        article = Article(
            id=uuid.uuid4(),
            rss_source_id=sample_rss_source.id,
            title="JSONB Test",
            url="https://example.com/jsonb",
            url_hash="jsonb123",
            category="general"
        )
        test_db.add(article)
        test_db.commit()
        
        # Complex validation results with citations
        validation_data = {
            "validation_results": [
                {
                    "claim": "The economy grew by 3.2% in Q4 2024",
                    "risk_level": "HIGH",
                    "validation_output": {
                        "verdict": "TRUE",
                        "confidence": 0.95,
                        "summary": "Claim verified by government data.",
                        "key_evidence": {
                            "supporting": ["Bureau of Labor Statistics Report"],
                            "contradicting": [],
                            "context": ["GDP growth consistent with forecasts"]
                        },
                        "references": [
                            {
                                "citation_id": 1,
                                "title": "Q4 GDP Report",
                                "url": "https://bls.gov/report",
                                "source": "Bureau of Labor Statistics",
                                "date": "2025-01-15",
                                "credibility": "HIGH"
                            }
                        ]
                    },
                    "num_sources": 25
                }
            ]
        }
        
        fact_check = ArticleFactCheck(
            id=uuid.uuid4(),
            article_id=article.id,
            verdict="TRUE",
            credibility_score=95,
            summary="Test",
            validation_results=validation_data,
            job_id="jsonb-test-job",
            fact_checked_at=datetime.now(timezone.utc)
        )
        test_db.add(fact_check)
        test_db.commit()
        
        # Retrieve and verify JSONB data
        test_db.refresh(fact_check)
        assert fact_check.validation_results is not None
        assert "validation_results" in fact_check.validation_results
        assert len(fact_check.validation_results["validation_results"]) == 1
        
        # Verify nested data
        first_result = fact_check.validation_results["validation_results"][0]
        assert first_result["claim"] == "The economy grew by 3.2% in Q4 2024"
        assert first_result["validation_output"]["verdict"] == "TRUE"
        assert len(first_result["validation_output"]["references"]) == 1
    
    def test_cascade_delete_article_deletes_fact_check(self, test_db, sample_rss_source):
        """Test CASCADE delete on article removes fact-check."""
        article = Article(
            id=uuid.uuid4(),
            rss_source_id=sample_rss_source.id,
            title="Delete Test",
            url="https://example.com/delete",
            url_hash="delete123",
            category="general"
        )
        test_db.add(article)
        test_db.commit()
        
        fact_check = ArticleFactCheck(
            id=uuid.uuid4(),
            article_id=article.id,
            verdict="TRUE",
            credibility_score=95,
            summary="Test",
            validation_results={},
            job_id="cascade-test",
            fact_checked_at=datetime.now(timezone.utc)
        )
        test_db.add(fact_check)
        test_db.commit()
        
        fact_check_id = fact_check.id
        
        # Delete article
        test_db.delete(article)
        test_db.commit()
        
        # Fact-check should be deleted
        deleted_fact_check = test_db.query(ArticleFactCheck).filter_by(id=fact_check_id).first()
        assert deleted_fact_check is None
    
    def test_create_source_credibility_score(self, test_db, sample_rss_source):
        """Test creating source credibility score."""
        now = datetime.now(timezone.utc)
        
        score = SourceCredibilityScore(
            id=uuid.uuid4(),
            rss_source_id=sample_rss_source.id,
            average_score=87.5,
            total_articles_checked=50,
            true_count=40,
            false_count=5,
            misleading_count=3,
            unverified_count=2,
            period_start=now,
            period_end=now,
            period_type="monthly",
            trend_data={"trend": [85, 86, 87, 87.5]}
        )
        test_db.add(score)
        test_db.commit()
        
        # Verify relationship
        test_db.refresh(sample_rss_source)
        assert len(sample_rss_source.credibility_scores) > 0
        assert sample_rss_source.credibility_scores[0].average_score == 87.5
    
    def test_source_period_unique_constraint(self, test_db, sample_rss_source):
        """Test unique constraint on (source, period_type, period_start)."""
        now = datetime.now(timezone.utc)
        
        score1 = SourceCredibilityScore(
            id=uuid.uuid4(),
            rss_source_id=sample_rss_source.id,
            average_score=85.0,
            total_articles_checked=10,
            period_start=now,
            period_end=now,
            period_type="daily"
        )
        test_db.add(score1)
        test_db.commit()
        
        # Duplicate should fail
        score2 = SourceCredibilityScore(
            id=uuid.uuid4(),
            rss_source_id=sample_rss_source.id,
            average_score=90.0,
            total_articles_checked=20,
            period_start=now,  # Same period_start
            period_end=now,
            period_type="daily"  # Same period_type
        )
        test_db.add(score2)
        
        with pytest.raises(IntegrityError):
            test_db.commit()
        test_db.rollback()


@pytest.mark.integration
class TestFactCheckQueries:
    """Test query performance patterns."""
    
    def test_fast_article_feed_query_with_fact_checks(self, test_db, sample_rss_source):
        """Test fast article feed using cached columns (no JOIN)."""
        # Create articles with fact-checks
        for i in range(5):
            article = Article(
                id=uuid.uuid4(),
                rss_source_id=sample_rss_source.id,
                title=f"Article {i}",
                url=f"https://example.com/article{i}",
                url_hash=f"hash{i}",
                category="general",
                fact_check_score=80 + i * 5,
                fact_check_verdict="TRUE" if i % 2 == 0 else "FALSE",
                fact_checked_at=datetime.now(timezone.utc)
            )
            test_db.add(article)
        test_db.commit()
        
        # Fast query using cached columns only
        articles = test_db.query(Article).filter(
            Article.category == "general",
            Article.fact_check_score != None
        ).order_by(Article.fact_check_score.desc()).limit(3).all()
        
        assert len(articles) == 3
        assert articles[0].fact_check_score >= articles[1].fact_check_score
    
    def test_article_with_full_fact_check_join(self, test_db, sample_rss_source):
        """Test fetching article with full fact-check details (LEFT JOIN)."""
        article = Article(
            id=uuid.uuid4(),
            rss_source_id=sample_rss_source.id,
            title="Join Test",
            url="https://example.com/join",
            url_hash="join123",
            category="general"
        )
        test_db.add(article)
        test_db.commit()
        
        fact_check = ArticleFactCheck(
            id=uuid.uuid4(),
            article_id=article.id,
            verdict="MOSTLY_TRUE",
            credibility_score=85,
            summary="Mostly accurate with minor issues.",
            validation_results={"test": "data"},
            job_id="join-job",
            num_sources=20,
            fact_checked_at=datetime.now(timezone.utc)
        )
        test_db.add(fact_check)
        test_db.commit()
        
        # Query with eager loading
        result = test_db.query(Article).filter(Article.id == article.id).first()
        
        # Access relationship (triggers JOIN)
        assert result.fact_check is not None
        assert result.fact_check.verdict == "MOSTLY_TRUE"
        assert result.fact_check.summary == "Mostly accurate with minor issues."
        assert result.fact_check.num_sources == 20
