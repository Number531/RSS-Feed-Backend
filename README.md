<div align="center">

# 📰 RSS Feed Backend API

**Production-Ready FastAPI Backend for RSS News Aggregation**

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Tests](https://img.shields.io/badge/tests-659%20passed-brightgreen.svg)](./tests)
[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen.svg)](./tests)
[![Security](https://img.shields.io/badge/security-audited-success.svg)](./SECURITY_AUDIT_REPORT.md)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

[Features](#-features) •
[Quick Start](#-quick-start) •
[API Docs](#-api-documentation) •
[Architecture](#-architecture) •
[Deployment](#-deployment) •
[Contributing](#-contributing)

</div>

---

## 🎯 Overview

A modern, production-ready FastAPI backend for RSS feed aggregation with Reddit-style features. Built with security, scalability, and developer experience in mind.

### ✨ Key Highlights

- **60 RESTful API Endpoints** - Comprehensive API coverage including search
- **44 RSS News Sources** - Diverse feeds across 10 categories
- **659 Tests Passing** - Enterprise-grade test coverage (95%+)
- **Enterprise Security** - Rate limiting, email verification, audit logging
- **JWT Authentication** - Secure token-based auth with refresh tokens
- **Reddit-Style Features** - Voting, comments, bookmarks
- **Full-Text Search** - PostgreSQL-powered content discovery
- **Real-Time Notifications** - WebSocket support
- **Production-Ready** - Security audited and deployment-ready
- **Comprehensive Docs** - 80+ documentation files

---

## 🚀 Features

### Core Functionality

<table>
<tr>
<td width="50%">

#### 🔐 Authentication & Security
- JWT access & refresh tokens
- Email/password authentication
- **Email verification system**
- **Rate limiting (3/min, 10/hour per IP)**
- **Strong password requirements**
- **Registration audit logging**
- User profiles & preferences
- Password reset flows

#### 📰 Content Management
- RSS feed aggregation
- Article categorization
- Full-text search & discovery
- Trending & popular articles
- Content deduplication

</td>
<td width="50%">

#### 💬 Social Features
- Reddit-style voting (up/down)
- Threaded comments
- Comment voting
- Real-time notifications

#### 📚 User Engagement
- Article bookmarks & collections
- Reading history tracking
- Personalized recommendations
- Reading time estimation

</td>
</tr>
</table>

### Technical Features

- **Async Architecture** - Built on FastAPI for high performance
- **PostgreSQL Database** - Robust data storage with Alembic migrations
- **Redis Caching** - Fast data access, session management, and rate limiting
- **Celery Workers** - Background task processing
- **Enterprise Security** - Rate limiting, email verification, password strength, audit logging
- **Production Hardening** - Config validators, security headers, request size limits (NEW)
- **Monitoring Ready** - Prometheus metrics & Sentry integration
- **CI/CD Pipelines** - Automated testing and deployment

### 🛡️ Middleware Stack (6 Layers)

1. **SecurityHeadersMiddleware** - Adds 5 security headers (X-Frame-Options, CSP, HSTS, etc.)
2. **RequestSizeLimitMiddleware** - Enforces 10MB limit, prevents DoS attacks
3. **RequestIDMiddleware** - Request tracking and tracing
4. **RateLimitMiddleware** - Per-IP rate limiting with Redis
5. **CORSMiddleware** - Cross-origin resource sharing
6. **PrometheusInstrumentatorMiddleware** - Metrics collection

---

## 📊 API Documentation

### Endpoint Overview

|| Category | Endpoints | Description |
||----------|-----------|-------------|
|| **Authentication** | 5 | Login, register, email verification, token refresh |
|| **Users** | 4 | Profile management, preferences |
|| **Articles** | 3 | Feed, search, article details |
|| **Search & Discovery** | 3 | Full-text search, trending, popular articles |
|| **RSS Feeds** | 8 | Listing, subscriptions, categories (44 active sources) |
|| **Votes** | 3 | Upvote/downvote articles |
|| **Comments** | 11 | CRUD, voting, threaded replies |
|| **Bookmarks** | 8 | Save, organize, manage collections |
|| **Reading History** | 8 | Track views, stats, recommendations |
|| **Notifications** | 9 | Real-time user notifications |
|| **Total** | **60** | Fully tested and documented |

### Interactive Documentation

Once running, explore the API at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

### For Frontend Developers

Complete API reference with TypeScript types:
- 📋 [Quick Reference Guide](./frontend-api-reference/01-API-QUICK-REFERENCE.md)
- 🔷 [TypeScript Types](./frontend-api-reference/02-TYPESCRIPT-TYPES.md)
- 📄 [OpenAPI Specification](./frontend-api-reference/03-OPENAPI-SPEC.md)

---

## 🔒 Security Features

### Enterprise-Grade Registration Security

Our user registration system implements multiple layers of security to protect against bot attacks, spam accounts, and unauthorized access:

#### 🛡️ Rate Limiting
- **Per-IP Rate Limits**: 3 registrations/minute, 10/hour
- **Redis-Backed**: Fast, distributed rate limit tracking
- **Proxy Support**: Handles X-Forwarded-For and X-Real-IP headers
- **Graceful Degradation**: Falls back safely if Redis is unavailable

#### 🔐 Strong Password Requirements
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit
- At least 1 special character
- Blocks 17+ common weak passwords ("password", "12345678", etc.)
- Prevents username similarity in passwords

#### 📧 Email Verification
- **Secure Token System**: 32-byte URL-safe tokens
- **Time-Limited**: 1-hour token expiration
- **Redis Storage**: Fast token validation
- **HTML + Text Emails**: Professional verification emails
- **Resend Protection**: Rate limited to 3/hour
- **Optional Mode**: Backward compatible (EMAIL_VERIFICATION_REQUIRED flag)

#### 📊 Registration Audit Logging
- **Complete Audit Trail**: Tracks all registration attempts (success + failure)
- **IP Address Tracking**: Identify bot patterns and abuse
- **User Agent Logging**: Detect automated registration attempts
- **Failure Reason Capture**: Debug issues and analyze security incidents
- **Database Storage**: Queryable audit logs with indexes
- **Compliance Ready**: GDPR/SOC2 audit trail support

### Additional Security Measures

- **JWT Authentication**: Secure token-based auth with refresh tokens
- **BCrypt Password Hashing**: Industry-standard password protection
- **Atomic Transactions**: Prevent data inconsistency and orphaned records
- **Race Condition Protection**: Database constraints + proper error handling
- **CORS Configuration**: Controlled cross-origin access
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries
- **Production Config Validation**: 7 critical checks + 3 warnings (NEW)
- **Security Headers**: 5 industry-standard headers (X-Frame-Options, CSP, etc.) (NEW)
- **Request Size Limits**: 10MB DoS protection (NEW)
- **Graph API Token Refresh**: 5-minute buffer prevents email failures (NEW)

### Security Test Coverage

- ✅ **51 Security-Focused Tests**
  - 26 tests for rate limiting & password validation
  - 16 tests for email verification system
  - 9 tests for service layer & audit logging
- ✅ **Integration Tests** for race conditions
- ✅ **Unit Tests** for all security components
- ✅ **659 Total Tests** with 95% coverage

For detailed security analysis, see [USER_REGISTRATION_ANALYSIS.md](./USER_REGISTRATION_ANALYSIS.md)

---

## 🏗️ Architecture

### System Design

```mermaid
graph TB
    Client["🌐 Client Apps<br/>(Web/Mobile)"]
    API["⚡ FastAPI<br/>Backend"]
    PG[("🐘 PostgreSQL<br/>Database")]
    Redis[("🔴 Redis<br/>Cache")]
    Celery["⚙️ Celery<br/>Workers"]
    
    Client -->|HTTPS/REST| API
    API -->|SQLAlchemy ORM| PG
    API -->|Cache/Sessions| Redis
    API -->|Queue Tasks| Celery
    Celery -->|Process RSS| PG
    Celery -->|Cache Results| Redis
    
    style API fill:#009688
    style Client fill:#2196F3
    style PG fill:#336791
    style Redis fill:#DC382D
    style Celery fill:#37A14C
```

### Project Structure

```
backend/
├── 📁 app/
│   ├── api/v1/           # 🔌 API endpoints (57 endpoints)
│   │   ├── endpoints/    # Route handlers
│   │   └── api.py        # API router aggregation
│   ├── core/             # ⚙️ Configuration & security
│   ├── db/               # 🗄️ Database session management
│   ├── models/           # 📊 SQLAlchemy models (9 models)
│   ├── schemas/          # 📋 Pydantic schemas (validation)
│   ├── services/         # 🎯 Business logic layer
│   ├── repositories/     # 💾 Data access layer
│   ├── tasks/            # ⏰ Celery background tasks
│   ├── middleware/       # 🔧 Request/response middleware
│   └── utils/            # 🛠️ Helper utilities
├── 📁 alembic/           # 🔄 Database migrations (4 migrations)
├── 📁 tests/             # 🧪 Test suite (135+ tests, 95% coverage)
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── 📁 frontend-api-reference/  # 📚 Frontend API docs
├── 📁 scripts/           # 🚀 Deployment & utility scripts
├── 📁 docker/            # 🐳 Docker configurations
└── 📄 requirements.txt   # 📦 Python dependencies
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system design.

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** - [Download](https://www.python.org/downloads/)
- **PostgreSQL 14+** - Database server
- **Redis 7.0+** - Caching & sessions
- **Docker** (optional) - For easy setup

### 1️⃣ Clone & Setup

```bash
# Clone repository
git clone https://github.com/Number531/RSS-Feed-Backend.git
cd RSS-Feed-Backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Generate secure keys
./scripts/setup/generate_secrets.sh

# Edit .env with your configuration
vim .env  # or nano, code, etc.
```

**Key variables to set:**
```env
DATABASE_URL=postgresql://user:pass@localhost/rss_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=<generated-secret>
JWT_SECRET_KEY=<generated-secret>
```

### 3️⃣ Start Services

**Option A: Docker (Recommended)**
```bash
# Start PostgreSQL + Redis + PgAdmin + Redis Commander
docker-compose -f docker/docker-compose.dev.yml --profile tools up -d
```

**Option B: Local Services**
```bash
# Start your local PostgreSQL and Redis instances
# Ensure they're running on the ports specified in .env
```

### 4️⃣ Initialize Database

```bash
# Run migrations
alembic upgrade head

# Seed with sample data (optional)
python scripts/database/seed_database.py
```

### 5️⃣ Run the Server

```bash
# Development server with auto-reload
uvicorn app.main:app --reload --port 8000

# Or use the provided script
./scripts/start_dev.sh
```

### 6️⃣ Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# Open interactive docs
open http://localhost:8000/docs
```

✅ **Success!** Your API is running at http://localhost:8000

---

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest

# With coverage report
pytest --cov=app --cov-report=html --cov-report=term

# Specific categories
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest tests/unit/          # Specific directory

# Watch mode (requires pytest-watch)
ptw -- --testmon
```

### Test Coverage

Current coverage: **95%**

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Manual API Testing

```bash
# Test scripts available
./scripts/testing/test_endpoints_complete.sh    # All endpoints
./scripts/testing/test_bookmark_api.sh          # Bookmarks
./scripts/utilities/test_voting_api.py          # Voting system
```

---

## 🔧 Development

### Code Quality Tools

```bash
# Format code
black app/
isort app/

# Linting
flake8 app/
pylint app/

# Type checking
mypy app/

# Security audit
bandit -r app/
safety check
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new feature"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# View history
alembic history
```

### Development Tools

Web UIs available when using Docker:
- **PgAdmin**: http://localhost:5050 (admin@rssfeed.com / admin)
- **Redis Commander**: http://localhost:8081

---

## 🚀 Deployment

### Staging Deployment

**Quick Start (30-60 minutes):**
```bash
# Follow the comprehensive guide
cat QUICK_START_STAGING.md
```

See [STAGING_DEPLOYMENT_READINESS.md](./STAGING_DEPLOYMENT_READINESS.md) for full checklist.

### Production Deployment

**Options:**
- **Docker** - See [docker-compose.prod.yml](./docker-compose.prod.yml)
- **Kubernetes** - Helm charts coming soon
- **Platform-as-a-Service** - Railway, Render, Fly.io compatible

**Pre-deployment checklist:**
- [ ] Run security audit: `./scripts/security_audit.sh`
- [ ] Verify tests pass: `pytest`
- [ ] Update environment variables (see production validators)
- [ ] ✨ **NEW: Review [PRODUCTION_READINESS_REVIEW.md](./PRODUCTION_READINESS_REVIEW.md)**
- [ ] Set `ENVIRONMENT=production` (triggers config validation)
- [ ] Change `ADMIN_PASSWORD` from default
- [ ] Generate strong `SECRET_KEY` (32+ chars)
- [ ] Use `https://` for `FRONTEND_URL`
- [ ] Enable `EMAIL_VERIFICATION_REQUIRED=true`
- [ ] Configure `SENTRY_DSN` for error tracking
- [ ] Set up monitoring (Sentry, Prometheus)
- [ ] Configure backups

See [PRODUCTION_READINESS_REVIEW.md](./PRODUCTION_READINESS_REVIEW.md) for comprehensive production hardening details.

---

## 📚 Documentation

### Essential Guides

- 📖 [Quick Start Staging](./QUICK_START_STAGING.md) - Deploy in 30-60 minutes
- 🔐 [Security Review](./SECURITY_REVIEW_CHECKLIST.md) - Security audit procedures
- 🏗️ [Architecture](./ARCHITECTURE.md) - System design details
- 🧪 [Testing Guide](./TEST_SUITE_SUMMARY.md) - Comprehensive testing
- 🚀 [Deployment Guide](./STAGING_DEPLOYMENT_GUIDE.md) - Full deployment
- 📊 [API Reference](./frontend-api-reference/README.md) - Frontend integration

### Complete Documentation

**80+ technical documents available** - See [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md)

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### Quick Contribution Guide

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Development Standards

- ✅ Write tests (maintain 95% coverage)
- ✅ Follow PEP 8 style guide
- ✅ Add docstrings to functions
- ✅ Update documentation
- ✅ Run linters before committing

---

## 🔒 Security

### Security Features

- ✅ JWT authentication with refresh tokens
- ✅ Password hashing with bcrypt
- ✅ CORS configuration
- ✅ Rate limiting (per-IP + Redis-backed)
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ XSS protection (security headers)
- ✅ **Production-grade security headers** (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, HSTS, CSP)
- ✅ **Request size limits** (10MB DoS protection)
- ✅ **Production config validators** (prevents insecure deployments)
- ✅ **Automated token refresh** (Graph API email reliability)
- ✅ Dependency vulnerability scanning

### Security Audit

**Status:** ✅ Audited and hardened

See [SECURITY_AUDIT_REPORT.md](./SECURITY_AUDIT_REPORT.md) for details.

### Reporting Vulnerabilities

Please report security vulnerabilities to: **security@example.com**

Do not open public issues for security concerns.

---

## 📊 Project Status

### Current State: **Production Ready** 🚀

| Component | Status | Coverage |
|-----------|--------|----------|
| API Endpoints | ✅ Complete | 60/60 |
| Test Suite | ✅ Passing | 95% |
| Security | ✅ **Production Hardened** | Strong |
| **Production Readiness** | ✅ **Enhanced** | **NEW** |
| Documentation | ✅ Comprehensive | 80+ docs |
| CI/CD | ✅ Automated | GitHub Actions |

### ✨ Latest Enhancement: Production Readiness (Nov 2025)

**Status**: All tests passed ✅ - [View Report](./PRODUCTION_READINESS_REVIEW.md)

- ✅ Production config validators (7 critical checks)
- ✅ Security headers middleware (5 headers)
- ✅ Request size limit middleware (10MB DoS protection)
- ✅ Dockerfile hardening (requirements-prod.txt)
- ✅ Graph API token refresh (5-min buffer)
- ✅ Comprehensive testing & documentation

### Roadmap

- [x] Phase 1: Core API Development
- [x] Phase 2: User Features (Auth, Profiles)
- [x] Phase 3: Social Features (Comments, Votes)
- [x] Phase 4: Advanced Features (Bookmarks, History)
- [x] Phase 5: Testing & Security Audit
- [ ] Phase 6: Production Deployment
- [ ] Phase 7: Mobile API Optimization
- [ ] Phase 8: GraphQL API Layer

---

## 🛠️ Tech Stack

### Core Technologies

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[SQLAlchemy](https://www.sqlalchemy.org/)** - ORM and database toolkit
- **[Alembic](https://alembic.sqlalchemy.org/)** - Database migrations
- **[Pydantic](https://pydantic-docs.helpmanual.io/)** - Data validation
- **[PostgreSQL](https://www.postgresql.org/)** - Primary database
- **[Redis](https://redis.io/)** - Caching and sessions

### Additional Tools

- **[Celery](https://docs.celeryq.dev/)** - Background task processing
- **[Pytest](https://pytest.org/)** - Testing framework
- **[Docker](https://www.docker.com/)** - Containerization
- **[Prometheus](https://prometheus.io/)** - Metrics and monitoring
- **[Sentry](https://sentry.io/)** - Error tracking

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](./LICENSE) file.

---

## 👥 Team & Support

### Maintainers

- Backend Lead: [@Number531](https://github.com/Number531)

### Getting Help

- 📖 **Documentation**: Start with [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/Number531/RSS-Feed-Backend/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/Number531/RSS-Feed-Backend/discussions)
- 📧 **Email**: support@example.com

### Acknowledgments

Built with modern Python best practices and influenced by:
- FastAPI official documentation
- Reddit API architecture
- Real Python tutorials
- Open source community

---

<div align="center">

**⭐ Star this repo if you find it useful!**

[Report Bug](https://github.com/Number531/RSS-Feed-Backend/issues) ·
[Request Feature](https://github.com/Number531/RSS-Feed-Backend/issues) ·
[Documentation](./DOCUMENTATION_INDEX.md)

</div>
