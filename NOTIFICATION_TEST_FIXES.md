# Notification Integration Test Fixes

## Summary

Fixed all 10 integration tests for the notification system by resolving two critical issues:
1. **Incorrect vote endpoint usage** in tests
2. **Event loop mismatch** when creating notifications

## Issues Found

### 1. Vote Endpoint Test Failures (3 tests affected)

**Problem:**
- Tests were calling `/api/v1/comments/vote` with JSON body containing `comment_id` and `vote_value`
- Actual endpoint is `/api/v1/comments/{comment_id}/vote?vote_type=upvote`

**Root Cause:**
Vote endpoint expects:
- Comment ID in URL path
- Vote type as query parameter (`upvote` or `downvote`)

**Tests Affected:**
- `test_comment_upvote_creates_notification`
- `test_own_vote_no_notification`  
- `test_downvote_no_notification`

**Solution:**
Updated all vote test calls to use correct endpoint format:
```python
# Before (incorrect):
vote_response = await client.post(
    "/api/v1/comments/vote",
    json={"comment_id": comment_id, "vote_value": 1},
    headers=auth_headers
)

# After (correct):
vote_response = await client.post(
    f"/api/v1/comments/{comment_id}/vote?vote_type=upvote",
    headers=auth_headers
)
```

### 2. Notification Creation Event Loop Mismatch (3 tests affected)

**Problem:**
- Notification service calls used `AsyncSessionLocal()` to create new database sessions
- This created sessions with different event loops than the test environment
- Led to `RuntimeError: Event loop is closed` and notifications not being created

**Root Cause:**
```python
# In comment_service.py and comment_vote_service.py (BEFORE):
async with AsyncSessionLocal() as notification_db:
    await NotificationService.create_reply_notification(
        db=notification_db,  # ❌ New session with different event loop
        ...
    )
```

**Tests Affected:**
- `test_comment_upvote_creates_notification` (notification not created)
- `test_comment_reply_creates_notification` (notification not created)
- `test_multiple_replies_create_multiple_notifications` (notifications not created)

**Solution:**
Reuse existing database session from repository instead of creating new one:

```python
# AFTER - comment_service.py:
db_session = self.comment_repo.db  # ✅ Reuse existing session
await NotificationService.create_reply_notification(
    db=db_session,
    recipient_id=parent_comment.user_id,
    actor_id=user_id,
    comment_id=comment.id,
    article_id=article_id
)

# AFTER - comment_vote_service.py:
db_session = self.vote_repo.db  # ✅ Reuse existing session
await NotificationService.create_vote_notification(
    db=db_session,
    recipient_id=comment.user_id,
    actor_id=user_id,
    entity_type='comment',
    entity_id=comment_id,
    vote_value=vote_value
)
```

### 3. Deprecation Warning Fix

**Problem:**
`Query(..., regex="...")` is deprecated in FastAPI/Pydantic v2

**Solution:**
```python
# Before:
vote_type: str = Query(..., regex="^(upvote|downvote)$")

# After:
vote_type: str = Query(..., pattern="^(upvote|downvote)$")
```

## Test Results

### Before Fixes:
- **3 failed**, 7 passed
- Failures: Vote notifications and reply notifications not being created
- Error: 405 Method Not Allowed on vote endpoint
- Error: Event loop closed / Future attached to different loop

### After Fixes:
- **10 passed**, 0 failed ✅
- All notification creation works correctly
- All vote endpoints work correctly
- No more event loop errors

## Files Modified

1. **tests/integration/test_notification_integrations.py**
   - Fixed vote endpoint calls to use correct URL format with query parameter

2. **app/services/comment_service.py**
   - Changed notification creation to reuse repository's db session instead of creating new one

3. **app/services/comment_vote_service.py**
   - Changed notification creation to reuse repository's db session instead of creating new one

4. **app/api/v1/endpoints/comments.py**
   - Fixed deprecation warning by replacing `regex` with `pattern` in Query parameter

## Key Takeaways

1. **Session Management in Async Code:**
   - Always reuse existing async sessions when possible
   - Creating new sessions can lead to event loop mismatches
   - In FastAPI/SQLAlchemy async contexts, pass sessions through dependency injection

2. **API Endpoint Testing:**
   - Always verify actual endpoint signatures before writing tests
   - URL path parameters vs query parameters vs request body are different

3. **Event Loop in Tests:**
   - Async test fixtures must use the same event loop as the code being tested
   - Creating new sessions with `AsyncSessionLocal()` can break this invariant

## Phase 3.5 Status

✅ **ALL INTEGRATION TESTS PASSING** (10/10)

- ✅ User registration creates default preferences (2 tests)
- ✅ Vote notifications (3 tests)
- ✅ Reply notifications (3 tests)
- ✅ Notification preferences (2 tests)

The notification system is now fully integrated and tested!
