"""
Content processing utilities for HTML sanitization and text extraction.
"""
import bleach
from bs4 import BeautifulSoup
from typing import Optional


# Allowed HTML tags for article content
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li',
    'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
]

# Allowed HTML attributes
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'img': ['src', 'alt', 'title'],
}


def sanitize_html(html_content: str) -> str:
    """
    Sanitize HTML content by removing dangerous tags and attributes.
    
    Args:
        html_content: Raw HTML content
        
    Returns:
        Sanitized HTML string safe for display
    """
    if not html_content:
        return ""
    
    # Use bleach to sanitize HTML
    cleaned = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,  # Strip disallowed tags instead of escaping
    )
    
    return cleaned


def html_to_text(html_content: str) -> str:
    """
    Extract plain text from HTML content.
    
    Args:
        html_content: HTML content
        
    Returns:
        Plain text string
    """
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text


def extract_first_image(html_content: str) -> Optional[str]:
    """
    Extract the first image URL from HTML content.
    
    Args:
        html_content: HTML content
        
    Returns:
        Image URL or None
    """
    if not html_content:
        return None
    
    soup = BeautifulSoup(html_content, 'html.parser')
    img = soup.find('img')
    
    if img and img.get('src'):
        return str(img.get('src'))
    
    return None


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Truncate text to maximum length, breaking at word boundaries.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    # Find last space before max_length
    truncated = text[:max_length].rsplit(' ', 1)[0]
    return truncated + suffix


def clean_description(description: str) -> str:
    """
    Clean article description by removing HTML and truncating.
    
    Args:
        description: Raw description (may contain HTML)
        
    Returns:
        Clean plain text description
    """
    if not description:
        return ""
    
    # Convert HTML to text
    text = html_to_text(description)
    
    # Truncate to reasonable length
    text = truncate_text(text, max_length=500)
    
    return text


# Aliases for backwards compatibility with tests
extract_plain_text = html_to_text
extract_preview_image = extract_first_image


def extract_metadata(html_content: str) -> dict:
    """
    Extract metadata from HTML content (stub implementation).
    
    Args:
        html_content: HTML content
        
    Returns:
        Dictionary with metadata like images, links, etc.
    """
    # TODO: Implement full metadata extraction
    return {
        "preview_image": extract_first_image(html_content),
        "plain_text": html_to_text(html_content)[:200] if html_content else "",
    }
