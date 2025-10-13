"""Protocol definitions for repository pattern."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, TypeVar, Generic
from uuid import UUID

T = TypeVar('T')


class BaseRepositoryProtocol(ABC, Generic[T]):
    """Base protocol for all repositories."""
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination."""
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Delete an entity by ID."""
        pass


class ModelRepositoryProtocol(BaseRepositoryProtocol):
    """Protocol for model repository operations."""
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[T]:
        """Get model by name."""
        pass
    
    @abstractmethod
    async def get_by_architecture(self, architecture: str) -> List[T]:
        """Get models by architecture."""
        pass
    
    @abstractmethod
    async def get_by_use_case(self, use_case: str) -> List[T]:
        """Get models suitable for a specific use case."""
        pass
    
    @abstractmethod
    async def search_models(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Search models with query and filters."""
        pass


class BenchmarkRepositoryProtocol(BaseRepositoryProtocol):
    """Protocol for benchmark repository operations."""
    
    @abstractmethod
    async def get_by_model_id(self, model_id: UUID) -> List[T]:
        """Get benchmarks by model ID."""
        pass
    
    @abstractmethod
    async def get_by_hardware_config(self, hardware_config_id: UUID) -> List[T]:
        """Get benchmarks by hardware configuration."""
        pass
    
    @abstractmethod
    async def get_by_framework(self, framework_id: UUID) -> List[T]:
        """Get benchmarks by inference framework."""
        pass
    
    @abstractmethod
    async def get_benchmarks_by_criteria(
        self,
        model_ids: Optional[List[UUID]] = None,
        hardware_config_ids: Optional[List[UUID]] = None,
        framework_ids: Optional[List[UUID]] = None,
        min_accuracy: Optional[float] = None,
        max_latency: Optional[float] = None,
        min_throughput: Optional[float] = None
    ) -> List[T]:
        """Get benchmarks filtered by multiple criteria."""
        pass
    
    @abstractmethod
    async def get_aggregated_stats(
        self,
        model_id: UUID,
        time_period: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get aggregated benchmark statistics for a model."""
        pass


class HardwareRepositoryProtocol(BaseRepositoryProtocol):
    """Protocol for hardware repository operations."""
    
    @abstractmethod
    async def get_by_gpu_type(self, gpu_type: str) -> List[T]:
        """Get hardware configs by GPU type."""
        pass
    
    @abstractmethod
    async def get_by_vram_range(
        self, 
        min_vram: float, 
        max_vram: float
    ) -> List[T]:
        """Get hardware configs by VRAM range."""
        pass
    
    @abstractmethod
    async def get_cost_optimized_configs(
        self,
        min_vram: float,
        max_cost_per_hour: Optional[float] = None,
        prefer_spot: bool = True
    ) -> List[T]:
        """Get cost-optimized hardware configurations."""
        pass


class UseCaseRepositoryProtocol(BaseRepositoryProtocol):
    """Protocol for use case repository operations."""
    
    @abstractmethod
    async def get_by_category(self, category: str) -> List[T]:
        """Get use cases by category."""
        pass
    
    @abstractmethod
    async def get_by_pipeline_tag(self, pipeline_tag: str) -> Optional[T]:
        """Get use case by HuggingFace pipeline tag."""
        pass
    
    @abstractmethod
    async def get_model_suitability_scores(self, model_id: UUID) -> List[Dict[str, Any]]:
        """Get suitability scores for a model across all use cases."""
        pass


class RankingRepositoryProtocol(BaseRepositoryProtocol):
    """Protocol for ranking repository operations."""
    
    @abstractmethod
    async def get_rankings_by_use_case(
        self, 
        use_case: str,
        limit: int = 10
    ) -> List[T]:
        """Get model rankings for a specific use case."""
        pass
    
    @abstractmethod
    async def get_top_ranked_models(
        self,
        use_case: str,
        criteria_weights: Optional[Dict[str, float]] = None,
        limit: int = 10
    ) -> List[T]:
        """Get top-ranked models for use case with custom weights."""
        pass
    
    @abstractmethod
    async def invalidate_rankings(self, use_case: Optional[str] = None) -> int:
        """Invalidate cached rankings."""
        pass
