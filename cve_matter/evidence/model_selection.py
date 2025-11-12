"""Model evidence analysis using information criteria."""
import numpy as np
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score


class EvidenceAnalyzer:
    """Compute model evidence using BIC and WAIC criteria.
    
    Provides Bayesian and information-theoretic model selection metrics
    for evaluating vulnerability prediction models. Blue-team analysis only.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize evidence analyzer with configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
    def compute_evidence_from_file(self, input_path: Path,
                                   criteria: List[str] = ['bic', 'waic']) -> Dict[str, Any]:
        """Compute model evidence from CVE data file.
        
        Args:
            input_path: Path to input JSON file with CVE data
            criteria: List of criteria to compute ('bic', 'waic')
            
        Returns:
            Dictionary with evidence analysis results
        """
        with open(input_path) as f:
            data = json.load(f)
            
        cves = data.get('cves', [])
        
        # Prepare data
        X, y = self._prepare_data(cves)
        
        if len(X) < 10:
            return {
                'status': 'insufficient_data',
                'message': 'Need at least 10 samples for evidence analysis'
            }
        
        # Compute evidence
        result = self._compute_evidence(X, y, criteria)
        
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
            feature_vec = [
                cve.get('cvss_score', 0.0),
                len(cve.get('references', [])),
                len(cve.get('description', '')),
            ]
            X.append(feature_vec)
            
            # Binary label (high risk vs low risk)
            y.append(1 if cve.get('cvss_score', 0.0) >= 7.0 else 0)
        
        return np.array(X), np.array(y)
    
    def _compute_evidence(self, X: np.ndarray, y: np.ndarray,
                         criteria: List[str]) -> Dict[str, Any]:
        """Compute model evidence using specified criteria.
        
        Args:
            X: Feature matrix
            y: Labels
            criteria: List of criteria to compute
            
        Returns:
            Evidence analysis results
        """
        try:
            # Fit a simple logistic regression model
            model = LogisticRegression(max_iter=1000, random_state=42)
            model.fit(X, y)
            
            n_samples = len(X)
            n_params = X.shape[1] + 1  # Features + intercept
            
            # Compute log-likelihood
            y_pred_proba = model.predict_proba(X)
            log_likelihood = np.sum(np.log(y_pred_proba[np.arange(n_samples), y] + 1e-10))
            
            result = {
                'status': 'success',
                'n_samples': n_samples,
                'n_parameters': n_params,
                'log_likelihood': float(log_likelihood),
            }
            
            # Compute BIC (Bayesian Information Criterion)
            if 'bic' in criteria:
                bic = -2 * log_likelihood + n_params * np.log(n_samples)
                result['bic'] = float(bic)
            
            # Compute WAIC (Watanabe-Akaike Information Criterion)
            if 'waic' in criteria:
                # Simplified WAIC computation
                # In practice, this requires sampling from posterior
                pointwise_log_likelihood = np.log(y_pred_proba[np.arange(n_samples), y] + 1e-10)
                lppd = np.sum(pointwise_log_likelihood)
                p_waic = np.var(pointwise_log_likelihood)
                waic = -2 * (lppd - p_waic)
                result['waic'] = float(waic)
                result['p_waic'] = float(p_waic)
            
            # Compute AIC for comparison
            aic = -2 * log_likelihood + 2 * n_params
            result['aic'] = float(aic)
            
            # Cross-validation score
            cv_scores = cross_val_score(model, X, y, cv=5)
            result['cv_accuracy_mean'] = float(np.mean(cv_scores))
            result['cv_accuracy_std'] = float(np.std(cv_scores))
            
        except Exception as e:
            result = {
                'status': 'error',
                'message': str(e)
            }
        
        return result
    
    def save_results(self, result: Dict[str, Any], output_path: Path) -> None:
        """Save evidence results to JSON file.
        
        Args:
            result: Evidence analysis results
            output_path: Path to output file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
