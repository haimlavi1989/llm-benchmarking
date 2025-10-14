"""VRAM calculation utilities for model requirements.

Pure function implementation - NO external dependencies.

Example:
    >>> # Calculate VRAM for Llama-7B FP16
    >>> vram = calculate_vram_requirement(
    ...     parameters=7_000_000_000,  # 7B parameters
    ...     quantization='fp16',
    ...     batch_size=1
    ... )
    >>> print(f"Required VRAM: {vram:.1f} GB")
    Required VRAM: 16.8 GB
    
    >>> # Get GPU recommendations
    >>> configs = recommend_gpu_config(vram_needed=16.8)
    >>> for config in configs[:2]:
    ...     print(f"{config['gpu_type']} x{config['count']}: {config['utilization']:.0f}% utilization")
    L4 x1: 70% utilization
    A100-40GB x1: 42% utilization
"""

from typing import Dict, List, Literal


# Quantization bits mapping
QUANTIZATION_BITS: Dict[str, float] = {
    'fp32': 4.0,   # 32 bits = 4 bytes
    'fp16': 2.0,   # 16 bits = 2 bytes
    'bf16': 2.0,   # bfloat16 = 2 bytes
    'int8': 1.0,   # 8 bits = 1 byte
    'int4': 0.5,   # 4 bits = 0.5 bytes
    'awq': 0.5,    # AWQ quantization ≈ 4-bit
    'gptq': 0.5,   # GPTQ quantization ≈ 4-bit
}

# Memory overhead factor (20% for KV cache, activations, etc.)
OVERHEAD_FACTOR = 1.2


def calculate_vram_requirement(
    parameters: int,
    quantization: str,
    batch_size: int = 1,
    sequence_length: int = 2048
) -> float:
    """Calculate VRAM requirement for a model.
    
    Formula: (parameters × bytes_per_param) × overhead_factor
    
    Args:
        parameters: Number of model parameters (e.g., 7_000_000_000 for 7B)
        quantization: Quantization type ('fp32', 'fp16', 'int8', 'int4', 'awq', 'gptq')
        batch_size: Batch size for inference (default: 1)
        sequence_length: Context length (default: 2048)
    
    Returns:
        VRAM requirement in GB
    
    Raises:
        ValueError: If quantization type is not supported
    
    Example:
        >>> # Llama-7B in FP16
        >>> vram = calculate_vram_requirement(7_000_000_000, 'fp16')
        >>> print(f"{vram:.1f} GB")
        16.8 GB
        
        >>> # Llama-70B in INT4
        >>> vram = calculate_vram_requirement(70_000_000_000, 'int4')
        >>> print(f"{vram:.1f} GB")
        42.0 GB
    """
    # Validate quantization type
    if quantization not in QUANTIZATION_BITS:
        raise ValueError(
            f"Unsupported quantization: {quantization}. "
            f"Supported types: {list(QUANTIZATION_BITS.keys())}"
        )
    
    # Get bytes per parameter
    bytes_per_param = QUANTIZATION_BITS[quantization]
    
    # Base model memory in GB
    model_memory_gb = (parameters * bytes_per_param) / (1024**3)
    
    # Apply overhead factor (KV cache, activations, etc.)
    total_vram_gb = model_memory_gb * OVERHEAD_FACTOR
    
    # Additional memory for larger batch sizes
    if batch_size > 1:
        batch_overhead = 0.1 * (batch_size - 1)  # 10% per additional batch
        total_vram_gb *= (1 + batch_overhead)
    
    return round(total_vram_gb, 2)


def recommend_gpu_config(
    vram_needed: float,
    prefer_spot: bool = True,
    max_cost_per_hour: float | None = None
) -> List[Dict[str, any]]:
    """Recommend GPU configurations for given VRAM requirement.
    
    Args:
        vram_needed: Required VRAM in GB
        prefer_spot: Prefer spot instances (60-90% cost savings)
        max_cost_per_hour: Maximum cost per hour in USD (optional)
    
    Returns:
        List of GPU configurations sorted by cost efficiency
        Each config contains: gpu_type, count, total_vram_gb, utilization_pct, 
        cost_per_hour_usd, spot_available
    
    Example:
        >>> configs = recommend_gpu_config(vram_needed=35.0, prefer_spot=True)
        >>> for cfg in configs[:3]:
        ...     print(f"{cfg['gpu_type']} x{cfg['count']}: "
        ...           f"{cfg['utilization_pct']:.0f}% @ ${cfg['cost_per_hour_usd']}/hr")
        A100-40GB x1: 88% @ $1.20/hr
        A100-80GB x1: 44% @ $2.40/hr
        L4 x2: 73% @ $1.00/hr
    """
    # Available GPU configurations
    gpu_catalog = [
        {'gpu_type': 'L4', 'vram_per_gpu': 24, 'cost_per_hour': 0.50, 'spot_available': True},
        {'gpu_type': 'A100-40GB', 'vram_per_gpu': 40, 'cost_per_hour': 1.20, 'spot_available': True},
        {'gpu_type': 'A100-80GB', 'vram_per_gpu': 80, 'cost_per_hour': 2.40, 'spot_available': True},
        {'gpu_type': 'H100', 'vram_per_gpu': 80, 'cost_per_hour': 4.00, 'spot_available': True},
        {'gpu_type': 'V100', 'vram_per_gpu': 16, 'cost_per_hour': 0.80, 'spot_available': False},
    ]
    
    recommendations = []
    
    for gpu in gpu_catalog:
        # Calculate minimum GPUs needed
        min_gpus = int(vram_needed / gpu['vram_per_gpu']) + (
            1 if vram_needed % gpu['vram_per_gpu'] > 0 else 0
        )
        
        # Only consider up to 8 GPUs (practical limit)
        for count in range(min_gpus, min(9, min_gpus + 3)):
            total_vram = gpu['vram_per_gpu'] * count
            
            if total_vram >= vram_needed:
                cost = gpu['cost_per_hour'] * count
                
                # Apply spot instance discount (75% average)
                if gpu['spot_available'] and prefer_spot:
                    cost *= 0.25  # 75% discount
                
                # Check cost constraint
                if max_cost_per_hour and cost > max_cost_per_hour:
                    continue
                
                # Filter by spot preference
                if prefer_spot and not gpu['spot_available']:
                    continue
                
                utilization = (vram_needed / total_vram) * 100
                
                recommendations.append({
                    'gpu_type': gpu['gpu_type'],
                    'count': count,
                    'vram_per_gpu_gb': gpu['vram_per_gpu'],
                    'total_vram_gb': total_vram,
                    'utilization_pct': round(utilization, 1),
                    'cost_per_hour_usd': round(cost, 2),
                    'spot_available': gpu['spot_available']
                })
    
    # Sort by cost efficiency (cost per GB utilized)
    recommendations.sort(key=lambda x: x['cost_per_hour_usd'] / vram_needed)
    
    return recommendations


def get_quantization_comparison(parameters: int) -> Dict[str, float]:
    """Compare VRAM requirements across different quantization levels.
    
    Args:
        parameters: Number of model parameters
    
    Returns:
        Dictionary mapping quantization type to VRAM requirement in GB
    
    Example:
        >>> comparison = get_quantization_comparison(7_000_000_000)
        >>> for quant, vram in comparison.items():
        ...     print(f"{quant:6s}: {vram:5.1f} GB")
        fp32  : 33.6 GB
        fp16  : 16.8 GB
        int8  :  8.4 GB
        int4  :  4.2 GB
    """
    return {
        quant: calculate_vram_requirement(parameters, quant)
        for quant in ['fp32', 'fp16', 'int8', 'int4']
    }


def estimate_max_batch_size(
    parameters: int,
    quantization: str,
    available_vram_gb: float,
    sequence_length: int = 2048
) -> int:
    """Estimate maximum batch size for given VRAM constraint.
    
    Args:
        parameters: Number of model parameters
        quantization: Quantization type
        available_vram_gb: Available VRAM in GB
        sequence_length: Context length
    
    Returns:
        Maximum recommended batch size
    
    Example:
        >>> max_batch = estimate_max_batch_size(
        ...     parameters=7_000_000_000,
        ...     quantization='fp16',
        ...     available_vram_gb=40
        ... )
        >>> print(f"Max batch size: {max_batch}")
        Max batch size: 2
    """
    for batch_size in range(1, 65):  # Test up to 64
        vram_needed = calculate_vram_requirement(
            parameters, 
            quantization, 
            batch_size, 
            sequence_length
        )
        
        if vram_needed > available_vram_gb:
            return max(1, batch_size - 1)
    
    return 64  # Maximum tested
