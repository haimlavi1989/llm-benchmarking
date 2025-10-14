"""Pydantic schemas for model-related API requests and responses.

NO business logic - only validation and serialization.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Base Schemas
# ============================================================================

class ModelBase(BaseModel):
    """Base model schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Model name")
    architecture: str = Field(..., min_length=1, max_length=100, description="Model architecture (llama, gpt, mistral)")
    parameters: int = Field(..., gt=0, description="Number of parameters in billions")
    base_model: Optional[str] = Field(None, max_length=255, description="Parent model if fine-tuned")
    tags: Optional[List[str]] = Field(None, description="Searchable tags")


class ModelVersionBase(BaseModel):
    """Base model version schema."""
    version: str = Field(..., min_length=1, max_length=50, description="Version string (e.g., v1.0)")
    quantization: str = Field(..., description="Quantization type (fp32, fp16, int8, int4)")
    quantization_bits: int = Field(..., ge=4, le=32, description="Quantization precision (4, 8, 16, 32)")
    format: str = Field(..., description="Model format (gguf, gptq, awq, safetensors)")
    artifact_uri: Optional[str] = Field(None, max_length=500, description="Storage location URI")
    vram_requirement_gb: float = Field(..., gt=0, description="Required VRAM in GB")


# ============================================================================
# Request Schemas
# ============================================================================

class ModelCreateRequest(ModelBase):
    """Request to create a new model."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Llama-3.1-7B",
                "architecture": "llama",
                "parameters": 7_000_000_000,
                "base_model": "Llama-3",
                "tags": ["chat", "instruction-following", "open-source"]
            }
        }
    )


class ModelUpdateRequest(BaseModel):
    """Request to update an existing model."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    architecture: Optional[str] = Field(None, min_length=1, max_length=100)
    parameters: Optional[int] = Field(None, gt=0)
    base_model: Optional[str] = Field(None, max_length=255)
    tags: Optional[List[str]] = None


class ModelVersionCreateRequest(ModelVersionBase):
    """Request to create a new model version."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "version": "v1.0",
                "quantization": "fp16",
                "quantization_bits": 16,
                "format": "safetensors",
                "artifact_uri": "s3://models/llama-3.1-7b-fp16",
                "vram_requirement_gb": 16.8
            }
        }
    )


class ModelSearchRequest(BaseModel):
    """Request to search models with filters."""
    query: Optional[str] = Field(None, min_length=1, description="Search query")
    architecture: Optional[str] = Field(None, description="Filter by architecture")
    min_parameters: Optional[int] = Field(None, gt=0, description="Minimum parameter count")
    max_parameters: Optional[int] = Field(None, gt=0, description="Maximum parameter count")
    skip: int = Field(0, ge=0, description="Pagination offset")
    limit: int = Field(20, ge=1, le=100, description="Maximum results")


# ============================================================================
# Response Schemas
# ============================================================================

class ModelVersionResponse(ModelVersionBase):
    """Response with model version details."""
    id: UUID
    model_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ModelResponse(ModelBase):
    """Response with model details."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    versions: List[ModelVersionResponse] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class ModelSummaryResponse(BaseModel):
    """Lightweight model summary for list views."""
    id: UUID
    name: str
    architecture: str
    parameters: int
    tags: Optional[List[str]] = None
    version_count: int = 0
    avg_accuracy: Optional[float] = None
    avg_throughput: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)


class ModelDetailResponse(ModelResponse):
    """Detailed model response with statistics and use cases."""
    avg_accuracy: Optional[float] = None
    avg_throughput: Optional[float] = None
    avg_latency_p90_ms: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)


class ModelListResponse(BaseModel):
    """Paginated list of models."""
    items: List[ModelSummaryResponse]
    total: int = Field(..., ge=0, description="Total number of models")
    skip: int = Field(..., ge=0)
    limit: int = Field(..., ge=1)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Llama-3.1-7B",
                        "architecture": "llama",
                        "parameters": 7000000000,
                        "tags": ["chat", "open-source"],
                        "version_count": 3,
                        "avg_accuracy": 0.85,
                        "avg_throughput": 450.0
                    }
                ],
                "total": 42,
                "skip": 0,
                "limit": 20
            }
        }
    )

