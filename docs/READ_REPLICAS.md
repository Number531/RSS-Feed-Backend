# Read Replicas Strategy Guide

## 4. 🔄 Read Replicas for Analytics Queries

### Overview
Read replicas are **separate database servers** that replicate data from your primary database. They allow you to:
- Offload read-heavy analytics queries from the primary database
- Scale horizontally to handle more concurrent users
- Improve performance without affecting write operations

**Perfect for:** Applications with **90%+ read operations** (like analytics dashboards).

---

## Architecture

```
┌─────────────────┐
│   Application   │
│   (FastAPI)     │
└────────┬────────┘
         │
    ┌────┴─────┐
    │          │
    ▼          ▼
┌───────┐  ┌───────────┐
│Primary│  │  Replica  │
│  DB   │─→│    DB     │
│(Write)│  │  (Read)   │
└───────┘  └───────────┘
   │           │
   │           └─→ Analytics Queries
   │
   └─→ User CRUD Operations
```

### **Data Flow:**
1. **Writes** → Primary database only
2. **Reads (User data)** → Primary database
3. **Reads (Analytics)** → Replica database(s)

---

## Benefits

| Metric | Primary Only | With Read Replica |
|--------|--------------|-------------------|
| Query response time | 200-500ms | 50-150ms |
| Primary DB load | 100% | 10-20% |
| Concurrent users | ~50 | 500+ |
| Write performance | Affected by reads | Unaffected |
| Failover capability | No | Yes (auto-failover) |

---

## Implementation with Supabase

### Step 1: Enable Read Replicas in Supabase

Supabase Pro plan includes read replicas:

1. Go to **Supabase Dashboard** → Your Project
2. Navigate to **Settings** → **Database**
3. Scroll to **Read Replicas** section
4. Click **Enable Read Replicas**
5. Choose region (preferably close to your API servers)
6. Wait for replica to provision (~5-10 minutes)

### Step 2: Get Replica Connection Strings

After provisioning, you'll get two connection strings:

```bash
# Primary (for writes)
DATABASE_URL=postgresql://user:pass@db.abc123.supabase.co:6543/postgres

# Replica (for reads)
DATABASE_REPLICA_URL=postgresql://user:pass@db-read-replica.abc123.supabase.co:6543/postgres
```

### Step 3: Update Configuration

Add to `.env`:

```bash
# Existing primary database
DATABASE_URL=postgresql://...@db.abc123.supabase.co:6543/postgres

# New read replica
DATABASE_REPLICA_URL=postgresql://...@db-read-replica.abc123.supabase.co:6543/postgres

# Enable replica routing
USE_READ_REPLICA=true
```

Update `app/core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings
    
    # Read replica configuration
    DATABASE_REPLICA_URL: Optional[str] = None
    USE_READ_REPLICA: bool = False
    
    @property
    def should_use_replica(self) -> bool:
        """Check if read replica should be used."""
        return self.USE_READ_REPLICA and self.DATABASE_REPLICA_URL is not None
```

---

## Database Session Management

### Update `app/db/session.py`

```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

# Primary database engine (for writes + reads)
primary_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=False,
)

# Read replica engine (for analytics reads)
replica_engine = None
if settings.should_use_replica:
    replica_engine = create_async_engine(
        settings.DATABASE_REPLICA_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        echo=False,
    )

# Session makers
PrimarySessionLocal = async_sessionmaker(
    primary_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

ReplicaSessionLocal = async_sessionmaker(
    replica_engine if replica_engine else primary_engine,
    class_=AsyncSession,
    expire_on_commit=False,
) if replica_engine else PrimarySessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get primary database session (for writes + general reads)."""
    async with PrimarySessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_read_replica_db() -> AsyncGenerator[AsyncSession, None]:
    """Get read replica database session (for analytics reads)."""
    async with ReplicaSessionLocal() as session:
        try:
            yield session
            # No commit needed for read-only operations
        except Exception:
            raise
        finally:
            await session.close()
```

---

## Update Analytics Endpoints

### Route Analytics Queries to Replica

Update `app/api/v1/endpoints/analytics.py`:

```python
from app.db.session import get_read_replica_db

@router.get("/stats", response_model=AggregateStatsResponse)
async def get_aggregate_statistics(
    include_lifetime: bool = Query(True),
    include_trends: bool = Query(True),
    db: AsyncSession = Depends(get_read_replica_db),  # ← Use replica
) -> AggregateStatsResponse:
    """Get aggregate statistics (reads from replica)."""
    analytics_repo = AnalyticsRepository(db)
    analytics_service = AnalyticsService(analytics_repo)
    
    result = await analytics_service.get_aggregate_stats(
        include_lifetime=include_lifetime,
        include_trends=include_trends
    )
    return result


@router.get("/sources")
async def get_source_reliability(
    days: int = Query(30, ge=1, le=365),
    min_articles: int = Query(5, ge=1, le=100),
    db: AsyncSession = Depends(get_read_replica_db),  # ← Use replica
):
    """Get source reliability (reads from replica)."""
    # ... implementation


@router.get("/categories", response_model=CategoryAnalyticsResponse)
async def get_category_analytics(
    days: int = Query(30, ge=1, le=365),
    min_articles: int = Query(5, ge=1, le=100),
    sort_by: str = Query("credibility"),
    db: AsyncSession = Depends(get_read_replica_db),  # ← Use replica
) -> CategoryAnalyticsResponse:
    """Get category analytics (reads from replica)."""
    # ... implementation


@router.get("/verdict-details", response_model=VerdictAnalyticsResponse)
async def get_verdict_details(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_read_replica_db),  # ← Use replica
) -> VerdictAnalyticsResponse:
    """Get verdict analytics (reads from replica)."""
    # ... implementation
```

### Keep User Operations on Primary

User-facing endpoints should still use primary database:

```python
@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),  # ← Use primary
):
    """Get user details (uses primary DB)."""
    # ... implementation


@router.post("/articles")
async def create_article(
    article_data: ArticleCreate,
    db: AsyncSession = Depends(get_db),  # ← Use primary
):
    """Create article (writes to primary DB)."""
    # ... implementation
```

---

## Replication Lag Handling

### Understanding Replication Lag

**Replication lag** is the time delay between when data is written to the primary and when it appears on the replica.

- **Typical lag:** 0-100ms (usually <50ms)
- **High traffic lag:** 100-500ms
- **Network issues:** 1-5 seconds (rare)

### Strategy 1: Accept Eventual Consistency

For analytics, slight delays are acceptable:

```python
# Analytics can tolerate 1-2 second lag
# Users won't notice if a new article appears in stats after 1 second
```

### Strategy 2: Fallback to Primary

For critical reads that must be up-to-date:

```python
async def get_user_analytics(
    user_id: str,
    db_replica: AsyncSession = Depends(get_read_replica_db),
    db_primary: AsyncSession = Depends(get_db),
):
    """Get user-specific analytics with lag fallback."""
    try:
        # Try replica first
        result = await analytics_service.get_user_stats(db_replica, user_id)
        return result
    except ReplicationLagError:
        # Fallback to primary if lag is too high
        logger.warning("High replication lag detected, using primary DB")
        result = await analytics_service.get_user_stats(db_primary, user_id)
        return result
```

### Strategy 3: Monitor Lag

Add endpoint to check replication lag:

```python
@router.get("/admin/replication-status")
async def get_replication_status(
    db_replica: AsyncSession = Depends(get_read_replica_db),
):
    """Check replication lag (admin only)."""
    # Query replica's lag behind primary
    query = """
        SELECT 
            EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()))::int 
            AS lag_seconds
    """
    result = await db_replica.execute(text(query))
    lag = result.scalar()
    
    return {
        "replication_lag_seconds": lag,
        "status": "healthy" if lag < 5 else "degraded",
        "warning": lag > 10
    }
```

---

## Advanced: Multiple Read Replicas

For even higher scale, use multiple replicas with load balancing:

```
┌─────────────┐
│ Application │
└──────┬──────┘
       │
   ┌───┴────┐
   │        │
   ▼        ▼
┌──────┐  ┌──────────┐
│Primary│→ │ Replica 1│
│  DB   │→ │ Replica 2│
└──────┘→ │ Replica 3│
          └──────────┘
               ↑
          Load Balancer
```

### Supabase Read Pool

Supabase automatically load-balances across multiple replicas:

```python
# Supabase handles load balancing internally
DATABASE_REPLICA_URL=postgresql://...@db-read-pool.supabase.co:6543/postgres
                                            ↑
                                    Automatically routes to
                                    available replicas
```

---

## Monitoring & Maintenance

### Key Metrics to Track

```python
# Add to monitoring dashboard
- Primary DB CPU: Should stay <50% after replica setup
- Replica DB CPU: Should be 60-80% (handling most reads)
- Replication lag: Should be <100ms average
- Read query distribution: 90%+ on replica
- Write performance: Should improve with reduced contention
```

### Health Checks

Add replica health check to `/health` endpoint:

```python
@app.get("/health")
async def health_check(
    db_primary: AsyncSession = Depends(get_db),
    db_replica: AsyncSession = Depends(get_read_replica_db),
):
    """Health check including replica status."""
    health = {
        "status": "healthy",
        "database": "connected",
        "replica": "not_configured"
    }
    
    # Test primary connection
    try:
        await db_primary.execute(text("SELECT 1"))
    except Exception as e:
        health["database"] = "error"
        health["status"] = "unhealthy"
    
    # Test replica connection
    if settings.should_use_replica:
        try:
            result = await db_replica.execute(
                text("SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()))")
            )
            lag = result.scalar()
            health["replica"] = "connected"
            health["replication_lag_seconds"] = lag
            if lag > 10:
                health["replica_warning"] = "High replication lag"
        except Exception as e:
            health["replica"] = "error"
            health["status"] = "degraded"
    
    return health
```

---

## Cost Considerations

### Supabase Pricing

| Plan | Read Replica Cost |
|------|-------------------|
| Free | Not available |
| Pro ($25/mo) | **+$100/mo** per replica |
| Team/Enterprise | Custom pricing |

**Break-even analysis:**
- If you're planning to scale beyond 50 concurrent users → Worth it
- If analytics queries are slowing down user operations → Worth it
- If you need 99.95%+ uptime with auto-failover → Worth it

### AWS RDS Pricing (Alternative)

If self-hosting:
- Primary: db.t3.medium ($60/mo)
- Read replica: db.t3.medium ($60/mo)
- **Total: ~$120/mo**

---

## Rollback Plan

If replicas cause issues, easy to disable:

```bash
# In .env
USE_READ_REPLICA=false

# Or comment out
# DATABASE_REPLICA_URL=...
```

Application automatically falls back to primary for all queries.

---

## Production Checklist

- [ ] Read replica enabled in Supabase/AWS
- [ ] `DATABASE_REPLICA_URL` configured
- [ ] Session management updated (`get_read_replica_db`)
- [ ] Analytics endpoints use replica dependency
- [ ] Replication lag monitoring in place
- [ ] Health checks include replica status
- [ ] Fallback logic tested (replica failure)
- [ ] Performance metrics tracked (before/after)
- [ ] Cost monitoring enabled
- [ ] Documentation updated for ops team

---

## Expected Impact

### Performance Improvements

```
Analytics Endpoint Performance:

Before Replica:
- GET /analytics/stats: 250ms (Primary DB load: 80%)
- GET /analytics/categories: 380ms
- GET /analytics/verdict-details: 450ms
- Concurrent users: ~50

After Replica:
- GET /analytics/stats: 180ms (Replica DB load: 60%, Primary: 15%)
- GET /analytics/categories: 280ms
- GET /analytics/verdict-details: 350ms
- Concurrent users: 500+
```

### Combined with Cache + Indexes

```
Ultimate Performance Stack:

Layer 1: Browser Cache (1 min)
Layer 2: Redis Cache (5-15 min)
Layer 3: Read Replica (with indexes)
Layer 4: Materialized Views

Result:
- 95% of requests: <50ms (cache hit)
- 4% of requests: 50-150ms (replica with indexes)
- 1% of requests: 150-300ms (cache miss, complex query)

User experience: ⚡ Lightning fast dashboard!
```

---

## When NOT to Use Read Replicas

❌ **Don't use replicas if:**
- You have <1000 users
- Analytics queries are already fast (<100ms)
- Your database has low read load
- Budget is very tight
- You need real-time data (can't tolerate 50-100ms lag)

✅ **DO use replicas if:**
- You have 1000+ users or plan to scale
- Analytics queries slow down user operations
- Primary database CPU is consistently >60%
- You need high availability with auto-failover
- You want to separate analytics and transactional workloads

---

## Next Steps

1. ✅ Enable read replica in Supabase
2. ✅ Update database session management
3. ✅ Route analytics queries to replica
4. ⏭ Monitor replication lag
5. ⏭ Track performance improvements
6. ⏭ Optimize query distribution
7. ⏭ Consider additional replicas for multi-region deployment
