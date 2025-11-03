"""
Pytest configuration and shared fixtures.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.session import Base, get_db
from app.core.config import settings


# Test database URL (use a separate test database)
TEST_DATABASE_URL = settings.DATABASE_URL.replace("/rss_feed", "/rss_feed_test")


@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for each test."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_engine():
    """Create test database engine for each test."""
    from sqlalchemy import text
    
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
        future=True,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        # Drop materialized views first (if they exist)
        await conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS analytics_category_summary CASCADE"))
        await conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS analytics_source_reliability CASCADE"))
        await conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS analytics_daily_summary CASCADE"))
        
        # Now drop and recreate tables
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup - dispose engine properly
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    connection = await test_engine.connect()
    transaction = await connection.begin()
    
    async_session = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    
    async with async_session() as session:
        yield session
        await transaction.rollback()
        await connection.close()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database session override."""
    from httpx import ASGITransport
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(client: AsyncClient) -> dict:
    """Create a test user and return user data with token."""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    # Register user
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    
    # Login to get token
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    
    # Get user ID from profile endpoint
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    profile_response = await client.get("/api/v1/users/me", headers=headers)
    profile = profile_response.json()
    
    return {
        "username": user_data["username"],
        "email": user_data["email"],
        "token": token_data["access_token"],
        "user_id": profile["id"]
    }


@pytest.fixture
async def test_user_2(client: AsyncClient) -> dict:
    """Create a second test user."""
    user_data = {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "testpassword123"
    }
    
    # Register user
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    
    # Login to get token
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    
    # Get user ID from profile endpoint
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    profile_response = await client.get("/api/v1/users/me", headers=headers)
    profile = profile_response.json()
    
    return {
        "username": user_data["username"],
        "email": user_data["email"],
        "token": token_data["access_token"],
        "user_id": profile["id"]
    }


@pytest.fixture
async def auth_headers(test_user: dict) -> dict:
    """Get authentication headers for test user."""
    return {"Authorization": f"Bearer {test_user['token']}"}


@pytest.fixture
async def auth_headers_2(test_user_2: dict) -> dict:
    """Get authentication headers for second test user."""
    return {"Authorization": f"Bearer {test_user_2['token']}"}


@pytest.fixture
async def authenticated_user(test_user: dict, db_session: AsyncSession) -> tuple:
    """Get authenticated regular user (not admin) as (User, token) tuple."""
    from app.models.user import User
    from uuid import UUID
    from sqlalchemy import select
    
    result = await db_session.execute(
        select(User).where(User.id == UUID(test_user["user_id"]))
    )
    user = result.scalar_one()
    return user, test_user["token"]


@pytest.fixture
async def sample_rss_source(db_session: AsyncSession):
    """Create a sample RSS source for testing."""
    from app.models.rss_source import RSSSource
    from uuid import uuid4
    
    source = RSSSource(
        id=uuid4(),
        name="Test Source",
        url="https://example.com/feed.xml",
        source_name="Example Source",
        category="technology",
        is_active=True
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)
    return source


@pytest.fixture
async def sample_rss_sources(db_session: AsyncSession) -> list:
    """Create multiple RSS sources for testing."""
    from app.models.rss_source import RSSSource
    from uuid import uuid4
    
    sources = [
        RSSSource(
            id=uuid4(),
            name="Tech Source 1",
            url="https://example.com/tech1.xml",
            source_name="TechSource1",
            category="technology",
            is_active=True
        ),
        RSSSource(
            id=uuid4(),
            name="Science Source 1",
            url="https://example.com/science1.xml",
            source_name="ScienceSource1",
            category="science",
            is_active=True
        ),
        RSSSource(
            id=uuid4(),
            name="Inactive Source",
            url="https://example.com/inactive.xml",
            source_name="InactiveSource",
            category="technology",
            is_active=False
        ),
    ]
    
    for source in sources:
        db_session.add(source)
    await db_session.commit()
    
    for source in sources:
        await db_session.refresh(source)
    
    return sources


@pytest.fixture
async def test_db(db_session: AsyncSession) -> AsyncSession:
    """Alias for db_session for compatibility."""
    return db_session


@pytest.fixture
async def test_article(client: AsyncClient, db_session: AsyncSession) -> dict:
    """Create a test article with unique URLs."""
    from app.models.article import Article
    from app.models.rss_source import RSSSource
    from uuid import uuid4
    from datetime import datetime
    import hashlib
    
    # Generate unique identifiers for this test
    unique_id = uuid4().hex[:8]
    
    # Create an RSS source first with unique URL
    source = RSSSource(
        id=uuid4(),
        name=f"Test Source Feed {unique_id}",
        url=f"https://example.com/feed-{unique_id}.xml",
        source_name=f"Test Source {unique_id}",
        category="general",
        is_active=True
    )
    db_session.add(source)
    await db_session.commit()
    
    # Create article with unique URL
    url = f"https://example.com/test-{unique_id}"
    article = Article(
        id=uuid4(),
        rss_source_id=source.id,
        title=f"Test Article {unique_id}",
        url=url,
        url_hash=hashlib.sha256(url.encode()).hexdigest(),
        description="Test article description",
        content="Test article content",
        author="Test Author",
        published_date=datetime.utcnow(),
        category="Technology",
        vote_score=0,
        vote_count=0,
        comment_count=0
    )
    
    db_session.add(article)
    await db_session.commit()
    await db_session.refresh(article)
    
    return {
        "id": str(article.id),
        "title": article.title,
        "url": article.url
    }


@pytest.fixture
async def admin_user(client: AsyncClient, db_session: AsyncSession) -> dict:
    """Create an admin user for testing."""
    from app.models.user import User
    from uuid import uuid4
    
    # Create admin user directly
    admin = User(
        id=uuid4(),
        username="adminuser",
        email="admin@example.com",
        is_active=True,
        is_superuser=True
    )
    admin.set_password("adminpassword123")
    
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    
    # Login to get token
    login_data = {
        "email": "admin@example.com",
        "password": "adminpassword123"
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    
    return {
        "username": admin.username,
        "email": admin.email,
        "token": token_data["access_token"],
        "user_id": str(admin.id)
    }


@pytest.fixture
async def admin_token(admin_user: dict) -> str:
    """Get admin access token."""
    return admin_user["token"]


@pytest.fixture
async def auth_token(test_user: dict) -> str:
    """Get regular user access token."""
    return test_user["token"]


@pytest.fixture
async def db(db_session: AsyncSession) -> AsyncSession:
    """Alias for db_session to match test expectations."""
    return db_session


@pytest.fixture
async def test_article_with_fact_check(client: AsyncClient, db_session: AsyncSession) -> dict:
    """Create a test article with a basic fact-check."""
    from app.models.article import Article
    from app.models.rss_source import RSSSource
    from app.models.fact_check import FactCheck
    from uuid import uuid4
    from datetime import datetime
    import hashlib
    
    unique_id = uuid4().hex[:8]
    
    # Create RSS source
    source = RSSSource(
        id=uuid4(),
        name=f"Test Source Feed {unique_id}",
        url=f"https://example.com/feed-{unique_id}.xml",
        source_name=f"Test Source {unique_id}",
        category="general",
        is_active=True
    )
    db_session.add(source)
    await db_session.commit()
    
    # Create article
    url = f"https://example.com/test-{unique_id}"
    article = Article(
        id=uuid4(),
        rss_source_id=source.id,
        title=f"Test Article {unique_id}",
        url=url,
        url_hash=hashlib.sha256(url.encode()).hexdigest(),
        description="Test article description",
        content="Test article content",
        author="Test Author",
        published_date=datetime.utcnow(),
        category="Technology",
        vote_score=0,
        vote_count=0,
        comment_count=0
    )
    db_session.add(article)
    await db_session.commit()
    
    # Create fact-check
    fact_check = FactCheck(
        id=uuid4(),
        article_id=article.id,
        job_id=f"test-job-{unique_id}",
        verdict="TRUE",
        credibility_score=85,
        confidence=0.9,
        summary="Test fact-check summary",
        claims_analyzed=1,
        claims_validated=1,
        claims_true=1,
        claims_false=0,
        claims_misleading=0,
        claims_unverified=0,
        validation_results={
            "claim": "Test claim",
            "verdict": "TRUE",
            "confidence": 0.9,
            "key_evidence": {
                "supporting": ["Evidence 1"],
                "contradicting": [],
                "context": []
            },
            "references": [
                {
                    "citation_id": 1,
                    "title": "Test Source",
                    "url": "https://example.com",
                    "source": "Test News",
                    "credibility": "HIGH"
                }
            ]
        },
        num_sources=10,
        source_consensus="STRONG_AGREEMENT",
        validation_mode="summary",
        processing_time_seconds=100,
        api_costs={"total": 0.005},
        fact_checked_at=datetime.utcnow()
    )
    db_session.add(fact_check)
    await db_session.commit()
    await db_session.refresh(article)
    
    return {
        "id": str(article.id),
        "title": article.title,
        "url": article.url,
        "fact_check_id": str(fact_check.id)
    }


@pytest.fixture
async def test_article_with_complete_fact_check(client: AsyncClient, db_session: AsyncSession) -> dict:
    """Create a test article with a complete fact-check (all fields populated)."""
    from app.models.article import Article
    from app.models.rss_source import RSSSource
    from app.models.fact_check import FactCheck
    from uuid import uuid4
    from datetime import datetime
    import hashlib
    
    unique_id = uuid4().hex[:8]
    
    # Create RSS source
    source = RSSSource(
        id=uuid4(),
        name=f"Test Source Feed {unique_id}",
        url=f"https://example.com/feed-{unique_id}.xml",
        source_name=f"Test Source {unique_id}",
        category="general",
        is_active=True
    )
    db_session.add(source)
    await db_session.commit()
    
    # Create article
    url = f"https://example.com/test-complete-{unique_id}"
    article = Article(
        id=uuid4(),
        rss_source_id=source.id,
        title=f"Complete Test Article {unique_id}",
        url=url,
        url_hash=hashlib.sha256(url.encode()).hexdigest(),
        description="Complete test article description",
        content="Complete test article content",
        author="Test Author",
        published_date=datetime.utcnow(),
        category="Technology",
        vote_score=0,
        vote_count=0,
        comment_count=0
    )
    db_session.add(article)
    await db_session.commit()
    
    # Create complete fact-check with all optional fields
    fact_check = FactCheck(
        id=uuid4(),
        article_id=article.id,
        job_id=f"test-job-complete-{unique_id}",
        verdict="MISLEADING",
        credibility_score=45,
        confidence=0.75,
        summary="Complete test fact-check with all fields",
        claims_analyzed=5,
        claims_validated=5,
        claims_true=2,
        claims_false=1,
        claims_misleading=2,
        claims_unverified=0,
        validation_results={
            "claim": "Complete test claim",
            "verdict": "MISLEADING",
            "confidence": 0.75,
            "key_evidence": {
                "supporting": ["Evidence 1", "Evidence 2"],
                "contradicting": ["Counter evidence"],
                "context": ["Context info"]
            },
            "references": [
                {
                    "citation_id": 1,
                    "title": "Source 1",
                    "url": "https://example.com/1",
                    "source": "News Outlet 1",
                    "credibility": "HIGH"
                },
                {
                    "citation_id": 2,
                    "title": "Source 2",
                    "url": "https://example.com/2",
                    "source": "News Outlet 2",
                    "credibility": "MEDIUM"
                }
            ]
        },
        num_sources=25,
        source_consensus="MIXED",
        validation_mode="thorough",
        processing_time_seconds=200,
        api_costs={"total": 0.015, "api_calls": 10},
        fact_checked_at=datetime.utcnow()
    )
    db_session.add(fact_check)
    await db_session.commit()
    await db_session.refresh(article)
    
    return {
        "id": str(article.id),
        "title": article.title,
        "url": article.url,
        "fact_check_id": str(fact_check.id)
    }
