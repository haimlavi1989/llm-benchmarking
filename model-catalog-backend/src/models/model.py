"""Model definitions for AI models and versions."""

from typing import List
from sqlalchemy import Column, String, BigInteger, Text, ARRAY, ForeignKey, Float
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class Model(BaseModel):
    """AI model definition."""
    
    __tablename__ = "models"
    
    # Basic information
    name = Column(String(255), unique=True, nullable=False, index=True)
    architecture = Column(String(100), nullable=False, index=True)  # e.g., llama, gpt, mistral
    parameters = Column(BigInteger, nullable=False)  # e.g., 7B, 13B, 70B
    base_model = Column(String(255), nullable=True)  # Parent model if fine-tuned
    
    # Metadata and tags
    metadata = Column(JSONB, nullable=True)  # Flexible model info
    tags = Column(ARRAY(Text), nullable=True)  # Searchable tags
    
    # Relationships
    versions = relationship("ModelVersion", back_populates="model", cascade="all, delete-orphan")
    use_cases = relationship("ModelUseCase", back_populates="model", cascade="all, delete-orphan")
    benchmarks = relationship("BenchmarkResult", back_populates="model_version", cascade="all, delete-orphan")
    daily_stats = relationship("DailyModelStats", back_populates="model", cascade="all, delete-orphan")
    rankings = relationship("ModelRanking", back_populates="model", cascade="all, delete-orphan")
    
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
    quantization_bits = Column(String(10), nullable=False)  # 4, 8, 16, 32
    format = Column(String(50), nullable=False)  # gguf, gptq, awq, safetensors
    
    # Storage and configuration
    artifact_uri = Column(String(500), nullable=True)  # Storage location
    model_config = Column(JSONB, nullable=True)  # Technical specs
    
    # VRAM requirements (calculated)
    vram_requirement_gb = Column(Float, nullable=False)
    
    # Relationships
    model = relationship("Model", back_populates="versions")
    benchmarks = relationship("BenchmarkResult", back_populates="model_version", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<ModelVersion(model={self.model.name if self.model else 'Unknown'}, version={self.version}, quantization={self.quantization})>"


class HardwareConfig(BaseModel):
    """Hardware configuration specifications."""
    
    __tablename__ = "hardware_configs"
    
    # GPU information
    gpu_type = Column(String(50), nullable=False, index=True)  # A100-80GB, H100, L4
    gpu_count = Column(String(10), nullable=False)  # 1, 2, 4, 8
    vram_per_gpu_gb = Column(String(10), nullable=False)  # 24, 40, 80
    total_vram_gb = Column(String(10), nullable=False)  # calculated
    
    # Cost and availability
    cost_per_hour_usd = Column(Float, nullable=False)
    cloud_provider = Column(String(50), nullable=False)  # aws, gcp, azure
    instance_type = Column(String(100), nullable=True)  # p4d.24xlarge, etc
    spot_available = Column(String(10), nullable=False, default="false")
    
    # Detailed specifications
    specs = Column(JSONB, nullable=True)  # detailed hardware info
    
    # Relationships
    benchmarks = relationship("BenchmarkResult", back_populates="hardware_config", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<HardwareConfig(gpu_type={self.gpu_type}, count={self.gpu_count}, vram={self.total_vram_gb}GB)>"


class InferenceFramework(BaseModel):
    """Inference framework specifications."""
    
    __tablename__ = "inference_frameworks"
    
    # Framework information
    name = Column(String(50), nullable=False, unique=True, index=True)  # vLLM, TGI, LMDeploy
    version = Column(String(20), nullable=False)  # v0.5.0
    
    # Capabilities
    capabilities = Column(JSONB, nullable=True)  # features supported
    supports_quantization = Column(String(10), nullable=False, default="true")
    supports_streaming = Column(String(10), nullable=False, default="true")
    config_template = Column(JSONB, nullable=True)  # default config
    
    # Relationships
    benchmarks = relationship("BenchmarkResult", back_populates="framework", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<InferenceFramework(name={self.name}, version={self.version})>"
