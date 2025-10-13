#!/usr/bin/env python3
"""
Integration tests for newly added Reading History endpoints:
- Export endpoint (JSON/CSV)
- Preferences endpoints (GET/PUT)
"""

import asyncio
import json
import csv
import io
from datetime import datetime
from uuid import uuid4

# Configure database for testing
import os
os.environ["DATABASE_URL"] = os.getenv("DATABASE_URL", "postgresql+asyncpg://rss_user:rss_password@localhost:5432/rss_feed_db")

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.user import User
from app.models.article import Article
from app.models.reading_history import ReadingHistory
from app.models.user_reading_preferences import UserReadingPreferences
from app.models.rss_source import RSSSource
from app.repositories.reading_history_repository import ReadingHistoryRepository
from app.repositories.reading_preferences_repository import ReadingPreferencesRepository
from app.services.reading_history_service import ReadingHistoryService


# Test database setup
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class TestNewEndpoints:
    """Integration tests for new endpoints."""
    
    def __init__(self):
        self.session = None
        self.test_user = None
        self.test_rss_source = None
        self.test_article1 = None
        self.test_article2 = None
        self.history_records = []
    
    async def setup(self):
        """Set up test environment."""
        print("🔧 Setting up test environment...")
        self.session = AsyncSessionLocal()
        
        # Create test user
        self.test_user = User(
            id=uuid4(),
            username=f"testuser_{uuid4().hex[:8]}",
            email=f"test_{uuid4().hex[:8]}@example.com",
            hashed_password="fakehash"
        )
        self.session.add(self.test_user)
        
        # Create test RSS source
        self.test_rss_source = RSSSource(
            id=uuid4(),
            name=f"Test Source {uuid4().hex[:8]}",
            url=f"https://example.com/feed_{uuid4().hex[:8]}.xml",
            category="technology",
            enabled=True
        )
        self.session.add(self.test_rss_source)
        
        # Create test articles
        unique_url1 = f"https://example.com/article1_{uuid4().hex[:8]}"
        unique_url2 = f"https://example.com/article2_{uuid4().hex[:8]}"
        
        self.test_article1 = Article(
            id=uuid4(),
            rss_source_id=self.test_rss_source.id,
            title="Test Article 1 - Tech News",
            url=unique_url1,
            url_hash=unique_url1,  # Simple hash for testing
            category="technology",
            published_date=datetime.utcnow()
        )
        self.test_article2 = Article(
            id=uuid4(),
            rss_source_id=self.test_rss_source.id,
            title="Test Article 2 - Science News",
            url=unique_url2,
            url_hash=unique_url2,  # Simple hash for testing
            category="science",
            published_date=datetime.utcnow()
        )
        self.session.add(self.test_article1)
        self.session.add(self.test_article2)
        
        await self.session.commit()
        await self.session.refresh(self.test_user)
        await self.session.refresh(self.test_rss_source)
        await self.session.refresh(self.test_article1)
        await self.session.refresh(self.test_article2)
        
        print(f"✅ Test user created: {self.test_user.username}")
        print(f"✅ Test RSS source created: {self.test_rss_source.name}")
        print(f"✅ Test articles created: {self.test_article1.id}, {self.test_article2.id}")
    
    async def teardown(self):
        """Clean up test data."""
        print("\n🧹 Cleaning up test data...")
        
        # Delete reading history
        if self.test_user:
            await self.session.execute(
                delete(ReadingHistory).where(ReadingHistory.user_id == self.test_user.id)
            )
            await self.session.execute(
                delete(UserReadingPreferences).where(UserReadingPreferences.user_id == self.test_user.id)
            )
            await self.session.delete(self.test_user)
        
        # Delete articles
        if self.test_article1:
            await self.session.delete(self.test_article1)
        if self.test_article2:
            await self.session.delete(self.test_article2)
        
        # Delete RSS source
        if self.test_rss_source:
            await self.session.delete(self.test_rss_source)
        
        await self.session.commit()
        await self.session.close()
        print("✅ Cleanup complete")
    
    async def create_test_history(self):
        """Create some test reading history."""
        print("\n📝 Creating test reading history...")
        
        service = ReadingHistoryService(self.session)
        
        # Record 3 views
        for i in range(3):
            article = self.test_article1 if i % 2 == 0 else self.test_article2
            history = await service.record_view(
                user_id=str(self.test_user.id),
                article_id=str(article.id),
                duration_seconds=60 + i * 30,
                scroll_percentage=75.5 + i * 5
            )
            self.history_records.append(history)
            print(f"  ✅ Recorded view {i+1}: {article.title[:30]}...")
        
        print(f"✅ Created {len(self.history_records)} history records")
    
    async def test_export_json(self):
        """Test JSON export endpoint logic."""
        print("\n" + "="*60)
        print("TEST 1: Export History as JSON")
        print("="*60)
        
        service = ReadingHistoryService(self.session)
        
        try:
            content, filename = await service.export_history(
                user_id=str(self.test_user.id),
                format="json",
                include_articles=True
            )
            
            # Parse JSON
            data = json.loads(content)
            
            print(f"✅ Export successful")
            print(f"  - Filename: {filename}")
            print(f"  - Total records: {data['total_records']}")
            print(f"  - Export date: {data['export_date']}")
            
            # Validate structure
            assert "export_date" in data, "Missing export_date"
            assert "total_records" in data, "Missing total_records"
            assert "records" in data, "Missing records"
            assert data["total_records"] == len(self.history_records), "Record count mismatch"
            
            # Validate record structure
            if data["records"]:
                record = data["records"][0]
                assert "id" in record, "Missing record id"
                assert "viewed_at" in record, "Missing viewed_at"
                assert "duration_seconds" in record, "Missing duration_seconds"
                assert "article" in record, "Missing article details"
                assert "title" in record["article"], "Missing article title"
                
                print(f"  - Sample record: {record['article']['title'][:40]}...")
            
            print("✅ JSON export test PASSED")
            return True
            
        except Exception as e:
            print(f"❌ JSON export test FAILED: {e}")
            return False
    
    async def test_export_csv(self):
        """Test CSV export endpoint logic."""
        print("\n" + "="*60)
        print("TEST 2: Export History as CSV")
        print("="*60)
        
        service = ReadingHistoryService(self.session)
        
        try:
            content, filename = await service.export_history(
                user_id=str(self.test_user.id),
                format="csv",
                include_articles=True
            )
            
            print(f"✅ Export successful")
            print(f"  - Filename: {filename}")
            
            # Parse CSV
            csv_file = io.StringIO(content)
            reader = csv.DictReader(csv_file)
            rows = list(reader)
            
            print(f"  - Total rows: {len(rows)}")
            
            # Validate structure
            assert len(rows) == len(self.history_records), "Row count mismatch"
            
            # Validate headers
            expected_headers = ['viewed_at', 'duration_seconds', 'scroll_percentage', 
                              'article_title', 'article_url', 'article_category', 'article_published_date']
            actual_headers = list(rows[0].keys())
            
            for header in expected_headers:
                assert header in actual_headers, f"Missing header: {header}"
            
            # Validate data
            if rows:
                row = rows[0]
                print(f"  - Sample row: {row['article_title'][:40]}...")
                assert row['viewed_at'], "Missing viewed_at"
                assert row['article_title'], "Missing article_title"
            
            print("✅ CSV export test PASSED")
            return True
            
        except Exception as e:
            print(f"❌ CSV export test FAILED: {e}")
            return False
    
    async def test_get_preferences(self):
        """Test get preferences endpoint logic."""
        print("\n" + "="*60)
        print("TEST 3: Get User Preferences")
        print("="*60)
        
        service = ReadingHistoryService(self.session)
        
        try:
            # Get or create preferences
            prefs = await service.get_user_preferences(str(self.test_user.id))
            
            print(f"✅ Preferences retrieved")
            print(f"  - User ID: {prefs.user_id}")
            print(f"  - Tracking enabled: {prefs.tracking_enabled}")
            print(f"  - Retention days: {prefs.retention_days}")
            print(f"  - Exclude categories: {prefs.exclude_categories}")
            
            # Validate structure
            assert prefs.user_id == self.test_user.id, "User ID mismatch"
            assert isinstance(prefs.tracking_enabled, bool), "tracking_enabled not bool"
            assert isinstance(prefs.retention_days, int), "retention_days not int"
            assert prefs.retention_days == 365, "Default retention days incorrect"
            assert prefs.exclude_categories == [], "Default exclude_categories incorrect"
            
            print("✅ Get preferences test PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Get preferences test FAILED: {e}")
            return False
    
    async def test_update_preferences(self):
        """Test update preferences endpoint logic."""
        print("\n" + "="*60)
        print("TEST 4: Update User Preferences")
        print("="*60)
        
        service = ReadingHistoryService(self.session)
        
        try:
            # Update preferences
            prefs = await service.update_user_preferences(
                user_id=str(self.test_user.id),
                tracking_enabled=False,
                retention_days=180,
                exclude_categories=["sports", "entertainment"]
            )
            
            print(f"✅ Preferences updated")
            print(f"  - Tracking enabled: {prefs.tracking_enabled}")
            print(f"  - Retention days: {prefs.retention_days}")
            print(f"  - Exclude categories: {prefs.exclude_categories}")
            
            # Validate updates
            assert prefs.tracking_enabled is False, "tracking_enabled not updated"
            assert prefs.retention_days == 180, "retention_days not updated"
            assert "sports" in prefs.exclude_categories, "exclude_categories not updated"
            assert "entertainment" in prefs.exclude_categories, "exclude_categories not updated"
            
            # Test should_track_reading
            should_track = await service.should_track_reading(
                user_id=str(self.test_user.id),
                category="technology"
            )
            print(f"  - Should track 'technology': {should_track}")
            assert should_track is False, "should_track_reading incorrect (tracking disabled)"
            
            # Re-enable tracking
            prefs = await service.update_user_preferences(
                user_id=str(self.test_user.id),
                tracking_enabled=True
            )
            
            # Test category exclusion
            should_track_tech = await service.should_track_reading(
                user_id=str(self.test_user.id),
                category="technology"
            )
            should_track_sports = await service.should_track_reading(
                user_id=str(self.test_user.id),
                category="sports"
            )
            
            print(f"  - Should track 'technology': {should_track_tech}")
            print(f"  - Should track 'sports': {should_track_sports}")
            
            assert should_track_tech is True, "Technology should be tracked"
            assert should_track_sports is False, "Sports should not be tracked (excluded)"
            
            print("✅ Update preferences test PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Update preferences test FAILED: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all integration tests."""
        print("\n" + "="*70)
        print("🧪 READING HISTORY - NEW ENDPOINTS INTEGRATION TESTS")
        print("="*70)
        
        results = []
        
        try:
            await self.setup()
            await self.create_test_history()
            
            # Run tests
            results.append(("Export JSON", await self.test_export_json()))
            results.append(("Export CSV", await self.test_export_csv()))
            results.append(("Get Preferences", await self.test_get_preferences()))
            results.append(("Update Preferences", await self.test_update_preferences()))
            
        finally:
            await self.teardown()
        
        # Print summary
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests PASSED! New endpoints are working correctly.")
            return True
        else:
            print(f"\n⚠️  {total - passed} test(s) FAILED. Please review.")
            return False


async def main():
    """Main test runner."""
    tester = TestNewEndpoints()
    success = await tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
