#!/usr/bin/env python
"""Test script for bookmark repository."""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

from app.core.config import settings
from app.repositories.bookmark_repository import BookmarkRepository
from app.models.user import User
from app.models.article import Article


async def test_repository():
    """Test bookmark repository operations."""
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            print("🔍 Testing Bookmark Repository...")
            print("=" * 60)
            
            # Get a test user and article
            result = await session.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            
            result = await session.execute(select(Article).limit(1))
            article = result.scalar_one_or_none()
            
            if not user or not article:
                print("❌ No test data found. Please run seed_database.py first.")
                return False
            
            print(f"✅ Found test user: {user.username} ({user.email})")
            print(f"✅ Found test article: {article.title[:50]}...")
            print()
            
            # Initialize repository
            repo = BookmarkRepository(session)
            
            # Test 1: Create bookmark
            print("Test 1: Create bookmark")
            bookmark = await repo.create(
                user_id=user.id,
                article_id=article.id,
                collection="Test Collection",
                notes="Test notes"
            )
            print(f"✅ Created bookmark: {bookmark.id}")
            print(f"   - Collection: {bookmark.collection}")
            print(f"   - Notes: {bookmark.notes}")
            print()
            
            # Test 2: Get bookmark by ID
            print("Test 2: Get bookmark by ID")
            fetched = await repo.get_by_id(bookmark.id)
            if fetched and fetched.id == bookmark.id:
                print(f"✅ Retrieved bookmark by ID: {fetched.id}")
            else:
                print("❌ Failed to retrieve bookmark by ID")
                return False
            print()
            
            # Test 3: Check existence
            print("Test 3: Check bookmark existence")
            exists = await repo.exists(user.id, article.id)
            if exists:
                print("✅ Bookmark exists check passed")
            else:
                print("❌ Bookmark exists check failed")
                return False
            print()
            
            # Test 4: Get by user and article
            print("Test 4: Get bookmark by user and article")
            fetched_by_combo = await repo.get_by_user_and_article(user.id, article.id)
            if fetched_by_combo and fetched_by_combo.id == bookmark.id:
                print("✅ Retrieved bookmark by user+article")
            else:
                print("❌ Failed to retrieve bookmark by user+article")
                return False
            print()
            
            # Test 5: Update bookmark
            print("Test 5: Update bookmark")
            updated = await repo.update(
                bookmark_id=bookmark.id,
                collection="Updated Collection",
                notes="Updated notes"
            )
            if updated and updated.collection == "Updated Collection":
                print("✅ Updated bookmark successfully")
                print(f"   - New collection: {updated.collection}")
                print(f"   - New notes: {updated.notes}")
            else:
                print("❌ Failed to update bookmark")
                return False
            print()
            
            # Test 6: List bookmarks
            print("Test 6: List user bookmarks")
            bookmarks, total = await repo.list_by_user(user.id, skip=0, limit=10)
            print(f"✅ Listed {len(bookmarks)} bookmarks (total: {total})")
            for bm in bookmarks:
                print(f"   - {bm.id}: {bm.article.title[:40] if bm.article else 'N/A'}...")
            print()
            
            # Test 7: Get collections
            print("Test 7: Get user collections")
            collections = await repo.get_collections(user.id)
            print(f"✅ Found {len(collections)} collections:")
            for coll in collections:
                print(f"   - {coll}")
            print()
            
            # Test 8: Count bookmarks
            print("Test 8: Count user bookmarks")
            count = await repo.count_by_user(user.id)
            print(f"✅ User has {count} bookmarks")
            print()
            
            # Test 9: Delete bookmark
            print("Test 9: Delete bookmark")
            deleted = await repo.delete(bookmark.id)
            if deleted:
                print("✅ Deleted bookmark successfully")
            else:
                print("❌ Failed to delete bookmark")
                return False
            print()
            
            # Test 10: Verify deletion
            print("Test 10: Verify deletion")
            fetched_after_delete = await repo.get_by_id(bookmark.id)
            if fetched_after_delete is None:
                print("✅ Bookmark deleted successfully (not found)")
            else:
                print("❌ Bookmark still exists after deletion")
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
    print("📦 Bookmark Repository Tests")
    print("=" * 60 + "\n")
    
    success = asyncio.run(test_repository())
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests completed successfully!")
    else:
        print("❌ Tests failed!")
    print("=" * 60 + "\n")
    
    sys.exit(0 if success else 1)
