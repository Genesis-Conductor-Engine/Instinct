"""Super-learner ensemble arbiter module."""
import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict
from sklearn.preprocessing import StandardScaler


class SuperLearner:
    """Super-learner ensemble for CVE risk prediction.

    Combines multiple base learners using stacking to create a meta-learner
    that provides robust predictions for vulnerability risk assessment.
    Blue-team defensive analysis only.
    """

    def __init__(self, config: dict[str, Any] | None = None, n_folds: int = 5):
        """Initialize super-learner with configuration.

        Args:
            config: Optional configuration dictionary
            n_folds: Number of cross-validation folds
        """
        self.config = config or {}
        self.n_folds = n_folds
        self.scaler = StandardScaler()

        # Base learners
        self.base_learners = [
            ('rf', RandomForestClassifier(n_estimators=100, random_state=42)),
            ('gb', GradientBoostingClassifier(n_estimators=100, random_state=42)),
            ('lr', LogisticRegression(max_iter=1000, random_state=42)),
        ]

        # Meta-learner
        self.meta_learner = LogisticRegression(max_iter=1000, random_state=42)

    def fit_predict_from_file(self, input_path: Path) -> dict[str, Any]:
        """Fit super-learner and generate predictions from file.

        Args:
            input_path: Path to input JSON file with CVE data

        Returns:
            Dictionary with predictions and metrics
        """
        with open(input_path) as f:
            data = json.load(f)

        cves = data.get('cves', [])

        # Extract features and labels
        X, y = self._prepare_data(cves)

        if len(X) < self.n_folds:
            return {
                'status': 'insufficient_data',
                'message': f'Need at least {self.n_folds} samples for cross-validation'
            }

        # Fit and predict
        result = self._fit_predict(X, y)

        return result

    def _prepare_data(self, cves: list) -> tuple:
        """Prepare feature matrix and labels from CVE records.

        Args:
            cves: List of CVE records

        Returns:
            Tuple of (features, labels)
        """
        X = []
        y = []

        for cve in cves:
            # Extract features
            feature_vec = [
                cve.get('cvss_score', 0.0),
                len(cve.get('references', [])),
                len(cve.get('description', '')),
                1 if cve.get('severity') in ['HIGH', 'CRITICAL'] else 0,
            ]
            X.append(feature_vec)

            # Create binary label (high risk vs low risk)
            y.append(1 if cve.get('cvss_score', 0.0) >= 7.0 else 0)

        return np.array(X), np.array(y)

    def _fit_predict(self, X: np.ndarray, y: np.ndarray) -> dict[str, Any]:
        """Fit super-learner and generate predictions.

        Args:
            X: Feature matrix
            y: Labels

        Returns:
            Predictions and metrics
        """
        try:
            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Generate base learner predictions using cross-validation
            base_predictions = []
            for name, learner in self.base_learners:
                preds = cross_val_predict(
                    learner, X_scaled, y, cv=self.n_folds, method='predict_proba'
                )
                base_predictions.append(preds[:, 1])  # Probability of class 1

            # Stack predictions for meta-learner
            meta_features = np.column_stack(base_predictions)

            # Train meta-learner
            meta_preds = cross_val_predict(
                self.meta_learner, meta_features, y, cv=self.n_folds
            )

            # Calculate accuracy
            accuracy = float(np.mean(meta_preds == y))

            result = {
                'status': 'success',
                'n_samples': len(X),
                'n_features': X.shape[1],
                'n_base_learners': len(self.base_learners),
                'cv_accuracy': accuracy,
                'predictions': meta_preds.tolist(),
            }
        except Exception as e:
            result = {
                'status': 'error',
                'message': str(e)
            }

        return result

    def save_predictions(self, result: dict[str, Any], output_path: Path) -> None:
        """Save predictions to JSON file.

        Args:
            result: Prediction results
            output_path: Path to output file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
