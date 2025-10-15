#!/usr/bin/env python3
"""
Add YouTube channel RSS feeds to the database.

Usage:
    python scripts/database/add_youtube_channels.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.rss_source import RSSSource

# YouTube RSS feed format: https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}

YOUTUBE_CHANNELS = [
    # Technology
    {
        "name": "Linus Tech Tips",
        "channel_id": "UCXuqSBlHAE6Xw-yeJA0Tunw",
        "category": "technology",
        "description": "Technology reviews, PC building, and tech entertainment"
    },
    {
        "name": "Marques Brownlee (MKBHD)",
        "channel_id": "UCBJycsmduvYEL83R_U4JriQ",
        "category": "technology",
        "description": "Tech reviews and flagship device comparisons"
    },
    {
        "name": "Fireship",
        "channel_id": "UCsBjURrPoezykLs9EqgamOA",
        "category": "technology",
        "description": "100-second coding tutorials and web development"
    },
    {
        "name": "TechLinked",
        "channel_id": "UCeeFfhMcJa1kjtfZAGskOCA",
        "category": "technology",
        "description": "Daily tech news in 5 minutes"
    },
    {
        "name": "Dave2D",
        "channel_id": "UCVYamHliCI9rw1tHR1xbkfw",
        "category": "technology",
        "description": "Laptop and mobile device reviews"
    },
    
    # Science & Education
    {
        "name": "Veritasium",
        "channel_id": "UCHnyfMqiRRG1u-2MsSQLbXA",
        "category": "science",
        "description": "Science and engineering explained through experiments"
    },
    {
        "name": "Kurzgesagt – In a Nutshell",
        "channel_id": "UCsXVk37bltHxD1rDPwtNM8Q",
        "category": "science",
        "description": "Animated explanations of science and philosophy"
    },
    {
        "name": "Vsauce",
        "channel_id": "UC6nSFpj9HTCZ5t-N3Rm3-HA",
        "category": "science",
        "description": "Mind-bending questions about science and reality"
    },
    {
        "name": "SmarterEveryDay",
        "channel_id": "UC6107grRI4m0o2-emgoDnAA",
        "category": "science",
        "description": "Exploring the world through science and engineering"
    },
    {
        "name": "Mark Rober",
        "channel_id": "UCY1kMZp36IQSyNx_9h4mpCg",
        "category": "science",
        "description": "Former NASA engineer creates science experiments"
    },
    
    # Business & Finance
    {
        "name": "CNBC",
        "channel_id": "UCvJJ_dzjViJCoLf5uKUTwoA",
        "category": "business",
        "description": "Business news and market analysis"
    },
    {
        "name": "Bloomberg Technology",
        "channel_id": "UCIALMKvObZNtJ6AmdCLP7Lg",
        "category": "business",
        "description": "Tech business news and startup coverage"
    },
    {
        "name": "Graham Stephan",
        "channel_id": "UCV6KDgJskWaEckne5aPA0aQ",
        "category": "business",
        "description": "Personal finance and investing advice"
    },
    
    # Entertainment
    {
        "name": "Variety",
        "channel_id": "UCp4QFUedmund2w5KlvRvk2A",
        "category": "entertainment",
        "description": "Entertainment industry news and interviews"
    },
    
    # Sports
    {
        "name": "ESPN",
        "channel_id": "UCiWLfSweyRNmLpgEHekhoAg",
        "category": "sports",
        "description": "Sports highlights and analysis"
    },
]


def add_youtube_channels(db: Session) -> None:
    """Add YouTube channel RSS feeds to the database."""
    added_count = 0
    skipped_count = 0
    
    for channel_data in YOUTUBE_CHANNELS:
        # Construct YouTube RSS feed URL
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_data['channel_id']}"
        
        # Check if already exists
        existing = db.query(RSSSource).filter(RSSSource.url == url).first()
        if existing:
            print(f"⏭️  Skipping {channel_data['name']} (already exists)")
            skipped_count += 1
            continue
        
        # Create new RSS source
        source = RSSSource(
            name=channel_data['name'],
            url=url,
            source_name=channel_data['name'],
            category=channel_data['category'],
            description=channel_data.get('description', ''),
            is_active=True,
            fetch_interval_minutes=60  # YouTube uploads aren't super frequent
        )
        
        db.add(source)
        print(f"✅ Added {channel_data['name']} ({channel_data['category']})")
        added_count += 1
    
    db.commit()
    print(f"\n📊 Summary:")
    print(f"   Added: {added_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Total YouTube channels: {added_count + skipped_count}")


def main():
    """Main function."""
    print("🎬 Adding YouTube channel RSS feeds...\n")
    
    db = SessionLocal()
    try:
        add_youtube_channels(db)
        print("\n✅ YouTube channels added successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
