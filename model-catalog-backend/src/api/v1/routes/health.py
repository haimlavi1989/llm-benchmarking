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
    description="Detailed health check with component status including cache hit rate"
)
async def detailed_health_check(
    db: AsyncSession = Depends(get_db)
) -> DetailedHealthStatus:
    """Detailed health check with all component status.
    
    Checks:
    - Database connectivity
    - Redis cache (with hit rate)
    - TOPSIS ranking service
    - VRAM calculator
    """
    components = {}
    
    # 1. Database health check
    try:
        await db.execute(text("SELECT 1"))
        components["database"] = "healthy"
    except Exception as e:
        components["database"] = f"unhealthy: {str(e)}"
    
    # 2. Redis health check with hit rate
    try:
        from src.services.cache.redis_cache import cache
        
        # Test connection
        cache.redis_client.ping()
        
        # Get cache statistics
        stats = cache.get_cache_stats()
        hit_rate = stats.get('hit_rate', 0.0)
        
        # Warn if hit rate is below target (80%)
        if hit_rate >= 80:
            components["redis"] = f"healthy (hit_rate: {hit_rate}%)"
        elif hit_rate >= 50:
            components["redis"] = f"degraded (hit_rate: {hit_rate}% - target: 80%)"
        else:
            components["redis"] = f"unhealthy (hit_rate: {hit_rate}% - target: 80%)"
            
    except Exception as e:
        components["redis"] = f"unhealthy: {str(e)}"
    
    # 3. TOPSIS ranking service health check
    try:
        from src.services.ranking.topsis import calculate_topsis_scores
        import pandas as pd
        
        # Quick sanity test
        test_df = pd.DataFrame({
            'a': [1.0, 2.0, 3.0],
            'b': [3.0, 2.0, 1.0]
        })
        result = calculate_topsis_scores(
            test_df,
            weights={'a': 0.5, 'b': 0.5},
            benefit_criteria=['a'],
            cost_criteria=['b']
        )
        
        # Verify result has expected columns
        if 'topsis_score' in result.columns and 'topsis_rank' in result.columns:
            components["topsis"] = "healthy"
        else:
            components["topsis"] = "unhealthy: missing expected columns"
            
    except Exception as e:
        components["topsis"] = f"unhealthy: {str(e)}"
    
    # 4. VRAM calculator health check
    try:
        from src.services.hardware.vram_calculator import calculate_vram_requirement
        
        # Quick calculation test
        vram = calculate_vram_requirement(
            parameters=7_000_000_000,
            quantization='fp16'
        )
        
        # Verify reasonable result (should be ~16.8 GB)
        if 16 <= vram <= 18:
            components["vram_calculator"] = "healthy"
        else:
            components["vram_calculator"] = f"degraded: unexpected result {vram} GB"
            
    except Exception as e:
        components["vram_calculator"] = f"unhealthy: {str(e)}"
    
    # 5. GPU matcher health check
    try:
        from src.services.hardware.vram_calculator import recommend_gpu_config
        
        # Quick recommendation test
        configs = recommend_gpu_config(vram_needed=20.0, prefer_spot=True)
        
        if configs and len(configs) > 0:
            components["gpu_matcher"] = "healthy"
        else:
            components["gpu_matcher"] = "degraded: no configurations found"
            
    except Exception as e:
        components["gpu_matcher"] = f"unhealthy: {str(e)}"
    
    # Determine overall status
    overall_status = "healthy"
    
    # If any component is unhealthy, overall is degraded
    if any("unhealthy" in v for v in components.values()):
        overall_status = "unhealthy"
    # If any component is degraded, overall is degraded
    elif any("degraded" in v for v in components.values()):
        overall_status = "degraded"
    
    return DetailedHealthStatus(
        status=overall_status,
        version=settings.VERSION,
        components=components
    )

