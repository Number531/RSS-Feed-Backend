#!/usr/bin/env python3
"""Inspect the CNN Politics RSS feed to see what articles it returns."""

import feedparser
import httpx
from datetime import datetime

async def main():
    url = "http://rss.cnn.com/rss/cnn_allpolitics.rss"
    
    print(f"\n{'='*80}")
    print(f"Fetching RSS Feed: {url}")
    print(f"{'='*80}\n")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.get(url)
        response.raise_for_status()
    
    feed = feedparser.parse(response.content)
    
    print(f"Feed Title: {feed.feed.get('title', 'N/A')}")
    print(f"Feed Description: {feed.feed.get('description', 'N/A')}")
    print(f"Total Entries: {len(feed.entries)}\n")
    
    print(f"{'='*80}")
    print(f"ARTICLES IN FEED (All {len(feed.entries)})")
    print(f"{'='*80}\n")
    
    from datetime import datetime, timedelta
    today = datetime.utcnow()
    recent_cutoff = today - timedelta(days=7)  # Last 7 days
    
    recent_articles = []
    old_articles = []
    
    for i, entry in enumerate(feed.entries, 1):
        title = entry.get('title', 'No Title')
        link = entry.get('link', 'No Link')
        
        # Get published date
        published = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            published = datetime(*entry.updated_parsed[:6])
        
        if published and published >= recent_cutoff:
            recent_articles.append((i, title, published, link))
        else:
            old_articles.append((i, title, published, link))
    
    print(f"\n{'='*80}")
    print(f"RECENT ARTICLES (Last 7 days): {len(recent_articles)}")
    print(f"{'='*80}\n")
    
    if recent_articles:
        for i, title, published, link in recent_articles[:10]:
            print(f"{i}. {title}")
            print(f"   Published: {published}")
            print(f"   URL: {link[:80]}...")
            print()
    else:
        print("❌ NO RECENT ARTICLES FOUND!\n")
    
    print(f"\n{'='*80}")
    print(f"OLD ARTICLES (Older than 7 days): {len(old_articles)}")
    print(f"{'='*80}\n")
    
    for i, title, published, link in old_articles[:5]:
        print(f"{i}. {title}")
        print(f"   Published: {published}")
        print(f"   URL: {link[:80]}...")
        print()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
