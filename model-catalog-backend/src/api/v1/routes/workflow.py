"""Workflow orchestration API endpoints for Argo."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.repositories.benchmark_config_repository import BenchmarkConfigRepository


router = APIRouter(prefix="/workflow", tags=["Workflow"])


# Request/Response Schemas
class ConfigBatchRequest(BaseModel):
    """Request for fetching pending configs."""
    limit: int = Field(100, ge=1, le=500, description="Batch size (1-500)")
    priority_threshold: int = Field(1000, ge=0, description="Max priority to fetch")


class ConfigResponse(BaseModel):
    """Single config response."""
    id: UUID
    model_version_id: UUID
    hardware_config_id: UUID
    framework_id: UUID
    workload_type: str
    batch_size: int
    sequence_length: int
    status: str
    priority: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int
    
    class Config:
        from_attributes = True


class ConfigStatusUpdate(BaseModel):
    """Update config status."""
    status: str = Field(..., pattern="^(completed|failed)$", description="New status: completed or failed")
    error_message: Optional[str] = Field(None, max_length=1000, description="Error message if failed")


class ProgressStatsResponse(BaseModel):
    """Progress statistics."""
    total: int = Field(..., description="Total number of configs")
    pending: int = Field(..., description="Configs waiting to run")
    running: int = Field(..., description="Configs currently running")
    completed: int = Field(..., description="Successfully completed configs")
    failed: int = Field(..., description="Failed configs")
    progress_pct: float = Field(..., description="Completion percentage (0-100)")


class StaleResetResponse(BaseModel):
    """Response from stale config reset."""
    success: bool
    configs_reset: int
    message: str


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool
    config_id: str
    message: Optional[str] = None


# API Endpoints
@router.post(
    "/configs/get-batch",
    response_model=List[ConfigResponse],
    summary="Get pending configs batch",
    description="""
    Get batch of pending configs for workflow to process.
    
    **Atomically** marks configs as 'running' to prevent race conditions.
    Use this endpoint from Argo workflow pods to fetch work.
    
    **Race-Condition Safe:**
    - Uses SELECT FOR UPDATE SKIP LOCKED
    - Multiple pods can call simultaneously
    - Each config assigned to exactly one pod
    
    **Example Usage:**
    ```bash
    curl -X POST http://api:8000/api/v1/workflow/configs/get-batch \\
      -H "Content-Type: application/json" \\
      -d '{"limit": 100, "priority_threshold": 1000}'
    ```
    """
)
async def get_pending_configs(
    request: ConfigBatchRequest,
    db: AsyncSession = Depends(get_db)
) -> List[ConfigResponse]:
    """Get batch of pending configs for workflow to process."""
    repo = BenchmarkConfigRepository(db)
    
    try:
        configs = await repo.get_pending_batch(
            limit=request.limit,
            priority_threshold=request.priority_threshold
        )
        
        return [
            ConfigResponse(
                id=c.id,
                model_version_id=c.model_version_id,
                hardware_config_id=c.hardware_config_id,
                framework_id=c.framework_id,
                workload_type=c.workload_type,
                batch_size=c.batch_size,
                sequence_length=c.sequence_length,
                status=c.status,
                priority=c.priority,
                created_at=c.created_at.isoformat() if c.created_at else None,
                started_at=c.started_at.isoformat() if c.started_at else None,
                completed_at=c.completed_at.isoformat() if c.completed_at else None,
                error_message=c.error_message,
                retry_count=c.retry_count
            )
            for c in configs
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch pending configs: {str(e)}"
        )


@router.post(
    "/configs/{config_id}/status",
    response_model=SuccessResponse,
    summary="Update config status",
    description="""
    Update config status after processing.
    
    Called by workflow after:
    - **Completing** a benchmark (status='completed')
    - **Failing** a benchmark (status='failed', error_message required)
    
    **Example - Success:**
    ```bash
    curl -X POST http://api:8000/api/v1/workflow/configs/{id}/status \\
      -H "Content-Type: application/json" \\
      -d '{"status": "completed"}'
    ```
    
    **Example - Failure:**
    ```bash
    curl -X POST http://api:8000/api/v1/workflow/configs/{id}/status \\
      -H "Content-Type: application/json" \\
      -d '{"status": "failed", "error_message": "OOM killed"}'
    ```
    """
)
async def update_config_status(
    config_id: UUID,
    update: ConfigStatusUpdate,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """Update config status after processing."""
    repo = BenchmarkConfigRepository(db)
    
    try:
        if update.status == "completed":
            config = await repo.mark_completed(config_id)
            message = "Config marked as completed"
            
        elif update.status == "failed":
            if not update.error_message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="error_message is required when status is 'failed'"
                )
            config = await repo.mark_failed(config_id, update.error_message)
            message = "Config marked as failed"
        
        return SuccessResponse(
            success=True,
            config_id=str(config.id),
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update config: {str(e)}"
        )


@router.get(
    "/progress/{model_version_id}",
    response_model=ProgressStatsResponse,
    summary="Get workflow progress",
    description="""
    Get workflow progress for a model version.
    
    Returns status breakdown and completion percentage.
    
    **Example:**
    ```bash
    curl http://api:8000/api/v1/workflow/progress/{model-version-id}
    ```
    
    **Response:**
    ```json
    {
      "total": 9000,
      "pending": 2000,
      "running": 100,
      "completed": 6800,
      "failed": 100,
      "progress_pct": 75.56
    }
    ```
    """
)
async def get_workflow_progress(
    model_version_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> ProgressStatsResponse:
    """Get workflow progress for a model version."""
    repo = BenchmarkConfigRepository(db)
    
    try:
        stats = await repo.get_progress_stats(model_version_id)
        return ProgressStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get progress stats: {str(e)}"
        )


@router.post(
    "/maintenance/reset-stale",
    response_model=StaleResetResponse,
    summary="Reset stale running configs",
    description="""
    Reset stale 'running' configs back to 'pending'.
    
    **Use Case:** Recover from spot instance interruptions.
    
    Configs stuck in 'running' status longer than `timeout_minutes`
    are reset to 'pending' for retry.
    
    **Recommended:** Run via CronWorkflow every 30 minutes.
    
    **Example:**
    ```bash
    curl -X POST "http://api:8000/api/v1/workflow/maintenance/reset-stale?timeout_minutes=120"
    ```
    """
)
async def reset_stale_configs(
    timeout_minutes: int = Query(120, ge=30, le=1440, description="Timeout in minutes (30-1440)"),
    db: AsyncSession = Depends(get_db)
) -> StaleResetResponse:
    """Reset stale 'running' configs back to 'pending'."""
    repo = BenchmarkConfigRepository(db)
    
    try:
        count = await repo.reset_stale_running(timeout_minutes)
        
        return StaleResetResponse(
            success=True,
            configs_reset=count,
            message=f"Reset {count} stale configs back to pending (timeout: {timeout_minutes}min)"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset stale configs: {str(e)}"
        )


@router.get(
    "/configs/{model_version_id}",
    response_model=List[ConfigResponse],
    summary="Get configs for model version",
    description="""
    Get all configs for a model version, optionally filtered by status.
    
    **Example - All configs:**
    ```bash
    curl http://api:8000/api/v1/workflow/configs/{model-version-id}
    ```
    
    **Example - Only failed:**
    ```bash
    curl "http://api:8000/api/v1/workflow/configs/{model-version-id}?status=failed"
    ```
    """
)
async def get_configs_by_model_version(
    model_version_id: UUID,
    status: Optional[str] = Query(None, pattern="^(pending|running|completed|failed)$"),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
) -> List[ConfigResponse]:
    """Get configs for a model version."""
    repo = BenchmarkConfigRepository(db)
    
    try:
        configs = await repo.get_by_model_version(
            model_version_id=model_version_id,
            status=status,
            limit=limit
        )
        
        return [
            ConfigResponse(
                id=c.id,
                model_version_id=c.model_version_id,
                hardware_config_id=c.hardware_config_id,
                framework_id=c.framework_id,
                workload_type=c.workload_type,
                batch_size=c.batch_size,
                sequence_length=c.sequence_length,
                status=c.status,
                priority=c.priority,
                created_at=c.created_at.isoformat() if c.created_at else None,
                started_at=c.started_at.isoformat() if c.started_at else None,
                completed_at=c.completed_at.isoformat() if c.completed_at else None,
                error_message=c.error_message,
                retry_count=c.retry_count
            )
            for c in configs
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configs: {str(e)}"
        )




