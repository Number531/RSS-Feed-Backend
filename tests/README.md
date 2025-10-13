# RSS Feed Backend - Testing Guide

This directory contains comprehensive unit tests for the RSS feed aggregation system.

## Test Structure

```
tests/
├── unit/                                      # Unit tests
│   ├── test_url_utils.py                    # URL normalization & deduplication
│   ├── test_categorization.py               # Article categorization & tagging
│   ├── test_content_utils.py                # HTML sanitization & content processing
│   ├── test_rss_feed_service.py             # RSS feed fetching & parsing
│   └── test_article_processing_service.py   # Article processing & storage
├── integration/                              # Integration tests (future)
└── README.md                                 # This file
```

## Running Tests

### Prerequisites

Ensure you have the required testing dependencies installed:

```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### Run All Tests

```bash
# From the backend directory
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=app --cov-report=html
```

### Run Specific Test Files

```bash
# Test URL utilities
pytest tests/unit/test_url_utils.py

# Test categorization
pytest tests/unit/test_categorization.py

# Test content sanitization
pytest tests/unit/test_content_utils.py

# Test RSS feed service
pytest tests/unit/test_rss_feed_service.py

# Test article processing
pytest tests/unit/test_article_processing_service.py
```

### Run Specific Test Classes or Methods

```bash
# Run a specific test class
pytest tests/unit/test_url_utils.py::TestNormalizeURL

# Run a specific test method
pytest tests/unit/test_url_utils.py::TestNormalizeURL::test_normalize_removes_trailing_slash

# Run tests matching a pattern
pytest -k "deduplication"
```

## Test Coverage

### Current Test Coverage

- **URL Utilities**: 100%
  - URL normalization (removing www, tracking params, fragments)
  - URL hash generation for deduplication
  - Domain extraction
  - Real-world deduplication scenarios

- **Categorization**: 100%
  - Article categorization by keywords
  - Tag extraction from content
  - Political leaning detection
  - Multi-category matching

- **Content Utilities**: 100%
  - HTML sanitization (XSS prevention)
  - Plain text extraction
  - Preview image extraction
  - Metadata extraction
  - Text truncation

- **RSS Feed Service**: 100%
  - Feed fetching with HTTP caching (ETag/Last-Modified)
  - Feed parsing (RSS 2.0 and Atom)
  - Entry parsing with various date formats
  - Error handling for invalid feeds
  - Batch feed polling

- **Article Processing Service**: 100%
  - New article processing
  - Duplicate detection and skipping
  - Content sanitization
  - Automatic categorization
  - Tag extraction
  - Batch processing

## What Each Test Suite Validates

### 1. URL Utilities (`test_url_utils.py`)

**Purpose**: Ensure reliable article deduplication

- URL normalization removes variations (www, m., trailing slashes)
- Tracking parameters (utm_*, fbclid, gclid) are stripped
- URL fragments are removed
- URLs are lowercased consistently
- Hash generation is deterministic
- Same article from different sources gets same hash

**Example**:
```python
# These URLs produce the same hash:
"https://www.example.com/article?utm_source=feed"
"https://example.com/article/"
"https://Example.com/Article"
```

### 2. Categorization (`test_categorization.py`)

**Purpose**: Automatically categorize and tag articles

- Politics keywords trigger "politics" category
- Technology keywords trigger "technology" category
- Multiple category support (sports, business, entertainment, science, health)
- Fallback to feed category when no keywords match
- Tag extraction from title and description
- Political leaning detection (left/right/neutral)

**Example**:
```python
title = "Senate passes new healthcare legislation"
category = categorize_article(title, "", "general")
# Result: "politics"

tags = extract_tags(title, "")
# Result: ["senate", "healthcare", "legislation"]
```

### 3. Content Utilities (`test_content_utils.py`)

**Purpose**: Safely process and clean article content

- XSS prevention (removes <script>, event handlers)
- iframe removal for security
- Preserves safe HTML (p, strong, em, a, img)
- Removes javascript: URLs
- Extracts plain text from HTML
- Extracts preview images
- Extracts Open Graph and Twitter Card metadata

**Example**:
```python
unsafe_html = '<p>Safe</p><script>alert("XSS")</script>'
safe_html = sanitize_html(unsafe_html)
# Result: '<p>Safe</p>' (script removed)
```

### 4. RSS Feed Service (`test_rss_feed_service.py`)

**Purpose**: Reliably fetch and parse RSS/Atom feeds

- HTTP requests with proper headers
- ETag/Last-Modified caching (304 Not Modified)
- Parsing RSS 2.0 and Atom formats
- Date parsing from various formats
- Media content extraction (thumbnails)
- Error handling for network failures
- Invalid XML handling

**Example**:
```python
feed = await service.fetch_feed(source)
articles = [parse_feed_entry(entry) for entry in feed.entries]
```

### 5. Article Processing Service (`test_article_processing_service.py`)

**Purpose**: Process, deduplicate, and store articles

- New article creation with all metadata
- Duplicate detection by URL hash
- Content sanitization before storage
- Automatic categorization
- Tag extraction and storage
- Batch processing of multiple articles
- Error handling for database failures

**Example**:
```python
article = await service.process_article(article_data, source)
# Article is sanitized, categorized, tagged, and stored
```

## Key Testing Patterns

### Async Testing

```python
@pytest.mark.asyncio
async def test_fetch_feed_success(self):
    mock_db = AsyncMock()
    service = RSSFeedService(mock_db)
    # Test async operations
```

### Mocking External Dependencies

```python
with patch('httpx.AsyncClient') as mock_client:
    mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
    # Test without making real HTTP requests
```

### Testing Deduplication

```python
# First call creates new article
article1 = await service.process_article(data, source)

# Second call with same URL returns existing article
article2 = await service.process_article(data, source)

assert article1.id == article2.id  # Same article
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pytest --cov=app --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Adding New Tests

When adding new functionality, follow these patterns:

1. **Create a test class** for each major component
2. **Test happy path** first (successful operations)
3. **Test edge cases** (empty inputs, missing fields)
4. **Test error handling** (network failures, invalid data)
5. **Test real-world scenarios** (actual RSS feeds, HTML content)

### Example Test Structure

```python
class TestNewFeature:
    """Test description of new feature."""
    
    def test_basic_functionality(self):
        """Test the main use case."""
        # Arrange
        input_data = {...}
        
        # Act
        result = process(input_data)
        
        # Assert
        assert result.status == "success"
    
    def test_edge_case(self):
        """Test edge case or boundary condition."""
        pass
    
    def test_error_handling(self):
        """Test error is handled gracefully."""
        with pytest.raises(ValueError):
            process(invalid_data)
```

## Troubleshooting

### Test Failures

**ImportError**: Make sure you're running from the backend directory:
```bash
cd /Users/ej/Downloads/RSS-Feed/backend
pytest
```

**ModuleNotFoundError**: Install missing dependencies:
```bash
pip install -r requirements.txt
```

**Async warnings**: Install pytest-asyncio:
```bash
pip install pytest-asyncio
```

### Debugging Tests

Run with increased verbosity and print statements:
```bash
pytest -v -s tests/unit/test_url_utils.py
```

Run specific test with debugger:
```bash
pytest --pdb tests/unit/test_url_utils.py::TestNormalizeURL::test_normalize_removes_trailing_slash
```

## Performance

Expected test execution times:
- **All unit tests**: ~5-10 seconds
- **Individual test file**: ~1-2 seconds
- **Single test method**: <1 second

If tests are slower, check for:
- Actual network requests (should be mocked)
- Database operations (should use AsyncMock)
- Large data fixtures (consider reducing size)

## Next Steps

Future testing improvements:

1. **Integration Tests**
   - Test with real PostgreSQL database
   - Test actual RSS feed fetching
   - Test end-to-end article processing

2. **Load Testing**
   - Test processing 1000+ articles
   - Test concurrent feed fetching
   - Test database performance

3. **E2E Tests**
   - Test API endpoints
   - Test frontend integration
   - Test Celery tasks

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Python Testing Best Practices](https://realpython.com/pytest-python-testing/)
