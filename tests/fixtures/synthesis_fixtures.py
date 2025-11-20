"""
Test fixtures for synthesis endpoints.
Creates realistic test data with proper UUIDs, relationships, and JSONB structures.
"""
import pytest
from datetime import datetime, timedelta
from typing import List
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.rss_source import RSSSource


@pytest.fixture
async def test_rss_source(test_db: AsyncSession) -> RSSSource:
    """Create a test RSS source for article relationships."""
    source = RSSSource(
        id=uuid.uuid4(),
        name="Test News Source",
        url="https://testnews.com/feed",
        category="general",
        is_active=True,
        fetch_interval=3600
    )
    test_db.add(source)
    await test_db.commit()
    await test_db.refresh(source)
    return source


@pytest.fixture
async def synthesis_articles(test_db: AsyncSession, test_rss_source: RSSSource) -> List[Article]:
    """
    Create a comprehensive set of synthesis articles for testing.
    
    Returns 5 articles:
    1. Full synthesis with all features (HIGH verdict)
    2. Synthesis with timeline only (MOSTLY TRUE)
    3. Synthesis with context emphasis only (MIXED)
    4. Minimal synthesis (MOSTLY FALSE)
    5. Regular article without synthesis (control)
    """
    base_time = datetime.utcnow()
    
    articles = [
        # Article 1: Full synthesis with all features
        Article(
            id=uuid.uuid4(),
            rss_source_id=test_rss_source.id,
            title="Climate Change Report: Global Temperature Rises 1.5°C",
            url="https://example.com/climate-report-2025",
            url_hash="a" * 64,
            content="Original article content about climate change...",
            synthesis_article="""
# Climate Change: Critical Threshold Reached

## Summary
Latest research confirms global temperatures have risen 1.5°C above pre-industrial levels.

### Key Findings
- Global average temperature increased 1.5°C since 1850
- Arctic ice melting at unprecedented rates
- Immediate action required within next decade

### Timeline
- **2015**: Paris Agreement signed
- **2020**: Record-breaking temperatures
- **2025**: 1.5°C threshold reached

> **Important Context**: This aligns with IPCC projections from 2018 report.

### References
Multiple peer-reviewed sources confirm these findings.
            """,
            published_date=base_time - timedelta(days=1),
            author="Dr. Jane Smith",
            category="science",
            # Synthesis helper columns
            has_synthesis=True,
            synthesis_preview="Latest research confirms global temperatures have risen 1.5°C above pre-industrial levels...",
            synthesis_word_count=245,
            has_context_emphasis=True,
            has_timeline=True,
            # Metadata enrichment
            timeline_event_count=3,
            reference_count=8,
            margin_note_count=2,
            fact_check_mode="synthesis",
            fact_check_processing_time=45,
            synthesis_generated_at=base_time - timedelta(hours=2),
            # UX enhancements
            synthesis_read_minutes=2,
            verdict_color="green",
            # Fact check fields
            fact_check_verdict="TRUE",
            fact_check_score=92,
            # JSONB data
            article_data={
                "references": [
                    {
                        "citation_number": 1,
                        "full_citation": "IPCC Special Report on Global Warming, 2018",
                        "url": "https://www.ipcc.ch/sr15/",
                        "credibility_rating": "HIGH"
                    },
                    {
                        "citation_number": 2,
                        "full_citation": "NASA Climate Change Evidence, 2024",
                        "url": "https://climate.nasa.gov/",
                        "credibility_rating": "HIGH"
                    }
                ],
                "event_timeline": [
                    {"date": "2015-12-12", "event": "Paris Agreement signed"},
                    {"date": "2020-07-01", "event": "Record temperatures recorded"},
                    {"date": "2025-01-15", "event": "1.5°C threshold officially reached"}
                ],
                "margin_notes": [
                    {"note_text": "Pre-industrial baseline: 1850-1900 average", "position": "paragraph-2"},
                    {"note_text": "Threshold is global average, not local", "position": "paragraph-4"}
                ],
                "context_and_emphasis": [
                    {"context_item": "IPCC projections from 2018 predicted this timeline", "impact": "Confirms model accuracy"}
                ]
            }
        ),
        
        # Article 2: Timeline only
        Article(
            id=uuid.uuid4(),
            rss_source_id=test_rss_source.id,
            title="Tech Company Announces Breakthrough in AI",
            url="https://example.com/ai-breakthrough",
            url_hash="b" * 64,
            content="Tech company reveals new AI system...",
            synthesis_article="# AI Breakthrough\n\n## Timeline\n- Jan 2025: Project started\n- May 2025: Announcement",
            published_date=base_time - timedelta(days=2),
            author="John Doe",
            category="general",
            has_synthesis=True,
            synthesis_preview="Tech company reveals new AI system with human-level reasoning...",
            synthesis_word_count=189,
            has_context_emphasis=False,
            has_timeline=True,
            timeline_event_count=2,
            reference_count=4,
            margin_note_count=0,
            fact_check_mode="synthesis",
            fact_check_processing_time=28,
            synthesis_generated_at=base_time - timedelta(hours=5),
            synthesis_read_minutes=1,
            verdict_color="lime",
            fact_check_verdict="MOSTLY TRUE",
            fact_check_score=78,
            article_data={
                "references": [],
                "event_timeline": [
                    {"date": "2025-01-01", "event": "Project initiated"},
                    {"date": "2025-05-01", "event": "Public announcement"}
                ],
                "margin_notes": [],
                "context_and_emphasis": []
            }
        ),
        
        # Article 3: Context emphasis only
        Article(
            id=uuid.uuid4(),
            rss_source_id=test_rss_source.id,
            title="Economic Policy Changes Impact Markets",
            url="https://example.com/economic-policy",
            url_hash="c" * 64,
            content="Central bank adjusts interest rates...",
            synthesis_article="# Economic Policy\n\n> **Key Context**: First rate change in 18 months.",
            published_date=base_time - timedelta(days=3),
            author="Sarah Johnson",
            category="politics",
            has_synthesis=True,
            synthesis_preview="Central bank adjusts interest rates affecting global markets...",
            synthesis_word_count=156,
            has_context_emphasis=True,
            has_timeline=False,
            timeline_event_count=0,
            reference_count=6,
            margin_note_count=4,
            fact_check_mode="synthesis",
            fact_check_processing_time=32,
            synthesis_generated_at=base_time - timedelta(hours=8),
            synthesis_read_minutes=1,
            verdict_color="yellow",
            fact_check_verdict="MIXED",
            fact_check_score=65,
            article_data={
                "references": [],
                "event_timeline": [],
                "margin_notes": [
                    {"note_text": "First change in 18 months", "position": "para-1"}
                ],
                "context_and_emphasis": [
                    {"context_item": "Historical volatility follows rate changes", "impact": "Markets may be unstable"}
                ]
            }
        ),
        
        # Article 4: Minimal synthesis
        Article(
            id=uuid.uuid4(),
            rss_source_id=test_rss_source.id,
            title="Local Event Draws Small Crowd",
            url="https://example.com/local-event",
            url_hash="d" * 64,
            content="Community gathering...",
            synthesis_article="# Local Event\n\nSmall turnout at community event.",
            published_date=base_time - timedelta(days=4),
            author="Mike Brown",
            category="general",
            has_synthesis=True,
            synthesis_preview="Community gathering attended by approximately 50 people.",
            synthesis_word_count=45,
            has_context_emphasis=False,
            has_timeline=False,
            timeline_event_count=0,
            reference_count=1,
            margin_note_count=0,
            fact_check_mode="synthesis",
            fact_check_processing_time=8,
            synthesis_generated_at=base_time - timedelta(hours=12),
            synthesis_read_minutes=1,
            verdict_color="orange",
            fact_check_verdict="MOSTLY FALSE",
            fact_check_score=45,
            article_data={
                "references": [],
                "event_timeline": [],
                "margin_notes": [],
                "context_and_emphasis": []
            }
        ),
        
        # Article 5: No synthesis (control)
        Article(
            id=uuid.uuid4(),
            rss_source_id=test_rss_source.id,
            title="Regular Article Without Synthesis",
            url="https://example.com/regular-article",
            url_hash="e" * 64,
            content="This article has not been processed...",
            synthesis_article=None,
            published_date=base_time - timedelta(days=5),
            author="Alex Lee",
            category="general",
            has_synthesis=False,
            synthesis_preview=None,
            synthesis_word_count=None,
            has_context_emphasis=False,
            has_timeline=False,
            timeline_event_count=None,
            reference_count=None,
            margin_note_count=None,
            fact_check_mode=None,
            fact_check_processing_time=None,
            synthesis_generated_at=None,
            synthesis_read_minutes=None,
            verdict_color=None,
            fact_check_verdict=None,
            fact_check_score=None,
            article_data=None
        )
    ]
    
    for article in articles:
        test_db.add(article)
    
    await test_db.commit()
    
    # Refresh all to get generated fields
    for article in articles:
        await test_db.refresh(article)
    
    return articles


@pytest.fixture
async def empty_database(test_db: AsyncSession):
    """Fixture that ensures database has no synthesis articles."""
    # Delete all articles
    from sqlalchemy import delete
    await test_db.execute(delete(Article))
    await test_db.commit()
    return test_db
