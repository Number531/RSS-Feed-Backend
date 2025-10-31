#!/usr/bin/env python3
"""Check what articles are currently in the database."""

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
        result = await session.execute(text('''
            SELECT 
                title,
                url,
                fact_check_score,
                fact_check_verdict,
                created_at
            FROM articles
            ORDER BY created_at DESC
        '''))
        articles = result.fetchall()
        
        print(f'\n{"="*80}')
        print(f'Articles in Database: {len(articles)} total')
        print(f'{"="*80}\n')
        
        for i, (title, url, score, verdict, created_at) in enumerate(articles, 1):
            print(f'{i}. {title}')
            print(f'   URL: {url[:70]}...')
            print(f'   Score: {score}, Verdict: {verdict}')
            print(f'   Created: {created_at}\n')
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
