"""Tests for TOPSIS algorithm implementation."""

import pytest
import pandas as pd
import numpy as np
from src.services.ranking.topsis import calculate_topsis_scores


class TestTOPSIS:
    """Test suite for TOPSIS algorithm."""
    
    def test_simple_example(self):
        """Test TOPSIS with a simple 3-alternative example."""
        # Create test data
        data = pd.DataFrame({
            'model': ['Model A', 'Model B', 'Model C'],
            'accuracy': [0.85, 0.90, 0.88],
            'latency': [100, 150, 120],
            'throughput': [500, 450, 480],
            'cost': [10, 15, 12]
        })
        
        # Define weights (must sum to 1.0)
        weights = {
            'accuracy': 0.3,
            'latency': 0.25,
            'throughput': 0.25,
            'cost': 0.2
        }
        
        # Define criteria types
        benefit_criteria = ['accuracy', 'throughput']  # Higher is better
        cost_criteria = ['latency', 'cost']  # Lower is better
        
        # Calculate TOPSIS scores
        result = calculate_topsis_scores(
            data, 
            weights, 
            benefit_criteria, 
            cost_criteria
        )
        
        # Assertions
        assert 'topsis_score' in result.columns
        assert 'topsis_rank' in result.columns
        assert len(result) == 3
        
        # Scores should be between 0 and 1
        assert (result['topsis_score'] >= 0).all()
        assert (result['topsis_score'] <= 1).all()
        
        # Ranks should be 1, 2, 3
        assert set(result['topsis_rank'].values) == {1, 2, 3}
        
        # Model A should have rank 1 (best balance: good accuracy, low latency, high throughput, low cost)
        best_model = result[result['topsis_rank'] == 1]['model'].values[0]
        assert best_model == 'Model A'
    
    def test_weights_sum_validation(self):
        """Test that weights must sum to 1.0."""
        data = pd.DataFrame({
            'accuracy': [0.85, 0.90],
            'latency': [100, 150]
        })
        
        # Weights that don't sum to 1.0
        weights = {
            'accuracy': 0.6,
            'latency': 0.5  # Sum = 1.1
        }
        
        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            calculate_topsis_scores(data, weights)
    
    def test_missing_criteria_columns(self):
        """Test error when weight keys are not in DataFrame."""
        data = pd.DataFrame({
            'accuracy': [0.85, 0.90],
            'latency': [100, 150]
        })
        
        weights = {
            'accuracy': 0.5,
            'throughput': 0.5  # This column doesn't exist
        }
        
        with pytest.raises(ValueError, match="Criteria columns not found"):
            calculate_topsis_scores(data, weights)
    
    def test_all_benefit_criteria_default(self):
        """Test that all criteria are treated as benefit by default."""
        data = pd.DataFrame({
            'metric1': [10, 20, 15],
            'metric2': [5, 8, 6]
        })
        
        weights = {
            'metric1': 0.6,
            'metric2': 0.4
        }
        
        # Don't specify benefit/cost criteria
        result = calculate_topsis_scores(data, weights)
        
        # Alternative with highest values should win
        best_idx = result['topsis_rank'].idxmin()
        assert result.loc[best_idx, 'metric1'] == 20  # Highest metric1
        assert result.loc[best_idx, 'metric2'] == 8   # Highest metric2
    
    def test_cost_criteria_reversal(self):
        """Test that cost criteria are correctly treated (lower is better)."""
        data = pd.DataFrame({
            'benefit': [10, 20, 15],
            'cost': [100, 50, 75]  # Lower is better
        })
        
        weights = {
            'benefit': 0.5,
            'cost': 0.5
        }
        
        result = calculate_topsis_scores(
            data, 
            weights,
            benefit_criteria=['benefit'],
            cost_criteria=['cost']
        )
        
        # Alternative with high benefit and low cost should win
        best_idx = result['topsis_rank'].idxmin()
        assert result.loc[best_idx, 'benefit'] == 20  # Highest benefit
        assert result.loc[best_idx, 'cost'] == 50     # Lowest cost
    
    def test_identical_alternatives(self):
        """Test handling of identical alternatives."""
        data = pd.DataFrame({
            'metric1': [10, 10, 10],
            'metric2': [5, 5, 5]
        })
        
        weights = {
            'metric1': 0.5,
            'metric2': 0.5
        }
        
        result = calculate_topsis_scores(data, weights)
        
        # All alternatives should have same score
        assert np.allclose(result['topsis_score'].values, result['topsis_score'].values[0])
    
    def test_realistic_model_selection(self):
        """Test with realistic LLM model selection scenario."""
        data = pd.DataFrame({
            'model': ['Llama-7B', 'GPT-3.5', 'Mistral-7B', 'Claude-2'],
            'accuracy': [0.82, 0.88, 0.85, 0.90],
            'ttft_p90_ms': [120, 180, 100, 200],  # Time to first token (lower better)
            'throughput': [450, 380, 500, 350],    # tokens/sec (higher better)
            'cost_per_hour': [8, 15, 7, 18]        # USD (lower better)
        })
        
        weights = {
            'accuracy': 0.35,
            'ttft_p90_ms': 0.25,
            'throughput': 0.25,
            'cost_per_hour': 0.15
        }
        
        result = calculate_topsis_scores(
            data,
            weights,
            benefit_criteria=['accuracy', 'throughput'],
            cost_criteria=['ttft_p90_ms', 'cost_per_hour']
        )
        
        # Sort by rank
        result_sorted = result.sort_values('topsis_rank')
        
        # Mistral-7B should rank high: good accuracy, low latency, high throughput, low cost
        assert result_sorted.iloc[0]['model'] in ['Mistral-7B', 'Llama-7B']
        
        # Claude-2 should rank lower: high accuracy but expensive and slow
        assert result_sorted.iloc[-1]['model'] == 'Claude-2'
    
    def test_overlapping_criteria_error(self):
        """Test error when criteria is both benefit and cost."""
        data = pd.DataFrame({
            'accuracy': [0.85, 0.90],
            'latency': [100, 150]
        })
        
        weights = {
            'accuracy': 0.5,
            'latency': 0.5
        }
        
        with pytest.raises(ValueError, match="cannot be both benefit and cost"):
            calculate_topsis_scores(
                data,
                weights,
                benefit_criteria=['accuracy', 'latency'],
                cost_criteria=['latency']  # Latency in both lists
            )
    
    def test_score_range(self):
        """Test that TOPSIS scores are always between 0 and 1."""
        # Extreme values test
        data = pd.DataFrame({
            'metric1': [0.001, 100, 50],
            'metric2': [1000, 0.01, 500]
        })
        
        weights = {
            'metric1': 0.6,
            'metric2': 0.4
        }
        
        result = calculate_topsis_scores(data, weights)
        
        assert (result['topsis_score'] >= 0).all()
        assert (result['topsis_score'] <= 1).all()
    
    def test_single_alternative(self):
        """Test TOPSIS with single alternative."""
        data = pd.DataFrame({
            'accuracy': [0.85],
            'latency': [100]
        })
        
        weights = {
            'accuracy': 0.5,
            'latency': 0.5
        }
        
        result = calculate_topsis_scores(data, weights)
        
        # Single alternative should have rank 1
        assert result['topsis_rank'].values[0] == 1
        # Score should be 0.5 (equal distance to ideal and anti-ideal)
        assert np.isclose(result['topsis_score'].values[0], 0.5)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

