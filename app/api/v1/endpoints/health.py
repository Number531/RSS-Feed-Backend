"""Enhanced health check API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.health_check_service import HealthCheckService

router = APIRouter()


@router.get(
    "/health/detailed",
    summary="Get detailed system health status",
    description="""
    Get comprehensive health check of all system components.
    
    **Components Checked:**
    - Database (PostgreSQL) - connection, response time, pool stats
    - Redis - connection, response time, memory usage
    - API server - responsiveness
    
    **Status Values:**
    - `healthy`: All components operational
    - `degraded`: One or more components unhealthy
    
    **Use Cases:**
    - Kubernetes liveness/readiness probes
    - Monitoring dashboards
    - Automated alerting
    - Load balancer health checks
    """,
    responses={
        200: {"description": "Health status retrieved successfully"},
        500: {"description": "Health check failed"},
    },
    tags=["health"],
)
async def get_detailed_health(db: AsyncSession = Depends(get_db)):
    """Get detailed health status of all system components."""
    service = HealthCheckService(db)
    health_status = await service.get_health_status()
    return health_status
