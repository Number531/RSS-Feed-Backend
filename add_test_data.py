#!/usr/bin/env python3
"""Add test data to the database for API testing."""

import asyncio
import hashlib
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
# Import all models to ensure relationships are properly configured
import app.models  # This imports all models
from app.models.rss_source import RSSSource
from app.models.article import Article

async def add_test_data():
    """Add test RSS source and article."""
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Create RSS Source
        rss_source = RSSSource(
            id=uuid4(),
            name="Test News Feed",
            url="https://example.com/feed",
            source_name="Test Source",
            category="tech",
            is_active=True
        )
        session.add(rss_source)
        await session.flush()
        
        # Create Article
        url = f"https://example.com/test-article-{uuid4().hex[:8]}"
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        
        article = Article(
            id=uuid4(),
            rss_source_id=rss_source.id,
            title="Test Article for Comment Voting",
            url=url,
            url_hash=url_hash,
            description="This is a test article for testing the comment voting system.",
            content="Full content of the test article...",
            author="Test Author",
            published_date=datetime.now(timezone.utc),
            category="tech",
            vote_score=0,
            vote_count=0,
            comment_count=0
        )
        session.add(article)
        
        await session.commit()
        
        print("✅ Test data added successfully!")
        print(f"   RSS Source ID: {rss_source.id}")
        print(f"   Article ID: {article.id}")
        print(f"   Article Title: {article.title}")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_test_data())
