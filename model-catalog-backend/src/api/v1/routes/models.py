"""Model-related API endpoints."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db, get_model_repository
from src.repositories import ModelRepository
from src.schemas import (
    ModelCreateRequest,
    ModelUpdateRequest,
    ModelSearchRequest,
    ModelResponse,
    ModelSummaryResponse,
    ModelDetailResponse,
    ModelListResponse,
    DeleteResponse,
    NotFoundError,
)
from src.models import Model


router = APIRouter(prefix="/models", tags=["Models"])


@router.post(
    "",
    response_model=ModelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new model",
    description="Create a new AI model entry in the catalog"
)
async def create_model(
    request: ModelCreateRequest,
    repo: ModelRepository = Depends(get_model_repository)
) -> ModelResponse:
    """Create a new model."""
    # Create model entity
    model = Model(
        name=request.name,
        architecture=request.architecture,
        parameters=request.parameters,
        base_model=request.base_model,
        tags=request.tags,
        metadata={}
    )
    
    # Save to database
    created_model = await repo.create(model)
    
    return ModelResponse.model_validate(created_model)


@router.get(
    "",
    response_model=ModelListResponse,
    summary="List models",
    description="Get paginated list of models with optional filters"
)
async def list_models(
    skip: int = 0,
    limit: int = 20,
    architecture: str | None = None,
    repo: ModelRepository = Depends(get_model_repository)
) -> ModelListResponse:
    """List models with pagination."""
    # Build criteria
    criteria = {}
    if architecture:
        criteria['architecture'] = architecture
    
    # Get models
    if criteria:
        models = await repo.find_by_criteria(criteria, skip=skip, limit=limit)
    else:
        models = await repo.list(skip=skip, limit=limit)
    
    # Get total count
    total = await repo.count()
    
    # Convert to summary responses
    items = [
        ModelSummaryResponse(
            id=m.id,
            name=m.name,
            architecture=m.architecture,
            parameters=m.parameters,
            tags=m.tags,
            version_count=len(m.versions) if hasattr(m, 'versions') else 0
        )
        for m in models
    ]
    
    return ModelListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{model_id}",
    response_model=ModelResponse,
    summary="Get model by ID",
    description="Retrieve a specific model by its UUID",
    responses={404: {"model": NotFoundError}}
)
async def get_model(
    model_id: UUID,
    repo: ModelRepository = Depends(get_model_repository)
) -> ModelResponse:
    """Get model by ID."""
    model = await repo.get_by_id(model_id)
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {model_id} not found"
        )
    
    return ModelResponse.model_validate(model)


@router.get(
    "/{model_id}/details",
    response_model=ModelDetailResponse,
    summary="Get detailed model information",
    description="Get model with statistics and benchmark data",
    responses={404: {"model": NotFoundError}}
)
async def get_model_details(
    model_id: UUID,
    repo: ModelRepository = Depends(get_model_repository)
) -> ModelDetailResponse:
    """Get detailed model information."""
    model = await repo.get_with_benchmarks(model_id)
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {model_id} not found"
        )
    
    return ModelDetailResponse.model_validate(model)


@router.patch(
    "/{model_id}",
    response_model=ModelResponse,
    summary="Update model",
    description="Update an existing model's information",
    responses={404: {"model": NotFoundError}}
)
async def update_model(
    model_id: UUID,
    request: ModelUpdateRequest,
    repo: ModelRepository = Depends(get_model_repository)
) -> ModelResponse:
    """Update model."""
    # Get existing model
    model = await repo.get_by_id(model_id)
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {model_id} not found"
        )
    
    # Update fields if provided
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(model, field, value)
    
    # Save changes
    updated_model = await repo.update(model_id, model)
    
    return ModelResponse.model_validate(updated_model)


@router.delete(
    "/{model_id}",
    response_model=DeleteResponse,
    summary="Delete model",
    description="Delete a model and all associated data",
    responses={404: {"model": NotFoundError}}
)
async def delete_model(
    model_id: UUID,
    repo: ModelRepository = Depends(get_model_repository)
) -> DeleteResponse:
    """Delete model."""
    # Check if exists
    exists = await repo.exists(model_id)
    
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {model_id} not found"
        )
    
    # Delete
    deleted = await repo.delete(model_id)
    
    return DeleteResponse(
        success=deleted,
        message="Model deleted successfully",
        deleted_id=str(model_id)
    )


@router.post(
    "/search",
    response_model=ModelListResponse,
    summary="Search models",
    description="Search models with advanced filters"
)
async def search_models(
    request: ModelSearchRequest,
    repo: ModelRepository = Depends(get_model_repository)
) -> ModelListResponse:
    """Search models with filters."""
    models = await repo.search_models(
        query=request.query or "",
        architecture=request.architecture,
        min_parameters=request.min_parameters,
        max_parameters=request.max_parameters
    )
    
    # Apply pagination
    paginated_models = models[request.skip:request.skip + request.limit]
    
    # Convert to summary responses
    items = [
        ModelSummaryResponse(
            id=m.id,
            name=m.name,
            architecture=m.architecture,
            parameters=m.parameters,
            tags=m.tags,
            version_count=len(m.versions) if hasattr(m, 'versions') else 0
        )
        for m in paginated_models
    ]
    
    return ModelListResponse(
        items=items,
        total=len(models),
        skip=request.skip,
        limit=request.limit
    )

