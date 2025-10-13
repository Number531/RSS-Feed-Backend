#!/usr/bin/env python
"""Script to apply reading history migration."""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings


async def run_migration():
    """Run the reading_history table migration."""
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    try:
        async with engine.begin() as conn:
            print("🔄 Running reading_history table migration...")
            
            # Create reading_history table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS reading_history (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
                    viewed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    duration_seconds INTEGER,
                    scroll_percentage DECIMAL(5,2)
                )
            """))
            
            # Create indexes
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_reading_history_user_id 
                ON reading_history(user_id)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_reading_history_article_id 
                ON reading_history(article_id)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_reading_history_viewed_at 
                ON reading_history(viewed_at)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_reading_history_user_viewed 
                ON reading_history(user_id, viewed_at)
            """))
            
            print("✅ Reading history table created successfully!")
            
            # Verify table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'reading_history'
                )
            """))
            exists = result.scalar()
            
            if exists:
                print("✅ Verification: reading_history table exists")
                
                # Get column information
                result = await conn.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'reading_history'
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
                    WHERE tablename = 'reading_history'
                    ORDER BY indexname
                """))
                indexes = result.fetchall()
                
                print("\n📊 Indexes:")
                for idx in indexes:
                    print(f"  - {idx[0]}")
                
                return True
            else:
                print("❌ Verification failed: reading_history table not found!")
                return False
            
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("📖 Reading History Table Migration")
    print("=" * 60)
    
    success = asyncio.run(run_migration())
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
