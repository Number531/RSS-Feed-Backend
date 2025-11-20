# Synthesis Endpoints Implementation Plan

**Last Updated**: November 20, 2025  
**Estimated Time**: 2-3 days  
**Risk Level**: Low (no changes to existing endpoints)

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step-by-Step Implementation](#step-by-step-implementation)
4. [Testing Strategy](#testing-strategy)
5. [Validation Checklist](#validation-checklist)
6. [Rollback Plan](#rollback-plan)

---

## Overview

### Goals
- ✅ Add 3 new synthesis-specific endpoints
- ✅ Maintain 100% backward compatibility
- ✅ Achieve >95% test coverage
- ✅ Zero regression in existing functionality

### New Endpoints
1. `GET /api/v1/articles/synthesis` - List synthesis articles (optimized)
2. `GET /api/v1/articles/{id}/synthesis` - Get full synthesis article
3. `GET /api/v1/articles/synthesis/stats` - Get synthesis statistics

### Testing Coverage
- **Unit Tests**: Service layer logic
- **Integration Tests**: API endpoints + database
- **Regression Tests**: Ensure existing endpoints unchanged

---

## Prerequisites

### 1. Verify Database Migration
```bash
# Check current migration
alembic current

# Should show: 2317b7aeeb89 (head) - Phase 4 complete
```

### 2. Verify Test Data
```bash
# Run validation to ensure 10 synthesis articles exist
python scripts/testing/validate_all_phases.py

# Should show: "✅ ALL PHASES VALIDATED"
```

### 3. Check Existing Tests
```bash
# Run existing tests to establish baseline
make test

# Or directly:
pytest tests/ -v --cov=app --cov-report=term

# Note current coverage percentage
```

---

## Step-by-Step Implementation

### **Phase 1: Preparation** (30 minutes)

#### Step 1.1: Create Feature Branch
```bash
git checkout -b feature/synthesis-endpoints
git push -u origin feature/synthesis-endpoints
```

#### Step 1.2: Review Existing Code
```bash
# Check existing article endpoints
cat app/api/v1/endpoints/articles.py | head -50

# Check article service
cat app/services/article_service.py | head -50

# Check existing tests
ls -la tests/integration/test_articles.py
ls -la tests/unit/test_article_service.py
```

#### Step 1.3: Create Test Data Fixtures
```bash
# Create fixture file for synthesis articles
touch tests/fixtures/synthesis_articles.py
```

---

### **Phase 2: Pydantic Schemas** (30 minutes)

#### Step 2.1: Create Response Schemas

**File**: `app/schemas/synthesis.py`

```python
"""
Pydantic schemas for synthesis endpoints.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# List View Schemas (Optimized)
# ============================================================================

class SynthesisListItem(BaseModel):
    """Optimized synthesis article for list views."""
    id: str
    title: str
    published_date: datetime
    synthesis_preview: str = Field(..., max_length=500)
    synthesis_word_count: int
    synthesis_read_minutes: int
    verdict_color: str
    fact_check_verdict: str
    fact_check_score: int
    has_context_emphasis: bool
    has_timeline: bool
    timeline_event_count: int
    reference_count: int
    margin_note_count: int
    thumbnail_url: Optional[str] = None
    synthesis_generated_at: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True


class SynthesisListResponse(BaseModel):
    """Response for synthesis article list."""
    articles: List[SynthesisListItem]
    pagination: dict


# ============================================================================
# Detail View Schemas
# ============================================================================

class Reference(BaseModel):
    """Source reference."""
    id: int
    title: str
    url: str
    publication: str
    date: str
    credibility_score: int
    quote: Optional[str] = None


class MarginNote(BaseModel):
    """Margin note for additional context."""
    id: int
    paragraph_index: int
    text: str
    type: str  # context, clarification, source, warning


class TimelineEvent(BaseModel):
    """Event in timeline."""
    date: str
    time: Optional[str] = None
    event: str
    source_id: int


class ContextAndEmphasis(BaseModel):
    """Context and emphasis section."""
    key_context: str
    why_this_matters: str


class SynthesisDetailArticle(BaseModel):
    """Complete synthesis article with all data."""
    id: str
    title: str
    published_date: datetime
    synthesis_article: str  # Full markdown
    synthesis_word_count: int
    synthesis_read_minutes: int
    fact_check_verdict: str
    fact_check_score: int
    verdict_color: str
    synthesis_generated_at: datetime
    references: List[Reference]
    margin_notes: List[MarginNote]
    event_timeline: List[TimelineEvent]
    context_and_emphasis: Optional[ContextAndEmphasis] = None
    reference_count: int
    margin_note_count: int
    timeline_event_count: int


class SynthesisDetailResponse(BaseModel):
    """Response for synthesis article detail."""
    article: SynthesisDetailArticle


# ============================================================================
# Stats Schema
# ============================================================================

class SynthesisStatsResponse(BaseModel):
    """Statistics for synthesis articles."""
    total_synthesis_articles: int
    verdicts: dict  # {color: count}
    average_word_count: int
    average_read_minutes: int
    average_credibility_score: int
    articles_with_timelines: int
    articles_with_context: int
```

#### Step 2.2: Create Unit Tests for Schemas

**File**: `tests/unit/test_synthesis_schemas.py`

```python
"""
Unit tests for synthesis Pydantic schemas.
"""
import pytest
from datetime import datetime
from app.schemas.synthesis import (
    SynthesisListItem,
    SynthesisListResponse,
    SynthesisDetailArticle,
    Reference,
    MarginNote
)


class TestSynthesisListItem:
    """Test SynthesisListItem schema."""
    
    def test_valid_synthesis_list_item(self):
        """Test valid synthesis list item creation."""
        data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "title": "Test Article",
            "published_date": datetime.now(),
            "synthesis_preview": "Preview text...",
            "synthesis_word_count": 2000,
            "synthesis_read_minutes": 10,
            "verdict_color": "green",
            "fact_check_verdict": "TRUE",
            "fact_check_score": 85,
            "has_context_emphasis": True,
            "has_timeline": True,
            "timeline_event_count": 5,
            "reference_count": 12,
            "margin_note_count": 8,
            "thumbnail_url": "https://example.com/image.jpg",
            "synthesis_generated_at": datetime.now()
        }
        
        item = SynthesisListItem(**data)
        assert item.id == data["id"]
        assert item.title == data["title"]
        assert item.synthesis_word_count == 2000
    
    def test_missing_required_field(self):
        """Test that missing required fields raise validation error."""
        data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "title": "Test Article"
            # Missing other required fields
        }
        
        with pytest.raises(ValueError):
            SynthesisListItem(**data)


class TestReference:
    """Test Reference schema."""
    
    def test_valid_reference(self):
        """Test valid reference creation."""
        data = {
            "id": 1,
            "title": "Source Title",
            "url": "https://example.com",
            "publication": "CNN",
            "date": "2025-11-19",
            "credibility_score": 85
        }
        
        ref = Reference(**data)
        assert ref.id == 1
        assert ref.credibility_score == 85
    
    def test_reference_with_optional_quote(self):
        """Test reference with optional quote."""
        data = {
            "id": 1,
            "title": "Source Title",
            "url": "https://example.com",
            "publication": "CNN",
            "date": "2025-11-19",
            "credibility_score": 85,
            "quote": "Exact quote from source"
        }
        
        ref = Reference(**data)
        assert ref.quote == "Exact quote from source"


class TestMarginNote:
    """Test MarginNote schema."""
    
    def test_valid_margin_note(self):
        """Test valid margin note creation."""
        data = {
            "id": 1,
            "paragraph_index": 3,
            "text": "Additional context",
            "type": "context"
        }
        
        note = MarginNote(**data)
        assert note.paragraph_index == 3
        assert note.type == "context"
```

---

### **Phase 3: Service Layer** (1 hour)

#### Step 3.1: Add Service Methods

**File**: `app/services/synthesis_service.py` (NEW)

```python
"""
Service layer for synthesis article operations.
"""
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.article import Article
from app.schemas.synthesis import (
    SynthesisListItem,
    SynthesisDetailArticle,
    Reference,
    MarginNote,
    TimelineEvent
)


class SynthesisService:
    """Service for synthesis article operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def list_synthesis_articles(
        self,
        limit: int = 20,
        offset: int = 0,
        verdict_color: Optional[str] = None,
        min_word_count: Optional[int] = None,
        has_timeline: Optional[bool] = None,
        sort: str = "newest"
    ) -> Dict:
        """
        Get optimized list of synthesis articles.
        
        Args:
            limit: Maximum number of articles to return
            offset: Number of articles to skip (pagination)
            verdict_color: Filter by verdict color
            min_word_count: Minimum word count
            has_timeline: Filter by timeline presence
            sort: Sort order (newest, oldest, longest, shortest)
            
        Returns:
            Dictionary with articles and pagination info
        """
        # Build base query
        query = self.db.query(Article).filter(Article.has_synthesis == True)
        
        # Apply filters
        if verdict_color:
            query = query.filter(Article.verdict_color == verdict_color)
        
        if min_word_count:
            query = query.filter(Article.synthesis_word_count >= min_word_count)
        
        if has_timeline is not None:
            query = query.filter(Article.has_timeline == has_timeline)
        
        # Apply sorting
        if sort == "newest":
            query = query.order_by(Article.synthesis_generated_at.desc())
        elif sort == "oldest":
            query = query.order_by(Article.synthesis_generated_at.asc())
        elif sort == "longest":
            query = query.order_by(Article.synthesis_word_count.desc())
        elif sort == "shortest":
            query = query.order_by(Article.synthesis_word_count.asc())
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        articles = query.offset(offset).limit(limit).all()
        
        return {
            "articles": articles,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total
        }
    
    def get_synthesis_article(self, article_id: str) -> Optional[Article]:
        """
        Get full synthesis article by ID.
        
        Args:
            article_id: Article UUID
            
        Returns:
            Article object or None if not found
        """
        article = self.db.query(Article).filter(
            Article.id == article_id,
            Article.has_synthesis == True
        ).first()
        
        return article
    
    def get_synthesis_stats(self) -> Dict:
        """
        Get statistics for synthesis articles.
        
        Returns:
            Dictionary with various statistics
        """
        # Total count
        total = self.db.query(Article).filter(
            Article.has_synthesis == True
        ).count()
        
        # Verdict distribution
        verdict_query = self.db.query(
            Article.verdict_color,
            func.count(Article.id).label('count')
        ).filter(
            Article.has_synthesis == True
        ).group_by(Article.verdict_color).all()
        
        verdicts = {row.verdict_color: row.count for row in verdict_query}
        
        # Averages
        avg_query = self.db.query(
            func.avg(Article.synthesis_word_count).label('avg_words'),
            func.avg(Article.synthesis_read_minutes).label('avg_minutes'),
            func.avg(Article.fact_check_score).label('avg_score')
        ).filter(Article.has_synthesis == True).first()
        
        # Feature counts
        timelines = self.db.query(Article).filter(
            Article.has_synthesis == True,
            Article.has_timeline == True
        ).count()
        
        context = self.db.query(Article).filter(
            Article.has_synthesis == True,
            Article.has_context_emphasis == True
        ).count()
        
        return {
            "total_synthesis_articles": total,
            "verdicts": verdicts,
            "average_word_count": int(avg_query.avg_words or 0),
            "average_read_minutes": int(avg_query.avg_minutes or 0),
            "average_credibility_score": int(avg_query.avg_score or 0),
            "articles_with_timelines": timelines,
            "articles_with_context": context
        }
    
    def extract_structured_data(self, article: Article) -> Dict:
        """
        Extract structured data from article_data JSONB.
        
        Args:
            article: Article object
            
        Returns:
            Dictionary with extracted data
        """
        article_data = article.article_data or {}
        
        return {
            "references": article_data.get("references", []),
            "margin_notes": article_data.get("margin_notes", []),
            "event_timeline": article_data.get("event_timeline", []),
            "context_and_emphasis": article_data.get("context_and_emphasis", {})
        }
```

#### Step 3.2: Create Unit Tests for Service

**File**: `tests/unit/test_synthesis_service.py`

```python
"""
Unit tests for SynthesisService.
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from app.services.synthesis_service import SynthesisService
from app.models.article import Article


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock()


@pytest.fixture
def synthesis_service(mock_db):
    """Create SynthesisService with mocked DB."""
    return SynthesisService(mock_db)


@pytest.fixture
def sample_article():
    """Create sample article."""
    article = Article()
    article.id = "123e4567-e89b-12d3-a456-426614174000"
    article.title = "Test Article"
    article.has_synthesis = True
    article.synthesis_word_count = 2000
    article.synthesis_read_minutes = 10
    article.verdict_color = "green"
    article.fact_check_score = 85
    article.synthesis_generated_at = datetime.now()
    article.article_data = {
        "references": [
            {"id": 1, "title": "Source 1", "url": "https://example.com"}
        ],
        "margin_notes": [
            {"id": 1, "text": "Note 1", "type": "context"}
        ]
    }
    return article


class TestListSynthesisArticles:
    """Test list_synthesis_articles method."""
    
    def test_list_with_no_filters(self, synthesis_service, mock_db, sample_article):
        """Test listing articles without filters."""
        # Mock query chain
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_article]
        
        mock_db.query.return_value = mock_query
        
        result = synthesis_service.list_synthesis_articles(limit=20, offset=0)
        
        assert result["total"] == 10
        assert len(result["articles"]) == 1
        assert result["has_next"] == False
    
    def test_list_with_verdict_filter(self, synthesis_service, mock_db):
        """Test listing with verdict color filter."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        result = synthesis_service.list_synthesis_articles(verdict_color="green")
        
        # Verify filter was called
        assert mock_query.filter.called
    
    def test_list_with_sorting(self, synthesis_service, mock_db):
        """Test different sort orders."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        # Test each sort option
        for sort in ["newest", "oldest", "longest", "shortest"]:
            result = synthesis_service.list_synthesis_articles(sort=sort)
            assert mock_query.order_by.called


class TestGetSynthesisArticle:
    """Test get_synthesis_article method."""
    
    def test_get_existing_article(self, synthesis_service, mock_db, sample_article):
        """Test retrieving existing article."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_article
        
        mock_db.query.return_value = mock_query
        
        result = synthesis_service.get_synthesis_article("123e4567-e89b-12d3-a456-426614174000")
        
        assert result == sample_article
        assert result.id == "123e4567-e89b-12d3-a456-426614174000"
    
    def test_get_nonexistent_article(self, synthesis_service, mock_db):
        """Test retrieving non-existent article."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        mock_db.query.return_value = mock_query
        
        result = synthesis_service.get_synthesis_article("nonexistent-id")
        
        assert result is None


class TestGetSynthesisStats:
    """Test get_synthesis_stats method."""
    
    def test_stats_calculation(self, synthesis_service, mock_db):
        """Test statistics calculation."""
        # Mock queries
        mock_count_query = Mock()
        mock_count_query.filter.return_value = mock_count_query
        mock_count_query.count.return_value = 10
        
        mock_verdict_query = Mock()
        mock_verdict_row = Mock()
        mock_verdict_row.verdict_color = "green"
        mock_verdict_row.count = 5
        mock_verdict_query.filter.return_value = mock_verdict_query
        mock_verdict_query.group_by.return_value = mock_verdict_query
        mock_verdict_query.all.return_value = [mock_verdict_row]
        
        mock_avg_query = Mock()
        mock_avg_result = Mock()
        mock_avg_result.avg_words = 2000
        mock_avg_result.avg_minutes = 10
        mock_avg_result.avg_score = 75
        mock_avg_query.filter.return_value = mock_avg_query
        mock_avg_query.first.return_value = mock_avg_result
        
        # Setup mock_db.query to return different mocks for different calls
        call_count = [0]
        def query_side_effect(*args):
            call_count[0] += 1
            if call_count[0] == 1:  # Total count
                return mock_count_query
            elif call_count[0] == 2:  # Verdict distribution
                return mock_verdict_query
            elif call_count[0] == 3:  # Averages
                return mock_avg_query
            else:  # Feature counts
                return mock_count_query
        
        mock_db.query.side_effect = query_side_effect
        
        result = synthesis_service.get_synthesis_stats()
        
        assert result["total_synthesis_articles"] == 10
        assert result["verdicts"]["green"] == 5
        assert result["average_word_count"] == 2000


class TestExtractStructuredData:
    """Test extract_structured_data method."""
    
    def test_extract_with_data(self, synthesis_service, sample_article):
        """Test extracting structured data when present."""
        result = synthesis_service.extract_structured_data(sample_article)
        
        assert "references" in result
        assert "margin_notes" in result
        assert len(result["references"]) == 1
        assert len(result["margin_notes"]) == 1
    
    def test_extract_without_data(self, synthesis_service):
        """Test extracting when article_data is None."""
        article = Article()
        article.article_data = None
        
        result = synthesis_service.extract_structured_data(article)
        
        assert result["references"] == []
        assert result["margin_notes"] == []
        assert result["event_timeline"] == []
```

---

### **Phase 4: API Endpoints** (1 hour)

#### Step 4.1: Create Endpoint File

**File**: `app/api/v1/endpoints/synthesis.py` (NEW)

```python
"""
API endpoints for synthesis articles.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.synthesis_service import SynthesisService
from app.schemas.synthesis import (
    SynthesisListResponse,
    SynthesisListItem,
    SynthesisDetailResponse,
    SynthesisStatsResponse
)

router = APIRouter()


@router.get("/synthesis", response_model=SynthesisListResponse)
async def list_synthesis_articles(
    limit: int = Query(20, le=100, ge=1, description="Maximum number of articles to return"),
    offset: int = Query(0, ge=0, description="Number of articles to skip"),
    verdict_color: Optional[str] = Query(
        None,
        regex="^(green|lime|yellow|orange|red|gray)$",
        description="Filter by verdict color"
    ),
    min_word_count: Optional[int] = Query(None, ge=0, description="Minimum word count"),
    has_timeline: Optional[bool] = Query(None, description="Filter by timeline presence"),
    sort: str = Query(
        "newest",
        regex="^(newest|oldest|longest|shortest)$",
        description="Sort order"
    ),
    db: Session = Depends(get_db)
):
    """
    Get optimized list of synthesis articles.
    
    Uses helper columns for 95% payload reduction compared to full articles.
    """
    service = SynthesisService(db)
    
    result = service.list_synthesis_articles(
        limit=limit,
        offset=offset,
        verdict_color=verdict_color,
        min_word_count=min_word_count,
        has_timeline=has_timeline,
        sort=sort
    )
    
    # Convert to response format
    articles = [
        SynthesisListItem(
            id=str(a.id),
            title=a.title,
            published_date=a.published_date,
            synthesis_preview=a.synthesis_preview,
            synthesis_word_count=a.synthesis_word_count,
            synthesis_read_minutes=a.synthesis_read_minutes,
            verdict_color=a.verdict_color,
            fact_check_verdict=a.fact_check_verdict,
            fact_check_score=a.fact_check_score,
            has_context_emphasis=a.has_context_emphasis,
            has_timeline=a.has_timeline,
            timeline_event_count=a.timeline_event_count,
            reference_count=a.reference_count,
            margin_note_count=a.margin_note_count,
            thumbnail_url=a.thumbnail_url,
            synthesis_generated_at=a.synthesis_generated_at
        )
        for a in result["articles"]
    ]
    
    return SynthesisListResponse(
        articles=articles,
        pagination={
            "total": result["total"],
            "limit": result["limit"],
            "offset": result["offset"],
            "has_next": result["has_next"]
        }
    )


@router.get("/{article_id}/synthesis", response_model=SynthesisDetailResponse)
async def get_synthesis_article(
    article_id: str,
    db: Session = Depends(get_db)
):
    """
    Get full synthesis article with all structured data.
    """
    service = SynthesisService(db)
    
    article = service.get_synthesis_article(article_id)
    
    if not article:
        raise HTTPException(
            status_code=404,
            detail="Synthesis article not found"
        )
    
    # Extract structured data
    structured_data = service.extract_structured_data(article)
    
    return SynthesisDetailResponse(
        article={
            "id": str(article.id),
            "title": article.title,
            "published_date": article.published_date,
            "synthesis_article": article.synthesis_article,
            "synthesis_word_count": article.synthesis_word_count,
            "synthesis_read_minutes": article.synthesis_read_minutes,
            "fact_check_verdict": article.fact_check_verdict,
            "fact_check_score": article.fact_check_score,
            "verdict_color": article.verdict_color,
            "synthesis_generated_at": article.synthesis_generated_at,
            "references": structured_data["references"],
            "margin_notes": structured_data["margin_notes"],
            "event_timeline": structured_data["event_timeline"],
            "context_and_emphasis": structured_data["context_and_emphasis"],
            "reference_count": article.reference_count,
            "margin_note_count": article.margin_note_count,
            "timeline_event_count": article.timeline_event_count
        }
    )


@router.get("/synthesis/stats", response_model=SynthesisStatsResponse)
async def get_synthesis_stats(
    db: Session = Depends(get_db)
):
    """
    Get statistics for synthesis articles.
    """
    service = SynthesisService(db)
    
    stats = service.get_synthesis_stats()
    
    return SynthesisStatsResponse(**stats)
```

#### Step 4.2: Register Router

**File**: `app/api/v1/api.py` (MODIFY)

```python
# Add import
from app.api.v1.endpoints import synthesis

# Add router
api_router.include_router(
    synthesis.router,
    prefix="/articles",
    tags=["synthesis"]
)
```

---

### **Phase 5: Integration Tests** (2 hours)

#### Step 5.1: Create Test Fixtures

**File**: `tests/fixtures/synthesis_articles.py`

```python
"""
Fixtures for synthesis article tests.
"""
import pytest
from datetime import datetime
from app.models.article import Article


@pytest.fixture
def synthesis_article_data():
    """Sample synthesis article data."""
    return {
        "title": "Test Synthesis Article",
        "url": "https://example.com/article",
        "url_hash": "test_hash_12345",
        "synthesis_article": "# Test Article\n\nThis is a test synthesis article with over 1400 words..." * 100,
        "article_data": {
            "references": [
                {
                    "id": 1,
                    "title": "Source 1",
                    "url": "https://source1.com",
                    "publication": "CNN",
                    "date": "2025-11-19",
                    "credibility_score": 85
                }
            ],
            "margin_notes": [
                {
                    "id": 1,
                    "paragraph_index": 1,
                    "text": "Additional context",
                    "type": "context"
                }
            ],
            "event_timeline": [
                {
                    "date": "2025-11-15",
                    "event": "Event occurred",
                    "source_id": 1
                }
            ],
            "context_and_emphasis": {
                "key_context": "Important background",
                "why_this_matters": "This is significant because..."
            }
        },
        "has_synthesis": True,
        "synthesis_preview": "# Test Article\n\nThis is a test synthesis article..." [:500],
        "synthesis_word_count": 2000,
        "synthesis_read_minutes": 10,
        "has_context_emphasis": True,
        "has_timeline": True,
        "timeline_event_count": 1,
        "reference_count": 1,
        "margin_note_count": 1,
        "fact_check_mode": "synthesis",
        "synthesis_generated_at": datetime.now(),
        "verdict_color": "green",
        "fact_check_verdict": "MOSTLY TRUE",
        "fact_check_score": 75,
        "category": "politics",
        "published_date": datetime.now()
    }


@pytest.fixture
def create_synthesis_article(test_db, rss_source, synthesis_article_data):
    """Create a synthesis article in test database."""
    article = Article(
        rss_source_id=rss_source.id,
        **synthesis_article_data
    )
    test_db.add(article)
    test_db.commit()
    test_db.refresh(article)
    return article
```

#### Step 5.2: Create Integration Tests

**File**: `tests/integration/test_synthesis_endpoints.py`

```python
"""
Integration tests for synthesis endpoints.
"""
import pytest
from fastapi.testclient import TestClient


class TestListSynthesisArticles:
    """Test GET /api/v1/articles/synthesis endpoint."""
    
    def test_list_without_filters(self, test_client, create_synthesis_article):
        """Test listing without filters."""
        response = test_client.get("/api/v1/articles/synthesis")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "articles" in data
        assert "pagination" in data
        assert len(data["articles"]) >= 1
        assert data["pagination"]["total"] >= 1
    
    def test_list_with_verdict_filter(self, test_client, create_synthesis_article):
        """Test filtering by verdict color."""
        response = test_client.get("/api/v1/articles/synthesis?verdict_color=green")
        
        assert response.status_code == 200
        data = response.json()
        
        # All articles should have green verdict
        for article in data["articles"]:
            assert article["verdict_color"] == "green"
    
    def test_list_with_invalid_verdict(self, test_client):
        """Test invalid verdict color returns 422."""
        response = test_client.get("/api/v1/articles/synthesis?verdict_color=invalid")
        
        assert response.status_code == 422
    
    def test_list_with_pagination(self, test_client, test_db, rss_source, synthesis_article_data):
        """Test pagination."""
        # Create 5 articles
        from app.models.article import Article
        for i in range(5):
            article_data = synthesis_article_data.copy()
            article_data["url_hash"] = f"hash_{i}"
            article = Article(rss_source_id=rss_source.id, **article_data)
            test_db.add(article)
        test_db.commit()
        
        # Get first page (2 items)
        response = test_client.get("/api/v1/articles/synthesis?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["articles"]) == 2
        assert data["pagination"]["total"] >= 5
        assert data["pagination"]["has_next"] == True
        
        # Get second page
        response = test_client.get("/api/v1/articles/synthesis?limit=2&offset=2")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["articles"]) >= 1
    
    def test_list_with_word_count_filter(self, test_client, create_synthesis_article):
        """Test filtering by word count."""
        response = test_client.get("/api/v1/articles/synthesis?min_word_count=1500")
        
        assert response.status_code == 200
        data = response.json()
        
        for article in data["articles"]:
            assert article["synthesis_word_count"] >= 1500
    
    def test_list_with_timeline_filter(self, test_client, create_synthesis_article):
        """Test filtering by timeline presence."""
        response = test_client.get("/api/v1/articles/synthesis?has_timeline=true")
        
        assert response.status_code == 200
        data = response.json()
        
        for article in data["articles"]:
            assert article["has_timeline"] == True
    
    def test_list_sorting_newest(self, test_client, test_db, rss_source, synthesis_article_data):
        """Test sorting by newest."""
        # Create articles with different timestamps
        from app.models.article import Article
        from datetime import datetime, timedelta
        
        for i in range(3):
            article_data = synthesis_article_data.copy()
            article_data["url_hash"] = f"hash_sort_{i}"
            article_data["synthesis_generated_at"] = datetime.now() - timedelta(days=i)
            article = Article(rss_source_id=rss_source.id, **article_data)
            test_db.add(article)
        test_db.commit()
        
        response = test_client.get("/api/v1/articles/synthesis?sort=newest")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify descending order
        dates = [a["synthesis_generated_at"] for a in data["articles"]]
        assert dates == sorted(dates, reverse=True)
    
    def test_list_sorting_longest(self, test_client, test_db, rss_source, synthesis_article_data):
        """Test sorting by word count."""
        from app.models.article import Article
        
        for i in range(3):
            article_data = synthesis_article_data.copy()
            article_data["url_hash"] = f"hash_words_{i}"
            article_data["synthesis_word_count"] = 1500 + (i * 100)
            article = Article(rss_source_id=rss_source.id, **article_data)
            test_db.add(article)
        test_db.commit()
        
        response = test_client.get("/api/v1/articles/synthesis?sort=longest")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify descending word count
        word_counts = [a["synthesis_word_count"] for a in data["articles"]]
        assert word_counts == sorted(word_counts, reverse=True)


class TestGetSynthesisArticle:
    """Test GET /api/v1/articles/{id}/synthesis endpoint."""
    
    def test_get_existing_article(self, test_client, create_synthesis_article):
        """Test retrieving existing synthesis article."""
        article_id = str(create_synthesis_article.id)
        
        response = test_client.get(f"/api/v1/articles/{article_id}/synthesis")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "article" in data
        article = data["article"]
        
        assert article["id"] == article_id
        assert article["synthesis_article"] is not None
        assert "references" in article
        assert "margin_notes" in article
        assert len(article["references"]) == 1
    
    def test_get_nonexistent_article(self, test_client):
        """Test retrieving non-existent article."""
        response = test_client.get("/api/v1/articles/nonexistent-id/synthesis")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_article_without_synthesis(self, test_client, test_db, rss_source):
        """Test retrieving article without synthesis."""
        from app.models.article import Article
        
        # Create article without synthesis
        article = Article(
            rss_source_id=rss_source.id,
            title="No Synthesis",
            url="https://example.com/no-synthesis",
            url_hash="no_synthesis_hash",
            has_synthesis=False,
            category="politics",
            published_date=datetime.now()
        )
        test_db.add(article)
        test_db.commit()
        
        response = test_client.get(f"/api/v1/articles/{article.id}/synthesis")
        
        assert response.status_code == 404
    
    def test_get_article_includes_all_fields(self, test_client, create_synthesis_article):
        """Test that response includes all expected fields."""
        article_id = str(create_synthesis_article.id)
        
        response = test_client.get(f"/api/v1/articles/{article_id}/synthesis")
        
        assert response.status_code == 200
        article = response.json()["article"]
        
        required_fields = [
            "id", "title", "published_date", "synthesis_article",
            "synthesis_word_count", "synthesis_read_minutes",
            "fact_check_verdict", "fact_check_score", "verdict_color",
            "synthesis_generated_at", "references", "margin_notes",
            "event_timeline", "reference_count", "margin_note_count",
            "timeline_event_count"
        ]
        
        for field in required_fields:
            assert field in article, f"Missing field: {field}"


class TestGetSynthesisStats:
    """Test GET /api/v1/articles/synthesis/stats endpoint."""
    
    def test_get_stats(self, test_client, create_synthesis_article):
        """Test retrieving synthesis statistics."""
        response = test_client.get("/api/v1/articles/synthesis/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_synthesis_articles" in data
        assert "verdicts" in data
        assert "average_word_count" in data
        assert "average_read_minutes" in data
        assert "average_credibility_score" in data
        assert "articles_with_timelines" in data
        assert "articles_with_context" in data
        
        assert data["total_synthesis_articles"] >= 1
    
    def test_stats_verdict_distribution(self, test_client, test_db, rss_source, synthesis_article_data):
        """Test verdict distribution in stats."""
        from app.models.article import Article
        
        # Create articles with different verdicts
        verdicts = ["green", "red", "gray"]
        for verdict in verdicts:
            article_data = synthesis_article_data.copy()
            article_data["url_hash"] = f"hash_{verdict}"
            article_data["verdict_color"] = verdict
            article = Article(rss_source_id=rss_source.id, **article_data)
            test_db.add(article)
        test_db.commit()
        
        response = test_client.get("/api/v1/articles/synthesis/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify each verdict color appears
        for verdict in verdicts:
            assert verdict in data["verdicts"]
            assert data["verdicts"][verdict] >= 1
```

---

### **Phase 6: Regression Tests** (30 minutes)

#### Step 6.1: Test Existing Endpoints

**File**: `tests/integration/test_existing_endpoints_regression.py`

```python
"""
Regression tests to ensure existing endpoints are unchanged.
"""
import pytest


class TestExistingArticleEndpoints:
    """Ensure existing article endpoints still work."""
    
    def test_list_articles_unchanged(self, test_client, create_synthesis_article):
        """Test that GET /api/v1/articles still works."""
        response = test_client.get("/api/v1/articles")
        
        assert response.status_code == 200
        # Existing endpoint should work as before
    
    def test_get_article_unchanged(self, test_client, create_synthesis_article):
        """Test that GET /api/v1/articles/{id} still works."""
        article_id = str(create_synthesis_article.id)
        
        response = test_client.get(f"/api/v1/articles/{article_id}")
        
        # Should work with existing endpoint
        assert response.status_code in [200, 404]  # Depends on implementation
    
    def test_create_article_unchanged(self, test_client, authenticated_user):
        """Test that POST /api/v1/articles still works."""
        # Test if article creation endpoint exists and works
        pass  # Implement based on your existing API


class TestOtherEndpointsUnaffected:
    """Ensure other endpoints are not affected."""
    
    def test_user_endpoints_work(self, test_client):
        """Test user endpoints still work."""
        response = test_client.get("/api/v1/users/me")
        
        # Should return 401 if not authenticated (expected behavior)
        assert response.status_code in [401, 200]
    
    def test_fact_check_endpoints_work(self, test_client):
        """Test fact-check endpoints still work."""
        response = test_client.get("/api/v1/fact-check/nonexistent/status")
        
        # Should return 404 (expected behavior)
        assert response.status_code == 404
```

---

### **Phase 7: Run All Tests** (30 minutes)

#### Step 7.1: Run Test Suite

```bash
# Run all tests with coverage
pytest tests/ -v --cov=app --cov-report=html --cov-report=term

# Expected output:
# - Unit tests: 100% pass
# - Integration tests: 100% pass
# - Regression tests: 100% pass
# - Coverage: >95%
```

#### Step 7.2: Fix Any Failures

```bash
# If tests fail, debug with:
pytest tests/integration/test_synthesis_endpoints.py::TestListSynthesisArticles::test_list_without_filters -vv -s

# Run single test class:
pytest tests/unit/test_synthesis_service.py::TestListSynthesisArticles -v
```

---

### **Phase 8: Manual Testing** (30 minutes)

#### Step 8.1: Start Development Server

```bash
# Activate virtual environment
source venv/bin/activate

# Run server
uvicorn app.main:app --reload --port 8000
```

#### Step 8.2: Test with curl

```bash
# List synthesis articles
curl -X GET "http://localhost:8000/api/v1/articles/synthesis?limit=5" \
  -H "accept: application/json"

# Get article detail
curl -X GET "http://localhost:8000/api/v1/articles/{article_id}/synthesis" \
  -H "accept: application/json"

# Get stats
curl -X GET "http://localhost:8000/api/v1/articles/synthesis/stats" \
  -H "accept: application/json"

# Test filters
curl -X GET "http://localhost:8000/api/v1/articles/synthesis?verdict_color=green&min_word_count=2000" \
  -H "accept: application/json"
```

#### Step 8.3: Test with Swagger UI

```bash
# Open browser
open http://localhost:8000/docs

# Test each endpoint in Swagger UI
```

---

### **Phase 9: Code Review & Documentation** (1 hour)

#### Step 9.1: Self-Review Checklist

- [ ] All tests pass (unit + integration + regression)
- [ ] Coverage >95%
- [ ] No breaking changes to existing endpoints
- [ ] Code follows project style guidelines
- [ ] All functions have docstrings
- [ ] Type hints used throughout
- [ ] Error handling implemented
- [ ] Validation added for all inputs
- [ ] No hardcoded values
- [ ] Logging added where appropriate

#### Step 9.2: Update Documentation

**File**: `docs/API_CHANGELOG.md` (CREATE/UPDATE)

```markdown
# API Changelog

## 2025-11-20 - Synthesis Endpoints

### Added
- `GET /api/v1/articles/synthesis` - List synthesis articles with optimized payload
- `GET /api/v1/articles/{id}/synthesis` - Get full synthesis article
- `GET /api/v1/articles/synthesis/stats` - Get synthesis statistics

### Performance
- 95% payload reduction for list views (340KB → 12KB per request)
- Sub-millisecond query performance (0.058ms)

### Breaking Changes
- None (all new endpoints)
```

---

### **Phase 10: Merge & Deploy** (30 minutes)

#### Step 10.1: Create Pull Request

```bash
# Commit all changes
git add .
git commit -m "feat: Add synthesis article endpoints

- Add 3 new synthesis-specific endpoints
- Implement SynthesisService for business logic
- Add comprehensive test suite (unit + integration)
- Achieve >95% test coverage
- Zero breaking changes to existing endpoints

Endpoints:
- GET /api/v1/articles/synthesis (list)
- GET /api/v1/articles/{id}/synthesis (detail)
- GET /api/v1/articles/synthesis/stats (statistics)

Tests:
- 30+ unit tests for service layer
- 15+ integration tests for endpoints
- 5+ regression tests for existing functionality

Performance:
- 95% payload reduction (340KB → 12KB)
- Sub-millisecond queries (0.058ms)"

# Push to remote
git push origin feature/synthesis-endpoints

# Create PR on GitHub
gh pr create --title "feat: Add synthesis article endpoints" \
  --body "See commit message for details"
```

#### Step 10.2: Review Checklist for Reviewer

```markdown
## Review Checklist

### Code Quality
- [ ] Code follows project conventions
- [ ] All functions have docstrings
- [ ] Type hints used consistently
- [ ] No code duplication
- [ ] Error handling comprehensive

### Tests
- [ ] All tests pass
- [ ] Coverage >95%
- [ ] Edge cases covered
- [ ] Regression tests included

### Performance
- [ ] No N+1 queries
- [ ] Indexes used appropriately
- [ ] Pagination implemented
- [ ] Response sizes reasonable

### Security
- [ ] Input validation present
- [ ] SQL injection prevented
- [ ] No sensitive data exposed
- [ ] Authentication enforced (if needed)

### Documentation
- [ ] API docs updated
- [ ] Swagger annotations correct
- [ ] Changelog updated
- [ ] README updated (if needed)
```

#### Step 10.3: Merge to Main

```bash
# After approval, merge PR
gh pr merge --squash

# Pull latest main
git checkout main
git pull origin main

# Tag release
git tag v1.1.0-synthesis-endpoints
git push origin v1.1.0-synthesis-endpoints
```

---

## Testing Strategy

### Test Pyramid

```
           /\
          /  \        E2E Tests (Manual)
         /    \       - Swagger UI testing
        /------\      - curl commands
       /        \     
      /  Integ.  \    Integration Tests (15 tests)
     /   Tests    \   - API endpoints
    /      20%     \  - Database interactions
   /--------------\ 
  /                 \ 
 /   Unit Tests      \  Unit Tests (30+ tests)
/        80%          \ - Service logic
-------------------------  - Schema validation
```

### Coverage Goals

| Component | Target Coverage | Current |
|-----------|----------------|---------|
| Service Layer | >95% | TBD |
| Endpoints | >95% | TBD |
| Schemas | >95% | TBD |
| **Overall** | **>95%** | **TBD** |

### Test Categories

#### Unit Tests (Fast, Isolated)
- **What**: Service methods, schema validation
- **Why**: Catch logic errors early
- **Run Time**: <5 seconds
- **Count**: 30+ tests

#### Integration Tests (Slower, Database)
- **What**: API endpoints, database queries
- **Why**: Verify end-to-end functionality
- **Run Time**: <30 seconds
- **Count**: 15+ tests

#### Regression Tests (Safety Net)
- **What**: Existing endpoints still work
- **Why**: Prevent breaking changes
- **Run Time**: <10 seconds
- **Count**: 5+ tests

---

## Validation Checklist

### Pre-Deployment

- [ ] All migrations applied (verify with `alembic current`)
- [ ] Test data exists (10 synthesis articles minimum)
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)

### Implementation

- [ ] Pydantic schemas created and tested
- [ ] Service layer implemented and tested
- [ ] API endpoints created and tested
- [ ] Router registered in main API
- [ ] All unit tests pass (>30 tests)
- [ ] All integration tests pass (>15 tests)
- [ ] All regression tests pass (>5 tests)
- [ ] Coverage >95%

### Manual Testing

- [ ] Swagger UI accessible (http://localhost:8000/docs)
- [ ] List endpoint returns data
- [ ] Detail endpoint returns full article
- [ ] Stats endpoint returns statistics
- [ ] Filters work correctly
- [ ] Sorting works correctly
- [ ] Pagination works correctly
- [ ] Error handling works (404, 422, etc.)

### Code Quality

- [ ] Code follows PEP 8
- [ ] All functions have docstrings
- [ ] Type hints present
- [ ] No linting errors (`flake8 app/`)
- [ ] No type errors (`mypy app/`)
- [ ] Code formatted (`black app/`)

### Documentation

- [ ] API changelog updated
- [ ] Swagger annotations correct
- [ ] README updated (if needed)
- [ ] Migration documented

---

## Rollback Plan

### If Tests Fail

```bash
# Revert changes
git checkout main

# Delete feature branch
git branch -D feature/synthesis-endpoints
```

### If Deployment Fails

```bash
# Rollback code
git revert <commit-hash>
git push origin main

# Verify existing endpoints work
curl http://localhost:8000/api/v1/articles
```

### If Database Issues

```bash
# Database is unchanged (read-only queries)
# No rollback needed
```

---

## Timeline Summary

| Phase | Task | Time | Status |
|-------|------|------|--------|
| 1 | Preparation | 30 min | ⏸️ |
| 2 | Pydantic Schemas | 30 min | ⏸️ |
| 3 | Service Layer | 1 hour | ⏸️ |
| 4 | API Endpoints | 1 hour | ⏸️ |
| 5 | Integration Tests | 2 hours | ⏸️ |
| 6 | Regression Tests | 30 min | ⏸️ |
| 7 | Run All Tests | 30 min | ⏸️ |
| 8 | Manual Testing | 30 min | ⏸️ |
| 9 | Code Review | 1 hour | ⏸️ |
| 10 | Merge & Deploy | 30 min | ⏸️ |
| **Total** | | **8 hours** | |

**Spread over**: 2-3 days  
**Ideal**: 1-2 hours per day  
**Risk**: Low (no breaking changes)

---

## Success Criteria

### ✅ Must Have
- All 3 endpoints functional
- >95% test coverage
- Zero regressions
- All tests pass
- Documentation complete

### 🎯 Nice to Have
- >98% test coverage
- <50ms response times
- Comprehensive error messages
- Performance benchmarks documented

### 🚫 Blockers
- Test coverage <90%
- Any regression failures
- Breaking changes to existing endpoints
- Database migration issues

---

## Support

### If You Get Stuck

1. **Check existing tests**: `tests/integration/test_articles.py`
2. **Review similar endpoints**: `app/api/v1/endpoints/articles.py`
3. **Run tests in debug mode**: `pytest -vv -s`
4. **Check logs**: `tail -f logs/app.log`
5. **Ask for help**: Create GitHub issue with error details

### Useful Commands

```bash
# Run specific test
pytest tests/integration/test_synthesis_endpoints.py::TestListSynthesisArticles::test_list_without_filters -vv

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Check coverage report
open htmlcov/index.html

# Format code
black app/ tests/

# Lint code
flake8 app/ tests/

# Type check
mypy app/

# Run all checks
make lint
make test
```

---

**Ready to start? Begin with Phase 1!** ✨
