import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.events import router as events_router
from app.routers.users import router as users_router
from app.routers.scores import router as scores_router
from app.routers.alerts import router as alerts_router
from app.routers.policy import router as policy_router
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

@app.on_event("startup")
def startup_event():
    logger.info("Initializing API and starting scheduled scoring worker...")
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