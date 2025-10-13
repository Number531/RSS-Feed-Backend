# 🚀 Supabase Setup - Quick Start

## ✅ What's Already Done

1. ✅ **Supabase CLI installed** via Homebrew
2. ✅ **Logged into Supabase** (authenticated)
3. ✅ **Project linked** to your backend directory
4. ✅ **API keys configured** in `.env` file
5. ✅ **Database connection string** added to `.env`

## 📊 Your Supabase Project

- **Name**: RSS Feed
- **Project ID**: `rtmcxjlagusjhsrslvab`
- **Region**: us-east-2 (Ohio)
- **Organization**: `hwpkigeiquzbjgcxfxep`
- **Status**: Active, empty database
- **Dashboard**: https://supabase.com/dashboard/project/rtmcxjlagusjhsrslvab

---

## 🎯 Next Steps (3 minutes)

### Step 1: Get Your Database Password

1. **Open dashboard**: https://supabase.com/dashboard/project/rtmcxjlagusjhsrslvab/settings/database
2. Scroll to **"Connection string"** section
3. Select **"Session Pooler"** tab (recommended) or **"Direct connection"**
4. Click **"Reveal password"** (or reset if you don't know it)
5. Copy the password

### Step 2: Run Setup Script

```bash
./setup_supabase.sh
```

The script will:
- ✅ Prompt for your database password
- ✅ Update the `.env` file automatically
- ✅ Test the database connection
- ✅ Show next steps

**That's it!** The script handles everything else.

---

## 🛠 Manual Setup (Alternative)

If you prefer to do it manually:

1. **Edit `.env` file:**
   ```bash
   nano .env
   ```

2. **Find line 22** and replace `[ENTER-PASSWORD-HERE]` with your actual password:
   ```bash
   # Before
   DATABASE_URL=postgresql+asyncpg://postgres.[ENTER-PASSWORD-HERE]@aws-0-us-east-2.pooler.supabase.com:6543/postgres
   
   # After (with your password)
   DATABASE_URL=postgresql+asyncpg://postgres.YOUR_PASSWORD_HERE@aws-0-us-east-2.pooler.supabase.com:6543/postgres
   ```

3. **Test connection:**
   ```bash
   python -c "
   import asyncio
   from sqlalchemy.ext.asyncio import create_async_engine
   from dotenv import load_dotenv
   import os
   
   load_dotenv()
   
   async def test():
       engine = create_async_engine(os.getenv('DATABASE_URL'))
       async with engine.begin() as conn:
           result = await conn.execute('SELECT version()')
           print('✅ Connected:', result.scalar())
       await engine.dispose()
   
   asyncio.run(test())
   "
   ```

---

## 📦 After Setup - Create Tables

Once connected, create your database tables:

```bash
# Create the tables script if it doesn't exist
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
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created!")
    
    # List tables
    async with engine.begin() as conn:
        result = await conn.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        print("\n📊 Tables:")
        for table in result:
            print(f"  - {table[0]}")

if __name__ == "__main__":
    asyncio.run(create_tables())
EOF

# Run it
python create_tables.py
```

Expected output:
```
Creating tables...
✅ Tables created!

📊 Tables:
  - articles
  - comments
  - rss_sources
  - votes
```

---

## 🌱 Seed RSS Sources

Add the 37 news RSS feeds:

```bash
# The seed script is in SUPABASE_SETUP_GUIDE.md (Step 6)
# Or use the seeder in your docs
python seed_sources.py
```

---

## 🧪 Test Feed Fetching

```bash
python test_feed_fetch.py
```

---

## 🚀 Start the Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then visit:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

---

## 📋 Environment Variables Set

Your `.env` file now has:

```bash
# Database (Supabase Production)
DATABASE_URL=postgresql+asyncpg://postgres.[YOUR-PASSWORD]@aws-0-us-east-2.pooler.supabase.com:6543/postgres

# Supabase API
SUPABASE_URL=https://rtmcxjlagusjhsrslvab.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_PROJECT_REF=rtmcxjlagusjhsrslvab
SUPABASE_ORG_ID=hwpkigeiquzbjgcxfxep
```

---

## 🔍 Useful Commands

```bash
# Check Supabase CLI login status
supabase --version

# List all your projects
supabase projects list

# View project details
supabase projects api-keys

# Pull database schema
supabase db pull

# Push migrations
supabase db push

# Open project dashboard
open https://supabase.com/dashboard/project/rtmcxjlagusjhsrslvab
```

---

## 🆘 Troubleshooting

### Can't connect to database
1. Check your password in `.env` file (line 22)
2. Ensure your IP is allowed in Supabase → Settings → Database → Connection Pooler
3. Try resetting your database password in Supabase dashboard

### "asyncpg" not found
```bash
pip install asyncpg
```

### SSL errors
Add `?sslmode=require` to your DATABASE_URL

### Import errors
```bash
pip install -r requirements.txt
```

---

## 📚 Documentation

- Full setup guide: `SUPABASE_SETUP_GUIDE.md`
- Database strategy: `DATABASE_STRATEGY.md`
- Article processing: `ARTICLE_PROCESSING_EXPLAINED.md`

---

## ✨ What's Next?

1. ✅ Complete Supabase setup (run `./setup_supabase.sh`)
2. ✅ Create tables
3. ✅ Seed RSS sources
4. ✅ Test feed fetching
5. ⏭ Set up Celery for automated fetching
6. ⏭ Build frontend integration
7. ⏭ Add user authentication

**Status**: Ready to go! 🚀
