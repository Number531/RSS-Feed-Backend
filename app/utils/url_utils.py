"""
URL normalization and hashing utilities for article deduplication.
"""
import hashlib
from urllib.parse import urlparse, parse_qs, urlunparse
from typing import Set


# Tracking parameters to remove for normalization
TRACKING_PARAMS: Set[str] = {
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'fbclid', 'gclid', 'msclkid', 'ref', 'source', 'mc_cid', 'mc_eid',
    '_ga', '_gac', '_gl', 'icid', 'ncid'
}


def normalize_url(url: str) -> str:
    """
    Normalize URL for deduplication.
    
    Steps:
    1. Convert to lowercase
    2. Remove trailing slashes from path
    3. Remove tracking query parameters
    4. Remove URL fragments
    5. Remove 'www.' prefix
    6. Normalize mobile URLs (m.example.com -> example.com)
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL string
        
    Examples:
        >>> normalize_url("https://example.com/article?utm_source=feed")
        'https://example.com/article'
        >>> normalize_url("https://example.com/article/")
        'https://example.com/article'
        >>> normalize_url("https://example.com/article#comments")
        'https://example.com/article'
    """
    # Parse URL
    parsed = urlparse(url.lower().strip())
    
    # Normalize domain (remove www. and m. prefixes)
    domain = parsed.netloc
    if domain.startswith('www.'):
        domain = domain[4:]
    elif domain.startswith('m.'):
        domain = domain[2:]
    
    # Remove tracking parameters
    query_dict = parse_qs(parsed.query)
    filtered_query = {
        k: v for k, v in query_dict.items() 
        if k.lower() not in TRACKING_PARAMS
    }
    
    # Reconstruct query string
    query = '&'.join(
        f'{k}={v[0]}' for k, v in sorted(filtered_query.items())
    )
    
    # Remove trailing slash from path
    path = parsed.path.rstrip('/')
    if not path:
        path = '/'
    
    # Reconstruct URL (without fragment)
    normalized = urlunparse((
        parsed.scheme,
        domain,
        path,
        '',  # params
        query,
        ''   # fragment
    ))
    
    return normalized


def generate_url_hash(url: str) -> str:
    """
    Generate SHA-256 hash of normalized URL.
    
    Args:
        url: URL to hash
        
    Returns:
        64-character hexadecimal hash string
        
    Example:
        >>> hash1 = generate_url_hash("https://example.com/article?utm_source=feed")
        >>> hash2 = generate_url_hash("https://example.com/article")
        >>> hash1 == hash2
        True
    """
    normalized = normalize_url(url)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def extract_domain(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain string (e.g., 'example.com')
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    # Remove www. prefix
    if domain.startswith('www.'):
        domain = domain[4:]
    
    return domain
