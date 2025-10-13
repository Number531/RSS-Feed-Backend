#!/usr/bin/env python
"""Script to run database migrations."""
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings


async def run_migration():
    """Run the bookmarks table migration."""
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    try:
        async with engine.begin() as conn:
            print("🔄 Running bookmarks table migration...")
            
            # Create bookmarks table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
                    collection VARCHAR(100),
                    notes TEXT,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    CONSTRAINT uq_user_article_bookmark UNIQUE (user_id, article_id)
                )
            """))
            
            # Create indexes
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bookmarks_user_id 
                ON bookmarks(user_id)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bookmarks_article_id 
                ON bookmarks(article_id)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bookmarks_created_at 
                ON bookmarks(created_at)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bookmarks_collection 
                ON bookmarks(collection) 
                WHERE collection IS NOT NULL
            """))
            
            print("✅ Bookmarks table created successfully!")
            
            # Verify table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'bookmarks'
                )
            """))
            exists = result.scalar()
            
            if exists:
                print("✅ Verification: bookmarks table exists")
                
                # Get column information
                result = await conn.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'bookmarks'
                    ORDER BY ordinal_position
                """))
                columns = result.fetchall()
                
                print("\n📋 Table structure:")
                for col in columns:
                    nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
                    print(f"  - {col[0]}: {col[1]} {nullable}")
                
                # Get index information
                result = await conn.execute(text("""
                    SELECT indexname
                    FROM pg_indexes
                    WHERE tablename = 'bookmarks'
                    ORDER BY indexname
                """))
                indexes = result.fetchall()
                
                print("\n📊 Indexes:")
                for idx in indexes:
                    print(f"  - {idx[0]}")
                
            else:
                print("❌ Verification failed: bookmarks table not found!")
                return False
            
            return True
            
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("📦 Bookmarks Table Migration")
    print("=" * 60)
    
    success = asyncio.run(run_migration())
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
