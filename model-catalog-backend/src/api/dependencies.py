"""FastAPI dependency injection for services and database sessions.

Clean dependency injection without business logic.
"""

from typing import AsyncGenerator
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.core.config import settings
from src.repositories import (
    ModelRepository,
    BenchmarkRepository,
    HardwareRepository
)
from src.services import ModelService


# ============================================================================
# Database Dependencies
# ============================================================================

# Create async engine
async_engine = create_async_engine(
    settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'),
    echo=settings.DEBUG,
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session.
    
    Yields:
        AsyncSession: Database session
        
    Example:
        ```python
        @router.get("/models")
        async def get_models(db: AsyncSession = Depends(get_db)):
            ...
        ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ============================================================================
# Repository Dependencies
# ============================================================================

async def get_model_repository(
    db: AsyncSession = Depends(get_db)
) -> ModelRepository:
    """Get model repository instance.
    
    Args:
        db: Database session from get_db dependency
        
    Returns:
        ModelRepository: Repository instance
    """
    return ModelRepository(db)


async def get_benchmark_repository(
    db: AsyncSession = Depends(get_db)
) -> BenchmarkRepository:
    """Get benchmark repository instance.
    
    Args:
        db: Database session from get_db dependency
        
    Returns:
        BenchmarkRepository: Repository instance
    """
    return BenchmarkRepository(db)


async def get_hardware_repository(
    db: AsyncSession = Depends(get_db)
) -> HardwareRepository:
    """Get hardware repository instance.
    
    Args:
        db: Database session from get_db dependency
        
    Returns:
        HardwareRepository: Repository instance
    """
    return HardwareRepository(db)


# ============================================================================
# Service Dependencies
# ============================================================================

async def get_model_service(
    model_repo: ModelRepository = Depends(get_model_repository),
    benchmark_repo: BenchmarkRepository = Depends(get_benchmark_repository),
    hardware_repo: HardwareRepository = Depends(get_hardware_repository)
) -> ModelService:
    """Get model service instance with injected repositories.
    
    Args:
        model_repo: Model repository (injected)
        benchmark_repo: Benchmark repository (injected)
        hardware_repo: Hardware repository (injected)
        
    Returns:
        ModelService: Service instance with all dependencies
        
    Example:
        ```python
        @router.post("/recommend")
        async def recommend_models(
            request: RecommendationRequest,
            service: ModelService = Depends(get_model_service)
        ):
            recommendations = await service.recommend_models(...)
            return recommendations
        ```
    """
    return ModelService(
        model_repo=model_repo,
        benchmark_repo=benchmark_repo,
        hardware_repo=hardware_repo
    )


# ============================================================================
# Utility Dependencies
# ============================================================================

async def verify_api_key(api_key: str = Header(None)) -> str:
    """Verify API key for protected endpoints (placeholder).
    
    Args:
        api_key: API key from header
        
    Returns:
        str: Verified API key
        
    Raises:
        HTTPException: If API key is invalid
        
    Note:
        This is a placeholder. Implement actual authentication as needed.
    """
    # TODO: Implement actual API key verification
    # For now, just return the key
    return api_key or "dev-key"


async def get_current_user(api_key: str = Depends(verify_api_key)) -> dict:
    """Get current authenticated user (placeholder).
    
    Args:
        api_key: Verified API key
        
    Returns:
        dict: User information
        
    Note:
        This is a placeholder. Implement actual user retrieval as needed.
    """
    # TODO: Implement actual user retrieval
    return {
        "id": "dev-user",
        "role": "admin",
        "api_key": api_key
    }

