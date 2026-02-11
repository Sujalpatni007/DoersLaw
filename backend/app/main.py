"""
DOER Platform - FastAPI Application Entry Point

This is the main application file that configures and runs the DOER platform API.

To run the development server:
    cd backend
    python -m venv venv
    source venv/bin/activate  # or venv\\Scripts\\activate on Windows
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000

Then visit http://localhost:8000/docs for the Swagger UI documentation.

PRODUCTION UPGRADES:
1. Redis Middleware: Add caching and session management
   ```python
   from fastapi_limiter import FastAPILimiter
   from redis import asyncio as aioredis
   
   @app.on_event("startup")
   async def startup():
       redis = await aioredis.from_url(settings.REDIS_URL)
       await FastAPILimiter.init(redis)
   ```

2. Sentry Error Tracking:
   ```python
   import sentry_sdk
   sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=1.0)
   ```

3. Structured Logging:
   ```python
   import structlog
   structlog.configure(processors=[...])
   ```

4. Metrics (Prometheus):
   ```python
   from prometheus_fastapi_instrumentator import Instrumentator
   Instrumentator().instrument(app).expose(app)
   ```

5. Background Tasks (Celery):
   Configure Celery with Redis as broker for document processing, notifications, etc.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.config import get_settings
from app.database import init_db, close_db
from app.schemas import HealthResponse

# Import routers
from app.routers import auth, cases, documents, tasks, talent, nlp, verification, agents, marketplace, sms, government, analytics, case_analysis

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    
    Startup:
    - Initialize database tables
    - PRODUCTION: Initialize Redis connection pool
    - PRODUCTION: Start background task workers
    
    Shutdown:
    - Close database connections
    - PRODUCTION: Close Redis connections
    - PRODUCTION: Graceful worker shutdown
    """
    # Startup
    print("🚀 Starting DOER Platform API...")
    await init_db()
    print("✅ Database initialized")
    
    # PRODUCTION: Initialize Redis
    # redis = await aioredis.from_url(settings.REDIS_URL)
    # await FastAPILimiter.init(redis)
    
    yield
    
    # Shutdown
    print("👋 Shutting down DOER Platform API...")
    await close_db()
    print("✅ Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
## DOER Platform - Land Dispute Resolution System

A comprehensive platform for managing land dispute cases, including:

- **User Management**: Registration, authentication, role-based access
- **Case Management**: Create, track, and resolve land disputes
- **Document Handling**: Upload and manage case-related documents
- **Workflow Tasks**: Manage case workflow with task assignments
- **Legal Talent**: Match cases with qualified legal professionals

### Authentication
Most endpoints require JWT authentication. Use the `/auth/login` endpoint to obtain tokens.

### Roles
- **client**: Regular users who submit cases
- **admin**: Platform administrators with full access
- **legal_talent**: Legal professionals assigned to cases
- **support**: Support staff for case management
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc alternative
    openapi_url="/openapi.json"
)


# =============================================================================
# MIDDLEWARE
# =============================================================================

# CORS Configuration
# PRODUCTION: Restrict origins to your actual frontend domains
origins = settings.CORS_ORIGINS.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware (development)
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Add processing time header to responses.
    
    PRODUCTION: Replace with proper observability (OpenTelemetry, Datadog, etc.)
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# PRODUCTION: Add rate limiting middleware
# @app.middleware("http")
# async def rate_limit_middleware(request: Request, call_next):
#     """Rate limiting using Redis."""
#     client_ip = request.client.host
#     key = f"rate_limit:{client_ip}"
#     
#     count = await redis.incr(key)
#     if count == 1:
#         await redis.expire(key, 60)  # 60 second window
#     
#     if count > 100:  # 100 requests per minute
#         return JSONResponse(
#             status_code=429,
#             content={"detail": "Too many requests"}
#         )
#     
#     return await call_next(request)


# =============================================================================
# ROUTERS
# =============================================================================

# Include all API routers with /api/v1 prefix
API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(cases.router, prefix=API_PREFIX)
app.include_router(documents.router, prefix=API_PREFIX)
app.include_router(tasks.router, prefix=API_PREFIX)
app.include_router(talent.router, prefix=API_PREFIX)
app.include_router(nlp.router, prefix=API_PREFIX)
app.include_router(verification.router, prefix=API_PREFIX)
app.include_router(agents.router, prefix=API_PREFIX)
app.include_router(marketplace.router, prefix=API_PREFIX)
app.include_router(sms.router, prefix=API_PREFIX)
app.include_router(sms.admin_router, prefix=API_PREFIX)
app.include_router(government.router, prefix=API_PREFIX)
app.include_router(analytics.router, prefix=API_PREFIX)
app.include_router(analytics.admin_router, prefix=API_PREFIX)
app.include_router(case_analysis.router, prefix=API_PREFIX)


# =============================================================================
# ROOT ENDPOINTS
# =============================================================================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint returning API information.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    PRODUCTION: Add more detailed health checks:
    - Database connectivity
    - Redis connectivity
    - External service health
    - Disk space
    - Memory usage
    """
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        database="sqlite"  # PRODUCTION: Check actual connection
    )


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    
    PRODUCTION:
    - Log to Sentry or similar
    - Don't expose internal error details
    - Return consistent error format
    """
    # PRODUCTION: Log to error tracking service
    # sentry_sdk.capture_exception(exc)
    
    # In debug mode, return full error details
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "type": type(exc).__name__
            }
        )
    
    # In production, return generic error
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred"}
    )


# =============================================================================
# DEVELOPMENT RUNNER
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # PRODUCTION: Set to False
        log_level="info"
    )
