#!/bin/bash

# Supabase Setup Helper Script
# This script helps you finalize your Supabase connection

set -e

echo "🚀 Supabase RSS Feed - Setup Helper"
echo "===================================="
echo ""
echo "✅ Project linked: RSS Feed (rtmcxjlagusjhsrslvab)"
echo "✅ API keys configured"
echo "✅ Region: us-east-2 (Ohio)"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    exit 1
fi

# Check if password is already set
if grep -q "\[ENTER-PASSWORD-HERE\]" .env; then
    echo "⚠️  Database password not set yet."
    echo ""
    echo "📋 To get your database password:"
    echo ""
    echo "1. Open this link in your browser:"
    echo "   https://supabase.com/dashboard/project/rtmcxjlagusjhsrslvab/settings/database"
    echo ""
    echo "2. Scroll to 'Connection string' section"
    echo "3. Click on 'Session Pooler' or 'Direct connection'"
    echo "4. Click 'Reveal password' (or reset if you don't know it)"
    echo ""
    
    # Prompt for password
    read -sp "Enter your database password: " DB_PASSWORD
    echo ""
    
    if [ -z "$DB_PASSWORD" ]; then
        echo "❌ No password entered. Exiting."
        exit 1
    fi
    
    # Escape special characters for sed
    ESCAPED_PASSWORD=$(echo "$DB_PASSWORD" | sed 's/[&/\]/\\&/g')
    
    # Update .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/\[ENTER-PASSWORD-HERE\]/$ESCAPED_PASSWORD/" .env
    else
        # Linux
        sed -i "s/\[ENTER-PASSWORD-HERE\]/$ESCAPED_PASSWORD/" .env
    fi
    
    echo "✅ Password set in .env file"
else
    echo "✅ Database password already configured"
fi

echo ""
echo "🔍 Testing connection..."
echo ""

# Create a simple Python test script
cat > /tmp/test_supabase_conn.py << 'EOF'
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_connection():
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        database_url = os.getenv("DATABASE_URL")
        
        if "[ENTER-PASSWORD-HERE]" in database_url:
            print("❌ Password placeholder still in DATABASE_URL")
            return False
        
        # Hide password in output
        safe_url = database_url.split('@')[1] if '@' in database_url else "unknown"
        print(f"🔌 Connecting to: {safe_url}")
        
        engine = create_async_engine(database_url, echo=False)
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected successfully!")
            print(f"📊 PostgreSQL version: {version[:50]}...")
            
            # Check tables
            result = await conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            count = result.scalar()
            print(f"📋 Tables in database: {count}")
            
            if count == 0:
                print("")
                print("⚠️  No tables found. Run migrations next:")
                print("   python create_tables.py")
            
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("")
        print("💡 Common fixes:")
        print("   1. Check your password in .env file")
        print("   2. Ensure your IP is allowed in Supabase dashboard")
        print("   3. Verify the connection string is correct")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
EOF

# Run the test
if python /tmp/test_supabase_conn.py; then
    echo ""
    echo "🎉 Setup complete!"
    echo ""
    echo "📋 Next steps:"
    echo ""
    echo "1. Create database tables:"
    echo "   python create_tables.py"
    echo ""
    echo "2. Seed RSS sources:"
    echo "   python seed_sources.py"
    echo ""
    echo "3. Test fetching a feed:"
    echo "   python test_feed_fetch.py"
    echo ""
    echo "4. Start the backend:"
    echo "   uvicorn app.main:app --reload"
else
    echo ""
    echo "⚠️  Connection test failed. Please check the error above."
    exit 1
fi

# Cleanup
rm -f /tmp/test_supabase_conn.py
