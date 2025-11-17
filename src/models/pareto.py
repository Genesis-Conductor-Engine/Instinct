import numpy as np
from typing import List, Tuple

def is_pareto_efficient(costs: np.ndarray) -> np.ndarray:
    """
    Find the Pareto-efficient points.
    Assumes all costs are to be minimized.

    Args:
        costs (np.ndarray): An (n_points, n_costs) array.

    Returns:
        np.ndarray: A (n_points,) boolean array indicating if
                    each point is Pareto efficient.
    """
    is_efficient = np.ones(costs.shape[0], dtype=bool)
    for i, c in enumerate(costs):
        if is_efficient[i]:
            # Keep i as efficient until proven otherwise
            # Find all points dominated by c
            dominated = np.all(costs[is_efficient] >= c, axis=1)
            # Find all points that dominate c
            dominating = np.all(costs[is_efficient] <= c, axis=1)
            
            # Combine dominated and dominating, excluding i itself
            is_efficient[is_efficient] = np.logical_not(np.logical_and(dominated, np.logical_not(dominating)))
            is_efficient[i] = True # Point i is efficient
            
    # Re-check for any dominated points
    for i, c in enumerate(costs):
        if is_efficient[i]:
            # Check if any *other* efficient point dominates i
            other_efficient = np.delete(costs[is_efficient], i, axis=0)
            if np.any(np.all(other_efficient <= c, axis=1)):
                is_efficient[i] = False
                
    # Final pass: A point is non-dominated if no other point is better or equal in all objectives
    is_efficient = np.ones(costs.shape[0], dtype=bool)
    for i, c in enumerate(costs):
        # Find if any other point dominates c
        # A point 'j' dominates 'i' if it's strictly better in at least one obj
        # and no worse in all other obj.
        is_dominated = np.any(
            np.all(costs[~np.eye(costs.shape[0], dtype=bool)[i]] <= c, axis=1) & 
            np.any(costs[~np.eye(costs.shape[0], dtype=bool)[i]] < c, axis=1)
        )
        if is_dominated:
            is_efficient[i] = False
            
    return is_efficient

def find_pareto_knee(pareto_costs: np.ndarray) -> int:
    """
    Finds the 'knee' of the Pareto frontier using the Utopian distance method.
    Assumes costs are to be minimized.

    Args:
        pareto_costs (np.ndarray): An (n_pareto_points, n_costs) array.

    Returns:
        int: The index (relative to the input array) of the knee point.
    """
    if pareto_costs.ndim == 1:
        return np.argmin(pareto_costs)
    if len(pareto_costs) == 0:
        return -1

    # Normalize the costs to a [0, 1] range
    normalized_costs = (pareto_costs - np.min(pareto_costs, axis=0)) / (
        np.max(pareto_costs, axis=0) - np.min(pareto_costs, axis=0) + 1e-9
    )
    
    # Utopian point is (0, 0, ... 0) in normalized space
    utopian_point = np.zeros(normalized_costs.shape[1])
    
    # Calculate Euclidean distance to the Utopian point
    distances = np.linalg.norm(normalized_costs - utopian_point, axis=1)
    
    # The knee is the point with the minimum distance
    knee_index = np.argmin(distances)
    
    return knee_index

def get_pareto_solutions(costs: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Gets all Pareto efficient solutions and identifies the knee point.

    Args:
        costs (np.ndarray): (n_points, n_costs) array. Costs are to be minimized.

    Returns:
        Tuple[np.ndarray, np.ndarray]:
            - pareto_indices: Indices of the Pareto efficient points.
            - knee_index: The single index of the knee point.
    """
    pareto_mask = is_pareto_efficient(costs)
    pareto_indices = np.where(pareto_mask)[0]
    
    if not pareto_indices.any():
        return np.array([]), -1
        
    pareto_costs = costs[pareto_mask]
    
    # Find the knee *among* the Pareto points
    knee_index_in_pareto_set = find_pareto_knee(pareto_costs)
    
    if knee_index_in_pareto_set == -1:
        return pareto_indices, -1

    # Map back to the original index
    knee_index = pareto_indices[knee_index_in_pareto_set]
    
    return pareto_indices, knee_index
