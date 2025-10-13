# Supabase Setup Guide - RSS Feed Project

## ✅ Your Supabase Project is Ready!

**Project Name**: RSS Feed  
**Status**: Empty database, ready to configure  

---

## Step 1: Get Your Supabase Connection Details

### From Supabase Dashboard:

1. **Go to**: https://supabase.com/dashboard/project/[YOUR_PROJECT_ID]

2. **Get Database Connection String**:
   - Click on **Settings** (gear icon in left sidebar)
   - Click on **Database**
   - Scroll to **Connection string**
   - Select **URI** tab
   - Copy the connection string (looks like):
     ```
     postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres
     ```

3. **Get API Keys**:
   - Click on **Settings** → **API**
   - Copy these values:
     - **Project URL**: `https://xxx.supabase.co`
     - **anon public** key
     - **service_role** key (keep this secret!)

---

## Step 2: Update Your .env File

Open `/Users/ej/Downloads/RSS-Feed/backend/.env` and update these lines:

```bash
# Replace the DATABASE_URL with your Supabase connection string
# IMPORTANT: Change [YOUR-PASSWORD] to your actual database password
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres

# Add Supabase-specific settings (optional but recommended)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

### Important Notes:
- ⚠️ The connection string will have `[YOUR-PASSWORD]` - replace this with your actual password
- ⚠️ For asyncpg (which we use), you might need to change `postgresql://` to `postgresql+asyncpg://`
- ✅ Keep your service_role key secret - never commit to git!

### Final DATABASE_URL format:
```bash
DATABASE_URL=postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres
```

---

## Step 3: Test the Connection

Let's verify your connection works:

```bash
cd /Users/ej/Downloads/RSS-Feed/backend

# Create a simple test script
cat > test_connection.py << 'EOF'
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
import os

load_dotenv()

async def test_connection():
    database_url = os.getenv("DATABASE_URL")
    print(f"Connecting to: {database_url.split('@')[1]}")  # Hide password
    
    engine = create_async_engine(database_url)
    
    try:
        async with engine.begin() as conn:
            result = await conn.execute("SELECT version()")
            version = result.scalar()
            print(f"✅ Connected successfully!")
            print(f"PostgreSQL version: {version}")
            
            # Check if any tables exist
            result = await conn.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            count = result.scalar()
            print(f"📊 Tables in database: {count}")
            
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_connection())
EOF

# Run the test
python test_connection.py
```

**Expected Output**:
```
Connecting to: db.xxx.supabase.co:5432/postgres
✅ Connected successfully!
PostgreSQL version: PostgreSQL 15.x on x86_64-pc-linux-gnu
📊 Tables in database: 0
```

---

## Step 4: Create Database Tables

Now let's set up your database schema using Alembic migrations.

### Check if Alembic is configured:

```bash
# Check if alembic.ini exists
ls -la alembic.ini

# If it exists, check the current state
alembic current

# If not, we'll need to initialize it
```

### Option A: If Alembic is Already Set Up

```bash
# Run all migrations to create tables
alembic upgrade head

# Verify tables were created
python test_connection.py
# Should now show: "📊 Tables in database: 4" (or more)
```

### Option B: If Alembic Needs Setup

We'll create the tables directly using SQLAlchemy:

```bash
cat > create_tables.py << 'EOF'
import asyncio
from app.db.session import engine, Base
from app.models.rss_source import RSSSource
from app.models.article import Article
from app.models.vote import Vote
from app.models.comment import Comment

async def create_tables():
    print("Creating tables...")
    async with engine.begin() as conn:
        # Drop all tables (be careful!)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Tables created successfully!")
    
    # List created tables
    async with engine.begin() as conn:
        result = await conn.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = result.fetchall()
        print(f"\n📊 Created tables:")
        for table in tables:
            print(f"  - {table[0]}")

if __name__ == "__main__":
    asyncio.run(create_tables())
EOF

python create_tables.py
```

**Expected Output**:
```
Creating tables...
✅ Tables created successfully!

📊 Created tables:
  - articles
  - comments
  - rss_sources
  - votes
```

---

## Step 5: Verify Table Structure

Check that all tables have the correct columns:

```bash
cat > verify_schema.py << 'EOF'
import asyncio
from app.db.session import engine

async def verify_schema():
    async with engine.begin() as conn:
        # Check rss_sources table
        result = await conn.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'rss_sources'
            ORDER BY ordinal_position
        """)
        print("📋 rss_sources columns:")
        for row in result:
            print(f"  - {row[0]}: {row[1]}")
        
        print("\n📋 articles columns:")
        result = await conn.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'articles'
            ORDER BY ordinal_position
        """)
        for row in result:
            print(f"  - {row[0]}: {row[1]}")

if __name__ == "__main__":
    asyncio.run(verify_schema())
EOF

python verify_schema.py
```

---

## Step 6: Seed RSS Sources

Now let's add the 37 RSS feed sources. First, let's create a simple seeding script:

```bash
cat > seed_sources.py << 'EOF'
import asyncio
from app.db.session import AsyncSessionLocal
from app.models.rss_source import RSSSource

RSS_SOURCES = [
    # CNN Feeds
    {"name": "CNN - Top Stories", "url": "http://rss.cnn.com/rss/cnn_topstories.rss", "source_name": "CNN", "category": "general"},
    {"name": "CNN - World", "url": "http://rss.cnn.com/rss/cnn_world.rss", "source_name": "CNN", "category": "world"},
    {"name": "CNN - US", "url": "http://rss.cnn.com/rss/cnn_us.rss", "source_name": "CNN", "category": "us"},
    {"name": "CNN - Politics", "url": "http://rss.cnn.com/rss/cnn_allpolitics.rss", "source_name": "CNN", "category": "politics"},
    
    # Fox News Feeds
    {"name": "Fox News - Latest", "url": "http://feeds.foxnews.com/foxnews/latest", "source_name": "Fox News", "category": "general"},
    {"name": "Fox News - Politics", "url": "http://feeds.foxnews.com/foxnews/politics", "source_name": "Fox News", "category": "politics"},
    {"name": "Fox News - World", "url": "http://feeds.foxnews.com/foxnews/world", "source_name": "Fox News", "category": "world"},
    {"name": "Fox News - US", "url": "http://feeds.foxnews.com/foxnews/national", "source_name": "Fox News", "category": "us"},
    
    # BBC Feeds
    {"name": "BBC - Top Stories", "url": "http://feeds.bbci.co.uk/news/rss.xml", "source_name": "BBC", "category": "general"},
    {"name": "BBC - World", "url": "http://feeds.bbci.co.uk/news/world/rss.xml", "source_name": "BBC", "category": "world"},
    {"name": "BBC - US & Canada", "url": "http://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml", "source_name": "BBC", "category": "us"},
    {"name": "BBC - Politics", "url": "http://feeds.bbci.co.uk/news/politics/rss.xml", "source_name": "BBC", "category": "politics"},
    {"name": "BBC - Technology", "url": "http://feeds.bbci.co.uk/news/technology/rss.xml", "source_name": "BBC", "category": "science"},
    
    # Reuters
    {"name": "Reuters - World News", "url": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best", "source_name": "Reuters", "category": "world"},
    {"name": "Reuters - US News", "url": "https://www.reutersagency.com/feed/?best-regions=united-states", "source_name": "Reuters", "category": "us"},
    
    # NPR
    {"name": "NPR - News", "url": "https://feeds.npr.org/1001/rss.xml", "source_name": "NPR", "category": "general"},
    {"name": "NPR - Politics", "url": "https://feeds.npr.org/1014/rss.xml", "source_name": "NPR", "category": "politics"},
    {"name": "NPR - World", "url": "https://feeds.npr.org/1004/rss.xml", "source_name": "NPR", "category": "world"},
    {"name": "NPR - US", "url": "https://feeds.npr.org/1003/rss.xml", "source_name": "NPR", "category": "us"},
    
    # The Guardian
    {"name": "The Guardian - World", "url": "https://www.theguardian.com/world/rss", "source_name": "The Guardian", "category": "world"},
    {"name": "The Guardian - US", "url": "https://www.theguardian.com/us-news/rss", "source_name": "The Guardian", "category": "us"},
    {"name": "The Guardian - Politics", "url": "https://www.theguardian.com/politics/rss", "source_name": "The Guardian", "category": "politics"},
    {"name": "The Guardian - Science", "url": "https://www.theguardian.com/science/rss", "source_name": "The Guardian", "category": "science"},
    
    # Al Jazeera
    {"name": "Al Jazeera - News", "url": "https://www.aljazeera.com/xml/rss/all.xml", "source_name": "Al Jazeera", "category": "world"},
    
    # Associated Press
    {"name": "AP - Top News", "url": "https://rsshub.app/apnews/topics/apf-topnews", "source_name": "AP", "category": "general"},
    
    # Politico
    {"name": "Politico - Politics", "url": "https://www.politico.com/rss/politics08.xml", "source_name": "Politico", "category": "politics"},
    {"name": "Politico - Congress", "url": "https://www.politico.com/rss/congress.xml", "source_name": "Politico", "category": "politics"},
    
    # The Hill
    {"name": "The Hill - News", "url": "https://thehill.com/feed/", "source_name": "The Hill", "category": "politics"},
    
    # Axios
    {"name": "Axios - Politics", "url": "https://api.axios.com/feed/politics", "source_name": "Axios", "category": "politics"},
    
    # Washington Post
    {"name": "Washington Post - Politics", "url": "https://feeds.washingtonpost.com/rss/politics", "source_name": "Washington Post", "category": "politics"},
    {"name": "Washington Post - World", "url": "https://feeds.washingtonpost.com/rss/world", "source_name": "Washington Post", "category": "world"},
    
    # New York Times
    {"name": "NYT - World", "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "source_name": "New York Times", "category": "world"},
    {"name": "NYT - US", "url": "https://rss.nytimes.com/services/xml/rss/nyt/US.xml", "source_name": "New York Times", "category": "us"},
    {"name": "NYT - Politics", "url": "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml", "source_name": "New York Times", "category": "politics"},
    
    # USA Today
    {"name": "USA Today - News", "url": "http://rssfeeds.usatoday.com/usatoday-NewsTopStories", "source_name": "USA Today", "category": "general"},
    
    # CBS News
    {"name": "CBS News - Latest", "url": "https://www.cbsnews.com/latest/rss/main", "source_name": "CBS News", "category": "general"},
]

async def seed_sources():
    print(f"🌱 Seeding {len(RSS_SOURCES)} RSS sources...")
    
    async with AsyncSessionLocal() as session:
        try:
            added = 0
            skipped = 0
            
            for source_data in RSS_SOURCES:
                # Check if source already exists
                from sqlalchemy import select
                result = await session.execute(
                    select(RSSSource).where(RSSSource.url == source_data["url"])
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    print(f"⏭️  Skipping (exists): {source_data['name']}")
                    skipped += 1
                    continue
                
                # Create new source
                source = RSSSource(**source_data)
                session.add(source)
                print(f"✅ Added: {source_data['name']}")
                added += 1
            
            await session.commit()
            
            print(f"\n🎉 Seeding complete!")
            print(f"   Added: {added}")
            print(f"   Skipped: {skipped}")
            print(f"   Total: {len(RSS_SOURCES)}")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error: {str(e)}")
            raise

if __name__ == "__main__":
    asyncio.run(seed_sources())
EOF

python seed_sources.py
```

---

## Step 7: Test Fetching a Feed

Let's test fetching an actual RSS feed:

```bash
cat > test_feed_fetch.py << 'EOF'
import asyncio
from app.db.session import AsyncSessionLocal
from app.services.rss_feed_service import RSSFeedService, parse_feed_entry
from sqlalchemy import select
from app.models.rss_source import RSSSource

async def test_fetch():
    async with AsyncSessionLocal() as session:
        rss_service = RSSFeedService(session)
        
        # Get first active source
        result = await session.execute(
            select(RSSSource).where(RSSSource.is_active == True).limit(1)
        )
        source = result.scalar_one_or_none()
        
        if not source:
            print("❌ No RSS sources found. Run seed_sources.py first.")
            return
        
        print(f"📡 Fetching feed: {source.name}")
        print(f"   URL: {source.url}")
        
        try:
            feed = await rss_service.fetch_feed(source)
            
            if feed and feed.entries:
                print(f"✅ Successfully fetched {len(feed.entries)} articles!")
                
                # Show first 3 articles
                print("\n📰 Sample articles:")
                for i, entry in enumerate(feed.entries[:3], 1):
                    article_data = parse_feed_entry(entry)
                    print(f"\n{i}. {article_data.get('title', 'No title')[:60]}...")
                    print(f"   URL: {article_data.get('url', 'No URL')[:80]}")
                    print(f"   Author: {article_data.get('author', 'Unknown')}")
            else:
                print("⚠️  Feed fetched but no entries found")
                
        except Exception as e:
            print(f"❌ Error fetching feed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_fetch())
EOF

python test_feed_fetch.py
```

---

## Troubleshooting

### Connection Error: "could not connect to server"
- ✅ Check your DATABASE_URL in `.env`
- ✅ Verify you replaced `[YOUR-PASSWORD]` with actual password
- ✅ Ensure your IP is allowed (Supabase auto-allows most IPs)

### Connection Error: "asyncpg" not found
```bash
pip install asyncpg
```

### SSL Error
Add `?sslmode=require` to your DATABASE_URL:
```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@db.xxx.supabase.co:5432/postgres?sslmode=require
```

### Tables not creating
Make sure all model imports are working:
```bash
python -c "from app.models.rss_source import RSSSource; print('✅ Models loaded')"
```

---

## Next Steps After Setup

1. ✅ **Verify all tables exist** - Run `verify_schema.py`
2. ✅ **Check RSS sources** - Ensure 37 sources are seeded
3. ✅ **Test feed fetching** - Run `test_feed_fetch.py`
4. ⏭️ **Process articles** - Integrate ArticleProcessingService
5. ⏭️ **Set up Celery** - Automate feed fetching every 15 minutes
6. ⏭️ **Create API endpoints** - Expose data to frontend

---

## Supabase Dashboard Useful Links

- **SQL Editor**: Run custom queries
- **Table Editor**: View/edit data visually
- **API Docs**: Auto-generated API documentation
- **Auth**: Set up user authentication
- **Storage**: Upload article images

---

**Status**: Ready to configure! 🚀  
**Next**: Get your connection string and update `.env`
