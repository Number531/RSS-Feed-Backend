# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- File reorganization with proper directory structure
- Comprehensive documentation in `docs/` directory
- MIT License
- Makefile for common development tasks
- GitHub issue and PR templates

## [1.0.0] - 2025-01-27

### Added
- Complete backend API implementation with 51 endpoints
- JWT authentication with access and refresh tokens
- Reddit-style features (voting, threaded comments)
- User management (registration, login, profiles, preferences)
- Article management (RSS feed aggregation, categorization, search)
- Bookmarks with collections
- Reading history tracking with analytics
- Real-time notifications system
- Comprehensive test suite (51 tests, 95% coverage)
- Security audit and hardening
- Production-ready documentation (80+ files)
- Frontend API reference with TypeScript types
- Docker and docker-compose configurations
- CI/CD workflows with GitHub Actions
- Database migrations with Alembic
- Celery background task processing
- Redis caching layer
- Prometheus metrics integration
- Sentry error tracking

### Security
- Password hashing with bcrypt
- JWT token validation
- CORS configuration
- Rate limiting
- SQL injection protection via ORM
- XSS protection
- Input validation with Pydantic
- Security headers

### Documentation
- Architecture documentation with system diagrams
- Contributing guidelines
- API documentation with OpenAPI specification
- Deployment guides (local, staging, production)
- Testing documentation
- Security review procedures

## [0.1.0] - 2024-12-01

### Added
- Initial project structure
- Basic FastAPI setup
- Database models
- Authentication endpoints

---

[Unreleased]: https://github.com/Number531/RSS-Feed-Backend/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Number531/RSS-Feed-Backend/releases/tag/v1.0.0
[0.1.0]: https://github.com/Number531/RSS-Feed-Backend/releases/tag/v0.1.0
