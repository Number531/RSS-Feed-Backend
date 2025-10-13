"""Unit test fixtures."""
import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User


@pytest.fixture
async def db_test_user(db_session: AsyncSession):
    """Create a test user directly in the database without API calls."""
    user_id = uuid4()
    user = User(
        id=user_id,
        email=f"test_{user_id.hex[:8]}@example.com",
        username=f"testuser_{user_id.hex[:8]}",
        hashed_password="hashedpw123",
        is_active=True,
        is_superuser=False,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    yield {"user_id": str(user.id)}
    
    # Cleanup is handled by CASCADE constraints


# Create alias for backward compatibility
@pytest.fixture
async def test_user(db_test_user):
    """Alias for db_test_user for backward compatibility."""
    return db_test_user
