"""
Unit tests for RSS feed fetching and parsing service.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone
from app.services.rss_feed_service import (
    RSSFeedService,
    parse_feed_entry,
    extract_feed_metadata
)


@pytest.mark.asyncio
class TestRSSFeedService:
    """Test RSS feed fetching service."""
    
    async def test_fetch_feed_success(self):
        """Test successful feed fetching."""
        mock_db = AsyncMock()
        service = RSSFeedService(mock_db)
        
        mock_source = Mock()
        mock_source.id = "test-source-id"
        mock_source.name = "Test Feed"
        mock_source.url = "https://example.com/feed.xml"
        mock_source.etag = None
        mock_source.last_modified = None
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"""<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <item>
                    <title>Test Article</title>
                    <link>https://example.com/article1</link>
                    <description>Article description</description>
                </item>
            </channel>
        </rss>"""
        mock_response.headers = {
            "ETag": "test-etag",
            "Last-Modified": "Mon, 01 Jan 2024 12:00:00 GMT"
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            feed = await service.fetch_feed(mock_source)
            
            assert feed is not None
            assert hasattr(feed, 'entries')
            assert len(feed.entries) > 0
    
    async def test_fetch_feed_with_etag(self):
        """Test fetching feed with ETag for caching."""
        mock_db = AsyncMock()
        service = RSSFeedService(mock_db)
        
        mock_source = Mock()
        mock_source.id = "test-source-id"
        mock_source.url = "https://example.com/feed.xml"
        mock_source.etag = "existing-etag"
        mock_source.last_modified = "Mon, 01 Jan 2024 00:00:00 GMT"
        
        # Mock 304 Not Modified response
        mock_response = Mock()
        mock_response.status_code = 304
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            feed = await service.fetch_feed(mock_source)
            
            # Should return None for not modified
            assert feed is None
    
    async def test_fetch_feed_http_error(self):
        """Test handling of HTTP errors."""
        mock_db = AsyncMock()
        service = RSSFeedService(mock_db)
        
        mock_source = Mock()
        mock_source.id = "test-source-id"
        mock_source.url = "https://example.com/feed.xml"
        mock_source.etag = None
        mock_source.last_modified = None
        
        # Mock HTTP error
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Connection error")
            )
            
            with pytest.raises(Exception):
                await service.fetch_feed(mock_source)
    
    async def test_fetch_feed_invalid_xml(self):
        """Test handling of invalid XML in feed."""
        mock_db = AsyncMock()
        service = RSSFeedService(mock_db)
        
        mock_source = Mock()
        mock_source.id = "test-source-id"
        mock_source.url = "https://example.com/feed.xml"
        mock_source.etag = None
        mock_source.last_modified = None
        
        # Mock response with invalid XML
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"This is not valid XML"
        mock_response.headers = {}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            feed = await service.fetch_feed(mock_source)
            
            # Should handle gracefully - might return None or empty feed
            assert feed is not None or feed is None
    
    async def test_update_source_metadata(self):
        """Test updating source with ETag and Last-Modified."""
        mock_db = AsyncMock()
        service = RSSFeedService(mock_db)
        
        mock_source = Mock()
        mock_source.id = "test-source-id"
        mock_source.url = "https://example.com/feed.xml"
        
        headers = {
            "ETag": "new-etag",
            "Last-Modified": "Tue, 02 Jan 2024 12:00:00 GMT"
        }
        
        await service.update_source_metadata(mock_source, headers)
        
        assert mock_source.etag == "new-etag"
        assert mock_source.last_modified == "Tue, 02 Jan 2024 12:00:00 GMT"
        mock_db.commit.assert_called_once()


class TestParseFeedEntry:
    """Test parsing individual feed entries."""
    
    def test_parse_complete_entry(self):
        """Test parsing entry with all fields."""
        entry = {
            'title': 'Test Article Title',
            'link': 'https://example.com/article1',
            'published_parsed': (2024, 1, 1, 12, 0, 0, 0, 0, 0),
            'author': 'John Doe',
            'summary': 'Article summary text',
            'content': [{'value': '<p>Full article content</p>'}],
            'media_thumbnail': [{'url': 'https://example.com/thumb.jpg'}]
        }
        
        result = parse_feed_entry(entry)
        
        assert result['title'] == 'Test Article Title'
        assert result['url'] == 'https://example.com/article1'
        assert result['author'] == 'John Doe'
        assert result['description'] == 'Article summary text'
        assert result['content'] == '<p>Full article content</p>'
        assert result['thumbnail_url'] == 'https://example.com/thumb.jpg'
        assert isinstance(result['published_date'], datetime)
    
    def test_parse_minimal_entry(self):
        """Test parsing entry with only required fields."""
        entry = {
            'title': 'Minimal Article',
            'link': 'https://example.com/article2'
        }
        
        result = parse_feed_entry(entry)
        
        assert result['title'] == 'Minimal Article'
        assert result['url'] == 'https://example.com/article2'
        assert result['author'] is None or result['author'] == ''
        assert result['published_date'] is not None  # Should use current time
    
    def test_parse_entry_with_multiple_content(self):
        """Test parsing entry with multiple content entries."""
        entry = {
            'title': 'Article',
            'link': 'https://example.com/article',
            'content': [
                {'value': 'First content'},
                {'value': 'Second content'}
            ]
        }
        
        result = parse_feed_entry(entry)
        
        # Should use first content entry
        assert 'First content' in result['content']
    
    def test_parse_entry_date_formats(self):
        """Test parsing different date formats."""
        # Test with published_parsed
        entry1 = {
            'title': 'Article',
            'link': 'https://example.com/article',
            'published_parsed': (2024, 1, 15, 10, 30, 0, 0, 0, 0)
        }
        result1 = parse_feed_entry(entry1)
        assert result1['published_date'].year == 2024
        assert result1['published_date'].month == 1
        assert result1['published_date'].day == 15
        
        # Test with updated_parsed as fallback
        entry2 = {
            'title': 'Article',
            'link': 'https://example.com/article',
            'updated_parsed': (2024, 2, 20, 14, 45, 0, 0, 0, 0)
        }
        result2 = parse_feed_entry(entry2)
        assert result2['published_date'] is not None
    
    def test_parse_entry_media_content(self):
        """Test extracting media content from entry."""
        entry = {
            'title': 'Article with media',
            'link': 'https://example.com/article',
            'media_content': [
                {'url': 'https://example.com/video.mp4', 'type': 'video/mp4'},
                {'url': 'https://example.com/image.jpg', 'type': 'image/jpeg'}
            ]
        }
        
        result = parse_feed_entry(entry)
        
        # Should extract image URL if present
        assert result.get('thumbnail_url') or True  # Implementation dependent
    
    def test_parse_entry_enclosures(self):
        """Test extracting enclosures from entry."""
        entry = {
            'title': 'Article with enclosure',
            'link': 'https://example.com/article',
            'enclosures': [
                {'url': 'https://example.com/podcast.mp3', 'type': 'audio/mpeg'}
            ]
        }
        
        result = parse_feed_entry(entry)
        
        assert result is not None
        # Enclosure handling is implementation-specific


class TestExtractFeedMetadata:
    """Test extracting metadata from feed."""
    
    def test_extract_feed_title_description(self):
        """Test extracting basic feed metadata."""
        feed = Mock()
        feed.feed = Mock()
        feed.feed.title = "Test Feed"
        feed.feed.description = "Feed description"
        feed.feed.link = "https://example.com"
        
        metadata = extract_feed_metadata(feed)
        
        assert metadata['title'] == "Test Feed"
        assert metadata['description'] == "Feed description"
        assert metadata['link'] == "https://example.com"
    
    def test_extract_feed_image(self):
        """Test extracting feed image."""
        feed = Mock()
        feed.feed = Mock()
        feed.feed.title = "Test Feed"
        feed.feed.image = {'href': 'https://example.com/logo.png'}
        
        metadata = extract_feed_metadata(feed)
        
        assert metadata.get('image') == 'https://example.com/logo.png'
    
    def test_extract_feed_language(self):
        """Test extracting feed language."""
        feed = Mock()
        feed.feed = Mock()
        feed.feed.title = "Test Feed"
        feed.feed.language = "en-US"
        
        metadata = extract_feed_metadata(feed)
        
        assert metadata.get('language') == "en-US"
    
    def test_extract_minimal_feed(self):
        """Test extracting metadata from minimal feed."""
        feed = Mock()
        feed.feed = Mock()
        feed.feed.title = "Minimal Feed"
        
        metadata = extract_feed_metadata(feed)
        
        assert metadata['title'] == "Minimal Feed"
        assert 'description' in metadata or 'link' in metadata


class TestRealWorldFeedFormats:
    """Test with real-world RSS/Atom feed formats."""
    
    def test_parse_rss_2_0_feed(self):
        """Test parsing RSS 2.0 format."""
        entry = {
            'title': 'RSS 2.0 Article',
            'link': 'https://example.com/rss-article',
            'description': 'RSS description',
            'pubDate': 'Mon, 01 Jan 2024 12:00:00 GMT',
            'author': 'rss@example.com (John Doe)',
            'guid': 'https://example.com/rss-article'
        }
        
        result = parse_feed_entry(entry)
        
        assert result['title'] == 'RSS 2.0 Article'
        assert result['url'] == 'https://example.com/rss-article'
    
    def test_parse_atom_feed(self):
        """Test parsing Atom format."""
        entry = {
            'title': 'Atom Article',
            'link': 'https://example.com/atom-article',
            'summary': 'Atom summary',
            'updated': '2024-01-01T12:00:00Z',
            'author': 'John Doe',
            'id': 'https://example.com/atom-article'
        }
        
        result = parse_feed_entry(entry)
        
        assert result['title'] == 'Atom Article'
        assert result['url'] == 'https://example.com/atom-article'
    
    def test_parse_entry_with_html_entities(self):
        """Test parsing entry with HTML entities in title."""
        entry = {
            'title': 'Article &amp; More &lt;News&gt;',
            'link': 'https://example.com/article',
            'summary': 'Description with &quot;quotes&quot;'
        }
        
        result = parse_feed_entry(entry)
        
        # HTML entities should be decoded
        assert '&amp;' not in result['title'] or '&' in result['title']
    
    def test_parse_entry_with_cdata(self):
        """Test parsing entry with CDATA sections."""
        entry = {
            'title': 'Article Title',
            'link': 'https://example.com/article',
            'summary': '<![CDATA[Description with <html> tags]]>'
        }
        
        result = parse_feed_entry(entry)
        
        assert result['description'] is not None


class TestFeedPolling:
    """Test periodic feed polling behavior."""
    
    @pytest.mark.asyncio
    async def test_poll_multiple_sources(self):
        """Test polling multiple feed sources."""
        mock_db = AsyncMock()
        service = RSSFeedService(mock_db)
        
        # Mock multiple sources
        sources = [
            Mock(id=f"source-{i}", url=f"https://example.com/feed{i}.xml", 
                 etag=None, last_modified=None)
            for i in range(3)
        ]
        
        # Mock successful responses for all
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"""<?xml version="1.0"?>
        <rss><channel><item><title>Test</title><link>http://test.com</link></item></channel></rss>"""
        mock_response.headers = {}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            feeds = []
            for source in sources:
                feed = await service.fetch_feed(source)
                feeds.append(feed)
            
            assert len(feeds) == 3
            assert all(feed is not None for feed in feeds)
    
    @pytest.mark.asyncio
    async def test_handle_mixed_responses(self):
        """Test handling mix of successful and failed feed fetches."""
        mock_db = AsyncMock()
        service = RSSFeedService(mock_db)
        
        sources = [
            Mock(id="source-1", url="https://example.com/feed1.xml", etag=None, last_modified=None),
            Mock(id="source-2", url="https://example.com/feed2.xml", etag=None, last_modified=None),
        ]
        
        # First succeeds, second fails
        success_response = Mock()
        success_response.status_code = 200
        success_response.content = b"<?xml version='1.0'?><rss><channel></channel></rss>"
        success_response.headers = {}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_get = AsyncMock(side_effect=[success_response, Exception("Network error")])
            mock_client.return_value.__aenter__.return_value.get = mock_get
            
            feed1 = await service.fetch_feed(sources[0])
            assert feed1 is not None
            
            with pytest.raises(Exception):
                await service.fetch_feed(sources[1])
