# Database Configuration Guide

## Supabase Connection Pooling

The backend uses Supabase's connection pooling to manage database connections efficiently. This document explains the configuration and troubleshooting.

---

## Current Configuration (Production)

### Connection String
```bash
# Supabase Transaction Pooler (Port 6543)
DATABASE_URL=postgresql+asyncpg://postgres.rtmcxjlagusjhsrslvab:%40136Breezylane%21@aws-1-us-east-2.pooler.supabase.com:6543/postgres
```

### Pool Settings
```bash
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=3
```

**Total Max Connections**: 5 + 3 = **8 concurrent connections**

---

## Supabase Pooler Modes

Supabase offers two pooler modes with different trade-offs:

### 1. Session Mode (Port 5432) ❌ Not Recommended
- **Limitation**: Max 15 connections per pool
- **Issue**: Each backend worker holds persistent connections
- **Problem**: With multiple services (backend, scripts, tests), easily exhausts the pool
- **Error**: `MaxClientsInSessionMode: max clients reached`

### 2. Transaction Mode (Port 6543) ✅ **Currently Used**
- **Advantage**: Connections released after each transaction
- **Benefit**: Supports higher concurrency
- **Best For**: Applications with connection pooling (like FastAPI + SQLAlchemy)
- **No practical connection limit** for our use case

---

## Why We Switched

### Problem (Session Mode - Port 5432)
```
asyncpg.exceptions.InternalServerError: MaxClientsInSessionMode: 
max clients reached - in Session mode max clients are limited to pool_size
```

With session mode:
- Backend server: 10 connections
- Test scripts: 5 connections  
- Background workers: 3 connections
- **Total**: 18 connections → **EXCEEDS 15 limit** → Server fails to start

### Solution (Transaction Mode - Port 6543)
- Connections released immediately after queries
- Same pool size (5) handles more concurrent requests
- No startup failures
- Better resource utilization

---

## Configuration Best Practices

### For Development
```bash
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=3
DATABASE_CONNECT_TIMEOUT=30
```

### For Production (with higher load)
```bash
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=5
DATABASE_CONNECT_TIMEOUT=30
```

### Important Notes
- **Don't exceed 15 total connections** with Transaction mode for consistent performance
- Monitor active connections with: `SELECT count(*) FROM pg_stat_activity`
- Use `pool_pre_ping=True` in engine configuration to handle stale connections

---

## Connection String Formats

### Development (Direct Connection)
```bash
# Direct to database (for migrations, admin tasks)
postgresql+asyncpg://postgres:[PASSWORD]@db.rtmcxjlagusjhsrslvab.supabase.co:5432/postgres
```

### Production (Transaction Pooler)
```bash
# Through pooler (for application servers)
postgresql+asyncpg://postgres:[PASSWORD]@aws-1-us-east-2.pooler.supabase.com:6543/postgres
```

### Testing (Local)
```bash
# Local PostgreSQL (optional)
postgresql+asyncpg://postgres:[PASSWORD]@localhost:5432/rss_feed_db
```

---

## Troubleshooting

### Issue: "Address already in use" on port 8000
**Cause**: Previous uvicorn process still running  
**Solution**:
```bash
pkill -9 -f "uvicorn.*8000"
sleep 2
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Issue: MaxClientsInSessionMode error
**Cause**: Using session mode (port 5432) with insufficient pool size  
**Solution**: Switch to transaction mode (port 6543)

### Issue: Slow query performance
**Cause**: Connection pool exhausted, queries queuing  
**Solution**: 
1. Increase `DATABASE_MAX_OVERFLOW`
2. Monitor with: `SELECT * FROM pg_stat_activity`
3. Optimize long-running queries

### Issue: Connection timeout during startup
**Cause**: Network latency or database unreachable  
**Solution**:
```bash
# Increase timeout in .env
DATABASE_CONNECT_TIMEOUT=60
```

---

## Monitoring

### Check Active Connections
```sql
SELECT 
    count(*) as total_connections,
    count(*) FILTER (WHERE state = 'active') as active,
    count(*) FILTER (WHERE state = 'idle') as idle
FROM pg_stat_activity 
WHERE datname = 'postgres';
```

### Check Connection Limits
```sql
SELECT 
    setting as max_connections 
FROM pg_settings 
WHERE name = 'max_connections';
```

### Application Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
    "status": "healthy",
    "database": "connected",
    "redis": "connected"
}
```

---

## Environment Variables Reference

| Variable | Current Value | Description |
|----------|--------------|-------------|
| `DATABASE_URL` | Port 6543 pooler | Main database connection |
| `DATABASE_POOL_SIZE` | 5 | Initial connection pool size |
| `DATABASE_MAX_OVERFLOW` | 3 | Additional connections when pool full |
| `DATABASE_CONNECT_TIMEOUT` | 30 | Seconds to wait for connection |

---

## Migration Notes

When switching pooler modes:
1. Stop all backend services
2. Update `DATABASE_URL` in `.env`
3. Adjust pool size if needed
4. Restart services
5. Verify with health check

**No database migrations required** - only connection configuration changes.

---

## References

- [Supabase Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [FastAPI Database Configuration](https://fastapi.tiangolo.com/tutorial/sql-databases/)
