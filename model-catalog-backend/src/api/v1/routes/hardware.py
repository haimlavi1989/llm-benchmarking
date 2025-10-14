"""Hardware and VRAM calculation API endpoints."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_hardware_repository
from src.repositories import HardwareRepository
from src.schemas import (
    HardwareConfigCreateRequest,
    HardwareConfigQueryRequest,
    VRAMCalculationRequest,
    GPURecommendationRequest,
    HardwareConfigResponse,
    VRAMCalculationResponse,
    GPURecommendationResponse,
    GPUConfigRecommendation,
    HardwareConfigListResponse,
    NotFoundError,
)
from src.models import HardwareConfig
from src.services.hardware.vram_calculator import (
    calculate_vram_requirement,
    recommend_gpu_config
)


router = APIRouter(prefix="/hardware", tags=["Hardware"])


# ============================================================================
# Hardware Config Endpoints
# ============================================================================

@router.post(
    "/configs",
    response_model=HardwareConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create hardware configuration",
    description="Add a new GPU hardware configuration"
)
async def create_hardware_config(
    request: HardwareConfigCreateRequest,
    repo: HardwareRepository = Depends(get_hardware_repository)
) -> HardwareConfigResponse:
    """Create a new hardware configuration."""
    config = HardwareConfig(
        gpu_type=request.gpu_type,
        gpu_count=request.gpu_count,
        vram_per_gpu_gb=request.vram_per_gpu_gb,
        total_vram_gb=request.total_vram_gb,
        cost_per_hour_usd=request.cost_per_hour_usd,
        cloud_provider=request.cloud_provider,
        instance_type=request.instance_type,
        spot_available=request.spot_available,
        specs=request.specs
    )
    
    created_config = await repo.create(config)
    
    return HardwareConfigResponse.model_validate(created_config)


@router.post(
    "/configs/query",
    response_model=HardwareConfigListResponse,
    summary="Query hardware configurations",
    description="Query GPU configurations with filters"
)
async def query_hardware_configs(
    request: HardwareConfigQueryRequest,
    repo: HardwareRepository = Depends(get_hardware_repository)
) -> HardwareConfigListResponse:
    """Query hardware configurations."""
    # Get configs by GPU type if specified
    if request.gpu_type:
        configs = await repo.get_by_gpu_type(request.gpu_type)
    # Get by VRAM requirement
    elif request.min_vram_gb:
        configs = await repo.get_by_vram_requirement(
            min_vram_gb=request.min_vram_gb,
            prefer_spot=request.spot_only
        )
    # Get cost-optimized
    elif request.min_vram_gb and request.max_cost_per_hour:
        configs = await repo.get_cost_optimized(
            min_vram_gb=request.min_vram_gb,
            max_cost_per_hour=request.max_cost_per_hour,
            cloud_provider=request.cloud_provider
        )
    # Get all
    else:
        configs = await repo.list(skip=request.skip, limit=request.limit)
    
    # Apply pagination
    total = len(configs)
    paginated = configs[request.skip:request.skip + request.limit]
    
    # Convert to responses
    items = [HardwareConfigResponse.model_validate(c) for c in paginated]
    
    return HardwareConfigListResponse(
        items=items,
        total=total,
        skip=request.skip,
        limit=request.limit
    )


@router.get(
    "/configs/{config_id}",
    response_model=HardwareConfigResponse,
    summary="Get hardware configuration",
    description="Get a specific hardware configuration by ID",
    responses={404: {"model": NotFoundError}}
)
async def get_hardware_config(
    config_id: UUID,
    repo: HardwareRepository = Depends(get_hardware_repository)
) -> HardwareConfigResponse:
    """Get hardware configuration by ID."""
    config = await repo.get_by_id(config_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hardware configuration with id {config_id} not found"
        )
    
    return HardwareConfigResponse.model_validate(config)


# ============================================================================
# VRAM Calculation Endpoints
# ============================================================================

@router.post(
    "/vram/calculate",
    response_model=VRAMCalculationResponse,
    summary="Calculate VRAM requirement",
    description="""
    Calculate VRAM requirement for a model.
    
    Formula: (parameters × bytes_per_param) × 1.2 overhead
    
    Supports quantization types: fp32, fp16, int8, int4, awq, gptq
    """
)
async def calculate_vram(
    request: VRAMCalculationRequest
) -> VRAMCalculationResponse:
    """Calculate VRAM requirement for a model.
    
    This is a pure calculation endpoint - no database access needed.
    """
    try:
        vram_gb = calculate_vram_requirement(
            parameters=request.parameters,
            quantization=request.quantization,
            batch_size=request.batch_size,
            sequence_length=request.sequence_length
        )
        
        return VRAMCalculationResponse(
            vram_required_gb=vram_gb,
            parameters=request.parameters,
            quantization=request.quantization,
            batch_size=request.batch_size,
            sequence_length=request.sequence_length
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


# ============================================================================
# GPU Recommendation Endpoints
# ============================================================================

@router.post(
    "/gpu/recommend",
    response_model=GPURecommendationResponse,
    summary="Get GPU recommendations",
    description="""
    Get GPU configuration recommendations for given VRAM requirement.
    
    Returns cost-optimized configurations with:
    - GPU type and count
    - VRAM utilization percentage
    - Cost per hour (with spot instance discounts)
    - Spot instance availability
    
    Results are sorted by cost efficiency.
    """
)
async def recommend_gpu(
    request: GPURecommendationRequest
) -> GPURecommendationResponse:
    """Get GPU configuration recommendations.
    
    This is a pure calculation endpoint - no database access needed.
    """
    try:
        configs = recommend_gpu_config(
            vram_needed=request.vram_needed_gb,
            prefer_spot=request.prefer_spot,
            max_cost_per_hour=request.max_cost_per_hour
        )
        
        # Convert to response models
        recommendations = [
            GPUConfigRecommendation(**config)
            for config in configs
        ]
        
        return GPURecommendationResponse(
            vram_needed_gb=request.vram_needed_gb,
            recommendations=recommendations
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GPU recommendation failed: {str(e)}"
        )

