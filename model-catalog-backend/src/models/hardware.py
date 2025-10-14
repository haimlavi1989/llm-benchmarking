"""Hardware configuration and use case taxonomy models."""

from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from .base import BaseModel


class HardwareConfig(BaseModel):
    """Hardware configuration specifications for GPU instances."""
    
    __tablename__ = "hardware_configs"
    
    # GPU information
    gpu_type = Column(String(50), nullable=False, index=True)  # A100-80GB, H100, L4
    gpu_count = Column(Integer, nullable=False)  # 1, 2, 4, 8
    vram_per_gpu_gb = Column(Integer, nullable=False)  # 24, 40, 80
    total_vram_gb = Column(Integer, nullable=False)  # Calculated: gpu_count × vram_per_gpu_gb
    
    # Cost and availability
    cost_per_hour_usd = Column(Float, nullable=False)
    cloud_provider = Column(String(50), nullable=False, index=True)  # aws, gcp, azure
    instance_type = Column(String(100), nullable=True)  # p4d.24xlarge, g5.12xlarge, etc.
    spot_available = Column(Boolean, nullable=False, default=False)
    
    # Detailed specifications
    specs = Column(JSONB, nullable=True)  # Additional hardware details
    
    # Relationships
    benchmarks = relationship("BenchmarkResult", back_populates="hardware_config")
    
    __table_args__ = (
        Index('idx_hardware_vram_cost', 'total_vram_gb', 'cost_per_hour_usd', 'spot_available'),
        Index('idx_hardware_provider_gpu', 'cloud_provider', 'gpu_type', 'gpu_count'),
    )
    
    def __repr__(self) -> str:
        return (f"<HardwareConfig(gpu_type={self.gpu_type}, count={self.gpu_count}, "
                f"vram={self.total_vram_gb}GB, provider={self.cloud_provider})>")


class InferenceFramework(BaseModel):
    """Inference framework specifications (vLLM, TGI, LMDeploy)."""
    
    __tablename__ = "inference_frameworks"
    
    # Framework information
    name = Column(String(50), nullable=False, unique=True, index=True)  # vLLM, TGI, LMDeploy
    version = Column(String(20), nullable=False)  # v0.5.0, v0.4.3, etc.
    
    # Capabilities
    capabilities = Column(JSONB, nullable=True)  # Features supported
    supports_quantization = Column(Boolean, nullable=False, default=True)
    supports_streaming = Column(Boolean, nullable=False, default=True)
    config_template = Column(JSONB, nullable=True)  # Default configuration
    
    # Relationships
    benchmarks = relationship("BenchmarkResult", back_populates="framework")
    
    def __repr__(self) -> str:
        return f"<InferenceFramework(name={self.name}, version={self.version})>"


class UseCaseTaxonomy(BaseModel):
    """Standardized use case categorization and characteristics."""
    
    __tablename__ = "use_case_taxonomy"
    
    # Categorization
    category = Column(String(100), nullable=False, index=True)  # text-generation, qa, etc.
    subcategory = Column(String(100), nullable=True)  # chatbot, creative-writing, etc.
    pipeline_tag = Column(String(100), nullable=True, index=True)  # HuggingFace pipeline tag
    
    # Use case characteristics
    characteristics = Column(JSONB, nullable=True)  # Typical requirements
    default_weights = Column(JSONB, nullable=True)  # Default TOPSIS weights
    
    # Relationships
    model_use_cases = relationship("ModelUseCase", back_populates="use_case")
    
    __table_args__ = (
        Index('idx_taxonomy_category_subcategory', 'category', 'subcategory'),
    )
    
    def __repr__(self) -> str:
        return f"<UseCaseTaxonomy(category={self.category}, subcategory={self.subcategory})>"


class ModelUseCase(BaseModel):
    """Pre-computed model-to-use-case suitability mappings."""
    
    __tablename__ = "model_use_cases"
    
    # Foreign keys
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id"), nullable=False, index=True)
    use_case_id = Column(UUID(as_uuid=True), ForeignKey("use_case_taxonomy.id"), nullable=False, index=True)
    
    # Suitability metrics
    suitability_score = Column(Float, nullable=False)  # 0.0 to 1.0
    recommended = Column(Boolean, nullable=False, default=False, index=True)
    priority = Column(Integer, nullable=True)  # Ranking order
    
    # Performance summary
    performance_summary = Column(JSONB, nullable=True)  # Quick stats for this combination
    
    # Relationships
    model = relationship("Model", back_populates="use_cases")
    use_case = relationship("UseCaseTaxonomy", back_populates="model_use_cases")
    
    __table_args__ = (
        Index('idx_model_use_case_suitability', 'model_id', 'use_case_id', 'suitability_score'),
        Index('idx_recommended_models', 'model_id', 'recommended', postgresql_where='recommended = true'),
    )
    
    def __repr__(self) -> str:
        return (f"<ModelUseCase(model_id={self.model_id}, use_case_id={self.use_case_id}, "
                f"suitability={self.suitability_score:.2f})>")

