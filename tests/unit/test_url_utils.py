"""
Unit tests for URL utilities and deduplication.
"""
import pytest
from app.utils.url_utils import normalize_url, generate_url_hash, extract_domain


class TestNormalizeURL:
    """Test URL normalization for deduplication."""
    
    def test_normalize_removes_trailing_slash(self):
        """Test that trailing slashes are removed."""
        url = "https://example.com/article/"
        expected = "https://example.com/article"
        assert normalize_url(url) == expected
    
    def test_normalize_removes_www_prefix(self):
        """Test that www. prefix is removed."""
        url = "https://www.example.com/article"
        expected = "https://example.com/article"
        assert normalize_url(url) == expected
    
    def test_normalize_removes_mobile_prefix(self):
        """Test that m. prefix is removed."""
        url = "https://m.example.com/article"
        expected = "https://example.com/article"
        assert normalize_url(url) == expected
    
    def test_normalize_removes_tracking_params(self):
        """Test that tracking parameters are removed."""
        url = "https://example.com/article?utm_source=feed&utm_medium=rss"
        expected = "https://example.com/article"
        assert normalize_url(url) == expected
    
    def test_normalize_removes_fragment(self):
        """Test that URL fragments are removed."""
        url = "https://example.com/article#comments"
        expected = "https://example.com/article"
        assert normalize_url(url) == expected
    
    def test_normalize_keeps_important_params(self):
        """Test that non-tracking parameters are kept."""
        url = "https://example.com/article?id=123&page=2"
        result = normalize_url(url)
        assert "id=123" in result
        assert "page=2" in result
    
    def test_normalize_lowercase(self):
        """Test that URLs are converted to lowercase."""
        url = "https://Example.Com/Article"
        expected = "https://example.com/article"
        assert normalize_url(url) == expected
    
    def test_normalize_complex_url(self):
        """Test normalization of complex URL with multiple issues."""
        url = "https://www.Example.com/Article/?utm_source=twitter&id=123#section"
        result = normalize_url(url)
        assert result == "https://example.com/article?id=123"
    
    def test_normalize_handles_empty_path(self):
        """Test that empty paths are normalized to /."""
        url = "https://example.com"
        expected = "https://example.com/"
        assert normalize_url(url) == expected


class TestGenerateURLHash:
    """Test URL hash generation for deduplication."""
    
    def test_same_url_same_hash(self):
        """Test that the same URL produces the same hash."""
        url = "https://example.com/article"
        hash1 = generate_url_hash(url)
        hash2 = generate_url_hash(url)
        assert hash1 == hash2
    
    def test_different_urls_different_hash(self):
        """Test that different URLs produce different hashes."""
        url1 = "https://example.com/article1"
        url2 = "https://example.com/article2"
        hash1 = generate_url_hash(url1)
        hash2 = generate_url_hash(url2)
        assert hash1 != hash2
    
    def test_normalized_urls_same_hash(self):
        """Test that URLs that normalize to the same URL produce same hash."""
        url1 = "https://www.example.com/article?utm_source=feed"
        url2 = "https://example.com/article/"
        url3 = "https://Example.com/Article"
        
        hash1 = generate_url_hash(url1)
        hash2 = generate_url_hash(url2)
        hash3 = generate_url_hash(url3)
        
        assert hash1 == hash2 == hash3
    
    def test_hash_length(self):
        """Test that hash is 64 characters (SHA-256)."""
        url = "https://example.com/article"
        hash_value = generate_url_hash(url)
        assert len(hash_value) == 64
    
    def test_hash_is_hexadecimal(self):
        """Test that hash contains only hexadecimal characters."""
        url = "https://example.com/article"
        hash_value = generate_url_hash(url)
        assert all(c in '0123456789abcdef' for c in hash_value)


class TestExtractDomain:
    """Test domain extraction from URLs."""
    
    def test_extract_domain_basic(self):
        """Test basic domain extraction."""
        url = "https://example.com/article"
        assert extract_domain(url) == "example.com"
    
    def test_extract_domain_removes_www(self):
        """Test that www. is removed from domain."""
        url = "https://www.example.com/article"
        assert extract_domain(url) == "example.com"
    
    def test_extract_domain_with_subdomain(self):
        """Test domain extraction with subdomain."""
        url = "https://news.example.com/article"
        assert extract_domain(url) == "news.example.com"
    
    def test_extract_domain_lowercase(self):
        """Test that domain is lowercase."""
        url = "https://Example.COM/article"
        assert extract_domain(url) == "example.com"


class TestDeduplicationScenarios:
    """Test real-world deduplication scenarios."""
    
    def test_same_article_different_sources(self):
        """Test that same article from wire service is deduplicated."""
        # AP News article published on multiple sites
        url1 = "https://apnews.com/article/abc123"
        url2 = "https://apnews.com/article/abc123?utm_source=rss"
        
        hash1 = generate_url_hash(url1)
        hash2 = generate_url_hash(url2)
        
        assert hash1 == hash2
    
    def test_amp_and_regular_urls(self):
        """Test that AMP and regular URLs of same article are different."""
        # Note: Our current implementation doesn't handle AMP URLs specially
        # This test documents current behavior
        url1 = "https://example.com/article"
        url2 = "https://example.com/amp/article"
        
        hash1 = generate_url_hash(url1)
        hash2 = generate_url_hash(url2)
        
        # These are treated as different articles (expected behavior for now)
        assert hash1 != hash2
    
    def test_social_media_sharing_links(self):
        """Test that social media parameters don't affect deduplication."""
        base_url = "https://example.com/article"
        facebook_url = f"{base_url}?fbclid=abc123"
        google_url = f"{base_url}?gclid=xyz789"
        
        hash_base = generate_url_hash(base_url)
        hash_fb = generate_url_hash(facebook_url)
        hash_google = generate_url_hash(google_url)
        
        assert hash_base == hash_fb == hash_google
