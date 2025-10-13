.PHONY: help install install-dev test test-unit test-integration lint format clean run setup db-upgrade db-downgrade db-seed

help:
	@echo "RSS Feed Backend - Available Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install        - Install production dependencies"
	@echo "  make install-dev    - Install development dependencies"
	@echo "  make setup          - Full development environment setup"
	@echo ""
	@echo "Development:"
	@echo "  make run            - Run development server with auto-reload"
	@echo "  make format         - Format code with Black and isort"
	@echo "  make lint           - Run linters (flake8, mypy)"
	@echo "  make clean          - Clean build files and caches"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all tests with coverage"
	@echo "  make test-unit      - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo ""
	@echo "Database:"
	@echo "  make db-upgrade     - Run database migrations"
	@echo "  make db-downgrade   - Rollback last migration"
	@echo "  make db-seed        - Seed database with sample data"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	pytest --cov=app --cov-report=term --cov-report=html

test-unit:
	pytest -m unit --cov=app

test-integration:
	pytest -m integration

lint:
	@echo "Running flake8..."
	flake8 app/
	@echo "Running mypy..."
	mypy app/

format:
	@echo "Formatting with Black..."
	black app/
	@echo "Sorting imports with isort..."
	isort app/

clean:
	@echo "Cleaning build files..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage build dist *.egg-info
	@echo "Clean complete!"

run:
	uvicorn app.main:app --reload --port 8000

setup: install-dev
	@echo "Setting up development environment..."
	alembic upgrade head
	@echo "Setup complete! Run 'make run' to start the server."

db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

db-seed:
	python scripts/database/seed_database.py
