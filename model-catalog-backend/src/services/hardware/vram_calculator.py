"""VRAM calculation utilities for model requirements."""

from typing import Dict, Any
from dataclasses import dataclass

from src.core.exceptions import VRAMCalculationError


@dataclass
class ModelSpecs:
    """Model specifications for VRAM calculation."""
    parameters: int  # Number of parameters (e.g., 7B, 13B, 70B)
    quantization_bits: int  # 4, 8, 16, 32
    sequence_length: int = 2048  # Context length
    batch_size: int = 1  # Batch size for inference


class VRAMCalculator:
    """Calculate VRAM requirements for models."""
    
    # Memory overhead factors
    OVERHEAD_FACTOR = 1.2  # 20% overhead for KV cache, activations, etc.
    KV_CACHE_FACTOR = 2.0  # Additional factor for KV cache at longer sequences
    
    def calculate_vram_requirement(self, model_specs: ModelSpecs) -> float:
        """
        Calculate VRAM requirement for a model.
        
        Formula: (parameters × bits/8) × overhead_factor + kv_cache_overhead
        
        Args:
            model_specs: Model specifications
            
        Returns:
            VRAM requirement in GB
        """
        try:
            # Base model memory (parameters in bytes)
            base_memory_gb = (model_specs.parameters * model_specs.quantization_bits / 8) / (1024**3)
            
            # Apply overhead factor
            model_memory_gb = base_memory_gb * self.OVERHEAD_FACTOR
            
            # KV cache memory (for transformer models)
            kv_cache_memory_gb = self._calculate_kv_cache_memory(model_specs)
            
            total_vram_gb = model_memory_gb + kv_cache_memory_gb
            
            return round(total_vram_gb, 2)
            
        except Exception as e:
            raise VRAMCalculationError(f"Failed to calculate VRAM requirement: {str(e)}")
    
    def _calculate_kv_cache_memory(self, model_specs: ModelSpecs) -> float:
        """Calculate KV cache memory requirement."""
        # Simplified KV cache calculation
        # This is a rough estimate - actual implementation would be more sophisticated
        kv_cache_bytes = (
            model_specs.parameters * 
            model_specs.sequence_length * 
            model_specs.batch_size * 
            2 *  # Key and Value matrices
            model_specs.quantization_bits / 8
        )
        
        return (kv_cache_bytes / (1024**3)) * self.KV_CACHE_FACTOR
    
    def get_quantization_memory_savings(self, parameters: int) -> Dict[str, float]:
        """Get memory requirements for different quantization levels."""
        quantizations = {
            "fp32": 32,
            "fp16": 16,
            "int8": 8,
            "int4": 4,
        }
        
        results = {}
        for name, bits in quantizations.items():
            specs = ModelSpecs(parameters=parameters, quantization_bits=bits)
            results[name] = self.calculate_vram_requirement(specs)
        
        return results
    
    def estimate_optimal_batch_size(
        self, 
        model_specs: ModelSpecs, 
        available_vram_gb: float
    ) -> int:
        """Estimate optimal batch size for given VRAM constraint."""
        max_batch_size = 1
        
        for batch_size in range(1, 33):  # Test up to batch size 32
            test_specs = ModelSpecs(
                parameters=model_specs.parameters,
                quantization_bits=model_specs.quantization_bits,
                sequence_length=model_specs.sequence_length,
                batch_size=batch_size
            )
            
            required_vram = self.calculate_vram_requirement(test_specs)
            
            if required_vram <= available_vram_gb:
                max_batch_size = batch_size
            else:
                break
        
        return max_batch_size
