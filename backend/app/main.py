import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from app.core.limiter import limiter
from app.routers.events import router as events_router
from app.routers.users import router as users_router
from app.routers.scores import router as scores_router
from app.routers.alerts import router as alerts_router
from app.routers.policy import router as policy_router
from app.routers.websocket import router as websocket_router, manager
from app.routers.webhooks import router as webhooks_router
from app.routers.reports import router as reports_router
from app.worker.scheduled_scoring import start_worker, shutdown_worker
from app.config import settings

# Configure logging baseline
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ZT-IP Dashboard API",
    version="1.0.0",
    description="Zero Trust Explainable Insider Threat Detection Policy Engine API"
)

# Attach rate limiter to app state and exception handlers
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add custom production-grade HTTP security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # Allow safe defaults for API docs / static resources if requested
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Enable CORS for frontend communications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, configure to allow only specific trusted domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include all endpoint routers under /api/v1
app.include_router(events_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(scores_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(policy_router, prefix="/api/v1")
app.include_router(websocket_router, prefix="/api/v1")
app.include_router(webhooks_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")



@app.on_event("startup")
async def startup_event():
    logger.info("Initializing API, WebSockets manager, and starting scheduled scoring worker...")
    await manager.initialize()
    start_worker()


@app.on_event("shutdown")
def shutdown_event():
    logger.info("Stopping scheduled scoring worker and cleaning up connections...")
    shutdown_worker()

@app.get("/health")
def health():
    """
    Public health check endpoint.
    """
    return {"status": "ok", "service": "zt-ip-dashboard"}