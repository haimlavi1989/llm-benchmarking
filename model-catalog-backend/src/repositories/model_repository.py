"""Model repository implementation."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Model, ModelVersion, ModelUseCase
from .base_repository import BaseRepository
from .protocols import ModelRepositoryProtocol


class ModelRepository(BaseRepository[Model]):
    """Repository for Model entity operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize model repository.
        
        Args:
            db: Async database session
        """
        super().__init__(db, Model)
    
    async def get_by_name(self, name: str) -> Optional[Model]:
        """Get model by name.
        
        Args:
            name: Model name to search for
            
        Returns:
            Model if found, None otherwise
        """
        stmt = select(Model).where(Model.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def search_by_use_case(self, use_case: str) -> List[Model]:
        """Get models suitable for a specific use case.
        
        Args:
            use_case: Use case category or subcategory
            
        Returns:
            List of models suitable for the use case
        """
        stmt = (
            select(Model)
            .join(ModelUseCase)
            .where(
                and_(
                    ModelUseCase.recommended == True,
                    or_(
                        ModelUseCase.use_case.has(category=use_case),
                        ModelUseCase.use_case.has(subcategory=use_case)
                    )
                )
            )
            .order_by(ModelUseCase.suitability_score.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_with_benchmarks(self, model_id: UUID) -> Optional[Model]:
        """Get model with all benchmark results eagerly loaded.
        
        Args:
            model_id: Model UUID
            
        Returns:
            Model with relationships loaded, or None
        """
        stmt = (
            select(Model)
            .where(Model.id == model_id)
            .options(
                joinedload(Model.versions).joinedload(ModelVersion.benchmarks),
                joinedload(Model.use_cases),
                joinedload(Model.rankings)
            )
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()
    
    async def search_models(
        self, 
        query: str,
        architecture: Optional[str] = None,
        min_parameters: Optional[int] = None,
        max_parameters: Optional[int] = None
    ) -> List[Model]:
        """Search models with filters.
        
        Args:
            query: Search query (matches name or tags)
            architecture: Filter by architecture (llama, gpt, mistral, etc.)
            min_parameters: Minimum parameter count (in billions)
            max_parameters: Maximum parameter count (in billions)
            
        Returns:
            List of matching models
        """
        stmt = select(Model)
        
        # Text search in name or tags
        if query:
            stmt = stmt.where(
                or_(
                    Model.name.ilike(f"%{query}%"),
                    Model.tags.any(query)
                )
            )
        
        # Architecture filter
        if architecture:
            stmt = stmt.where(Model.architecture == architecture)
        
        # Parameter range filters
        if min_parameters is not None:
            stmt = stmt.where(Model.parameters >= min_parameters)
        
        if max_parameters is not None:
            stmt = stmt.where(Model.parameters <= max_parameters)
        
        # Order by relevance (parameters desc)
        stmt = stmt.order_by(Model.parameters.desc())
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_architecture(self, architecture: str, limit: int = 100) -> List[Model]:
        """Get models by architecture type.
        
        Args:
            architecture: Architecture name (llama, gpt, mistral, etc.)
            limit: Maximum number of results
            
        Returns:
            List of models with the specified architecture
        """
        stmt = (
            select(Model)
            .where(Model.architecture == architecture)
            .order_by(Model.parameters.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_popular_models(self, limit: int = 10) -> List[Model]:
        """Get most popular models based on benchmark count.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of popular models
        """
        stmt = (
            select(Model)
            .join(Model.versions)
            .join(ModelVersion.benchmarks)
            .group_by(Model.id)
            .order_by(Model.daily_stats.count().desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.unique().scalars().all())

