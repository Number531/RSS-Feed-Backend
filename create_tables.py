#!/usr/bin/env python
"""Create all database tables for RSS Feed Aggregator"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import models to register them with SQLAlchemy
from app.db.session import engine, Base
from app.models.user import User
from app.models.rss_source import RSSSource
from app.models.article import Article
from app.models.vote import Vote
from app.models.comment import Comment

async def create_tables():
    """Create all database tables"""
    print("🏗️  Creating database tables...")
    print("=" * 70)
    
    # Check connection first
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False
    
    print(f"📡 Connected to: {database_url.split('@')[1].split('/')[0]}")
    print("")
    
    try:
        async with engine.begin() as conn:
            # Create all tables
            print("Creating tables from models...")
            await conn.run_sync(Base.metadata.create_all)
            
            print("✅ Tables created successfully!")
            print("")
            
            # List created tables
            result = await conn.execute(text("""
                SELECT table_name, 
                       pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = result.fetchall()
            
            if not tables:
                print("⚠️  No tables found after creation!")
                return False
            
            print(f"📊 Created {len(tables)} tables:")
            print("")
            for table_name, size in tables:
                print(f"   ✓ {table_name:<20} ({size})")
            
            print("")
            
            # Show table details
            print("📋 Table Details:")
            print("")
            
            for table_name, _ in tables:
                result = await conn.execute(text(f"""
                    SELECT COUNT(*) as column_count
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table_name}'
                """))
                col_count = result.scalar()
                print(f"   {table_name}: {col_count} columns")
            
            print("")
            print("=" * 70)
            print("🎉 Database setup complete!")
            print("")
            print("📦 Next steps:")
            print("   1. Seed RSS sources: python seed_sources.py")
            print("   2. Test feed fetching: python test_feed_fetch.py")
            print("   3. Start backend: uvicorn app.main:app --reload")
            
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()

if __name__ == '__main__':
    # Unset any shell DATABASE_URL that might override .env
    if 'DATABASE_URL' in os.environ and not os.environ['DATABASE_URL'].startswith('postgresql+asyncpg://postgres.rtmcxjlagusjhsrslvab'):
        print('⚠️  Warning: DATABASE_URL found in shell environment')
        print('   Temporarily unsetting to use .env value...')
        print('')
        del os.environ['DATABASE_URL']
        load_dotenv(override=True)
    
    success = asyncio.run(create_tables())
    sys.exit(0 if success else 1)
