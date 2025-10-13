"""Pareto optimization implementation for multi-objective optimization."""

from typing import List, Dict, Tuple
import numpy as np
from dataclasses import dataclass

from src.core.exceptions import TOPSISCalculationError


@dataclass
class Objective:
    """Represents an objective for Pareto optimization."""
    name: str
    is_maximize: bool  # True to maximize, False to minimize


class ParetoOptimizer:
    """Pareto optimization for multi-objective decision making."""
    
    def __init__(self, objectives: List[Objective]):
        """Initialize Pareto optimizer with objectives."""
        self.objectives = {obj.name: obj for obj in objectives}
    
    def find_pareto_front(
        self, 
        alternatives: List[Dict[str, float]]
    ) -> List[Tuple[Dict[str, float], float]]:
        """
        Find Pareto-optimal solutions.
        
        Args:
            alternatives: List of alternative dictionaries with objective values
            
        Returns:
            List of Pareto-optimal alternatives with their dominance score
        """
        if not alternatives:
            return []
        
        # Convert to numpy array
        objective_names = list(self.objectives.keys())
        matrix = np.array([
            [alt.get(obj_name, 0.0) for obj_name in objective_names]
            for alt in alternatives
        ])
        
        # Find non-dominated solutions
        pareto_indices = self._find_non_dominated_indices(matrix, objective_names)
        
        # Calculate dominance scores (number of solutions dominated)
        dominance_scores = self._calculate_dominance_scores(matrix, objective_names)
        
        # Return Pareto-optimal solutions with dominance scores
        results = [
            (alternatives[i], dominance_scores[i]) 
            for i in pareto_indices
        ]
        
        # Sort by dominance score descending
        return sorted(results, key=lambda x: x[1], reverse=True)
    
    def _find_non_dominated_indices(
        self, 
        matrix: np.ndarray, 
        objective_names: List[str]
    ) -> List[int]:
        """Find indices of non-dominated solutions."""
        n_solutions = matrix.shape[0]
        non_dominated = []
        
        for i in range(n_solutions):
            is_dominated = False
            for j in range(n_solutions):
                if i != j and self._dominates(matrix[j], matrix[i], objective_names):
                    is_dominated = True
                    break
            
            if not is_dominated:
                non_dominated.append(i)
        
        return non_dominated
    
    def _dominates(
        self, 
        solution1: np.ndarray, 
        solution2: np.ndarray, 
        objective_names: List[str]
    ) -> bool:
        """Check if solution1 dominates solution2."""
        better_in_at_least_one = False
        
        for i, obj_name in enumerate(objective_names):
            objective = self.objectives[obj_name]
            
            if objective.is_maximize:
                # For maximization objectives
                if solution1[i] < solution2[i]:
                    return False  # solution1 is worse in this objective
                elif solution1[i] > solution2[i]:
                    better_in_at_least_one = True
            else:
                # For minimization objectives
                if solution1[i] > solution2[i]:
                    return False  # solution1 is worse in this objective
                elif solution1[i] < solution2[i]:
                    better_in_at_least_one = True
        
        return better_in_at_least_one
    
    def _calculate_dominance_scores(
        self, 
        matrix: np.ndarray, 
        objective_names: List[str]
    ) -> np.ndarray:
        """Calculate dominance scores for all solutions."""
        n_solutions = matrix.shape[0]
        scores = np.zeros(n_solutions)
        
        for i in range(n_solutions):
            for j in range(n_solutions):
                if i != j and self._dominates(matrix[i], matrix[j], objective_names):
                    scores[i] += 1
        
        return scores
