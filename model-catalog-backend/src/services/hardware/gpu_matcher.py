"""GPU matching utilities for hardware optimization."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from src.core.exceptions import HardwareConfigError


class GPUType(Enum):
    """Supported GPU types."""
    L4 = "L4"
    A100_40GB = "A100-40GB"
    A100_80GB = "A100-80GB"
    H100 = "H100"
    V100 = "V100"


@dataclass
class GPUConfig:
    """GPU configuration specification."""
    gpu_type: GPUType
    count: int
    vram_per_gpu_gb: int
    total_vram_gb: int
    cost_per_hour_usd: float
    spot_available: bool
    cloud_provider: str


@dataclass
class HardwareRequirement:
    """Hardware requirements for a model."""
    min_vram_gb: float
    preferred_gpu_type: Optional[GPUType] = None
    max_cost_per_hour: Optional[float] = None
    prefer_spot_instances: bool = True


class GPUMatcher:
    """Match hardware requirements to available GPU configurations."""
    
    def __init__(self):
        """Initialize GPU matcher with available configurations."""
        self.available_configs = self._initialize_gpu_configs()
    
    def _initialize_gpu_configs(self) -> List[GPUConfig]:
        """Initialize available GPU configurations."""
        return [
            GPUConfig(
                gpu_type=GPUType.L4,
                count=1,
                vram_per_gpu_gb=24,
                total_vram_gb=24,
                cost_per_hour_usd=0.50,
                spot_available=True,
                cloud_provider="aws"
            ),
            GPUConfig(
                gpu_type=GPUType.A100_40GB,
                count=1,
                vram_per_gpu_gb=40,
                total_vram_gb=40,
                cost_per_hour_usd=1.20,
                spot_available=True,
                cloud_provider="aws"
            ),
            GPUConfig(
                gpu_type=GPUType.A100_80GB,
                count=1,
                vram_per_gpu_gb=80,
                total_vram_gb=80,
                cost_per_hour_usd=2.40,
                spot_available=True,
                cloud_provider="aws"
            ),
            GPUConfig(
                gpu_type=GPUType.H100,
                count=1,
                vram_per_gpu_gb=80,
                total_vram_gb=80,
                cost_per_hour_usd=4.00,
                spot_available=True,
                cloud_provider="aws"
            ),
            # Multi-GPU configurations
            GPUConfig(
                gpu_type=GPUType.A100_80GB,
                count=2,
                vram_per_gpu_gb=80,
                total_vram_gb=160,
                cost_per_hour_usd=4.80,
                spot_available=True,
                cloud_provider="aws"
            ),
            GPUConfig(
                gpu_type=GPUType.A100_80GB,
                count=4,
                vram_per_gpu_gb=80,
                total_vram_gb=320,
                cost_per_hour_usd=9.60,
                spot_available=True,
                cloud_provider="aws"
            ),
            GPUConfig(
                gpu_type=GPUType.H100,
                count=4,
                vram_per_gpu_gb=80,
                total_vram_gb=320,
                cost_per_hour_usd=16.00,
                spot_available=True,
                cloud_provider="aws"
            ),
        ]
    
    def find_matching_configs(
        self, 
        requirement: HardwareRequirement
    ) -> List[GPUConfig]:
        """
        Find GPU configurations that match the requirements.
        
        Args:
            requirement: Hardware requirements
            
        Returns:
            List of matching GPU configurations, sorted by cost efficiency
        """
        matching_configs = []
        
        for config in self.available_configs:
            if self._config_matches_requirement(config, requirement):
                matching_configs.append(config)
        
        # Sort by cost efficiency (cost per GB of VRAM)
        matching_configs.sort(key=lambda x: x.cost_per_hour_usd / x.total_vram_gb)
        
        return matching_configs
    
    def _config_matches_requirement(
        self, 
        config: GPUConfig, 
        requirement: HardwareRequirement
    ) -> bool:
        """Check if a GPU configuration matches the requirements."""
        # Check VRAM requirement
        if config.total_vram_gb < requirement.min_vram_gb:
            return False
        
        # Check preferred GPU type
        if (requirement.preferred_gpu_type and 
            config.gpu_type != requirement.preferred_gpu_type):
            return False
        
        # Check cost constraint
        if (requirement.max_cost_per_hour and 
            config.cost_per_hour_usd > requirement.max_cost_per_hour):
            return False
        
        # Check spot instance preference
        if (requirement.prefer_spot_instances and 
            not config.spot_available):
            return False
        
        return True
    
    def get_cost_optimized_config(
        self, 
        requirement: HardwareRequirement
    ) -> Optional[GPUConfig]:
        """Get the most cost-effective configuration that meets requirements."""
        matching_configs = self.find_matching_configs(requirement)
        
        if not matching_configs:
            return None
        
        # Return the most cost-effective option
        return matching_configs[0]
    
    def calculate_cost_savings_with_spot(self, config: GPUConfig) -> Dict[str, float]:
        """Calculate potential cost savings with spot instances."""
        if not config.spot_available:
            return {"savings_percent": 0.0, "savings_per_hour": 0.0}
        
        # Typical spot instance savings (60-90%)
        spot_savings_percent = 0.75  # 75% average savings
        spot_cost_per_hour = config.cost_per_hour_usd * (1 - spot_savings_percent)
        savings_per_hour = config.cost_per_hour_usd - spot_cost_per_hour
        
        return {
            "savings_percent": spot_savings_percent * 100,
            "savings_per_hour": round(savings_per_hour, 2),
            "spot_cost_per_hour": round(spot_cost_per_hour, 2)
        }
    
    def get_recommendation_for_model(
        self, 
        model_parameters: int, 
        quantization_bits: int,
        batch_size: int = 1,
        max_cost_per_hour: Optional[float] = None
    ) -> Optional[GPUConfig]:
        """
        Get GPU recommendation for a specific model.
        
        Args:
            model_parameters: Number of model parameters
            quantization_bits: Quantization precision (4, 8, 16, 32)
            batch_size: Batch size for inference
            max_cost_per_hour: Maximum cost constraint
            
        Returns:
            Recommended GPU configuration
        """
        from .vram_calculator import VRAMCalculator, ModelSpecs
        
        # Calculate VRAM requirement
        vram_calc = VRAMCalculator()
        model_specs = ModelSpecs(
            parameters=model_parameters,
            quantization_bits=quantization_bits,
            batch_size=batch_size
        )
        
        required_vram = vram_calc.calculate_vram_requirement(model_specs)
        
        # Create hardware requirement
        requirement = HardwareRequirement(
            min_vram_gb=required_vram,
            max_cost_per_hour=max_cost_per_hour,
            prefer_spot_instances=True
        )
        
        return self.get_cost_optimized_config(requirement)
