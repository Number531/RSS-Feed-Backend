# Phase 3: Notification System - Quick Start Guide

## 🚀 Quick Implementation Steps

### Step 1: Database Migration (30 min)
```bash
# Create migration file
alembic revision -m "add notification system"

# Edit the migration file with provided schema
# Run migration
alembic upgrade head

# Verify
python -c "
from app.core.config import settings
from sqlalchemy import create_engine, text
engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))
with engine.connect() as conn:
    result = conn.execute(text('SELECT * FROM notifications LIMIT 1'))
    print('✅ notifications table exists')
"
```

### Step 2: Models (30 min)
```bash
# Create files
touch app/models/notification.py
touch app/models/notification_preferences.py

# Update app/models/__init__.py
# Add to imports and __all__

# Test
python -c "from app.models import Notification, NotificationPreferences; print('✅ Models imported')"
```

### Step 3: Schemas (30 min)
```bash
# Create files
touch app/schemas/notification.py
touch app/schemas/notification_preferences.py

# Test validation
python -c "
from app.schemas.notification import NotificationCreate
data = NotificationCreate(...)
print('✅ Schemas working')
"
```

### Step 4: Services (1.5 hours)
```bash
# Create files
touch app/services/notification_service.py
touch app/services/notification_preferences_service.py

# Create dependencies
touch app/api/dependencies.py  # Add get_notification_service

# Test
python -c "
from app.services.notification_service import NotificationService
print('✅ Services imported')
"
```

### Step 5: API Endpoints (1 hour)
```bash
# Create file
touch app/api/v1/endpoints/notifications.py

# Update app/api/v1/api.py
# Add router

# Test
curl http://localhost:8081/api/v1/notifications  # Should return 403 (auth required)
```

### Step 6: Integration (1 hour)
```bash
# Update existing services:
# - app/services/comment_vote_service.py
# - app/services/comment_service.py
# - app/api/v1/endpoints/auth.py

# Test Phase 1 still works
python test_voting_api.py  # Should still pass all 10 tests
```

### Step 7: Integration Tests (1.5 hours)
```bash
# Create test file
touch tests/integration/test_notification_system.py

# Run tests
pytest tests/integration/test_notification_system.py -v

# Should see 30+ tests passing
```

---

## 📋 Checklist

### Database
- [ ] Migration created
- [ ] Migration runs successfully
- [ ] Tables created with correct schema
- [ ] Indexes created
- [ ] Can rollback migration

### Models
- [ ] Notification model created
- [ ] NotificationPreferences model created
- [ ] Relationships added to User model
- [ ] Models import without errors
- [ ] Can create instances

### Schemas
- [ ] NotificationCreate schema
- [ ] NotificationResponse schema
- [ ] NotificationPreferencesUpdate schema
- [ ] NotificationPreferencesResponse schema
- [ ] Validation works correctly

### Services
- [ ] NotificationService implemented
- [ ] NotificationPreferencesService implemented
- [ ] All methods have docstrings
- [ ] Error handling implemented
- [ ] Pagination works

### API Endpoints
- [ ] GET /api/v1/notifications
- [ ] GET /api/v1/notifications/{id}
- [ ] GET /api/v1/notifications/unread/count
- [ ] PUT /api/v1/notifications/{id}/read
- [ ] PUT /api/v1/notifications/read-all
- [ ] DELETE /api/v1/notifications/{id}
- [ ] DELETE /api/v1/notifications/read
- [ ] GET /api/v1/notifications/preferences
- [ ] PUT /api/v1/notifications/preferences

### Integration
- [ ] Vote notifications working
- [ ] Reply notifications working
- [ ] Self-notifications prevented
- [ ] Preferences respected
- [ ] Default preferences created on registration
- [ ] Phase 1 tests still passing

### Tests
- [ ] Unit tests for models
- [ ] Unit tests for services
- [ ] Unit tests for schemas
- [ ] API integration tests
- [ ] Vote notification tests
- [ ] Reply notification tests
- [ ] Full system tests
- [ ] All 30+ tests passing

---

## 🧪 Testing Commands

```bash
# Test Phase 1 (should still pass)
python test_voting_api.py

# Test specific components
pytest tests/unit/test_notification_model.py -v
pytest tests/unit/test_notification_service.py -v
pytest tests/integration/test_notification_api.py -v

# Test everything
pytest tests/ -v

# Test with coverage
pytest tests/ --cov=app --cov-report=html
```

---

## 🔍 Verification Queries

```python
# Check notifications table
from app.core.config import settings
from sqlalchemy import create_engine, text

engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))
with engine.connect() as conn:
    # Count notifications
    result = conn.execute(text('SELECT COUNT(*) FROM notifications'))
    print(f"Total notifications: {result.scalar()}")
    
    # Count unread
    result = conn.execute(text('SELECT COUNT(*) FROM notifications WHERE is_read = false'))
    print(f"Unread notifications: {result.scalar()}")
    
    # Check preferences
    result = conn.execute(text('SELECT COUNT(*) FROM notification_preferences'))
    print(f"Users with preferences: {result.scalar()}")
```

---

## 🐛 Common Issues & Solutions

### Issue: Migration fails
**Solution**: Check if tables already exist, rollback and try again
```bash
alembic downgrade -1
alembic upgrade head
```

### Issue: Models not importing
**Solution**: Make sure models are in `__init__.py`
```python
# app/models/__init__.py
from app.models.notification import Notification
from app.models.notification_preferences import NotificationPreferences
```

### Issue: Services not injecting
**Solution**: Add to dependencies
```python
# app/api/dependencies.py
def get_notification_service(db: AsyncSession = Depends(get_db)):
    return NotificationService(db)
```

### Issue: Phase 1 tests failing
**Solution**: Check if notification integration broke existing functionality
- Review vote service changes
- Review comment service changes
- Ensure dependencies are optional

### Issue: Notifications not created
**Solution**: Check preferences and service integration
```python
# Debug: Check if should_notify is being called
# Debug: Check if preferences exist for user
# Debug: Check if notification service is injected
```

---

## 📊 Success Indicators

After implementation, you should see:

```
✅ Phase 1 Tests: 10/10 passing
✅ Phase 3 Tests: 30+/30+ passing
✅ Database: 2 new tables created
✅ API: 9 new endpoints working
✅ Services: 2 new services implemented
✅ Models: 2 new models created
✅ Schemas: 5+ new schemas created
✅ Integration: Vote & reply notifications working
```

---

## 🎯 Next Steps After Phase 3

1. **Phase 4**: Implement article voting (similar to comments)
2. **Phase 5**: Add notification email delivery
3. **Phase 6**: Add real-time WebSocket notifications
4. **Phase 7**: Add @mention parsing and notifications

---

## 📞 Support

If you encounter issues:
1. Check the detailed plan: `PHASE_3_NOTIFICATION_PLAN.md`
2. Review error messages carefully
3. Test components in isolation
4. Verify Phase 1 still works

---

**Ready to begin? Start with Step 1!** 🚀
