# Reading History Enhancements - Implementation Plan

**Date:** 2025-10-10 21:06 UTC  
**Scope:** Option B (Export + Privacy) + Option C (Analytics)  
**Timeline:** 7-10 days total  
**Approach:** Step-by-step, test-driven, modular implementation

---

## 📋 **Table of Contents**

1. [Overview & Architecture](#overview--architecture)
2. [Database Changes](#database-changes)
3. [Option B Implementation](#option-b-implementation)
4. [Option C Implementation](#option-c-implementation)
5. [Testing Strategy](#testing-strategy)
6. [Integration Plan](#integration-plan)
7. [Deployment Checklist](#deployment-checklist)

---

## 🎯 **Overview & Architecture**

### **Design Principles**

1. **Modularity** - Each feature is self-contained and can be deployed independently
2. **Backward Compatibility** - All existing endpoints remain unchanged
3. **Performance** - Efficient queries with proper indexes
4. **Security** - User-scoped data access, authentication required
5. **Testability** - 100% test coverage for all new code

### **Feature Breakdown**

```
Option B (2-3 days):
├── Export History (1 day)
│   ├── JSON format export
│   ├── CSV format export
│   └── Background job for large exports
└── Privacy Controls (1-2 days)
    ├── User preferences model
    ├── Settings endpoints
    └── Privacy enforcement

Option C (4-5 days):
├── Reading Patterns (1.5 days)
│   ├── Time-based analysis
│   ├── Category distribution
│   └── Reading streaks
├── Reading Trends (1.5 days)
│   ├── Time-series data
│   ├── Engagement trends
│   └── Category trends
├── Export (shared with Option B)
└── History Search (1.5 days)
    ├── Full-text search
    ├── Filtering
    └── Relevance ranking
```

### **Technology Stack**

- **Database:** PostgreSQL (existing)
- **ORM:** SQLAlchemy with async support
- **Export:** Python CSV module + JSON
- **Search:** PostgreSQL full-text search (existing TSVECTOR)
- **Testing:** pytest with async support

---

## 💾 **Database Changes**

### **Migration 1: User Reading Preferences Table**

**Purpose:** Store user privacy and reading preferences

**File:** `alembic/versions/XXXX_add_user_reading_preferences.py`

```python
"""add user reading preferences table

Revision ID: XXXX
Revises: [previous_migration_id]
Create Date: 2025-10-10 21:06:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers
revision = 'XXXX'
down_revision = '[previous_migration_id]'
branch_labels = None
depends_on = None


def upgrade():
    # Create user_reading_preferences table
    op.create_table(
        'user_reading_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        
        # Tracking preferences
        sa.Column('tracking_enabled', sa.Boolean, default=True, nullable=False),
        sa.Column('analytics_opt_in', sa.Boolean, default=True, nullable=False),
        
        # Auto-cleanup settings
        sa.Column('auto_cleanup_enabled', sa.Boolean, default=False, nullable=False),
        sa.Column('retention_days', sa.Integer, default=365, nullable=False),
        
        # Privacy settings
        sa.Column('exclude_categories', postgresql.ARRAY(sa.String), default=[], nullable=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_user_reading_preferences_user_id', 'user_reading_preferences', ['user_id'])
    
    # Add check constraint for retention_days
    op.create_check_constraint(
        'ck_retention_days_positive',
        'user_reading_preferences',
        'retention_days > 0 AND retention_days <= 3650'
    )


def downgrade():
    op.drop_index('ix_user_reading_preferences_user_id')
    op.drop_table('user_reading_preferences')
```

**Verification:**
```sql
-- Check table exists
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name = 'user_reading_preferences';

-- Check columns
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'user_reading_preferences';

-- Check indexes
SELECT indexname FROM pg_indexes 
WHERE tablename = 'user_reading_preferences';
```

---

## 🔧 **Option B Implementation**

### **Phase B1: User Reading Preferences Model**

**File:** `app/models/user_reading_preferences.py`

```python
"""User reading preferences model."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Boolean, Integer, ARRAY, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.session import Base


class UserReadingPreferences(Base):
    """User preferences for reading history tracking and privacy."""
    
    __tablename__ = "user_reading_preferences"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        unique=True,
        index=True
    )
    
    # Tracking preferences
    tracking_enabled = Column(Boolean, default=True, nullable=False)
    analytics_opt_in = Column(Boolean, default=True, nullable=False)
    
    # Auto-cleanup settings
    auto_cleanup_enabled = Column(Boolean, default=False, nullable=False)
    retention_days = Column(Integer, default=365, nullable=False)
    
    # Privacy settings
    exclude_categories = Column(ARRAY(String), default=[], nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="reading_preferences")
    
    def __repr__(self):
        return f"<UserReadingPreferences(user_id='{self.user_id}', tracking_enabled={self.tracking_enabled})>"
```

**Update User Model:**

**File:** `app/models/user.py` (add to existing)

```python
# Add to User model relationships:
reading_preferences = relationship(
    "UserReadingPreferences", 
    back_populates="user", 
    uselist=False,
    cascade="all, delete-orphan"
)
```

---

### **Phase B2: Preferences Schemas**

**File:** `app/schemas/reading_preferences.py`

```python
"""Schemas for user reading preferences."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class ReadingPreferencesBase(BaseModel):
    """Base schema for reading preferences."""
    tracking_enabled: bool = Field(True, description="Enable reading history tracking")
    analytics_opt_in: bool = Field(True, description="Opt-in to analytics")
    auto_cleanup_enabled: bool = Field(False, description="Enable automatic cleanup")
    retention_days: int = Field(365, ge=1, le=3650, description="Days to retain history (1-3650)")
    exclude_categories: List[str] = Field(default_factory=list, description="Categories to exclude from tracking")


class ReadingPreferencesCreate(ReadingPreferencesBase):
    """Schema for creating preferences."""
    pass


class ReadingPreferencesUpdate(BaseModel):
    """Schema for updating preferences (all fields optional)."""
    tracking_enabled: Optional[bool] = None
    analytics_opt_in: Optional[bool] = None
    auto_cleanup_enabled: Optional[bool] = None
    retention_days: Optional[int] = Field(None, ge=1, le=3650)
    exclude_categories: Optional[List[str]] = None
    
    @validator('retention_days')
    def validate_retention_days(cls, v):
        if v is not None and (v < 1 or v > 3650):
            raise ValueError('retention_days must be between 1 and 3650')
        return v


class ReadingPreferencesResponse(ReadingPreferencesBase):
    """Schema for reading preferences response."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
        
    @classmethod
    def from_orm_preferences(cls, prefs):
        """Convert ORM model to response schema."""
        return cls(
            id=str(prefs.id),
            user_id=str(prefs.user_id),
            tracking_enabled=prefs.tracking_enabled,
            analytics_opt_in=prefs.analytics_opt_in,
            auto_cleanup_enabled=prefs.auto_cleanup_enabled,
            retention_days=prefs.retention_days,
            exclude_categories=prefs.exclude_categories or [],
            created_at=prefs.created_at,
            updated_at=prefs.updated_at
        )
```

---

### **Phase B3: Export Schemas**

**File:** `app/schemas/reading_history.py` (add to existing)

```python
"""Add export schemas to existing file."""
from enum import Enum
from typing import Optional


class ExportFormat(str, Enum):
    """Export format options."""
    JSON = "json"
    CSV = "csv"


class ExportHistoryRequest(BaseModel):
    """Schema for history export request."""
    format: ExportFormat = Field(ExportFormat.JSON, description="Export format")
    start_date: Optional[datetime] = Field(None, description="Start date for export range")
    end_date: Optional[datetime] = Field(None, description="End date for export range")
    include_articles: bool = Field(True, description="Include full article details")


class ExportHistoryResponse(BaseModel):
    """Schema for export response."""
    export_format: str
    records_count: int
    file_name: str
    generated_at: datetime
    file_content: Optional[str] = None  # Base64 for small exports
    download_url: Optional[str] = None  # For large exports
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

---

### **Phase B4: Preferences Repository**

**File:** `app/repositories/reading_preferences_repository.py`

```python
"""Repository for user reading preferences."""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_reading_preferences import UserReadingPreferences


class ReadingPreferencesRepository:
    """Repository for reading preferences operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_user_id(self, user_id: UUID) -> Optional[UserReadingPreferences]:
        """Get preferences for a user."""
        result = await self.db.execute(
            select(UserReadingPreferences)
            .where(UserReadingPreferences.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create(self, user_id: UUID, **kwargs) -> UserReadingPreferences:
        """Create preferences for a user."""
        prefs = UserReadingPreferences(user_id=user_id, **kwargs)
        self.db.add(prefs)
        await self.db.flush()
        await self.db.refresh(prefs)
        return prefs
    
    async def update(
        self, 
        user_id: UUID, 
        **kwargs
    ) -> Optional[UserReadingPreferences]:
        """Update preferences for a user."""
        prefs = await self.get_by_user_id(user_id)
        if not prefs:
            return None
        
        for key, value in kwargs.items():
            if value is not None and hasattr(prefs, key):
                setattr(prefs, key, value)
        
        await self.db.flush()
        await self.db.refresh(prefs)
        return prefs
    
    async def get_or_create(self, user_id: UUID) -> UserReadingPreferences:
        """Get existing preferences or create default ones."""
        prefs = await self.get_by_user_id(user_id)
        if not prefs:
            prefs = await self.create(user_id=user_id)
        return prefs
```

---

### **Phase B5: Export & Preferences Service Methods**

**File:** `app/services/reading_history_service.py` (add methods)

```python
"""Add export and preferences methods to existing service."""
import csv
import json
import io
from datetime import datetime, timedelta
from typing import Tuple, Optional

# Add new imports
from app.repositories.reading_preferences_repository import ReadingPreferencesRepository
from app.models.user_reading_preferences import UserReadingPreferences


class ReadingHistoryService:
    """Extended service with export and preferences."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.history_repo = ReadingHistoryRepository(session)
        self.article_repo = ArticleRepository(session)
        self.preferences_repo = ReadingPreferencesRepository(session)  # NEW
    
    # ... existing methods ...
    
    async def export_history(
        self,
        user_id: str,
        format: str = "json",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_articles: bool = True
    ) -> Tuple[str, str]:
        """
        Export reading history in specified format.
        
        Returns:
            Tuple of (content, filename)
        """
        # Get all history (no pagination for export)
        history_list, total = await self.history_repo.get_user_history(
            user_id=user_id,
            skip=0,
            limit=10000,  # Max export limit
            start_date=start_date,
            end_date=end_date
        )
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"reading_history_{timestamp}.{format}"
        
        if format == "json":
            content = self._export_json(history_list, include_articles)
        elif format == "csv":
            content = self._export_csv(history_list, include_articles)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported export format: {format}"
            )
        
        return content, filename
    
    def _export_json(self, history_list: List[ReadingHistory], include_articles: bool) -> str:
        """Export history as JSON."""
        data = []
        for h in history_list:
            item = {
                "id": str(h.id),
                "viewed_at": h.viewed_at.isoformat(),
                "duration_seconds": h.duration_seconds,
                "scroll_percentage": float(h.scroll_percentage) if h.scroll_percentage else None,
            }
            
            if include_articles and h.article:
                item["article"] = {
                    "id": str(h.article.id),
                    "title": h.article.title,
                    "url": h.article.url,
                    "category": h.article.category,
                    "published_date": h.article.published_date.isoformat() if h.article.published_date else None,
                }
            else:
                item["article_id"] = str(h.article_id)
            
            data.append(item)
        
        export_data = {
            "export_date": datetime.utcnow().isoformat(),
            "total_records": len(data),
            "records": data
        }
        
        return json.dumps(export_data, indent=2)
    
    def _export_csv(self, history_list: List[ReadingHistory], include_articles: bool) -> str:
        """Export history as CSV."""
        output = io.StringIO()
        
        if include_articles:
            fieldnames = [
                'viewed_at', 'duration_seconds', 'scroll_percentage',
                'article_title', 'article_url', 'article_category', 'article_published_date'
            ]
        else:
            fieldnames = ['article_id', 'viewed_at', 'duration_seconds', 'scroll_percentage']
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for h in history_list:
            if include_articles and h.article:
                row = {
                    'viewed_at': h.viewed_at.isoformat(),
                    'duration_seconds': h.duration_seconds or '',
                    'scroll_percentage': h.scroll_percentage or '',
                    'article_title': h.article.title,
                    'article_url': h.article.url,
                    'article_category': h.article.category,
                    'article_published_date': h.article.published_date.isoformat() if h.article.published_date else ''
                }
            else:
                row = {
                    'article_id': str(h.article_id),
                    'viewed_at': h.viewed_at.isoformat(),
                    'duration_seconds': h.duration_seconds or '',
                    'scroll_percentage': h.scroll_percentage or ''
                }
            
            writer.writerow(row)
        
        return output.getvalue()
    
    # Preferences methods
    
    async def get_user_preferences(self, user_id: str) -> UserReadingPreferences:
        """Get or create user reading preferences."""
        return await self.preferences_repo.get_or_create(user_id=user_id)
    
    async def update_user_preferences(
        self,
        user_id: str,
        **kwargs
    ) -> UserReadingPreferences:
        """Update user reading preferences."""
        prefs = await self.preferences_repo.update(user_id=user_id, **kwargs)
        
        if not prefs:
            # Create if doesn't exist
            prefs = await self.preferences_repo.create(user_id=user_id, **kwargs)
        
        await self.session.commit()
        await self.session.refresh(prefs)
        
        return prefs
    
    async def should_track_reading(
        self,
        user_id: str,
        category: Optional[str] = None
    ) -> bool:
        """Check if reading should be tracked based on user preferences."""
        prefs = await self.get_user_preferences(user_id)
        
        # Check if tracking is enabled
        if not prefs.tracking_enabled:
            return False
        
        # Check if category is excluded
        if category and category in prefs.exclude_categories:
            return False
        
        return True
```

---

### **Phase B6: Privacy & Export Endpoints**

**File:** `app/api/v1/endpoints/reading_history.py` (add endpoints)

```python
"""Add export and preferences endpoints to existing router."""
from fastapi.responses import Response

# Add new imports
from app.schemas.reading_preferences import (
    ReadingPreferencesResponse,
    ReadingPreferencesUpdate,
)
from app.schemas.reading_history import (
    ExportHistoryRequest,
    ExportHistoryResponse,
)


# Export endpoint
@router.post(
    "/export",
    response_model=ExportHistoryResponse,
    summary="Export reading history",
    description="Export reading history in JSON or CSV format. Supports date range filtering."
)
async def export_history(
    request: ExportHistoryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export user's reading history."""
    service = ReadingHistoryService(db)
    
    # Validate date range
    if request.start_date and request.end_date and request.start_date > request.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date"
        )
    
    # Export history
    content, filename = await service.export_history(
        user_id=current_user.id,
        format=request.format.value,
        start_date=request.start_date,
        end_date=request.end_date,
        include_articles=request.include_articles
    )
    
    # Get record count
    _, total = await service.get_user_history(
        user_id=current_user.id,
        skip=0,
        limit=1,
        start_date=request.start_date,
        end_date=request.end_date
    )
    
    # For small exports, return content directly
    # For large exports (>1MB), you'd return a download URL
    return ExportHistoryResponse(
        export_format=request.format.value,
        records_count=total,
        file_name=filename,
        generated_at=datetime.utcnow(),
        file_content=content if len(content) < 1_000_000 else None,
        download_url=None  # Implement for large files
    )


# Download export endpoint
@router.get(
    "/export/download/{filename}",
    summary="Download exported history file",
    description="Download a previously exported history file."
)
async def download_export(
    filename: str,
    format: str = Query("json", regex="^(json|csv)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Download export file."""
    service = ReadingHistoryService(db)
    
    # Generate export
    content, _ = await service.export_history(
        user_id=current_user.id,
        format=format
    )
    
    # Determine media type
    media_type = "application/json" if format == "json" else "text/csv"
    
    # Return as downloadable file
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


# Preferences endpoints
@router.get(
    "/preferences",
    response_model=ReadingPreferencesResponse,
    summary="Get reading preferences",
    description="Get current user's reading history preferences and privacy settings."
)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's reading preferences."""
    service = ReadingHistoryService(db)
    prefs = await service.get_user_preferences(user_id=current_user.id)
    
    return ReadingPreferencesResponse.from_orm_preferences(prefs)


@router.patch(
    "/preferences",
    response_model=ReadingPreferencesResponse,
    summary="Update reading preferences",
    description="Update reading history preferences and privacy settings."
)
async def update_preferences(
    updates: ReadingPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user's reading preferences."""
    service = ReadingHistoryService(db)
    
    # Get update dict, excluding None values
    update_data = updates.dict(exclude_none=True)
    
    # Update preferences
    prefs = await service.update_user_preferences(
        user_id=current_user.id,
        **update_data
    )
    
    return ReadingPreferencesResponse.from_orm_preferences(prefs)
```

**Test Option B endpoints:**

```bash
# Test export JSON
curl -X POST "http://localhost:8000/api/v1/reading-history/export" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"format": "json", "include_articles": true}'

# Test export CSV
curl -X POST "http://localhost:8000/api/v1/reading-history/export" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"format": "csv"}'

# Get preferences
curl "http://localhost:8000/api/v1/reading-history/preferences" \
  -H "Authorization: Bearer $TOKEN"

# Update preferences
curl -X PATCH "http://localhost:8000/api/v1/reading-history/preferences" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tracking_enabled": false, "retention_days": 90}'
```

---

## 📊 **Option C Implementation**

### **Phase C1: Analytics Repository Methods**

**File:** `app/repositories/reading_history_repository.py` (add methods)

```python
"""Add analytics methods to existing repository."""
from collections import defaultdict
from sqlalchemy import func, extract, case


class ReadingHistoryRepository:
    """Extended repository with analytics methods."""
    
    # ... existing methods ...
    
    async def get_reading_patterns(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get reading patterns analysis."""
        # Base query
        query = (
            select(
                extract('hour', ReadingHistory.viewed_at).label('hour'),
                extract('dow', ReadingHistory.viewed_at).label('day_of_week'),
                func.count().label('count')
            )
            .where(ReadingHistory.user_id == user_id)
            .group_by('hour', 'day_of_week')
        )
        
        if start_date:
            query = query.where(ReadingHistory.viewed_at >= start_date)
        if end_date:
            query = query.where(ReadingHistory.viewed_at <= end_date)
        
        result = await self.db.execute(query)
        patterns = result.all()
        
        # Organize by hour and day
        by_hour = defaultdict(int)
        by_weekday = defaultdict(int)
        
        for hour, dow, count in patterns:
            by_hour[int(hour)] += count
            by_weekday[int(dow)] += count
        
        return {
            'by_hour': dict(by_hour),
            'by_weekday': dict(by_weekday)
        }
    
    async def get_category_distribution(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get reading distribution by category."""
        from app.models.article import Article
        
        query = (
            select(
                Article.category,
                func.count().label('count'),
                func.avg(ReadingHistory.duration_seconds).label('avg_duration'),
                func.avg(ReadingHistory.scroll_percentage).label('avg_scroll')
            )
            .join(Article, ReadingHistory.article_id == Article.id)
            .where(ReadingHistory.user_id == user_id)
            .group_by(Article.category)
        )
        
        if start_date:
            query = query.where(ReadingHistory.viewed_at >= start_date)
        if end_date:
            query = query.where(ReadingHistory.viewed_at <= end_date)
        
        result = await self.db.execute(query)
        categories = result.all()
        
        return {
            cat: {
                'count': count,
                'avg_duration': float(avg_dur) if avg_dur else 0,
                'avg_scroll': float(avg_scroll) if avg_scroll else 0
            }
            for cat, count, avg_dur, avg_scroll in categories
        }
    
    async def get_reading_streak(self, user_id: UUID) -> dict:
        """Calculate current and longest reading streaks."""
        # Get all reading dates
        query = (
            select(func.date(ReadingHistory.viewed_at).label('date'))
            .where(ReadingHistory.user_id == user_id)
            .distinct()
            .order_by('date')
        )
        
        result = await self.db.execute(query)
        dates = [row[0] for row in result.all()]
        
        if not dates:
            return {'current_streak': 0, 'longest_streak': 0}
        
        # Calculate streaks
        current_streak = 0
        longest_streak = 0
        temp_streak = 1
        
        today = datetime.utcnow().date()
        
        # Check current streak
        if dates[-1] == today or dates[-1] == today - timedelta(days=1):
            current_streak = 1
            for i in range(len(dates) - 2, -1, -1):
                if (dates[i + 1] - dates[i]).days == 1:
                    current_streak += 1
                else:
                    break
        
        # Calculate longest streak
        for i in range(1, len(dates)):
            if (dates[i] - dates[i-1]).days == 1:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 1
        
        longest_streak = max(longest_streak, temp_streak, current_streak)
        
        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'total_reading_days': len(dates)
        }
    
    async def get_daily_trends(
        self,
        user_id: UUID,
        days: int = 30
    ) -> List[dict]:
        """Get daily reading trends."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = (
            select(
                func.date(ReadingHistory.viewed_at).label('date'),
                func.count().label('article_count'),
                func.sum(ReadingHistory.duration_seconds).label('total_duration'),
                func.avg(ReadingHistory.scroll_percentage).label('avg_scroll')
            )
            .where(
                ReadingHistory.user_id == user_id,
                ReadingHistory.viewed_at >= start_date
            )
            .group_by('date')
            .order_by('date')
        )
        
        result = await self.db.execute(query)
        trends = result.all()
        
        return [
            {
                'date': date.isoformat(),
                'article_count': count,
                'total_duration': total_dur or 0,
                'avg_scroll': float(avg_scroll) if avg_scroll else 0
            }
            for date, count, total_dur, avg_scroll in trends
        ]
    
    async def get_top_sources(
        self,
        user_id: UUID,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[dict]:
        """Get top RSS sources by reading count."""
        from app.models.article import Article
        from app.models.rss_source import RSSSource
        
        query = (
            select(
                RSSSource.name,
                RSSSource.id,
                func.count().label('article_count'),
                func.avg(ReadingHistory.duration_seconds).label('avg_duration')
            )
            .join(Article, ReadingHistory.article_id == Article.id)
            .join(RSSSource, Article.rss_source_id == RSSSource.id)
            .where(ReadingHistory.user_id == user_id)
            .group_by(RSSSource.id, RSSSource.name)
            .order_by(func.count().desc())
            .limit(limit)
        )
        
        if start_date:
            query = query.where(ReadingHistory.viewed_at >= start_date)
        if end_date:
            query = query.where(ReadingHistory.viewed_at <= end_date)
        
        result = await self.db.execute(query)
        sources = result.all()
        
        return [
            {
                'source_id': str(source_id),
                'source_name': name,
                'article_count': count,
                'avg_duration': float(avg_dur) if avg_dur else 0
            }
            for name, source_id, count, avg_dur in sources
        ]
    
    async def search_history(
        self,
        user_id: UUID,
        query: str,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[ReadingHistory], int]:
        """Search through reading history."""
        from app.models.article import Article
        
        # Use PostgreSQL full-text search
        search_query = (
            select(ReadingHistory)
            .join(Article, ReadingHistory.article_id == Article.id)
            .where(
                ReadingHistory.user_id == user_id,
                Article.search_vector.match(query)
            )
            .options(selectinload(ReadingHistory.article))
            .order_by(desc(ReadingHistory.viewed_at))
        )
        
        # Count query
        count_query = (
            select(func.count())
            .select_from(ReadingHistory)
            .join(Article, ReadingHistory.article_id == Article.id)
            .where(
                ReadingHistory.user_id == user_id,
                Article.search_vector.match(query)
            )
        )
        
        # Execute queries
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()
        
        search_query = search_query.offset(skip).limit(limit)
        result = await self.db.execute(search_query)
        history = result.scalars().all()
        
        return list(history), total
```

---

### **Phase C2: Analytics Schemas**

**File:** `app/schemas/analytics.py` (new file)

```python
"""Schemas for reading analytics endpoints."""
from datetime import datetime, date
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ReadingPatternsByHour(BaseModel):
    """Reading patterns by hour of day."""
    by_hour: Dict[int, int] = Field(..., description="Articles read by hour (0-23)")
    by_weekday: Dict[int, int] = Field(..., description="Articles read by day of week (0=Monday, 6=Sunday)")


class CategoryDistribution(BaseModel):
    """Category reading distribution."""
    count: int
    avg_duration: float
    avg_scroll: float


class ReadingPatternsResponse(BaseModel):
    """Response for reading patterns endpoint."""
    reading_by_hour: Dict[int, int]
    reading_by_weekday: Dict[str, int]
    category_distribution: Dict[str, CategoryDistribution]
    reading_velocity: Dict[str, float]
    streaks: Dict[str, int]
    most_active_period: str
    
    class Config:
        schema_extra = {
            "example": {
                "reading_by_hour": {8: 5, 12: 10, 18: 15},
                "reading_by_weekday": {"Monday": 20, "Tuesday": 15},
                "category_distribution": {
                    "science": {
                        "count": 45,
                        "avg_duration": 320,
                        "avg_scroll": 78.5
                    }
                },
                "reading_velocity": {
                    "articles_per_day": 8.5,
                    "articles_per_week": 59.5
                },
                "streaks": {
                    "current_streak": 5,
                    "longest_streak": 14,
                    "total_reading_days": 87
                },
                "most_active_period": "18:00-20:00"
            }
        }


class DailyTrend(BaseModel):
    """Daily reading trend."""
    date: str
    article_count: int
    total_duration: int
    avg_scroll: float


class CategoryTrend(BaseModel):
    """Category trend over time."""
    category: str
    data: List[int]


class ReadingTrendsResponse(BaseModel):
    """Response for reading trends endpoint."""
    daily_reads: List[DailyTrend]
    category_trends: Dict[str, List[int]]
    engagement_trends: Dict[str, List[float]]
    period_start: datetime
    period_end: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TopSource(BaseModel):
    """Top reading source."""
    source_id: str
    source_name: str
    article_count: int
    avg_duration: float


class ReadingInsightsResponse(BaseModel):
    """Response for reading insights endpoint."""
    favorite_categories: List[Dict[str, any]]
    top_sources: List[TopSource]
    engagement_metrics: Dict[str, any]
    reading_milestones: Dict[str, any]
    period_summary: Dict[str, any]


class HistorySearchResult(BaseModel):
    """Search result item."""
    id: str
    article_id: str
    article_title: str
    article_url: str
    viewed_at: datetime
    duration_seconds: Optional[int]
    scroll_percentage: Optional[float]
    
    class Config:
        orm_mode = True


class HistorySearchResponse(BaseModel):
    """Response for history search."""
    results: List[HistorySearchResult]
    total: int
    query: str
    page: int
    page_size: int
```

---

### **Phase C3: Analytics Service Methods**

**File:** `app/services/reading_history_service.py` (add methods)

```python
"""Add analytics methods to existing service."""

class ReadingHistoryService:
    """Extended service with analytics."""
    
    # ... existing methods ...
    
    async def get_reading_patterns(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get comprehensive reading patterns."""
        # Get base patterns
        patterns = await self.history_repo.get_reading_patterns(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get category distribution
        categories = await self.history_repo.get_category_distribution(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get streaks
        streaks = await self.history_repo.get_reading_streak(user_id=user_id)
        
        # Calculate reading velocity
        days_in_period = 30  # Default
        if start_date and end_date:
            days_in_period = (end_date - start_date).days
        
        total_articles, _ = await self.history_repo.count_views_by_user(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        articles_per_day = total_articles / max(days_in_period, 1)
        
        # Find most active period
        by_hour = patterns['by_hour']
        if by_hour:
            peak_hour = max(by_hour.items(), key=lambda x: x[1])[0]
            most_active = f"{peak_hour:02d}:00-{(peak_hour+2) % 24:02d}:00"
        else:
            most_active = "N/A"
        
        # Map day of week numbers to names
        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        reading_by_weekday = {
            weekday_names[dow]: count 
            for dow, count in patterns['by_weekday'].items()
        }
        
        return {
            'reading_by_hour': patterns['by_hour'],
            'reading_by_weekday': reading_by_weekday,
            'category_distribution': categories,
            'reading_velocity': {
                'articles_per_day': round(articles_per_day, 2),
                'articles_per_week': round(articles_per_day * 7, 2)
            },
            'streaks': streaks,
            'most_active_period': most_active
        }
    
    async def get_reading_trends(
        self,
        user_id: str,
        days: int = 30
    ) -> dict:
        """Get reading trends over time."""
        # Get daily trends
        daily_trends = await self.history_repo.get_daily_trends(
            user_id=user_id,
            days=days
        )
        
        # Get category trends (simplified)
        start_date = datetime.utcnow() - timedelta(days=days)
        categories = await self.history_repo.get_category_distribution(
            user_id=user_id,
            start_date=start_date
        )
        
        # Calculate engagement trends (weekly aggregation)
        engagement_trends = {
            'avg_duration_by_week': [],
            'avg_scroll_by_week': []
        }
        
        # Group daily trends by week
        weeks = {}
        for trend in daily_trends:
            date_obj = datetime.fromisoformat(trend['date'])
            week_num = date_obj.isocalendar()[1]
            
            if week_num not in weeks:
                weeks[week_num] = {'durations': [], 'scrolls': []}
            
            weeks[week_num]['durations'].append(trend['total_duration'] / max(trend['article_count'], 1))
            weeks[week_num]['scrolls'].append(trend['avg_scroll'])
        
        # Calculate weekly averages
        for week in sorted(weeks.keys()):
            avg_dur = sum(weeks[week]['durations']) / len(weeks[week]['durations'])
            avg_scroll = sum(weeks[week]['scrolls']) / len(weeks[week]['scrolls'])
            engagement_trends['avg_duration_by_week'].append(round(avg_dur, 2))
            engagement_trends['avg_scroll_by_week'].append(round(avg_scroll, 2))
        
        return {
            'daily_reads': daily_trends,
            'category_trends': {cat: [data['count']] for cat, data in categories.items()},
            'engagement_trends': engagement_trends,
            'period_start': datetime.utcnow() - timedelta(days=days),
            'period_end': datetime.utcnow()
        }
    
    async def get_reading_insights(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get comprehensive reading insights."""
        # Get category distribution
        categories = await self.history_repo.get_category_distribution(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get top sources
        top_sources = await self.history_repo.get_top_sources(
            user_id=user_id,
            limit=10,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get engagement metrics
        total_views = await self.history_repo.count_views_by_user(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        total_time = await self.history_repo.get_total_reading_time(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Sort categories by reading time
        favorite_categories = [
            {
                'category': cat,
                'articles_read': data['count'],
                'avg_duration': data['avg_duration'],
                'total_time': data['count'] * data['avg_duration']
            }
            for cat, data in categories.items()
        ]
        favorite_categories.sort(key=lambda x: x['total_time'], reverse=True)
        
        # Calculate engagement threshold (articles with above-average engagement)
        avg_duration = total_time / max(total_views, 1)
        high_engagement_threshold = avg_duration * 1.5
        
        return {
            'favorite_categories': favorite_categories[:5],
            'top_sources': top_sources,
            'engagement_metrics': {
                'high_engagement_threshold_seconds': int(high_engagement_threshold),
                'total_articles_read': total_views,
                'avg_reading_time': round(avg_duration, 2)
            },
            'reading_milestones': {
                'total_hours_read': round(total_time / 3600, 2),
                'articles_this_period': total_views
            },
            'period_summary': {
                'start_date': start_date,
                'end_date': end_date
            }
        }
    
    async def search_reading_history(
        self,
        user_id: str,
        query: str,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[ReadingHistory], int]:
        """Search through reading history."""
        if not query or len(query.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query must be at least 2 characters"
            )
        
        return await self.history_repo.search_history(
            user_id=user_id,
            query=query,
            skip=skip,
            limit=limit
        )
```

---

### **Phase C4: Analytics Endpoints**

**File:** `app/api/v1/endpoints/reading_history.py` (add endpoints)

```python
"""Add analytics endpoints to existing router."""
from app.schemas.analytics import (
    ReadingPatternsResponse,
    ReadingTrendsResponse,
    ReadingInsightsResponse,
    HistorySearchResponse,
    HistorySearchResult,
)


@router.get(
    "/patterns",
    response_model=ReadingPatternsResponse,
    summary="Get reading patterns",
    description="Get comprehensive reading patterns including time distribution, categories, and streaks."
)
async def get_reading_patterns(
    start_date: Optional[datetime] = Query(None, description="Analysis period start"),
    end_date: Optional[datetime] = Query(None, description="Analysis period end"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's reading patterns."""
    service = ReadingHistoryService(db)
    
    patterns = await service.get_reading_patterns(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    return ReadingPatternsResponse(**patterns)


@router.get(
    "/trends",
    response_model=ReadingTrendsResponse,
    summary="Get reading trends",
    description="Get time-series reading trends for visualization and analytics."
)
async def get_reading_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's reading trends over time."""
    service = ReadingHistoryService(db)
    
    trends = await service.get_reading_trends(
        user_id=current_user.id,
        days=days
    )
    
    return ReadingTrendsResponse(**trends)


@router.get(
    "/insights",
    response_model=ReadingInsightsResponse,
    summary="Get reading insights",
    description="Get personalized reading insights and recommendations based on history."
)
async def get_reading_insights(
    start_date: Optional[datetime] = Query(None, description="Analysis period start"),
    end_date: Optional[datetime] = Query(None, description="Analysis period end"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's reading insights."""
    service = ReadingHistoryService(db)
    
    insights = await service.get_reading_insights(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    return ReadingInsightsResponse(**insights)


@router.get(
    "/search",
    response_model=HistorySearchResponse,
    summary="Search reading history",
    description="Search through your reading history by article title and content."
)
async def search_history(
    q: str = Query(..., min_length=2, max_length=200, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search user's reading history."""
    service = ReadingHistoryService(db)
    
    skip = (page - 1) * page_size
    
    history_list, total = await service.search_reading_history(
        user_id=current_user.id,
        query=q,
        skip=skip,
        limit=page_size
    )
    
    # Convert to response format
    results = [
        HistorySearchResult(
            id=str(h.id),
            article_id=str(h.article_id),
            article_title=h.article.title if h.article else "Unknown",
            article_url=h.article.url if h.article else "",
            viewed_at=h.viewed_at,
            duration_seconds=h.duration_seconds,
            scroll_percentage=h.scroll_percentage
        )
        for h in history_list
    ]
    
    return HistorySearchResponse(
        results=results,
        total=total,
        query=q,
        page=page,
        page_size=page_size
    )
```

**Test Option C endpoints:**

```bash
# Test patterns
curl "http://localhost:8000/api/v1/reading-history/patterns" \
  -H "Authorization: Bearer $TOKEN"

# Test trends
curl "http://localhost:8000/api/v1/reading-history/trends?days=30" \
  -H "Authorization: Bearer $TOKEN"

# Test insights
curl "http://localhost:8000/api/v1/reading-history/insights" \
  -H "Authorization: Bearer $TOKEN"

# Test search
curl "http://localhost:8000/api/v1/reading-history/search?q=artificial+intelligence" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🧪 **Testing Strategy**

### **Phase T1: Repository Tests**

**File:** `tests/test_reading_preferences_repository.py` (new)

```python
"""Tests for reading preferences repository."""
import pytest
from uuid import uuid4

from app.repositories.reading_preferences_repository import ReadingPreferencesRepository


@pytest.mark.asyncio
async def test_create_preferences(db_session, test_user):
    """Test creating user preferences."""
    repo = ReadingPreferencesRepository(db_session)
    
    prefs = await repo.create(
        user_id=test_user.id,
        tracking_enabled=True,
        retention_days=90
    )
    
    assert prefs.user_id == test_user.id
    assert prefs.tracking_enabled is True
    assert prefs.retention_days == 90


@pytest.mark.asyncio
async def test_get_or_create_preferences(db_session, test_user):
    """Test get or create preferences."""
    repo = ReadingPreferencesRepository(db_session)
    
    # First call creates
    prefs1 = await repo.get_or_create(user_id=test_user.id)
    assert prefs1.user_id == test_user.id
    
    # Second call retrieves existing
    prefs2 = await repo.get_or_create(user_id=test_user.id)
    assert prefs1.id == prefs2.id


@pytest.mark.asyncio
async def test_update_preferences(db_session, test_user):
    """Test updating preferences."""
    repo = ReadingPreferencesRepository(db_session)
    
    # Create preferences
    await repo.create(user_id=test_user.id, tracking_enabled=True)
    
    # Update preferences
    updated = await repo.update(
        user_id=test_user.id,
        tracking_enabled=False,
        retention_days=30
    )
    
    assert updated.tracking_enabled is False
    assert updated.retention_days == 30
```

**File:** `tests/test_reading_history_analytics.py` (new)

```python
"""Tests for analytics repository methods."""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.repositories.reading_history_repository import ReadingHistoryRepository


@pytest.mark.asyncio
async def test_get_reading_patterns(db_session, test_user, test_article):
    """Test reading patterns analysis."""
    repo = ReadingHistoryRepository(db_session)
    
    # Create test data with specific patterns
    for hour in [8, 8, 12, 12, 12, 18, 18]:
        viewed_at = datetime.utcnow().replace(hour=hour, minute=0, second=0)
        await repo.record_view(
            user_id=test_user.id,
            article_id=test_article.id,
            duration_seconds=300
        )
        await db_session.commit()
    
    # Get patterns
    patterns = await repo.get_reading_patterns(user_id=test_user.id)
    
    assert patterns['by_hour'][8] == 2
    assert patterns['by_hour'][12] == 3
    assert patterns['by_hour'][18] == 2


@pytest.mark.asyncio
async def test_get_category_distribution(db_session, test_user, test_articles_by_category):
    """Test category distribution analysis."""
    repo = ReadingHistoryRepository(db_session)
    
    # Record views for different categories
    for article in test_articles_by_category:
        await repo.record_view(
            user_id=test_user.id,
            article_id=article.id,
            duration_seconds=300
        )
    await db_session.commit()
    
    # Get distribution
    distribution = await repo.get_category_distribution(user_id=test_user.id)
    
    assert 'science' in distribution
    assert 'politics' in distribution
    assert distribution['science']['count'] > 0


@pytest.mark.asyncio
async def test_get_reading_streak(db_session, test_user, test_article):
    """Test reading streak calculation."""
    repo = ReadingHistoryRepository(db_session)
    
    # Create consecutive reading days
    for days_ago in range(5):
        viewed_at = datetime.utcnow() - timedelta(days=days_ago)
        await repo.record_view(
            user_id=test_user.id,
            article_id=test_article.id,
            viewed_at=viewed_at
        )
    await db_session.commit()
    
    # Get streaks
    streaks = await repo.get_reading_streak(user_id=test_user.id)
    
    assert streaks['current_streak'] >= 5
    assert streaks['longest_streak'] >= 5
    assert streaks['total_reading_days'] == 5


@pytest.mark.asyncio
async def test_search_history(db_session, test_user, test_articles_with_content):
    """Test history search functionality."""
    repo = ReadingHistoryRepository(db_session)
    
    # Record views for articles
    for article in test_articles_with_content:
        await repo.record_view(
            user_id=test_user.id,
            article_id=article.id
        )
    await db_session.commit()
    
    # Search history
    results, total = await repo.search_history(
        user_id=test_user.id,
        query="artificial intelligence",
        skip=0,
        limit=10
    )
    
    assert total > 0
    assert len(results) > 0
    assert "artificial" in results[0].article.title.lower() or \
           "intelligence" in results[0].article.title.lower()
```

---

### **Phase T2: API Integration Tests**

**File:** `tests/test_api_reading_history_enhanced.py` (new)

```python
"""Integration tests for enhanced reading history endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_export_history_json(async_client: AsyncClient, auth_headers, test_reading_history):
    """Test exporting history as JSON."""
    response = await async_client.post(
        "/api/v1/reading-history/export",
        headers=auth_headers,
        json={"format": "json", "include_articles": True}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["export_format"] == "json"
    assert data["records_count"] > 0
    assert "file_content" in data or "download_url" in data


@pytest.mark.asyncio
async def test_export_history_csv(async_client: AsyncClient, auth_headers):
    """Test exporting history as CSV."""
    response = await async_client.post(
        "/api/v1/reading-history/export",
        headers=auth_headers,
        json={"format": "csv"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["export_format"] == "csv"


@pytest.mark.asyncio
async def test_get_preferences(async_client: AsyncClient, auth_headers):
    """Test getting user preferences."""
    response = await async_client.get(
        "/api/v1/reading-history/preferences",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "tracking_enabled" in data
    assert "retention_days" in data


@pytest.mark.asyncio
async def test_update_preferences(async_client: AsyncClient, auth_headers):
    """Test updating preferences."""
    response = await async_client.patch(
        "/api/v1/reading-history/preferences",
        headers=auth_headers,
        json={
            "tracking_enabled": False,
            "retention_days": 90
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["tracking_enabled"] is False
    assert data["retention_days"] == 90


@pytest.mark.asyncio
async def test_get_reading_patterns(async_client: AsyncClient, auth_headers, test_reading_history):
    """Test getting reading patterns."""
    response = await async_client.get(
        "/api/v1/reading-history/patterns",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "reading_by_hour" in data
    assert "reading_by_weekday" in data
    assert "category_distribution" in data
    assert "streaks" in data


@pytest.mark.asyncio
async def test_get_reading_trends(async_client: AsyncClient, auth_headers):
    """Test getting reading trends."""
    response = await async_client.get(
        "/api/v1/reading-history/trends?days=30",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "daily_reads" in data
    assert "category_trends" in data
    assert "engagement_trends" in data


@pytest.mark.asyncio
async def test_get_reading_insights(async_client: AsyncClient, auth_headers, test_reading_history):
    """Test getting reading insights."""
    response = await async_client.get(
        "/api/v1/reading-history/insights",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "favorite_categories" in data
    assert "top_sources" in data
    assert "engagement_metrics" in data


@pytest.mark.asyncio
async def test_search_history(async_client: AsyncClient, auth_headers, test_reading_history):
    """Test searching reading history."""
    response = await async_client.get(
        "/api/v1/reading-history/search?q=test&page=1&page_size=10",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total" in data
    assert "query" in data
    assert data["query"] == "test"


@pytest.mark.asyncio
async def test_search_history_validation(async_client: AsyncClient, auth_headers):
    """Test search validation."""
    # Query too short
    response = await async_client.get(
        "/api/v1/reading-history/search?q=a",
        headers=auth_headers
    )
    assert response.status_code == 422
```

---

## 📦 **Integration Plan**

### **Step-by-Step Integration**

**Day 1: Database & Models**
```bash
# 1. Create and run migration
alembic revision --autogenerate -m "add_user_reading_preferences"
alembic upgrade head

# 2. Verify migration
python -c "
from app.models.user_reading_preferences import UserReadingPreferences
print('Model imported successfully')
"

# 3. Test database connection
pytest tests/test_reading_preferences_repository.py -v
```

**Day 2: Option B - Export & Privacy**
```bash
# 1. Run repository tests
pytest tests/test_reading_preferences_repository.py -v

# 2. Run service tests
pytest tests/test_reading_history_service.py::test_export -v

# 3. Run API tests
pytest tests/test_api_reading_history_enhanced.py::test_export -v
pytest tests/test_api_reading_history_enhanced.py::test_preferences -v

# 4. Manual testing
python scripts/test_export_endpoints.py
```

**Day 3-4: Option C - Analytics (Patterns & Trends)**
```bash
# 1. Run analytics repository tests
pytest tests/test_reading_history_analytics.py -v

# 2. Run API tests
pytest tests/test_api_reading_history_enhanced.py::test_patterns -v
pytest tests/test_api_reading_history_enhanced.py::test_trends -v

# 3. Performance testing
python scripts/test_analytics_performance.py
```

**Day 5-6: Option C - Search & Insights**
```bash
# 1. Run search tests
pytest tests/test_reading_history_analytics.py::test_search -v

# 2. Run insights tests
pytest tests/test_api_reading_history_enhanced.py::test_insights -v

# 3. Integration testing
pytest tests/test_api_reading_history_enhanced.py -v
```

**Day 7: Final Testing & Documentation**
```bash
# 1. Run full test suite
pytest tests/ -v --cov=app --cov-report=html

# 2. Verify all endpoints
python scripts/verify_all_endpoints.py

# 3. Generate API documentation
python scripts/generate_api_docs.py

# 4. Performance benchmarks
python scripts/benchmark_analytics.py
```

---

## ✅ **Deployment Checklist**

### **Pre-Deployment**
- [ ] All database migrations applied
- [ ] All tests passing (100% coverage)
- [ ] Code review completed
- [ ] API documentation updated
- [ ] Performance benchmarks acceptable

### **Deployment**
- [ ] Backup database
- [ ] Deploy database migration
- [ ] Deploy application code
- [ ] Verify all endpoints responding
- [ ] Monitor error logs

### **Post-Deployment**
- [ ] Run smoke tests
- [ ] Monitor performance metrics
- [ ] Check error rates
- [ ] Verify user feedback
- [ ] Document any issues

---

## 📊 **Success Metrics**

### **Performance Targets**
- Export endpoint: < 2s for 1000 records
- Patterns endpoint: < 500ms
- Trends endpoint: < 1s
- Search endpoint: < 300ms

### **Quality Metrics**
- Test coverage: 100%
- Code review: Approved
- Zero critical bugs
- All endpoints documented

### **User Experience**
- Export completion rate: > 95%
- Search relevance: > 80%
- Analytics load time: < 2s
- User satisfaction: > 4/5

---

**This plan provides a complete, step-by-step approach to implementing both Option B and Option C enhancements with comprehensive testing and validation at each phase.**
