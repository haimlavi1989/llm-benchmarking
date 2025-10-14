"""Benchmark repository implementation with aggregation support."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import BenchmarkResult, ModelVersion, HardwareConfig, InferenceFramework
from .base_repository import BaseRepository
from .protocols import BenchmarkRepositoryProtocol


class BenchmarkRepository(BaseRepository[BenchmarkResult]):
    """Repository for BenchmarkResult entity operations with aggregations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize benchmark repository.
        
        Args:
            db: Async database session
        """
        super().__init__(db, BenchmarkResult)
    
    async def get_by_model_version(self, model_version_id: UUID) -> List[BenchmarkResult]:
        """Get all benchmarks for a specific model version.
        
        Args:
            model_version_id: Model version UUID
            
        Returns:
            List of benchmark results
        """
        stmt = (
            select(BenchmarkResult)
            .where(BenchmarkResult.model_version_id == model_version_id)
            .options(
                joinedload(BenchmarkResult.hardware_config),
                joinedload(BenchmarkResult.framework)
            )
            .order_by(desc(BenchmarkResult.benchmark_date))
        )
        result = await self.db.execute(stmt)
        return list(result.unique().scalars().all())
    
    async def get_by_criteria(
        self,
        model_version_id: Optional[UUID] = None,
        hardware_config_id: Optional[UUID] = None,
        framework_id: Optional[UUID] = None,
        workload_type: Optional[str] = None,
        max_ttft_p90: Optional[float] = None,
        min_throughput: Optional[float] = None
    ) -> List[BenchmarkResult]:
        """Get benchmarks filtered by multiple criteria.
        
        Args:
            model_version_id: Filter by model version
            hardware_config_id: Filter by hardware configuration
            framework_id: Filter by inference framework
            workload_type: Filter by workload type (chatbot, summarization, etc.)
            max_ttft_p90: Maximum acceptable TTFT P90 latency (ms)
            min_throughput: Minimum acceptable throughput (tokens/sec)
            
        Returns:
            List of matching benchmark results
        """
        stmt = select(BenchmarkResult)
        
        conditions = []
        
        if model_version_id:
            conditions.append(BenchmarkResult.model_version_id == model_version_id)
        
        if hardware_config_id:
            conditions.append(BenchmarkResult.hardware_config_id == hardware_config_id)
        
        if framework_id:
            conditions.append(BenchmarkResult.framework_id == framework_id)
        
        if workload_type:
            conditions.append(BenchmarkResult.workload_type == workload_type)
        
        if max_ttft_p90 is not None:
            conditions.append(BenchmarkResult.ttft_p90_ms <= max_ttft_p90)
        
        if min_throughput is not None:
            conditions.append(BenchmarkResult.throughput_tokens_sec >= min_throughput)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        stmt = stmt.order_by(
            desc(BenchmarkResult.throughput_tokens_sec),
            BenchmarkResult.ttft_p90_ms
        )
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_aggregated_stats(
        self,
        model_version_id: UUID,
        workload_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get aggregated benchmark statistics for a model version.
        
        Args:
            model_version_id: Model version UUID
            workload_type: Optional workload type filter
            
        Returns:
            Dictionary with aggregated metrics (avg, min, max, percentiles)
        """
        stmt = select(
            func.count(BenchmarkResult.id).label('total_benchmarks'),
            func.avg(BenchmarkResult.ttft_p50_ms).label('avg_ttft_p50'),
            func.avg(BenchmarkResult.ttft_p90_ms).label('avg_ttft_p90'),
            func.avg(BenchmarkResult.tpot_p50_ms).label('avg_tpot_p50'),
            func.avg(BenchmarkResult.tpot_p90_ms).label('avg_tpot_p90'),
            func.avg(BenchmarkResult.throughput_tokens_sec).label('avg_throughput'),
            func.max(BenchmarkResult.throughput_tokens_sec).label('max_throughput'),
            func.avg(BenchmarkResult.accuracy_score).label('avg_accuracy'),
            func.avg(BenchmarkResult.gpu_utilization_pct).label('avg_gpu_util'),
            func.avg(BenchmarkResult.memory_used_gb).label('avg_memory_used')
        ).where(BenchmarkResult.model_version_id == model_version_id)
        
        if workload_type:
            stmt = stmt.where(BenchmarkResult.workload_type == workload_type)
        
        result = await self.db.execute(stmt)
        row = result.first()
        
        if not row or row.total_benchmarks == 0:
            return {
                'total_benchmarks': 0,
                'avg_ttft_p50_ms': None,
                'avg_ttft_p90_ms': None,
                'avg_tpot_p50_ms': None,
                'avg_tpot_p90_ms': None,
                'avg_throughput': None,
                'max_throughput': None,
                'avg_accuracy': None,
                'avg_gpu_utilization_pct': None,
                'avg_memory_used_gb': None
            }
        
        return {
            'total_benchmarks': row.total_benchmarks,
            'avg_ttft_p50_ms': float(row.avg_ttft_p50) if row.avg_ttft_p50 else None,
            'avg_ttft_p90_ms': float(row.avg_ttft_p90) if row.avg_ttft_p90 else None,
            'avg_tpot_p50_ms': float(row.avg_tpot_p50) if row.avg_tpot_p50 else None,
            'avg_tpot_p90_ms': float(row.avg_tpot_p90) if row.avg_tpot_p90 else None,
            'avg_throughput': float(row.avg_throughput) if row.avg_throughput else None,
            'max_throughput': float(row.max_throughput) if row.max_throughput else None,
            'avg_accuracy': float(row.avg_accuracy) if row.avg_accuracy else None,
            'avg_gpu_utilization_pct': float(row.avg_gpu_util) if row.avg_gpu_util else None,
            'avg_memory_used_gb': float(row.avg_memory_used) if row.avg_memory_used else None
        }
    
    async def get_latest_benchmarks(
        self,
        model_version_id: UUID,
        limit: int = 10
    ) -> List[BenchmarkResult]:
        """Get latest benchmarks for a model version.
        
        Args:
            model_version_id: Model version UUID
            limit: Maximum number of results
            
        Returns:
            List of latest benchmark results
        """
        stmt = (
            select(BenchmarkResult)
            .where(BenchmarkResult.model_version_id == model_version_id)
            .order_by(desc(BenchmarkResult.benchmark_date))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_best_performing_configs(
        self,
        model_version_id: UUID,
        metric: str = 'throughput',
        limit: int = 5
    ) -> List[BenchmarkResult]:
        """Get best performing hardware/framework configurations.
        
        Args:
            model_version_id: Model version UUID
            metric: Metric to optimize ('throughput', 'latency', 'cost')
            limit: Maximum number of results
            
        Returns:
            List of best performing benchmark configurations
        """
        stmt = select(BenchmarkResult).where(
            BenchmarkResult.model_version_id == model_version_id
        )
        
        if metric == 'throughput':
            stmt = stmt.order_by(desc(BenchmarkResult.throughput_tokens_sec))
        elif metric == 'latency':
            stmt = stmt.order_by(BenchmarkResult.ttft_p90_ms)
        elif metric == 'accuracy':
            stmt = stmt.order_by(desc(BenchmarkResult.accuracy_score))
        
        stmt = stmt.limit(limit)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_benchmarks_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        model_version_id: Optional[UUID] = None
    ) -> List[BenchmarkResult]:
        """Get benchmarks within a date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            model_version_id: Optional model version filter
            
        Returns:
            List of benchmark results in date range
        """
        stmt = select(BenchmarkResult).where(
            and_(
                BenchmarkResult.benchmark_date >= start_date.date(),
                BenchmarkResult.benchmark_date <= end_date.date()
            )
        )
        
        if model_version_id:
            stmt = stmt.where(BenchmarkResult.model_version_id == model_version_id)
        
        stmt = stmt.order_by(desc(BenchmarkResult.benchmark_date))
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

