"""Base repository implementation with common functionality."""

from typing import List, Optional, Dict, Any, TypeVar, Generic
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from sqlalchemy.ext.declarative import DeclarativeMeta

from .protocols import BaseRepositoryProtocol

T = TypeVar('T', bound=DeclarativeMeta)


class BaseRepository(BaseRepositoryProtocol[T], Generic[T]):
    """Base repository implementation with common CRUD operations."""
    
    def __init__(self, db: Session, model_class: type[T]):
        """
        Initialize base repository.
        
        Args:
            db: Database session
            model_class: SQLAlchemy model class
        """
        self.db = db
        self.model_class = model_class
    
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity
    
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """Get entity by ID."""
        stmt = select(self.model_class).where(self.model_class.id == entity_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination."""
        stmt = select(self.model_class).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        await self.db.commit()
        await self.db.refresh(entity)
        return entity
    
    async def delete(self, entity_id: UUID) -> bool:
        """Delete an entity by ID."""
        stmt = delete(self.model_class).where(self.model_class.id == entity_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0
    
    async def count(self) -> int:
        """Get total count of entities."""
        stmt = select(self.model_class).count()
        result = await self.db.execute(stmt)
        return result.scalar()
    
    async def exists(self, entity_id: UUID) -> bool:
        """Check if entity exists by ID."""
        entity = await self.get_by_id(entity_id)
        return entity is not None
    
    async def bulk_create(self, entities: List[T]) -> List[T]:
        """Create multiple entities in bulk."""
        self.db.add_all(entities)
        await self.db.commit()
        for entity in entities:
            await self.db.refresh(entity)
        return entities
    
    async def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """Bulk update entities."""
        updated_count = 0
        for update_data in updates:
            entity_id = update_data.pop('id')
            stmt = update(self.model_class).where(
                self.model_class.id == entity_id
            ).values(**update_data)
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
        """Find entities by criteria."""
        stmt = select(self.model_class)
        
        for field, value in criteria.items():
            if hasattr(self.model_class, field):
                stmt = stmt.where(getattr(self.model_class, field) == value)
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def find_one_by_criteria(self, criteria: Dict[str, Any]) -> Optional[T]:
        """Find single entity by criteria."""
        entities = await self.find_by_criteria(criteria, limit=1)
        return entities[0] if entities else None
