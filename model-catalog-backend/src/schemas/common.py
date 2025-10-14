"""Common Pydantic schemas used across the API.

Shared schemas for errors, pagination, health checks, etc.
"""

from typing import Optional, Any, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorDetail(BaseModel):
    """Error detail information."""
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    type: Optional[str] = Field(None, description="Error type")


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "ValidationError",
                "message": "Invalid input parameters",
                "details": [
                    {
                        "field": "parameters",
                        "message": "Must be greater than 0",
                        "type": "value_error"
                    }
                ],
                "timestamp": "2025-10-14T12:00:00Z"
            }
        }
    )


class NotFoundError(BaseModel):
    """404 Not Found error response."""
    error: str = "NotFound"
    message: str
    resource_type: str = Field(..., description="Type of resource not found")
    resource_id: Optional[str] = Field(None, description="ID of resource not found")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "NotFound",
                "message": "Model not found",
                "resource_type": "Model",
                "resource_id": "123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2025-10-14T12:00:00Z"
            }
        }
    )


# ============================================================================
# Success Schemas
# ============================================================================

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str
    data: Optional[Any] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": None
            }
        }
    )


class DeleteResponse(BaseModel):
    """Response for successful deletion."""
    success: bool = True
    message: str = "Resource deleted successfully"
    deleted_id: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Model deleted successfully",
                "deleted_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
    )


# ============================================================================
# Pagination Schemas
# ============================================================================

class PaginationParams(BaseModel):
    """Query parameters for pagination."""
    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of items to return")


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    total: int = Field(..., ge=0, description="Total number of items")
    skip: int = Field(..., ge=0, description="Number of items skipped")
    limit: int = Field(..., ge=1, description="Maximum items per page")
    has_more: bool = Field(..., description="Whether more items exist")
    
    @classmethod
    def from_params(cls, total: int, skip: int, limit: int) -> "PaginationMeta":
        """Create pagination metadata from parameters."""
        return cls(
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total
        )


# ============================================================================
# Health Check Schemas
# ============================================================================

class HealthStatus(BaseModel):
    """Health check status response."""
    status: str = Field(..., description="Overall status (healthy, unhealthy, degraded)")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "timestamp": "2025-10-14T12:00:00Z"
            }
        }
    )


class DetailedHealthStatus(HealthStatus):
    """Detailed health check with component status."""
    components: dict[str, str] = Field(
        ..., 
        description="Status of individual components"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "timestamp": "2025-10-14T12:00:00Z",
                "components": {
                    "database": "healthy",
                    "cache": "healthy",
                    "ranking_service": "healthy"
                }
            }
        }
    )


# ============================================================================
# Metadata Schemas
# ============================================================================

class APIMetadata(BaseModel):
    """API metadata and information."""
    name: str = "Model Catalog API"
    version: str = "0.1.0"
    description: str = "LLM Model Benchmarking & Recommendation API"
    documentation_url: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Model Catalog API",
                "version": "0.1.0",
                "description": "LLM Model Benchmarking & Recommendation API",
                "documentation_url": "https://api.example.com/docs"
            }
        }
    )

