# Implementation Guide: New Analytics Endpoints

## Overview
Implementing 4 new endpoints:
1. `GET /articles/high-risk` - List high-risk articles
2. `GET /articles/{id}/source-breakdown` - Article source details
3. `GET /analytics/source-quality` - Source quality metrics
4. `GET /analytics/risk-correlation` - Risk vs credibility analysis

## Status

### ✅ Completed:
- Database migrations (source analysis fields)
- Schemas added to `app/schemas/analytics.py`
- Repository methods drafted in `app/repositories/analytics_repository_new_methods.py`

### ⏳ Remaining:
1. Append repository methods to `app/repositories/analytics_repository.py`
2. Add service methods to `app/services/analytics_service.py`
3. Add API endpoints to `app/api/v1/endpoints/analytics.py`
4. Write unit tests for repository methods
5. Write unit tests for service methods
6. Write integration tests for endpoints
7. Run all tests
8. Update `docs/ANALYTICS_API.md`
9. Copy to frontend docs
10. Commit and push

## Quick Implementation Commands

### Step 1: Append repository methods
```bash
# The methods are ready in analytics_repository_new_methods.py
# Need to copy lines 13-191 and append to analytics_repository.py
```

### Step 2-3: Service & Endpoints
Patterns established in existing code - follow same structure as:
- `get_source_reliability_stats` (service)
- `GET /analytics/sources` (endpoint)

### Step 4-6: Tests
Follow existing test patterns in:
- `tests/unit/test_analytics_repository.py`
- `tests/unit/test_analytics_service.py`
- `tests/integration/test_analytics_phase2a.py`

### Step 7: Run tests
```bash
pytest tests/unit/test_analytics*.py -v
pytest tests/integration/test_analytics*.py -v
```

### Step 8-9: Documentation
Add to `docs/ANALYTICS_API.md` following existing format

### Step 10: Deploy
```bash
black app/ tests/
git add -A
git commit -m "Add high-risk and source quality analytics endpoints"
git push
```

## Due to Token Constraints

This is a large implementation. I recommend:
1. Use the provided repository methods file as reference
2. Follow existing patterns in the codebase
3. Test incrementally
4. Or I can continue in a new conversation with this guide as context

Would you like me to continue with manual implementation or provide the specific code blocks needed?
