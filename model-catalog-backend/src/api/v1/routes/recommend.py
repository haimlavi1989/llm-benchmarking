"""Model recommendation API endpoints.

The core recommendation engine that integrates:
- Repository queries
- TOPSIS multi-criteria ranking
- VRAM calculation
- GPU matching
"""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_model_service
from src.services import ModelService, UseCaseConstraints
from src.schemas import (
    RecommendationRequest,
    RecommendationResponse,
    ModelCardResponse,
)


router = APIRouter(prefix="/recommend", tags=["Recommendations"])


@router.post(
    "",
    response_model=RecommendationResponse,
    summary="Get model recommendations",
    description="""
    Get AI model recommendations based on use case and constraints.
    
    This endpoint performs multi-criteria decision making using TOPSIS algorithm,
    matching models to hardware requirements and optimizing for cost.
    
    The algorithm considers:
    - Accuracy (configurable weight)
    - Latency/TTFT (configurable weight)
    - Throughput (configurable weight)
    - Cost per hour (configurable weight)
    
    Returns ranked models with TOPSIS scores and recommended GPU configurations.
    """,
    response_description="List of recommended models ranked by TOPSIS score"
)
async def recommend_models(
    request: RecommendationRequest,
    service: ModelService = Depends(get_model_service)
) -> RecommendationResponse:
    """Get model recommendations based on use case and constraints.
    
    Args:
        request: Recommendation request with use case and constraints
        service: Model service (injected)
        
    Returns:
        RecommendationResponse with ranked model recommendations
        
    Raises:
        HTTPException 422: If weights don't sum to 1.0
        HTTPException 404: If use case not found
        HTTPException 500: If recommendation fails
    """
    # Validate weights sum to 1.0
    if not request.validate_weights_sum():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Weights must sum to 1.0"
        )
    
    # Build constraints
    constraints = UseCaseConstraints(
        use_case=request.use_case,
        max_latency_p90_ms=request.max_latency_p90_ms,
        min_throughput=request.min_throughput,
        min_accuracy=request.min_accuracy,
        max_cost_per_hour=request.max_cost_per_hour,
        prefer_spot_instances=request.prefer_spot_instances,
        weight_accuracy=request.weight_accuracy,
        weight_latency=request.weight_latency,
        weight_throughput=request.weight_throughput,
        weight_cost=request.weight_cost
    )
    
    try:
        # Get recommendations from service
        recommendations = await service.recommend_models(
            constraints=constraints,
            limit=request.limit
        )
        
        # Convert to response models
        model_cards = [
            ModelCardResponse(
                model_id=rec.model_id,
                model_name=rec.model_name,
                architecture=rec.architecture,
                parameters=rec.parameters,
                quantization=rec.quantization,
                avg_accuracy=rec.avg_accuracy,
                avg_ttft_p90_ms=rec.avg_ttft_p90_ms,
                avg_throughput=rec.avg_throughput,
                vram_requirement_gb=rec.vram_requirement_gb,
                recommended_gpu=rec.recommended_gpu,
                topsis_score=rec.topsis_score,
                rank=rec.rank
            )
            for rec in recommendations
        ]
        
        # Build constraints dict for response
        constraints_dict = {
            "use_case": request.use_case,
            "max_latency_p90_ms": request.max_latency_p90_ms,
            "min_throughput": request.min_throughput,
            "min_accuracy": request.min_accuracy,
            "max_cost_per_hour": request.max_cost_per_hour,
            "prefer_spot_instances": request.prefer_spot_instances,
            "weights": {
                "accuracy": request.weight_accuracy,
                "latency": request.weight_latency,
                "throughput": request.weight_throughput,
                "cost": request.weight_cost
            }
        }
        
        return RecommendationResponse(
            use_case=request.use_case,
            total_candidates=len(model_cards),  # Could be improved with actual count
            recommendations=model_cards,
            constraints=constraints_dict
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation failed: {str(e)}"
        )

