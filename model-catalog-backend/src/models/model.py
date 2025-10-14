"""Model definitions for AI models and versions."""

from sqlalchemy import Column, String, BigInteger, ARRAY, Text, ForeignKey, Float, Integer, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class Model(BaseModel):
    """AI model definition."""
    
    __tablename__ = "models"
    
    # Basic information
    name = Column(String(255), unique=True, nullable=False, index=True)
    architecture = Column(String(100), nullable=False, index=True)  # e.g., llama, gpt, mistral
    parameters = Column(BigInteger, nullable=False)  # e.g., 7B, 13B, 70B (in billions)
    base_model = Column(String(255), nullable=True)  # Parent model if fine-tuned
    
    # Metadata and tags
    metadata = Column(JSONB, nullable=True)  # Flexible model info
    tags = Column(ARRAY(Text), nullable=True)  # Searchable tags
    
    # Relationships
    versions = relationship("ModelVersion", back_populates="model", cascade="all, delete-orphan")
    use_cases = relationship("ModelUseCase", back_populates="model", cascade="all, delete-orphan")
    daily_stats = relationship("DailyModelStats", back_populates="model", cascade="all, delete-orphan")
    rankings = relationship("ModelRanking", back_populates="model", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_model_architecture_params', 'architecture', 'parameters'),
    )
    
    def __repr__(self) -> str:
        return f"<Model(name={self.name}, architecture={self.architecture}, parameters={self.parameters}B)>"


class ModelVersion(BaseModel):
    """Specific version of a model with quantization and format details."""
    
    __tablename__ = "model_versions"
    
    # Foreign keys
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id"), nullable=False, index=True)
    
    # Version information
    version = Column(String(50), nullable=False)  # e.g., v1.0, v2.1
    quantization = Column(String(20), nullable=False, index=True)  # fp32, fp16, int8, int4
    quantization_bits = Column(Integer, nullable=False)  # 4, 8, 16, 32
    format = Column(String(50), nullable=False)  # gguf, gptq, awq, safetensors
    
    # Storage and configuration
    artifact_uri = Column(String(500), nullable=True)  # Storage location (S3, HuggingFace Hub)
    model_config = Column(JSONB, nullable=True)  # Technical specs
    
    # VRAM requirements (calculated: params × bits/8 × 1.2)
    vram_requirement_gb = Column(Float, nullable=False)
    
    # Relationships
    model = relationship("Model", back_populates="versions")
    benchmarks = relationship("BenchmarkResult", back_populates="model_version", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_model_version_vram_quant', 'vram_requirement_gb', 'quantization_bits', 'format'),
        Index('idx_model_version_model_quant', 'model_id', 'quantization'),
    )
    
    def __repr__(self) -> str:
        model_name = self.model.name if hasattr(self, 'model') and self.model else 'Unknown'
        return f"<ModelVersion(model={model_name}, version={self.version}, quantization={self.quantization})>"
