# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Common Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
make install-dev          # Install all dev dependencies
make setup               # Full dev environment setup (includes DB migration)

# Start services (PostgreSQL + Redis + Admin tools)
docker-compose -f docker/docker-compose.dev.yml --profile tools up -d

# Initialize database
alembic upgrade head
python scripts/database/seed_database.py  # Optional sample data
```

### Running the Application
```bash
make run                 # Development server with auto-reload
# OR directly:
uvicorn app.main:app --reload --port 8000

# Verify installation
curl http://localhost:8000/health
```

### Testing Commands
```bash
# Run all tests with coverage
make test
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test categories
make test-unit           # Unit tests only
make test-integration    # Integration tests only
pytest -m unit          # Using pytest markers
pytest -m integration

# Run single test file or function
pytest tests/unit/test_article_service.py
pytest tests/integration/test_auth.py::test_login_success

# Watch mode for continuous testing
ptw -- --testmon
```

### Code Quality
```bash
make format              # Format with Black + isort
make lint               # Run flake8 + mypy
make clean              # Clean build artifacts

# Individual tools
black app/
isort app/
flake8 app/
mypy app/
bandit -r app/          # Security audit
```

### Database Operations
```bash
make db-upgrade          # Apply migrations
make db-downgrade       # Rollback last migration
make db-seed            # Add sample data

# Create new migration
alembic revision --autogenerate -m "Description of changes"
alembic history         # View migration history
```

### API Testing
```bash
# Comprehensive endpoint testing
./scripts/testing/test_endpoints_complete.sh
./scripts/testing/test_bookmark_api.sh
./scripts/utilities/test_voting_api.py

# Manual testing (requires running server)
python scripts/utilities/manual_testing.py
```

## Architecture Overview

### Layer-Based Architecture
This is a **layered FastAPI application** following clean architecture principles:

```
Client Request → API Layer → Service Layer → Repository Layer → Database
```

**Key Layers:**
- **API Layer** (`app/api/v1/endpoints/`) - HTTP request handling, validation, auth
- **Service Layer** (`app/services/`) - Business logic, transaction management, orchestration
- **Repository Layer** (`app/repositories/`) - Data access abstraction, queries
- **Model Layer** (`app/models/`) - SQLAlchemy ORM models and relationships

### Core Services Architecture
The application is built around **9 core services** that handle different domains:

1. **UserService** - Authentication, profiles, preferences
2. **ArticleService** - RSS feed processing, article CRUD
3. **CommentService** - Threaded comments, moderation
4. **VoteService** - Reddit-style voting for articles and comments
5. **BookmarkService** - Article bookmarking and collections
6. **NotificationService** - Real-time user notifications
7. **ReadingHistoryService** - Track user engagement, recommendations
8. **RSSFeedService** - Background RSS parsing and fetching
9. **CommentVoteService** - Specialized voting logic for comments

### Database Schema Pattern
**9 Main Models** with relationships:
- `User` → `Article` (1:many), `Comment` (1:many), `Vote` (1:many), `Bookmark` (1:many)
- `Article` → `Comment` (1:many), `Vote` (1:many), `Bookmark` (1:many)
- `Comment` → `Comment` (self-referential for threading), `Vote` (1:many)
- Plus: `RSSSource`, `ReadingHistory`, `Notification`, `UserReadingPreferences`

### Async Processing with Celery
**Background Tasks:**
- RSS feed fetching (every 15 minutes)
- Notification delivery (real-time queue)
- Reading stats aggregation (daily)
- Database cleanup (weekly)

## Development Patterns

### Service Layer Pattern
When adding new business logic, **always use the service layer**:

```python
# ✅ Correct - Business logic in service
class ArticleService:
    async def create_from_rss(self, feed_data: dict) -> Article:
        # 1. Validate & transform data
        # 2. Check for duplicates (repository call)
        # 3. Create article (repository call)
        # 4. Update cache
        # 5. Trigger notifications
        return article

# ❌ Incorrect - Business logic in endpoint
@router.post("/articles")
async def create_article(data: dict, db: Session):
    # Don't put business logic directly in endpoints
```

### Repository Pattern
Data access is abstracted through repositories:

```python
# ✅ Use repositories for data access
article = await self.article_repo.get_by_id(article_id)
articles = await self.article_repo.get_feed(category, page)

# ❌ Don't use ORM directly in services
article = await db.query(Article).filter(Article.id == article_id).first()
```

### Error Handling Strategy
The app uses **structured error handling**:
- Custom exceptions in `app/core/exceptions.py`
- Service layer raises domain-specific exceptions
- API layer converts to HTTP responses with proper status codes
- Sentry integration for production error tracking

### Authentication Pattern
JWT-based auth with refresh tokens:
- **Access tokens**: 15 minutes (for API calls)
- **Refresh tokens**: 7 days (stored in Redis)
- Middleware: `get_current_user` dependency for protected endpoints

## Testing Strategy

### Test Structure
```
tests/
├── unit/          # Fast, isolated tests for services/utils
├── integration/   # API endpoint tests with database
└── conftest.py    # Shared fixtures
```

### Test Categories (pytest markers)
- `@pytest.mark.unit` - Service logic, utilities
- `@pytest.mark.integration` - API endpoints, DB operations
- `@pytest.mark.slow` - Long-running tests (can skip with `-m "not slow"`)

### Key Test Fixtures
- `test_db` - Isolated test database session
- `test_client` - FastAPI test client
- `authenticated_user` - User with valid JWT token
- `sample_articles` - Pre-populated test data

### Test Patterns
```python
# Unit test example
@pytest.mark.unit
async def test_article_service_create():
    service = ArticleService(mock_repo)
    # Test business logic in isolation

# Integration test example  
@pytest.mark.integration
async def test_create_article_endpoint(test_client, authenticated_user):
    response = await test_client.post("/api/v1/articles", ...)
    # Test full API flow
```

## Configuration Management

### Environment Files
- `.env` - Local development (copy from `.env.example`)
- `.env.staging` - Staging environment
- Production uses environment variables directly

### Key Settings (app/core/config.py)
All configuration is centralized in `Settings` class using Pydantic:
- Database URLs, pool sizes
- JWT secrets and expiration times
- Redis configuration
- Rate limiting settings
- CORS origins
- External service APIs (Sentry, Supabase)

## Development Workflow

### Branch Strategy
- `main` - Production-ready code
- `feature/description` - New features
- `fix/description` - Bug fixes  
- `docs/description` - Documentation
- `refactor/description` - Code improvements

### Code Quality Requirements
- **95%+ test coverage** (enforced)
- **Black formatting** (88 character line limit)
- **Import sorting** with isort
- **Type hints** for all public functions
- **Docstrings** for all services and complex functions
- **Security scanning** with bandit and safety

### CI/CD Pipeline (GitHub Actions)
1. **On Push**: Run tests, linting, security scans
2. **On PR**: Integration tests, coverage check
3. **On Merge**: Build Docker image
4. **On Tag**: Deploy to production

## Production Deployment

### Docker Architecture
Multi-container setup:
- **API servers** (3 replicas)
- **PostgreSQL** database
- **Redis** cache  
- **Celery workers** (2 replicas)
- **Celery beat** scheduler

### Health Checks
- `/health` endpoint tests DB and Redis connectivity
- Prometheus metrics at `/metrics`
- Structured JSON logging
- Sentry error tracking

### Security Features
- JWT with refresh tokens
- Bcrypt password hashing
- CORS configuration
- Rate limiting middleware
- SQL injection protection (SQLAlchemy ORM)
- Security headers
- Dependency vulnerability scanning

## Common Troubleshooting

### Database Issues
```bash
# Reset database
alembic downgrade base
alembic upgrade head
python scripts/database/seed_database.py

# Check migration status  
alembic current
alembic history
```

### Redis Connection Issues
```bash
# Check Redis connectivity
redis-cli ping
# Or via Python
python -c "import redis; r=redis.Redis(); print(r.ping())"
```

### Test Failures
```bash
# Run specific failing test with verbose output
pytest tests/path/to/test.py::test_function -v -s

# Check test database state
pytest tests/integration/test_articles.py --pdb  # Drop into debugger
```

## File Structure Context

### Critical Directories
- `app/api/v1/endpoints/` - **9 endpoint modules** (auth, articles, comments, votes, bookmarks, etc.)
- `app/services/` - **Core business logic** - modify here for feature changes
- `app/repositories/` - **Database queries** - modify for data access changes  
- `app/models/` - **9 SQLAlchemy models** - modify for schema changes
- `scripts/` - **Utility scripts** for testing, deployment, database operations
- `alembic/versions/` - **Database migrations** - auto-generated, rarely edit directly

### Configuration Files
- `pyproject.toml` - **Tool configuration** (Black, pytest, mypy, coverage)
- `Makefile` - **Common commands** - use this for development tasks
- `requirements*.txt` - **Dependencies** split by environment
- `docker-compose*.yml` - **Container orchestration** for different environments

When working on this codebase, always follow the **layered architecture**: API → Service → Repository → Model. Use the service layer for business logic, repositories for data access, and keep endpoints thin with just validation and response formatting.