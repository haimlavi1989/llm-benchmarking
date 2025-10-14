"""TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) implementation.

Pure function implementation - NO external project dependencies.
Only numpy and pandas required.

Example:
    >>> import pandas as pd
    >>> data = pd.DataFrame({
    ...     'accuracy': [0.85, 0.90, 0.88],
    ...     'latency': [100, 150, 120],
    ...     'throughput': [500, 450, 480],
    ...     'cost': [10, 15, 12]
    ... })
    >>> weights = {
    ...     'accuracy': 0.3,
    ...     'latency': 0.25,
    ...     'throughput': 0.25,
    ...     'cost': 0.2
    ... }
    >>> benefit_criteria = ['accuracy', 'throughput']  # Higher is better
    >>> cost_criteria = ['latency', 'cost']  # Lower is better
    >>> 
    >>> result = calculate_topsis_scores(data, weights, benefit_criteria, cost_criteria)
    >>> print(result[['accuracy', 'latency', 'score']].round(3))
"""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd


def calculate_topsis_scores(
    data: pd.DataFrame,
    weights: Dict[str, float],
    benefit_criteria: Optional[List[str]] = None,
    cost_criteria: Optional[List[str]] = None
) -> pd.DataFrame:
    """Calculate TOPSIS scores for multi-criteria decision making.
    
    TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) ranks
    alternatives based on their similarity to the ideal solution and distance from
    the anti-ideal solution.
    
    Args:
        data: DataFrame with criteria columns (e.g., accuracy, latency, throughput, cost)
        weights: Dictionary mapping criteria names to their weights (must sum to 1.0)
        benefit_criteria: List of criteria where higher is better (default: all)
        cost_criteria: List of criteria where lower is better (default: none)
    
    Returns:
        Original DataFrame with added 'topsis_score' column (0-1, higher is better)
        and 'topsis_rank' column (1 = best)
    
    Raises:
        ValueError: If weights don't sum to 1.0 or criteria are invalid
    
    Example:
        >>> data = pd.DataFrame({
        ...     'model': ['Model A', 'Model B', 'Model C'],
        ...     'accuracy': [0.85, 0.90, 0.88],
        ...     'latency': [100, 150, 120],
        ...     'throughput': [500, 450, 480],
        ...     'cost': [10, 15, 12]
        ... })
        >>> weights = {'accuracy': 0.3, 'latency': 0.25, 'throughput': 0.25, 'cost': 0.2}
        >>> result = calculate_topsis_scores(
        ...     data, 
        ...     weights, 
        ...     benefit_criteria=['accuracy', 'throughput'],
        ...     cost_criteria=['latency', 'cost']
        ... )
        >>> print(result.sort_values('topsis_rank'))
    """
    # Validate inputs
    _validate_inputs(data, weights, benefit_criteria, cost_criteria)
    
    # Extract criteria columns
    criteria_cols = list(weights.keys())
    decision_matrix = data[criteria_cols].values
    
    # Default: all criteria are benefit unless specified in cost_criteria
    if benefit_criteria is None and cost_criteria is None:
        benefit_criteria = criteria_cols
        cost_criteria = []
    elif benefit_criteria is None:
        benefit_criteria = [c for c in criteria_cols if c not in (cost_criteria or [])]
    elif cost_criteria is None:
        cost_criteria = [c for c in criteria_cols if c not in (benefit_criteria or [])]
    
    # Step 1: Normalize the decision matrix (vector normalization)
    normalized_matrix = _normalize_matrix(decision_matrix)
    
    # Step 2: Calculate weighted normalized matrix
    weight_array = np.array([weights[col] for col in criteria_cols])
    weighted_matrix = normalized_matrix * weight_array
    
    # Step 3: Determine ideal and anti-ideal solutions
    ideal_solution, anti_ideal_solution = _calculate_ideal_solutions(
        weighted_matrix, criteria_cols, benefit_criteria, cost_criteria
    )
    
    # Step 4: Calculate Euclidean distances
    ideal_distances = np.sqrt(np.sum((weighted_matrix - ideal_solution) ** 2, axis=1))
    anti_ideal_distances = np.sqrt(np.sum((weighted_matrix - anti_ideal_solution) ** 2, axis=1))
    
    # Step 5: Calculate relative closeness (TOPSIS score)
    # Handle edge case where both distances are 0
    with np.errstate(divide='ignore', invalid='ignore'):
        scores = anti_ideal_distances / (ideal_distances + anti_ideal_distances)
        scores = np.nan_to_num(scores, nan=0.5)  # If equal distances, score = 0.5
    
    # Add scores to dataframe
    result = data.copy()
    result['topsis_score'] = scores
    result['topsis_rank'] = result['topsis_score'].rank(ascending=False, method='min').astype(int)
    
    return result


def _validate_inputs(
    data: pd.DataFrame,
    weights: Dict[str, float],
    benefit_criteria: Optional[List[str]],
    cost_criteria: Optional[List[str]]
) -> None:
    """Validate TOPSIS inputs."""
    # Check weights sum to 1.0
    total_weight = sum(weights.values())
    if not np.isclose(total_weight, 1.0, atol=1e-6):
        raise ValueError(f"Weights must sum to 1.0, got {total_weight:.6f}")
    
    # Check all weight keys exist in dataframe
    missing_cols = set(weights.keys()) - set(data.columns)
    if missing_cols:
        raise ValueError(f"Criteria columns not found in DataFrame: {missing_cols}")
    
    # Check benefit and cost criteria are valid
    if benefit_criteria:
        invalid_benefit = set(benefit_criteria) - set(weights.keys())
        if invalid_benefit:
            raise ValueError(f"Invalid benefit criteria: {invalid_benefit}")
    
    if cost_criteria:
        invalid_cost = set(cost_criteria) - set(weights.keys())
        if invalid_cost:
            raise ValueError(f"Invalid cost criteria: {invalid_cost}")
    
    # Check for overlapping benefit and cost criteria
    if benefit_criteria and cost_criteria:
        overlap = set(benefit_criteria) & set(cost_criteria)
        if overlap:
            raise ValueError(f"Criteria cannot be both benefit and cost: {overlap}")


def _normalize_matrix(matrix: np.ndarray) -> np.ndarray:
    """Normalize decision matrix using vector normalization.
    
    For each column j: normalized_value = value / sqrt(sum of squares)
    """
    # Calculate norm for each column
    column_norms = np.sqrt(np.sum(matrix ** 2, axis=0))
    
    # Avoid division by zero
    column_norms[column_norms == 0] = 1
    
    return matrix / column_norms


def _calculate_ideal_solutions(
    weighted_matrix: np.ndarray,
    criteria_names: List[str],
    benefit_criteria: List[str],
    cost_criteria: List[str]
) -> tuple[np.ndarray, np.ndarray]:
    """Calculate ideal (best) and anti-ideal (worst) solutions.
    
    For benefit criteria: ideal = max, anti-ideal = min
    For cost criteria: ideal = min, anti-ideal = max
    """
    n_criteria = len(criteria_names)
    ideal_solution = np.zeros(n_criteria)
    anti_ideal_solution = np.zeros(n_criteria)
    
    for i, criterion in enumerate(criteria_names):
        column_values = weighted_matrix[:, i]
        
        if criterion in benefit_criteria:
            # Benefit criterion: higher is better
            ideal_solution[i] = np.max(column_values)
            anti_ideal_solution[i] = np.min(column_values)
        else:
            # Cost criterion: lower is better
            ideal_solution[i] = np.min(column_values)
            anti_ideal_solution[i] = np.max(column_values)
    
    return ideal_solution, anti_ideal_solution
