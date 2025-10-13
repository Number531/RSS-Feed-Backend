# RSS News Aggregator - Backend

FastAPI backend for the RSS News Aggregator platform.

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- PostgreSQL 14+ (or Docker)
- Redis 7.0+ (or Docker)

### Setup

1. **Create and activate virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Copy environment file:**
```bash
cp .env.example .env
# Edit .env and set your configuration
```

4. **Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy the output and set it as SECRET_KEY in .env
```

5. **Start PostgreSQL and Redis (Docker):**
```bash
docker-compose -f docker/docker-compose.dev.yml up -d
```

6. **Run database migrations:**
```bash
alembic upgrade head
```

7. **Start the FastAPI server:**
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Optional: Start with web UIs for database/redis

```bash
docker-compose -f docker/docker-compose.dev.yml --profile tools up -d
```

This will start:
- **PgAdmin**: http://localhost:5050 (admin@rssfeed.com / admin)
- **Redis Commander**: http://localhost:8081

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/v1/           # API endpoints
│   ├── core/             # Configuration and security
│   ├── db/               # Database config
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── tasks/            # Celery tasks
│   └── utils/            # Utilities
├── alembic/              # Database migrations
├── tests/                # Test suite
├── docker/               # Docker configurations
└── requirements.txt      # Python dependencies
```

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_main.py

# Run integration tests only
pytest -m integration

# Run unit tests only
pytest -m unit
```

## 📊 Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show migration history
alembic history

# Show current revision
alembic current
```

## 🔧 Development Tools

### Code Formatting
```bash
# Format code with Black
black app/

# Sort imports with isort
isort app/

# Run both
black app/ && isort app/
```

### Linting
```bash
# Lint with flake8
flake8 app/

# Type checking with mypy
mypy app/
```

## 🐳 Docker Commands

```bash
# Start services
docker-compose -f docker/docker-compose.dev.yml up -d

# Stop services
docker-compose -f docker/docker-compose.dev.yml down

# View logs
docker-compose -f docker/docker-compose.dev.yml logs -f

# Remove volumes (WARNING: deletes all data)
docker-compose -f docker/docker-compose.dev.yml down -v
```

## 🔑 Environment Variables

Key environment variables (see `.env.example` for full list):

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - JWT secret key (generate with `secrets.token_urlsafe(32)`)
- `DEBUG` - Enable debug mode (True/False)
- `ENVIRONMENT` - Environment name (development/production)

## 🚦 API Endpoints

### Core Endpoints
- `GET /` - Root health check
- `GET /health` - Detailed health check
- `GET /api/v1/` - API information

### Documentation
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc documentation

## 📝 Next Steps

After Phase 2 completion:
- Phase 3: RSS Feed Aggregation Module
- Phase 4: Complete REST API Implementation
- Phase 5: React Native Frontend
- Phase 6: Production Deployment

## 🤝 Contributing

See main project `CONTRIBUTING.md` for contribution guidelines.

## 📄 License

TBD
