"""Base repository implementation with common functionality."""

from typing import List, Optional, Dict, Any, TypeVar, Generic, Type
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import DeclarativeBase

from .protocols import BaseRepositoryProtocol

T = TypeVar('T', bound=DeclarativeBase)


class BaseRepository(Generic[T]):
    """Base repository implementation with common CRUD operations."""
    
    def __init__(self, db: AsyncSession, model_class: Type[T]):
        """Initialize base repository.
        
        Args:
            db: Async database session
            model_class: SQLAlchemy model class
        """
        self.db = db
        self.model_class = model_class
    
    async def create(self, entity: T) -> T:
        """Create a new entity.
        
        Args:
            entity: Entity instance to create
            
        Returns:
            Created entity with populated fields
        """
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity
    
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """Get entity by ID.
        
        Args:
            entity_id: Entity UUID
            
        Returns:
            Entity if found, None otherwise
        """
        stmt = select(self.model_class).where(self.model_class.id == entity_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of entities
        """
        stmt = select(self.model_class).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def update(self, entity_id: UUID, entity: T) -> T:
        """Update an existing entity.
        
        Args:
            entity_id: Entity UUID
            entity: Entity with updated values
            
        Returns:
            Updated entity
        """
        await self.db.commit()
        await self.db.refresh(entity)
        return entity
    
    async def delete(self, entity_id: UUID) -> bool:
        """Delete an entity by ID.
        
        Args:
            entity_id: Entity UUID
            
        Returns:
            True if deleted, False if not found
        """
        stmt = delete(self.model_class).where(self.model_class.id == entity_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0
    
    async def count(self) -> int:
        """Get total count of entities.
        
        Returns:
            Total number of entities
        """
        stmt = select(func.count()).select_from(self.model_class)
        result = await self.db.execute(stmt)
        return result.scalar() or 0
    
    async def exists(self, entity_id: UUID) -> bool:
        """Check if entity exists by ID.
        
        Args:
            entity_id: Entity UUID
            
        Returns:
            True if exists, False otherwise
        """
        entity = await self.get_by_id(entity_id)
        return entity is not None
    
    async def bulk_create(self, entities: List[T]) -> List[T]:
        """Create multiple entities in bulk.
        
        Args:
            entities: List of entity instances
            
        Returns:
            List of created entities
        """
        self.db.add_all(entities)
        await self.db.commit()
        for entity in entities:
            await self.db.refresh(entity)
        return entities
    
    async def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """Bulk update entities.
        
        Args:
            updates: List of dictionaries with 'id' and update fields
            
        Returns:
            Number of updated entities
        """
        updated_count = 0
        for update_data in updates:
            entity_id = update_data.pop('id')
            stmt = (
                update(self.model_class)
                .where(self.model_class.id == entity_id)
                .values(**update_data)
            )
            result = await self.db.execute(stmt)
            updated_count += result.rowcount
        
        await self.db.commit()
        return updated_count
    
    async def find_by_criteria(
        self, 
        criteria: Dict[str, Any],
        skip: int = 0,
        limit: int = 100
    ) -> List[T]:
        """Find entities by criteria.
        
        Args:
            criteria: Dictionary of field:value pairs
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching entities
        """
        stmt = select(self.model_class)
        
        for field, value in criteria.items():
            if hasattr(self.model_class, field):
                stmt = stmt.where(getattr(self.model_class, field) == value)
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def find_one_by_criteria(self, criteria: Dict[str, Any]) -> Optional[T]:
        """Find single entity by criteria.
        
        Args:
            criteria: Dictionary of field:value pairs
            
        Returns:
            First matching entity, or None
        """
        entities = await self.find_by_criteria(criteria, limit=1)
        return entities[0] if entities else None
