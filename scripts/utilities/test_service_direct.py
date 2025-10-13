#!/usr/bin/env python
"""Direct test of reading history service."""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.reading_history_service import ReadingHistoryService


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        service = ReadingHistoryService(session)
        
        # Test parameters
        user_id = "40fccf1f-f779-44a7-94cb-f8c70fa6cc05"  # Our test user
        article_id = "c66d9651-8369-4f51-8499-cc12b563f3bb"  # Test article
        
        try:
            print("Testing service.record_view()...")
            history = await service.record_view(
                user_id=user_id,
                article_id=article_id,
                duration_seconds=120,
                scroll_percentage=85.5
            )
            print(f"✅ Success! Created history: {history.id}")
            print(f"   - User: {history.user_id}")
            print(f"   - Article: {history.article_id}")
            print(f"   - Duration: {history.duration_seconds}s")
            print(f"   - Scroll: {history.scroll_percentage}%")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
