"""Integration tests for recommendation flow.

Tests the complete flow from API request to response with mocked repositories.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from src.services.model_service import ModelService, UseCaseConstraints, ModelCard
from src.repositories import ModelRepository, BenchmarkRepository, HardwareRepository
from src.models import Model, ModelVersion


@pytest.fixture
def mock_model():
    """Create a mock Model instance."""
    model = MagicMock(spec=Model)
    model.id = uuid4()
    model.name = "Llama-3.1-7B"
    model.architecture = "llama"
    model.parameters = 7_000_000_000
    model.tags = ["chat", "open-source"]
    
    # Mock version
    version = MagicMock(spec=ModelVersion)
    version.id = uuid4()
    version.version = "v1.0"
    version.quantization = "fp16"
    version.quantization_bits = 16
    version.vram_requirement_gb = 16.8
    
    model.versions = [version]
    model.use_cases = []
    
    return model


@pytest.fixture
async def mock_repositories(mock_model):
    """Create mock repositories with sample data."""
    # Model repository
    model_repo = AsyncMock(spec=ModelRepository)
    model_repo.search_by_use_case.return_value = [mock_model]
    model_repo.get_with_benchmarks.return_value = mock_model
    
    # Benchmark repository
    benchmark_repo = AsyncMock(spec=BenchmarkRepository)
    benchmark_repo.get_aggregated_stats.return_value = {
        'total_benchmarks': 10,
        'avg_accuracy': 0.85,
        'avg_ttft_p50_ms': 105.0,
        'avg_ttft_p90_ms': 120.0,
        'avg_tpot_p50_ms': 10.0,
        'avg_tpot_p90_ms': 12.0,
        'avg_throughput': 450.0,
        'max_throughput': 500.0,
        'avg_gpu_utilization_pct': 85.0,
        'avg_memory_used_gb': 16.2
    }
    
    # Hardware repository
    hardware_repo = AsyncMock(spec=HardwareRepository)
    
    return model_repo, benchmark_repo, hardware_repo


@pytest.mark.asyncio
async def test_recommendation_flow_end_to_end(mock_repositories):
    """Test complete recommendation flow with mocked dependencies."""
    model_repo, benchmark_repo, hardware_repo = mock_repositories
    
    # Create service with mocked repositories
    service = ModelService(
        model_repo=model_repo,
        benchmark_repo=benchmark_repo,
        hardware_repo=hardware_repo
    )
    
    # Create constraints
    constraints = UseCaseConstraints(
        use_case='chatbot',
        max_latency_p90_ms=300,
        min_throughput=400,
        min_accuracy=0.80,
        max_cost_per_hour=5.0,
        prefer_spot_instances=True,
        weight_accuracy=0.30,
        weight_latency=0.25,
        weight_throughput=0.25,
        weight_cost=0.20
    )
    
    # Execute recommendation
    results = await service.recommend_models(constraints, limit=5)
    
    # Assertions
    assert isinstance(results, list)
    assert len(results) <= 5
    
    # Verify repositories were called
    assert model_repo.search_by_use_case.called
    assert model_repo.search_by_use_case.call_args[0][0] == 'chatbot'
    assert benchmark_repo.get_aggregated_stats.called


@pytest.mark.asyncio
async def test_vram_to_gpu_matching_integration():
    """Test VRAM calculation integrates correctly with GPU matching."""
    from src.services.hardware.vram_calculator import (
        calculate_vram_requirement,
        recommend_gpu_config
    )
    
    # Scenario: Llama-7B in FP16
    vram_needed = calculate_vram_requirement(
        parameters=7_000_000_000,
        quantization='fp16',
        batch_size=1
    )
    
    # Should be around 16.8 GB
    assert 16 < vram_needed < 18
    
    # Get GPU recommendations
    configs = recommend_gpu_config(
        vram_needed=vram_needed,
        prefer_spot=True,
        max_cost_per_hour=2.0
    )
    
    # Assertions
    assert len(configs) > 0
    
    # First recommendation should meet requirements
    best_config = configs[0]
    assert best_config['total_vram_gb'] >= vram_needed
    assert best_config['spot_available'] is True
    assert best_config['cost_per_hour_usd'] <= 2.0
    
    # Verify it's L4 or A100-40GB (cheapest options)
    assert best_config['gpu_type'] in ['L4', 'A100-40GB']


@pytest.mark.asyncio
async def test_topsis_integration_with_real_data():
    """Test TOPSIS algorithm with realistic model comparison."""
    import pandas as pd
    from src.services.ranking.topsis import calculate_topsis_scores
    
    # Create realistic benchmark comparison
    data = pd.DataFrame({
        'model': ['Llama-7B-fp16', 'Llama-7B-int4', 'Mistral-7B-fp16'],
        'accuracy': [0.85, 0.83, 0.87],
        'latency': [120, 90, 110],
        'throughput': [450, 520, 480],
        'cost': [0.60, 0.30, 0.65]
    })
    
    weights = {
        'accuracy': 0.30,
        'latency': 0.25,
        'throughput': 0.25,
        'cost': 0.20
    }
    
    # Calculate scores
    result = calculate_topsis_scores(
        data,
        weights,
        benefit_criteria=['accuracy', 'throughput'],
        cost_criteria=['latency', 'cost']
    )
    
    # Assertions
    assert 'topsis_score' in result.columns
    assert 'topsis_rank' in result.columns
    
    # INT4 should rank high (good balance of cost and performance)
    int4_row = result[result['model'] == 'Llama-7B-int4']
    assert int4_row['topsis_rank'].values[0] <= 2


@pytest.mark.asyncio  
async def test_model_service_search(mock_repositories):
    """Test model search functionality."""
    model_repo, benchmark_repo, hardware_repo = mock_repositories
    
    # Setup mock return
    model_repo.search_models.return_value = [mock_repositories[0]]
    
    service = ModelService(
        model_repo=model_repo,
        benchmark_repo=benchmark_repo,
        hardware_repo=hardware_repo
    )
    
    # Search for models
    results = await service.search_models(
        query="llama",
        architecture="llama",
        min_parameters=7_000_000_000,
        limit=10
    )
    
    # Assertions
    assert isinstance(results, list)
    assert model_repo.search_models.called


@pytest.mark.asyncio
async def test_recommendation_respects_constraints(mock_repositories):
    """Test that recommendations respect SLA constraints."""
    model_repo, benchmark_repo, hardware_repo = mock_repositories
    
    service = ModelService(
        model_repo=model_repo,
        benchmark_repo=benchmark_repo,
        hardware_repo=hardware_repo
    )
    
    # Very strict constraints
    constraints = UseCaseConstraints(
        use_case='chatbot',
        max_latency_p90_ms=100,  # Very strict
        min_throughput=500,       # High requirement
        min_accuracy=0.90,        # High quality
        max_cost_per_hour=1.0    # Low budget
    )
    
    results = await service.recommend_models(constraints, limit=10)
    
    # With strict constraints, might get fewer results
    assert isinstance(results, list)
    # All results should meet constraints (if any returned)
    for rec in results:
        if rec.avg_ttft_p90_ms:
            assert rec.avg_ttft_p90_ms <= 100
        if rec.avg_throughput:
            assert rec.avg_throughput >= 500
        if rec.avg_accuracy:
            assert rec.avg_accuracy >= 0.90

