"""
Test utility functions for integration and unit tests.
"""
import hashlib


def generate_url_hash(url: str) -> str:
    """
    Generate SHA-256 hash of URL for deduplication.
    
    This matches the hashing logic used in the Article model for url_hash field.
    
    Args:
        url: The URL to hash
        
    Returns:
        64-character hex string (SHA-256 hash)
        
    Example:
        >>> generate_url_hash("https://example.com/article")
        'a948904f2f0f479b8f8197694b30184b0d2ed1c1cd2a1ec0fb85d299a192a447'
    """
    return hashlib.sha256(url.encode('utf-8')).hexdigest()
