"""API v1 routes."""

from fastapi import APIRouter

from .models import router as models_router
from .benchmarks import router as benchmarks_router
from .recommend import router as recommend_router
from .hardware import router as hardware_router
from .health import router as health_router


# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(health_router)
api_router.include_router(models_router)
api_router.include_router(benchmarks_router)
api_router.include_router(recommend_router)
api_router.include_router(hardware_router)


__all__ = ["api_router"]
