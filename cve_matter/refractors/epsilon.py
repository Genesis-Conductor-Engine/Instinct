"""Epsilon refractor module for model refinement."""
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

try:
    import cupy as cp
    CUDA_AVAILABLE = True
except ImportError:
    CUDA_AVAILABLE = False


class EpsilonCalculator:
    """Calculate epsilon refraction values for model refinement.

    Epsilon values are used for sensitivity analysis and model stability
    assessment in vulnerability predictions. Supports GPU acceleration
    via CUDA when available. Defensive analysis only.
    """

    def __init__(self, config: dict[str, Any] | None = None, use_gpu: bool = False):
        """Initialize epsilon calculator with configuration.

        Args:
            config: Optional configuration dictionary
            use_gpu: Whether to use GPU acceleration (requires CUDA)
        """
        self.config = config or {}
        self.use_gpu = use_gpu and CUDA_AVAILABLE

        if use_gpu and not CUDA_AVAILABLE:
            print("Warning: CUDA not available, falling back to CPU", file=sys.stderr)
            self.use_gpu = False

    def compute_epsilon_sweep(self, input_path: Path,
                             epsilon_min: float = 0.001,
                             epsilon_max: float = 0.1,
                             n_steps: int = 20) -> dict[str, Any]:
        """Compute epsilon values across a range for sensitivity analysis.

        Args:
            input_path: Path to input JSON file with CVE data
            epsilon_min: Minimum epsilon value
            epsilon_max: Maximum epsilon value
            n_steps: Number of steps in the sweep

        Returns:
            Dictionary with epsilon sweep results
        """
        with open(input_path) as f:
            data = json.load(f)

        cves = data.get('cves', [])

        # Extract features
        features = self._extract_features(cves)

        if len(features) < 2:
            return {
                'status': 'insufficient_data',
                'message': 'Need at least 2 samples for epsilon calculation'
            }

        # Perform epsilon sweep
        result = self._sweep_epsilon(features, epsilon_min, epsilon_max, n_steps)

        return result

    def _extract_features(self, cves: list) -> np.ndarray:
        """Extract feature matrix from CVE records.

        Args:
            cves: List of CVE records

        Returns:
            NumPy array of features
        """
        features = []
        for cve in cves:
            feature_vec = [
                cve.get('cvss_score', 0.0),
                len(cve.get('references', [])),
                len(cve.get('description', '')),
            ]
            features.append(feature_vec)

        return np.array(features)

    def _sweep_epsilon(self, features: np.ndarray,
                      epsilon_min: float,
                      epsilon_max: float,
                      n_steps: int) -> dict[str, Any]:
        """Perform epsilon sweep calculations.

        Args:
            features: Feature matrix
            epsilon_min: Minimum epsilon value
            epsilon_max: Maximum epsilon value
            n_steps: Number of steps

        Returns:
            Epsilon sweep results
        """
        try:
            epsilon_values = np.linspace(epsilon_min, epsilon_max, n_steps)
            stability_scores = []
            variance_scores = []

            if self.use_gpu:
                features_gpu = cp.asarray(features)

            for epsilon in epsilon_values:
                # Compute stability metric using prediction variance under perturbation
                # Run multiple perturbations to measure consistency
                n_trials = 10
                perturbed_samples = []
                
                for _ in range(n_trials):
                    if self.use_gpu:
                        noise = cp.random.randn(*features_gpu.shape) * epsilon
                        perturbed = features_gpu + noise
                        perturbed_samples.append(cp.asnumpy(perturbed))
                    else:
                        noise = np.random.randn(*features.shape) * epsilon
                        perturbed = features + noise
                        perturbed_samples.append(perturbed)
                
                # Measure variance across perturbed samples (instability indicator)
                perturbed_array = np.array(perturbed_samples)
                variance = float(np.mean(np.var(perturbed_array, axis=0)))
                variance_scores.append(variance)
                
                # Normalized stability score (inverse of variance, normalized by epsilon)
                # Higher score = more stable
                stability = float(1.0 / (1.0 + variance / (epsilon + 1e-10)))
                stability_scores.append(stability)

            # Find optimal epsilon (highest stability score)
            optimal_idx = int(np.argmax(stability_scores))
            
            result = {
                'status': 'success',
                'epsilon_range': [float(epsilon_min), float(epsilon_max)],
                'n_steps': n_steps,
                'epsilon_values': epsilon_values.tolist(),
                'stability_scores': stability_scores,
                'variance_scores': variance_scores,
                'gpu_used': self.use_gpu,
                'optimal_epsilon': float(epsilon_values[optimal_idx]),
                'optimal_stability': float(stability_scores[optimal_idx]),
                'method': 'prediction_variance',
            }
        except Exception as e:
            result = {
                'status': 'error',
                'message': str(e)
            }

        return result

    def save_results(self, result: dict[str, Any], output_path: Path) -> None:
        """Save epsilon results to JSON file.

        Args:
            result: Epsilon calculation results
            output_path: Path to output file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
