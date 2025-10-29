"""Benchmark configuration matrix model."""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import BaseModel


class BenchmarkConfig(BaseModel):
    """
    Benchmark test configuration matrix.
    
    Represents a single test configuration (model × hardware × framework × workload).
    Populated when model is added, consumed by Argo workflows.
    
    Status Flow:
        pending → running → completed/failed
    
    Spot Instance Recovery:
        Configs stuck in 'running' > 2 hours auto-reset to 'pending'
    """
    
    __tablename__ = "benchmark_configs"
    
    # Foreign keys - the test matrix dimensions
    model_version_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("model_versions.id"), 
        nullable=False, 
        index=True
    )
    hardware_config_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("hardware_configs.id"), 
        nullable=False, 
        index=True
    )
    framework_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("inference_frameworks.id"), 
        nullable=False, 
        index=True
    )
    
    # Test parameters
    workload_type = Column(String(100), nullable=False, index=True)
    # Values: chatbot, summarization, qa, code-generation, creative-writing
    
    batch_size = Column(Integer, nullable=False)
    # Inference batch size: 1, 2, 4, 8
    
    sequence_length = Column(Integer, nullable=False)
    # Context length: 1024, 2048, 4096, 8192
    
    # Status tracking for workflow orchestration
    status = Column(String(20), nullable=False, default='pending', index=True)
    # Status values: pending, running, completed, failed
    
    priority = Column(Integer, nullable=False, default=100)
    # Lower number = higher priority
    # chatbot + batch_size=1 gets priority 100 (highest)
    # Other workloads get priority 200-1000
    
    # Timestamps for tracking
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Error tracking
    error_message = Column(String(1000), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    
    # Relationships
    model_version = relationship("ModelVersion", back_populates="benchmark_configs")
    hardware_config = relationship("HardwareConfig", back_populates="benchmark_configs")
    framework = relationship("InferenceFramework", back_populates="benchmark_configs")
    benchmark_result = relationship(
        "BenchmarkResult", 
        uselist=False,  # One-to-one relationship
        back_populates="benchmark_config"
    )
    
    # Indexes for performance
    __table_args__ = (
        # Workflow queries: get pending configs ordered by priority
        Index(
            'idx_benchmark_config_status_priority', 
            'status', 'priority', 'created_at',
            postgresql_where=Column('status').in_(['pending', 'running'])
        ),
        
        # Uniqueness: prevent duplicate configs
        Index(
            'idx_benchmark_config_unique', 
            'model_version_id', 
            'hardware_config_id', 
            'framework_id',
            'workload_type', 
            'batch_size', 
            'sequence_length',
            unique=True
        ),
        
        # Progress tracking: count by model and status
        Index('idx_benchmark_config_model_status', 'model_version_id', 'status'),
        
        # Spot recovery: find stale running configs
        Index(
            'idx_benchmark_config_stale_running',
            'status', 'started_at',
            postgresql_where=Column('status') == 'running'
        ),
    )
    
    def __repr__(self) -> str:
        return (
            f"<BenchmarkConfig("
            f"model_version={self.model_version_id}, "
            f"status={self.status}, "
            f"workload={self.workload_type}, "
            f"priority={self.priority}"
            f")>"
        )
    
    @property
    def is_completed(self) -> bool:
        """Check if config has been completed (success or failure)."""
        return self.status in ('completed', 'failed')
    
    @property
    def is_pending(self) -> bool:
        """Check if config is pending execution."""
        return self.status == 'pending'
    
    @property
    def is_running(self) -> bool:
        """Check if config is currently running."""
        return self.status == 'running'




