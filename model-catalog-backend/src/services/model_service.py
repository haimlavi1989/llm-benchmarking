"""Model service - orchestrates model recommendations and queries.

This service integrates:
- Repository layer (data access)
- TOPSIS algorithm (multi-criteria ranking)
- VRAM calculator (hardware matching)
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from dataclasses import dataclass
import pandas as pd

from src.repositories import ModelRepository, BenchmarkRepository, HardwareRepository
from src.services.ranking.topsis import calculate_topsis_scores
from src.services.hardware.vram_calculator import (
    calculate_vram_requirement,
    recommend_gpu_config
)


@dataclass
class ModelCard:
    """Model card with recommendation details."""
    model_id: UUID
    model_name: str
    architecture: str
    parameters: int
    quantization: str
    
    # Performance metrics
    avg_accuracy: Optional[float] = None
    avg_ttft_p90_ms: Optional[float] = None
    avg_throughput: Optional[float] = None
    
    # Hardware requirements
    vram_requirement_gb: Optional[float] = None
    recommended_gpu: Optional[Dict[str, Any]] = None
    
    # Ranking
    topsis_score: Optional[float] = None
    rank: Optional[int] = None


@dataclass
class UseCaseConstraints:
    """Use case constraints for model selection."""
    use_case: str
    max_latency_p90_ms: Optional[float] = None
    min_throughput: Optional[float] = None
    min_accuracy: Optional[float] = None
    max_cost_per_hour: Optional[float] = None
    prefer_spot_instances: bool = True
    
    # TOPSIS weights (must sum to 1.0)
    weight_accuracy: float = 0.30
    weight_latency: float = 0.25
    weight_throughput: float = 0.25
    weight_cost: float = 0.20


class ModelService:
    """Service for model recommendations and queries."""
    
    def __init__(
        self,
        model_repo: ModelRepository,
        benchmark_repo: BenchmarkRepository,
        hardware_repo: HardwareRepository
    ):
        """Initialize model service with repositories.
        
        Args:
            model_repo: Model repository for model data
            benchmark_repo: Benchmark repository for performance data
            hardware_repo: Hardware repository for GPU configurations
        """
        self.model_repo = model_repo
        self.benchmark_repo = benchmark_repo
        self.hardware_repo = hardware_repo
    
    async def recommend_models(
        self,
        constraints: UseCaseConstraints,
        limit: int = 10
    ) -> List[ModelCard]:
        """Recommend models based on use case and constraints.
        
        This method:
        1. Queries models suitable for the use case
        2. Fetches benchmark data
        3. Applies TOPSIS multi-criteria ranking
        4. Matches hardware requirements
        5. Returns top N recommendations
        
        Args:
            constraints: Use case constraints and preferences
            limit: Maximum number of recommendations to return
            
        Returns:
            List of recommended models with scores and hardware configs
        
        Example:
            >>> constraints = UseCaseConstraints(
            ...     use_case='chatbot',
            ...     max_latency_p90_ms=300,
            ...     min_accuracy=0.80,
            ...     max_cost_per_hour=5.0
            ... )
            >>> recommendations = await service.recommend_models(constraints, limit=5)
        """
        # Step 1: Query models for use case
        models = await self.model_repo.search_by_use_case(constraints.use_case)
        
        if not models:
            return []
        
        # Step 2: Build evaluation dataset
        evaluation_data = []
        
        for model in models:
            # Get benchmark statistics
            for version in model.versions:
                stats = await self.benchmark_repo.get_aggregated_stats(
                    model_version_id=version.id
                )
                
                if stats['total_benchmarks'] == 0:
                    continue
                
                # Apply hard constraints
                if constraints.max_latency_p90_ms and stats['avg_ttft_p90_ms']:
                    if stats['avg_ttft_p90_ms'] > constraints.max_latency_p90_ms:
                        continue
                
                if constraints.min_throughput and stats['avg_throughput']:
                    if stats['avg_throughput'] < constraints.min_throughput:
                        continue
                
                if constraints.min_accuracy and stats['avg_accuracy']:
                    if stats['avg_accuracy'] < constraints.min_accuracy:
                        continue
                
                # Calculate VRAM requirement
                vram_needed = calculate_vram_requirement(
                    parameters=model.parameters,
                    quantization=version.quantization
                )
                
                # Get cost-optimized GPU config
                gpu_configs = recommend_gpu_config(
                    vram_needed=vram_needed,
                    prefer_spot=constraints.prefer_spot_instances,
                    max_cost_per_hour=constraints.max_cost_per_hour
                )
                
                if not gpu_configs:
                    continue
                
                best_gpu = gpu_configs[0]
                
                evaluation_data.append({
                    'model_id': model.id,
                    'model_name': model.name,
                    'architecture': model.architecture,
                    'parameters': model.parameters,
                    'version_id': version.id,
                    'quantization': version.quantization,
                    'vram_requirement_gb': vram_needed,
                    'accuracy': stats['avg_accuracy'] or 0.0,
                    'latency': stats['avg_ttft_p90_ms'] or 0.0,
                    'throughput': stats['avg_throughput'] or 0.0,
                    'cost': best_gpu['cost_per_hour_usd'],
                    'gpu_config': best_gpu
                })
        
        if not evaluation_data:
            return []
        
        # Step 3: Apply TOPSIS ranking
        df = pd.DataFrame(evaluation_data)
        
        weights = {
            'accuracy': constraints.weight_accuracy,
            'latency': constraints.weight_latency,
            'throughput': constraints.weight_throughput,
            'cost': constraints.weight_cost
        }
        
        ranked_df = calculate_topsis_scores(
            df,
            weights,
            benefit_criteria=['accuracy', 'throughput'],
            cost_criteria=['latency', 'cost']
        )
        
        # Step 4: Build model cards
        ranked_df = ranked_df.sort_values('topsis_rank').head(limit)
        
        recommendations = []
        for _, row in ranked_df.iterrows():
            card = ModelCard(
                model_id=row['model_id'],
                model_name=row['model_name'],
                architecture=row['architecture'],
                parameters=row['parameters'],
                quantization=row['quantization'],
                avg_accuracy=row['accuracy'],
                avg_ttft_p90_ms=row['latency'],
                avg_throughput=row['throughput'],
                vram_requirement_gb=row['vram_requirement_gb'],
                recommended_gpu=row['gpu_config'],
                topsis_score=row['topsis_score'],
                rank=row['topsis_rank']
            )
            recommendations.append(card)
        
        return recommendations
    
    async def get_model_with_stats(self, model_id: UUID) -> Optional[Dict[str, Any]]:
        """Get detailed model information with statistics.
        
        Args:
            model_id: Model UUID
            
        Returns:
            Dictionary with model details, benchmarks, and hardware recommendations
        
        Example:
            >>> details = await service.get_model_with_stats(model_id)
            >>> print(f"{details['name']}: {details['avg_accuracy']:.2%} accuracy")
        """
        # Get model with relationships
        model = await self.model_repo.get_with_benchmarks(model_id)
        
        if not model:
            return None
        
        # Aggregate statistics across all versions
        all_stats = []
        version_details = []
        
        for version in model.versions:
            stats = await self.benchmark_repo.get_aggregated_stats(version.id)
            
            if stats['total_benchmarks'] > 0:
                all_stats.append(stats)
                
                # Get VRAM and hardware recommendations
                vram_needed = calculate_vram_requirement(
                    parameters=model.parameters,
                    quantization=version.quantization
                )
                
                gpu_configs = recommend_gpu_config(vram_needed, prefer_spot=True)
                
                version_details.append({
                    'version': version.version,
                    'quantization': version.quantization,
                    'vram_requirement_gb': vram_needed,
                    'recommended_gpus': gpu_configs[:3],  # Top 3
                    'stats': stats
                })
        
        # Calculate overall averages
        if all_stats:
            avg_accuracy = sum(s['avg_accuracy'] for s in all_stats if s['avg_accuracy']) / len(all_stats)
            avg_throughput = sum(s['avg_throughput'] for s in all_stats if s['avg_throughput']) / len(all_stats)
            avg_latency = sum(s['avg_ttft_p90_ms'] for s in all_stats if s['avg_ttft_p90_ms']) / len(all_stats)
        else:
            avg_accuracy = avg_throughput = avg_latency = None
        
        return {
            'id': model.id,
            'name': model.name,
            'architecture': model.architecture,
            'parameters': model.parameters,
            'base_model': model.base_model,
            'tags': model.tags,
            'avg_accuracy': avg_accuracy,
            'avg_throughput': avg_throughput,
            'avg_latency_p90_ms': avg_latency,
            'versions': version_details,
            'use_cases': [
                {
                    'category': uc.use_case.category,
                    'suitability_score': uc.suitability_score,
                    'recommended': uc.recommended
                }
                for uc in model.use_cases
            ] if hasattr(model, 'use_cases') else []
        }
    
    async def search_models(
        self,
        query: str,
        architecture: Optional[str] = None,
        min_parameters: Optional[int] = None,
        max_parameters: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search models with filters.
        
        Args:
            query: Search query (model name or tags)
            architecture: Filter by architecture (llama, gpt, mistral)
            min_parameters: Minimum parameter count
            max_parameters: Maximum parameter count
            limit: Maximum results
            
        Returns:
            List of model summaries
        """
        models = await self.model_repo.search_models(
            query=query,
            architecture=architecture,
            min_parameters=min_parameters,
            max_parameters=max_parameters
        )
        
        results = []
        for model in models[:limit]:
            # Get quick stats
            latest_stats = None
            if model.versions:
                latest_version = model.versions[0]
                latest_stats = await self.benchmark_repo.get_aggregated_stats(
                    latest_version.id
                )
            
            results.append({
                'id': model.id,
                'name': model.name,
                'architecture': model.architecture,
                'parameters': model.parameters,
                'tags': model.tags,
                'version_count': len(model.versions) if hasattr(model, 'versions') else 0,
                'avg_accuracy': latest_stats.get('avg_accuracy') if latest_stats else None,
                'avg_throughput': latest_stats.get('avg_throughput') if latest_stats else None
            })
        
        return results

