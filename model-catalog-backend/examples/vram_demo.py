"""Demo script for VRAM calculator - standalone example."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.hardware.vram_calculator import (
    calculate_vram_requirement,
    recommend_gpu_config,
    get_quantization_comparison,
    estimate_max_batch_size
)


def main():
    print("=" * 80)
    print("VRAM Calculator & GPU Matcher Demo")
    print("=" * 80)
    print()
    
    # Example 1: Calculate VRAM for popular models
    print("📊 Example 1: VRAM Requirements for Popular Models")
    print("-" * 80)
    
    models = [
        ("Llama-3.1-7B", 7_000_000_000, 'fp16'),
        ("Llama-3.1-70B", 70_000_000_000, 'int4'),
        ("GPT-3.5", 175_000_000_000, 'int8'),
        ("Mistral-7B", 7_300_000_000, 'fp16'),
    ]
    
    for name, params, quant in models:
        vram = calculate_vram_requirement(params, quant)
        print(f"{name:20s} ({quant:4s}): {vram:6.1f} GB")
    print()
    
    # Example 2: Quantization comparison
    print("🔬 Example 2: Quantization Comparison for Llama-7B")
    print("-" * 80)
    
    comparison = get_quantization_comparison(7_000_000_000)
    for quant, vram in comparison.items():
        savings = ((comparison['fp32'] - vram) / comparison['fp32']) * 100
        print(f"{quant:6s}: {vram:5.1f} GB (saves {savings:4.0f}% vs FP32)")
    print()
    
    # Example 3: GPU recommendations
    print("🎯 Example 3: GPU Recommendations for Llama-70B (INT4)")
    print("-" * 80)
    
    vram_needed = calculate_vram_requirement(70_000_000_000, 'int4')
    print(f"Required VRAM: {vram_needed:.1f} GB\n")
    
    configs = recommend_gpu_config(vram_needed, prefer_spot=True)
    
    print("Top 5 Cost-Effective Configurations:\n")
    for i, cfg in enumerate(configs[:5], 1):
        spot_tag = "☁️ Spot" if cfg['spot_available'] else "🔒 On-Demand"
        print(f"{i}. {cfg['gpu_type']:12s} x{cfg['count']}  "
              f"({cfg['utilization_pct']:5.1f}% util)  "
              f"${cfg['cost_per_hour_usd']:5.2f}/hr  {spot_tag}")
    print()
    
    # Example 4: Batch size estimation
    print("⚡ Example 4: Maximum Batch Size Estimation")
    print("-" * 80)
    
    test_cases = [
        (7_000_000_000, 'fp16', 40),  # Llama-7B on A100-40GB
        (7_000_000_000, 'fp16', 80),  # Llama-7B on A100-80GB
        (70_000_000_000, 'int4', 80), # Llama-70B INT4 on A100-80GB
    ]
    
    for params, quant, available_vram in test_cases:
        model_size = f"{params/1e9:.0f}B"
        max_batch = estimate_max_batch_size(params, quant, available_vram)
        print(f"{model_size:4s} model ({quant:4s}) on {available_vram}GB GPU: "
              f"max batch size = {max_batch}")
    print()
    
    # Example 5: Real-world scenario
    print("🌟 Example 5: Real-World Deployment Planning")
    print("-" * 80)
    print("Scenario: Deploy Llama-3.1-70B for production chatbot")
    print()
    
    model_params = 70_000_000_000
    
    print("1. Choosing quantization:")
    for quant in ['fp16', 'int8', 'int4']:
        vram = calculate_vram_requirement(model_params, quant)
        configs = recommend_gpu_config(vram, prefer_spot=True, max_cost_per_hour=5.0)
        if configs:
            best = configs[0]
            print(f"   {quant:4s}: {vram:5.1f} GB → {best['gpu_type']} x{best['count']} "
                  f"@ ${best['cost_per_hour_usd']:.2f}/hr (spot)")
    
    print()
    print("2. Selected: INT4 quantization")
    selected_vram = calculate_vram_requirement(model_params, 'int4')
    print(f"   Required VRAM: {selected_vram:.1f} GB")
    
    print()
    print("3. GPU Configuration Options:")
    configs = recommend_gpu_config(selected_vram, prefer_spot=True)
    for cfg in configs[:3]:
        monthly_cost = cfg['cost_per_hour_usd'] * 24 * 30
        print(f"   • {cfg['gpu_type']:12s} x{cfg['count']}: "
              f"${cfg['cost_per_hour_usd']:5.2f}/hr (${monthly_cost:7.2f}/month)")
    
    print()
    print("4. Throughput Estimation:")
    best_config = configs[0]
    max_batch = estimate_max_batch_size(model_params, 'int4', best_config['total_vram_gb'])
    print(f"   Max batch size on {best_config['gpu_type']} x{best_config['count']}: {max_batch}")
    print(f"   Est. throughput: ~{max_batch * 50} tokens/sec (assuming 50 tok/s per batch)")
    
    print()
    print("=" * 80)
    print("✨ Demo Complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()

