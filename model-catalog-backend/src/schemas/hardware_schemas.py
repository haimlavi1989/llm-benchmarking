"""Pydantic schemas for hardware-related API requests and responses.

NO business logic - only validation and serialization.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Base Schemas
# ============================================================================

class HardwareConfigBase(BaseModel):
    """Base hardware configuration schema."""
    gpu_type: str = Field(..., max_length=50, description="GPU type (A100-80GB, H100, L4)")
    gpu_count: int = Field(..., ge=1, le=8, description="Number of GPUs")
    vram_per_gpu_gb: int = Field(..., gt=0, description="VRAM per GPU in GB")
    total_vram_gb: int = Field(..., gt=0, description="Total VRAM across all GPUs")
    cost_per_hour_usd: float = Field(..., ge=0, description="Cost per hour in USD")
    cloud_provider: str = Field(..., max_length=50, description="Cloud provider (aws, gcp, azure)")
    instance_type: Optional[str] = Field(None, max_length=100, description="Instance type")
    spot_available: bool = Field(True, description="Spot instance availability")
    specs: Optional[Dict[str, Any]] = None


class InferenceFrameworkBase(BaseModel):
    """Base inference framework schema."""
    name: str = Field(..., max_length=50, description="Framework name (vLLM, TGI, LMDeploy)")
    version: str = Field(..., max_length=20, description="Framework version")
    supports_quantization: bool = True
    supports_streaming: bool = True
    capabilities: Optional[Dict[str, Any]] = None
    config_template: Optional[Dict[str, Any]] = None


# ============================================================================
# Request Schemas
# ============================================================================

class HardwareConfigCreateRequest(HardwareConfigBase):
    """Request to create hardware configuration."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "gpu_type": "A100-80GB",
                "gpu_count": 4,
                "vram_per_gpu_gb": 80,
                "total_vram_gb": 320,
                "cost_per_hour_usd": 9.60,
                "cloud_provider": "aws",
                "instance_type": "p4d.24xlarge",
                "spot_available": True
            }
        }
    )


class HardwareConfigQueryRequest(BaseModel):
    """Request to query hardware configurations."""
    gpu_type: Optional[str] = None
    min_vram_gb: Optional[int] = Field(None, gt=0)
    max_cost_per_hour: Optional[float] = Field(None, ge=0)
    cloud_provider: Optional[str] = None
    spot_only: bool = False
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)


class InferenceFrameworkCreateRequest(InferenceFrameworkBase):
    """Request to create inference framework."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "vLLM",
                "version": "v0.5.0",
                "supports_quantization": True,
                "supports_streaming": True,
                "capabilities": {
                    "max_batch_size": 256,
                    "supports_awq": True,
                    "supports_gptq": True
                }
            }
        }
    )


class VRAMCalculationRequest(BaseModel):
    """Request to calculate VRAM requirements."""
    parameters: int = Field(..., gt=0, description="Number of parameters")
    quantization: str = Field(..., description="Quantization type (fp32, fp16, int8, int4)")
    batch_size: int = Field(1, ge=1, description="Batch size")
    sequence_length: int = Field(2048, ge=1, description="Sequence length")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "parameters": 7_000_000_000,
                "quantization": "fp16",
                "batch_size": 1,
                "sequence_length": 2048
            }
        }
    )


class GPURecommendationRequest(BaseModel):
    """Request for GPU configuration recommendations."""
    vram_needed_gb: float = Field(..., gt=0, description="Required VRAM in GB")
    prefer_spot: bool = Field(True, description="Prefer spot instances")
    max_cost_per_hour: Optional[float] = Field(None, ge=0, description="Maximum cost constraint")
    cloud_provider: Optional[str] = Field(None, description="Filter by cloud provider")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "vram_needed_gb": 42.0,
                "prefer_spot": True,
                "max_cost_per_hour": 5.0,
                "cloud_provider": "aws"
            }
        }
    )


# ============================================================================
# Response Schemas
# ============================================================================

class HardwareConfigResponse(HardwareConfigBase):
    """Response with hardware configuration details."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class InferenceFrameworkResponse(InferenceFrameworkBase):
    """Response with inference framework details."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class VRAMCalculationResponse(BaseModel):
    """Response with VRAM calculation results."""
    vram_required_gb: float = Field(..., description="Required VRAM in GB")
    parameters: int
    quantization: str
    batch_size: int
    sequence_length: int
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "vram_required_gb": 16.8,
                "parameters": 7_000_000_000,
                "quantization": "fp16",
                "batch_size": 1,
                "sequence_length": 2048
            }
        }
    )


class GPUConfigRecommendation(BaseModel):
    """Single GPU configuration recommendation."""
    gpu_type: str
    count: int
    vram_per_gpu_gb: int
    total_vram_gb: int
    utilization_pct: float = Field(..., ge=0, le=100)
    cost_per_hour_usd: float
    spot_available: bool
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "gpu_type": "A100-80GB",
                "count": 1,
                "vram_per_gpu_gb": 80,
                "total_vram_gb": 80,
                "utilization_pct": 52.5,
                "cost_per_hour_usd": 0.60,
                "spot_available": True
            }
        }
    )


class GPURecommendationResponse(BaseModel):
    """Response with GPU recommendations."""
    vram_needed_gb: float
    recommendations: list[GPUConfigRecommendation]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "vram_needed_gb": 42.0,
                "recommendations": [
                    {
                        "gpu_type": "A100-80GB",
                        "count": 1,
                        "vram_per_gpu_gb": 80,
                        "total_vram_gb": 80,
                        "utilization_pct": 52.5,
                        "cost_per_hour_usd": 0.60,
                        "spot_available": True
                    }
                ]
            }
        }
    )


class HardwareConfigListResponse(BaseModel):
    """Paginated list of hardware configurations."""
    items: list[HardwareConfigResponse]
    total: int = Field(..., ge=0)
    skip: int = Field(..., ge=0)
    limit: int = Field(..., ge=1)

