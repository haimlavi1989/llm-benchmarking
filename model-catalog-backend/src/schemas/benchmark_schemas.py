"""Pydantic schemas for benchmark-related API requests and responses.

NO business logic - only validation and serialization.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Base Schemas
# ============================================================================

class BenchmarkBase(BaseModel):
    """Base benchmark schema."""
    model_version_id: UUID
    hardware_config_id: UUID
    framework_id: UUID
    benchmark_date: date
    workload_type: str = Field(..., max_length=100, description="Workload type (chatbot, summarization)")
    batch_size: int = Field(..., ge=1)
    sequence_length: int = Field(..., ge=1)


# ============================================================================
# Request Schemas
# ============================================================================

class BenchmarkCreateRequest(BenchmarkBase):
    """Request to create a benchmark result."""
    # Latency metrics
    ttft_p50_ms: float = Field(..., ge=0, description="Time to first token P50")
    ttft_p90_ms: float = Field(..., ge=0, description="Time to first token P90")
    ttft_p99_ms: float = Field(..., ge=0, description="Time to first token P99")
    
    # Token generation metrics
    tpot_p50_ms: float = Field(..., ge=0, description="Time per output token P50")
    tpot_p90_ms: float = Field(..., ge=0, description="Time per output token P90")
    tpot_p99_ms: float = Field(..., ge=0, description="Time per output token P99")
    
    # Throughput metrics
    throughput_tokens_sec: float = Field(..., ge=0, description="Throughput in tokens/second")
    rps_sustained: float = Field(..., ge=0, description="Requests per second")
    
    # Quality metrics
    accuracy_score: Optional[float] = Field(None, ge=0, le=1, description="Accuracy score 0-1")
    
    # Resource utilization
    gpu_utilization_pct: float = Field(..., ge=0, le=100, description="GPU utilization percentage")
    memory_used_gb: float = Field(..., ge=0, description="Memory used in GB")
    
    # Detailed metrics
    detailed_metrics: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model_version_id": "123e4567-e89b-12d3-a456-426614174000",
                "hardware_config_id": "223e4567-e89b-12d3-a456-426614174000",
                "framework_id": "323e4567-e89b-12d3-a456-426614174000",
                "benchmark_date": "2025-10-14",
                "workload_type": "chatbot",
                "batch_size": 1,
                "sequence_length": 2048,
                "ttft_p50_ms": 100.5,
                "ttft_p90_ms": 120.0,
                "ttft_p99_ms": 150.0,
                "tpot_p50_ms": 10.2,
                "tpot_p90_ms": 12.5,
                "tpot_p99_ms": 15.0,
                "throughput_tokens_sec": 450.0,
                "rps_sustained": 30.0,
                "accuracy_score": 0.85,
                "gpu_utilization_pct": 85.5,
                "memory_used_gb": 16.2
            }
        }
    )


class BenchmarkQueryRequest(BaseModel):
    """Request to query benchmarks with filters."""
    model_version_id: Optional[UUID] = None
    hardware_config_id: Optional[UUID] = None
    framework_id: Optional[UUID] = None
    workload_type: Optional[str] = None
    max_ttft_p90_ms: Optional[float] = Field(None, ge=0, description="Max acceptable P90 latency")
    min_throughput: Optional[float] = Field(None, ge=0, description="Min acceptable throughput")
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=200)


# ============================================================================
# Response Schemas
# ============================================================================

class BenchmarkResponse(BenchmarkBase):
    """Response with benchmark details."""
    id: UUID
    
    # Latency metrics
    ttft_p50_ms: float
    ttft_p90_ms: float
    ttft_p99_ms: float
    tpot_p50_ms: float
    tpot_p90_ms: float
    tpot_p99_ms: float
    
    # Throughput metrics
    throughput_tokens_sec: float
    rps_sustained: float
    
    # Quality metrics
    accuracy_score: Optional[float] = None
    
    # Resource utilization
    gpu_utilization_pct: float
    memory_used_gb: float
    
    # Metadata
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class BenchmarkStatsResponse(BaseModel):
    """Aggregated benchmark statistics."""
    total_benchmarks: int = Field(..., ge=0)
    avg_ttft_p50_ms: Optional[float] = None
    avg_ttft_p90_ms: Optional[float] = None
    avg_tpot_p50_ms: Optional[float] = None
    avg_tpot_p90_ms: Optional[float] = None
    avg_throughput: Optional[float] = None
    max_throughput: Optional[float] = None
    avg_accuracy: Optional[float] = None
    avg_gpu_utilization_pct: Optional[float] = None
    avg_memory_used_gb: Optional[float] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_benchmarks": 25,
                "avg_ttft_p50_ms": 105.2,
                "avg_ttft_p90_ms": 125.5,
                "avg_tpot_p50_ms": 10.8,
                "avg_tpot_p90_ms": 13.2,
                "avg_throughput": 445.3,
                "max_throughput": 520.0,
                "avg_accuracy": 0.84,
                "avg_gpu_utilization_pct": 83.5,
                "avg_memory_used_gb": 16.5
            }
        }
    )


class BenchmarkListResponse(BaseModel):
    """Paginated list of benchmarks."""
    items: list[BenchmarkResponse]
    total: int = Field(..., ge=0)
    skip: int = Field(..., ge=0)
    limit: int = Field(..., ge=1)

