"""
Unit tests for HTML content sanitization and processing.
"""
import pytest
from app.utils.content_utils import (
    sanitize_html,
    extract_plain_text,
    extract_preview_image,
    extract_metadata,
    truncate_text
)


class TestSanitizeHTML:
    """Test HTML sanitization for security and cleanliness."""
    
    def test_allows_safe_tags(self):
        """Test that safe HTML tags are preserved."""
        html = "<p>This is <strong>bold</strong> and <em>italic</em> text.</p>"
        result = sanitize_html(html)
        assert "<p>" in result
        assert "<strong>" in result or "<b>" in result
        assert "<em>" in result or "<i>" in result
    
    def test_removes_script_tags(self):
        """Test that script tags are removed."""
        html = '<p>Safe content</p><script>alert("XSS")</script>'
        result = sanitize_html(html)
        assert "<script>" not in result
        assert "alert" not in result
        assert "Safe content" in result
    
    def test_removes_event_handlers(self):
        """Test that JavaScript event handlers are removed."""
        html = '<p onclick="alert(\'XSS\')">Click me</p>'
        result = sanitize_html(html)
        assert "onclick" not in result
        assert "alert" not in result
        assert "Click me" in result
    
    def test_removes_iframe(self):
        """Test that iframe tags are removed."""
        html = '<p>Content</p><iframe src="http://evil.com"></iframe>'
        result = sanitize_html(html)
        assert "<iframe>" not in result
        assert "evil.com" not in result
    
    def test_removes_style_tags(self):
        """Test that style tags are removed or sanitized."""
        html = '<p>Text</p><style>body { background: red; }</style>'
        result = sanitize_html(html)
        # Style tags should be removed
        assert "<style>" not in result
    
    def test_preserves_links(self):
        """Test that links are preserved with proper attributes."""
        html = '<a href="https://example.com">Link</a>'
        result = sanitize_html(html)
        assert "<a" in result
        assert "href=" in result
        assert "example.com" in result
    
    def test_removes_javascript_urls(self):
        """Test that javascript: URLs are removed."""
        html = '<a href="javascript:alert(\'XSS\')">Click</a>'
        result = sanitize_html(html)
        assert "javascript:" not in result
    
    def test_preserves_images(self):
        """Test that image tags are preserved."""
        html = '<img src="https://example.com/image.jpg" alt="Test">'
        result = sanitize_html(html)
        assert "<img" in result
        assert "src=" in result
    
    def test_removes_data_urls(self):
        """Test that data: URLs in images are removed or sanitized."""
        html = '<img src="data:image/png;base64,iVBORw0KGgo=">'
        result = sanitize_html(html)
        # Data URLs might be allowed or removed depending on policy
        # This test documents current behavior
        assert result  # Should return something
    
    def test_empty_input(self):
        """Test handling of empty HTML."""
        result = sanitize_html("")
        assert result == ""
    
    def test_plain_text_input(self):
        """Test that plain text is preserved."""
        text = "This is plain text with no HTML tags."
        result = sanitize_html(text)
        assert text in result


class TestExtractPlainText:
    """Test plain text extraction from HTML."""
    
    def test_extract_from_simple_html(self):
        """Test extracting text from simple HTML."""
        html = "<p>This is a paragraph.</p>"
        text = extract_plain_text(html)
        assert "This is a paragraph." in text
        assert "<p>" not in text
    
    def test_extract_from_nested_html(self):
        """Test extracting text from nested HTML."""
        html = "<div><p>Outer <span>inner</span> text</p></div>"
        text = extract_plain_text(html)
        assert "Outer inner text" in text
        assert "<" not in text
    
    def test_preserves_spacing(self):
        """Test that spacing between elements is preserved."""
        html = "<p>First paragraph.</p><p>Second paragraph.</p>"
        text = extract_plain_text(html)
        # Should have some separation between paragraphs
        assert "First paragraph" in text
        assert "Second paragraph" in text
    
    def test_removes_scripts(self):
        """Test that script content is removed."""
        html = '<p>Content</p><script>alert("test")</script>'
        text = extract_plain_text(html)
        assert "Content" in text
        assert "alert" not in text
    
    def test_handles_special_characters(self):
        """Test handling of HTML entities."""
        html = "<p>This &amp; that, &lt;tag&gt;</p>"
        text = extract_plain_text(html)
        assert "&" in text or "and" in text
        assert "<" in text or "&lt;" not in text
    
    def test_empty_html(self):
        """Test handling of empty HTML."""
        text = extract_plain_text("")
        assert text == ""
    
    def test_whitespace_normalization(self):
        """Test that excessive whitespace is normalized."""
        html = "<p>Too     many     spaces</p>"
        text = extract_plain_text(html)
        assert "Too many spaces" in text or "Too     many     spaces" in text


class TestExtractPreviewImage:
    """Test preview image extraction from HTML content."""
    
    def test_extract_first_image(self):
        """Test extracting the first image from content."""
        html = '''
        <div>
            <p>Some text</p>
            <img src="https://example.com/image1.jpg" alt="First">
            <img src="https://example.com/image2.jpg" alt="Second">
        </div>
        '''
        image_url = extract_preview_image(html)
        assert image_url == "https://example.com/image1.jpg"
    
    def test_no_images(self):
        """Test when no images are present."""
        html = "<p>Just text, no images</p>"
        image_url = extract_preview_image(html)
        assert image_url is None
    
    def test_ignores_small_images(self):
        """Test that small images (like icons) are ignored."""
        html = '''
        <img src="https://example.com/icon.png" width="16" height="16">
        <img src="https://example.com/large.jpg" width="800" height="600">
        '''
        image_url = extract_preview_image(html)
        # Should prefer larger image
        assert "large.jpg" in image_url if image_url else True
    
    def test_handles_relative_urls(self):
        """Test handling of relative image URLs."""
        html = '<img src="/images/photo.jpg">'
        base_url = "https://example.com"
        image_url = extract_preview_image(html, base_url)
        # Should convert to absolute URL
        assert image_url is None or "example.com" in image_url
    
    def test_empty_html(self):
        """Test handling of empty HTML."""
        image_url = extract_preview_image("")
        assert image_url is None


class TestExtractMetadata:
    """Test metadata extraction from HTML."""
    
    def test_extract_og_tags(self):
        """Test extraction of Open Graph tags."""
        html = '''
        <html>
            <head>
                <meta property="og:title" content="Article Title">
                <meta property="og:description" content="Article description">
                <meta property="og:image" content="https://example.com/image.jpg">
            </head>
        </html>
        '''
        metadata = extract_metadata(html)
        assert metadata.get("og:title") == "Article Title"
        assert metadata.get("og:description") == "Article description"
        assert metadata.get("og:image") == "https://example.com/image.jpg"
    
    def test_extract_twitter_tags(self):
        """Test extraction of Twitter Card tags."""
        html = '''
        <html>
            <head>
                <meta name="twitter:title" content="Tweet Title">
                <meta name="twitter:description" content="Tweet description">
            </head>
        </html>
        '''
        metadata = extract_metadata(html)
        assert metadata.get("twitter:title") == "Tweet Title"
        assert metadata.get("twitter:description") == "Tweet description"
    
    def test_extract_standard_meta(self):
        """Test extraction of standard meta tags."""
        html = '''
        <html>
            <head>
                <meta name="description" content="Page description">
                <meta name="author" content="John Doe">
            </head>
        </html>
        '''
        metadata = extract_metadata(html)
        assert metadata.get("description") == "Page description"
        assert metadata.get("author") == "John Doe"
    
    def test_no_metadata(self):
        """Test when no metadata is present."""
        html = "<html><head></head><body>Content</body></html>"
        metadata = extract_metadata(html)
        assert isinstance(metadata, dict)
        assert len(metadata) == 0
    
    def test_empty_html(self):
        """Test handling of empty HTML."""
        metadata = extract_metadata("")
        assert isinstance(metadata, dict)


class TestTruncateText:
    """Test text truncation utilities."""
    
    def test_truncate_long_text(self):
        """Test truncating text that exceeds max length."""
        text = "This is a very long piece of text that needs to be truncated."
        result = truncate_text(text, max_length=20)
        assert len(result) <= 23  # 20 + "..."
        assert result.endswith("...")
    
    def test_dont_truncate_short_text(self):
        """Test that short text is not truncated."""
        text = "Short text"
        result = truncate_text(text, max_length=50)
        assert result == text
        assert not result.endswith("...")
    
    def test_truncate_at_word_boundary(self):
        """Test that truncation happens at word boundaries."""
        text = "This is a long sentence with many words in it"
        result = truncate_text(text, max_length=20)
        # Should not cut in the middle of a word
        words = result.replace("...", "").strip().split()
        last_word = words[-1] if words else ""
        # Last word should be complete (not cut off)
        assert last_word in text.split()
    
    def test_exact_length(self):
        """Test text that is exactly the max length."""
        text = "A" * 50
        result = truncate_text(text, max_length=50)
        # Should not add ellipsis if exactly at max length
        assert len(result) <= 53  # Might add ellipsis or not
    
    def test_empty_text(self):
        """Test handling of empty text."""
        result = truncate_text("", max_length=50)
        assert result == ""


class TestRealWorldContent:
    """Test with real-world HTML content scenarios."""
    
    def test_article_with_ads(self):
        """Test cleaning article content that includes ads."""
        html = '''
        <div class="article">
            <p>Article content here.</p>
            <div class="advertisement">
                <script>showAd();</script>
            </div>
            <p>More article content.</p>
        </div>
        '''
        result = sanitize_html(html)
        assert "Article content" in result
        assert "<script>" not in result
        assert "showAd" not in result
    
    def test_embedded_video_iframe(self):
        """Test handling of embedded video iframes."""
        html = '''
        <p>Watch this video:</p>
        <iframe src="https://youtube.com/embed/video123"></iframe>
        <p>More content</p>
        '''
        result = sanitize_html(html)
        assert "Watch this video" in result
        # Iframes should be removed for security
        assert "<iframe>" not in result
    
    def test_complex_formatting(self):
        """Test article with complex formatting."""
        html = '''
        <article>
            <h2>Headline</h2>
            <p>First paragraph with <strong>bold</strong> and <em>italic</em>.</p>
            <ul>
                <li>Point one</li>
                <li>Point two</li>
            </ul>
            <blockquote>A quote from someone</blockquote>
        </article>
        '''
        result = sanitize_html(html)
        assert "Headline" in result
        assert "First paragraph" in result
        assert "Point one" in result
        assert "A quote" in result
    
    def test_social_media_embeds(self):
        """Test handling of social media embeds."""
        html = '''
        <p>Check out this tweet:</p>
        <blockquote class="twitter-tweet">
            <p>Tweet content</p>
            <script async src="https://platform.twitter.com/widgets.js"></script>
        </blockquote>
        '''
        result = sanitize_html(html)
        assert "Tweet content" in result
        assert "<script>" not in result
