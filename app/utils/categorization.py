"""
Content categorization utilities for articles.
"""
from typing import Dict, List, Set


# Political keywords for political leaning detection
POLITICAL_KEYWORDS: Dict[str, Set[str]] = {
    "left": {
        "progressive", "liberal", "democrat", "left-wing", "socialism",
        "social justice", "equality", "climate action", "gun control",
        "medicare for all", "progressive tax", "union", "workers rights"
    },
    "right": {
        "conservative", "republican", "right-wing", "traditional",
        "free market", "small government", "second amendment",
        "pro-life", "family values", "law and order", "border security"
    }
}

# Category keywords for classification
CATEGORY_KEYWORDS: Dict[str, Set[str]] = {
    "politics": {
        "election", "congress", "senate", "house", "president", "vice president",
        "white house", "legislation", "policy", "political", "politician",
        "democrat", "republican", "campaign", "vote", "voting", "governor",
        "mayor", "bill", "law", "supreme court", "judicial", "impeachment",
        "administration", "cabinet", "executive order", "veto"
    },
    "us": {
        "america", "american", "united states", "u.s.", "usa", "domestic",
        "state", "states", "city", "local", "community", "region", "regional",
        "county", "municipal", "nationwide", "coast to coast"
    },
    "world": {
        "international", "global", "foreign", "overseas", "abroad",
        "country", "countries", "nation", "nations", "embassy", "diplomat",
        "diplomacy", "war", "conflict", "treaty", "alliance", "united nations",
        "un", "nato", "eu", "european union", "middle east", "asia", "africa",
        "europe", "latin america", "refugee", "immigration"
    },
    "science": {
        "research", "study", "studies", "scientist", "scientists",
        "innovation", "discovery", "experiment", "laboratory", "lab",
        "climate", "environment", "environmental", "energy", "renewable",
        "space", "nasa", "spacecraft", "satellite",
        "quantum", "genetics", "dna", "biology", "physics", "chemistry"
    },
    "technology": {
        "tech", "technology", "software", "hardware", "computer", "app",
        "iphone", "android", "apple", "google", "microsoft", "amazon",
        "artificial intelligence", "ai", "machine learning", "algorithm",
        "data", "cloud", "cybersecurity", "blockchain", "cryptocurrency",
        "internet", "digital", "online", "startup", "silicon valley"
    },
    "sports": {
        "basketball", "football", "soccer", "baseball", "hockey", "tennis",
        "nba", "nfl", "mlb", "nhl", "mls", "championship", "playoffs",
        "game", "match", "tournament", "olympics", "athlete", "team",
        "coach", "player", "score", "win", "defeat", "overtime"
    },
    "business": {
        "stock", "market", "investment", "investor", "trading", "wall street",
        "economy", "economic", "financial", "finance", "bank", "banking",
        "startup", "company", "corporation", "ceo", "merger", "acquisition",
        "revenue", "profit", "earnings", "ipo", "nasdaq", "dow jones"
    },
    "entertainment": {
        "movie", "film", "cinema", "hollywood", "actor", "actress",
        "music", "song", "album", "concert", "artist", "band",
        "television", "tv show", "series", "streaming", "netflix",
        "celebrity", "oscar", "grammy", "emmy", "box office"
    },
    "health": {
        "medical", "medicine", "health", "healthcare", "hospital",
        "doctor", "physician", "nurse", "patient", "treatment",
        "disease", "vaccine", "pandemic", "epidemic", "virus",
        "covid", "coronavirus", "symptoms", "diagnosis", "therapy"
    }
}


def categorize_article(
    title: str,
    description: str,
    feed_category: str
) -> str:
    """
    Categorize article based on content and feed category.
    
    Priority:
    1. If feed_category is specific (not 'general'), use it
    2. Otherwise, analyze title and description for keywords
    3. Default to 'general' if no match
    
    Args:
        title: Article title
        description: Article description/summary
        feed_category: Category from RSS feed source
        
    Returns:
        Category string ('general', 'politics', 'us', 'world', or 'science')
        
    Examples:
        >>> categorize_article("Biden Signs Climate Bill", "...", "general")
        'politics'
        >>> categorize_article("NASA Launches Mars Rover", "...", "general")
        'science'
        >>> categorize_article("Election Results", "...", "politics")
        'politics'
    """
    # If feed category is specific, use it
    if feed_category and feed_category != "general":
        return feed_category
    
    # Combine title and description for analysis
    text = f"{title} {description}".lower()
    
    # Score each category based on keyword matches
    scores: Dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        scores[category] = score
    
    # Find category with highest score
    if scores and max(scores.values()) > 0:
        return max(scores, key=scores.get)  # type: ignore
    
    # Default to general if no matches
    return "general"


def extract_tags(title: str, description: str, max_tags: int = 5) -> List[str]:
    """
    Extract relevant tags from article content.
    
    Args:
        title: Article title
        description: Article description
        max_tags: Maximum number of tags to return
        
    Returns:
        List of tag strings
    """
    text = f"{title} {description}".lower()
    tags: Set[str] = set()
    
    # Extract tags from all category keywords
    for category_keywords in CATEGORY_KEYWORDS.values():
        for keyword in category_keywords:
            if keyword in text:
                tags.add(keyword)
                if len(tags) >= max_tags:
                    return list(tags)[:max_tags]
    
    return list(tags)[:max_tags]


def get_category_name(category: str) -> str:
    """
    Get display name for category.
    
    Args:
        category: Category code
        
    Returns:
        Display name
    """
    category_names = {
        "general": "General",
        "politics": "Politics",
        "us": "U.S. News",
        "world": "World",
        "science": "Science",
        "technology": "Technology",
        "sports": "Sports",
        "business": "Business",
        "entertainment": "Entertainment",
        "health": "Health"
    }
    return category_names.get(category, "General")


def get_political_leaning(title: str, description: str, source_name: str = "") -> str:
    """
    Determine political leaning of an article.
    
    Args:
        title: Article title
        description: Article description
        source_name: Name of the source (optional)
        
    Returns:
        Political leaning: 'left', 'center', 'right', or 'neutral'
    """
    # Combine title and description for analysis
    text = f"{title} {description}".lower()
    
    # Score each political leaning
    scores = {}
    for leaning, keywords in POLITICAL_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        scores[leaning] = score
    
    # If no keywords match, return neutral
    if not scores or max(scores.values()) == 0:
        return "neutral"
    
    # If scores are equal (balanced content), return neutral
    left_score = scores.get("left", 0)
    right_score = scores.get("right", 0)
    
    if left_score == right_score:
        return "neutral"
    
    # Return the leaning with higher score
    return "left" if left_score > right_score else "right"
