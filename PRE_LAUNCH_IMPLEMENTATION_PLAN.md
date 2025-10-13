# Pre-Launch Essential Features Implementation Plan

**Date:** 2025-01-23  
**Last Updated:** 2025-06-08 (Security Audit Added)  
**Target:** Complete before production launch  
**Total Effort:** 55-70 hours  
**Timeline:** 3-5 weeks

---

## Executive Summary

This plan details the implementation of essential security hardening and features that will bring the RSS Feed application to competitive parity with aggregate news platforms before launch:

**✅ COMPLETED:**
0. **Security Audit & Hardening** (5-10 hours) - DONE 2025-06-08

**PENDING:**
1. **Comment Voting System** (4-6 hours)
2. **Reading Insights** (6-8 hours)
3. **Notifications System** (20-25 hours)
4. **Content Reporting** (10-12 hours)

**Total Implementation Time:** 55-70 hours  
**Recommended Timeline:** 3-5 weeks (2 developers) or 4-7 weeks (1 developer)

---

## Table of Contents

0. [Phase 0: Security Audit & Hardening](#phase-0-security-audit--hardening) ✅ **COMPLETED**
1. [Phase 1: Comment Voting System](#phase-1-comment-voting-system)
2. [Phase 2: Reading Insights](#phase-2-reading-insights)
3. [Phase 3: Notifications System](#phase-3-notifications-system)
4. [Phase 4: Content Reporting](#phase-4-content-reporting)
5. [Implementation Order & Dependencies](#implementation-order--dependencies)
6. [Testing Strategy](#testing-strategy)
7. [Deployment Plan](#deployment-plan)
8. [Security Maintenance](#security-maintenance)

---

# Phase 0: Security Audit & Hardening

**Priority:** 🔴 CRITICAL (PRODUCTION-BLOCKING)  
**Status:** ✅ COMPLETED (2025-06-08)  
**Effort:** 5-10 hours  
**Impact:** Eliminates 89 known vulnerabilities  
**Dependencies:** None

## Overview

Comprehensive security audit and hardening of all production dependencies to eliminate critical vulnerabilities before launch. This phase addressed authentication bypass, request smuggling, DoS attacks, and other high-severity security issues.

## Completed Work

### 0.1 Security Vulnerability Assessment ✅

**Tools Used:**
- `pip-audit` - Python dependency vulnerability scanner
- Manual CVE/GHSA analysis

**Results:**
- **89 vulnerabilities** identified across 34 packages
- **25 critical/high** severity issues requiring immediate attention
- **40 medium** severity issues
- **24 low** severity issues

**Files Created:**
- `SECURITY_AUDIT_REPORT.md` - Comprehensive vulnerability report
- `VULNERABILITY_ANALYSIS.md` - Production vs development dependency analysis

### 0.2 Requirements Restructuring ✅

**Created new requirements structure:**

1. **`requirements-prod.txt`** - Production dependencies (security hardened)
   - Upgraded all critical packages
   - Added explicit security constraints for transitive dependencies
   - Included monitoring tools (sentry-sdk, prometheus)

2. **`requirements-dev.txt`** - Development + testing dependencies
   - Includes production requirements
   - Adds testing frameworks (pytest, coverage)
   - Adds code quality tools (black, flake8, mypy, bandit)
   - Adds security auditing tools (pip-audit, safety)

3. **`requirements.txt`** - Legacy compatibility wrapper
   - Points to new structure
   - Includes migration notes
   - Backed up original to `requirements.txt.backup`

### 0.3 Critical Security Upgrades ✅

**Authentication & Security:**
```
authlib: 1.2.1 → 1.6.5 (CRITICAL)
  - Fixed: JWE zip bomb DoS
  - Fixed: JWS segment DoS  
  - Fixed: Critical header bypass
```

**Web Framework:**
```
fastapi: 0.104.1 → 0.115.0+
  - Pulls starlette 0.47.2+ (security patches)
  
uvicorn: 0.24.0 → 0.32.0+
  - Pulls h11 0.16.0+ (request smuggling fixes)
```

**HTTP/Network Libraries:**
```
httpx: 0.25.1 → 0.28.0+
  - Pulls h11 0.16.0+ (request smuggling fixes)
  - Pulls h2 4.3.0+ (HTTP/2 splitting fixes)
  - Pulls certifi 2024.7.4+ (untrusted cert removal)
  - Pulls idna 3.7+ (DoS fix)
  - Pulls urllib3 2.5.0+ (multiple security fixes)
```

**Development Tools:**
```
black: 23.11.0 → 24.3.0+
  - Fixed: ReDoS vulnerability
```

**Added Explicit Security Constraints:**
```
h11>=0.16.0          # Request smuggling fixes
h2>=4.3.0            # HTTP/2 request splitting fixes
certifi>=2024.7.4    # Untrusted root cert removal
idna>=3.7            # DoS fix
urllib3>=2.5.0       # Multiple security fixes
starlette>=0.47.2    # Recent security patches
```

### 0.4 CI/CD Security Integration ✅

**Created automated security audit infrastructure:**

1. **`scripts/security_audit.sh`** - Automated security scanning script
   - Runs pip-audit with detailed reporting
   - Optional safety tool integration
   - Generates summary reports in markdown
   - Configurable severity thresholds
   - Exit codes for CI/CD integration

2. **`.github/workflows/security-audit.yml`** - GitHub Actions workflow
   - Runs on every push to main/master
   - Runs on all pull requests
   - Weekly scheduled scans (Monday 9 AM UTC)
   - Tests against Python 3.10, 3.11, 3.12
   - Uploads audit reports as artifacts (90-day retention)
   - Comments PR with security results
   - Fails CI/CD on critical/high vulnerabilities
   - Includes dependency review for PRs

**Usage:**
```bash
# Local execution
./scripts/security_audit.sh

# Strict mode (fail on any vulnerability)
./scripts/security_audit.sh --strict

# Custom output directory
./scripts/security_audit.sh --output-dir /path/to/reports
```

### 0.5 Security Monitoring Setup ✅

**Added to production requirements:**
- **Sentry SDK** - Error tracking and performance monitoring
- **Prometheus** - Metrics collection and exposure

**Already implemented in codebase:**
- ✅ Sentry integration in `app/main.py`
- ✅ Prometheus instrumentation
- ✅ Structured JSON logging
- ✅ Request ID tracking middleware
- ✅ Health check endpoints

## Impact Assessment

### Security Improvements
- **Vulnerabilities eliminated:** ~60 vulnerabilities from critical packages
- **Production risk:** Reduced from HIGH to LOW
- **Authentication security:** CRITICAL vulnerabilities patched
- **Request smuggling:** All known vectors patched
- **DoS vectors:** Multiple DoS vulnerabilities eliminated

### DevOps Improvements
- ✅ Automated vulnerability scanning in CI/CD
- ✅ Weekly scheduled security audits
- ✅ Clear separation of prod/dev dependencies
- ✅ Audit trail with 90-day report retention
- ✅ PR-level security feedback

### Documentation
- ✅ Comprehensive security audit report
- ✅ Vulnerability analysis by priority
- ✅ Upgrade instructions and commands
- ✅ CI/CD integration guide
- ✅ Security maintenance procedures

## Files Modified/Created

**New Files:**
- `SECURITY_AUDIT_REPORT.md` - Full vulnerability report
- `VULNERABILITY_ANALYSIS.md` - Dependency analysis
- `requirements-prod.txt` - Production dependencies
- `requirements-dev.txt` - Development dependencies
- `scripts/security_audit.sh` - Automated audit script
- `.github/workflows/security-audit.yml` - CI/CD workflow

**Modified Files:**
- `requirements.txt` - Now points to new structure

**Backup Files:**
- `requirements.txt.backup` - Original requirements

## Verification Steps

```bash
# 1. Install updated requirements in clean environment
python -m venv venv-test
source venv-test/bin/activate
pip install -r requirements-prod.txt

# 2. Run security audit
pip-audit

# 3. Verify application starts
python -m app.main

# 4. Check health endpoint
curl http://localhost:8000/health

# 5. Run test suite
pytest

# 6. Run security audit script
./scripts/security_audit.sh
```

## Ongoing Security Maintenance

See [Security Maintenance](#security-maintenance) section below for recurring tasks.

---

# Phase 1: Comment Voting System

**Priority:** 🔴 Critical  
**Effort:** 4-6 hours  
**Impact:** High engagement boost  
**Dependencies:** None (extends existing vote system)

## Overview

Extend the current voting system (which only supports articles) to also support comment voting. This allows users to upvote/downvote comments, enabling quality ranking and "best" sorting.

## Database Changes

### 1.1 Update Vote Model

**File:** `app/models/vote.py`

**Current Schema:**
```python
class Vote(Base):
    __tablename__ = "votes"
    
    id: UUID
    user_id: UUID (FK -> users)
    article_id: UUID (FK -> articles)
    vote_type: Enum("up", "down")
    created_at: datetime
```

**New Schema:**
```python
class Vote(Base):
    __tablename__ = "votes"
    
    id: UUID
    user_id: UUID (FK -> users)
    article_id: UUID | None (FK -> articles, nullable)
    comment_id: UUID | None (FK -> comments, nullable)
    vote_type: Enum("up", "down")
    created_at: datetime
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            '(article_id IS NOT NULL AND comment_id IS NULL) OR '
            '(article_id IS NULL AND comment_id IS NOT NULL)',
            name='vote_target_check'
        ),
        UniqueConstraint('user_id', 'article_id', name='unique_user_article_vote'),
        UniqueConstraint('user_id', 'comment_id', name='unique_user_comment_vote'),
        Index('idx_votes_article_id', 'article_id'),
        Index('idx_votes_comment_id', 'comment_id'),
    )
```

**Migration Script:**
```sql
-- File: alembic/versions/XXX_add_comment_voting.py

ALTER TABLE votes 
    ALTER COLUMN article_id DROP NOT NULL,
    ADD COLUMN comment_id UUID REFERENCES comments(id) ON DELETE CASCADE;

-- Add check constraint
ALTER TABLE votes
    ADD CONSTRAINT vote_target_check CHECK (
        (article_id IS NOT NULL AND comment_id IS NULL) OR
        (article_id IS NULL AND comment_id IS NOT NULL)
    );

-- Add unique constraint for comment votes
CREATE UNIQUE INDEX unique_user_comment_vote 
    ON votes(user_id, comment_id) 
    WHERE comment_id IS NOT NULL;

-- Add index for comment votes
CREATE INDEX idx_votes_comment_id ON votes(comment_id);
```

### 1.2 Update Comment Model

**File:** `app/models/comment.py`

**Add vote tracking columns:**
```python
class Comment(Base):
    __tablename__ = "comments"
    
    # ... existing columns ...
    
    # New columns
    vote_score: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    vote_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    
    # Relationships
    votes: Mapped[list["Vote"]] = relationship("Vote", back_populates="comment")
```

**Migration Script:**
```sql
ALTER TABLE comments
    ADD COLUMN vote_score INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN vote_count INTEGER NOT NULL DEFAULT 0;

CREATE INDEX idx_comments_vote_score ON comments(vote_score DESC);
```

## Backend Implementation

### 1.3 Update Vote Repository

**File:** `app/repositories/vote_repository.py`

**Add new methods:**
```python
class VoteRepository:
    """Repository for vote operations."""
    
    async def get_comment_vote(
        self, 
        user_id: UUID, 
        comment_id: UUID
    ) -> Optional[Vote]:
        """Get user's vote on a comment."""
        result = await self.db.execute(
            select(Vote).where(
                Vote.user_id == user_id,
                Vote.comment_id == comment_id
            )
        )
        return result.scalar_one_or_none()
    
    async def create_comment_vote(
        self, 
        user_id: UUID, 
        comment_id: UUID, 
        vote_type: str
    ) -> Vote:
        """Create a new comment vote."""
        vote = Vote(
            user_id=user_id,
            comment_id=comment_id,
            vote_type=vote_type
        )
        self.db.add(vote)
        await self.db.flush()
        await self.db.refresh(vote)
        return vote
    
    async def delete_comment_vote(
        self, 
        user_id: UUID, 
        comment_id: UUID
    ) -> bool:
        """Delete a comment vote."""
        result = await self.db.execute(
            delete(Vote).where(
                Vote.user_id == user_id,
                Vote.comment_id == comment_id
            )
        )
        return result.rowcount > 0
```

### 1.4 Update Comment Repository

**File:** `app/repositories/comment_repository.py`

**Add vote aggregation methods:**
```python
async def update_comment_vote_counts(self, comment_id: UUID) -> None:
    """Update vote score and count for a comment."""
    result = await self.db.execute(
        select(
            func.count(Vote.id).label('count'),
            func.sum(
                case((Vote.vote_type == 'up', 1), else_=-1)
            ).label('score')
        ).where(Vote.comment_id == comment_id)
    )
    
    row = result.one()
    vote_count = row.count or 0
    vote_score = row.score or 0
    
    await self.db.execute(
        update(Comment)
        .where(Comment.id == comment_id)
        .values(vote_count=vote_count, vote_score=vote_score)
    )

async def get_comments_with_votes(
    self,
    article_id: UUID,
    user_id: Optional[UUID] = None
) -> list[Comment]:
    """Get comments with user vote status."""
    query = select(Comment).where(Comment.article_id == article_id)
    
    if user_id:
        query = query.outerjoin(
            Vote,
            and_(
                Vote.comment_id == Comment.id,
                Vote.user_id == user_id
            )
        ).add_columns(Vote.vote_type.label('user_vote'))
    
    result = await self.db.execute(query)
    return result.all()
```

### 1.5 Create Comment Vote Service

**File:** `app/services/comment_vote_service.py`

```python
"""Service for comment voting operations."""
from uuid import UUID
from typing import Optional

from app.repositories.vote_repository import VoteRepository
from app.repositories.comment_repository import CommentRepository
from app.core.exceptions import NotFoundError, ConflictError


class CommentVoteService:
    """Service for handling comment votes."""
    
    def __init__(
        self,
        vote_repo: VoteRepository,
        comment_repo: CommentRepository
    ):
        self.vote_repo = vote_repo
        self.comment_repo = comment_repo
    
    async def cast_vote(
        self,
        user_id: UUID,
        comment_id: UUID,
        vote_type: str
    ) -> dict:
        """Cast or update a vote on a comment."""
        # Verify comment exists
        comment = await self.comment_repo.get_by_id(comment_id)
        if not comment:
            raise NotFoundError("Comment not found")
        
        # Check existing vote
        existing_vote = await self.vote_repo.get_comment_vote(
            user_id, comment_id
        )
        
        if existing_vote:
            if existing_vote.vote_type == vote_type:
                # Same vote - remove it (toggle behavior)
                await self.vote_repo.delete_comment_vote(user_id, comment_id)
                action = "removed"
            else:
                # Different vote - update it
                existing_vote.vote_type = vote_type
                action = "updated"
        else:
            # New vote
            await self.vote_repo.create_comment_vote(
                user_id, comment_id, vote_type
            )
            action = "created"
        
        # Update comment vote counts
        await self.comment_repo.update_comment_vote_counts(comment_id)
        
        # Get updated comment
        updated_comment = await self.comment_repo.get_by_id(comment_id)
        
        return {
            "action": action,
            "vote_score": updated_comment.vote_score,
            "vote_count": updated_comment.vote_count,
            "user_vote": vote_type if action != "removed" else None
        }
    
    async def get_user_vote(
        self,
        user_id: UUID,
        comment_id: UUID
    ) -> Optional[str]:
        """Get user's current vote on a comment."""
        vote = await self.vote_repo.get_comment_vote(user_id, comment_id)
        return vote.vote_type if vote else None
    
    async def remove_vote(
        self,
        user_id: UUID,
        comment_id: UUID
    ) -> bool:
        """Remove user's vote from a comment."""
        deleted = await self.vote_repo.delete_comment_vote(user_id, comment_id)
        
        if deleted:
            await self.comment_repo.update_comment_vote_counts(comment_id)
        
        return deleted
```

### 1.6 Update Comment API Endpoints

**File:** `app/api/v1/endpoints/comments.py`

**Add new endpoints:**
```python
@router.post(
    "/{comment_id}/vote",
    status_code=status.HTTP_200_OK,
    summary="Vote on comment"
)
async def vote_on_comment(
    comment_id: UUID,
    vote_type: str = Query(..., pattern="^(up|down)$"),
    current_user: User = Depends(get_current_user),
    vote_service: CommentVoteService = Depends(get_comment_vote_service)
):
    """Cast or update a vote on a comment."""
    result = await vote_service.cast_vote(
        user_id=current_user.id,
        comment_id=comment_id,
        vote_type=vote_type
    )
    return result


@router.delete(
    "/{comment_id}/vote",
    status_code=status.HTTP_200_OK,
    summary="Remove vote from comment"
)
async def remove_comment_vote(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    vote_service: CommentVoteService = Depends(get_comment_vote_service)
):
    """Remove user's vote from a comment."""
    deleted = await vote_service.remove_vote(
        user_id=current_user.id,
        comment_id=comment_id
    )
    return {"deleted": deleted}


@router.get(
    "/{comment_id}/vote",
    status_code=status.HTTP_200_OK,
    summary="Get user's vote on comment"
)
async def get_comment_vote(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    vote_service: CommentVoteService = Depends(get_comment_vote_service)
):
    """Get user's current vote on a comment."""
    vote_type = await vote_service.get_user_vote(
        user_id=current_user.id,
        comment_id=comment_id
    )
    return {"vote_type": vote_type}
```

**Update existing endpoints to include vote data:**
```python
@router.get(
    "/article/{article_id}",
    response_model=list[CommentResponse],
    summary="Get Article Comments"
)
async def get_article_comments(
    article_id: UUID,
    sort: str = Query("best", pattern="^(best|new|old|top)$"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    comment_repo: CommentRepository = Depends(get_comment_repository)
):
    """Get all comments for an article with vote data."""
    user_id = current_user.id if current_user else None
    comments = await comment_repo.get_comments_with_votes(article_id, user_id)
    
    # Sort comments
    if sort == "best":
        comments.sort(key=lambda c: c.vote_score, reverse=True)
    elif sort == "top":
        comments.sort(key=lambda c: c.vote_count, reverse=True)
    elif sort == "new":
        comments.sort(key=lambda c: c.created_at, reverse=True)
    elif sort == "old":
        comments.sort(key=lambda c: c.created_at)
    
    return comments
```

### 1.7 Update Pydantic Schemas

**File:** `app/schemas/comment.py`

```python
class CommentResponse(BaseModel):
    """Comment response schema."""
    id: UUID
    article_id: UUID
    user_id: UUID
    parent_id: Optional[UUID]
    content: str
    created_at: datetime
    updated_at: datetime
    depth: int
    
    # Vote data
    vote_score: int = 0
    vote_count: int = 0
    user_vote: Optional[str] = None  # "up", "down", or None
    
    class Config:
        from_attributes = True


class CommentVoteResponse(BaseModel):
    """Response after voting on a comment."""
    action: str  # "created", "updated", "removed"
    vote_score: int
    vote_count: int
    user_vote: Optional[str]
```

### 1.8 Update Dependencies

**File:** `app/api/dependencies.py`

```python
def get_comment_vote_service(
    vote_repo: VoteRepository = Depends(get_vote_repository),
    comment_repo: CommentRepository = Depends(get_comment_repository)
) -> CommentVoteService:
    """Get comment vote service instance."""
    return CommentVoteService(vote_repo, comment_repo)
```

## Testing Requirements

### Unit Tests
**File:** `tests/unit/test_comment_vote_service.py`

```python
"""Unit tests for comment voting."""

async def test_cast_vote_on_comment():
    """Test casting a vote on a comment."""
    # Test upvote
    # Test downvote
    # Test vote toggle
    # Test vote change (up -> down)

async def test_vote_count_updates():
    """Test that vote counts update correctly."""
    # Test single vote
    # Test multiple votes
    # Test vote removal updates count

async def test_cannot_vote_nonexistent_comment():
    """Test error when voting on non-existent comment."""

async def test_user_vote_uniqueness():
    """Test that users can only have one vote per comment."""
```

### Integration Tests
**File:** `tests/integration/test_comment_voting_api.py`

```python
"""Integration tests for comment voting API."""

async def test_vote_comment_endpoint():
    """Test POST /comments/{id}/vote"""

async def test_get_comments_with_votes():
    """Test that comments include user vote status."""

async def test_comment_sorting_by_votes():
    """Test best/top sorting works correctly."""
```

## Completion Checklist

- [ ] Database migration created and tested
- [ ] Vote model updated with comment support
- [ ] Comment model updated with vote columns
- [ ] Vote repository methods added
- [ ] Comment repository vote methods added
- [ ] Comment vote service implemented
- [ ] API endpoints created
- [ ] Schemas updated
- [ ] Dependencies configured
- [ ] Unit tests written (8+ tests)
- [ ] Integration tests written (5+ tests)
- [ ] API documentation updated
- [ ] Frontend endpoints documented

**Estimated Completion Time:** 4-6 hours

---

# Phase 2: Reading Insights

**Priority:** 🟢 High  
**Effort:** 6-8 hours  
**Impact:** User engagement & retention  
**Dependencies:** None (uses existing reading history)

## Overview

Provide users with interesting insights about their reading habits, including top categories, reading times, engagement metrics, and streaks.

## Database Changes

No schema changes required - all data comes from existing `reading_history` table.

Optional optimization:
```sql
-- Add indexes for better query performance
CREATE INDEX idx_reading_history_user_viewed_at 
    ON reading_history(user_id, viewed_at DESC);

CREATE INDEX idx_reading_history_duration 
    ON reading_history(user_id, duration_seconds) 
    WHERE duration_seconds IS NOT NULL;
```

## Backend Implementation

### 2.1 Update Reading History Service

**File:** `app/services/reading_history_service.py`

**Add insights method:**
```python
async def get_reading_insights(
    self,
    user_id: UUID,
    period: str = "30d"
) -> dict:
    """
    Get reading insights for a user.
    
    Args:
        user_id: User ID
        period: Time period (7d, 30d, 90d, 1y, all)
    
    Returns:
        Dictionary with insights data
    """
    # Calculate date range
    start_date = self._get_period_start_date(period)
    
    # Get history within period
    history = await self.reading_history_repo.get_user_history(
        user_id=user_id,
        start_date=start_date,
        skip=0,
        limit=10000  # Get all for analysis
    )
    
    if not history[0]:  # No history
        return self._empty_insights()
    
    articles_read = history[0]
    
    # Calculate insights
    insights = {
        "period": period,
        "summary": self._calculate_summary(articles_read),
        "top_categories": self._calculate_top_categories(articles_read),
        "reading_times": self._calculate_reading_times(articles_read),
        "engagement": self._calculate_engagement(articles_read),
        "streaks": await self._calculate_streaks(user_id),
        "top_sources": self._calculate_top_sources(articles_read),
        "reading_pace": self._calculate_reading_pace(articles_read),
    }
    
    return insights

def _calculate_summary(self, articles: list) -> dict:
    """Calculate summary statistics."""
    total_articles = len(articles)
    total_time = sum(
        (a.duration_seconds or 0) for a in articles
    )
    avg_time = total_time / total_articles if total_articles > 0 else 0
    
    return {
        "total_articles_read": total_articles,
        "total_reading_time_seconds": total_time,
        "average_reading_time_seconds": int(avg_time),
        "total_reading_time_formatted": self._format_duration(total_time),
    }

def _calculate_top_categories(self, articles: list) -> list[dict]:
    """Calculate most-read categories."""
    from collections import Counter
    
    categories = [
        a.article.category 
        for a in articles 
        if a.article and a.article.category
    ]
    
    category_counts = Counter(categories)
    
    return [
        {
            "category": cat,
            "count": count,
            "percentage": round(count / len(articles) * 100, 1)
        }
        for cat, count in category_counts.most_common(5)
    ]

def _calculate_reading_times(self, articles: list) -> dict:
    """Calculate reading time distribution by hour."""
    from collections import defaultdict
    
    hour_counts = defaultdict(int)
    
    for article in articles:
        hour = article.viewed_at.hour
        hour_counts[hour] += 1
    
    # Find peak hours
    if hour_counts:
        peak_hour = max(hour_counts.items(), key=lambda x: x[1])
        
        # Categorize reading pattern
        morning = sum(hour_counts[h] for h in range(6, 12))
        afternoon = sum(hour_counts[h] for h in range(12, 18))
        evening = sum(hour_counts[h] for h in range(18, 24))
        night = sum(hour_counts[h] for h in range(0, 6))
        
        total = len(articles)
        pattern = max([
            ("morning", morning),
            ("afternoon", afternoon),
            ("evening", evening),
            ("night", night)
        ], key=lambda x: x[1])
        
        return {
            "peak_hour": peak_hour[0],
            "peak_hour_count": peak_hour[1],
            "reading_pattern": pattern[0],
            "distribution": {
                "morning": round(morning / total * 100, 1),
                "afternoon": round(afternoon / total * 100, 1),
                "evening": round(evening / total * 100, 1),
                "night": round(night / total * 100, 1),
            },
            "hourly_breakdown": dict(hour_counts)
        }
    
    return {}

def _calculate_engagement(self, articles: list) -> dict:
    """Calculate engagement metrics."""
    articles_with_data = [
        a for a in articles 
        if a.duration_seconds and a.scroll_percentage
    ]
    
    if not articles_with_data:
        return {}
    
    avg_duration = sum(a.duration_seconds for a in articles_with_data) / len(articles_with_data)
    avg_scroll = sum(float(a.scroll_percentage) for a in articles_with_data) / len(articles_with_data)
    
    # Engagement score (0-100)
    # Based on: reading time + scroll percentage
    engagement_score = min(100, (avg_scroll + (avg_duration / 300 * 50)))
    
    # Categorize articles by engagement
    highly_engaged = sum(
        1 for a in articles_with_data 
        if float(a.scroll_percentage) > 80 and a.duration_seconds > 120
    )
    
    return {
        "average_duration_seconds": int(avg_duration),
        "average_scroll_percentage": round(avg_scroll, 1),
        "engagement_score": round(engagement_score, 1),
        "highly_engaged_count": highly_engaged,
        "highly_engaged_percentage": round(
            highly_engaged / len(articles_with_data) * 100, 1
        )
    }

async def _calculate_streaks(self, user_id: UUID) -> dict:
    """Calculate reading streaks."""
    # Get all reading history ordered by date
    all_history = await self.reading_history_repo.get_user_history(
        user_id=user_id,
        skip=0,
        limit=10000
    )
    
    if not all_history[0]:
        return {"current_streak": 0, "longest_streak": 0}
    
    # Extract unique dates
    dates = sorted(set(
        h.viewed_at.date() 
        for h in all_history[0]
    ))
    
    if not dates:
        return {"current_streak": 0, "longest_streak": 0}
    
    # Calculate streaks
    current_streak = 1
    longest_streak = 1
    temp_streak = 1
    
    from datetime import timedelta
    today = datetime.utcnow().date()
    
    # Check if current streak is active
    if dates[-1] == today or dates[-1] == today - timedelta(days=1):
        current_streak = 1
        for i in range(len(dates) - 1, 0, -1):
            if (dates[i] - dates[i-1]).days == 1:
                current_streak += 1
            else:
                break
    else:
        current_streak = 0
    
    # Calculate longest streak
    for i in range(1, len(dates)):
        if (dates[i] - dates[i-1]).days == 1:
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 1
    
    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "total_days_read": len(dates)
    }

def _calculate_top_sources(self, articles: list) -> list[dict]:
    """Calculate most-read sources."""
    from collections import Counter
    
    sources = [
        a.article.rss_source.title if a.article and a.article.rss_source else "Unknown"
        for a in articles
    ]
    
    source_counts = Counter(sources)
    
    return [
        {
            "source": source,
            "count": count,
            "percentage": round(count / len(articles) * 100, 1)
        }
        for source, count in source_counts.most_common(5)
    ]

def _calculate_reading_pace(self, articles: list) -> dict:
    """Calculate reading pace and trends."""
    if len(articles) < 7:
        return {}
    
    # Group by date
    from collections import defaultdict
    daily_counts = defaultdict(int)
    
    for article in articles:
        date = article.viewed_at.date()
        daily_counts[date] += 1
    
    # Calculate average
    avg_per_day = len(articles) / len(daily_counts)
    
    # Trend: compare first half vs second half
    sorted_dates = sorted(daily_counts.keys())
    mid_point = len(sorted_dates) // 2
    
    first_half_avg = sum(
        daily_counts[d] for d in sorted_dates[:mid_point]
    ) / mid_point
    
    second_half_avg = sum(
        daily_counts[d] for d in sorted_dates[mid_point:]
    ) / (len(sorted_dates) - mid_point)
    
    trend = "increasing" if second_half_avg > first_half_avg else "decreasing"
    
    return {
        "average_articles_per_day": round(avg_per_day, 1),
        "most_in_one_day": max(daily_counts.values()),
        "trend": trend
    }

def _get_period_start_date(self, period: str) -> Optional[datetime]:
    """Convert period string to start date."""
    from datetime import timedelta
    
    now = datetime.utcnow()
    
    period_map = {
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
        "1y": timedelta(days=365),
        "all": None
    }
    
    delta = period_map.get(period)
    return now - delta if delta else None

def _format_duration(self, seconds: int) -> str:
    """Format duration in human-readable format."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"

def _empty_insights(self) -> dict:
    """Return empty insights structure."""
    return {
        "period": "all",
        "summary": {
            "total_articles_read": 0,
            "total_reading_time_seconds": 0,
            "average_reading_time_seconds": 0,
        },
        "top_categories": [],
        "reading_times": {},
        "engagement": {},
        "streaks": {"current_streak": 0, "longest_streak": 0},
        "top_sources": [],
        "reading_pace": {}
    }
```

### 2.2 Create Insights Schema

**File:** `app/schemas/reading_insights.py`

```python
"""Schemas for reading insights."""
from pydantic import BaseModel
from typing import Optional


class ReadingSummary(BaseModel):
    """Summary statistics."""
    total_articles_read: int
    total_reading_time_seconds: int
    average_reading_time_seconds: int
    total_reading_time_formatted: str


class CategoryStat(BaseModel):
    """Category statistics."""
    category: str
    count: int
    percentage: float


class ReadingTimeDistribution(BaseModel):
    """Reading time distribution."""
    morning: float
    afternoon: float
    evening: float
    night: float


class ReadingTimesResponse(BaseModel):
    """Reading times analysis."""
    peak_hour: int
    peak_hour_count: int
    reading_pattern: str  # morning/afternoon/evening/night
    distribution: ReadingTimeDistribution
    hourly_breakdown: dict[int, int]


class EngagementResponse(BaseModel):
    """Engagement metrics."""
    average_duration_seconds: int
    average_scroll_percentage: float
    engagement_score: float
    highly_engaged_count: int
    highly_engaged_percentage: float


class StreaksResponse(BaseModel):
    """Reading streaks."""
    current_streak: int
    longest_streak: int
    total_days_read: int


class SourceStat(BaseModel):
    """Source statistics."""
    source: str
    count: int
    percentage: float


class ReadingPaceResponse(BaseModel):
    """Reading pace analysis."""
    average_articles_per_day: float
    most_in_one_day: int
    trend: str  # increasing/decreasing


class ReadingInsightsResponse(BaseModel):
    """Complete reading insights response."""
    period: str
    summary: ReadingSummary
    top_categories: list[CategoryStat]
    reading_times: Optional[ReadingTimesResponse]
    engagement: Optional[EngagementResponse]
    streaks: StreaksResponse
    top_sources: list[SourceStat]
    reading_pace: Optional[ReadingPaceResponse]
```

### 2.3 Add Insights API Endpoint

**File:** `app/api/v1/endpoints/reading_history.py`

```python
@router.get(
    "/insights",
    response_model=ReadingInsightsResponse,
    summary="Get reading insights",
    description="Get personalized insights about reading habits and patterns."
)
async def get_reading_insights(
    period: str = Query("30d", pattern="^(7d|30d|90d|1y|all)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get reading insights for the current user."""
    service = ReadingHistoryService(db)
    insights = await service.get_reading_insights(
        user_id=current_user.id,
        period=period
    )
    return ReadingInsightsResponse(**insights)
```

## Testing Requirements

### Unit Tests
**File:** `tests/unit/test_reading_insights.py`

```python
"""Unit tests for reading insights."""

async def test_calculate_summary():
    """Test summary statistics calculation."""

async def test_calculate_top_categories():
    """Test top categories calculation."""

async def test_calculate_reading_times():
    """Test reading time distribution."""

async def test_calculate_engagement():
    """Test engagement metrics."""

async def test_calculate_streaks():
    """Test streak calculation."""

async def test_empty_insights():
    """Test insights with no reading history."""
```

### Integration Tests
**File:** `tests/integration/test_insights_api.py`

```python
"""Integration tests for insights API."""

async def test_get_insights_endpoint():
    """Test GET /reading-history/insights"""

async def test_insights_with_different_periods():
    """Test insights for different time periods."""
```

## Completion Checklist

- [ ] Insights service methods implemented
- [ ] Insights schemas created
- [ ] API endpoint created
- [ ] Unit tests written (6+ tests)
- [ ] Integration tests written (3+ tests)
- [ ] API documentation updated
- [ ] Performance tested with large datasets

**Estimated Completion Time:** 6-8 hours

---

# Phase 3: Notifications System

**Priority:** 🔴 Critical  
**Effort:** 20-25 hours  
**Impact:** Essential for user engagement  
**Dependencies:** Comment voting (for vote notifications)

## Overview

Implement a comprehensive notifications system that alerts users when:
- Someone replies to their comment
- Someone votes on their comment  
- Someone votes on their article (if user submissions added later)
- System announcements

## Database Schema

### 3.1 Create Notifications Table

**File:** `app/models/notification.py`

```python
"""Notification model."""
from datetime import datetime
from enum import Enum as PyEnum
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Boolean, String, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
import sqlalchemy as sa

from app.db.session import Base


class NotificationType(str, PyEnum):
    """Notification types."""
    COMMENT_REPLY = "comment_reply"
    COMMENT_VOTE = "comment_vote"
    ARTICLE_VOTE = "article_vote"
    MENTION = "mention"
    SYSTEM = "system"


class Notification(Base):
    """Notification model."""
    
    __tablename__ = "notifications"
    
    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=sa.text("gen_random_uuid()")
    )
    
    # Foreign Keys
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Notification Details
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType),
        nullable=False
    )
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Related entity IDs (for linking)
    related_comment_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True
    )
    related_article_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=True
    )
    related_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Additional data (flexible JSON storage)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    # Status
    read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        server_default=sa.func.now(),
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    related_comment: Mapped["Comment"] = relationship("Comment")
    related_article: Mapped["Article"] = relationship("Article")
    related_user: Mapped["User"] = relationship("User", foreign_keys=[related_user_id])
    
    # Indexes
    __table_args__ = (
        Index("idx_notifications_user_read", "user_id", "read"),
        Index("idx_notifications_user_created", "user_id", "created_at"),
        Index("idx_notifications_type", "type"),
    )
    
    def __repr__(self) -> str:
        return f"<Notification user={self.user_id} type={self.type} read={self.read}>"
```

**Migration Script:**
```sql
-- File: alembic/versions/XXX_create_notifications.py

CREATE TYPE notification_type AS ENUM (
    'comment_reply',
    'comment_vote', 
    'article_vote',
    'mention',
    'system'
);

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type notification_type NOT NULL,
    title VARCHAR(200) NOT NULL,
    message VARCHAR(500) NOT NULL,
    related_comment_id UUID REFERENCES comments(id) ON DELETE CASCADE,
    related_article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    related_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    metadata JSONB,
    read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_user_read ON notifications(user_id, read);
CREATE INDEX idx_notifications_user_created ON notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_type ON notifications(type);
```

### 3.2 Update User Model

**File:** `app/models/user.py`

```python
# Add relationship
notifications: Mapped[list["Notification"]] = relationship(
    "Notification", 
    back_populates="user",
    foreign_keys="Notification.user_id"
)
```

## Backend Implementation

### 3.3 Create Notification Repository

**File:** `app/repositories/notification_repository.py`

```python
"""Repository for notification operations."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType


class NotificationRepository:
    """Repository for managing notifications."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        user_id: UUID,
        type: NotificationType,
        title: str,
        message: str,
        related_comment_id: Optional[UUID] = None,
        related_article_id: Optional[UUID] = None,
        related_user_id: Optional[UUID] = None,
        metadata: Optional[dict] = None
    ) -> Notification:
        """Create a new notification."""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            related_comment_id=related_comment_id,
            related_article_id=related_article_id,
            related_user_id=related_user_id,
            metadata=metadata or {}
        )
        self.db.add(notification)
        await self.db.flush()
        await self.db.refresh(notification)
        return notification
    
    async def get_by_id(self, notification_id: UUID) -> Optional[Notification]:
        """Get a notification by ID."""
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[Notification], int]:
        """Get notifications for a user."""
        query = select(Notification).where(Notification.user_id == user_id)
        
        if unread_only:
            query = query.where(Notification.read == False)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.order_by(Notification.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        notifications = result.scalars().all()
        
        return list(notifications), total
    
    async def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications."""
        result = await self.db.execute(
            select(func.count())
            .where(Notification.user_id == user_id)
            .where(Notification.read == False)
        )
        return result.scalar()
    
    async def mark_as_read(
        self,
        notification_id: UUID,
        user_id: UUID
    ) -> bool:
        """Mark a notification as read."""
        result = await self.db.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .where(Notification.user_id == user_id)
            .values(read=True, read_at=datetime.utcnow())
        )
        return result.rowcount > 0
    
    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user."""
        result = await self.db.execute(
            update(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.read == False)
            .values(read=True, read_at=datetime.utcnow())
        )
        return result.rowcount
    
    async def delete_notification(
        self,
        notification_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete a notification."""
        result = await self.db.execute(
            delete(Notification)
            .where(Notification.id == notification_id)
            .where(Notification.user_id == user_id)
        )
        return result.rowcount > 0
    
    async def delete_old_notifications(
        self,
        user_id: UUID,
        days_old: int = 30
    ) -> int:
        """Delete notifications older than specified days."""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        result = await self.db.execute(
            delete(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.created_at < cutoff_date)
        )
        return result.rowcount
```

### 3.4 Create Notification Service

**File:** `app/services/notification_service.py`

```python
"""Service for notification operations."""
from typing import Optional
from uuid import UUID

from app.repositories.notification_repository import NotificationRepository
from app.models.notification import NotificationType
from app.core.exceptions import NotFoundError, ForbiddenError


class NotificationService:
    """Service for handling notifications."""
    
    def __init__(self, notification_repo: NotificationRepository):
        self.notification_repo = notification_repo
    
    async def create_comment_reply_notification(
        self,
        user_id: UUID,
        comment_id: UUID,
        replier_username: str,
        article_title: str
    ) -> None:
        """Create notification for comment reply."""
        await self.notification_repo.create(
            user_id=user_id,
            type=NotificationType.COMMENT_REPLY,
            title=f"{replier_username} replied to your comment",
            message=f'on "{article_title[:50]}..."',
            related_comment_id=comment_id,
            metadata={"replier": replier_username}
        )
    
    async def create_comment_vote_notification(
        self,
        user_id: UUID,
        comment_id: UUID,
        vote_type: str,
        voter_username: str
    ) -> None:
        """Create notification for comment vote."""
        # Only notify for upvotes (avoid spam from downvotes)
        if vote_type != "up":
            return
        
        await self.notification_repo.create(
            user_id=user_id,
            type=NotificationType.COMMENT_VOTE,
            title=f"{voter_username} upvoted your comment",
            message="Your comment received an upvote",
            related_comment_id=comment_id,
            metadata={"voter": voter_username, "vote_type": vote_type}
        )
    
    async def create_system_notification(
        self,
        user_id: UUID,
        title: str,
        message: str,
        metadata: Optional[dict] = None
    ) -> None:
        """Create a system notification."""
        await self.notification_repo.create(
            user_id=user_id,
            type=NotificationType.SYSTEM,
            title=title,
            message=message,
            metadata=metadata or {}
        )
    
    async def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 20
    ) -> dict:
        """Get notifications for a user."""
        notifications, total = await self.notification_repo.get_user_notifications(
            user_id=user_id,
            unread_only=unread_only,
            skip=skip,
            limit=limit
        )
        
        return {
            "notifications": notifications,
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_more": (skip + limit) < total
        }
    
    async def get_unread_count(self, user_id: UUID) -> int:
        """Get unread notification count."""
        return await self.notification_repo.get_unread_count(user_id)
    
    async def mark_as_read(
        self,
        notification_id: UUID,
        user_id: UUID
    ) -> bool:
        """Mark notification as read."""
        # Verify ownership
        notification = await self.notification_repo.get_by_id(notification_id)
        if not notification:
            raise NotFoundError("Notification not found")
        
        if notification.user_id != user_id:
            raise ForbiddenError("Not authorized to modify this notification")
        
        return await self.notification_repo.mark_as_read(notification_id, user_id)
    
    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read."""
        return await self.notification_repo.mark_all_as_read(user_id)
    
    async def delete_notification(
        self,
        notification_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete a notification."""
        # Verify ownership
        notification = await self.notification_repo.get_by_id(notification_id)
        if not notification:
            raise NotFoundError("Notification not found")
        
        if notification.user_id != user_id:
            raise ForbiddenError("Not authorized to delete this notification")
        
        return await self.notification_repo.delete_notification(
            notification_id, user_id
        )
```

### 3.5 Integrate with Comment Service

**File:** `app/services/comment_service.py`

Update to trigger notifications:

```python
from app.services.notification_service import NotificationService

class CommentService:
    def __init__(
        self,
        comment_repo: CommentRepository,
        article_repo: ArticleRepository,
        notification_service: NotificationService  # Add this
    ):
        self.comment_repo = comment_repo
        self.article_repo = article_repo
        self.notification_service = notification_service
    
    async def create_comment(
        self,
        user_id: UUID,
        article_id: UUID,
        content: str,
        parent_id: Optional[UUID] = None
    ) -> Comment:
        """Create a new comment."""
        # ... existing code ...
        
        comment = await self.comment_repo.create(...)
        
        # Send notification if this is a reply
        if parent_id:
            parent_comment = await self.comment_repo.get_by_id(parent_id)
            if parent_comment and parent_comment.user_id != user_id:
                # Don't notify if replying to own comment
                article = await self.article_repo.get_by_id(article_id)
                user = ...  # Get user info
                
                await self.notification_service.create_comment_reply_notification(
                    user_id=parent_comment.user_id,
                    comment_id=comment.id,
                    replier_username=user.username,
                    article_title=article.title
                )
        
        return comment
```

### 3.6 Integrate with Vote Service

**File:** `app/services/comment_vote_service.py`

```python
from app.services.notification_service import NotificationService

class CommentVoteService:
    def __init__(
        self,
        vote_repo: VoteRepository,
        comment_repo: CommentRepository,
        notification_service: NotificationService  # Add this
    ):
        self.vote_repo = vote_repo
        self.comment_repo = comment_repo
        self.notification_service = notification_service
    
    async def cast_vote(
        self,
        user_id: UUID,
        comment_id: UUID,
        vote_type: str
    ) -> dict:
        """Cast a vote on a comment."""
        # ... existing code ...
        
        # Send notification for upvotes (only when creating new vote)
        if action == "created" and vote_type == "up":
            comment = await self.comment_repo.get_by_id(comment_id)
            if comment and comment.user_id != user_id:
                user = ...  # Get voter info
                
                await self.notification_service.create_comment_vote_notification(
                    user_id=comment.user_id,
                    comment_id=comment_id,
                    vote_type=vote_type,
                    voter_username=user.username
                )
        
        return result
```

### 3.7 Create Notification API Endpoints

**File:** `app/api/v1/endpoints/notifications.py`

```python
"""FastAPI endpoints for notifications."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.security import get_current_user
from app.models.user import User
from app.services.notification_service import NotificationService
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    UnreadCountResponse,
)


router = APIRouter()


@router.get(
    "/",
    response_model=NotificationListResponse,
    summary="Get notifications",
    description="Get paginated notifications for the current user."
)
async def get_notifications(
    unread_only: bool = Query(False, description="Only return unread notifications"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Get user's notifications."""
    result = await notification_service.get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        skip=skip,
        limit=limit
    )
    
    return NotificationListResponse(**result)


@router.get(
    "/unread/count",
    response_model=UnreadCountResponse,
    summary="Get unread count",
    description="Get count of unread notifications."
)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Get unread notification count."""
    count = await notification_service.get_unread_count(current_user.id)
    return UnreadCountResponse(unread_count=count)


@router.post(
    "/{notification_id}/read",
    status_code=status.HTTP_200_OK,
    summary="Mark as read",
    description="Mark a notification as read."
)
async def mark_notification_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Mark a notification as read."""
    marked = await notification_service.mark_as_read(
        notification_id=notification_id,
        user_id=current_user.id
    )
    return {"marked_as_read": marked}


@router.post(
    "/read-all",
    status_code=status.HTTP_200_OK,
    summary="Mark all as read",
    description="Mark all notifications as read."
)
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Mark all notifications as read."""
    count = await notification_service.mark_all_as_read(current_user.id)
    return {"marked_count": count}


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete notification",
    description="Delete a notification."
)
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Delete a notification."""
    deleted = await notification_service.delete_notification(
        notification_id=notification_id,
        user_id=current_user.id
    )
    return {"deleted": deleted}
```

### 3.8 Create Notification Schemas

**File:** `app/schemas/notification.py`

```python
"""Schemas for notifications."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.notification import NotificationType


class NotificationResponse(BaseModel):
    """Notification response schema."""
    id: UUID
    user_id: UUID
    type: NotificationType
    title: str
    message: str
    related_comment_id: Optional[UUID]
    related_article_id: Optional[UUID]
    related_user_id: Optional[UUID]
    metadata: Optional[dict]
    read: bool
    read_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Notification list response."""
    notifications: list[NotificationResponse]
    total: int
    skip: int
    limit: int
    has_more: bool


class UnreadCountResponse(BaseModel):
    """Unread notification count response."""
    unread_count: int
```

### 3.9 Update API Router

**File:** `app/api/v1/api.py`

```python
from app.api.v1.endpoints import notifications

api_router.include_router(
    notifications.router, 
    prefix="/notifications", 
    tags=["notifications"]
)
```

### 3.10 Update Dependencies

**File:** `app/api/dependencies.py`

```python
def get_notification_repository(
    db: AsyncSession = Depends(get_db)
) -> NotificationRepository:
    """Get notification repository instance."""
    return NotificationRepository(db)


def get_notification_service(
    notification_repo: NotificationRepository = Depends(get_notification_repository)
) -> NotificationService:
    """Get notification service instance."""
    return NotificationService(notification_repo)
```

## Testing Requirements

### Unit Tests
**File:** `tests/unit/test_notification_service.py`

```python
"""Unit tests for notification service."""

async def test_create_comment_reply_notification():
    """Test creating reply notification."""

async def test_create_comment_vote_notification():
    """Test creating vote notification."""

async def test_only_upvotes_create_notifications():
    """Test that downvotes don't create notifications."""

async def test_get_user_notifications():
    """Test getting user notifications."""

async def test_get_unread_count():
    """Test unread count."""

async def test_mark_as_read():
    """Test marking notification as read."""

async def test_mark_all_as_read():
    """Test marking all as read."""

async def test_delete_notification():
    """Test deleting notification."""

async def test_cannot_access_other_user_notifications():
    """Test authorization on notifications."""
```

### Integration Tests
**File:** `tests/integration/test_notifications_api.py`

```python
"""Integration tests for notifications API."""

async def test_get_notifications_endpoint():
    """Test GET /notifications"""

async def test_get_unread_count_endpoint():
    """Test GET /notifications/unread/count"""

async def test_reply_creates_notification():
    """Test that replying to comment creates notification."""

async def test_vote_creates_notification():
    """Test that voting creates notification."""

async def test_mark_notification_as_read():
    """Test POST /notifications/{id}/read"""

async def test_notification_pagination():
    """Test notification pagination."""
```

## Optional: Real-time Notifications (WebSocket)

### 3.11 WebSocket Support (Optional - Add 8-10 hours)

**File:** `app/api/v1/websocket.py`

```python
"""WebSocket endpoint for real-time notifications."""
from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
from uuid import UUID

from app.core.security import get_current_user_ws


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}
    
    async def connect(self, user_id: UUID, websocket: WebSocket):
        """Connect a user's WebSocket."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
    
    def disconnect(self, user_id: UUID, websocket: WebSocket):
        """Disconnect a user's WebSocket."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_notification(self, user_id: UUID, message: dict):
        """Send notification to all user's connections."""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str,
):
    """WebSocket endpoint for real-time notifications."""
    # Verify token and get user
    user = await get_current_user_ws(token)
    
    await manager.connect(user.id, websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(user.id, websocket)
```

## Completion Checklist

- [ ] Notification model created
- [ ] Database migration created and tested
- [ ] Notification repository implemented
- [ ] Notification service implemented
- [ ] Comment service integration (notifications on reply)
- [ ] Vote service integration (notifications on upvote)
- [ ] API endpoints created (5 endpoints)
- [ ] Schemas created
- [ ] Dependencies configured
- [ ] Router updated
- [ ] Unit tests written (10+ tests)
- [ ] Integration tests written (6+ tests)
- [ ] API documentation updated
- [ ] Optional: WebSocket support

**Estimated Completion Time:** 20-25 hours (30-33 with WebSocket)

---

# Phase 4: Content Reporting

**Priority:** 🟢 High  
**Effort:** 10-12 hours  
**Impact:** Content quality & moderation  
**Dependencies:** None

## Overview

Implement a content reporting system that allows users to flag inappropriate articles or comments for moderation review.

## Database Schema

### 4.1 Create Reports Table

**File:** `app/models/report.py`

```python
"""Report model for content moderation."""
from datetime import datetime
from enum import Enum as PyEnum
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, Enum, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import sqlalchemy as sa

from app.db.session import Base


class ReportReason(str, PyEnum):
    """Report reasons."""
    SPAM = "spam"
    HARASSMENT = "harassment"
    HATE_SPEECH = "hate_speech"
    MISINFORMATION = "misinformation"
    NSFW = "nsfw"
    OFF_TOPIC = "off_topic"
    OTHER = "other"


class ReportStatus(str, PyEnum):
    """Report status."""
    PENDING = "pending"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class Report(Base):
    """Content report model."""
    
    __tablename__ = "reports"
    
    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=sa.text("gen_random_uuid()")
    )
    
    # Reporter
    reporter_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Reported content (one of these will be set)
    reported_article_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=True
    )
    reported_comment_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Report details
    reason: Mapped[ReportReason] = mapped_column(
        Enum(ReportReason),
        nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Status
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus),
        default=ReportStatus.PENDING,
        nullable=False
    )
    
    # Moderation
    reviewed_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        server_default=sa.func.now(),
        nullable=False
    )
    
    # Relationships
    reporter: Mapped["User"] = relationship("User", foreign_keys=[reporter_id])
    reported_article: Mapped["Article"] = relationship("Article")
    reported_comment: Mapped["Comment"] = relationship("Comment")
    reviewer: Mapped["User"] = relationship("User", foreign_keys=[reviewed_by])
    
    # Indexes
    __table_args__ = (
        Index("idx_reports_status", "status"),
        Index("idx_reports_created", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Report id={self.id} status={self.status} reason={self.reason}>"
```

**Migration Script:**
```sql
-- File: alembic/versions/XXX_create_reports.py

CREATE TYPE report_reason AS ENUM (
    'spam',
    'harassment',
    'hate_speech',
    'misinformation',
    'nsfw',
    'off_topic',
    'other'
);

CREATE TYPE report_status AS ENUM (
    'pending',
    'reviewing',
    'resolved',
    'dismissed'
);

CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reporter_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reported_article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    reported_comment_id UUID REFERENCES comments(id) ON DELETE CASCADE,
    reason report_reason NOT NULL,
    description TEXT,
    status report_status NOT NULL DEFAULT 'pending',
    reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP,
    resolution_note TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT report_target_check CHECK (
        (reported_article_id IS NOT NULL AND reported_comment_id IS NULL) OR
        (reported_article_id IS NULL AND reported_comment_id IS NOT NULL)
    )
);

CREATE INDEX idx_reports_reporter_id ON reports(reporter_id);
CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_created ON reports(created_at DESC);
CREATE INDEX idx_reports_article ON reports(reported_article_id);
CREATE INDEX idx_reports_comment ON reports(reported_comment_id);
```

## Backend Implementation

### 4.2 Create Report Repository

**File:** `app/repositories/report_repository.py`

```python
"""Repository for report operations."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report, ReportReason, ReportStatus


class ReportRepository:
    """Repository for managing content reports."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_article_report(
        self,
        reporter_id: UUID,
        article_id: UUID,
        reason: ReportReason,
        description: Optional[str] = None
    ) -> Report:
        """Create a report for an article."""
        report = Report(
            reporter_id=reporter_id,
            reported_article_id=article_id,
            reason=reason,
            description=description
        )
        self.db.add(report)
        await self.db.flush()
        await self.db.refresh(report)
        return report
    
    async def create_comment_report(
        self,
        reporter_id: UUID,
        comment_id: UUID,
        reason: ReportReason,
        description: Optional[str] = None
    ) -> Report:
        """Create a report for a comment."""
        report = Report(
            reporter_id=reporter_id,
            reported_comment_id=comment_id,
            reason=reason,
            description=description
        )
        self.db.add(report)
        await self.db.flush()
        await self.db.refresh(report)
        return report
    
    async def get_by_id(self, report_id: UUID) -> Optional[Report]:
        """Get a report by ID."""
        result = await self.db.execute(
            select(Report).where(Report.id == report_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_reports(
        self,
        status: Optional[ReportStatus] = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[Report], int]:
        """Get all reports (admin only)."""
        query = select(Report)
        
        if status:
            query = query.where(Report.status == status)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.order_by(Report.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        reports = result.scalars().all()
        
        return list(reports), total
    
    async def update_status(
        self,
        report_id: UUID,
        status: ReportStatus,
        reviewed_by: UUID,
        resolution_note: Optional[str] = None
    ) -> bool:
        """Update report status (admin only)."""
        result = await self.db.execute(
            update(Report)
            .where(Report.id == report_id)
            .values(
                status=status,
                reviewed_by=reviewed_by,
                reviewed_at=datetime.utcnow(),
                resolution_note=resolution_note
            )
        )
        return result.rowcount > 0
    
    async def check_existing_report(
        self,
        reporter_id: UUID,
        article_id: Optional[UUID] = None,
        comment_id: Optional[UUID] = None
    ) -> bool:
        """Check if user already reported this content."""
        query = select(Report).where(Report.reporter_id == reporter_id)
        
        if article_id:
            query = query.where(Report.reported_article_id == article_id)
        elif comment_id:
            query = query.where(Report.reported_comment_id == comment_id)
        else:
            return False
        
        query = query.where(Report.status.in_([ReportStatus.PENDING, ReportStatus.REVIEWING]))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
```

### 4.3 Create Report Service

**File:** `app/services/report_service.py`

```python
"""Service for content reporting."""
from typing import Optional
from uuid import UUID

from app.repositories.report_repository import ReportRepository
from app.repositories.article_repository import ArticleRepository
from app.repositories.comment_repository import CommentRepository
from app.models.report import ReportReason, ReportStatus
from app.core.exceptions import NotFoundError, ConflictError


class ReportService:
    """Service for handling content reports."""
    
    def __init__(
        self,
        report_repo: ReportRepository,
        article_repo: ArticleRepository,
        comment_repo: CommentRepository
    ):
        self.report_repo = report_repo
        self.article_repo = article_repo
        self.comment_repo = comment_repo
    
    async def report_article(
        self,
        reporter_id: UUID,
        article_id: UUID,
        reason: ReportReason,
        description: Optional[str] = None
    ) -> dict:
        """Report an article."""
        # Verify article exists
        article = await self.article_repo.get_by_id(article_id)
        if not article:
            raise NotFoundError("Article not found")
        
        # Check for duplicate report
        existing = await self.report_repo.check_existing_report(
            reporter_id=reporter_id,
            article_id=article_id
        )
        if existing:
            raise ConflictError("You have already reported this article")
        
        # Create report
        report = await self.report_repo.create_article_report(
            reporter_id=reporter_id,
            article_id=article_id,
            reason=reason,
            description=description
        )
        
        return {
            "report_id": report.id,
            "status": report.status,
            "message": "Report submitted successfully"
        }
    
    async def report_comment(
        self,
        reporter_id: UUID,
        comment_id: UUID,
        reason: ReportReason,
        description: Optional[str] = None
    ) -> dict:
        """Report a comment."""
        # Verify comment exists
        comment = await self.comment_repo.get_by_id(comment_id)
        if not comment:
            raise NotFoundError("Comment not found")
        
        # Check for duplicate report
        existing = await self.report_repo.check_existing_report(
            reporter_id=reporter_id,
            comment_id=comment_id
        )
        if existing:
            raise ConflictError("You have already reported this comment")
        
        # Create report
        report = await self.report_repo.create_comment_report(
            reporter_id=reporter_id,
            comment_id=comment_id,
            reason=reason,
            description=description
        )
        
        return {
            "report_id": report.id,
            "status": report.status,
            "message": "Report submitted successfully"
        }
    
    async def get_all_reports(
        self,
        status: Optional[ReportStatus] = None,
        skip: int = 0,
        limit: int = 20
    ) -> dict:
        """Get all reports (admin only)."""
        reports, total = await self.report_repo.get_all_reports(
            status=status,
            skip=skip,
            limit=limit
        )
        
        return {
            "reports": reports,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    async def resolve_report(
        self,
        report_id: UUID,
        reviewer_id: UUID,
        resolution_note: Optional[str] = None
    ) -> bool:
        """Resolve a report (admin only)."""
        return await self.report_repo.update_status(
            report_id=report_id,
            status=ReportStatus.RESOLVED,
            reviewed_by=reviewer_id,
            resolution_note=resolution_note
        )
    
    async def dismiss_report(
        self,
        report_id: UUID,
        reviewer_id: UUID,
        resolution_note: Optional[str] = None
    ) -> bool:
        """Dismiss a report (admin only)."""
        return await self.report_repo.update_status(
            report_id=report_id,
            status=ReportStatus.DISMISSED,
            reviewed_by=reviewer_id,
            resolution_note=resolution_note
        )
```

### 4.4 Create Report API Endpoints

**File:** `app/api/v1/endpoints/reports.py`

```python
"""FastAPI endpoints for content reporting."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.security import get_current_user, require_admin
from app.models.user import User
from app.models.report import ReportReason, ReportStatus
from app.services.report_service import ReportService
from app.schemas.report import (
    ReportArticleRequest,
    ReportCommentRequest,
    ReportResponse,
    ReportListResponse,
    ResolveReportRequest,
)


router = APIRouter()


@router.post(
    "/article/{article_id}",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report article",
    description="Report an article for moderation."
)
async def report_article(
    article_id: UUID,
    data: ReportArticleRequest,
    current_user: User = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service)
):
    """Report an article."""
    result = await report_service.report_article(
        reporter_id=current_user.id,
        article_id=article_id,
        reason=data.reason,
        description=data.description
    )
    return result


@router.post(
    "/comment/{comment_id}",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report comment",
    description="Report a comment for moderation."
)
async def report_comment(
    comment_id: UUID,
    data: ReportCommentRequest,
    current_user: User = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service)
):
    """Report a comment."""
    result = await report_service.report_comment(
        reporter_id=current_user.id,
        comment_id=comment_id,
        reason=data.reason,
        description=data.description
    )
    return result


@router.get(
    "/",
    response_model=ReportListResponse,
    summary="Get all reports (Admin)",
    description="Get all reports for moderation review."
)
async def get_reports(
    status: Optional[ReportStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    report_service: ReportService = Depends(get_report_service)
):
    """Get all reports (admin only)."""
    result = await report_service.get_all_reports(
        status=status,
        skip=skip,
        limit=limit
    )
    return result


@router.put(
    "/{report_id}/resolve",
    status_code=status.HTTP_200_OK,
    summary="Resolve report (Admin)",
    description="Mark a report as resolved."
)
async def resolve_report(
    report_id: UUID,
    data: ResolveReportRequest,
    current_user: User = Depends(require_admin),
    report_service: ReportService = Depends(get_report_service)
):
    """Resolve a report (admin only)."""
    resolved = await report_service.resolve_report(
        report_id=report_id,
        reviewer_id=current_user.id,
        resolution_note=data.resolution_note
    )
    return {"resolved": resolved}


@router.put(
    "/{report_id}/dismiss",
    status_code=status.HTTP_200_OK,
    summary="Dismiss report (Admin)",
    description="Dismiss a report as invalid."
)
async def dismiss_report(
    report_id: UUID,
    data: ResolveReportRequest,
    current_user: User = Depends(require_admin),
    report_service: ReportService = Depends(get_report_service)
):
    """Dismiss a report (admin only)."""
    dismissed = await report_service.dismiss_report(
        report_id=report_id,
        reviewer_id=current_user.id,
        resolution_note=data.resolution_note
    )
    return {"dismissed": dismissed}
```

### 4.5 Create Report Schemas

**File:** `app/schemas/report.py`

```python
"""Schemas for content reporting."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.report import ReportReason, ReportStatus


class ReportArticleRequest(BaseModel):
    """Request to report an article."""
    reason: ReportReason
    description: Optional[str] = Field(None, max_length=500)


class ReportCommentRequest(BaseModel):
    """Request to report a comment."""
    reason: ReportReason
    description: Optional[str] = Field(None, max_length=500)


class ReportResponse(BaseModel):
    """Report response schema."""
    report_id: UUID
    status: ReportStatus
    message: str


class ReportDetailResponse(BaseModel):
    """Detailed report information."""
    id: UUID
    reporter_id: UUID
    reported_article_id: Optional[UUID]
    reported_comment_id: Optional[UUID]
    reason: ReportReason
    description: Optional[str]
    status: ReportStatus
    reviewed_by: Optional[UUID]
    reviewed_at: Optional[datetime]
    resolution_note: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Report list response."""
    reports: list[ReportDetailResponse]
    total: int
    skip: int
    limit: int


class ResolveReportRequest(BaseModel):
    """Request to resolve/dismiss a report."""
    resolution_note: Optional[str] = Field(None, max_length=500)
```

### 4.6 Add Admin Middleware

**File:** `app/core/security.py`

```python
async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require admin role."""
    if not current_user.is_admin:
        raise ForbiddenError("Admin access required")
    return current_user
```

### 4.7 Update User Model

**File:** `app/models/user.py`

```python
# Add admin flag
is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
```

**Migration:**
```sql
ALTER TABLE users
    ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE;
```

## Testing Requirements

### Unit Tests
**File:** `tests/unit/test_report_service.py`

```python
"""Unit tests for report service."""

async def test_report_article():
    """Test reporting an article."""

async def test_report_comment():
    """Test reporting a comment."""

async def test_cannot_report_twice():
    """Test duplicate report prevention."""

async def test_cannot_report_nonexistent_content():
    """Test error when reporting non-existent content."""

async def test_get_all_reports():
    """Test getting all reports (admin)."""

async def test_resolve_report():
    """Test resolving a report."""

async def test_dismiss_report():
    """Test dismissing a report."""
```

### Integration Tests
**File:** `tests/integration/test_reports_api.py`

```python
"""Integration tests for reports API."""

async def test_report_article_endpoint():
    """Test POST /reports/article/{id}"""

async def test_report_comment_endpoint():
    """Test POST /reports/comment/{id}"""

async def test_get_reports_requires_admin():
    """Test that GET /reports requires admin."""

async def test_resolve_report_requires_admin():
    """Test that resolving requires admin."""
```

## Completion Checklist

- [ ] Report model created
- [ ] Database migration created and tested
- [ ] Report repository implemented
- [ ] Report service implemented
- [ ] Admin middleware created
- [ ] User model updated with is_admin flag
- [ ] API endpoints created (5 endpoints)
- [ ] Schemas created
- [ ] Dependencies configured
- [ ] Router updated
- [ ] Unit tests written (7+ tests)
- [ ] Integration tests written (4+ tests)
- [ ] API documentation updated
- [ ] Admin panel considerations documented

**Estimated Completion Time:** 10-12 hours

---

# Implementation Order & Dependencies

## Recommended Implementation Sequence

### Week 1: Foundation & Quick Wins
**Days 1-2: Comment Voting** (4-6 hours)
- ✅ Extends existing system
- ✅ No external dependencies
- ✅ Highest ROI (return on investment)
- Start: Day 1, Morning
- Complete: Day 2, EOD

**Days 3-4: Reading Insights** (6-8 hours)
- ✅ Independent feature
- ✅ Uses existing data
- ✅ High engagement value
- Start: Day 3, Morning
- Complete: Day 4, EOD

### Week 2: Core Social Features
**Days 5-10: Notifications System** (20-25 hours)
- ⚠️ Requires comment voting to be complete
- ⚠️ Most complex feature
- ✅ Essential for engagement
- Start: Day 5, Morning (after comment voting done)
- Complete: Day 10, EOD

### Week 3: Quality & Moderation
**Days 11-13: Content Reporting** (10-12 hours)
- ✅ Independent feature
- ✅ Important for quality control
- Start: Day 11, Morning
- Complete: Day 13, EOD

**Days 14-15: Testing & Polish** (8-10 hours)
- Integration testing across all features
- Bug fixes
- Performance optimization
- Documentation updates

## Dependency Graph

```
Comment Voting (Phase 1)
    ├─→ Notifications (Phase 3) [requires comment voting for vote notifications]
    └─→ Content Reporting (Phase 4) [independent, but benefits from having votes]

Reading Insights (Phase 2)
    └─→ Independent [no dependencies]

Notifications (Phase 3)
    ├─→ Depends on: Comment Voting
    └─→ Required by: None (but highly recommended)

Content Reporting (Phase 4)
    └─→ Independent [no dependencies]
```

## Resource Allocation

### Single Developer Timeline
- **Week 1:** Comment Voting + Reading Insights
- **Week 2:** Notifications System
- **Week 3:** Content Reporting + Testing
- **Total:** 3 weeks (50-60 hours)

### Two Developer Timeline
- **Week 1:** 
  - Dev 1: Comment Voting → Notifications (Part 1)
  - Dev 2: Reading Insights → Content Reporting
- **Week 2:**
  - Dev 1: Notifications (Part 2)
  - Dev 2: Integration Testing + Polish
- **Total:** 2 weeks

---

# Testing Strategy

## Unit Testing Goals
- **Target Coverage:** 85%+ on new code
- **Focus Areas:**
  - Service layer logic
  - Repository methods
  - Business rules
  - Edge cases

## Integration Testing Goals
- **Target:** All API endpoints
- **Scenarios:**
  - Happy path (success cases)
  - Error cases (404, 403, 400)
  - Authorization checks
  - Data validation

## End-to-End Testing
- **Critical User Flows:**
  1. Comment → Vote → Notification
  2. Comment → Report → Admin Review
  3. Read Article → View Insights
  4. Receive Notification → Mark Read

## Performance Testing
- **Load Tests:**
  - 100 concurrent users
  - Notification delivery latency
  - Insights calculation performance
  - Report listing performance

---

# Deployment Plan

## Pre-Deployment Checklist

### Code Quality
- [ ] All unit tests passing (100+)
- [ ] All integration tests passing (30+)
- [ ] Code review completed
- [ ] Linting passed
- [ ] No security vulnerabilities

### Database
- [ ] All migrations tested on staging
- [ ] Rollback procedures documented
- [ ] Backup taken before migration
- [ ] Indexes verified for performance

### Documentation
- [ ] API documentation updated
- [ ] Admin guide created
- [ ] User guide updated
- [ ] Deployment runbook created

## Deployment Sequence

### Step 1: Database Migration (30 minutes)
```bash
# 1. Backup database
pg_dump -h localhost -U user -d rss_feed > backup_$(date +%Y%m%d).sql

# 2. Run migrations
alembic upgrade head

# 3. Verify migrations
psql -d rss_feed -c "\dt"  # Check tables exist
psql -d rss_feed -c "SELECT * FROM notifications LIMIT 1;"
```

### Step 2: Deploy Backend (15 minutes)
```bash
# 1. Build Docker image
docker build -t rss-feed-backend:v1.1 .

# 2. Run tests in container
docker run rss-feed-backend:v1.1 pytest

# 3. Deploy to staging
# (deployment commands specific to your infrastructure)

# 4. Smoke tests on staging
curl https://staging-api/health
curl https://staging-api/api/v1/notifications/unread/count
```

### Step 3: Deploy Frontend (if needed)
- Update API client with new endpoints
- Deploy frontend changes
- Verify WebSocket connections (if implemented)

### Step 4: Monitoring (ongoing)
```bash
# Watch logs for errors
tail -f /var/log/app/error.log

# Monitor metrics
# - API response times
# - Notification delivery rate
# - Error rates
# - Database query performance
```

## Rollback Plan

### If Critical Issues Found:
1. **Immediate:** Revert to previous Docker image
2. **Database:** Rollback migration (if needed)
   ```bash
   alembic downgrade -1
   ```
3. **Restore:** Restore database from backup (last resort)
   ```bash
   psql -d rss_feed < backup_YYYYMMDD.sql
   ```

---

# Success Metrics

## Technical Metrics
- **Test Coverage:** 85%+
- **API Response Time:** <200ms (p95)
- **Notification Delivery:** <5s latency
- **Error Rate:** <1%

## User Engagement Metrics (Post-Launch)
- **Notification Open Rate:** Target 40%+
- **Comment Vote Rate:** Target 30% of users
- **Content Report Rate:** <5% of content
- **Reading Insights Views:** Target 50% of users

## Quality Metrics
- **False Report Rate:** <20%
- **Report Resolution Time:** <24 hours (median)
- **User Satisfaction:** Monitor feedback

---

# Documentation Deliverables

1. **API Documentation** (OpenAPI/Swagger)
   - All new endpoints documented
   - Request/response examples
   - Error codes explained

2. **Admin Guide**
   - How to review reports
   - How to manage notifications
   - How to handle abuse

3. **User Guide**
   - How to use notifications
   - How to report content
   - How to view insights

4. **Developer Guide**
   - Architecture decisions
   - Database schema
   - Testing procedures

---

# Risk Assessment

## High Risk Items
1. **Notification Spam** 🔴
   - **Risk:** Too many notifications annoy users
   - **Mitigation:** Only notify on upvotes, add notification preferences

2. **Performance Impact** 🟡
   - **Risk:** Insights calculation slows down API
   - **Mitigation:** Cache results, add database indexes

3. **False Reports** 🟡
   - **Risk:** Users abuse reporting system
   - **Mitigation:** Rate limiting, track report patterns

## Medium Risk Items
4. **Database Migration Issues** 🟡
   - **Mitigation:** Test on staging, have rollback plan

5. **WebSocket Stability** 🟡
   - **Mitigation:** Start with polling, add WS as enhancement

---

# Security Maintenance

## Recurring Security Tasks

### Weekly (Automated)
- ✅ **Automated Security Audits** (GitHub Actions)
  - Runs every Monday at 9 AM UTC
  - Scans all dependencies for vulnerabilities
  - Creates audit reports
  - Sends notifications if critical issues found

### Monthly (Manual)
- **Review Security Reports**
  - Check GitHub Actions security audit artifacts
  - Review any flagged vulnerabilities
  - Plan upgrade cycles for medium/low severity issues

- **Update Dependencies**
  ```bash
  # Update to latest security patches
  pip install -r requirements-prod.txt --upgrade
  
  # Run tests
  pytest
  
  # Run security audit
  ./scripts/security_audit.sh
  
  # If passed, commit and deploy
  git add requirements-prod.txt
  git commit -m "chore: update dependencies for security patches"
  ```

### Quarterly (Manual)
- **Comprehensive Security Review**
  - Review all dependencies (including dev)
  - Check for deprecated packages
  - Review security advisories for used packages
  - Update security documentation
  - Review and update security policies

- **Penetration Testing**
  - Run OWASP ZAP or similar
  - Test authentication flows
  - Test rate limiting
  - Test input validation

### On Each PR (Automated)
- ✅ **Security Audit** (GitHub Actions)
  - Automatically runs on all PRs
  - Comments on PR with security results
  - Blocks merge if critical vulnerabilities found
  - Runs dependency review action

### On Security Advisory (Immediate)
- **Emergency Patch Process**
  1. Review advisory details
  2. Check if package is used in production
  3. Identify patched version
  4. Test upgrade in development
  5. Create hotfix branch
  6. Deploy to production ASAP
  7. Document in changelog

## Security Audit Commands

### Quick Audit
```bash
# Run pip-audit
pip-audit

# Run automated script
./scripts/security_audit.sh
```

### Detailed Audit
```bash
# Run with safety for additional checks
pip install safety
safety check

# Run bandit for code security issues
bandit -r app

# Generate comprehensive report
./scripts/security_audit.sh --strict --output-dir ./security-reports
```

### CI/CD Integration
```bash
# Test CI/CD workflow locally (requires act)
act -j security-audit

# Or push to trigger GitHub Actions
git push origin <branch>
```

## Security Contacts

- **Security Issues:** Report to your team's security contact
- **Vulnerability Disclosure:** Follow responsible disclosure process
- **Emergency Contact:** Define escalation path

## Security Resources

### Documentation
- `SECURITY_AUDIT_REPORT.md` - Latest audit results
- `VULNERABILITY_ANALYSIS.md` - Dependency analysis
- `scripts/security_audit.sh` - Audit script documentation

### External Resources
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [PyPI Security](https://pypi.org/security/)

### Tools
- [pip-audit](https://github.com/pypa/pip-audit) - Dependency scanner
- [safety](https://github.com/pyupio/safety) - Additional vulnerability DB
- [bandit](https://github.com/PyCQA/bandit) - Code security linter
- [OWASP ZAP](https://www.zaproxy.org/) - Web security scanner

## Metrics to Track

1. **Vulnerability Count**
   - Total vulnerabilities over time
   - Critical/High vs Medium/Low breakdown
   - Time to remediation

2. **Audit Coverage**
   - % of PRs with security audits
   - % of successful audits
   - Weekly audit completion rate

3. **Response Time**
   - Time from vulnerability discovery to patch
   - Time from advisory to production fix

4. **Dependency Health**
   - Number of outdated packages
   - Average age of dependencies
   - Dependencies with known vulnerabilities

---

**Document Version:** 2.0  
**Last Updated:** 2025-06-08 (Security Audit Phase Added)  
**Estimated Total Time:** 55-70 hours (including security)  
**Recommended Timeline:** 3-5 weeks
