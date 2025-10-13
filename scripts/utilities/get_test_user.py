#!/usr/bin/env python
"""Get test user information."""
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
    
    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == 'testuser99'))
        user = result.scalar_one_or_none()
        
        if user:
            print(f"Email: {user.email}")
            print(f"Username: {user.username}")
        else:
            print("User not found")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
