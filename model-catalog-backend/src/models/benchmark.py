"""Benchmark results and performance metrics models."""

from datetime import date
from sqlalchemy import Column, String, Integer, Float, Date, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from .base import BaseModel


class BenchmarkResult(BaseModel):
    """Benchmark performance results for model-hardware-framework combinations."""
    
    __tablename__ = "benchmark_results"
    
    # Foreign keys
    model_version_id = Column(UUID(as_uuid=True), ForeignKey("model_versions.id"), nullable=False, index=True)
    hardware_config_id = Column(UUID(as_uuid=True), ForeignKey("hardware_configs.id"), nullable=False, index=True)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("inference_frameworks.id"), nullable=False, index=True)
    
    # Link to configuration that generated this result (nullable for backward compatibility)
    config_id = Column(UUID(as_uuid=True), ForeignKey("benchmark_configs.id"), nullable=True, index=True)
    
    # Benchmark metadata
    benchmark_date = Column(Date, nullable=False, index=True)  # For TimescaleDB partitioning
    workload_type = Column(String(100), nullable=False, index=True)  # chatbot, summarization, etc.
    batch_size = Column(Integer, nullable=False)
    sequence_length = Column(Integer, nullable=False)
    
    # Latency metrics - Time to First Token (TTFT)
    ttft_p50_ms = Column(Float, nullable=False)
    ttft_p90_ms = Column(Float, nullable=False, index=True)  # SLA queries
    ttft_p99_ms = Column(Float, nullable=False)
    
    # Latency metrics - Time per Output Token (TPOT)
    tpot_p50_ms = Column(Float, nullable=False)
    tpot_p90_ms = Column(Float, nullable=False)
    tpot_p99_ms = Column(Float, nullable=False)
    
    # Throughput metrics
    throughput_tokens_sec = Column(Float, nullable=False, index=True)
    rps_sustained = Column(Float, nullable=False)  # Requests per second
    
    # Quality metrics
    accuracy_score = Column(Float, nullable=True)  # Task-specific accuracy
    
    # Resource utilization
    gpu_utilization_pct = Column(Float, nullable=False)
    memory_used_gb = Column(Float, nullable=False)
    
    # Detailed metrics storage
    detailed_metrics = Column(JSONB, nullable=True)  # Raw benchmark data
    
    # Relationships
    model_version = relationship("ModelVersion", back_populates="benchmarks")
    hardware_config = relationship("HardwareConfig", back_populates="benchmarks")
    framework = relationship("InferenceFramework", back_populates="benchmarks")
    benchmark_config = relationship("BenchmarkConfig", back_populates="benchmark_result")
    
    # Composite indexes for performance
    __table_args__ = (
        Index('idx_benchmark_composite', 'model_version_id', 'hardware_config_id', 'framework_id', 'benchmark_date', 'config_id'),
        Index('idx_benchmark_latency_sla', 'ttft_p90_ms', 'throughput_tokens_sec'),
        Index('idx_benchmark_date_workload', 'benchmark_date', 'workload_type'),
    )
    
    def __repr__(self) -> str:
        return (f"<BenchmarkResult(model_version_id={self.model_version_id}, "
                f"hardware={self.hardware_config_id}, framework={self.framework_id}, "
                f"ttft_p90={self.ttft_p90_ms}ms)>")


class DailyModelStats(BaseModel):
    """Aggregated daily statistics for models (Materialized view data)."""
    
    __tablename__ = "daily_model_stats"
    
    # Foreign key
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id"), nullable=False, index=True)
    
    # Date partition
    stats_date = Column(Date, nullable=False, index=True)
    
    # Aggregated metrics
    avg_accuracy = Column(Float, nullable=True)
    avg_throughput = Column(Float, nullable=False)
    p95_latency_ms = Column(Float, nullable=False)
    total_benchmarks = Column(Integer, nullable=False, default=0)
    
    # Detailed aggregations
    aggregated_metrics = Column(JSONB, nullable=True)  # Pre-computed stats
    
    # Relationships
    model = relationship("Model", back_populates="daily_stats")
    
    __table_args__ = (
        Index('idx_daily_stats_model_date', 'model_id', 'stats_date'),
    )
    
    def __repr__(self) -> str:
        return f"<DailyModelStats(model_id={self.model_id}, date={self.stats_date})>"


class ModelRanking(BaseModel):
    """Pre-computed model rankings using TOPSIS/Pareto optimization."""
    
    __tablename__ = "model_rankings"
    
    # Foreign key
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id"), nullable=False, index=True)
    
    # Use case category
    use_case_category = Column(String(100), nullable=False, index=True)
    
    # Ranking results
    composite_score = Column(Float, nullable=False)  # TOPSIS/Pareto score
    rank_position = Column(Integer, nullable=False)  # 1, 2, 3...
    score_breakdown = Column(JSONB, nullable=True)  # Per-criterion scores
    
    # Cache TTL
    calculated_at = Column(Date, nullable=False)
    expires_at = Column(Date, nullable=False, index=True)
    
    # Relationships
    model = relationship("Model", back_populates="rankings")
    
    __table_args__ = (
        Index('idx_rankings_use_case', 'use_case_category', 'composite_score'),
        Index('idx_rankings_active', 'use_case_category', 'rank_position', postgresql_where='expires_at > NOW()'),
    )
    
    def __repr__(self) -> str:
        return (f"<ModelRanking(model_id={self.model_id}, use_case={self.use_case_category}, "
                f"rank={self.rank_position}, score={self.composite_score:.3f})>")

