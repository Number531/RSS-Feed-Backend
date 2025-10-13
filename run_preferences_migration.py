"""Run user_reading_preferences migration."""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


async def run_migration():
    """Run the migration to create user_reading_preferences table."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    try:
        async with engine.begin() as conn:
            # Create table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_reading_preferences (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                    
                    -- Tracking preferences
                    tracking_enabled BOOLEAN NOT NULL DEFAULT TRUE,
                    analytics_opt_in BOOLEAN NOT NULL DEFAULT TRUE,
                    
                    -- Auto-cleanup settings
                    auto_cleanup_enabled BOOLEAN NOT NULL DEFAULT FALSE,
                    retention_days INTEGER NOT NULL DEFAULT 365,
                    
                    -- Privacy settings
                    exclude_categories TEXT[] NOT NULL DEFAULT '{}',
                    
                    -- Timestamps
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """))
            print("✅ Table created")
            
            # Create indexes
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_user_reading_preferences_user_id 
                ON user_reading_preferences(user_id)
            """))
            print("✅ Index created")
            
            # Add check constraint
            await conn.execute(text("""
                ALTER TABLE user_reading_preferences
                DROP CONSTRAINT IF EXISTS ck_retention_days_positive
            """))
            
            await conn.execute(text("""
                ALTER TABLE user_reading_preferences
                ADD CONSTRAINT ck_retention_days_positive 
                CHECK (retention_days > 0 AND retention_days <= 3650)
            """))
            print("✅ Constraint added")
            
            # Create function for update trigger
            await conn.execute(text("""
                CREATE OR REPLACE FUNCTION update_user_reading_preferences_updated_at()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql
            """))
            print("✅ Function created")
            
            # Drop trigger if exists
            await conn.execute(text("""
                DROP TRIGGER IF EXISTS trigger_update_user_reading_preferences_updated_at 
                ON user_reading_preferences
            """))
            
            # Create trigger
            await conn.execute(text("""
                CREATE TRIGGER trigger_update_user_reading_preferences_updated_at
                    BEFORE UPDATE ON user_reading_preferences
                    FOR EACH ROW
                    EXECUTE FUNCTION update_user_reading_preferences_updated_at()
            """))
            print("✅ Trigger created")
            
        # Verify table exists
        async with engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'user_reading_preferences'
            """))
            table = result.scalar_one_or_none()
            
            if table:
                print(f"\n✅ Migration completed successfully!")
                print(f"✅ Table '{table}' exists in database")
                
                # Get column count
                result = await conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_name = 'user_reading_preferences'
                """))
                col_count = result.scalar()
                print(f"✅ Table has {col_count} columns")
            else:
                print("❌ Table verification failed")
                
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_migration())
