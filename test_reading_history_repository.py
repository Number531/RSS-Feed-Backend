#!/usr/bin/env python
"""Comprehensive tests for reading history repository."""
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.repositories.reading_history_repository import ReadingHistoryRepository
from app.models.user import User
from app.models.article import Article


async def test_repository():
    """Test reading history repository operations."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            print("🔍 Testing Reading History Repository...")
            print("=" * 60)
            
            # Get test user and articles
            result = await session.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            
            result = await session.execute(select(Article).limit(3))
            articles = list(result.scalars().all())
            
            if not user or len(articles) < 2:
                print("❌ Insufficient test data. Need user and at least 2 articles.")
                return False
            
            print(f"✅ Test user: {user.username}")
            print(f"✅ Test articles: {len(articles)}")
            print()
            
            # Initialize repository
            repo = ReadingHistoryRepository(session)
            
            # Test 1: Record basic view
            print("Test 1: Record basic article view")
            history1 = await repo.record_view(
                user_id=user.id,
                article_id=articles[0].id
            )
            print(f"✅ Recorded view: {history1.id}")
            print(f"   - Article: {history1.article.title[:50] if history1.article else 'N/A'}...")
            print(f"   - Viewed at: {history1.viewed_at}")
            print()
            
            # Test 2: Record view with metrics
            print("Test 2: Record view with engagement metrics")
            history2 = await repo.record_view(
                user_id=user.id,
                article_id=articles[1].id,
                duration_seconds=120,
                scroll_percentage=85.5
            )
            print(f"✅ Recorded view with metrics: {history2.id}")
            print(f"   - Duration: {history2.duration_seconds}s")
            print(f"   - Scroll: {history2.scroll_percentage}%")
            print()
            
            # Test 3: Record multiple views
            print("Test 3: Record multiple views of same article")
            history3 = await repo.record_view(
                user_id=user.id,
                article_id=articles[0].id,
                duration_seconds=60
            )
            print(f"✅ Recorded second view of same article: {history3.id}")
            print()
            
            # Test 4: Get user history
            print("Test 4: Get user history with pagination")
            history_list, total = await repo.get_user_history(
                user_id=user.id,
                skip=0,
                limit=10
            )
            print(f"✅ Retrieved {len(history_list)} items (total: {total})")
            for h in history_list:
                print(f"   - {h.viewed_at}: {h.article.title[:40] if h.article else 'N/A'}...")
            print()
            
            # Test 5: Get recently read
            print("Test 5: Get recently read articles")
            recent = await repo.get_recently_read(
                user_id=user.id,
                days=7,
                limit=5
            )
            print(f"✅ Found {len(recent)} recently read articles")
            print()
            
            # Test 6: Count views
            print("Test 6: Count total views by user")
            count = await repo.count_views_by_user(user.id)
            print(f"✅ User has {count} total views")
            print()
            
            # Test 7: Get total reading time
            print("Test 7: Get total reading time")
            total_time = await repo.get_total_reading_time(user.id)
            print(f"✅ Total reading time: {total_time} seconds ({total_time // 60} minutes)")
            print()
            
            # Test 8: Date filtering
            print("Test 8: Filter history by date range")
            yesterday = datetime.utcnow() - timedelta(days=1)
            tomorrow = datetime.utcnow() + timedelta(days=1)
            filtered, filtered_total = await repo.get_user_history(
                user_id=user.id,
                start_date=yesterday,
                end_date=tomorrow,
                skip=0,
                limit=10
            )
            print(f"✅ Filtered results: {len(filtered)} items (total: {filtered_total})")
            print()
            
            # Test 9: Count with date range
            print("Test 9: Count views within date range")
            count_filtered = await repo.count_views_by_user(
                user_id=user.id,
                start_date=yesterday,
                end_date=tomorrow
            )
            print(f"✅ Views in date range: {count_filtered}")
            print()
            
            # Test 10: Pagination
            print("Test 10: Test pagination")
            page1, total = await repo.get_user_history(user.id, skip=0, limit=2)
            page2, _ = await repo.get_user_history(user.id, skip=2, limit=2)
            print(f"✅ Page 1: {len(page1)} items")
            print(f"✅ Page 2: {len(page2)} items")
            print(f"✅ Total: {total} items")
            print()
            
            # Test 11: Clear partial history
            print("Test 11: Clear history before specific date")
            cutoff = datetime.utcnow() - timedelta(hours=1)
            deleted_count = await repo.clear_history(
                user_id=user.id,
                before_date=cutoff
            )
            print(f"✅ Deleted {deleted_count} old history items")
            print()
            
            # Test 12: Verify remaining history
            print("Test 12: Verify remaining history after partial clear")
            remaining, remaining_total = await repo.get_user_history(user.id)
            print(f"✅ Remaining history: {remaining_total} items")
            print()
            
            # Test 13: Clear all history
            print("Test 13: Clear all remaining history")
            all_deleted = await repo.clear_history(user_id=user.id)
            print(f"✅ Deleted all {all_deleted} remaining items")
            print()
            
            # Test 14: Verify empty history
            print("Test 14: Verify history is empty")
            empty, empty_total = await repo.get_user_history(user.id)
            if empty_total == 0:
                print("✅ History is empty as expected")
            else:
                print(f"❌ Expected empty, but found {empty_total} items")
                return False
            print()
            
            print("=" * 60)
            print("✅ All repository tests passed!")
            return True
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("📖 Reading History Repository Tests")
    print("=" * 60 + "\n")
    
    success = asyncio.run(test_repository())
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests completed successfully!")
    else:
        print("❌ Tests failed!")
    print("=" * 60 + "\n")
    
    sys.exit(0 if success else 1)
