"""Tests for VRAM calculator."""

import pytest
from src.services.hardware.vram_calculator import (
    calculate_vram_requirement,
    recommend_gpu_config,
    get_quantization_comparison,
    estimate_max_batch_size,
)


class TestVRAMCalculator:
    """Test suite for VRAM calculation functions."""
    
    def test_calculate_vram_fp16(self):
        """Test VRAM calculation for FP16 model."""
        # Llama-7B in FP16: ~16.8 GB
        vram = calculate_vram_requirement(7_000_000_000, 'fp16')
        assert 16 < vram < 18, f"Expected ~16.8 GB, got {vram}"
    
    def test_calculate_vram_int4(self):
        """Test VRAM calculation for INT4 model."""
        # Llama-70B in INT4: ~42 GB
        vram = calculate_vram_requirement(70_000_000_000, 'int4')
        assert 40 < vram < 45, f"Expected ~42 GB, got {vram}"
    
    def test_invalid_quantization(self):
        """Test error on invalid quantization type."""
        with pytest.raises(ValueError, match="Unsupported quantization"):
            calculate_vram_requirement(7_000_000_000, 'invalid')
    
    def test_batch_size_overhead(self):
        """Test that larger batch sizes require more VRAM."""
        vram_batch_1 = calculate_vram_requirement(7_000_000_000, 'fp16', batch_size=1)
        vram_batch_4 = calculate_vram_requirement(7_000_000_000, 'fp16', batch_size=4)
        
        assert vram_batch_4 > vram_batch_1, "Larger batch should need more VRAM"
        # Should be roughly 30% more for batch=4 (10% per additional batch)
        assert vram_batch_4 < vram_batch_1 * 1.5
    
    def test_quantization_comparison(self):
        """Test quantization comparison returns correct order."""
        comparison = get_quantization_comparison(7_000_000_000)
        
        # Should have all quantization types
        assert 'fp32' in comparison
        assert 'fp16' in comparison
        assert 'int8' in comparison
        assert 'int4' in comparison
        
        # Order should be: fp32 > fp16 > int8 > int4
        assert comparison['fp32'] > comparison['fp16']
        assert comparison['fp16'] > comparison['int8']
        assert comparison['int8'] > comparison['int4']
        
        # FP32 should be ~2x FP16
        assert 1.9 < comparison['fp32'] / comparison['fp16'] < 2.1
    
    def test_recommend_gpu_config_basic(self):
        """Test GPU recommendations for basic requirement."""
        configs = recommend_gpu_config(vram_needed=20.0, prefer_spot=True)
        
        # Should return at least one configuration
        assert len(configs) > 0
        
        # All configs should meet VRAM requirement
        for cfg in configs:
            assert cfg['total_vram_gb'] >= 20.0
            assert cfg['spot_available'] is True  # Prefer spot
        
        # First config should be most cost-effective
        first_efficiency = configs[0]['cost_per_hour_usd'] / 20.0
        for cfg in configs[1:]:
            efficiency = cfg['cost_per_hour_usd'] / 20.0
            assert efficiency >= first_efficiency
    
    def test_recommend_gpu_config_cost_limit(self):
        """Test GPU recommendations with cost constraint."""
        configs = recommend_gpu_config(
            vram_needed=35.0,
            prefer_spot=True,
            max_cost_per_hour=2.0
        )
        
        # All configs should be under cost limit
        for cfg in configs:
            assert cfg['cost_per_hour_usd'] <= 2.0
    
    def test_recommend_gpu_config_utilization(self):
        """Test that utilization is calculated correctly."""
        configs = recommend_gpu_config(vram_needed=16.0)
        
        for cfg in configs:
            expected_util = (16.0 / cfg['total_vram_gb']) * 100
            assert abs(cfg['utilization_pct'] - expected_util) < 0.1
    
    def test_estimate_max_batch_size(self):
        """Test maximum batch size estimation."""
        # Llama-7B FP16 on A100-80GB should support batch > 1
        max_batch = estimate_max_batch_size(
            parameters=7_000_000_000,
            quantization='fp16',
            available_vram_gb=80
        )
        
        assert max_batch > 1, "Should support batch size > 1"
        assert max_batch < 64, "Should be under max tested value"
        
        # Verify the batch size fits in VRAM
        vram_needed = calculate_vram_requirement(
            7_000_000_000, 'fp16', max_batch
        )
        assert vram_needed <= 80
    
    def test_estimate_max_batch_size_tight_fit(self):
        """Test batch size with tight VRAM constraint."""
        # Llama-7B FP16 needs ~16.8 GB, so on 18 GB should only fit batch=1
        max_batch = estimate_max_batch_size(
            parameters=7_000_000_000,
            quantization='fp16',
            available_vram_gb=18
        )
        
        assert max_batch == 1, "Tight constraint should only allow batch=1"
    
    def test_all_quantizations_supported(self):
        """Test that all documented quantization types work."""
        quantizations = ['fp32', 'fp16', 'bf16', 'int8', 'int4', 'awq', 'gptq']
        
        for quant in quantizations:
            vram = calculate_vram_requirement(7_000_000_000, quant)
            assert vram > 0, f"Failed for {quant}"
            assert isinstance(vram, float)
    
    def test_realistic_scenario_llama_70b(self):
        """Test realistic deployment scenario for Llama-70B."""
        # INT4 quantization
        vram = calculate_vram_requirement(70_000_000_000, 'int4')
        
        # Should need ~42 GB
        assert 40 < vram < 45
        
        # Get recommendations
        configs = recommend_gpu_config(vram, prefer_spot=True)
        
        # Should recommend A100-80GB or H100
        assert len(configs) > 0
        best = configs[0]
        assert best['total_vram_gb'] >= vram
        assert best['gpu_type'] in ['A100-80GB', 'H100', 'A100-40GB']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

