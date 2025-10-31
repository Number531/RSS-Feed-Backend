#!/usr/bin/env python3
"""Check publication dates of articles in database."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

async def main():
    engine = create_async_engine(str(settings.DATABASE_URL), echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT 
                title,
                published_date,
                url
            FROM articles
            ORDER BY created_at DESC
        """))
        articles = result.fetchall()
        
        print(f"\n{'='*80}")
        print(f"Fox News Articles - Publication Dates")
        print(f"{'='*80}\n")
        
        for i, (title, pub_date, url) in enumerate(articles, 1):
            # Extract year from URL if possible
            year_from_url = "Unknown"
            if "/2025/" in url:
                year_from_url = "2025"
            elif "/2024/" in url:
                year_from_url = "2024"
            elif "/2023/" in url:
                year_from_url = "2023"
            elif "/2022/" in url:
                year_from_url = "2022"
            
            print(f"{i}. {title[:70]}...")
            print(f"   Published Date: {pub_date}")
            print(f"   Year from URL: {year_from_url}")
            print(f"   URL: {url[:80]}...")
            print()
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
