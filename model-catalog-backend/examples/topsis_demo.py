"""Demo script for TOPSIS algorithm - standalone example."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from src.services.ranking.topsis import calculate_topsis_scores


def main():
    """Run TOPSIS algorithm demo with realistic model selection example."""
    
    print("=" * 80)
    print("TOPSIS Algorithm Demo - LLM Model Selection")
    print("=" * 80)
    print()
    
    # Create realistic benchmark data for LLM models
    data = pd.DataFrame({
        'model': ['Llama-3.1-7B', 'GPT-3.5-Turbo', 'Mistral-7B-v0.3', 'Claude-2', 'Qwen2.5-7B'],
        'accuracy': [0.82, 0.88, 0.85, 0.90, 0.87],
        'ttft_p90_ms': [120, 180, 100, 200, 110],      # Time to first token (lower better)
        'throughput': [450, 380, 500, 350, 470],       # tokens/sec (higher better)
        'cost_per_hour': [8, 15, 7, 18, 9],            # USD (lower better)
        'vram_gb': [14, 16, 13, 20, 15]                # VRAM required (lower better for cost)
    })
    
    print("📊 Input Data:")
    print(data.to_string(index=False))
    print()
    
    # Define criteria weights (must sum to 1.0)
    weights = {
        'accuracy': 0.30,       # 30% - Model quality
        'ttft_p90_ms': 0.25,   # 25% - Latency
        'throughput': 0.25,     # 25% - Speed
        'cost_per_hour': 0.15,  # 15% - Cost
        'vram_gb': 0.05        # 5%  - Hardware requirements
    }
    
    print("⚖️  Criteria Weights:")
    for criterion, weight in weights.items():
        print(f"  - {criterion:15s}: {weight:.1%}")
    print(f"  {'Total':15s}: {sum(weights.values()):.1%}")
    print()
    
    # Define criteria types
    benefit_criteria = ['accuracy', 'throughput']  # Higher is better
    cost_criteria = ['ttft_p90_ms', 'cost_per_hour', 'vram_gb']  # Lower is better
    
    print("📈 Benefit Criteria (higher is better):", benefit_criteria)
    print("📉 Cost Criteria (lower is better):", cost_criteria)
    print()
    
    # Calculate TOPSIS scores
    print("🔄 Calculating TOPSIS scores...")
    result = calculate_topsis_scores(
        data, 
        weights, 
        benefit_criteria, 
        cost_criteria
    )
    
    # Sort by rank
    result_sorted = result.sort_values('topsis_rank')
    
    print()
    print("=" * 80)
    print("🏆 RESULTS - Ranked Models")
    print("=" * 80)
    print()
    
    # Display results with formatting
    display_cols = ['topsis_rank', 'model', 'topsis_score', 'accuracy', 'ttft_p90_ms', 'throughput', 'cost_per_hour']
    result_display = result_sorted[display_cols].copy()
    result_display['topsis_score'] = result_display['topsis_score'].round(4)
    
    print(result_display.to_string(index=False))
    print()
    
    # Highlight top 3
    print("🥇 Top 3 Recommended Models:")
    for i, row in result_sorted.head(3).iterrows():
        rank_emoji = ['🥇', '🥈', '🥉'][int(row['topsis_rank']) - 1]
        print(f"{rank_emoji} Rank {int(row['topsis_rank'])}: {row['model']}")
        print(f"   Score: {row['topsis_score']:.4f}")
        print(f"   Accuracy: {row['accuracy']:.2f} | Latency: {row['ttft_p90_ms']:.0f}ms | "
              f"Throughput: {row['throughput']:.0f} tok/s | Cost: ${row['cost_per_hour']:.0f}/hr")
        print()
    
    # Analysis
    print("=" * 80)
    print("📝 Analysis:")
    print("=" * 80)
    best_model = result_sorted.iloc[0]
    print(f"✅ Best Model: {best_model['model']}")
    print(f"   - Balances all criteria optimally with score {best_model['topsis_score']:.4f}")
    print(f"   - Good accuracy ({best_model['accuracy']:.2f}), low latency ({best_model['ttft_p90_ms']:.0f}ms),")
    print(f"     high throughput ({best_model['throughput']:.0f} tok/s), and reasonable cost (${best_model['cost_per_hour']:.0f}/hr)")
    print()
    
    worst_model = result_sorted.iloc[-1]
    print(f"⚠️  Lowest Ranked: {worst_model['model']}")
    print(f"   - Score: {worst_model['topsis_score']:.4f}")
    print(f"   - Likely penalized by high cost (${worst_model['cost_per_hour']:.0f}/hr) and/or latency ({worst_model['ttft_p90_ms']:.0f}ms)")
    print()
    
    print("=" * 80)
    print("✨ TOPSIS Demo Complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()

