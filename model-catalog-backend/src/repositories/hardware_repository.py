"""Hardware configuration repository implementation."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import HardwareConfig
from .base_repository import BaseRepository
from .protocols import HardwareRepositoryProtocol


class HardwareRepository(BaseRepository[HardwareConfig]):
    """Repository for HardwareConfig entity operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize hardware repository.
        
        Args:
            db: Async database session
        """
        super().__init__(db, HardwareConfig)
    
    async def get_by_gpu_type(self, gpu_type: str) -> List[HardwareConfig]:
        """Get hardware configs by GPU type.
        
        Args:
            gpu_type: GPU type (A100-80GB, H100, L4, etc.)
            
        Returns:
            List of hardware configurations with specified GPU type
        """
        stmt = (
            select(HardwareConfig)
            .where(HardwareConfig.gpu_type == gpu_type)
            .order_by(HardwareConfig.gpu_count, HardwareConfig.cost_per_hour_usd)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_vram_requirement(
        self, 
        min_vram_gb: int,
        prefer_spot: bool = True
    ) -> List[HardwareConfig]:
        """Get hardware configs meeting VRAM requirement.
        
        Args:
            min_vram_gb: Minimum required VRAM in GB
            prefer_spot: Prefer spot instances when available
            
        Returns:
            List of hardware configurations meeting VRAM requirement
        """
        stmt = select(HardwareConfig).where(
            HardwareConfig.total_vram_gb >= min_vram_gb
        )
        
        # Order by: spot first (if preferred), then by cost, then by VRAM
        if prefer_spot:
            stmt = stmt.order_by(
                desc(HardwareConfig.spot_available),
                asc(HardwareConfig.cost_per_hour_usd),
                asc(HardwareConfig.total_vram_gb)
            )
        else:
            stmt = stmt.order_by(
                asc(HardwareConfig.cost_per_hour_usd),
                asc(HardwareConfig.total_vram_gb)
            )
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_cost_optimized(
        self,
        min_vram_gb: int,
        max_cost_per_hour: Optional[float] = None,
        cloud_provider: Optional[str] = None
    ) -> List[HardwareConfig]:
        """Get cost-optimized hardware configurations.
        
        Args:
            min_vram_gb: Minimum required VRAM in GB
            max_cost_per_hour: Maximum cost per hour in USD
            cloud_provider: Filter by cloud provider (aws, gcp, azure)
            
        Returns:
            List of cost-optimized hardware configurations
        """
        conditions = [HardwareConfig.total_vram_gb >= min_vram_gb]
        
        if max_cost_per_hour is not None:
            conditions.append(HardwareConfig.cost_per_hour_usd <= max_cost_per_hour)
        
        if cloud_provider:
            conditions.append(HardwareConfig.cloud_provider == cloud_provider)
        
        stmt = (
            select(HardwareConfig)
            .where(and_(*conditions))
            .order_by(
                desc(HardwareConfig.spot_available),  # Spot instances first (60-90% savings)
                asc(HardwareConfig.cost_per_hour_usd),  # Then by cost
                asc(HardwareConfig.total_vram_gb)  # Then by VRAM (smallest sufficient)
            )
        )
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_cloud_provider(
        self,
        cloud_provider: str,
        spot_only: bool = False
    ) -> List[HardwareConfig]:
        """Get hardware configs by cloud provider.
        
        Args:
            cloud_provider: Cloud provider (aws, gcp, azure)
            spot_only: Only return spot instance configurations
            
        Returns:
            List of hardware configurations for the provider
        """
        conditions = [HardwareConfig.cloud_provider == cloud_provider]
        
        if spot_only:
            conditions.append(HardwareConfig.spot_available == True)
        
        stmt = (
            select(HardwareConfig)
            .where(and_(*conditions))
            .order_by(HardwareConfig.cost_per_hour_usd)
        )
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_spot_available_configs(self) -> List[HardwareConfig]:
        """Get all hardware configs with spot instance availability.
        
        Returns:
            List of hardware configurations available as spot instances
        """
        stmt = (
            select(HardwareConfig)
            .where(HardwareConfig.spot_available == True)
            .order_by(
                HardwareConfig.cost_per_hour_usd,
                desc(HardwareConfig.total_vram_gb)
            )
        )
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def find_best_match_for_model(
        self,
        required_vram_gb: float,
        workload_type: str = "balanced",
        budget_per_hour: Optional[float] = None
    ) -> Optional[HardwareConfig]:
        """Find best hardware match for a model's requirements.
        
        Args:
            required_vram_gb: Required VRAM in GB
            workload_type: Workload type (balanced, throughput, latency)
            budget_per_hour: Optional budget constraint per hour
            
        Returns:
            Best matching hardware configuration, or None
        """
        conditions = [HardwareConfig.total_vram_gb >= required_vram_gb]
        
        if budget_per_hour:
            conditions.append(HardwareConfig.cost_per_hour_usd <= budget_per_hour)
        
        stmt = select(HardwareConfig).where(and_(*conditions))
        
        # Optimize based on workload type
        if workload_type == "throughput":
            # Prefer more GPUs for higher throughput
            stmt = stmt.order_by(
                desc(HardwareConfig.gpu_count),
                desc(HardwareConfig.spot_available)
            )
        elif workload_type == "latency":
            # Prefer powerful single GPUs for low latency
            stmt = stmt.order_by(
                desc(HardwareConfig.vram_per_gpu_gb),
                asc(HardwareConfig.gpu_count)
            )
        else:  # balanced
            # Optimize for cost-performance
            stmt = stmt.order_by(
                desc(HardwareConfig.spot_available),
                asc(HardwareConfig.cost_per_hour_usd)
            )
        
        stmt = stmt.limit(1)
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

