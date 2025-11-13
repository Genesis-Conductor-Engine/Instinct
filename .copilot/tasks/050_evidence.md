# Task 050: Bayesian Evidence Calculation

## Goal

Implement Bayesian evidence calculation for model comparison and vulnerability prioritization using BIC, WAIC, Bayes factors, and Jeffreys scale interpretation.

## Files to Create/Edit

### New Files
- `src/evaluation/__init__.py` - Package initialization
- `src/evaluation/evidence.py` - Bayesian evidence implementation
- `src/evaluation/bayes_factor.py` - Bayes factor calculation
- `src/evaluation/jeffreys.py` - Jeffreys scale interpretation
- `tests/evaluation/__init__.py` - Test package initialization
- `tests/evaluation/test_evidence.py` - Tests for evidence calculation
- `tests/evaluation/test_bayes_factor.py` - Tests for Bayes factors

### Supporting Files
- `requirements.txt` - Add `scipy` for statistical functions
- `config/evidence.yaml` - Evidence calculation configuration

## Requirements

### Functional Requirements

1. **BIC (Bayesian Information Criterion)**
   - Calculate BIC = -2*log_likelihood + k*log(n)
   - Use for model selection and comparison
   - Lower BIC indicates better model fit

2. **WAIC (Widely Applicable Information Criterion)**
   - Calculate WAIC for hierarchical models
   - Use as default method (more robust than BIC)
   - Provide pointwise WAIC for diagnostic purposes

3. **Bayes Factor**
   - Calculate Bayes factor for model comparison
   - BF = p(Data|Model1) / p(Data|Model2)
   - Support log-space calculations for numerical stability

4. **Jeffreys Scale**
   - Interpret Bayes factors using Jeffreys scale
   - Classify evidence strength: weak, moderate, strong, decisive
   - Provide human-readable interpretations

5. **Priority Scoring**
   - Combine evidence scores for vulnerability prioritization
   - Normalize scores to [0, 1] range
   - Support custom weighting schemes

### Acceptance Criteria
- [ ] BIC calculation implemented correctly
- [ ] WAIC calculation working (default method)
- [ ] Bayes factor computation in log-space
- [ ] Jeffreys scale interpretation
- [ ] Priority score generation
- [ ] Tests with known statistical examples
- [ ] Tests achieve >80% coverage
- [ ] Docstrings for all public APIs

## Implementation Guidance

```python
import numpy as np
from scipy.special import logsumexp

def calculate_bic(log_likelihood: float, n_params: int, n_samples: int) -> float:
    """Calculate Bayesian Information Criterion"""
    return -2 * log_likelihood + n_params * np.log(n_samples)

def calculate_waic(log_likelihoods: np.ndarray) -> float:
    """Calculate Widely Applicable Information Criterion"""
    # WAIC = -2 * (lppd - p_waic)
    # lppd: log pointwise predictive density
    # p_waic: effective number of parameters
    
    lppd = np.sum(logsumexp(log_likelihoods, axis=0) - np.log(log_likelihoods.shape[0]))
    p_waic = np.sum(np.var(log_likelihoods, axis=0))
    
    waic = -2 * (lppd - p_waic)
    return waic

def calculate_bayes_factor(
    log_evidence_m1: float,
    log_evidence_m2: float
) -> float:
    """Calculate Bayes factor for model comparison"""
    return np.exp(log_evidence_m1 - log_evidence_m2)

def interpret_bayes_factor(bf: float) -> str:
    """Interpret Bayes factor using Jeffreys scale"""
    log_bf = np.log10(bf)
    
    if log_bf < 0.5:
        return "Weak evidence"
    elif log_bf < 1.0:
        return "Moderate evidence"
    elif log_bf < 1.5:
        return "Strong evidence"
    elif log_bf < 2.0:
        return "Very strong evidence"
    else:
        return "Decisive evidence"

class EvidenceCalculator:
    """Calculate Bayesian evidence for CVE prioritization"""
    
    def __init__(self, method: str = 'waic'):
        self.method = method
        
    def calculate_evidence(
        self,
        predictions: np.ndarray,
        ground_truth: np.ndarray,
        **kwargs
    ) -> Dict[str, float]:
        """
        Calculate evidence scores for predictions.
        
        Returns dict with:
        - evidence_score: primary score (BIC or WAIC)
        - log_likelihood: model fit
        - complexity_penalty: model complexity term
        """
        if self.method == 'bic':
            return self._calculate_bic_evidence(predictions, ground_truth, **kwargs)
        elif self.method == 'waic':
            return self._calculate_waic_evidence(predictions, ground_truth, **kwargs)
        else:
            raise ValueError(f"Unknown method: {self.method}")
```

## Configuration

```yaml
evidence:
  default_method: waic  # or bic
  jeffreys_scale:
    weak: 1.0
    moderate: 3.2
    strong: 10.0
    very_strong: 31.6
    decisive: 100.0
```

## References
- Gelman, A. et al. (2014). "Bayesian Data Analysis" (3rd ed.)
- Watanabe, S. (2010). "Asymptotic Equivalence of Bayes Cross Validation and WAIC"
- Jeffreys, H. (1961). "Theory of Probability" (3rd ed.)
- Kass, R. E. & Raftery, A. E. (1995). "Bayes Factors"
