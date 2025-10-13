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
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
        future=True,
    )
    
    # Create all tables
    async with engine.begin() as conn:
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
