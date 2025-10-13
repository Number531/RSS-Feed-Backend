# Contributing to RSS Feed Backend

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Documentation](#documentation)

---

## 🤝 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, gender identity, sexual orientation, disability, ethnicity, religion, or nationality.

### Expected Behavior

- ✅ Be respectful and considerate
- ✅ Welcome newcomers and help them get started
- ✅ Provide constructive feedback
- ✅ Accept constructive criticism gracefully
- ✅ Focus on what's best for the community

### Unacceptable Behavior

- ❌ Harassment or discrimination
- ❌ Trolling or insulting comments
- ❌ Personal or political attacks
- ❌ Publishing others' private information
- ❌ Other conduct that would be inappropriate in a professional setting

---

## 🚀 Getting Started

### 1. Fork the Repository

Click the "Fork" button at the top right of the repository page.

### 2. Clone Your Fork

```bash
git clone https://github.com/YOUR-USERNAME/RSS-Feed-Backend.git
cd RSS-Feed-Backend
```

### 3. Add Upstream Remote

```bash
git remote add upstream https://github.com/Number531/RSS-Feed-Backend.git
```

### 4. Set Up Development Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Start services (Docker)
docker-compose -f docker/docker-compose.dev.yml up -d

# Run migrations
alembic upgrade head
```

### 5. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or updates
- `chore/` - Maintenance tasks

---

## 💻 Development Workflow

### 1. Keep Your Fork Updated

```bash
# Fetch upstream changes
git fetch upstream

# Merge into your local main
git checkout main
git merge upstream/main

# Update your fork
git push origin main
```

### 2. Make Your Changes

- Write clean, readable code
- Follow coding standards (see below)
- Add or update tests
- Update documentation if needed

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
```

### 4. Format Code

```bash
# Format with Black
black app/

# Sort imports
isort app/

# Run linters
flake8 app/
mypy app/
```

### 5. Commit Your Changes

Follow commit message guidelines (see below)

```bash
git add .
git commit -m "feat: add user profile picture upload"
```

### 6. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 7. Open a Pull Request

Go to the original repository and click "New Pull Request"

---

## 📝 Coding Standards

### Python Style Guide

**We follow PEP 8** with some modifications.

#### General Guidelines

- **Line length**: 88 characters (Black default)
- **Indentation**: 4 spaces (no tabs)
- **Imports**: Grouped and sorted (use isort)
- **Docstrings**: Google style for all public functions

#### Example Code

```python
"""Module for user authentication services."""

from typing import Optional
from datetime import datetime

from app.models.user import User
from app.core.security import verify_password


class AuthService:
    """Service for handling user authentication.
    
    This service manages user login, registration, and token
    generation for the application.
    """
    
    def __init__(self, db_session):
        """Initialize the authentication service.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
    
    def authenticate_user(
        self, 
        email: str, 
        password: str
    ) -> Optional[User]:
        """Authenticate a user with email and password.
        
        Args:
            email: User's email address
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
            
        Raises:
            ValueError: If email format is invalid
        """
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            return None
            
        if not verify_password(password, user.hashed_password):
            return None
            
        return user
```

### Code Organization

#### File Structure

```python
# Imports (grouped and sorted)
# 1. Standard library
import os
from typing import List, Optional

# 2. Third-party
from fastapi import HTTPException
from sqlalchemy.orm import Session

# 3. Local application
from app.models.user import User
from app.schemas.user import UserCreate

# Constants
MAX_USERNAME_LENGTH = 50

# Classes
class UserService:
    pass

# Functions
def create_user(data: UserCreate) -> User:
    pass
```

### Type Hints

**Always use type hints** for function parameters and return values:

```python
from typing import Optional, List, Dict

def get_user(user_id: int, db: Session) -> Optional[User]:
    """Fetch user by ID."""
    pass

def get_all_users(limit: int = 100) -> List[User]:
    """Get all users with limit."""
    pass

def get_user_stats(user_id: int) -> Dict[str, int]:
    """Get user statistics."""
    pass
```

### Naming Conventions

```python
# Classes: PascalCase
class UserService:
    pass

# Functions/methods: snake_case
def get_user_by_email(email: str):
    pass

# Variables: snake_case
user_count = 10
is_active = True

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_PAGE_SIZE = 20

# Private methods/attributes: leading underscore
def _internal_helper():
    pass
```

---

## 🧪 Testing Guidelines

### Test Coverage Requirements

- **Minimum**: 80% overall coverage
- **Target**: 95% coverage (current level)
- All new features must include tests

### Writing Tests

#### Unit Tests

```python
import pytest
from app.services.user_service import UserService

def test_create_user_success(db_session):
    """Test successful user creation."""
    service = UserService(db_session)
    
    user_data = {
        "email": "test@example.com",
        "password": "SecurePass123",
        "username": "testuser"
    }
    
    user = service.create_user(user_data)
    
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.id is not None

def test_create_user_duplicate_email(db_session):
    """Test user creation fails with duplicate email."""
    service = UserService(db_session)
    
    # Create first user
    service.create_user({"email": "test@example.com", ...})
    
    # Attempt duplicate
    with pytest.raises(ValueError, match="Email already exists"):
        service.create_user({"email": "test@example.com", ...})
```

#### Integration Tests

```python
import pytest
from fastapi.testclient import TestClient

def test_register_user_endpoint(client: TestClient):
    """Test user registration endpoint."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "SecurePass123",
            "username": "newuser"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data

def test_register_invalid_email(client: TestClient):
    """Test registration fails with invalid email."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "SecurePass123"
        }
    )
    
    assert response.status_code == 422  # Validation error
```

### Test Organization

```
tests/
├── unit/               # Pure unit tests
│   ├── test_services/
│   ├── test_utils/
│   └── test_models/
├── integration/        # API + DB tests
│   ├── test_auth_api.py
│   ├── test_users_api.py
│   └── test_articles_api.py
└── conftest.py         # Shared fixtures
```

---

## 🔀 Pull Request Process

### Before Submitting

- [ ] All tests pass locally
- [ ] Code is formatted (Black + isort)
- [ ] Linters pass (flake8, mypy)
- [ ] Test coverage maintained/improved
- [ ] Documentation updated
- [ ] Commit messages follow guidelines

### PR Title Format

Use conventional commit format:

```
feat: add user profile picture upload
fix: resolve bookmark deletion error
docs: update API endpoint documentation
refactor: simplify article service logic
test: add missing vote service tests
```

### PR Description Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All existing tests pass
- [ ] New tests added
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated

## Related Issues
Closes #123
Relates to #456
```

### Review Process

1. **Automated Checks** - CI/CD runs tests automatically
2. **Code Review** - At least one maintainer review required
3. **Feedback** - Address review comments
4. **Approval** - Maintainer approves PR
5. **Merge** - Maintainer merges PR

### After Merge

- Delete your feature branch
- Pull latest changes from upstream
- Celebrate! 🎉

---

## 📝 Commit Message Guidelines

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **style**: Code style (formatting, no logic change)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks
- **perf**: Performance improvements

### Scope (Optional)

Component affected: `auth`, `articles`, `comments`, `votes`, etc.

### Examples

```bash
# Simple feature
git commit -m "feat: add bookmark collections"

# Bug fix with scope
git commit -m "fix(auth): resolve token refresh issue"

# With detailed body
git commit -m "feat(articles): implement full-text search

Added PostgreSQL full-text search for articles using tsvector.
Includes index optimization for better performance.

Closes #123"

# Breaking change
git commit -m "feat(api)!: change article feed response format

BREAKING CHANGE: Feed endpoint now returns pagination metadata
at root level instead of nested in 'data' field"
```

---

## 📖 Documentation

### When to Update Docs

Update documentation when:
- Adding new API endpoints
- Changing existing endpoints
- Adding new features
- Modifying configuration options
- Updating deployment procedures

### Documentation Files

- **README.md** - Project overview, quick start
- **ARCHITECTURE.md** - System design, architecture
- **API Documentation** - `frontend-api-reference/`
- **Deployment Guides** - `*_DEPLOYMENT_*.md`
- **Code Comments** - Inline documentation

### Docstring Format

Use Google-style docstrings:

```python
def fetch_articles(
    category: str,
    limit: int = 20,
    offset: int = 0
) -> List[Article]:
    """Fetch articles by category with pagination.
    
    Args:
        category: Article category filter
        limit: Maximum number of articles to return
        offset: Number of articles to skip
        
    Returns:
        List of Article objects matching the criteria
        
    Raises:
        ValueError: If limit is negative or exceeds MAX_LIMIT
        
    Example:
        >>> articles = fetch_articles("technology", limit=10)
        >>> len(articles)
        10
    """
    pass
```

---

## 🔍 Code Review Checklist

### For Contributors

Before requesting review:
- [ ] Code compiles without errors
- [ ] All tests pass
- [ ] Code is formatted correctly
- [ ] No debug code left in
- [ ] Documentation updated
- [ ] Self-review completed

### For Reviewers

When reviewing PRs:
- [ ] Code follows project standards
- [ ] Logic is sound and efficient
- [ ] Tests are comprehensive
- [ ] No security vulnerabilities
- [ ] Documentation is clear
- [ ] Breaking changes are documented

---

## 🐛 Reporting Bugs

### Bug Report Template

```markdown
**Describe the bug**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen

**Screenshots**
If applicable

**Environment:**
- OS: [e.g. macOS 12.0]
- Python version: [e.g. 3.10.5]
- Browser: [if applicable]

**Additional context**
Any other relevant information
```

---

## 💡 Feature Requests

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
Clear description of the problem

**Describe the solution you'd like**
What you want to happen

**Describe alternatives you've considered**
Other solutions you thought about

**Additional context**
Mockups, examples, etc.
```

---

## 🎯 Best Practices

### General

1. **Keep PRs small** - Easier to review, faster to merge
2. **One feature per PR** - Don't mix unrelated changes
3. **Test thoroughly** - Prevent regressions
4. **Document decisions** - Help future contributors
5. **Be responsive** - Reply to review comments promptly

### Security

1. **Never commit secrets** - Use environment variables
2. **Validate all inputs** - Prevent injection attacks
3. **Use parameterized queries** - SQLAlchemy ORM does this
4. **Hash passwords** - Never store plain text
5. **Follow OWASP guidelines** - Security best practices

### Performance

1. **Optimize database queries** - Use indexes, avoid N+1
2. **Cache wisely** - Balance freshness and performance
3. **Use async when beneficial** - Non-blocking operations
4. **Profile before optimizing** - Data-driven decisions
5. **Load test** - Verify scalability

---

## 📞 Getting Help

### Communication Channels

- **GitHub Issues** - Bug reports, feature requests
- **GitHub Discussions** - Questions, ideas, help
- **Email** - support@example.com

### Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org)
- [Project Documentation](./DOCUMENTATION_INDEX.md)
- [Architecture Overview](./ARCHITECTURE.md)

---

## 🏆 Recognition

Contributors who make significant improvements will be:
- Listed in the project README
- Recognized in release notes
- Invited to join the core team (for consistent contributors)

---

## ✅ Checklist for First-Time Contributors

- [ ] Read this contributing guide
- [ ] Set up development environment
- [ ] Run tests locally
- [ ] Pick a "good first issue"
- [ ] Ask questions if stuck
- [ ] Submit your first PR
- [ ] Celebrate! 🎉

---

**Thank you for contributing to RSS Feed Backend!**

Your contributions make this project better for everyone.

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-27  
**Questions?** Open a GitHub Discussion
