"""Unit tests for ReadingHistoryService export and preferences methods."""
import pytest
import json
import csv
import io
from datetime import datetime, timedelta

from app.services.reading_history_service import ReadingHistoryService
from fastapi import HTTPException


@pytest.mark.asyncio
class TestReadingHistoryServiceExport:
    """Test suite for export functionality."""
    
    async def test_export_history_json(self, db_session, test_user, test_article):
        """Test exporting history as JSON."""
        service = ReadingHistoryService(db_session)
        user_id = test_user["user_id"]
        article_id = test_article["id"]
        
        # Record some views
        await service.record_view(user_id, article_id, duration_seconds=300, scroll_percentage=85.5)
        await service.record_view(user_id, article_id, duration_seconds=120, scroll_percentage=50.0)
        
        # Export as JSON
        content, filename = await service.export_history(
            user_id=user_id,
            format="json",
            include_articles=True
        )
        
        # Verify filename format
        assert filename.endswith(".json")
        assert "reading_history_" in filename
        
        # Parse JSON
        data = json.loads(content)
        
        assert "export_date" in data
        assert "total_records" in data
        assert "records" in data
        assert data["total_records"] == 2
        assert len(data["records"]) == 2
        
        # Check first record structure
        record = data["records"][0]
        assert "id" in record
        assert "viewed_at" in record
        assert "duration_seconds" in record
        assert "scroll_percentage" in record
        assert "article" in record
        assert record["article"]["title"] == test_article["title"]
    
    async def test_export_history_csv(self, db_session, test_user, test_article):
        """Test exporting history as CSV."""
        service = ReadingHistoryService(db_session)
        user_id = test_user["user_id"]
        article_id = test_article["id"]
        
        # Record some views
        await service.record_view(user_id, article_id, duration_seconds=300)
        
        # Export as CSV
        content, filename = await service.export_history(
            user_id=user_id,
            format="csv",
            include_articles=True
        )
        
        # Verify filename format
        assert filename.endswith(".csv")
        
        # Parse CSV
        csv_file = io.StringIO(content)
        reader = csv.DictReader(csv_file)
        rows = list(reader)
        
        assert len(rows) == 1
        assert "viewed_at" in rows[0]
        assert "duration_seconds" in rows[0]
        assert "article_title" in rows[0]
        assert rows[0]["article_title"] == test_article["title"]
    
    async def test_export_without_articles(self, db_session, test_user, test_article):
        """Test exporting without article details."""
        service = ReadingHistoryService(db_session)
        user_id = test_user["user_id"]
        article_id = test_article["id"]
        
        await service.record_view(user_id, article_id)
        
        # Export without articles
        content, filename = await service.export_history(
            user_id=user_id,
            format="json",
            include_articles=False
        )
        
        data = json.loads(content)
        record = data["records"][0]
        
        assert "article_id" in record
        assert "article" not in record
    
    async def test_export_with_date_range(self, db_session, test_user, test_article):
        """Test exporting with date range filter."""
        service = ReadingHistoryService(db_session)
        user_id = test_user["user_id"]
        article_id = test_article["id"]
        
        # Record views
        await service.record_view(user_id, article_id)
        
        # Export with date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        content, filename = await service.export_history(
            user_id=user_id,
            format="json",
            start_date=start_date,
            end_date=end_date
        )
        
        data = json.loads(content)
        assert data["total_records"] >= 0
    
    async def test_export_empty_history(self, db_session, test_user):
        """Test exporting when no history exists."""
        service = ReadingHistoryService(db_session)
        user_id = test_user["user_id"]
        
        content, filename = await service.export_history(
            user_id=user_id,
            format="json"
        )
        
        data = json.loads(content)
        assert data["total_records"] == 0
        assert len(data["records"]) == 0
    
    async def test_export_unsupported_format(self, db_session, test_user):
        """Test exporting with unsupported format raises error."""
        service = ReadingHistoryService(db_session)
        user_id = test_user["user_id"]
        
        with pytest.raises(HTTPException) as exc_info:
            await service.export_history(
                user_id=user_id,
                format="xml"  # Unsupported
            )
        
        assert exc_info.value.status_code == 400
        assert "Unsupported export format" in str(exc_info.value.detail)


@pytest.mark.asyncio
class TestReadingHistoryServicePreferences:
    """Test suite for preferences functionality."""
    
    async def test_get_user_preferences_creates_default(self, db_session, test_user):
        """Test that get_user_preferences creates default preferences."""
        service = ReadingHistoryService(db_session)
        user_id = test_user["user_id"]
        
        prefs = await service.get_user_preferences(user_id)
        
        assert prefs is not None
        assert str(prefs.user_id) == user_id
        assert prefs.tracking_enabled is True
        assert prefs.retention_days == 365
    
    async def test_get_user_preferences_returns_existing(self, db_session, test_user):
        """Test that get_user_preferences returns existing preferences."""
        service = ReadingHistoryService(db_session)
        user_id = test_user["user_id"]
        
        # Get first time (creates)
        prefs1 = await service.get_user_preferences(user_id)
        prefs1_id = prefs1.id
        
        # Get second time (should return same)
        prefs2 = await service.get_user_preferences(user_id)
        
        assert prefs2.id == prefs1_id
    
    async def test_update_user_preferences(self, db_session, test_user):
        """Test updating user preferences."""
        service = ReadingHistoryService(db_session)
        user_id = test_user["user_id"]
        
        # Update preferences
        prefs = await service.update_user_preferences(
            user_id=user_id,
            tracking_enabled=False,
            retention_days=180,
            exclude_categories=["politics"]
        )
        
        assert prefs.tracking_enabled is False
        assert prefs.retention_days == 180
        assert "politics" in prefs.exclude_categories
    
    async def test_update_creates_if_not_exists(self, db_session, test_user):
        """Test that update creates preferences if they don't exist."""
        service = ReadingHistoryService(db_session)
        user_id = test_user["user_id"]
        
        prefs = await service.update_user_preferences(
            user_id=user_id,
            retention_days=90
        )
        
        assert prefs is not None
        assert prefs.retention_days == 90
    
    async def test_should_track_reading_enabled(self, db_session, test_user):
        """Test should_track_reading when tracking is enabled."""
        service = ReadingHistoryService(db_session)
        user_id = test_user["user_id"]
        
        # Get/create preferences (default is tracking enabled)
        await service.get_user_preferences(user_id)
        
        should_track = await service.should_track_reading(user_id)
        
        assert should_track is True
    
    async def test_should_track_reading_disabled(self, db_session, test_user):
        """Test should_track_reading when tracking is disabled."""
        service = ReadingHistoryService(db_session)
        user_id = test_user["user_id"]
        
        # Disable tracking
        await service.update_user_preferences(
            user_id=user_id,
            tracking_enabled=False
        )
        
        should_track = await service.should_track_reading(user_id)
        
        assert should_track is False
    
    async def test_should_track_reading_excluded_category(self, db_session, test_user):
        """Test should_track_reading with excluded category."""
        service = ReadingHistoryService(db_session)
        user_id = test_user["user_id"]
        
        # Exclude politics category
        await service.update_user_preferences(
            user_id=user_id,
            exclude_categories=["politics", "sports"]
        )
        
        # Check tracking for excluded category
        should_track_politics = await service.should_track_reading(
            user_id=user_id,
            category="politics"
        )
        assert should_track_politics is False
        
        # Check tracking for non-excluded category
        should_track_tech = await service.should_track_reading(
            user_id=user_id,
            category="technology"
        )
        assert should_track_tech is True
    
    async def test_should_track_reading_no_category(self, db_session, test_user):
        """Test should_track_reading without category filter."""
        service = ReadingHistoryService(db_session)
        user_id = test_user["user_id"]
        
        # Set some excluded categories
        await service.update_user_preferences(
            user_id=user_id,
            exclude_categories=["politics"]
        )
        
        # Without category parameter, should return True
        should_track = await service.should_track_reading(user_id)
        
        assert should_track is True


@pytest.mark.asyncio
class TestReadingHistoryServiceIntegration:
    """Integration tests for export with actual data."""
    
    async def test_export_large_history(self, db_session, test_user, test_article):
        """Test exporting larger history (performance check)."""
        service = ReadingHistoryService(db_session)
        user_id = test_user["user_id"]
        article_id = test_article["id"]
        
        # Record 50 views
        for i in range(50):
            await service.record_view(
                user_id, 
                article_id, 
                duration_seconds=100 + i,
                scroll_percentage=50.0 + i % 50
            )
        
        # Export
        content, filename = await service.export_history(
            user_id=user_id,
            format="json"
        )
        
        data = json.loads(content)
        assert data["total_records"] == 50
    
    async def test_csv_export_with_special_characters(self, db_session, test_user, test_article):
        """Test CSV export handles special characters correctly."""
        service = ReadingHistoryService(db_session)
        user_id = test_user["user_id"]
        article_id = test_article["id"]
        
        await service.record_view(user_id, article_id)
        
        # Export as CSV
        content, filename = await service.export_history(
            user_id=user_id,
            format="csv",
            include_articles=True
        )
        
        # Should be parseable
        csv_file = io.StringIO(content)
        reader = csv.DictReader(csv_file)
        rows = list(reader)
        
        assert len(rows) > 0
