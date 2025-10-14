"""Benchmark-related API endpoints."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_benchmark_repository
from src.repositories import BenchmarkRepository
from src.schemas import (
    BenchmarkCreateRequest,
    BenchmarkQueryRequest,
    BenchmarkResponse,
    BenchmarkStatsResponse,
    BenchmarkListResponse,
    NotFoundError,
)
from src.models import BenchmarkResult


router = APIRouter(prefix="/benchmarks", tags=["Benchmarks"])


@router.post(
    "",
    response_model=BenchmarkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create benchmark result",
    description="Add a new benchmark result to the database"
)
async def create_benchmark(
    request: BenchmarkCreateRequest,
    repo: BenchmarkRepository = Depends(get_benchmark_repository)
) -> BenchmarkResponse:
    """Create a new benchmark result."""
    # Create benchmark entity
    benchmark = BenchmarkResult(
        model_version_id=request.model_version_id,
        hardware_config_id=request.hardware_config_id,
        framework_id=request.framework_id,
        benchmark_date=request.benchmark_date,
        workload_type=request.workload_type,
        batch_size=request.batch_size,
        sequence_length=request.sequence_length,
        ttft_p50_ms=request.ttft_p50_ms,
        ttft_p90_ms=request.ttft_p90_ms,
        ttft_p99_ms=request.ttft_p99_ms,
        tpot_p50_ms=request.tpot_p50_ms,
        tpot_p90_ms=request.tpot_p90_ms,
        tpot_p99_ms=request.tpot_p99_ms,
        throughput_tokens_sec=request.throughput_tokens_sec,
        rps_sustained=request.rps_sustained,
        accuracy_score=request.accuracy_score,
        gpu_utilization_pct=request.gpu_utilization_pct,
        memory_used_gb=request.memory_used_gb,
        detailed_metrics=request.detailed_metrics
    )
    
    # Save to database
    created_benchmark = await repo.create(benchmark)
    
    return BenchmarkResponse.model_validate(created_benchmark)


@router.post(
    "/query",
    response_model=BenchmarkListResponse,
    summary="Query benchmarks",
    description="Query benchmarks with filters and pagination"
)
async def query_benchmarks(
    request: BenchmarkQueryRequest,
    repo: BenchmarkRepository = Depends(get_benchmark_repository)
) -> BenchmarkListResponse:
    """Query benchmarks with filters."""
    # Get filtered benchmarks
    benchmarks = await repo.get_by_criteria(
        model_version_id=request.model_version_id,
        hardware_config_id=request.hardware_config_id,
        framework_id=request.framework_id,
        workload_type=request.workload_type,
        max_ttft_p90=request.max_ttft_p90_ms,
        min_throughput=request.min_throughput
    )
    
    # Apply pagination
    total = len(benchmarks)
    paginated = benchmarks[request.skip:request.skip + request.limit]
    
    # Convert to responses
    items = [BenchmarkResponse.model_validate(b) for b in paginated]
    
    return BenchmarkListResponse(
        items=items,
        total=total,
        skip=request.skip,
        limit=request.limit
    )


@router.get(
    "/{benchmark_id}",
    response_model=BenchmarkResponse,
    summary="Get benchmark by ID",
    description="Retrieve a specific benchmark result by its UUID",
    responses={404: {"model": NotFoundError}}
)
async def get_benchmark(
    benchmark_id: UUID,
    repo: BenchmarkRepository = Depends(get_benchmark_repository)
) -> BenchmarkResponse:
    """Get benchmark by ID."""
    benchmark = await repo.get_by_id(benchmark_id)
    
    if not benchmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benchmark with id {benchmark_id} not found"
        )
    
    return BenchmarkResponse.model_validate(benchmark)


@router.get(
    "/model-version/{model_version_id}",
    response_model=BenchmarkListResponse,
    summary="Get benchmarks for model version",
    description="Get all benchmarks for a specific model version"
)
async def get_benchmarks_by_model_version(
    model_version_id: UUID,
    skip: int = 0,
    limit: int = 50,
    repo: BenchmarkRepository = Depends(get_benchmark_repository)
) -> BenchmarkListResponse:
    """Get benchmarks for a model version."""
    benchmarks = await repo.get_by_model_version(model_version_id)
    
    # Apply pagination
    total = len(benchmarks)
    paginated = benchmarks[skip:skip + limit]
    
    # Convert to responses
    items = [BenchmarkResponse.model_validate(b) for b in paginated]
    
    return BenchmarkListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/model-version/{model_version_id}/stats",
    response_model=BenchmarkStatsResponse,
    summary="Get aggregated statistics",
    description="Get aggregated benchmark statistics for a model version"
)
async def get_benchmark_stats(
    model_version_id: UUID,
    workload_type: str | None = None,
    repo: BenchmarkRepository = Depends(get_benchmark_repository)
) -> BenchmarkStatsResponse:
    """Get aggregated benchmark statistics."""
    stats = await repo.get_aggregated_stats(
        model_version_id=model_version_id,
        workload_type=workload_type
    )
    
    return BenchmarkStatsResponse(**stats)


@router.get(
    "/model-version/{model_version_id}/latest",
    response_model=BenchmarkListResponse,
    summary="Get latest benchmarks",
    description="Get most recent benchmarks for a model version"
)
async def get_latest_benchmarks(
    model_version_id: UUID,
    limit: int = 10,
    repo: BenchmarkRepository = Depends(get_benchmark_repository)
) -> BenchmarkListResponse:
    """Get latest benchmarks."""
    benchmarks = await repo.get_latest_benchmarks(
        model_version_id=model_version_id,
        limit=limit
    )
    
    # Convert to responses
    items = [BenchmarkResponse.model_validate(b) for b in benchmarks]
    
    return BenchmarkListResponse(
        items=items,
        total=len(items),
        skip=0,
        limit=limit
    )

