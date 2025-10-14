"""Health check and system status endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.api.dependencies import get_db
from src.core.config import settings
from src.schemas import HealthStatus, DetailedHealthStatus


router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=HealthStatus,
    summary="Basic health check",
    description="Simple health check endpoint"
)
async def health_check() -> HealthStatus:
    """Basic health check."""
    return HealthStatus(
        status="healthy",
        version=settings.VERSION
    )


@router.get(
    "/detailed",
    response_model=DetailedHealthStatus,
    summary="Detailed health check",
    description="Detailed health check with component status"
)
async def detailed_health_check(
    db: AsyncSession = Depends(get_db)
) -> DetailedHealthStatus:
    """Detailed health check with component status."""
    components = {}
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        components["database"] = "healthy"
    except Exception as e:
        components["database"] = f"unhealthy: {str(e)}"
    
    # Check ranking service (always healthy - it's a pure function)
    components["ranking_service"] = "healthy"
    
    # Check vram calculator (always healthy - it's a pure function)
    components["vram_calculator"] = "healthy"
    
    # Determine overall status
    overall_status = "healthy" if all(
        v == "healthy" for v in components.values()
    ) else "degraded"
    
    return DetailedHealthStatus(
        status=overall_status,
        version=settings.VERSION,
        components=components
    )

