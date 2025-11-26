"""
Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.session import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Setup structured logging
    from app.core.logging_config import setup_logging

    setup_logging()

    # Startup
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    print(f"🔍 Debug mode: {settings.DEBUG}")

    # Initialize Sentry for error tracking
    if settings.SENTRY_DSN:
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT or settings.ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=0.1,
            integrations=[
                # FastAPI integration included automatically
            ],
            release=f"{settings.APP_NAME}@{settings.APP_VERSION}",
        )
        print("✅ Sentry error tracking initialized")

    # Validate production configuration
    try:
        settings.validate_production_config()
        if settings.is_production:
            print("✅ Production configuration validated")
    except ValueError as e:
        print(f"❌ Configuration validation failed: {e}")
        raise

    # Initialize database connection
    await init_db()
    print("✅ Database connection initialized")

    # Initialize cache manager
    from app.utils.cache import cache_manager

    await cache_manager.connect()
    print("✅ Cache manager initialized")

    # Initialize metrics endpoint
    from app.main import instrumentator

    instrumentator.expose(app, endpoint="/metrics", include_in_schema=False)
    print("✅ Metrics endpoint exposed at /metrics")

    yield

    # Shutdown
    print("🛑 Shutting down application...")
    await cache_manager.disconnect()
    print("✅ Cache manager disconnected")
    await close_db()
    print("✅ Database connection closed")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="RSS News Aggregator API - Reddit-style news platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# Add Prometheus metrics instrumentation
from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=False,  # Always enable metrics
    should_instrument_requests_inprogress=True,
    excluded_handlers=[".*admin.*", "/metrics"],
    inprogress_name="fastapi_inprogress",
    inprogress_labels=True,
)
instrumentator.instrument(app)


# Add Security Headers middleware (first for all responses)
from app.middleware.security_headers import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)

# Add Request Size Limit middleware (before processing request body)
from app.middleware.request_size_limit import RequestSizeLimitMiddleware

app.add_middleware(RequestSizeLimitMiddleware)

# Add Request ID middleware (before CORS)
from app.middleware.request_id import RequestIDMiddleware

app.add_middleware(RequestIDMiddleware)

# Add Rate Limit middleware (after Request ID)
from app.middleware.rate_limit import limiter, RateLimitMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app.state.limiter = limiter
app.add_middleware(RateLimitMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "healthy",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with actual dependency testing."""
    from datetime import datetime, timezone

    from sqlalchemy import text

    from app.db.session import get_db

    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION,
    }

    # Test database connectivity
    try:
        async for db in get_db():
            await db.execute(text("SELECT 1"))
            health_status["database"] = "connected"
            break
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"] = f"error: {str(e)}"

    # Test Redis connectivity (if configured)
    try:
        if settings.REDIS_URL:
            import redis.asyncio as redis

            redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await redis_client.ping()
            health_status["redis"] = "connected"
            await redis_client.close()
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"
        # Redis is optional, don't mark as unhealthy

    # Return appropriate status code
    from fastapi import status as http_status
    from fastapi.responses import JSONResponse

    status_code = (
        http_status.HTTP_200_OK
        if health_status["status"] == "healthy"
        else http_status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(content=health_status, status_code=status_code)


@app.get(f"{settings.API_V1_PREFIX}/")
async def api_root():
    """API v1 root endpoint."""
    return {
        "message": "RSS News Aggregator API v1",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "articles": f"{settings.API_V1_PREFIX}/articles",
            "auth": f"{settings.API_V1_PREFIX}/auth",
            "users": f"{settings.API_V1_PREFIX}/users",
            "sources": f"{settings.API_V1_PREFIX}/sources",
        },
    }


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 Not Found errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "message": "The requested resource was not found",
            "path": str(request.url.path),
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 Internal Server errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An internal server error occurred",
        },
    )


# Import and include API routers
from app.api.v1.api import api_router

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
