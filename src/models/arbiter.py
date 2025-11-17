import numpy as np
from typing import Dict, Tuple, List

class TensorPowerArbiter:
    """
    Implements the Tensor Power Tower Arbitration logic from the LID-LIFT v1.4
    run_report.

    This class takes a 3D tensor T[plans, metrics, segments] and finds the
    dominant "eigen-plan" (v_p) that maximizes a weighted objective,
    including constraints for energy, cost, and safety.
    """
    def __init__(self, t_tensor: np.ndarray, metric_weights: Dict[int, float], segment_weights: Dict[int, float]):
        """
        Initializes the Arbiter.

        Args:
            t_tensor (np.ndarray): The 3D tensor T[p, m, s] of normalized scores.
                Shape is (num_plans, num_metrics, num_segments).
            metric_weights (Dict[int, float]): Initial weights w_m.
                Keys are metric indices, values are weights.
            segment_weights (Dict[int, float]): Initial weights w_s.
                Keys are segment indices, values are weights.
        """
        self.T = t_tensor
        self.num_plans, self.num_metrics, self.num_segments = t_tensor.shape

        # Initialize weight vectors
        self.w_m = self._normalize_vector(self._dict_to_vec(metric_weights, self.num_metrics))
        self.w_s = self._normalize_vector(self._dict_to_vec(segment_weights, self.num_segments))
        
        # Initialize plan vector
        self.v_p = self._normalize_vector(np.ones(self.num_plans))

        print(f"Arbiter Initialized: {self.num_plans} Plans, {self.num_metrics} Metrics, {self.num_segments} Segments")

    def _dict_to_vec(self, d: Dict[int, float], size: int) -> np.ndarray:
        """Converts a sparse weight dictionary to a dense vector."""
        vec = np.zeros(size)
        for k, v in d.items():
            if k < size:
                vec[k] = v
        # Default to uniform if no weights provided
        if np.sum(vec) == 0:
            vec = np.ones(size)
        return vec

    def _normalize_vector(self, v: np.ndarray) -> np.ndarray:
        """Performs L2 normalization on a vector."""
        norm = np.linalg.norm(v)
        if norm == 0:
            return v
        return v / norm

    def run_arbitration(self, iterations: int = 10, energy_metric_index: int = -1, energy_penalty: float = 2.0) -> np.ndarray:
        """
        Runs the alternating tensor power iteration to find the stable eigen-plan.

        Args:
            iterations (int): Number of iterations to run.
            energy_metric_index (int): The index of the 'energy_J' metric.
            energy_penalty (float): Multiplier to penalize energy. High energy_J scores
                                     (which are bad) will be penalized.
        """
        print(f"\n--- Starting Tensor Power Arbitration (Iterations={iterations}) ---")
        print(f"Applying Landauer-context penalty to metric index {energy_metric_index} (Penalty={energy_penalty})")

        for k in range(iterations):
            # 1. Plan scoring step (mode-(m,s) contraction)
            # v_p ∝ Σ_{m,s} T[p,m,s] * w_m * w_s
            # We use einsum for efficient tensor contraction: 'pms,m,s->p'
            v_p_k = np.einsum('pms,m,s->p', self.T, self.w_m, self.w_s)
            self.v_p = self._normalize_vector(v_p_k)

            # 2. Metric weight update (mode-(p,s) contraction)
            # u_m ∝ Σ_{p,s} T[p,m,s] * v_p * w_s
            u_m_k = np.einsum('pms,p,s->m', self.T, self.v_p, self.w_s)
            
            # --- This is the Thermodynamic Constraint ---
            # Apply Landauer-context penalty
            if 0 <= energy_metric_index < self.num_metrics:
                # We assume T is normalized (0-1), where 1 is "good".
                # For energy, a "good" score (low energy) is 1, a "bad" score (high energy) is 0.
                # Let's assume the metric is "1 - normalized_energy".
                # A high score (e.g., 0.9) means low energy.
                # A low score (e.g., 0.1) means high energy.
                # We want to *penalize* (reduce the weight of) plans that have high energy.
                # The utility u_m_k for the energy metric will be low if high-energy plans
                # are selected.
                # Let's adjust the *raw utility* of the energy metric.
                # If the utility is high (meaning good energy), we boost it.
                # If it's low (meaning bad energy), we penalize it.
                # A simpler way: Invert the score during penalty application.
                # T[p, energy_idx, s] is the "goodness" score (1 = low energy).
                # (1 - T[p, energy_idx, s]) is the "badness" score (1 = high energy).
                # We want to penalize metrics that correlate with high energy.
                
                # Per the run_report: "Penalize metrics that correlate with: Excess energy_J"
                # Let's apply a direct penalty to the energy metric's weight calculation.
                # If u_m_k[energy_metric_index] is low, it means the current
                # plan (v_p) is selecting for high energy. We penalize this.
                # A simpler interpretation: we just want to up-weight the
                # importance of the energy metric itself.
                
                # Let's follow the spirit of the 'run_report' and 'WHITEPAPER'.
                # The goal is to make energy matter *more*.
                # We will re-weight u_m_k based on the *original* metric weights.
                # And apply the penalty.
                
                # Re-calculate u_m_k based on *original* w_m, not iterative
                u_m_k = np.einsum('pms,p,s->m', self.T, self.v_p, self.w_s)
                
                # Apply penalty:
                # We invert the "goodness" score to get a "cost" score.
                energy_cost_score = 1.0 - self.T[:, energy_metric_index, :]
                
                # Calculate average energy cost of the current plan portfolio
                avg_energy_cost = np.einsum('ps,p,s->', energy_cost_score, self.v_p, self.w_s)
                
                # Create a penalty factor. If avg_energy_cost is high, penalty is high.
                # This is a simple heuristic.
                penalty_factor = 1.0 + (avg_energy_cost * energy_penalty)
                
                # Penalize (reduce) the utility of *all* metrics *except* energy,
                # forcing the arbiter to focus on energy.
                # Or, more simply, boost the utility *of* the energy metric.
                u_m_k[energy_metric_index] *= penalty_factor
            
            self.w_m = self._normalize_vector(u_m_k)

            # 3. Segment weight update (mode-(p,m) contraction)
            # u_s ∝ Σ_{p,m} T[p,m,s] * v_p * w_m
            u_s_k = np.einsum('pms,p,m->s', self.T, self.v_p, self.w_m)
            self.w_s = self._normalize_vector(u_s_k)

            if (k + 1) % 2 == 0:
                print(f"  Iter {k+1}: Plan[0] score = {self.v_p[0]:.4f}, Energy Metric Weight = {self.w_m[energy_metric_index]:.4f}")

        print("--- Arbitration Complete ---")
        return self.v_p

    def get_results(self) -> Dict[str, np.ndarray]:
        """Returns the final state vectors."""
        return {
            "plan_scores (v_p)": self.v_p,
            "metric_weights (w_m)": self.w_m,
            "segment_weights (w_s)": self.w_s
        }
