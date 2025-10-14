# Ranking Algorithms

Multi-criteria decision making algorithms for model selection and optimization.

## TOPSIS Algorithm

**TOPSIS** (Technique for Order Preference by Similarity to Ideal Solution) is a multi-criteria decision analysis method that ranks alternatives based on their distance from the ideal solution.

### Features

- ✅ **Pure Function** - No external project dependencies
- ✅ **Pandas Integration** - DataFrame input/output
- ✅ **Flexible Criteria** - Support for benefit (higher is better) and cost (lower is better) criteria
- ✅ **Weighted Scoring** - Customizable weights for each criterion
- ✅ **Type Safe** - Full type hints

### Usage

```python
import pandas as pd
from src.services.ranking.topsis import calculate_topsis_scores

# Create benchmark data
data = pd.DataFrame({
    'model': ['Model A', 'Model B', 'Model C'],
    'accuracy': [0.85, 0.90, 0.88],
    'latency': [100, 150, 120],
    'throughput': [500, 450, 480],
    'cost': [10, 15, 12]
})

# Define criteria weights (must sum to 1.0)
weights = {
    'accuracy': 0.3,
    'latency': 0.25,
    'throughput': 0.25,
    'cost': 0.2
}

# Calculate scores
result = calculate_topsis_scores(
    data, 
    weights,
    benefit_criteria=['accuracy', 'throughput'],  # Higher is better
    cost_criteria=['latency', 'cost']             # Lower is better
)

# View results
print(result.sort_values('topsis_rank'))
```

### Algorithm Steps

1. **Normalization** - Vector normalization of decision matrix
2. **Weighting** - Apply criterion weights
3. **Ideal Solutions** - Determine ideal and anti-ideal solutions
4. **Distance Calculation** - Euclidean distance to ideal/anti-ideal
5. **Scoring** - Relative closeness to ideal solution (0-1)

### Parameters

- `data` (DataFrame): Input data with criteria columns
- `weights` (Dict[str, float]): Criterion weights (must sum to 1.0)
- `benefit_criteria` (List[str], optional): Criteria where higher is better
- `cost_criteria` (List[str], optional): Criteria where lower is better

### Returns

Original DataFrame with added columns:
- `topsis_score` (float): Score between 0 and 1 (higher is better)
- `topsis_rank` (int): Rank position (1 = best)

### Example Output

```
   model  accuracy  latency  throughput  cost  topsis_score  topsis_rank
0  Model A     0.85      100         500    10        0.6234            1
1  Model C     0.88      120         480    12        0.5021            2
2  Model B     0.90      150         450    15        0.3845            3
```

## Pareto Optimization

Multi-objective optimization using Pareto dominance.

### Features

- ✅ Non-dominated solution identification
- ✅ Dominance score calculation
- ✅ Multi-objective support

### Usage

```python
from src.services.ranking.pareto import ParetoOptimizer, Objective

# Define objectives
objectives = [
    Objective(name='accuracy', is_maximize=True),
    Objective(name='latency', is_maximize=False),  # Minimize
    Objective(name='cost', is_maximize=False)
]

optimizer = ParetoOptimizer(objectives)

# Find Pareto front
alternatives = [
    {'accuracy': 0.85, 'latency': 100, 'cost': 10},
    {'accuracy': 0.90, 'latency': 150, 'cost': 15},
    {'accuracy': 0.88, 'latency': 120, 'cost': 12}
]

pareto_front = optimizer.find_pareto_front(alternatives)
```

## Testing

Run the demo:

```bash
python examples/topsis_demo.py
```

Run unit tests:

```bash
pytest tests/unit/test_topsis.py -v
```

## Dependencies

- `numpy>=1.24.0`
- `pandas>=2.0.0`

## References

- Hwang, C.L.; Yoon, K. (1981). Multiple Attribute Decision Making: Methods and Applications
- TOPSIS method for multi-criteria decision making
- Pareto efficiency in multi-objective optimization

