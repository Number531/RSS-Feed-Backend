#!/usr/bin/env python
"""Create or update test user for integration tests."""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.models.user import User


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    test_email = "test.history@example.com"
    test_password = "TestHistory123!"
    
    async with async_session() as session:
        # Check if user exists
        result = await session.execute(select(User).where(User.email == test_email))
        user = result.scalar_one_or_none()
        
        if user:
            print(f"✅ Test user already exists: {test_email}")
            # Update password
            user.set_password(test_password)
            print("✅ Updated password")
        else:
            # Create new user
            user = User(
                email=test_email,
                username="testhistory",
                full_name="Test History User",
                is_active=True
            )
            user.set_password(test_password)
            session.add(user)
            print(f"✅ Created new test user: {test_email}")
        
        await session.commit()
        await session.refresh(user)
        
        print()
        print("=" * 60)
        print("Test User Credentials:")
        print("=" * 60)
        print(f"Email: {test_email}")
        print(f"Password: {test_password}")
        print(f"Username: {user.username}")
        print(f"User ID: {user.id}")
        print("=" * 60)
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
