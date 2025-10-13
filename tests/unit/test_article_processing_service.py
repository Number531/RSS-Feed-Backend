"""
Unit tests for article processing and storage service.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone
from app.services.article_processing_service import ArticleProcessingService
from app.utils.url_utils import generate_url_hash


@pytest.mark.asyncio
class TestArticleProcessingService:
    """Test article processing and storage service."""
    
    async def test_process_new_article(self):
        """Test processing a new article (not a duplicate)."""
        mock_db = AsyncMock()
        service = ArticleProcessingService(mock_db)
        
        article_data = {
            'url': 'https://example.com/article1',
            'title': 'Test Article',
            'description': 'Article description',
            'content': '<p>Article content</p>',
            'author': 'John Doe',
            'published_date': datetime.now(timezone.utc),
            'thumbnail_url': 'https://example.com/thumb.jpg'
        }
        
        mock_source = Mock()
        mock_source.id = 'source-id'
        mock_source.category = 'technology'
        mock_source.name = 'Tech Feed'
        
        # Mock that article doesn't exist (not a duplicate)
        with patch.object(service, '_get_article_by_url_hash', AsyncMock(return_value=None)):
            with patch('app.utils.categorization.categorize_article', return_value='technology'):
                with patch('app.utils.categorization.extract_tags', return_value=['tech', 'news']):
                    article = await service.process_article(article_data, mock_source)
                    
                    assert article is not None
                    assert article.title == 'Test Article'
                    assert article.rss_source_id == 'source-id'
                    mock_db.add.assert_called_once()
                    mock_db.commit.assert_called_once()
    
    async def test_skip_duplicate_article(self):
        """Test that duplicate articles are skipped."""
        mock_db = AsyncMock()
        service = ArticleProcessingService(mock_db)
        
        article_data = {
            'url': 'https://example.com/article1',
            'title': 'Test Article',
            'description': 'Article description',
            'content': '<p>Article content</p>',
            'author': 'John Doe',
            'published_date': datetime.now(timezone.utc),
            'thumbnail_url': 'https://example.com/thumb.jpg'
        }
        
        mock_source = Mock()
        mock_source.id = 'source-id'
        mock_source.category = 'technology'
        
        # Mock that article already exists (duplicate)
        existing_article = Mock()
        existing_article.id = 'existing-article-id'
        
        with patch.object(service, '_get_article_by_url_hash', AsyncMock(return_value=existing_article)):
            article = await service.process_article(article_data, mock_source)
            
            # Should return existing article, not create new one
            assert article == existing_article
            mock_db.add.assert_not_called()
    
    async def test_sanitize_article_content(self):
        """Test that article content is sanitized."""
        mock_db = AsyncMock()
        service = ArticleProcessingService(mock_db)
        
        article_data = {
            'url': 'https://example.com/article1',
            'title': 'Test Article',
            'description': 'Description',
            'content': '<p>Safe content</p><script>alert("XSS")</script>',
            'author': 'John Doe',
            'published_date': datetime.now(timezone.utc),
        }
        
        mock_source = Mock()
        mock_source.id = 'source-id'
        mock_source.category = 'general'
        
        with patch.object(service, '_get_article_by_url_hash', AsyncMock(return_value=None)):
            with patch('app.utils.content_utils.sanitize_html') as mock_sanitize:
                mock_sanitize.return_value = '<p>Safe content</p>'
                
                article = await service.process_article(article_data, mock_source)
                
                # Sanitize should have been called
                mock_sanitize.assert_called()
    
    async def test_categorize_article_content(self):
        """Test that articles are categorized correctly."""
        mock_db = AsyncMock()
        service = ArticleProcessingService(mock_db)
        
        article_data = {
            'url': 'https://example.com/article1',
            'title': 'Senate passes healthcare bill',
            'description': 'Congress votes on legislation',
            'content': '<p>Political news</p>',
            'author': 'Reporter',
            'published_date': datetime.now(timezone.utc),
        }
        
        mock_source = Mock()
        mock_source.id = 'source-id'
        mock_source.category = 'general'
        
        with patch.object(service, '_get_article_by_url_hash', AsyncMock(return_value=None)):
            with patch('app.utils.categorization.categorize_article', return_value='politics') as mock_categorize:
                article = await service.process_article(article_data, mock_source)
                
                # Categorize should have been called
                mock_categorize.assert_called_with(
                    article_data['title'],
                    article_data['description'],
                    mock_source.category
                )
    
    async def test_extract_tags_from_article(self):
        """Test that tags are extracted from articles."""
        mock_db = AsyncMock()
        service = ArticleProcessingService(mock_db)
        
        article_data = {
            'url': 'https://example.com/article1',
            'title': 'Biden announces climate policy',
            'description': 'President discusses environment',
            'content': '<p>Climate change news</p>',
            'author': 'Reporter',
            'published_date': datetime.now(timezone.utc),
        }
        
        mock_source = Mock()
        mock_source.id = 'source-id'
        mock_source.category = 'politics'
        
        with patch.object(service, '_get_article_by_url_hash', AsyncMock(return_value=None)):
            with patch('app.utils.categorization.extract_tags', return_value=['biden', 'climate', 'environment']) as mock_tags:
                article = await service.process_article(article_data, mock_source)
                
                # Extract tags should have been called
                mock_tags.assert_called()
    
    async def test_generate_url_hash(self):
        """Test that URL hash is generated for deduplication."""
        mock_db = AsyncMock()
        service = ArticleProcessingService(mock_db)
        
        url1 = 'https://example.com/article?utm_source=feed'
        url2 = 'https://www.example.com/article'
        
        # Both should generate same hash after normalization
        hash1 = generate_url_hash(url1)
        hash2 = generate_url_hash(url2)
        
        assert hash1 == hash2
    
    async def test_handle_missing_required_fields(self):
        """Test handling of articles with missing required fields."""
        mock_db = AsyncMock()
        service = ArticleProcessingService(mock_db)
        
        # Missing URL
        article_data = {
            'title': 'Test Article',
            'description': 'Description',
        }
        
        mock_source = Mock()
        mock_source.id = 'source-id'
        mock_source.category = 'general'
        
        # Should raise error or handle gracefully
        with pytest.raises(Exception):
            await service.process_article(article_data, mock_source)


class TestBatchProcessing:
    """Test batch processing of multiple articles."""
    
    @pytest.mark.asyncio
    async def test_process_multiple_articles(self):
        """Test processing multiple articles from feed."""
        mock_db = AsyncMock()
        service = ArticleProcessingService(mock_db)
        
        articles = [
            {
                'url': f'https://example.com/article{i}',
                'title': f'Article {i}',
                'description': f'Description {i}',
                'content': f'<p>Content {i}</p>',
                'author': 'Author',
                'published_date': datetime.now(timezone.utc),
            }
            for i in range(5)
        ]
        
        mock_source = Mock()
        mock_source.id = 'source-id'
        mock_source.category = 'general'
        
        processed = []
        with patch.object(service, '_get_article_by_url_hash', AsyncMock(return_value=None)):
            for article_data in articles:
                article = await service.process_article(article_data, mock_source)
                processed.append(article)
        
        assert len(processed) == 5
    
    @pytest.mark.asyncio
    async def test_process_articles_with_duplicates(self):
        """Test processing articles where some are duplicates."""
        mock_db = AsyncMock()
        service = ArticleProcessingService(mock_db)
        
        articles = [
            {
                'url': 'https://example.com/article1',
                'title': 'Article 1',
                'description': 'Description',
                'content': '<p>Content</p>',
                'author': 'Author',
                'published_date': datetime.now(timezone.utc),
            },
            {
                'url': 'https://example.com/article1',  # Duplicate
                'title': 'Article 1 (duplicate)',
                'description': 'Description',
                'content': '<p>Content</p>',
                'author': 'Author',
                'published_date': datetime.now(timezone.utc),
            },
            {
                'url': 'https://example.com/article2',
                'title': 'Article 2',
                'description': 'Description',
                'content': '<p>Content</p>',
                'author': 'Author',
                'published_date': datetime.now(timezone.utc),
            }
        ]
        
        mock_source = Mock()
        mock_source.id = 'source-id'
        mock_source.category = 'general'
        
        # First article is new, second is duplicate, third is new
        side_effects = [None, Mock(id='existing-id'), None]
        
        processed = []
        with patch.object(service, '_get_article_by_url_hash', AsyncMock(side_effect=side_effects)):
            for article_data in articles:
                article = await service.process_article(article_data, mock_source)
                processed.append(article)
        
        assert len(processed) == 3
        # Second one should be the existing article (duplicate)
        assert processed[1].id == 'existing-id'


class TestArticleMetadata:
    """Test extraction and storage of article metadata."""
    
    @pytest.mark.asyncio
    async def test_extract_preview_image(self):
        """Test extracting preview image from article content."""
        mock_db = AsyncMock()
        service = ArticleProcessingService(mock_db)
        
        article_data = {
            'url': 'https://example.com/article1',
            'title': 'Article with image',
            'description': 'Description',
            'content': '<p>Text</p><img src="https://example.com/image.jpg">',
            'author': 'Author',
            'published_date': datetime.now(timezone.utc),
        }
        
        mock_source = Mock()
        mock_source.id = 'source-id'
        mock_source.category = 'general'
        
        with patch.object(service, '_get_article_by_url_hash', AsyncMock(return_value=None)):
            with patch('app.utils.content_utils.extract_preview_image', return_value='https://example.com/image.jpg') as mock_extract:
                article = await service.process_article(article_data, mock_source)
                
                # Extract preview image should have been called
                mock_extract.assert_called()
    
    @pytest.mark.asyncio
    async def test_extract_plain_text_summary(self):
        """Test extracting plain text summary from HTML content."""
        mock_db = AsyncMock()
        service = ArticleProcessingService(mock_db)
        
        article_data = {
            'url': 'https://example.com/article1',
            'title': 'Article',
            'description': 'Description',
            'content': '<p>This is <strong>formatted</strong> text.</p>',
            'author': 'Author',
            'published_date': datetime.now(timezone.utc),
        }
        
        mock_source = Mock()
        mock_source.id = 'source-id'
        mock_source.category = 'general'
        
        with patch.object(service, '_get_article_by_url_hash', AsyncMock(return_value=None)):
            with patch('app.utils.content_utils.extract_plain_text', return_value='This is formatted text.') as mock_extract:
                article = await service.process_article(article_data, mock_source)
                
                # Plain text extraction should have been called
                mock_extract.assert_called()


class TestErrorHandling:
    """Test error handling in article processing."""
    
    @pytest.mark.asyncio
    async def test_handle_database_error(self):
        """Test handling database errors during article save."""
        mock_db = AsyncMock()
        mock_db.commit.side_effect = Exception("Database error")
        
        service = ArticleProcessingService(mock_db)
        
        article_data = {
            'url': 'https://example.com/article1',
            'title': 'Test Article',
            'description': 'Description',
            'content': '<p>Content</p>',
            'author': 'Author',
            'published_date': datetime.now(timezone.utc),
        }
        
        mock_source = Mock()
        mock_source.id = 'source-id'
        mock_source.category = 'general'
        
        with patch.object(service, '_get_article_by_url_hash', AsyncMock(return_value=None)):
            with pytest.raises(Exception, match="Database error"):
                await service.process_article(article_data, mock_source)
    
    @pytest.mark.asyncio
    async def test_handle_malformed_date(self):
        """Test handling articles with malformed publication dates."""
        mock_db = AsyncMock()
        service = ArticleProcessingService(mock_db)
        
        article_data = {
            'url': 'https://example.com/article1',
            'title': 'Test Article',
            'description': 'Description',
            'content': '<p>Content</p>',
            'author': 'Author',
            'published_date': 'not-a-valid-date',  # Invalid date
        }
        
        mock_source = Mock()
        mock_source.id = 'source-id'
        mock_source.category = 'general'
        
        with patch.object(service, '_get_article_by_url_hash', AsyncMock(return_value=None)):
            # Should handle gracefully or raise specific error
            try:
                article = await service.process_article(article_data, mock_source)
                # If it succeeds, date should be None or current time
                assert article.published_date is None or isinstance(article.published_date, datetime)
            except (TypeError, ValueError):
                # Expected for invalid date format
                pass


class TestArticleUpdates:
    """Test updating existing articles."""
    
    @pytest.mark.asyncio
    async def test_update_article_content(self):
        """Test updating content of existing article."""
        mock_db = AsyncMock()
        service = ArticleProcessingService(mock_db)
        
        existing_article = Mock()
        existing_article.id = 'article-id'
        existing_article.title = 'Old Title'
        existing_article.content = '<p>Old content</p>'
        
        updated_data = {
            'url': 'https://example.com/article1',
            'title': 'Updated Title',
            'description': 'Updated description',
            'content': '<p>Updated content</p>',
            'author': 'Author',
            'published_date': datetime.now(timezone.utc),
        }
        
        mock_source = Mock()
        mock_source.id = 'source-id'
        mock_source.category = 'general'
        
        with patch.object(service, '_get_article_by_url_hash', AsyncMock(return_value=existing_article)):
            article = await service.process_article(updated_data, mock_source)
            
            # Should return existing article (no update by default for duplicates)
            assert article == existing_article
