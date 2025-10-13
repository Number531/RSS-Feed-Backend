# Fix Supabase Connection - IP Whitelist

## 🔴 Issue: "Tenant or user not found"

This error means your IP address needs to be allowed in Supabase.

---

## ✅ Solution: Add Your IP to Whitelist

### Step 1: Go to Database Settings

**Open this link:**
https://supabase.com/dashboard/project/rtmcxjlagusjhsrslvab/settings/database

### Step 2: Allow Your IP Address

1. Scroll down to **"Connection Pooling"** section
2. Look for **"Restrict connections to specific IP addresses"**
3. Click **"Add restriction"** or **"Manage"**
4. Add your IP address: **98.236.86.54**
5. Click **"Apply"** or **"Save"**

### Step 3: Test Connection

After adding your IP, run:
```bash
python test_supabase_connection.py
```

---

## 🔓 Alternative: Allow All IPs (For Testing Only)

**⚠️ Warning**: This is less secure, only use for testing

1. In the same "Connection Pooling" section
2. **Disable IP restrictions** or add `0.0.0.0/0`
3. **Remember to re-enable restrictions later!**

---

## 📋 Your Connection Details

- **Your IP**: 98.236.86.54
- **Project**: rtmcxjlagusjhsrslvab  
- **Region**: us-east-2 (Ohio)
- **Password**: @136Breezylane!  
- **Host**: aws-0-us-east-2.pooler.supabase.com
- **Port**: 6543

---

## ✅ After Whitelisting

Once your IP is whitelisted, the connection should work immediately. Run:

```bash
python test_supabase_connection.py
```

Expected output:
```
✅ Connected successfully!
📊 PostgreSQL: PostgreSQL 15.x...
📋 Tables in database: 0
✨ Database is empty and ready for setup!
```

Then proceed to:
1. `python create_tables.py` - Create database tables
2. `python seed_sources.py` - Add RSS sources
3. `python test_feed_fetch.py` - Test fetching feeds

---

## 🆘 Still Not Working?

### Check Password

The password in `.env` should be URL-encoded:
```
DATABASE_URL=postgresql+asyncpg://postgres.rtmcxjlagusjhsrslvab:%40136Breezylane%21@aws-0-us-east-2.pooler.supabase.com:6543/postgres
```

Notice:
- `@` → `%40`
- `!` → `%21`

### Verify Project is Active

1. Go to dashboard: https://supabase.com/dashboard/project/rtmcxjlagusjhsrslvab
2. Check project status is "Active" (green)
3. If paused, click "Resume"

### Reset Password (If Needed)

1. Go to: https://supabase.com/dashboard/project/rtmcxjlagusjhsrslvab/settings/database
2. Find "Database password" section
3. Click "Reset database password"
4. Copy new password
5. Update `.env` file with URL-encoded version

---

**Next**: After whitelisting your IP, test the connection!
