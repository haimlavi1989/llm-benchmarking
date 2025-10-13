"""TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) implementation."""

from typing import Dict, List, Tuple
import numpy as np
from dataclasses import dataclass

from src.core.exceptions import TOPSISCalculationError


@dataclass
class CriteriaWeight:
    """Represents a criteria weight for TOPSIS calculation."""
    name: str
    weight: float
    is_benefit: bool  # True for benefit criteria (higher is better), False for cost criteria


class TOPSISRanker:
    """TOPSIS algorithm implementation for multi-criteria decision making."""
    
    def __init__(self, criteria_weights: List[CriteriaWeight]):
        """Initialize TOPSIS ranker with criteria weights."""
        self.criteria_weights = {c.name: c for c in criteria_weights}
        self._validate_weights()
    
    def _validate_weights(self) -> None:
        """Validate that weights sum to 1.0."""
        total_weight = sum(c.weight for c in self.criteria_weights.values())
        if not np.isclose(total_weight, 1.0, atol=1e-6):
            raise TOPSISCalculationError(
                f"Weights must sum to 1.0, got {total_weight}"
            )
    
    def calculate_scores(
        self, 
        alternatives: List[Dict[str, float]]
    ) -> List[Tuple[Dict[str, float], float]]:
        """
        Calculate TOPSIS scores for alternatives.
        
        Args:
            alternatives: List of alternative dictionaries with criteria values
            
        Returns:
            List of tuples (alternative, score) sorted by score descending
        """
        if not alternatives:
            return []
        
        # Convert to numpy array for calculations
        criteria_names = list(self.criteria_weights.keys())
        matrix = np.array([
            [alt.get(criteria, 0.0) for criteria in criteria_names]
            for alt in alternatives
        ])
        
        # Step 1: Normalize the decision matrix
        normalized_matrix = self._normalize_matrix(matrix)
        
        # Step 2: Calculate weighted normalized matrix
        weights = np.array([self.criteria_weights[name].weight for name in criteria_names])
        weighted_matrix = normalized_matrix * weights
        
        # Step 3: Determine ideal and anti-ideal solutions
        ideal_solution, anti_ideal_solution = self._calculate_ideal_solutions(
            weighted_matrix, criteria_names
        )
        
        # Step 4: Calculate distances to ideal and anti-ideal solutions
        ideal_distances = np.sqrt(np.sum((weighted_matrix - ideal_solution) ** 2, axis=1))
        anti_ideal_distances = np.sqrt(np.sum((weighted_matrix - anti_ideal_solution) ** 2, axis=1))
        
        # Step 5: Calculate relative closeness to ideal solution
        scores = anti_ideal_distances / (ideal_distances + anti_ideal_distances)
        
        # Return alternatives with scores, sorted by score descending
        results = list(zip(alternatives, scores))
        return sorted(results, key=lambda x: x[1], reverse=True)
    
    def _normalize_matrix(self, matrix: np.ndarray) -> np.ndarray:
        """Normalize the decision matrix using vector normalization."""
        # Calculate the norm for each column
        norms = np.sqrt(np.sum(matrix ** 2, axis=0))
        # Avoid division by zero
        norms[norms == 0] = 1
        return matrix / norms
    
    def _calculate_ideal_solutions(
        self, 
        weighted_matrix: np.ndarray, 
        criteria_names: List[str]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate ideal and anti-ideal solutions."""
        ideal_solution = np.zeros(len(criteria_names))
        anti_ideal_solution = np.zeros(len(criteria_names))
        
        for i, criteria_name in enumerate(criteria_names):
            criteria = self.criteria_weights[criteria_name]
            column = weighted_matrix[:, i]
            
            if criteria.is_benefit:
                # For benefit criteria, higher is better
                ideal_solution[i] = np.max(column)
                anti_ideal_solution[i] = np.min(column)
            else:
                # For cost criteria, lower is better
                ideal_solution[i] = np.min(column)
                anti_ideal_solution[i] = np.max(column)
        
        return ideal_solution, anti_ideal_solution
