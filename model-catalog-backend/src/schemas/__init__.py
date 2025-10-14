"""Pydantic schemas for API validation and serialization."""

# Model schemas
from .model_schemas import (
    ModelCreateRequest,
    ModelUpdateRequest,
    ModelSearchRequest,
    ModelVersionCreateRequest,
    ModelResponse,
    ModelVersionResponse,
    ModelSummaryResponse,
    ModelDetailResponse,
    ModelListResponse,
)

# Benchmark schemas
from .benchmark_schemas import (
    BenchmarkCreateRequest,
    BenchmarkQueryRequest,
    BenchmarkResponse,
    BenchmarkStatsResponse,
    BenchmarkListResponse,
)

# Hardware schemas
from .hardware_schemas import (
    HardwareConfigCreateRequest,
    HardwareConfigQueryRequest,
    InferenceFrameworkCreateRequest,
    VRAMCalculationRequest,
    GPURecommendationRequest,
    HardwareConfigResponse,
    InferenceFrameworkResponse,
    VRAMCalculationResponse,
    GPUConfigRecommendation,
    GPURecommendationResponse,
    HardwareConfigListResponse,
)

# Recommendation schemas
from .recommendation_schemas import (
    RecommendationRequest,
    ModelCardResponse,
    RecommendationResponse,
    UseCaseResponse,
    UseCaseListResponse,
)

# Common schemas
from .common import (
    ErrorResponse,
    NotFoundError,
    SuccessResponse,
    DeleteResponse,
    PaginationParams,
    PaginationMeta,
    HealthStatus,
    DetailedHealthStatus,
    APIMetadata,
)

__all__ = [
    # Model schemas
    "ModelCreateRequest",
    "ModelUpdateRequest",
    "ModelSearchRequest",
    "ModelVersionCreateRequest",
    "ModelResponse",
    "ModelVersionResponse",
    "ModelSummaryResponse",
    "ModelDetailResponse",
    "ModelListResponse",
    
    # Benchmark schemas
    "BenchmarkCreateRequest",
    "BenchmarkQueryRequest",
    "BenchmarkResponse",
    "BenchmarkStatsResponse",
    "BenchmarkListResponse",
    
    # Hardware schemas
    "HardwareConfigCreateRequest",
    "HardwareConfigQueryRequest",
    "InferenceFrameworkCreateRequest",
    "VRAMCalculationRequest",
    "GPURecommendationRequest",
    "HardwareConfigResponse",
    "InferenceFrameworkResponse",
    "VRAMCalculationResponse",
    "GPUConfigRecommendation",
    "GPURecommendationResponse",
    "HardwareConfigListResponse",
    
    # Recommendation schemas
    "RecommendationRequest",
    "ModelCardResponse",
    "RecommendationResponse",
    "UseCaseResponse",
    "UseCaseListResponse",
    
    # Common schemas
    "ErrorResponse",
    "NotFoundError",
    "SuccessResponse",
    "DeleteResponse",
    "PaginationParams",
    "PaginationMeta",
    "HealthStatus",
    "DetailedHealthStatus",
    "APIMetadata",
]
