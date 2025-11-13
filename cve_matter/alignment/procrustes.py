"""Procrustes alignment analysis module."""
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial import procrustes


class ProcrustesAlignment:
    """Perform Procrustes analysis for shape alignment in CVE feature space.

    This module provides statistical alignment methods for comparing
    vulnerability patterns across different datasets or time periods.
    Defensive analysis only - no offensive capabilities.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize Procrustes alignment with configuration.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.alignment_params = self.config.get('alignment', {})

    def align_from_file(self, input_path: Path) -> dict[str, Any]:
        """Perform Procrustes alignment on CVE data from file.

        Args:
            input_path: Path to input JSON file with CVE data

        Returns:
            Dictionary with alignment results
        """
        with open(input_path) as f:
            data = json.load(f)

        cves = data.get('cves', [])

        # Extract feature matrices for alignment
        features = self._extract_features(cves)

        # Perform alignment if we have enough data
        if len(features) >= 2:
            result = self._perform_alignment(features)
        else:
            result = {
                'status': 'insufficient_data',
                'message': 'Need at least 2 data points for alignment'
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
            # Extract numerical features for alignment
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

    def _perform_alignment(self, features: np.ndarray) -> dict[str, Any]:
        """Perform Procrustes alignment on feature matrices.

        Args:
            features: Feature matrix

        Returns:
            Alignment results
        """
        # Split data for comparison (e.g., first half vs second half)
        mid = len(features) // 2
        matrix1 = features[:mid]
        matrix2 = features[mid:2*mid]  # Match dimensions

        try:
            # Perform Procrustes analysis
            mtx1, mtx2, disparity = procrustes(matrix1, matrix2)

            result = {
                'status': 'success',
                'disparity': float(disparity),
                'transformation': 'procrustes',
                'matrix1_shape': matrix1.shape,
                'matrix2_shape': matrix2.shape,
                'aligned_matrix1_shape': mtx1.shape,
                'aligned_matrix2_shape': mtx2.shape,
            }
        except Exception as e:
            result = {
                'status': 'error',
                'message': str(e)
            }

        return result

    def save_results(self, result: dict[str, Any], output_path: Path) -> None:
        """Save alignment results to JSON file.

        Args:
            result: Alignment result dictionary
            output_path: Path to output file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
