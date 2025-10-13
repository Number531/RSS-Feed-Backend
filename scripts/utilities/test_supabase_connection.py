#!/usr/bin/env python
"""Test Supabase database connection"""

import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_connection():
    """Test the database connection"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print('❌ DATABASE_URL not found in environment')
        return False
    
    print('🔌 Connecting to Supabase RSS Feed database...')
    print(f'   Project: rtmcxjlagusjhsrslvab')
    print(f'   Region: us-east-2 (Ohio)')
    print('')
    
    engine = create_async_engine(database_url, echo=False)
    
    try:
        async with engine.begin() as conn:
            # Test connection
            result = await conn.execute(text('SELECT version()'))
            version = result.scalar()
            print('✅ Connected successfully!')
            print(f'📊 PostgreSQL: {version[:70]}...')
            print('')
            
            # Check tables
            result = await conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            count = result.scalar()
            print(f'📋 Tables in database: {count}')
            
            if count == 0:
                print('')
                print('✨ Database is empty and ready for setup!')
                print('')
                print('📦 Next steps:')
                print('   1. Create tables: python create_tables.py')
                print('   2. Seed RSS sources: python seed_sources.py')
                print('   3. Test feed fetching: python test_feed_fetch.py')
            else:
                # List tables
                result = await conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """))
                tables = [row[0] for row in result]
                print(f"   Existing tables: {', '.join(tables)}")
            
        await engine.dispose()
        print('')
        print('🎉 Connection test passed!')
        return True
        
    except Exception as e:
        print(f'❌ Connection failed: {str(e)}')
        print('')
        print('💡 Troubleshooting:')
        print('   1. Check your password in .env file')
        print('   2. Verify Supabase project is active')
        print('   3. Ensure your IP is allowed in Supabase dashboard')
        print(f'   4. Dashboard: https://supabase.com/dashboard/project/rtmcxjlagusjhsrslvab')
        return False

if __name__ == '__main__':
    # Unset any shell DATABASE_URL that might override .env
    if 'DATABASE_URL' in os.environ:
        print('⚠️  Warning: DATABASE_URL found in shell environment')
        print('   Temporarily unsetting to use .env value...')
        print('')
        del os.environ['DATABASE_URL']
        load_dotenv(override=True)
    
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
