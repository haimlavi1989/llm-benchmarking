"""Protocol definitions for repository pattern."""

from typing import Protocol, List, Optional, Dict, Any, TypeVar, Generic
from uuid import UUID

T = TypeVar('T')


class BaseRepositoryProtocol(Protocol, Generic[T]):
    """Base protocol for all repositories."""
    
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        ...
    
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """Get entity by ID."""
        ...
    
    async def list(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination."""
        ...
    
    async def update(self, entity_id: UUID, entity: T) -> T:
        """Update an existing entity."""
        ...
    
    async def delete(self, entity_id: UUID) -> bool:
        """Delete an entity by ID."""
        ...
    
    async def count(self) -> int:
        """Get total count of entities."""
        ...
    
    async def exists(self, entity_id: UUID) -> bool:
        """Check if entity exists."""
        ...


class ModelRepositoryProtocol(BaseRepositoryProtocol[T], Protocol):
    """Protocol for model repository operations."""
    
    async def get_by_name(self, name: str) -> Optional[T]:
        """Get model by name."""
        ...
    
    async def search_by_use_case(self, use_case: str) -> List[T]:
        """Get models suitable for a specific use case."""
        ...
    
    async def get_with_benchmarks(self, model_id: UUID) -> Optional[T]:
        """Get model with all benchmark results."""
        ...
    
    async def search_models(
        self, 
        query: str, 
        architecture: Optional[str] = None,
        min_parameters: Optional[int] = None,
        max_parameters: Optional[int] = None
    ) -> List[T]:
        """Search models with filters."""
        ...


class BenchmarkRepositoryProtocol(BaseRepositoryProtocol[T], Protocol):
    """Protocol for benchmark repository operations."""
    
    async def get_by_model_version(self, model_version_id: UUID) -> List[T]:
        """Get benchmarks by model version ID."""
        ...
    
    async def get_by_criteria(
        self,
        model_version_id: Optional[UUID] = None,
        hardware_config_id: Optional[UUID] = None,
        framework_id: Optional[UUID] = None,
        workload_type: Optional[str] = None,
        max_ttft_p90: Optional[float] = None,
        min_throughput: Optional[float] = None
    ) -> List[T]:
        """Get benchmarks filtered by multiple criteria."""
        ...
    
    async def get_aggregated_stats(
        self,
        model_version_id: UUID,
        workload_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get aggregated benchmark statistics."""
        ...
    
    async def get_latest_benchmarks(
        self,
        model_version_id: UUID,
        limit: int = 10
    ) -> List[T]:
        """Get latest benchmarks for a model version."""
        ...


class HardwareRepositoryProtocol(BaseRepositoryProtocol[T], Protocol):
    """Protocol for hardware repository operations."""
    
    async def get_by_gpu_type(self, gpu_type: str) -> List[T]:
        """Get hardware configs by GPU type."""
        ...
    
    async def get_by_vram_requirement(
        self, 
        min_vram_gb: int,
        prefer_spot: bool = True
    ) -> List[T]:
        """Get hardware configs meeting VRAM requirement."""
        ...
    
    async def get_cost_optimized(
        self,
        min_vram_gb: int,
        max_cost_per_hour: Optional[float] = None,
        cloud_provider: Optional[str] = None
    ) -> List[T]:
        """Get cost-optimized hardware configurations."""
        ...
