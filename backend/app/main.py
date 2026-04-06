# backend/app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api.datasets import router as datasets_router
from backend.app.api.experiments import router as experiments_router
from backend.app.core.config import settings
from backend.app.core.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: runs on startup and shutdown."""
    setup_logging(settings.log_level)
    logger.info("ai_sandbox_startup", app_name=settings.app_name, version=settings.app_version)
    yield
    logger.info("ai_sandbox_shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# API Routers
app.include_router(datasets_router, prefix="/api/v1")
app.include_router(experiments_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }
