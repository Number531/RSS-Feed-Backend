"""
Utility for parsing @username mentions in comment content.
"""

import re
from typing import List


def parse_mentions(content: str) -> List[str]:
    """
    Extract @username mentions from comment content.
    
    Args:
        content: Comment text content
        
    Returns:
        List of unique usernames (without @ symbol)
        
    Example:
        >>> parse_mentions("Hey @john and @jane, check this out!")
        ['john', 'jane']
    """
    # Pattern matches @username where username can contain letters, numbers, underscores, hyphens
    # Must start with letter/number, can be 3-30 characters
    pattern = r'@([a-zA-Z0-9][a-zA-Z0-9_-]{2,29})'
    
    matches = re.findall(pattern, content)
    
    # Return unique usernames (deduplicate)
    return list(set(matches))
