"""Pydantic schemas for model recommendation API.

NO business logic - only validation and serialization.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ============================================================================
# Request Schemas
# ============================================================================

class RecommendationRequest(BaseModel):
    """Request for model recommendations based on use case and constraints."""
    # Use case
    use_case: str = Field(..., min_length=1, max_length=100, description="Use case category")
    
    # SLA constraints
    max_latency_p90_ms: Optional[float] = Field(None, gt=0, description="Maximum acceptable P90 latency")
    min_throughput: Optional[float] = Field(None, gt=0, description="Minimum throughput requirement")
    min_accuracy: Optional[float] = Field(None, ge=0, le=1, description="Minimum accuracy requirement")
    
    # Cost constraints
    max_cost_per_hour: Optional[float] = Field(None, gt=0, description="Maximum cost per hour in USD")
    prefer_spot_instances: bool = Field(True, description="Prefer spot instances for cost savings")
    
    # TOPSIS weights (must sum to 1.0)
    weight_accuracy: float = Field(0.30, ge=0, le=1, description="Weight for accuracy criterion")
    weight_latency: float = Field(0.25, ge=0, le=1, description="Weight for latency criterion")
    weight_throughput: float = Field(0.25, ge=0, le=1, description="Weight for throughput criterion")
    weight_cost: float = Field(0.20, ge=0, le=1, description="Weight for cost criterion")
    
    # Pagination
    limit: int = Field(10, ge=1, le=50, description="Maximum number of recommendations")
    
    @field_validator('weight_accuracy', 'weight_latency', 'weight_throughput', 'weight_cost')
    @classmethod
    def validate_weight_range(cls, v):
        """Validate weight is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError('Weight must be between 0 and 1')
        return v
    
    def validate_weights_sum(self) -> bool:
        """Validate that all weights sum to 1.0."""
        total = self.weight_accuracy + self.weight_latency + self.weight_throughput + self.weight_cost
        return abs(total - 1.0) < 0.001  # Allow small floating point errors
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "use_case": "chatbot",
                "max_latency_p90_ms": 300,
                "min_throughput": 400,
                "min_accuracy": 0.80,
                "max_cost_per_hour": 5.0,
                "prefer_spot_instances": True,
                "weight_accuracy": 0.30,
                "weight_latency": 0.25,
                "weight_throughput": 0.25,
                "weight_cost": 0.20,
                "limit": 10
            }
        }
    )


# ============================================================================
# Response Schemas
# ============================================================================

class ModelCardResponse(BaseModel):
    """Model card in recommendation response."""
    # Model identification
    model_id: UUID
    model_name: str
    architecture: str
    parameters: int
    quantization: str
    
    # Performance metrics
    avg_accuracy: Optional[float] = Field(None, ge=0, le=1)
    avg_ttft_p90_ms: Optional[float] = Field(None, gt=0)
    avg_throughput: Optional[float] = Field(None, gt=0)
    
    # Hardware requirements
    vram_requirement_gb: float = Field(..., gt=0)
    recommended_gpu: Dict[str, Any]
    
    # Ranking
    topsis_score: float = Field(..., ge=0, le=1, description="TOPSIS score (0-1, higher is better)")
    rank: int = Field(..., ge=1, description="Rank position (1 = best)")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "model_id": "123e4567-e89b-12d3-a456-426614174000",
                "model_name": "Llama-3.1-7B",
                "architecture": "llama",
                "parameters": 7_000_000_000,
                "quantization": "fp16",
                "avg_accuracy": 0.85,
                "avg_ttft_p90_ms": 120.0,
                "avg_throughput": 450.0,
                "vram_requirement_gb": 16.8,
                "recommended_gpu": {
                    "gpu_type": "L4",
                    "count": 1,
                    "total_vram_gb": 24,
                    "utilization_pct": 70.0,
                    "cost_per_hour_usd": 0.13,
                    "spot_available": True
                },
                "topsis_score": 0.82,
                "rank": 1
            }
        }
    )


class RecommendationResponse(BaseModel):
    """Response with model recommendations."""
    use_case: str
    total_candidates: int = Field(..., ge=0, description="Total number of candidate models evaluated")
    recommendations: list[ModelCardResponse]
    
    # Applied constraints
    constraints: Dict[str, Any]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "use_case": "chatbot",
                "total_candidates": 25,
                "recommendations": [
                    {
                        "model_id": "123e4567-e89b-12d3-a456-426614174000",
                        "model_name": "Llama-3.1-7B",
                        "architecture": "llama",
                        "parameters": 7_000_000_000,
                        "quantization": "fp16",
                        "avg_accuracy": 0.85,
                        "avg_ttft_p90_ms": 120.0,
                        "avg_throughput": 450.0,
                        "vram_requirement_gb": 16.8,
                        "recommended_gpu": {
                            "gpu_type": "L4",
                            "count": 1,
                            "total_vram_gb": 24,
                            "utilization_pct": 70.0,
                            "cost_per_hour_usd": 0.13,
                            "spot_available": True
                        },
                        "topsis_score": 0.82,
                        "rank": 1
                    }
                ],
                "constraints": {
                    "max_latency_p90_ms": 300,
                    "min_throughput": 400,
                    "min_accuracy": 0.80,
                    "max_cost_per_hour": 5.0
                }
            }
        }
    )


class UseCaseResponse(BaseModel):
    """Use case information response."""
    id: UUID
    category: str
    subcategory: Optional[str] = None
    pipeline_tag: Optional[str] = None
    characteristics: Optional[Dict[str, Any]] = None
    default_weights: Optional[Dict[str, float]] = None
    
    model_config = ConfigDict(from_attributes=True)


class UseCaseListResponse(BaseModel):
    """List of available use cases."""
    items: list[UseCaseResponse]
    total: int = Field(..., ge=0)

