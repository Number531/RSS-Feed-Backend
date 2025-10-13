# Phase 3: Notification System - Implementation Plan

## 🎯 Overview

Phase 3 implements a comprehensive notification system that alerts users when:
- Their comment receives an upvote/downvote
- Their comment receives a reply
- They are mentioned in a comment (optional enhancement)

**Implementation Strategy**: Modular, test-driven approach with isolated components that integrate seamlessly into the existing system.

---

## 📋 Architecture Design

### Component Structure
```
Phase 3: Notification System
├── Database Layer
│   ├── notifications table (migration)
│   └── notification_preferences table (migration)
├── Model Layer
│   ├── Notification model
│   └── NotificationPreferences model
├── Service Layer
│   ├── NotificationService (core logic)
│   └── NotificationPreferencesService
├── Schema Layer
│   ├── Notification schemas (Pydantic)
│   └── NotificationPreferences schemas
├── API Layer
│   └── Notifications endpoints
└── Integration Layer
    └── Event triggers (vote/comment events)
```

### Database Schema

**notifications table:**
```sql
- id: UUID (primary key)
- user_id: UUID (foreign key to users)
- notification_type: ENUM ('vote_received', 'comment_reply', 'mention')
- reference_id: UUID (ID of vote/comment that triggered notification)
- reference_type: ENUM ('vote', 'comment')
- message: VARCHAR(500)
- is_read: BOOLEAN (default false)
- created_at: TIMESTAMP
- read_at: TIMESTAMP (nullable)
```

**notification_preferences table:**
```sql
- id: UUID (primary key)
- user_id: UUID (foreign key to users, unique)
- notify_on_votes: BOOLEAN (default true)
- notify_on_replies: BOOLEAN (default true)
- notify_on_mentions: BOOLEAN (default true)
- email_notifications: BOOLEAN (default false)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

---

## 🔧 Implementation Steps

### **Step 1: Database Migration**
**File**: `alembic/versions/004_add_notification_system.py`

**Tasks**:
1. Create `notifications` table with indexes
2. Create `notification_preferences` table
3. Add enum types for notification_type and reference_type
4. Create indexes on user_id, is_read, created_at

**Success Criteria**:
- Migration runs without errors
- Tables created successfully
- Indexes properly configured
- Can be rolled back cleanly

**Test**: Direct SQL queries to verify schema

---

### **Step 2: Model Layer**
**Files**: 
- `app/models/notification.py`
- `app/models/notification_preferences.py`

**Tasks**:
1. Create Notification model with relationships
2. Create NotificationPreferences model
3. Add relationships to User model
4. Update models __init__.py

**Success Criteria**:
- Models can be imported without errors
- Relationships properly defined
- SQLAlchemy can create instances

**Test**: Unit tests for model instantiation

---

### **Step 3: Schema Layer**
**Files**:
- `app/schemas/notification.py`
- `app/schemas/notification_preferences.py`

**Schemas to Create**:
1. **NotificationCreate** (input)
2. **NotificationResponse** (output)
3. **NotificationList** (paginated list)
4. **NotificationPreferencesUpdate** (input)
5. **NotificationPreferencesResponse** (output)

**Success Criteria**:
- Schemas validate correctly
- Serialization/deserialization works
- Type hints are accurate

**Test**: Schema validation tests

---

### **Step 4: Service Layer - Core Logic**
**File**: `app/services/notification_service.py`

**Methods to Implement**:

```python
class NotificationService:
    # Creation
    async def create_notification(
        user_id: UUID,
        notification_type: str,
        reference_id: UUID,
        reference_type: str,
        message: str
    ) -> Notification
    
    # Retrieval
    async def get_user_notifications(
        user_id: UUID,
        unread_only: bool = False,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Notification], dict]
    
    async def get_notification_by_id(
        notification_id: UUID,
        user_id: UUID
    ) -> Notification
    
    # Updates
    async def mark_as_read(
        notification_id: UUID,
        user_id: UUID
    ) -> Notification
    
    async def mark_all_as_read(
        user_id: UUID
    ) -> int  # Returns count of marked notifications
    
    # Deletion
    async def delete_notification(
        notification_id: UUID,
        user_id: UUID
    ) -> bool
    
    async def delete_all_read(
        user_id: UUID
    ) -> int  # Returns count of deleted notifications
    
    # Statistics
    async def get_unread_count(
        user_id: UUID
    ) -> int
    
    # Preferences Check
    async def should_notify(
        user_id: UUID,
        notification_type: str
    ) -> bool
```

**Success Criteria**:
- All methods work independently
- Proper error handling
- Pagination works correctly
- Database queries optimized

**Test**: Unit tests for each method

---

### **Step 5: Service Layer - Preferences**
**File**: `app/services/notification_preferences_service.py`

**Methods to Implement**:

```python
class NotificationPreferencesService:
    async def get_preferences(
        user_id: UUID
    ) -> NotificationPreferences
    
    async def update_preferences(
        user_id: UUID,
        preferences_data: dict
    ) -> NotificationPreferences
    
    async def create_default_preferences(
        user_id: UUID
    ) -> NotificationPreferences
```

**Success Criteria**:
- Preferences created on user registration
- Updates work correctly
- Default values applied

**Test**: Unit tests for preferences management

---

### **Step 6: API Endpoints**
**File**: `app/api/v1/endpoints/notifications.py`

**Endpoints to Create**:

```python
# Get notifications
GET /api/v1/notifications
- Query params: page, page_size, unread_only
- Response: Paginated list of notifications

# Get single notification
GET /api/v1/notifications/{notification_id}
- Response: Single notification

# Get unread count
GET /api/v1/notifications/unread/count
- Response: { "count": 5 }

# Mark as read
PUT /api/v1/notifications/{notification_id}/read
- Response: Updated notification

# Mark all as read
PUT /api/v1/notifications/read-all
- Response: { "marked_count": 10 }

# Delete notification
DELETE /api/v1/notifications/{notification_id}
- Response: 204 No Content

# Delete all read
DELETE /api/v1/notifications/read
- Response: { "deleted_count": 5 }

# Get preferences
GET /api/v1/notifications/preferences
- Response: User's notification preferences

# Update preferences
PUT /api/v1/notifications/preferences
- Body: NotificationPreferencesUpdate
- Response: Updated preferences
```

**Success Criteria**:
- All endpoints properly authenticated
- Responses match schemas
- Error handling works
- Authorization enforced (users can only access their notifications)

**Test**: API integration tests

---

### **Step 7: Integration - Vote Notifications**
**File**: Update `app/services/comment_vote_service.py`

**Changes**:
1. Inject NotificationService dependency
2. After successful vote cast, check preferences
3. Create notification if enabled
4. Get comment author's user_id
5. Send notification

**Example Integration**:
```python
async def cast_vote(
    self,
    user_id: UUID,
    comment_id: UUID,
    vote_value: int
) -> Optional[Vote]:
    # Existing vote logic...
    vote = await self._cast_vote_logic(...)
    
    # NEW: Check if we should notify
    comment = await self._get_comment(comment_id)
    if comment.user_id != user_id:  # Don't notify self
        should_notify = await self.notification_service.should_notify(
            comment.user_id,
            "vote_received"
        )
        
        if should_notify:
            vote_type = "upvote" if vote_value == 1 else "downvote"
            await self.notification_service.create_notification(
                user_id=comment.user_id,
                notification_type="vote_received",
                reference_id=vote.id,
                reference_type="vote",
                message=f"Your comment received a {vote_type}"
            )
    
    return vote
```

**Success Criteria**:
- Notifications created on vote events
- No notifications for self-votes
- Preferences respected
- Doesn't break existing functionality

**Test**: Integration test for vote notification creation

---

### **Step 8: Integration - Reply Notifications**
**File**: Update `app/services/comment_service.py`

**Changes**:
1. Inject NotificationService dependency
2. After comment creation with parent_id
3. Check parent comment author preferences
4. Create notification if enabled

**Example Integration**:
```python
async def create_comment(
    self,
    user_id: UUID,
    article_id: UUID,
    content: str,
    parent_comment_id: Optional[UUID] = None
) -> Comment:
    # Existing comment logic...
    comment = await self._create_comment_logic(...)
    
    # NEW: Notify parent comment author
    if parent_comment_id:
        parent_comment = await self._get_comment(parent_comment_id)
        if parent_comment.user_id != user_id:  # Don't notify self
            should_notify = await self.notification_service.should_notify(
                parent_comment.user_id,
                "comment_reply"
            )
            
            if should_notify:
                await self.notification_service.create_notification(
                    user_id=parent_comment.user_id,
                    notification_type="comment_reply",
                    reference_id=comment.id,
                    reference_type="comment",
                    message=f"Someone replied to your comment"
                )
    
    return comment
```

**Success Criteria**:
- Notifications created on replies
- No notifications for self-replies
- Preferences respected
- Doesn't break existing functionality

**Test**: Integration test for reply notification creation

---

### **Step 9: Default Preferences on Registration**
**File**: Update `app/api/v1/endpoints/auth.py`

**Changes**:
1. Inject NotificationPreferencesService
2. After user registration, create default preferences

**Example**:
```python
@router.post("/register", ...)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    prefs_service: NotificationPreferencesService = Depends(...)
):
    # Existing registration logic...
    user = await create_user(...)
    
    # NEW: Create default notification preferences
    await prefs_service.create_default_preferences(user.id)
    
    return user
```

**Success Criteria**:
- Preferences created automatically
- Doesn't break registration
- Default values applied

**Test**: Registration integration test

---

### **Step 10: Comprehensive Integration Tests**
**File**: `tests/integration/test_notification_system.py`

**Test Scenarios**:

1. **Notification CRUD Operations**
   - Create notification
   - Get notifications (paginated)
   - Mark as read
   - Delete notification

2. **Notification Preferences**
   - Get default preferences
   - Update preferences
   - Preferences affect notification creation

3. **Vote Notification Flow**
   - User A votes on User B's comment
   - User B receives notification
   - Notification contains correct info
   - Self-votes don't create notifications

4. **Reply Notification Flow**
   - User A replies to User B's comment
   - User B receives notification
   - Notification contains correct info
   - Self-replies don't create notifications

5. **Preference Filtering**
   - Disable vote notifications
   - Vote on comment
   - No notification created

6. **Batch Operations**
   - Mark all as read
   - Delete all read notifications

7. **Unread Count**
   - Get unread count
   - Mark as read
   - Verify count decreases

8. **Authorization**
   - User can't access other user's notifications
   - User can't delete other user's notifications

**Success Criteria**:
- All tests pass
- 100% coverage of notification functionality
- No breaking changes to existing features

---

## 🧪 Testing Strategy

### Unit Tests (per component)
```bash
# Models
pytest tests/unit/test_notification_model.py
pytest tests/unit/test_notification_preferences_model.py

# Services
pytest tests/unit/test_notification_service.py
pytest tests/unit/test_notification_preferences_service.py

# Schemas
pytest tests/unit/test_notification_schemas.py
```

### Integration Tests (end-to-end)
```bash
# API endpoints
pytest tests/integration/test_notification_api.py

# Event triggers
pytest tests/integration/test_vote_notifications.py
pytest tests/integration/test_reply_notifications.py

# Full system
pytest tests/integration/test_notification_system.py
```

### Manual Testing Script
```bash
# Run comprehensive manual test
python test_notification_system_manual.py
```

---

## 📊 Database Indexes

**Optimize Query Performance**:
```sql
-- notifications table
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, is_read) 
    WHERE is_read = false;

-- notification_preferences table
CREATE UNIQUE INDEX idx_notification_prefs_user_id 
    ON notification_preferences(user_id);
```

---

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Manual testing complete
- [ ] Code review completed
- [ ] Database migration tested on staging

### Deployment Steps
1. **Backup Database**
2. **Run Migration**: `alembic upgrade head`
3. **Verify Migration**: Check tables exist
4. **Restart Server**: Apply code changes
5. **Run Smoke Tests**: Quick validation
6. **Monitor Logs**: Check for errors

### Post-Deployment
- [ ] Verify notifications created on votes
- [ ] Verify notifications created on replies
- [ ] Verify preferences work
- [ ] Check API response times
- [ ] Monitor database performance

---

## 🔄 Rollback Plan

If issues arise:

```bash
# Rollback database migration
alembic downgrade -1

# Revert code changes
git revert <commit-hash>

# Restart server
pkill -f "uvicorn app.main:app"
uvicorn app.main:app --reload
```

---

## 📈 Success Metrics

**After Implementation**:
- ✅ All 10 Phase 1 tests still passing
- ✅ 30+ new notification tests passing
- ✅ No performance degradation
- ✅ API response times < 200ms
- ✅ Database queries optimized
- ✅ Zero breaking changes

---

## 🎯 Implementation Timeline

**Estimated Time: 4-6 hours**

| Step | Component | Time | Dependencies |
|------|-----------|------|--------------|
| 1 | Database Migration | 30 min | None |
| 2 | Models | 30 min | Step 1 |
| 3 | Schemas | 30 min | Step 2 |
| 4 | Notification Service | 1 hour | Step 3 |
| 5 | Preferences Service | 30 min | Step 3 |
| 6 | API Endpoints | 1 hour | Steps 4-5 |
| 7 | Vote Integration | 30 min | Step 6 |
| 8 | Reply Integration | 30 min | Step 6 |
| 9 | Registration Integration | 15 min | Step 5 |
| 10 | Integration Tests | 1.5 hours | All steps |

---

## 🔧 Optional Enhancements (Phase 3.5)

**Can be added later**:
1. **Mention Notifications**: @username parsing
2. **Email Notifications**: Send emails for important events
3. **Push Notifications**: Mobile/browser push
4. **Notification Grouping**: Combine similar notifications
5. **Real-time Updates**: WebSocket support
6. **Notification Templates**: Customizable messages

---

## 📝 Notes

- **Modular Design**: Each component can be tested independently
- **Backward Compatible**: No breaking changes to existing APIs
- **Scalable**: Database indexes optimize for growth
- **Extensible**: Easy to add new notification types
- **User Control**: Preferences give users full control

---

## ✅ Ready to Implement!

This plan provides:
- ✅ Clear, step-by-step instructions
- ✅ Test-driven approach
- ✅ Modular implementation
- ✅ Zero breaking changes
- ✅ Production-ready code

**Next Step**: Begin with Step 1 - Database Migration
