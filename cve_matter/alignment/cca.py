"""Canonical Correlation Analysis (CCA) alignment module."""
import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.cross_decomposition import CCA


class CCAAlignment:
    """Perform Canonical Correlation Analysis for multivariate alignment.

    CCA finds linear combinations of features that maximize correlation
    between datasets. Useful for identifying common vulnerability patterns.
    Defensive analysis only.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize CCA alignment with configuration.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.n_components = self.config.get('alignment', {}).get('n_components', 2)

    def align_from_file(self, input_path: Path) -> dict[str, Any]:
        """Perform CCA alignment on CVE data from file.

        Args:
            input_path: Path to input JSON file with CVE data

        Returns:
            Dictionary with alignment results
        """
        with open(input_path) as f:
            data = json.load(f)

        cves = data.get('cves', [])

        # Extract feature matrices
        features = self._extract_features(cves)

        # Perform CCA alignment
        if len(features) >= 4:  # Need sufficient samples
            result = self._perform_cca(features)
        else:
            result = {
                'status': 'insufficient_data',
                'message': 'Need at least 4 data points for CCA'
            }

        return result

    def _extract_features(self, cves: list) -> np.ndarray:
        """Extract feature matrix from CVE records.

        Args:
            cves: List of CVE records

        Returns:
            NumPy array of features
        """
        # Deterministic mapping for severity levels
        severity_map = {'LOW': 0, 'MEDIUM': 25, 'HIGH': 50, 'CRITICAL': 75, 'NONE': -1}
        
        features = []
        for cve in cves:
            severity = cve.get('severity', '').upper()
            severity_value = severity_map.get(severity, -1)
            
            feature_vec = [
                cve.get('cvss_score', 0.0),
                len(cve.get('references', [])),
                len(cve.get('description', '')),
                severity_value,  # Deterministic categorical encoding
            ]
            features.append(feature_vec)

        return np.array(features)

    def _perform_cca(self, features: np.ndarray) -> dict[str, Any]:
        """Perform CCA on feature matrices.

        Args:
            features: Feature matrix

        Returns:
            CCA results
        """
        # Split data for CCA (two views)
        mid = len(features) // 2
        X = features[:mid]
        Y = features[mid:2*mid]

        try:
            # Fit CCA
            cca = CCA(n_components=min(self.n_components, min(X.shape[1], Y.shape[1])))
            X_c, Y_c = cca.fit_transform(X, Y)

            # Compute correlations
            correlations = [
                np.corrcoef(X_c[:, i], Y_c[:, i])[0, 1]
                for i in range(X_c.shape[1])
            ]

            result = {
                'status': 'success',
                'n_components': X_c.shape[1],
                'canonical_correlations': [float(c) for c in correlations],
                'X_shape': X.shape,
                'Y_shape': Y.shape,
            }
        except Exception as e:
            result = {
                'status': 'error',
                'message': str(e)
            }

        return result

    def save_results(self, result: dict[str, Any], output_path: Path) -> None:
        """Save CCA results to JSON file.

        Args:
            result: CCA result dictionary
            output_path: Path to output file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
