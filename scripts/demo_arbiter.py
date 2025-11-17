import numpy as np
import sys
import os
from typing import List, Tuple

# --- FIX ---
# Get the project root directory (one level up from 'scripts')
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Add the 'src' directory (where 'models' lives) to the Python path
src_path = os.path.join(project_root, 'src')
sys.path.append(src_path)
# --- END FIX ---

from models.arbiter import TensorPowerArbiter
from models.pareto import get_pareto_solutions

def create_mock_tensor() -> Tuple[np.ndarray, List[str], List[str], List[str]]:
    """
    Creates a mock Tensor T[p, m, s] for demonstration.
    
    Plans (P=4):
    - P0: Balanced
    - P1: High Revenue, High Energy
    - P2: Low Energy, Low Revenue
    - P3: High Safety, Low Revenue
    
    Metrics (M=4):
    - M0: revenue_$
    - M1: energy_J (Landauer-context)
    - M2: safety_risk
    - M3: latency_ms
    
    Segments (S=2):
    - S0: Enterprise (High Revenue)
    - S1: Free Tier (High Latency concern)
    """
    
    plan_names = ["P0: Balanced", "P1: High-Rev/High-Energy", "P2: Low-Energy/Low-Rev", "P3: High-Safety/Low-Rev"]
    metric_names = ["revenue", "energy_J", "safety", "latency"]
    segment_names = ["Enterprise", "Free Tier"]

    num_p, num_m, num_s = len(plan_names), len(metric_names), len(segment_names)
    
    # T is normalized so 1.0 is GOOD and 0.0 is BAD.
    # For cost metrics (energy, safety, latency), score = 1.0 - normalized_cost
    T = np.zeros((num_p, num_m, num_s))

    # --- S0: Enterprise Segment ---
    # P0 (Balanced)
    T[0, :, 0] = [0.7, 0.7, 0.7, 0.7] # [rev, nrg, safe, lat]
    # P1 (High-Rev/High-Energy)
    T[1, :, 0] = [1.0, 0.1, 0.5, 0.5] # Good rev, BAD energy
    # P2 (Low-Energy/Low-Rev)
    T[2, :, 0] = [0.2, 1.0, 0.8, 0.8] # Bad rev, GOOD energy
    # P3 (High-Safety/Low-Rev)
    T[3, :, 0] = [0.3, 0.8, 1.0, 0.6] # Bad rev, GOOD safety

    # --- S1: Free Tier Segment ---
    # P0 (Balanced)
    T[0, :, 1] = [0.6, 0.7, 0.7, 0.7] # [rev, nrg, safe, lat]
    # P1 (High-Rev/High-Energy)
    T[1, :, 1] = [0.8, 0.1, 0.5, 0.2] # Good rev, BAD energy, BAD latency
    # P2 (Low-Energy/Low-Rev)
    T[2, :, 1] = [0.1, 1.0, 0.8, 1.0] # Bad rev, GOOD energy, GOOD latency
    # P3 (High-Safety/Low-Rev)
    T[3, :, 1] = [0.2, 0.8, 1.0, 0.8] # Bad rev, GOOD safety
    
    # This is the BBS (Black-Box Substrate) in action:
    # Let's override P2's energy score for Enterprise with a "real" (non-simulated) value
    # T[2, 1, 0] = 1.0 (simulated) -> 0.9 (real)
    T[2, 1, 0] = 0.9
    print("BBS: Overwrote T[P2, energy, Enterprise] with 'real' data (1.0 -> 0.9)")
    
    return T, plan_names, metric_names, segment_names

def run_pareto_demo(T: np.ndarray, plan_names: List[str]):
    """Demonstrates the Pareto functions."""
    print("\n--- Running Pareto Optimization Demo (Enterprise Segment) ---")
    
    # We want to MAXIMIZE revenue and MINIMIZE energy_J cost.
    # Our T tensor is "goodness" (1=good).
    # We convert to "cost" (0=good) for minimization.
    # costs = [1 - revenue, 1 - energy_goodness]
    
    costs = np.zeros((T.shape[0], 2))
    costs[:, 0] = 1.0 - T[:, 0, 0] # 1 - revenue
    costs[:, 1] = 1.0 - T[:, 1, 0] # 1 - energy_goodness (aka energy_cost)
    
    print("Costs (to be minimized): [1-Revenue, 1-Energy]")
    for i, p in enumerate(plan_names):
        print(f"  {p}: {costs[i]}")
        
    pareto_indices, knee_index = get_pareto_solutions(costs)
    
    print("\nPareto Efficient Plans:")
    for idx in pareto_indices:
        print(f"  -> {plan_names[idx]}")
        
    print(f"\nRecommended 'Knee' Plan: {plan_names[knee_index]}")

def main():
    T, p_names, m_names, s_names = create_mock_tensor()
    
    ENERGY_METRIC_INDEX = m_names.index("energy_J")

    # --- Scenario 1: No Energy Penalty ---
    # We only care about revenue (M0) and safety (M2)
    metric_weights = {0: 1.0, 2: 0.5} 
    # We only care about Enterprise (S0)
    segment_weights = {0: 1.0}

    arbiter_no_penalty = TensorPowerArbiter(T, metric_weights, segment_weights)
    v_p_no_penalty = arbiter_no_penalty.run_arbitration(
        iterations=10, 
        energy_metric_index=ENERGY_METRIC_INDEX, 
        energy_penalty=0.0 # No penalty
    )
    
    print("\n--- Results (No Energy Penalty) ---")
    results_no_penalty = sorted(zip(p_names, v_p_no_penalty), key=lambda x: x[1], reverse=True)
    for name, score in results_no_penalty:
        print(f"  {name}: {score:.4f}")
    
    # --- Scenario 2: With Landauer-Context Energy Penalty ---
    # Same initial weights, but we apply a heavy penalty
    
    arbiter_with_penalty = TensorPowerArbiter(T, metric_weights, segment_weights)
    v_p_with_penalty = arbiter_with_penalty.run_arbitration(
        iterations=10, 
        energy_metric_index=ENERGY_METRIC_INDEX, 
        energy_penalty=5.0 # High penalty
    )
    
    print("\n--- Results (WITH Landauer-Context Penalty) ---")
    results_with_penalty = sorted(zip(p_names, v_p_with_penalty), key=lambda x: x[1], reverse=True)
    for name, score in results_with_penalty:
        print(f"  {name}: {score:.4f}")
        
    # --- Final Check ---
    print("\n--- Comparison ---")
    print(f"Top Plan (No Penalty):   {results_no_penalty[0][0]}")
    print(f"Top Plan (With Penalty): {results_with_penalty[0][0]}")
    
    # --- Pareto Demo ---
    run_pareto_demo(T, p_names)

if __name__ == "__main__":
    main()
